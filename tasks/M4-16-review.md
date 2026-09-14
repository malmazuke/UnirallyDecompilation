# M4-16 initial independent review

## Scope and candidate

This is the required initial review of the **unaccepted** product candidate
`84dfa40db896e317022631e66d31b977fda8fbad` in the detached isolated checkout
`.worktrees/m4-16-review`. It is not final acceptance and intentionally does not
run broad, sanitizer, merge or CI suites. The primary remains responsible for
implementation and final evidence; this checkout contains no implementation
fixes.

Review started with shared weekly usage reported as 64% used versus 57% at task
startup. The final 20% review/recovery reserve remains intact. No reset,
purchase, provider switch, child dispatch, push or integration occurred.

The candidate and its task record already disclose incomplete ordinary
brake/trick controls, result/next-race producer inventory, restart/reference and
negative controls, independent cases, frozen visual contracts, live full-race
evidence and broad gates. The findings below identify concrete defects in the
implemented state contract and evidence harness rather than counting those
listed gates again.

## Findings

1. **Required correction — URZZ0005 admits impossible initializer phases that
   affect the next update.** `deserialize_zoom_zoo` validates `fade_level`,
   `start_boost` and `result_updates` separately, but does not validate their
   relationship with frame/countdown and race phase
   (`src/core/movement.cpp:1268-1274`). Starting from the authentic native frame
   1376 state, changing bytes 565-566 from fade 0 to fade 30 leaves countdown
   270 and both start boosts 384. The exact candidate accepts this state. One
   neutral update immediately decrements countdown, whereas the valid state
   first increments fade and retains countdown; the resulting state hashes are
   `aa551364...` and `98a6531c...`. This is a state the initializer cannot
   produce, and it changes future timing. Require phase relations for the
   initialization interval, including the reached fade/countdown/frame relation
   and start-boost availability/consumption, or encode a phase that makes those
   relations explicit. Add URZZ0005 malformed mutations and verify rejected
   operations preserve the caller's input state where that API contract applies.

2. **Required correction — malformed result restores can change the winner and
   graph.** The decoder does not validate completed lap-slot structure or the
   relationship between lap times and totals. From the authentic fully visible
   result state at frame 6839, changing player total bytes 507-508 from 9802 to
   60000 is accepted by both `zoom_zoo_runner` and
   `zoom_zoo_presentation_runner`; changing the first three player lap slots at
   bytes 467-472 to sentinels is also accepted. The valid, wrong-total and
   missing-laps renders have distinct PPM SHA-256 values `c1d2cffe...`,
   `9f9eb356...` and `a4cec35f...`; the first corruption changes the displayed
   outcome and the second changes the result graph. For this fixed three-lap
   scenario, enforce the reached completed-slot/sentinel ordering, total from
   the completed laps, and result-phase finish implications. The focused native
   test at candidate `84dfa40` exercises only the older serialized formats, so
   its pass does not cover either new malformed-state class.

3. **Required evidence correction — the playable comparator manufactures its
   post-load expected rows.** After original result loading begins,
   `tools/unirally_lab/native/zoom_zoo_playable.py:47-53` copies the last race
   archive, advances only frame/result count, and checks only SRAM lap/total
   bytes 467-510. It then compares native output with those manufactured rows
   and can report one `rows_sha256` and `status=passed` over frames 1376-7600.
   That result does not establish that any other post-load state was inventoried
   or recovered. This representation can be a valid product-level result model,
   but its report must distinguish exact race projection from semantic result
   phase and cannot support the task's complete future-state claim until a
   source-backed result/next-action inventory proves which state is future
   relevant. Include negative controls that mutate an omitted result producer
   and the displayed outcome/graph inputs.

4. **Required presentation correction for this candidate — rider art is below
   the accepted DRAGSTER behavior.** `render_zoom_zoo` overwrites both pose
   indices with `0x04f9/0x0263` and forces both reflections true on every frame
   (`src/core/presentation.cpp:990-997`). Position changes remain visible, but
   direction reversals, jumps and pose changes are not represented. This is
   weaker than DRAGSTER's recovered-pose/last-recovered fallback and cannot show
   the requested direction and jump response in the live presentation. The
   primary has separately reported replacing this after `84dfa40`; final review
   must inspect the replacement and its fallback metrics.

## Result and restart assessment

The original result video becomes fully bright at 6839, but it is not a frozen
image: authenticated primary video hashes at 6839/6840 agree, while frames 6900,
7000, 7100 and 7199 all differ. The contract's `stable_result` name is therefore
a phase label derived as `first_visible + 6`, not a tested pixel-stability fact.
Final evidence should call it fully visible or inventory the continuing result
animation before claiming stable visual output. Candidate native rendering
saturates `result_updates` at 115 and then remains static.

The product's explicit **Race Again** action is a defensible restart design.
Authenticated original Start after the result advances tour progression to
STUNT, so it is not an original ZOOM ZOO restart oracle. Reconstructing the same
one-player MIKE/BRONSEN CRAWLER/ZOOM ZOO scenario with
`classic_crawler_zoom_zoo_start`, assigning the whole state, and clearing input
avoids stale race fields. Acceptance still needs to compare the restarted state
with a separate fresh native initialization and continue both with the same
nontrivial controller prefix. The current playable comparator never invokes the
frontend restart and therefore cannot establish that property.

## Preregistered final-candidate variations

These two cases were chosen from the frozen primary timeline without running an
original or native candidate. They must remain untuned until a final candidate
is frozen. If an original case does not complete, retain it as a nonqualifier
and preregister a fresh replacement before native evaluation.

1. `m4-16-review-mid-race-brake-before-reversal`: override frames 3388-3403
   with `[left,y]`, then resume the primary timeline. This adds sixteen updates
   of braking during the long lap-two left segment immediately before its 3409
   reversal. It is distinct from the producer's late 6400-6410 loss case and
   pre-start charge case and exercises brake/contact/throttle ordering while the
   race remains live.
2. `m4-16-review-airborne-rotation-jump`: override frames 1681-1695 with
   `[left,b,r]`, then resume the primary timeline. This combines the primary
   route direction with a jump and positive shoulder rotation in the first-lap
   airborne window. The added rotation makes it materially different from the
   previously tuned B-only landing case.

## Focused commands and results

- `tools/project.py bootstrap --report artifacts/m4-16-review/bootstrap.json`:
  passed, isolated CMake 3.31.10 and Ninja 1.13.2.
- `tools/project.py build --preset app-debug --report
  artifacts/m4-16-review/build.json`: passed configure/build for exact detached
  candidate.
- `ctest --test-dir build/app-debug -R
  'zoom_zoo_trial|content_pack' --output-on-failure`: 2/2 passed
  (`classic_content_pack_identity_rejection` and
  `zoom_zoo_trial_width_state_and_guards`). The content test constructs only the
  legacy 25-entry pack; the exact local 46-entry pack was independently opened
  by the mutation runs through both new runners, but comprehensive extraction
  and corrupt-pack negatives remain for the final candidate.
- A temporary binary mutation runner invoked exact candidate
  `build/app-debug/src/core/zoom_zoo_runner` against the read-only local pack
  `5bd961f6...`. The valid/impossible initializer pair both exited zero and
  diverged on the first continuation update as described in finding 1.
- A second temporary mutation run invoked both exact candidate runners for the
  valid, wrong-total and missing-lap frame-6839 states. All six invocations
  exited zero and produced the distinct render hashes in finding 2.
- Read-only inspection of `artifacts/m4-16/result-audit` found an authenticated
  6725-7200 access capture with 6,770,790 instructions and zero unresolved
  stores, but no completed producer-to-semantic-state inventory. Read-only
  `restart-explore` confirms that post-result Start changes WRAM/SRAM and later
  reaches STUNT, consistent with the task's recorded exclusion.

## Disposition

Reject `84dfa40` as expected for an initial unaccepted candidate. Correct the
two malformed-state classes and the result harness claim before broad suites.
Re-review the updated result inventory, restart differential and DRAGSTER-style
rider fallback on an exact frozen candidate. Do not evaluate the preregistered
controller cases until that candidate is frozen.

## Targeted re-review — candidate 6c1d5ef

Targeted re-review used frozen candidate
`6c1d5effe3ee3f9a392e29eb1ce40800dbdd889e` in the same detached isolated
checkout. Shared weekly usage was reported as 67% used; the 20% final reserve
remains intact. This was a focused correction review while the primary's full
immutable start/result/restart run continued. No broad suites, preregistered
case evaluation, child dispatch, reset, purchase, push or integration occurred.

### Correction assessment

- The original impossible fade/countdown mutation now rejects with
  `inconsistent ZOOM ZOO countdown/fade phase`. The decoder derives the reached
  fade and countdown from the serialized frame, and it constrains unconsumed
  start boosts in the early countdown.
- The completed-lap slot, total-time and new result-publication mutations all
  reject. In an authentic primary result, original and native publication bytes
  agree exactly: update105/frame6829 is all zero; update106/frame6830 publishes
  graph minimum/maximum `0c10/0cd8`; update107/frame6831 additionally publishes
  totals `264a/2652`; all eight bytes remain unchanged through frame7600.
- `--restart-from` on the authentic frame7600 state deserializes in a fresh
  process, calls the shared `restart_zoom_zoo` operation, emits an exact copy of
  the original native frame1376 state, and accepted a neutral 1377-1379
  continuation. The comparator now requires the entire second race to equal a
  clean native start. Early restart is rejected before mutation in the authored
  core test.
- Live ZOOM ZOO now uses the same recovered-pair/last-recovered-pair policy as
  DRAGSTER and resets its cached presentation pair at restart. The renderer also
  applies the original prior-update fade rule. This resolves the fixed reflected
  poses in the reviewed candidate at the design level; final visible evidence
  and fallback metrics remain required.

### Remaining finding

5. **Required correction — result/finish phase can still be transplanted onto
   the initialization clock.** The new checks relate fade/countdown to frame and
   result publications to `result_updates`, but only require nonzero result
   updates to have `finish_delay == 240` (`src/core/movement.cpp:1295-1323`).
   They do not require a finished/result phase to have completed the countdown
   and fade.

   Starting with the authentic V6 frame7600 state, the review retained its
   finished riders, lap archive and `finish_delay=240`, then changed frame to
   1376, countdown to270, fade to0, start boosts to384/384, result updates to1,
   and the not-yet-published result words to zero. Every individually checked
   relation passes. Exact candidate `zoom_zoo_runner --seed` exits zero, emits
   the impossible result at frame1376, and advances it on the next update. This
   can never be produced by the native initializer and bypasses racing from the
   initial frame. Require `finish_delay == 240` or `result_updates > 0` to imply
   countdown zero and completed fade (plus any stronger reached phase relation
   supported by the frozen domain). Add the mutation to the URZZ0006 test.

### Result abstraction and restart boundary

URZZ0006 materially improves the result claim. Before result loading, 571 bytes
remain the exact original race projection. After loading, those bytes are
explicitly an archived final race whose lap/totals are checked against surviving
SRAM; eight appended bytes are actual original graph and displayed-total
publications; the two-byte load counter is explicitly semantic. The report's
`comparison_domains` now makes this distinction rather than presenting the
whole post-load row as original state.

For the chosen product flow this abstraction is defensible once the remaining
phase mutation and producer inventory are closed. The native result renderer
consumes archived lap slots plus the eight authenticated publications, and the
only supported next action discards the archive through a complete fresh-scenario
restart. Original tour selection and its transition to STUNT remain expressly
excluded. This supports a bounded product-state equivalence claim, not byte-exact
equivalence to overwritten original result WRAM. Continuing original result
animation and visual contracts still need their separately declared presentation
evidence.

### Focused re-review commands

- `git switch --detach 6c1d5ef` and `git rev-parse HEAD`: exact candidate
  `6c1d5effe3ee3f9a392e29eb1ce40800dbdd889e`.
- `tools/project.py build --preset app-debug --report
  artifacts/m4-16-review/rereview-build.json`: passed. Reviewed runner SHA-256
  was `dc45bd7d...`; presentation runner was `aa24ee75...`.
- `ctest --test-dir build/app-debug -R
  'zoom_zoo_trial|frontend_contract' --output-on-failure`: the selected
  `zoom_zoo_trial_width_state_and_guards` test passed; no test name matched the
  second expression.
- Temporary mutations of authentic V6 primary state exercised lap slot467,
  total507, graph573/575 and published total577. All rejected; the error was
  either inconsistent completed slots or inconsistent result publication.
- `zoom_zoo_runner --restart-from` on the authentic frame7600 V6 state emitted
  exact fresh state and frames1377-1379. The cross-phase mutation in finding 5
  was accepted by `--seed` and rejected by `--restart-from` only because its
  result count was below the restart gate.

### Targeted disposition

Do not approve `6c1d5ef` yet. Findings 1, 2 and 4 are corrected, finding 3 now
has a defensible explicitly bounded abstraction, and the native restart boundary
is substantially stronger. Correct finding 5, finish the source-backed result
inventory, and re-run the affected focused gate before final-candidate review.
The two preregistered controller variations remain untuned and unevaluated.

## Final-candidate review — candidate 4f8aaad

This review used exact detached candidate
`4f8aaada48a326eefacad264b5de3beebc0ada50`. The candidate built cleanly and
the focused `zoom_zoo_trial_width_state_and_guards` test passed. This remains a
task acceptance review: no implementation was changed here, and broad suites,
merge, CI, push and milestone approval remain with the primary.

### Independent controller cases

The two preregistered cases were captured on the original twice before any
native evaluation of each case.

- `m4-16-review-airborne-rotation-jump` overlays frames 1681–1695 with
  `[left,b,r]`. Both original runs were identical and completed: player/opponent
  finishes were 6483/6488, result loading was 6724, first visible result was
  6832 and the fully visible result boundary was 6838. Its frozen 632-byte
  contract has rows SHA-256 `71392af5...`. Exact candidate comparison passed all
  6,225 states from 1376 through 7600, 480 fresh-process restore points,
  a second clean native initialization, and the full restarted race.
- `m4-16-review-mid-race-brake-before-reversal` overlays frames 3388–3403 with
  `[left,y]`. Two original runs were deterministic, but it did not qualify at
  7600. Two further original-only runs through frame 10000 show a route failure,
  rather than a delayed finish: the opponent finishes at 6488 while the player
  remains at two laps remaining, checkpoint 2, next checkpoint 3, with no finish
  through 10000. The freeze correctly rejects `case must finish both riders`.
  The case and captures are retained as preregistered evidence and were never
  evaluated on native code.
- Following the preregistered replacement rule, I chose
  `m4-16-review-short-mid-race-brake-before-reversal` before native evaluation.
  It retains the material left-plus-Y moving brake at the same lap-two boundary
  but limits it to frames 3388–3395. The two original runs were identical and
  completed at 6481/6488, loaded at 6722, and reached the fully visible result
  boundary at 6836. Its frozen rows SHA-256 is `78bc9241...`. Exact candidate
  comparison passed all 6,225 updates, 476 restore points, repeated clean
  initialization, and the complete restarted race.

### State, result and source assessment

The URZZ0008 corrections resolve the review's state findings. The authored
cross-phase mutation now rejects, and focused exact-result mutations of graph
minimum, published total, either charge flag, queue cursors, cooldown, reward
weight, hint enable/tick/group and empty-display flag all exited 1 with the
appropriate publication, charge or announcement-state error. The independent
case comparisons also restore from initialization, racing, finish, loading,
fully visible result and final state, then restart from the final serialized
state in a fresh process and compare the entire new race with clean native
initialization.

The result abstraction is defensible for the declared fresh-scenario product
flow. Before loading, 622 bytes are original projections. After loading, those
bytes are explicitly the final-race archive, while eight result publication
bytes remain independently projected from original SRAM and the last two bytes
are a semantic loading clock. Rendering consumes the archived lap slots and the
eight publications; the only next action replaces the whole state through the
shared clean restart. This does not claim equivalence to overwritten original
result WRAM or original tour progression. `stable_result` in reports denotes the
fully visible boundary; original result animation continues changing afterward.

The source audit is adequate for the reached event-one producer. The read-only
`trick-long-audit` authenticates 6,394 whole-WRAM frames and its focused
1718–1785 instruction/access capture reports zero unresolved store PCs. The
implemented queue, hint, cooldown and boost paths cite the reached producers at
`$81C598-C5C8`, `$81BEA8-BEF1`, `$81C0CE-C18A`, `$81C02A-C054` and
`$83CDBC-CE43`. This evidence does not establish general multi-event rotations;
the implementation correctly keeps unrecovered reward classes outside its
claim.

### Presentation and acceptance finding

The current race scene is readable and materially improved from the initial
candidate. At frame 3208 the native renderer places the same checker line,
curved green/blue/yellow track, tiled background and both riders in the current
camera scene as the original capture. Live rendering now follows DRAGSTER's
recovered-pair/last-recovered-pair policy and resets that cache on restart, so
its art fallback is no worse than the accepted DRAGSTER design. The headless
renderer's fixed pair is only its fallback when no live art pair is supplied.

**Acceptance blocker:** candidate `4f8aaad` is still not an acceptable M4-16
product completion. The tracked visual contract itself remains marked pending;
the native result is an authored legible layout rather than the original result
art; required both-outcome screenshots and representative visual checks are not
present. More decisively, there is no visible actual-app complete race through
result and restart, nor the required independent live-control exercise. The app
still throws on A/X/Up/Down/Select/Start during racing, and the task has not
shown that those guarded controls are outside ordinary supported play. Headless
byte equality and scripted restart cannot substitute for acceptance items 5 and
6. Keep this candidate unaccepted until the primary supplies the live and visual
evidence and either recovers those ordinary controls or narrows them with
source-backed evidence.

### Focused commands and results

- `tools/project.py build --preset app-debug --report
  artifacts/m4-16-review/candidate-4f8aaad-build.json`: passed on the exact
  candidate; runner SHA-256 `ffde80ce...`, pack SHA-256 `5bd961f6...`.
- Four original-only 7600-horizon captures plus two 10000-horizon extensions
  used `tools.unirally_lab.native.zoom_zoo_playable_reference capture --case`.
  Each repeated pair was identical.
- `tools.unirally_lab.native.zoom_zoo_playable freeze` rejected the long brake
  case at both horizons and froze the two completing cases before native use.
- `tools.unirally_lab.native.zoom_zoo_playable compare` passed the airborne and
  replacement brake contracts with 480 and 476 restore boundaries respectively,
  including each complete fresh restart race.
- `ctest --test-dir build/app-debug -R
  'zoom_zoo_trial|zoom_zoo_runner|presentation_contract' --output-on-failure`:
  the selected `zoom_zoo_trial_width_state_and_guards` test passed; no other test
  name matched the expression.

### Disposition

The state, result, restart, producer-closure and deterministic independent-case
corrections pass this review. Do not accept M4-16 at `4f8aaad`: the required live
full-race/result/restart review and final visual evidence are still absent, and
ordinary guarded controls remain unresolved as a product boundary.
