# Deep-Dive macOS Translation Layer & Porting Guide (M5 Max 128GB)

This document explains the low-level mechanics of how `m5-wine-runner` bridges Windows x86_64/x86 games to Apple Silicon Metal on an **Apple M5 Max (128GB Unified Memory)** running **macOS 26+ (Tahoe)**.

---

## 1. Why the M5 Max (128GB) Changes the Engineering Equation

On 16GB–32GB Apple Silicon Macs, translation layer engineering is dominated by two failure modes:
1. **D3DMetal Residency Set & Descriptor Heap Leaks**: Titles like *Star Wars Jedi: Survivor*, *Horizon Forbidden West*, and *Red Dead Redemption 2* allocate unbounded Metal heaps across transitions, climbing past 24GB–32GB and triggering macOS jetsam/swap crashes. With **128GB of unified memory**, the M5 Max absorbs multi-hour sessions without swapping while `m5runner` flushes `wineserver -k` post-exit.
2. **CPU Thread Contention on Draw-Call Submission**: Rosetta-translated worker threads should not round-trip to `wineserver` for every sync call. GPTK Wine 7.7 implements esync (`WINEESYNC=1`, set automatically for D3DMetal titles); it has no msync, so `WINEMSYNC` is a no-op there.

---

## 2. How the Three Graphics Translation Layers Work

### Backend A: Apple D3DMetal (`d3dmetal` / `d3dmetal_gptk4`)
D3DMetal ships inside Apple's patched GPTK Wine, installed by `m5runner bootstrap` from Gcenx's `game-porting-toolkit` 3.0-3 into `~/Games/sdk/wine-gptk` (Wine 7.7, D3DMetal 3.0):
- **Host Metal Framework (`lib/external/`)**: `D3DMetal.framework`, `libd3dshared.dylib`
- **Wine Unix Bridges (`lib/wine/x86_64-unix/`)**: `d3d10.so`, `d3d11.so`, `d3d12.so`, `dxgi.so`, `nvapi64.so`, `nvngx.so`, symlinks to `../../external/libd3dshared.dylib` (found through its `@loader_path` rpath)
- **Windows PE Stubs (`lib/wine/x86_64-windows/`)**: Wine's builtin `d3d10.dll`, `d3d11.dll`, `d3d12.dll`, `dxgi.dll` *are* the D3DMetal stubs, so no DLL overrides are needed.

GPTK Wine's `ntdll.so` also loads `libd3dshared.dylib` to register Rosetta non-native code regions. Stock Wine has no such hook, which is one reason D3DMetal crashes on stock Wine Staging.

`m5runner import-gptk` can extract newer Apple DMGs (e.g. 4.0 beta 3) into `~/Games/sdk/d3dmetal`, but they are **not** staged: GPTK 4's PE stubs call `GetProcAddress(ntdll, "__wine_unix_call_dispatcher")` in `__wine_init_unix_call` and fail `DllMain` with `0xC0000135` on GPTK Wine 7.7, which only exports the older `__wine_unix_call`. Apple's Read Me documents CrossOver's `lib64/apple_gptk` as a host that accepts them.

#### How DLSS-to-MetalFX Translation Works
When `dlss_metalfx = true` is set on a profile:
1. `m5runner` copies GPTK Wine's `nvngx.dll` and `nvapi64.dll` into the prefix's `drive_c/windows/system32/` (Apple's documented step); the runtime itself is never modified.
2. `spoof_nvidia_dlss_registry` writes the NVIDIA GeForce RTX 4090 PCI ID (`VEN_10DE&DEV_2684`) and `HKLM\Software\NVIDIA Corporation\Global\NGXCore` keys into the prefix registry.
3. `D3DM_ENABLE_METALFX=1` redirects the game's `NVSDK_NGX_D3D12_Init` and `EvaluateFeature` calls directly into Apple's `MTLFXTemporalScaler` and `MTL4FXFrameInterpolator` on the M5 Max GPU.

---

### Backend B: DXMT (`dxmt`)
Downloaded from `3Shain/dxmt` (`v0.80+`) into `~/Games/sdk/dxmt`:
- **Unix Bridge**: `x86_64-unix/winemetal.so`
- **64-bit PE DLLs**: `x86_64-windows/{d3d10core.dll, d3d11.dll, dxgi.dll, winemetal.dll, nvapi64.dll, nvngx.dll}`
- **32-bit WoW64 PE DLLs**: `i386-windows/{d3d10core.dll, d3d11.dll, dxgi.dll, winemetal.dll}`

**When to choose DXMT over D3DMetal**:
- Any **DirectX 11** or **DirectX 10** title (*Sekiro: Shadows Die Twice*, *The Witcher 3* DX11 path, *Devil May Cry 4*).
- DXMT encodes Metal command buffers natively with lower CPU overhead than D3DMetal's DX11-on-12 path and supports both 64-bit and 32-bit (`i386-windows` WoW64) binaries.

---

### Backend C: Custom MoltenVK with Hardware Ray Tracing (`moltenvk_rt`)
Built via `m5runner build-moltenvk-rt` (`scripts/build-moltenvk-rt.sh`) into `~/Games/sdk/moltenvk-rt/libMoltenVK.dylib`:
- Compiles the experimental MoltenVK Ray Tracing pull request (`PR #2771`) with Xcode to expose `VK_KHR_acceleration_structure`, `VK_KHR_ray_tracing_pipeline`, and `VK_KHR_ray_query` mapped onto Metal 3/4 `MTLAccelerationStructure` and `MTLIntersectionFunctionTable`.
- Isolated from the rest of the system: `m5runner` injects it via `VK_ICD_FILENAMES` and `DYLD_LIBRARY_PATH` **only** when launching `moltenvk_rt` profiles (*DOOM: The Dark Ages*).

---

## 3. Common Porting Bottlenecks & Proven Fixes

| Symptom | Root Cause | `m5-wine-runner` Fix |
| :--- | :--- | :--- |
| **Game exits immediately on boot with `Illegal Instruction` (`0xc000001d`)** | Binary executes `AVX`, `AVX2`, or `F16C` instructions not advertised by default Rosetta 2 CPUID | Set `require_avx = true` (`ROSETTA_ADVERTISE_AVX=1`). |
| **Game hangs or crashes inside launcher window before reaching 3D engine** | CEF (Chromium Embedded Framework) sandbox/GPU compositing deadlock in Wine (`REDlauncher`, `Steam`, `EA App`, `Rockstar`) | Pass `--launcher-skip` (Witcher 3), target the `-Win64-Shipping.exe` binary directly, or pass `-cef-disable-gpu-compositing -no-cef-sandbox`. |
| **Permanent black screen right after Capcom / studio logo** | Missing GStreamer hardware video decode or legacy WMV (`wmvcore.dll`) cutscene crash; OR RE Engine anti-tamper hang | Set `GST_PLUGIN_FEATURE_RANK=vtdec:MAX` (RE Engine), install `wmp11 quartz devenum` in `legacy_wow64` (DMC4), or inject `REFramework` `dinput8.dll` (MH Wilds). |
| **Black screen for 2–4 minutes on first launch with high CPU/GPU usage** | Initial PSO / Metal shader cache compilation (especially Decima Engine in *Horizon Forbidden West* and UE5 titles) | Wait 2–4 minutes on first boot without killing the process; subsequent boots load the compiled Metal shader cache immediately. |
| **In-game DLSS / Frame Generation option is greyed out** | Game queries Windows registry for NVIDIA NGX core path and `0x10DE` vendor PCI ID | Add `"spoof_nvidia_dlss_registry"` hook and set `dlss_metalfx = true`. |
| **Dialogue / center-channel voice audio is missing or silent** | Game defaults to 5.1/7.1 surround output while macOS stereo speakers drop the center channel | Apply the `horizon_stereo.reg` CoreAudio `DefaultChannelMask=3` / `Speakers=2` registry patch. |
| **Wireless DualSense / Xbox controller is ignored in FromSoftware games** | `winebus` enumerates virtual HID devices ahead of XInput slot 0 | Apply `sekiro_input.reg` (`EnableHidraw=1`, `EnableSDL=1`, `MapControllers=1`) and `xinput1_3,dinput8=n,b`. |
