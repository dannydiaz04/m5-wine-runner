# AGENTS.md — Operational & Porting Playbook for Humans and AI Agents

This document is the authoritative guide for both human engineers and AI coding agents (Antigravity, Claude Code, Cursor, Codex) working in **`m5-wine-runner`**. Follow these instructions to install, launch, troubleshoot, and port Windows PC games onto **Apple Silicon (M5 Max with 128GB Unified Memory, macOS 26+ Tahoe)**.

---

## 1. System Architecture & Directory Map

`m5-wine-runner` separates declarative runner logic (tracked in Git) from heavy binary translation SDKs and Wine prefixes (stored in `~/Games`):

```text
~/projects/m5-wine-runner/          # Git repository (Code, Profiles, Patchers, Tests)
├── AGENTS.md                       # Agent & developer operational playbook (this file)
├── README.md                       # Quick-start overview & 14-game matrix
├── docs/
│   └── PORTING_GUIDE.md            # Deep-dive engineering guide for porting new games
├── profiles/
│   └── games.toml                  # Declarative registry of all supported games
├── scripts/
│   └── build-moltenvk-rt.sh        # Xcode builder for experimental MoltenVK Ray Tracing
├── src/m5runner/
│   ├── config.py                   # Paths & M5 Max base environment variables
│   ├── profiles.py                 # TOML parser, GameProfile model, binary discovery
│   ├── backends.py                 # D3DMetal 4 / DXMT / MoltenVK-RT / XIVMac router
│   ├── patchers.py                 # Idempotent per-game bypasses, XML/INI & registry hooks
│   ├── bootstrap.py                # Doctor, Wine/DXMT/Steam installer, nested GPTK DMG extractor
│   ├── app_generator.py            # macOS ~/Applications/<Game>.app bundle generator
│   └── cli.py                      # `m5runner` CLI entry point
└── tests/
    └── test_runner.py              # Automated pytest verification suite

~/Games/                            # Local runtime root (untracked, managed by `m5runner`)
├── prefixes/
│   ├── default_prefix/             # 64-bit Windows 11 prefix (DX11 / DX12 / Vulkan titles)
│   └── legacy_wow64/               # 32-bit/64-bit WoW64 prefix (DMC4 / legacy WMV titles)
├── sdk/
│   ├── wine/                       # Gcenx Wine Staging 11.x (WoW64 + Mach msync)
│   ├── d3dmetal/                   # Apple Game Porting Toolkit 4.0+ (D3DMetal.framework + MetalFX)
│   ├── dxmt/                       # 3Shain/dxmt v0.80+ (Native DirectX 10/11 -> Metal)
│   └── moltenvk-rt/                # Isolated custom libMoltenVK.dylib with HW Ray Tracing
├── mods_cache/                     # Downloaded mod/bypass payloads (e.g., REFramework dinput8.dll)
└── logs/                           # Per-game execution logs (<slug>.log)
```

---

## 2. Standard Workflow: Provisioning, Downloading, & Launching Games

### Step 1: Verify Environment Health (`doctor`)
Always run `m5runner doctor` first to verify hardware, Rosetta 2, Wine, Winetricks, DXMT, and D3DMetal status:
```bash
m5runner doctor
```

### Step 2: Bootstrap or Repair Runtime SDKs (`bootstrap` & `import-gptk`)
If `wine`, `winetricks`, or `dxmt` show `[WARN]`:
```bash
m5runner bootstrap
```
If `d3dmetal` shows `[WARN]`, import Apple's Game Porting Toolkit 4.0+ DMG (supports both outer `Game_Porting_Toolkit_*.dmg` with a nested Evaluation Environment DMG and direct `Evaluation environment*.dmg` files):
```bash
m5runner import-gptk ~/Downloads/Game_Porting_Toolkit_4.0_beta_3.dmg
```

### Step 3: Download & Install a Game (`download` or `steam`)
Because macOS Steam cannot download Windows-only depots natively, use either:

1. **Automated CLI Download via `steamcmd` (Preferred for automation)**:
   ```bash
   m5runner download <game-slug> --user <steam_username>
   ```
   - Forces `+sSteamCmdForcePlatformType windows`.
   - Installs directly into `~/Games/prefixes/<prefix>/drive_c/Program Files (x86)/Steam/steamapps/common/<Game Name>`.
2. **Windows Steam Client GUI inside the Prefix**:
   ```bash
   m5runner steam
   ```
   - Installs `SteamSetup.exe` if missing, or launches `steam.exe` with `-cef-disable-gpu-compositing -no-cef-sandbox` so Steam's Chromium UI never black-screens under Wine.

### Step 4: Patch & Launch (`patch`, `launch`, `create-apps`)
```bash
# 1. Dry-run to inspect all hooks, DLL overrides, and environment variables:
m5runner launch <game-slug> --dry-run

# 2. Launch the game with the Metal performance HUD enabled:
m5runner launch <game-slug> --hud

# 3. Override the graphics backend on the fly (e.g. DXMT vs D3DMetal):
m5runner launch witcher3 --backend dxmt --hud

# 4. Generate a Spotlight/Dock macOS .app bundle in ~/Applications:
m5runner create-apps <game-slug>
# Or generate .app bundles for all registered games:
m5runner create-apps --all
```

---

## 3. How to Port a New Game Perfectly (Agent & Engineer Checklist)

When asked to add or port a new Windows game to `m5-wine-runner`, follow this exact 5-step engineering protocol:

### Phase 1: Classify the Game's Technical Profile
Determine the following 5 attributes before writing any config:
1. **Graphics API & Engine**:
   - **DirectX 12** (UE4, UE5, RE Engine, Decima, REDengine 4, RAGE, FromSoftware DX12) $\rightarrow$ Use `backend = "d3dmetal"` (or `"d3dmetal_gptk4"` if the engine uses advanced SM6.6+ compute shaders, DirectStorage, or heavy fast-travel streaming like Decima / RE Engine *MH Wilds*).
   - **DirectX 10 / DirectX 11** (FromSoftware DX11, REDengine DX11, MT Framework DX10) $\rightarrow$ Use `backend = "dxmt"` (`3Shain/dxmt` native Metal backend, which significantly outperforms D3DMetal in CPU-bound DX11 draw-call submission).
   - **32-bit (`i386`) Legacy DirectX 9 / 10 + WMV Cutscenes** $\rightarrow$ Use `prefix = "legacy_wow64"`, `backend = "dxmt"`, and `winetricks = ["wmp11", "quartz", "devenum"]`.
   - **Vulkan with Mandatory Hardware Ray Tracing** (`VK_KHR_ray_query` / `VK_KHR_ray_tracing_pipeline`, e.g. id Tech 8) $\rightarrow$ Use `backend = "moltenvk_rt"`.
2. **CPU Instruction Requirements**:
   - Does the binary execute `AVX`, `AVX2`, or `F16C` instructions on startup? Set `require_avx = true` (enforces `ROSETTA_ADVERTISE_AVX=1`).
3. **Upscaling / Frame Generation Support**:
   - Does the game support NVIDIA DLSS or DLSS Frame Generation? Set `dlss_metalfx = true` and add `"spoof_nvidia_dlss_registry"` to `hooks`. This injects the NVIDIA RTX 4090 PCI ID (`VEN_10DE&DEV_2684`), stages `nvngx-on-metalfx.dll` / `nvngx.dll`, and sets `D3DM_ENABLE_METALFX=1`.
4. **Shipping Executable vs. Launcher Binary**:
   - Never target a CEF/Chromium launcher (`REDlauncher.exe`, `2KLauncher.exe`, ` paradox-launcher.exe`) or an anti-cheat wrapper (`start_protected_game.exe`) directly if the shipping binary can be targeted or bypassed.
   - For Unreal Engine 4/5 games, list the deep shipping binary first in `exe_rel_paths` (e.g., `"<Game>/Binaries/Win64/<Game>-Win64-Shipping.exe"`).
5. **DRM / Anti-Cheat / Middleware Quirks**:
   - **Easy Anti-Cheat (EAC)**: Write a hook that backs up `start_protected_game.exe` to `.bak`, copies the main game `.exe` in its place, and writes `steam_appid.txt`.
   - **Sony PlayStation PC SDK (`PsPcSdk.dll`)**: Add `PsPcSdk = "n,b"` to `dll_overrides` and stub/install `PsPcSdkRuntimeInstaller.msi`.
   - **Capcom RE Engine Anti-Tamper**: Inject `REFramework` (`dinput8.dll`) with `dinput8 = "n,b"`.
   - **Rockstar / EA Background Services**: Add pre-launch `pkill -f` cleanup for zombie helper processes (`SocialClubHelper.exe`, `EABackgroundService.exe`).

### Phase 2: Add the Game Profile to `profiles/games.toml`
Add a new `[games.<slug>]` block in [profiles/games.toml](file:///Users/danieldiaz/projects/m5-wine-runner/profiles/games.toml):
```toml
[games.example-game]
name = "Example Game"
tier = "Tier 2: Medium Lift"
engine = "Unreal Engine 5 (DX12)"
backend = "d3dmetal_gptk4"
alt_backends = ["d3dmetal"]
prefix = "default_prefix"
steam_app_id = 1234560
exe_rel_paths = [
    "ExampleGame/Binaries/Win64/ExampleGame-Win64-Shipping.exe",
    "ExampleGame.exe",
]
launch_args = ["-dx12"]
winetricks = ["vcrun2022"]
dlss_metalfx = true
require_avx = true
dll_overrides = { d3d12 = "n,b", dxgi = "n,b", nvngx = "n,b" }
env = { ROSETTA_ADVERTISE_AVX = "1" }
hooks = ["spoof_nvidia_dlss_registry"]
notes = "Explanation of backend choice and required bypasses."
```

### Phase 3: Implement Any Custom Hook in `src/m5runner/patchers.py`
If the game needs file patching (XML/INI/JSON config edits, DLL injection, EAC binary swap, or registry tweaks):
1. Write a pure/idempotent function in [src/m5runner/patchers.py](file:///Users/danieldiaz/projects/m5-wine-runner/src/m5runner/patchers.py) with signature:
   ```python
   def my_custom_hook(
       profile: GameProfile,
       game_dir: Path | None = None,
       dry_run: bool = False,
   ) -> list[str]:
   ```
2. Always honor `dry_run=True` (append descriptions of actions to the returned `list[str]` without mutating disk when `dry_run` is `True`).
3. Register the function in `HOOK_REGISTRY` at the bottom of `src/m5runner/patchers.py`.

### Phase 4: Verify with `pytest` and `--dry-run`
```bash
uv run pytest -v
m5runner launch <new-game-slug> --dry-run
```
Ensure all unit tests pass and update `EXPECTED_14_SLUGS` (or profile tests) in [tests/test_runner.py](file:///Users/danieldiaz/projects/m5-wine-runner/tests/test_runner.py).

For deep technical details on how `D3DMetal 4.0`, `DXMT`, and `MoltenVK-RT` work under the hood, read [docs/PORTING_GUIDE.md](file:///Users/danieldiaz/projects/m5-wine-runner/docs/PORTING_GUIDE.md).
