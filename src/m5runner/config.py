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
GPTK_PREFIX = PREFIXES_DIR / "gptk_prefix"
LEGACY_WOW64_PREFIX = PREFIXES_DIR / "legacy_wow64"

SDK_DIR = BASE_GAMES_DIR / "sdk"

# One Wine runtime per backend family. D3DMetal only runs inside Apple's patched GPTK Wine,
# while DXMT needs the newer unix-call ABI (`__wine_unix_call_dispatcher`) that GPTK Wine 7.7
# lacks, so the two can never share a runtime. A prefix is only ever run by one runtime.
GPTK_WINE_DIR = SDK_DIR / "wine-gptk"        # Gcenx game-porting-toolkit (Wine 7.7 + bundled D3DMetal 3)
STAGING_WINE_DIR = SDK_DIR / "wine-staging"  # Gcenx Wine Staging 11.x (DXMT / MoltenVK)
GPTK_WINE_VERSION = "3.0-3"
GPTK_WINE_SHA256 = "d377683937340f914823dbb2e1252b329cbf834ff58907d0293db8cebf0e392e"

BACKEND_RUNTIME: dict[str, str] = {
    "d3dmetal": "gptk",
    "d3dmetal_gptk4": "gptk",
    "dxmt": "staging",
    "moltenvk_rt": "staging",
    "xivmac": "staging",
}
RUNTIME_DIRS: dict[str, Path] = {"gptk": GPTK_WINE_DIR, "staging": STAGING_WINE_DIR}
RUNTIME_PREFIXES: dict[str, str] = {"gptk": GPTK_PREFIX.name, "staging": DEFAULT_PREFIX.name}  # names under PREFIXES_DIR
RUNTIME_ENV: dict[str, dict[str, str]] = {
    "gptk": {"WINEESYNC": "1"},  # GPTK Wine 7.7 implements esync only (no msync)
    "staging": {},
}

# Apple's GPTK evaluation environment as imported from a DMG. Kept for reference/CrossOver use:
# the 4.0 betas need a newer Wine than the GPTK cask ships, so the runner does not stage them.
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

# Base Environment Variables for M5 Max (128GB Unified Memory); runtime-specific sync flags
# come from RUNTIME_ENV.
DEFAULT_M5_ENV: dict[str, str] = {
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
        SDK_DIR,
        D3DMETAL_SDK_DIR,
        DXMT_SDK_DIR,
        MOLTENVK_RT_SDK_DIR,
        MODS_CACHE_DIR,
        LOGS_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)
