# Reassessment handover — M4 paused after M4-11

Updated 13 September 2026. This is the starting point for reassessing the
project approach. No implementation task is claimed.

## Accepted boundary

- Milestones M0--M3 are accepted; `m3` is the latest milestone tag.
- M4-00 through M4-11 are accepted as individually bounded tasks. M4 itself is
  **not** accepted.
- The native product remains the identified PAL one-player CRAWLER/DRAGSTER
  slice. It exact-gates the supported ROM into a 25-entry local Classic pack,
  then runs without original CPU execution or the ROM present.
- ZOOM ZOO remains reference research only. The accepted frame-1650--1700 chain
  covers content reads, 102 contact calls/1,020 sample words, recurrent x/y and
  residues, response B, and vertical velocity. It is not a playable second
  native track.

## Latest completed task

[M4-11](../tasks/M4-11.md) seeds player/opponent vertical velocity once at
end-frame 1649 and computes every reached speed-cap, jump, gravity, motion and
contact stage through frame 1700. The bounded domain has 102 gravity writes, 28
boost decrements, no cap or jump velocity writes, and final vertical velocity
player 241/opponent 0. Cap/jump preservation is not claimed outside this window.

The first independent review returned a real verifier defect: freshly rebound
documents could evade pose-consumer, access-width, stage-order and writer-
exhaustiveness checks. Correction `f7ff0e3` added semantic validation independent
of the outer capture hash. Focused re-review replayed all seven contradictions
plus missing/duplicate/unclassified `$0FAB` writers and approved the correction.
See [R-0029](research/R-0029-zoom-zoo-vertical-velocity.md), the
[review](../tasks/M4-11-review.md) and [re-review](../tasks/M4-11-rereview.md).

Accepted technical integration `0a2b9bb` passes:

- Focused M4-05--M4-11 tests: 60/60.
- Clean app-debug and app-sanitize: 373 Python tests, 20 CTests and
  three-process repeatability each.
- Exact primary/variation/comparison reports: `de4cbfbe...`, `69655d09...`,
  `1ab5bec0...`.
- Worker replay 24/24, ZOOM ZOO contract 3/3, Classic pack 3/3, and DRAGSTER
  finish plus four restores 18/18.
- Hosted CI run `34750113118`: macOS 15 and Ubuntu 24.04 green, including Linux
  SDL sanitizers.

## Explicit remaining boundary

The accepted ZOOM ZOO recurrence still takes these as external inputs:

- Horizontal velocity and its throttle/speed-limit/boost/progress producers.
- Pose, reflection, orientation, animation and displacement history.
- Jump/control state beyond the values inventoried for the vertical producer.
- Other contact/motion state, AI, progress, finish, camera and presentation.
- Audio and frames/branches outside the bounded research window.

Production `src/`, serialization and the Classic pack were deliberately not
expanded for ZOOM ZOO. Original ROMs, captures, generated content and build
reports remain ignored and untracked.

## Reassessment questions

Before creating M4-12, decide whether to continue the current one-producer-at-a-
time differential method or change the investment gate. Useful options include:

1. Continue toward bounded ZOOM ZOO autonomy, probably with horizontal velocity
   next, followed by the larger pose/orientation dependency cluster.
2. Pause second-track reconstruction and consolidate the accepted research into
   a broader architecture/feasibility decision.
3. Re-scope M4 toward another coverage axis such as modes, multiplayer,
   progression or audio, with a new evidence-backed task decomposition.
4. Stop M4 and treat the accepted M3 playable slice plus M4 research archive as
   the project outcome for now.

Do not infer a preferred option from the existing queue. A future coordinator
should first read [project state](STATE.md), [the compact session handoff](../tasks/NEXT_SESSION.md),
the M4-10/M4-11 records and this document, then record any changed scope or
acceptance strategy before dispatching work.

## Repository state

The coordinator acceptance commit containing this handover is intended to be
the synchronized `main` tip. Verify with:

```sh
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
```

No weekly usage reset was consumed during the unattended M4 work.
