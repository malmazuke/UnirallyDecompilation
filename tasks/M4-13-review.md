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

Candidate `f1cd99355add5c0ac7ba0fcb290af87953e388d1` is returned with
acceptance-blocking findings. Correction re-review is pending.

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
