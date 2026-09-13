# Project state

Updated 13 September 2026: M4-14 sustained traversal is independently approved
and all local gates pass. Acceptance is conditional on merged checks, private
remote ref and exact final-tip CI in `artifacts/m4-14-integration/closeout.json`.
Start with [NEXT_SESSION](../tasks/NEXT_SESSION.md); do not dispatch M4-15.

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

## M4-14 capability and integration

[R-0033](research/R-0033-sustained-traversal.md) records native continuous Right
from authentic end-1649 through 3299: 1,650 updates / 33 PAL seconds, both riders,
423-byte state (`URZZ0002`), no captured dynamic inputs or original CPU fallback.
Recovery at 2185 leaves 1,114 updates. This is local resumed progress followed
by continued traversal; the rider revisits the same section. It does not prove
monotonic advance, obstacle clearance or full-race completion.

Recovered behavior includes inverted/horizontal probes, steep contact and
landing, tile-selected mode/angle lifecycle, pose/control consumers, and leading
landing reward bookkeeping. The seven additive words per rider preserve old
395-byte `URZZ0001` expectations. Full reference hashes, static inputs and guard
identities are frozen; corrected continuous instruction audit authenticates
30,355,912 instructions and closes the reached future-state inventory.

Fresh Sol/medium [review](../tasks/M4-14-review.md) approved corrected candidate
`e730aaa`. Review found an extra conversion on a full 28-unit landing, missing
binary restore validation and an unclosed audit record. All are resolved; the
failed case remains a regression and a fresh untuned replacement passes 96
restores. A separate material late variation also passes. Primary and cases
retain the complete horizon and frozen recovery requirement.

App-debug and app-sanitize each passed 403 checks, no skips; all accepted
M4-12/M4-13 differential cases/restores and DRAGSTER/content/replay/presentation
gates pass. Denied-ROM/repository execution and negative controls establish the
bounded native runtime's autonomy. M4 remains incomplete; ZOOM ZOO frontend,
presentation/audio, full-track support and private Linux differential execution
are not claimed.

Primary Astra/medium started 13:09 UTC, shared weekly usage 26%; independent
approval around 13:54, usage 35%. These are account-wide observations, not a
controlled model comparison. No reset, purchase or provider switch occurred.
The [task](../tasks/M4-14.md) records the 45-minute reassessment and integration
commands. Actual final SHA/time/usage/remote/CI belong in the ignored closeout.
If absent, recover using git and GitHub as NEXT_SESSION describes. Do not create
a second documentation-only CI cycle to transcribe that result.

M4-13 remains accepted at `b288396`; its final closeout took 42.81 minutes and
eight shared usage points (15% to 23%). Historical evidence remains in R-0032
and its task/review. For any future task, retain D-0004/D-0006 budget and automatic
review practices; M4-14's exception does not authorize another task now.

## Where to look

- [Task registry](../tasks/README.md), [M4-14](../tasks/M4-14.md) and
  [R-0033](research/R-0033-sustained-traversal.md): actual commits, commands,
  resources, review and next reference experiment.
- [Build and validation](BUILD_AND_VALIDATION.md): implemented CLI and private
  fixture boundaries; [native source guide](../src/core/README.md): source map.
- [Project plan](PROJECT_PLAN.md): longer-term M4–M6 scope; M5/M6 have not started.
- [Workflow](AGENT_WORKFLOW.md): ownership, review and required private-origin sync.
