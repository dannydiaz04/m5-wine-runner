"""Graphics backend environment builder & DLL staging router (D3DMetal, DXMT, MoltenVK-RT)."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

from m5runner.config import (
    BACKEND_RUNTIME,
    DEFAULT_M5_ENV,
    DXMT_SDK_DIR,
    MOLTENVK_RT_SDK_DIR,
    RUNTIME_DIRS,
    RUNTIME_ENV,
)
from m5runner.profiles import GameProfile

D3DMETAL_BUILTIN_DLLS = ("d3d10", "d3d10core", "d3d11", "d3d12", "d3d12core", "dxgi")


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


def runtime_for(backend: str) -> str:
    """Name of the Wine runtime ("gptk" or "staging") that hosts a graphics backend."""
    return BACKEND_RUNTIME[backend]


def find_wine_binary(backend: str = "d3dmetal") -> Path:
    """Locate the Wine executable of the runtime that hosts the given backend."""
    runtime = runtime_for(backend)
    runtime_dir = RUNTIME_DIRS[runtime]
    candidates = [runtime_dir / "bin" / "wine64", runtime_dir / "bin" / "wine"]
    if runtime == "gptk":
        candidates.append(Path("/Applications/Game Porting Toolkit.app/Contents/Resources/wine/bin/wine64"))
    else:
        candidates.append(Path("/Applications/Wine Staging.app/Contents/Resources/wine/bin/wine"))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def ensure_prefix(prefix_path: Path, backend: str, dry_run: bool = False) -> list[str]:
    """Create a prefix with the runtime that will run it, reporting Windows 10.

    Never point two runtimes at one prefix: Wine "updates" a prefix to whichever version touches
    it last, and moving a prefix to an older Wine is unsupported.
    """
    if (prefix_path / "system.reg").exists():
        return []
    wine_bin = find_wine_binary(backend)
    actions = [f"Create Windows 10 prefix {prefix_path} with {wine_bin}"]
    if dry_run:
        return actions
    env = {
        **os.environ,
        **RUNTIME_ENV[runtime_for(backend)],
        "WINEPREFIX": str(prefix_path),
        "WINEDEBUG": "-all",
    }
    subprocess.run([str(wine_bin), "wineboot", "-i"], env=env, check=True)
    subprocess.run([str(wine_bin), "winecfg", "-v", "win10"], env=env, check=True)
    subprocess.run([str(wine_bin.parent / "wineserver"), "-w"], env=env, check=False)
    return actions


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
    env.update(RUNTIME_ENV[runtime_for(active_backend)])
    env["WINEPREFIX"] = str(profile.prefix_path_for(active_backend))
    env["MTL_HUD_ENABLED"] = "1" if enable_hud else "0"

    if profile.require_avx:
        env["ROSETTA_ADVERTISE_AVX"] = "1"

    if profile.dlss_metalfx:
        env["D3DM_ENABLE_METALFX"] = "1"

    # 2. Merge backend-specific DLL overrides and dynamic library paths
    dll_overrides: dict[str, str] = dict(profile.dll_overrides)

    wine_lib_dir = find_wine_binary(active_backend).parent.parent / "lib"

    if active_backend in ("d3dmetal", "d3dmetal_gptk4"):
        # GPTK Wine's builtin d3d10/d3d11/d3d12/dxgi already are D3DMetal (resolved through
        # lib/external via the bridge's @loader_path rpath), so no DYLD paths, and a native
        # override could only shadow them with a stray DLL from system32.
        for dll in D3DMETAL_BUILTIN_DLLS:
            dll_overrides.pop(dll, None)
        env["M5RUNNER_ACTIVE_BACKEND"] = active_backend
        if profile.dlss_metalfx:
            dll_overrides.setdefault("nvngx", "n,b")
            dll_overrides.setdefault("nvapi64", "n,b")

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
    if dll_overrides:
        env["WINEDLLOVERRIDES"] = format_winedlloverrides(dll_overrides)
    else:
        env.pop("WINEDLLOVERRIDES", None)
    return env


def stage_backend_dlls_into_prefix(
    profile: GameProfile,
    backend_override: str | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Stage backend DLLs into the prefix. Never writes into the GPTK runtime itself."""
    active_backend = backend_override or profile.backend
    prefix_path = profile.prefix_path_for(active_backend)
    sys32_dir = prefix_path / "drive_c" / "windows" / "system32"
    syswow64_dir = prefix_path / "drive_c" / "windows" / "syswow64"
    actions: list[str] = []

    if active_backend in ("d3dmetal", "d3dmetal_gptk4"):
        # Apple's Read Me: copy nvngx.dll and nvapi64.dll into system32 to enable DLSS -> MetalFX.
        # Only DLSS titles need it; the builtin D3D DLLs come straight from the runtime.
        if profile.dlss_metalfx:
            runtime_win_dir = RUNTIME_DIRS["gptk"] / "lib" / "wine" / "x86_64-windows"
            for dll in ("nvngx.dll", "nvapi64.dll"):
                src = runtime_win_dir / dll
                if src.exists():
                    actions.append(f"Stage D3DMetal {dll} (DLSS -> MetalFX) -> {sys32_dir / dll}")
                    if not dry_run:
                        sys32_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, sys32_dir / dll)

    elif active_backend == "dxmt":
        # 3Shain/dxmt builtin archive provides x86_64-windows, i386-windows, and x86_64-unix
        x64_src_dirs = [
            DXMT_SDK_DIR / "x86_64-windows",
            *sorted(DXMT_SDK_DIR.glob("v*/x86_64-windows"), reverse=True),
            DXMT_SDK_DIR / "lib" / "wine" / "x86_64-windows",
            DXMT_SDK_DIR,
        ]
        x86_src_dirs = [
            DXMT_SDK_DIR / "i386-windows",
            *sorted(DXMT_SDK_DIR.glob("v*/i386-windows"), reverse=True),
            DXMT_SDK_DIR / "lib" / "wine" / "i386-windows",
        ]
        unix_src_dirs = [
            DXMT_SDK_DIR / "x86_64-unix",
            *sorted(DXMT_SDK_DIR.glob("v*/x86_64-unix"), reverse=True),
        ]
        for dll in ("d3d10core.dll", "d3d11.dll", "dxgi.dll", "winemetal.dll", "nvapi64.dll", "nvngx.dll"):
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

        # DXMT's winemetal.so belongs to the staging runtime (it needs __wine_unix_call_dispatcher)
        wine_unix_dst = RUNTIME_DIRS["staging"] / "lib" / "wine" / "x86_64-unix"
        for sdir in unix_src_dirs:
            wm_so = sdir / "winemetal.so"
            if wm_so.exists() and wine_unix_dst.exists():
                actions.append(f"Stage DXMT Unix bridge {wm_so.name} -> {wine_unix_dst / wm_so.name}")
                if not dry_run:
                    shutil.copy2(wm_so, wine_unix_dst / wm_so.name)
                break

    return actions
