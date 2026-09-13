# Project state

Updated 13 September 2026: M4-12 native capability trial accepted at integration
`1889d9cbc56fec4437bc67835cd885677cc29e03`, with a documentation-only closeout.
M4-12 is complete; M4-13 is prepared and unclaimed for the next user-started session. Start with [NEXT_SESSION](../tasks/NEXT_SESSION.md).

## Accepted product and evidence

- Milestones M0–M3 are accepted; `m3` remains the latest milestone tag. The
  playable product is the identified PAL one-player CRAWLER/DRAGSTER slice
  through stable winner/loser results. Native play does not execute the original
  CPU. [M3 acceptance](research/R-0017-m3-acceptance.md) and
  [M4-01](../tasks/M4-01.md) define the presentation boundary.
- Exact user-ROM extraction produces the local 25-entry Classic pack. Audio,
  full rider-art coverage, other playable tracks/modes/riders, menus/progression
  and multiplayer remain outside the product. ROM/content/captures remain ignored.
- PAL ROM SHA-256 is
  `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`;
  the private locator is `local/rom-location.txt`.
- M4-00 through M4-12 are individually accepted; **M4 is not accepted**.
  M4-12 adds experimental autonomous native ZOOM ZOO continuation for both riders
  from end-1649 through 1849: 200 updates, exact 395-byte state, Right/neutral
  controller-0 input, initial state and authenticated static content only.
  Dynamic captured runtime inputs remaining: zero. This includes later support,
  reflection, landing-matrix and boost-tile transitions. It is not full-track
  support and has no production frontend/presentation dispatch.
- Two independently selected, untuned variations pass the full horizon; the
  review-discovered delayed-acceleration failure is preserved as a corrected
  regression. Primary and all three cases pass fresh-process restores at
  1700/1804/1823. [R-0030](research/R-0030-zoom-zoo-native-trial.md) records exact
  identities, source inventory, commands, negative evidence and limits.
- Fresh Sol/medium [review](../tasks/M4-12-review.md) approved corrected code
  `aef2245e9b90ae648356752ca45e7a234910d836` after one finding/fix/re-review round.
  App-debug and app-sanitize each pass 400 checks (376 Python tests, 21 CTests
  and native repeatability). Frozen DRAGSTER/ZOOM ZOO/content/presentation gates
  pass; hosted candidate run `34754212973` passed macOS and Linux. Integration
  code/build/test sources exactly match that reviewed and tested candidate.

## Next work and policy

[M4-13](../tasks/M4-13.md) is ready/unclaimed following the user-approved
[R-0031 retrospective](research/R-0031-m4-12-retrospective.md). Target native
player support loss, landing and recovery plus at least 100 subsequent updates;
freeze the sequence/horizon before tuning. Necessary control/camera dependencies
remain internal experiments. Finish/presentation remain excluded; M4 is incomplete.

[D-0006](decisions/D-0006-capability-driven-work.md) now extends the sustained
Astra/medium primary and automatic fresh Sol review approach to M4-13. Focused
checks precede initial review; broad validation follows resolved findings. Use the
corrected cache/report layout. The M4-12 result supports continuing this workflow,
not a causal model-speed claim: approximately 71 minutes/12 shared usage points
through final closeout versus 60 minutes/11 points at review approval.

[D-0004's extension](decisions/D-0004-model-and-usage-budget.md#m4-13-trial-extension)
waives the task cap but preserves the final 20% review reserve. Preparation
observed 13% weekly used and no reset credits; sample fresh usage at startup.
No reset, purchases or provider switch authorized. No gameplay work was started
by preparation. Do not automatically dispatch M4-14 after M4-13.

## Where to look

- [Task registry](../tasks/README.md) and [M4-12](../tasks/M4-12.md): actual commits,
  validation reports, resources, review and next recovery experiment.
- [Build and validation](BUILD_AND_VALIDATION.md): implemented CLI and M4-12
  extraction/capture/compare/restore commands, with private fixture boundaries.
- [Native source guide](../src/core/README.md): code, units and source links.
- [Project plan](PROJECT_PLAN.md): longer-term M4–M6 scope; M5/M6 have not started.
- [Workflow](AGENT_WORKFLOW.md): ownership, review and required private-origin sync.
