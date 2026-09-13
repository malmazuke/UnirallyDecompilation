# M4-12 independent review

## Assignment and preregistration

- Candidate: `43198c6242ae2d55d025704522f947f88d2ed84e`
- Reviewer: OpenAI `gpt-5.6-sol` / medium, isolated checkout
  `.worktrees/m4-12-review`, branch `review/M4-12-native-zoom-zoo`.
- Review scope: inspect the native dependency closure and exact integer/data-flow
  implementation; reproduce the primary evidence; run two independently selected
  Right/neutral cases from the authentic end-1649 seed through frame 1849, each
  with two fresh original processes, exact native comparison and fresh-process
  restores at 1700, 1804 and 1823.
- Candidate native behavior had not been executed or compared in this checkout
  when the cases below were selected. Reading the submitted task/research claim
  preceded selection, as required to identify relevant transition boundaries.

The two cases were frozen before evaluation:

1. `m4-12-review-delayed-right-1650-1660` replaces primary Right with neutral
   for frames 1650--1660, then restores Right. Prediction: this changes the
   player throttle/velocity producer early enough to alter subsequent movement
   and contact state; exact transition timing is deliberately not preclaimed.
2. `m4-12-review-neutral-1818-1826` replaces primary Right with neutral across
   the submitted 1823 landing and 1824 boost-tile boundary, then restores Right.
   Prediction: this changes the active horizontal-input producer and should
   exercise a different throttle/landing/boost continuation. Exact branch and
   persistence are left to the authentic reference result.

Both cases preserve the primary seed, horizon, opponent inputs and all excluded
mode guards. A failed capture, native rejection or byte mismatch will be retained
as review evidence rather than tuned away.

## Verdict

Pending independent execution and inspection.
