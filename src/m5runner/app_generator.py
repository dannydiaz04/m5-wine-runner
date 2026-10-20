"""macOS .app bundle generator for ~/Applications matching native/Steam app bundles."""

from __future__ import annotations

from pathlib import Path
import plistlib
import stat

from m5runner.config import APPLICATIONS_DIR, LOGS_DIR, PROJECT_ROOT
from m5runner.profiles import GameProfile


def create_macos_app_bundle(
    profile: GameProfile,
    output_dir: Path = APPLICATIONS_DIR,
    enable_hud: bool = True,
    dry_run: bool = False,
) -> Path:
    """Create a double-clickable macOS .app wrapper for a GameProfile in ~/Applications."""
    safe_app_name = profile.name.replace(":", " -").replace("/", "-")
    app_bundle_path = output_dir / f"{safe_app_name}.app"
    contents_dir = app_bundle_path / "Contents"
    macos_dir = contents_dir / "MacOS"
    resources_dir = contents_dir / "Resources"
    info_plist_path = contents_dir / "Info.plist"
    launcher_script_path = macos_dir / "run.sh"

    hud_flag = "--hud" if enable_hud else "--no-hud"
    log_file = LOGS_DIR / f"{profile.slug}.log"

    run_sh_content = f"""#!/bin/zsh
set -euo pipefail
mkdir -p "{LOGS_DIR}"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
exec uv run --project "{PROJECT_ROOT}" m5runner launch "{profile.slug}" {hud_flag} >> "{log_file}" 2>&1
"""

    plist_dict = {
        "CFBundleName": profile.name,
        "CFBundleDisplayName": profile.name,
        "CFBundleIdentifier": f"com.danieldiaz.m5runner.{profile.slug}",
        "CFBundleExecutable": "run.sh",
        "CFBundleIconFile": "shortcut.icns",
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundlePackageType": "APPL",
        "CFBundleSignature": "????",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1.0.0",
        "LSMinimumSystemVersion": "15.0",
        "NSHighResolutionCapable": True,
    }

    if not dry_run:
        macos_dir.mkdir(parents=True, exist_ok=True)
        resources_dir.mkdir(parents=True, exist_ok=True)
        with info_plist_path.open("wb") as f:
            plistlib.dump(plist_dict, f)
        launcher_script_path.write_text(run_sh_content, encoding="utf-8")
        current_mode = launcher_script_path.stat().st_mode
        launcher_script_path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return app_bundle_path
