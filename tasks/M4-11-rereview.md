# M4-11 focused independent re-review

- Corrected candidate: `9d9e582c12c9e573cdabadb76d270be580ba81ac`
- Correction commits in this worktree: `554d8ec` (semantic enforcement) and
  `9d9e582` (evidence record), following original review `b7a8db9`
- Verdict: **approved without a remaining material finding**

## Returned finding

The correction closes the semantic-enforcement defect returned in the first
review. I inspected the correction and reran the original reviewer harness on
the unchanged private frame-1674 capture, rebinding each mutated document as a
fresh private capture identity so rejection did not depend on the worker's
fixed access SHA-256. All seven original contradictions now reject:

- wrong frame-1650 `$83:F00D` pose-consumed response-B value;
- byte-width motion scratch load;
- byte-width motion persistent publication;
- byte-width contact scratch load;
- byte-width contact persistent publication;
- cap consumption reordered before gravity publication; and
- an additional same-value, otherwise unclassified `$0FAB` motion writer.

The correction requires one complete width-two `$83:F00D` read from `$0F57`
per call, equal to computed response B, and hashes `pose_consumed` in all 102
response rows. It requires width two on all seven motion/contact boundary
events. Its event validator binds the exact jump, gravity, cap/boost,
integration, motion publication, contact-response and final-publication
sequence rather than accepting coincident values in a different order.

Freshly rebound writer mutations also reject at the intended semantic checks:
missing and distinct-sequence duplicate gravity writers; missing and
distinct-sequence duplicate `$81:970B` contact-response writers; an
unclassified writer inside the motion interval; and an unclassified writer
outside both riders' classified intervals. The access format deduplicates an
identical tuple with the same execution sequence, so duplicate-execution tests
use a distinct sequence, as an actual second writer would. The per-frame domain
check reconciles every write overlapping `$0FAB` against the two riders'
classified writer lists exactly once.

No source capture was regenerated and no captured arithmetic expectation was
changed. The only manifest changes are the evidence-row hashes and the added
observed contact-response writer count required by the stronger semantics.

## Exact recurrence and private evidence

The original primary and worker frame-1672 captures still verify exactly from
the single end-1649 seed with no later captured vertical velocity as input.
They retain 102 calls, 1,020 sample words/source offsets, final velocity player
241/opponent 0, final response B zero/zero, and the accepted final position and
residue words. Corrected exact report SHA-256 values reproduce the worker
record:

- primary: `de4cbfbe06b4969e4bb1b3077ca8c6e570f4660a1e8233efc42ab8920c751892`;
- worker variation:
  `69655d09714221dd83e46705bf4e08bcb7acb833a9c52c4f97d9e28af519739c`;
- comparison:
  `1ab5bec0b81f857781a7ab7a38dd8f4fee4941d73f5b3ea6121fb257769e905b`.

Both already-captured reviewer frame-1674 records remain byte-identical at
access SHA-256
`b682aeaa34856c898c25cc4a4447da20bf296591610e97879bb16a1dc76dbb01`.
Each independently passes the corrected 102-row evaluator. All 102 pose reads
equal their computed response-B values. The strengthened private row digest is
`2db565428fb7a55d355979ec31853f067969c5966ddabeb3893758d25dc251ac`
and its response-B evidence digest is
`00784c4f7615b33be831bb02d90095e44e5ec487941cccef30db3ff9d663a9d7`.
Its 73 contact-response writers are all classified; the remaining contact
paths preserve velocity.

The private arithmetic and observed relevance are unchanged: gravity has 24
negative and 78 nonnegative inputs, final velocity is player 241/opponent 0,
sample/source digests remain `7cb3af73...6e63` and `36a78f08...896`, and final
position/residue remains player `(9824,1605,9,15)` and opponent
`(7489,1520,-4,12)`. There is no later captured-velocity field in the recurrent
row schema; captured motion/contact values remain comparison targets.

## Checks run

```sh
python3 local/review/m4-11-vertical-velocity-review/adversarial.py
# 37/37 general adversarial checks pass; all seven original semantic
# contradictions now reject.

# Fresh rebound access mutations, run from an ignored one-off harness:
# missing/duplicate gravity, missing/duplicate contact response,
# unclassified in-interval and unclassified out-of-interval writers all reject.

python3 -m unittest tests.tooling.test_zoom_zoo_position \
  tests.tooling.test_zoom_zoo_contact \
  tests.tooling.test_zoom_zoo_vertical_contact \
  tests.tooling.test_zoom_zoo_reflected_vertical_contact \
  tests.tooling.test_zoom_zoo_composition \
  tests.tooling.test_zoom_zoo_response_b \
  tests.tooling.test_zoom_zoo_vertical_velocity -v
# 60/60 passed.

python3 -m tools.unirally_lab.native.zoom_zoo_vertical_velocity verify \
  --access <unchanged-primary-access> --content <unchanged-content> \
  --manifest tests/manifests/native/zoom-zoo-vertical-velocity-primary.reference.json \
  --report <ignored-primary-report>
python3 -m tools.unirally_lab.native.zoom_zoo_vertical_velocity verify \
  --access <unchanged-worker-variation-access> --content <unchanged-content> \
  --manifest tests/manifests/native/zoom-zoo-vertical-velocity-right-release-1672.reference.json \
  --report <ignored-variation-report>
python3 -m tools.unirally_lab.native.zoom_zoo_vertical_velocity compare-inputs \
  --primary-access <unchanged-primary-access> \
  --variation-access <unchanged-worker-variation-access> \
  --content <unchanged-content> --report <ignored-comparison-report>
# All passed with the exact hashes above.
```

I did not repeat the broad debug/sanitizer, replay, pack, contract, projection
or DRAGSTER gates: the correction is confined to the research evaluator,
authored evidence hashes and focused tests, the worker recorded clean corrected
full-suite results, and the original independent review had already passed all
of those broader gates on the same arithmetic. This re-review ran the complete
focused M4-05--M4-11 suite, both exact authored verifications, the exact worker
comparison, both unchanged private captures, and all returned-finding
mutations.

`git diff --check b7a8db9..9d9e582` passes. No production-native, pack,
serialization, frontend, coordinator state or registry behavior changed. The
bounded limits remain accurate. M4-11 is approved for coordinator integration
and hosted CI.
