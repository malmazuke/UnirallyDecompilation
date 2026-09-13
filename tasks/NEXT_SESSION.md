# M4-15 integration handoff

M4-15 now reproduces a complete native ZOOM ZOO race from authentic end-1649:
5,075 updates, 565 exact state bytes for both riders, finishes at 6484/6488,
and 240 player post-finish updates. No fallback was used. Native race-start
initialization, frontend, rendering/audio and subsequent result-screen loading
remain outside this capability. M4 itself is not accepted.

Read [M4-15](M4-15.md), its [review](M4-15-review.md),
[R-0034](../docs/research/R-0034-zoom-zoo-race-completion.md) and
[STATE](../docs/STATE.md). Corrected code is `6faff68`; the task branch also includes
review evidence and consolidated handoff. Independent review and local gates
are complete; acceptance is conditional on exact merged checks, private main
push/ref verification and exact-tip hosted macOS/Linux CI.

Actual integration SHA, commands/results, remote ref, CI URL and final
clock/quota belong in ignored `artifacts/m4-15-integration/closeout.json`.
If missing, recover with git history, `git ls-remote origin refs/heads/main`,
`gh run list --commit <integration-sha>` and `gh run view <id> --json jobs`.
Do not infer remote acceptance from this conditional tracked handoff.

If those checks are pending, finish them without a new user dispatch. Once
verified, stop: no automatic M4-16 dispatch and no M4 milestone tag. A future
user-assigned product task must choose its own outcome; this task has not
accepted a ZOOM ZOO frontend or initialization from race start.
