"""Automated unit and integration tests for m5-wine-runner."""

from __future__ import annotations

from pathlib import Path
import plistlib

from m5runner.app_generator import create_macos_app_bundle
from m5runner.backends import (
    build_execution_environment,
    format_winedlloverrides,
)
from m5runner.cli import main
from m5runner.patchers import (
    bypass_eac_elden_ring,
    patch_rdr2_settings_and_launcher,
    seed_mgs_delta_config,
)
from m5runner.profiles import load_profiles


EXPECTED_14_SLUGS = {
    "ffxiv",
    "sekiro",
    "pragmata",
    "witcher3",
    "elden-ring",
    "stellar-blade",
    "gow-ragnarok",
    "horizon-fw",
    "mgs-delta",
    "rdr2",
    "jedi-survivor",
    "dmc4",
    "mhwilds",
    "doom-dark-ages",
}


def test_all_14_profiles_load_cleanly() -> None:
    profiles = load_profiles()
    assert set(profiles.keys()) == EXPECTED_14_SLUGS
    assert profiles["ffxiv"].backend == "xivmac"
    assert profiles["sekiro"].backend == "dxmt"
    assert profiles["horizon-fw"].backend == "d3dmetal_gptk4"
    assert profiles["mhwilds"].backend == "d3dmetal_gptk4"
    assert profiles["doom-dark-ages"].backend == "moltenvk_rt"
    assert profiles["dmc4"].prefix == "legacy_wow64"


def test_format_winedlloverrides() -> None:
    overrides = {"d3d11": "n,b", "d3d12": "n,b", "dxgi": "n,b"}
    assert format_winedlloverrides(overrides) == "d3d11,d3d12,dxgi=n,b"


def test_build_execution_environment_m5_defaults() -> None:
    profiles = load_profiles()
    witcher = profiles["witcher3"]

    env_dx12 = build_execution_environment(witcher, backend_override="d3dmetal", enable_hud=True, base_env={})
    assert env_dx12["WINEMSYNC"] == "1"
    assert env_dx12["ROSETTA_ADVERTISE_AVX"] == "1"
    assert env_dx12["D3DM_ENABLE_METALFX"] == "1"
    assert env_dx12["MTL_HUD_ENABLED"] == "1"
    assert "d3d11,d3d12,dxgi" in env_dx12["WINEDLLOVERRIDES"]
    assert env_dx12["M5RUNNER_ACTIVE_BACKEND"] == "d3dmetal"

    env_dx11 = build_execution_environment(witcher, backend_override="dxmt", enable_hud=False, base_env={})
    assert env_dx11["MTL_HUD_ENABLED"] == "0"
    assert env_dx11["M5RUNNER_ACTIVE_BACKEND"] == "dxmt"
    assert "d3d10core" in env_dx11["WINEDLLOVERRIDES"]


def test_witcher3_dual_executable_resolution(tmp_path: Path) -> None:
    profiles = load_profiles()
    witcher = profiles["witcher3"]

    dx11_exe = tmp_path / "bin" / "x64" / "witcher3.exe"
    dx12_exe = tmp_path / "bin" / "x64_dx12" / "witcher3.exe"
    dx11_exe.parent.mkdir(parents=True)
    dx12_exe.parent.mkdir(parents=True)
    dx11_exe.write_text("dx11", encoding="utf-8")
    dx12_exe.write_text("dx12", encoding="utf-8")

    assert witcher.resolve_executable(backend_override="d3dmetal", explicit_dir=tmp_path) == dx12_exe
    assert witcher.resolve_executable(backend_override="dxmt", explicit_dir=tmp_path) == dx11_exe
    assert "--launcher-skip" in witcher.launch_args


def test_elden_ring_eac_bypass_patcher(tmp_path: Path) -> None:
    profiles = load_profiles()
    er = profiles["elden-ring"]

    game_sub = tmp_path / "Game"
    game_sub.mkdir(parents=True)
    eac_exe = game_sub / "start_protected_game.exe"
    main_exe = game_sub / "eldenring.exe"
    eac_exe.write_text("original_eac_binary", encoding="utf-8")
    main_exe.write_text("real_eldenring_binary", encoding="utf-8")

    actions = bypass_eac_elden_ring(er, game_dir=tmp_path, dry_run=False)
    assert any("Backup EAC launcher" in a for a in actions)
    assert (game_sub / "start_protected_game.exe.bak").read_text(encoding="utf-8") == "original_eac_binary"
    assert (game_sub / "start_protected_game.exe").read_text(encoding="utf-8") == "real_eldenring_binary"
    assert (game_sub / "steam_appid.txt").read_text(encoding="utf-8").strip() == "1245620"


def test_rdr2_system_xml_vulkan_to_dx12_patcher(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("m5runner.profiles.PREFIXES_DIR", tmp_path)
    profiles = load_profiles()
    rdr2 = profiles["rdr2"]

    settings_dir = (
        rdr2.prefix_path
        / "drive_c"
        / "users"
        / "steamuser"
        / "Documents"
        / "Rockstar Games"
        / "Red Dead Redemption 2"
        / "Settings"
    )
    settings_dir.mkdir(parents=True)
    sys_xml = settings_dir / "system.xml"
    sys_xml.write_text(
        "<rage><advancedGraphics><API>kSettingAPI_Vulkan</API></advancedGraphics></rage>",
        encoding="utf-8",
    )

    patch_rdr2_settings_and_launcher(rdr2, dry_run=False)
    updated = sys_xml.read_text(encoding="utf-8")
    assert "<API>kSettingAPI_DX12</API>" in updated
    assert "kSettingAPI_Vulkan" not in updated


def test_mgs_delta_config_seeding(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("m5runner.profiles.PREFIXES_DIR", tmp_path)
    profiles = load_profiles()
    mgs = profiles["mgs-delta"]

    game_dir = tmp_path / "MGSDeltaInstall"
    seed_mgs_delta_config(mgs, game_dir=game_dir, dry_run=False)

    in_game_ini = game_dir / "MGSDelta" / "Saved" / "Config" / "Windows" / "GameUserSettings.ini"
    assert in_game_ini.exists()
    assert "UpscalerType=DLSS" in in_game_ini.read_text(encoding="utf-8")


def test_create_macos_app_bundle(tmp_path: Path) -> None:
    profiles = load_profiles()
    sekiro = profiles["sekiro"]

    app_path = create_macos_app_bundle(sekiro, output_dir=tmp_path, enable_hud=True, dry_run=False)
    info_plist = app_path / "Contents" / "Info.plist"
    run_sh = app_path / "Contents" / "MacOS" / "run.sh"

    assert info_plist.exists()
    assert run_sh.exists()
    with info_plist.open("rb") as f:
        plist_data = plistlib.load(f)
    assert plist_data["CFBundleExecutable"] == "run.sh"
    assert "sekiro" in run_sh.read_text(encoding="utf-8")


def test_cli_dry_run_commands() -> None:
    assert main(["list"]) == 0
    assert main(["doctor"]) == 0
    assert main(["launch", "witcher3", "--dry-run"]) == 0
    assert main(["launch", "mhwilds", "--dry-run"]) == 0
    assert main(["launch", "doom-dark-ages", "--dry-run"]) == 0
