# WINE_CX_BUILD_PLAN: Wine built from CodeWeavers' CrossOver 26.3.0 open-source tarball, for D3DMetal 4.0b3, Steam and Elden Ring

## Executive summary for Daniel

**What we are building, and why.** We compile our own Wine (the layer that runs Windows programs on macOS) on this Mac, from the open-source tarball CodeWeavers publishes for CrossOver 26.3.0. That source already has the hooks Apple's D3DMetal 4.0b3 needs. D3DMetal translates DirectX 12 to Metal, and 4.0b3 also bridges NVIDIA DLSS to Apple's MetalFX upscaler (useful only for DLSS games; Elden Ring has no DLSS). Today's GPTK 7.7 runtime cannot host D3DMetal 4, and its Windows Steam never logs in. The goal: Windows Steam logs in, Elden Ring runs through D3DMetal 4.0b3 with the Metal HUD on, and `m5runner` drives it all. Your GPTK 7.7 and Wine Staging/DXMT setups stay untouched. The work happens in a second checkout of the repo, so your `~/Applications` launchers keep working. No Apple or CrossOver files ever go into the public repo.

**Milestones** (agent time; your part in brackets): M0 tools, second checkout, patches, test helpers 1-2 h [approvals, two settings] · M1 Intel-format libraries 0.5-1 h · M2 source and configure about 30 min · M3 build and checks about 1 h · M4 smoke tests 30-60 min · M5 D3DMetal hookup 1-4 h · M6 Steam 2 h to 2 days, the biggest unknown [one sign-in, about 10 min, at a time you pick] · M7 Elden Ring 1-4 h [one setting, a 10-minute play test at a time you pick] · M8 MetalFX check 1-3 h [one free benchmark install and one benchmark run, about 15 min; a repeat run only if the agent asks] · M9 runner integration 4-8 h · M10 docs and PR 1-2 h [review and merge]. Only one Wine session runs at a time, and a Steam window or game handed to you stays yours: the agent's scripts refuse to close it until you quit it or tell the agent you are done (a game left running is closed after 4 hours). Total: about 2-5 working days of agent time, plus 0.5-2 days waiting on your steps.

**Approvals needed from Daniel**
1. Install arm64 Homebrew build tools: `bison`, `pkgconf`, `ccache`, `cmake`, `ninja`, `freetype` and `mingw-w64` (a compiler for Windows programs). Nothing Intel-only comes from Homebrew.
2. Turn off automatic macOS updates until M10. An update mid-run reboots the Mac and changes how D3DMetal behaves.
3. Optional: download athei's public reference Wine build (235 MB, built from the same CrossOver 26.3 source, and it bundles Apple's GPTK 4.0b2). It is used only to tell "our build is broken" from "Steam is broken on this Mac", and it stays outside the repo.
4. Two free DLSS test titles in the new Steam: the Black Myth: Wukong Benchmark Tool (AppID 3132990), which the MetalFX check needs (M8.4), and, only if Wukong cannot be used, the FINAL FANTASY XVI DEMO (AppID 2738000). Their download sizes are not checked yet.
5. Only if a step calls for it: Microsoft's Visual C++ runtime installers in the new prefix (a prefix is Wine's private C: drive), MacPorts (needs your password) if the library build stalls, and the CrossOver trial as a last-resort comparison.
6. Pushing the branch and opening the PR (M10).

**Steps only Daniel can do**
1. Merge PR #1 (`fix/gptk-runtime-split`) when you are happy with it. The new branch sits on top of it.
2. M0: give the terminal the Screen Recording permission (it lets the agent screenshot only Wine windows), switch off automatic macOS updates, and keep the lid open and the charger in during long runs.
3. M6: at a time you pick, sign in to Steam in the new prefix, approve the Steam Guard code (Steam's two-factor check) and tick "Remember me". The window stays yours until you quit Steam (Steam > Exit) or tell the agent you are done. Never press Install, Update or Verify for Elden Ring in that Steam.
4. Only if no Steam window ever draws (rung L6): sign in once in the reference Wine build or the CrossOver trial instead, then quit Steam there; the agent copies the login over. If Steam then works only in the background ("headless only"), reply "OK headless only" so the agent can record your sign-off.
5. M7: at a time you pick, set System > Network > Launch Setting to "Start offline" once in Elden Ring. Then play for 10 minutes, note the FPS the HUD shows, and quit with System > Quit Game.
6. M8: install the free Black Myth: Wukong Benchmark Tool when the agent opens its install dialog, then run its benchmark once with DLSS (and Frame Generation, if offered) selected (numbered steps in M8.4). Only if the MetalFX check fails, the agent asks for one more run after each setting it changes.
7. Only if the agent asks: reboot the Mac at a moment that suits you. The agent never reboots it, so your downloads keep running.
8. M10: review and merge the PR, then double-click Elden Ring.app once to confirm it starts on the new runtime.

---

Status: plan only. Nothing has been built or installed yet. Written 2026-10-20 and revised the same day after three review rounds (round 1: feasibility review F1-F20 and completeness review C1-C26; round 2: review F15 and C13, R1-3 to R1-24; round 3: review F15, R1-6, R1-18 and R2-4 to R2-19) plus a targeted fourth (R3-1 to R3-20) and a targeted fifth (R4-1 to R4-7). The final check's two findings (R5-1, R5-2) were fixed by hand. Appendix C maps every item to its change. It lives in the repo at `docs/WINE_CX_BUILD_PLAN.md` on branch `feat/cx-runtime`, which was created with this plan's commit (PR #2, stacked on PR #1).

How to use it: run the milestones in the order of the dependency graph in 1.3. Each milestone has the exact commands, the expected output, gates with IDs and the known failure modes. Every fix attempt follows the cycle in section 4 and gets an entry in `docs/cx/BUILD_LOG.md`.

Conventions
- `wine/...` means `~/Games/src/cx-26.3.0/sources/wine/...`, the pristine CrossOver 26.3.0 source. The tarball's sha256 is `ac99c8ca4b3848f3e81784135f023df266b61c2345726ea55a50b3e030dd6872`.
- `research/...` means `~/Games/src/research/...`, where the researchers saved downloads and notes. **It is local only: nothing under `research/` is ever committed.** The repo carries only the patches vendored in M0.5, each with its provenance.
- `$REPO` means the development worktree `~/projects/m5-wine-runner-cx` (branch `feat/cx-runtime`). The stable checkout `~/projects/m5-wine-runner` stays on Daniel's branch, because his `~/Applications/*.app` launchers run `uv run --project ~/projects/m5-wine-runner` (D18). `X=$REPO/scripts/cx` is the harness directory (Appendix A).
- "verified" means seen in source or docs, or reproduced on this Mac. **ASSUMPTION** marks anything unverified and names the test that settles it.
- **Shell.** Every code block is bash and must also run under Apple's `/bin/bash` 3.2.57.
  - Stage code lives in `scripts/cx/stages/<stage>.sh` and runs only through `scripts/build-wine-cx.sh`.
  - Inline blocks are saved to a file and run with `/bin/bash FILE`, or run as `/bin/bash -c '...'`. Never paste a block into the agent's zsh tool shell: zsh does not word-split `$VAR`, aborts on an unmatched glob, and wraps `grep` in a shell function. Inline checks call `/usr/bin/grep`.
  - Bash 3.2 rules: no `${v,,}`, `mapfile` or `declare -A`; expand a possibly empty array as `${a[@]+"${a[@]}"}`; write zero-padded numbers as `$((10#$n))`; feed a loop that must `exit` or count with `done < <(...)`, not through a pipe; macOS `head -n 0` is an error.
  - Never end a `pipefail` pipeline with `grep -q`. The producer can die of SIGPIPE and turn a match into a failure (reproduced: `yes | head -c 200000 | grep -q y` exits 141 under `set -euo pipefail`). Use `grep -c` or capture the output.
  - Gate scripts use `set -u` only and print `PASS`, `FAIL` or `INCONCLUSIVE` for each gate.
- **Sessions.** One Wine session runs at a time. Every script or block that starts Wine processes of the cx runtime takes `~/Games/logs/cx/SESSION.lock` first, itself or through the `steam.sh` and `er.sh` modes it calls, and `cx-run.sh` refuses a `wineserver -k` that would end someone else's session (4.9). A lock counts as live only while its anchor process still runs with the start time recorded in the lock and the lock is younger than the last boot, so a reused PID or a reboot never keeps a dead session's lock alive (R2-5, R2-10). A Steam window or game handed to Daniel has its own lock owner (`steam-daniel`, `er-daniel`, `m84-daniel`) that no agent script ends without `--force` (R2-8, R2-9).
- **Long jobs** run as background jobs of the agent's shell tool, with their log tailed, because one foreground tool call ends after 10 minutes (R2-12): `build-wine-cx.sh` (`all`, `from`, `iter`, `promote` and any single M1-M3 stage), `smoke.sh`, `steam.sh ui`, `er.sh`, and every block that calls one of them. A stage killed by the limit starts over (`deps` rebuilds every library from scratch), and a promote killed with SIGKILL skips its rollback trap (4.8 step 4).
- **IDs** (R2-19). Gates carry letter prefixes: DEP1-DEP4 (M1), CFG1-CFG4 (M2), V1-V15, T1-T14, H1-H10, S1-S9, E1-E9 and X1-X8. A bare F1-F7 is an acceptance criterion (1.2) and D1-D21 a decision (2.6). Review items always carry the word "review": "review F6" for the feasibility review, "review C13" for the completeness review, and one "review" covers a list such as "review C2, F8". Verification items are R1-n, R2-n, R3-n and R4-n. The tables of Appendix C list review items without the prefix. The language standard C23 (GCC, M3) is not a review item.
- **Redaction.** Tracked files (this plan, BUILD_LOG, PR text) never contain a SteamID64, a `[U:1:…]` account id, Steam account or persona names, IP addresses, Steam Guard codes or `/Users/<name>` paths. Raw logs stay in `~/Games/logs/cx`. Every excerpt quoted in a tracked file goes through `scripts/cx/redact.sh` first (4.2). `tests/test_repo_hygiene.py`, added in M0.6, enforces the rule before every commit, new files included (R3-20), and before the push M10 scans every line the branch adds to its history the same way (5.3, 5.5; R2-17).

---

## 0. Summary

**What we build.** A new Wine runtime with the internal label `cx` (directory name `wine-cx26`). It is Wine 11.0 plus CodeWeavers' changes, built from CodeWeavers' CrossOver 26.3.0 open-source tarball, plus 6 small LGPL base patches, compiled on this Mac. The unix side is x86_64 and runs under Rosetta. The Windows side is i386 + x86_64 ("new WoW64"). Each build installs into its own immutable directory `~/Games/sdk/wine-cx26.builds/bNNN-…`. The symlink `~/Games/sdk/wine-cx26` names the current build, and only the `promote` stage moves it. The runtime gets its own prefix, `~/Games/prefixes/cx_prefix`.

Apple's GPTK 4.0b3 (D3DMetal 4.0b3 plus the DLSS-to-MetalFX bridge) is kept as a separate, unmodified "renderer tree" at `~/Games/sdk/gptk/4.0b3`. That tree is put in front of Wine's own Direct3D only for game processes. Steam's own processes never load D3DMetal, and gate S9 checks it.

**Already in hand (verified at plan time).**
- **D3DMetal 4 and MetalFX: yes, we have both.**
  - `~/Games/sdk/d3dmetal` holds the complete GPTK 4.0b3 redist, byte-identical to the DMG, and `D3DMetal.framework` reports `4.0b3` (metalfx research).
  - The MetalFX bridge ships as `nvngx-on-metalfx.{dll,so}` and needs only Apple's documented rename to `nvngx`.
  - The MetalFX spatial and temporal scalers report `supportsDevice=YES` to x86_64 processes on this M5 Max (`research/toolchain/probe/fx.m`).
- **The CrossOver tree already has every Wine-side hook D3DMetal needs:**
  - `__wine_unix_call_dispatcher` (`wine/dlls/ntdll/ntdll.spec:1753`)
  - the libd3dshared loader and the ms_abi thunks (`wine/dlls/ntdll/unix/loader.c:1297-1366`, `wine/dlls/ntdll/unix/unix_private.h:600-637`)
  - `macdrv_functions` (`wine/dlls/winemac.drv/d3dmetal.c:397`)
  - the WDDM 2.7 scheduling caps (`wine/dlls/win32u/d3dkmt.c:715-731`)
  - msync and bcrypt pseudo-handles
- **What the tarball lacks:** CrossOver's closed launcher and `cxcompatdb.so`, which pick the graphics backend for each process. We replace them with environment variables and one ntdll patch (section 2.2).
- **Patch series:** 22 candidates, 6 base and 16 standby. On a pristine copy of the tree they apply with `git apply` in the order of 2.7. This was verified on 2026-10-20 three times: in both reviewers' scratch clones and in the editor's scratch tree of the 33 files the patches touch. Constraints found: hb-0011 needs hb-0008 and hb-0009, hb-0016 needs hb-0011, and at-0008 conflicts with hb-0007 in `dlls/winemac.drv/window.c`. With an annotated tag, `git describe` prints `winecx-26.3.0-6-g…` for the base series.
- **Build tools are missing:** bison ≥ 3.0 (Apple ships 2.3, which configure rejects), mingw-w64, pkgconf, cmake, ninja, ccache and an arm64 freetype. M0 installs them, with Daniel's OK.

**Decisions at a glance.** Section 2.6 gives the reasons and the alternatives.
1. PE toolchain: Homebrew mingw-w64 GCC, not llvm-mingw. An llvm-mingw-built kernelbase.dll has been shown to stall Steam's login.
2. The build runs natively on arm64. The unix side is cross-compiled with `/usr/bin/clang -arch x86_64`, and the Wine build tools are built for arm64.
3. The x86_64 libraries are cross-built: gmp, gnutls and freetype from the tarball, plus nettle 3.10.2, SDL2 2.32.10 and MoltenVK 1.4.2.
4. GPTK lives outside the Wine install. Each process opts in with `WINEDLLPATH_PREPEND` (Highball patch 0003).
5. Steam's UI renderer follows a ladder ranked by evidence: rung L1 is athei's recipe (DXMT plus `--in-process-gpu`), rung L2 is Highball's (patch 0007 plus DXMT, GPU process out of process). If no rung renders, a headless sign-in still lets Elden Ring run (rung L6).
6. Sync: `WINEMSYNC=0` everywhere until Elden Ring works. After that, msync is A/B-tested for game sessions only.
7. No automatic prefix updates. The prefix's `.update-timestamp` reads `disable`, and a build becomes current only through `promote`, which runs `wineboot -u` in a clean environment (2.4).
8. Runner development happens in a git worktree, so Daniel's launchers keep running the stable checkout (D18).
9. Wine sessions never overlap: each takes the session lock, the DLSS tests run in a prefix of their own, `cx_dlss`, and a Steam window or game handed to Daniel is locked to him (owners `steam-daniel`, `er-daniel` and `m84-daniel`), so no test can kill his Steam window or game (D21, 4.9).

---

## 1. Goal and success criteria

### 1.1 Goal
Run the current 64-bit Windows Steam client and Elden Ring (AppID 1245620, DirectX 12, EAC bypassed for offline play) on this Apple M5 Max with macOS 26.5.1. Elden Ring must render through Apple's D3DMetal 4.0b3, and the DLSS-to-MetalFX path must be available for DLSS titles (Elden Ring itself has no DLSS). The runtime is built from CodeWeavers' CrossOver 26.3.0 open-source tarball and driven by `m5runner`. The existing GPTK 7.7 and Wine Staging/DXMT runtimes must not regress.

### 1.2 Final acceptance (all required)

| ID | Criterion | Measured by |
|---|---|---|
| F1 | Steam works in `cx_prefix` | The S-core gates (S1, S6, S7, S8) and S9 pass, and the S-UI gates (S2-S5) pass: the UI shows the Library after sign-in. If only the headless rung L6 works, F1 is recorded as "headless only" and counts as met only with Daniel's written OK in BUILD_LOG (M6) |
| F2 | Elden Ring reaches the main menu and gameplay through D3DMetal 4.0b3 | E6 (window-only screenshot of the title screen or main menu, not black) and E8 (Daniel plays at least 10 minutes without a crash) (M7) |
| F3 | Metal HUD visible in Elden Ring | The HUD shows in the screenshot, and `metal-HUD:` per-frame lines (`MTL_HUD_LOG_ENABLED=1`) appear with increasing frame numbers (E5) |
| F4 | D3DMetal 4 confirmed | E4: `D3DM` lines are captured (game stderr or unified-log category `D3DMetal`). E3: the probe's lsof and vmmap listings of the running game show both `d3d12.dll` and `dxgi.dll` mapped from `~/Games/sdk/gptk/4.0b3/wine/x86_64-windows/` (`lib.sh gptk_mapped` counts 2). Wine's `+module` "mapping PE file" trace cannot show this: it names the file the loader asked for (the system32 placeholder or copy), not where the builtin was found (review F15, round 3). F4b: the mapped `libd3dshared.dylib` has the 4.0b3 file's size (250,672 bytes) and inode, `D3DMetal.framework` is mapped from `gptk/4.0b3`, and the tree still matches its `MANIFEST.sha256`, whose `version.plist` reads `4.0b3`. F4c: if the HUD shows a Game Porting Toolkit version label, its text is recorded, and the gate fails if it reads 3.x |
| F5 | MetalFX verified | The HUD shows a "MetalFX Scaling" row with input resolution below target in two legally obtainable DLSS programs, and both are required: NVIDIA's DLSS SDK sample (gates X1-X3, M8.2, in the test prefix `cx_dlss`; it calls NGX directly), and the Black Myth: Wukong Benchmark Tool (gate X7, M8.4; Steam AppID 3132990, free), the only test of a shipping Steam title's Streamline path. The sample runs are A/B-tested with `D3DM_ENABLE_METALFX` set to 1 and to 0. Frame generation (X8) is recorded, not required. If either part cannot pass after every M8.3 variable in its own prefix (`cx_dlss` for the sample, `cx_prefix` for Wukong; R3-15), BUILD_LOG records "pending" with the exact next test (R2-13) |
| F6 | GPTK 7.7 and Wine Staging/DXMT paths not regressed | `(cd ~/Games/sdk && shasum -a 256 -c --quiet ~/Games/logs/cx/baseline-sdk.sha256)` passes. The Elden Ring tripwire passes: `(cd "$HOME/Games/prefixes/default_prefix/drive_c/Program Files (x86)/Steam/steamapps/common/Elden Ring/Game" && shasum -a 256 -c --quiet ~/Games/logs/cx/baseline-er.sha256)`. Dry-run environments for `--runtime gptk` and `--backend dxmt` match the M0.3 baseline |
| F7 | Repo tests pass | `uv run pytest -v` is green, including the new cx tests and `tests/test_repo_hygiene.py` (present since M0.6): no Apple, Wine or CrossOver binaries and nothing from `research/` tracked, no account data, and `/bin/bash -n` passes on every script. Before the push, the same scan over every line the branch adds is clean (M10) |

### 1.3 Milestone exit criteria and order

| Milestone | Exit criterion |
|---|---|
| M0 Toolchain, worktree, patches, harness, renderer tree | Tools report the expected versions. Baselines are recorded. The worktree `~/projects/m5-wine-runner-cx` is on `feat/cx-runtime`. Patches are vendored with provenance. `~/Games/tools/wine-windows` runs. The renderer tree `~/Games/sdk/gptk/4.0b3` passes its manifest check. The test programs are built. The unattended preconditions (M0.9) are met |
| M1 x86_64 dependencies | Gates DEP1-DEP4: 7 x86_64 dylibs with `@rpath` ids, no absolute paths, signed, headers present |
| M2 Source, tools, configure | The series is applied with a matching commit count, `git describe` reads `winecx-26.3.0-6-g…`, the arm64 tools are built and gates CFG1-CFG4 pass |
| M3 Build, assemble, verify, promote | `make` succeeds, an immutable `bNNN-…` dir exists, V1-V15 pass on it, and `promote` made it current |
| M4 Smoke tests | Gates T1-T14 pass in the scratch prefix `cx_smoke` |
| M5 D3DMetal 4.0b3 hookup | Gates H1-H10 pass with our own D3D12 and D3D11 test programs, which do not depend on DLSS |
| M6 Steam | S-core (S1, S6, S7, S8) and S9 pass. S-UI (S2-S5) passes, or Daniel accepts "headless only". Daniel has signed in, a headless session is ready within 120 s, and Steam is pinned |
| M7 Elden Ring | Gates E1-E9 pass and F2, F3 and F4 are met. The msync and hb-0013 A/B results are recorded |
| M8 MetalFX | Gates X1-X7 pass and X8 is recorded, or F5 is recorded as pending with the next test |
| M9 Runner integration | M9a code: the cx code and unit tests are green (pytest starts no Wine process). M9a acceptance, after M7: `m5runner` reproduces the S-core and E1-E7 gates through the CLI. M9b: after the flip, `--runtime gptk` still works and F6 passes |
| M10 Docs and PR | README, AGENTS.md, PORTING_GUIDE and BUILD_LOG are updated. A PR is opened once Daniel says to push. After he merges, Elden Ring.app is regenerated |

Dependency graph. Milestones run in this order. Wine sessions never overlap, because each one takes the session lock (4.9). "In parallel" below therefore means either interleaved sessions or work that starts no Wine process.
```text
M0 -> M1 -> M2 -> M3 -> M4 -> M5 -+-> M6 -> M7 ------------------------------+-> M8.4 (Wukong, required) -> M9a acceptance -> M9b -> M10
                                  +-> M8.0-M8.2, X6, and M8.3 only if X1-X3 -+
                                      fail (prefix cx_dlss; sessions of their own, between Steam cycles)
M9a code and unit tests: any time after M0.6. They start no Wine process, so they fill the waits for Daniel.
M6.0 (reference runtime): after M1.1 (SteamSetup.exe) and Daniel's OK. It is another runtime and prefix, so it
     takes no session lock and may run while M1.2-M5 build.
```
- M8.0-M8.3 and X6 need only M5. Run them right after M5, or between Steam cycles outside the sign-in slot agreed with Daniel (M0.12). Never run them while a Steam UI session or `er.sh` holds the lock: they refuse, and they also refuse while a headless Steam runs (`steam.sh stop` first).
- M8.4 always runs, after M7 and after M8.2 (and M8.3, when X1-X3 failed): it needs the cx Steam (or the Steam that drew for the L6 sign-in), Daniel's benchmark run (R2-13), and the DLSS setup with which the sample passed, which it copies into `cx_prefix` before the first launch (R3-4).
- During Daniel's sign-in slot (M6.3), his play test (M7.3) and his benchmark run (M8.4) the session holds the lock, so the agent does only work that starts no Wine process: M9a code and unit tests, BUILD_LOG and docs.
- M9a acceptance replays E1-E7 through the runner, so it needs M6's S-core and M7 (R1-22).

The renderer tree, formerly step M5.1, is built in M0.10. M4 therefore already runs with libd3dshared in the environment, as every later session does.

---

## 2. Architecture

### 2.1 On-disk layout

```
~/projects/m5-wine-runner-cx/                $REPO: git worktree, branch feat/cx-runtime (all development)
~/projects/m5-wine-runner/                   stable checkout used by ~/Applications/*.app; switched only in M10, after Daniel merges
~/Games/build.noindex/cx26/                  build root ($CXB); ".noindex" keeps Spotlight out
  downloads/  deps-src/  deps/ (private x86_64 prefix)  wine-src/ (git repo)  wine-tools/ (arm64)
  wine-x86_64/ (main build)  stage/install/  logs/  ccache/  stamps/ (with assembled.id)  tests/bin/ (test .exe files)
  local.env                                  machine-local settings sourced by env.sh: CX_BUNDLE_DXMT=1 after the winemetal
                                             fallback (M6), CX_SESSION_FILTER=0 if gate T13 fails (M4)
  wukong.installdir                          the benchmark's install folder name (M8.4)
~/Games/sdk/wine-cx26.builds/bNNN-winecx-26.3.0-<n>-g<sha>/     one immutable install per build (stage assemble)
  bin/wine -> ../lib/wine/x86_64-unix/wine     symlink: the loader finds ntdll.so through its realpath (wine/loader/main.c:98-170)
  bin/wineserver
  lib/libfreetype.6, libgnutls.30, libnettle.8, libhogweed.6, libgmp.10, libSDL2-2.0.0, libMoltenVK (.dylib, @rpath ids)
  lib/wine/{x86_64-unix, x86_64-windows, i386-windows}/
  share/wine/{wine.inf, nls, fonts, mono/wine-mono-10.4.1, gecko/wine-gecko-2.47.4-x86, gecko/wine-gecko-2.47.4-x86_64}
  dSYM/{ntdll,win32u,winemac}.so.dSYM         unix-side symbols that survive later rebuilds of the build tree
  BUILDINFO                                  line 1 = build id; macOS build, toolchain, patch list
~/Games/sdk/wine-cx26.builds/dev/            optional mutable clone for single-module hot swaps (4.5)
~/Games/sdk/wine-cx26 -> wine-cx26.builds/<current>        moved only by the promote stage
~/Games/sdk/gptk/4.0b3/                      Apple redist/lib, unmodified except Apple's documented nvngx rename (M0.10)
  external/D3DMetal.framework  external/libd3dshared.dylib
  wine/x86_64-windows/{d3d10,d3d11,d3d12,d3d12core,dxgi,nvapi64,nvngx}.dll
  wine/x86_64-unix/{same names}.so -> ../../external/libd3dshared.dylib
  MANIFEST.sha256                            excludes itself
~/Games/sdk/gptk/4.0b3-overlay/wine/         only if M8.3 needs the nvapi alias
~/Games/sdk/gptk/3.0/                        optional A/B tree (D3DMetal 3.0 copied from wine-gptk; triage only)
~/Games/sdk/cx-overlays/dxmt/                only if rung L1 needs the winemetal fallback (M6)
~/Games/sdk/ref/athei-cx-26.3.0-9/           optional reference runtime (M6.0); third-party, contains Apple's GPTK 4.0b2; never copied from
  RUNTIME_ROOT                               one line: the extracted runtime's root (read by ref-run.sh and steam.sh --ref)
~/Games/prefixes/cx_prefix/                  new prefix, created and owned by the cx runtime; Steam lives here
  .update-timestamp ("disable")  .m5runner-runtime (BUILDINFO line 1)  .cx-session (msync=, offline= and log offsets of the last Steam start)
  drive_c/Program Files (x86)/Steam/steamapps/common/Elden Ring/   APFS clone of default_prefix's copy (D15)
~/Games/prefixes/cx_prefix.snap-<tag>/       APFS clones taken by lib.sh snap_prefix before risky steps (an older one of that tag: .old-<UTC>)
~/Games/prefixes/<p>.snap-prepromote-<UTC>/  promote's rollback point for cx_prefix and cx_dlss; deleted when promote succeeds
~/Games/prefixes/<p>.failed-promote-<build>-<UTC>/   kept for triage when promote fails after its switch (M3.5)
~/Games/prefixes/cx_dlss/                    DLSS and MetalFX test prefix (M8.0); promoted and stamped like cx_prefix; no Steam
~/Games/prefixes/cx_smoke/                   disposable smoke-test prefix, recreated by smoke.sh and promote
~/Games/prefixes/cx_ref_prefix/              scratch prefix for the reference runtime only (M6.0)
~/Games/logs/cx/C<NNN>-<slug>/               evidence for each cycle
~/Games/logs/cx/SESSION.lock                 exists while a Wine session runs (owner, pid, prefix; 4.9)
~/Games/backups/cx/<UTC>/                    user-data backups (saves, Steam login state); newest 10 kept; local only
~/Games/tools/wine-windows                   CGWindowList helper (Appendix A.4)
$(getconf DARWIN_USER_CACHE_DIR)d3dm.cx-stash/  D3DMetal shader caches of eldenring.exe and the test programs, one per GPTK version,
                                             plus the parked original (M7.5); d3dm/ itself keeps GPTK 7.7's layout
$REPO/patches/cx26.3/  $REPO/scripts/build-wine-cx.sh  $REPO/scripts/cx/  $REPO/docs/cx/BUILD_LOG.md
```

These stay read-only throughout: `~/Games/sdk/{wine-gptk,wine-staging,d3dmetal,dxmt}`, `~/Games/prefixes/{gptk_prefix,default_prefix,legacy_wow64}`, `~/Games/src/cx-26.3.0` and the stable checkout `~/projects/m5-wine-runner`, which changes only in M10, after Daniel merges. The 52 GB Elden Ring folder in `default_prefix` is APFS-cloned into `cx_prefix` with `cp -Rc`, not symlinked. A clone shares blocks until a file changes, so it costs no space, and nothing done in the cx Steam can write through to `default_prefix`.

**Why GPTK is a separate tree and not merged into `lib/wine`.**
- Builtin lookup searches Wine's own `lib/wine` before any `WINEDLLPATH` entry (`wine/dlls/ntdll/unix/loader.c:387-406`). So GPTK's `d3d11`, `dxgi` and `d3d12` either replace Wine's for every process (the merge route) or must be prepended for each process.
- Merging would make D3DMetal and Apple's nvapi64 the builtins of Steam's webhelper too. On Apple's stack the webhelper's GPU process crash-loops, and its NVAPI probe kills it (frankea/Whisky#276; research/steam-compat).
- A separate tree keeps Apple's files out of every Wine rebuild.
- It also allows A/B tests between 4.0b3 and 3.0 by changing one variable.

### 2.2 Replacing CrossOver's closed launcher and cxcompatdb.so

The trial is CodeWeavers' product. We read only its plain-text launcher and bottle scripts. The `cxcompatdb.so` behaviour in this table is **inferred from symbol names** in the research's listing of that binary (d3dmetal-integration research, finding 4). It is not verified, and no further `strings`, `nm`, `otool` or disassembly of CodeWeavers' closed binaries is done (4.6, 6.1).

| CrossOver does (closed code) | Evidence | We do instead |
|---|---|---|
| The launcher sets `CX_APPLEGPTK_LIBD3DSHARED_PATH=$CX_ROOT/lib64/apple_gptk/external/libd3dshared.dylib` for every process; its comment says libd3dshared is used whether or not D3DMetal is enabled | Trial launcher `research/d3dmetal-integration/cx_text/CrossOver.app/Contents/SharedSupport/CrossOver/CrossOver-Hosted Application/wine:679-684` (plain text) | Set it for every cx process, to the realpath of `~/Games/sdk/gptk/<ver>/external/libd3dshared.dylib`. ntdll dlopens exactly that path on Darwin ≥ 23 (`wine/dlls/ntdll/unix/loader.c:1323-1331`), but only when the first non-builtin PE module loads (`wine/dlls/ntdll/loader.c:2357-2364`). Wine's own builtin programs (cmd, notepad, wineboot) therefore never load it; Steam, games and our test programs do. ntdll then records libd3dshared's `__TEXT` range so that 9 Nt* calls coming from Apple code use ms_abi thunks (`unix_private.h:600-637`). Without the variable those calls take the sysv entry with garbled arguments, which is the likely cause of the crash on stock Staging 11.18 (likely, research) |
| The launcher sets `ROSETTA_ADVERTISE_AVX=1` unless the user overrides it, and `DOTNET_EnableWriteXorExecute=0` | launcher:697, 724-738 | Set both for every cx process. To turn AVX off, unset the variable; Rosetta treats any value as on (launcher comment at 727-731) |
| `cxcompatdb.so` calls `prepend_dll_path("$CX_ROOT/lib64/apple_gptk/wine")` for D3DMetal processes and sets `CX_ACTIVE_GRAPHICS_BACKEND` | Inferred from symbol names (see above); the hook it uses is at `wine/dlls/ntdll/unix/loader.c:365-385, 2246-2259` | Game processes only: `WINEDLLPATH_PREPEND=<gptk>/wine` (patch hb-0003) and `CX_ACTIVE_GRAPHICS_BACKEND=d3dmetal`. The latter turns on the WDDM 2.7 hardware-scheduling caps that Streamline checks (`d3dkmt.c:715-731`). Never copy the trial's `cxcompatdb.so`: it is CodeWeavers' closed code under the trial licence |
| Per-app DllOverrides and switches from a signed compat database | Inferred, as above | Registry `HKCU\Software\Wine\AppDefaults\<exe>\...` plus `CommandLineAppend` (patch hb-0006) |
| `redirect_nvngx_to_d3dmetal` | Inferred from a symbol name, as above | CW HACK 22435 already makes wineboot write placeholder `atidxx64/nvapi64/nvngx.dll` files into system32 (`wine/loader/wine.inf.in:739-742`; a `*` source means `build_fake_dll`, `wine/dlls/setupapi/fakedll.c:1122`). Loading a placeholder resolves the builtin from the first DLL path (`loader.c:1660-1666`), which is GPTK's in game processes |
| Bottle settings `CX_GRAPHICS_BACKEND` and `WINEMSYNC` | Bottle templates in the trial (plain-text Perl, `CXBT_win10_64.pm:448-466`) | The m5runner backend, plus `WINEMSYNC` chosen per session |
| `WINEDLLPATH` including `lib/wine`, which turns on the per-exe Dock names of CW HACK 22144 | launcher:655-668, 712; `loader.c:565-686` | Not replicated (cosmetic). Optional later: `WINEDLLPATH=$RT/lib/wine` |

Fallback, if the prepend patch ever conflicts: build `research/d3dmetal-integration/shim/m5compat.c` as `$RT/lib/wine/x86_64-unix/cxcompatdb.so`. It calls `prepend_dll_path()` from `M5_DLLPATH_PREPEND`, with no ntdll change.

### 2.3 Process environments (single source of truth: `scripts/cx/cx-run.sh`, later `backends.py`)

`cx-run.sh` first scrubs the inherited environment (review C20): it unsets every exported `WINE*`, `D3DM_*`, `DXMT_*`, `MTL_*`, `CX_*`, `DYLD_*`, `VK_*` and `M5RUNNER_*` variable plus `SteamAppId` and `SteamGameId`, after reading its own knobs. That covers `WINESERVER` (`loader.c:748`: tried after the runtime's own `bin/wineserver`, so a stale value matters only when that exec fails, but then it would start another runtime's server), `WINESERVERSOCKET`, `WINELOADERNOEXEC`, `WINEPRELOADRESERVE`, `WINE_LARGE_ADDRESS_AWARE`, `WINENCPU`, `WINE_SIMULATE_WRITECOPY`, `WINEMSYNC_QLIMIT` and `WINE_DISABLE_NX_COMPAT`. It also covers the runner's `DXMT_CONFIG` (its `customVendorId=10de` would make DXMT report an NVIDIA GPU to steamwebhelper in rung L1), `VK_ICD_FILENAMES` and `DYLD_FALLBACK_LIBRARY_PATH`. Then it exports this table.

| Variable | Every cx process | Steam session (steam.exe and children) | D3DMetal game process |
|---|---|---|---|
| `WINEPREFIX` | `~/Games/prefixes/cx_prefix` | same | same |
| `WINEARCH` | `wow64`. Stops 32-bit programs relaunching through a phantom i386 loader (`loader.c:505-527`; values validated at `wine/dlls/ntdll/unix/server.c:1615-1620`) | same | same |
| `WINEMSYNC` | the session's value, `0` until M7.4 | `0` for UI sessions (Steam's CEF hangs under msync: Highball steam.json) | must equal the running wineserver's value; a mismatched client exits with "Server is running with WINEMSYNC but this process is not" (`wine/dlls/ntdll/unix/msync.c:587-600`) or, the other way round, "Failed bootstrap_look_up" (`msync.c:636`) |
| `CX_APPLEGPTK_LIBD3DSHARED_PATH` | realpath of `~/Games/sdk/gptk/<ver>/external/libd3dshared.dylib`; loaded only by processes whose main exe is not a Wine builtin | same (`--no-d3dshared` exists for A/B tests) | same |
| `ROSETTA_ADVERTISE_AVX`, `DOTNET_EnableWriteXorExecute` | `1`, `0` | same | same |
| `WINEDLLPATH_PREPEND` | unset | unset; rung L1 and L2 use the realpath of `~/Games/sdk/dxmt` | realpath of `~/Games/sdk/gptk/<ver>/wine`, optionally after an overlay (M8.3; hb-0003 splits the value on `:`) |
| `CX_ACTIVE_GRAPHICS_BACKEND` | unset | unset | `d3dmetal` |
| `WINEDLLOVERRIDES` | none | none | `d3d10,d3d11,d3d12,d3d12core,dxgi=b` plus profile extras. These names must never be `n`: a builtin-tagged file with native load order is refused (`loader.c:1655-1659`) |
| `MTL_HUD_ENABLED`, `MTL_HUD_LOG_ENABLED` | `0` | `0` | `1`, `1` while testing (Apple: the log needs the HUD enabled) |
| `D3DM_ENABLE_METALFX` | unset | unset | `1` only for DLSS profiles. Community reports say it also switches D3DMetal's DXGI vendor id from AMD (0x1002) to NVIDIA (0x10de): **ASSUMPTION**, settled by gate X6 (M8.2) |
| `SteamAppId`, `SteamGameId` | unset | unset | only for a Steamworks title launched directly, through `--steam-appid` (M8.4) |
| `WINEDEBUG` | `-all` for play, explicit channels for tests | | |
| Never set | `WINEESYNC` (CX has no esync), `WINEDLLPATH`, `CX_REPORT_REAL_USERNAME` (it changes GetUserNameA, which salts DPAPI and would break Steam's saved login), `DYLD_*`, `D3DM_MTL4` (no effect before macOS 27, metalfx research) | | |

### 2.4 Prefix rules and registry baseline (`cx_prefix`)
- `cx_prefix` is created by the cx runtime with `wineboot -i` in a clean environment: no `WINEDLLPATH_PREPEND`. As a result, system32 holds Wine's own d3d copies plus placeholders for `nvapi64`, `nvngx` and `atidxx64`. Right after `wineboot -i` the harness writes `disable` into `.update-timestamp`, stamps `.m5runner-runtime` with BUILDINFO line 1 and sets `ShowCrashDialog=0` (M5.2).
- **Automatic prefix updates are switched off (review C2, F8, D17).**
  - *Why.* Every new `bNNN` gets a new `share/wine/wine.inf` mtime: Wine's install tool parses `-p` but never preserves timestamps (`wine/tools/install.c:38, 151-163, 323`). wineboot treats any difference between that mtime and the prefix's `.update-timestamp` as stale. It tests for equality (`wine/programs/wineboot/wineboot.c:121-160`, at :138), so a rollback to an older build triggers an update too. The update runs inside `wineboot --init`, which ntdll starts from the first parentless process of every wineserver session, with that process's environment (`wine/dlls/ntdll/unix/env.c:1543-1600, 1886-1908`). With `WINEDLLPATH_PREPEND` set, wineboot copies DLLs from every `WINEDLLDIRn`, and the first copy wins (`env.c:1043-1049`, `wine/dlls/setupapi/fakedll.c:1081-1087`). The FakeDllsWin64 placeholders are processed before `Needs=BaseInstall`, and the handled list is cleared in between (`wine/dlls/setupapi/install.c:1151-1152, 1296-1297`). So all seven GPTK names, placeholders included, would become GPTK or DXMT copies in system32. That would happen in rung L1 (Steam on the DXMT prepend) and in any M5 or M8 re-run after a rebuild, where the D3DMetal program is the first process. The feasibility review verified this from source (former assumptions A8: the copy happens; A9: copies are byte-for-byte).
  - *What we do instead.*
    1. Right after `wineboot -i` (M4 `cx_smoke`, M5.2 `cx_prefix`, M8.0 `cx_dlss`, the runner's `ensure_prefix` in M9), write `disable` into `.update-timestamp`. wineboot then skips the automatic update (`wineboot.c:137`), while `wineboot -u` still forces it (`update_wineprefix( update )` at `wineboot.c:1713`).
    2. A build becomes current only through `build-wine-cx.sh promote` (M3.5). It takes the session lock, refuses while any process of the current build runs, backs up user data, snapshots `cx_prefix` and `cx_dlss` (instant APFS clones), switches the symlink, and in each of them runs `cx-run.sh -- wineboot -u` in plain mode, writes `disable` again, stamps `.m5runner-runtime`, re-stages the DLSS copies where the marker exists and runs `prefix-check.sh`. If anything fails after the switch, it switches back and restores the snapshots.
    3. `cx-run.sh` refuses `--d3dmetal` and `--dxmt` (exit 3) unless `.update-timestamp` reads `disable` and `.m5runner-runtime` equals the current BUILDINFO line 1.
    4. `steam.sh` and `er.sh` run `preflight_prefix` (Appendix A.9): the same two checks, plus `prefix-check.sh` (system32 `d3d10/d3d11/d3d12/d3d12core/dxgi` are cmp-equal to the runtime's own copies; `nvapi64/nvngx/atidxx64` read "Wine placeholder DLL") and the GPTK manifest. When a stamp differs, the fix is `promote`, never a session.
- The Windows user is `crossover` (CrossOver Hack 12735, `wine/dlls/advapi32/advapi.c:51-80`, `wine/dlls/shell32/shellpath.c:2635`). Profile paths are therefore `C:\users\crossover\...`, and Elden Ring saves go to `C:\users\crossover\AppData\Roaming\EldenRing\<SteamID64>`. No saves exist yet: the save folder in `default_prefix` is empty. `backup-userdata.sh` protects them from M7 on (4.7).
- Registry baseline, applied once in M6.1 through `cx-run.sh -- reg add ...`:
  - `HKCU\Software\Wine\AppDefaults\<exe>\DllOverrides` with `nvapi64=""` and `nvapi=""` for each of `steam.exe`, `steamwebhelper.exe`, `steamservice.exe` and `gameoverlayui64.exe` (review C26; steam-compat research). This keeps Apple's NVAPI out of every Steam process, and DXMT's too: the DXMT tree used by rungs L1 and L2 ships `nvapi64.dll` and `nvngx.dll`.
  - `HKCU\Software\Valve\Steam`: `GPUAccelWebViewsV3=dword:1`. With GPU web views off, Steam's window stays black on Wine 11 engines (highball#282, Highball steam.json)
  - `HKCU\Software\Wine\AppDefaults\eldenring.exe\DllOverrides`: `gameoverlayrenderer64=""` for the first runs (the soju overlay deadlock report)
  - delete `HKCU\Software\Microsoft\Windows\CurrentVersion\Run /v Steam` before every Steam start
  - `HKCU\Software\Wine\WineDbg`: `ShowCrashDialog=dword:0`, already set when the prefix is created (review C13). Crash dialogs then never block an unattended run, and winedbg prints to the log. Wine's own unattended test runner sets the same value (`wine/programs/winetest/main.c:425-437`); the default is on (`wine/programs/winedbg/intvar.h:41`)
  - DLSS profiles only, so not in M6.1: `HKLM\SOFTWARE\NVIDIA Corporation\Global\NGXCore FullPath=C:\Windows\System32` plus an empty `C:\ProgramData\NVIDIA\NGX\models\nvngx_config.txt`, both written by the M8.1 block: in `cx_dlss` before the sample, and in `cx_prefix` before the Wukong test (M8.4; R3-17)
  - only if the controller is not detected (review F6): `HKLM\System\CurrentControlSet\Services\WineBus` `"Enable SDL"=dword:1`. winebus reads its options from that service key (`wine/dlls/winebus.sys/main.c:498`), and "Enable SDL" already defaults to 1 (`main.c:1200`). Then A/B `"Map Controllers"` at 0 and 1 (`main.c:1213`), with `WINEDEBUG=+hid,+plugplay` to record which bus (`bus_iohid` or `bus_sdl`) enumerates the pad. `DisableHidraw` is not used: it only affects the Linux udev backend. The runner's own Sekiro controller `.reg` spells these names without spaces today, so winebus ignores it; 5.2 fixes it (R1-10)

### 2.5 Runner mapping and fallbacks
- **Until M9a:** `m5runner` does not know about `cx`. The harness scripts are the reference implementation.
- **M9a (opt-in):**
  - `config.py` gains `RUNTIME_DIRS["cx"] = ~/Games/sdk/wine-cx26`, `RUNTIME_PREFIXES["cx"] = "cx_prefix"`, and `RUNTIME_ENV["cx"]` holding the "every cx process" column of 2.3.
  - `launch` and `steam` take `--runtime {gptk,staging,cx}` and `--gptk VER`.
  - Hooks receive the effective prefix and runtime, so no `--runtime cx` launch can write into `gptk_prefix` or `default_prefix` (review C9).
  - `BACKEND_RUNTIME` is unchanged.
- **M9b (flip, only after F1-F4 pass):**
  - `BACKEND_RUNTIME["d3dmetal"]` and `BACKEND_RUNTIME["d3dmetal_gptk4"]` become `"cx"`, both with GPTK 4.0b3. `--gptk 3.0` selects the A/B tree.
  - GPTK 7.7 (`wine-gptk` + `gptk_prefix`) stays reachable with `--runtime gptk`, or by setting `runtime = "gptk"` in a profile, for any DX12 title that regresses on cx. Steam there remains broken, as today.
  - `dxmt`, `moltenvk_rt` and `xivmac` stay on Wine Staging 11.18 + `default_prefix`. Moving DXMT onto cx (`WINEDLLPATH_PREPEND=~/Games/sdk/dxmt`) is a later, optional experiment.
  - After Daniel merges, `m5runner create-apps elden-ring` regenerates Elden Ring.app (M10, review C10).

### 2.6 Decision record

| # | Decision | Choice and why | Alternative (when to switch) |
|---|---|---|---|
| D1 | PE toolchain | Homebrew mingw-w64 GCC 16.2 (`i386_CC`, `x86_64_CC`). frankea traced Steam's CM login stall to an llvm-mingw-built kernelbase.dll by module bisection, and Highball's `inputs.json` repeats the warning. Highball and steamplay built this tarball with Homebrew mingw in Sep-Oct 2026. winegcc finds `<target>-gcc` on `PATH`, so no toolchain patches are needed (`wine/tools/winegcc/winegcc.c:399-441`) | llvm-mingw 20261006 (`research/toolchain/dl`, sha256 `a7a19b11…ebf6`) in a separate tree with Gcenx patches 7-9 (`research/source-inventory/gcenx-wine-11.0-llvm-mingw_fixes.patch`, dry-run clean), keeping kernelbase.dll GCC-built. Use it only if GCC fails twice |
| D2 | Build style | Native arm64 `make`. The unix side is cross-compiled with `/usr/bin/clang -arch x86_64 --host=x86_64-apple-darwin --build=aarch64-apple-darwin`. Wine's own tools are an arm64 tree passed through `--with-wine-tools` (steamplay-mac on macOS 26.6; frankea notes that Rosetta tool storms load the Mac) | Run configure and make under `arch -x86_64` (athei, WineHQ CI) if the cross configure misdetects something |
| D3 | Unix arch | x86_64 only. The D3DMetal glue is `#if defined(__x86_64__)` (`wine/dlls/winemac.drv/d3dmetal.c:25`, `d3dmetal_objc.h:21`) and D3DMetal is x86_64-only | none |
| D4 | x86_64 libraries | Cross-built into `$CXB/deps` with `@rpath` ids, using steamplay's recipe | A: reuse Gcenx Staging 11.18's dylibs with rewritten ids. B: MacPorts with `build_arch x86_64` (needs sudo). x86_64 Homebrew is Tier 3 and nixpkgs x86_64-darwin is ending, so neither |
| D5 | GPTK placement | Separate versioned tree plus `WINEDLLPATH_PREPEND` per process (2.1) | Merge into `lib/wine` (rejected: it would put D3DMetal into Steam). The m5compat shim if hb-0003 ever conflicts |
| D6 | libd3dshared for all processes | Mirrors the CrossOver launcher (2.2). In practice only processes with a non-builtin main exe load it: Steam, games and the test programs | `--no-d3dshared` for Steam A/B; T11 and T12 record the baseline |
| D7 | 32-bit relaunch | `WINEARCH=wow64`, no patch (`loader.c:505-527`) | hb-0012 (also carries athei's x87 sidecar) |
| D8 | Windows username | Keep `crossover`. Fresh prefix, nothing to migrate, consistent with DPAPI | hb-0001 if a prefix must be shared with a stock-Wine runtime |
| D9 | Deployment target | `MACOSX_DEPLOYMENT_TARGET=14.0` (Gcenx, Highball, steamplay; D3DMetal 4.0b3 declares `LSMinimumSystemVersion` 14.0). SDK 26.5 has no `pipe2`, so a newer-API weak import is not a risk | 15.0 (athei) |
| D10 | Install | `make install-lib` into staging, then an immutable `bNNN` dir (assemble), then `promote`. `install` would add install-dev; CrossOver's `install-image` renames `bin/wine` (`wine/configure.ac:3773-3780`) | none |
| D11 | Wine Mono and Gecko | Install Mono 10.4.1 and Gecko 2.47.4, the versions pinned in `wine/dlls/appwiz.cpl/addons.c:47,59`. Avoids the blocking "install Mono?" prompt (Highball build.yml) | `CX_EXTRA_OVERRIDES='mscoree,mshtml='` during wineboot if the downloads fail |
| D12 | Sync | `WINEMSYNC=0` until M7 passes, then A/B for game sessions only | none |
| D13 | Steam renderer | Ladder L0-L7 (M6), ordered by evidence. Two recipes have direct evidence on CrossOver 26.3 builds of this tarball. Rung L1 is athei's: Steam's webhelper on DXMT with `--in-process-gpu` (compatdb `builtin.rs:116-131`, cx-26.3.0-9 builds). Rung L2 is Highball's: patch 0007 plus DXMT for Steam's processes, GPU web views on, GPU process out of process (Highball `steam.json`; patches `README.md:19, 52`; `inputs.json` pins this exact tarball) | headless sign-in (L6), then escalation (L7) |
| D14 | Version string | Annotated tag `winecx-26.3.0`, so that `wine --version` prints `git describe HEAD` (`wine/configure.ac:3789`; `git describe` ignores lightweight tags) | none |
| D15 | Prefix and Steam data | New `cx_prefix`, fresh Steam install, Elden Ring APFS-cloned in (AGENTS.md hard rule 1; review C8) | Copy `Program Files (x86)/Steam` from `gptk_prefix` (1.7 GB) to skip the 15-25 min first update, but never its native `bcrypt.dll` |
| D16 | Game launch | Launch `eldenring.exe` directly with the D3DMetal environment while Steam runs headless. Never use Steam's Play button, because the game would inherit Steam's environment | Later: per-exe selection in a cxcompatdb shim |
| D17 | Prefix updates | `.update-timestamp` reads `disable`; only `promote` runs `wineboot -u`, in plain mode (2.4) | Automatic updates (rejected: they copy prepended DLLs into system32) |
| D18 | Development checkout | Worktree `~/projects/m5-wine-runner-cx` on `feat/cx-runtime`, based on `fix/gptk-runtime-split` (PR #1, open). The `~/Applications` launchers keep running the stable checkout | Developing in the stable checkout (rejected: every double-click would run half-finished code, review C10) |
| D19 | Steam gates | S-core (S1, S6, S7, S8) gates M7; S-UI (S2-S5) gates only F1; S9 gates F1 and the M9b flip (review C6) | One S1-S8 block (rejected: a black UI would block the game, although the game needs only a ready client) |
| D20 | Steam readiness | `steam.sh` resets `HKCU\Software\Valve\Steam\ActiveProcess` `ActiveUser` and `pid` to 0 before each start, because the values survive a crash (R1-23). Ready = both non-zero again, a live `steam.exe` of this session, and, in online sessions, a `[Logged On,` line after the start offset. Offline sessions never log that line, so for them the registry is the only signal (review C7); `.cx-session` records the mode (`offline=1`), so readiness checks and restarts keep it (R3-1) | connection_log only (rejected: offline sessions never log it). Comparing `pid` with its pre-start value (rejected: a fresh wineserver hands out process ids in the same order every time, `wine/server/process.c:647-676`, so `steam.exe` can get the same id again and pass as stale) |
| D21 | Session concurrency | One Wine session at a time: `SESSION.lock` with owner, anchor pid, the anchor's start time and prefix; a lock is live only while that same process runs (R2-5, R2-10); nested steps pass `CX_SESSION_PARENT`; `cx-run.sh` refuses a `wineserver -k` that would end another session (exit 5). Sessions handed to Daniel have owners of their own (`steam-daniel`, `er-daniel`, `m84-daniel`) that agent scripts never end. The DLSS tests use their own prefix `cx_dlss`, and capture and the dialog watcher see only the session's own processes (4.9; R1-3, R1-12, R2-9) | Parallel sessions in separate prefixes (rejected: one runtime means shared PIDs for capture and the watcher, one GPU, and Daniel's open windows at stake) |

### 2.7 Patch series (`$REPO/patches/cx26.3/`, LGPL-2.1-or-later like Wine)

All patches are LGPL-2.1-or-later, like Wine: Highball's `NOTICE.md` says so for its series, and athei's and frankea's patches modify Wine and inherit its licence. M0.5 vendors them into the repo with `PROVENANCE.md` (source repository URL, commit, upstream path, full sha256), `SHA256SUMS` and a `README.md`. "Verified" means `git apply` succeeds in this order on the pristine tree. Three checks on 2026-10-20 agree: both reviewers' scratch clones, and the editor's scratch tree holding pristine copies of the 33 files the 22 patches touch.

Sources:
- **hb**: github.com/gauthierpiarrette/highball-engine at snapshot `fc628ae` (`research/build-recipes/highball-engine/patches`)
- **fk**: github.com/frankea/winecx-gptk at snapshot `d20cb7f`, the CrossOver 26.3 lane (`research/build-recipes/frankea-winecx-gptk-cx26-lane/patches`)
- **at**: github.com/athei/wine, branch `cx-26-patched`, commits as listed (`research/build-recipes/athei-wine-patches`)
- **up**: upstream Wine (gitlab.winehq.org/wine/wine), fetched through wine-mirror (`research/plan`)

| Order | File (repo name) | Source and commit | sha256 | Status | Purpose, or when to enable |
|---|---|---|---|---|---|
| 1 | `hb-0003-ntdll-winedllpath-prepend.patch` | hb, `patches/0003-…` (MacPorts GPTK patch 1005, unchanged) | `8a56c175…68dc9` | base | `WINEDLLPATH_PREPEND` (`:`-separated), searched before Wine's own dir |
| 2 | `hb-0006-kernelbase-per-exe-command-line-append.patch` | hb 0006 | `cda40f36…a7332b` | base | `HKCU\Software\Wine\AppDefaults\<exe>\CommandLineAppend` appended at CreateProcess (CEF switches that steam.exe would filter) |
| 3 | `fk-0001-ntdll-foreign-personality-routine.patch` | fk, `patches/0001-…` | `20b0fcda…37da` | base | Stops libunwind personality routines being called as SEH handlers. Measured in steamwebhelper: 255 collided unwinds in 70 s → 0 |
| 4 | `hb-0014-msync-unregister-early-return.patch` | hb 0014 | `09c46f06…158715` | base | Fixes an msync wineserver node leak in long sessions |
| 5 | `at-0005-kernelbase-debugger-std-handles.patch` | at `b41ea309af8d` "kernelbase: Preserve standard handles when starting debugger." | `71a5df00…a5cb` | base (review C4) | Crash backtraces of GUI programs (games, steamwebhelper, the test programs) go to the run log instead of a newly allocated console; today `start_debugger` sets only `STARTF_USESHOWWINDOW` (`wine/dlls/kernelbase/debug.c:650`). Changes nothing on a passing gate |
| 6 | `at-0010-dbghelp-dwarf-div-by-zero.patch` | at `e8fd146944f8` "dbghelp: Don't divide by zero when computing a DWARF location." | `6205c691…293a` | base (review C4) | winedbg no longer dies while printing a backtrace from our `-g` DWARF builds; Steam's steamerrorreporter64 triggers the bug |
| 7-10 | `hb-0008-macos-mirror-teb-fiberdata`, `hb-0009-macos-swap-fiberdata-and-qos-slot`, `hb-0011-macos-lasterror-in-gs-slot`, `hb-0016-macos-lasterror-callback-return-once` (`.patch`) | hb | `036980ab…`, `0fcd084e…`, `f9141f3f…`, `e9d86793…` | standby, a set | %gs-slot fiber/QoS/LastError fixes for CrossOver 26.3's pre-Wine-10.5 macOS %gs model. Use only on fiber-switch or LastError crash signatures. hb-0011 needs hb-0008 and hb-0009; hb-0016 needs hb-0011 |
| 11 | `hb-0013-ntdll-nx-compat-from-main-image-permanent-under-rosetta.patch` | hb 0013 | `a208a9b4…db7ab` | standby, A/B in M7.6 (review C3) | eldenring.exe statically imports `bink2w64.dll`, which lacks `NX_COMPAT` (DllCharacteristics 0x0040), so stock CX ntdll turns no-exec off for the whole game (`wine/dlls/ntdll/loader.c:1616-1621`) and Rosetta takes the fault-storm path (athei measured a 190x frame-time regression). Signature: `disabling no-exec because of L"bink2w64.dll"` (gate E9). athei ships the same fix as its patch 0002; take hb-0013 only (their contents differ) |
| 12 | `hb-0005-ntdll-yield-after-auto-event-set.patch` | hb 0005 | `bc2c02bb…a2e` | standby (review C25) | A hang at a loading screen with low CPU, under msync or with sync off (lost wake-ups when an auto-reset event is set twice under Rosetta) |
| 13 | `hb-0025-ntdll-threadpool-io-release-once.patch` | hb 0025 | `ff1e608b…8031` | standby (review C25) | `assert ioqueue.objcount`, or a crash in `threadpool.c` |
| 14 | `hb-0018-macos-commit-charge-is-the-footprint.patch` | hb 0018 | `c8ec9641…28b7` | standby (review C25) | The game warns about low memory (inflated commit charge) |
| 15 | `hb-0020-winemac-retina-horzres-not-doubled.patch` | hb 0020 | `77cffeb2…6dc6` | standby (review C25) | A cropped fullscreen game with `HKCU\Software\Wine\Mac Driver` `RetinaMode=y` (athei 0011 is the same fix) |
| 16 | `hb-0007-winemac-cross-process-child-swapchains.patch` | hb 0007 | `cd1fe231…d74d26` | standby (rungs L2, L3) | Wine bug 60263: a CEF GPU process presents into another process's window via CAContext/CALayerHost. Touches only `dlls/winemac.drv`, including the D3DMetal client surface, so re-run M5.3 after enabling it. Conflicts with at-0008 |
| 17 | `hb-0002-wined3d-auto-renderer-opengl-first.patch` | hb 0002 | `011e682a…` | standby | Prefer the registry knob first (`AppDefaults\<exe>\Direct3D\renderer=gl`, `wine/dlls/wined3d/wined3d_main.c:328-348, 465-480`) |
| 18 | `hb-0015-winecoreaudio-io-buffer-under-half-a-period.patch` | hb 0015 | `052b593e…` | standby | Fixes audio dropouts at 48 kHz |
| 19 | `hb-0017-kernelbase-getintegrateddisplaysize-stub.patch` | hb 0017 (upstream c68ed23672) | `4a1d36cf…` | standby | Missing export (Forza Horizon 6) |
| 20 | `up-c3a1bc86-winmm-hardcode-supported-formats.patch` | up `c3a1bc86134b` (Wine 11.5) | `e5b4196d…caac0b` | standby (was base; review F7) | Removes winmm format probing that can stall Steam's main loop (soju STEAM-GAMES.md item 11). Upstream hard-coded the formats only after three earlier commits (`8b1e971fb9ef`, `3eda8f91607d`, `bb465ced5a31`) made every format openable through AUTOCONVERTPCM. CrossOver 26.3 has none of them, so this patch alone would advertise formats that opening still checks with IsFormatSupported plus ACM (`wine/dlls/winmm/waveform.c:1124-1139`). Enable it only when a Steam stall shows the steamclient64 → winmm → mmdevapi IsFormatSupported stack, and then prefer backporting the whole chain in order, checked with `git apply --check` |
| 21 | `at-0001-winemac-run-cocoa-app-uaf.patch` | at `df416a601ed8` | `7e52f200…143c` | standby (review C4) | A window that draws but ignores all input (use-after-free race in `run_cocoa_app`) |
| 22 | `at-0008-winemac-destroy-window-races.patch` | at `2bfc0a54ffb7` | `bca4ac0a…3eff` | standby (review C4); never together with hb-0007 | A hang with threads parked in `macdrv_DestroyWindow` or `client_surface_release` (take a `spindump` of the hung PID): a lock-order deadlock between `win_data_mutex` and `surfaces_lock` around the CW HACK 22435 D3DMetal client surfaces. It conflicts with hb-0007 in `dlls/winemac.drv/window.c` near line 1334 (verified both ways), so enabling it with L2 or L3 needs a hand merge, kept as its own patch |

Each standby patch also applies alone on the base series, except hb-0011 and hb-0016 (their prerequisites above). In the series file, entries 7-22 are in the verified cumulative order; at-0008 applies after all others only while hb-0007 is off.

Not taken: hb-0001 (real user name, D8); hb-0012 (D7); athei 0002 (the same fix as hb-0013); hb-0010, hb-0019 and hb-0021 to hb-0024 (media, keychain, GLES, spatial-audio and app-package fixes, with no symptom in our targets); and the upstream clang BOOLEAN syscall wrappers (d1415ab2 + f43402cd). Those wrappers need a manual merge around `KeServiceDescriptorTable` (source-inventory); take them only if a crash points at a narrow syscall argument.

---

## 3. Milestones

Stage code (M1-M3) is the content of `scripts/cx/stages/<stage>.sh`. It runs only through `scripts/build-wine-cx.sh <stage>` (Appendix A.10), which logs to `$CXB/logs/<stage>.log`, stamps `$CXB/stamps/<stage>.ok`, keeps the Mac awake with `caffeinate`, and stops at the first failing stage. `build-wine-cx.sh` always runs as a background job of the agent's shell tool, with the stage log tailed (Conventions, R2-12). Inline blocks elsewhere follow the shell rules in Conventions, every long wait is wrapped in `scripts/cx/with-timeout.sh`, and every block that starts Wine processes directly begins with `source "$X/lib.sh"; begin_session <owner> [idle]`; a block that starts Wine only through `steam.sh` modes leaves the locking to them (4.9, R2-7).

### M0: Toolchain, worktree, patch series, harness, renderer tree (1-2 h)

M0.1 (Daniel approves; Daniel-queue item, M0.12) Install the arm64 Homebrew build tools. Nothing x86_64 comes from Homebrew.
```bash
brew install bison pkgconf ccache cmake ninja freetype mingw-w64
```

M0.2 Sanity checks:
```bash
/opt/homebrew/opt/bison/bin/bison --version | head -1     # bison (GNU Bison) 3.8.2 (keg-only; Apple's /usr/bin/bison 2.3 fails configure.ac:240-256)
x86_64-w64-mingw32-gcc --version | head -1                # x86_64-w64-mingw32-gcc (GCC) 16.2.0
i686-w64-mingw32-gcc --version | head -1                  # i686-w64-mingw32-gcc (GCC) 16.2.0
pkg-config --version; cmake --version | head -1; ninja --version; ccache --version | head -1
xcodebuild -version | head -1; xcrun --show-sdk-version   # Xcode 26.6 / 26.5
arch -x86_64 /usr/bin/true && echo rosetta-ok
echo "ac99c8ca4b3848f3e81784135f023df266b61c2345726ea55a50b3e030dd6872  $HOME/Games/src/crossover-sources-26.3.0.tar.gz" | shasum -a 256 -c -
```

M0.3 Record baselines for F6. `winemetal.so` is excluded because the runner's DXMT staging writes it into wine-staging (`src/m5runner/backends.py:224-232`). The Elden Ring tripwire guards `default_prefix`'s game files (review F16). The three dry runs are written out one by one: in zsh, a loop over `"witcher3 --backend dxmt"` would pass a single argument and corrupt the baseline (review C21). The pytest and dry-run baselines run in the stable checkout, whose tracked files they do not change.
```bash
mkdir -p ~/Games/logs/cx
(cd ~/Games/sdk && find wine-gptk wine-staging d3dmetal dxmt -type f ! -name winemetal.so -print0 | xargs -0 shasum -a 256) > ~/Games/logs/cx/baseline-sdk.sha256
(cd "$HOME/Games/prefixes/default_prefix/drive_c/Program Files (x86)/Steam/steamapps/common/Elden Ring/Game" \
  && shasum -a 256 eldenring.exe start_protected_game.exe steam_api64.dll steam_appid.txt) > ~/Games/logs/cx/baseline-er.sha256
cd ~/projects/m5-wine-runner && uv run pytest -q > ~/Games/logs/cx/baseline-pytest.txt 2>&1; tail -1 ~/Games/logs/cx/baseline-pytest.txt
{ uv run m5runner launch elden-ring --dry-run
  uv run m5runner launch witcher3 --backend dxmt --dry-run
  uv run m5runner launch sekiro --dry-run; } > ~/Games/logs/cx/baseline-dryrun.txt 2>&1
```

M0.4 Check the worktree and create the directories (review C10, D18). The worktree `~/projects/m5-wine-runner-cx` and the branch `feat/cx-runtime` were created with this plan's commit (PR #2). PR #1 (`fix/gptk-runtime-split`, https://github.com/dannydiaz04/m5-wine-runner/pull/1) was still open, so the branch stacks on it. The stable checkout stays on `fix/gptk-runtime-split`, so the `~/Applications/*.app` launchers keep running it.
```bash
[ -d ~/projects/m5-wine-runner-cx ] || git -C ~/projects/m5-wine-runner worktree add ~/projects/m5-wine-runner-cx feat/cx-runtime   # exists since the plan's commit
git -C ~/projects/m5-wine-runner-cx log -2 --oneline             # the plan commit on top of the tip of PR #1
mkdir -p ~/Games/build.noindex/cx26 ~/Games/tools ~/Games/sdk/gptk ~/Games/sdk/wine-cx26.builds ~/Games/logs/cx ~/Games/backups/cx
tmutil addexclusion ~/Games/build.noindex 2>/dev/null || true    # optional: keep build trees out of Time Machine
```

M0.5 Vendor the patch series into the repo with provenance. `research/` stays local; only these copies are committed.
```bash
R=~/projects/m5-wine-runner-cx/patches/cx26.3; RB=~/Games/src/research/build-recipes
H=$RB/highball-engine/patches; F=$RB/frankea-winecx-gptk-cx26-lane/patches; A=$RB/athei-wine-patches
mkdir -p "$R"
for n in 0003-ntdll-winedllpath-prepend 0006-kernelbase-per-exe-command-line-append 0014-msync-unregister-early-return \
         0008-macos-mirror-teb-fiberdata 0009-macos-swap-fiberdata-and-qos-slot 0011-macos-lasterror-in-gs-slot \
         0016-macos-lasterror-callback-return-once 0013-ntdll-nx-compat-from-main-image-permanent-under-rosetta \
         0005-ntdll-yield-after-auto-event-set 0025-ntdll-threadpool-io-release-once 0018-macos-commit-charge-is-the-footprint \
         0020-winemac-retina-horzres-not-doubled 0007-winemac-cross-process-child-swapchains \
         0002-wined3d-auto-renderer-opengl-first 0015-winecoreaudio-io-buffer-under-half-a-period \
         0017-kernelbase-getintegrateddisplaysize-stub; do
  cp "$H/$n.patch" "$R/hb-$n.patch"
done
cp "$F/0001-ntdll-foreign-personality-routine.patch" "$R/fk-0001-ntdll-foreign-personality-routine.patch"
cp "$A/0005-b41ea309af8d.patch" "$R/at-0005-kernelbase-debugger-std-handles.patch"
cp "$A/0010-e8fd146944f8.patch" "$R/at-0010-dbghelp-dwarf-div-by-zero.patch"
cp "$A/0001-df416a601ed8.patch" "$R/at-0001-winemac-run-cocoa-app-uaf.patch"
cp "$A/0008-2bfc0a54ffb7.patch" "$R/at-0008-winemac-destroy-window-races.patch"
cp ~/Games/src/research/plan/up-c3a1bc86-winmm-hardcode-supported-formats.patch "$R/"
(cd "$R" && shasum -a 256 *.patch > SHA256SUMS && wc -l < SHA256SUMS)      # 22
```
Then resolve the snapshot commits and prove that the local copies equal the published files (git blob ids):
```bash
hb=$(gh api repos/gauthierpiarrette/highball-engine/commits/fc628ae --jq .sha)
fk=$(gh api repos/frankea/winecx-gptk/commits/d20cb7f --jq .sha); echo "highball $hb  frankea $fk"
for f in "$R"/hb-*.patch; do u=${f##*/hb-}
  if [ "$(git hash-object "$f")" = "$(gh api "repos/gauthierpiarrette/highball-engine/contents/patches/$u?ref=$hb" --jq .sha)" ]; then echo "same $u"; else echo "DIFFERS $u"; fi
done
[ "$(git hash-object "$R/fk-0001-ntdll-foreign-personality-routine.patch")" = \
  "$(gh api "repos/frankea/winecx-gptk/contents/patches/0001-ntdll-foreign-personality-routine.patch?ref=$fk" --jq .sha)" ] && echo "same fk-0001"
for c in b41ea309af8d e8fd146944f8 df416a601ed8 2bfc0a54ffb7; do gh api "repos/athei/wine/commits/$c" --jq .sha; done
gh api -H 'Accept: application/vnd.github.patch' repos/wine-mirror/wine/commits/c3a1bc86134bd6ae4bd781f6ae79f98122ba5e98 | shasum -a 256   # e5b4196d...caac0b
```
If a line prints `DIFFERS` or a hash differs, stop: the research copy is not the published file. Re-fetch it from upstream and record the new hash.

Then write three files:
- `$R/series` (Appendix A.7).
- `$R/PROVENANCE.md`: one row per patch with the upstream repository URL, the full commit id printed above (athei: the commit itself), the upstream path, and the full sha256 from `SHA256SUMS`. The patch headers keep their authors' names as published upstream.
- `$R/README.md`: the licence (LGPL-2.1-or-later, like Wine; Highball `NOTICE.md`), attribution to Highball, frankea, athei and the Wine project, the verified apply order, the dependencies (hb-0011 needs hb-0008 and hb-0009, hb-0016 needs hb-0011, at-0008 conflicts with hb-0007), the enable signature of every standby patch (2.7), and the decision to keep up-c3a1bc86 in standby (review F7).

M0.6 Add the harness to the worktree: the sources of Appendix A, the stage files of M1-M3, `scripts/cx/downloads.sha256` and the test sources (A.12). The plan itself is already at `docs/WINE_CX_BUILD_PLAN.md`, and the four absolute `file:///Users/<name>/…` links in `AGENTS.md` (lines 140, 166, 182, 184) became relative links in the plan's commit (PR #2). In the M0.6 commit, add `tests/test_repo_hygiene.py` (5.3), so the hygiene test guards every later commit, including the BUILD_LOG excerpts of M0-M8 (R2-17). Then check the syntax with Apple's bash, run the hygiene test and build the window helper:
```bash
cd ~/projects/m5-wine-runner-cx
chmod +x scripts/build-wine-cx.sh scripts/cx/*.sh scripts/cx/stages/*.sh
for f in scripts/build-wine-cx.sh scripts/cx/*.sh scripts/cx/stages/*.sh; do /bin/bash -n "$f" || echo "SYNTAX $f"; done   # no output
uv run pytest -q tests/test_repo_hygiene.py                    # passes; it runs before every commit from now on (5.5) and scans new files too
xcrun swiftc -O -o ~/Games/tools/wine-windows scripts/cx/wine-windows.swift
~/Games/tools/wine-windows; echo "exit=$?"                     # prints nothing and exit=1 while no Wine window exists
~/Games/tools/wine-windows --session-check; echo "exit=$?"     # unlocked, exit=0 (4 while the screen is locked)
```

M0.7 (Daniel, one time)
1. Open System Settings > Privacy & Security > Screen & System Audio Recording.
2. Enable the terminal app the agent runs in.
3. Quit and reopen that terminal.

This lets `screencapture -l` capture Wine windows and lets CGWindowList report window titles.

M0.8 Create `docs/cx/BUILD_LOG.md` from the template in 4.2, including the Daniel queue table. Entry `C000` records the tool versions from M0.2 and `sw_vers -buildVersion`.

M0.9 Unattended preconditions (review C12). The plan runs for days without supervision. Four conditions break that today: macOS installs updates automatically (`AutomaticallyInstallMacOSUpdates = 1`), the system sleep timer is 1 minute (held off only by other processes' assertions), a locked screen breaks window capture, and macOS has no `timeout` command.

Daniel, once:
1. Open System Settings > General > Software Update, click the (i) next to Automatic Updates, and turn off "Install macOS updates". Turn it back on after M10.
2. Keep the lid open and the charger connected while long jobs run.

Agent checks:
```bash
defaults read /Library/Preferences/com.apple.SoftwareUpdate AutomaticallyInstallMacOSUpdates   # 0
pmset -g batt | head -1                                                                       # Now drawing from 'AC Power'
sw_vers -buildVersion                                                                         # 25F80 today; recorded in C000
~/Games/tools/wine-windows --session-check                                                    # unlocked
```
Harness rules that follow from this:
- Every long-running entry point (`build-wine-cx.sh`, `smoke.sh`, `er.sh`, `promote`, every `begin_session` block) starts `caffeinate -dimsu -w $$ &`. `steam.sh` binds it to the prefix's wineserver instead (`caffeinate -dimsu -w <server pid>`), because Steam keeps running after `steam.sh ui` or `silent` returns (R1-16).
- `with-timeout.sh` wraps every wait (it uses perl's `alarm`, which survives `exec`; exit 142 on timeout).
- `capture.sh` exits 4 on a locked screen, and capture or HUD gates then report INCONCLUSIVE, not FAIL.
- BUILDINFO and every `gates.txt` record the macOS build. A macOS change is a new variable: re-run M4 and M5.3 before comparing results.

M0.10 Build the GPTK renderer tree (formerly M5.1; moved here so that M4 already runs with libd3dshared in the environment, review F20, C19). Apple's files are not modified; the only change is Apple's documented rename.
```bash
G=~/Games/sdk/gptk/4.0b3; mkdir -p "$G"
ditto ~/Games/sdk/d3dmetal/external "$G/external"      # byte-identical to the DMG (metalfx research); ditto keeps symlinks and signatures
ditto ~/Games/sdk/d3dmetal/wine "$G/wine"
mv "$G/wine/x86_64-unix/nvngx-on-metalfx.so" "$G/wine/x86_64-unix/nvngx.so"            # GPTK 4.0b3 Read Me: MetalFX rename
mv "$G/wine/x86_64-windows/nvngx-on-metalfx.dll" "$G/wine/x86_64-windows/nvngx.dll"
xattr -drs com.apple.quarantine "$G"
codesign -v --strict "$G/external/D3DMetal.framework" && codesign -v "$G/external/libd3dshared.dylib" && echo signatures-ok
plutil -extract CFBundleShortVersionString raw "$G/external/D3DMetal.framework/Versions/A/Resources/version.plist"   # 4.0b3
ls -l "$G/wine/x86_64-unix"                            # 7 symlinks -> ../../external/libd3dshared.dylib
(cd "$G" && find . -type f ! -name MANIFEST.sha256 -print0 | xargs -0 shasum -a 256 > ../.MANIFEST.4.0b3.tmp && mv ../.MANIFEST.4.0b3.tmp MANIFEST.sha256)
(cd "$G" && shasum -a 256 -s -c MANIFEST.sha256) && echo manifest-ok
```
The manifest is written outside the tree and moved in, so it never hashes itself (review F9, C17).

The `.so` files must stay symlinks. libd3dshared finds `@rpath/D3DMetal.framework` through `LC_RPATH @loader_path`, so copies break it with "Failed to dlopen D3DMetal" (frankea/Whisky#163). In M9, `m5runner import-gptk` produces this same tree straight from the DMG. From here on `cx-run.sh` exports `CX_APPLEGPTK_LIBD3DSHARED_PATH` for every process, and it refuses to run (exit 2) without the tree unless `--no-d3dshared` is given (review C19).

M0.11 Build the test programs (review C1, C19, F18). Their sources live in `$REPO/scripts/cx/tests/` (Appendix A.12) and their binaries in `$CXB/tests/bin`, never in the repo; the hygiene test rejects `.exe` files.
```bash
T=~/projects/m5-wine-runner-cx/scripts/cx/tests; B=~/Games/build.noindex/cx26/tests/bin; mkdir -p "$B"
x86_64-w64-mingw32-gcc -O2 -static -o "$B/hello64.exe" "$T/hello.c"
i686-w64-mingw32-gcc -O2 -static -o "$B/hello32.exe" "$T/hello.c"
x86_64-w64-mingw32-gcc -O2 -static -Wall -o "$B/d3d12_clear.exe" "$T/d3d12_clear.c" -ld3d12 -ldxgi -ldxguid -luser32 -lgdi32
x86_64-w64-mingw32-gcc -O2 -static -Wall -o "$B/d3d11_clear.exe" "$T/d3d11_clear.c" -ld3d11 -ldxgi -ldxguid -luser32 -lgdi32
file "$B"/*.exe      # PE32+ executable (console) x86-64 for three of them; PE32 executable (console) Intel 80386 for hello32.exe
```
Why our own programs:
- The DLSS sample quits with a modal "Error" box when its NGX probe fails (`DemoMain.cpp:1311-1314`). M5.3 would run it without the NGX prerequisites and with MetalFX off, so an M5 gate built on it would blame a healthy D3DMetal (review C1).
- The clear programs need no shaders, no NGX and no NVAPI. They print the DXGI adapter identity, which settles the vendor question of gate X6.
- `hello64.exe` is a non-builtin PE, the only kind of process that loads libd3dshared (T11).

M0.12 First Daniel-queue request (review C23). Combine everything that needs Daniel early into one message: the brew installs (M0.1), the Screen Recording permission (M0.7), the macOS update setting (M0.9), the optional reference-runtime download (M6.0), the DLSS test titles with the benchmark install and benchmark run (M8.4), and time slots for the Steam sign-in (M6.3) and the Elden Ring play test (M7.3). The Steam UI session and the handed-over game run only inside those slots, so the agent can run its other Wine sessions (M8.0-M8.3, X6) outside them (4.9, R3-9). Give numbered steps for each, notify Daniel (a push notification where the agent has one, otherwise a chat message), and add the rows to the Daniel queue in BUILD_LOG.

Failure modes M0

| Symptom | Fix |
|---|---|
| A bottle download fails | `brew update`, then retry the formula. If Homebrew falls back to a source build, mingw-w64 takes much longer |
| A shell still finds bison 2.3 | The scripts put `/opt/homebrew/opt/bison/bin` first in `PATH` (env.sh). Check `command -v bison` after sourcing env.sh in `/bin/bash` |
| `swiftc` license error | `sudo xcodebuild -license accept` (ask Daniel), or run the helper interpreted with `xcrun swift scripts/cx/wine-windows.swift` |
| `gh api` rate limit or 404 | Retry later, or ask Daniel to run `gh auth login`. A 404 on a snapshot commit means the upstream history was rewritten: record the tarball's short id as the provenance and note it in PROVENANCE.md |
| A test program fails to compile in C | mingw-w64's widl headers return structs through an extra output parameter in C (A.12); check the installed `d3d12.h` and call the macro form it declares |

### M1: x86_64 dependencies (stages `fetch` and `deps`, 20-40 min)

This is steamplay-mac's recipe (`research/build-recipes/drustburn-steamplay-mac/scripts/build-deps.sh:16-144`), proven on Apple Silicon with macOS 26.6 and arm64 Homebrew only. Word lists are bash arrays, so the stage cannot depend on the shell's word splitting (review F11).

Run it as a background job and tail the stage log (R2-12): `scripts/build-wine-cx.sh all` (or `from deps`) in the background, then check `tail -20 ~/Games/build.noindex/cx26/logs/deps.log` between other work (never `tail -f` in a foreground call: it does not end). In the foreground, the 10-minute tool limit would kill the deps stage every time, and because each library starts with `rm -rf` of its build directory, it would never finish.

M1.1 `scripts/cx/stages/fetch.sh` (pins in Appendix A.7). SteamSetup.exe is fetched here so that the M6 install has a recorded input. Valve publishes no checksum and replaces the file over time, so its hash goes into BUILD_LOG instead of a pin (review F13).
```bash
#!/bin/bash
# stage fetch: pinned downloads (checksums in scripts/cx/downloads.sha256); SteamSetup.exe is recorded, not pinned
set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd -P)/env.sh"
D="$CXB/downloads"; mkdir -p "$D"; cd "$D"
for f in nettle-3.10.2.tar.gz SDL2-2.32.10.tar.gz; do      # already hash-checked by the toolchain research
  [ -f "$f" ] || cp "$HOME/Games/src/research/toolchain/dl/$f" . 2>/dev/null || true
done
[ -f nettle-3.10.2.tar.gz ] || curl -fL -o nettle-3.10.2.tar.gz https://ftpmirror.gnu.org/gnu/nettle/nettle-3.10.2.tar.gz
[ -f SDL2-2.32.10.tar.gz ] || curl -fL -o SDL2-2.32.10.tar.gz https://github.com/libsdl-org/SDL/releases/download/release-2.32.10/SDL2-2.32.10.tar.gz
[ -f MoltenVK-1.4.2-macos.tar ] || curl -fL -o MoltenVK-1.4.2-macos.tar https://github.com/KhronosGroup/MoltenVK/releases/download/v1.4.2/MoltenVK-macos.tar
[ -f wine-mono-10.4.1-x86.tar.xz ] || curl -fLO https://dl.winehq.org/wine/wine-mono/10.4.1/wine-mono-10.4.1-x86.tar.xz
for a in x86 x86_64; do
  [ -f "wine-gecko-2.47.4-$a.tar.xz" ] || curl -fLO "https://dl.winehq.org/wine/wine-gecko/2.47.4/wine-gecko-2.47.4-$a.tar.xz"
done
shasum -a 256 -c "$REPO/scripts/cx/downloads.sha256"
[ -f SteamSetup.exe ] || curl -fL -o SteamSetup.exe https://cdn.akamai.steamstatic.com/client/installer/SteamSetup.exe
shasum -a 256 SteamSetup.exe | tee "$CXB/logs/steamsetup.sha256"   # Valve publishes no checksum: copy this line into BUILD_LOG
```
**ASSUMPTION:** the Gecko checksums come from frankea's workflow, because dl.winehq.org publishes none; the Mono and MoltenVK pins match GitHub's published digests (feasibility review). `shasum -c` catches a mismatch. If one fails, re-check against dl.winehq.org and record the result in BUILD_LOG.

M1.2 `scripts/cx/stages/deps.sh`. Each library goes into `$DEPS` with an `@rpath` id, and gates DEP1-DEP4 end the stage:
```bash
#!/bin/bash
# stage deps: x86_64 gmp, nettle, gnutls, freetype, SDL2 and MoltenVK into $DEPS with @rpath ids (steamplay-mac recipe)
set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd -P)/env.sh"
W="$CXB/deps-src"; DL="$CXB/downloads"; mkdir -p "$W" "$DEPS/lib"
export CC="/usr/bin/clang -arch x86_64" CXX="/usr/bin/clang++ -arch x86_64" CFLAGS=-O2 CXXFLAGS=-O2
export CPPFLAGS="-I$DEPS/include" LDFLAGS="-L$DEPS/lib -Wl,-headerpad_max_install_names"
export PKG_CONFIG_LIBDIR="$DEPS/lib/pkgconfig" PKG_CONFIG_PATH=          # never see arm64 Homebrew .pc files
H=(--host=x86_64-apple-darwin --build=aarch64-apple-darwin "--prefix=$DEPS" --enable-shared --disable-static)
CM=(-G Ninja -DCMAKE_BUILD_TYPE=Release "-DCMAKE_INSTALL_PREFIX=$DEPS" -DCMAKE_OSX_ARCHITECTURES=x86_64
    -DCMAKE_OSX_DEPLOYMENT_TARGET=14.0 -DCMAKE_POLICY_VERSION_MINIMUM=3.5)
fix_ids() {
  local f id d
  for f in "$DEPS"/lib/*.dylib; do
    [ -e "$f" ] && [ ! -L "$f" ] || continue
    id=$(otool -D "$f" | tail -1); install_name_tool -id "@rpath/${id##*/}" "$f"
    for d in $(otool -L "$f" | awk 'NR>1{print $1}' | /usr/bin/grep "^$DEPS/lib/" || true); do
      install_name_tool -change "$d" "@rpath/${d##*/}" "$f"
    done
    install_name_tool -add_rpath @loader_path "$f" 2>/dev/null || true
    codesign -f -s - "$f"
  done
}
# gmp 6.3.0 from the tarball (cp -p keeps mtimes so autotools do not try to regenerate)
rm -rf "$W/gmp"; cp -Rp "$CXSRC/gnutls/gmp" "$W/gmp"
(cd "$W/gmp" && ./configure "${H[@]}" --disable-assembly && make -j"$JOBS" && make install); fix_ids
# nettle 3.10.2 release tarball (the CrossOver copy ships configure.ac only, no configure/Makefile.in)
rm -rf "$W/nettle"; mkdir "$W/nettle"; tar -xzf "$DL/nettle-3.10.2.tar.gz" -C "$W/nettle" --strip-components=1
(cd "$W/nettle" && ./configure "${H[@]}" "--libdir=$DEPS/lib" --disable-documentation --disable-openssl --disable-assembler \
   && make -j"$JOBS" && make install); fix_ids
# gnutls 3.8.3 from the tarball; *_LIBS must be single words (gnutls m4/hooks.m4:74,83 tests them unquoted)
rm -rf "$W/gnutls"; cp -Rp "$CXSRC/gnutls/gnutls" "$W/gnutls"
(cd "$W/gnutls" && ./configure "${H[@]}" --with-included-libtasn1 --with-included-unistring --without-p11-kit --without-idn \
   --without-brotli --without-zstd --without-tpm --without-tpm2 --disable-doc --disable-tests --disable-tools --disable-cxx \
   --disable-nls --disable-guile --disable-libdane --disable-full-test-suite --disable-gost \
   GMP_LIBS=-lgmp NETTLE_LIBS=-lnettle HOGWEED_LIBS=-lhogweed && make -j"$JOBS" && make install); fix_ids
# freetype 2.13.3 (tarball) and SDL2 2.32.10 via CMake 4 (the policy flag is needed for older CMakeLists)
rm -rf "$W/freetype"; cp -Rp "$CXSRC/freetype" "$W/freetype"
(cd "$W/freetype" && cmake -S . -B build "${CM[@]}" -DBUILD_SHARED_LIBS=ON -DFT_DISABLE_HARFBUZZ=ON -DFT_DISABLE_PNG=ON \
   -DFT_DISABLE_BROTLI=ON -DFT_DISABLE_BZIP2=ON -DFT_REQUIRE_ZLIB=ON && cmake --build build && cmake --install build); fix_ids
rm -rf "$W/SDL2"; mkdir "$W/SDL2"; tar -xzf "$DL/SDL2-2.32.10.tar.gz" -C "$W/SDL2" --strip-components=1
(cd "$W/SDL2" && cmake -S . -B build "${CM[@]}" -DSDL_SHARED=ON -DSDL_STATIC=OFF -DSDL_TEST=OFF \
   && cmake --build build && cmake --install build); fix_ids
# MoltenVK 1.4.2 prebuilt; must exist at configure time (wine/dlls/win32u/vulkan.c:3009 uses SONAME_LIBVULKAN unguarded)
rm -rf "$W/moltenvk"; mkdir "$W/moltenvk"; tar -xf "$DL/MoltenVK-1.4.2-macos.tar" -C "$W/moltenvk"
mvk=$(find "$W/moltenvk" -path '*dynamic/dylib/macOS/libMoltenVK.dylib' | head -1)
lipo -thin x86_64 "$mvk" -output "$DEPS/lib/libMoltenVK.dylib" 2>/dev/null || cp "$mvk" "$DEPS/lib/libMoltenVK.dylib"
install_name_tool -id @rpath/libMoltenVK.dylib "$DEPS/lib/libMoltenVK.dylib"; codesign -f -s - "$DEPS/lib/libMoltenVK.dylib"
# Gates DEP1-DEP4: the stage fails on any FAIL
bad=0; n=0
for f in "$DEPS"/lib/*.dylib; do
  [ -L "$f" ] && continue; n=$((n + 1))
  a=$(lipo -archs "$f"); id=$(otool -D "$f" | tail -1)
  case "$a $id" in "x86_64 @rpath/"*) echo "DEP1 $a $id" ;; *) echo "FAIL DEP1 $f: $a $id"; bad=1 ;; esac
done
[ "$n" -eq 7 ] || { echo "FAIL DEP1: expected 7 real dylibs, found $n"; bad=1; }
leaks=$(for f in "$DEPS"/lib/*.dylib; do otool -L "$f" | /usr/bin/grep -v ':$'; done | /usr/bin/grep -E "$DEPS|/opt/homebrew|/usr/local" || true)
[ -z "$leaks" ] || { echo "FAIL DEP2:"; echo "$leaks"; bad=1; }
for f in "$DEPS"/lib/*.dylib; do codesign -v "$f" 2>/dev/null || { echo "FAIL DEP3 $f"; bad=1; }; done
ls "$DEPS"/include/freetype2/ft2build.h "$DEPS"/include/gnutls/gnutls.h "$DEPS"/include/SDL2/SDL.h > /dev/null || { echo "FAIL DEP4"; bad=1; }
[ "$bad" = 0 ] && echo "PASS DEP1-DEP4"
exit "$bad"
```
Gates DEP1-DEP4 (the stage fails on any FAIL):
```text
DEP1 seven real (non-symlink) dylibs, each "x86_64 @rpath/...": libfreetype.6, libgmp.10, libgnutls.30, libhogweed.6,
     libMoltenVK, libnettle.8, libSDL2-2.0.0
DEP2 no otool -L dependency points into $DEPS, /opt/homebrew or /usr/local. The header lines of otool -L (the file's own
     path, and one per architecture in a universal file) end with ':' and are dropped before the grep (review F3)
DEP3 every dylib passes codesign -v
DEP4 ft2build.h, gnutls/gnutls.h and SDL2/SDL.h exist under $DEPS/include
```

Failure modes M1

| Symptom | Diagnosis | Fix |
|---|---|---|
| gmp: "could not find a working compiler" | CC lacks `-arch x86_64` or the SDK is not found | Check that `env.sh` exports `SDKROOT` and that `CC` is exactly as above |
| gnutls: "Libtasn1 4.9 was not found" | bundled copy not selected | `--with-included-libtasn1` (present above) |
| gnutls: nettle/hogweed not found | a `*_LIBS` value contains a space | Use single words; `-L` already comes from `LDFLAGS` |
| `aclocal-1.16: command not found` | mtimes were not preserved | Use `cp -Rp`. As a last resort, ask before `brew install automake autoconf libtool`, then run `autoreconf -fi` |
| freetype: "Compatibility with CMake < 3.5 has been removed" | CMake 4 | `-DCMAKE_POLICY_VERSION_MINIMUM=3.5` (included above) |
| DEP1 shows `x86_64 arm64` for libMoltenVK | `lipo -thin` failed and the universal file was copied | Check the MoltenVK tarball layout, thin it by hand, then `build-wine-cx.sh from deps` |
| DEP2 shows an absolute path | an id was not rewritten | Re-run the stage; inspect that dylib's own `otool -L` |
| Still blocked after 2 h | — | **Fallback A**: copy (never move) `~/Games/sdk/wine-staging/lib/*.dylib` into `$DEPS/lib` and run `install_name_tool -id @rpath/<versioned leaf>` on `libfreetype.6` and `libgnutls.30`. Their ids lack a slash, which breaks configure's SONAME sed (`wine/aclocal.m4:61-87`). Take headers from the tarball, generating `gnutls.h` from `gnutls.h.in` (research/source-inventory). **Fallback B**: MacPorts with `build_arch x86_64` (needs sudo; Daniel decides) |

### M2: Source tree, native tools, configure (stages `src`, `tools`, `configure`; 10-20 min)

M2.1 `scripts/cx/stages/src.sh`: a git-tracked working copy with the active series. A patch that fails `git apply --check` stops the stage with its name, and the commit count must equal the number of active series lines, so `src.ok` can never be stamped on a partly patched tree (review F2).
```bash
#!/bin/bash
# stage src: git-tracked copy of the pristine wine tree plus every active line of patches/cx26.3/series
set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd -P)/env.sh"
S="$REPO/patches/cx26.3"
(cd "$S" && shasum -a 256 -s -c SHA256SUMS) || { echo "FAIL: patches/cx26.3/SHA256SUMS mismatch" >&2; exit 1; }
G() { git -C "$SRC" -c user.name=m5runner -c user.email=m5runner@localhost "$@"; }
rm -rf "$SRC"; cp -Rp "$CXSRC/wine" "$SRC"
G init -q; G add -A; G commit -qm "CrossOver 26.3.0 wine, pristine (tarball sha256 ac99c8ca...6872)"
G tag -a winecx-26.3.0 -m "CrossOver 26.3.0 pristine"        # annotated: wine/configure.ac:3789 runs 'git describe HEAD'
n=0
while read -r p; do
  G apply --check "$S/$p" || { echo "FAIL: $p does not apply on top of the previous entries" >&2; exit 1; }
  G apply "$S/$p"; G add -A; G commit -qm "$p"; n=$((n + 1))
done < <(/usr/bin/grep -v '^[[:space:]]*#' "$S/series" | /usr/bin/grep .)
[ "$(G rev-list --count winecx-26.3.0..HEAD)" -eq "$n" ] || { echo "FAIL: commit count is not $n" >&2; exit 1; }
echo "applied $n patches: $(G describe HEAD)"        # base series: winecx-26.3.0-6-g<sha>
```

M2.2 `scripts/cx/stages/tools.sh`: a native arm64 tree.
```bash
#!/bin/bash
# stage tools: native arm64 Wine tools tree. --enable-archs only satisfies configure's PE-compiler check;
# only __tooldeps__ is built (frankea build.yml).
set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd -P)/env.sh"
rm -rf "$TOOLS"; mkdir -p "$TOOLS"; cd "$TOOLS"
"$SRC/configure" --enable-archs=i386,x86_64 --disable-tests --with-freetype \
  --without-x --without-wayland --without-gnutls --without-sdl --without-vulkan --without-gstreamer --without-ffmpeg \
  --without-coreaudio --without-opencl --without-cups --without-pcap --without-usb --without-inotify --without-krb5 \
  --without-gssapi --without-netapi --without-capi --without-sane --without-v4l2 --without-pulse --without-alsa \
  --without-oss --without-dbus --without-udev \
  CC="ccache /usr/bin/clang" CXX="ccache /usr/bin/clang++" CFLAGS="-O2 -g0" \
  FREETYPE_CFLAGS="-I/opt/homebrew/opt/freetype/include/freetype2" FREETYPE_LIBS="-L/opt/homebrew/opt/freetype/lib -lfreetype"
make -j"$JOBS" __tooldeps__
mkdir -p nls && for f in "$SRC"/nls/*.nls; do ln -sf "$f" nls/; done     # wrc reads <tools>/nls (wine/tools/tools.h get_nlsdir)
case "$(file tools/winebuild/winebuild)" in *arm64*) ;; *) echo "FAIL: winebuild is not arm64" >&2; exit 1 ;; esac
test -r nls/locale.nls && echo tools-ok
```

M2.3 `scripts/cx/stages/configure.sh`: x86_64 host, i386 + x86_64 PE, with gates CFG1-CFG4 at the end.
```bash
#!/bin/bash
# stage configure: x86_64 host, i386 + x86_64 PE. Never pass --with-opengl (the EGL check becomes fatal, configure.ac:1250-1257).
set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd -P)/env.sh"
rm -rf "$BUILD"; mkdir -p "$BUILD"; cd "$BUILD"
PKG_CONFIG_LIBDIR="$DEPS/lib/pkgconfig" PKG_CONFIG_PATH= "$SRC/configure" \
  --prefix="$STAGE" --host=x86_64-apple-darwin --build=aarch64-apple-darwin --with-wine-tools="$TOOLS" \
  --enable-archs=i386,x86_64 --with-mingw --disable-tests --disable-winemenubuilder --disable-winebth_sys \
  --with-coreaudio --with-freetype --with-gnutls --with-sdl --with-vulkan \
  --without-x --without-wayland --without-fontconfig --without-alsa --without-pulse --without-oss --without-capi \
  --without-cups --without-dbus --without-gphoto --without-sane --without-udev --without-usb --without-v4l2 \
  --without-krb5 --without-gssapi --without-netapi --without-pcap --without-gstreamer --without-ffmpeg --without-inotify \
  CC="ccache /usr/bin/clang -arch x86_64" CXX="ccache /usr/bin/clang++ -arch x86_64" OBJC="ccache /usr/bin/clang -arch x86_64" \
  i386_CC="ccache i686-w64-mingw32-gcc" x86_64_CC="ccache x86_64-w64-mingw32-gcc" \
  CFLAGS="${CX_CFLAGS:--O2 -g}" CROSSCFLAGS="${CX_CROSSCFLAGS:--O2 -g}" CPPFLAGS="-I$DEPS/include" \
  LDFLAGS="-L$DEPS/lib -Wl,-rpath,@loader_path/../.. -Wl,-headerpad_max_install_names" \
  PKG_CONFIG=/opt/homebrew/bin/pkg-config \
  FREETYPE_CFLAGS="-I$DEPS/include/freetype2" FREETYPE_LIBS="-L$DEPS/lib -lfreetype" \
  GNUTLS_CFLAGS="-I$DEPS/include" GNUTLS_LIBS="-L$DEPS/lib -lgnutls" \
  SDL2_CFLAGS="-I$DEPS/include/SDL2 -D_THREAD_SAFE" SDL2_LIBS="-L$DEPS/lib -lSDL2" \
  ac_cv_lib_soname_MoltenVK=libMoltenVK.dylib
# Gates CFG1-CFG4: the stage fails on any FAIL
bad=0
for s in SONAME_LIBFREETYPE SONAME_LIBGNUTLS SONAME_LIBSDL2 SONAME_LIBVULKAN; do
  line=$(/usr/bin/grep -E "#define $s " include/config.h || true)
  if [ -n "$line" ]; then echo "CFG1 $line"; else echo "FAIL CFG1 $s missing"; bad=1; fi
done
[ "$(/usr/bin/grep -cE '^PE_ARCHS *= *i386 x86_64$' Makefile || true)" = 1 ] || { echo "FAIL CFG2 PE_ARCHS"; bad=1; }
[ "$(/usr/bin/grep -cE '^WINELOADER_LDFLAGS.*-no_huge' Makefile || true)" -ge 1 ] || { echo "FAIL CFG3 no -no_huge"; bad=1; }
[ "$(/usr/bin/grep -cE '^(i386|x86_64)_CC *= *ccache [a-z0-9_]+-w64-mingw32-gcc$' Makefile || true)" = 2 ] || { echo "FAIL CFG4 PE compilers"; bad=1; }
[ "$bad" = 0 ] && echo "PASS CFG1-CFG4"
exit "$bad"
```
- The `--with-*` flags act as gates: configure fails instead of silently dropping a feature (`wine/aclocal.m4:347-353`).
- The rpath `@loader_path/../..` lets `lib/wine/x86_64-unix/*.so` find `lib/*.dylib`. A leaf-name `dlopen` searches the caller's `LC_RPATH` (`man dlopen`, verified on this Mac).
- `CX_CFLAGS` and `CX_CROSSCFLAGS` are the knobs the M3 failure table uses; both default to `-O2 -g`.

Gates CFG1-CFG4 (the stage fails on any FAIL):
```text
CFG1 include/config.h defines SONAME_LIBFREETYPE "libfreetype.6.dylib", SONAME_LIBGNUTLS "libgnutls.30.dylib",
     SONAME_LIBSDL2 "libSDL2-2.0.0.dylib" and SONAME_LIBVULKAN "libMoltenVK.dylib"
CFG2 Makefile: PE_ARCHS = i386 x86_64
CFG3 Makefile: WINELOADER_LDFLAGS contains -no_huge, so no preloader is needed (configure.ac:945-959)
CFG4 Makefile: i386_CC and x86_64_CC are the two "ccache ...-w64-mingw32-gcc" lines
```

Failure modes M2

| Symptom | Diagnosis | Fix |
|---|---|---|
| "FAIL: patches/cx26.3/SHA256SUMS mismatch" | a patch file changed | `git -C $REPO diff patches/`; restore it, or record the change as a new patch with provenance |
| "FAIL: <patch> does not apply" | wrong tree, or a standby patch enabled without its prerequisite | Check the tarball checksum and the dependencies in 2.7 (hb-0011 needs hb-0008 and hb-0009; hb-0016 needs hb-0011; at-0008 conflicts with hb-0007) |
| `wine --version` later prints `wine-11.0` | the tag is lightweight | `git tag -a` (D14) |
| tools configure: "PE cross-compilation is required for aarch64" | arch list missing | Keep `--enable-archs=i386,x86_64` in the tools tree |
| "bison ... too old" or a `%define parse.error` failure | Apple's bison 2.3 is on PATH | env.sh PATH order |
| "you must use the --with-wine-tools option" or "Wine tools have not yet been built" | tools stage incomplete | `build-wine-cx.sh from tools` |
| FAIL CFG1 | a library link test failed | `/usr/bin/grep -n -B2 -A20 'checking for -lfreetype' config.log`. An arm64 library means `PKG_CONFIG_LIBDIR` or `LDFLAGS` is wrong. For MoltenVK keep `ac_cv_lib_soname_MoltenVK` |
| FAIL CFG3 | the linker refused `-no_huge` | `ld -v` must report ld-1267 (Xcode 26.6). The probe `research/toolchain/probe/t_nohuge` linked fine |
| "no suitable PE compiler for i386" | `i686-w64-mingw32-gcc` not on PATH | `brew list mingw-w64`; PATH contains `/opt/homebrew/bin` |

### M3: Build, assemble, verify, promote (stages `make`, `install`, `assemble`, `verify`, `promote`; cold 15-30 min, incremental 2-5 min)

Run every `build-wine-cx.sh` call of M3 (`all`, `from <stage>`, `iter`, `promote`) as a background job of the shell tool and tail the stage log (Conventions, R2-12). A cold make takes 15-30 minutes, and promote's own timeouts add up to about 52 minutes in the worst case (300 + 300 + 120 s for its smoke test, then up to 900 + 300 s per promoted prefix). Never end a running promote with SIGKILL: bash runs the EXIT trap that rolls a failed promote back on SIGTERM, but not on SIGKILL (4.8 step 4 recovers from that).

M3.1 `scripts/cx/stages/make.sh`. It refuses to build from a source tree with uncommitted edits, because neither BUILDINFO nor `wine --version` (`git describe` without `--dirty`) would show them (review C22).
```bash
#!/bin/bash
# stage make: refuses a dirty source tree, because BUILDINFO and 'wine --version' would not show uncommitted edits
set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd -P)/env.sh"
[ -z "$(git -C "$SRC" status --porcelain)" ] || { echo "FAIL: $SRC has uncommitted changes; commit them as a patch first" >&2; exit 1; }
make -C "$BUILD" -j"$JOBS"
ccache -s | head -12
```

M3.2 `scripts/cx/stages/install.sh`. Use `install-lib`, not `install` (D10). Make's own exit status decides the stage, because a `| tail` would hide a failed install (review F2).
```bash
#!/bin/bash
# stage install: 'make install-lib', not 'install' (D10); make's own exit status decides
set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd -P)/env.sh"
rm -rf "$STAGE"
make -C "$BUILD" -j"$JOBS" install-lib > "$CXB/logs/install-lib.log" 2>&1 || { tail -40 "$CXB/logs/install-lib.log"; exit 1; }
echo "installed into $STAGE"
```

M3.3 `scripts/cx/stages/assemble.sh`: an immutable build directory, not yet current (review C5).
```bash
#!/bin/bash
# stage assemble: immutable bNNN build dir from the staged install. It does NOT switch the runtime; promote does.
set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd -P)/env.sh"
mkdir -p "$RT_ROOT"
last=$(find "$RT_ROOT" -maxdepth 1 -type d -name 'b[0-9][0-9][0-9]-*' | sed -E 's#.*/b([0-9]{3})-.*#\1#' | sort -n | tail -1)
BID="b$(printf %03d $((10#${last:-0} + 1)))-$(git -C "$SRC" describe HEAD)"; B="$RT_ROOT/$BID"   # 10#: '008' is not octal
[ ! -e "$B" ] || { echo "refusing to overwrite $B" >&2; exit 1; }
mkdir -p "$B" && ditto "$STAGE" "$B" && cp -a "$DEPS"/lib/*.dylib "$B/lib/"
[ -e "$B/bin/wine" ] || ln -s ../lib/wine/x86_64-unix/wine "$B/bin/wine"   # cross builds never configure tools/wine (aclocal.m4:325)
mkdir -p "$B/share/wine/mono" "$B/share/wine/gecko"
tar -xJf "$CXB/downloads/wine-mono-10.4.1-x86.tar.xz" -C "$B/share/wine/mono"
for a in x86 x86_64; do tar -xJf "$CXB/downloads/wine-gecko-2.47.4-$a.tar.xz" -C "$B/share/wine/gecko"; done
if [ "${CX_BUNDLE_DXMT:-0}" = 1 ]; then          # winemetal fallback only (M6 rung L1, review F12): DXMT's winemetal inside our own build
  for a in x86_64 i386; do cp -p "$HOME/Games/sdk/dxmt/$a-windows/winemetal.dll" "$B/lib/wine/$a-windows/"; done
  cp -p "$HOME/Games/sdk/dxmt/x86_64-unix/winemetal.so" "$B/lib/wine/x86_64-unix/"
fi
mkdir -p "$B/dSYM"          # unix-side symbols survive later rebuilds of $BUILD
for m in ntdll win32u winemac; do
  xcrun dsymutil "$B/lib/wine/x86_64-unix/$m.so" -o "$B/dSYM/$m.so.dSYM" || echo "warn: no dSYM for $m"
done
find "$B/bin" "$B/lib" -type f \( -name '*.so' -o -name '*.dylib' -o -name wine -o -name wineserver \) -print0 \
  | xargs -0 -n 64 codesign -f -s -
{ echo "$BID"
  echo "macos $(sw_vers -productVersion) ($(sw_vers -buildVersion)), SDK $(xcrun --show-sdk-version)"
  x86_64-w64-mingw32-gcc --version | head -1; /usr/bin/clang --version | head -1
  echo "bundled-dxmt=${CX_BUNDLE_DXMT:-0}"
  echo "series:"; git -C "$SRC" log --reverse --format='  %s' winecx-26.3.0..HEAD; } > "$B/BUILDINFO"
echo "$BID" > "$CXB/stamps/assembled.id"
echo "assembled $BID (not current until promote)"
```
- Build numbers continue from the highest existing index. Counting directories would reuse a number after housekeeping deleted old builds, and `ls` on an empty glob under `set -euo pipefail` killed the first run (review F1, reproduced with `/bin/bash` 3.2.57). The `10#` prefix stops bash reading `008` as octal.
- The stage refuses to overwrite an existing directory, and it never touches `~/Games/sdk/wine-cx26`.
- `dSYM/` keeps the unix-side symbols of ntdll, win32u and winemac, so crash reports of older builds can still be symbolicated after `$BUILD` is rebuilt (review C22).
- Ad-hoc signing matches Gcenx's runtimes: no hardened runtime, no entitlements. Unsigned x86_64 code also runs under Rosetta (toolchain research). Never strip the unix `.so` files beyond `strip -x`, because `macdrv_functions` and `prepend_dll_path` must stay exported.
- `CX_BUNDLE_DXMT=1` exists only for the rung-L1 fallback in M6.

M3.4 `scripts/cx/stages/verify.sh` runs `scripts/cx/verify-runtime.sh` (Appendix A.11) on the build that assemble just made, not on the current runtime. It prints PASS or FAIL for each gate and exits 1 on any FAIL. It never touches a prefix; V14 only runs `wine --version`.
```bash
#!/bin/bash
# stage verify: gates V1-V15 on the build that assemble just made (not on the current runtime)
set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd -P)/env.sh"
exec /bin/bash "$REPO/scripts/cx/verify-runtime.sh" "$RT_ROOT/$(cat "$CXB/stamps/assembled.id")"
```
```text
V1  lipo -archs lib/wine/x86_64-unix/wine is x86_64
V2  otool -hv of the loader shows no PIE flag (NOUNDEFS DYLDLINK TWOLEVEL)
V3  the loader has a WINE_RESERVE segment (zerofill reserve; no preloader)
V4  lipo -archs is x86_64 for ntdll.so, win32u.so and winemac.so, one file per call (lipo -archs takes one input, review F3)
V5  ntdll.so minos is 14.0
V6  ntdll.so's LC_RPATH includes @loader_path/../..
V7  winemac.so exports _macdrv_functions (d3dmetal.c:397); ntdll.so exports _prepend_dll_path, _add_load_order_override,
    _KeServiceDescriptorTable and _NtCreateThreadEx
V8  ntdll.so contains the string WINEDLLPATH_PREPEND (hb-0003 compiled in)
V9  ntdll.dll exports __wine_unix_call_dispatcher and __wine_unix_call
V10 lib/wine/i386-windows holds more than 500 files (WoW64 half present)
V11 no otool -L dependency points into /opt/homebrew, /opt/local, /usr/local or /Users/; header lines are excluded (review F3)
V12 win32u.so names libfreetype.6.dylib and libMoltenVK.dylib; bcrypt.so names libgnutls.30.dylib; winebus.so names libSDL2
V13 every non-symlink lib/*.dylib passes codesign -v
V14 wine --version equals BUILDINFO line 1 without its "bNNN-" prefix (review F18)
V15 share/wine holds wine-mono-10.4.1 and both wine-gecko-2.47.4 trees
```
The script was dry-run on 2026-10-20 against the existing `~/Games/sdk/wine-staging`, with V9 and V14 skipped and nothing from that runtime executed. V1-V4, V6, V10 and V11 passed; V5, V7, V8, V12, V13 and V15 failed, as expected for a non-CrossOver build. So the checks run and discriminate. That run also showed that a universal dylib prints one `otool -L` header line per architecture, which is why V11 and DEP2 drop every line that ends with `:` instead of only the first line.

M3.5 `scripts/cx/stages/promote.sh`: make the assembled and verified build current, safely (review C5, C2, R1-5, R1-14, R1-15).
```bash
#!/bin/bash
# stage promote: make the assembled and verified build current, safely (plan 2.4, 4.7, 4.9)
set -euo pipefail
source "$(cd "$(dirname "$0")/.." && pwd -P)/lib.sh"     # env.sh and the lock helpers; works before the first promote
NEW="$(cat "$CXB/stamps/assembled.id")"; NEWRT="$RT_ROOT/$NEW"; OLDRT="$RTR"; PR="$HOME/Games/prefixes"
TS="$(date -u +%Y%m%dT%H%M%SZ)"; switched=0; finished=0; SNAPS=""
# 1. Take the session lock for every prefix, and never switch under running processes of the current build.
claim_session promote $$ all || exit 1
export CX_SESSION_PARENT=$$
finish() {   # on any failure after the switch: back to the previous build and the pre-promote prefixes
  local rc=$? q
  if [ "$switched" = 1 ] && [ "$finished" = 0 ]; then
    echo "promote of $NEW failed after the switch: restoring ${OLDRT##*/} and the pre-promote prefixes" >&2
    if [ -n "$OLDRT" ]; then ln -sfn "wine-cx26.builds/${OLDRT##*/}" "$RT_LINK"; else rm -f "$RT_LINK"; fi
    for q in $SNAPS; do
      CX_RT="$NEWRT" "$X/cx-run.sh" --prefix "$q" -- wineserver -k 2>/dev/null || true
      mv "$PR/$q" "$PR/$q.failed-promote-$NEW-$TS" && mv "$PR/$q.snap-prepromote-$TS" "$PR/$q" || true
    done
  fi
  release_session promote $$
  exit "$rc"
}
trap finish EXIT
if [ -n "$OLDRT" ] && [ -n "$(lsof -t "$OLDRT/lib/wine/x86_64-unix/ntdll.so" 2>/dev/null || true)" ]; then
  echo "REFUSE: processes of $OLDRT are still running (steam.sh stop first)" >&2; exit 1
fi
# 2. Minimal smoke of the new build in the disposable prefix: T1, T2, T4. A fresh log dir per run: --log appends.
L="$CX_LOG_ROOT/promote-$NEW-$TS"; mkdir -p "$L"; rm -rf "$PR/cx_smoke"
[ "$("$NEWRT/bin/wine" --version)" = "${NEW#b[0-9][0-9][0-9]-}" ] || { echo "FAIL T1 on $NEW" >&2; exit 1; }
CX_RT="$NEWRT" "$X/with-timeout.sh" 300 "$X/cx-run.sh" --prefix cx_smoke --log "$L/t2.log" -- wineboot -i
CX_RT="$NEWRT" "$X/with-timeout.sh" 300 "$X/cx-run.sh" --prefix cx_smoke -- wineserver -w
CX_RT="$NEWRT" "$X/with-timeout.sh" 120 "$X/cx-run.sh" --prefix cx_smoke --log "$L/t4.log" -- cmd /c 'echo %USERNAME% %PROCESSOR_ARCHITECTURE%'
[ "$(/usr/bin/grep -c 'crossover AMD64' "$L/t4.log" || true)" -ge 1 ] || { echo "FAIL T4 on $NEW" >&2; exit 1; }
CX_RT="$NEWRT" "$X/cx-run.sh" --prefix cx_smoke -- wineserver -k || true
# 3. Back up user data, stop the old servers, snapshot the promoted prefixes (instant APFS clones), switch the link.
PFXS=""; for q in cx_prefix cx_dlss; do if [ -d "$PR/$q/drive_c" ]; then PFXS="$PFXS $q"; fi; done
if [ -d "$PR/cx_prefix/drive_c" ]; then "$X/backup-userdata.sh" cx_prefix; fi
if [ -n "$OLDRT" ]; then for q in $PFXS; do CX_RT="$OLDRT" "$X/cx-run.sh" --prefix "$q" -- wineserver -k 2>/dev/null || true; done; fi
for q in $PFXS; do cp -Rc "$PR/$q" "$PR/$q.snap-prepromote-$TS"; SNAPS="$SNAPS $q"; done
ln -sfn "wine-cx26.builds/$NEW" "$RT_LINK"; switched=1
# 4. Update each promoted prefix explicitly, in a plain environment, then stamp and check it.
for q in $PFXS; do
  "$X/with-timeout.sh" 900 "$X/cx-run.sh" --prefix "$q" -- wineboot -u      # forced update: runs although the stamp reads 'disable'
  "$X/with-timeout.sh" 300 "$X/cx-run.sh" --prefix "$q" -- wineserver -w
  printf 'disable\n' > "$PR/$q/.update-timestamp"; head -1 "$NEWRT/BUILDINFO" > "$PR/$q/.m5runner-runtime"
  if [ -e "$PR/$q/.cx-dlss-copies" ]; then "$X/stage-dlss-copies.sh" "$q"; fi      # also runs prefix-check.sh
  CX_RT="$NEWRT" "$X/prefix-check.sh" "$q"
done
finished=1
for q in $SNAPS; do rm -rf "$PR/$q.snap-prepromote-$TS"; done
echo "promoted $NEW (previous: ${OLDRT##*/})"
```
1. It takes the session lock for all prefixes (owner `promote`) and refuses while a live lock exists or any process of the current runtime runs. A switch under a running session would let clients of one build attach to another build's wineserver. A stale lock (its anchor no longer runs with the recorded start time, or it predates the last boot) is replaced with a message (4.9).
2. It smoke-tests the new build in the disposable `cx_smoke` (T1, T2, T4) before switching anything. Each run logs into a fresh `promote-<build>-<UTC>/`, because `cx-run.sh --log` appends: a second promote of the same build (a rollback to the LKG, or a retry) must not pass T4 on an old line (R1-5).
3. It backs up user data, stops the old build's wineservers, takes instant APFS snapshots of `cx_prefix` and `cx_dlss`, and switches the symlink.
4. In each promoted prefix it runs the forced `wineboot -u` in plain mode, writes `disable` again, stamps the prefix, re-stages the DLSS copies where the marker exists, and checks the prefix.
5. If any step after the switch fails, the EXIT trap switches the link back to the previous build, moves the half-updated prefixes aside as `<prefix>.failed-promote-<build>-<UTC>` for triage, and puts the snapshots back, so the prefixes again match the stamps of the build that is current. On success the snapshots are deleted (R1-14). This path was exercised on 2026-10-20 with stand-in runtimes and prefixes in a scratch HOME: a clean promote of two prefixes, and a failure in `prefix-check.sh` after the switch, which restored the old link and both prefixes and released the lock.

A build becomes LKG (last known good) in BUILD_LOG only after promote succeeded and the milestone's gates passed on it. The first `promote` happens before `cx_prefix` exists, so steps 3 to 5 only switch the link then. `build-wine-cx.sh iter` = make, install, assemble, verify, promote.

Failure modes M3

| Symptom | Fix |
|---|---|
| Unix side: "call to undeclared function" or "incompatible function pointer types" (Apple clang 21 makes these errors) | `CX_CFLAGS="-O2 -g -Wno-error=implicit-function-declaration" scripts/build-wine-cx.sh from configure` (frankea uses it), or `-Wno-error=incompatible-function-pointer-types` |
| Errors in CrossOver-only ObjC files (`winemac.drv/d3dmetal_objc.m`, `cocoa_icon_utils.m`, `winecoreaudio.drv/authorization.m`) | **ASSUMPTION** that they compile with SDK 26.5 (untested). First try `-Wno-error=deprecated-declarations` in `CX_CFLAGS`; otherwise write a minimal source fix as a new patch and record it |
| PE side, GCC 16 errors (implicit-function-declaration, int-conversion and incompatible-pointer-types are errors since GCC 14; the default is C23 since GCC 15) | `CX_CROSSCFLAGS="-O2 -g -std=gnu17 -Wno-error=incompatible-pointer-types -Wno-error=int-conversion -Wno-error=implicit-function-declaration" scripts/build-wine-cx.sh from configure`. **ASSUMPTION** that no flags are needed, because Highball and steamplay built this tarball with Homebrew mingw |
| winegcc: "Could not find gcc" | `PATH` lacks `/opt/homebrew/bin` (winegcc.c:399-441) |
| make: "has uncommitted changes" | Commit the edit in `$SRC` and export it as a patch (4.1 step 7) |
| V5 is not 14.0 | `MACOSX_DEPLOYMENT_TARGET` was not exported for make (env.sh) |
| V7 symbols missing | wrong source tree, or someone stripped the binaries |
| V11 shows a path | A dependency id was not rewritten: `scripts/build-wine-cx.sh from deps`. The failed bNNN stays as it is, and a new one is assembled |
| V14: "could not load ntdll.so" | `bin/wine` is a copy rather than a symlink, or a dylib is missing. Check with `DYLD_PRINT_LIBRARIES=1 $RT/bin/wine --version` |
| promote: "REFUSE: session lock held" or "processes ... still running" | `steam.sh stop` for an agent-run Steam (`steam-ui`); wait for `er.sh`, a test block or a session handed to Daniel (`steam-daniel`, `er-daniel`, `m84-daniel`) to end. A stale lock is replaced automatically (4.9) |
| promote: "FAIL T1/T4 on <build>" | The new build stays assembled but not current. Triage it with `CX_RT=~/Games/sdk/wine-cx26.builds/<build> scripts/cx/smoke.sh` |
| promote: "failed after the switch" | The previous build is current again and the prefixes are back as they were. Compare `prefix-check.sh` output and the wineboot log in the `promote-<build>-<UTC>/` dir with `<prefix>.failed-promote-<build>-<UTC>`; delete that copy once the cause is in BUILD_LOG |

Fallback toolchain, only after GCC fails twice: build a second tree `wine-x86_64-llvm` with llvm-mingw 20261006 (D1). Configure it with `--with-mingw=$CXB/llvm-mingw/bin/clang`, append `$CXB/llvm-mingw/bin` to `PATH`, and apply Gcenx patches 7-9. Then copy a GCC-built `kernelbase.dll` into its runtime.

### M4: Runtime smoke tests (30-60 min)

`scripts/cx/smoke.sh` (Appendix A.13) runs T1-T14 against the disposable prefix `cx_smoke`. It is a session of its own (`begin_session smoke idle`, 4.9), every step logs with `--log`, and every wait has a timeout. Its timeouts add up to more than 15 minutes, so run the block below as a background job and tail `$CX_LOGS/gates.txt` (R2-12).
```bash
X=~/projects/m5-wine-runner-cx/scripts/cx; eval "$("$X/newcycle.sh" smoke)"; "$X/smoke.sh"; cat "$CX_LOGS/gates.txt"
```
```text
T1  wine --version equals BUILDINFO line 1 without "bNNN-" (winecx-26.3.0-6-g<sha>)
T2  wineboot -i and wineserver -w exit 0 within 300 s; system32 and syswow64 hold more than 500 files each
T3  prefix-check.sh: Wine's own d3d10/d3d11/d3d12/d3d12core/dxgi copies, and nvapi64/nvngx/atidxx64 placeholders (wine.inf.in:739-742)
T4  t4.log: a version line, then "crossover AMD64"
T5  t5.log: "x86", and no "start.exe" relaunch in the +process trace (D7)
T6  t6.log: "HTTP 200" (any real status proves schannel -> GnuTLS)
T7  notepad.png holds only the Notepad window (INCONCLUSIVE while the screen is locked)
T8  logs exist (every step uses --log) and none has "cannot find the FreeType font library" (review F4)
T9  a wineserver started with msync 1; a client with msync 0 then exits 1 with "Server is running with WINEMSYNC but this
    process is not" in a log made with err+all; the server log has no "msync: error" (review F4)
T10 HKCU\Software\Wine\WineDbg ShowCrashDialog reads 0x0 (review C13)
T11 hello64.exe (a non-builtin PE) prints "hello from x86_64", and its +module log has "Loaded libd3dshared.dylib, does
    support non-native code regions"
T12 the same with --no-d3dshared prints the greeting and has no "Loaded libd3dshared" (the A/B baseline for D6)
T13 while Notepad runs, lib.sh session_pids lists it and server_pid finds cx_smoke's wineserver: ps -E shows the
    WINEPREFIX of Wine processes, which capture.sh, probe.sh and the dialog watcher rely on (4.9)
T14 stage-dlss-copies.sh cx_smoke, then prefix-check.sh: "Apple copy (DLSS route)" for nvapi64 and nvngx, so the
    marker written by one script is the path the other reads (R1-4)
```
- **T13 settles an ASSUMPTION.** Wine starts every child with a double fork, sometimes with `setsid()`, and then execs the loader with its own unix environment (`wine/dlls/ntdll/unix/process.c:866-937`). So a child is not a descendant of the process that started the session, but it does carry the session's `WINEPREFIX`. That variable is neither special nor ignored (`env.c:332-358`), and CrossOver's alternate loader is used only when `CX_ALT_LOADER_SOCKET` is set (`process.c:333-338`), which `cx-run.sh` scrubs. `ps -E -ww -o command=` printed the environment of a same-user, non-Apple process on this Mac (checked 2026-10-20 with a Homebrew bash); T13 shows whether it does so for Rosetta-translated Wine processes.
- **T9 is a negative test.** The mismatch error (`wine/dlls/ntdll/unix/msync.c:587-600`) proves the msync server is really running. It is an ERR, so it is printed only with `err+all`. `cx-run.sh` defaults to `WINEDEBUG=-all`, which is why the earlier version of this test could never pass. `wineserver --persistent=60` keeps the msync server up without depending on a long-running client.
- **T11 and T12 replace "repeat T6 and T7 with and without libd3dshared" (review F20, C19).** ntdll loads libd3dshared only when a non-builtin PE module loads (`wine/dlls/ntdll/loader.c:2357-2364`). cmd, cscript and notepad are Wine builtins, so T4-T7 never load it, whatever the environment says. A native program is the only valid test. The first real A/B of D6 is Steam (knob `--no-d3dshared`).

Failure modes M4

| Symptom | Diagnosis and fix |
|---|---|
| T1: "could not load ntdll.so" | See V14 |
| T2 hangs on a Mono or Gecko prompt | Addons not found (V15). Workaround: `CX_EXTRA_OVERRIDES='mscoree,mshtml='` for the wineboot |
| T2: "failed to update ... wine.inf not found" | `share/wine` is missing; re-run `install` and `assemble` (`build-wine-cx.sh from install`) |
| T3 shows "Wine builtin DLL" or a missing file | wineboot ran with `WINEDLLPATH_PREPEND` set (it must not), or the build lacks CW HACK 22435 |
| T4 or T5 fail with c0000135 | PE half missing (V10) |
| T5 shows a `start.exe` relaunch | `WINEARCH=wow64` is not exported (D7); check `cx-run.sh --print-env` |
| T6 prints "HTTP 0" or a script error | GnuTLS did not load. With `+secur32,+bcrypt`, look for "failed to load libgnutls" (V12, V13) |
| T8 finds FreeType errors | SONAME or rpath problem (V12, V6). A textless Steam UI later has the same cause |
| T9 does not show the message | First check that t9b.log was made with `err+all`. Then check that `WINEMSYNC=1` reached the server (`ps eww <pid>`). `server/msync.c` is compiled for every `__APPLE__` build |
| T10 is not 0x0 | The `reg add` after `wineboot -i` failed; see t10.log |
| T11 has no "Loaded libd3dshared" | The renderer tree is missing (M0.10), or the variable is not exported (`cx-run.sh --print-env`), or libd3dshared is quarantined or its signature fails (`xattr -l`, `codesign -v`) |
| T12 still loads libd3dshared | `--no-d3dshared` was not parsed: check the argument order (options before `--`) |
| T13 fails | `ps -E -ww -o command= -p <notepad pid>` shows no `WINEPREFIX=`. Write `export CX_SESSION_FILTER=0` into `$CXB/local.env`: capture and the watcher then see every process of the runtime, which is safe because sessions never overlap (4.9). Record it in BUILD_LOG |
| T14 fails | Read t14.txt. "DLSS copy missing or changed" means the marker and `prefix-check.sh` disagree about the path: the marker must hold the realpath of `<gptk>/wine` (A.14) |
| smoke.sh: "REFUSE: session lock held" or "processes ... still running" | Another session runs. Wait for it, or `steam.sh stop` for a headless Steam (4.9) |

### M5: D3DMetal 4.0b3 hookup (1-4 h)

M5.1 Check the renderer tree (built in M0.10):
```bash
(cd ~/Games/sdk/gptk/4.0b3 && shasum -a 256 -s -c MANIFEST.sha256) && echo manifest-ok
plutil -extract CFBundleShortVersionString raw ~/Games/sdk/gptk/4.0b3/external/D3DMetal.framework/Versions/A/Resources/version.plist   # 4.0b3
stat -f '%z' ~/Games/sdk/gptk/4.0b3/external/libd3dshared.dylib                                                                   # 250672
```

M5.2 Create the main prefix in a clean environment, switch off automatic updates (2.4), stamp it and turn off crash dialogs (review C13):
```bash
X=~/projects/m5-wine-runner-cx/scripts/cx; source "$X/lib.sh"; begin_session setup idle    # lib.sh sets P=~/Games/prefixes/cx_prefix
"$X/with-timeout.sh" 300 "$X/cx-run.sh" -- wineboot -i && "$X/with-timeout.sh" 120 "$X/cx-run.sh" -- winecfg -v win10 \
  && "$X/with-timeout.sh" 300 "$X/cx-run.sh" -- wineserver -w || exit 1        # a timeout (142) or a failure ends the block
printf 'disable\n' > "$P/.update-timestamp"
head -1 ~/Games/sdk/wine-cx26/BUILDINFO > "$P/.m5runner-runtime"
"$X/with-timeout.sh" 120 "$X/cx-run.sh" -- reg add 'HKCU\Software\Wine\WineDbg' /v ShowCrashDialog /t REG_DWORD /d 0 /f || exit 1
"$X/prefix-check.sh" cx_prefix                                    # 8 PASS lines
"$X/cx-run.sh" -- wineserver -k; snap_prefix m5-clean              # lib.sh; never cp -Rc onto an existing snapshot (R3-6)
```
wineboot copies builtin PE files byte for byte (verified from source by the feasibility review), so the `cmp` checks in `prefix-check.sh` hold.

M5.3 D3D12 and D3D11 smoke test with our own test programs (review C1). They need no Steam, no NGX and no shaders. The block is a session of its own, and a dialog ends the run at once instead of holding it until the timeout (review C13). `V` selects the GPTK tree (M5.4 runs the same block with `V=3.0`), and each program runs with that version's own D3DMetal shader cache (M7.5).
```bash
X=~/projects/m5-wine-runner-cx/scripts/cx; source "$X/lib.sh"; begin_session d3d-smoke idle
V="${V:-4.0b3}"; eval "$("$X/newcycle.sh" "d3d-smoke-$V")"; L="$CX_LOGS"; CX_GPTK="$V"      # not exported: for gates_header
gates_header 0 "d3d-smoke-$V" > "$L/gates.txt"                                              # first line of every gates.txt (R3-2)
T=~/Games/prefixes/cx_prefix/drive_c/tests; mkdir -p "$T"; cp ~/Games/build.noindex/cx26/tests/bin/*.exe "$T/"
cd "$T"
for api in d3d12 d3d11; do
  D="$L/$api"; mkdir -p "$D"; gates_header 0 "d3d-smoke-$V-$api" > "$D/gates.txt"         # the watcher appends DIALOG lines
  echo "$api shader cache: $(d3dm_cache_in "${api}_clear.exe" "$V")" >> "$L/gates.txt"
  watch_dialogs "$D" $$ & WP=$!
  "$X/d3dm-log.sh" "$L/$api-d3dm.log" & LP=$!
  "$X/with-timeout.sh" 150 "$X/cx-run.sh" --d3dmetal "$V" --debug err+all,warn+seh,+module,+loaddll,+macdrv_d3dmtl,+d3dkmt \
      --log "$L/$api.log" -- "C:\\tests\\${api}_clear.exe" 60 & AP=$!
  wait_or_dialog 30 "$D"; "$X/probe.sh" "$D" "${api}_clear.exe" "$V" > "$L/$api-probe.txt"
  echo "H3 $api: $(gptk_mapped "$D" "$V" "$api|dxgi") of 2 DLLs mapped from gptk/$V" >> "$L/$api-probe.txt"
  if [ -e "$D/FAIL-dialog" ]; then echo "FAIL-dialog: run ended at the dialog" >> "$L/$api-probe.txt"; "$X/cx-run.sh" -- wineserver -k; fi
  rc=0; wait "$AP" || rc=$?; echo "exit=$rc" >> "$L/$api-probe.txt"
  kill "$LP" "$WP" 2>/dev/null
  "$X/cx-run.sh" -- wineserver -k; d3dm_cache_out "${api}_clear.exe"
done
```

Gates H1-H10:
```text
H1  d3d12.log: "Loaded libd3dshared.dylib, does support non-native code regions"   (loader.c:1348)
H2  d3d12.log: "Marking non_native_code_region" lines                               (loader.c:1362)
H3  the probe's lsof and vmmap listings of d3d12_clear.exe (d3d12/lsof.txt, d3d12/vmmap.txt) show both d3d12.dll and
    dxgi.dll mapped from ~/Games/sdk/gptk/4.0b3/wine/x86_64-windows (review F15, round 3):
      n=$(gptk_mapped "$L/d3d12" 4.0b3 'd3d12|dxgi')               # lib.sh; PASS only when n = 2
    The block prints the same count as "H3 d3d12: N of 2" in d3d12-probe.txt. The +module "mapping PE file" and
    "looking for" traces name only the file the loader asked for (system32), so they are not evidence here
H4  d3d12-probe.txt: "libd3dshared __TEXT images: 1" and "PASS F4b libd3dshared size+inode 250672 <inode>"
H5  d3d12-probe.txt: "PASS F4b D3DMetal.framework from gptk/4.0b3"
H6  d3d12.log, channel macdrv_d3dmtl: get_win_data -> macdrv_view_create_metal_view -> macdrv_view_get_metal_layer (d3dmetal.c:105-193)
H7  at least one "D3DM" line in d3d12-d3dm.log or d3d12.log
H8  "metal-HUD:" lines with increasing frame numbers; the program's output ends with frames=N, N > 600 for 60 s;
    the screenshot shows the HUD over a coloured window: 'is_black PNG hud' returns 1 (the HUD corner is masked),
    and the agent sees the HUD in the PNG
H9  exit=0; no "Unhandled exception" and no "page fault" in the log; no FAIL-dialog; no new
    ~/Library/Logs/DiagnosticReports/wine*.ips during the run
H10 H1-H9 again for d3d11_clear.exe (D3DMetal's D3D11); its H3 is n=$(gptk_mapped "$L/d3d11" 4.0b3 'd3d11|dxgi') = 2
```
- **Why H3 reads lsof and vmmap, not the `+module` trace (review F15, round 3).** The "mapping PE file" trace (`wine/dlls/ntdll/unix/virtual.c:3044`, and the section lines at 3156) prints the NT name the loader asked for, not where the builtin was found. `find_builtin_dll` opens the GPTK file with object attributes that carry the requested name (`wine/dlls/ntdll/unix/loader.c:1519`, through `open_unix_file` at 1456); the server stores that client-supplied name (`wine/server/file.c:269`, `wine/server/fd.c:1997`) and returns it from `get_mapping_info` (`wine/server/mapping.c:1578`); `virtual_map_builtin_module` hands it to `virtual_map_image` (`virtual.c:3810`). A correct D3DMetal setup therefore prints `\??\C:\windows\system32\d3d12.dll`, and no ntdll trace prints the resolved builtin path (`load_builtin_unixlib` at `virtual.c:870` and `open_unix_file` are silent). The process's own mappings do show it: on x86_64 hosts the page mask is a fixed 4 KiB (`virtual.c:180-182`) and `map_pe_header` mmaps the header straight from the file (`virtual.c:2726-2734`), so lsof and vmmap list every PE image under its real path (the GPTK DLLs are Wine builtin PEs; d3d12.dll is 196,608 B and dxgi.dll 135,168 B).
- `gptk_mapped` counts distinct DLL names under `gptk/<ver>/wine/x86_64-windows/`, so a d3d12.dll from GPTK plus a dxgi.dll from `lib/wine` counts 1, and `d3d12core.dll` never counts as d3d12. If a trace-based check is ever wanted, `WINEDEBUG=+server` prints the unix `filename=` of every `create_file` request (`wine/server/request_trace.h:621-630`). H1, H6 and H7 remain the behavioural confirmation.
- **ASSUMPTION** (H8): the Metal HUD draws in the top-right corner, which `is_black … hud` ignores. Check it on the first H8 screenshot; if the HUD sits elsewhere, change the mask in `lib.sh`.

Record the program's `adapter vendor=… device=… desc=…` line; gate X6 compares it with MetalFX on.

**ASSUMPTION:** `metal-HUD:` lines go to the process's stderr or the unified log. Apple only says "to the console". The harness captures both, so record where they actually land the first time.

M5.4 A/B tree with D3DMetal 3.0, only if H-gates fail and the failure points at D3DMetal. Copy from the GPTK 7.7 runtime; never move. CrossOver 26.3 itself ships D3DMetal 3.0, and its libd3dshared is the same 95,952 bytes as wine-gptk's. The 3.0 stubs use the older `__wine_unix_call` export, which this tree also provides (`ntdll.spec:1773`, CW HACK 22435). That this tree hosts 3.0 is likely, not verified.
```bash
G3=~/Games/sdk/gptk/3.0; S=~/Games/sdk/wine-gptk/lib; mkdir -p "$G3/wine/x86_64-unix" "$G3/wine/x86_64-windows"
ditto "$S/external" "$G3/external"
for d in atidxx64 d3d10 d3d11 d3d12 dxgi nvapi64; do cp -p "$S/wine/x86_64-windows/$d.dll" "$G3/wine/x86_64-windows/"; ln -s ../../external/libd3dshared.dylib "$G3/wine/x86_64-unix/$d.so"; done
cp -p "$S/wine/x86_64-windows/nvngx-on-metalfx.dll" "$G3/wine/x86_64-windows/nvngx.dll"; ln -s ../../external/libd3dshared.dylib "$G3/wine/x86_64-unix/nvngx.so"
(cd "$G3" && find . -type f ! -name MANIFEST.sha256 -print0 | xargs -0 shasum -a 256 > ../.MANIFEST.3.0.tmp && mv ../.MANIFEST.3.0.tmp MANIFEST.sha256)
```
wine-gptk's own `nvngx.dll` is an older 2025-09-05 build, so use `nvngx-on-metalfx.dll` (metalfx research). Re-run the M5.3 block with `V=3.0` (`V=3.0 /bin/bash <block file>`): it passes `--d3dmetal 3.0`, gives `probe.sh` and `gptk_mapped` that version, and swaps in each test program's 3.0 shader cache (M7.5, R2-11).

Failure modes M5, in triage order

| Symptom | Diagnosis | Fix |
|---|---|---|
| H1 shows "Loading libd3dshared.dylib failed: ..." | wrong path, quarantine or signature | the realpath in `cx-run.sh --print-env`; `xattr -l`; `codesign -v` |
| H1 missing with no message at all | the variable is not in that process | `ps eww <pid> \| tr ' ' '\n' \| /usr/bin/grep CX_` |
| H3: `d3d12/lsof.txt` shows d3d12.dll or dxgi.dll from `$RT/lib/wine/x86_64-windows` (or from system32) instead of `gptk/4.0b3` | prepend inactive | V8; the variable's spelling (`cx-run.sh --print-env`); is the system32 file still Wine's copy (`prefix-check.sh`)? |
| `d3d12.dll failed to initialize` or c0000135 | the GPTK stub cannot get its unix functions | `ls -L $G/wine/x86_64-unix/d3d12.so` and gate V9 |
| "Failed to dlopen D3DMetal" assertion | framework not beside libd3dshared, or `.so` files copied | Rebuild the tree with M0.10 (`ditto`) |
| Crash inside NtCreateThreadEx or the event functions, or a `pthread_setname_np` null read | thunk inactive: two images, or the variable unset | H1 and H4 first; same realpath (`unix_private.h:600-637`). If both pass, see the next row |
| H1 and H4 pass, but the crash report (`~/Library/Logs/DiagnosticReports/wine*.ips`) shows the crashed thread in libd3dshared.dylib calling an ntdll.so `NtXxx` that is not one of the 9 wrapped functions (NtCreateThreadEx, NtClose, NtCreateSemaphore, NtReleaseSemaphore, NtCreateEvent, NtSetEvent, NtResetEvent, NtClearEvent, NtPulseEvent), which then faults on bad arguments (review C14) | 4.0b3's libd3dshared (250,672 B, against 95,952 B for 3.0) calls a tenth ntdll function with ms_abi; only 4.0b2 was validated on these hooks | 1. A/B with `--d3dmetal 3.0` to confirm it is 4.0b3-specific. 2. In `$SRC`, edit the file that defines `NtXxx`, following `wine/dlls/ntdll/unix/thread.c:1480-1494`: rename the definition to `NTSTATUS WINAPI GPT_IMPORT(NtXxx)( … )`, and add `NTSTATUS __attribute__((ms_abi)) msthunk_NtXxx( <same args> ) { return sysv_NtXxx( <args> ); }` plus `GPT_ABI_WRAPPER( NtXxx );` inside `#if defined(__APPLE__) && defined(__x86_64__)` (macros at `unix_private.h:600-637`). 3. Commit it in `$SRC` (`git -C "$SRC" commit -qam "ntdll: GPT ABI wrapper for NtXxx"`; the make stage refuses a dirty tree), then `build-wine-cx.sh iter`. `iter` starts at make, so the commit carries the change; a file written only under `patches/` would never reach this build (R1-18). An ntdll unix change needs the full install that `iter` does. 4. If the fix is kept, export it per 4.1 step 7 as `patches/cx26.3/m5-0001-ntdll-gpt-abi-wrap-NtXxx.patch` and add it to `series`, `SHA256SUMS` and `PROVENANCE.md`, so a later `from src` rebuild keeps it. This uses only the crash report and Wine source, never Apple's binary (GPTK licence §2D) |
| Black window and no `get_win_data` trace | swapchain never created | Read the D3DM lines; `+macdrv_d3dmtl` |
| `get_win_data` returns NULL | the window belongs to another process (`d3dmetal.c:100-122`) | Expected only for CEF. For games, look at window creation |
| No HUD | `MTL_HUD_ENABLED` missing in the game process | `ps eww <pid>` |
| Works with 3.0, fails with 4.0b3 | D3DMetal 4 on macOS 26.5.1 (most third-party validation was on macOS 27) | `--gptk 3.0` for that title; record it; macOS 27 is Daniel's call later |
| A program complains about a missing VC++ runtime | Wine builtins usually cover it | With Daniel's OK, download Microsoft's `https://aka.ms/vs/17/release/vc_redist.x64.exe` and `vc_redist.x86.exe` into `$CXB/downloads`, record their sha256 in BUILD_LOG, then run `"$X/cx-run.sh" -- "$CXB/downloads/vc_redist.x64.exe" /install /quiet /norestart` and the same for x86. Never use winetricks in `cx_prefix`: it unsets `WINEARCH` and does not accept `wow64`, so its 32-bit steps would relaunch through `start.exe /exec` (review F19) |

### M6: Steam (2 h to 2 days; the largest uncertainty)

The gates are split (D19). **S-core** (S1, S6, S7, S8) gates M7, because the game only needs a ready client, online or offline. **S-UI** (S2-S5) gates only F1. **S9** gates F1 and the M9b flip. Steam sessions hold the session lock like every other Wine session (4.9). A Steam window handed to Daniel (the sign-in in M6.3, the benchmark install in M8.4) runs as `steam.sh ui --hold`, whose lock owner `steam-daniel` no agent script stops without `--force` (R2-9). While the agent waits for Daniel's sign-in, it does only work that starts no Wine process (M9a code and unit tests); M8.0-M8.3 and X6 run as sessions of their own, between Steam cycles and outside the agreed sign-in slot (1.3).

M6.0 (optional; Daniel approves the 235 MB download) Reference baseline (review C6). athei's public cx-26.3.0-9 release is a build of the same CrossOver 26.3.0 source that runs Steam's webhelper on DXMT with an in-process GPU through a built-in rule, which is the rung-L1 recipe. It needs `SteamSetup.exe`, so it starts after M1.1. It does not need our runtime: in `--ref` mode, `steam.sh` exports `CX_RT` (the reference root) and `CX_PREFIX_NAME=cx_ref_prefix` before it sources `lib.sh`, sends every Wine call through `ref-run.sh` and takes no session lock (R1-8, R1-17). The reference is another runtime and prefix, so cx's `wineserver -k` cannot reach it, its processes are not in our runtime's PID list, and an M3 promote is not blocked by it. It may therefore run while M1.2-M5 build.
```bash
D=~/Games/sdk/ref/athei-cx-26.3.0-9; mkdir -p "$D/rt" && cd "$D"
gh release download cx-26.3.0-9 -R athei/wine-build -p 'wine-cx-26.3.0-9-macos-x86_64.tar.xz'
echo "af3682051414eeffa5be48584a671790fd3852e980ff5acd38facff6f4bff1e9  wine-cx-26.3.0-9-macos-x86_64.tar.xz" | shasum -a 256 -c -
tar -xJf wine-cx-26.3.0-9-macos-x86_64.tar.xz -C rt
w="$(find rt -maxdepth 5 -path '*/bin/wine' -print | head -1)"; [ -n "$w" ] || { echo "no bin/wine in the bundle" >&2; exit 1; }
(cd "$(dirname "$w")/.." && pwd -P) > RUNTIME_ROOT; cat RUNTIME_ROOT
test -e "$(cat RUNTIME_ROOT)/lib/wine/x86_64-unix/ntdll.so" && echo layout-ok     # runtime_pids, capture.sh and probe.sh need it
```
The release asset is 235,425,012 bytes; `-p` downloads only that asset. athei's README for this build (`research/build-recipes/athei-wine-build-cx-26.3.0-9/README.md:35-56`) shows the same `lib/wine/x86_64-unix` layout, and the bundle loads its own `lib/external` libd3dshared unless `CX_APPLEGPTK_LIBD3DSHARED_PATH` says otherwise, so `ref-run.sh`'s scrub is enough.
1. `ref-run.sh -- wineboot -i` creates `cx_ref_prefix`. Then `ref-run.sh -- cmd /c 'echo %USERNAME%'` records its Windows user name. Its DPAPI behaviour is unknown, and it matters for rung L6.
2. `eval "$(scripts/cx/newcycle.sh steam-ref)"; scripts/cx/steam.sh --ref install`, then `steam.sh --ref ui --timeout 1800` (a background job). Let the first update finish, then record S2-S5 on the second start, after `steam.sh --ref stop`: `--ref ui` refuses while a reference Steam runs (R4-4). Capture, probe and the dialog watcher look at the reference's own processes in `cx_ref_prefix`. Once S2-S5 are recorded, end with `steam.sh --ref stop`: this window is the agent's, never Daniel's, and a reference Steam left running would make the L6 sign-in's `--ref ui --hold` refuse (R5-1).
3. Read the result:
   - Steam renders there but not on ours: the cause is our build or our patches. Diff modules, environment and series.
   - Black on both: the cause is this Mac's environment, not our build. Skip the DXMT rungs L1 and L2 and continue with L3 (patch 0007 with wined3d), then L5 (CPU raster) and L6 (headless sign-in).

Rules: this is a third-party build, and it bundles Apple's GPTK 4.0b2 (its release notes). Keep it under `~/Games/sdk/ref`, never copy files out of it, never commit or redistribute it, never prepend our GPTK tree into it and never point it at `cx_prefix`.

M6.1 Registry baseline and install. Snapshot first. Do not bring over the native `bcrypt.dll` workaround: CrossOver 26.3's bcrypt accepts `BCRYPT_RNG_ALG_HANDLE` (`wine/dlls/bcrypt/bcrypt_main.c:208-222, 262-290, 312-354`).
```bash
X=~/projects/m5-wine-runner-cx/scripts/cx; source "$X/lib.sh"; begin_session steam-setup idle    # P=~/Games/prefixes/cx_prefix
"$X/cx-run.sh" -- wineserver -k; snap_prefix m6-pre-steam || exit 1
r() { "$X/with-timeout.sh" 120 "$X/cx-run.sh" -- reg add "$@" /f || exit 1; }   # a timeout (142) or a failure ends the block
for e in steam.exe steamwebhelper.exe steamservice.exe gameoverlayui64.exe; do
  for d in nvapi64 nvapi; do r "HKCU\\Software\\Wine\\AppDefaults\\$e\\DllOverrides" /v "$d" /t REG_SZ /d ''; done
done
r 'HKCU\Software\Valve\Steam' /v GPUAccelWebViewsV3 /t REG_DWORD /d 1
r 'HKCU\Software\Wine\AppDefaults\eldenring.exe\DllOverrides' /v gameoverlayrenderer64 /t REG_SZ /d ''
eval "$("$X/newcycle.sh" steam-install)"; "$X/steam.sh" install      # SteamSetup.exe /S from $CXB/downloads, WINEMSYNC=0
cat ~/Games/build.noindex/cx26/logs/steamsetup.sha256               # copy this hash into the cycle's BUILD_LOG entry (review F13)
```
`steam.sh install` runs inside this block's session: it inherits `CX_SESSION_PARENT` from `begin_session`, so its lock check passes (4.9).

M6.2 First launch, which is the update run (review C16). In a new cycle, `steam.sh ui --timeout 1800`, run as a background job of the agent's shell tool:
1. It checks the session lock, takes it (owner `steam-ui`), kills this prefix's wineserver, runs the pre-flight and hygiene (including the reset of `ActiveProcess`, D20; every hygiene call uses the session's msync, R2-4), then starts `steam.exe -no-cef-sandbox` with `WINEMSYNC=0` and `WINEDEBUG=err+all,+seh`.
2. The first launch downloads and unpacks the client, which takes 15-25 min under Rosetta (Highball steam.json). `steam.sh` waits until `logs/webhelper.txt` exists, which means the updated client got as far as starting its UI. A dialog ends the wait early as FAIL-dialog (review C13).
3. Then `steam.sh stop` and the snapshot, in a session of its own: `/bin/bash -c 'source "$0"; begin_session snap idle; snap_prefix "$1"' "$X/lib.sh" m6-updated`. lib.sh's `snap_prefix` moves an older snapshot of the same tag aside (`.old-<UTC>`) before it clones, because BSD `cp -Rc` onto an existing directory nests the new copy inside it and leaves the stale one on top (R3-6).

Rung L0 is evaluated on the second start, so the update's own restart cannot break S2's "one webhelper launch per start". **ASSUMPTION:** the first start ends with one client restart and a webhelper start. Record the bootstrap_log lines you see.

Do not pass `-cef-disable-gpu-compositing`, which the GPTK 7.7 runner used. It makes Steam append `--disable-gpu`, and GPU-off web views stay black on Wine 11 engines (highball#282). It also appeared in the old failing logs.

Gates S1-S9 (`steam.sh gates`, reading `drive_c/Program Files (x86)/Steam/logs/` and the registry):
```text
S-core (gates M7)
S1  bootstrap_log.txt: no "http error 0" after the update (schannel -> GnuTLS works)
S6  after Daniel signs in: connection_log.txt gains a line matching '\[Logged On,' after the start offset, and
    config/loginusers.vdf has an account block with "RememberPassword" "1" (the gate prints only "account present")
S7  steam.sh silent is ready within 120 s with no window. Ready (D20): steam.sh set HKCU\Software\Valve\Steam\ActiveProcess
    ActiveUser and pid to 0 before the start, and reg query now shows both non-zero again (printed only as "nonzero":
    ActiveUser is the account id); a steam.exe of this session is alive (session_pids, filtered by ps -o args); and,
    when .cx-session reads offline=0, connection_log.txt has a '\[Logged On,' line after the start offset (an offline
    session, offline=1, never logs one; R3-1)
S8  steam.log has neither "Server is running with WINEMSYNC but this process is not" (a client without msync on an
    msync server, msync.c:600) nor "Failed bootstrap_look_up" (a client with msync on a server without it, msync.c:636):
    either one means two msync values met in one session (R2-4, R2-14)
S-UI (gates F1 only)
S2  webhelper.txt: exactly one "Startup - webhelper launched" per Steam start over 120 s (second and later starts)
S3  steamui_html.txt: no "Restart webhelper process" after the start
S4  cef_log.txt: no "exit_code=-1073740791"
S5  sign-in window visible and not black (window-only screenshot of this session; 'is_black PNG' returns 1, Steam has no
    HUD; agents also inspect the PNG)
S-design (gates F1 and the M9b flip)
S9  for every steam*.exe PID of this session, lsof -p lists no path under /gptk/ except external/libd3dshared.dylib,
    and no D3DMetal.framework
```
- `reg query` runs with the msync value that `steam.sh` recorded in `$P/.cx-session`, so it never trips S8 itself.
- **ASSUMPTION** (S6, S7): the exact connection_log text. Confirm it at the first successful login and fix the pattern then. The ActiveProcess values are verified in the existing `gptk_prefix` user.reg: while logged off, ActiveUser is 0, next to `pid`, `SteamClientDll64` and `Universe`.
- **ASSUMPTION** (S7, R1-23): a starting client writes `pid` at once and `ActiveUser` at logon, so the reset to 0 cannot hide a fresh session. Values left over from a crash would otherwise let a client stuck at the account picker pass S7, and the game would then fail in SteamAPI_Init (M7 failure table). The first S7 run in M6.4 settles it: `pid` must turn non-zero within seconds of the start.
- **ASSUMPTION** (S9): libd3dshared maps D3DMetal.framework only when a D3D device is created; the "Failed to dlopen D3DMetal" message implies a runtime dlopen. If S9 finds the framework in Steam processes, record it and A/B with `steam.sh ui --no-d3dshared`. We learn this from lsof at run time, never by inspecting Apple's binary.

Ladder (review F5 and C16). One rung per cycle; take the next rung only after the gates fail. Each rung takes under 30 min once Steam is installed. Every rung starts with `steam.sh stop` and `steam.sh reset-rung` with the rung's options (both check the session lock, and `reset-rung` takes it for its own registry and file changes; 4.9, R2-7), or with the prefix rollback of 4.7 to `snap-m6-updated`, which backs up user data first and restores it afterwards (R1-19). Its BUILD_LOG entry stores `appdefaults-start.txt` (the output of `reg query 'HKCU\Software\Wine\AppDefaults' /s`), so no rung inherits another rung's `CommandLineAppend`, `Direct3D` renderer key or winemetal copies.

| Rung | Change | Evidence |
|---|---|---|
| L0 | Defaults: wined3d, GPU on, out-of-process GPU | Probably fails: CEF's GPU process cannot present into the browser's window (Wine bug 60263; `wine/dlls/winemac.drv/d3dmetal.c:100-122`, `wine/dlls/winemac.drv/opengl.c:1468-1472`). Record the signature anyway |
| L1 | athei's recipe: Steam's processes on the DXMT prepend plus `--in-process-gpu` (commands below; the winemetal pre-check first) | athei compatdb `builtin.rs:116-131`, used on CrossOver 26.3.0-9 builds |
| L2 | Highball's recipe: a new build = base + hb-0007 (at-0008 stays off: they conflict); the Steam session on the DXMT prepend, with `winemetal.dll` in system32 and syswow64 as in L1 (`reset-rung --winemetal`); `GPUAccelWebViewsV3=1`; no `CommandLineAppend`; GPU process out of process. If the L1 pre-check needed the fallback (BUILD_LOG `winemetal pre-check: FAIL`), the hb-0007 build is assembled with `CX_BUNDLE_DXMT=1` (already in `$CXB/local.env`) and the session runs with `CX_DXMT_DIR=~/Games/sdk/cx-overlays/dxmt`, with no manual copies (R1-7). Re-run M5.3 after promote, because 0007 changes the D3DMetal client surface | Highball `steam.json` ("renderer": "dxmt", keep GPU-accelerated web views on, highball#282); `patches/README.md:19, 52` (0007 "Fixes the blank CEF sign-in / black Steam client"); `inputs.json` pins this tarball |
| L3 | The hb-0007 build with the default wined3d (no DXMT prepend). reset-rung must have removed any `Direct3D\renderer=gl` key: hb-0007 adds cross-process swapchains only for the Vulkan and D3DMetal surfaces, and `opengl.c:1468-1472` still refuses foreign windows | Open question in the steam-compat research: both the Highball and frankea successes used DXMT or DXVK |
| L4 | wined3d with an in-process GPU (`CommandLineAppend=--in-process-gpu`, no DXMT). If the window is black, also set `HKCU\Software\Wine\AppDefaults\steamwebhelper.exe\Direct3D` `renderer=gl` | Fewer moving parts. CW HACK 18311 otherwise picks Vulkan/MoltenVK first (`wine/dlls/wined3d/directx.c:3531`) |
| L5 | CPU raster: `CommandLineAppend` = `--disable-gpu --single-process` | Draws with text on stock Wine 11.0 (notpop, soju). **ASSUMPTION** for CrossOver 26.3 |
| L6 | Headless sign-in (review C6). Daniel signs in once wherever the UI renders: the reference runtime if M6.0 printed the user `crossover`, otherwise the CrossOver trial (Daniel's decision, 6.2); then he quits Steam there (Daniel queue, numbered steps below). `copy-steam-login.sh <that prefix or bottle dir>` (A.14) copies `config.vdf`, `loginusers.vdf`, `local.vdf`, the `HKLM\SOFTWARE\Microsoft\Cryptography` `MachineGuid` value and `HKCU\Software\Valve\Steam` `AutoLoginUser` and `RememberPassword` into `cx_prefix`, without printing any value; then `steam.sh silent` runs against S7 | steam-compat research fallback (c), "headless operation only". **ASSUMPTION** that the DPAPI-protected tokens survive the copy when user name and MachineGuid match, and **ASSUMPTION** that Windows Steam needs the two registry values for auto-login, as account switchers on Windows set them (R1-19); S7 settles both. F1 then reads "headless only" and needs Daniel's written OK |
| L7 | Escalate to Daniel | Options: (a) the CrossOver 26.3 trial on this Mac with Apple's documented 4.0b3 drop-in, to learn whether Steam works there at all; (b) Highball's DXMT fork, which allows cross-process swapchains behind `DXMT_ALLOW_CROSS_PROCESS_SWAPCHAIN` but requires building DXMT; (c) native macOS Steam with an lsteamclient bridge (the NotProton approach, a different architecture) |

Rung commands (R2-7). Each rung is `steam.sh stop`, a new cycle, `steam.sh reset-rung <options>`, then `steam.sh ui <options>`; for Daniel's sign-in the same rung runs as `ui --hold` (M6.3). The rung's registry values and winemetal copies are written by `reset-rung` under its own lock, never by a bare `cx-run.sh` call in a block, so every Wine call of the ladder goes through `steam.sh`'s lock handling:

| Rung | `reset-rung` options | `ui` options and environment |
|---|---|---|
| L0 | none | none |
| L1 | `--winemetal --append '--in-process-gpu'` | `--dxmt`, `CX_STEAM_DEBUG=err+all,+seh,+module`; then the winemetal pre-check (below) |
| L1 after the winemetal fallback | `--append '--in-process-gpu'` | `--dxmt`, `CX_DXMT_DIR=~/Games/sdk/cx-overlays/dxmt` |
| L2 | `--winemetal` (does nothing on a bundled build) | `--dxmt`, plus `CX_DXMT_DIR=~/Games/sdk/cx-overlays/dxmt` after the fallback; on the hb-0007 build |
| L3 | none | none; on the hb-0007 build |
| L4 | `--append '--in-process-gpu'`, plus `--renderer gl` if the window stays black | none |
| L5 | `--append '--disable-gpu --single-process'` | none |
| L6 | none | none: `copy-steam-login.sh`, then `steam.sh silent` against S7 |

L6 sign-in elsewhere (Daniel, only if the agent asks):
1. The agent starts Steam in the reference runtime (`steam.sh --ref ui --hold`; if its own M6.0 reference Steam still runs, and no window has been announced to you, it runs `steam.sh --ref stop` first, R5-1) or tells you which CrossOver trial bottle to open, and says when the sign-in window is up. The reference runtime takes no session lock, so `--hold` there only keeps the session from ending itself at a dialog once the window is announced (R3-3), and the agent never runs `steam.sh --ref stop`, nor `steam.sh --ref ui` again, while that window is yours (R4-4).
2. Sign in, approve the Steam Guard code and tick "Remember me".
3. Wait for the Library, then quit with Steam > Exit, so Steam writes its login files.
4. Tell the agent. It runs `copy-steam-login.sh` and tests the headless start (S7).
5. If S7 passes but no rung ever showed the Steam window, the agent asks whether "headless only" is acceptable for F1. Reply "OK headless only" or "not OK"; the agent records your answer in BUILD_LOG.

L1 commands. `winemetal.dll` needs a system32 entry because Wine has no builtin with that name; Highball adds it for the same reason (build.yml, "engine layout"). The copied files are builtin-tagged, so they resolve to DXMT's files only when DXMT is prepended. The pre-check comes first (review F12): DXMT's `winemetal.so` links `@rpath/winemac.so` and `@rpath/ntdll.so`, and its `LC_RPATH`s (`@loader_path/`, `@loader_path/../../`) point into `~/Games/sdk/dxmt`, where neither library exists. Loading it from the prepend directory works only if dyld binds those two names to the already-loaded images, which nobody has checked. `nm -m` on that `winemetal.so` shows it imports only `_NtSetEvent` from `@rpath/ntdll.so`, which the GPT_ABI wrapper exports globally (`unix_private.h:607-610`), and nothing from `winemac.so`, so `@rpath` resolution is the only risk. The runner side-steps the question today by copying `winemetal.so` next to `winemac.so` (`backends.py:224-232`).
```bash
X=~/projects/m5-wine-runner-cx/scripts/cx; source "$X/lib.sh"                          # P=~/Games/prefixes/cx_prefix
"$X/steam.sh" stop || exit 1                      # refuses while another session, or one handed to Daniel, holds the lock
eval "$("$X/newcycle.sh" steam-l1)"
"$X/steam.sh" reset-rung --winemetal --append '--in-process-gpu' || exit 1   # under its own lock: reg calls and winemetal copies
CX_STEAM_DEBUG=err+all,+seh,+module "$X/steam.sh" ui --dxmt    # Steam session runs with WINEDLLPATH_PREPEND=<realpath ~/Games/sdk/dxmt>
steam_lsof "$CX_LOGS/lsof"                                     # lsof of this session's running steam.exe and steamwebhelper.exe
winemetal_check "$CX_LOGS/steam.log" "$CX_LOGS/lsof" | tee -a "$CX_LOGS/gates.txt"      # record the line in BUILD_LOG
```
The block itself starts no Wine process: `reset-rung` writes `CommandLineAppend` and copies DXMT's `winemetal.dll` (x86_64 into system32, i386 into syswow64) inside its own lock, and `ui` takes the `steam-ui` lock (R2-7).

`winemetal_check` (A.9) reports FAIL when any process logged `failed to load "…winemetal.so"`, which Wine prints with dyld's own reason (`wine/dlls/ntdll/unix/virtual.c:851-853`; L1's `+module` enables it), so an `@rpath` error, a code-signature refusal and any other `dlopen` failure all count. It reports PASS only when there is no such line and the lsof listing of a running `steam.exe` or `steamwebhelper.exe` of this session has `…/x86_64-unix/winemetal.so` mapped (from `~/Games/sdk/dxmt` in L1, from the runtime's own `lib/wine` after the fallback); a library that `dlopen` loaded always appears in lsof and vmmap. Otherwise it reports INCONCLUSIVE, so an empty log or a session without a live Steam can never pass. The `+module` "mapping PE file" line cannot be the PASS evidence: `winemetal.dll` loads through its system32 entry, so that line names `C:\windows\system32\winemetal.dll` whichever file was mapped (the chain under H3; R1-6, round 3). On INCONCLUSIVE, check first that the session used DXMT at all: `cat "$CX_LOGS"/lsof/*.txt | /usr/bin/grep -cE '/sdk/(dxmt|cx-overlays/dxmt)/x86_64-windows/(d3d11|dxgi)\.dll'` must print at least 1 (the overlay's entries are symlinks into `~/Games/sdk/dxmt`, and lsof shows the file they resolve to). Tested on 2026-10-20 (round 3) on sample logs and listings: both failure kinds give FAIL, the system32 mapping line alone gives INCONCLUSIVE, and a listing with DXMT's `winemetal.so` gives PASS.

If the pre-check fails, use the fallback, which leaves `~/Games/sdk/dxmt` untouched. It persists: `CX_BUNDLE_DXMT=1` goes into `$CXB/local.env`, so every later build bundles DXMT's winemetal, and every later DXMT rung (L2) runs with the cx-owned overlay (R1-7):
1. `CX_BUNDLE_DXMT=1` assembles a build that holds DXMT's `winemetal.dll` (both arches) and `winemetal.so` inside our own `lib/wine`; promote's `wineboot -u` then writes the system32 and syswow64 winemetal entries itself (`wine/loader/wine.inf.in:799, 865`, `11,,*`).
2. The overlay holds only DXMT's d3d10core, d3d11 and dxgi.

The block rebuilds and promotes, so run it as a background job (R2-12):
```bash
X=~/projects/m5-wine-runner-cx/scripts/cx; source "$X/lib.sh"
"$X/steam.sh" stop || exit 1
touch "$CXB/local.env"; /usr/bin/grep -qx 'export CX_BUNDLE_DXMT=1' "$CXB/local.env" || echo 'export CX_BUNDLE_DXMT=1' >> "$CXB/local.env"
"$REPO/scripts/build-wine-cx.sh" iter || exit 1          # a new bNNN whose BUILDINFO says bundled-dxmt=1, then promote
O=~/Games/sdk/cx-overlays/dxmt; mkdir -p "$O/x86_64-windows" "$O/i386-windows"
for a in x86_64 i386; do for d in d3d10core d3d11 dxgi; do ln -sf ~/Games/sdk/dxmt/$a-windows/$d.dll "$O/$a-windows/$d.dll"; done; done
eval "$("$X/newcycle.sh" steam-l1-fallback)"
"$X/steam.sh" reset-rung --append '--in-process-gpu' || exit 1     # no --winemetal: the bundled build's wineboot made those entries
CX_DXMT_DIR="$O" CX_STEAM_DEBUG=err+all,+seh,+module "$X/steam.sh" ui --dxmt
steam_lsof "$CX_LOGS/lsof"; winemetal_check "$CX_LOGS/steam.log" "$CX_LOGS/lsof" | tee -a "$CX_LOGS/gates.txt"
```
On a build whose BUILDINFO says `bundled-dxmt=1`, `reset-rung` leaves the wineboot-made winemetal entries alone (A.8).

Knobs to use only when their signature appears:
- Steam processes crash inside libd3dshared: A/B with `--no-d3dshared`.
- Login loops on "EConnect called - scheduling connection" with "Schedule init returned 22": this is the llvm-mingw kernelbase signature (frankea/Whisky#163). Check the toolchain line in BUILDINFO.
- The UI goes unresponsive after about 11-13 game launches: rpcrt4 waits on more than 64 handles (Wine bug 60334). Restart Steam. An optional rpcrt4 patch (bug 55705, attachment 82326) is untested.
- A brand-new client quits about 3 minutes after its first self-update, or logs "nested exception on signal stack": relaunch (steam-for-linux#13576; Highball steam.json).
- "NO CONNECTION" right after login: quit the native macOS Steam client.
- A Steam main-loop stall with the steamclient64 → winmm → mmdevapi IsFormatSupported stack: the winmm standby patch (2.7, entry 20).

M6.3 Sign-in (Daniel). The agent runs the rung under test as `steam.sh ui --hold [--dxmt]` with that rung's `reset-rung` options first. The lock owner is then `steam-daniel`, which `steam.sh stop` refuses without `--force`, and once the sign-in window is up (S5 passes) the session only records dialogs and never ends itself, so nothing the agent runs can close the window while Daniel uses it (R2-9):
1. At the time slot agreed in M0.12, the agent starts the session and tells you when the sign-in window is up. From then on the window is yours, and the agent starts no other Wine session (4.9).
2. Sign in, approve the Steam Guard code, and tick "Remember me".
3. Wait until the Library appears, then tell the agent.
4. Never press Install, Update or Verify for Elden Ring in this Steam, and never start games from Steam's Play button. The game folder there is the agent's clone (M7.1), which this Steam does not manage.
5. When you are done, quit with Steam > Exit. Or tell the agent "done": it writes your go-ahead into BUILD_LOG and then runs `steam.sh stop --force`.

M6.4 Check the headless session and pin the client (review C22). `steam.sh stop`, then `steam.sh silent --msync 0` must pass S7. As soon as S6 has passed, pin the client, so that self-updates stop changing the variable under test:
```bash
printf 'BootStrapperInhibitAll=enable\nBootStrapperForceSelfUpdate=disable\n' > "$HOME/Games/prefixes/cx_prefix/drive_c/Program Files (x86)/Steam/Steam.cfg"
```

The offline-mode check (review C7), formerly M6.4b, needs the Elden Ring clone, so it runs as M7.1b (R1-13).

M6.5 `steam.sh stop`, `backup-userdata.sh`, then the snapshot one-liner of M6.2 step 3 with the tag `m6-steam-ok` (R3-6). Record the winning rung in BUILD_LOG; it becomes the runner's Steam profile in M9.

M6.6 Unpinning is a cycle of its own: remove `Steam.cfg`, let Steam update once, then re-run S-core and S-UI. Do it before Steam's minimum-version enforcement catches up, and never in the same cycle as another change.

### M7: Elden Ring (1-4 h, plus Daniel's play test)

M7.1 Clone the game files into `cx_prefix` and check the EAC bypass (review C8). The bypass is already applied in `default_prefix`'s copy, and Valve's `steam_api64.dll` is restored. The block is a session of its own: Steam is stopped and nothing of the runtime runs while the old clone is deleted (R3-8).
```bash
X=~/projects/m5-wine-runner-cx/scripts/cx; "$X/steam.sh" stop || exit 1; source "$X/lib.sh"; begin_session er-clone idle
A="$P/drive_c/Program Files (x86)/Steam/steamapps"; C="$A/common"; mkdir -p "$C"
rm -f "$A/appmanifest_1245620.acf"   # first: a cx Steam that installed or verified the game forgets it (M7 table)
rm -rf "$C/Elden Ring"          # only ever cx_prefix's clone; cp -Rc onto an existing folder would nest the copy inside it
cp -Rc "$HOME/Games/prefixes/default_prefix/drive_c/Program Files (x86)/Steam/steamapps/common/Elden Ring" "$C/Elden Ring"
G="$C/Elden Ring/Game"; cmp "$G/eldenring.exe" "$G/start_protected_game.exe" && cat "$G/steam_appid.txt" \
  && cmp "$G/steam_api64.dll" "$G/steam_api64.dll.valve_bak" && echo eac-bypass-ok      # prints 1245620 and eac-bypass-ok
test ! -e "$A/appmanifest_1245620.acf" && echo no-appmanifest
```
Both prefixes are on the same APFS volume, so `cp -Rc` clones the 52 GB folder without using space until files change. Nothing done in the cx Steam can reach `default_prefix`, and the F6 tripwire (`baseline-er.sha256`) still guards its copy. The `rm -rf` makes a re-run safe (R2-15): BSD `cp -Rc src dst` onto an existing `dst` creates `dst/Elden Ring` and leaves the changed files in place, so the `cmp` checks would fail again (reproduced in a scratch directory). `steam.sh stop` refuses while a handed-over game holds the lock, and `begin_session … idle` refuses while any process of the runtime runs, so a re-run can neither race a cx Steam that is installing or verifying into the folder nor delete files under a running game.

M7.1b Offline mode (review C7), once, after S6 and M7.1 (formerly M6.4b; `er.sh` refuses without the M7.1 clone, R1-13):
1. `steam.sh stop`, then `steam.sh silent --offline`. Attempt A passes `-offlinemode`, which the current client's option list includes (steam-compat research). Attempt B, only if ActiveUser stays 0, sets `"WantsOfflineMode" "1"` and `"SkipOfflineModeWarning" "1"` in the most recent account's block of `config/loginusers.vdf`. Both are **ASSUMPTIONS**, settled by the ActiveUser check. `silent --offline` writes `offline=1` into `.cx-session`, so `steam.sh status` and S7 drop the connection_log condition, and er.sh keeps the session offline: it restarts it, if at all, with `--offline`, never online (R3-1).
2. Check S7 (ActiveUser non-zero after the reset, D20), then run `er.sh --probe-only` (E1-E3), and record the connection_log state string through `redact.sh`. The BUILD_LOG entry records the mode: `steam.sh status` and the er cycle's gates.txt header both read `offline=1`.
3. Switch back online: `steam.sh stop`, undo the change, `steam.sh silent`.

Never cut the Mac's network for this test: Daniel's other downloads must keep running.

M7.2 Run a session: `eval "$("$X/newcycle.sh" er)"; "$X/er.sh" --msync 0 --duration 300`, as a background job of the agent's shell tool. Every cycle the agent runs alone uses `--duration 300` (or `--probe-only`): the game ends 300 s after the first frame and E1-E7 are written at once, so no `er-daniel` lock waits for an absent Daniel. Only Daniel's play test (M7.3), in the slot agreed through M0.12 and the Daniel queue, runs without `--duration`, which hands the game over (R3-9). `er.sh` (A.8) runs these steps in three phases (review C8, C11, C17, C24, R2-8):
1. **Start.** It takes the session lock (owner `er`; its own PID and that PID's start time) and refuses while any other session holds it (4.9). It starts `caffeinate -w $$`, writes `gates_header N er` as the first line of `gates.txt` (R3-2), then starts the dialog watcher (`watch_dialogs "$CX_LOGS" $$`; its PID and start time go into the lock) and its EXIT trap (step 9).
2. **Pre-flight**, refusing to start on any failure: `preflight_prefix` (promoted prefix, `prefix-check.sh`, GPTK manifest); the M7.1 `cmp` checks; no `appmanifest_1245620.acf`; `d3dm_cache_in eldenring.exe <VER>`, which swaps in this GPTK version's shader cache and records `cache=warm` or `cold` (M7.5). For A/B runs it also records and enforces the hygiene of M7.4. `<VER>` is `--gptk VER` (default 4.0b3), used for every step below (R3-10).
3. **Steam.** If `steam.sh status` does not report Steam ready (S7) with the same msync, `steam.sh stop`, then `steam.sh silent --msync N`, with `--offline` when `.cx-session` reads `offline=1`: an offline session stays offline and is never restarted online (R3-1). Both run inside er.sh's session (`CX_SESSION_PARENT`), so `stop` leaves er.sh's lock in place and `silent` takes none.
4. **Game.** It starts `d3dm-log.sh` (its PID and start time go into `$CX_LOGS/d3dm-log.pid`), then the game from the `Game` directory, bounded by `--max-session` (default 14400 s, 4 h): `with-timeout.sh <max-session> cx-run.sh --d3dmetal <VER> --msync N --debug err+all,warn+seh,+module,+loaddll --log $CX_LOGS/er.log -- eldenring.exe`.
5. **Phase 1, first frame** (review C24, R1-11): `first_frame eldenring.exe "$CX_LOGS" <first-frame-timeout>` (A.9; default 1200 s) captures the game window every 15 s (`capture.sh --pid <game pid>`). The first capture that `is_black PNG hud` calls not black sets `t_first_frame`. The HUD corner is masked because the HUD draws over a black frame too, and loading and shader-compile frames already produce `metal-HUD:` lines, so the first HUD line only sets `t_first_hud` (E5 evidence). Shader compilation can keep the first boot black for minutes, so polling goes on until a frame shows or the limit passes; no fixed +30/+180 s judgement decides E6. After the limit, E6 fails with the black-screen signature (INCONCLUSIVE if every capture met a locked screen), and the game is ended.
6. **Phase 2, probes:** `probe.sh "$CX_LOGS/probe30" eldenring.exe <VER>` at `t_first_frame` + 30 s and `probe.sh "$CX_LOGS/probe180" eldenring.exe <VER>` at + 180 s, each wait through `wait_or_dialog S "$CX_LOGS" <game pid>`. `--probe-only` ends the game after `probe30` (M7.1b).
7. **Dialogs in phases 1 and 2** (review C13, R2-8). Only a dialog owned by the game PID ends the run: `probe.sh` once more for evidence, then the game alone is ended (`kill <game pid>`, `kill -9` after 10 s; the headless Steam keeps running), and `FAIL-dialog` with the dialog PNG goes into `gates.txt`. A dialog of another process, such as Steam's, is recorded as a `DIALOG` line and listed in the gates, but ends nothing.
8. **Phase 3, the game is handed over.** Without `--duration` (only in Daniel's play-test slot, M7.3), er.sh moves the lock's anchor to the game process (`lock_anchor <game pid> er-daniel`), starts a detached `reap_after <game pid> <d3dm-log.sh pid>` (A.9), which ends the log stream when the game exits even if er.sh is gone by then (R3-9), writes `HANDED-OVER <time>` into `gates.txt`, and the agent tells Daniel the game is his (M7.3). It then waits for the game to exit, bounded only by `--max-session`. From now on the watcher only records: no dialog ends the run, and because the lock now lives exactly as long as the game, no other session can start, and no `wineserver -k` can reach the game, even if er.sh itself dies. With `--duration S` (every agent-only cycle and the A/B runs, M7.4) the owner stays `er`, and er.sh ends the game S seconds after the first frame, or S seconds after the file named by `--start-on FILE` appears.
9. **On exit.** "Exit" means any end of er.sh: the game exited; a limit (`--duration`, `--max-session`, the first-frame timeout) or `--probe-only` ended it; a phase-1/2 dialog of the game ended it; or er.sh received SIGTERM, SIGINT or SIGHUP (the EXIT trap; SIGKILL skips it, 4.8). er.sh then ends the game if it still runs, except in an interactive phase 3: there a signalled er.sh leaves the game and its `er-daniel` lock alone, writes `INTERRUPTED` into `gates.txt` and exits; the reaper of step 8 ends `d3dm-log.sh` once the game has exited, and the lock goes stale then (collect and back up later, 4.8). In every other case it stops `d3dm-log.sh`, runs `steam.sh collect "$CX_LOGS/steam-logs"`, `d3dm_cache_out eldenring.exe` and `backup-userdata.sh`, writes gates E1-E9 into `gates.txt` (with `hud-stats.sh` for `--duration` runs), and releases the lock (`release_session`, which also stops the watcher). A headless Steam it started keeps running, without a lock (4.9).

Gates E1-E9:
```text
E1  Steam ready before the game starts (S7: ActiveUser and pid non-zero after the reset, steam.exe of this session alive)
E2  er.log: "Loaded libd3dshared.dylib, does support non-native code regions"
E3  n=$(gptk_mapped "$CX_LOGS/probe30" "$VER" 'd3d12|dxgi') is 2: the probe's lsof and vmmap show both DLLs mapped
    from gptk/<VER>, 4.0b3 unless --gptk (review F15, as H3; R3-10); probe30: one libd3dshared __TEXT image and
    "PASS F4b ..." for that tree
E4  D3DM lines captured (F4)
E5  metal-HUD lines with increasing frame numbers; HUD in the screenshot (F3)
E6  a capture of the game window that 'is_black PNG hud' calls not black, within the first-frame limit, which the agent
    confirms shows the title screen or main menu (F2, part 1). A modal notice that waits for a key, or a locked screen,
    makes E6 INCONCLUSIVE, not FAIL
E7  no "page fault on execute access"; no "free_modref ... steamclient64.dll" before the window; no new DiagnosticReports
    wine*.ips; no FAIL-dialog of the game process (DIALOG lines of other processes are listed, R2-8)
E8  (Daniel) at least 10 min in-game without a crash; HUD FPS in a typical scene recorded as the baseline (F2, part 2)
E9  record whether er.log has 'disabling no-exec because of L"bink2w64.dll"' (expected on the base build; input to M7.6, review C3)
```

M7.3 Play test (Daniel):
1. At the time slot agreed in M0.12, the agent runs `er.sh` without `--duration` and tells you when the game window is up and handed to you (phase 3). From then on the game is yours: no agent script can close it, and it is only closed if it is still running after 4 hours.
2. Once only: open System > Network and set Launch Setting to "Start offline". Without EAC the game may otherwise stop at a network notice that waits for a key.
3. At the title screen press any key or button, then choose Continue, Load Game or New Game.
4. Play for at least 10 minutes: walk, fight, open the map, rest at a Site of Grace.
5. Note the HUD FPS in a typical scene, then quit with System > Quit Game.
6. Tell the agent the FPS you noted. er.sh has already collected the logs, evaluated gates E1-E9 and backed up your save when the game closed.

M7.4 msync A/B (review C23, C24, R2-8): `er.sh --msync 1 --duration 300` against `er.sh --msync 0 --duration 300`; each runs Steam headless and the game under the same msync value. The scene is the title-screen backdrop with no input: er.sh ends the game 300 s after the first frame, after both probes, and `hud-stats.sh <log> --last 120` measures the last 120 `metal-HUD` lines (one per second) before the stop, read from whichever log holds them (`er.log` or `d3dm.log`; the ASSUMPTION under M5.3). If Daniel is at hand and wants a gameplay scene, run both arms as `er.sh --msync N --duration 120 --start-on "$CX_LOGS/go"`: he loads in, stands idle at the first Site of Grace and tells the agent, which runs `touch "$CX_LOGS/go"`, and er.sh ends the game 120 s later. Run only when `pgrep -x wineserver` lists this session's server alone, no build runs (`pgrep -f build-wine-cx.sh` prints nothing), and the 1-minute load average is below 8; `gates.txt` records `uptime`. Compare the median and p95 frame interval (`hud-stats.sh`). Adopt msync for game sessions if it is at least 10% faster and adds no new errors; Highball measured about 40% in other games. The Steam UI stays at msync 0.

M7.5 Shader cache (review C24, R2-11). The first boot can show a black screen for minutes while D3DMetal compiles shaders. D3DMetal keeps one cache directory per executable, `$(getconf DARWIN_USER_CACHE_DIR)d3dm/<exe>/` (GPTK Read Me; `getconf` ends the path with a slash). On this Mac `d3dm/` already holds GPTK 7.7's `steam.exe/` and `steamwebhelper.exe/`, and the 3.0 tree, the 4.0b3 tree and any GPTK 7.7 run of Elden Ring would all use `d3dm/eldenring.exe/`. So `er.sh --gptk VER` moves only that one directory, with lib.sh's `d3dm_cache_in` and `d3dm_cache_out` (A.9):
- At start, whatever `d3dm/eldenring.exe` holds is parked in `d3dm.cx-stash/original/` next to `d3dm`. An unmarked directory there belongs to another runtime (GPTK 7.7), so it is never mixed with ours. Then this version's own cache comes back from `d3dm.cx-stash/<VER>/` (warm) or starts empty (cold), and `d3dm.cx-stash/active-eldenring.exe` records the version in use.
- On exit, the cache goes back to `d3dm.cx-stash/<VER>/` and the parked original returns, so outside er.sh sessions `d3dm/` looks exactly as GPTK 7.7 left it. If er.sh died without its trap, the next `d3dm_cache_in` reads the `active-…` file and files the cache under that version first.
- Other executables' directories are never touched. Every BUILD_LOG entry notes `cache=warm` or `cold`. To rule out corruption, delete only that version's copy, `d3dm.cx-stash/<VER>/eldenring.exe`, while no er.sh runs. The M5.3 block treats the test programs the same way.

M7.6 hb-0013 A/B (review C3). If E9 shows the bink2w64 line, enable hb-0013 in `series` (one cycle: `build-wine-cx.sh from src`, then promote). Keep the scene, the msync value and the cache state, and run under the M7.4 hygiene. Compare the median and p95 frame interval and the seconds from launch to the title screen against the base build; switch back by promoting the base build id (4.7). Adopt hb-0013 if it is at least 10% better and adds no new errors. Record the result either way.

Failure modes M7

| Symptom | Diagnosis | Fix |
|---|---|---|
| "Steam not running", or the game exits right after start | Steam is not ready in this session, or `WINEMSYNC` differs from the running server's: steam.log or er.log has "Server is running with WINEMSYNC but this process is not" or "Failed bootstrap_look_up" (`msync.c:600, 636`) | S7 first; use the same `--msync` for Steam and the game; `steam.sh stop`, then start again (R2-14) |
| `free_modref ... steamclient64.dll`, then "page fault on execute access" at exit | SteamAPI_Init failed and steam_api unloaded steamclient64 (use-after-unload; research analysis of `~/Games/logs/er-gptk3.log`) | Fix the Steam logon |
| er.sh: REFUSE, `appmanifest_1245620.acf` exists | somebody pressed Install or Verify in the cx Steam | Redo M7.1: under its own lock it stops Steam, deletes the appmanifest, then the old clone, and clones again (R3-8) |
| er.sh: REFUSE, the cmp checks fail | the clone lost the bypass (Steam verified it) | Redo M7.1. Its `rm -rf` of the old clone comes first: `cp -Rc` onto an existing folder nests the copy inside it and keeps the changed files (R2-15) |
| er.sh: "REFUSE: session lock held" | another session runs: a Steam UI session, a test block or promote | `steam.sh status`; end an agent-run Steam UI session (`steam-ui`) with `steam.sh stop`; for a session handed to Daniel (`steam-daniel`) or any other owner, wait for it to finish (4.9) |
| E6 INCONCLUSIVE: a notice waits for a key | no EAC, so the game warns about online play | Daniel sets "Start offline" (M7.3 step 2) |
| Black screen for 20 minutes | shader compilation, or no present | M7.5 cache; the D3DM lines; H6 chain |
| 0xc000001d illegal instruction | AVX not advertised | Check `ROSETTA_ADVERTISE_AVX=1` with `ps eww` |
| Crash around `amd_ags_x64.dll` or `atidxx64` lookups | GPTK 4.0b3 dropped `atidxx64`, so the placeholder finds no builtin | A/B with `--gptk 3.0`, which ships `atidxx64` |
| Crash on fiber switches, or a hang with a black window at full CPU | CrossOver 26.3 keeps the pre-Wine-10.5 macOS %gs model | Enable the standby set hb-0008+0009+0011+0016 (verified to apply) in `series`, then `build-wine-cx.sh from src` (route B, 4.5). `iter` would skip the stamped src stage and rebuild the old tree (R1-18) |
| Hang at a loading screen with low CPU | lost wake-ups on an auto-reset event | Standby hb-0005 |
| Poor frame times with E9's no-exec line | NX off for the whole process under Rosetta | M7.6 (hb-0013) |
| Crash when ray tracing is enabled in-game | DXR is on by default on M3 and later | A/B `D3DM_SUPPORT_DXR=0` |
| Controller not detected | winebus SDL path or controller mapping | The WineBus service-key values in 2.4 (review F6) |
| Audio dropouts | 48 kHz I/O buffer | Standby hb-0015 |
| The game ran on wined3d | Started from Steam's Play button | Launch only through `er.sh` or the runner (D16) |

### M8: MetalFX (1-3 h, plus a download for the Steam test)

Elden Ring has no DLSS, so F2-F4 do not depend on this milestone. M8.0-M8.3 and X6 need no Steam. They run in the DLSS test prefix `cx_dlss`, each block as a session of its own (R1-3, R1-12): it takes the session lock, refuses while any process of the runtime runs (stop a headless Steam first), and its `wineserver -k` reaches only `cx_dlss`. Capture, probe and the dialog watcher see only `cx_dlss`'s processes, so the sample's expected Error box (X4) can never land in a Steam cycle. The prefix also keeps the DLSS-only registry values, and Apple's nvngx/nvapi64 copies if M8.3 step 1 needs them, away from the prefix where Steam and Elden Ring live. Only M8.4 uses Steam, so it runs after M7, and only then does `cx_prefix` get the DLSS setup with which the sample passed (R3-4).

M8.0 Create `cx_dlss`. It is a promoted prefix like `cx_prefix`: `promote` updates, stamps and checks it too (M3.5), and `cx-run.sh` refuses renderer modes on it until it is stamped (2.4).
```bash
X=~/projects/m5-wine-runner-cx/scripts/cx; export CX_PREFIX_NAME=cx_dlss; source "$X/lib.sh"; begin_session dlss-setup idle   # P=.../cx_dlss
"$X/with-timeout.sh" 300 "$X/cx-run.sh" --prefix cx_dlss -- wineboot -i \
  && "$X/with-timeout.sh" 120 "$X/cx-run.sh" --prefix cx_dlss -- winecfg -v win10 \
  && "$X/with-timeout.sh" 300 "$X/cx-run.sh" --prefix cx_dlss -- wineserver -w || exit 1       # 142: timeout
printf 'disable\n' > "$P/.update-timestamp"
head -1 ~/Games/sdk/wine-cx26/BUILDINFO > "$P/.m5runner-runtime"
"$X/with-timeout.sh" 120 "$X/cx-run.sh" --prefix cx_dlss -- reg add 'HKCU\Software\Wine\WineDbg' /v ShowCrashDialog /t REG_DWORD /d 0 /f || exit 1
"$X/prefix-check.sh" cx_dlss                                       # 8 PASS lines
"$X/cx-run.sh" --prefix cx_dlss -- wineserver -k || true           # exit 1 only means no server was left (R3-16)
```

M8.1 Prerequisites, set in `cx_dlss` before the sample's first launch (review C1). Both are harmless if unused; Proton, DXMT and Heroic set the same. `PN` selects the prefix: M8.4 runs the same block with `PN=cx_prefix` (after `steam.sh stop`) before the first Wukong launch (R3-4, R3-17):
```bash
X=~/projects/m5-wine-runner-cx/scripts/cx; PN="${PN:-cx_dlss}"; export CX_PREFIX_NAME="$PN"; source "$X/lib.sh"; begin_session dlss-setup idle
"$X/with-timeout.sh" 120 "$X/cx-run.sh" --prefix "$PN" -- reg add 'HKLM\SOFTWARE\NVIDIA Corporation\Global\NGXCore' /v FullPath /t REG_SZ /d 'C:\Windows\System32' /f || exit 1
mkdir -p "$P/drive_c/ProgramData/NVIDIA/NGX/models" && : > "$P/drive_c/ProgramData/NVIDIA/NGX/models/nvngx_config.txt"
"$X/cx-run.sh" --prefix "$PN" -- wineserver -k || true             # exit 1 only means no server was left (R3-16)
```

M8.2 A/B the DLSS sample: NVIDIA's DLSS SDK release v310.9.16, asset `ngx_dlss_demo_windows.zip` (sha256 `ae025a276ed03d35fab05157acc528c23dac17be7d7ded81bfd26d6e0de0e092`, already at `research/metalfx/dlss-demo-zip/`), a prebuilt, legally downloadable binary that renders Sponza with `-d3d12`, `-d3d11` or `-vulkan`. It calls `NvAPI_Initialize` at startup (`DemoMain.cpp:1260`), which resolves to Apple's nvapi64 through the system32 placeholder in game processes. Its DLSS path then calls NGX directly, with no Streamline gate (review C18 corrected the earlier "no NVAPI" wording). Every log line it writes goes to `OutputDebugStringA`, which Wine prints only on the warn channel of `seh` (`wine/dlls/kernelbase/debug.c:42, 182-190`), so every launch uses `warn+seh` (review C1). A dialog ends a run as soon as the watcher sees it (review C13).
```bash
X=~/projects/m5-wine-runner-cx/scripts/cx; export CX_PREFIX_NAME=cx_dlss; source "$X/lib.sh"; begin_session dlss idle
eval "$("$X/newcycle.sh" metalfx)"; L="$CX_LOGS"; gates_header 0 metalfx > "$L/gates.txt"      # R3-2
OV=; if [ -e "$P/.cx-dlss-copies" ]; then OV=~/Games/sdk/gptk/4.0b3-overlay/wine; fi   # after M8.3 step 1, as the M8.4 launch (R4-5)
echo "setup: Apple copies and alias overlay: ${OV:-no}" >> "$L/gates.txt"
T="$P/drive_c/tests"; mkdir -p "$T"
ditto -x -k ~/Games/src/research/metalfx/dlss-demo-zip/ngx_dlss_demo_windows.zip "$T/"
cd "$T/DLSS_Sample_App/bin/ngx_dlss_demo"
for fx in 1 0; do
  D="$L/fx$fx"; mkdir -p "$D"; gates_header 0 "metalfx-fx$fx" > "$D/gates.txt"       # the watcher appends DIALOG lines
  watch_dialogs "$D" $$ & WP=$!
  "$X/d3dm-log.sh" "$D/d3dm.log" & LP=$!
  CX_PREPEND_EXTRA="$OV" CX_METALFX=$fx "$X/with-timeout.sh" 120 "$X/cx-run.sh" --prefix cx_dlss --d3dmetal 4.0b3 --debug err+all,warn+seh,+module,+loaddll \
     --log "$D/demo.log" -- ngx_dlss_demo.exe -d3d12 -width 1280 -height 720 & AP=$!
  wait_or_dialog 60 "$D" || echo "dialog seen at $(date +%T): run ended (expected for fx0, X4; a FAIL for fx1, X2)" >> "$D/probe.txt"
  "$X/probe.sh" "$D" ngx_dlss_demo.exe >> "$D/probe.txt"
  "$X/cx-run.sh" --prefix cx_dlss -- wineserver -k; rc=0; wait "$AP" || rc=$?; echo "exit=$rc" >> "$D/probe.txt"
  kill "$LP" "$WP" 2>/dev/null
done
```

Gates X1-X6 (X7 and X8 belong to M8.4):
```text
X1  n=$(gptk_mapped "$L/fx1" 4.0b3 nvngx) is 1: the probe's lsof and vmmap of the fx1 run show nvngx.dll mapped from
    gptk/4.0b3 (placeholder -> GPTK builtin; review F15: the +module trace names only system32\nvngx.dll). When cx_dlss
    holds Apple's copies (.cx-dlss-copies, after M8.3 step 1), the system32 copy counts too: X1 is then judged with the
    M8.3 step-1 grep on fx1/lsof.txt, which shows which of the two files was mapped (R3-18)
X2  fx1: no Error dialog (no FAIL-dialog), and the warn+seh log has none of "DLSS not available. Shutting down NGX.",
    "NVIDIA NGX not available on this hardware/platform" and "Requested NGX DLSS Feature not supported"
X3  fx1 screenshot: HUD row "MetalFX Scaling" (temporal) with input resolution below target
X4  fx0: the warn+seh log has "Requested NGX DLSS Feature not supported" and an Error dialog was captured
    (fx0/dialog-*.png and its DIALOG line; GPTK Read Me: 0 makes DLSS unavailable)
X5  the D3DM lines that differ between fx1 and fx0 are recorded in BUILD_LOG (the activation text is undocumented)
X6  vendor switch (review F18): d3d12_clear.exe prints vendor=0x10de with CX_METALFX=1 and vendor=0x1002 with
    D3DM_ENABLE_METALFX unset (community-reported; ASSUMPTION until this runs)
```
X4 differs from the review's proposal (review C1), which asked for exit code 1. The sample shows its MessageBox before it returns 1 (`donut/src/core/log.cpp:46-54`, `DemoMain.cpp:1311-1314`), so the process blocks until someone dismisses the box. The watcher captures the box, `wait_or_dialog` ends the wait, and the harness ends the run with `wineserver -k`. The captured dialog plus the log line is the observable equivalent; the exit code is recorded whenever it is available. The same dialog in an fx1 run is a FAIL-app-error.

X6 commands (a cycle of its own, because the variable differs). The second run leaves `D3DM_ENABLE_METALFX` unset, the 2.3 default for games without DLSS, which is the case the vendor question is about:
```bash
X=~/projects/m5-wine-runner-cx/scripts/cx; export CX_PREFIX_NAME=cx_dlss; source "$X/lib.sh"; begin_session x6 idle
eval "$("$X/newcycle.sh" x6-vendor)"; L="$CX_LOGS"; gates_header 0 x6-vendor > "$L/gates.txt"      # R3-2
T="$P/drive_c/tests"; mkdir -p "$T"; cp ~/Games/build.noindex/cx26/tests/bin/d3d12_clear.exe "$T/"; cd "$T"
CX_METALFX=1 "$X/with-timeout.sh" 60 "$X/cx-run.sh" --prefix cx_dlss --d3dmetal 4.0b3 --log "$L/x6-fx1.log" -- d3d12_clear.exe 3
CX_METALFX= "$X/with-timeout.sh" 60 "$X/cx-run.sh" --prefix cx_dlss --d3dmetal 4.0b3 --log "$L/x6-unset.log" -- d3d12_clear.exe 3
/usr/bin/grep -H '^adapter' "$L"/x6-*.log | tee -a "$L/gates.txt"
"$X/cx-run.sh" --prefix cx_dlss -- wineserver -k || true           # exit 1 only means no server was left (R3-16)
```
Also run the sample once with `-d3d11`. It settles whether D3DMetal bridges D3D11 NGX calls, an open question. If it does not, D3D11 DLSS titles go to DXMT with `DXMT_ENABLE_NVEXT=1`.

M8.3 If X1-X3 fail, try these one variable per cycle, in this order, both in `cx_dlss` (the Steam title test is M8.4, which always runs):
1. Apple's documented route (review C18). `scripts/cx/stage-dlss-copies.sh cx_dlss` (A.14) copies `nvngx.dll` and `nvapi64.dll` from the GPTK tree into system32. It also writes the marker `$P/.cx-dlss-copies`, which holds the realpath of `~/Games/sdk/gptk/4.0b3/wine`: `prefix-check.sh` reads it as `<marker>/x86_64-windows/<dll>` (R1-4, R1-14), and `promote` copies the files again after its forced `wineboot -u`, which would otherwise turn them back into placeholders. The script ends with `prefix-check.sh`, which must print 8 PASS lines; gate T14 tests the same contract in `cx_smoke`. Builtin lookup goes by the PE export name, and Apple's nvapi64 reportedly exports `nvapi.dll` (metalfx research; `loader.c:1521-1560`). So add the alias in an overlay, never inside the verified 4.0b3 tree:
```bash
X=~/projects/m5-wine-runner-cx/scripts/cx; export CX_PREFIX_NAME=cx_dlss; source "$X/lib.sh"; begin_session m83 idle
eval "$("$X/newcycle.sh" m83-dlss-copies)"; L="$CX_LOGS"; gates_header 0 m83-dlss-copies > "$L/gates.txt"      # R3-2
G=$(cd ~/Games/sdk/gptk/4.0b3 && pwd -P); O=~/Games/sdk/gptk/4.0b3-overlay/wine; mkdir -p "$O/x86_64-windows" "$O/x86_64-unix"
cp -p "$G/wine/x86_64-windows/nvapi64.dll" "$O/x86_64-windows/nvapi.dll"     # byte-identical copy under the export name
ln -sf "$G/external/libd3dshared.dylib" "$O/x86_64-unix/nvapi.so"            # absolute: the same image as the 4.0b3 tree
"$X/stage-dlss-copies.sh" cx_dlss || exit 1                                   # ends with prefix-check.sh: 8 PASS lines
cd "$P/drive_c/tests/DLSS_Sample_App/bin/ngx_dlss_demo"
watch_dialogs "$L" $$ & WP=$!
CX_PREPEND_EXTRA="$O" CX_METALFX=1 "$X/with-timeout.sh" 120 "$X/cx-run.sh" --prefix cx_dlss --d3dmetal 4.0b3 \
  --debug err+all,warn+seh,+module,+loaddll --log "$L/m83.log" \
  -- ngx_dlss_demo.exe -d3d12 -width 1280 -height 720 & AP=$!     # WINEDLLPATH_PREPEND=<overlay>:<4.0b3>/wine; hb-0003 splits on ':'
wait_or_dialog 60 "$L" || echo "FAIL-dialog (see dialog-*.png)" >> "$L/gates.txt"
"$X/probe.sh" "$L/m83" ngx_dlss_demo.exe > "$L/m83-probe.txt"
"$X/cx-run.sh" --prefix cx_dlss -- wineserver -k; wait "$AP"; kill "$WP" 2>/dev/null
```
   Judge X1 on the probe's own listing, not on the `+module` trace, which names only the requested system32 file (review F15): `/usr/bin/grep -cE '/(gptk/4\.0b3/wine/x86_64-windows|drive_c/windows/system32)/nvngx\.dll' "$L/m83/lsof.txt"` must print at least 1, because with the copies in place Wine may map either the GPTK builtin or the system32 copy. Judge X2 and X3 on `m83.log` and the probe screenshot.
2. The NVIDIA signature-override value (review F14), before F5 may be marked pending. DXMT's NVEXT mode and yaagl set it; whether D3DMetal's nvngx needs it is open. Set it in `cx_dlss`, then re-run the M8.2 block (a new cycle) and compare X1-X3 with the earlier M8.2 cycle. Step 2 runs on top of step 1: while `cx_dlss` holds Apple's copies, the M8.2 block also prepends the alias overlay, as the M8.4 launch does, so the setup that passes is the one M8.4 copies (R4-5). M8.4 runs the same block with `PN=cx_prefix` (R3-4, R3-15):
```bash
X=~/projects/m5-wine-runner-cx/scripts/cx; PN="${PN:-cx_dlss}"; export CX_PREFIX_NAME="$PN"; source "$X/lib.sh"; begin_session m83 idle
r() { "$X/with-timeout.sh" 120 "$X/cx-run.sh" --prefix "$PN" -- reg add "$@" /f || exit 1; }   # 142: timeout
r 'HKLM\SOFTWARE\NVIDIA Corporation\Global' /v '{41FCC608-8496-4DEF-B43E-7D9BD675A6FF}' /t REG_DWORD /d 1
r 'HKLM\SYSTEM\ControlSet001\Services\nvlddmkm' /v '{41FCC608-8496-4DEF-B43E-7D9BD675A6FF}' /t REG_DWORD /d 1
"$X/cx-run.sh" --prefix "$PN" -- wineserver -k || true             # exit 1 only means no server was left (R3-16)
```

M8.4 The Steam title test (required for F5; R2-13): the Black Myth: Wukong Benchmark Tool (AppID 3132990, free; Unreal Engine 5 with DLSS super resolution and frame generation through Streamline, metalfx research). It always runs, after M7, whether or not the sample passed: the sample calls NGX directly, while shipping DLSS titles go through Streamline, NVAPI with hardware scheduling and a Steamworks launch, which only a Steam title exercises. It runs in `cx_prefix`, where Steam lives. Daniel approves the download first (M0.12).

Before the first launch, `cx_prefix` gets the DLSS setup with which the sample passed (R3-4, R3-17). Each step is a cycle and a session of its own after `steam.sh stop`, and goes into BUILD_LOG:
1. The prerequisites of 2.4: the M8.1 block with `PN=cx_prefix` (`NGXCore FullPath` and an empty `nvngx_config.txt`). The launch block refuses to start without them.
2. Exactly the M8.3 variables with which the sample passed X1-X3: nothing when M8.2 passed as it is, and nothing yet when the sample never passed (the X7 failure step below then tries them in `cx_prefix`). After M8.3 step 1: the block below, which stages Apple's copies (promote then keeps them) and makes sure the nvapi alias overlay exists; the launch block adds that overlay through `CX_PREPEND_EXTRA` whenever `cx_prefix` holds the copies marker. After step 2: also the M8.3 step-2 block with `PN=cx_prefix`, because the sample passed step 2 with step 1's copies and overlay still in place (R4-5).
```bash
X=~/projects/m5-wine-runner-cx/scripts/cx; source "$X/lib.sh"; begin_session m84-dlss-copies idle   # P=~/Games/prefixes/cx_prefix
G=$(cd ~/Games/sdk/gptk/4.0b3 && pwd -P); O=~/Games/sdk/gptk/4.0b3-overlay/wine; mkdir -p "$O/x86_64-windows" "$O/x86_64-unix"
cp -p "$G/wine/x86_64-windows/nvapi64.dll" "$O/x86_64-windows/nvapi.dll"; ln -sf "$G/external/libd3dshared.dylib" "$O/x86_64-unix/nvapi.so"
"$X/stage-dlss-copies.sh" cx_prefix || exit 1      # ends with prefix-check.sh: 8 PASS lines
```

Install, route A (the cx Steam draws its window; R1-24). The agent runs `steam.sh stop` (er.sh leaves a headless Steam running, R3-14), then `steam.sh ui --hold` on the winning rung (owner `steam-daniel`, M6.3), then `steam.sh open steam://install/3132990`, which hands the URL to the running client inside that session (A.8). Daniel:
1. The agent tells you when the install dialog is up.
2. Keep the default library folder and confirm the install (Next, then Finish, or Install).
3. Wait until the Library lists the benchmark as installed (the download size is not known yet), then tell the agent.
4. Do not press Play: the agent launches it. Quit with Steam > Exit, or tell the agent you are done.

The agent then records the install folder's name:
```bash
X=~/projects/m5-wine-runner-cx/scripts/cx; source "$X/lib.sh"
A="$P/drive_c/Program Files (x86)/Steam/steamapps/appmanifest_3132990.acf"
sed -n 's/^[[:space:]]*"installdir"[[:space:]]*"\([^"]*\)".*/\1/p' "$A" > "$CXB/wukong.installdir"; cat "$CXB/wukong.installdir"
```

Install, route B (F1 is "headless only" and the reference runtime drew for the L6 sign-in). The agent runs `steam.sh --ref ui --hold` (R3-3), then `scripts/cx/ref-run.sh -- 'C:\Program Files (x86)\Steam\steam.exe' steam://install/3132990`, which the running reference client takes. Daniel follows route A's steps 1-4 in that window; the agent never runs `steam.sh --ref stop`, nor `steam.sh --ref ui` again, while the window is his, and retries a failed hand-off with the `ref-run.sh` line alone (R4-4).

Install, route C (F1 is "headless only" and the CrossOver trial drew for the L6 sign-in). Our scripts cannot drive a trial bottle, so Daniel installs it there:
1. Open CrossOver, select the bottle you signed in with for L6, and start Steam in it.
2. In Steam's Store, search for "Black Myth: Wukong Benchmark Tool", open its page and click its free download button.
3. Keep the default library folder and confirm.
4. Wait until the Library lists it as installed, then quit with Steam > Exit.
5. Tell the agent the bottle's name.

Routes B and C end with an APFS clone of the benchmark's own folder into `cx_prefix`, as M7.1 does for Elden Ring. Only the game's files are copied (Steam downloaded them; nothing of CrossOver or of the reference build comes along), and the cx Steam gets no appmanifest, so it never manages the copy:
```bash
X=~/projects/m5-wine-runner-cx/scripts/cx; source "$X/lib.sh"
SRCP="$HOME/Games/prefixes/cx_ref_prefix"          # route C: SRCP="$HOME/Library/Application Support/CrossOver/Bottles/<bottle name>"
SA="$SRCP/drive_c/Program Files (x86)/Steam/steamapps"
I="$(sed -n 's/^[[:space:]]*"installdir"[[:space:]]*"\([^"]*\)".*/\1/p' "$SA/appmanifest_3132990.acf")"
{ [ -n "$I" ] && [ -d "$SA/common/$I" ]; } || { echo "no installed benchmark under $SA" >&2; exit 1; }
D="$P/drive_c/Program Files (x86)/Steam/steamapps/common"; mkdir -p "$D"
rm -rf "$D/$I"; cp -Rc "$SA/common/$I" "$D/$I" && printf '%s\n' "$I" > "$CXB/wukong.installdir"
```

Launch (agent). A session of its own, without `idle`, because the headless Steam must keep running. It starts the shipping exe directly with the D3DMetal environment, `--steam-appid 3132990` (exports `SteamAppId` and `SteamGameId`) and `CX_METALFX=1`; without the app id, Steamworks relaunches the exe through Steam, where it inherits Steam's environment and gets no D3DMetal (review C18). NVAPI stays enabled for this exe (no `DllOverrides` entry): `--d3dmetal` sets `CX_ACTIVE_GRAPHICS_BACKEND=d3dmetal`, and Streamline needs the hardware scheduling it turns on (`d3dkmt.c:715-731`). Like er.sh, the block waits for the first frame, and a dialog of the benchmark in that phase ends the run. Once the window is handed to Daniel, it moves the lock's anchor to the benchmark process (owner `m84-daniel`) and only records: a screenshot every 30 s and the process's lsof every 60 s, until Daniel quits it, bounded by 3600 s. Run it as a background job. The dialog watcher starts before the Steam check, so a Steam error dialog during the headless start is recorded too (`silent` runs no watcher of its own inside a session; R3-13). **ASSUMPTION:** the shipping exe matches `*/Binaries/Win64/*-Win64-Shipping.exe`, as Unreal Engine games ship it; record the real path at the first launch.
```bash
X=~/projects/m5-wine-runner-cx/scripts/cx; source "$X/lib.sh"; begin_session m84-wukong      # no 'idle': headless Steam stays
[ -e "$P/drive_c/ProgramData/NVIDIA/NGX/models/nvngx_config.txt" ] || { echo "REFUSE: run the M8.1 block with PN=cx_prefix first" >&2; exit 1; }
OV=; if [ -e "$P/.cx-dlss-copies" ]; then OV=~/Games/sdk/gptk/4.0b3-overlay/wine; fi   # M8.3 step 1 = copies + nvapi alias overlay
eval "$("$X/newcycle.sh" m84-wukong)"; L="$CX_LOGS"; mkdir -p "$L/shots" "$L/lsof"
gates_header 0 m84-wukong > "$L/gates.txt"; echo "M8.4 setup: Apple copies and alias overlay: ${OV:-no}" >> "$L/gates.txt"
watch_dialogs "$L" $$ & WP=$!                                                   # before Steam starts (R3-13)
{ [ "$(sed -n 's/^msync=//p' "$P/.cx-session" 2>/dev/null)" = 0 ] && "$X/steam.sh" status > /dev/null; } \
  || { "$X/steam.sh" stop && "$X/steam.sh" silent --msync 0; } || exit 1           # a ready headless Steam with msync 0
W="$P/drive_c/Program Files (x86)/Steam/steamapps/common/$(cat "$CXB/wukong.installdir")"
EXE="$(find "$W" -path '*/Binaries/Win64/*-Win64-Shipping.exe' | head -1)"
[ -n "$EXE" ] || { echo "no *-Win64-Shipping.exe under $W" >&2; exit 1; }
N="$(basename "$EXE")"; cd "$(dirname "$EXE")" || exit 1; printf '3132990\n' > steam_appid.txt
"$X/d3dm-log.sh" "$L/d3dm.log" & LP=$!
CX_PREPEND_EXTRA="$OV" CX_METALFX=1 "$X/with-timeout.sh" 3600 "$X/cx-run.sh" --d3dmetal 4.0b3 --steam-appid 3132990 --msync 0 \
  --debug err+all,warn+seh,+module --log "$L/wukong.log" -- "$N" & AP=$!
s="$(first_frame "$N" "$L" 1200)"; rc=$?; gp="$(game_pid "$N")"
if [ "$rc" -eq 0 ] && [ -n "$gp" ] && wait_or_dialog 30 "$L" "$gp"; then
  echo "first frame after ${s}s" >> "$L/gates.txt"; "$X/probe.sh" "$L/probe" "$N" > "$L/probe.txt"
  lock_anchor "$gp" m84-daniel; export CX_SESSION_PARENT="$gp"                 # the lock now lives as long as the benchmark
  detach /bin/bash -c 'source "$0"; reap_after "$1" "$2"' "$X/lib.sh" "$gp" "$LP" &   # the log stream ends with it (R3-9)
  echo "HANDED-OVER $(date +%T): Daniel runs the benchmark (M8.4 steps)" >> "$L/gates.txt"
  i=0
  while [ -n "$(game_pid "$N")" ]; do                                           # Daniel quits it; with-timeout bounds it
    "$X/capture.sh" --pid "$gp" "$L/shots/$(date +%H%M%S).png" > /dev/null 2>&1
    if [ $((i % 2)) -eq 0 ]; then lsof -p "$gp" > "$L/lsof/$(date +%H%M%S).txt" 2>/dev/null; fi
    i=$((i + 1)); sleep 30
  done
  release_session m84-daniel "$gp"
else
  echo "no usable first frame (first_frame rc=$rc: 1 a dialog of $N, 2 not running or limit, 3 locked screen; or a dialog within 30 s)" >> "$L/gates.txt"
  if [ -n "$gp" ]; then kill "$gp" 2>/dev/null; sleep 10; kill -9 "$gp" 2>/dev/null; fi
fi
wait "$AP"; kill "$LP" "$WP" 2>/dev/null
cat "$L"/lsof/*.txt > "$L/lsof-all.txt" 2>/dev/null
s7=-; if [ -n "$OV" ]; then s7="$(/usr/bin/grep -cE '/drive_c/windows/system32/nvngx\.dll' "$L/lsof-all.txt")"; fi   # R3-5
echo "X7 evidence: nvngx.dll mapped from gptk/4.0b3: $(gptk_mapped "$L/lsof-all.txt" 4.0b3 nvngx), from system32 (Apple copy): $s7" >> "$L/gates.txt"
echo "msync mismatch lines: $(/usr/bin/grep -cE 'Failed bootstrap_look_up|Server is running with WINEMSYNC' "$L/wukong.log")" >> "$L/gates.txt"   # want 0
```

Benchmark run (Daniel):
1. The agent tells you when the benchmark's window is up and handed to you. From then on it is yours; it is closed only if it is still running after an hour.
2. In its settings, choose NVIDIA DLSS as the upscaler (the menu may call it Super Resolution), any quality mode below native, and switch Frame Generation on if it is offered.
3. Start the benchmark run and leave the Mac alone until the results screen shows (a few minutes).
4. Tell the agent what the menu offered, for example "DLSS greyed out" or "no Frame Generation".
5. Quit the benchmark with its Exit or Quit button.

Gates X7-X8:
```text
X7  (required for F5) a screenshot in shots/ taken during the run shows the HUD row "MetalFX Scaling" with an input
    resolution below the target; lsof-all.txt shows nvngx.dll mapped from gptk/4.0b3 (gptk_mapped = 1), or, when
    cx_prefix holds Apple's copies (.cx-dlss-copies), from either gptk/4.0b3 or system32: Wine may map either file then
    (M8.3 step 1), and the "X7 evidence" line records which (R3-5); no FAIL-dialog of the benchmark before the
    hand-over; no msync mismatch line (S8)
X8  (recorded, not required) with Frame Generation selected, a screenshot shows "MetalFX Frame Interpolator: on". Which
    DLSS features D3DMetal 4.0b3 maps on macOS 26 is undocumented (metalfx research), so "not offered" or "off" is
    recorded as a finding, not a failure
```

If X7 fails, F5 may not read pending yet (R3-15): apply the M8.3 variables that `cx_prefix` does not have yet, one per cycle in M8.3's order (step 1: the copies block above; step 2: the M8.3 step-2 block with `PN=cx_prefix`), and after each re-run the launch block with Daniel's benchmark steps (one Daniel-queue row each).

M8.5 Record the result. If X1-X3 or X7 cannot pass after every M8.3 variable in the prefix of the failing gate (`cx_dlss` for X1-X3, `cx_prefix` for X7), F5 = "pending" with the evidence collected so far and the next test: for Wukong, the FINAL FANTASY XVI DEMO (AppID 2738000) through the same M8.4 route with `D3DM_ENABLE_METALFX=1`.

### M9: Runner integration and automation (4-8 h)

Implement section 5.

M9a is split in two (R1-22). Its code and unit tests start no Wine process, so they can be written any time after M0.6 and fill the waits for Daniel. Its acceptance replays the S-core and E1-E7 gates through the runner, so it needs M6 and M7.
- **M9a code, opt-in:** add the `cx` runtime, `--runtime` and `--gptk`, the cx environment builders, the Steam modes, `import-gptk` into versioned trees, the doctor rows, `build-wine-cx`, the hook refactor (review C9), `m5runner/proc.py` (every subprocess call goes through it, so `M5RUNNER_NO_EXEC=1` stubs them all; 5.2) and the tests (`tests/test_repo_hygiene.py` already landed in M0.6 and the `AGENTS.md` link fix with the plan's commit, R2-17). Acceptance:
  - `uv run m5runner launch elden-ring --runtime cx --dry-run` prints exactly the 2.3 environment, and the parity test against `cx-run.sh --print-env` passes.
  - The protected-prefix test (5.3) runs a real, non-dry-run `launch --runtime cx` with every subprocess stubbed, and leaves a recursive file listing of `gptk_prefix` and `default_prefix` unchanged (review C9).
  - pytest is green, and it started no Wine process: conftest swaps the `subprocess` module of every runner module except `proc.py` for a stub that fails the test, and points `M5RUNNER_GAMES_DIR` at a temporary directory, so the suite never reads the live session lock or a real prefix while Daniel's sessions run (5.3; R2-6, R2-18).
- **M9a acceptance, after M7:** in a session of its own (4.9), `m5runner steam --runtime cx --silent` followed by `m5runner launch elden-ring --runtime cx` reproduces S-core and E1-E7 (the runner nests in that session through `CX_SESSION_PARENT`, 5.2, and the block ends the game before its session ends), and that launch leaves the listings of `gptk_prefix` and `default_prefix` unchanged.
- **M9b, the flip:** done after F1-F4 pass (F1 may read "headless only" with Daniel's OK). `d3dmetal` and `d3dmetal_gptk4` map to `cx`. Acceptance:
  - `m5runner launch elden-ring` uses cx with no flags, and starts Steam headless first when it is not ready. The agent checks this as in M9a, in a new cycle and a session of its own (`begin_session m9b`, no `idle`), so the runner nests and takes no `runner-er` lock. The block runs as a background job (Conventions, long jobs). It writes `gates_header` first, starts `watch_dialogs "$CX_LOGS" $$ &` as M8.4 does, and runs `steam.sh stop` inside the session, so the not-ready path is really exercised. It then starts the launch in the background (`RP=$!`) and waits up to 300 s for `game_pid eldenring.exe` to appear, which covers S7's 120 s plus the game start, recording the seconds as the Steam start time; if the game never appears, the check records FAIL. Only then does it run `first_frame eldenring.exe "$CX_LOGS" 1200`. On every path it ends the game (`kill` of `game_pid eldenring.exe`, `kill -9` after 10 s), then runs `kill "$RP" 2>/dev/null; wait "$RP"`, so nothing the runner started outlives the session (R4-6, R5-2).
  - `--runtime gptk` still gives `wine-gptk`, `gptk_prefix` and `WINEESYNC=1`.
  - DXMT titles still use `wine-staging` and `default_prefix`.
  - `(cd ~/Games/sdk && shasum -a 256 -c --quiet ~/Games/logs/cx/baseline-sdk.sha256)` and the Elden Ring tripwire pass (F6).
  - The dry runs from M0.3 match, except for the intended d3dmetal change.
  - S9 passes with the runner's Steam profile.

### M10: Docs and PR (1-2 h)

- Update README: the Runtimes table gains `cx`, described as "Wine built from CodeWeavers' CrossOver 26.3.0 open-source tarball (LGPL); internal label cx". The Known issue section is rewritten.
- Update AGENTS.md hard rules for the cx runtime:
  - Rule 2 becomes "never copy GPTK into a Wine runtime; on cx it is selected per process from `~/Games/sdk/gptk/<ver>`".
  - Rule 3 becomes "on cx, force d3d1x/dxgi to b".
  - Add the Steam session rules, the redaction rule, and "nothing from `research/`, Apple or the CrossOver trial goes into git". (The four absolute `file:///Users/<name>/…` links became relative in the plan's commit, PR #2.)
- Update `docs/PORTING_GUIDE.md`:
  - D3DMetal on cx.
  - DLSS facts: on macOS 26, D3DMetal runs its Metal 3 backend, and `D3DM_MTL4` has no effect before macOS 27.
  - Remove the unverified `MTL4FXFrameInterpolator` claim (`docs/PORTING_GUIDE.md:31`).
  - Elden Ring, Sekiro, DMC4 SE, DOOM TDA and FFXIV have no D3DMetal MetalFX benefit.
- Close out `docs/cx/BUILD_LOG.md`. It holds only redacted excerpts; run the hygiene test before the commit.
- Finish `patches/cx26.3/README.md` and `PROVENANCE.md`.
- Before the push, scan the whole branch history, because an excerpt committed early and fixed later would still be published by the push (R2-17): `M5_HYGIENE_BASE=fix/gptk-runtime-split uv run pytest -q tests/test_repo_hygiene.py` (base `main` after the rebase onto `main`). It applies the hygiene regexes to every line the branch adds (`git log -p <base>..HEAD`). On a hit, fix the file, squash the branch into one commit (`git -C ~/projects/m5-wine-runner-cx reset --soft <base>`, then `git commit`), and scan again.
- Push and open a PR only when Daniel says so; Daniel merges. If PR #1 is still open, stack the PR on it. If PR #1 has merged by then, rebase first with `git -C ~/projects/m5-wine-runner-cx rebase --onto main fix/gptk-runtime-split feat/cx-runtime` and target `main`.
- After Daniel merges (review C10):
  1. Daniel tells the agent the PR is merged.
  2. The agent switches the stable checkout to the branch the cx PR was merged into, which is `main` only if PR #1 has merged too (R1-21), updates it, and checks that the cx code is there before regenerating anything:
     ```bash
     B=$(gh pr view <cx PR number> -R dannydiaz04/m5-wine-runner --json baseRefName --jq .baseRefName)   # main or fix/gptk-runtime-split
     S=~/projects/m5-wine-runner; git -C "$S" fetch origin && git -C "$S" switch "$B" && git -C "$S" pull --ff-only
     test -f "$S/scripts/build-wine-cx.sh" && test -f "$S/scripts/cx/cx-run.sh" && git -C "$S" log --oneline -3   # the cx commits are in
     ```
     If PR #1 merges later, repeat this step with `main`.
  3. The agent runs `uv run --project ~/projects/m5-wine-runner m5runner create-apps elden-ring`, and removes the worktree with `git -C ~/projects/m5-wine-runner worktree remove ~/projects/m5-wine-runner-cx` once nothing runs from it.
  4. Daniel double-clicks Elden Ring.app. It now starts Steam headless first, then the game on the cx runtime, with the HUD in the corner. A Steam window he opened through the runner may stay open (5.2, R3-11).
  5. Daniel turns automatic macOS updates back on if he wants them (M0.9).

---

## 4. Iteration protocol

### 4.1 The cycle (one variable per cycle)
1. Pick the first failing gate of the current milestone.
2. Run `eval "$(scripts/cx/newcycle.sh <slug>)"`. It takes the next free C-number from BUILD_LOG, creates `~/Games/logs/cx/C<NNN>-<slug>/`, appends an entry stub and exports `CX_LOGS`. Fill in the header (build, hypothesis with evidence, planned change) before running anything.
3. If the change touches the prefix: `steam.sh stop` (it refuses while `er.sh`, promote, a rollback, a test block or a session handed to Daniel holds the session lock, so it can never end his sign-in window or play test; 4.9), `backup-userdata.sh`, then the snapshot one-liner of M6.2 step 3 with `<tag>` (`snap_prefix`, which never clones onto an existing snapshot; R3-6).
4. Make exactly one change: a patch, a flag, an environment variable, a registry value or a file. A Steam self-update, a macOS update or another GPTK version is a change too. The first line of every `gates.txt` (`build= os= steam= gptk=<version>:<manifest hash> rung= msync= offline= load=`, lib.sh `gates_header`) makes such changes visible (review C22). Every script and block that writes a `gates.txt`, or hands its directory to the dialog watcher, writes this header first (R3-2).
5. Rebuild the minimum (4.5) and promote.
6. Run the milestone's script. Every gate prints PASS, FAIL or INCONCLUSIVE, and the evidence lands in `$CX_LOGS`, together with `gates.txt` and a copy of any build log produced in the cycle.
7. Fill in Result, Evidence and Decision (keep, revert, or next).
   - A kept source change is committed in `$SRC`, exported with `git -C "$SRC" format-patch -1 -o "$REPO/patches/cx26.3/"`, renamed to `m5-NNNN-<subject>.patch`, and added to `series`, `SHA256SUMS` and `PROVENANCE.md` (source: this repo). The make stage refuses a dirty `$SRC`.
   - A kept environment or registry change goes into the harness, and in M9 into the runner.
8. Repeat. A milestone passes only on a promoted full-install build (`bNNN`), never on `dev` hot swaps.

### 4.2 Records
`docs/cx/BUILD_LOG.md` is tracked, append-only and **public** (review C15). It holds gate IDs, PASS/FAIL/INCONCLUSIVE, decisions, and excerpts that went through `scripts/cx/redact.sh`. Raw logs, screenshots, user-data backups and Steam files stay under `~/Games` and are never committed. `tests/test_repo_hygiene.py` fails on a SteamID64, a `[U:1:…]` id, an AccountName or PersonaName value, a `/Users/<name>/` path, or an IPv4 address other than 127.0.0.1 and 0.0.0.0 in any tracked file (5.3).

Its header holds:
- the current build, the LKG build (recorded only after promote and the milestone's gates) and the LKG prefix snapshot;
- the last user-data backup (review C11);
- the Steam rung in use, the Steam client version and whether it is pinned;
- the macOS build;
- a milestone status table (M0-M10, with PASS, FAIL or OPEN);
- the **Daniel queue** (review C23):

| Item | Numbered steps | Asked at | Done at |
|---|---|---|---|
| Steam sign-in (M6.3) | M6.3 steps 1-5 | 2026-10-22 14:05 | |
| Only if no rung renders: sign in elsewhere (L6) | M6 "L6 sign-in elsewhere" steps 1-4 | | |
| Only if F1 is headless only: written OK | M6 "L6 sign-in elsewhere" step 5 | | |
| Elden Ring play test, in an agreed slot (M7.3) | M7.3 steps 1-6 | | |
| Install the Wukong benchmark (M8.4) | M8.4 Install, route A steps 1-4 (route C steps 1-5 if F1 is headless only through the trial) | | |
| Run the Wukong benchmark once with DLSS (M8.4) | M8.4 "Benchmark run" steps 1-5 | | |
| Only if X7 fails: one more benchmark run after each M8.3 variable (M8.4) | M8.4 "Benchmark run" steps 1-5 | | |
| Only if asked: reboot when convenient (4.6) | the request's own numbered steps | | |

Each entry looks like this:
```markdown
## C014 2026-10-22 14:05 steam-l1
- Build: b002-winecx-26.3.0-6-g1a2b3c4 | GPTK 4.0b3 | prefix cx_prefix (from snap m6-updated) | macOS 25F80 | Steam pinned
- Hypothesis: CEF's GPU process cannot present cross-process on stock winemac; athei keeps it in-process on DXMT (builtin.rs:116-131)
- Change: Steam session WINEDLLPATH_PREPEND=~/Games/sdk/dxmt; winemetal.dll in system32/syswow64; CommandLineAppend=--in-process-gpu
- Command: eval "$(scripts/cx/newcycle.sh steam-l1)"; scripts/cx/steam.sh reset-rung --winemetal --append '--in-process-gpu'; scripts/cx/steam.sh ui --dxmt
- Result: PASS S1 S2 S3 S4 S5 S8 S9 | FAIL - | pending S6 (Daniel) | INCONCLUSIVE -
- Evidence: ~/Games/logs/cx/C014-steam-l1/{steam.log,steam-logs/,appdefaults-start.txt,gates.txt}
- Decision: keep; Steam rung = L1; next M6.3 sign-in
```
Other records:
- **Build logs:** `$CXB/logs/<stage>.log`, overwritten each run, so copy them into the cycle directory when they matter.
- **`BUILDINFO`:** in every build directory; line 1 is the build id.
- **Promote evidence:** `~/Games/logs/cx/promote-<build>-<UTC>/`, one directory per promote run (R1-5).
- **Baselines:** `~/Games/logs/cx/baseline-*`.

### 4.3 Harness commands (Appendix A)

| Purpose | Command |
|---|---|
| Build or rebuild | `scripts/build-wine-cx.sh all`, `... <stage>`, `... from <stage>`, `... iter` (= from make: make, install, assemble, verify, promote). Always a background job of the shell tool, with `$CXB/logs/<stage>.log` tailed (R2-12) |
| Static gates | `scripts/cx/verify-runtime.sh [RT]` |
| Smoke | `scripts/cx/smoke.sh` (T1-T14; a background job, R2-12) |
| New cycle | `eval "$(scripts/cx/newcycle.sh SLUG)"` |
| Run anything | `scripts/cx/cx-run.sh [--d3dmetal VER \| --dxmt] [--msync N] [--prefix NAME] [--debug SPEC] [--log FILE] [--no-d3dshared] [--steam-appid N] [--print-env] -- PROGRAM ...`. Exit 2: no GPTK tree; 3: prefix not promoted; 5: a `wineserver -k` that would end another session (4.9) |
| Session lock | `source scripts/cx/lib.sh`, then `begin_session OWNER [idle]` in a block, `claim_session`/`release_session` and `lock_anchor PID [OWNER]` in scripts, `lock_live` (the anchor runs with its recorded start time and the lock is younger than the last boot), `lock_field owner`; `scripts/cx/steam.sh status` prints the lock (4.9) |
| Timeouts | `scripts/cx/with-timeout.sh SECONDS CMD ...` (exit 142 on timeout) |
| Prefix invariants | `scripts/cx/prefix-check.sh [PREFIX]` |
| Prefix snapshot | lib.sh `snap_prefix TAG`, inside a session (the one-liner of M6.2 step 3): an older `cx_prefix.snap-TAG` is moved aside to `.old-<UTC>` first (R3-6) |
| DLSS copies | `scripts/cx/stage-dlss-copies.sh [PREFIX]` (M8.3 step 1; ends with `prefix-check.sh`) |
| Capture only Wine windows | `scripts/cx/capture.sh [--pid N]... [--title REGEX] OUT.png`. It takes this session's Wine PIDs (lib.sh `session_pids`: this runtime's processes, from `lsof -t $RT/lib/wine/x86_64-unix/ntdll.so`, whose environment has `WINEPREFIX=<the session's prefix>`), or the given `--pid`s, picks the largest on-screen window of those PIDs with `~/Games/tools/wine-windows` (CGWindowListCopyWindowInfo), then runs `screencapture -x -o -l <windowid>`. Exit 4 means the screen is locked: INCONCLUSIVE |
| D3DMetal and HUD logs | `scripts/cx/d3dm-log.sh OUT.log &`, a wrapper for `log stream --style compact --level debug --predicate 'category == "D3DMetal" OR eventMessage CONTAINS "D3DM" OR eventMessage BEGINSWITH "metal-HUD" OR subsystem == "com.apple.metal.hud"'`. After a run, `log show --start "<time>"` with the same predicate recovers missed lines |
| Process snapshot | `scripts/cx/probe.sh DIR EXE [GPTK_VER]` (lsof, vmmap, gate F4b, screenshot of that process's window); `gptk_mapped DIR VER 'a\|b'` counts the named DLLs mapped from `gptk/VER` (H3, E3, X1, X7) |
| Shader cache | lib.sh `d3dm_cache_in EXE VER` and `d3dm_cache_out EXE`: one D3DMetal cache per GPTK version for one exe (M7.5) |
| Winemetal pre-check | lib.sh `steam_lsof DIR`, then `winemetal_check STEAMLOG DIR` (rung L1, M6) |
| Steam | `scripts/cx/steam.sh [--ref] [--dxmt] [--msync N] [--offline] [--no-d3dshared] [--hold] [--timeout S] [--force] install\|ui\|silent\|gates\|collect DIR\|stop\|reset-rung [--append ARGS] [--renderer gl] [--winemetal]\|open URL\|status` (`ui --hold`: a window handed to Daniel, owner `steam-daniel`; with `--ref` the same without a lock, R3-3) |
| Elden Ring | `scripts/cx/er.sh [--msync N] [--gptk VER] [--no-d3dshared] [--probe-only] [--first-frame-timeout S] [--duration S [--start-on FILE]] [--max-session S]` |
| HUD statistics | `scripts/cx/hud-stats.sh LOG [--last N \| FROM_FRAME TO_FRAME]` (median and p95 frame interval) |
| User data | `scripts/cx/backup-userdata.sh [PREFIX]` and `... --restore [DIR] [PREFIX]` (also Steam's auto-login registry values) |
| Login copy (rung L6) | `scripts/cx/copy-steam-login.sh SRC_PREFIX_DIR` (vdf files, MachineGuid, AutoLoginUser, RememberPassword; prints no value) |
| Redaction | `scripts/cx/redact.sh FILE`, before anything is quoted in a tracked file |
| Reference runtime | `scripts/cx/ref-run.sh -- PROGRAM ...` (M6.0) |
| Unix-side crashes | `ls -t ~/Library/Logs/DiagnosticReports/ \| /usr/bin/grep -i wine \| head`; symbolicate our own frames with `atos` against `bNNN/dSYM` |
| Windows-side crashes | the `Unhandled exception` backtrace in the run log. at-0005 keeps it there for GUI programs, and `ShowCrashDialog=0` keeps winedbg non-interactive |

### 4.4 Triage decision tree
1. **Build or configure gate (M1-M3).** Read the tail of `$CXB/logs/<stage>.log`.
   - Missing tool or library: fix env.sh or the deps, then `from configure`.
   - Unix compile error: a `CX_CFLAGS` flag, then `from configure`; a source fix committed in `$SRC` (route A, 4.5), then `iter`; a vendored patch switched on in `series` (route B), then `from src`. `iter` never re-runs the src stage, so it cannot pick up a series edit (R1-18).
   - PE compile error: `CX_CROSSCFLAGS`, then `from configure`.
   - Path or rpath leak: `fix_ids` or LDFLAGS, then `from deps`.
   - "uncommitted changes": commit the edit as a patch (4.1 step 7).
2. **Boot gate (M4).** Use `DYLD_PRINT_LIBRARIES=1` for loader and dylib problems, `WINEDEBUG=+loaddll,+module` for DLL resolution, and T11 for libd3dshared.
3. **D3DMetal gate (M5, M7).** Walk the chain in order and stop at the first broken link:
   1. libd3dshared loaded (H1)
   2. GPTK DLLs mapped from the GPTK tree (H3: the probe's lsof and vmmap; the `+module` trace names only the requested system32 file)
   3. DllMain succeeds
   4. one image of the 4.0b3 file (H4, F4b)
   5. swapchain created (H6)
   6. frames presented (H8)
   7. a crash in an unwrapped `NtXxx` called from libd3dshared (M5 failure table, review C14)
   8. A/B with the 3.0 tree
   9. A/B with the previous build
4. **Steam gate (M6).** Classify the failure, then take the matching action:
   - S-core fails (S1, S6, S7, S8): the game is blocked; fix this first.
   - webhelper restart loop (S2, S3): next ladder rung.
   - black window (S5): the GPU path, so the ladder; compare with the reference runtime (M6.0).
   - window without text: FreeType (V12).
   - login loop: toolchain (D1).
   - `http error 0` (S1): GnuTLS (T6).
   - msync mismatch (S8: "Server is running with WINEMSYNC but this process is not" or "Failed bootstrap_look_up"): `steam.sh stop`, then start Steam and the game again with one `--msync` value (R2-4).
   - a captured dialog (FAIL-dialog): the run ended at the dialog; read the dialog PNG and the `warn+seh` log.
   - "REFUSE: session lock held" or `cx-run.sh` exit 5: another session runs; `steam.sh status`, then 4.9. An owner `steam-daniel`, `er-daniel`, `m84-daniel` or the runner's `runner-er` (5.2) is Daniel's window or game: wait for him. The one exception is a `runner-er` lock from a runner launch the agent itself ran outside a session (BUILD_LOG shows the command; the M9 checks nest and take none): the agent ends that game (`kill` of `game_pid eldenring.exe`), and the lock goes stale with it (R4-6).
   - no rung renders: L6 (headless sign-in), then L7.
5. **Game gate (M7).** Check in order:
   1. Steam ready (S7)?
   2. AVX advertised?
   3. First frame within 20 minutes (shader cache)?
   4. E9's no-exec line (M7.6)?
   5. Faulting module from `+seh` or the backtrace: is it D3DMetal, the game, or Wine?
   6. A/B with the 3.0 tree, the standby patches, `D3DM_SUPPORT_DXR=0`.
6. **Regression after a new build.** Promote the previous `bNNN` (4.7) and confirm that the problem disappears. Then bisect the series with `git -C $SRC` (patches are separate commits) and rebuild with `iter`.
7. **The macOS build or the Steam client changed between cycles** (gates.txt header). Treat it as a new variable: re-run M4 and M5.3 before comparing.

### 4.5 Rebuild matrix
Wine 11 generates a single top-level Makefile. Each module's target is `<dir>/all` (`wine/tools/makedep.c:4130-4135`). PE outputs land in `<dir>/<arch>-windows/` (`makedep.c:4806`) and unix libraries in `<dir>/<name>.so`.

The fast loop uses the `dev` runtime (`~/Games/sdk/wine-cx26.builds/dev`). Use it only inside a session of its own: `source scripts/cx/lib.sh; begin_session dev idle` refuses while another session holds the lock or any process of the current runtime runs (4.9). Inside that session, remake `dev` from the current build with `rm -rf ~/Games/sdk/wine-cx26.builds/dev && cp -Rc "$(cd ~/Games/sdk/wine-cx26 && pwd -P)" ~/Games/sdk/wine-cx26.builds/dev`: a `cp -Rc` onto an existing `dev` would nest the new copy inside the old one (R3-6). Run `cx-run.sh -- wineserver -k` before swapping files, then run the test with `CX_RT=~/Games/sdk/wine-cx26.builds/dev`.

A new source change and a series edit take different routes, and each needs its own command (R1-18):
- **Route A, a new change to Wine source** (a fix found in this project, such as m5-0001): edit and commit it in `$SRC`, then `build-wine-cx.sh iter`. `iter` starts at make, so the commit is what reaches the build. Keep it: export it per 4.1 step 7 into `patches/cx26.3/`, `series`, `SHA256SUMS` and `PROVENANCE.md`.
- **Route B, a vendored patch switched on or off:** edit `series` (and `SHA256SUMS` when a file changed), then `build-wine-cx.sh from src`, which rebuilds `$SRC` from the pristine tree. A patch file that exists only under `patches/` reaches no build through `iter`.

| Change | Rebuild | Deploy |
|---|---|---|
| `dlls/<mod>/*` (PE or unix) | `make -C $BUILD -j$JOBS dlls/<mod>/all` | Fast loop: copy `$BUILD/dlls/<mod>/<mod>.so`, `x86_64-windows/<file>` and `i386-windows/<file>` into `dev`, then `codesign -f -s -` the `.so`. To accept: commit the change as a patch, then `build-wine-cx.sh iter` (new `bNNN`, verify, promote) |
| `programs/<prog>/*` | `make -C $BUILD programs/<prog>/all` | same pattern |
| `server/*.c` | `make -C $BUILD server/all` | copy `server/wineserver` to `dev/bin/wineserver`; `wineserver -k` before testing |
| `server/protocol.def` | `(cd $SRC && tools/make_requests)`, commit, then `iter` | full |
| `include/*`, `dlls/ntdll/unix/*`, `loader/*` | `iter` | full |
| `loader/wine.inf.in` | `iter` | full; promote runs the forced `wineboot -u` |
| `tools/*` | `make -C $TOOLS __tooldeps__`, then `iter` | full |
| `configure.ac`, `Makefile.in`, new module | `tools/make_makefiles` and `autoreconf -fi` (needs autoconf; ask first), then `from tools` | full |
| CFLAGS, CROSSCFLAGS or configure flags | `CX_CFLAGS=… CX_CROSSCFLAGS=… build-wine-cx.sh from configure` | full |
| New source change (route A) | commit in `$SRC`, then `build-wine-cx.sh iter` | full; export per 4.1 step 7 when kept |
| Series edit (enable or disable a patch; route B) | `build-wine-cx.sh from src` | full |
| Dependencies | `build-wine-cx.sh from deps` | full |
| Environment or registry only | none | none |

### 4.6 Stop and escalation
- **Same failure three times.** After 3 cycles on one failure signature without new information: stop, write a summary in BUILD_LOG, and ask Daniel, offering the fallbacks from section 6.
- **Over budget.** When a milestone takes more than twice its time box (section 7): ask Daniel.
- **Stop immediately** if any of these comes up:
  - modifying, disassembling or string-dumping Apple binaries (GPTK licence §2D). Triage uses crash reports, logs and Wine source only;
  - running `strings`, `nm`, `otool` or a disassembler on CodeWeavers' closed binaries (`cxcompatdb.so`, the launcher executables, `CrossOver.app`). Only the trial's plain-text Perl and Python scripts may be read (review F17);
  - copying CrossOver's closed files, anything from the trial, or anything from `research/d3dmetal-integration/cx_bin` into our runtime or the repo;
  - committing anything from `research/`, an Apple file, or an unredacted log excerpt;
  - writing to `wine-gptk`, `wine-staging`, `d3dmetal`, `dxmt`, `gptk_prefix`, `default_prefix`, `legacy_wow64`, `~/Games/src/cx-26.3.0` or the stable checkout (the only exception is the M10 switch, after Daniel merges).
- **Machine health.** If the load average stays above 30 for 10 minutes with no build running, or ecosystemanalyticsd is pegged by Rosetta tools (frankea notes): stop, record the state in BUILD_LOG (load, top processes, the running session), and ask Daniel to reboot when it suits him, with numbered steps: 1. save your work; 2. Apple menu > Restart; 3. tell the agent when the Mac is back. Never reboot unattended, because Daniel's own jobs (for example the Codex model downloads) must keep running (R1-20). After the reboot, resume per 4.8. If a macOS update appears despite M0.9: stop and tell Daniel.
- **Ask Daniel before:**
  - Homebrew or MacPorts installs (sudo);
  - downloads: the reference runtime, Microsoft's VC++ runtimes, the DLSS test titles;
  - `git push` or opening a PR;
  - Steam account actions (signing in is his);
  - buying or installing CrossOver.
- **Leave other jobs alone.** Never pause or kill other user jobs (for example the Codex model downloads) to free resources. Lower `JOBS` instead.

### 4.7 Rollback
- **Runtime:** promote the LKG build, which reuses every safety step of `promote` (lock check, mini smoke, backup, `wineserver -k` of the old build, switch, forced `wineboot -u`, `prefix-check.sh`):
  `echo <LKG build id> > ~/Games/build.noindex/cx26/stamps/assembled.id && scripts/build-wine-cx.sh promote`
- **Prefix:** a session of its own (owner `rollback`; R1-15). Save the block to a file, set `TAG`, and run it with `/bin/bash`. Every destructive step is guarded (R2-15): nothing is removed before the snapshot is known to exist and the backup has succeeded, and the old prefix is only moved aside until the clone and the restore have worked.
```bash
X=~/projects/m5-wine-runner-cx/scripts/cx; source "$X/lib.sh"; TAG=m6-updated         # the snapshot to restore
PR="$HOME/Games/prefixes"; SNAP="$PR/cx_prefix.snap-$TAG"
[ -d "$SNAP/drive_c" ] || { echo "no snapshot $SNAP" >&2; exit 1; }
[ ! -e "$SNAP/cx_prefix" ] || { echo "$SNAP holds a nested copy (a cp -Rc onto an existing snapshot): pick another" >&2; exit 1; }
"$X/steam.sh" stop || exit 1          # refuses while er.sh, promote, a test block or a session handed to Daniel holds the lock
begin_session rollback idle           # takes the lock; refuses while any process of the runtime still runs
"$X/backup-userdata.sh" cx_prefix || exit 1
"$X/cx-run.sh" -- wineserver -k
OLD="$PR/cx_prefix.before-rollback-$(date -u +%Y%m%dT%H%M%SZ)"
mv "$PR/cx_prefix" "$OLD" || exit 1
if ! cp -Rc "$SNAP" "$PR/cx_prefix"; then
  rm -rf "$PR/cx_prefix"; mv "$OLD" "$PR/cx_prefix"; echo "clone failed; cx_prefix is unchanged" >&2; exit 1
fi
"$X/backup-userdata.sh" --restore "" cx_prefix || { echo "restore failed; the previous prefix is kept at $OLD" >&2; exit 1; }
rm -rf "$OLD"
```
  `backup-userdata.sh --restore` puts back the saves, the Steam config, `local.vdf` and Steam's auto-login registry values (`AutoLoginUser`, `RememberPassword`) from the backup taken a few lines earlier. When the cycle is testing those files, replace the restore line with nothing and keep the last line (review C11, R1-19). The block was run on 2026-10-20 (round 3) in a scratch HOME with a stub `steam.sh`: a missing snapshot and a failing backup both stopped it before the prefix was touched, and a normal run left the snapshot's clone in place, no `before-rollback` copy and no lock (R2-15). Round 4 ran it again with the round-4 sources: a snapshot holding a nested `cx_prefix/` (made with a bare `cp -Rc`) was refused before anything changed (R3-6), and a `reg add` that failed inside the restore stopped it with the old prefix kept as `before-rollback`. If the snapshot's `.m5runner-runtime` names another build, promote the current build id again; the pre-flight refuses otherwise. APFS clones are instant and take no space until they diverge.
- **Source:** `git -C $SRC revert <commit>`, or `git -C $SRC reset --hard winecx-26.3.0` and re-run `src`.
- **Runner:** `git revert` on `feat/cx-runtime` in the worktree.
- **For the user:** GPTK 7.7 and Staging are never touched, so `--runtime gptk` and DXMT keep working throughout.
- **Housekeeping:** keep the current build, the LKG build and the 5 newest builds; delete older `bNNN` directories. assemble numbers from the highest existing index, and the newest build is always kept, so a number is never reused (review F1).

### 4.8 Resume after a reboot or a lost session (review C22)
1. Read the BUILD_LOG header: current build, LKG, rung, milestone table and Daniel queue.
2. `cat ~/Games/logs/cx/SESSION.lock`, then `/bin/bash -c 'source scripts/cx/lib.sh; lock_live && echo live || echo stale'`. `lock_live` is the same test the scripts use (R2-10): the lock is live only if its `pid` still runs with the start time recorded as `pid_start` (`ps -o lstart= -p <pid>`) and its `epoch` is later than the last boot (`sysctl -n kern.boottime`). A bare `kill -0 <pid>` is not enough: after a reboot or days of builds, the PID may belong to an unrelated process. If the lock is live, that session is still running: let it finish or end it the proper way (4.9); an owner `steam-daniel`, `er-daniel`, `m84-daniel` or `runner-er` is Daniel's, except a `runner-er` lock from a launch the agent ran itself (4.4 step 4; R4-6). If it is stale, the next claim of any session, promote included, replaces it with a message.
3. Only when step 2 found no live lock, kill leftovers of this runtime: `lsof -t ~/Games/sdk/wine-cx26/lib/wine/x86_64-unix/ntdll.so | xargs kill; scripts/cx/cx-run.sh -- wineserver -k; scripts/cx/cx-run.sh --prefix cx_dlss -- wineserver -k`. (macOS `xargs` runs nothing on empty input.)
4. An interrupted promote (R2-12): if a `~/Games/prefixes/<prefix>.snap-prepromote-<UTC>` directory exists, a promote died without its EXIT trap (SIGKILL or a reboot). Compare `readlink ~/Games/sdk/wine-cx26` and each prefix's `.m5runner-runtime` with BUILD_LOG's current build. If the link names the new build while a prefix is still stamped for the old one, switch the link back (`ln -sfn wine-cx26.builds/<old build> ~/Games/sdk/wine-cx26`), move each half-updated prefix aside as `<prefix>.failed-promote-<build>-<UTC>`, move its snapshot back to `<prefix>`, and promote again. If link and stamps agree, delete the leftover snapshot.
5. An interrupted er.sh: if the last er cycle's `gates.txt` ends with `INTERRUPTED` or lacks the E-gates, wait until the game has closed (the `er-daniel` lock goes stale then). End the cycle's `d3dm-log.sh` if it still runs; after a hand-over its reaper has normally done so already, but an er.sh killed before it leaves the log stream behind (R3-9): `/bin/bash -c 'source scripts/cx/lib.sh; read -r p s < "$0"; if pid_is "$p" "$s"; then kill "$p"; fi' <that cycle's dir>/d3dm-log.pid`. Then run `scripts/cx/backup-userdata.sh`, `/bin/bash -c 'source scripts/cx/lib.sh; d3dm_cache_out eldenring.exe'` (M7.5) and `scripts/cx/steam.sh collect <that cycle's dir>/steam-logs`.
6. `ls ~/Games/build.noindex/cx26/stamps/`. `build-wine-cx.sh all` (a background job) resumes at the first unstamped stage.
7. Compare `sw_vers -buildVersion` and the Steam client version with the last `gates.txt` header. A difference is a new variable: re-run M4 and M5.3 first.
8. Continue at the first OPEN gate of the current milestone, in a new cycle.

### 4.9 Sessions, the lock and parallel work (R1-3, R1-12, R1-15, R1-16; R2-5, R2-7, R2-8, R2-9, R2-10)
A Wine session is anything that starts Wine processes of the cx runtime. Only one runs at a time.
1. **The lock.** `~/Games/logs/cx/SESSION.lock` holds `owner`, `pid`, `pid_start`, `prefix` (or `all` for promote), `start`, `epoch`, `build` and, while a dialog watcher runs, `watcher` and `watcher_start`. `pid` is the anchor whose life is the session's life: the script's own PID for `er`, `promote`, `rollback`, `smoke`, `steam-rung` and every `begin_session` block; the prefix's wineserver for a Steam UI session (`steam-ui`, `steam-daniel`), because Steam restarts its own `steam.exe` during updates while the server lives on; and the game's own process once er.sh or the M8.4 block hands the game to Daniel (`er-daniel`, `m84-daniel`). `pid_start` is that process's start time (`ps -o lstart=`), and `epoch` the claim time in seconds. The start time identifies a process better than its command line would: a `begin_session` block's command line is just `/bin/bash FILE`, while a process that later reuses the PID would have to start in the same second to match. A lock is live only while its `pid` runs with that same start time and its `epoch` is later than the last boot (`sysctl -n kern.boottime`). Otherwise it is stale, and the next claim replaces it with a message. A PID reused after a reboot, or after days of builds have wrapped the PID space, can therefore neither keep a stale lock alive nor make the agent wait for it (R2-10).
2. **Who takes it.** `smoke.sh`, `promote`, `er.sh`, `steam.sh ui` (owner `steam-ui`, or `steam-daniel` with `--hold`), `steam.sh reset-rung` (owner `steam-rung`, for its own registry and file changes), `copy-steam-login.sh`, the 4.7 prefix rollback, the dev fast loop (4.5), every inline block that starts Wine processes directly (M5.2, M5.3, M6.1, M8.0-M8.4, X6), the M7.1 clone (R3-8) and the snapshot one-liner of M6.2 step 3 (R3-6) take it with `claim_session` or `begin_session`. The runner follows the same rules with its own owners (`runner-er` for `launch`, `steam-daniel` marked `by=runner` for `steam --ui`; 5.2, R3-11). `begin_session OWNER idle` also refuses while any process of the runtime runs, a headless Steam included. A block that starts Wine only through `steam.sh` modes (the rung blocks of M6) does not wrap itself in `begin_session`: a nested claim would stop `steam.sh ui` from taking its own lock, so the block leaves the locking to those modes (R2-7). `steam.sh open URL` runs only inside a live `steam-ui` or `steam-daniel` session of the prefix, as part of that session.
3. **Nesting.** A session's own steps pass `CX_SESSION_PARENT=<lock pid>`: `claim_session` then returns 0 without touching the lock, and `cx-run.sh` allows their `wineserver -k`. This is how `er.sh` calls `steam.sh stop` and `steam.sh silent` and keeps its lock, and how promote and the blocks end their own servers.
4. **The guard.** `cx-run.sh -- wineserver -k` exits 5 while a live lock (the same test as item 1) names the same prefix (or `all`) and the caller is not inside that session. `CX_FORCE=1` (`steam.sh --force`) overrides the lock checks; use it only after writing the reason in BUILD_LOG.
5. **Steam.** `steam.sh ui` holds the lock for as long as Steam runs. An agent-run rung test is owner `steam-ui`: `steam.sh stop` may end it and then removes its lock. A window handed to Daniel runs as `ui --hold`, owner `steam-daniel`: `stop` refuses it without `--force`, and once the window is announced (S5 passed) `ui` only records dialogs and never ends the session itself. Daniel ends it with Steam > Exit, after which the server exits and the lock goes stale, or by telling the agent he is done, which the agent records in BUILD_LOG before it runs `steam.sh stop --force` (R2-9). `stop` refuses during `er.sh`, promote, a rollback or a test block, and inside the owner's own session (`CX_SESSION_PARENT` is the lock's pid; `ui`'s own stop of a leftover headless Steam is such a call, R4-1) it stops Steam but leaves the owner's lock in place. `steam.sh silent` takes no lock of its own: a headless Steam holds no unsaved state, and inside `er.sh` it is covered by er.sh's lock. A headless Steam left running between `er.sh` sessions is ended by `steam.sh stop`; blocks that need an idle runtime refuse until then. This differs from the review's wording, which named the owner `steam` for every Steam session: only an interactive session has something to protect, so only `ui` locks, and only a session handed to Daniel is protected from the agent's own `stop`.
6. **Games handed to Daniel** (R2-8). When er.sh (M7.2 phase 3) or the M8.4 block hands a game window to Daniel, it moves the lock's anchor to the game process (`lock_anchor`, owner `er-daniel` or `m84-daniel`). The lock then lives exactly as long as the game, even if the script that started it dies, so no other session can start and no `wineserver -k` can reach the game.
7. **Lifetimes (R1-16, R2-5).** `caffeinate -dimsu -w <anchor>` keeps the Mac awake exactly as long as the session. The dialog watcher (`watch_dialogs DIR ANCHOR`) exits by itself when its anchor dies. Its PID and start time are in the lock, and `release_session` signals it only while that PID still has the recorded start time, so a reused PID is never killed. `steam.sh stop` releases only a live lock; it never signals the watcher of a stale lock, which ends by itself with its anchor. `steam.sh` starts Steam, its watcher and caffeinate through `detach` (a new session through `setsid`), so they outlive `steam.sh` and the agent's tool call.
8. **Scope.** `capture.sh`, `probe.sh` and `watch_dialogs` look only at the session's own processes: this runtime's PIDs whose environment has `WINEPREFIX=<the session's prefix>` (`session_pids`, gate T13). Wine starts children with a double fork and sometimes `setsid` (`wine/dlls/ntdll/unix/process.c:866-937`), so the process tree cannot tell sessions apart, while the inherited environment can. This is why the scope is the prefix, not the descendants of the first process as the review suggested.
9. **The reference runtime** (M6.0) is another runtime and prefix: `steam.sh --ref` takes no lock, so `--ref ui` refuses rather than stops a running reference Steam (R4-4); its PIDs are not in our runtime's list, and our `wineserver -k` cannot reach its server.
10. **Parallel work.** While a session runs, including Daniel's sign-in slot, his play test and his benchmark run, the agent does only work that starts no Wine process: M9a code and unit tests (pytest stubs every subprocess and uses a scratch `~/Games`, 5.3), BUILD_LOG and docs.

Tested on 2026-10-20 in a scratch HOME with stand-in runtimes. Round 2: a second claim was refused; a nested claim and a release by a non-owner left the lock alone; `cx-run.sh` refused `wineserver -k` on the locked prefix (exit 5), also during promote's `all` lock, and allowed it inside the session, on another prefix and with `CX_FORCE=1`; a stale lock was replaced; and a `begin_session` block released its lock on exit. Round 3 repeated these with the A.2 and A.9 code below and added: a lock whose `pid` is alive but has another start time is stale, both for `lock_live` and for the `cx-run.sh` guard; a lock whose `epoch` predates the last boot is stale; `lock_anchor` moves a live lock to another process; and `release_session` leaves a watcher PID alone once its start time no longer matches. Round 4 repeated all of them with the round-4 `lib.sh`, with the same results. Round 5 ran sketches of `steam.sh ui` and `stop` (A.8 as now written) with that `lib.sh` and a stand-in headless Steam: a `steam-ui` and a `steam-daniel` lock survived `ui`'s nested stop and its `lock_anchor`, stayed live and refused a second claim, where the round-4 wording left no live lock; a `stop` from outside then removed the `steam-ui` lock and refused the `steam-daniel` one without `--force` (R4-1, R4-3).

---

## 5. Repo changes

All of this lands in the worktree `~/projects/m5-wine-runner-cx` on `feat/cx-runtime` (D18).

### 5.1 New files
- `scripts/build-wine-cx.sh` (Appendix A.10): the stage driver. Stages are `fetch deps src tools configure make install assemble verify promote`. It takes `all`, `<stage>`, `from <stage>` or `iter`, uses stamps in `$CXB/stamps`, logs to `$CXB/logs`, and on failure prints the last 40 log lines.
- `scripts/cx/stages/{fetch,deps,src,tools,configure,make,install,assemble,verify,promote}.sh`: the stage code of M1-M3.
- `scripts/cx/`:
  - full sources in Appendix A: `env.sh`, `cx-run.sh`, `capture.sh`, `wine-windows.swift`, `d3dm-log.sh`, `probe.sh`, `lib.sh` (session lock with anchor identity, session PIDs, `is_black`, the dialog watcher, `first_frame`, `gptk_mapped`, `steam_lsof`, `winemetal_check`, the shader-cache swap, `regval`, `snap_prefix`, `reap_after`), `verify-runtime.sh` (V1-V15), `smoke.sh` (T1-T14), `prefix-check.sh`, `stage-dlss-copies.sh`, `copy-steam-login.sh`, `with-timeout.sh`, `redact.sh`, `backup-userdata.sh`, `newcycle.sh`, `downloads.sha256`
  - specified by interface (A.8): `steam.sh` (gates S1-S9), `er.sh` (gates E1-E9), `hud-stats.sh`, `ref-run.sh`
  - `tests/hello.c`, `tests/d3d12_clear.c`, `tests/d3d11_clear.c` (A.12; their `.exe` files are never committed)
- `patches/cx26.3/`: `series`, `SHA256SUMS`, `PROVENANCE.md`, `README.md`, 6 base and 16 standby patches.
- `docs/cx/BUILD_LOG.md` and `docs/WINE_CX_BUILD_PLAN.md` (this file).
- `src/m5runner/proc.py`: the one place the runner starts subprocesses (5.2, R1-22).
- `tests/test_cx_runtime.py`, `tests/test_cx_harness.py` (shell helpers: `is_black`, `gptk_mapped`, `winemetal_check`, the lock functions, `d3dm_cache_in`/`out`, `regval`, `snap_prefix`, `reap_after`, `gates_header`, the exit status of `steam.sh stop` and `reset-rung`, and the lock `steam.sh ui` holds after its internal stop), `tests/test_repo_hygiene.py` (added in M0.6), `tests/conftest.py`.

### 5.2 Modified modules
`src/m5runner/config.py`
- New paths:
  - `CX_WINE_DIR = SDK_DIR / "wine-cx26"`
  - `CX_WINE_BUILDS_DIR = SDK_DIR / "wine-cx26.builds"`
  - `CX_PREFIX = PREFIXES_DIR / "cx_prefix"`
  - `GPTK_TREES_DIR = SDK_DIR / "gptk"`
  - `DEFAULT_GPTK_VERSION = "4.0b3"`
  - `CX_BUILD_ROOT = BASE_GAMES_DIR / "build.noindex" / "cx26"`
  - `VALID_RUNTIMES = {"gptk", "staging", "cx"}`
  - `CX_SESSION_LOCK = BASE_GAMES_DIR / "logs" / "cx" / "SESSION.lock"`: the runner reads the shell harness's lock through this path, so it follows `M5RUNNER_GAMES_DIR` like every other path (R2-18)
- Runtime tables:
  - `RUNTIME_DIRS["cx"]`
  - `RUNTIME_PREFIXES["cx"] = "cx_prefix"`
  - `RUNTIME_ENV["cx"] = {"WINEARCH": "wow64", "WINEMSYNC": "0", "ROSETTA_ADVERTISE_AVX": "1", "DOTNET_EnableWriteXorExecute": "0"}`
- `CX_LEAK_PREFIXES = ("WINE", "D3DM_", "DXMT_", "MTL_", "CX_", "DYLD_", "VK_", "M5RUNNER_")` and `CX_LEAK_NAMES = {"SteamAppId", "SteamGameId"}`: the same scrub as `cx-run.sh` (review C20).
- `BACKEND_RUNTIME`: unchanged in M9a; the flip happens in M9b. `DEFAULT_M5_ENV` stays as it is for gptk and staging, to avoid regressions.

`src/m5runner/profiles.py`
- `GameProfile` gains optional `runtime` (pins a title, for example to `"gptk"`) and `gptk`.
- `prefix_path_for(backend, runtime=None)` resolves through the effective runtime (today `profiles.py:43-44, 77` derive it from the backend alone).

`src/m5runner/backends.py`
- `runtime_for(backend, runtime_override=None, profile=None)`: precedence is the override, then the profile, then `BACKEND_RUNTIME`.
- `find_wine_binary(backend, runtime=None)`: on cx this is `CX_WINE_DIR/bin/wine` (no wine64).
- `gptk_tree(version)`: returns the realpath. If the tree is missing, it raises with a hint to run `m5runner import-gptk`.
- `cx_session_env(prefix, *, msync, gptk_version, mode in {"plain","d3dmetal","dxmt"}, hud, metalfx, steam_appid, base_env)`: builds the exact 2.3 table. It first removes every variable that matches `CX_LEAK_PREFIXES` or `CX_LEAK_NAMES` from the inherited environment.
- `ensure_prefix(prefix, backend, runtime)`:
  - A new prefix on cx: clean environment, `wineboot -i`, `winecfg -v win10`, `wineserver -w`; then `disable` in `.update-timestamp`, `.m5runner-runtime` = BUILDINFO line 1, and `ShowCrashDialog=0` (2.4, review C2, C13).
  - An existing prefix whose `.update-timestamp` is not `disable` or whose stamp differs from the current build: refuse with "prefix <name> is not promoted to <build>: run build-wine-cx.sh promote", and start nothing (R2-16). Only `promote` updates a prefix (2.4), because only promote takes the lock, backs up user data, snapshots the prefix, re-stages the DLSS copies after `wineboot -u` and runs `prefix-check.sh`. A runner-side `wineboot -u` would silently turn Apple's nvngx/nvapi64 copies back into placeholders on a DLSS prefix, the failure review C18 describes.
  - `check_placeholders(prefix)` applies `prefix-check.sh`'s rules: system32 `d3d10/d3d11/d3d12/d3d12core/dxgi` equal the runtime's own copies; `nvapi64` and `nvngx` are byte-equal to `<marker>/x86_64-windows/<dll>` when the DLSS-copies marker `.cx-dlss-copies` exists, and "Wine placeholder DLL" otherwise; `atidxx64` is always a placeholder (R2-16).
- `build_execution_environment(...)`, cx branch:
  - D3DMetal mode for the d3dmetal backends.
  - Drops profile overrides for `d3d10, d3d10core, d3d11, d3d12, d3d12core, dxgi` and adds `d3d10,d3d11,d3d12,d3d12core,dxgi=b`.
  - Rejects `n` for `nvngx` and `nvapi64`; `n,b` or `b` are fine.
  - Sets `D3DM_ENABLE_METALFX=1` only when `dlss_metalfx` is set.
  - The gptk and staging branches are unchanged.
- `stage_backend_dlls_into_prefix`: on cx with d3dmetal, copies nothing (placeholders plus prepend). New `stage_dxmt_for_steam(prefix)` copies `winemetal.dll`, used only if the winning Steam rung is L1 or L2 without the winemetal fallback. With the fallback (BUILD_LOG `winemetal pre-check: FAIL`, `bundled-dxmt=1` in BUILDINFO) the runtime already holds winemetal, and the Steam session prepends `~/Games/sdk/cx-overlays/dxmt` instead (R1-7).

`src/m5runner/patchers.py` (review C8, C9)
- `run_profile_hooks(profile, *, prefix_path, runtime, game_dir, dry_run)`. Every hook receives the effective prefix; today the hooks use `profile.prefix_path` and `find_game_dir()`, both derived from `BACKEND_RUNTIME` (`patchers.py:111, 468, 552`), so a `--runtime cx` launch would write `.reg` files into `gptk_prefix`.
- New helper `windows_user(prefix, runtime)`: `crossover` on cx, otherwise the first non-`Public` folder under `drive_c/users`. The RDR2 and MGS Delta hooks hard-code `steamuser` today (`patchers.py:199, 329`).
- `bypass_eac_elden_ring` becomes idempotent: it compares with `filecmp.cmp(shallow=False)` and checks the content before each write. Today it writes `steam_appid.txt` and copies `eldenring.exe` over `start_protected_game.exe` on every non-dry-run launch (`patchers.py:151, 161`).
- `spoof_nvidia_dlss_registry`:
  - Keep `NGXCore FullPath`.
  - Drop the made-up `Control\Video\{00000001-0002-0003-0004-000000000005}\0000 MatchingDeviceId`. Nothing in the Wine/D3DMetal path reads it; D3DMetal reports its own adapter identity (metalfx research).
  - Add `ProgramData/NVIDIA/NGX/models/nvngx_config.txt` for Streamline.
- New `import_reg_file(prefix, runtime, path)`. Today `_write_reg_file_to_prefix` only writes `.reg` files into `windows/temp` and never imports them (`patchers.py:111-123`). On cx, import with `wine regedit /S` in the clean environment.
- Fix `SEKIRO_INPUT_REG_FILE` (`patchers.py:96-101`, R1-10). It writes `"EnableSDL"`, `"EnableHidraw"` and `"MapControllers"` under `HKLM\System\CurrentControlSet\Services\winebus`, but winebus reads only `"Enable SDL"` and `"Map Controllers"` (`wine/dlls/winebus.sys/main.c:1200, 1213`), and its hidraw option is `DisableHidraw`, which affects only the Linux udev backend (`main.c:1202`). Rename the two values to `"Enable SDL"=dword:00000001` and `"Map Controllers"=dword:00000001` and drop `"EnableHidraw"`; `"DisableInput"=dword:00000000` stays (a udev option at its default, harmless). Both values equal Wine's defaults, so nothing changes on gptk or staging; on cx, `import_reg_file` imports the corrected text, and the WineBus A/B of 2.4 (review F6) then changes `Map Controllers` on purpose.

`src/m5runner/bootstrap.py`
- `bootstrap_environment` pins runtimes explicitly, for example `ensure_prefix(GPTK_PREFIX, "d3dmetal", runtime="gptk")` (today `bootstrap.py:194`). Otherwise, after M9b, a clean machine would create `gptk_prefix` with the cx runtime (review C9).
- `import_gptk_d3dmetal`:
  - After mounting (existing code), `ditto` `redist/lib/external` and `redist/lib/wine` into `GPTK_TREES_DIR/<CFBundleShortVersionString>`.
  - Apply Apple's nvngx rename, `xattr -drs`, a `codesign -v --strict` check, and a `MANIFEST.sha256` that does not list itself (review F9).
  - Keep the `D3DMETAL_SDK_DIR` copy for backward compatibility. Never write into a Wine runtime.
- `run_doctor`: new rows for the cx runtime (BUILDINFO, `wine --version`), the GPTK trees and their versions, the `cx_prefix` stamp compared with the current build, whether `loginusers.vdf` exists, and the placeholder check. With `M5RUNNER_NO_EXEC=1` it reads files only and runs no binaries; `tests/conftest.py` sets that, because `tests/test_runner.py:193` runs `doctor` (review C9).

`src/m5runner/proc.py` (new; R1-22)
- `run`, `call`, `popen` and `check_output`: thin wrappers over `subprocess` with the same signatures. Every subprocess start in the runner goes through them: at `fix/gptk-runtime-split` 647a527 that is 21 call sites, in `bootstrap.py` (lines 160, 187, 232, 240, 257, 276, 357, 359, 365, 465, 472, 479, 496), `patchers.py` (191, 400), `backends.py` (77-79) and `cli.py` (75, 168, 173).
- With `M5RUNNER_NO_EXEC=1` they start nothing: they append the argv, cwd and the environment's `WINEPREFIX` to `proc.CALLS` and return a success result (exit 0, empty output; `popen` returns an object whose `wait()` and `poll()` give 0). So `launch`, `ensure_prefix`, the Steam paths and `doctor` can run for real under pytest without starting Wine or Steam.
- `setup_or_launch_windows_steam(prefix, backend, runtime, mode)`. For cx:
  - Modes: `install|ui|silent|stop|status`, plus `offline`. After it takes its lock, `ui` stops a headless Steam of this prefix inside its own session, as `steam.sh ui` does (R3-14); that internal stop keeps the runner's lock (R4-1).
  - Arguments: `-no-cef-sandbox` (+ `-silent`); never `-cef-disable-gpu-compositing`.
  - Registry baseline (2.4), plus the winning rung's settings.
  - Hygiene: htmlcache `Singleton*` and `lockfile`, and the Run key. Every Wine call of the hygiene and of the pre-start registry resets runs with the coming session's msync, after a `wineserver -k` of any leftover server and followed by `wineserver -w`, as in `steam.sh` (A.8, R2-4).
  - Readiness as in D20: reset `ActiveProcess` `ActiveUser` and `pid` to 0 before the start, then both non-zero, a live steam.exe of this prefix, and, unless `.cx-session` reads `offline=1`, a `[Logged On,` line after the start offset (R3-1).
  - Session lock and scope as in 4.9, read and written at `config.CX_SESSION_LOCK` with the same fields and liveness test as `lib.sh` (R3-11):
    - `ui` takes the lock as `steam-daniel` with the extra field `by=runner`: the window is Daniel's own.
    - A cx `launch` claims the lock as `runner-er`, anchored first on the runner's process and then on the game, as er.sh's lock is, so no agent session starts while Daniel plays. Unlike er.sh it sets no time limit: the agent's own launches nest (next sentence), so a `runner-er` lock is Daniel's own game, which a 4-hour cap would close mid-play (R4-6). When `CX_SESSION_PARENT` names the live lock's pid (the agent's own session in the M9a and M9b checks, 4.9 item 3), `launch` and `steam` nest and take nothing. Inside a live `steam-daniel` lock marked `by=runner` whose Steam is ready, it does not refuse: the game runs inside that session with the msync recorded in `.cx-session`, so Elden Ring.app starts while Daniel's runner-opened Steam window is up.
    - `steam --stop`, run from outside that session, may end a `steam-daniel` session marked `by=runner`, which Daniel opened through the runner, and releases its lock; `ui`'s internal stop never does (R4-1).
    - Any other live lock makes `launch` and `steam` refuse and name its owner: a `steam-daniel` lock without `by=runner`, `er-daniel`, `m84-daniel`, `runner-er` and every agent session.
  - Session file `$WINEPREFIX/.cx-session` holds `msync=` and `offline=` as `steam.sh` writes them (A.8). A different msync means `wineserver -k` first.
- `build_wine_cx(args, dry_run)`: runs `scripts/build-wine-cx.sh`.

`src/m5runner/cli.py`
- `build-wine-cx [all|STAGE|from STAGE|iter] [--dry-run]`.
- `launch ... --runtime {gptk,staging,cx} --gptk VER`. For a cx d3dmetal launch it first ensures that Steam is ready, starting `silent` with the same msync if it is not, under the lock rules above.
- The printed environment adds `WINEARCH`, `WINEMSYNC`, `WINEDLLPATH_PREPEND`, `CX_APPLEGPTK_LIBD3DSHARED_PATH` and `CX_ACTIVE_GRAPHICS_BACKEND`. The old "falls back to D3DMetal 3" note is dropped for cx.
- `steam ... --runtime cx [--ui|--silent|--stop|--status|--offline] [--dxmt]`.
- `doctor` prints the new rows.

`profiles/games.toml`
- Update the Elden Ring notes (cx, Steam headless, gates).
- No behavior changes before M9b.

### 5.3 Tests

New in `tests/test_cx_runtime.py`:
- **cx environment for `elden-ring`** must have:
  - `WINEPREFIX` ending in `cx_prefix`
  - `WINEARCH=wow64`, `WINEMSYNC` present, no `WINEESYNC`
  - `WINEDLLPATH_PREPEND` ending in `gptk/4.0b3/wine`
  - `CX_APPLEGPTK_LIBD3DSHARED_PATH` ending in `gptk/4.0b3/external/libd3dshared.dylib`
  - `CX_ACTIVE_GRAPHICS_BACKEND=d3dmetal`
  - `WINEDLLOVERRIDES` containing `d3d10,d3d11,d3d12,d3d12core,dxgi=b`
  - no `D3DM_ENABLE_METALFX`
  - HUD following `--hud`
- **cx Steam environment** (plain): no prepend, no `CX_ACTIVE_GRAPHICS_BACKEND`, `WINEMSYNC=0`. With `--dxmt`, the prepend is the DXMT realpath.
- **Leak test (review C20):** stale `WINEDLLPATH_PREPEND`, `WINEESYNC`, `WINESERVER` and `DXMT_CONFIG` in `base_env` are removed.
- **Parity (review C9):** with `HOME` pointed at a `tmp_path` tree that holds a fake runtime (`CX_RT`) and a fake `Games/sdk/gptk/4.0b3`, the output of `bash scripts/cx/cx-run.sh --print-env --d3dmetal 4.0b3 -- x` equals `cx_session_env(mode="d3dmetal")`, ignoring the `HOME` prefix of paths.
- **DLSS profile on cx:** `D3DM_ENABLE_METALFX=1` and `nvngx` never `n`.
- **No writes to protected prefixes (review C9, R1-22):** with a tmp `PREFIXES_DIR`, a real (not dry-run) `launch <each d3dmetal slug> --runtime cx` runs the hooks with every subprocess stubbed by `proc.py`, leaves a recursive file listing of `gptk_prefix` and `default_prefix` unchanged, and every recorded call in `proc.CALLS` names `cx_prefix` as `WINEPREFIX`.
- **Controller registry text (R1-10):** parse `SEKIRO_INPUT_REG_FILE`; its value names are a subset of what winebus reads (`"Enable SDL"`, `"Map Controllers"`, `"DisableInput"`), and none of `EnableSDL`, `EnableHidraw` or `MapControllers` appears.
- **EAC hook idempotent (review C8, C9):** a second run leaves the mtimes unchanged.
- **Stamp mismatch (review C9, R2-16):** on a tmp prefix stamped for another build, `ensure_prefix` on cx raises with "run build-wine-cx.sh promote", records nothing in `proc.CALLS` and leaves `.update-timestamp` and `.m5runner-runtime` unchanged. `check_placeholders` accepts Apple's nvngx/nvapi64 copies only when they are byte-equal to the files under the marker's path, and reports them otherwise.
- **Runner lock (R3-11):** with lock files under the scratch `~/Games` and the liveness test stubbed: `launch --runtime cx` claims `runner-er` when no lock is live; nests and leaves the lock unchanged when `CX_SESSION_PARENT` names the live lock's pid; runs inside a live `steam-daniel` lock marked `by=runner` with a ready Steam, using its msync; and refuses a `steam-daniel` lock without `by=runner`, `er-daniel` and `steam-ui`. `steam --stop` ends a `steam-daniel` lock marked `by=runner` and refuses one without the mark. `steam --ui`, started while a stubbed headless Steam of the prefix runs, stops it and still holds its own `steam-daniel` lock marked `by=runner` (R4-1).
- **One subprocess door (R1-22, R2-6):** apart from `proc.py`, no file under `src/m5runner/` contains `subprocess.run`, `.Popen`, `.call`, `.check_call`, `.check_output` or `from subprocess import` (a text scan).
- **`import-gptk`** against a fake redist in `tmp_path`, with symlinks: layout, rename, preserved symlink targets, nothing written under runtime directories, and a `MANIFEST.sha256` that passes `shasum -c` and does not list itself (review F9).
- **Fallback:** `--runtime gptk` still gives `wine-gptk`, `gptk_prefix` and `WINEESYNC=1`; DXMT stays on staging.

Changed in `tests/test_runner.py` at the M9b flip: the current d3dmetal expectations (`tests/test_runner.py:62-73, 82-89`) move to `--runtime gptk`, and new cx expectations are added.

New `tests/conftest.py` (R1-22, R2-6, R2-18):
- **A scratch `~/Games`.** At import time, before any test module imports `m5runner`, it points `M5RUNNER_GAMES_DIR` and `M5RUNNER_APPS_DIR` at a fresh temporary directory and sets `M5RUNNER_NO_EXEC=1`. `config.py:12` reads `M5RUNNER_GAMES_DIR` once, at import, so this order matters. The suite then never reads the live `~/Games/logs/cx/SESSION.lock` or a real prefix, and the real launch test cannot fail just because one of Daniel's sessions holds the lock (4.9 item 10). The existing `tests/test_runner.py` assertions compare with `config` paths, so they follow the redirect; `find_wine_binary` returns its first candidate under the redirected SDK directory when nothing exists (`backends.py:44-56`), and neither `/Applications` fallback exists on this Mac.
- **No direct subprocess.** An autouse fixture clears `proc.CALLS` and replaces the `subprocess` attribute of every runner module except `proc.py`: `monkeypatch.setattr(mod, "subprocess", STUB, raising=False)` for `m5runner.backends`, `bootstrap`, `cli`, `patchers` and any other module that imports it. `STUB` keeps the constants (`PIPE`, `DEVNULL`, `STDOUT`) and the classes `CalledProcessError`, `TimeoutExpired` and `CompletedProcess` of the real module, and its `run`, `Popen`, `call`, `check_call` and `check_output` raise `AssertionError("unstubbed subprocess")`, so a call site that bypasses `proc.py` fails the suite instead of starting Wine. Patching `subprocess.run` itself (for example `monkeypatch.setattr("m5runner.backends.subprocess.run", …)`) would be wrong: every module shares one `subprocess` module object, so that would also break the bash calls of `test_cx_harness.py` and the parity test, which use the real module through their own import (R2-6).
- **Shell tests** pass `HOME=<tmp_path>` in the environment of every `bash` call, so the harness reads and writes a scratch `~/Games` as well.

New in `tests/test_cx_harness.py` (R1-11, review F15, R1-6, R1-19, R2-5, R2-10, R2-11). They source `scripts/cx/lib.sh` in `/bin/bash` with `HOME=<tmp_path>`, and the `is_black` cases skip when `sips` is missing:
- `is_black` on PNGs the test writes itself with `zlib` and `struct`: an opaque-black RGBA image returns 0 (a 32-bit BMP's alpha bytes are skipped); uniform grey 20, 40 and 60 return 1 (`od -v`, so repeated rows are not collapsed); near-black 5 returns 0; a black frame with a bright block in the top-right quarter returns 1, and 0 with `hud`; the same block in the top-left or bottom-right returns 1 with `hud`; a missing file returns 2. These cases passed on 2026-10-20 with the A.9 code, including the verifier's images.
- `gptk_mapped` reads probe output, never run logs (review F15, round 3). On sample lsof and vmmap listings it returns 1 when only d3d12.dll is mapped from `gptk/4.0b3` and dxgi.dll from `$RT/lib/wine`, 2 when both come from the GPTK tree, 0 for another version, and 0 when only `d3d12core.dll` comes from it. A run log whose `+module` lines carry the real trace text (`mapping PE file L"\\??\\C:\\windows\\system32\\d3d12.dll"`) gives 0: such a log is not evidence.
- `winemetal_check` returns FAIL for an `@rpath` and for a code-signature `failed to load "…winemetal.so"` line; INCONCLUSIVE for an empty log, and for a log whose only evidence is `mapping PE file L"\\??\\C:\\windows\\system32\\winemetal.dll"`; and PASS only with a sample lsof listing that maps `…/x86_64-unix/winemetal.so` (R1-6, round 3).
- The lock functions: a lock naming a live process with another start time is stale for `lock_live`; so is a lock whose `epoch` predates `kern.boottime`; `lock_anchor` moves a live lock to another live process; `release_session` does not signal a watcher PID whose start time differs (R2-5, R2-10).
- `d3dm_cache_in` and `d3dm_cache_out` with `D3DM_CACHE_ROOT=<tmp_path>/` standing in for `getconf DARWIN_USER_CACHE_DIR`: an unmarked `eldenring.exe` directory is parked and comes back unchanged; each version keeps its own copy; `steam.exe/` is never touched; a leftover `active-…` file from a killed run files the cache under that version (R2-11).
- `regval` reads a value from a sample `user.reg` key and does not confuse the key with its subkey or the `Wow6432Node` view.
- `snap_prefix` (R3-6): a second snapshot with the same tag moves the first aside to `.old-<UTC>`, and the new one holds the prefix's current files with no nested copy (`<snapshot>/cx_prefix` absent).
- `reap_after` (R3-9): the target ends once the anchor exits, and a target PID whose start time no longer matches is left alone.
- `gates_header` (R3-1, R3-2, R3-10): the line starts with `build=`, carries `gptk=<CX_GPTK>:<hash>` and `offline=` from `.cx-session` (`none` without one). A text test over `scripts/cx/*.sh` and the bash blocks of `docs/WINE_CX_BUILD_PLAN.md`: every script or block that writes a `gates.txt`, or hands a directory to `watch_dialogs`, writes `gates_header … > …/gates.txt` to that file first, unless an earlier line runs `smoke.sh`, `er.sh` or a `steam.sh` mode that does.
- `steam.sh stop` and `reset-rung` (R3-7, R3-16) against a stand-in runtime whose stubs exit as Wine does with no server running and no AppDefaults values (R4-2, R4-7): `wineserver -k` and `wine reg delete` exit 1; `wineserver -w`, `reg add` and `reg query` exit 0. With no Steam running, `stop` and option-less `reset-rung` exit 0; with `reg add` made to exit 1, `reset-rung --append X` exits 1; with a live `er` lock, `stop` exits 1.
- `steam.sh ui` and `ui --hold` (R4-1, R4-3), started while a stand-in headless `steam.exe` of the prefix runs and no lock is live: once `ui` has moved its lock to the stand-in server, the lock names `steam-ui` (with `--hold`: `steam-daniel`), that server as `pid`, `prefix` and `epoch`; `lock_live` calls it live, a second `claim_session` refuses, and the headless stand-in has ended. The stand-ins are non-Apple executables (Homebrew's bash under `exec -a`): on this Mac `ps -E` showed the environment of a Homebrew bash but none for `/bin/sleep` (checked 2026-10-20, round 5), and `session_pids` needs it.

New in `tests/test_repo_hygiene.py` (review C15, C21; licence rules of 6.1). It is added in M0.6, so it checks every commit from the first one on (R2-17):
```python
BINARY = re.compile(r"\.(dylib|dll|so|exe|dmg|pkg|zip|xz|gz|tbz2)$|\.framework/|(^|/)(research|cx_bin)/", re.I)
ACCOUNT = re.compile(r'7656119\d{10}|\[U:1:\d{3,}\]|"(?:Account|Persona)Name"\s+"[^"<]+"|/Users/[A-Za-z0-9._-]+/')
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
IPV4_OK = {"127.0.0.1", "0.0.0.0"}
```
- The scan covers `git ls-files --cached --others --exclude-standard`: tracked and staged files, and new files that `.gitignore` does not exclude, so a file is checked before its first commit (R3-20). No such path matches `BINARY`: no Apple, Wine or CrossOver binaries, archives, frameworks, `research/` or `cx_bin/`.
- No such text file matches `ACCOUNT`, and every `IPV4` match is in `IPV4_OK`. A four-part version number that trips the IPv4 check gets an allowlist entry, never a weaker pattern.
- `/bin/bash -n` (Apple's bash 3.2) passes on `scripts/build-wine-cx.sh`, `scripts/cx/*.sh` and `scripts/cx/stages/*.sh`.
- History scan, run only when `M5_HYGIENE_BASE` is set (M10, before the push): every added line of `git log -p --no-color "$M5_HYGIENE_BASE"..HEAD` (lines starting with `+`, without the `+++` headers) is checked against `ACCOUNT` and `IPV4` the same way. A tree scan alone would miss an excerpt that was committed early and fixed later, which the push would still publish (R2-17).

### 5.4 Documentation
README, AGENTS.md, `docs/PORTING_GUIDE.md`, `docs/cx/BUILD_LOG.md`, `patches/cx26.3/README.md` and `PROVENANCE.md`, as described in M10. `.gitignore` already excludes `sdk/`, `prefixes/`, `logs/`, `*.dmg`, `*.pkg`, `*.tar.xz` and `*.tar.gz`; the hygiene test keeps binaries, research files and account data out.

### 5.5 Git
- Worktree `~/projects/m5-wine-runner-cx`, branch `feat/cx-runtime` from `fix/gptk-runtime-split` (PR #1, open). The stable checkout is not switched until Daniel merges (M10).
- When PR #1 merges, rebase with `git -C ~/projects/m5-wine-runner-cx rebase --onto main fix/gptk-runtime-split feat/cx-runtime` and retarget to `main`.
- One commit per milestone. Run `uv run pytest -q tests/test_repo_hygiene.py` before each commit; the test exists from M0.6 on (R2-17) and also scans new, not yet staged files (R3-20).
- Before the push (M10): `M5_HYGIENE_BASE=<base> uv run pytest -q tests/test_repo_hygiene.py` scans every line the branch adds; on a hit, fix the file, squash the branch (`git reset --soft <base>`, then one commit) and scan again.
- No push and no PR without Daniel's go-ahead. Daniel merges.

---

## 6. Risks and fallbacks (ranked)

| Rank | Risk | Likelihood / impact | Early signal | Mitigation, then fallback |
|---|---|---|---|---|
| 1 | Steam UI or login fails on cx: CEF 126 GPU process, Wine bug 60263, msync hangs | High / High | S2-S5 fail at L0 | Ladder L1-L5 (L1 athei, L2 Highball), the reference runtime A/B (M6.0), L6 headless sign-in, then L7: CrossOver trial A/B, Highball's DXMT fork or a native Steam bridge (Daniel decides). Elden Ring needs only S-core (D19) |
| 2 | D3DMetal 4.0b3 unstable on macOS 26.5.1, or its larger libd3dshared calls an ntdll function that CW Hack 23015 does not wrap. Third-party validation was mostly on macOS 27; athei shipped 4.0b2 on 26.4+ | Medium / High | H-gates fail with 4.0b3 and pass with 3.0; a crash report in an unwrapped `NtXxx` | The m5-0001 wrapper patch (M5, review C14); per-title `--gptk 3.0`; record; macOS 27 later (Daniel) |
| 3 | Missing closed CrossOver behavior (cxcompatdb per-app database) | Medium / Medium | A title works in the CrossOver trial with the same GPTK but not on cx | AppDefaults and `CommandLineAppend`; the m5compat shim; compare the trial bottle's text settings |
| 4 | Build breaks on Xcode 26.6, GCC 16, or the cross-built deps | Medium / Medium | M1-M3 gates | Flags (M3 table); Gcenx dylib reuse; MacPorts; the llvm-mingw tree with a GCC-built kernelbase |
| 5 | Elden Ring specifics: no atidxx64 in 4.0b3, fibers and the %gs model, DXR, and no-exec turned off by `bink2w64.dll` (the Rosetta fault-storm path) | Medium / Medium | E7 crash signatures; E9 | 3.0 A/B; standby gs-slot set; `D3DM_SUPPORT_DXR=0`; hb-0013 A/B (M7.6) |
| 6 | A prefix update copies prepended DLLs into system32. Verified from source (2.4); with `disable` and `promote` it can no longer happen by accident | Low after mitigation / Medium | `prefix-check.sh` fails in a pre-flight | `promote`; never run a renderer session on a prefix that is not promoted (cx-run.sh exits 3) |
| 7 | Rosetta: AVX advertisement, exec/W^X faults, and Apple's announced wind-down after macOS 27 (reported) | Low now, High long-term | 0xc000001d; execute faults | `ROSETTA_ADVERTISE_AVX`; CrossOver's Rosetta hacks are already in the tree. Long-term an arm64 Wine (Highball and athei arm64+FEX lines) is out of scope |
| 8 | A Steam client update breaks a working setup | Medium / Medium | Sudden S-gate failures; the `steam=` field of gates.txt changes | Pin as soon as S6 passes (M6.4); unpin as a cycle of its own (M6.6); prefix snapshots |
| 9 | Unattended-run hazards: an automatic macOS update and reboot, sleep, a locked screen, modal dialogs, hangs, and one session killing another | Medium / Medium | Missing evidence, hung cycles, a Steam window or game that vanishes | M0.9 settings; `caffeinate` bound to each session's anchor; `--session-check` turns capture gates INCONCLUSIVE; `ShowCrashDialog=0`, and the dialog watcher ends the run at a dialog; `with-timeout.sh` on every wait; one session at a time with the lock (anchor identity checked) and the `wineserver -k` guard; Steam windows and games handed to Daniel locked to him; long jobs as background jobs (review C12, C13, 4.9) |
| 10 | Saves or Steam login lost in a prefix rollback | Low / High | — | `backup-userdata.sh` before restores and promotes and after every er.sh session; restore after a snapshot rollback (review C11) |
| 11 | Account data leaks through the public repo | Low / High | The hygiene test fails | `redact.sh`; the hygiene test; raw logs stay in `~/Games/logs` (review C15) |
| 12 | License or trademark mistakes | Low / High | — | Rules in 6.1 |
| 13 | msync instability or leaks | Low / Medium | wineserver RSS keeps growing | hb-0014 is in base; msync only for game sessions |
| 14 | Disk or CPU contention | Low / Low | — | Prune builds; lower `JOBS`; never pause other user jobs |

### 6.1 License and trademark rules
- Never commit or redistribute any of these:
  - Apple binaries (D3DMetal, libd3dshared, the GPTK redist), DMGs, the GPTK Read Me or License RTFs, or extracted payloads;
  - anything from the CrossOver trial or `CrossOver.app`: binaries, scripts or excerpts;
  - the athei reference runtime, which bundles Apple's GPTK 4.0b2;
  - anything under `~/Games/src/research`;
  - any `strings`, symbol or disassembly output of Apple or CodeWeavers binaries.

  Record only hashes and version strings. Basis: GPTK licence §2A (personal evaluation use), §2C (non-commercial distribution only) and §2D (no reverse engineering or derivative works).
- Never disassemble, string-dump or symbol-dump Apple binaries; triage uses crash reports, logs and Wine source only (§2D). Never modify Apple files. The only exceptions are Apple's documented nvngx rename in our own copy and the byte-identical alias copy in our overlay (M8.3). Never sign, re-sign or rewrite Apple files (`codesign -s` or `-f`, `install_name_tool`); read-only verification with `codesign -v` is allowed, as M0.10, `import-gptk` and the T11 and H1 triage rows use it (R1-9).
- CodeWeavers' closed binaries (`cxcompatdb.so`, the launcher executables, `CrossOver.app`): no `strings`, `nm`, `otool` or disassembly. For comparison, read only the trial's plain-text Perl and Python scripts (review F17). Never copy `research/d3dmetal-integration/cx_bin` anywhere.
- Do not call the runtime "CrossOver". "cx" and "wine-cx26" are internal labels. Describe it as "Wine built from CodeWeavers' CrossOver 26.3.0 open-source tarball (LGPL)". If Wine binaries built here are ever distributed, the LGPL source and patches must go with them, and they must not be presented as a CodeWeavers product.
- The patches in `patches/cx26.3` are LGPL-2.1-or-later (Wine; Highball `NOTICE.md`), with attribution in their README and provenance in `PROVENANCE.md`.

### 6.2 Last-resort fallback
Use the CrossOver 26.3 trial (14 days) with Apple's documented 4.0b3 drop-in into `lib64/apple_gptk`, per the GPTK Read Me. It serves two purposes:
- an A/B test that shows whether a failure is ours;
- a stopgap so Daniel can play while cx is fixed. It can also host the one-time Steam sign-in of rung L6.

Keep it outside `m5runner`, and nothing from it enters the repo. If it is kept beyond the trial, Daniel buys a license.

---

## 7. Time and resource estimates

| Milestone | Agent time | Daniel | CPU | Disk |
|---|---|---|---|---|
| M0 | 1-2 h | approve installs, grant Screen Recording, switch off macOS updates (one combined request) | Homebrew bottles (mingw-w64 is the largest) | ~3 GB |
| M1 | 0.5-1 h (20-40 min of builds) | — | 18 cores | ~2 GB |
| M2 | ~0.5 h | — | short | ~1 GB tools tree |
| M3 | ~1 h (cold make 10-25 min at -j27; incremental 1-3 min with ccache; assemble, verify and promote about 5 min) | — | full load during make | ~15 GB build tree, 8 GB ccache cap, ~1.8 GB per `bNNN` including dSYMs (PE debug info kept) |
| M4 | 0.5-1 h | — | light | <1 GB |
| M5 | 1-4 h | look at screenshots | light | 68 MB GPTK tree, test programs |
| M6 | 2 h to 2 days; M6.0 adds 0.5-1 h | sign in once (~10 min); approve the reference download | Steam's first update is 15-25 min under Rosetta | ~2-3 GB Steam; reference runtime 235 MB download, about 1 GB extracted, plus ~3 GB Steam in `cx_ref_prefix` |
| M7 | 1-4 h; M7.6 adds about 1 h | one setting, 15-30 min play test; only if he wants the gameplay A/B, a 2-minute Site of Grace scene per arm (M7.4) | game-level | none: the 52 GB game folder is an APFS clone |
| M8 | 1-3 h, plus the benchmark download (size not checked) | approve the DLSS test titles; install the benchmark when the agent opens its dialog, then run it once with DLSS (M8.4, about 15 min), again only if X7 fails | game-level | 84 MB sample, `cx_dlss` prefix (~1 GB), benchmark size |
| M9 | 4-8 h | review | light | — |
| M10 | 1-2 h | merge, one double-click | — | — |

- **Total:** about 2-3 working days if Steam passes at L1 or L2, and 3-5 days in the expected case. M6 dominates.
- **Daniel's response time:** 0.5-2 days in total across the queue items (review C23). M9a code fills the waits; M8.0-M8.3 and X6 run as their own sessions between Steam cycles, outside the sign-in slot (1.3, 4.9).
- **Disk:** about 35-50 GB including ccache, dSYMs, 5 kept builds and the optional reference runtime; 1.7 TB is free.
- **Build cost** comes from steamplay-mac (20-30 min on an M3 Max) and frankea (15-20 min self-hosted). **ASSUMPTION:** this Mac will be at least as fast. Measure it in C00x.

---

## Appendix A. Harness sources

All scripts are bash 3.2-compatible. On 2026-10-20, after the round-4 edits, every bash block of this plan (59 blocks: Appendix A, the M1-M3 stages and the inline blocks, indented ones included) was extracted again and passed `/bin/bash -n` with Apple's bash 3.2.57. These were exercised as well:
- `verify-runtime.sh` against `~/Games/sdk/wine-staging` (V9 and V14 skipped), and `newcycle.sh` numbering and `redact.sh` on sample text in a scratch directory (round 2);
- in a scratch HOME with stand-in runtimes and prefixes (round 3): the lock functions with the anchor start-time and boot checks, `lock_anchor`, the watcher identity check and the `cx-run.sh` guard (4.9); promote's success path and its rollback after a failure past the switch (M3.5); the guarded prefix rollback of 4.7 with a stub `steam.sh`; and the DLSS marker contract of `stage-dlss-copies.sh` and `prefix-check.sh` (A.14);
- the `lib.sh` helpers on test data (round 3): `is_black` on the round-2 images (17 in round 2, the ten key cases again now), `gptk_mapped` on sample lsof and vmmap listings and on real-format and synthetic run logs, `winemetal_check` on the verifier's failure log, an empty log, the system32 trace line and sample listings, `dialog_seen` and `wait_or_dialog` with and without a PID, `d3dm_cache_in` and `d3dm_cache_out` with a stand-in cache root, and `regval` on a sample `user.reg`;
- in a scratch HOME with stand-in runtimes and stub `wine`, `wineserver` and `steam.sh` (round 4): every round-3 test above again with the round-4 `lib.sh` (lock, helpers, `is_black`, `regval`, promote, the 4.7 rollback); `gates_header` (`gptk=` and `offline=`, also under `set -euo pipefail` without a `.cx-session`); `snap_prefix` against a bare `cp -Rc`; `reap_after`, also detached as er.sh starts it; the 4.8 step-5 one-liner (it ends a recorded log stream, and leaves a PID with another start time alone); the snapshot one-liner of M6.2; the blocks of M5.2, M6.1, M7.1 (twice, and while another session held the lock), M8.0, M8.1 and M8.3 step 2 (with `PN=cx_prefix`) and the M8.4 copies block; `copy-steam-login.sh` against a fake source prefix; `backup-userdata.sh --restore` with a failing and with a hung `reg add` (its timeout lowered for the test: exit 142); the X7 evidence lines on sample listings; and the gates-header text check of 5.3 over every block and script (round 3's blocks fail it four times, round 4's pass). `cx-run.sh -- wineserver -k` with no server passes the exit 1 through, which is why `steam.sh` adds `|| true` (A.8).

The A.1, A.2 and A.9 sources, `prefix-check.sh`, `copy-steam-login.sh` and `backup-userdata.sh` in A.14, the promote stage in M3.5 and the 4.7 prefix-rollback block are byte-identical to the files exercised above in round 4, and `stage-dlss-copies.sh` to the round-3 file, which ran again inside the M8.4 copies block (the restore half of `backup-userdata.sh` calls `reg add` through Wine, here a stand-in). `capture.sh`, `probe.sh`, `smoke.sh`, `first_frame` and `steam_lsof` need a running Wine, so they were syntax-checked only. The Swift helper passed `xcrun swiftc -typecheck`.

### A.1 `scripts/cx/env.sh` (sourced, bash)
`REPO` is derived from the file's own location, so the harness works from the worktree during development and from the stable checkout after the merge (review C10).
```bash
# scripts/cx/env.sh: sourced by every cx script and stage (bash 3.2). Never source it from zsh.
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"     # the checkout this file lives in (the worktree)
export REPO
export CXB="${CXB:-$HOME/Games/build.noindex/cx26}"
export CXSRC_TARBALL="$HOME/Games/src/crossover-sources-26.3.0.tar.gz"
export CXSRC_SHA256=ac99c8ca4b3848f3e81784135f023df266b61c2345726ea55a50b3e030dd6872
export CXSRC="$HOME/Games/src/cx-26.3.0/sources"            # extracted tarball, read only
export SRC="$CXB/wine-src" DEPS="$CXB/deps" TOOLS="$CXB/wine-tools" BUILD="$CXB/wine-x86_64" STAGE="$CXB/stage/install"
export RT_ROOT="$HOME/Games/sdk/wine-cx26.builds" RT_LINK="$HOME/Games/sdk/wine-cx26"
export CX_LOG_ROOT="$HOME/Games/logs/cx" CX_LOCK="$HOME/Games/logs/cx/SESSION.lock"
export MACOSX_DEPLOYMENT_TARGET=14.0
SDKROOT="$(xcrun --sdk macosx --show-sdk-path)"; export SDKROOT
export PATH="/opt/homebrew/opt/bison/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export CCACHE_DIR="$CXB/ccache" CCACHE_MAXSIZE=8G CCACHE_COMPILERCHECK=content CCACHE_BASEDIR="$CXB" \
       CCACHE_NOHASHDIR=1 CCACHE_SLOPPINESS=time_macros
export JOBS="${JOBS:-$(( $(sysctl -n hw.ncpu) * 3 / 2 ))}"
unset CC CXX OBJC CFLAGS CXXFLAGS CPPFLAGS LDFLAGS PKG_CONFIG_PATH PKG_CONFIG_LIBDIR
# Machine-local settings that must survive rebuilds (plan 2.1), e.g. CX_BUNDLE_DXMT=1 after the winemetal fallback (M6)
# or CX_SESSION_FILTER=0 if gate T13 fails (M4). The file lives under ~/Games and is never committed.
if [ -f "$CXB/local.env" ]; then . "$CXB/local.env"; fi
```

### A.2 `scripts/cx/cx-run.sh`
```bash
#!/bin/bash
# Run Wine from the cx runtime with the environment recipe of plan section 2.3.
# usage: cx-run.sh [--d3dmetal VER | --dxmt] [--msync 0|1] [--prefix NAME] [--debug SPEC] [--log FILE]
#                  [--no-d3dshared] [--steam-appid N] [--print-env] [--] PROGRAM [ARGS...]
#        PROGRAM "wineserver" runs bin/wineserver. --print-env prints the exported recipe and exits 0.
# knobs, read BEFORE the scrub below: CX_RT (runtime dir), CX_GPTK (default 4.0b3), CX_HUD (1/0), CX_METALFX (1/0),
#        CX_EXTRA_OVERRIDES, CX_PREPEND_EXTRA (colon list put in front of the mode's prepend), CX_DXMT_DIR,
#        CX_SESSION_PARENT and CX_FORCE (session lock, plan 4.9), WINEDEBUG and WINEMSYNC (defaults only)
set -euo pipefail
RT="$(cd "${CX_RT:-$HOME/Games/sdk/wine-cx26}" && pwd -P)"
MODE=plain; VER="${CX_GPTK:-4.0b3}"; MSYNC="${WINEMSYNC:-0}"; PFX=cx_prefix; DBG="${WINEDEBUG:--all}"; LOG=; SHARED=1
APPID=; PRINT=0; HUD="${CX_HUD:-1}"; METALFX="${CX_METALFX:-}"; EXTRA="${CX_EXTRA_OVERRIDES:-}"
PRE_EXTRA="${CX_PREPEND_EXTRA:-}"; DXMTDIR="${CX_DXMT_DIR:-$HOME/Games/sdk/dxmt}"
SPARENT="${CX_SESSION_PARENT:-}"; FORCE="${CX_FORCE:-0}"; LOCK="$HOME/Games/logs/cx/SESSION.lock"
while [ $# -gt 0 ]; do
  case "$1" in
    --d3dmetal) MODE=d3dmetal; VER="$2"; shift 2 ;;
    --dxmt) MODE=dxmt; shift ;;
    --msync) MSYNC="$2"; shift 2 ;;
    --prefix) PFX="$2"; shift 2 ;;
    --debug) DBG="$2"; shift 2 ;;
    --log) LOG="$2"; shift 2 ;;
    --no-d3dshared) SHARED=0; shift ;;
    --steam-appid) APPID="$2"; shift 2 ;;
    --print-env) PRINT=1; shift ;;
    --) shift; break ;;
    *) break ;;
  esac
done
P="$HOME/Games/prefixes/$PFX"
# A 'wineserver -k' never ends a live session that this caller does not belong to (plan 4.9; exit 5). Live = the lock's
# anchor still runs with its recorded start time, and the lock is younger than the last boot (as lib.sh lock_live; R2-10).
if [ "${1:-}" = wineserver ] && [ "${2:-}" = -k ] && [ -e "$LOCK" ] && [ "$FORCE" != 1 ]; then
  lf() { sed -n "s/^$1=//p" "$LOCK" | head -1; }
  lpid="$(lf pid)"; lpfx="$(lf prefix)"; lst="$(lf pid_start)"; lep="$(lf epoch)"
  boot="$(sysctl -n kern.boottime | sed -E 's/^\{ sec = ([0-9]+),.*/\1/')"
  if [ -n "$lpid" ] && [ -n "$lst" ] && [ "$(ps -o lstart= -p "$lpid" 2>/dev/null | awk '{$1 = $1; print}')" = "$lst" ] \
     && [ "${lep:-0}" -ge "$boot" ] 2>/dev/null && { [ "$lpfx" = "$PFX" ] || [ "$lpfx" = all ]; } && [ "$SPARENT" != "$lpid" ]; then
    echo "REFUSE: 'wineserver -k' on $PFX would end a live session: $(tr '\n' ' ' < "$LOCK")" >&2; exit 5
  fi
fi
GPTK=""
if [ -d "$HOME/Games/sdk/gptk/$VER" ]; then GPTK="$(cd "$HOME/Games/sdk/gptk/$VER" && pwd -P)"; fi
if [ -z "$GPTK" ] && { [ "$MODE" = d3dmetal ] || [ "$SHARED" = 1 ]; }; then
  echo "missing ~/Games/sdk/gptk/$VER (plan M0.10); use --no-d3dshared to run without libd3dshared" >&2; exit 2
fi
# Renderer modes only run on a prefix that 'promote' moved to this build (plan 2.4); never let wineboot pick DLLs here.
if [ "$MODE" != plain ] && [ "$PRINT" = 0 ]; then
  ts="$(head -c 7 "$P/.update-timestamp" 2>/dev/null || true)"
  stamp="$(cat "$P/.m5runner-runtime" 2>/dev/null || true)"
  if [ "$ts" != disable ] || [ "$stamp" != "$(head -1 "$RT/BUILDINFO")" ]; then
    echo "prefix $PFX is not promoted to $(head -1 "$RT/BUILDINFO"): run build-wine-cx.sh promote" >&2; exit 3
  fi
fi
# Scrub every inherited Wine, renderer and runner variable (compgen -e lists exported names; works in bash 3.2).
for v in $(compgen -e); do
  case "$v" in WINE*|D3DM_*|DXMT_*|MTL_*|CX_*|DYLD_*|VK_*|M5RUNNER_*|SteamAppId|SteamGameId) unset "$v" ;; esac
done
export WINEPREFIX="$P" WINEARCH=wow64 WINEMSYNC="$MSYNC" WINEDEBUG="$DBG" \
       ROSETTA_ADVERTISE_AVX=1 DOTNET_EnableWriteXorExecute=0 MTL_HUD_ENABLED=0
if [ "$SHARED" = 1 ]; then export CX_APPLEGPTK_LIBD3DSHARED_PATH="$GPTK/external/libd3dshared.dylib"; fi
case "$MODE" in
  d3dmetal)
    export WINEDLLPATH_PREPEND="${PRE_EXTRA:+$PRE_EXTRA:}$GPTK/wine" CX_ACTIVE_GRAPHICS_BACKEND=d3dmetal \
           WINEDLLOVERRIDES="${EXTRA:+$EXTRA;}d3d10,d3d11,d3d12,d3d12core,dxgi=b" \
           MTL_HUD_ENABLED="$HUD" MTL_HUD_LOG_ENABLED="$HUD"
    if [ -n "$METALFX" ]; then export D3DM_ENABLE_METALFX="$METALFX"; fi ;;
  dxmt)
    export WINEDLLPATH_PREPEND="${PRE_EXTRA:+$PRE_EXTRA:}$(cd "$DXMTDIR" && pwd -P)"
    if [ -n "$EXTRA" ]; then export WINEDLLOVERRIDES="$EXTRA"; fi ;;
  plain)
    if [ -n "$EXTRA" ]; then export WINEDLLOVERRIDES="$EXTRA"; fi ;;
esac
if [ -n "$APPID" ]; then export SteamAppId="$APPID" SteamGameId="$APPID"; fi
if [ "$PRINT" = 1 ]; then
  env | LC_ALL=C sort | /usr/bin/grep -E '^(WINE|CX_|D3DM_|MTL_|ROSETTA_|DOTNET_|SteamAppId=|SteamGameId=)' || true
  exit 0
fi
BIN="$RT/bin/wine"
if [ "${1:-}" = wineserver ]; then BIN="$RT/bin/wineserver"; shift; fi
if [ -n "$LOG" ]; then mkdir -p "$(dirname "$LOG")"; exec "$BIN" "$@" >>"$LOG" 2>&1; fi
exec "$BIN" "$@"
```
Exit 2: the GPTK tree is missing. Exit 3: a renderer mode on a prefix that `promote` has not moved to this build (2.4). Exit 5: a `wineserver -k` that would end a live session the caller does not belong to (4.9; R1-3, R1-12); live means the lock's anchor still runs with the start time recorded in the lock, and the lock is younger than the last boot, the same test as `lib.sh lock_live` (R2-10). The knobs are read before the scrub, so a caller's `CX_*` settings, `CX_SESSION_PARENT` and `CX_FORCE` included, still work, while nothing else leaks in.

### A.3 `scripts/cx/capture.sh`
```bash
#!/bin/bash
# capture.sh [--pid N]... [--title REGEX] OUT.png: screenshot the largest on-screen window of this session's Wine processes.
# Session = runtime CX_RT (default wine-cx26) and prefix ~/Games/prefixes/$CX_PREFIX_NAME (default cx_prefix), see lib.sh
# session_pids. --pid narrows it to given processes (probe.sh and er.sh pass the program's PID).
# exit 0 captured, 1 no window, 4 screen locked (callers record INCONCLUSIVE, never FAIL)
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd -P)/lib.sh"
W="$HOME/Games/tools/wine-windows"; args=(--largest); n=0; title=
while [ $# -gt 1 ]; do
  case "$1" in
    --pid) args+=(--pid "$2"); n=$((n + 1)); shift 2 ;;
    --title) title="$2"; shift 2 ;;
    *) break ;;
  esac
done
OUT="${1:?usage: capture.sh [--pid N]... [--title REGEX] OUT.png}"
"$W" --session-check > /dev/null || { echo "INCONCLUSIVE: screen locked" >&2; exit 4; }
if [ "$n" -eq 0 ]; then for p in $(session_pids); do args+=(--pid "$p"); n=$((n + 1)); done; fi
if [ "$n" -eq 0 ]; then echo "no Wine process of this session ($P on ${RTR:-no runtime}) is running" >&2; exit 1; fi
if [ -n "$title" ]; then args+=(--title "$title"); fi
row="$("$W" "${args[@]}")" || { echo "no matching Wine window" >&2; exit 1; }
screencapture -x -o -l "$(printf '%s\n' "$row" | cut -f1)" "$OUT"
echo "captured $row -> $OUT"
```
Without `--pid` the candidates are lib.sh's `session_pids` (4.9), so the capture can no longer pick another session's larger window, such as Steam's, over the program under test (R1-12); `probe.sh` and `er.sh` pass the program's own PID. `lsof -t <file>` lists the PIDs that have the file mapped (checked on this Mac with `/usr/lib/dyld`). `screencapture` flags: `-l <windowid>` captures one window, `-o` drops the shadow, `-x` silences the sound. Window titles need the Screen Recording permission from M0.7; owner PIDs do not.

### A.4 `scripts/cx/wine-windows.swift` (type-checked with `xcrun swiftc -typecheck`)
```swift
// List on-screen windows owned by given PIDs (or owner-name regex) for `screencapture -l <id>`.
// Usage: wine-windows [--pid N]... [--owner REGEX] [--title REGEX] [--largest]
//        wine-windows --session-check     exit 4 if the screen is locked, 0 if unlocked
import CoreGraphics
import Foundation

var ownerPattern = "(?i)^wine|\\.exe$"
var titlePattern: String? = nil
var pids = Set<Int>()
var largestOnly = false
var it = CommandLine.arguments.dropFirst().makeIterator()
while let a = it.next() {
    switch a {
    case "--owner": ownerPattern = it.next() ?? ownerPattern
    case "--title": titlePattern = it.next()
    case "--pid": if let s = it.next(), let v = Int(s) { pids.insert(v) }
    case "--largest": largestOnly = true
    case "--session-check":
        let session = CGSessionCopyCurrentDictionary() as? [String: Any] ?? [:]
        let locked = (session["CGSSessionScreenIsLocked"] as? Bool) ?? false
        print(locked ? "locked" : "unlocked")
        exit(locked ? 4 : 0)
    default: FileHandle.standardError.write("unknown argument \(a)\n".data(using: .utf8)!); exit(2)
    }
}
func re(_ p: String) -> NSRegularExpression {
    guard let r = try? NSRegularExpression(pattern: p) else { FileHandle.standardError.write("bad regex \(p)\n".data(using: .utf8)!); exit(2) }
    return r
}
func hit(_ r: NSRegularExpression, _ s: String) -> Bool { r.firstMatch(in: s, range: NSRange(s.startIndex..., in: s)) != nil }
let ownerRe = re(ownerPattern)
let titleRe = titlePattern.map(re)
guard let list = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] else { exit(1) }
struct Row { let id: Int; let pid: Int; let owner: String; let title: String; let w: Int; let h: Int }
var rows: [Row] = []
for w in list {
    let pid = w[kCGWindowOwnerPID as String] as? Int ?? -1
    let owner = w[kCGWindowOwnerName as String] as? String ?? ""
    let title = w[kCGWindowName as String] as? String ?? ""   // empty without Screen Recording permission
    var rect = CGRect.zero
    if let b = w[kCGWindowBounds as String] as? NSDictionary, let r = CGRect(dictionaryRepresentation: b) { rect = r }
    if rect.width < 64 || rect.height < 64 { continue }
    if pids.isEmpty ? !hit(ownerRe, owner) : !pids.contains(pid) { continue }
    if let t = titleRe, !hit(t, title) { continue }
    rows.append(Row(id: w[kCGWindowNumber as String] as? Int ?? 0, pid: pid, owner: owner, title: title, w: Int(rect.width), h: Int(rect.height)))
}
if largestOnly, let big = rows.max(by: { $0.w * $0.h < $1.w * $1.h }) { rows = [big] }
for r in rows { print("\(r.id)\t\(r.pid)\t\(r.owner)\t\(r.title)\t\(r.w)x\(r.h)") }
exit(rows.isEmpty ? 1 : 0)
```
`--session-check` reads `CGSSessionScreenIsLocked` from `CGSessionCopyCurrentDictionary()` (review C12). The earlier copy at `research/plan/wine-windows.swift` lacks this option.

### A.5 `scripts/cx/d3dm-log.sh`
```bash
#!/bin/bash
# d3dm-log.sh OUT.log: stream D3DMetal and Metal HUD lines from the unified log until killed
exec /usr/bin/log stream --style compact --level debug \
  --predicate 'category == "D3DMetal" OR eventMessage CONTAINS "D3DM" OR eventMessage BEGINSWITH "metal-HUD" OR subsystem == "com.apple.metal.hud"' \
  > "$1"
```
The GPTK Read Me says D3DMetal messages are prefixed `D3DM` and use the system log category `D3DMetal`. Apple's HUD docs say `MTL_HUD_LOG_ENABLED=1` (which needs `MTL_HUD_ENABLED=1`) writes `metal-HUD: <frame>,<gfx mem>,<proc mem>,<interval>,<gpu time>...` once per second. The game's stderr goes to the run log anyway, so grep both places.

### A.6 `scripts/cx/probe.sh`
```bash
#!/bin/bash
# probe.sh DIR EXE [GPTK_VER]: files a running Wine process of this session has mapped (lsof, vmmap) and a screenshot of
# its window. Session = lib.sh session_pids (CX_RT, CX_PREFIX_NAME).
# Gate-style script: set -u only (no pipefail, so grep can stop early without turning a match into a failure).
set -u
source "$(cd "$(dirname "$0")" && pwd -P)/lib.sh"
D="$1"; EXE="$2"; VER="${3:-4.0b3}"; mkdir -p "$D"; pid=""
for p in $(session_pids); do
  case "$(ps -o args= -p "$p" 2>/dev/null)" in *"$EXE"*) pid=$p; break ;; esac
done
[ -n "$pid" ] || { echo "FAIL probe: $EXE is not running in $P on ${RTR:-no runtime}"; exit 1; }
lsof -p "$pid" > "$D/lsof.txt"; vmmap "$pid" > "$D/vmmap.txt" 2>/dev/null
echo "GPTK files mapped:"; /usr/bin/grep -oE '/[^ ]*/gptk/[^ ]+' "$D/lsof.txt" | sort -u
echo "libd3dshared __TEXT images: $(/usr/bin/grep -c '__TEXT.*libd3dshared\.dylib' "$D/vmmap.txt")"   # H4/E3 expect 1
G="$(cd "$HOME/Games/sdk/gptk/$VER" 2>/dev/null && pwd -P)"
if [ -n "$G" ]; then
  want="$(stat -f '%z %i' "$G/external/libd3dshared.dylib")"
  got="$(awk -v f="$G/external/libd3dshared.dylib" '$NF == f {print $(NF-2), $(NF-1); exit}' "$D/lsof.txt")"
  if [ "$got" = "$want" ]; then echo "PASS F4b libd3dshared size+inode $got"; else echo "FAIL F4b mapped='$got' expected='$want'"; fi
  if /usr/bin/grep -q "$G/external/D3DMetal.framework/" "$D/lsof.txt"; then echo "PASS F4b D3DMetal.framework from gptk/$VER"
  else echo "INFO no D3DMetal.framework mapped from gptk/$VER"; fi
fi
"$X/capture.sh" --pid "$pid" "$D/$EXE.png"; rc=$?
[ "$rc" -ne 4 ] || echo "INCONCLUSIVE screenshot: screen locked"
exit 0
```
H3, E3, X1 and X7 count the GPTK DLLs in its `lsof.txt` and `vmmap.txt` with `gptk_mapped` (A.9; review F15). The F4b check compares lsof's size and inode columns, counted from the end of the line so that command names with spaces cannot shift them, with `stat` of the 4.0b3 file (review C17). lsof and vmmap see the dylibs of Rosetta-translated processes, and opening one file through its realpath and through a symlink maps one image (both reviewers' probes).

### A.7 Pins
`scripts/cx/downloads.sha256` (run in `$CXB/downloads`). `SteamSetup.exe` is deliberately absent: its hash is recorded in BUILD_LOG at download time (M1.1).
```text
fe9ff51cb1f2abb5e65a6b8c10a92da0ab5ab6eaf26e7fc2b675c45f1fb519b5  nettle-3.10.2.tar.gz
5f5993c530f084535c65a6879e9b26ad441169b3e25d789d83287040a9ca5165  SDL2-2.32.10.tar.gz
f95765a6229cb7b915990a2890ce12ebe36a730b021545d3d52ae69ce4c4024e  MoltenVK-1.4.2-macos.tar
a16606ef0724202e6a6848ece6e0cbba64d11e2f11aefe744af1d93c6d9f99bb  wine-mono-10.4.1-x86.tar.xz
2cfc8d5c948602e21eff8a78613e1826f2d033df9672cace87fed56e8310afb6  wine-gecko-2.47.4-x86.tar.xz
fd88fc7e537d058d7a8abf0c1ebc90c574892a466de86706a26d254710a82814  wine-gecko-2.47.4-x86_64.tar.xz
```
`patches/cx26.3/series`. Uncomment a standby entry only through a BUILD_LOG decision. This order is verified (2.7).
```text
# patches/cx26.3/series: applied top to bottom by stages/src.sh; lines starting with # are off.
# Dependencies: hb-0011 requires hb-0008+hb-0009; hb-0016 requires hb-0011.
# Conflict: at-0008 does not apply together with hb-0007 (dlls/winemac.drv/window.c); never enable both without a hand merge.
hb-0003-ntdll-winedllpath-prepend.patch
hb-0006-kernelbase-per-exe-command-line-append.patch
fk-0001-ntdll-foreign-personality-routine.patch
hb-0014-msync-unregister-early-return.patch
at-0005-kernelbase-debugger-std-handles.patch
at-0010-dbghelp-dwarf-div-by-zero.patch
#hb-0008-macos-mirror-teb-fiberdata.patch
#hb-0009-macos-swap-fiberdata-and-qos-slot.patch
#hb-0011-macos-lasterror-in-gs-slot.patch
#hb-0016-macos-lasterror-callback-return-once.patch
#hb-0013-ntdll-nx-compat-from-main-image-permanent-under-rosetta.patch
#hb-0005-ntdll-yield-after-auto-event-set.patch
#hb-0025-ntdll-threadpool-io-release-once.patch
#hb-0018-macos-commit-charge-is-the-footprint.patch
#hb-0020-winemac-retina-horzres-not-doubled.patch
#hb-0007-winemac-cross-process-child-swapchains.patch
#hb-0002-wined3d-auto-renderer-opengl-first.patch
#hb-0015-winecoreaudio-io-buffer-under-half-a-period.patch
#hb-0017-kernelbase-getintegrateddisplaysize-stub.patch
#up-c3a1bc86-winmm-hardcode-supported-formats.patch
#at-0001-winemac-run-cocoa-app-uaf.patch
#at-0008-winemac-destroy-window-races.patch
```

### A.8 Interfaces of the remaining scripts
These are written in M0.6 against this specification. They use `lib.sh` (A.9), print PASS, FAIL or INCONCLUSIVE per gate, and wrap every wait in `with-timeout.sh`.
- **`steam.sh [--ref] [--dxmt] [--msync N] [--offline] [--no-d3dshared] [--hold] [--timeout S] [--force] MODE`**, where MODE is `install`, `ui`, `silent`, `gates`, `collect DIR`, `stop`, `reset-rung [--append ARGS] [--renderer gl] [--winemetal]`, `open URL` or `status`
  - Common:
    - `ui`, `silent`, `reset-rung` and `gates` need `CX_LOGS` (newcycle.sh). The debug spec comes from `CX_STEAM_DEBUG` (default `err+all,+seh`).
    - `--ref` (M6.0): before sourcing `lib.sh`, export `CX_RT="$(cat ~/Games/sdk/ref/athei-cx-26.3.0-9/RUNTIME_ROOT)"` and `CX_PREFIX_NAME=cx_ref_prefix`, so `P`, `RTR`, `session_pids`, `capture.sh` and `probe.sh` all point at the reference. Every Wine call (`wineserver -k`, `reg`, `steam.exe`, `-shutdown`) goes through `ref-run.sh` instead of `cx-run.sh`. No `preflight_prefix` (it belongs to our runtime) and no session lock (4.9, R1-8, R1-17). `--ref` never reads `~/Games/sdk/wine-cx26`, so it works before the first promote. `--ref ui --hold` keeps the announce semantics of `--hold` without a lock: once S5 first passes it writes `ANNOUNCED` into `gates.txt`, and from then on it only records dialogs and never ends the session (R3-3). Without a lock nothing tells whose a running reference Steam is, so `--ref ui` never stops one: while a steam.exe or steamwebhelper.exe of `cx_ref_prefix` runs, it prints `REFUSE: a reference Steam is running; end it with steam.sh --ref stop only if the window is not Daniel's` and exits 1 (R4-4).
    - Lock check (4.9; R1-15, R2-5, R2-9, R2-10), first thing in `install`, `ui`, `silent`, `stop`, `reset-rung` and `open`. A lock counts only when `lock_live` says it is live (its anchor still runs with the recorded start time, and it is younger than the last boot). Go on when no lock is live; when `CX_SESSION_PARENT` equals the live lock's pid (er.sh, the setup blocks and `ui`'s own `stop` call it that way and keep their lock, whatever its owner; R4-1); for `stop` also when the live lock's owner is `steam-ui` (an agent-run rung test); for `open` only inside a live `steam-ui` or `steam-daniel` lock of this prefix; or with `--force` (sets `CX_FORCE=1`; write the reason into BUILD_LOG first). A `steam-daniel` lock, a window handed to Daniel, is never ended from outside its session without `--force`. Otherwise print `REFUSE: session lock held: …` and exit 1.
    - One msync value per wineserver (R2-4, R2-14). A client whose `WINEMSYNC` differs from the running server's exits at once: "Server is running with WINEMSYNC but this process is not" (`wine/dlls/ntdll/unix/msync.c:600`) or "Failed bootstrap_look_up" (`msync.c:636`). An idle server lingers 3 s after its last client (`wine/server/main.c:48`), long enough for the next call to attach to it. So every Wine call that `steam.sh` makes passes an explicit `--msync`: in `ui` and `silent` the `--msync N` of the coming start; in `stop`, `gates`, `status`, `open` and `collect` the value recorded in `$P/.cx-session`; `install` and `reset-rung` run on a stopped Steam with 0 and end with `wineserver -w`.
    - Exit status (R3-7, R3-16). A Wine call whose non-zero exit is the normal case never decides `steam.sh`'s status, so it runs with `|| true`, as in promote: `wineserver -k` exits 1 whenever no server runs (`kill_lock_owner` returns 0 without a server directory or a held lock, and `-k` exits with `!ret`: `wine/server/request.c:718-761`, `wine/server/main.c:86-91`), and `reg delete` exits 1 when the value or key is absent (`wine/programs/reg/delete.c:62, 121`). `stop` exits 0 when it stopped Steam or nothing ran, 1 only for REFUSE, and 2 when a steam.exe of this session still runs after `-shutdown` and `wineserver -k`. `reset-rung` exits 0, or 1 for REFUSE or a write that failed or timed out (`reg add`, a copy, or a `wineserver -w` that did not exit 0, which with real Wine means its timeout: `-w` itself always exits 0, `wine/server/main.c:101-103`; R4-2).
    - `gates.txt` (R3-2): `ui`, `silent` and `gates` write `gates_header N RUNG` as its first line when the file is missing or empty, before they start a watcher.
    - Start sequence of `ui` and `silent`, when no steam.exe or steamwebhelper.exe of this session runs: `cx-run.sh -- wineserver -k` (it ends a server another caller left behind, whatever its msync); write `$P/.cx-session`: `msync=N`, `offline=1` for `silent --offline` and `offline=0` otherwise (R3-1), and the start offsets of the Steam log files; then the hygiene, every Wine call with `--msync N`: remove `drive_c/users/crossover/AppData/Local/Steam/htmlcache/{Singleton*,lockfile}`; `reg delete 'HKCU\Software\Microsoft\Windows\CurrentVersion\Run' /v Steam /f`; `reg add 'HKCU\Software\Valve\Steam\ActiveProcess' /v ActiveUser /t REG_DWORD /d 0 /f` and the same for `pid`, because values left by a crashed client would otherwise pass S7 (D20, R1-23). Then `cx-run.sh --msync N -- wineserver -w` under a 30 s timeout, so steam.exe starts a fresh server with msync N.
    - Steam and its helpers start through `detach` (setsid), so they outlive `steam.sh` and the agent's tool call. Once Steam runs, `server_pid` gives the prefix's wineserver (waited for up to 30 s), and `caffeinate -dimsu -w <server pid>` keeps the Mac awake exactly as long as that server lives (R1-16).
  - `install`: lock check; `preflight_prefix`; then `cx-run.sh --msync 0 -- "$CXB/downloads/SteamSetup.exe" /S` under a 900 s timeout, then `wineserver -w`.
  - `ui`: lock check; `claim_session steam-ui $$` (with `--hold`: owner `steam-daniel`) and `export CX_SESSION_PARENT=$$`, so the guard lets its own `wineserver -k` through; `preflight_prefix`; if a steam.exe or steamwebhelper.exe of this session already runs, a headless Steam that holds no lock (er.sh leaves one behind), `stop` inside ui's own session, so a second client never starts with another msync or without the rung's environment (R3-14). That nested `stop` keeps ui's lock, and if it does not exit 0, `ui` releases its lock and exits 1 (R4-1, R4-3); `--ref ui` refuses instead of stopping (R4-4). Then the start sequence. It starts `cx-run.sh [--dxmt] [--no-d3dshared] --msync N --debug "$CX_STEAM_DEBUG" --log "$CX_LOGS/steam.log" -- 'C:\Program Files (x86)\Steam\steam.exe' -no-cef-sandbox` from the Steam directory through `detach`. When `server_pid` answers, it moves the lock to that server (`lock_anchor <server pid>`), exports it as `CX_SESSION_PARENT` for its own later calls, starts `caffeinate -w <server pid>`, and starts the dialog watcher through `detach`: `/bin/bash -c 'source "$0"; watch_dialogs "$1" "$2"' "$X/lib.sh" "$CX_LOGS" <server pid>`, whose PID and start time go into the lock as `watcher=` and `watcher_start=`. It then polls S1-S5 every 30 s until they pass or `--timeout` expires (default 300 s; 1800 s for the first start, M6.2) and writes `gates.txt`.
    - Dialogs: while no window has been announced, `dialog_seen "$CX_LOGS"` ends the run on every pass (review C13): `collect "$CX_LOGS/steam-logs"`, `wineserver -k`, `release_session <owner> <server pid>`, a `FAIL-dialog` line with the dialog PNG in `gates.txt`, exit 1. Without `--hold` that holds until `ui` returns. With `--hold`, the window counts as announced when S5 passes for the first time: `ui` writes `announced=<time>` into the lock and `ANNOUNCED` into `gates.txt` (the agent then tells Daniel the window is up), and from then on it only records dialogs (R2-9). If `--timeout` expires before the window was announced, nothing was handed to Daniel yet, so `ui --hold` ends the session itself the same way and exits 1.
    - It returns with Steam still running and the lock held: a `steam-ui` lock until `stop`, a `steam-daniel` lock until Daniel quits Steam (the server exits and the lock goes stale) or tells the agent he is done (`stop --force`). A dialog that appears after `ui` returned is reported by the next `gates` or `stop`; the agent never ends an interactive session on its own.
  - `silent`: lock check; no lock of its own (4.9). If a steam.exe of this session already runs: exit 0 when it is ready (S7) and `.cx-session` holds `msync=N` and the requested mode (`offline=1` with `--offline`, else `offline=0`), otherwise `REFUSE: Steam runs with msync <M>, offline <0|1>; steam.sh stop first`. Otherwise the start sequence, then the same start with `-silent`; with `--offline` it adds `-offlinemode` (attempt A) or edits `loginusers.vdf` (attempt B, M7.1b). It starts `caffeinate -w <server pid>`. Unless `CX_SESSION_PARENT` is set (then the parent's watcher covers it), it runs a watcher for the length of its own wait and stops it on return. It waits up to `--timeout` (default 120 s) for S7, checking `dialog_seen` on every pass and ending the run the same way as `ui` when a dialog appears.
  - `gates`: S1-S9 into `$CX_LOGS/gates.txt` (the header first if the file is new). `ActiveUser` and `pid` are printed only as zero or nonzero. `reg query` runs with the msync recorded in `.cx-session`, and S7 drops the connection_log condition when it reads `offline=1` (R3-1). S8 looks for both mismatch messages. Any `DIALOG` lines and a `FAIL-dialog` marker are listed.
  - `collect DIR`: copies `Steam/logs/*.txt` (raw; they stay under `~/Games`).
  - `stop`: lock check. When a steam.exe of this session runs: `cx-run.sh --msync <.cx-session> -- 'C:\Program Files (x86)\Steam\steam.exe' -shutdown` and a wait of up to 20 s (with no Steam running it skips this, so it never starts one); then `wineserver -k` with the lock's pid as `CX_SESSION_PARENT`, so the guard in `cx-run.sh` allows it. The lock: from outside the session, a live `steam-ui` lock, or a `steam-daniel` lock with `--force`, is released with `release_session`, which signals the watcher only while the watcher's PID still has its recorded start time. A nested `stop`, whose `CX_SESSION_PARENT` equals the live lock's pid (`ui`'s stop of a leftover headless Steam, er.sh, a block), ends Steam and the server but never releases the lock and never refuses, whatever the owner, so `ui`'s later `lock_anchor` moves a complete lock (4.9 item 5; R4-1, R4-3). A stale lock is left for the next claim to replace, and its watcher is never signalled: it exits by itself with its anchor (R2-5). The lock of `er.sh`, promote, a rollback or a test block is never removed by `stop`. Exit status 0, 1 (REFUSE) or 2, as above; with no Steam and no server running it exits 0.
  - `reset-rung [--append ARGS] [--renderer gl] [--winemetal]` (review C16, R2-7): lock check; refuses while a steam.exe of this session runs (`steam.sh stop` first); `claim_session steam-rung $$` (inside a caller's session the claim is nested and changes nothing). Then, with msync 0:
    1. Reset: delete `CommandLineAppend` and the `Direct3D` subkey under `HKCU\Software\Wine\AppDefaults\steamwebhelper.exe` (`|| true`: on the first rung neither exists); remove `winemetal.dll` from system32 and syswow64 when it is `cmp`-equal to DXMT's copy and BUILDINFO says `bundled-dxmt=0` (on a bundled build those files come from wineboot and stay, R1-7).
    2. The rung: `--append ARGS` writes `CommandLineAppend=ARGS`; `--renderer gl` writes `Direct3D` `renderer=gl`; `--winemetal` copies DXMT's `winemetal.dll` (x86_64 into system32, i386 into syswow64) when BUILDINFO says `bundled-dxmt=0`, and does nothing on a bundled build.
    3. It saves `reg query 'HKCU\Software\Wine\AppDefaults' /s` to `$CX_LOGS/appdefaults-start.txt`, runs `wineserver -w` and releases its lock.
  - `open URL` (R2-7): only inside a live `steam-ui` or `steam-daniel` session of this prefix. It runs `cx-run.sh --msync <.cx-session> -- 'C:\Program Files (x86)\Steam\steam.exe' URL` with `CX_SESSION_PARENT` set to the lock's pid; the running client takes the URL and the helper process exits. M8.4 uses it for `steam://install/3132990`.
  - `status`: prints the lock (owner, prefix, live or stale), whether a steam.exe of this session is alive, and the ready state (S7) with the msync and the mode from `.cx-session`; for `offline=1` readiness needs no `[Logged On,` line (R3-1). It exits 0 only when Steam is ready.
- **`er.sh [--msync N] [--gptk VER] [--no-d3dshared] [--probe-only] [--first-frame-timeout S] [--duration S [--start-on FILE]] [--max-session S]`**: the M7.2 sequence and its three phases (R2-8). It holds the session lock (owner `er`, its own PID and start time) and passes `CX_SESSION_PARENT=$$` to `steam.sh stop` and `steam.sh silent`, so the lock survives its internal Steam restart (R1-15).
  - Defaults: msync is the running session's (`.cx-session`), else 0, and so is the Steam mode: a restart of an `offline=1` session uses `silent --offline`, never an online start (R3-1); `--gptk` 4.0b3; `--first-frame-timeout` 1200 s; `--max-session` 14400 s, applied by running the game under `with-timeout.sh <max-session>`; no `--duration`. Agent-only cycles pass `--duration 300` or `--probe-only`; only Daniel's play test runs without them (M7.2, R3-9).
  - `VER` from `--gptk` is used throughout (R3-10): `cx-run.sh --d3dmetal "$VER"`, `probe.sh DIR eldenring.exe "$VER"`, `gptk_mapped DIR "$VER" 'd3d12|dxgi'` and `d3dm_cache_in eldenring.exe "$VER"`. er.sh sets `CX_GPTK=$VER` without exporting it, so its own `preflight_prefix` checks that tree's manifest and `gates_header` records it, while a Steam it restarts keeps the default tree.
  - Start: `gates_header N er` is the first line of `gates.txt`, written before the watcher starts (R3-2). `d3dm-log.sh`'s PID and start time go into `$CX_LOGS/d3dm-log.pid` as one line, `<pid> <pid_start>` (4.8 step 5).
  - Phases 1 and 2 (first frame, probes at +30 and +180 s): `first_frame` and `wait_or_dialog … <game pid>`, so only a dialog owned by the game PID ends the run (review C13). Ending the run means `probe.sh` once more, then `kill <game pid>` and `kill -9` after 10 s; the headless Steam keeps running. `--probe-only` ends the game after the first probe (M7.1b).
  - Phase 3: without `--duration`, `lock_anchor <game pid> er-daniel`, `export CX_SESSION_PARENT=<game pid>`, `detach /bin/bash -c 'source "$0"; reap_after "$1" "$2"' "$X/lib.sh" <game pid> <d3dm-log.sh pid> &` (R3-9), `HANDED-OVER` into `gates.txt`, then wait for the game to exit; dialogs are only recorded. With `--duration S` the owner stays `er`, and er.sh ends the game S seconds after the first frame, or after `FILE` appears when `--start-on FILE` is given.
  - On exit, meaning any end of er.sh including SIGTERM, SIGINT and SIGHUP through its EXIT trap: as M7.2 step 9. In an interactive phase 3 with the game still running, it leaves the game and the `er-daniel` lock alone and writes `INTERRUPTED`, and the reaper ends `d3dm-log.sh` once the game has exited; otherwise it ends the game if it still runs, stops `d3dm-log.sh`, runs `steam.sh collect`, `d3dm_cache_out eldenring.exe` and `backup-userdata.sh`, writes the gates and releases the lock.
  - It exits 0 only if E1-E7 pass and E9 is recorded; INCONCLUSIVE gates are listed separately.
- **`hud-stats.sh LOG [--last N | FROM_FRAME TO_FRAME]`**: reads `metal-HUD: <frame>,<gfx mem>,<proc mem>,<interval>,<gpu time>,…` lines (one per second), takes field 4 (the frame interval) of the last N lines (`--last`, as M7.4 uses it) or of the frames in range, and prints `n=… median=… p95=…` using `sort -n` and `awk`. **ASSUMPTION:** the field order Apple documents; confirm it on the first log.
- **`ref-run.sh [--prefix NAME] [--debug SPEC] [--log FILE] -- PROGRAM ...`**: runs the reference runtime's `bin/wine`, or `bin/wineserver` when PROGRAM is `wineserver`, from `$(cat ~/Games/sdk/ref/athei-cx-26.3.0-9/RUNTIME_ROOT)` (written in M6.0), after the same scrub as `cx-run.sh`, with `WINEPREFIX=~/Games/prefixes/cx_ref_prefix` (default), `WINEMSYNC=0` and `WINEDEBUG`. It sets no `WINEDLLPATH_PREPEND` and no `CX_*` variable: the reference build carries its own compatdb rules and finds its own libd3dshared. It refuses a prefix named `cx_prefix` or `cx_dlss`.
- `stage-dlss-copies.sh` and `copy-steam-login.sh` are given in full in A.14.

### A.9 `scripts/cx/lib.sh` (sourced by the cx scripts and the session blocks)
```bash
# scripts/cx/lib.sh: helpers shared by the cx scripts and the inline session blocks (sourced; bash 3.2; sets no shell options)
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/env.sh"
X="$REPO/scripts/cx"
P="$HOME/Games/prefixes/${CX_PREFIX_NAME:-cx_prefix}"            # the session's prefix: cx_prefix, cx_smoke, cx_dlss or cx_ref_prefix
RTR="$(cd "${CX_RT:-$RT_LINK}" 2>/dev/null && pwd -P || true)"    # empty before the first promote; --ref mode sets CX_RT (M6.0)

# ---- Session lock (plan 4.9). Fields: owner, pid (the anchor whose life is the session's life), pid_start (that process's
# ---- start time), prefix (or all), start, epoch (claim time in seconds), build; while a watcher runs: watcher, watcher_start.
lock_field() { sed -n "s/^$1=//p" "$CX_LOCK" 2>/dev/null | head -1; }
pid_start() { ps -o lstart= -p "$1" 2>/dev/null | awk '{$1 = $1; print}'; }   # e.g. "Tue Oct 20 16:00:43 2026"; empty if gone
pid_is() { [ -n "$1" ] && [ -n "$2" ] && [ "$(pid_start "$1")" = "$2" ]; }     # pid_is PID START: that very process still runs
boot_epoch() { sysctl -n kern.boottime | sed -E 's/^\{ sec = ([0-9]+),.*/\1/'; }
lock_live() {   # live = the anchor still runs with its recorded start time, and the lock was written after the last boot
  [ -e "$CX_LOCK" ] || return 1
  [ "$(lock_field epoch)" -ge "$(boot_epoch)" ] 2>/dev/null || return 1
  pid_is "$(lock_field pid)" "$(lock_field pid_start)"
}
lock_set() {   # lock_set FIELD VALUE
  { /usr/bin/grep -v "^$1=" "$CX_LOCK" || true; printf '%s=%s\n' "$1" "$2"; } > "$CX_LOCK.tmp" && mv "$CX_LOCK.tmp" "$CX_LOCK"
}
lock_anchor() {   # lock_anchor PID [OWNER]: move the lock to another anchor in one write (steam.sh ui: the wineserver;
                  # er.sh and the M8.4 block: the game handed to Daniel, owner er-daniel or m84-daniel)
  local o s; o="${2:-$(lock_field owner)}"; s="$(pid_start "$1")"
  { /usr/bin/grep -vE '^(owner|pid|pid_start)=' "$CX_LOCK" || true; printf 'owner=%s\npid=%s\npid_start=%s\n' "$o" "$1" "$s"; } \
    > "$CX_LOCK.tmp" && mv "$CX_LOCK.tmp" "$CX_LOCK"
}
claim_session() {   # claim_session OWNER PID [PREFIX|all]: 0 = taken, or already ours (nested); 1 = refused
  mkdir -p "$CX_LOG_ROOT"
  if lock_live; then
    if [ -n "${CX_SESSION_PARENT:-}" ] && [ "$(lock_field pid)" = "$CX_SESSION_PARENT" ]; then return 0; fi
    if [ "${CX_FORCE:-0}" != 1 ]; then echo "REFUSE: session lock held: $(tr '\n' ' ' < "$CX_LOCK")" >&2; return 1; fi
    echo "FORCE: replacing a live lock: $(tr '\n' ' ' < "$CX_LOCK")" >&2
  elif [ -e "$CX_LOCK" ]; then
    echo "stale lock replaced: $(tr '\n' ' ' < "$CX_LOCK")" >&2
  fi
  printf 'owner=%s\npid=%s\npid_start=%s\nprefix=%s\nstart=%s\nepoch=%s\nbuild=%s\n' "$1" "$2" "$(pid_start "$2")" \
    "${3:-$(basename "$P")}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(date +%s)" "$(head -1 "$RTR/BUILDINFO" 2>/dev/null || true)" \
    > "$CX_LOCK.tmp" && mv "$CX_LOCK.tmp" "$CX_LOCK"
}
release_session() {   # release_session OWNER PID: remove the lock only if OWNER and PID hold it. Its watcher is signalled only
                      # while the watcher's PID still has the recorded start time, so a reused PID is never killed (R2-5)
  local w
  { [ -e "$CX_LOCK" ] && [ "$(lock_field owner)" = "$1" ] && [ "$(lock_field pid)" = "$2" ]; } || return 0
  w="$(lock_field watcher)"
  if pid_is "$w" "$(lock_field watcher_start)"; then kill "$w" 2>/dev/null || true; fi
  rm -f "$CX_LOCK"
}
begin_session() {   # begin_session OWNER [idle]: top-level blocks only. Lock for this script ($$), release on exit,
                    # keep the Mac awake. 'idle' also refuses while any process of the runtime runs (headless Steam too).
  claim_session "$1" $$ || exit 1
  if [ "$(lock_field pid)" = "$$" ]; then export CX_SESSION_PARENT=$$; fi
  trap "release_session '$1' $$" EXIT
  if [ "${2:-}" = idle ] && [ -n "$(runtime_pids)" ]; then
    echo "REFUSE: processes of $RTR are still running (steam.sh stop, or plan 4.8 step 3)" >&2; exit 1
  fi
  caffeinate -dimsu -w $$ &
}
detach() {   # detach CMD [ARGS...] & : run CMD in a new session, so it outlives this script and the agent's tool call
  exec /usr/bin/perl -MPOSIX -e 'POSIX::setsid(); exec @ARGV or die "exec $ARGV[0]: $!\n"' "$@"
}
reap_after() {   # reap_after ANCHOR PID : once ANCHOR exits, end PID if it is still the same process (start times checked).
                 # er.sh and the M8.4 block run it detached at a hand-over, so their log stream ends with the game (R3-9)
  local as ps; as="$(pid_start "$1")"; ps="$(pid_start "$2")"
  while pid_is "$1" "$as"; do sleep 10; done
  if pid_is "$2" "$ps"; then kill "$2" 2>/dev/null; fi
  return 0
}

# ---- Processes of this runtime and of this session
runtime_pids() { [ -n "$RTR" ] || return 0; lsof -t "$RTR/lib/wine/x86_64-unix/ntdll.so" 2>/dev/null | sort -u; }
session_pids() {   # this runtime's processes whose exec-time environment has WINEPREFIX=$P (one session; checked by T13).
                   # CX_SESSION_FILTER=0 (local.env) returns every runtime PID: safe, because sessions never overlap (4.9)
  local p
  for p in $(runtime_pids); do
    if [ "${CX_SESSION_FILTER:-1}" = 0 ]; then echo "$p"; continue; fi
    case " $(ps -E -ww -o command= -p "$p" 2>/dev/null) " in *" WINEPREFIX=$P "*) echo "$p" ;; esac
  done
}
server_pid() {   # the wineserver serving $P. It outlives Steam's self-restarts, so it anchors a Steam session (4.9)
  local p
  [ -n "$RTR" ] || return 1
  for p in $(lsof -t "$RTR/bin/wineserver" 2>/dev/null); do
    if [ "${CX_SESSION_FILTER:-1}" = 0 ]; then echo "$p"; return 0; fi
    case " $(ps -E -ww -o command= -p "$p" 2>/dev/null) " in *" WINEPREFIX=$P "*) echo "$p"; return 0 ;; esac
  done
  return 1
}
game_pid() {   # game_pid EXE: the PID of this session's Wine process whose command line contains EXE (empty if none)
  local p
  for p in $(session_pids); do
    case "$(ps -o args= -p "$p" 2>/dev/null)" in *"$1"*) echo "$p"; return 0 ;; esac
  done
  return 1
}

gates_header() {   # gates_header MSYNC RUNG: first line of every gates.txt (plan 4.1). gptk = version:manifest hash (R3-10);
                   # offline = the offline= field of $P/.cx-session, the last Steam start (none without one; R3-1)
  local cl steamv off
  cl="$P/drive_c/Program Files (x86)/Steam/logs/connection_log.txt"
  steamv="$( { /usr/bin/grep -h 'Client version' "$cl" 2>/dev/null || true; } | tail -1 | sed 's/.*Client version: *//')"
  off="$(sed -n 's/^offline=//p' "$P/.cx-session" 2>/dev/null || true)"
  printf 'build=%s os=%s steam=%s gptk=%s:%s rung=%s msync=%s offline=%s load="%s"\n' \
    "$(head -1 "$RTR/BUILDINFO" 2>/dev/null || echo "ref:${RTR##*/}")" "$(sw_vers -buildVersion)" "${steamv:-none}" \
    "${CX_GPTK:-4.0b3}" "$(shasum -a 256 "$HOME/Games/sdk/gptk/${CX_GPTK:-4.0b3}/MANIFEST.sha256" 2>/dev/null | cut -c1-12)" \
    "${2:-}" "${1:-}" "${off:-none}" "$(uptime | sed 's/.*load averages*: //')"
}

preflight_prefix() {   # refuse to run on a prefix that is not promoted to the current build (plan 2.4, review C2 and F8)
  local want; want="$(head -1 "$RTR/BUILDINFO")"
  [ "$(head -c 7 "$P/.update-timestamp" 2>/dev/null)" = disable ] \
    || { echo "REFUSE: $P/.update-timestamp is not 'disable' (run build-wine-cx.sh promote)" >&2; return 1; }
  [ "$(cat "$P/.m5runner-runtime" 2>/dev/null)" = "$want" ] \
    || { echo "REFUSE: $P is stamped for another build than $want (run build-wine-cx.sh promote)" >&2; return 1; }
  CX_RT="$RTR" "$X/prefix-check.sh" "$(basename "$P")" > /dev/null \
    || { echo "REFUSE: prefix-check.sh failed for $P" >&2; return 1; }
  (cd "$HOME/Games/sdk/gptk/${CX_GPTK:-4.0b3}" && shasum -a 256 -s -c MANIFEST.sha256) \
    || { echo "REFUSE: the GPTK ${CX_GPTK:-4.0b3} tree no longer matches MANIFEST.sha256" >&2; return 1; }
}
snap_prefix() {   # snap_prefix TAG: APFS clone of $P to $P.snap-TAG, inside a session with Wine stopped (plan 4.1, M6.2).
                  # BSD 'cp -Rc SRC DST' onto an existing DST copies into DST/<name> and keeps the stale top level, so an
                  # existing snapshot of that tag is moved aside to $P.snap-TAG.old-<UTC> first (R3-6)
  local d="$P.snap-$1" o
  if [ -e "$d" ]; then o="$d.old-$(date -u +%Y%m%dT%H%M%SZ)"; mv "$d" "$o" || return 1; echo "kept the previous snapshot as $o" >&2; fi
  cp -Rc "$P" "$d"
}

is_black() {   # is_black PNG [hud]: 0 = (nearly) all black, 1 = not black, 2 = error. Uses sips + od only.
               # 8x8 downsample; the mean of the colour bytes (alpha skipped) below 8 of 255 counts as black.
               # 'hud' ignores the top-right quarter, where the Metal HUD draws (ASSUMPTION checked at H8).
  local t off w h bpp rc=0
  t="$(mktemp -t cxpx)" || return 2
  sips -z 8 8 -s format bmp "$1" --out "$t.bmp" > /dev/null 2>&1 || true        # sips can exit 0 on a missing input
  if [ ! -s "$t.bmp" ]; then rm -f "$t" "$t.bmp"; return 2; fi
  off="$(od -An -v -tu4 -j10 -N4 "$t.bmp" | tr -d ' ')"
  w="$(od -An -v -td4 -j18 -N4 "$t.bmp" | tr -d ' ')"; h="$(od -An -v -td4 -j22 -N4 "$t.bmp" | tr -d ' ')"
  bpp="$(od -An -v -tu2 -j28 -N2 "$t.bmp" | tr -d ' ')"
  od -An -v -tu1 -j"$off" "$t.bmp" | awk -v w="$w" -v h="$h" -v bpp="$bpp" -v mask="${2:-}" '
    { for (i = 1; i <= NF; i++) b[n++] = $i }
    END {
      if (bpp != 24 && bpp != 32) exit 2
      B = bpp / 8; rowlen = int((w * B + 3) / 4) * 4; H = (h < 0) ? -h : h
      for (r = 0; r < H; r++) {
        top = (h > 0) ? H - 1 - r : r                     # rows are stored bottom-up when the height is positive
        for (c = 0; c < w; c++) {
          if (mask == "hud" && top < H / 2 && c >= w / 2) continue
          p = r * rowlen + c * B
          s += b[p] + b[p + 1] + b[p + 2]; k += 3         # B, G, R; the 4th byte of a 32-bit pixel (alpha) is skipped
        }
      }
      if (k == 0) exit 2
      if (s / k < 8) exit 0
      exit 1
    }' || rc=$?
  rm -f "$t" "$t.bmp"; return "$rc"
}

watch_dialogs() {   # watch_dialogs DIR [ANCHOR_PID] & : modal-looking windows of this session -> a DIALOG line, a PNG, and the
                    # owner PID appended to DIR/FAIL-dialog. It only records; each poll loop decides whether a dialog ends
                    # its run (review C13, R2-8). Ends by itself when ANCHOR_PID (checked with its start time) exits.
  local d="$1" anchor="${2:-}" as="" p id pid owner title size w h lt
  if [ -n "$anchor" ]; then as="$(pid_start "$anchor")"; fi
  while sleep 10; do
    if [ -n "$anchor" ] && ! pid_is "$anchor" "$as"; then return 0; fi
    set --; for p in $(session_pids); do set -- "$@" --pid "$p"; done
    [ $# -gt 0 ] || continue
    while IFS="$(printf '\t')" read -r id pid owner title size; do
      w="${size%x*}"; h="${size#*x}"
      lt="$(printf '%s' "$title" | tr '[:upper:]' '[:lower:]')"
      case "$lt" in *error*|*fatal*|wine|*crash*) ;; *) continue ;; esac
      if [ "$w" -lt 800 ] && [ "$h" -lt 600 ] && [ ! -e "$d/dialog-$id.png" ]; then
        screencapture -x -o -l "$id" "$d/dialog-$id.png" 2>/dev/null
        echo "DIALOG pid=$pid title=$title" >> "$d/gates.txt"; echo "$pid" >> "$d/FAIL-dialog"
      fi
    done < <("$HOME/Games/tools/wine-windows" "$@" 2>/dev/null)
  done
}
dialog_seen() {   # dialog_seen DIR [PID]: 0 if a dialog was recorded in DIR (with PID: only a dialog owned by that PID)
  [ -e "$1/FAIL-dialog" ] || return 1
  [ -n "${2:-}" ] || return 0
  [ "$(/usr/bin/grep -cx -- "$2" "$1/FAIL-dialog" || true)" -ge 1 ]
}
wait_or_dialog() {   # wait_or_dialog SECONDS DIR [PID]: sleep in 5-s steps; return 1 as soon as dialog_seen DIR [PID]
  local left="$1"
  while [ "$left" -gt 0 ]; do
    if dialog_seen "$2" "${3:-}"; then return 1; fi
    sleep 5; left=$((left - 5))
  done
  ! dialog_seen "$2" "${3:-}"
}
first_frame() {   # first_frame EXE DIR LIMIT: every 15 s, capture EXE's window and test it with 'is_black PNG hud' (review C24).
                  # 0 = a frame that is not black (prints the seconds; DIR/first-frame.png), 1 = a dialog owned by EXE's PID,
                  # 2 = EXE gone (or not started within 60 s) or LIMIT passed, 3 = LIMIT passed and every capture met a locked screen
  local t=0 gp rc shot=0 locked=0
  while [ "$t" -lt "$3" ]; do
    sleep 15; t=$((t + 15))
    gp="$(game_pid "$1")" || { if [ "$t" -lt 60 ]; then continue; fi; return 2; }
    if dialog_seen "$2" "$gp"; then return 1; fi
    "$X/capture.sh" --pid "$gp" "$2/first-frame.png" > /dev/null 2>&1; rc=$?
    if [ "$rc" -eq 4 ]; then locked=$((locked + 1)); continue; fi
    [ "$rc" -eq 0 ] || continue
    shot=$((shot + 1)); is_black "$2/first-frame.png" hud; rc=$?
    if [ "$rc" -eq 1 ]; then echo "$t"; return 0; fi
  done
  if [ "$shot" -eq 0 ] && [ "$locked" -gt 0 ]; then return 3; fi
  return 2
}

gptk_mapped() {   # gptk_mapped PATH VER 'd3d12|dxgi': how many of the named DLLs a process had mapped from
                  # ~/Games/sdk/gptk/VER/wine/x86_64-windows. PATH is a probe.sh directory (its lsof.txt and vmmap.txt) or
                  # one listing file. lsof and vmmap name the real file, as an absolute path after a blank; Wine's "mapping
                  # PE file" trace names the file the loader asked for (system32), so run logs are never evidence (review F15).
  local v
  local -a f
  v="$(printf '%s' "$2" | sed 's/\./\\./g')"
  if [ -d "$1" ]; then f=("$1/lsof.txt" "$1/vmmap.txt"); else f=("$1"); fi
  { cat "${f[@]}" 2>/dev/null || true; } \
    | { /usr/bin/grep -oE '(^|[[:space:]])/[^[:space:]]*/gptk/'"$v"'/wine/x86_64-windows/('"$3"')\.dll' || true; } \
    | sed 's#.*/##' | sort -u | wc -l | tr -d ' '
}
steam_lsof() {   # steam_lsof DIR: lsof of every running steam.exe and steamwebhelper.exe of this session into DIR/<pid>.txt
  local p
  mkdir -p "$1"
  for p in $(session_pids); do
    case "$(ps -o args= -p "$p" 2>/dev/null)" in *steam.exe*|*steamwebhelper.exe*) lsof -p "$p" > "$1/$p.txt" 2>/dev/null ;; esac
  done
}
winemetal_check() {   # winemetal_check STEAMLOG LSOFDIR: the rung-L1 winemetal pre-check (M6, review F12; R1-6).
                      # FAIL: a process logged 'failed to load "...winemetal.so"' (+module WARN with dyld's reason).
                      # PASS: no such line, and a Steam process's lsof (steam_lsof) maps .../x86_64-unix/winemetal.so.
                      # INCONCLUSIVE otherwise. The +module "mapping PE file" line names system32\winemetal.dll whatever
                      # file was found, so it is never PASS evidence.
  local bad ok
  bad="$(/usr/bin/grep -cE 'failed to load "[^"]*winemetal\.so"' "$1" 2>/dev/null || true)"
  ok="$(cat "$2"/*.txt 2>/dev/null | /usr/bin/grep -cE '/x86_64-unix/winemetal\.so$' || true)"
  if [ "${bad:-0}" -ge 1 ]; then
    echo "winemetal pre-check: FAIL (winemetal.so did not load)"; /usr/bin/grep -m1 -E 'failed to load "[^"]*winemetal\.so"' "$1"; return 1
  elif [ "${ok:-0}" -ge 1 ]; then echo "winemetal pre-check: PASS (winemetal.so mapped in a Steam process, no load failure)"
  else echo "winemetal pre-check: INCONCLUSIVE (no running Steam process of this session maps winemetal.so)"; return 2; fi
}

# ---- D3DMetal shader cache: one copy per GPTK version for one exe (plan M7.5, R2-11). Only d3dm/<EXE> moves; other exes'
# ---- caches (GPTK 7.7's steam.exe/, steamwebhelper.exe/) are never touched. D3DM_CACHE_ROOT exists for the unit tests.
D3DM_ROOT="${D3DM_CACHE_ROOT:-$(getconf DARWIN_USER_CACHE_DIR)}"
d3dm_cache_in() {   # d3dm_cache_in EXE VER: park d3dm/EXE, bring back VER's own copy; prints warm or cold; 1 = refused
  local c="${D3DM_ROOT%/}/d3dm/$1" s="${D3DM_ROOT%/}/d3dm.cx-stash" a
  mkdir -p "${D3DM_ROOT%/}/d3dm" "$s/$2" "$s/original"
  if [ -f "$s/active-$1" ]; then              # a killed run never swapped back: file its cache under that run's version
    a="$(cat "$s/active-$1")"; mkdir -p "$s/$a"
    if [ -e "$c" ]; then rm -rf "$s/$a/$1"; mv "$c" "$s/$a/$1"; fi
    rm -f "$s/active-$1"
  elif [ -e "$c" ]; then                      # not ours (GPTK 7.7's, or unmarked): parked until d3dm_cache_out
    if [ -e "$s/original/$1" ]; then echo "REFUSE: $s/original/$1 exists already; sort it out by hand (plan M7.5)" >&2; return 1; fi
    mv "$c" "$s/original/$1"
  fi
  if [ -e "$s/$2/$1" ]; then mv "$s/$2/$1" "$c"; echo warm; else echo cold; fi
  printf '%s\n' "$2" > "$s/active-$1"
}
d3dm_cache_out() {   # d3dm_cache_out EXE: file the active version's cache in the stash and put the parked original back
  local c="${D3DM_ROOT%/}/d3dm/$1" s="${D3DM_ROOT%/}/d3dm.cx-stash" a
  [ -f "$s/active-$1" ] || return 0
  a="$(cat "$s/active-$1")"; mkdir -p "$s/$a"
  if [ -e "$c" ]; then rm -rf "$s/$a/$1"; mv "$c" "$s/$a/$1"; fi
  if [ -e "$s/original/$1" ]; then mv "$s/original/$1" "$c"; fi
  rm -f "$s/active-$1"
}

regval() {   # regval FILE 'Software\\Valve\\Steam' NAME: raw value of NAME in that key of a Wine .reg file (no Wine run).
             # Callers keep the value in a variable and never print it (account data, plan Conventions)
  K="[$2]" N="\"$3\"=" awk 'index($0, ENVIRON["K"]) == 1 { s = 1; next } /^\[/ { s = 0 }
    s && index($0, ENVIRON["N"]) == 1 { print substr($0, length(ENVIRON["N"]) + 1); exit }' "$1"
}
```
- **Session lock and scope** (4.9). `claim_session`, `release_session`, `begin_session` and `lock_anchor` implement the lock. A lock is live only while its anchor runs with the start time recorded at the claim (`ps -o lstart=`, with blanks normalized by awk) and its `epoch` is later than `kern.boottime`, so a reused PID or a reboot makes it stale (R2-5, R2-10). `session_pids` and `server_pid` find one session's processes by their `WINEPREFIX` (gate T13), and `game_pid` finds a program among them by its command line. `detach` starts a process in a new session (perl's `POSIX::setsid`; checked on this Mac: the child became its own process-group leader). The lock functions and the `cx-run.sh` guard were exercised in a scratch HOME on 2026-10-20, in round 4 with exactly these sources (4.9).
- **`is_black`** (R1-11) downsamples the screenshot to 8x8 with `sips`, reads the BMP header (pixel offset at byte 10, width 18, height 22, bit depth 28) and the pixel bytes with `od -v`, which never collapses repeated rows into `*`. It skips the 4th byte of 32-bit pixels, because macOS window captures carry an alpha channel and opaque alpha would make a black frame look bright, and it calls the image black when the mean colour value is below 8 of 255. With `hud` it ignores the top-right quarter, where the Metal HUD draws, so a black frame with the HUD on still counts as black. `sips` writes top-down BMPs here (negative height); bottom-up files are handled too. Tested on 2026-10-20 on the verifier's images and our own (`tests/test_cx_harness.py` keeps the cases): opaque-black RGBA 0, black RGB 0, near-black 3 and 5 black; uniform grey 20, 40, 60 and 128 not black; a black frame with a bright top-right block not black, black with `hud`; the same block top-left or bottom-right not black with `hud`; a dark title-like frame not black; a missing file 2.
- **`watch_dialogs`** (review C13, R2-8) looks only at this session's processes and matches titles case-insensitively against `*error*`, `*fatal*`, `wine` and `*crash*`, which also covers Steam's "Steam - Error", "Steam - Fatal Error" and "Fatal Error" boxes and upper-case "ERROR" titles. A window smaller than 800x600 with such a title is captured once (`dialog-<window id>.png`), logged as a `DIALOG` line, and its owner PID is appended to `DIR/FAIL-dialog`. The watcher never kills anything; the poll loops decide, through `dialog_seen DIR [PID]`. `wait_or_dialog SECONDS DIR` in the M5.3 and M8 blocks ends the run on any dialog of the session, which holds only the test program. `steam.sh ui` ends its run on a dialog only until the window is announced, and `silent` only during its own wait. er.sh and the M8.4 block pass the game PID (`wait_or_dialog SECONDS DIR PID`, `first_frame`), so only the game's own dialog ends their phase-1 and phase-2 waits, and after the hand-over no dialog ends anything. Tested on 2026-10-20 (round 3): `dialog_seen` and `wait_or_dialog` with and without a PID.
- **`first_frame`** (review C24, R2-8) polls every 15 s: it finds the program with `game_pid`, stops at a dialog of that PID, captures the program's window and returns as soon as `is_black PNG hud` calls a capture not black. It needs a running Wine program, so it was syntax-checked only.
- **`gptk_mapped`** (review F15, round 3) reads a probe directory's `lsof.txt` and `vmmap.txt`, or one listing file, and counts distinct DLL names mapped from `gptk/<ver>/wine/x86_64-windows/`. It accepts only absolute paths after a blank, as lsof and vmmap print them, so a Wine run log never counts. Tested on sample listings: d3d12.dll from GPTK with dxgi.dll from `lib/wine` gives 1, both from GPTK 2, `d3d12core.dll` alone 0, another version 0; the real trace text, the round-2 verifier's synthetic log and the round-2 sample log all give 0.
- **`steam_lsof` and `winemetal_check`** (R1-6, round 3) are the rung-L1 pre-check (M6). Tested: the verifier's two failure lines give FAIL (exit 1); an empty log, and the system32 mapping line alone, give INCONCLUSIVE (exit 2); a listing with DXMT's `winemetal.so` gives PASS (exit 0).
- **`d3dm_cache_in` and `d3dm_cache_out`** (R2-11, M7.5). Tested with a stand-in cache root: an unmarked `eldenring.exe` directory was parked and came back unchanged; 4.0b3 and 3.0 kept separate copies (cold, then warm); a run killed without `d3dm_cache_out` was filed under its version by the next `d3dm_cache_in`; `steam.exe/` was never touched.
- **`regval`** (R1-19) reads one value from a Wine `.reg` text file through `ENVIRON`, so the doubled backslashes of the key name survive (awk's `-v` would unescape them).
- **`gates_header`** (R3-1, R3-2, R3-10) prints `gptk=<CX_GPTK>:<manifest hash>` and `offline=` from `.cx-session` (`none` without one). Tested with and without a `.cx-session`, with `CX_GPTK=3.0`, and under `set -euo pipefail`.
- **`snap_prefix`** (R3-6) moves an existing `$P.snap-TAG` aside before `cp -Rc`. Tested: a second snapshot of a changed prefix holds the new files, the first is kept as `.old-<UTC>`, and nothing is nested; a bare `cp -Rc` onto the same snapshot left the old files on top and the new copy at `<snapshot>/cx_prefix`.
- **`reap_after`** (R3-9) ends the target once the anchor exits; both identities are checked with `pid_start`. Tested directly and started through `detach`, as er.sh and the M8.4 block start it.

### A.10 `scripts/build-wine-cx.sh`
```bash
#!/bin/bash
# build-wine-cx.sh all | STAGE | from STAGE | iter
# Runs scripts/cx/stages/<stage>.sh in a fresh /bin/bash, logs to $CXB/logs/<stage>.log, stamps $CXB/stamps/<stage>.ok.
# 'from S' clears the stamps of S and every later stage; 'iter' = 'from make'. Exits non-zero at the first failing stage.
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd -P)/cx/env.sh"
ORDER="fetch deps src tools configure make install assemble verify promote"
mkdir -p "$CXB/logs" "$CXB/stamps"
caffeinate -dimsu -w $$ &
invalidate_from() {
  local hit=0 s
  for s in $ORDER; do [ "$s" = "$1" ] && hit=1; [ "$hit" = 1 ] && rm -f "$CXB/stamps/$s.ok"; done
  [ "$hit" = 1 ] || { echo "unknown stage $1" >&2; exit 2; }
}
run() {
  local s="$1"
  if [ -f "$CXB/stamps/$s.ok" ]; then echo "skip $s (stamped)"; return 0; fi
  echo "== $s $(date '+%H:%M:%S')"
  if /bin/bash "$REPO/scripts/cx/stages/$s.sh" > "$CXB/logs/$s.log" 2>&1; then
    touch "$CXB/stamps/$s.ok"
  else
    echo "FAIL $s (log: $CXB/logs/$s.log)"; tail -40 "$CXB/logs/$s.log"; exit 1
  fi
}
case "${1:-all}" in
  all)  for s in $ORDER; do run "$s"; done ;;
  from) invalidate_from "${2:?usage: build-wine-cx.sh from STAGE}"; for s in $ORDER; do run "$s"; done ;;
  iter) invalidate_from make; for s in $ORDER; do run "$s"; done ;;
  *)    case " $ORDER " in
          *" $1 "*) rm -f "$CXB/stamps/$1.ok"; run "$1" ;;
          *) echo "usage: build-wine-cx.sh all|STAGE|from STAGE|iter" >&2; exit 2 ;;
        esac ;;
esac
```

### A.11 `scripts/cx/verify-runtime.sh`
```bash
#!/bin/bash
# verify-runtime.sh [RT]: static gates V1-V15 (plan M3.4). Never touches a prefix; V14 only runs 'wine --version'.
# Gate-style script: set -u only, and every check captures output instead of ending a pipeline with grep -q.
set -u
RT="$(cd "${1:-$HOME/Games/sdk/wine-cx26}" && pwd -P)"; U="$RT/lib/wine/x86_64-unix"; bad=0
has() { [ "$(printf '%s\n' "$1" | /usr/bin/grep -cE "$2")" -ge "${3:-1}" ]; }   # has TEXT REGEX [MIN]
v1()  { [ "$(lipo -archs "$U/wine")" = x86_64 ]; }
v2()  { ! has "$(otool -hv "$U/wine")" ' PIE( |$)'; }
v3()  { has "$(otool -l "$U/wine")" 'segname WINE_RESERVE'; }
v4()  { local f; for f in ntdll.so win32u.so winemac.so; do [ "$(lipo -archs "$U/$f")" = x86_64 ] || { echo "  V4 $f"; return 1; }; done; }
v5()  { [ "$(otool -l "$U/ntdll.so" | awk '/LC_BUILD_VERSION/{f=1} f&&/minos/{print $2; exit}')" = 14.0 ]; }
v6()  { has "$(otool -l "$U/ntdll.so" | /usr/bin/grep -A2 LC_RPATH)" '@loader_path/\.\./\.\.'; }
v7()  { has "$(nm -gU "$U/winemac.so")" ' _macdrv_functions$' &&
        has "$(nm -gU "$U/ntdll.so")" ' _(prepend_dll_path|add_load_order_override|KeServiceDescriptorTable|NtCreateThreadEx)$' 4; }
v8()  { has "$(strings -a "$U/ntdll.so")" 'WINEDLLPATH_PREPEND'; }
v9()  { local o; o="$(x86_64-w64-mingw32-objdump -p "$RT/lib/wine/x86_64-windows/ntdll.dll")"
        has "$o" '__wine_unix_call_dispatcher$' && has "$o" '__wine_unix_call$'; }
v10() { [ "$(ls "$RT/lib/wine/i386-windows" | wc -l)" -gt 500 ]; }
v11() { local leaks
        leaks="$(find "$RT" -type f \( -name '*.so' -o -name '*.dylib' \) -exec sh -c 'for f; do otool -L "$f" | /usr/bin/grep -v ":\$"; done' sh {} + \
                 | /usr/bin/grep -E '/opt/homebrew|/opt/local|/usr/local|/Users/')"
        [ -z "$leaks" ] || { printf '  %s\n' "$leaks" | head -5; return 1; }; }
v12() { has "$(strings -a "$U/win32u.so")" 'libfreetype\.6\.dylib' && has "$(strings -a "$U/win32u.so")" 'libMoltenVK\.dylib' &&
        has "$(strings -a "$U/bcrypt.so")" 'libgnutls\.30\.dylib' && has "$(strings -a "$U/winebus.so")" 'libSDL2'; }
v13() { local f; for f in "$RT"/lib/*.dylib; do [ -L "$f" ] || codesign -v "$f" 2>/dev/null || { echo "  V13 $f"; return 1; }; done; }
v14() { [ "$("$RT/bin/wine" --version)" = "$(head -1 "$RT/BUILDINFO" | sed 's/^b[0-9]*-//')" ]; }
v15() { [ -d "$RT/share/wine/mono/wine-mono-10.4.1" ] && [ -d "$RT/share/wine/gecko/wine-gecko-2.47.4-x86" ] &&
        [ -d "$RT/share/wine/gecko/wine-gecko-2.47.4-x86_64" ]; }
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  if "v$i"; then echo "PASS V$i"; else echo "FAIL V$i"; bad=1; fi
done
exit "$bad"
```

### A.12 Test programs (`scripts/cx/tests/`)
`hello.c` (syntax-checked with clang on 2026-10-20):
```c
/* scripts/cx/tests/hello.c: a non-builtin PE for T11/T12 (ntdll loads libd3dshared only for non-builtin modules) */
#include <stdio.h>

int main(void)
{
    printf("hello from %s\n", sizeof(void *) == 8 ? "x86_64" : "i386");
    return 0;
}
```
`d3d12_clear.c` and `d3d11_clear.c` are written in M0.11 from this specification. They could not be compiled at plan time, because mingw-w64 is not installed yet.
- Usage: `<program> SECONDS [WIDTH HEIGHT]` (defaults 60, 1280 720). Console subsystem; the program opens one Win32 window.
- At start it prints `adapter vendor=0x%04x device=0x%04x desc=<description>` from the `DXGI_ADAPTER_DESC1` of the adapter the device runs on. D3D12: `ID3D12Device::GetAdapterLuid`, then `IDXGIFactory4::EnumAdapterByLuid`. D3D11: `IDXGIDevice::GetAdapter`, then `IDXGIAdapter::GetDesc`.
- D3D12: `CreateDXGIFactory2` → `D3D12CreateDevice(NULL, D3D_FEATURE_LEVEL_11_0)` → a DIRECT command queue → `IDXGIFactory2::CreateSwapChainForHwnd` (2 buffers, `DXGI_FORMAT_R8G8B8A8_UNORM`, `DXGI_SWAP_EFFECT_FLIP_DISCARD`) → an RTV heap of 2 → the RTVs → allocator, list and fence. Per frame: reset; barrier PRESENT→RENDER_TARGET; `ClearRenderTargetView` with a bright colour that changes every frame (each channel between 64 and 255, so no frame can pass for black in H8); barrier back; `Close`; `ExecuteCommandLists`; `Present(1, 0)`; signal and wait on the fence.
- D3D11: `D3D11CreateDevice` (feature level 11_0) → `IDXGIFactory2::CreateSwapChainForHwnd` (2 buffers, FLIP_DISCARD) → an RTV of buffer 0. Per frame: `OMSetRenderTargets`, `ClearRenderTargetView` with the same bright, changing colour, `Present(1, 0)`.
- The window title reads `<program> frame N`, updated once per second. The message loop uses `PeekMessage`; `WM_CLOSE` ends the run early.
- At the end it prints `frames=N seconds=S` and returns 0. On any failed HRESULT it prints `FAIL <call> hr=0x%08lx` and returns 3. No shaders, no NGX, no NVAPI.
- C pitfall: mingw-w64's widl-generated headers declare struct-returning methods (`GetCPUDescriptorHandleForHeapStart`, `GetAdapterLuid`) with an extra output parameter in C. Check the form in the installed header (`find /opt/homebrew/opt/mingw-w64 -name d3d12.h | head -1`) and call the macro accordingly.
- Acceptance (M0.11): both build with the commands there, without warnings under `-Wall`, and `file` reports a PE32+ console executable.

### A.13 `scripts/cx/smoke.sh`
```bash
#!/bin/bash
# smoke.sh: T1-T14 against the disposable prefix cx_smoke (plan M4). Needs CX_LOGS (eval "$(newcycle.sh smoke)").
# Gate-style script: set -u only; every step logs with --log and every wait has a timeout. A session of its own (4.9).
set -u
export CX_PREFIX_NAME=cx_smoke
source "$(cd "$(dirname "$0")" && pwd -P)/lib.sh"
L="${CX_LOGS:?run newcycle.sh first}"; G="$L/gates.txt"; PF="$P"
begin_session smoke idle
export CX_RT="$RTR"; mkdir -p "$L"
gates_header 0 smoke > "$G"
r() { local s="$1"; shift; "$X/with-timeout.sh" "$s" "$X/cx-run.sh" --prefix cx_smoke "$@"; }
gate() { if [ "$2" = 0 ]; then echo "PASS $1" | tee -a "$G"; else echo "FAIL $1${3:+ ($3)}" | tee -a "$G"; fi; }
has() { [ "$(/usr/bin/grep -c -- "$2" "$1" 2>/dev/null || true)" -ge 1 ]; }
want="$(head -1 "$RTR/BUILDINFO" | sed 's/^b[0-9]*-//')"
[ "$("$RTR/bin/wine" --version)" = "$want" ]; gate T1 $? "expected $want"
rm -rf "$PF"
r 300 --log "$L/t2.log" -- wineboot -i && r 300 -- wineserver -w; rc=$?
[ "$rc" = 0 ] && [ "$(ls "$PF/drive_c/windows/system32" | wc -l)" -gt 500 ] && [ "$(ls "$PF/drive_c/windows/syswow64" | wc -l)" -gt 500 ]
gate T2 $? "rc=$rc"
printf 'disable\n' > "$PF/.update-timestamp"; head -1 "$RTR/BUILDINFO" > "$PF/.m5runner-runtime"      # plan 2.4
r 60 --log "$L/t10.log" -- reg add 'HKCU\Software\Wine\WineDbg' /v ShowCrashDialog /t REG_DWORD /d 0 /f > /dev/null
"$X/prefix-check.sh" cx_smoke > "$L/t3.txt"; gate T3 $?
r 120 --log "$L/t4.log" -- cmd /c 'ver & echo %USERNAME% %PROCESSOR_ARCHITECTURE%'; has "$L/t4.log" 'crossover AMD64'; gate T4 $?
r 120 --debug err+all,+process --log "$L/t5.log" -- 'C:\windows\syswow64\cmd.exe' /c 'echo %PROCESSOR_ARCHITECTURE%'
has "$L/t5.log" 'x86' && ! has "$L/t5.log" 'start.exe'; gate T5 $? "expect x86 and no start.exe relaunch"
cat > "$PF/drive_c/https.js" <<'JS'
var r = new ActiveXObject("WinHttp.WinHttpRequest.5.1");
r.Open("GET", "https://client-update.steamstatic.com/steam_client_win64", false); r.Send();
WScript.Echo("HTTP " + r.Status);
JS
r 120 --debug err+all,warn+secur32,warn+bcrypt --log "$L/t6.log" -- cscript 'C:\https.js'; has "$L/t6.log" 'HTTP 200'; gate T6 $?
r 30 --log "$L/t7.log" -- notepad & sleep 8
np=""; for p in $(session_pids); do case "$(ps -o args= -p "$p" 2>/dev/null)" in *notepad*) np=$p ;; esac; done
[ -n "$np" ] && [ -n "$(server_pid)" ]; t13=$?                        # T13 is printed below, in order
"$X/capture.sh" "$L/notepad.png"; rc=$?
case "$rc" in 0) gate T7 0 ;; 4) echo "INCONCLUSIVE T7 (screen locked)" | tee -a "$G" ;; *) gate T7 1 "no window" ;; esac
r 30 -- wineserver -k
ls "$L"/*.log > /dev/null && [ -z "$(/usr/bin/grep -l 'cannot find the FreeType font library' "$L"/*.log)" ]; gate T8 $?
r 30 -- wineserver -k
r 30 --msync 1 --log "$L/t9a.log" -- wineserver --persistent=60
rc=0; r 60 --msync 0 --debug err+all --log "$L/t9b.log" -- cmd /c exit || rc=$?
[ "$rc" -eq 1 ] && has "$L/t9b.log" 'Server is running with WINEMSYNC but this process is not' && ! has "$L/t9a.log" 'msync: error'
gate T9 $? "rc=$rc (needs err+all: the mismatch is an ERR, msync.c:587-600)"
r 30 --msync 1 -- wineserver -k
r 60 --log "$L/t10q.log" -- reg query 'HKCU\Software\Wine\WineDbg' /v ShowCrashDialog; has "$L/t10q.log" '0x0'; gate T10 $?
mkdir -p "$PF/drive_c/tests"; cp "$CXB/tests/bin/hello64.exe" "$PF/drive_c/tests/"
r 60 --debug err+all,+module --log "$L/t11.log" -- 'C:\tests\hello64.exe'
has "$L/t11.log" 'hello from x86_64' && has "$L/t11.log" 'Loaded libd3dshared.dylib, does support non-native code regions'
gate T11 $? "native exe must load libd3dshared"
r 60 --no-d3dshared --debug err+all,+module --log "$L/t12.log" -- 'C:\tests\hello64.exe'
has "$L/t12.log" 'hello from x86_64' && ! has "$L/t12.log" 'Loaded libd3dshared'; gate T12 $? "A/B baseline for D6"
gate T13 "$t13" "ps -E must show WINEPREFIX of Wine processes; else CX_SESSION_FILTER=0 in local.env (A.9)"
r 30 -- wineserver -k
"$X/stage-dlss-copies.sh" cx_smoke > "$L/t14.txt" 2>&1; gate T14 $? "stage-dlss-copies.sh, then prefix-check.sh (marker contract)"
! has "$G" '^FAIL'
```

### A.14 Small helpers
`scripts/cx/prefix-check.sh`:
```bash
#!/bin/bash
# prefix-check.sh [PREFIX_NAME]: the M5.2 invariants. system32 holds the runtime's own d3d copies and the three Wine
# placeholders, or, after stage-dlss-copies.sh, Apple's nvngx/nvapi64 copies; the marker .cx-dlss-copies holds the
# realpath of <gptk>/wine. Exit 1 on any FAIL.
set -u
P="$HOME/Games/prefixes/${1:-cx_prefix}"; S32="$P/drive_c/windows/system32"
RT="$(cd "${CX_RT:-$HOME/Games/sdk/wine-cx26}" && pwd -P)"; bad=0
for d in d3d10 d3d11 d3d12 d3d12core dxgi; do
  if cmp -s "$S32/$d.dll" "$RT/lib/wine/x86_64-windows/$d.dll"; then echo "PASS $d: Wine copy"
  else echo "FAIL $d: not the runtime's copy"; bad=1; fi
done
for d in nvapi64 nvngx atidxx64; do
  if [ -e "$P/.cx-dlss-copies" ] && [ "$d" != atidxx64 ]; then
    if cmp -s "$S32/$d.dll" "$(cat "$P/.cx-dlss-copies")/x86_64-windows/$d.dll"; then echo "PASS $d: Apple copy (DLSS route)"
    else echo "FAIL $d: DLSS copy missing or changed (run stage-dlss-copies.sh)"; bad=1; fi
    continue
  fi
  tag="$(dd if="$S32/$d.dll" bs=1 skip=64 count=20 2>/dev/null)"
  if [ "$tag" = "Wine placeholder DLL" ]; then echo "PASS $d: placeholder"; else echo "FAIL $d: '$tag'"; bad=1; fi
done
exit "$bad"
```

`scripts/cx/stage-dlss-copies.sh` (M8.3 step 1; T14):
```bash
#!/bin/bash
# stage-dlss-copies.sh [PREFIX_NAME]: Apple's documented DLSS route (plan M8.3 step 1). Copies nvngx.dll and nvapi64.dll
# from the GPTK tree into the prefix's system32 and writes the marker .cx-dlss-copies = the realpath of <gptk>/wine.
# prefix-check.sh compares with "<marker>/x86_64-windows/<dll>"; promote re-runs this script after its wineboot -u.
set -euo pipefail
PN="${1:-cx_prefix}"; P="$HOME/Games/prefixes/$PN"; S32="$P/drive_c/windows/system32"
[ -d "$S32" ] || { echo "no prefix $P" >&2; exit 1; }
G="$(cd "$HOME/Games/sdk/gptk/${CX_GPTK:-4.0b3}/wine" && pwd -P)"
for d in nvngx nvapi64; do cp -p "$G/x86_64-windows/$d.dll" "$S32/$d.dll"; done
printf '%s\n' "$G" > "$P/.cx-dlss-copies"
"$(cd "$(dirname "$0")" && pwd -P)/prefix-check.sh" "$PN"
```
The marker holds the realpath of `<gptk>/wine`, and `prefix-check.sh` appends `/x86_64-windows/<dll>` to it; both sides now say so in their headers (R1-4, R1-14). Tested on 2026-10-20 in a scratch HOME: before the copies `prefix-check.sh` printed 8 PASS lines with three placeholders, and after them 8 PASS lines with "Apple copy (DLSS route)" for nvapi64 and nvngx.

`scripts/cx/copy-steam-login.sh` (rung L6; R1-19):
```bash
#!/bin/bash
# copy-steam-login.sh SRC_PREFIX_DIR: rung L6 (plan M6). Copy the Steam login state of a prefix where Daniel signed in
# (the reference runtime's cx_ref_prefix, or a CrossOver trial bottle) into cx_prefix: config.vdf, loginusers.vdf,
# local.vdf, HKLM MachineGuid and HKCU\Software\Valve\Steam AutoLoginUser and RememberPassword. The values are read from
# the source's .reg text files (nothing runs in the source) and are never printed. Daniel quits Steam there first.
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd -P)/lib.sh"
SP="${1:?usage: copy-steam-login.sh SRC_PREFIX_DIR}"; S="drive_c/Program Files (x86)/Steam"; U="drive_c/users/crossover"
{ [ -f "$SP/user.reg" ] && [ -f "$SP/system.reg" ]; } || { echo "no user.reg/system.reg in $SP" >&2; exit 1; }
[ -d "$SP/$U" ] || { echo "the source's Windows user is not 'crossover', so DPAPI-protected tokens cannot match (M6.0 step 1)" >&2; exit 1; }
"$X/steam.sh" stop
begin_session steam-login idle
"$X/backup-userdata.sh" cx_prefix > /dev/null
mkdir -p "$P/$S/config" "$P/$U/AppData/Local/Steam"
cp -p "$SP/$S/config/config.vdf" "$SP/$S/config/loginusers.vdf" "$P/$S/config/"
cp -p "$SP/$U/AppData/Local/Steam/local.vdf" "$P/$U/AppData/Local/Steam/"
g="$(regval "$SP/system.reg" 'Software\\Microsoft\\Cryptography' MachineGuid)"
a="$(regval "$SP/user.reg" 'Software\\Valve\\Steam' AutoLoginUser)"
m="$(regval "$SP/user.reg" 'Software\\Valve\\Steam' RememberPassword)"
r() { "$X/with-timeout.sh" 120 "$X/cx-run.sh" -- reg add "$@" /f > /dev/null; }    # set -e: a timeout (142) ends the script
if [ -n "$g" ]; then r 'HKLM\SOFTWARE\Microsoft\Cryptography' /v MachineGuid /t REG_SZ /d "${g//\"/}"; fi
if [ -n "$a" ]; then r 'HKCU\Software\Valve\Steam' /v AutoLoginUser /t REG_SZ /d "${a//\"/}"; fi
case "$m" in dword:*) r 'HKCU\Software\Valve\Steam' /v RememberPassword /t REG_DWORD /d "0x${m#dword:}" ;; esac
"$X/with-timeout.sh" 300 "$X/cx-run.sh" -- wineserver -w
st() { if [ -n "$1" ]; then echo set; else echo MISSING; fi; }      # prints only whether a value exists
echo "copied 3 vdf files; MachineGuid $(st "$g"), AutoLoginUser $(st "$a"), RememberPassword $(st "$m")"
```
It reads the three registry values from the source prefix's `user.reg` and `system.reg` text with `regval` (A.9) rather than with `reg query`, because a CrossOver trial bottle cannot be queried with our runtime and a text read starts nothing in the source. It writes them with `reg add`, whose DWORD parser takes `0x` hex (`wine/programs/reg/add.c:60`). No value reaches the terminal or a log; the last line says only which values were found. Every Wine call runs under `with-timeout.sh` (R3-12). Tested in round 4 against a fake source prefix with stub `wine` and `steam.sh`: the three files and three `reg add` calls arrived, nothing was printed, and a failing `reg add` stopped it and released the lock.

`scripts/cx/with-timeout.sh`:
```bash
#!/bin/bash
# with-timeout.sh SECONDS CMD [ARGS...]: run CMD and kill it with SIGALRM after SECONDS (exit 142 on timeout).
# macOS has no timeout(1); the alarm survives exec.
exec /usr/bin/perl -e 'alarm shift; exec @ARGV or die "exec failed: $!\n"' "$@"
```
Tested on this Mac: a 1-second alarm on `sleep 3` exits 142, and a 3-second alarm on `sleep 1` exits 0.

`scripts/cx/redact.sh`:
```bash
#!/bin/bash
# redact.sh [FILE...]: print FILE (or stdin) with account data replaced. Every excerpt quoted in a tracked
# file (BUILD_LOG, PR text, docs) goes through this first. Over-redaction is acceptable; under-redaction is not.
exec /usr/bin/perl -pe '
  s/7656119\d{10}/<STEAMID64>/g;
  s/\[U:1:\d+\]/[U:1:<ACCOUNT>]/g;
  s/("(?:AccountName|PersonaName)"\s+")[^"]*(")/$1<REDACTED>$2/gi;
  s{/Users/[^/\s"]+}{/Users/<name>}g;
  s/\b(?:\d{1,3}\.){3}\d{1,3}\b/<IPV4>/g;
  s/\b(?:[0-9A-Fa-f]{1,4}:){3,7}[0-9A-Fa-f]{1,4}\b/<IPV6>/g;
  s/\b[0-9A-Fa-f:]*::[0-9A-Fa-f:]+\b/<IPV6>/g;
  s/\b[A-Z0-9]{5}\b/<CODE>/g if /guard|auth.?code|two.?factor/i;
' "$@"
```
Tested on sample text: it replaces SteamID64s, `[U:1:…]` ids, AccountName and PersonaName values, IPv4 and IPv6 addresses, `/Users/<name>` paths and Steam Guard codes, and it leaves times such as `12:05:33` and version numbers such as `26.3.0` alone.

`scripts/cx/backup-userdata.sh`:
```bash
#!/bin/bash
# backup-userdata.sh [PREFIX_NAME]            copy saves and Steam login state to ~/Games/backups/cx/<UTC>/ (keeps 10)
# backup-userdata.sh --restore [DIR] [PREFIX]  put back saves, Steam config, local.vdf and Steam's auto-login registry
#                                              values AutoLoginUser and RememberPassword (default DIR: newest)
# Local only: these files hold account data and are never copied into the repo; registry values are never printed.
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd -P)/lib.sh"
BK="$HOME/Games/backups/cx"
if [ "${1:-}" = --restore ]; then
  SRCB="${2:-}"; [ -n "$SRCB" ] || SRCB="$(find "$BK" -maxdepth 1 -type d -name '2*Z' | sort | tail -1)"
  PN="${3:-cx_prefix}"; P="$HOME/Games/prefixes/$PN"
  { [ -n "$SRCB" ] && [ -d "$SRCB" ]; } || { echo "no backup to restore" >&2; exit 1; }
  U="$P/drive_c/users/crossover"; S="$P/drive_c/Program Files (x86)/Steam"
  if [ -d "$SRCB/saves/EldenRing" ]; then mkdir -p "$U/AppData/Roaming"; ditto "$SRCB/saves/EldenRing" "$U/AppData/Roaming/EldenRing"; fi
  if [ -f "$SRCB/steam-local/local.vdf" ]; then mkdir -p "$U/AppData/Local/Steam"; ditto "$SRCB/steam-local/local.vdf" "$U/AppData/Local/Steam/local.vdf"; fi
  if [ -d "$SRCB/steam/config" ]; then ditto "$SRCB/steam/config" "$S/config"; fi
  if [ -f "$SRCB/reg/user.reg" ]; then             # Windows Steam keeps its auto-login choice in the registry (R1-19)
    a="$(regval "$SRCB/reg/user.reg" 'Software\\Valve\\Steam' AutoLoginUser)"
    m="$(regval "$SRCB/reg/user.reg" 'Software\\Valve\\Steam' RememberPassword)"
    r() { "$X/with-timeout.sh" 120 "$X/cx-run.sh" --prefix "$PN" -- reg add 'HKCU\Software\Valve\Steam' "$@" /f > /dev/null; }
    if [ -n "$a" ]; then r /v AutoLoginUser /t REG_SZ /d "${a//\"/}"; fi       # set -e: a timeout (142) ends the script
    case "$m" in dword:*) r /v RememberPassword /t REG_DWORD /d "0x${m#dword:}" ;; esac
    "$X/with-timeout.sh" 300 "$X/cx-run.sh" --prefix "$PN" -- wineserver -w
  fi
  echo "restored from $SRCB into $P"; exit 0
fi
P="$HOME/Games/prefixes/${1:-cx_prefix}"; [ -d "$P/drive_c" ] || { echo "no prefix $P" >&2; exit 1; }
B="$BK/$(date -u +%Y%m%dT%H%M%SZ)"; mkdir -p "$B"
U="$P/drive_c/users/crossover"; S="$P/drive_c/Program Files (x86)/Steam"
copy() { if [ -e "$1" ]; then mkdir -p "$B/$2"; ditto "$1" "$B/$2/$(basename "$1")"; fi; }
copy "$U/AppData/Roaming/EldenRing" saves
copy "$U/AppData/Local/Steam/local.vdf" steam-local
copy "$S/config" steam
copy "$S/userdata" steam
copy "$P/user.reg" reg
copy "$P/system.reg" reg
old=$(find "$BK" -maxdepth 1 -type d -name '2*Z' | sort)
n=$(printf '%s\n' "$old" | /usr/bin/grep -c . || true)
if [ "$n" -gt 10 ]; then          # macOS head rejects -n 0, so only prune when there is something to prune
  printf '%s\n' "$old" | head -n $((n - 10)) | while read -r o; do rm -rf "$o"; done
fi
echo "$B"
```
`scripts/cx/newcycle.sh`:
```bash
#!/bin/bash
# newcycle.sh SLUG: take the next free cycle id from BUILD_LOG, create its evidence dir, append an entry stub,
# and print the exports for the cycle. Use: eval "$(scripts/cx/newcycle.sh steam-l1)"
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd -P)/env.sh"
LOGMD="$REPO/docs/cx/BUILD_LOG.md"; slug="${1:?usage: newcycle.sh SLUG}"
last=$( { /usr/bin/grep -oE '^## C[0-9]{3}' "$LOGMD" || true; } | sed 's/^## C//' | sort -n | tail -1)
id=$(printf 'C%03d' $((10#${last:-0} + 1)))
D="$CX_LOG_ROOT/$id-$slug"; mkdir -p "$D"
printf '\n## %s %s %s\n- Build: \n- Hypothesis: \n- Change: \n- Command: \n- Result: \n- Evidence: ~/Games/logs/cx/%s-%s/\n- Decision: \n' \
  "$id" "$(date '+%Y-%m-%d %H:%M')" "$slug" "$id" "$slug" >> "$LOGMD"
echo "export CX_LOGS='$D' CX_CYCLE=$id"
```

---

## Appendix B. Evidence index
- Source facts:
  - `wine/dlls/ntdll/unix/loader.c` 365-385 (`prepend_dll_path`), 387-406 (search order), 505-527 (alternate loader), 748 (`WINESERVER`, a fallback after `bin/wineserver`), 1297-1366 (libd3dshared; traces at 1348 and 1362), 1456 (`open_dll_file` opens the found file through `open_unix_file` with the caller's object attributes), 1505-1636 (`find_builtin_dll`; 1519 `InitializeObjectAttributes( &attr, nt_name, … )` carries the requested name; "looking for" at 1570), 1646-1690 (`load_builtin`), 2246-2259 (cxcompatdb)
  - `wine/dlls/ntdll/loader.c` 1616-1621 (`disabling no-exec because of …`), 2357-2364 (libd3dshared only for non-builtin modules)
  - `wine/dlls/ntdll/unix/unix_private.h` 600-637; `wine/dlls/ntdll/unix/thread.c` 1338, 1480-1494 (the GPT_IMPORT and msthunk pattern)
  - `wine/dlls/ntdll/unix/virtual.c` 180-182 (x86_64 hosts: fixed 4 KiB host pages), 851-853 (`failed to load %s: %s`, the unix-library dlopen failure with dyld's reason), 870 (`load_builtin_unixlib`, no trace of the resolved path), 2726-2734 (`map_pe_header` mmaps the header from the file), 3026 and 3044 (`map_image_into_view` prints "mapping PE file" with the NT name it was given), 3156 (the "mapping … section" trace, same name), 3530 (`load_builtin` called with the requested system32 name), 3788-3811 (`get_mapping_info`, `virtual_map_builtin_module` hands the server's name to `virtual_map_image` at 3810)
  - `wine/server/file.c` 269 and `wine/server/fd.c` 1997 (the server keeps the client-supplied NT name of an opened file), `wine/server/mapping.c` 1578 (`get_mapping_info` returns that name), `wine/server/request_trace.h` 621-630 (`+server` prints the unix `filename=` of each `create_file`), `wine/server/main.c` 48 (an idle server lingers 3 s), 86-91 (`-k` exits with `!ret`) and 101-103 (`-w` always exits 0), `wine/server/request.c` 718-761 (`kill_lock_owner` returns 0 without a server directory or a held lock), `wine/programs/reg/delete.c` 62 and 121 (`reg delete` exits 1 for an absent key or value; R3-7, R3-16)
  - `wine/dlls/winemac.drv/d3dmetal.c` 35, 100-122, 397; `wine/dlls/winemac.drv/opengl.c` 1468-1472
  - `wine/dlls/win32u/d3dkmt.c` 715-731
  - `wine/loader/wine.inf.in` 739-742, 799 and 865 (`11,,*`: wineboot copies every builtin into system32)
  - `wine/dlls/setupapi/fakedll.c` 1081-1087, 1122; `wine/dlls/setupapi/install.c` 1151-1152, 1296-1297
  - `wine/dlls/ntdll/unix/env.c` 1043-1049, 1543-1600 (`run_wineboot`), 1886-1908, 332-358 (`is_special_env_var`, `is_ignored_env_var`: `WINEPREFIX` is passed on)
  - `wine/programs/wineboot/wineboot.c` 121-160 (equality test at 138, `disable` at 137), 1713
  - `wine/tools/install.c` 38, 151-163, 323 (timestamps never preserved)
  - `wine/dlls/kernelbase/debug.c` 42 (channel seh), 182-190 (`OutputDebugStringA` → WARN), 650 (`STARTF_USESHOWWINDOW` only)
  - `wine/programs/winedbg/intvar.h` 41; `wine/programs/winetest/main.c` 425-437 (ShowCrashDialog)
  - `wine/dlls/winebus.sys/main.c` 498, 1200-1213 (bus options: `Enable SDL`, `DisableHidraw`, `DisableInput`, `Map Controllers`), 1725
  - `wine/dlls/ntdll/unix/process.c` 333-338 (the alternate loader only with `CX_ALT_LOADER_SOCKET`), 866-937 (`spawn_process`: double fork, `setsid` in some cases, exec of the loader with the inherited environment)
  - `wine/server/process.c` 647-676 (`alloc_ptid`: process ids handed out in order from a fresh table, D20)
  - `wine/programs/reg/add.c` 60 (`0x` selects hex for DWORD data)
  - `wine/dlls/winmm/waveform.c` 432-496, 1124-1139
  - `wine/dlls/ntdll/unix/msync.c` 417-425, 587-600 ("Server is running with WINEMSYNC but this process is not" at 600), 636 ("Failed bootstrap_look_up": a client with msync on a server without it)
  - `wine/dlls/ntdll/unix/server.c` 1615-1620
  - `wine/configure.ac` 240-256, 945-959, 1250-1257, 3773-3780, 3789; `wine/aclocal.m4` 61-87, 325, 347-353
  - `wine/tools/makedep.c` 4130-4135, 4797-4807
  - `wine/tools/winegcc/winegcc.c` 399-441
  - `wine/dlls/wined3d/directx.c` 3531; `wine/dlls/wined3d/wined3d_main.c` 328-348, 465-480
- CrossOver 26.3.0 trial (plain-text files only): `research/d3dmetal-integration/cx_text/.../CrossOver-Hosted Application/wine` 653-738; bottle templates `CXBT_win10_64.pm` 448-466. The `cxcompatdb.so` notes are inferences from the research's symbol listing (2.2).
- Recipes and patch sources:
  - `research/build-recipes/drustburn-steamplay-mac/scripts/{build-deps.sh,build-wine.sh}` (snapshot `e350a87`)
  - `research/build-recipes/frankea-winecx-gptk-cx26-lane/{README.md,.github/workflows/build.yml,patches/}` (frankea/winecx-gptk snapshot `d20cb7f`)
  - `research/build-recipes/highball-engine/{inputs.json,.github/workflows/build.yml,patches/README.md,NOTICE.md}` (snapshot `fc628ae`)
  - `research/build-recipes/athei-wine-build-cx-26.3.0-9/compatdb/src/builtin.rs` (athei/wine-build snapshot `218222f`); `research/build-recipes/athei-wine-patches/` (athei/wine branch `cx-26-patched`, commits df416a601ed8, 49817a1b104d, b41ea309af8d, 2bfc0a54ffb7, e8fd146944f8)
  - athei's reference release: `gh api repos/athei/wine-build/releases/tags/cx-26.3.0-9` (asset `wine-cx-26.3.0-9-macos-x86_64.tar.xz`, 235,425,012 B, sha256 `af368205…bff1e9`)
- Steam: `research/steam-compat/highball/{steam.json,elden-ring.json,x64-crossover26.3-r26.json}`; logs in `~/Games/logs/` and `gptk_prefix/drive_c/Program Files (x86)/Steam/logs/`; the `ActiveProcess` values in `gptk_prefix` user.reg.
- DLSS sample (`research/metalfx/dlss-demo-zip/`): `DLSS_Sample_App/ngx_dlss_demo/DemoMain.cpp` 1260, 1291, 1311-1314; `NGXWrapper.cpp` 500-578; `donut/src/core/log.cpp` 46-54.
- Elden Ring PE headers (read-only scan, completeness review): `bink2w64.dll` DllCharacteristics 0x0040, a static import of `eldenring.exe` (0x8160).
- Runner: `src/m5runner/patchers.py` 96-101 (`SEKIRO_INPUT_REG_FILE`), 111-123, 151, 161, 199, 329, 462, 468, 552; `src/m5runner/profiles.py` 43-44, 77; `src/m5runner/bootstrap.py` 194; `src/m5runner/backends.py` 77-79, 224-232; the 21 `subprocess` call sites listed in 5.2 (`proc.py`); `tests/test_runner.py` 62-73, 82-89, 193; `~/Applications/Elden Ring.app/Contents/MacOS/run.sh`; `AGENTS.md` 140, 166, 182, 184 (absolute links).
- Machine state (review C12): `defaults read /Library/Preferences/com.apple.SoftwareUpdate` (automatic installs on), `pmset -g` (sleep 1, on AC), no `timeout` or `gtimeout`, `sw_vers` 26.5.1 (25F80); Apple's `/bin/bash` 3.2.57. Round 3: `ps -o lstart= -p PID` prints a padded start time such as `Tue Oct 20 16:00:43 2026`; `sysctl -n kern.boottime` prints `{ sec = …, usec = … } <date>`; `$(getconf DARWIN_USER_CACHE_DIR)d3dm/` already holds `steam.exe/` and `steamwebhelper.exe/` from GPTK 7.7 runs; the GPTK 4.0b3 `d3d12.dll` (196,608 B) and `dxgi.dll` (135,168 B) are Wine builtin PEs.
- Toolchain probes: `research/toolchain/probe/` (x86_64 C/ObjC/Metal/MetalFX under Rosetta; Wine loader flags with ld-1267).
- Apple docs: Metal HUD environment variables and per-frame logging (developer.apple.com/documentation/xcode/customizing-metal-performance-hud, .../monitoring-your-metal-apps-graphics-performance); the GPTK 4.0b3 Read Me inside the DMG.
- Plan scratch artifacts: `research/plan/up-c3a1bc86-winmm-hardcode-supported-formats.patch` (sha256 `e5b4196d…caac0b`, fetched with `gh api -H 'Accept: application/vnd.github.patch' repos/wine-mirror/wine/commits/c3a1bc86134bd6ae4bd781f6ae79f98122ba5e98`) and `research/plan/wine-windows.swift`.
- Round-2 verification artifacts (local only, under the session scratch directory): the verifiers' sample logs for H3 (one GPTK image plus a `lib/wine` dxgi, where the old line count gave 3) and for the winemetal pre-check (an `@rpath` and a code-signature failure, and an empty log), their RGBA test images for `is_black`, and the editor's stand-in runtimes used to exercise promote, the lock and the DLSS marker.
- Round-3 verification artifacts (local only, under the session scratch directory): sample lsof and vmmap listings for `gptk_mapped` and `winemetal_check`, run-log lines with the real system32 trace text, a stand-in cache root for `d3dm_cache_in`/`out`, and the scratch HOME in which the lock identity tests and promote were re-run with the round-3 sources.
- Round-4 verification artifacts (local only, under the session scratch directory): stand-in runtimes whose stub `wine` (with a settable `reg` exit status and delay) and `wineserver` (`-k` exits 1, as with no server) replace Wine, a stub `steam.sh`, a fake source prefix for `copy-steam-login.sh`, sample lsof rows for the X7 evidence lines, and the gates-header text check of 5.3.
- Round-5 verification artifacts (local only, under the session scratch directory): stubs that exit as Wine does (`wineserver -k` 1 without a server and `-w` 0, `wine/server/main.c:86-91, 101-103`; `reg delete` 1 for an absent value, `wine/programs/reg/delete.c:62, 121`; `reg add` and `reg query` 0), stand-in Steam and server processes run by Homebrew's bash under `exec -a`, and sketches of `steam.sh ui`, `stop` and `reset-rung` that follow A.8 (R4-1 to R4-4, R4-7).
- athei's reference bundle layout: `research/build-recipes/athei-wine-build-cx-26.3.0-9/README.md` 35-56 (`lib/wine/x86_64-unix`, `lib/external` libd3dshared by default). DXMT's `winemetal.so` (`nm -m`, `otool -L`): imports only `_NtSetEvent` from `@rpath/ntdll.so`, links `@rpath/winemac.so`.

---

## Appendix C. Review changes

Every review item was applied. Where the plan differs from a reviewer's proposed fix, the reason is given at the place of the change and repeated here. In the tables below, F and C numbers are review items (the body writes them as "review F6", Conventions).

### Round 1 (feasibility F1-F20, completeness C1-C26)

| Item | Change | Where |
|---|---|---|
| F1 | Build numbers continue from the highest existing index (`10#`); assemble refuses to overwrite | M3.3, 4.7 |
| F2 | The series loop stops at the first patch that does not apply and checks the commit count; dependency comments in `series`; install checks make's own status | M2.1, M3.2, A.7 |
| F3 | V4 checks one file per call; V11 and DEP2 drop every `otool -L` line ending in `:`. That is broader than "skip the first line": the dry run on wine-staging showed one header line per architecture in universal files | M1.2, M3.4, A.11 |
| F4 | Every smoke step logs; T8 requires logs; T9 rebuilt with `err+all` and `wineserver --persistent=60` | M4, A.13 |
| F5 | Ladder reordered: L1 athei, L2 Highball 0007+DXMT, L3 0007+wined3d, L4 wined3d in-process, L5 CPU raster; D13 corrected | M6, 2.6 |
| F6 | WineBus options moved to the HKLM service key; `Enable SDL`, a `Map Controllers` A/B, `+hid,+plugplay`; `DisableHidraw` dropped | 2.4, M7 |
| F7 | up-c3a1bc86 moved to standby with its signature, and a whole-chain backport if ever needed | 2.7, A.7 |
| F8 | Superseded by C2: `disable` plus `promote`, whose forced `wineboot -u` replaces the per-session timestamp comparison; "differs from" wording; former A8 and A9 marked verified; risk 6 rewritten | 2.4, M3.5, 6 |
| F9 | The manifest is written outside the tree and moved in | M0.10, M5.4, 5.3 |
| F10 | The F6 check runs from `~/Games/sdk` | 1.2, M9b |
| F11 | Stage code is `#!/bin/bash` files run only by the driver; `H` and `CM` are arrays; shell conventions | Conventions, M1-M3, A.10 |
| F12 | winemetal dyld pre-check before L1; fallback with `CX_BUNDLE_DXMT=1` and a cx-owned overlay | M6, M3.3 |
| F13 | SteamSetup.exe fetched in M1.1, hash recorded in BUILD_LOG | M1.1, M6.1 |
| F14 | NVIDIA signature-override A/B before F5 may read pending | M8.3 |
| F15 | H3, E3 and X1 grep the `+module` mapping lines; lsof is secondary. The regex uses `[\\/]+` between path parts, not `.`: `debugstr_us` escapes backslashes, so one wildcard character could miss. Superseded in round 3: see F15 (R2-1) | M5.3, M7.2, M8.2 |
| F16 | M6.3 step "never Install, Update or Verify"; Elden Ring tripwire baseline in M0.3, checked in F6 | M0.3, M6.3, 1.2 |
| F17 | No `strings`, `nm`, `otool` or disassembly of CodeWeavers' closed binaries; `cx_bin` never copied; 2.2 labelled "inferred from symbol names" | 2.2, 4.6, 6.1 |
| F18 | (a) M7.4, (b) "differs from", (c) V14 compares without the `bNNN-` prefix, (d) the vendor switch is an ASSUMPTION checked by X6. X6 reads our own `d3d12_clear` adapter line instead of the DLSS sample's log, because that sample's logging is not known to print the adapter ids | 2.3, 2.4, M3.4, M8.2 |
| F19 | VC++ runtimes through Microsoft's installers via `cx-run.sh`; winetricks banned in `cx_prefix` | M5 failure modes |
| F20 | The renderer tree moved to M0.10. The A/B uses a native `hello64.exe` (T11/T12) instead of T6/T7, because cmd, cscript and notepad are Wine builtins and never load libd3dshared (`wine/dlls/ntdll/loader.c:2357-2364`) | M0.10, M4 |
| C1 | Own D3D12/D3D11 test programs for M5; DLSS sample only in M8; M8.1 before its first launch; `warn+seh`, `-width 1280 -height 720`, dialog capture. X4 expects the captured Error dialog plus the log line instead of exit code 1, because the sample blocks on its MessageBox before returning | M0.11, M5.3, M8 |
| C2 | `disable`, `promote`, the `cx-run.sh` guard (exit 3) and `preflight_prefix` | 2.4, M3.5, A.2, A.9 |
| C3 | hb-0013 in standby; gate E9; A/B M7.6; `WINE_DISABLE_NX_COMPAT` scrubbed | 2.7, M7, 2.3 |
| C4 | at-0005 and at-0010 in base; at-0001 and at-0008 in standby; the at-0008/hb-0007 conflict recorded; provenance | 2.7, M0.5 |
| C5 | assemble and promote split; verify runs on the new build; session lock; dev hot swaps and rollback guarded | M3, 4.5, 4.7 |
| C6 | S-core/S-UI split; reference runtime M6.0; headless rung L6. "Skip ahead to L3/L4" is translated to F5's numbering: L3, then L5 and L6 | M6, D19 |
| C7 | Readiness from `ActiveProcess`; offline mode M6.4b (now M7.1b, R1-13). Attempt A first tries `-offlinemode`, which the current client lists, before the proposed `loginusers.vdf` keys | M6, M7, D20 |
| C8 | APFS clone instead of a symlink; idempotent EAC hook; er.sh pre-flight; M6.3 step; "Start offline"; INCONCLUSIVE | M7, 5.2 |
| C9 | Hook signature with prefix and runtime; `windows_user`; bootstrap pins runtimes; `M5RUNNER_NO_EXEC`; tests for protected prefixes, idempotence, stamp mismatch and parity | 5.2, 5.3, M9a |
| C10 | Worktree; `REPO` derived from the script location; `create-apps` after the merge, with numbered steps | M0.4, A.1, M10 |
| C11 | `backup-userdata.sh`, run before restores and promotes and after er.sh; restore after a snapshot rollback; BUILD_LOG header row | 4.7, M3.5, M7.2, A.14 |
| C12 | M0.9 settings; `caffeinate`; `--session-check`; `with-timeout.sh`; macOS build recorded | M0.9, A |
| C13 | `ShowCrashDialog=0` at prefix creation; gate T10; dialog watcher | 2.4, M4, M5.2, A.9 |
| C14 | Triage row and the m5-0001 wrapper-patch recipe | M5, 4.4 |
| C15 | Redaction rule, `redact.sh`, hygiene regexes; the AGENTS.md links fixed with the test | Conventions, 4.2, 5.3, M9a |
| C16 | Update-run snapshot; L0 on the second start; `reset-rung`; `appdefaults-start.txt` | M6.2, M6, A.8 |
| C17 | Manifest fix; manifest pre-flight; F4b size and inode; F4c HUD label | M0.10, A.6, A.9, 1.2 |
| C18 | nvapi alias in an overlay; `stage-dlss-copies.sh` re-run by promote; Wukong app id; NVAPI wording | M8, A.2, A.8 |
| C19 | Renderer tree before M4; `cx-run.sh` exits 2 without it. T11 uses `hello64.exe`, not notepad, for the reason given under F20 | M0.10, M4, A.2 |
| C20 | Prefix-based scrub; `CX_LEAK_PREFIXES`; leak test. The `WINESERVER` risk is described as source shows it: a fallback after the runtime's own `bin/wineserver` (`loader.c:748`) | 2.3, A.2, 5.2, 5.3 |
| C21 | Shell conventions; explicit dry runs; `/bin/bash -n` in the hygiene test | Conventions, M0.3, 5.3 |
| C22 | `newcycle.sh`; gates.txt header; dirty-tree refusal; dSYMs; pin right after S6; Resume checklist | 4.1, 4.8, M3, M6.4 |
| C23 | Dependency graph; Daniel queue; one combined first request; the M7.4 scene; response time in section 7 | 1.3, M0.12, 4.2, 7 |
| C24 | First-frame polling; one shader cache per GPTK version; A/B hygiene | M7.2, M7.4, M7.5 |
| C25 | hb-0005, hb-0025, hb-0018 and hb-0020 in standby with signatures, in the verified order | 2.7, A.7 |
| C26 | nvapi overrides for four Steam executables; gate S9 | 2.4, M6.1, M6 |

### Round 2 (verification of round 1)

Every item was applied. Where the plan differs from the verifier's proposed fix, the reason is given at the place of the change and repeated here.

| Item | Change | Where |
|---|---|---|
| F15 | H3 and E3 count distinct DLL names on the once-per-image "mapping PE file" line (`gptk_mapped`) and pass only at 2; X1 needs at least 1 for nvngx.dll; H10 counts d3d11 and dxgi. Tested on the verifier's mixed log (1) and on logs in both path styles (2) Superseded in round 3: see F15 (R2-1) | M5.3, M7.2, M8.2, A.9, 1.2 |
| C13 | Every poll loop checks the FAIL-dialog marker and ends its run (collect, `wineserver -k`, FAIL-dialog): `wait_or_dialog` in M5.3 and the M8 blocks, `steam.sh ui` and `silent`, er.sh's first-frame and probe waits. Titles match case-insensitively (`*error*`, `*fatal*`, `wine`, `*crash*`), a superset of the proposed list that also catches "ERROR"; only the session's own PIDs are watched. Modified: an interactive Steam window that is already up for Daniel is not ended by the agent; `gates` and `stop` report its dialogs | A.9, A.8, M5.3, M7.2, M8 |
| R1-3 | Sessions never overlap: the lock, `begin_session`, and the `cx-run.sh` guard (exit 5 on a `wineserver -k` that would end another session). The DLSS work moved to its own promoted prefix `cx_dlss`, and capture takes `--pid`. Both of the proposed alternatives are applied, not one | 1.3, 4.9, M8, A.2, A.3 |
| R1-4 | The marker holds the realpath of `<gptk>/wine` in both scripts; `stage-dlss-copies.sh` is now full source and ends with `prefix-check.sh`; gate T14 checks the contract in `cx_smoke`, and it passed in a scratch HOME | A.14, M8.3, M4 |
| R1-5 | Each promote logs into `promote-<build>-<UTC>/` | M3.5, 4.2 |
| R1-6 | `winemetal_check`: FAIL on any `failed to load "…winemetal.so"` line, PASS only with a mapped `winemetal.dll`, otherwise INCONCLUSIVE. `+loaddll` was not added: the `+module` mapping line already shows the load, and L1's debug spec has `+module`. Superseded in round 3: the mapping line names only system32, so PASS now comes from lsof; see R1-6 (R2-2) | M6 L1, A.9 |
| R1-7 | The pre-check result goes into BUILD_LOG; the fallback writes `CX_BUNDLE_DXMT=1` into `$CXB/local.env` (sourced by env.sh), so every later build bundles winemetal, and L2 runs with the cx-owned overlay; the fallback block gained `newcycle` and `reset-rung` | M6, A.1, A.8, 5.2 |
| R1-8 | `--ref` exports `CX_RT` and `CX_PREFIX_NAME=cx_ref_prefix` before sourcing lib.sh, routes every Wine call through `ref-run.sh`, takes no lock; M6.0 writes `RUNTIME_ROOT` | M6.0, A.8 |
| R1-9 | 6.1: never sign, re-sign or rewrite Apple files; read-only `codesign -v` is allowed | 6.1 |
| R1-10 | 5.2 renames the runner's controller values to "Enable SDL" and "Map Controllers" and drops "EnableHidraw"; a unit test parses the `.reg` text | 5.2, 5.3, 2.4 |
| R1-11 | `is_black` rewritten: `od -v`, the BMP header read, alpha skipped, mean below 8, optional HUD mask; regression cases in `tests/test_cx_harness.py`; er.sh takes `t_first_frame` from the first non-black masked capture and polls E6 until the limit | A.9, M7.2, M5.3 H8, 5.3, A.12 |
| R1-12 | As R1-3. Modified: the session scope is the prefix (`WINEPREFIX` in each process's environment), not the descendants of the first process, because Wine double-forks its children and sometimes calls `setsid` (`process.c:866-937`); gate T13 checks it | 4.9, A.9, M4 |
| R1-13 | M6.4b moved after M7.1 as M7.1b | M6, M7 |
| R1-14 | As R1-4, plus promote's rollback: a failure after the switch relinks the previous build and restores the pre-promote snapshots of `cx_prefix` and `cx_dlss` (tested with stand-in runtimes) | M3.5 |
| R1-15 | `steam.sh install`, `ui`, `silent`, `stop` and `reset-rung` check the lock; `stop` removes only a `steam-ui` lock; er.sh keeps its lock through its internal stop and silent; promote and the 4.7 rollback take the lock. Modified: only `ui` takes a Steam lock (owner `steam-ui`); `silent` takes none, because a headless Steam holds no unsaved state and inside er.sh the er lock covers it | A.8, 4.9, 4.7, M3.5, 4.1 |
| R1-16 | `caffeinate -w <wineserver pid>` for Steam; the watcher's PID is in the lock and is killed by `release_session` and `stop`; the watcher also exits when its anchor dies; Steam and its helpers start through `detach` | A.8, A.9, 4.9, M0.9 |
| R1-17 | As R1-8, plus: M6.0 starts after M1.1; lib.sh tolerates a missing `wine-cx26` link | M6.0, 1.3, A.9 |
| R1-18 | One route per kind of change: a new source change is committed in `$SRC` and built with `iter`, then exported per 4.1 step 7; a series edit uses `from src` | M5 failure table, 4.5 |
| R1-19 | `copy-steam-login.sh` (L6) and `backup-userdata.sh --restore` carry `AutoLoginUser` and `RememberPassword` (and L6 the MachineGuid) without printing them; the ladder restore is the 4.7 rollback, which backs up first; ASSUMPTION settled by S7. Modified: the values are read from the source's `.reg` text, not with `reg query`, because a CrossOver bottle cannot be queried with our runtime | M6 ladder, A.14, 4.7 |
| R1-20 | Machine health: record the state and ask Daniel to reboot when convenient (numbered steps); never reboot unattended | 4.6, executive summary |
| R1-21 | M10 switches the stable checkout to the branch the cx PR was merged into, checks that the cx files are there, then runs `create-apps` | M10 |
| R1-22 | M9a split into code and unit tests (any time) and runner acceptance (after M7), with the edge in 1.3; `proc.py` routes all 21 subprocess call sites, `M5RUNNER_NO_EXEC=1` stubs them, and conftest makes a direct `subprocess` call fail | M9, 1.3, 5.2, 5.3 |
| R1-23 | Modified: `steam.sh` resets `ActiveUser` and `pid` to 0 before each start, and S7 needs both non-zero again plus, online, a `[Logged On,` line after the start offset. Comparing `pid` with its pre-start value was rejected because a fresh wineserver hands out ids in the same order (`server/process.c:647-676`), so a healthy restart can reuse the old id | D20, M6 S7, A.8, 5.2 |
| R1-24 | Numbered Daniel steps for the benchmark install (the agent opens `steam://install/3132990`), the headless-only route (install where L6 signed in, then clone), the conditional L6 sign-in and the written "headless only" OK, in the executive summary and the Daniel queue | M8.4 (formerly M8.3 step 3), M6 ladder, executive summary, 4.2 |

### Round 3 (verification of round 2)

The items keep the verifier's ids. The first three re-open earlier items and are R2-1 to R2-3 by position. Every item was applied. Where the plan differs from the proposed fix, the reason is given at the place of the change and repeated here.

| Item | Change | Where |
|---|---|---|
| F15 (R2-1) | H3, E3, X1 and X7 read the probe's lsof and vmmap listings through `gptk_mapped`, which accepts only absolute listing paths, so a run log never counts. The `+module` "mapping PE file" trace is no longer evidence: it names the requested system32 file, because `find_builtin_dll` opens the GPTK file with the requested name and the server keeps and returns that name (`loader.c:1519, 1456`; `server/fd.c:1997`; `server/mapping.c:1578`; `virtual.c:3810, 3044`). The H3 triage row, F4 in 1.2, 4.4 step 3.2 and M8.3 step 1 were rewritten; the tests use the real trace text; `+server` is named as the trace-based alternative. Tested on sample listings | M5.3, M7.2, M8.2-M8.4, A.9, 1.2, 4.4, 5.3, B |
| R1-6 (R2-2) | `winemetal_check STEAMLOG LSOFDIR`: PASS needs no `failed to load "…winemetal.so"` line plus `…/x86_64-unix/winemetal.so` in the lsof of a running steam.exe or steamwebhelper.exe of the session (new `steam_lsof`); the INCONCLUSIVE advice now checks lsof for DXMT's d3d11/dxgi. The output reads "winemetal pre-check" (R2-19) | M6 L1 and fallback, A.9, 5.3 |
| R1-18 (R2-3) | The M7 failure row says: enable the set in `series`, then `build-wine-cx.sh from src`; 4.4 step 1 names both routes (a committed source fix, then `iter`; a vendored patch, then `from src`) | M7, 4.4 |
| R2-4 | Every Wine call of `steam.sh` passes an explicit msync. Before a start, `ui` and `silent` end any leftover server, run the hygiene and the `ActiveProcess` resets with the coming `--msync N`, then `wineserver -w`. S8, the M7 table and 4.4 also look for "Failed bootstrap_look_up" (`msync.c:636`). Both proposed measures are applied, not one | A.8, M6 S8, M7, 4.4, 5.2 |
| R2-5 | The lock stores the anchor's start time and the watcher's; `lock_live` and `release_session` compare them, and `stop` never signals the watcher of a stale lock. Start times (`ps -o lstart=`) were chosen over command lines, because a `begin_session` block's command line is just `/bin/bash FILE` | A.9, A.2, A.8, 4.9 |
| R2-6 | conftest replaces the `subprocess` attribute of every runner module except `proc.py` with a stub module that keeps the constants and exception classes; a text test keeps every subprocess call in `proc.py` | 5.3 |
| R2-7 | Applied the second option: the rung settings (`CommandLineAppend`, the `Direct3D` renderer key, the winemetal copies) moved into `steam.sh reset-rung --append/--renderer/--winemetal`, which takes the lock itself (owner `steam-rung`); `steam.sh open URL` runs the benchmark install inside the held Steam session; the rung blocks start Wine only through `steam.sh`, and a rung command table replaces the hand-written steps. The blocks are not wrapped in `begin_session`, as the verifier warned | M6, A.8, 4.9, M8.4 |
| R2-8 | er.sh runs in phases: first frame, probes, hand-over. `--max-session` (4 h), `--duration` and `--start-on` bound the run; only a dialog of the game PID ends phases 1-2; at the hand-over the lock's anchor becomes the game (`er-daniel`) and dialogs are only recorded; "on exit" is spelled out. Modified: the M7.4 A/B scene is the title-screen backdrop, timed by `--duration 300` and measured with `hud-stats.sh --last 120`, because a scene that starts whenever Daniel is ready cannot be timed from the first frame; the Site of Grace scene stays as an option through `--start-on` | M7.2-M7.4, A.8, A.9, 4.9 |
| R2-9 | `steam.sh ui --hold` (owner `steam-daniel`) for every window handed to Daniel: `stop` refuses it without `--force`, and after the window is announced `ui` only records dialogs; `reset-rung` claims the lock; the executive summary now states exactly what is guaranteed | M6.3, M8.4, A.8, 4.9, executive summary |
| R2-10 | `lock_live`: same PID, same start time, and a lock younger than the last boot (`kern.boottime`); the same test in the `cx-run.sh` guard and in 4.8 step 2. Tested: a live PID with another start time, and an epoch before the boot, are both stale | A.9, A.2, 4.8, 4.9 |
| R2-11 | Only `d3dm/<exe>` moves (`d3dm_cache_in`/`d3dm_cache_out`); an unmarked directory is parked and put back on exit, so GPTK 7.7 always finds its own cache; an `active-<exe>` file recovers a killed run. Tested with a stand-in cache root | M7.5, M5.3, A.9, 5.3 |
| R2-12 | `build-wine-cx.sh`, `smoke.sh` and every block that calls them run as background jobs with the log tailed; 4.8 step 4 recovers from a promote killed with SIGKILL | Conventions, M1, M3, M4, M6, 4.3, 4.8 |
| R2-13 | Wukong is required: M8.4 always runs after M7 (gate X7; X8 for frame generation is recorded, not required). Install routes A (cx Steam), B (reference runtime) and C (CrossOver trial, Daniel's own steps), with an APFS clone for B and C; a launch block with the watcher, first-frame wait, hand-over and recording; Daniel's benchmark steps. F5, 1.3, M8.5, the Daniel queue, section 7 and the executive summary match | M8.4, M8.5, 1.2, 1.3, 4.2, 7, executive summary |
| R2-14 | The same defect as R2-4, reported twice; the same fix | A.8, M6 S8, M7 |
| R2-15 | 4.7 rollback: the snapshot must exist, the backup must succeed, and the old prefix is moved aside until the clone and the restore have worked; M7.1 removes the old clone before `cp -Rc` | 4.7, M7.1, M7 table |
| R2-16 | `ensure_prefix` refuses a mismatched or unstamped prefix with "run build-wine-cx.sh promote" and starts nothing; `check_placeholders` follows `prefix-check.sh`'s marker rule; the 5.3 test expects the refusal | 5.2, 5.3 |
| R2-17 | The hygiene test and the `AGENTS.md` link fix move to M0.6; before the push, `M5_HYGIENE_BASE` scans every line the branch adds, and a hit means fix, squash and scan again | M0.6, M9a, M10, 5.3, 5.5, Conventions |
| R2-18 | conftest points `M5RUNNER_GAMES_DIR` and `M5RUNNER_APPS_DIR` at a temporary directory before `m5runner` is imported; `config.CX_SESSION_LOCK` derives from `BASE_GAMES_DIR` | 5.2, 5.3, M9a |
| R2-19 | Stage gates renamed DEP1-DEP4 and CFG1-CFG4; in the body every review item carries the word "review"; the "F12 pre-check" output and "F12 fallback" became "winemetal pre-check" and "winemetal fallback"; the convention is in Conventions | throughout; Conventions |

### Round 4 (targeted verification of round 3)

The items are numbered R3-1 to R3-20; where one re-opens an earlier item, that item is named in brackets. Every item was applied. Where the plan differs from the proposed fix, the reason is given at the place of the change and repeated here.

| Item | Change | Where |
|---|---|---|
| R3-1 (review C7) | `.cx-session` holds `msync=`, `offline=` and the log offsets; `silent --offline` writes `offline=1`; `status`, `gates`, S7 and the runner's readiness drop the `[Logged On,` condition for it; er.sh restarts an offline session only with `--offline`; the gates.txt header carries `offline=`, and M7.1b records the mode in BUILD_LOG | 2.1, D20, M6 S7, M7.1b, M7.2, M8.4, A.8, A.9, 4.1, 5.2 |
| R3-2 (review C22) | `gates_header` is the first write of every gates.txt: M5.3 and M8.2 (also the per-run directories the watcher writes to), X6 (whose adapter lines now go into gates.txt), M8.3 step 1, M8.4, er.sh (before its watcher) and the `steam.sh` modes that write one. A text test in 5.3 checks every block and script; round 3's blocks fail it four times, round 4's pass | M5.3, M7.2, M8.2-M8.4, A.8, 4.1, 5.3 |
| R3-3 (R2-9) | `steam.sh --ref ui --hold` keeps the announce semantics without a lock; the L6 sign-in and M8.4 route B use it | A.8, M6 L6, M8.4, 4.3 |
| R3-4 | Before the first Wukong launch, `cx_prefix` gets the M8.1 prerequisites (the block takes `PN`) and exactly the M8.3 variables with which the sample passed: a new copies block (Apple's copies and the alias overlay, which the launch adds through `CX_PREPEND_EXTRA` whenever the copies marker exists) and the step-2 block with `PN=cx_prefix`, each in BUILD_LOG. The launch refuses without `nvngx_config.txt`. 1.3 gains the M8.2/M8.3 -> M8.4 edge | 1.3, M8 intro, M8.1, M8.3, M8.4 |
| R3-5 | When `cx_prefix` holds the copies marker, X7's lsof part accepts nvngx.dll from gptk/4.0b3 or from system32, and the "X7 evidence" line records both counts | M8.4 block, X7 |
| R3-6 | lib.sh `snap_prefix TAG` moves an existing snapshot aside to `.old-<UTC>` before `cp -Rc` (moving aside rather than refusing, so a redone step never stalls); M5.2, M6.1 and the M6.2 one-liner (used by M6.5 and 4.1) use it; `dev` is removed before it is cloned again; the 4.7 rollback refuses a snapshot that holds a nested copy | 2.1, A.9, M5.2, M6.1, M6.2, M6.5, 4.1, 4.3, 4.5, 4.7, 4.9 |
| R3-7 | `steam.sh stop` exits 0 when it stopped Steam or nothing ran, 1 only for REFUSE, and 2 when a steam.exe of the session still runs afterwards; a harness test runs it with stub binaries that exit 1 | A.8, 5.3 |
| R3-8 | M7.1 starts with `steam.sh stop` and `begin_session er-clone idle` and deletes the appmanifest before the old clone; 4.9 item 2 lists it; the M7 failure row points at it | M7.1, M7 table, 4.9 |
| R3-9 | Agent-only M7 cycles run `er.sh --duration 300` or `--probe-only`; the hand-over form runs only in the play-test slot agreed through M0.12, with a Daniel-queue row. Modified: a signalled er.sh exits at once and cannot wait for the game, so at the hand-over it starts a detached `reap_after` (new in lib.sh), which ends `d3dm-log.sh` once the game has exited, also on the INTERRUPTED path; 4.8 step 5 ends a log stream left by an er.sh killed earlier (`d3dm-log.pid`); the M8.4 block does the same at its hand-over | M7.2, M7.3, M0.12, 4.2, 4.8, A.8, A.9, M8.4, executive summary |
| R3-10 | er.sh uses `VER` for `--d3dmetal`, `probe.sh`, `gptk_mapped`, the shader cache and its own `preflight_prefix` (`CX_GPTK` set but not exported, so a Steam it restarts keeps the default tree); the header records `gptk=<ver>:<hash>`; E3 reads `$VER` | M7.2, E3, A.8, A.9, 4.1 |
| R3-11 | Runner lock rules: `launch` claims `runner-er` and nests under `CX_SESSION_PARENT`; a ready Steam in a runner-started `steam-daniel` session (`by=runner`) is used, not refused; `steam --stop` may end that session; unit tests for each case | 5.2, 5.3, 4.4, 4.8, 4.9, M9a, M10 |
| R3-12 | `with-timeout.sh` around the untimed `reg add` calls (120 s; M5.2, M6.1, M8.0, M8.1, M8.3 step 2, `backup-userdata.sh --restore`, `copy-steam-login.sh`) and their `wineserver -w` (300 s); a timeout (142) or failure ends the block or script, and the wineboot chains of M5.2 and M8.0 now end with `\|\| exit 1` | M5.2, M6.1, M8.0, M8.1, M8.3, A.14 |
| R3-13 | The M8.4 launch block starts its watcher right after `newcycle`, before the Steam check | M8.4 |
| R3-14 (R2-4) | `steam.sh ui` stops a headless Steam of its session first, inside its own session; M8.4 route A runs `steam.sh stop` first, and the runner's `ui` stops too. Stopping was chosen over refusing: a headless Steam holds no lock and no unsaved state, so an unattended flow never stalls on one | A.8, M8.4, 5.2 |
| R3-15 (review F14) | If X7 fails, the M8.3 variables `cx_prefix` lacks are applied there one per cycle, each followed by a launch and a benchmark run (a Daniel-queue row), before F5 may read pending; F5 and M8.5 name the prefix of the failing gate | M8.4, M8.5, 1.2, 4.2, 7, executive summary |
| R3-16 | As R3-7, plus `reg delete`: A.8 lists the Wine calls that run with `\|\| true` (`wineserver -k`, `reg delete` of an absent value or key) with their source lines. Modified: `reset-rung` exits 1 for REFUSE and also for a failed or timed-out write, because a lost rung setting must not pass silently. The trailing `wineserver -k` of the M8.0, M8.1, X6 and M8.3 step-2 blocks gained `\|\| true` | A.8, M8.0, M8.1, M8.3, X6, 5.3, B |
| R3-17 | As R3-4; 2.4 now says the DLSS prerequisites are not part of the M6.1 baseline and are written by the M8.1 block in `cx_dlss` and, before M8.4, in `cx_prefix` | 2.4, M8.1, M8.4 |
| R3-18 | As R3-5, and X1 accepts the system32 copy when `cx_dlss` holds the copies marker, judged with the M8.3 step-1 grep | M8.2 X1, X7 |
| R3-19 | The same defect as R3-13; the same fix | M8.4 |
| R3-20 | The hygiene test scans `git ls-files --cached --others --exclude-standard`, so a new file is checked before its first commit without staging (`.venv/` and `logs/` stay excluded by `.gitignore`) | 5.3, 5.5, M0.6, Conventions |

### Round 5 (targeted verification of round 4)

The items are numbered R4-1 to R4-7; where one re-opens an earlier item, that item is named in brackets. Every item was applied. Where the plan differs from the proposed fix, the reason is given at the place of the change and repeated here.

| Item | Change | Where |
|---|---|---|
| R4-1 (R3-14) | `stop` releases a live `steam-ui` lock, or a `steam-daniel` lock with `--force`, only when called from outside the session; a nested call (`CX_SESSION_PARENT` = the lock's pid: `ui`'s stop of a leftover headless Steam, er.sh, a block) ends Steam and the server and keeps the lock; the lock check and 4.9 item 5 say the same; `ui` releases its lock and exits 1 if that stop fails. The runner's `ui` stops a headless Steam after taking its lock and keeps it, and only an outside `steam --stop` releases a `by=runner` lock. A harness case and a runner case check it. The nested rule was chosen over stopping before the claim, because it also covers er.sh and the blocks and leaves no moment without a lock. Tested with sketches and stand-ins | A.8, 4.9, 5.1, 5.2, 5.3 |
| R4-2 (R3-7, R3-16) | The 5.3 stubs exit as Wine does: `wineserver -k` and `reg delete` 1, `wineserver -w`, `reg add` and `reg query` 0. `stop` and option-less `reset-rung` exit 0 with them, and a new case makes `reg add` exit 1, so `reset-rung --append X` exits 1. A.8 says a failed `wineserver -w` means its timeout, because `-w` itself always exits 0 (`main.c:101-103`). Tested with the stubs and a `reset-rung` sketch, including a `-w` past its timeout | 5.3, A.8, B |
| R4-3 | As R4-1, reported from the `stop` paragraph: a nested `stop` never refuses, whatever the owner, so `ui --hold` is never stopped by its own `steam-daniel` lock; the 5.3 case covers both owners | A.8, 4.9, 5.3 |
| R4-4 (R3-3) | `--ref ui` never stops a running reference Steam: it refuses with `REFUSE: a reference Steam is running; …`. M6.0 runs `steam.sh --ref stop` before its second start; the L6 sign-in and route B add "nor `steam.sh --ref ui` again", and route B retries a failed hand-off with the `ref-run.sh` line alone | A.8, M6.0, M6 L6, M8.4, 4.9 |
| R4-5 (R3-4) | The M8.2 block prepends the alias overlay whenever `cx_dlss` holds the copies marker, as the M8.4 launch does, and records the setup in gates.txt; M8.3 step 2 thus runs on top of step 1's copies and overlay, and M8.4 item 2 says so | M8.2, M8.3, M8.4 |
| R4-6 (R3-11) | M9b's real launch runs in a new cycle and a session of its own, as M9a's does, so the runner nests and takes no `runner-er` lock, and the block ends the game after its first frame (M9a's block ends it too); 4.4 step 4 and 4.8 step 2 treat a `runner-er` lock from a launch the agent ran itself as the agent's to end. Modified: the runner's `launch` gets no 4-hour bound, because outside the agent's nested checks a `runner-er` lock is Daniel's own game (Elden Ring.app after M10), which the cap would close mid-play | M9, 5.2, 4.4, 4.8 |
| R4-7 | The same defect as R4-2; the same fix | 5.3, A.8 |

### Final check (verification of round 5)

The final check confirmed R4-1 to R4-7 and found two new minor defects. No further review round was run; both were fixed by hand.

| Item | Change | Where |
|---|---|---|
| R5-1 (R4-4) | M6.0 step 2 ends with `steam.sh --ref stop` once S2-S5 are recorded, because `--ref ui` now refuses while a reference Steam runs and the L6 sign-in would otherwise refuse in Daniel's slot; L6 step 1 also stops a leftover agent-owned reference Steam first | M6.0, L6 sign-in |
| R5-2 (R4-6) | The M9b launch check writes the gates header, starts the dialog watcher, stops Steam inside its session, waits up to 300 s for the game process before `first_frame` (the runner starts Steam headless first, up to 120 s for S7), records FAIL if the game never appears, and always reaps the runner (`kill "$RP"; wait "$RP"`); it runs as a background job | M9b |
