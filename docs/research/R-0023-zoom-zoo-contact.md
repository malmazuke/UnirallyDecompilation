# R-0023 — ZOOM ZOO contact-path audit

- Task: [M4-05](../../tasks/M4-05.md)
- Status: candidate research, pending independent review
- Base: claim commit `93a9efe6c40248d9dcd28137e54861d3c38aa3b7`
- Source: PAL ROM SHA-256
  `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`;
  bsnes `7d5aa1e656b9171524d01b1b22917197d8121cb4`; patch
  `a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885`;
  Strict serialization and default options
- Domain: both rider calls, in original execution order, on frames 1650--1700
  of the accepted cold-start 1P MIKE/CRAWLER/ZOOM ZOO primary schedule. The
  independently reconstructed branch is limited to its first incompatible call
  and the immediately preceding and following calls.

## Outcome

The 51-frame capture is complete: 102 calls, player then opponent on every
frame, with no trace overflow, truncation, unresolved store, failed frame or PC
outside ROM. Classification applies the original predicates in this order:
marker `(descriptor & 0x03ff) == 0`; direction/special
`(descriptor & 0xc001) != 0`; horizontal tile flag; nonzero surface angle;
negative penetration. The compact ordered result hashes to
`4f4c7fc0e0e6bf4fe89bfdaafe0d8fcc4824eb9214930507a17e42c97ec15dc4`:

| First failed guard | calls |
| --- | ---: |
| none (current flat-contact domain) | 67 |
| non-flat angle | 17 |
| direction or special | 18 |

This also corrects the earlier frame-1650 interpretation without changing any
accepted value. Player point 9 is `0x1ae6` and passes the direction mask. Player
points 0--8 are `0x5800`, and all ten opponent points are `0x7800`; those 19
words satisfy the earlier marker predicate and never reach the direction test.
Width 256, stride 512, wrap mask `0x3fff` and absent pack content remain
separate integration facts. The mask observation does not itself show a wrap.

The first genuine incompatibility is ordered call 22 (zero based): frame 1661,
player, collision point 9, `non_flat_angle`. Calls 0--21 are compatible under
the stated guard order. The first later direction/special failure is frame 1683,
so it is deliberately not reconstructed here.

## Captured arguments and independent content

`zoom_zoo_contact capture` watches the complete shared contact scratch
`$0230-$02f1`, raw arrays at `$0b5a`, direct-page response arguments and the
caller publications. It binds arguments to calls at the response boundary and
requires exactly `(frame 1650, rider 0)`, `(1650, 1)` through `(1700, 1)`, with
contiguous ordinals. PC snapshots are pre-instruction; only access-record
sequence numbers establish ordering.

The component does not reuse captured result bytes as inputs. Its content step
first runs the accepted M4-03 contract validator, then independently decodes
the track object and reads collision poses, templates, the 24 ordered tile
tables and flags from their authenticated ROM sources. It reads only the two
coefficient bytes reached by this first branch: `$00:822c = 4` and
`$00:824c = 1`. The six payload identities are:

| payload | bytes | SHA-256 |
| --- | ---: | --- |
| track data | 50,665 | `db6770152e399f9d16fc6937b5d56588a8f67e825ae70d6578b77d36053fdd28` |
| collision poses | 32,768 | `9d1754d38c20cb2900239557550211ab6fc23d9b0237e17b78fb29f3bf272c32` |
| collision templates | 17,249 | `2f03a8cb985899436603ef36b233b28f7b4213e4ba106fca328a6b02cdb081c7` |
| ordered tile tables | 6,496 | `649b96ff43ef467fe57bac16eb876f96a1ebc6f0307a5270f97a7ce1f63a84c7` |
| ordered tile flags | 203 | `11aa211a148bced17e6c1b63a19e6e9c71ff1f8fed83954613f2ea62b15069c4` |
| slope coefficients | 2 | `38b8bc5c86db41a80615b2f4694fc754cccffb95e8933d5b376021feab83cea3` |

The accepted content contract itself hashes to
`017a4eb941abb0e87ea0e3be4509d9043198466cb461f560517f355938c1d699`.
The generated content metadata hashes to
`7352761224b68a5e5e22f60992d1462f9d29e721d6d862e29783371471bcbb2b`.
ROM bytes and generated payloads remain ignored.

## First branch contract

The neighbourhood is frame 1660 opponent, frame 1661 player, then frame 1661
opponent. Every value below is a captured input or independently reconstructed
output compared with the observed original; no missing field is defaulted.

For the target player call, incoming x/y are 9258/1562, vx/vy are 287/19,
unsupported count/duration are 0/0 and phase is 1. Point 9 has descriptor
`0x0020`: marker false, direction/special false, tile index 8, tile flag 0,
local column 7 and local y 0. Ordered-table offset 270 contains height `0xff`
and angle `0xff`. Eight-bit wrapping gives penetration
`u8(0 - u8(0xff - 1)) = 2`. The other nine marker samples reduce to the
established empty values. Reduction therefore selects descriptor `0x0020`,
vertical correction 2, angle `0xff` (-1) and support summary 2.

The response sign-extends the angle to `0xffff`, clears the angle sentinel and
indexes the two static tables by `abs(-1)`. Shift 4 and multiplier 1 yield
`287 >> 4 = 17`; the negative-angle signed transform produces
`vy = -17 + 1 = -16` (`0xfff0`). Its horizontal contribution is
`-(abs(-1) >> 1) = 0`, so vx remains 287. The response saves the uncorrected
x/y 9258/1562, corrects y to 1560, and leaves count/duration at 0. Surface,
sentinel, velocities, saved coordinates, corrected position, counts,
selection and the remaining response words all match the original exactly.

Observed access order supports the calculation. At frame 1661, sequence 4604
reads point 9 at `$0262` and 4605 writes descriptor `0x0020` to `$02d2`;
4671 writes penetration 2 and 4678 writes angle `0xff`. The reducer reads that
penetration at 5081, publishes the selected descriptor at 5098, correction at
5121 and angle at 5125. Response sequences 5201/5211 publish surface/sentinel,
5261 computes the shifted x velocity, 5284 publishes vy, 5311 preserves vx,
5323 saves the incoming y, 5328 corrects y and 5330 saves x. Caller publication
then proceeds in access order through duration, marker/selection, response
channels, count, saved coordinates, corrected positions, velocities, previous
count, selected high byte and selected word.

The preceding opponent call remains unsupported: summary `0xff`, count 9,
duration 30 to 31, x/y 8094/1474 and vx/vy `0xfe40`/122 remain exact. The
following opponent call similarly advances duration 31 to 32 at x/y 8080/1479
and vx/vy `0xfe40`/138. This establishes read-before-write state across the
shared scratch boundary without widening the branch claim.

## Preregistered variation

Before execution the worker preregistered delaying first Right by two updates,
from frame 1650 to 1652, while retaining release at 3299 and all other events.
The prediction was exact agreement through end-frame 1649 and the first input
difference at frame 1650; neither contact timing nor reconvergence was promised.
This is intentionally distinct from the reviewer's undisclosed adjacent case.

Two fresh processes reproduce the variation exactly: sample digest
`31a092b8a80277c462d4aadc157f8bac05dae75f087c7e3c74385bb348`, final state
`d61def5c0330d35979fdee600ab2bf52d495d0bbfa79694cdf197f5694ab182c`
and aggregate A/V
`39fca18e630cb5d612617f202e709c5f3b7ad5881598e02e97b728970f4614ad`.
The primary comparison first differs at frame 1650 as predicted and does not
reconverge through 1700 for player contact; all 51 opponent calls remain exact
for the captured argument, reduction, response and publication fields.

The variation still has 102 ordered calls. It classifies as 70 compatible, 16
non-flat and 16 direction/special; its compact classification hashes to
`bb5aa59d1bc6a6e6ac0084b44767a194df37bf91c9af929350a4da8bcaca3c2d`.
Its first incompatibility moves to ordinal 26, frame 1663 player point 9, again
non-flat angle -1. Actual incoming y 1563 yields correction 3 and final y 1560;
x 9258, vx 287 and predicted vy -16 remain exact. This is a prediction from the
new captured arguments and immutable static content, not reuse of the primary
result.

## Integrity and reproduction

The component exact-compares every computed `(penetration, angle, descriptor)`
against the captured result before reduction. Its report includes computed and
captured values plus the match result for all ten points, in order, on each of
the preceding, target and following calls: the full ordered 30-tuple rather
than only its lossy reducer summary. The ROM-free focused tests mutate call
loss, duplication, order, rider and ordinal; guard/classification inputs;
incoming state and static coefficients; incomplete capture fields; and one
per-point preprocessing tuple while leaving the later summary unchanged. Each
contradiction fails or changes the reconstruction. Command verification also
exact-binds source ROM/core/patch/replay identities, access hash, frame range,
call count, guard order, classification digest/counts, first branch,
neighbourhood and all independent content identities.

```sh
python3 -m tools.unirally_lab.native.zoom_zoo_contact extract-content --contract tests/manifests/content/zoom-zoo-reference-contract.json --rom "$(cat local/rom-location.txt)" --out artifacts/m4-05/content
python3 -m tools.unirally_lab.native.zoom_zoo_contact capture --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --out artifacts/m4-05/final-primary-1650-1700 --from-frame 1650 --to-frame 1700
python3 -m tools.unirally_lab.native.zoom_zoo_contact verify --access artifacts/m4-05/final-primary-1650-1700/access.json --content artifacts/m4-05/content --manifest tests/manifests/native/zoom-zoo-contact-reference.json --report artifacts/m4-05/component-report.json
python3 -m unittest tests.tooling.test_zoom_zoo_contact -v
```

The reproduced M4-04 start access record hashes to
`1243dbe510368cebedd3af96b9e844af89a8c8f75aa61bcd287f4927a772a269`.
The primary and variation full access records hash to
`267ecfbf7223a3c2a9e6844d620feda0c41adb98fd9a5280d10320d3682fab67`
and `0f04150363bdfbf41f53ca192ee091529c36933950bfb74daa6eea8001178dec`.
The corrected successful component reports hash to
`01cc1b5cc27c7c03b20825f4f1daa4eddf86c7514a5c5e3b258548812fadac70`
and `89f46dd8406453b06eec24258215d61ac43e77b2622485e940f92745d014f0fc`.

## Limits

This is captured-argument reference research, not an autonomous movement
producer. It reconstructs only the first exercised -1 vertical-slope response
and state required for the adjacent calls. It does not recover later non-flat
or direction/special branches, horizontal/wrap cases, track sampling,
reflection, AI, finish, camera, presentation or audio. Production native code,
serialization, Classic pack/profile/start and all accepted projections,
manifests, core and locks are unchanged. A separate reviewed task must decide
whether and how this branch enters production.
