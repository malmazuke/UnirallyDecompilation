# R-0030 — M4-12 native capability trial (in progress)

No autonomous capability is accepted. The playable product remains DRAGSTER.

## Reference contract before whole-update tuning

The additive `tests/manifests/native/zoom-zoo-trial-primary.reference.json`
freezes end-1649 and all 200 updates through 1849. Its 394-byte projection
contains the established semantic movement layout (including actual original
transition rejection words projected to their binary fields), fifteen additional
words per rider and the opponent horizontal input byte. The added fields cover
reflection step/end/table base/pose override/completion/hold, drive-pose enable,
reflection air turns, direction latch, base velocity cap, synthesized brake,
rotation and jump inputs, and the wrong-direction counter. The controller is
Right on port zero through the full horizon; port one is neutral.

The first 333 bytes follow `prepare.py:canonical_seed` and
`movement.cpp:serialize_movement_state`, with the new `URZZ0001` identity and
actual frame number. This is a reference projection, not permission to accept
unvalidated native input. Runtime validation, serialization and restores are
still to be implemented. The native-only transient rejection placeholder in the
old seed writer is replaced by reads from `$0FD1/$0FD3` in the reference tool;
no expected byte is supplied by a native result or missing-input default.

`zoom_zoo_trial_reference.py` captures WRAM and cartridge RAM directly from two
fresh original processes. Every observed frame's whole-WRAM hash must match the
unchanged accepted primary replay. Both processes produce identical projections
with row digest `0588e60a73b79948567e1e5ec692e4cdf95cf9ee5a315905a9f556652e931568`.
The seed matches the complete original M4-04 WRAM and cartridge identities.
Original bytes, projected rows and traces remain ignored under `artifacts/m4-12`.
The tracked contract stores hashes and field/source metadata only.

## Dependency audit and pending closure

The two expanded access captures agree exactly. They cover every original
instruction from 1649 through 1849, including 3,679,052 instructions and
1,821,598 accesses. The ordered watches cover the accepted M4-11 surface plus
persistent-state neighborhoods and both displacement histories. No store is
unresolved, no watch is truncated and no memory resolution conflicts occur;
4,400 unresolved **reads** remain in the aggregate and require classification
before dependency closure can be claimed.

Dispatcher loads at `$82:89xx--8C2D` identify the prior-frame semantic fields.
Matched scratch stores and subsequent routine accesses distinguish persistence
from overwritten temporaries. `$0BC3`, for example, supplies a per-update
animation override that `$81:8681` clears before use; `$0E03`, conversely,
feeds the ongoing reflection counter at `$82:A3B3` and must persist. The
additional scoped mode/input guards in the reference tool are read directly
from the seed and remain unchanged over all 201 observed states. This is an
inventory and tested-domain observation, not yet proof of autonomous closure.

Static content uses the accepted ZOOM ZOO track/columns/flags/pose extraction,
identity-verified common DRAGSTER motion tables, and the 128-byte reflection
pose table at PAL `$82:A2DB` used by `$82:A447`. All seventeen files are bound
by byte length and SHA-256 in the additive contract. Future missing static
inputs require an explicit additive contract supplement before their tuning;
accepted identities must not be replaced.

The longer interval reaches opponent reflection and new recontacts at 1778
and 1823. The latter reaches a special tile/landing velocity transform absent
from the accepted short component. Full reference coverage is frozen at 1849;
it must not be shortened to avoid these branches.

## Early native component

`vertical_contact.*` ports the accepted direct/mirrored vertical preprocessing,
ordered signed-byte reduction and bounded continuous/sentinel response into
C++. It is separate from the accepted flat contact implementation. The probe
matches all eighteen motion/contact outputs on the 102 calls from 1650--1700.
This component uses captured incoming arguments in its research probe; it does
not demonstrate autonomous movement. The C++ port preceded the expanded whole-
update freeze but was compared only to the already-frozen short component.
No whole-update implementation or expanded native tuning preceded the freeze.

A first diagnostic compared a stale scratch duration after an unknown RMW and
reported a one-unit mismatch at 1650/opponent. Using the caller's publication
(the accepted evidence method) resolves it without native arithmetic changes.
Preserve that distinction when inspecting traces: unknown RMW values are not
observed output values.

## Reproduction at this checkpoint

- Expanded capture: exact argument arrays are in
  `artifacts/m4-12/expanded-primary-{a,b}/command.json`; these invoke the
  existing bounded `tools/project.py access capture` surface and preserve its
  original replay expectations. The source/watch recipe will be promoted into
  the trial tooling before review.
- Projection: `python3 -m tools.unirally_lab.native.zoom_zoo_trial_reference
  --access-dir artifacts/m4-12/expanded-primary-a
  --out artifacts/m4-12/reference-final-a.json` (fresh output required);
  repeat with the independent capture and output `b`, with a 90-second bound.
- Startup and early component commands/results are recorded in M4-12.

Independent variations, native autonomy, restore, full regressions, independent
Sol review, hosted CI and integration are outstanding.

## Static landing matrix supplement (before transform tuning)

The 1,512 bytes at WRAM `$0572--0B59` are three 63-angle coefficient matrices,
not a captured motion series. `$81:9A4D--9E12` builds them from ROM coefficient
words using signed fixed-point products. They first equal the final tables at
end-1297, before the first race update at 1377, and remain byte-identical at
**every** captured frame 1297--1849. The initialization capture confirms their
writers; the expanded movement capture contains no writer into the tables.
The additive `zoom-zoo-trial-landing-content.reference.json` freezes their
identity before implementing the landing transform. The main contract remains
unchanged.

Implementation decision: permit bounded original execution during extraction
of these pre-race immutable tables, as already permitted for the original seed
and reference laboratory. Native gameplay must never run that extractor or
open original state/ROM/core/captures. The extraction stops at 1297 and copies
only the declared static range; it does not provide post-seed state. A native
mathematical replacement for the initializer can follow if independently
verified; guessing fixed-point rounding now would weaken the evidence.

## Native review candidate: exact primary and dependency inventory

The primary now reproduces 200 consecutive updates (1650–1849) for both riders,
all 395 canonical bytes, from one end-1649 seed. Two new fresh original captures
have identical projected-row digest
`a0f39c3b22f9e5c5ca62331281126a2a4df6b8d712881ad910e4329015ab1947`.
The original 394-byte contract remains frozen; additive manifests bind immutable
landing content, the retained OAM seed byte, and excluded-mode guards. This is
candidate evidence, not task acceptance or a full-track claim.

| Future-affecting input | Native producer / authenticated source |
| --- | --- |
| Both motion/contact records, four residues, pose/history and idle oscillator | Original seed projection in `prepare.rider_seed`; native `integrate_zoom_axis`, `update_pose`, `update_idle_pose`, vertical contact. No per-frame import. |
| Throttle, jump, rolling, quarter turns, speed modifiers, progress | Reused semantic helpers plus `update_zoom_throttle`; caller order follows `$82:8Axx–92xx`. Phase-selected progress precedes limits/integration. |
| Reflection step/end/base/override/completion/hold/drive flag/air turns | Explicit extra words from the seed; `update_reflection_transition` (`$82:A35B–A49E`) and active pose control (`$82:A237–A287`). Air-turn clear follows `$82:9D7F`. Reflection's ordinary gate uses the inactive phase; player call precedes active functions, opponent follows rolling. |
| Controller axes and synthesized brake/rotation/jump words | `sample_controller` and `update_zoom_ai` (`$83:E082–E253`). Current native input domain is Right/neutral; no invented brake/trick mapping is exposed. |
| AI counters/selector, learned-feature value, queue/timer | Seeded canonical records; native AI, quarter-turn/reward and timer functions. Combined rotation/reward, nonzero landing orientation response and multi-axis AI tricks reject. |
| Base cap, direction latch, wrong-direction counter | Explicit per-rider seed fields and native active recurrence. Unrecovered wrong-direction reward rejects at its trigger. |
| Speed-decay screen predicate | Opponent `$150B` has no overlapping writer in complete primary accesses: retained seed byte 101 is serialized. Player boost is zero in the reference; native requires boost below 16, for which either optional 16-unit subtraction leaves it unchanged. No provisional screen value remains. Cases must retain the OAM invariant. |
| Geometry, collision poses, angle coefficients, landing matrices, reflection poses, animation/reward/decay tables | Identity-bound static inventory and reproducible extractor. Landing matrices are pre-race constants, not captured velocities. |
| Excluded mode/control guards, track masks, AI strength/adjustment, SRAM options | Original seed plus unchanged per-frame primary/reference guard checks; main and additive guard manifests. Native constants implement only those authenticated modes. A changed reference guard rejects the case. |
| Caller scratch, contact probes, multiply temporaries, phase-selected rider selector | Derived locally each update; no scratch dump is a native input. `$1003/1005` gate only audio commands after response-B publication and do not affect this gameplay projection. |

The audit distinguishes scratch from persistent words. For example `$11D7` is
the current rider's boost scratch; persistent rider boosts are `$11D9/$11DB`.
Reads of `$0359/$035B`, extra trick counters `$042F–0435`, AI mode `$0C6D`,
AI control `$0C73`, boost bonus `$0DED`, AI strength `$1275`, adjustment `$1281`
and `$1283` are guarded by the additive inventory. Source copy-in/copy-out paths
and the field map in `prepare.py` bind persistent state to semantic records.
No later captured dynamic input is passed to the native runner. Independent
review must scrutinize the bounded guard assumptions and the inventory itself.

The expanded interval adds opponent support/reacquisition at 1778, auxiliary
boundary contact at 1804, and the matrix landing at 1823 followed by boost tile
at 1824. The landing changes velocity `(-302,+286)` to `(-90,-182)`; the transform
uses the signed middle product before doubling (negative products round down).
The next boost update resets vertical velocity and adds 128 to horizontal
velocity before active damping/throttle. The auxiliary boundary path increments
only the low duration byte and retains both previous uncorrected coordinates.
ROM-free tests cover that width distinction, negative slope rounding, malformed
state/input, transactional rejection and altered static content.

`zoom_zoo_trial compare` passes the primary and fresh-process restores at 1700,
1804 and 1823 with extracted content. It copies only seed, static files and
controllers into a new native working directory. Native code neither links an
emulator nor reads the ROM/reference. Full acceptance still needs reviewer-owned
relevant variations, Sol approval and the final regression/CI/private-push matrix.

## Candidate regression evidence (`43198c6`)

Clean source reports bind commit `43198c6242ae2d55d025704522f947f88d2ed84e`;
no tracked source changed during either full suite. Each app preset passed 376
Python tests, 21 CTests and native fresh-process repeatability (400 checks total).
The experimental native primary and three restores also pass under ASan/UBSan.

| Gate | Result | Report SHA-256 |
| --- | --- | --- |
| `app-debug-clean-report.json` | 400 checks, passed | `84b5973312daea9b82a410d9fc5ab9ae03fb76fc7946469afea94c75cd90b64a` |
| `app-sanitize-report.json` | 400 checks, passed | `0defa9e28a8fd801eb1c9131d78b1401837331c314a4a9b648127f651eb22659` |
| `trial-primary-final-report.json` | 200 updates + 3 restores, passed | `80460e13b5b1dd5a888cdcdc6c57d7aeeea75b6a6619c1c7efdabd0862a3fcea` |
| `trial-primary-sanitize-report.json` | 200 updates + 3 restores, passed | `ac6298731b0f908c97cd0afac0dd99ba82ce4797aab33352fe4c5af8bf3a9dc0` |
| `regressions/zoom-contract.json` | 3 checks, passed | `b053a0077869ee41d96f866a76286abdef8af4c9e428849d7bfc110260207b67` |
| `regressions/pack.json` | 3 checks, passed | `ce1ab2663f0b2f1a154c1b51b70e36cfd40e0fb8303c8818a7bce6957cd42dff` |
| `regressions/finish/report.json` | 18 checks, passed | `9bb3f11e62ac8726ac6b2c1f1e28d0c2743d84c0587abdaa9c5c1b4b84fe94ae` |
| `regressions/opponent/report.json` | 12 checks, passed | `5154900681737f0f7acbaa2134277bd97d567328988ba4308ab3ff3b38949520` |
| `regressions/winner-visual/report.json` | 8 checks, passed | `3408d8df0e998a43568c593766f824a9c565a55e67211a7855f438b7a156fc12` |
| `regressions/loser-visual/report.json` | 2 checks, passed | `fe99892e49111df041680940943ba8493b4308d55a27a398c6e9e5af84601a5b` |
| `regressions/zoom-replay.json` | 24 checks, passed | `bc81584ad9dfcfb8eae4db09092d3a6c51f1ce7b9868bae5e7a07b8bb3e007e4` |

Exact regression argument arrays are preserved in
`artifacts/m4-12/regressions/commands-final.json`; each invokes
`python3 tools/project.py`. The full-race restore frames are 1600/3213/3453/3678;
opponent-first restores are 3213/3800. Frozen winner and loser presentation
contracts use their accepted fixture directories. Report inventory, source
identities and command arrays are in `artifacts/m4-12/validation-inventory.json`.

A first broad run failed 12 Python cases because top-level private-cache
symlinks resolved outside the checkout; CTests passed. Replacing only the
agent-created links with real directories and reusing caches beneath them
resolved the path-containment failures. No tests or expected values changed.
An initial native-regression invocation also rejected a report path outside its
fresh artifact directory; corrected commands keep each report inside that
directory. Neither preliminary attempt counts as a pass.

## Independent finding and correction

Reviewer preregistration `6c4a3b4` fixed two cases before native evaluation.
Neutral 1650–1660 then Right failed candidate `43198c6` first at 1661, with only
the player's wrong-direction counter one too high. `$82:971A–9725` clears the
counter when velocity is in `[-16,16)` before testing marker/input direction;
that guard was omitted. `next_wrong_direction_counter` now preserves the exact
wrapped comparisons, and ROM-free tests distinguish -17/-16/+15/+16. The
corrected candidate passes primary, that now-tuned regression and the original
passing neutral-1818–1826 case, each for 200 updates plus three restores. The
failed case is no longer counted as withheld; a fresh reviewer-owned case is
required before approval. Independent review and final CI are still pending.
