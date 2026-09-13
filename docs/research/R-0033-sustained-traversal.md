# R-0033 — Sustained native ZOOM ZOO traversal

## Frozen domain and observations

M4-14 retains authentic end-1649, original pre-seed controller history, continuous
Right for player and neutral controller 1, through 3299 (1,650 updates). ROM
SHA-256 `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`
and pinned core identity are unchanged from R-0030. Commit `5806ab0` freezes
repeat-matching original WRAM hashes and initial 423-byte inventory before tuning.
The original 395-byte prefix remains intact apart from the new `URZZ0002` magic;
seven appended words per rider retain surface mode, its angle, `$0B9B`, leading
support, `$0DE3`, animation override and `$0E8F`. Existing `URZZ0001` remains 395
bytes and retains its old horizon. No old expectation was replaced.

The player first lands at 1991, with leading support and inverted vertical
geometry; mode enters at 1992 and exits at 1993, then repeatedly re-enters.
`$0B93` is a tile-selected surface behavior, not an established crash/tumble
label. The task froze recovery as a full landing after mode entry/exit, nonzero
horizontal velocity and positive progress-count change since entry, followed by
200 further traversal updates. First recovery is 2185, leaving 1,114 updates.
The scenario repeatedly returns to the same section. This criterion does not
claim monotonic progress, obstacle clearance or full-race completion.

Primary reference rows SHA-256 is
`dce7c14b80c66e4bd831cff3733c6cba02d1c4c40cefd96ae2760bf6d4fa74de`.
Fresh supplemental captures preserve every frozen state and WRAM hash while
also checking the constant-input inventory. Private files are in the M4-14 task
checkout's `artifacts/m4-14/primary-{e,f}.json`; earlier exploratory captures and
full WRAM remain there for audit. Captured dynamic inputs to native runtime: zero.

## Recovered producers and ordering

| Producer | Source and recovered behavior |
| --- | --- |
| Contact probe preprocessing | `$81:8BE3–8CE9`: inverted vertical local-Y complement, horizontal axis swap, mirrored columns and explicit correction directions. Sampling remains the existing authenticated static geometry. |
| Ordered reducer/correction | `$81:8FEF–9132`, `$81:97E4–9829`: leading-probe selection, separate horizontal and vertical penetration, ties, conditional preservation of previous uncorrected Y and signed axis correction. `$81:8DDC` persists leading support to `$0BAB`. |
| Steep contact | `$81:9278–92AD`, `$81:9697–97E4`: 31-unit airborne endpoint, 26–30 response branches, 28-unit vertical-to-horizontal conversion. Both ordinary and mode-selected 32-byte shift/multiplier pairs are independently extracted from the ROM. |
| Landing | `$81:924E–9275` clamps incoming horizontal velocity into an inverted face. `$81:931C–9477` handles low displacement, reflected pose, response decay and long airtime. `$81:992B–996F` adjusts matrix selection for leading support. Integer width, signed shifts and matrix coefficient ordering are preserved. |
| Surface lifecycle | `$81:8592–8678` clears per-update modes after mode-sensitive idle decay; `$81:84EC–8553` applies tile-6 drive/damping and records current surface angle. `$82:A6DC–A6ED` changes position bias in that mode. |
| Pose/control | `$83:EF67–F005` selects inverted pose-table half and adds mode angle. `$82:A288–A2D7` makes inverted support rolling and suppresses ordinary rolling in surface mode. `$82:A9C1–AA3D` follows existing velocity direction on inverted tiles. Leading support suppresses throttle/idle and triggers landing bookkeeping even on the inactive phase. |
| Leading landing event | `$82:9B87–9BBD` enqueues event 14 and clears boost when completed turns meet leading support. `$81:C241–C249` authenticates its class `255`, bypassing learned-feature/boost rewards while preserving queue/cooldown processing. |

The native code remains in `movement.cpp`, `vertical_contact.cpp` and the
small `SurfaceTransition` record in `zoom_zoo_movement.hpp`. New static inputs
are additive files; old content identities remain unchanged. Each input's ROM
offset/hash and the constant input guards have tracked manifests.

Targeted complete instruction/access windows are `entry-access` (1989–1994),
`steep-access` (1853–1855), `mode-followup-access` (2021–2025),
`horizontal-access` (2042–2052), `long-airtime-access` (2190–2193) and
`continuous-reward-access` (2706–2709). The original `reward-access` and
`full-read-audit` followed the legacy manifest's Up pulse at 2200–2259; they are
not continuous-Right evidence. The corrected `continuous-read-audit` removes
that pulse while preserving the pre-seed history. Every whole-WRAM sample in
both corrected captures agrees with the frozen primary, all 1,651 states.

The complete aggregate covers 30,355,912 instructions, maximum 18,777 per frame
against ring capacity 262,144; no unresolved stores, non-ROM PCs, resolution
conflicts or dropped resolutions. There are 38,455 unresolved reads across all
subsystems, but zero in the recovered producer regions (listed in the private
`dependency-audit.json`). DMA/HDMA is not instruction execution and this is not
a presentation/audio completeness claim. Access SHA-256:
`923547855a6a305711c84afcfc107a361d387202949e4ab62e8fc271ba94edf0`.

The newly reached read sites, compared with M4-13, close as follows:

| Reads | State/input disposition |
| --- | --- |
| `$8184EE–854D` surface behavior | Existing selected descriptor, surface angle and velocity plus appended surface mode/angle; working `$0Fxx` copies are rebuilt in update order. |
| `$818C14–8C81`, `$818FF9–9126` probes | Authenticated columns/flags and collision points; local probe scratch is produced inside the update, with leading support persisted in the appended state. |
| `$819260–99B1` steep/landing paths | Existing position, previous uncorrected position, velocity, airtime, pose and response fields; local angle/matrix scratch is rebuilt. Six newly reached coefficient read sites use the additive four-table ROM extraction. |
| `$829B17–9BA6` quarter/leading reward | Existing serialized quarter counts, air turns, boost, reward queue and cooldown; additive event-14 value/class tables. |
| `$82A41C`, `$82A9C9–AA33`, `$83EFCF/F01C` | Existing response, velocity, controller and pose fields, plus appended mode angle. |
| `$82A74C` reads `$1513` | Camera byte cannot affect the reached branch: player boost is below 16 throughout; native rejects a boost reaching 16. Existing opponent retained `$150B` remains serialized and constant-checked. |
| `$818233–828E`, `$828907/8912` | Audio/presentation bookkeeping outside the recovered simulation; no new future simulation input is inferred from these output-side reads. |

The constant manifest authenticates omitted branch guards on every captured
state for primary and review cases. Dynamic producer outputs are serialized or
rebuilt from the seed/static inputs inside each update; no new untracked dynamic
input was identified by this audit. The conclusion is bounded to these captures.

## Independent review corrections

The review's neutral 2037–2052 / B 2053–2067 case first diverged at 2076:
player horizontal velocity expected 48, native 7. An authentic case-specific
2074–2077 access window (all whole-WRAM samples match the review freeze) shows
`$8192FE–9309` sends a full 28-unit landing directly to correction. The native
continued-contact conversion was incorrectly applied afterward. It now applies
only before full airtime saturation; a focused branch test preserves velocity
and clears airtime. The failed case remains a disclosed regression and passes
all states/restores after the correction; it cannot replace fresh review evidence.
Review also found missing malformed-state validation for appended binary flags.
Both riders' five binary fields now reject values above one, with corruption
checks. No reference expectations were changed.

## Reproduction

Use real local/artifacts directories and verified cache links per
BUILD_AND_VALIDATION. Obtain CORE from an authenticated prior samples.json.
Each original/extraction child uses a 180-second timeout; native children 30.
Each output must be fresh. The primary case defaults to continuous Right.

```sh
python3 tools/project.py build --preset app-debug
python3 -m tools.unirally_lab.native.zoom_zoo_sustained extract-content --core "$CORE" --out artifacts/m4-14/fresh-content
python3 -m tools.unirally_lab.native.zoom_zoo_sustained capture --core "$CORE" --out artifacts/m4-14/fresh-a.json
python3 -m tools.unirally_lab.native.zoom_zoo_sustained capture --core "$CORE" --out artifacts/m4-14/fresh-b.json
python3 -m tools.unirally_lab.native.zoom_zoo_sustained compare --reference artifacts/m4-14/fresh-a.json --repeat artifacts/m4-14/fresh-b.json --contract tests/manifests/native/zoom-zoo-sustained-primary.freeze.json --binary build/app-debug/src/core/zoom_zoo_runner --content-dir artifacts/m4-14/fresh-content --out artifacts/m4-14/fresh-report.json
```

For independent variations, preregister `id`/`changes` JSON, use `capture --case`
in both fresh processes, and run `freeze --reference A --repeat B --out CONTRACT`
before candidate evaluation. Changes replace controller 0 over inclusive frames;
Right resumes afterward. `--horizon H` can extend the same reference scenario to
9999 when recovery needs it. The harness rejects cases lacking recovery plus
200 updates. Such exploration is not acceptance of every frame/input to 9999.
Comparison checks every byte twice, then restores around every full landing of
both riders, initial/late surface transitions and a later traversal boundary.

## Validation and acceptance status

Primary all 423 bytes through 3299 and fresh-process restores pass. Fresh
Sol/medium review approved corrected candidate `e730aaa` in `ec543c52`, with
one fresh replacement after the disclosed 2076 failure and the retained passing
late variation. Both are material, frozen before evaluation and reach 3299.
The fresh replacement passes 96 restores; review explicitly accepts the frozen
local recovery criterion without implying monotonic/full-track progress.

App-debug and app-sanitize each pass 403 checks with no skips. Each also passes
all four M4-12 cases, all five M4-13 cases and sustained primary/retained cases
with restores. Frozen content/replay, DRAGSTER finish/opponent-first and both
presentation gates pass. Fresh extraction reproduces all static identities;
corrected native runs with repository and ROM access denied, with independent
negative controls and a missing-static-file failure. Exact local commands are
in `artifacts/m4-14/final-gates` and `regression-matrix`.

Early authored-test/signedness builds and the first malformed exploratory audit
manifest failed and were corrected; these failures were not counted as passes.
Acceptance remains conditional on the merged checks and exact private remote/CI
results in `artifacts/m4-14-integration/closeout.json`, per the consolidated task
handoff. This avoids a second documentation-only CI push.

M4 remains incomplete. Frontend, presentation, audio, other scenarios and full
race support are not claimed. Hosted Linux synthetic checks and private Linux
differential execution are distinct; the latter remains unverified.
