# M5 Max Unified Wine / D3DMetal 4 / DXMT / MoltenVK-RT Game Runner (`m5-wine-runner`)

A modular, declarative macOS translation-layer runner and `.app` bundle generator engineered for **Apple M5 Max with 128GB Unified Memory** on **macOS 26+ (Tahoe)**.

Instead of maintaining 14 brittle one-off Wine wrappers, `m5-wine-runner` routes each title to its optimal translation backend inside `~/Games`:

- **Backend A (`d3dmetal` / `d3dmetal_gptk4`)**: Apple's Game Porting Toolkit 3/4 (`D3DMetal.framework`) for DirectX 12 titles with automatic **DLSS-to-MetalFX** and **Frame Generation** hooks (`D3DM_ENABLE_METALFX=1`) plus NVIDIA RTX 4090 PCI ID / NGX registry spoofing.
- **Backend B (`dxmt`)**: Open-source native DirectX 10/11-to-Metal translation (`3Shain/dxmt` `d3d11.dll` / `dxgi.dll` / `winemetal`) for ultra-high rasterized FPS in CPU-bound DirectX 11 and WoW64 DirectX 10 titles.
- **Backend C (`moltenvk_rt`)**: Isolated experimental **MoltenVK Hardware Ray Tracing** (`VK_KHR_ray_query`, `VK_KHR_ray_tracing_pipeline`, `VK_KHR_acceleration_structure`) compiled via Xcode specifically for id Tech 8 (*DOOM: The Dark Ages*).
- **Backend D (`xivmac`)**: Native delegation to **[XIV on Mac](https://www.xivmac.com/)** (Swift + bundled Wine + DXMT + Dalamud) for *Final Fantasy XIV*.

---

## Base M5 Max Environment Variables

Every game launched through `m5runner` automatically receives the core M5 Max environment configuration:

```bash
export WINEPREFIX="$HOME/Games/prefixes/default_prefix"
export WINEMSYNC=1                                  # Critical for multi-core CPU scaling on M5 Max
export ROSETTA_ADVERTISE_AVX=1                      # Exposes AVX/AVX2/F16C via Rosetta 2
export D3DM_ENABLE_METALFX=1                        # Hooks DLSS calls into Apple MetalFX
export MTL_HUD_ENABLED=1                            # Optional: Metal performance/FPS overlay (--no-hud to disable)
export WINEDLLOVERRIDES="d3d11,d3d12,dxgi=n,b"      # Forces Wine to load injected D3DMetal/DXMT DLLs
```

---

## Supported 14-Game Engineering Matrix

| Slug | Game | Engine & API | Optimal Backend | Tier | Automated Hook / Fix |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ffxiv` | **Final Fantasy XIV** | Custom (DX11) | `xivmac` | Tier 1 (Zero) | Delegates to native **XIV on Mac** for Square Enix OAuth handshake |
| `sekiro` | **Sekiro: Shadows Die Twice** | FromSoftware (DX11) | `dxmt` | Tier 1 (Low) | `xinput1_3,dinput8=n,b` + Hidraw controller ordering registry patch |
| `pragmata` | **Pragmata** | RE Engine (DX12) | `d3dmetal` | Tier 1 (Low) | `GST_PLUGIN_FEATURE_RANK=vtdec:MAX` hardware cutscene decoding + MetalFX |
| `witcher3` | **The Witcher 3 (Next-Gen)** | REDengine 4 (DX11/12) | `d3dmetal` / `dxmt` | Tier 1 (Low) | `--launcher-skip` to bypass REDlauncher CEF hang; dual DX12/DX11 binary router |
| `elden-ring` | **Elden Ring** | FromSoftware (DX12) | `d3dmetal` | Tier 2 (Low–Med) | Backs up `start_protected_game.exe`, writes `steam_appid.txt` (`1245620`), detects Seamless Co-op |
| `stellar-blade` | **Stellar Blade** | UE4 (DX12) | `d3dmetal` | Tier 2 (Low–Med) | `vcrun2022` + NVIDIA RTX 4090 PCI ID / NGX registry spoof to unlock DLSS/MetalFX |
| `gow-ragnarok` | **God of War Ragnarök** | Jetpack (DX12) | `d3dmetal` | Tier 2 (Medium) | `ROSETTA_ADVERTISE_AVX=1` + `PsPcSdk=n,b` PlayStation PC SDK stubbing |
| `horizon-fw` | **Horizon Forbidden West** | Decima (DX12) | `d3dmetal_gptk4` | Tier 2 (Medium) | Enforces GPTK 4 D3DMetal + Stereo `2.0` CoreAudio registry fix for dialogue |
| `mgs-delta` | **Metal Gear Solid Δ: Snake Eater** | UE5 (DX12) | `d3dmetal` | Tier 2 (Medium) | Pre-seeds `Saved/Config/Windows/` INI files to prevent first-boot/cutscene crash |
| `rdr2` | **Red Dead Redemption 2** | RAGE (DX12/Vulkan) | `d3dmetal` | Tier 2 (Medium) | Rewrites `system.xml` to `<API>kSettingAPI_DX12</API>`, passes `-sgadriver=d3d12`, kills zombie `SocialClubHelper.exe` |
| `jedi-survivor` | **Star Wars Jedi: Survivor** | UE4 (DX12) | `d3dmetal` | Tier 2 (Medium) | Kills corrupted `EABackgroundService.exe` pre-launch; flushes `wineserver -k` post-exit |
| `dmc4` | **Devil May Cry 4 Special Edition** | MT Framework (32-bit) | `dxmt` | Tier 3 (Med–High) | Uses `legacy_wow64` prefix with `wmp11`/`quartz`/`devenum` + optional WMV intro bypass |
| `mhwilds` | **Monster Hunter Wilds** | RE Engine (DX12) | `d3dmetal_gptk4` | Tier 3 (High) | Downloads & injects **REFramework** (`dinput8.dll`) with `dinput8=n,b` + GPTK 4 |
| `doom-dark-ages` | **DOOM: The Dark Ages** | id Tech 8 (Vulkan RT) | `moltenvk_rt` | Tier 3 (Very High) | Compiles & injects isolated MoltenVK with `VK_KHR_ray_query` / `VK_KHR_ray_tracing_pipeline` |

---

## Quick Start

```bash
cd ~/projects/m5-wine-runner
uv sync

# 1. Inspect hardware and translation SDK status
uv run m5runner doctor

# 2. List all 14 games and their configured backends
uv run m5runner list

# 3. Bootstrap open-source runtime (Wine 11.x WoW64, winetricks, DXMT v0.80+, prefixes)
uv run m5runner bootstrap --with-xiv

# 4. Import Apple's D3DMetal (GPTK 3/4) from a downloaded Evaluation Environment DMG
uv run m5runner import-gptk ~/Downloads/Evaluation_environment_for_Windows_games.dmg

# 5. Download a Windows game via steamcmd (or install/launch Windows Steam GUI)
uv run m5runner download sekiro --user <your_steam_username>
# OR launch Windows Steam inside the prefix:
uv run m5runner steam

# 6. Preview or launch any game (supports --backend dxmt|d3dmetal and --no-hud)
uv run m5runner launch witcher3 --dry-run
uv run m5runner launch rdr2 --dry-run
uv run m5runner launch witcher3 --backend dxmt --dry-run

# 7. Generate macOS .app bundles in ~/Applications
uv run m5runner create-apps --all
```

---

## Testing

```bash
uv run pytest -v
```
