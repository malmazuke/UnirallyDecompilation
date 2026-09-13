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
