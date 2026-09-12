# R-0016 — Minimal SDL3 frontend contract

Status: frozen before SDL UI implementation, 12 September 2026. Task M3-03.

## Observations

- The accepted native boundary exposes one `update_movement` call per PAL game
  update, a validated `ClassicContentPack`, and a 256 by 224 RGB headless
  renderer. The renderer accepts presentation-only camera and scroll values and
  does not mutate canonical gameplay state. See R-0015 and `src/core/README.md`.
- The content command already exact-gates the supported PAL ROM and commits a
  complete pack atomically. The C++ pack reader independently validates all 25
  identities and payload hashes before exposing an entry.
- SDL's documented CMake integration supports a vendored source tree and the
  `SDL3::SDL3` target. Release 3.4.10's source archive is 15,606,216 bytes with
  SHA-256 `12b34280415ec8418c864408b93d008a20a6530687ee613d60bfbd20411f2785`
  (downloaded from the upstream release on 12 September 2026).

## Decisions (frontend-only)

### Dependency and build

SDL 3.4.10 is fetched by CMake from the pinned upstream release URL with the
above required digest and built inside `build/app-*`; it is never installed.
`LAB_BUILD_APP` defaults off, so `lab-debug`, `lab-release` and `lab-sanitize`
remain window-independent and do not download, configure, link or require SDL.
The tracked `app-debug` and `app-sanitize` presets enable the desktop target.
ROM-free hosted CI retains the headless jobs and additionally builds/tests
`app-debug` on macOS and Linux and `app-sanitize` on Linux, with a pack-free
`--help` runtime-link smoke. SDL examples, tests and install targets are
disabled. macOS uses the platform SDK; Linux uses the host window-system
development interfaces SDL detects.

### Scheduler

One update is due every 20,000,000 monotonic nanoseconds. At construction or
resume the first deadline is `now + 20 ms`: an early poll runs zero updates and
the exact deadline runs one. A poll may run at most four updates. If five or
more are due, four run and accumulated debt is dropped by setting the next
deadline to `now + 20 ms`; this bounds work after suspend or a stalled display.
Otherwise deadlines advance by the number run, retaining sub-update lateness.
While paused no update is due. Focus loss pauses, clears held input, and resume
starts a fresh 20 ms interval. Rendering occurs once after the due update batch;
display refresh and resize never create simulation updates.

The current held input is snapshotted separately for every due update. During a
catch-up batch those snapshots can be equal, but there is still exactly one
snapshot and one `update_movement` call per update.

### Input

The accepted 16-bit controller mask is B/Y/Select/Start/Up/Down/Left/Right/
A/X/L/R in bits 0 through 11. Keyboard port 0 maps Z/X/Backspace/Return/arrows/
A/S/Q/W in that order. Standard gamepad buttons map South/West/Back/Start/
D-pad/East/North/left shoulder/right shoulder. The first opened gamepad owns
port 0 and the second owns port 1; keyboard and gamepad state are ORed on port
0. Simultaneous inputs are preserved. Key/button release clears only that
source. Gamepad removal clears and releases its port; focus loss clears all
sources. The M3 simulation consumes port 0 only because local two-rider control
is outside the recovered gameplay domain; port 1 remains explicit and tested.

### Pack and first launch

`python3 tools/project.py frontend run` defaults to
`local/classic-crawler-dragster.pack`. An explicit `--pack` overrides it. A
valid existing pack takes precedence over `--rom` and launches without opening
the ROM. An invalid existing pack fails and is never silently overwritten. If
the pack is absent, `--rom` is required; it is exact-gated and atomically
extracted through the accepted pack implementation, then revalidated before
launch. Omitted/cancelled ROM input, a missing file, wrong ROM, failed
extraction, missing executable, SDL initialization, renderer or texture failure
all produce a nonzero launch. The app executable itself accepts only a pack;
the tracked frontend command owns extraction.

### Display and presentation

The source is always 256 by 224 RGB. Each drawable-size change selects
`max(1, min(width/256, height/224))`, centers that exact integer viewport and
clears unused pixels to black. The texture uses nearest-neighbor scaling.
Window size starts at 768 by 672 (3x) and has a 256 by 224 minimum.

The accepted core has no live camera recurrence. For this minimal frontend,
race presentation uses a deterministic, presentation-only follow rule:
`camera_x = max(0, signed_player_x - 880)`, BG1 X is `camera_x - 14`, BG2 X is
integer division of BG1 X by two, BG1 Y is 208 and BG2 Y is 104. Finish/result
uses the last race camera; the accepted renderer ignores those values for the
result screen. This is an explicit UI decision, not a recovered gameplay claim,
and it never enters canonical state. The values agree within three pixels of
the four frozen moving race samples and exactly in their vertical/parallax
relationship after the opening sample.

Audio is not initialized or implemented in M3-03. Help and startup output say
so explicitly.

The accepted atlas boundary intentionally recognizes only the five recovered
rider-pose pairs frozen by M3-02. The frontend calls it unchanged. Between
supported pairs it renders a fresh frame from the current gameplay state,
camera, scroll, rider positions and timer, but substitutes the last recovered
pair's pose indices/reflection in a temporary presentation copy. Before the
first supported pair that copy uses the opening recovered pair. Canonical
gameplay is never changed. Startup reports this rider-art omission once. This
makes the whole accepted simulation readable without pretending that
unrecovered animation frames exist; extending pose coverage belongs to a later
presentation task.

## Validation domain and limits

Pure authored tests cover deadline boundaries, bounded recovery, pause/resume,
all mappings, simultaneous/released input, focus/disconnect clearing, two-port
ownership and integer viewports without SDL or a display. A pack-backed frozen
input/cadence test must compare the complete canonical state sequence under two
display poll schedules and require presentation rendering not to alter it.
Real window/backend availability remains an M3-04 sustained-play check; a CI
machine without a display builds but does not claim an interactive launch.

## Returned-review observations and correction

Independent review of `6489c64` established that 1,421 of the 2,147 canonical
continuous-right states use an unrecovered atlas pair (66.185%). The first
implementation held the complete prior RGB frame for those states, including
race freezes as long as 153 updates / 3.06 seconds. That behavior contradicted
the rider-only omission above and is rejected; see `tasks/M3-03-review.md` for
the input/output hashes and interval inventory.

The corrected pure adapter stores only two pose indices and reflection flags.
Every redraw copies the current semantic state, substitutes those four
presentation-only fields when needed, and renders current camera, scroll,
positions and HUD. An authored regression uses two distinct unsupported
states, camera values and timer digits: their RGB frames differ, each exactly
equals a direct render of that current state with only the recovered pair
substituted, and both canonical states remain unchanged.

An actual dummy-video, fixed continuous-right launch from frame 1533 through
3679 produced 2,145 redraws; two display iterations batched updates under the
unchanged scheduler. It used rider-pose fallback on 1,419 redraws and had
**zero identical consecutive fallback redraws while Racing** (longest such run
zero). Across all phases it had 383 identical redraws and a longest run of 228,
which the metric reports rather than misclassifying as the former race fallback
freeze. The launch report is
`artifacts/m3-03-correction-continuous-right-3.json`; ignored artifacts are not
tracked.

The review also reproduced `--timeout nan` escaping the bounded-process helper,
losing the requested report and orphaning a child. Frontend argument validation
now requires a finite positive timeout before pack access or process creation.
Authored NaN, positive-infinity and negative-infinity cases require exit 3, a
failed JSON report and zero calls to the child runner. The exact NaN CLI
reproduction now emits its report and leaves no matching app process.

Finally, SDL 3.4.10 declares `SDL_RenderPresent` as returning `bool`. The prior
discarded return is rejected; the app now throws a renderer-specific launch
failure when it is false. No backend-independent way to force that SDL call to
fail was introduced merely for the test, so source inspection plus hosted/local
runtime smokes cover this narrow error check.
