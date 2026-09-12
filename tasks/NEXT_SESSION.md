# Sol coordinator handover — begin M3-02A Classic content pack

M3-01 is accepted through merge `c393c54` after two returned arithmetic
findings, an approving fresh review and green private CI run34682900511 on
macOS15 and Ubuntu24.04. Read [M3-02A](M3-02A.md),
[D-0005](../docs/decisions/D-0005-classic-content-distribution.md),
[R-0013](../docs/research/R-0013-native-finish-reference-freeze.md) and the
[native source guide](../src/core/README.md). Do not repeat finish research or
begin renderer/frontend work.

## Operating instructions

Use OpenAI Sol with medium reasoning under D-0004, one child in an isolated
worktree, then a fresh sequential reviewer. Resample quota at claim and preserve
the final20% reserve. The post-M3-01 sample unexpectedly reported1% used after
the task had sampled51%; record that telemetry discontinuity rather than
attributing it to this task. No purchase, reset redemption, publication,
deployment or provider switch is authorized.

ROMs, decoded content, generated Classic packs, save states, screenshots and
large traces stay ignored. M3-01's accepted full-race cases and explicit
333-byte V1/369-byte V2 state transition are frozen regressions.

## Next ready work

Claim M3-02A from current `main`. Reproduce the accepted M3-01 reviewer-owned
finish case and one restore boundary, then inventory every static-content read
made by the native runner. Freeze a minimal logical-ID pack schema and a public,
semantic playable-start state before implementing commands.

Implement deterministic atomic extraction from the exact supported PAL ROM,
pack inspection and mutation rejection using authored ROM-free fixtures. Prove
two separately generated packs are byte-identical, then move the ROM aside and
show that the validated pack alone reproduces canonical native state. Never
track or expose original bytes in CI artifacts.

Presentation extraction is M3-02, SDL/live controls are M3-03, and playable
acceptance is M3-04. Do not collapse them into M3-02A or claim M3 accepted.
