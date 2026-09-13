# Project state

Updated 13 September 2026: M4-13 player landing/recovery accepted at integration
`b288396ba3a81f35699648cff4ef92ddbd1c1c59`, synchronized to private origin with
macOS/Linux CI passed. Start with [NEXT_SESSION](../tasks/NEXT_SESSION.md).
Do not automatically dispatch M4-14.

## Accepted product and evidence

- Milestones M0–M3 are accepted; `m3` remains the latest milestone tag. The
  playable product is the identified PAL one-player CRAWLER/DRAGSTER slice
  through stable winner/loser results. Native play does not execute the original
  CPU. [M3 acceptance](research/R-0017-m3-acceptance.md) and
  [M4-01](../tasks/M4-01.md) define presentation limits.
- Exact user-ROM extraction produces the local 25-entry Classic pack. Audio,
  full rider art, other playable tracks/modes/riders, menus/progression and
  multiplayer remain outside the product. ROM/content/captures remain ignored.
- PAL ROM SHA-256 is
  `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`;
  the private locator is `local/rom-location.txt`.
- M4-00 through M4-13 are individually accepted; **M4 is not accepted**.
  M4-12 added autonomous native ZOOM ZOO continuation for both riders from
  end-1649 through 1849: 200 updates, exact 395-byte state, Right/neutral input,
  one seed and authenticated static content. [R-0030](research/R-0030-zoom-zoo-native-trial.md).
- M4-13 adds B jump, actual player support loss, landing and recovery in the
  same horizon. Primary B1681–1695 lands at 1745 and matches 104 subsequent
  updates. Two fresh independent cases and two corrected regressions match all
  bytes and restore before/after each full player landing. Captured dynamic
  native inputs remaining: zero. This is still not full-track support and has
  no production ZOOM ZOO frontend/presentation dispatch.
- Fresh Sol/medium [review](../tasks/M4-13-review.md) approved corrected code
  `13f80ff` after two findings in one correction round. App-debug and app-sanitize
  each passed 400 checks with no skips; all M4-12, DRAGSTER, content/replay and
  presentation gates passed. The merged build repeated primary and independent
  cases/restores. Hosted integration CI `34757217687` passed both platforms.
  Hosted Linux is synthetic coverage, not private Linux differential execution.

## Trial assessment and next work

[R-0032](research/R-0032-player-landing-recovery.md) records reused versus newly
recovered behavior, exact identities, negative evidence, restores and limits.
The sustained Astra/medium primary plus fresh automatic Sol review delivered
the second capability; review found real zero-displacement and first-probe
boundary gaps, both corrected with fresh untuned evidence. About 26 minutes
elapsed from startup to approval; shared usage grew from 15% at startup to 22%
at the 12:29 integration checkpoint. These observations are not a controlled
model comparison or full-game estimate. Final closeout time/usage/ref/CI are in
`artifacts/m4-13-integration/closeout.json`. No reset or purchase occurred.

[D-0004](decisions/D-0004-model-and-usage-budget.md) and
[D-0006](decisions/D-0006-capability-driven-work.md) remain the trial policies.
No further capability has been dispatched. Reassess before M4-14 when authorized;
full-track ZOOM ZOO, frontend/presentation, finish and audio remain future work.

## Where to look

- [Task registry](../tasks/README.md), [M4-13](../tasks/M4-13.md) and
  [R-0032](research/R-0032-player-landing-recovery.md): actual commits, commands,
  resources, review and next reference experiment.
- [Build and validation](BUILD_AND_VALIDATION.md): implemented CLI and private
  fixture boundaries; [native source guide](../src/core/README.md): source map.
- [Project plan](PROJECT_PLAN.md): longer-term M4–M6 scope; M5/M6 have not started.
- [Workflow](AGENT_WORKFLOW.md): ownership, review and required private-origin sync.
