"""Runtime bootstrapper, hardware doctor, and Apple GPTK D3DMetal DMG extractor."""

from __future__ import annotations

import json
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
import urllib.request

from m5runner.backends import find_wine_binary
from m5runner.config import (
    D3DMETAL_SDK_DIR,
    DEFAULT_PREFIX,
    DXMT_SDK_DIR,
    LEGACY_WOW64_PREFIX,
    MOLTENVK_RT_SDK_DIR,
    WINE_SDK_DIR,
    ensure_runtime_dirs,
)


def run_doctor() -> dict[str, dict[str, str | bool]]:
    """Inspect M5 Max hardware, macOS version, Rosetta 2, and translation SDK status."""
    report: dict[str, dict[str, str | bool]] = {}

    # 1. CPU & Unified Memory check
    cpu_brand = _sysctl_str("machdep.cpu.brand_string") or platform.processor()
    mem_bytes_str = _sysctl_str("hw.memsize")
    mem_gb = int(mem_bytes_str) // (1024**3) if mem_bytes_str.isdigit() else 0
    report["hardware"] = {
        "ok": "M5" in cpu_brand or mem_gb >= 64,
        "detail": f"{cpu_brand} ({mem_gb} GB Unified Memory)",
    }

    # 2. macOS Version check
    macos_ver = platform.mac_ver()[0] or "unknown"
    report["macos"] = {
        "ok": True,
        "detail": f"macOS {macos_ver}",
    }

    # 3. Rosetta 2 check
    rosetta_ok = Path("/Library/Apple/usr/share/rosetta/rosetta").exists() or Path(
        "/usr/libexec/rosetta/oahd"
    ).exists()
    report["rosetta2"] = {
        "ok": rosetta_ok,
        "detail": "Installed (AVX/AVX2/F16C advertisement supported)" if rosetta_ok else "Not detected",
    }

    # 4. Wine WoW64 Runtime check
    wine_bin = find_wine_binary()
    report["wine"] = {
        "ok": wine_bin.exists(),
        "detail": str(wine_bin) if wine_bin.exists() else f"Missing (run 'm5runner bootstrap' -> {WINE_SDK_DIR})",
    }

    # 5. Winetricks check
    winetricks_bin = shutil.which("winetricks")
    report["winetricks"] = {
        "ok": bool(winetricks_bin),
        "detail": winetricks_bin or "Missing (run 'm5runner bootstrap')",
    }

    # 6. DXMT Backend check
    dxmt_candidates = [
        DXMT_SDK_DIR / "x86_64-windows" / "d3d11.dll",
        DXMT_SDK_DIR / "lib" / "wine" / "x86_64-windows" / "d3d11.dll",
        DXMT_SDK_DIR / "d3d11.dll",
        *sorted(DXMT_SDK_DIR.glob("v*/x86_64-windows/d3d11.dll"), reverse=True),
    ]
    dxmt_dll = _find_first(dxmt_candidates)
    report["dxmt"] = {
        "ok": dxmt_dll is not None,
        "detail": str(dxmt_dll) if dxmt_dll else f"Missing (run 'm5runner bootstrap' -> {DXMT_SDK_DIR})",
    }

    # 7. Apple D3DMetal (GPTK 3/4) check
    d3dmetal_bin = _find_first(
        [
            D3DMETAL_SDK_DIR / "external" / "D3DMetal.framework" / "Versions" / "A" / "D3DMetal",
            D3DMETAL_SDK_DIR / "external" / "D3DMetal.framework" / "D3DMetal",
            D3DMETAL_SDK_DIR / "D3DMetal.framework" / "Versions" / "A" / "D3DMetal",
            D3DMETAL_SDK_DIR / "D3DMetal.framework" / "D3DMetal",
            D3DMETAL_SDK_DIR / "wine" / "x86_64-windows" / "d3d12.dll",
            D3DMETAL_SDK_DIR / "windows" / "system32" / "d3d12.dll",
            D3DMETAL_SDK_DIR / "d3d12.dll",
        ]
    )
    report["d3dmetal"] = {
        "ok": d3dmetal_bin is not None,
        "detail": (
            str(d3dmetal_bin)
            if d3dmetal_bin
            else f"Missing (run 'm5runner import-gptk <GPTK.dmg>' -> {D3DMETAL_SDK_DIR})"
        ),
    }

    # 8. Custom MoltenVK Ray Tracing check
    mvk_rt = MOLTENVK_RT_SDK_DIR / "libMoltenVK.dylib"
    report["moltenvk_rt"] = {
        "ok": mvk_rt.exists(),
        "detail": (
            str(mvk_rt)
            if mvk_rt.exists()
            else f"Optional for DOOM: The Dark Ages (run 'm5runner build-moltenvk-rt' -> {mvk_rt})"
        ),
    }

    # 9. XIV on Mac check
    xiv_app = _find_first(
        [
            Path("/Applications/XIV on Mac.app"),
            Path.home() / "Applications" / "XIV on Mac.app",
        ]
    )
    report["xiv_on_mac"] = {
        "ok": xiv_app is not None,
        "detail": str(xiv_app) if xiv_app else "Optional for FFXIV (run 'm5runner bootstrap --with-xiv')",
    }

    return report


def bootstrap_environment(
    install_xiv: bool = False,
    gptk_source: Path | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Install and configure DXMT, Wine 11.x WoW64, winetricks, prefixes, and optional GPTK/XIV."""
    steps: list[str] = []
    if not dry_run:
        ensure_runtime_dirs()
    steps.append(f"Initialized runtime directory layout under {WINE_SDK_DIR.parent.parent}")

    # 1. Install winetricks via Homebrew if missing
    if not shutil.which("winetricks"):
        steps.append("Install winetricks via Homebrew (`brew install winetricks`)")
        if not dry_run:
            subprocess.run(["brew", "install", "winetricks"], check=True)
    else:
        steps.append("Verified winetricks is already installed")

    # 2. Download & extract 3Shain/dxmt latest release into ~/Games/sdk/dxmt
    steps.append(f"Provision latest 3Shain/dxmt release into {DXMT_SDK_DIR}")
    if not dry_run:
        _install_latest_dxmt()

    # 3. Download & extract Gcenx Wine Staging 11.x (WoW64 + msync) into ~/Games/sdk/wine
    if not find_wine_binary().exists():
        steps.append(f"Download & extract Gcenx Wine 11.x (WoW64 + msync) into {WINE_SDK_DIR}")
        if not dry_run:
            _install_latest_gcenx_wine()
    else:
        steps.append(f"Verified Wine binary at {find_wine_binary()}")

    # 4. Optional XIV on Mac installation
    if install_xiv:
        steps.append("Install XIV on Mac via Homebrew (`brew install --cask xiv-on-mac`)")
        if not dry_run:
            subprocess.run(["brew", "install", "--cask", "xiv-on-mac"], check=False)

    # 5. Optional GPTK D3DMetal extraction
    if gptk_source:
        steps.extend(import_gptk_d3dmetal(gptk_source, dry_run=dry_run))

    # 6. Prepare default_prefix and legacy_wow64 directories
    steps.append(f"Prepared 64-bit prefix at {DEFAULT_PREFIX} and WoW64 prefix at {LEGACY_WOW64_PREFIX}")
    return steps


def setup_or_launch_windows_steam(
    prefix_path: Path = DEFAULT_PREFIX,
    dry_run: bool = False,
) -> list[str]:
    """Download/install Windows SteamSetup.exe into the prefix or launch steam.exe."""
    actions: list[str] = []
    steam_exe = prefix_path / "drive_c" / "Program Files (x86)" / "Steam" / "steam.exe"
    installer_path = prefix_path / "drive_c" / "windows" / "temp" / "SteamSetup.exe"
    wine_bin = find_wine_binary()

    env = {
        **dict(__import__("os").environ),
        "WINEPREFIX": str(prefix_path),
        "WINEMSYNC": "1",
        "ROSETTA_ADVERTISE_AVX": "1",
    }

    if not steam_exe.exists():
        actions.append(f"Download Windows SteamSetup.exe -> {installer_path}")
        actions.append(f"Run `{wine_bin} {installer_path}` inside {prefix_path}")
        if not dry_run:
            installer_path.parent.mkdir(parents=True, exist_ok=True)
            req = urllib.request.Request(
                "https://cdn.akamai.steamstatic.com/client/installer/SteamSetup.exe",
                headers={"User-Agent": "m5-wine-runner/0.1.0"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                installer_path.write_bytes(resp.read())
            subprocess.run([str(wine_bin), str(installer_path)], env=env, check=True)
    else:
        cmd = [
            str(wine_bin),
            str(steam_exe),
            "-cef-disable-gpu-compositing",
            "-no-cef-sandbox",
        ]
        actions.append(f"Launch Windows Steam inside prefix: {' '.join(cmd)}")
        if not dry_run:
            subprocess.run(cmd, env=env, check=False)

    return actions


def download_game_via_steamcmd(
    app_id: int,
    game_name: str,
    install_dir: Path,
    steam_user: str,
    dry_run: bool = False,
) -> list[str]:
    """Download a Windows game depot on macOS using steamcmd."""
    actions: list[str] = []
    if not shutil.which("steamcmd"):
        actions.append("Install steamcmd via Homebrew (`brew install --cask steamcmd`)")
        if not dry_run:
            subprocess.run(["brew", "install", "--cask", "steamcmd"], check=True)

    cmd = [
        "steamcmd",
        "+@sSteamCmdForcePlatformType",
        "windows",
        "+force_install_dir",
        str(install_dir),
        "+login",
        steam_user,
        "+app_update",
        str(app_id),
        "validate",
        "+quit",
    ]
    actions.append(f"Download {game_name} (AppID {app_id}) -> {install_dir}")
    actions.append(f"Command: {' '.join(cmd)}")
    if not dry_run:
        install_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(cmd, check=True)

    return actions


def _install_latest_dxmt() -> Path:
    """Download the latest dxmt-v*-builtin.tar.gz release from 3Shain/dxmt and extract it."""
    api_url = "https://api.github.com/repos/3Shain/dxmt/releases/latest"
    req = urllib.request.Request(api_url, headers={"User-Agent": "m5-wine-runner/0.1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        release = json.loads(resp.read().decode("utf-8"))

    asset_url = None
    asset_name = "dxmt-builtin.tar.gz"
    for asset in release.get("assets", []):
        if asset["name"].endswith(".tar.gz"):
            asset_url = asset["browser_download_url"]
            asset_name = asset["name"]
            break

    if not asset_url:
        raise RuntimeError("No .tar.gz asset found in 3Shain/dxmt latest release")

    DXMT_SDK_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = DXMT_SDK_DIR / asset_name
    dl_req = urllib.request.Request(asset_url, headers={"User-Agent": "m5-wine-runner/0.1.0"})
    with urllib.request.urlopen(dl_req, timeout=60) as resp:
        archive_path.write_bytes(resp.read())

    with tarfile.open(archive_path, "r:gz") as tf:
        tf.extractall(path=DXMT_SDK_DIR, filter="data")

    # Flatten versioned subdirectory (e.g. v0.80/{x86_64-unix,x86_64-windows,i386-windows})
    for ver_dir in sorted(DXMT_SDK_DIR.glob("v*")):
        if ver_dir.is_dir():
            for sub in ver_dir.iterdir():
                dst = DXMT_SDK_DIR / sub.name
                if dst.exists():
                    shutil.rmtree(dst) if dst.is_dir() else dst.unlink()
                shutil.copytree(sub, dst) if sub.is_dir() else shutil.copy2(sub, dst)

    return DXMT_SDK_DIR


def _install_latest_gcenx_wine() -> Path:
    """Download the latest wine-staging-*-osx64.tar.xz from Gcenx/macOS_Wine_builds."""
    api_url = "https://api.github.com/repos/Gcenx/macOS_Wine_builds/releases/latest"
    req = urllib.request.Request(api_url, headers={"User-Agent": "m5-wine-runner/0.1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        release = json.loads(resp.read().decode("utf-8"))

    asset_url = None
    asset_name = "wine-staging-osx64.tar.xz"
    for asset in release.get("assets", []):
        if "staging" in asset["name"] and asset["name"].endswith(".tar.xz"):
            asset_url = asset["browser_download_url"]
            asset_name = asset["name"]
            break

    if not asset_url:
        raise RuntimeError("Could not find wine-staging tar.xz in Gcenx/macOS_Wine_builds")

    WINE_SDK_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = WINE_SDK_DIR.parent / asset_name
    dl_req = urllib.request.Request(asset_url, headers={"User-Agent": "m5-wine-runner/0.1.0"})
    with urllib.request.urlopen(dl_req, timeout=180) as resp:
        archive_path.write_bytes(resp.read())

    subprocess.run(["tar", "-xf", str(archive_path), "-C", str(WINE_SDK_DIR.parent)], check=True)
    extracted_app = WINE_SDK_DIR.parent / "Wine Staging.app"
    if extracted_app.exists():
        subprocess.run(
            ["/usr/bin/xattr", "-drs", "com.apple.quarantine", str(extracted_app)],
            check=False,
        )
        wine_res = extracted_app / "Contents" / "Resources" / "wine"
        if wine_res.exists():
            if WINE_SDK_DIR.exists():
                shutil.rmtree(WINE_SDK_DIR)
            shutil.move(str(wine_res), str(WINE_SDK_DIR))
            shutil.rmtree(extracted_app, ignore_errors=True)
    archive_path.unlink(missing_ok=True)
    return WINE_SDK_DIR


def _attach_dmg(dmg_path: Path) -> Path:
    """Attach a DMG read-only and return its /Volumes/... mount point."""
    out = subprocess.check_output(
        ["hdiutil", "attach", "-nobrowse", "-readonly", str(dmg_path)],
        text=True,
    )
    for line in out.splitlines():
        if "/Volumes/" in line:
            return Path(line[line.index("/Volumes/") :].strip())
    raise RuntimeError(f"Failed to determine mount point for {dmg_path}")


def import_gptk_d3dmetal(source_path: Path, dry_run: bool = False) -> list[str]:
    """Extract D3DMetal.framework and redistribution libraries from an Apple GPTK DMG or directory.

    Supports both outer `Game_Porting_Toolkit_*.dmg` (which contains a nested
    `Evaluation environment for Windows games *.dmg`) and direct `Evaluation environment*.dmg`.
    """
    actions: list[str] = []
    if not source_path.exists():
        raise FileNotFoundError(f"GPTK source not found: {source_path}")

    if dry_run:
        actions.append(
            f"Mount/inspect {source_path} (including nested Evaluation Environment DMG) and copy redist/lib into {D3DMETAL_SDK_DIR}"
        )
        return actions

    ensure_runtime_dirs()
    mounted_volumes: list[Path] = []

    try:
        if source_path.suffix.lower() == ".dmg":
            outer_vol = _attach_dmg(source_path)
            mounted_volumes.append(outer_vol)
            search_root = outer_vol

            # Check for nested "Evaluation environment for Windows games *.dmg"
            nested_dmgs = list(outer_vol.glob("*Evaluation environment*.dmg")) + list(
                outer_vol.glob("*/*.dmg")
            )
            if nested_dmgs:
                inner_vol = _attach_dmg(nested_dmgs[0])
                mounted_volumes.append(inner_vol)
                search_root = inner_vol
                actions.append(f"Mounted nested image: {nested_dmgs[0].name} -> {inner_vol}")
        else:
            search_root = source_path

        # 1. If standard GPTK `redist/lib` layout exists, copy `external` and `wine` trees intact
        redist_lib = search_root / "redist" / "lib"
        if redist_lib.exists():
            for subdir_name in ("external", "wine"):
                src_sub = redist_lib / subdir_name
                if src_sub.exists():
                    dst_sub = D3DMETAL_SDK_DIR / subdir_name
                    if dst_sub.exists():
                        shutil.rmtree(dst_sub)
                    shutil.copytree(src_sub, dst_sub, symlinks=True)
                    actions.append(f"Extracted {src_sub} -> {dst_sub}")

            # Also expose top-level D3DMetal.framework symlink/copy for compatibility
            ext_fw = D3DMETAL_SDK_DIR / "external" / "D3DMetal.framework"
            top_fw = D3DMETAL_SDK_DIR / "D3DMetal.framework"
            if ext_fw.exists():
                if top_fw.exists() or top_fw.is_symlink():
                    shutil.rmtree(top_fw) if top_fw.is_dir() and not top_fw.is_symlink() else top_fw.unlink()
                top_fw.symlink_to(ext_fw)

            # Copy external/{D3DMetal.framework, libd3dshared.dylib} into Wine SDK's lib/external
            if (WINE_SDK_DIR / "lib").exists() and (D3DMETAL_SDK_DIR / "external").exists():
                wine_ext = WINE_SDK_DIR / "lib" / "external"
                if wine_ext.exists():
                    shutil.rmtree(wine_ext)
                shutil.copytree(D3DMETAL_SDK_DIR / "external", wine_ext, symlinks=True)
                actions.append(f"Linked GPTK 4 external libraries into Wine runtime: {wine_ext}")
        else:
            # Fallback recursive search for custom extracted directories
            for candidate in search_root.rglob("D3DMetal.framework"):
                dst_fw = D3DMETAL_SDK_DIR / "D3DMetal.framework"
                if dst_fw.exists():
                    shutil.rmtree(dst_fw)
                shutil.copytree(candidate, dst_fw, symlinks=True)
                actions.append(f"Extracted {candidate} -> {dst_fw}")
                break

            for dll_name in (
                "d3d10.dll",
                "d3d11.dll",
                "d3d12.dll",
                "d3d12core.dll",
                "dxgi.dll",
                "nvapi64.dll",
                "nvngx.dll",
                "nvngx-on-metalfx.dll",
                "libd3dshared.dylib",
            ):
                for match in search_root.rglob(dll_name):
                    dst = D3DMETAL_SDK_DIR / match.name
                    shutil.copy2(match, dst)
                    actions.append(f"Extracted {match.name} -> {dst}")
                    break

        subprocess.run(
            ["/usr/bin/xattr", "-drs", "com.apple.quarantine", str(D3DMETAL_SDK_DIR)],
            check=False,
        )
    finally:
        for vol in reversed(mounted_volumes):
            if vol.exists():
                subprocess.run(["hdiutil", "detach", str(vol)], check=False, capture_output=True)

    return actions


def _sysctl_str(key: str) -> str:
    try:
        return subprocess.check_output(["sysctl", "-n", key], text=True).strip()
    except Exception:
        return ""


def _find_first(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None
