# M3-03 independent review — minimal frontend and controls

- Handoff head reviewed: `7972b16e35bf0eb0c95b12266a6c11fb4a212617`
- Behavioral commit reviewed: `6489c644a327e4eeb54b04822b2aa92e8869c2e0`
- Behavioral diff: `759ed9e0b130819d09392b61946c27e433f44438..6489c644a327e4eeb54b04822b2aa92e8869c2e0`
- Reviewer: fresh OpenAI Codex Sol/medium session
- Worktree/branch: `.worktrees/m3-03-review`, `review/M3-03-minimal-frontend`
- Date: 13 September 2026 AEST
- Verdict: **returned with material findings; not approved**

## Findings

### 1. Unsupported poses freeze the whole displayed race, not only the rider pose

Holding a last recovered **rider pose** would be a reasonable declared M3-03
visual omission pending M3-04. That is not what this implementation does.
`sdl_main.cpp:332-361` assigns `last_supported_frame` only when the complete
headless render accepts the current pose pair. On an unsupported pair, once an
earlier frame exists, it sends that unchanged complete RGB frame to SDL. The
track, camera, rider positions and timer therefore all stop visibly while the
simulation and live controls continue advancing, then jump to a later state
when a supported pair next appears.

I independently decoded the two canonical pose indices from every state in the
accepted continuous-right full-race producer output. Of 2,147 states from
frames 1533 through 3679, only 726 have one of the five supported atlas pairs;
**1,421 states (66.185%) take the held-frame path**. The longest continuous
whole-frame freezes are:

| Frames | Updates | PAL duration |
| --- | ---: | ---: |
| 1601-1753 | 153 | 3.06 s |
| 3323-3451 | 129 | 2.58 s |
| 3214-3321 | 108 | 2.16 s |
| 1533-1599 | 67 | 1.34 s |

The analyzed producer output is SHA-256
`f28d411a4e4bb464276c71d42e509de508ec06890fbfabe70dbbf0531e8c2a95`;
its update input file is
`4ed3dbc56301009a5377116d187631bc34616bd10528663fbc07e5266a2e6298`.
The supported-pair count also reproduces each frozen M3-02 pose pair at its
declared frame, so this is not an offset guess.

This is a material M3-03 display/readability failure and would also block the
M3 playable gate. It is more severe than the frozen contract's wording about
holding an intermediate rider pose. The smallest correction is to retain the
last supported pose pair but render a presentation-only copy of the **current**
state with only those pose fields substituted, so current track/camera/HUD and
rider positions remain visible. Recovering more atlas poses is the higher-
fidelity alternative. A sustained full-race test must bound complete-frame
staleness; checking only canonical-state invariance cannot detect this defect.

### 2. A non-finite frontend timeout crashes the command and leaves its app running

`frontend/commands.py:28` rejects only values `<= 0`. IEEE NaN passes that
test and reaches `subprocess.Popen.communicate(timeout=nan)`. On the review
host, `selectors.select` raised `ValueError: cannot convert float NaN to
integer`; the stable command exited 1 with an uncaught traceback, wrote no
requested JSON report, and left the launched dummy-video frontend alive as PID
66122. I stopped that exact review-created process immediately after recording
the result.

Reproduction:

```text
SDL_VIDEODRIVER=dummy python3 tools/project.py frontend run --pack '/Users/markfeaver/Projects/Unirally Decompilation/.worktrees/m3-03-minimal-frontend/artifacts/m3-03-first-launch.pack' --preset app-debug --hidden --timeout nan --report artifacts/m3-03-review/timeout-nan-orphan.json --task M3-03
pgrep -fl '/m3-03-review/build/app-debug/src/app/unirally'
```

The command must reject non-finite timeouts as invalid input before spawning,
write the failed report, and leave no child. Use `math.isfinite(args.timeout)`
in the frontend command and add an exact regression; defensively rejecting
non-finite values in the shared bounded-process helper would protect future
callers as well. Positive infinity must not become an unbounded launch.

### 3. The SDL present failure result is discarded

The pinned SDL 3.4.10 header declares `SDL_RenderPresent` as a `bool` that is
false on failure. `sdl_main.cpp:240` calls it without checking the result,
although every preceding renderer operation is checked. A backend present
failure can therefore be followed by a normal zero exit (especially under a
bounded `--updates` smoke), contradicting the frozen rule that renderer
failures are unsuccessful launches and the README's same claim.

Check the return and throw `sdl_error`, as is already done for clear, texture
update and texture render. A narrow wrapper/injected failure seam would make
this outcome testable without relying on a backend to fail naturally.

### 4. Hosted CI never compiles the app target or SDL on either platform

Hosted run `34697744435` is green at exact handoff head `7972b16`, on macOS 15
and Ubuntu 24.04. Its job steps build/test only `lab-debug` and, on Linux,
`lab-sanitize`. `LAB_BUILD_APP` defaults off, so those presets compile the pure
frontend library/test but not `sdl_main.cpp`, not the SDL dependency, and not
the desktop executable. This leaves the task's required Linux SDL compilation
and the declared hosted app-debug/app-sanitize evidence absent. A green
headless workflow is not evidence for this acceptance criterion.

The smallest correction is to make the existing matrix build/test
`app-debug` on both hosts and `app-sanitize` in the Linux sanitizer step (these
presets retain the same headless tests), optionally executing the app's
pack-independent `--help` path to prove runtime linking. Then rerun hosted CI
on the exact correction candidate. Public CI cannot run Classic gameplay
without private content, so the pack-backed SDL dummy smoke remains local or a
trusted-runner check.

## Independent checks that passed

The first attempted app build correctly reported the missing isolated
toolchain (exit 2). After the tracked bootstrap, these clean review-worktree
commands passed at exact handoff head `7972b16`:

```text
python3 tools/project.py bootstrap --report artifacts/m3-03-review/bootstrap.json
python3 tools/project.py build --preset app-debug --report artifacts/m3-03-review/app-debug-build.json --timeout 600 --task M3-03
python3 tools/project.py test --suite synthetic --preset app-debug --artifacts artifacts/m3-03-review/app-debug-synthetic --report artifacts/m3-03-review/app-debug-synthetic/report.json --timeout 600 --test-timeout 120 --task M3-03
python3 tools/project.py build --preset app-sanitize --report artifacts/m3-03-review/app-sanitize-build.json --timeout 600 --task M3-03
python3 tools/project.py test --suite synthetic --preset app-sanitize --artifacts artifacts/m3-03-review/app-sanitize-synthetic --report artifacts/m3-03-review/app-sanitize-synthetic/report.json --timeout 600 --test-timeout 120 --task M3-03
SDL_VIDEODRIVER=dummy python3 tools/project.py frontend run --pack '/Users/markfeaver/Projects/Unirally Decompilation/.worktrees/m3-03-minimal-frontend/artifacts/m3-03-first-launch.pack' --preset app-debug --hidden --updates 20 --timeout 30 --report artifacts/m3-03-review/dummy-debug.json --task M3-03
SDL_VIDEODRIVER=dummy python3 tools/project.py frontend run --pack '/Users/markfeaver/Projects/Unirally Decompilation/.worktrees/m3-03-minimal-frontend/artifacts/m3-03-first-launch.pack' --preset app-sanitize --hidden --updates 20 --timeout 30 --report artifacts/m3-03-review/dummy-sanitize.json --task M3-03
python3 tools/project.py content pack-inspect --pack '/Users/markfeaver/Projects/Unirally Decompilation/.worktrees/m3-03-minimal-frontend/artifacts/m3-03-first-launch.pack' --report artifacts/m3-03-review/pack-inspect.json --task M3-03-review
```

Both suites passed 281 Python tests, 20 CTests and three fresh-process runs:
304 required report checks, no failure or skip. Both dummy-video launches
validated the pack, opened no ROM, reported the 50 Hz/four-update scheduler and
audio omission, advanced 20 updates, and exited successfully. Pack inspection
validated the schema, all top-level identities, canonical layout and all 25
entry hashes. The pack SHA-256 is
`5c1fc5b00747621ccd2c0a1f6f34cf6ba290c8808e6bb1d92b8c0ad4b0df1529`.

Report SHA-256 values:

| Evidence | SHA-256 |
| --- | --- |
| app-debug build | `efe6eb3a74d09fefa9f973772b42cc2cede680d823507d2652f703015072eeda` |
| app-debug synthetic | `c0acae6812fa995aa2518f5ff37c17e483887a2d8bdd875f5ca05d5f59a01328` |
| app-sanitize build | `1ac2e2d7a99ff8e1b6e1d55feb175951ff5b9019be755e745605b19e1062c480` |
| app-sanitize synthetic | `e268716cb3d2a54bb5039fbf5c7ca194fd6f16b9c2f23388de2c1656accb4b64` |
| dummy debug | `4e51ab6957240c356c8c90160d5fcebc58cc6ffd42c20c532c7e6b3a38555f1d` |
| dummy sanitizer | `474b8ed3f8c212d993de9bfd5c70cc35d9e4b4cef4950527634076c824e2013c` |
| pack inspection | `05b60537b08766b9f971928b2af52344a4656b572468b703fbd8d2ff58c77386` |

The downloaded SDL archive is exactly 15,606,216 bytes and independently
hashes to the locked
`12b34280415ec8418c864408b93d008a20a6530687ee613d60bfbd20411f2785`.
CMake builds the shared library under the app build tree and the executable's
runtime path points there; no global SDL installation is used.

## Remaining audit conclusions

- Scheduler boundaries, the four-update cap, debt drop, pause/resume and the
  actual one-snapshot/one-update loop are correct over the practical
  `SDL_GetTicksNS` domain. All scheduler arithmetic is unsigned, so no UB was
  found. Deadline addition is not wrap-aware at `UINT64_MAX`; that is roughly
  a 584-year uptime horizon and is not a material M3 blocker.
- Keyboard/gamepad mapping covers all twelve accepted bits. State-source OR,
  release, focus clearing, disconnect clearing and two-port ownership are
  explicit. SDL object ownership destroys gamepads, texture, renderer and
  window before `SDL_Quit`; no lifetime defect was found.
- The Python layer validates an existing pack before considering `--rom`, does
  not overwrite existing corruption, uses the accepted exact-ROM/atomic pack
  writer when absent, revalidates before launch, and the C++ process validates
  all identities again before SDL initialization. Missing/wrong/cancelled ROM,
  corrupt pack, missing executable, ordinary nonzero child exit and finite
  timeout outcomes are correctly distinguished by source/tests.
- Integer viewport centering, 1x minimum, nearest texture scaling and per-redraw
  output-size queries implement the frozen 256x224 scaling contract. The
  renderer is guarded by before/after canonical serialization and receives a
  presentation-only camera; no gameplay-state coupling was found.
- SDL initializes video and gamepad only. Help, startup text, README and report
  metadata explicitly declare that audio is omitted; no audio success is
  claimed.

## Repository hygiene

`git diff --check 759ed9e..6489c64` passed. The behavioral diff contains 17
tracked source/test/doc/lock paths and text-only additions. `git ls-files`
finds no ROM, generated Classic pack, state, capture, screenshot or report.
All review builds, reports and the reviewed private pack remain ignored under
`build/`, `artifacts/` or another isolated worktree. The review worktree had no
tracked modification before this report.

## Required correction and re-review

Keep the screen current while only unrecovered rider poses are held (or recover
the needed atlas poses), reject NaN/infinite timeouts before spawning and prove
no report/process leak, check `SDL_RenderPresent`, and add hosted app-preset
compilation on macOS/Linux. Re-run both local app suites, the two dummy-video
smokes, the continuous-race staleness check, the non-finite-timeout mutation and
hosted app builds on the exact correction candidate. Do not accept M3-03 or the
M3 playable gate before those results pass independent re-review.

## Worker correction response — 13 September 2026

All four findings are addressed on the assigned task branch without changing
the accepted core, pack, state, cases, visual limits or scheduler contract:

1. `LivePresentation` now retains only the last recovered pose pair and renders
   a fresh current-state frame through a temporary copy. The native regression
   proves two distinct unsupported gameplay/camera/timer states produce
   distinct RGB frames, each equal to a current-state render with only pose
   fields substituted. A 1533–3679 SDL dummy continuous-right run rendered
   2,145 frames (two batched display iterations), used fallback on 1,419, and
   found zero identical consecutive fallback redraws while Racing.
2. `frontend run` rejects NaN and both infinities before pack access or child
   execution. Each authored mutation requires a failed requested JSON report
   and a mocked child-call count of zero. The review's exact NaN CLI shape now
   exits 3, writes the report, and `pgrep` finds no matching app.
3. `SDL_RenderPresent` is checked and throws `cannot present rendered frame`
   with SDL's error on false.
4. The ROM-free workflow retains headless debug/sanitizer steps, adds
   `app-debug` build/test and pack-free `--help` on macOS 15 and Ubuntu 24.04,
   and adds `app-sanitize` build/test/help on Ubuntu. Every new command has a
   600-second command bound inside the existing 30-minute job bound.

Local broad debug and sanitizer suites passed on the uncommitted correction
(282 Python tests, 20 CTests and repeatability). Exact-commit reports, private
finish/presentation reruns, commit IDs and hashes are recorded in M3-03 after
the coherent correction commit. Fresh sequential re-review and hosted results
remain required; this response does not approve the task.

The exact behavioral correction is
`3509ae99ed5102d8d7e2afdbea9d7e4ecbeda4da`. Both complete app suites,
debug/sanitizer dummy smokes, the 2,146-update continuous-right run, and the
private finish/presentation gates passed at that SHA. The exact continuous run
again recorded 1,419 fallback frames and zero identical consecutive fallback
redraws while Racing. `tasks/M3-03.md` contains the exact commands and report
hashes. This documentation-only follow-up does not replace the required fresh
review or hosted macOS/Linux evidence.

## Fresh sequential re-review — correction round 2

- Handoff head reviewed: `126cd1685e1711f0e87e816058a0c4dcaba8c194`
- Behavioral correction reviewed:
  `3509ae99ed5102d8d7e2afdbea9d7e4ecbeda4da`
- Correction diff: `8ccb0377ae0f9a244b7bb11638f875be6a625342..3509ae99ed5102d8d7e2afdbea9d7e4ecbeda4da`
- Reviewer: fresh sequential OpenAI Codex Sol/medium session
- Worktree/branch:
  `.worktrees/m3-03-minimal-frontend/.worktrees/m3-03-rereview`,
  `review/M3-03-minimal-frontend-r2`
- Date: 13 September 2026 AEST
- Verdict: **returned with material findings; not approved**

### Findings

#### 1. The fallback still changes scene-wide effects, not only rider art

The former complete-frame freeze is corrected: camera, track, rider positions
and timer now come from a fresh current-state render, and the external
canonical state is not mutated. The replacement is nevertheless not yet the
declared rider-only fallback. `LivePresentation::render` copies the complete
state, substitutes the retained pose indices/reflection, and passes that copy
through the complete renderer (`frontend.cpp:128-151`). Those pose fields also
select the scene-wide racing/finish palette (`presentation.cpp:158-169`) and
the GO/winner window effects (`presentation.cpp:760-763,787-788`), in addition
to selecting rider atlas tiles.

An independent pack-backed boundary made both riders wholly off-screen and
rendered the **same current unsupported state**, camera, scroll and HUD twice.
One `LivePresentation` instance had last accepted the late-finish pair
`04fe/037c`; the other had last accepted the rolling pair `0855/0895`. The two
fallback frames differed in **14,290 RGB channel bytes** even though no rider
pixel could contribute. The probe deliberately exited 7 on a difference. A
second authored-content probe with a visible synthetic window differed in
114,448 channel bytes. This proves fallback history leaks into non-rider scene
pixels. It also explains why the new regression misses the defect: its GO and
winner window tables are empty, and its expected frame is produced by the same
whole-state pose substitution.

Holding recovered rider art is acceptable for M3-03; recovering sustained pose
coverage and judging real play belong to M3-04. The acceptable boundary must,
however, apply retained pose/reflection only to atlas/rider drawing while the
current semantic state continues to control palette, effects, camera and HUD.
Add a regression in which the same unsupported current state and off-screen
riders render identically after two different recovered-art histories.

The exact final probe command was:

```text
/usr/bin/clang++ -std=c++20 -Isrc/app -Isrc/core -x c++ - -x none build/app-debug/src/app/libunirally_frontend.a build/app-debug/src/core/libunirally_presentation.a build/app-debug/src/core/libunirally_movement.a build/app-debug/src/core/libunirally_contact.a build/app-debug/src/core/libunirally_input_timer.a build/app-debug/src/core/libunirally_speed_limits.a build/app-debug/src/core/libunirally_sampling.a -o artifacts/m3-03-rereview/fallback-history-pack-boundary
artifacts/m3-03-rereview/fallback-history-pack-boundary '/Users/markfeaver/Projects/Unirally Decompilation/.worktrees/m3-03-minimal-frontend/artifacts/m3-03-first-launch.pack'
```

The inline probe loaded that identity-validated pack, used the public semantic
start, captured its valid opening presentation position, set phase Racing,
made both rider X coordinates zero and both poses reflected unsupported
`04fa`, primed separate presentation instances with the pairs above, and
counted unequal channel bytes with `std::inner_product`. The output was
`same_current_state_offscreen_riders_history_pixel_differences=14290` and exit
7. The private pack is unchanged and remains ignored.

#### 2. Separated negative infinity still loses the requested report

The command handler now rejects non-finite values before pack access or child
creation. At the real CLI boundary, however, argparse interprets the natural
two-token spelling `--timeout -inf` as a new option and exits before
`cmd_run`. `tools/project.py` maps that usage exit to 3, but no requested JSON
report is written. The authored test calls `cmd_run` directly, so it cannot
detect this parser boundary.

Exact results using the valid review pack were:

```text
--timeout nan       -> exit 3, failed report written, no matching child
--timeout inf       -> exit 3, failed report written, no matching child
--timeout -inf      -> exit 3, argparse error, no report, no matching child
--timeout=-inf      -> exit 3, failed report written, no matching child
```

The post-run process scan
`pgrep -fl '/m3-03-rereview/build/app-debug/src/app/unirally'` exited 1. Thus
the crash/orphan defect is corrected, but the requirement that every
non-finite timeout produce its requested failed report is not. Add a
subprocess-level CLI regression for all four spellings above and handle the
separated negative-infinity token before argparse loses command/report
context.

#### 3. Exact-head hosted Linux app and sanitizer evidence failed

Hosted run `34699306504` ran at exact head `126cd16`. macOS 15 passed the
headless suite, `app-debug` build and suite, and the executable help/link
smoke. Ubuntu 24.04 passed the existing headless debug build and suite, then
failed configuring `app-debug`: SDL reported that it could find neither X11
nor Wayland development libraries (with a separate non-fatal ALSA warning).
The Linux app-debug suite/help and the complete Linux `app-sanitize`
build/suite/help step were consequently skipped. The run conclusion is
failure.

This confirms that the workflow selects the right app presets and preserves
the headless path, but it does not yet provide Linux SDL compilation/linking or
sanitizer evidence. The smallest correction is a bounded Ubuntu-only install
of an explicit SDL-documented X11 or Wayland development package set before
the app steps, followed by an exact-candidate rerun. Disabling SDL's Unix
desktop-backend check would compile dummy/offscreen support only and would not
satisfy the desktop-window acceptance criterion. Dependency preparation and
the build remain bounded by the 30-minute job limit and should also retain
explicit command-level timeouts.

Reproduction/inspection:

```text
gh run view 34699306504 --json status,conclusion,jobs,url,headSha
gh run view 34699306504 --job 103568159240 --log-failed
```

### Corrected items confirmed

- The only tracked `SDL_RenderPresent` call is now checked; false throws
  `cannot present rendered frame` with SDL's error. No discarded present call
  remains.
- NaN, positive infinity and the equals-form negative infinity all exit 3,
  write a failed exact-head report before pack/child execution, and leave no
  app process. The remaining report gap is the parser boundary above.
- The fallback does not mutate accepted canonical gameplay state, and it no
  longer holds complete RGB frames. The remaining defect is presentation-only
  but material because startup and R-0016 claim that the whole scene stays
  current while only rider art is held.
- The hidden `--fixed-controller-mask` seam overrides port 0 only after the
  ordinary per-update input snapshot. It is suitable for deterministic
  scheduler/simulation/presentation smoke evidence and does not change the
  canonical core. It does bypass SDL event-to-mask delivery, so the 2,146-
  update run is not evidence that live keyboard/gamepad input works. Pure
  mapping/state tests and source inspection cover the logical boundary;
  M3-04's real sustained-play check must exercise actual live input. With that
  evidence scope stated accurately, the seam itself is not a blocker.

### Local validation

These commands passed at exact handoff head `126cd16`:

```text
python3 tools/project.py build --preset app-debug --report artifacts/m3-03-rereview/app-debug-build.json --timeout 600 --task M3-03-review-r2
python3 tools/project.py test --suite synthetic --preset app-debug --artifacts artifacts/m3-03-rereview/app-debug-synthetic --report artifacts/m3-03-rereview/app-debug-synthetic/report.json --timeout 600 --test-timeout 120 --task M3-03-review-r2
python3 tools/project.py build --preset app-sanitize --report artifacts/m3-03-rereview/app-sanitize-build.json --timeout 600 --task M3-03-review-r2
python3 tools/project.py test --suite synthetic --preset app-sanitize --artifacts artifacts/m3-03-rereview/app-sanitize-synthetic --report artifacts/m3-03-rereview/app-sanitize-synthetic/report.json --timeout 600 --test-timeout 120 --task M3-03-review-r2
SDL_VIDEODRIVER=dummy python3 tools/project.py frontend run --pack '/Users/markfeaver/Projects/Unirally Decompilation/.worktrees/m3-03-minimal-frontend/artifacts/m3-03-first-launch.pack' --preset app-debug --hidden --updates 20 --timeout 30 --report artifacts/m3-03-rereview/dummy-debug.json --task M3-03-review-r2
SDL_VIDEODRIVER=dummy python3 tools/project.py frontend run --pack '/Users/markfeaver/Projects/Unirally Decompilation/.worktrees/m3-03-minimal-frontend/artifacts/m3-03-first-launch.pack' --preset app-sanitize --hidden --updates 20 --fixed-controller-mask 128 --timeout 30 --report artifacts/m3-03-rereview/dummy-sanitize.json --task M3-03-review-r2
```

Both suites ran 282 Python tests, 20 CTests and three fresh processes: 305
required checks, no failure or skip. Both pack-only dummy-video launches
validated the pack without opening a ROM and exited successfully. Report
SHA-256 values:

| Evidence | SHA-256 |
| --- | --- |
| app-debug build | `7536caf7597e3b6e4b0fdfe489612b8a24430124d0ed675eb45bcf0db8cd7733` |
| app-debug synthetic | `3f5cb55126f26d4b7a1db22d3624d37d2db3ff994e4f0536f2799dfcd86da9e9` |
| app-sanitize build | `d67c698e6c6fef59c950ec79d6c900d79a154bd54928d2c4f938a69d94c72281` |
| app-sanitize synthetic | `fa53bc89863be928a21269efaf6acdde583429d651c00c924e0e73e4c169551c` |
| dummy debug | `67d4bc9447c2edacbc660ffb14833bc1fdbd5e8a3dab42a17547eb9f537f7e00` |
| dummy sanitizer | `766b685ce9af5a40b77e97a02938f1ef33db2feeb929968ba8ef762f7a0b33d3` |
| rejected NaN | `aa1cdd1db5650ed88c57fc8b2929e406b07e929e0f1e172770f3b6b5ec40d35a` |
| rejected positive infinity | `12d8254f3d46713c8d209cf06c42a6f024813b8fc0d30fb0751202feda070740` |
| rejected equals-form negative infinity | `f22eb4f631a259f66ffe3796bf46f39f53428ebedde5e3ef16e4a9dea8de7d55` |

All nine reports name `126cd1685e1711f0e87e816058a0c4dcaba8c194`
as their source commit. The three timeout reports correctly have overall
status `failed`; that is the required mutation result. The separated
negative-infinity case has no report and is therefore intentionally absent
from the table.

`git diff --check 8ccb037..3509ae9` passed. The review worktree had no tracked
changes before this appended round. Generated builds, reports, probe binaries,
the toolchain links and the Classic pack all remain ignored. No implementation,
case, manifest, threshold or accepted core semantic was changed by this
review.

### Required correction and next review

Decouple retained rider art from pose-derived palette/window scene behavior;
make every CLI spelling of negative infinity emit the requested invalid-input
report without starting a child; prepare a real Linux SDL window backend in
the hosted workflow and obtain green Linux app-debug/app-sanitize evidence.
Then rerun both local app suites, the same-state/off-screen-rider fallback
boundary, all CLI non-finite mutations, dummy smokes and exact-head hosted CI.
M3-03 remains unapproved.

## Worker correction response — round 2

All three findings are corrected without changing the accepted gameplay,
pack/state formats, cases, scheduler or visual thresholds:

1. The existing M3-02 headless API remains and delegates without an override.
   A new additive renderer call accepts only two `RiderArtPose` values. Atlas
   loading and rider-frame validation consume that override; the current
   semantic state alone drives palette, GO/winner windows, camera, positions
   and HUD. The authored regression uses active effect tables and a nonuniform
   palette, primes rolling and late-finish histories, and proves the same
   unsupported state is pixel-identical when riders are off-screen. With riders
   visible the histories differ only inside their two 64-pixel rider rectangles.
   Both canonical states remain byte-identical.
2. `tools/project.py` narrowly normalizes only a separated negative-infinity
   token following `frontend run --timeout`; generic argparse behavior for all
   other commands is unchanged. A subprocess regression exercises `nan`,
   `inf`, separated `-inf` and `--timeout=-inf`, requiring exit 3, a written
   failed report and an executable sentinel that never starts. Real pre-commit
   probes reproduced all four successful rejection outcomes and found no app
   process.
3. Ubuntu CI now installs SDL 3.4.10's documented X11 development package set
   before app builds. Both APT operations have 300-second bounds inside the
   existing 30-minute job. This ephemeral hosted preparation is distinct from
   the pinned, build-local SDL source dependency and does not install SDL
   globally or disable its desktop backend.

Pre-commit app-debug and app-sanitize suites passed 283 Python tests, 20 CTests
and three fresh processes. Exact correction commits and evidence are recorded
in `tasks/M3-03.md` after the coherent commit. Fresh re-review and exact-head
hosted CI remain required; this response does not approve M3-03.

The exact round-2 behavioral correction is
`457ba885f82856b5b328243ecffcacce03312bf5`. Both complete app suites,
debug/sanitizer SDL dummy smokes, the sustained continuous-right diagnostic,
all four real CLI timeout spellings and the private finish/presentation gates
passed at that SHA. `tasks/M3-03.md` records exact commands and hashes. This
documentation-only follow-up still requires independent re-review and hosted
Linux/macOS evidence.

Post-push hosted run `34700625467` completed successfully at handoff SHA
`6b4ac12cf7d9c1097a5cf7e41c3f159be34898ee`: macOS app-debug and Ubuntu
X11 preparation, app-debug and app-sanitize all passed, including both
runtime-link help smokes. Fresh independent review remains required.

## Final fresh independent re-review — correction round 3

- Handoff head reviewed:
  `509d43fac4666a6c95716dbcff35e740817a8ee1`
- Behavioral correction reviewed:
  `457ba885f82856b5b328243ecffcacce03312bf5`
- Complete behavioral diff:
  `759ed9e0b130819d09392b61946c27e433f44438..457ba885f82856b5b328243ecffcacce03312bf5`
- Reviewer: fresh sequential OpenAI Codex Sol/medium session
- Worktree/branch: `.worktrees/m3-03-final-review`,
  `review/M3-03-minimal-frontend-r3`
- Date: 13 September 2026 AEST
- Verdict: **returned with one material CLI safety finding; not approved**

### Finding: `--report` can overwrite the user-supplied ROM or validated pack

The frontend command does not reject a report path that aliases an input or
runtime artifact. It reads the ROM at `frontend/commands.py:59-69`, launches
the child, and then unconditionally writes the report to `args.report` at
`frontend/commands.py:20-23`. Consequently a first-launch command with
`--report` equal to `--rom` completes successfully and replaces the user's ROM
with JSON. The corresponding existing-pack spelling can replace a validated
Classic pack after a successful pack-only launch. This is a material
first-launch/data-safety defect, particularly because the supported ROM is a
user-owned prerequisite that may not be recoverable from the generated pack.

I reproduced the ROM case only on an ignored disposable copy. The original
source ROM was checked before and after and remained unchanged:

```text
cp '/Users/markfeaver/Projects/Unirally Decompilation - Assets/Unirally (Europe).sfc' artifacts/m3-03-final-review/disposable-rom.sfc
python3 tools/project.py frontend run \
  --pack artifacts/m3-03-final-review/collision.pack \
  --rom artifacts/m3-03-final-review/disposable-rom.sfc \
  --executable /usr/bin/true --updates 1 --timeout 30 \
  --report artifacts/m3-03-final-review/disposable-rom.sfc \
  --task M3-03-final-review-collision
```

The command exited 0 and reported successful exact-ROM validation, atomic
25-entry pack creation and frontend launch. The collision target changed from
2,097,152 bytes with PAL ROM SHA-256
`a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`
to a 2,724-byte passed JSON report with SHA-256
`a65d3aa96c0669f468c1f62f29b42d8429d7e5dab80a9288f65172cbbdd19ee1`.
The report itself still recorded the overwritten input's former size and
identity, demonstrating that the overwrite occurs only at final report write.

Reject `--report` aliases of at least `--rom` and `--pack` before reading,
extracting or spawning, including resolved/same-file aliases, and add
subprocess regressions proving both inputs remain byte-identical and no child
starts. The same guard should cover the explicit rules/executable paths so a
hidden testing override cannot overwrite those files either. This correction
does not require a gameplay, pack-format, renderer or scheduler change.

### Round-2 corrections independently confirmed

The rider-art seam now has the required boundary. `LivePresentation` passes
the current `MovementState` unchanged and supplies recovered history only as
two additive `RiderArtPose` values (`frontend.cpp:128-149`). In the core,
current state selects the background, race palette, GO/winner windows, HUD,
camera and rider positions; only the temporary atlas state and rider-pose
validation consume the override (`presentation.cpp:757-803`). The original
M3-02 `render_dragster_headless` entry point remains and delegates without an
override, so its source/API behavior is preserved.

The authored same-state/off-screen history regression passed in both broad
suites. I also compiled an independent pack-backed boundary using the current
GO semantic state and two different rolling/finish art overrides. With visible
riders it found 800 different pixels and every difference was inside the two
64-pixel rider rectangles. With the same riders wholly off-screen it found zero
different pixels. Canonical serialization was byte-identical before and after.
This independently confirms that palette/window/history leakage is corrected,
not merely hidden by the authored test's data.

All required real CLI spellings now behave correctly: `nan`, `inf`, separated
`--timeout -inf`, and `--timeout=-inf` each exited 3 and wrote its requested
failed report at exact head `509d43f`. A separate executable-sentinel run of
the natural separated `--timeout -inf` form also exited 3, wrote the failed
report and left the sentinel absent, proving no child started. Source and an
independent direct assertion confirm normalization changes only a separated
`-inf`/`-infinity` immediately following `frontend run --timeout`; native and
other subcommands, ordinary negative numbers, `nan`, and unrelated frontend
arguments retain generic argparse behavior.

The exact hosted evidence is valid. `gh run view 34700625467` reports success
at `6b4ac12cf7d9c1097a5cf7e41c3f159be34898ee`, whose only successor before
this review is the documentation-only `509d43f`. macOS 15 passed headless
debug, app-debug build/test and the executable help/link smoke in 2m59s.
Ubuntu 24.04 first passed the headless suite, then completed both explicitly
300-second-bounded APT operations for the tracked X11 package set, configured
and built the pinned SDL desktop frontend, passed app-debug test/help, and
passed lab-sanitize plus app-sanitize build/test/help in 4m38s. Downloaded
hosted reports bind the app builds and tests to clean `6b4ac12`; both app
suites ran 283 Python tests, the frontend contract CTest and fresh-process
repeatability. The workflow retains its 30-minute job bound and 600-second app
build/test bounds. The only annotations/log warnings are the recorded GitHub
Node-action deprecations; no product warning or skipped required Linux app step
remains.

### Local exact-head validation

The following commands passed at `509d43f`:

```text
python3 tools/project.py build --preset app-debug --report artifacts/m3-03-final-review/app-debug-build.json --timeout 600 --task M3-03-final-review
python3 tools/project.py test --suite synthetic --preset app-debug --artifacts artifacts/m3-03-final-review/app-debug-synthetic --report artifacts/m3-03-final-review/app-debug-synthetic/report.json --timeout 600 --test-timeout 120 --task M3-03-final-review
python3 tools/project.py build --preset app-sanitize --report artifacts/m3-03-final-review/app-sanitize-build.json --timeout 600 --task M3-03-final-review
python3 tools/project.py test --suite synthetic --preset app-sanitize --artifacts artifacts/m3-03-final-review/app-sanitize-synthetic --report artifacts/m3-03-final-review/app-sanitize-synthetic/report.json --timeout 600 --test-timeout 120 --task M3-03-final-review
SDL_VIDEODRIVER=dummy python3 tools/project.py frontend run --pack <ignored-pack> --preset app-debug --hidden --updates 20 --timeout 30 --report artifacts/m3-03-final-review/dummy-debug.json --task M3-03-final-review
SDL_VIDEODRIVER=dummy python3 tools/project.py frontend run --pack <ignored-pack> --preset app-sanitize --hidden --updates 20 --fixed-controller-mask 128 --timeout 30 --report artifacts/m3-03-final-review/dummy-sanitize.json --task M3-03-final-review
SDL_VIDEODRIVER=dummy python3 tools/project.py frontend run --pack <ignored-pack> --preset app-debug --hidden --updates 2146 --fixed-controller-mask 128 --timeout 90 --report artifacts/m3-03-final-review/continuous-right.json --task M3-03-final-review
python3 tools/project.py native finish-check --manifest tests/manifests/native/full-race-continuous.case.json --content-pack <ignored-pack> --save-frame 3213 --save-frame 3453 --preset lab-debug --artifacts artifacts/m3-03-final-review/finish --report artifacts/m3-03-final-review/finish/report.json --timeout 600 --task M3-03-final-review
python3 tools/project.py native presentation-check --manifest tests/manifests/presentation/classic-crawler-dragster-v1.json --fixtures artifacts/m3-03-final-review/private-fixtures --content-pack <ignored-pack> --preset lab-debug --artifacts artifacts/m3-03-final-review/presentation --report artifacts/m3-03-final-review/presentation/report.json --timeout 600 --task M3-03-final-review
```

Both broad app suites passed 283 Python tests, 20 CTests and three fresh
processes: 306 required checks, no failure or skip. The 2,146-update diagnostic
rendered 2,146 frames, used rider-art fallback on 1,421, and retained zero
identical consecutive fallback redraws while Racing. Private finish passed the
full-race identity and both continuation boundaries. Private presentation
retained exact accepted mismatch counts 36, 697, 279, 445, 653, 962 and 961.
Focused frontend CTest, all five frontend tooling tests and executable help
also passed. The SDL archive independently hashes to the lock
`12b34280415ec8418c864408b93d008a20a6530687ee613d60bfbd20411f2785`;
the macOS executable links the build-local SDL dylib and exports both the old
and additive presentation symbols.

Report SHA-256 values:

| Evidence | SHA-256 |
| --- | --- |
| app-debug build | `30abc0de2351b7526210186ae713158c21d34d1ee222ccf2c0395a9c5649b0eb` |
| app-debug synthetic | `05db83b30cc4632d26d6317ac88b658f707443386f0ab3fef66b0cd99a590c2d` |
| app-sanitize build | `9265333e87ff78fee1f2fd3d23e54c5e5ca43971652e04993cbc41272c02fb13` |
| app-sanitize synthetic | `8212a9d2c2a2ad1103c9c01c9a4fdfb6dbb2d83f5fafdb58bd8be7576d54f430` |
| dummy debug | `62a36b82f00877889df6ebb27236b01b8688d744280e5e669e9578a40bc61d96` |
| dummy sanitizer | `8f52d433bc8f6542053f5b727d0228d0f011977507c5d43961488e32eafb8caa` |
| continuous right | `bc82aa769c18fb41ecb2b07d2f95d07544d57264a59997e43eb8fec9b7555c66` |
| rejected `nan` | `278bd7ffc7ecf27653efb872cb3f4820e014c26905c01ad9031bea5ba42c578d` |
| rejected `inf` | `28b61bc2595244f65d4ffe3c14e96f849f1d3a4e1e8164369659180db614e9d1` |
| rejected separated `-inf` | `0b0341f89ab28e7a5d3ed1019223bedbfeb0c00832353bb85b7381e691c812bd` |
| rejected equals `-inf` | `d923c106c6c5860ed717f865d2a1f7b1fa0449e8b05d654085d907c1007da40f` |
| separated `-inf` sentinel | `2fc6d958393c89c54dbb4349dda23a461949a568508d9648e907300f3038e461` |
| private finish | `649a469fac8d6d47aaa4a02dc06baa45fa5c8e67826887b82deb756d7b078e21` |
| private presentation | `bb53ed7061581a375eb477579db94e65d757d91c0ffcfd354ef5ee20a71589df` |

Every listed local report names `509d43f`. The timeout reports intentionally
have failed overall status; all other listed reports passed.

### Remaining audit conclusions and hygiene

No additional scheduler, SDL lifetime/error, input ownership, renderer,
canonical-state, pack-validation or accepted-core regression was found.
`SDL_RenderPresent` remains checked. Pack validation still precedes SDL and
gameplay, existing corruption is not silently replaced, and pack-only launches
do not open the ROM. Scheduler boundaries/catch-up/debt drop, focus clearing,
all 12 logical controls, simultaneous/released inputs, gamepad disconnect and
two-port ownership remain explicit and covered. Nearest integer scaling and
the 256x224 render boundary remain unchanged. Audio omission is explicit.

The declared rider-art hold is acceptable for M3-03 now that history is
strictly confined to rider rectangles and canonical gameplay remains current.
The fixed-mask sustained diagnostic is not evidence of actual keyboard/gamepad
delivery; the task record correctly defers a real sustained live-input/window
check and the final readability judgment to M3-04. That stated evidence limit
is not itself a blocker for M3-03.

`git diff --check 759ed9e..509d43f` passed. The implementation does not change
accepted gameplay serialization, cases, private expectations or visual
thresholds. `git ls-files` finds no ROM, generated pack, state, capture,
screenshot or report payload. All local builds, hosted downloads, private
fixtures, the disposable collision input and boundary probes are ignored under
`build/`, `local/` or `artifacts/`. Before this appended report the worktree had
no tracked modification.

### Required correction and re-review

Reject report/input aliases before any pack/ROM access or child creation, prove
the ROM and pack remain byte-identical for collision attempts, and rerun the
focused frontend tooling test. The local/hosted build, renderer and private
gameplay/presentation evidence above need not be repeated if that fix is
strictly limited to the Python path-collision guard and its tests; a fresh
review should inspect and reproduce the exact correction. M3-03 remains
unapproved until this material data-safety finding is corrected.

## Worker response — final path-collision correction

The frontend command now rejects `--report` aliases of the ROM, pack,
extraction rules and explicit/default executable before timeout reporting,
input reads, extraction or child creation. The comparison covers normalized
lexical paths, non-strict resolved paths, symlinks and hardlinks. Because a
collision report cannot be written safely, the command emits a clear stderr
diagnostic and exits 3 without writing it; unrelated failure reports retain
their prior behavior.

Authored direct tests cover existing ROM lexical/symlink/hardlink aliases,
rules and executable aliases, a normalized absent-pack alias and an existing
pack alias. Subprocess tests reproduce ROM and pack collision commands with an
executable sentinel. They require byte-identical inputs, no created pack in the
ROM collision, no sentinel child, exit 3 and the specific diagnostic. Exact
candidate SHA and full-suite/first-launch evidence are appended to M3-03 after
the coherent commit. Fresh narrow review remains required; this response does
not approve M3-03.
