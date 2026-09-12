# Sol coordinator handover — M3-04 playable acceptance

M3-03 is accepted through integration `36f742f` after five returned review
rounds and final approval; hosted run `34703787445` passed macOS app-debug and
Ubuntu app-debug/app-sanitize. Read [M3-04](M3-04.md),
[M3-03](M3-03.md), [R-0016](../docs/research/R-0016-minimal-frontend.md),
[M3-03 review](M3-03-review.md), [D-0005](../docs/decisions/D-0005-classic-content-distribution.md)
and the M3 records cited by the task. Do not repeat recovered mechanics,
presentation or collision-path research.

Use one Sol/medium worker in the clean acceptance worktree, then a fresh
sequential reviewer. The user authorized uninterrupted work through M3 and
removed project percentage reserves for this run, but explicitly excluded the
weekly usage reserve: do not redeem reset credits, buy usage, publish or deploy.
The account-wide weekly bucket reported 35% used at claim.

First reproduce a clean supported-ROM launch and pack-only relaunch with the ROM
removed. Use the computer-use workflow for the visible SDL window and actual
keyboard input; `--fixed-controller-mask` remains a deterministic test seam and
is not live-control evidence. Record real observed responsiveness/readability
separately from exact replay comparison. If the UI exposes a defect, add the
smallest diagnostic/regression and correct it under review rather than arguing
around the gate.

Rerun all three accepted full-race native inputs, restore boundaries, the seven
unchanged presentation cases, both suites and repository hygiene. Assemble
R-0017 with exact identities and omissions. Only after independent approval and
green exact-merge CI should the coordinator accept M3 and create tag `m3`.
