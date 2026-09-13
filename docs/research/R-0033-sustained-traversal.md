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
`reward-access` (2706–2709). One lean whole-horizon access audit aggregates
read/write sites without watched-instruction logs; completeness assessment is
pending. The full WRAM projection allows additional fields to be frozen before
any further native tuning if that audit or review identifies an omission.

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

## Initial candidate status

Primary all 423 bytes through 3299 and fresh-process restores pass. Focused
21 CTests and six tooling tests pass after correcting an authored-test variable
name compilation error. M4-12 and M4-13 primary comparisons/restores pass.
A prior ceiling experiment also failed compilation on signedness; neither failed
build was counted as a pass. Independent review, complete source/constant audit,
autonomy negatives and final broad/integration gates remain required.

M4 remains incomplete. Frontend, presentation, audio, other scenarios and full
race support are not claimed. Hosted Linux synthetic checks and private Linux
differential execution are distinct; the latter remains unverified.
