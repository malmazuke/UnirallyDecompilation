# Sol coordinator handover — begin M3-01 native finish/full-race state

M3-00 is accepted at `0bc4938` after one returned verifier finding and approved
re-review. Read [M3-01](M3-01.md),
[R-0012](../docs/research/R-0012-complete-race-evidence.md) and the
[finish-state contract](../docs/state/race-finish.md). Do not repeat the long
finish discovery or begin presentation/frontend work.

## Operating instructions

Use OpenAI Sol with medium reasoning under D-0004, one child in an isolated
worktree, then a fresh sequential reviewer. Resample quota before claim; the
last review sample was 44% used / 56% remaining in the seven-day window. Keep
the final20% reserve and the original session's50%-used checkpoint. No purchase,
reset redemption, publication, deployment or provider switch is authorized.

ROMs, decoded content, save states, screenshots and large traces stay ignored.
The accepted M2 state is333 bytes with ROM-free continuation hash
`7c799b4393d171f2`; M3-01 must preserve those frozen cases while introducing an
explicit state revision for genuinely new future-affecting fields.

## Next ready work

Claim M3-01 from current `main`. Reproduce one accepted M2 native comparison,
its restore identity, the287-check suite and the M3-00 25-check compact analyzer.
Then run the smallest reference experiment that locates the stored per-rider
finish time/outcome and transition state shown on the result screen. Freeze the
new field projections before native code computes them.

Implement only the full-race semantic state/update after that freeze. Match both
accepted M3-00 paths through finish, including player/opponent instance order,
the next-frame dispatcher reaction,240 delay updates, derived-axis override and
fresh-process continuation around the boundaries. Never use emulator state or
per-frame captured reference values in the native runner.

Presentation extraction is M3-02, SDL/live controls are M3-03, and playable
acceptance is M3-04. Their boundaries are documented in R-0012; do not collapse
them into M3-01 or claim M3 accepted early.
