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
