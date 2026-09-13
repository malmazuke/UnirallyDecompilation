# Project state

Updated 13 September 2026: M4-11 accepted; M4-12 process trial prepared, unclaimed.
Implementation resumes in the next user-started Astra/medium session, subject to
fresh resource readiness. Start with [NEXT_SESSION](../tasks/NEXT_SESSION.md).

## Accepted product and evidence

- Milestones M0--M3 are accepted; `m3` is the latest milestone tag. The native
  product supports the identified PAL one-player CRAWLER/DRAGSTER slice through
  stable result, with controls, presentation, native restores and macOS/Linux
  checks. No original CPU executes during native play. See
  [M3 acceptance](research/R-0017-m3-acceptance.md).
- Exact-gated user-ROM extraction creates a local 25-entry Classic pack; later
  runs work with the ROM absent. Audio, intermediate rider-art coverage, other
  tracks/modes/riders, menus/progression and local multiplayer remain omissions.
  [M4-01](../tasks/M4-01.md) adds the accepted DRAGSTER loser-result presentation.
- PAL ROM SHA-256:
  `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`.
  Its locator is ignored `local/rom-location.txt`. ROM, extracted content, packs,
  captures and save states remain untracked. Identity evidence: [R-0001](research/R-0001-rom-identity.md).
- M4-00 through M4-11 are individually accepted; **M4 is not accepted**. ZOOM ZOO
  remains reference research only. Frames 1650--1700 cover both riders' 102
  contact calls/1,020 samples, recurrent position/residues, response B and vertical
  velocity. Horizontal velocity, pose and remaining control/contact/AI state
  remain external. [R-0029](research/R-0029-zoom-zoo-vertical-velocity.md) links
  the dependency evidence; [reassessment handover](REASSESSMENT_HANDOVER.md)
  records the precise boundary.
- M4-11 technical integration `0a2b9bb`, accepted in `1523795`, passes focused
  60/60, app-debug/app-sanitize 373 Python tests plus 20 CTests/repeatability,
  frozen private gates and hosted run `34750113118`. Returned semantic verifier
  gaps were corrected and independently approved. These are historical test
  results, not results for the upcoming trial.

## Next work and policy

[M4-12](../tasks/M4-12.md) is ready, not claimed: autonomous native ZOOM ZOO
movement across a larger declared domain. [D-0006](decisions/D-0006-capability-driven-work.md)
assigns coupled recovery and native implementation to one sustained Astra/medium
primary, with automatic fresh Sol/medium independent review. Small experiments
and commits do not each require a new task lifecycle. New native interfaces are
allowed within the task; accepted reference expectations and DRAGSTER behavior
remain frozen. Acceptance does not imply a playable full second track.

[D-0004's exception](decisions/D-0004-model-and-usage-budget.md#m4-12-trial-exception)
waives the 20-point task cap while retaining the final 20% review/recovery reserve.
Preparation observed 98% weekly used and one reset available; sample fresh usage
at startup. No reset was consumed or authorized for this trial by repository
preparation. Do not infer redemption permission or resource capacity from the
handoff. No purchases, provider switch, public release or deployment authorized.

## Where to look

- [Task registry](../tasks/README.md): accepted tasks and links to detailed history.
- [Build and validation](BUILD_AND_VALIDATION.md): actual command inventory,
  private/public fixture boundary and staged validation; proposed commands are
  not capabilities. The M4-12 native runner is not implemented yet.
- [Native source guide](../src/core/README.md): established code and units.
- [Project plan](PROJECT_PLAN.md): long-term M4--M6 scope; M5/M6 not started.
- [Workflow](AGENT_WORKFLOW.md): ownership, automatic review and integration.

No scheduler, automatic quota limiter or automatic model router exists. Agents
apply the policy through available tools. A result is accepted only after
independent review, exact integration checks and verified private-origin sync.
