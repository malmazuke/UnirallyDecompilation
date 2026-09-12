# Sol coordinator handover — begin M3 playable DRAGSTER slice

M2 is accepted through PR5/`144fd48` and the milestone audit
[R-0011](../docs/research/R-0011-m2-acceptance.md). Start from current `main`;
do not repeat M2's movement or save/restore implementation.

## Operating instructions

Use OpenAI Sol with medium reasoning under D-0004. Keep one active child by
default and use a separate checkout for independent review. The user removed
the percentage guardrail for the completed M2 session; no purchase, reset
redemption, publication, deployment or provider switch is authorized. Read
`AGENTS.md`, `docs/STATE.md`, `docs/AGENT_WORKFLOW.md`,
`docs/BUILD_AND_VALIDATION.md`, `docs/PROJECT_PLAN.md` and R-0011.

Original ROMs, decoded content, save states and large traces stay ignored.
The accepted native state is333 bytes and the ROM-free continuation hash is
`7c799b4393d171f2`. Primary and two withheld M2 cases match all13 required
projections from frames1534–2999; this is a short-domain result, not a complete
race or playable build.

## Next ready work

Keep the Crawler/DRAGSTER scenario: it already has reviewed reference, state,
track-content and native-mechanics identities. Create the first bounded M3 task
to extend the reference replay through an actual finish and inventory the
missing dependencies for native completion, controls, rider presentation and a
minimal frontend. Pre-register the finish observations and controller variation
before implementing new native behavior. Record exact frame ranges, finish/race
state writers, uncovered code/content and whether the existing decoded track
buffer is sufficient for the whole race.

Use that evidence to split M3-01 along real interfaces. Do not begin by building
a speculative frontend around the 1,466-update M2 slice, and do not describe an
emulator-assisted result as native gameplay. The M3 gate requires a complete
track, real controls, rider animation, collision/tricks/race finish, scoped
full-track differential checks, a repeatable clean build and explicit visual or
audio omissions.

The initial M3 planning range is6–20 worker hours and3–8 review rounds. It is a
prioritization range, not a date, cost or permission to spend.
