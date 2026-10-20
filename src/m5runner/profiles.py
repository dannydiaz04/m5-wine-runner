"""Game profile loading, validation, and installation path discovery."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import tomllib

from m5runner.config import (
    PREFIXES_DIR,
    PROFILES_PATH,
    STEAM_COMMON_DIR,
)

VALID_BACKENDS = {"d3dmetal", "d3dmetal_gptk4", "dxmt", "moltenvk_rt", "xivmac"}


@dataclass
class GameProfile:
    slug: str
    name: str
    tier: str
    engine: str
    backend: str
    alt_backends: list[str] = field(default_factory=list)
    prefix: str = "default_prefix"
    steam_app_id: int | None = None
    exe_rel_paths: list[str] = field(default_factory=list)
    dx11_exe_rel_path: str | None = None
    dx12_exe_rel_path: str | None = None
    launch_args: list[str] = field(default_factory=list)
    winetricks: list[str] = field(default_factory=list)
    dlss_metalfx: bool = False
    require_avx: bool = False
    dll_overrides: dict[str, str] = field(default_factory=dict)
    env: dict[str, str] = field(default_factory=dict)
    hooks: list[str] = field(default_factory=list)
    notes: str = ""

    @property
    def prefix_path(self) -> Path:
        return PREFIXES_DIR / self.prefix

    def candidate_install_dirs(self) -> list[Path]:
        """Return candidate directories where the game may be installed."""
        candidates: list[Path] = []
        pfx_steam = (
            self.prefix_path
            / "drive_c"
            / "Program Files (x86)"
            / "Steam"
            / "steamapps"
            / "common"
        )
        for root in (
            pfx_steam,
            STEAM_COMMON_DIR,
            self.prefix_path / "drive_c" / "Games",
            Path.home() / "Games" / "installs",
        ):
            if not root.exists():
                continue
            for child in sorted(root.iterdir()):
                if child.is_dir():
                    candidates.append(child)
        return candidates

    def find_game_dir(self, explicit_dir: Path | None = None) -> Path | None:
        """Locate the game root directory by checking candidate paths for known executables."""
        if explicit_dir and explicit_dir.exists():
            return explicit_dir
        for candidate in self.candidate_install_dirs():
            for rel_exe in self.exe_rel_paths:
                if (candidate / rel_exe).exists():
                    return candidate
        return None

    def resolve_executable(
        self,
        backend_override: str | None = None,
        explicit_dir: Path | None = None,
    ) -> Path:
        """Resolve the target Windows executable path for the chosen backend."""
        active_backend = backend_override or self.backend
        game_dir = self.find_game_dir(explicit_dir)

        # Special dual-executable handling for The Witcher 3 (DX11 via DXMT vs DX12 via D3DMetal)
        if active_backend == "dxmt" and self.dx11_exe_rel_path:
            rel_target = self.dx11_exe_rel_path
        elif active_backend in ("d3dmetal", "d3dmetal_gptk4") and self.dx12_exe_rel_path:
            rel_target = self.dx12_exe_rel_path
        else:
            rel_target = self.exe_rel_paths[0] if self.exe_rel_paths else f"{self.slug}.exe"

        if game_dir:
            for candidate_rel in ([rel_target] + self.exe_rel_paths):
                full_path = game_dir / candidate_rel
                if full_path.exists():
                    return full_path
            return game_dir / rel_target

        # Fallback canonical path inside the Wine prefix Steam folder
        default_dir_name = self.name.replace(":", "").strip()
        return (
            self.prefix_path
            / "drive_c"
            / "Program Files (x86)"
            / "Steam"
            / "steamapps"
            / "common"
            / default_dir_name
            / rel_target
        )


def load_profiles(profiles_file: Path = PROFILES_PATH) -> dict[str, GameProfile]:
    """Parse profiles/games.toml and validate all game definitions."""
    with profiles_file.open("rb") as f:
        raw = tomllib.load(f)

    games_raw = raw.get("games", {})
    profiles: dict[str, GameProfile] = {}

    for slug, data in games_raw.items():
        backend = data["backend"]
        if backend not in VALID_BACKENDS:
            raise ValueError(f"Invalid backend '{backend}' for game '{slug}'")

        profiles[slug] = GameProfile(
            slug=slug,
            name=data["name"],
            tier=data["tier"],
            engine=data["engine"],
            backend=backend,
            alt_backends=list(data.get("alt_backends", [])),
            prefix=data.get("prefix", "default_prefix"),
            steam_app_id=data.get("steam_app_id"),
            exe_rel_paths=list(data.get("exe_rel_paths", [])),
            dx11_exe_rel_path=data.get("dx11_exe_rel_path"),
            dx12_exe_rel_path=data.get("dx12_exe_rel_path"),
            launch_args=list(data.get("launch_args", [])),
            winetricks=list(data.get("winetricks", [])),
            dlss_metalfx=bool(data.get("dlss_metalfx", False)),
            require_avx=bool(data.get("require_avx", False)),
            dll_overrides=dict(data.get("dll_overrides", {})),
            env={k: str(v) for k, v in data.get("env", {}).items()},
            hooks=list(data.get("hooks", [])),
            notes=data.get("notes", ""),
        )

    return profiles
