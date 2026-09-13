# M4-13 independent review

## Assignment and preregistration

- Candidate: `f1cd99355add5c0ac7ba0fcb290af87953e388d1`.
- Reviewer: OpenAI `gpt-5.6-sol` / medium, isolated checkout
  `.worktrees/m4-13-review`, branch `review/M4-13-player-landing`.
- Review scope: independently select and freeze two untuned player-jump timing
  variations before candidate evaluation; reproduce the primary and variations;
  inspect native arithmetic, update ordering, dependency closure and explicit
  limitations; run the focused 21 CTests and landing tooling checks.

The candidate native behavior and implementation were not inspected or executed
in this checkout before the cases below were selected and frozen. Reading the
submitted task and research claims preceded selection so the variations could
target the declared Right+B launch and player landing boundaries.

The two variations retain the authentic end-1649 seed, continuous Right baseline,
opponent controller, 395-byte projection and fixed end-1849 horizon. Each shifts
the submitted 15-update Right+B interval by three updates, holding its duration
constant:

1. `m4-13-review-player-jump-1678-1692` starts and releases B three updates
   earlier. Prediction before capture: launch state and later landing response
   should differ from the primary while leaving at least 100 updates after the
   selected player landing.
2. `m4-13-review-player-jump-1684-1698` starts and releases B three updates
   later. Prediction before capture: the altered launch state should delay or
   otherwise change the full player landing while retaining the required recovery
   horizon.

Both variations qualified from reference evidence before native evaluation. The
early case lands at 1740 and 1760, leaving 109 updates after its selected landing;
the late case lands at 1746 and 1762, leaving 103. Each pair of fresh original
captures is byte-identical. Their frozen rows SHA-256 values are respectively
`2e9480094840d31a03f49d46ec7abd89982b96fae7e1c06e46b8b8467541a336`
and `d512819d5eba735dcdbdde3d246c52a0b49dc5195ea48df8f79844171d4a7018`.
The frozen restore boundaries straddle every full player landing: 1739/1740 and
1759/1760 for the early case; 1745/1746 and 1761/1762 for the late case.

## Verdict

**Approve corrected candidate
`13f80ff0654e840848f78845364764bf3954b271`; no material finding remains.**
Initial candidate `f1cd99355add5c0ac7ba0fcb290af87953e388d1` was returned with
two acceptance-blocking landing gaps. Both are fixed, preserved as regressions
and covered by focused boundary tests. The corrected candidate also passes two
fresh untuned cases frozen before its source or native behavior was evaluated.

## Correction re-review preregistration

The original early and late cases informed correction of the missing landing
branches and are retained as disclosed regressions. Before reading, building or
executing the correction candidate, I selected two fresh cases:

1. `m4-13-rereview-player-jump-1682-1696` delays the complete 15-update
   Right+B interval by one update. Prediction: it changes launch and landing
   timing/state while retaining at least 100 updates after its first full player
   landing.
2. `m4-13-rereview-neutral-1675-1680-jump-1681-1695` removes Right for six
   updates immediately before the primary jump, then applies the original
   Right+B interval. Prediction: lower incoming horizontal velocity changes the
   launch/contact trajectory and exercises a landing distinct from a pure B
   timing shift while retaining the recovery horizon.

Both preserve the authentic seed, opponent controls, fixed end-1849 horizon and
all excluded mode guards. Reference qualification and freezing precede any
correction evaluation.

Both fresh cases qualified and repeated exactly. Delayed B lands at 1744 and
1771, leaving 105 updates after its selected landing; its rows SHA-256 is
`843a43b6be6044f405577ed9f7f3a019249554b67746a88606bfc1924746016a`.
The neutral-prelaunch case lands at 1745 and 1762, leaving 104 updates; its rows
SHA-256 is
`f9f199958b78e34e83c16fc329597cb0ed66ad72597135142c719aef7cecfb7d`.
Their frozen restore boundaries respectively are 1743/1744/1770/1771 and
1744/1745/1761/1762.

## Initial findings and correction assessment

### R1 — zero vertical half-displacement rejected a valid landing

The early case matched until its second full landing at frame 1760, where
candidate `f1cd993` aborted with `unrecovered zero-divisor landing angle`. The
original contact input was x 10721 versus previous x 10706 (dx 15), y 1755
versus previous y 1754 (dy 1, therefore half-dy zero), prior x displacement 17
and velocity `(470,-31)`. The original completed the landing with velocity
`(180,-158)` and orientation impulse 5.

The source at `$81:984D–98A8` uses bounded subtraction rather than mathematical
division. A zero half-dy reaches horizontal endpoint 4; zero dx reaches vertical
endpoint 32 and then clamps to 31; both zero selects the horizontal path. The
correction implements these endpoints explicitly and adds authored checks for
all three zero-component combinations. The retained early regression now
matches all 200 updates and restores at 1739/1740/1759/1760.

### R2 — initial first-probe support was excluded before ordered reduction

The late case aborted at its first landing, frame 1746, with `vertical contact
reaches nonnegative first-probe support`. Its first probe has penetration 0,
angle -4 and descriptor 14, but later ordered winners replace it; probe 9 wins
with penetration 13, angle -3 and descriptor 38. Final `$0F5D`/leading support
is therefore zero. The original completes recontact with velocity `(170,-272)`
and orientation impulse 5.

The correction initializes support, selected metadata, correction and
`leading_support` from the first probe, then preserves the existing ordered
reduction in which a later winner or tie clears the predicate. The separate
rejection for a final leading probe remains explicit. An authored first-probe
case and later tied replacement cover the ordering. The retained late regression
now matches all 200 updates and restores at 1745/1746/1761/1762.

The corrected endpoint arithmetic preserves signed 16-bit deltas before taking
absolute values, clamps only at the source endpoints and leaves landing-matrix
selection before orientation-quadrant clamping. The primary and all four review
cases compare every byte of the 395-byte state on every update. I found no
remaining arithmetic or update-order defect in the reviewed domain.

## Independent evidence and identities

| Case | Canonical case SHA-256 | Fresh reference file SHA-256 | Rows SHA-256 | Corrected result |
| --- | --- | --- | --- | --- |
| early B 1678–1692 regression | `d8335ea2933d58af5ef17de571dabd740d1a7d2dbec98f87942becfed9cd11a2` | both `44869de671eb2f2917e0b1523b5d83d8c3f19fde66e3b612a1604630cfa015b7` | `2e9480094840d31a03f49d46ec7abd89982b96fae7e1c06e46b8b8467541a336` | exact; four restores |
| late B 1684–1698 regression | `1dd725b66110faa8a28622f8b8b595b3a0207dbf84cb33e25df5f963f30f8ff9` | both `235eb897db83303e319a9c2822369a4badc731576be113b154bd22de69944ee6` | `d512819d5eba735dcdbdde3d246c52a0b49dc5195ea48df8f79844171d4a7018` | exact; four restores |
| fresh delayed B 1682–1696 | `14bc4f31176930822fda788755c06f0e572a6ca89a9aa59366ba3ac994335a1b` | both `a0680725c232878effe0dbdda6773b23690d5141f930030d4837a1aa3286a2cc` | `843a43b6be6044f405577ed9f7f3a019249554b67746a88606bfc1924746016a` | exact; four restores |
| fresh neutral 1675–1680, B 1681–1695 | `59b98afaf379588ac7ea4253be513d2c611d9889f8d7ad69d2bdce34967abc68` | both `c64e5b76b5a85e8f80577fa0e837349d82b9b868f4ed0de1626c3eb5d5497a5d` | `f9f199958b78e34e83c16fc329597cb0ed66ad72597135142c719aef7cecfb7d` | exact; four restores |

The fresh delayed-B case differs from the primary landing at 1744: y 1851
versus 1848, velocity `(352,-468)` versus `(483,448)`, surface angle -2 versus
zero and recontact one versus zero. It remains different at its second landing
and at 1849. The neutral-prelaunch case changes player velocity on frame 1675,
shifts x by one by jump onset and retains different position/contact/pose state
through 1849. These are material future-state variations rather than controller
rows that reconverge before landing.

The primary independently built comparison also passes all 200 updates and
restores at 1744/1745/1761/1762. The review runner SHA-256 is
`add6f5da67591ea4fd25e3c9c3b855e7caa949a22c58e440934d6af57bc3df62`.
Report SHA-256 values are `8e083b5d948c2989c3e6934d266430aa3b8b4cb720ae0ef73303caed4ff8b9fd`
for primary, `50933ed26fa900e2d7dcb06aea40dd37617eeae87869486df68e4a8da23a683c`
and `4f155a00d85510a8db0fa88dc6c530b24e54a6efe8096d1a5d8588b92103c31f`
for the regressions, and
`83c634fd48ffb87fb0925047cec5309c7769684f025902f0c22ab152d898533`
and `39d642ef5401069d89afe7cf58396eb852eefd1177c19f09c8f4cd5012acdfd9`
for the fresh cases.

## Dependency closure and limits

The complete primary access record covers 3,684,948 instructions on frames
1649–1849 with no capture failure or truncated watched-PC data. The two player
landing calls show zero incoming response channels, ordinary mode, authenticated
option `$132B == 0`, and all resulting velocity/impulse/contact publications.
The source-access audit reports 38 newly reached gameplay read sites versus
M4-12 and no new ROM-read sites. The reads are existing serialized jump,
landing, orientation, duration, input and rolling fields plus `$132B`, the only
new constant guard. No new future-affecting persistent field is omitted from the
395-byte state in the observed domain.

The runner links only libc++ and libSystem. Primary's corrected denied-reference
experiment independently denied reads of the repository and ROM directory,
verified both negative controls failed, and still reproduced all 201 native
states from one seed, authenticated static content and controller rows; its
report SHA-256 is
`f998e0e745b5fd8ac0dbae3fbfea696b6b6d23683bd20c79627d5828504c9878`.

Approval is limited to the authentic end-1649 seed, controller-0 Right/neutral/B
combinations exercised here, both riders, the exact 395-byte state and fixed
end-1849 horizon. Nonzero response inputs, final leading-probe landings, low
prior displacement, long airtime, special geometry, changed option guards and
the player camera predicate remain explicit rejections. This does not establish
full-track support or production frontend/presentation dispatch.

## Commands and results

- Four initial and four fresh `zoom_zoo_player_landing capture` commands ran in
  separate original processes; every pair was byte-identical. Four `freeze`
  commands created the committed contracts before the corresponding candidate
  evaluation.
- `python3 tools/project.py build --preset app-debug` passed from the corrected
  source in this checkout.
- Five corrected `zoom_zoo_player_landing compare` commands covered primary,
  both disclosed regressions and both fresh cases. Each matched 200 updates and
  performed four fresh-process restores around all full player landings.
- `ctest --test-dir build/app-debug --output-on-failure` passed 21/21.
- `python3 -m unittest tests.tooling.test_zoom_zoo_trial` passed 3/3.
- `python3 tools/project.py rom inspect --expect
  tests/manifests/rom/unirally-pal.json` passed all ten identity fields and the
  internal checksum for PAL ROM SHA-256
  `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`.

Primary separately reports corrected app-debug and app-sanitize at 400/400 each,
the seven frozen private gates, M4-12 regressions and corrected M4-13
primary/early/late all passing. Those broad runs were intentionally not
duplicated by this focused independent review.
