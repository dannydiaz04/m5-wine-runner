"""Core paths, hardware constants, and base environment variables for M5 Max."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROFILES_PATH = PROJECT_ROOT / "profiles" / "games.toml"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

BASE_GAMES_DIR = Path(os.environ.get("M5RUNNER_GAMES_DIR", Path.home() / "Games"))
PREFIXES_DIR = BASE_GAMES_DIR / "prefixes"
DEFAULT_PREFIX = PREFIXES_DIR / "default_prefix"
LEGACY_WOW64_PREFIX = PREFIXES_DIR / "legacy_wow64"

SDK_DIR = BASE_GAMES_DIR / "sdk"
WINE_SDK_DIR = SDK_DIR / "wine"
D3DMETAL_SDK_DIR = SDK_DIR / "d3dmetal"
DXMT_SDK_DIR = SDK_DIR / "dxmt"
MOLTENVK_RT_SDK_DIR = SDK_DIR / "moltenvk-rt"

MODS_CACHE_DIR = BASE_GAMES_DIR / "mods_cache"
LOGS_DIR = BASE_GAMES_DIR / "logs"

APPLICATIONS_DIR = Path(os.environ.get("M5RUNNER_APPS_DIR", Path.home() / "Applications"))
STEAM_COMMON_DIR = (
    Path.home()
    / "Library"
    / "Application Support"
    / "Steam"
    / "steamapps"
    / "common"
)

# Base Environment Variables for M5 Max (128GB Unified Memory)
DEFAULT_M5_ENV: dict[str, str] = {
    "WINEMSYNC": "1",                   # Critical for multi-core CPU scaling on M5 Max
    "WINEESYNC": "0",                   # Prefer Mach semaphore msync over esync on macOS
    "ROSETTA_ADVERTISE_AVX": "1",       # Exposes AVX/AVX2/F16C via Rosetta 2
    "D3DM_ENABLE_METALFX": "1",         # Hooks DLSS calls into Apple MetalFX
    "MTL_HUD_ENABLED": "1",             # Metal performance/FPS overlay (can be toggled with --no-hud)
    "WINEDEBUG": "-all",                # Suppress verbose Wine console spam for max CPU throughput
}


def ensure_runtime_dirs() -> None:
    """Create the ~/Games directory hierarchy if it does not exist."""
    for directory in (
        BASE_GAMES_DIR,
        PREFIXES_DIR,
        DEFAULT_PREFIX,
        LEGACY_WOW64_PREFIX,
        SDK_DIR,
        WINE_SDK_DIR,
        D3DMETAL_SDK_DIR,
        DXMT_SDK_DIR,
        MOLTENVK_RT_SDK_DIR,
        MODS_CACHE_DIR,
        LOGS_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)
