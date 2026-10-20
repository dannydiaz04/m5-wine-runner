"""Runtime bootstrapper, hardware doctor, and Apple GPTK D3DMetal DMG extractor."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import plistlib
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request

from m5runner.backends import ensure_prefix, find_wine_binary
from m5runner.config import (
    D3DMETAL_SDK_DIR,
    DEFAULT_PREFIX,
    DXMT_SDK_DIR,
    GPTK_PREFIX,
    GPTK_WINE_DIR,
    GPTK_WINE_SHA256,
    GPTK_WINE_VERSION,
    LOGS_DIR,
    MOLTENVK_RT_SDK_DIR,
    RUNTIME_ENV,
    SDK_DIR,
    STAGING_WINE_DIR,
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

    # 4. Wine runtimes: GPTK Wine hosts D3DMetal, Wine Staging hosts DXMT / MoltenVK
    for key, backend, runtime_dir in (
        ("wine_gptk", "d3dmetal", GPTK_WINE_DIR),
        ("wine_staging", "dxmt", STAGING_WINE_DIR),
    ):
        wine_bin = find_wine_binary(backend)
        report[key] = {
            "ok": wine_bin.exists(),
            "detail": (
                f"{_wine_version(wine_bin)} ({wine_bin})"
                if wine_bin.exists()
                else f"Missing (run 'm5runner bootstrap' -> {runtime_dir})"
            ),
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

    # 7. Apple D3DMetal: the copy bundled with GPTK Wine is the one games actually use
    runtime_d3dm = _d3dmetal_version(GPTK_WINE_DIR / "lib" / "external")
    report["d3dmetal"] = {
        "ok": runtime_d3dm is not None,
        "detail": (
            f"D3DMetal {runtime_d3dm} bundled with GPTK Wine"
            if runtime_d3dm
            else f"Missing (run 'm5runner bootstrap' -> {GPTK_WINE_DIR})"
        ),
    }
    imported_d3dm = _d3dmetal_version(D3DMETAL_SDK_DIR / "external")
    if imported_d3dm:
        report["gptk_import"] = {
            "ok": True,
            "detail": (
                f"D3DMetal {imported_d3dm} imported to {D3DMETAL_SDK_DIR} (reference only: 4.x needs "
                "a newer Wine than GPTK Wine 7.7, e.g. CrossOver's lib64/apple_gptk)"
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
    """Install both Wine runtimes, DXMT, winetricks, prefixes, and optional GPTK/XIV."""
    steps: list[str] = []
    if not dry_run:
        ensure_runtime_dirs()
    steps.append(f"Initialized runtime directory layout under {SDK_DIR.parent}")

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

    # 3. Download & extract both Wine runtimes (one per backend family)
    if not find_wine_binary("d3dmetal").exists():
        steps.append(f"Download Gcenx game-porting-toolkit {GPTK_WINE_VERSION} (D3DMetal host) into {GPTK_WINE_DIR}")
        if not dry_run:
            _install_gptk_wine()
    else:
        steps.append(f"Verified GPTK Wine at {find_wine_binary('d3dmetal')}")
    if not find_wine_binary("dxmt").exists():
        steps.append(f"Download Gcenx Wine Staging 11.x (DXMT host) into {STAGING_WINE_DIR}")
        if not dry_run:
            _install_wine_staging()
    else:
        steps.append(f"Verified Wine Staging at {find_wine_binary('dxmt')}")

    # 4. Optional XIV on Mac installation
    if install_xiv:
        steps.append("Install XIV on Mac via Homebrew (`brew install --cask xiv-on-mac`)")
        if not dry_run:
            subprocess.run(["brew", "install", "--cask", "xiv-on-mac"], check=False)

    # 5. Optional GPTK D3DMetal extraction
    if gptk_source:
        steps.extend(import_gptk_d3dmetal(gptk_source, dry_run=dry_run))

    # 6. Initialize one prefix per runtime (Windows 10, created by the runtime that will run it)
    for backend, prefix in (("d3dmetal", GPTK_PREFIX), ("dxmt", DEFAULT_PREFIX)):
        steps.extend(ensure_prefix(prefix, backend, dry_run=dry_run))
    return steps


def setup_or_launch_windows_steam(
    prefix_path: Path = GPTK_PREFIX,
    backend: str = "d3dmetal",
    dry_run: bool = False,
) -> list[str]:
    """Install Windows Steam into the prefix if needed, then start it in the background.

    Games launched outside Steam (EAC bypass + steam_appid.txt) still call SteamAPI_Init(),
    which needs this client running and signed in inside the same prefix.
    """
    actions: list[str] = ensure_prefix(prefix_path, backend, dry_run=dry_run)
    steam_dir = prefix_path / "drive_c" / "Program Files (x86)" / "Steam"
    steam_exe = steam_dir / "Steam.exe"
    installer_path = prefix_path / "drive_c" / "users" / "Public" / "SteamSetup.exe"
    wine_bin = find_wine_binary(backend)
    env = {
        **os.environ,
        **RUNTIME_ENV["gptk" if backend.startswith("d3dmetal") else "staging"],
        "WINEPREFIX": str(prefix_path),
        "WINEDEBUG": "-all",
    }

    if not steam_exe.exists():
        actions.append(f"Download Windows SteamSetup.exe -> {installer_path}")
        actions.append(f"Silently install Steam into {steam_dir}")
        if not dry_run:
            installer_path.parent.mkdir(parents=True, exist_ok=True)
            req = urllib.request.Request(
                "https://cdn.cloudflare.steamstatic.com/client/installer/SteamSetup.exe",
                headers={"User-Agent": "m5-wine-runner/0.1.0"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                installer_path.write_bytes(resp.read())
            subprocess.run([str(wine_bin), str(installer_path), "/S"], env=env, check=True)

    log_path = LOGS_DIR / "steam.log"
    cmd = [str(wine_bin), str(steam_exe), "-cef-disable-gpu-compositing", "-no-cef-sandbox"]
    actions.append(f"Start Windows Steam in the background (log: {log_path}); sign in once, then leave it running")
    if not dry_run:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        with log_path.open("ab") as log:
            subprocess.Popen(cmd, env=env, cwd=steam_dir, stdout=log, stderr=log, start_new_session=True)

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


def _install_gptk_wine() -> Path:
    """Install Gcenx's game-porting-toolkit build (Apple's GPTK Wine 7.7 + bundled D3DMetal 3).

    Pinned and checksummed: D3DMetal's bridge DLLs must match this Wine's unix-call ABI, so the
    runtime is never upgraded implicitly and nothing is ever overlaid onto it.
    """
    url = (
        "https://github.com/Gcenx/game-porting-toolkit/releases/download/"
        f"Game-Porting-Toolkit-{GPTK_WINE_VERSION}/game-porting-toolkit-{GPTK_WINE_VERSION}.tar.xz"
    )
    return _install_wine_app_archive(url, "Game Porting Toolkit.app", GPTK_WINE_DIR, GPTK_WINE_SHA256)


def _install_wine_staging() -> Path:
    """Install the latest Gcenx Wine Staging build (hosts DXMT and MoltenVK)."""
    api_url = "https://api.github.com/repos/Gcenx/macOS_Wine_builds/releases/latest"
    req = urllib.request.Request(api_url, headers={"User-Agent": "m5-wine-runner/0.1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        release = json.loads(resp.read().decode("utf-8"))

    for asset in release.get("assets", []):
        if "staging" in asset["name"] and asset["name"].endswith(".tar.xz"):
            return _install_wine_app_archive(asset["browser_download_url"], "Wine Staging.app", STAGING_WINE_DIR)
    raise RuntimeError("Could not find wine-staging tar.xz in Gcenx/macOS_Wine_builds")


def _install_wine_app_archive(url: str, app_name: str, dest: Path, sha256: str | None = None) -> Path:
    """Download a Gcenx Wine .app tarball and move its Contents/Resources/wine to dest."""
    if dest.exists():
        raise FileExistsError(f"{dest} already exists; refusing to overwrite a Wine runtime")
    with tempfile.TemporaryDirectory(dir=SDK_DIR) as tmp:
        archive_path = Path(tmp) / "wine.tar.xz"
        req = urllib.request.Request(url, headers={"User-Agent": "m5-wine-runner/0.1.0"})
        with urllib.request.urlopen(req, timeout=300) as resp:
            archive_path.write_bytes(resp.read())
        if sha256 and hashlib.sha256(archive_path.read_bytes()).hexdigest() != sha256:
            raise RuntimeError(f"Checksum mismatch for {url}")
        subprocess.run(["tar", "-xf", str(archive_path), "-C", tmp], check=True)
        shutil.move(str(Path(tmp) / app_name / "Contents" / "Resources" / "wine"), str(dest))
    subprocess.run(["/usr/bin/xattr", "-drs", "com.apple.quarantine", str(dest)], check=False)
    return dest


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

            # Deliberately not copied into a Wine runtime: GPTK 4.x bridge DLLs look up
            # __wine_unix_call_dispatcher, which GPTK Wine 7.7 does not export, so they fail
            # DllMain there. The bundled D3DMetal 3 in GPTK Wine is what the runner uses.
            actions.append(
                "Kept imported D3DMetal out of the runtimes; GPTK Wine keeps its matching bundled D3DMetal"
            )
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


def _wine_version(wine_bin: Path) -> str:
    try:
        return subprocess.check_output([str(wine_bin), "--version"], text=True, timeout=30).strip()
    except Exception:
        return "unknown version"


def _d3dmetal_version(external_dir: Path) -> str | None:
    """D3DMetal.framework version inside a GPTK lib/external directory, if present."""
    plist = external_dir / "D3DMetal.framework" / "Versions" / "A" / "Resources" / "version.plist"
    try:
        with plist.open("rb") as f:
            return str(plistlib.load(f).get("CFBundleShortVersionString", "unknown"))
    except OSError:
        return None


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
