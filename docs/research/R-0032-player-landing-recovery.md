# R-0032 — M4-13 player landing and recovery

## Frozen experiment and observations

Primary reference was frozen in `d3cbcd0` before native tuning: authentic
end-1649 seed, Right continuously, plus B on 1681–1695, through end-1849.
The PAL ROM and pinned bsnes identities remain those of R-0030. The 395-byte
projection and all 18 static-content identities are unchanged. Both original
captures give rows SHA-256
`9d1b4d9b9f3ed4a1a038d491c8536dbf609b3fc4c4edd86968791a804c05dcc9`.
The later supplemental-guard captures have the identical full state and WRAM
hash sequences; their additive freeze does not replace the earlier expectation.

Player support count `$054B` reaches two at 1684 and saturates at nine at 1691.
At 1745 it resets from nine to zero, previous count `$054F` is nine and recontact
`$127B` is one. This is player contact, not the opponent event. The landing
changes velocity `(483,453)` to `(168,-276)` and leaves orientation impulse four.
A second landing at 1762 changes `(216,47)` to `(62,-94)` and leaves impulse six.
The horizon includes **104 updates after the selected 1745 landing**. It includes
all of 1650–1849; it does not claim 100 updates after the secondary landing.

Private primary files are `artifacts/m4-13/primary-{a,b,c,d}.json` in the task
checkout. The first pair predates tuning; the second additionally authenticates
`$132B == 0` every frame. `primary-access/access.json` traces every instruction
1649–1849, with complete watches, zero unresolved stores and zero resolution
conflicts. Its WRAM series confirms `$132B` remains zero. The player landing
reads it at `$81:94B9`; zero preserves the chosen matrix. This guarded option is
not a camera constant or per-frame native input.

Continuous Right exploration first reaches a full player landing at 1991 and
changes excluded guards. A single-frame B pulse did not produce a full jump.
Held B was selected as the smaller domain before implementation, not by changing
the horizon after a native failure. These negative reference experiments remain
under `artifacts/m4-13/explore-*`.

## Recovered behavior and dependency closure

- `$82:AAE2–AAFB`: B maps to jump `$0331`; Y maps to brake `$0325`.
  The former unexercised native stub incorrectly mapped B to both. The new
  admitted input is B plus existing Right/neutral; other controls still reject.
  Pending jump, impulse phase, baseline and previous input already serialize.
- `$83:EED2–EEDB`: a low animation rate decrements rolling level, then selects
  the ordinary pose even if the level remains nonzero. The existing shared
  helper incorrectly continued to alternate rolling animation. The jump exposes
  this at 1691. Its phase/level fields already serialize; DRAGSTER gates must
  remain frozen while changing this shared helper.
- `$81:982C–996F`: the landing matrix selection uses the signed coarse motion
  angle. `$81:996F–99C6` then clamps a separately transformed direction by
  displacement quadrant for orientation response. Conflating these directions
  caused an intermediate opponent mismatch at 1667; this was corrected from
  the original writer trace without modifying expected results.
- `$81:935B–9477`: a nontrivial direction difference produces an orientation
  impulse from prior displacement, `(displacement >> 2) + 1`, with original
  sign. Short airtime clears the temporary response-A but retains this impulse.
  It decays through the existing pose update in following frames. Incoming
  response channels and impulse, contact duration/history and the resulting
  impulse were already in the canonical state. Matrix coefficients remain the
  immutable pre-race M4-12 extraction; no new content is needed.
- `$0F5D` is a derived winning-leading-probe predicate, not persistent state.
  The new reducer records it; unrecovered leading-probe landing response rejects
  explicitly. Nonzero incoming response, low prior displacement, long airtime,
  unsupported geometry and changed option guards remain outside this domain.

All reached future-affecting state is in the existing 395-byte record or an
explicit authenticated constant/guard from R-0030 plus `$132B`. Both riders use
native updates from one seed; no captured later state, ROM execution or camera
repair is supplied. The scoped player boost stays below the existing camera
predicate boundary. No frontend/presentation dispatch is added.

## Implemented reproduction and candidate checks

Use the worktree cache layout in BUILD_AND_VALIDATION. Set `CORE` from the
verified prior `samples.json`; static content is available at
`../m4-12-native-zoom-zoo/artifacts/m4-12/extracted-content` relative to this
checkout, and must pass the harness's complete identity check.

```sh
python3 tools/project.py build --preset app-debug
python3 -m tools.unirally_lab.native.zoom_zoo_player_landing capture --case tests/manifests/native/zoom-zoo-player-landing-primary.case.json --core "$CORE" --out artifacts/m4-13/primary-c.json
python3 -m tools.unirally_lab.native.zoom_zoo_player_landing capture --case tests/manifests/native/zoom-zoo-player-landing-primary.case.json --core "$CORE" --out artifacts/m4-13/primary-d.json
python3 -m tools.unirally_lab.native.zoom_zoo_player_landing compare --reference artifacts/m4-13/primary-c.json --repeat artifacts/m4-13/primary-d.json --contract tests/manifests/native/zoom-zoo-player-landing-primary.freeze.json --binary build/app-debug/src/core/zoom_zoo_runner --content-dir ../m4-12-native-zoom-zoo/artifacts/m4-12/extracted-content --out artifacts/m4-13/primary-report.json
```

Capture outputs must be fresh; use another suffix to reproduce. Each original
process is bounded to 180 seconds; native subprocesses to 30. Independent cases
are selected and committed before evaluation, then captured twice and frozen
with `zoom_zoo_player_landing freeze --reference A --repeat B --out CONTRACT`
before comparison. That command requires an actual player recontact and at least
100 subsequent updates in the fixed horizon. Restores automatically straddle
all full player landings in the case. Captures that miss this criterion cannot
be counted as acceptance evidence.

Initial focused checks: all 21 CTests and three original trial protocol Python
tests pass. Primary comparison passes 200 exact updates and fresh native restores
1744/1745/1761/1762. Accepted M4-12 primary and its three restores also pass.
Independent cases/review, full corrected-source gates, denied-reference runtime
experiment and final private main synchronization/CI remain pending.
