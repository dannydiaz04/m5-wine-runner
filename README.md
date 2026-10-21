# M5 Max Unified Wine / D3DMetal / DXMT / MoltenVK-RT Game Runner (`m5-wine-runner`)

A modular, declarative macOS translation-layer runner and `.app` bundle generator engineered for **Apple M5 Max with 128GB Unified Memory** on **macOS 26+ (Tahoe)**.

Instead of maintaining 14 brittle one-off Wine wrappers, `m5-wine-runner` routes each title to its optimal translation backend inside `~/Games`:

- **Backend A (`d3dmetal` / `d3dmetal_gptk4`)**: Apple's `D3DMetal.framework` for DirectX 12 titles, running inside Apple's patched GPTK Wine (Gcenx `game-porting-toolkit` 3.0-3 = Wine 7.7 + bundled D3DMetal 3.0), with **DLSS-to-MetalFX** hooks (`D3DM_ENABLE_METALFX=1`) plus NVIDIA RTX 4090 PCI ID / NGX registry spoofing. `d3dmetal_gptk4` currently falls back to D3DMetal 3: GPTK 4.0 betas need a newer Wine than GPTK Wine 7.7 (see [Runtimes](#runtimes)).
- **Backend B (`dxmt`)**: Open-source native DirectX 10/11-to-Metal translation (`3Shain/dxmt` `d3d11.dll` / `dxgi.dll` / `winemetal`) for ultra-high rasterized FPS in CPU-bound DirectX 11 and WoW64 DirectX 10 titles.
- **Backend C (`moltenvk_rt`)**: Isolated experimental **MoltenVK Hardware Ray Tracing** (`VK_KHR_ray_query`, `VK_KHR_ray_tracing_pipeline`, `VK_KHR_acceleration_structure`) compiled via Xcode specifically for id Tech 8 (*DOOM: The Dark Ages*).
- **Backend D (`xivmac`)**: Native delegation to **[XIV on Mac](https://www.xivmac.com/)** (Swift + bundled Wine + DXMT + Dalamud) for *Final Fantasy XIV*.

---

## Base M5 Max Environment Variables

Every game launched through `m5runner` automatically receives the core M5 Max environment configuration:

```bash
export WINEPREFIX="$HOME/Games/prefixes/gptk_prefix"   # D3DMetal games (default_prefix for DXMT games)
export WINEESYNC=1                                     # GPTK Wine 7.7 supports esync (not msync)
export ROSETTA_ADVERTISE_AVX=1                         # Exposes AVX/AVX2/F16C via Rosetta 2
export D3DM_ENABLE_METALFX=1                           # Hooks DLSS calls into Apple MetalFX
export MTL_HUD_ENABLED=1                               # Optional: Metal performance/FPS overlay (--no-hud to disable)
# D3DMetal needs no DLL overrides: GPTK Wine's builtin d3d11/d3d12/dxgi are D3DMetal.
# DXMT games get d3d10core,d3d11,dxgi=n,b in default_prefix.
```

---

## Runtimes

One Wine runtime per backend family, each with its own prefix. Never point two runtimes at one prefix (Wine "updates" a prefix to whichever version touched it last; downgrades are unsupported), and never copy D3DMetal files into a runtime by hand.

| Runtime | Path | Hosts | Prefix |
| :--- | :--- | :--- | :--- |
| Apple GPTK Wine 7.7 (Gcenx `game-porting-toolkit` 3.0-3, pinned + checksummed) | `~/Games/sdk/wine-gptk` | `d3dmetal`, `d3dmetal_gptk4` (bundled D3DMetal 3.0) | `~/Games/prefixes/gptk_prefix` |
| Wine Staging 11.x (Gcenx) | `~/Games/sdk/wine-staging` | `dxmt`, `moltenvk_rt` | `~/Games/prefixes/default_prefix` |

Why they can't be merged (verified against the binaries, not docs):
- D3DMetal only works inside Apple's patched Wine (Apple's GPTK Read Me: the bridge libraries "must be configured with a custom version of the Wine translation environment"). On stock Wine Staging 11.18 it crashes after loading.
- GPTK 4.0 beta bridge DLLs (`d3d12.dll`, `dxgi.dll`) look up `__wine_unix_call_dispatcher` in ntdll and fail `DllMain` with `0xC0000135` without it. GPTK Wine 7.7 only exports the older `__wine_unix_call`, so `m5runner import-gptk` keeps GPTK 4 in `~/Games/sdk/d3dmetal` for reference (e.g. CrossOver's `lib64/apple_gptk`) and never stages it.
- DXMT's `winemetal.dll` also needs `__wine_unix_call_dispatcher`, so DXMT can't run on GPTK Wine 7.7.

### Known issue: Windows Steam on GPTK Wine 7.7

Games launched outside Steam (e.g. Elden Ring's EAC bypass) still call `SteamAPI_Init()`, which needs the Windows Steam client running and signed in *in the same prefix*. The current (Oct 2026) Steam client does not yet run on GPTK Wine 7.7:
1. `BCryptGenRandom(BCRYPT_RNG_ALG_HANDLE)` crashes Wine 7.7's bcrypt (pseudo-handle unsupported). Manual workaround (tested, not automated): a native-marked copy of Wine 11.18's `bcrypt.dll` (`~/Games/sdk/compat-fixes/`) placed next to `steam.exe` and `steamwebhelper.exe`, with `bcrypt=n,b`.
2. `steamwebhelper.exe` (CEF 126) starts, then is shut down every ~10 s, so the login window never appears.
3. A game's `steam_api64.dll` crashes inside Steam's `steamclient64.dll` (execute fault).

The runner does not use Steam emulators (they key saves to a fake SteamID and can't serve Seamless Co-op).

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

# 3. Bootstrap both runtimes (GPTK Wine + bundled D3DMetal, Wine Staging), winetricks, DXMT, prefixes
uv run m5runner bootstrap --with-xiv

# 4. Optional: import a newer GPTK DMG for reference (not staged into GPTK Wine; see Runtimes)
uv run m5runner import-gptk ~/Downloads/Evaluation_environment_for_Windows_games.dmg

# 5. Download a Windows game via steamcmd into its runtime's prefix
uv run m5runner download sekiro --user <your_steam_username>
# Install/start Windows Steam in a game's prefix (needed by games launched outside Steam):
uv run m5runner steam elden-ring

# 6. Preview or launch any game (supports --backend dxmt|d3dmetal and --no-hud)
uv run m5runner launch witcher3 --dry-run
uv run m5runner launch rdr2 --dry-run
uv run m5runner launch witcher3 --backend dxmt --dry-run

# 7. Generate macOS .app bundles in ~/Applications
uv run m5runner create-apps --all
```

---

## Documentation for Developers & AI Agents

- **[AGENTS.md](AGENTS.md)**: Complete operational playbook for humans and AI coding agents — directory architecture, end-to-end game download/launch commands, and a 5-step checklist for porting any new game into `m5-wine-runner`.
- **[docs/PORTING_GUIDE.md](docs/PORTING_GUIDE.md)**: Deep-dive technical reference on D3DMetal, DXMT v0.80, MoltenVK Ray Tracing, DLSS-to-MetalFX registry spoofing, and common translation-layer fixes.

---

## Testing

```bash
uv run pytest -v
```
