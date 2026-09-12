# Sol coordinator handover — M3-03 minimal frontend

M3-02 is accepted through integration `759ed9e` after three independent review
rounds and green hosted run `34696469012` on macOS 15 and Ubuntu 24.04. Read
[M3-03](M3-03.md), [M3-02](M3-02.md),
[R-0015](../docs/research/R-0015-native-presentation.md),
[D-0005](../docs/decisions/D-0005-classic-content-distribution.md) and the
[native source guide](../src/core/README.md). Do not repeat presentation,
pack-identity or full-race mechanics research.

## Operating instructions

Use OpenAI Sol/medium with one worker in the assigned isolated worktree and a
fresh sequential reviewer. The user removed percentage stop/reserve limits for
this unattended run through all remaining M3 tasks, but did not authorize use
of the weekly reset reserve: do not redeem reset credits, purchase usage,
publish or deploy. At M3-03 claim, the account-wide weekly bucket reported 24%
used; this telemetry may include unrelated work. Keep 45-minute checkpoints
and durable ten-minute handoffs as recovery practice, not as a reason to stop.

## Current work

The M3-03 claim record is on current `main`. Implement the smallest SDL3 desktop
boundary that shows the accepted 256x224 pack-backed renderer, samples
keyboard/gamepad state into the accepted two-port masks exactly once per PAL
simulation update, and advances at a bounded 50 Hz independently of display
refresh. Freeze/test the scheduler and input mapping separately from the UI.

First launch must exact-gate a user-selected supported ROM and atomically create
the ignored Classic pack; later launch must succeed from the validated pack
with the ROM absent. Failure/cancel/corruption paths must be explicit. Audio is
deliberately omitted and must be visible in the CLI/UI/help rather than implied
working. Keep CI ROM-free; use a dependency arrangement that is pinned,
reproducible, warning-clean and does not install globally.

M3-04 owns clean-checkout playable acceptance, sustained real play, full-track
comparison and the milestone tag. Do not claim M3 accepted from M3-03 alone.
