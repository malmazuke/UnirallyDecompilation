# M4-11 independent review

- Candidate: `61b940c30f823d30c17c5963c61d38cbdea87273`
- Reviewed range: `e21e87b6e1de390f92a77e2c3f00596df90dc627..61b940c30f823d30c17c5963c61d38cbdea87273`
- Review branch/worktree: `review/M4-11-vertical-velocity`,
  `.worktrees/m4-11-vertical-velocity-review`
- Verdict: **returned with one material semantic-enforcement finding**

## Finding

The captured result and arithmetic are sound, but the new evaluator does not
enforce all evidence that its acceptance contract says it checks. In
`_computed_response_rows`, it bypasses M4-10's `$83:F00D` pose-consumption
comparison. `_motion_block` extracts the seven motion/contact boundary events
without validating their two-byte widths. `velocity_composition` relates the
gravity, cap and integrator values but does not compare their event sequence,
and it does not reject additional writes to `$0FAB` outside its individually
queried writer PCs.

This is independently reproducible without relying on a stale authored hash. I
changed one semantic fact at a time in the complete private capture and rebound
that document as a new private capture identity, exactly as a new reviewer
scenario must be admitted. All seven contradictory documents unexpectedly
complete the 102-row evaluation:

- change the frame-1650 `$83:F00D` response-B read from 0 to 1;
- change each of the player motion scratch load, motion persistent publication,
  contact scratch load and contact persistent publication from width two to
  width one;
- move the frame-1650 cap input read before the gravity publication while
  keeping its coincident value; or
- insert an additional same-value `$0FAB` writer between gravity and cap.

The fixed access SHA-256 catches an edit to either authored worker capture, but
that is identity binding, not the required independent pose, width, writer and
order validation. In particular, M4-11 acceptance requires retained
response-B/pose comparisons and requires wrong order/width or an omitted or
duplicated reached writer to reject or change the result. The current focused
tests exercise only manifest ordering/identity and selected arithmetic widths,
so they do not expose this gap.

Precise remediation:

1. Restore the M4-10 pose-consumer assertion in `_computed_response_rows`:
   require exactly one complete width-two `$83:F00D` read from `$0F57` per call,
   equal to the computed response B, and include `pose_consumed` in the hashed
   response row.
2. Require width two on every motion load/publication and contact
   load/publication boundary event returned by `_motion_block`.
3. Assert event sequence, not only equal values: persistent/scratch load,
   reached active jump and state publication, gravity input/write, cap
   input/optional cap write and boost update, integrator read, motion
   publication, contact load/accepted contact writer, and final persistent
   publication.
4. Enumerate all writes overlapping `$0FAB` in the motion and contact intervals
   and reject missing, duplicate or unclassified writers. Bind the reached
   writer PC, width, count and value to the computed branch.
5. Add focused mutations for each contradiction above through a semantic event
   validator independent of the outer access digest, then regenerate only the
   affected row/manifest hashes from the same original captures.

No candidate implementation was changed in this review.

## Source, writer and order audit

I read the required workflow, state, plan, build, task and M4-05--M4-10 research
records before reviewing the nine-file, 1,149-line additive diff.
`git diff --check` passes, and no frozen production, pack, serialization,
frontend, coordinator state or registry file changed.

An independent read of the supported PAL ROM
`a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`
reproduces the candidate routine identities:

- `$82:A81A--A872`: 89 bytes,
  `abfe21846d6e3d2f91bc649e510db6d5616fb5d7ea879192ec1aa5b8e72aac31`;
- `$82:A8C9--A96E`: 166 bytes,
  `2a21e360ddac360508870de522d2a779c6e75bfdb21f46645690728302077078`;
- `$82:A96F--A9B2`: 68 bytes,
  `5f3d24df4c743df33e24d2febc24522cd2abe68fe5597ee2abf3ebfac413653c`.

The reached instruction audit confirms 16-bit motion arithmetic. All 102 calls
execute gravity before the cap despite the lower cap address. Gravity uses the
N flag from wrapped `vy - 0x0200`; its nonnegative path performs five logical
right shifts and its negative path retains addend 16, then both add three and
wrap the final word. The cap derives `(extra >> 1) + 0x0300`, uses wrapped
subtraction signs for positive and negative limits, and preserves all primary
velocities. Its adjacent boost subtract rejects wrapped underflow. Jump runs
only for the active rider, all reached guards are observed, all 51 active calls
publish `$0FA5`, and none reaches a vertical-velocity write.

Across frames 1650--1700, the actual vertical-velocity access inventory is:

- each persistent word has 51 motion reads/writes and 51 contact reads/writes,
  all width two; opponent `$04C1` also has 43 width-two AI reads at `$83:E228`;
- `$0FAB` has 102 gravity writes at `$82:A9AA`, 102 integrator reads, 102 cap
  reads, 19 negative-cap comparison reads, 83 nonnegative-cap comparison reads,
  32 slope-tail reads, 102 motion loads/reads and 102 contact loads/caller reads;
- accepted contact performs 73 width-two `$81:970B` scratch writes among the
  102 calls, with the remaining contact paths preserving before all 102 final
  persistent publications.

Direct sequence checks confirm all 102 width-two chains in the observed order:
motion persistent/scratch load, active jump or preserve, gravity, cap,
integrator, motion persistent publication, contact persistent/scratch load,
accepted contact response, and contact persistent publication. There are no
other actual vertical-velocity writers, unresolved stores or non-ROM PCs in
either private capture. Thus the finding is an evaluator enforcement defect,
not a contradiction in the captured primary behavior.

The worker primary and frame-1672 manifests both verify from one end-1649 seed
without later captured velocity input. All 102 motion/post-jump/post-gravity/
post-cap/integrator/contact rows and all 1,020 sample words/source offsets match;
the final primary words remain player 241/opponent 0, both response-B words are
zero, and the accepted final position/residue words remain unchanged. The
primary, variation and comparison reports reproduce the worker's exact hashes
`d23db223...f8cb`, `3d0514ed...94a3` and `ad42728b...12c`.

## Private frame-1674 case

Before inspecting any new evaluator output, I chose release Right at frame 1674
only and restoration at 1675. The choice and bounded predictions were recorded
under ignored `local/review/m4-11-vertical-velocity-review/`. Controller
divergence only at 1674, exact behavior through 1673, first player composition
difference at 1674, unchanged opponent, divergent player at 1700, unchanged
response-B values and unchanged final velocity all hold.

Two timing/relevance predictions are retained as falsified. Sample words first
differ at 1675 rather than the predicted 1676. Contact vertical velocity first
differs at frame 1675, and the recurrent motion/post-jump/gravity/cap/integrator
chain differs on five player calls beginning at 1676; the predicted complete
vertical-velocity invariance is therefore false. The private split is 24
negative and 78 nonnegative gravity inputs, versus 23/79 primary, but both final
velocity words reconverge to player 241/opponent 0. Response-B values remain
unchanged, while its evidence-row digest changes because captured producer
inputs differ.

Both final fresh captures pass and are byte-identical at access SHA-256
`b682aeaa34856c898c25cc4a4447da20bf296591610e97879bb16a1dc76dbb01`
and WRAM-series SHA-256
`5e803b5664414d30565887c01a2d55c6b6cadb55b42171fa9c3ec1bc8e34be8f`.
Each has 953,521 instructions, 472,012 accesses, zero unresolved stores, zero
non-ROM PCs, no truncation and maximum ring use 18,640/262,144. Independent
evaluation closes all 102 rows and 1,020 samples. The private row/sample/source
hashes are `9000b7da...ed55`, `7cb3af73...6e63` and
`36a78f08...896`; final position/residue is player `(9824,1605,9,15)` and
unchanged opponent `(7489,1520,-4,12)`.

## Adversarial and regression evidence

The ignored review harness derives the real primary chain and changes one
dependency at a time. Seed, rider, call order/loss/duplication, reseed,
captured substitution, phase, jump, gravity/cap/integrator ordering value,
motion/contact publication, same-rider feedback, every authored manifest
identity/result family, cap mode/sign/wrap/boost behavior and gravity signed
formula/logical-shift/wrapped predicate all behave as required: 37/37 checks
pass. The seven additional semantic event mutations above unexpectedly pass
and are the returned finding.

Focused M4-05--M4-11 tests pass 57/57. Clean `app-debug` and `app-sanitize`
each pass 370 Python tests, all 20 CTests and three-process repeatability; their
393-check reports hash to
`73339356b083e51d0b303a470a03da32b80869aeb29f4c812b6bce7562c6c5a2`
and `2607da038408ddd6cb9a468828b37c786fc4cf68456db7c58d06a4c982cb810c`.
The worker replay passes 24/24 (`ad621dbd...5e18`), ZOOM ZOO contract and
Classic pack pass 3/3 each (`6cbe5c43...5577`, `1ac338cc...cd7`), the frozen
projection pair remains exact with its declared frame-2500 divergence, and
DRAGSTER finish plus four restores passes 18/18 (`990e25b8...a2a`).

Non-passes remain explicit. The first two private capture attempts reported the
missing task-local core after an incorrectly resolved ignored symlink. The two
placeholder-expectation captures then failed exactly their sample/final-state
digest checks before the result was frozen and two fresh passing captures were
made. The first clean debug test run lacked the required empty ignored
`artifacts/` directory and reported two tooling-test failures; its other 368
Python tests, 20 CTests and repeatability passed. Creating only that prerequisite
and rerunning the unchanged candidate produced the clean result above. An
initial ignored adversarial invocation had a module search-path error and was
corrected without changing a candidate expectation.

Private ROM bytes, captures, content, reports and builds remain ignored. The
candidate should not be accepted until the finding is corrected and focused
re-review passes.
