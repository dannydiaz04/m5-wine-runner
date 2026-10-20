"""Graphics backend environment builder & DLL staging router (D3DMetal, DXMT, MoltenVK-RT)."""

from __future__ import annotations

import os
from pathlib import Path
import shutil

from m5runner.config import (
    D3DMETAL_SDK_DIR,
    DEFAULT_M5_ENV,
    DXMT_SDK_DIR,
    MOLTENVK_RT_SDK_DIR,
    WINE_SDK_DIR,
)
from m5runner.profiles import GameProfile


def format_winedlloverrides(overrides: dict[str, str]) -> str:
    """Group DLL overrides with identical load orders into a compact Wine string.

    Example:
        {"d3d11": "n,b", "d3d12": "n,b", "dxgi": "n,b"} -> "d3d11,d3d12,dxgi=n,b"
    """
    grouped: dict[str, list[str]] = {}
    for dll, mode in overrides.items():
        grouped.setdefault(mode, []).append(dll)

    segments: list[str] = []
    for mode, dlls in grouped.items():
        segments.append(f"{','.join(dlls)}={mode}")
    return ";".join(segments)


def find_wine_binary() -> Path:
    """Locate the active Wine64 / Wine WoW64 executable."""
    candidates = [
        WINE_SDK_DIR / "bin" / "wine64",
        WINE_SDK_DIR / "bin" / "wine",
        Path("/Applications/Wine Staging.app/Contents/Resources/wine/bin/wine64"),
        Path("/Applications/Wine Staging.app/Contents/Resources/wine/bin/wine"),
        Path("/Applications/Wine Devel.app/Contents/Resources/wine/bin/wine64"),
        Path("/Applications/Game Porting Toolkit.app/Contents/Resources/wine/bin/wine64"),
        Path("/opt/homebrew/bin/wine64"),
        Path("/opt/homebrew/bin/wine"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return WINE_SDK_DIR / "bin" / "wine64"


def build_execution_environment(
    profile: GameProfile,
    backend_override: str | None = None,
    enable_hud: bool = True,
    base_env: dict[str, str] | None = None,
) -> dict[str, str]:
    """Construct the complete environment dictionary for launching a game."""
    active_backend = backend_override or profile.backend
    env: dict[str, str] = dict(base_env) if base_env is not None else dict(os.environ)

    # 1. Apply M5 Max base environment variables
    env.update(DEFAULT_M5_ENV)
    env["WINEPREFIX"] = str(profile.prefix_path)
    env["MTL_HUD_ENABLED"] = "1" if enable_hud else "0"

    if profile.require_avx:
        env["ROSETTA_ADVERTISE_AVX"] = "1"

    if profile.dlss_metalfx:
        env["D3DM_ENABLE_METALFX"] = "1"

    # 2. Merge backend-specific DLL overrides and dynamic library paths
    dll_overrides: dict[str, str] = {
        "d3d11": "n,b",
        "d3d12": "n,b",
        "dxgi": "n,b",
    }
    dll_overrides.update(profile.dll_overrides)

    wine_lib_dir = find_wine_binary().parent.parent / "lib"

    if active_backend in ("d3dmetal", "d3dmetal_gptk4"):
        d3dm_fw_lib = D3DMETAL_SDK_DIR / "D3DMetal.framework" / "Versions" / "A" / "Libraries"
        dyld_paths = [
            str(d3dm_fw_lib),
            str(D3DMETAL_SDK_DIR / "external"),
            str(D3DMETAL_SDK_DIR),
            str(wine_lib_dir),
            "/usr/lib",
        ]
        env["DYLD_FALLBACK_LIBRARY_PATH"] = ":".join(dyld_paths)
        env["M5RUNNER_ACTIVE_BACKEND"] = active_backend
        if profile.dlss_metalfx:
            dll_overrides.setdefault("nvngx", "n,b")
            dll_overrides.setdefault("_nvngx", "n,b")

    elif active_backend == "dxmt":
        # DXMT uses native d3d10core.dll, d3d11.dll, dxgi.dll + winemetal
        dll_overrides["d3d10core"] = "n,b"
        dll_overrides["d3d11"] = "n,b"
        dll_overrides["dxgi"] = "n,b"
        dyld_paths = [
            str(DXMT_SDK_DIR),
            str(wine_lib_dir),
            "/usr/lib",
        ]
        env["DYLD_FALLBACK_LIBRARY_PATH"] = ":".join(dyld_paths)
        env.setdefault("DXMT_CONFIG", "d3d11.metalSpatialUpscaleFactor=1;dxgi.customVendorId=10de")
        env["M5RUNNER_ACTIVE_BACKEND"] = "dxmt"

    elif active_backend == "moltenvk_rt":
        # DOOM: The Dark Ages — Vulkan-only + Mandatory Hardware Ray Tracing
        # Prepend isolated MoltenVK-RT directory so custom libMoltenVK.dylib is loaded
        dyld_paths = [
            str(MOLTENVK_RT_SDK_DIR),
            str(wine_lib_dir),
            "/usr/lib",
        ]
        env["DYLD_LIBRARY_PATH"] = f"{MOLTENVK_RT_SDK_DIR}:{env.get('DYLD_LIBRARY_PATH', '')}".rstrip(":")
        env["DYLD_FALLBACK_LIBRARY_PATH"] = ":".join(dyld_paths)
        icd_json = MOLTENVK_RT_SDK_DIR / "MoltenVK_icd.json"
        if icd_json.exists():
            env["VK_ICD_FILENAMES"] = str(icd_json)
        env["M5RUNNER_ACTIVE_BACKEND"] = "moltenvk_rt"

    elif active_backend == "xivmac":
        env["M5RUNNER_ACTIVE_BACKEND"] = "xivmac"

    # 3. Apply per-game environment overrides last so profile specifics take precedence
    env.update(profile.env)
    env["WINEDLLOVERRIDES"] = format_winedlloverrides(dll_overrides)
    return env


def stage_backend_dlls_into_prefix(
    profile: GameProfile,
    backend_override: str | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Stage D3DMetal or DXMT DLLs into the target Wine prefix system32 directory."""
    active_backend = backend_override or profile.backend
    sys32_dir = profile.prefix_path / "drive_c" / "windows" / "system32"
    syswow64_dir = profile.prefix_path / "drive_c" / "windows" / "syswow64"
    actions: list[str] = []

    if active_backend in ("d3dmetal", "d3dmetal_gptk4"):
        source_dirs = [
            D3DMETAL_SDK_DIR / "windows" / "system32",
            D3DMETAL_SDK_DIR,
        ]
        dll_names = ["d3d11.dll", "d3d12.dll", "dxgi.dll", "nvngx.dll", "_nvngx.dll"]
        for dll in dll_names:
            for sdir in source_dirs:
                src = sdir / dll
                if src.exists():
                    dst = sys32_dir / dll
                    actions.append(f"Stage D3DMetal {src.name} -> {dst}")
                    if not dry_run:
                        sys32_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dst)
                    break

    elif active_backend == "dxmt":
        # 3Shain/dxmt builtin archive provides x86_64-windows and i386-windows
        x64_src_dirs = [
            DXMT_SDK_DIR / "x86_64-windows",
            DXMT_SDK_DIR / "lib" / "wine" / "x86_64-windows",
            DXMT_SDK_DIR,
        ]
        x86_src_dirs = [
            DXMT_SDK_DIR / "i386-windows",
            DXMT_SDK_DIR / "lib" / "wine" / "i386-windows",
        ]
        for dll in ("d3d10core.dll", "d3d11.dll", "dxgi.dll", "winemetal.dll"):
            for sdir in x64_src_dirs:
                src = sdir / dll
                if src.exists():
                    dst = sys32_dir / dll
                    actions.append(f"Stage DXMT (64-bit) {src.name} -> {dst}")
                    if not dry_run:
                        sys32_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dst)
                    break
            for sdir in x86_src_dirs:
                src = sdir / dll
                if src.exists():
                    dst = syswow64_dir / dll
                    actions.append(f"Stage DXMT (32-bit WoW64) {src.name} -> {dst}")
                    if not dry_run:
                        syswow64_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dst)
                    break

    return actions
