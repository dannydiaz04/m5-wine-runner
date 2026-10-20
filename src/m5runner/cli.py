"""Command-line interface for M5 Max Unified Wine / D3DMetal / DXMT Game Runner."""

from __future__ import annotations

import argparse
from pathlib import Path
import shlex
import subprocess
import sys

from m5runner.app_generator import create_macos_app_bundle
from m5runner.backends import (
    build_execution_environment,
    find_wine_binary,
    stage_backend_dlls_into_prefix,
)
from m5runner.bootstrap import (
    bootstrap_environment,
    download_game_via_steamcmd,
    import_gptk_d3dmetal,
    run_doctor,
    setup_or_launch_windows_steam,
)
from m5runner.config import APPLICATIONS_DIR, DEFAULT_PREFIX, SCRIPTS_DIR
from m5runner.patchers import run_profile_hooks
from m5runner.profiles import VALID_BACKENDS, load_profiles


def _cmd_list(args: argparse.Namespace) -> int:
    profiles = load_profiles()
    print(f"{'SLUG':<16} {'GAME':<38} {'BACKEND':<16} {'TIER'}")
    print("-" * 100)
    for slug, p in profiles.items():
        print(f"{slug:<16} {p.name:<38} {p.backend:<16} {p.tier}")
    return 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    report = run_doctor()
    print("=== M5 Max Translation Layer Doctor ===")
    for key, info in report.items():
        status = "[OK]  " if info["ok"] else "[WARN]"
        print(f"{status} {key:<14}: {info['detail']}")
    return 0


def _cmd_bootstrap(args: argparse.Namespace) -> int:
    gptk_path = Path(args.gptk_dmg).expanduser() if args.gptk_dmg else None
    steps = bootstrap_environment(
        install_xiv=args.with_xiv,
        gptk_source=gptk_path,
        dry_run=args.dry_run,
    )
    prefix = "[DRY-RUN] " if args.dry_run else ""
    for step in steps:
        print(f"{prefix}- {step}")
    return 0


def _cmd_import_gptk(args: argparse.Namespace) -> int:
    src = Path(args.source).expanduser()
    actions = import_gptk_d3dmetal(src, dry_run=args.dry_run)
    prefix = "[DRY-RUN] " if args.dry_run else ""
    for action in actions:
        print(f"{prefix}- {action}")
    return 0


def _cmd_build_moltenvk_rt(args: argparse.Namespace) -> int:
    script = SCRIPTS_DIR / "build-moltenvk-rt.sh"
    if args.dry_run:
        print(f"[DRY-RUN] Execute {script}")
        return 0
    return subprocess.call(["/bin/zsh", str(script)])


def _cmd_patch(args: argparse.Namespace) -> int:
    profiles = load_profiles()
    if args.game not in profiles:
        print(f"Unknown game slug '{args.game}'. Run 'm5runner list' to view valid slugs.", file=sys.stderr)
        return 1
    profile = profiles[args.game]
    game_dir = Path(args.game_dir).expanduser() if args.game_dir else None
    actions = run_profile_hooks(profile, game_dir=game_dir, dry_run=args.dry_run)
    prefix = "[DRY-RUN] " if args.dry_run else ""
    print(f"=== Patching {profile.name} ({profile.slug}) ===")
    for action in actions:
        print(f"{prefix}- {action}")
    return 0


def _cmd_launch(args: argparse.Namespace) -> int:
    profiles = load_profiles()
    if args.game not in profiles:
        print(f"Unknown game slug '{args.game}'. Run 'm5runner list' to view valid slugs.", file=sys.stderr)
        return 1
    profile = profiles[args.game]
    active_backend = args.backend or profile.backend
    enable_hud = not args.no_hud
    game_dir = Path(args.game_dir).expanduser() if args.game_dir else None

    # 1. Run pre-launch hooks
    hook_actions = run_profile_hooks(profile, game_dir=game_dir, dry_run=args.dry_run)
    dll_actions = stage_backend_dlls_into_prefix(
        profile,
        backend_override=active_backend,
        dry_run=args.dry_run,
    )

    # 2. Build execution environment
    env = build_execution_environment(
        profile,
        backend_override=active_backend,
        enable_hud=enable_hud,
    )

    # 3. Handle XIV on Mac native delegation
    if active_backend == "xivmac":
        cmd = ["open", "-a", "XIV on Mac"]
    else:
        wine_bin = find_wine_binary()
        target_exe = profile.resolve_executable(
            backend_override=active_backend,
            explicit_dir=game_dir,
        )
        cmd = [str(wine_bin), str(target_exe), *profile.launch_args, *args.extra_args]

    print(f"=== Launching {profile.name} [{active_backend}] ===")
    for act in hook_actions + dll_actions:
        print(f"  * {act}")

    exported_keys = (
        "WINEPREFIX",
        "WINEMSYNC",
        "ROSETTA_ADVERTISE_AVX",
        "D3DM_ENABLE_METALFX",
        "MTL_HUD_ENABLED",
        "WINEDLLOVERRIDES",
        "DYLD_FALLBACK_LIBRARY_PATH",
        "VK_ICD_FILENAMES",
    )
    print("\nEnvironment:")
    for k in exported_keys:
        if k in env:
            print(f'  export {k}="{env[k]}"')

    print(f"\nCommand:\n  {shlex.join(cmd)}")

    if args.dry_run:
        return 0

    try:
        return subprocess.call(cmd, env=env)
    finally:
        if "cleanup_jedi_survivor_ea_and_mem" in profile.hooks:
            wineserver = find_wine_binary().parent / "wineserver"
            if wineserver.exists():
                subprocess.run([str(wineserver), "-k"], env=env, check=False)


def _cmd_create_apps(args: argparse.Namespace) -> int:
    profiles = load_profiles()
    out_dir = Path(args.output_dir).expanduser() if args.output_dir else APPLICATIONS_DIR
    targets = list(profiles.values()) if args.all else [profiles[args.game]]

    prefix = "[DRY-RUN] " if args.dry_run else ""
    for profile in targets:
        app_path = create_macos_app_bundle(
            profile,
            output_dir=out_dir,
            enable_hud=not args.no_hud,
            dry_run=args.dry_run,
        )
        print(f"{prefix}Created {app_path}")
    return 0


def _cmd_steam(args: argparse.Namespace) -> int:
    actions = setup_or_launch_windows_steam(prefix_path=DEFAULT_PREFIX, dry_run=args.dry_run)
    prefix = "[DRY-RUN] " if args.dry_run else ""
    for act in actions:
        print(f"{prefix}- {act}")
    return 0


def _cmd_download(args: argparse.Namespace) -> int:
    profiles = load_profiles()
    if args.game not in profiles:
        print(f"Unknown game slug '{args.game}'. Run 'm5runner list' to view valid slugs.", file=sys.stderr)
        return 1
    profile = profiles[args.game]
    if not profile.steam_app_id:
        print(f"No Steam AppID configured for {profile.name}.", file=sys.stderr)
        return 1

    default_dir_name = profile.name.replace(":", "").strip()
    install_dir = (
        Path(args.install_dir).expanduser()
        if args.install_dir
        else (
            profile.prefix_path
            / "drive_c"
            / "Program Files (x86)"
            / "Steam"
            / "steamapps"
            / "common"
            / default_dir_name
        )
    )
    actions = download_game_via_steamcmd(
        app_id=profile.steam_app_id,
        game_name=profile.name,
        install_dir=install_dir,
        steam_user=args.user,
        dry_run=args.dry_run,
    )
    prefix = "[DRY-RUN] " if args.dry_run else ""
    for act in actions:
        print(f"{prefix}- {act}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="m5runner",
        description="Unified Wine / D3DMetal 4 / DXMT / MoltenVK-RT Runner for Apple M5 Max (128GB)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = sub.add_parser("list", help="List all 14 supported game profiles and optimal backends")
    p_list.set_defaults(func=_cmd_list)

    # doctor
    p_doc = sub.add_parser("doctor", help="Inspect M5 Max hardware, Rosetta 2, and SDK readiness")
    p_doc.set_defaults(func=_cmd_doctor)

    # bootstrap
    p_boot = sub.add_parser("bootstrap", help="Install Wine 11.x WoW64, winetricks, DXMT, and prefixes")
    p_boot.add_argument("--with-xiv", action="store_true", help="Also install XIV on Mac via Homebrew")
    p_boot.add_argument("--gptk-dmg", help="Optional path to Apple GPTK Evaluation Environment DMG")
    p_boot.add_argument("--dry-run", action="store_true", help="Print actions without modifying disk")
    p_boot.set_defaults(func=_cmd_bootstrap)

    # import-gptk
    p_gptk = sub.add_parser("import-gptk", help="Extract D3DMetal.framework from Apple GPTK DMG or folder")
    p_gptk.add_argument("source", help="Path to GPTK .dmg or extracted directory")
    p_gptk.add_argument("--dry-run", action="store_true", help="Preview extraction steps")
    p_gptk.set_defaults(func=_cmd_import_gptk)

    # build-moltenvk-rt
    p_mvk = sub.add_parser(
        "build-moltenvk-rt",
        help="Compile experimental MoltenVK Hardware Ray Tracing branch for DOOM: The Dark Ages",
    )
    p_mvk.add_argument("--dry-run", action="store_true", help="Print build command without running")
    p_mvk.set_defaults(func=_cmd_build_moltenvk_rt)

    # patch
    p_patch = sub.add_parser("patch", help="Run automated bypass/config/mod hooks for a game")
    p_patch.add_argument("game", help="Game slug (e.g., elden-ring, rdr2, mhwilds)")
    p_patch.add_argument("--game-dir", help="Explicit path to the game installation directory")
    p_patch.add_argument("--dry-run", action="store_true", help="Preview patches without writing files")
    p_patch.set_defaults(func=_cmd_patch)

    # launch
    p_launch = sub.add_parser("launch", help="Configure backend, run patches, and launch a game")
    p_launch.add_argument("game", help="Game slug (see 'm5runner list')")
    p_launch.add_argument("--backend", choices=sorted(VALID_BACKENDS), help="Override graphics backend")
    p_launch.add_argument("--game-dir", help="Explicit path to the game installation directory")
    p_launch.add_argument("--hud", action="store_true", default=True, help="Enable Metal HUD overlay")
    p_launch.add_argument("--no-hud", action="store_true", help="Disable Metal HUD overlay")
    p_launch.add_argument("--dry-run", action="store_true", help="Print environment and command without executing")
    p_launch.add_argument("extra_args", nargs="*", help="Extra arguments passed to the game binary")
    p_launch.set_defaults(func=_cmd_launch)

    # create-apps
    p_apps = sub.add_parser("create-apps", help="Generate macOS .app wrappers in ~/Applications")
    group = p_apps.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Generate .app bundles for all 14 games")
    group.add_argument("game", nargs="?", help="Single game slug to generate an .app bundle for")
    p_apps.add_argument("--output-dir", help="Target directory (defaults to ~/Applications)")
    p_apps.add_argument("--no-hud", action="store_true", help="Disable Metal HUD by default in .app wrapper")
    p_apps.add_argument("--dry-run", action="store_true", help="Preview .app bundle creation")
    p_apps.set_defaults(func=_cmd_create_apps)

    # steam
    p_steam = sub.add_parser("steam", help="Install or launch Windows Steam inside default_prefix")
    p_steam.add_argument("--dry-run", action="store_true", help="Preview Windows Steam setup/launch")
    p_steam.set_defaults(func=_cmd_steam)

    # download
    p_dl = sub.add_parser("download", help="Download a Windows game depot into the prefix via steamcmd")
    p_dl.add_argument("game", help="Game slug (e.g., sekiro, witcher3, elden-ring)")
    p_dl.add_argument("--user", required=True, help="Your Steam username")
    p_dl.add_argument("--install-dir", help="Optional custom target directory")
    p_dl.add_argument("--dry-run", action="store_true", help="Preview steamcmd download command")
    p_dl.set_defaults(func=_cmd_download)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
