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
disabled. macOS uses the platform SDK. On ephemeral Ubuntu runners only, CI
installs the X11 development package set listed by SDL 3.4.10's
`docs/README-linux.md` before app builds, with each APT operation bounded to
300 seconds. These OS headers compile SDL's real desktop backend; they are
distinct from the SHA-256-pinned SDL source build and do not require or
authorize a global SDL installation on a developer machine.

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
camera, scroll, rider positions, timer, palette and window effects. A narrow
renderer input selects only rider atlas art from the last recovered pose pair;
before the first supported pair it uses the opening recovered pair. Canonical
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

The first correction's pure adapter stored only two pose indices and reflection
flags, but substituted them into a complete temporary semantic state. A second
review proved those fields also selected race palette and GO/winner windows,
so fallback history changed 14,290 RGB channel bytes with both riders
off-screen. That presentation leakage is rejected.

The final additive renderer seam accepts a separate two-rider art selection.
Only atlas loading and rider-frame validation consume it; current semantic
state continues to select palette/windows as well as camera, scroll, positions
and HUD. The original M3-02 renderer API delegates to the same implementation
without an override and remains source-compatible. The authored regression
renders one unsupported state after rolling and late-finish histories: with
both riders off-screen the frames are identical despite active effect tables
and a nonuniform palette; with riders visible, history-dependent differences
exist and are confined to the two rider rectangles. Canonical state remains
byte-identical.

An actual dummy-video, fixed continuous-right launch from frame 1533 through
3679 produced 2,145 redraws; two display iterations batched updates under the
unchanged scheduler. It used rider-pose fallback on 1,419 redraws and had
**zero identical consecutive fallback redraws while Racing** (longest such run
zero). Across all phases it had 383 identical redraws and a longest run of 228,
which the metric reports rather than misclassifying as the former race fallback
freeze. The round-2 exact-candidate launch report is
`artifacts/m3-03-r2-exact-continuous-right.json`; ignored artifacts are not
tracked. Its scheduler happened to render all 2,146 update iterations, used
fallback on 1,420 and retained zero identical fallback redraws while Racing.

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

### Correction-round-2 observations and decisions

Fresh re-review found two further integration boundaries. First, the initial
pose-field substitution changed 14,290 RGB channel bytes with both riders
off-screen because pose fields also select palette and window effects. Second,
argparse rejected the separated spelling `--timeout -inf` before the frontend
handler could emit its requested report. Hosted run `34699306504` also showed
that Ubuntu lacked the X11/Wayland development headers SDL requires to compile
a real desktop backend; macOS app-debug passed, while Linux app-debug failed at
configuration and the later Linux app checks did not run. These are observed
failures, not acceptance evidence.

The reversible decisions are the additive rider-art renderer input described
above; frontend-only normalization of a separated negative-infinity timeout
before generic argparse processing; and the bounded ephemeral Ubuntu X11
header preparation described in the dependency section. Subprocess tests cover
`nan`, `inf`, separated `-inf` and equals-form `-inf`, each requiring exit 3, a
failed report and a sentinel child that never starts. Other subcommands retain
the generic CLI parser unchanged. Hosted run `34700625467` subsequently passed
at handoff SHA `6b4ac12`: macOS passed app-debug build/test/help, and Ubuntu
passed bounded X11 preparation, app-debug build/test/help and the complete
app-sanitize step. That is the required hosted evidence rather than an
inference from local macOS builds.
