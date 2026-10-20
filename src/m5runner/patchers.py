"""Automated per-game patchers, launcher bypasses, registry spoofs, and mod hooks."""

from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import urllib.request
import zipfile

from m5runner.config import (
    D3DMETAL_SDK_DIR,
    MODS_CACHE_DIR,
    MOLTENVK_RT_SDK_DIR,
)
from m5runner.profiles import GameProfile

RDR2_DEFAULT_SYSTEM_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rage__fwuiSystemSettingsCollection>
  <version value="37" />
  <configSource>kSettingsConfig_Auto</configSource>
  <graphics>
    <tessellation>kSettingLevel_High</tessellation>
    <shadowQuality>kSettingLevel_High</shadowQuality>
    <farShadowQuality>kSettingLevel_High</farShadowQuality>
    <reflectionQuality>kSettingLevel_High</reflectionQuality>
    <mirrorQuality>kSettingLevel_Ultra</mirrorQuality>
    <ssao>kSettingLevel_High</ssao>
    <textureQuality>kSettingLevel_Ultra</textureQuality>
    <particleQuality>kSettingLevel_Ultra</particleQuality>
    <waterQuality>kSettingLevel_High</waterQuality>
    <volumetricsQuality>kSettingLevel_High</volumetricsQuality>
    <lightingQuality>kSettingLevel_Ultra</lightingQuality>
    <ambientLightingQuality>kSettingLevel_High</ambientLightingQuality>
    <dlssIndex value="2" />
  </graphics>
  <advancedGraphics>
    <API>kSettingAPI_DX12</API>
    <locked value="false" />
    <asyncComputeEnabled value="false" />
    <transferQueuesEnabled value="true" />
  </advancedGraphics>
  <video>
    <adapterIndex value="0" />
    <outputIndex value="0" />
    <resolutionIndex value="0" />
    <screenWidth value="3840" />
    <screenHeight value="2160" />
    <refreshRateIndex value="0" />
    <refreshRateNumerator value="120" />
    <refreshRateDenominator value="1" />
    <windowed value="0" />
    <vSync value="0" />
    <tripleBuffered value="true" />
  </video>
</rage__fwuiSystemSettingsCollection>
"""

MGS_DELTA_GAME_USER_SETTINGS_INI = """[/Script/MGSDelta.MGSDeltaGameUserSettings]
bUseVSync=False
bUseDynamicResolution=False
ResolutionSizeX=3840
ResolutionSizeY=2160
LastUserConfirmedResolutionSizeX=3840
LastUserConfirmedResolutionSizeY=2160
WindowPosX=-1
WindowPosY=-1
FullscreenMode=1
LastConfirmedFullscreenMode=1
PreferredFullscreenMode=1
FrameRateLimit=60.000000
UpscalerType=DLSS
DLSSQuality=Quality
"""

MGS_DELTA_ENGINE_INI = """[SystemSettings]
r.D3D12.UseAllowTearing=1
r.ShaderPipelineCache.Enabled=1
r.ShaderPipelineCache.AsyncCompileRate=32
"""

NVIDIA_DLSS_REG_FILE = """Windows Registry Editor Version 5.00

[HKEY_LOCAL_MACHINE\\Software\\NVIDIA Corporation\\Global\\NGXCore]
"FullPath"="C:\\\\Windows\\\\System32"
"Installed"=dword:00000001

[HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\Video\\{00000001-0002-0003-0004-000000000005}\\0000]
"MatchingDeviceId"="pci\\\\ven_10de&dev_2684"
"DriverDesc"="NVIDIA GeForce RTX 4090 (Apple M5 Max D3DMetal MetalFX)"
"""

SEKIRO_INPUT_REG_FILE = """Windows Registry Editor Version 5.00

[HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Services\\winebus]
"DisableInput"=dword:00000000
"EnableHidraw"=dword:00000001
"EnableSDL"=dword:00000001
"MapControllers"=dword:00000001
"""

HORIZON_STEREO_REG_FILE = """Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\\Software\\Wine\\Drivers\\winecoreaudio.drv]
"DefaultChannelMask"=dword:00000003
"Speakers"=dword:00000002
"""


def _write_reg_file_to_prefix(
    prefix_path: Path,
    reg_filename: str,
    reg_contents: str,
    dry_run: bool = False,
) -> str:
    """Write a .reg file into the prefix drive_c/windows/temp folder for Wine regedit."""
    temp_dir = prefix_path / "drive_c" / "windows" / "temp"
    reg_path = temp_dir / reg_filename
    if not dry_run:
        temp_dir.mkdir(parents=True, exist_ok=True)
        reg_path.write_text(reg_contents, encoding="utf-8")
    return f"Prepared registry patch {reg_path}"


def bypass_eac_elden_ring(
    profile: GameProfile,
    game_dir: Path | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Automate Elden Ring Easy Anti-Cheat bypass and Seamless Co-op detection."""
    actions: list[str] = []
    target_dir = game_dir or profile.find_game_dir()
    if not target_dir:
        actions.append(
            "Elden Ring game directory not yet present on disk; EAC bypass will run automatically once installed."
        )
        return actions

    # Check both root and Game/ subdirectory
    game_sub = target_dir / "Game" if (target_dir / "Game").is_dir() else target_dir
    eac_exe = game_sub / "start_protected_game.exe"
    eac_bak = game_sub / "start_protected_game.exe.bak"
    main_exe = game_sub / "eldenring.exe"
    coop_exe = game_sub / "ersc_launcher.exe"
    appid_file = game_sub / "steam_appid.txt"

    actions.append(f"Write Steam AppID 1245620 -> {appid_file}")
    if not dry_run:
        game_sub.mkdir(parents=True, exist_ok=True)
        appid_file.write_text("1245620\n", encoding="utf-8")

    if eac_exe.exists() and not eac_bak.exists():
        actions.append(f"Backup EAC launcher: {eac_exe} -> {eac_bak}")
        if not dry_run:
            shutil.copy2(eac_exe, eac_bak)

    if main_exe.exists():
        actions.append(f"Replace {eac_exe.name} with offline {main_exe.name} binary")
        if not dry_run:
            shutil.copy2(main_exe, eac_exe)

    if coop_exe.exists():
        actions.append(f"Detected Seamless Co-op launcher ({coop_exe}); prioritizing multiplayer bypass.")

    return actions


def patch_rdr2_settings_and_launcher(
    profile: GameProfile,
    game_dir: Path | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Force <API>kSettingAPI_DX12</API> in RDR2 system.xml and kill zombie Rockstar processes."""
    actions: list[str] = []

    # 1. Kill any zombie SocialClubHelper.exe or LauncherPatcher.exe processes
    actions.append("Clean up zombie SocialClubHelper.exe / LauncherPatcher.exe processes")
    if not dry_run:
        subprocess.run(
            ["pkill", "-f", "SocialClubHelper\\.exe|LauncherPatcher\\.exe"],
            check=False,
            capture_output=True,
        )

    # 2. Locate or create Documents/Rockstar Games/Red Dead Redemption 2/Settings/system.xml
    users_dir = profile.prefix_path / "drive_c" / "users"
    user_candidates = ["steamuser", "crossover"]
    if users_dir.exists():
        for child in sorted(users_dir.iterdir()):
            if child.is_dir() and child.name not in ("Public", "All Users", "Default"):
                if child.name not in user_candidates:
                    user_candidates.insert(0, child.name)

    target_user = user_candidates[0]
    settings_dir = (
        users_dir
        / target_user
        / "Documents"
        / "Rockstar Games"
        / "Red Dead Redemption 2"
        / "Settings"
    )
    system_xml = settings_dir / "system.xml"

    if system_xml.exists():
        content = system_xml.read_text(encoding="utf-8", errors="ignore")
        if "<API>" in content:
            updated = re.sub(
                r"<API>\s*kSettingAPI_[A-Za-z0-9_]+\s*</API>",
                "<API>kSettingAPI_DX12</API>",
                content,
            )
        else:
            updated = content.replace(
                "</advancedGraphics>",
                "    <API>kSettingAPI_DX12</API>\n  </advancedGraphics>",
            )
        actions.append(f"Patch RDR2 graphics API to kSettingAPI_DX12 in {system_xml}")
        if not dry_run:
            system_xml.write_text(updated, encoding="utf-8")
    else:
        actions.append(f"Create default DX12 RDR2 system.xml at {system_xml}")
        if not dry_run:
            settings_dir.mkdir(parents=True, exist_ok=True)
            system_xml.write_text(RDR2_DEFAULT_SYSTEM_XML, encoding="utf-8")

    return actions


def inject_reframework_mhwilds(
    profile: GameProfile,
    game_dir: Path | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Download and inject REFramework (dinput8.dll) into Monster Hunter Wilds."""
    actions: list[str] = []
    cache_dir = MODS_CACHE_DIR / "mhwilds"
    cached_dll = cache_dir / "dinput8.dll"

    if not cached_dll.exists():
        actions.append(
            f"Fetch latest REFramework (MHWILDS.zip -> dinput8.dll) into {cached_dll}"
        )
        if not dry_run:
            cache_dir.mkdir(parents=True, exist_ok=True)
            _download_reframework_dinput8(cached_dll)

    target_dir = game_dir or profile.find_game_dir()
    if target_dir:
        dst_dll = target_dir / "dinput8.dll"
        actions.append(f"Inject REFramework dinput8.dll -> {dst_dll}")
        if not dry_run and cached_dll.exists():
            shutil.copy2(cached_dll, dst_dll)
    else:
        actions.append(
            f"Staged REFramework dinput8.dll in {cached_dll} (will copy into Monster Hunter Wilds folder on install)"
        )

    return actions


def _download_reframework_dinput8(dest_dll: Path) -> bool:
    """Download MHWILDS.zip from praydog/REFramework-nightly or praydog/REFramework."""
    urls = [
        "https://github.com/praydog/REFramework-nightly/releases/latest/download/MHWILDS.zip",
        "https://api.github.com/repos/praydog/REFramework/releases/latest",
    ]
    zip_path = dest_dll.parent / "MHWILDS.zip"
    try:
        req = urllib.request.Request(
            urls[0],
            headers={"User-Agent": "m5-wine-runner/0.1.0"},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            zip_path.write_bytes(resp.read())
        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.namelist():
                if member.lower().endswith("dinput8.dll"):
                    dest_dll.write_bytes(zf.read(member))
                    return True
    except Exception:
        return False
    return False


def stub_pspcsdk_gow_ragnarok(
    profile: GameProfile,
    game_dir: Path | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Configure AVX advertisement and PlayStation PC SDK bypass/installer for God of War Ragnarok."""
    actions: list[str] = [
        "Enforce ROSETTA_ADVERTISE_AVX=1 for F16C/AVX2 boot instructions",
    ]
    target_dir = game_dir or profile.find_game_dir()
    if target_dir:
        msi_installer = target_dir / "PsPcSdkRuntimeInstaller.msi"
        if msi_installer.exists():
            actions.append(
                f"Detected {msi_installer.name}; queuing silent msiexec /i installation in prefix"
            )
    actions.append("Configure WINEDLLOVERRIDES PsPcSdk=n,b to prevent Sony overlay deadlock")
    return actions


def seed_mgs_delta_config(
    profile: GameProfile,
    game_dir: Path | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Pre-populate Saved/Config/Windows INI files for Metal Gear Solid Delta: Snake Eater."""
    actions: list[str] = []
    local_appdata_cfg = (
        profile.prefix_path
        / "drive_c"
        / "users"
        / "steamuser"
        / "AppData"
        / "Local"
        / "MGSDelta"
        / "Saved"
        / "Config"
        / "Windows"
    )
    game_user_ini = local_appdata_cfg / "GameUserSettings.ini"
    engine_ini = local_appdata_cfg / "Engine.ini"

    actions.append(f"Seed UE5 GameUserSettings.ini & Engine.ini in {local_appdata_cfg}")
    if not dry_run:
        local_appdata_cfg.mkdir(parents=True, exist_ok=True)
        if not game_user_ini.exists():
            game_user_ini.write_text(MGS_DELTA_GAME_USER_SETTINGS_INI, encoding="utf-8")
        if not engine_ini.exists():
            engine_ini.write_text(MGS_DELTA_ENGINE_INI, encoding="utf-8")

    if game_dir:
        in_game_cfg = game_dir / "MGSDelta" / "Saved" / "Config" / "Windows"
        actions.append(f"Seed UE5 Saved/Config/Windows in game directory: {in_game_cfg}")
        if not dry_run:
            in_game_cfg.mkdir(parents=True, exist_ok=True)
            (in_game_cfg / "GameUserSettings.ini").write_text(
                MGS_DELTA_GAME_USER_SETTINGS_INI,
                encoding="utf-8",
            )
            (in_game_cfg / "Engine.ini").write_text(
                MGS_DELTA_ENGINE_INI,
                encoding="utf-8",
            )

    return actions


def enforce_horizon_stereo_and_gptk4(
    profile: GameProfile,
    game_dir: Path | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Enforce GPTK 4 D3DMetal and stereo audio output for Horizon Forbidden West."""
    actions: list[str] = []
    d3dm_plist = (
        D3DMETAL_SDK_DIR
        / "D3DMetal.framework"
        / "Versions"
        / "A"
        / "Resources"
        / "Info.plist"
    )
    if d3dm_plist.exists():
        actions.append(f"Verified D3DMetal framework bundle at {d3dm_plist}")
    else:
        actions.append(
            "Reminder: Run 'm5runner import-gptk <GPTK4.dmg>' to populate ~/Games/sdk/d3dmetal with GPTK 4.0+ DLLs"
        )

    reg_msg = _write_reg_file_to_prefix(
        profile.prefix_path,
        "horizon_stereo.reg",
        HORIZON_STEREO_REG_FILE,
        dry_run=dry_run,
    )
    actions.append(f"{reg_msg} (Forces Stereo 2.0 layout so Decima dialogue audio is never muted)")
    actions.append(
        "Note: Initial Decima shader compilation displays a black screen for 2-4 minutes on first boot."
    )
    return actions


def cleanup_jedi_survivor_ea_and_mem(
    profile: GameProfile,
    game_dir: Path | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Kill corrupted EA Background Service processes before launching Star Wars Jedi: Survivor."""
    actions = [
        "Terminate stale EABackgroundService.exe / EADesktop.exe processes before launch",
        "Register post-exit wineserver -k cleanup hook to reclaim D3DMetal memory pages on exit",
    ]
    if not dry_run:
        subprocess.run(
            ["pkill", "-f", "EABackgroundService\\.exe|EADesktop\\.exe"],
            check=False,
            capture_output=True,
        )
    return actions


def prepare_dmc4_wmv_codecs(
    profile: GameProfile,
    game_dir: Path | None = None,
    dry_run: bool = False,
    disable_wmv_cutscenes: bool = False,
) -> list[str]:
    """Configure WoW64 WMV/Quartz overrides and optional WMV logo bypass for Devil May Cry 4."""
    actions = [
        f"Target WoW64 prefix: {profile.prefix_path} (winetricks: wmp11, quartz, devenum)",
    ]
    target_dir = game_dir or profile.find_game_dir()
    if target_dir and disable_wmv_cutscenes:
        movie_dir = target_dir / "nativeDX10" / "movie"
        if not movie_dir.exists():
            movie_dir = target_dir / "nativePC" / "movie"
        if movie_dir.exists():
            for wmv in sorted(movie_dir.glob("*.wmv")):
                bak = wmv.with_suffix(".wmv.bak")
                actions.append(f"Bypass legacy WMV cutscene: {wmv.name} -> {bak.name}")
                if not dry_run and not bak.exists():
                    wmv.rename(bak)
    return actions


def configure_sekiro_input(
    profile: GameProfile,
    game_dir: Path | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Configure XInput/Hidraw registry settings for Sekiro wireless controllers."""
    reg_msg = _write_reg_file_to_prefix(
        profile.prefix_path,
        "sekiro_input.reg",
        SEKIRO_INPUT_REG_FILE,
        dry_run=dry_run,
    )
    return [
        reg_msg,
        "Configured WINEDLLOVERRIDES xinput1_3,dinput8=n,b for controller ordering",
    ]


def select_witcher3_binary(
    profile: GameProfile,
    game_dir: Path | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Verify Witcher 3 --launcher-skip and DX11/DX12 executable routing."""
    return [
        "Bypass REDlauncher CEF hang via --launcher-skip",
        "Route DX12 (bin/x64_dx12/witcher3.exe) -> D3DMetal or DX11 (bin/x64/witcher3.exe) -> DXMT",
    ]


def spoof_nvidia_dlss_registry(
    profile: GameProfile,
    game_dir: Path | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Write NVIDIA RTX 4090 PCI ID & NGX registry keys so DLSS/FrameGen menus unlock for MetalFX."""
    reg_msg = _write_reg_file_to_prefix(
        profile.prefix_path,
        "nvidia_dlss_spoof.reg",
        NVIDIA_DLSS_REG_FILE,
        dry_run=dry_run,
    )
    return [
        f"{reg_msg} (Unlocks in-game DLSS & Frame Generation menus hooked into D3DM_ENABLE_METALFX=1)"
    ]


def ensure_gstreamer_codecs(
    profile: GameProfile,
    game_dir: Path | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Enable Hardware VideoToolbox decoding in Wine GStreamer for RE Engine cutscenes."""
    return [
        "Set GST_PLUGIN_FEATURE_RANK=vtdec:MAX to prevent RE Engine cutscene black screens"
    ]


def verify_moltenvk_rt(
    profile: GameProfile,
    game_dir: Path | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Verify custom MoltenVK with Hardware Ray Tracing for DOOM: The Dark Ages."""
    dylib = MOLTENVK_RT_SDK_DIR / "libMoltenVK.dylib"
    icd_json = MOLTENVK_RT_SDK_DIR / "MoltenVK_icd.json"
    actions: list[str] = []

    if not icd_json.exists() and not dry_run:
        MOLTENVK_RT_SDK_DIR.mkdir(parents=True, exist_ok=True)
        icd_payload = {
            "file_format_version": "1.0.0",
            "ICD": {
                "library_path": str(dylib),
                "api_version": "1.3.296",
                "is_portability_driver": True,
            },
        }
        icd_json.write_text(json.dumps(icd_payload, indent=2) + "\n", encoding="utf-8")

    if dylib.exists():
        actions.append(f"Verified experimental Ray Tracing MoltenVK dylib: {dylib}")
    else:
        actions.append(
            "Custom MoltenVK-RT not yet compiled. Run 'm5runner build-moltenvk-rt' to compile PR #2771 via Xcode."
        )
    return actions


def launch_xiv_on_mac(
    profile: GameProfile,
    game_dir: Path | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Check for XIV on Mac.app installation."""
    xiv_app = Path("/Applications/XIV on Mac.app")
    user_xiv_app = Path.home() / "Applications" / "XIV on Mac.app"
    if xiv_app.exists() or user_xiv_app.exists():
        return ["Verified XIV on Mac.app installation (native Swift + DXMT runtime)"]
    return ["XIV on Mac.app not yet installed; run 'm5runner bootstrap --with-xiv' to install via Homebrew"]


HOOK_REGISTRY = {
    "bypass_eac_elden_ring": bypass_eac_elden_ring,
    "patch_rdr2_settings_and_launcher": patch_rdr2_settings_and_launcher,
    "inject_reframework_mhwilds": inject_reframework_mhwilds,
    "stub_pspcsdk_gow_ragnarok": stub_pspcsdk_gow_ragnarok,
    "seed_mgs_delta_config": seed_mgs_delta_config,
    "enforce_horizon_stereo_and_gptk4": enforce_horizon_stereo_and_gptk4,
    "cleanup_jedi_survivor_ea_and_mem": cleanup_jedi_survivor_ea_and_mem,
    "prepare_dmc4_wmv_codecs": prepare_dmc4_wmv_codecs,
    "configure_sekiro_input": configure_sekiro_input,
    "select_witcher3_binary": select_witcher3_binary,
    "spoof_nvidia_dlss_registry": spoof_nvidia_dlss_registry,
    "ensure_gstreamer_codecs": ensure_gstreamer_codecs,
    "verify_moltenvk_rt": verify_moltenvk_rt,
    "launch_xiv_on_mac": launch_xiv_on_mac,
}


def run_profile_hooks(
    profile: GameProfile,
    game_dir: Path | None = None,
    dry_run: bool = False,
) -> list[str]:
    """Execute all registered pre-launch hooks for a given game profile."""
    results: list[str] = []
    for hook_name in profile.hooks:
        fn = HOOK_REGISTRY.get(hook_name)
        if not fn:
            results.append(f"Unknown hook: {hook_name}")
            continue
        results.extend(fn(profile, game_dir=game_dir, dry_run=dry_run))
    return results
