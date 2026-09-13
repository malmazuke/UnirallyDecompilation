# R-0022 — ZOOM ZOO riding reference and continuation boundary

- Task: [M4-04](../../tasks/M4-04.md)
- Status: accepted reference freeze; integrated as `4f7b248` after one returned
  integrity finding and approved focused re-review
- Source identity: PAL ROM SHA-256
  `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`
- Reference: bsnes `7d5aa1e656b9171524d01b1b22917197d8121cb4`,
  patch `a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885`,
  Strict serialization, default options, fresh private SRAM directory per run
- Domain: the accepted cold-start PAL 1P MIKE/CRAWLER/ZOOM ZOO primary and
  release-2500--2599 controller schedules through frame 3299. This is
  reference-only evidence; no native ZOOM ZOO, content-pack or presentation
  support is claimed.

## Outcome

Two additive field-bearing replay manifests preserve the accepted controller
schedules byte-for-byte at the manifest input level. Two fresh processes per
case reproduce complete frames 0--3299, every declared field, accepted whole-
WRAM/register sample and final-state identities, and aggregate A/V:

| Case | Accepted sample / final state | A/V | field rows 1649--3299 | projection file |
| --- | --- | --- | --- | --- |
| primary | `791a7863...57b68` / `2a843314...6aeb` | `dc7ca8ff...be22a` | `84bed2b1...18aae` | `130e4631...92766` |
| release 2500--2599 | `c253de4b...d63e` / `00bf36ed...127d` | `5f5388da...012e` | `5558632a...40949` | `90adf082...ba247` |

The tracked field-manifest hashes are `e6a02eea...a7426` and
`628822f8...db3e`; the accepted source manifests remain unchanged at
`acd29bfb...1aefd` and `66399d29...8ff7`. Each projection contains 1,651
contiguous end-of-frame rows: the candidate initial observation at 1649 and
updates 1650--3299. `freeze_zoom_zoo verify-pair` rejects loss, duplication,
row-width changes, changed projection metadata, contradictory seeds and any
first perturbation divergence other than frame 2500. It also verifies that
both original executions retain zero player/opponent finish flags and a zero
finish-delay counter throughout the projection; no finish or result transition
occurs in this bounded interval.

Following independent review, the public verifier also exact-binds the entire
canonical seed object at SHA-256
`d16d7576d556ac09adf842a890d68498db858c3f1c771fcfa499d181a398bc45`.
This covers every recorded value, memory/address/width/signedness inventory
entry, queue digest and source-provenance identity in addition to the WRAM and
cartridge-RAM dump hashes. Synchronously changing both projection copies can
therefore no longer make a contradictory candidate seed pass pair verification.

## Repeated continuation candidate

The boundary was declared before capture as end-of-frame 1649. Two separate
fresh original processes, each driven from one of the two complete primary
captures, produced identical memory:

| Memory | Size | SHA-256 |
| --- | ---: | --- |
| WRAM | 131,072 | `9c80a52a47706929c2a4a08a012799eb1163c3a6ccfd985e9be3cacae78d805e` |
| cartridge RAM | 8,192 | `cdd747a31846cfa03de238c622ea3154b396ef9d9d4541e2d6854b15866b7867` |
| WRAM reward queue `$0CEB-$0D0A` | 32 | `66687aadf862bd776c8fc18b8e9f8e20089714856ee233b3902a591d0d5f2925` |

The seed reports have distinct process ids and hashes `bd926492...d20f` and
`4b963547...7e67`. Both bind normalized manifest identity
`862b9941...25d`, derived controller script `2ced1e6e...ff1b`, the accepted
primary sample digest, full memory hashes and an explicit 124-field inventory.
Raw memory remains ignored. The tracked projection copies only the named
inventory, addresses, widths, signedness and values, not either dump.

Selected direct end-1649 values are:

| State | player | opponent | Address/interpretation |
| --- | ---: | ---: | --- |
| x / y | 9200 / 1561 | 8248 / 1452 | `$0415/$0419`, `$0417/$041B`; u16 coordinates |
| vx / vy | 0 / 0 | -448 / -78 | `$04BB/$04BF`, `$04BD/$04C1`; s16, 1/32 coordinate units |
| pose / reflection | 1468 / 0 | 805 / 0 | `$0411/$0BA7`, `$0413/$0BA9`; u16 pose, binary word |
| unsupported count / duration | 0 / 0 | 9 / 20 | `$054B/$0FC1`, `$054D/$0FC3`; u16 |
| marker / transition / tag | 22528 / 12 / 0 | 30720 / 12 / 6 | `$0FC5/$0FC9/$0FCD` and adjacent opponent words; opaque u16 progress recurrence |

Shared values are contact/progress phase 1/1 (`$0300/$0302`, u8), neutral
JOY1H/horizontal axis 0/1 (`$0313/$0319`, u8), countdown 1 (`$11C5`, u16),
timer digits `0:01.3` with sub-tenth frame 2 (`$0E19/$0E1D/$0E21/$0E25/$0E29`,
u16), wrap mask `0x3FFF` (`$0D4F`, u16), queue read/write 0/1
(`$0D11/$0D13`, u8), cooldown 6 (`$0CA7`, u16), learned event-one weight 4
(`$7E:2102`, u8), and learned feature total 0 at cartridge RAM `$77:0825`
(u16). The zero feature total is a direct read, not a default. R-0011 shows
that this SRAM word changes AI decisions after reward feedback; the complete
cartridge image is therefore part of the candidate even though only this word
has an established riding meaning.

The inventory also carries both riders' fractional residues, prior contact
counts/positions, surface/sentinel/auxiliary/selected state, response words,
jump latches/baselines, orientation/pose history, quarter tracking, speed
modifiers and opponent AI/reward queue continuation. Exact addresses and widths
are machine-readable under each projection's `seed.inventory`. This is a
candidate sufficient-state boundary for a later task, not proof that every
future dependency has been found and not permission to replace an unobserved
field with zero.

## Field mapping and sampling phase

All replay fields are sampled after `retro_run` for their numbered frame.
Multi-byte values are little-endian. Signed values retain original 16-bit
bit patterns and are interpreted as two's-complement only where R-0011
established that arithmetic. The most important row mappings are:

| Projection | Persistent source | Width / interpretation | observed producer or consumer |
| --- | --- | --- | --- |
| input images / axes | `$0311,$0313,$0315,$0319` | u8 | `$80:87EC/$80:87F2`, `$82:AB36/$82:AB52` |
| pose / reflection | `$0411/$0413`, `$0BA7/$0BA9` | u16 / binary u16 | pose publish `$83:CD8E`; contact caller reads `$81:8D12/$81:8E6C` |
| x/y | `$0415/$0417`, `$0419/$041B` | u16 coordinate | motion `$82:8DB9` family, contact publication `$81:8E17/$81:8F6B` |
| vx/vy and residues | `$04BB-$04C1`, `$0401-$0407` | s16, 1/32 units / signed remainder | integration `$82:A627-$82:A6F7`; contact publication |
| contact count/duration | `$054B/$054D`, `$0FC1/$0FC3` | u16 | response `$81:8F98-$81:982B`; caller publication |
| contact geometry state | `$04D7-$04ED`, `$0B6E-$0B74`, `$0E9F/$0EA1` | u16; surface signed where established | sample/reduction `$81:8B66-$81:9235` and response |
| progress marker/count/tag | `$0FC5-$0FCF` | opaque u16 recurrence | sampled after contact; R-0010/R-0011 progress consumers |
| throttle | `$0BEB/$0BED` | s16 | `$82:98E4-$82:9A4F` family |
| timer | `$0E19-$0E29`, four-byte slots | five u16 digits | `$81:C6C9/$81:C6ED` family |
| learned state | `$7E:2102` / `$77:0825` | u8 / u16 | reward consumer `$81:C260-$81:C280` |

The six access records deliberately cover only 18 frames total: 1649--1651,
1671--1673, 2199--2201, 2259--2261, 2499--2501 and 2599--2601. Each record is
complete and nontruncated, has no ring overflow, no unresolved stores and no
PC outside ROM. Separate PC snapshot arrays are used only for register values;
ordering claims below use watched access sequence numbers.

At frame 1650, the observed order includes JOY1H 1 written by `$80:87F2` at
sequence 582, horizontal axis 2 written by `$82:AB52` at 848, player motion
state reads from 1159, integrated/published x/y at 2188/2190, velocity writes
at 2264/2266, track/sample setup from 3350, new pose publication at 4528/4530,
contact input reads from 4541, and corrected player publication at 6028--6034.
This confirms input -> motion -> pose -> contact for this window without using
the unordered PC arrays as cross-PC evidence.

The reward window independently shows cartridge total `$77:0825` written to 4
at sequence 5343 by `$81:C274`, with learned weight `$7E:2102` read as 4 at
`$81:C260` and written as 2 at `$81:C280`; the end-frame field change is 4 to
2 at frame 1672. Queue read cursor changes 0 to 1, cooldown 2 to 40 and then
38 on 1671/1672/1673. These are observed values only; other reward events are
outside this task.

## Boundary perturbations

The primary and release projections are identical for every field through
frame 2499. At frame 2500, and not earlier, the release case changes JOY1H
1 to 0 and horizontal axis 2 to 1. In the same update its player x is
13996 rather than 13997, x residue 21 rather than 14, vx 413 rather than 438,
vy -207 rather than -220 and throttle 0 rather than 432. This is the predicted
original motion response, not a native comparison. At frame 2600 input returns
to Right: JOY1H/axis become 1/2, throttle becomes 16 and then 32; vx changes
from -305 at 2599 to -285 and -265 while x continues 13788, 13779, 13771.

The primary Up entry is likewise explicit: frame 2199 has JOY1H 1/vertical
axis 1, frame 2200 has 9/0, and frame 2201 retains 9/0. At release, frame 2259
has 9/0 and frame 2260 has 1/1. The tracked task does not assign an unobserved
high-level trick meaning to these changes. A reviewer owns a fresh one-frame
Up entry or release shift.

## First native-domain blocker

The first observed incompatibility after the proposed boundary is the track
sampler on update 1650. Original snapshots at `$81:8AA1` and `$81:8AC0` carry
Y=256 for both rider calls, consistent with the accepted width 256/stride 512.
The end-frame field and six observed reads retain `$0D4F=0x3FFF`; no write to
that word occurs in the window. Current native `update_movement` instead calls
`sample_track(..., 1024)`, and `integrate_motion` wraps only through u16 rather
than the track mask. The Classic profile also has no ZOOM ZOO static content.
These are readiness guards, not authorization to alter native or pack code.

Even if a later task supplies correct content and width, the first original
player sample set on frame 1650 exposes the next contact prerequisite. The ten
`$81:8B6A` reads occur point 9 down to point 0; reordered by collision-point
index they are nine `0x5800` descriptors followed by `0x1AE6`. Point 0 is thus
`0x5800`, whose `0x4000` direction bit violates the current native
`(descriptor & 0xC001) == 0` flat-contact guard before response. This is a
precise observed branch; the meaning or response formula for that bit remains
unrecovered.

The existing 1700/2220 checks reinforce, but do not move, that first blocker.
At end 1700 player/opponent x,y are 9824/1605 and 7489/1520; velocities are
487/241 and -494/0; poses/reflections are 2192/1 and 2133/0; surface angles
are 8/0 and selected words `0x4CE0/0x0802`. At end 2220 they are
13577/1746 and 11530/3482; velocities 30/-16 and 464/230;
poses/reflections 459/1 and 2192/1; angles -8/8 and selected words
`0x08E2/0x40CE`. M4-03's position values are the pre-contact call inputs, so
their slightly higher y values are not contradictory to these end-frame rows.
Directional descriptors, non-flat angles and reflection are all outside the
current flat-contact native domain. No formulas for those branches are inferred.

## Reproduction and artifact identities

```sh
python3 tools/project.py replay compare --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300-riding-fields.json --runs 2 --artifacts artifacts/m4-04/primary-final/runs --report artifacts/m4-04/primary-final/report.json
python3 tools/project.py replay compare --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300-release-2500-2599-riding-fields.json --runs 2 --artifacts artifacts/m4-04/release-final/runs --report artifacts/m4-04/release-final/report.json
python3 -m tools.unirally_lab.native.freeze_zoom_zoo capture-seed --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300-riding-fields.json --samples artifacts/m4-04/primary-final/runs/run1-samples.json --out artifacts/m4-04/seed-final-1
python3 -m tools.unirally_lab.native.freeze_zoom_zoo capture-seed --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300-riding-fields.json --samples artifacts/m4-04/primary-final/runs/run2-samples.json --out artifacts/m4-04/seed-final-2
python3 -m tools.unirally_lab.native.freeze_zoom_zoo verify-pair --primary tests/manifests/native/zoom-zoo-primary.reference.json --release tests/manifests/native/zoom-zoo-release-2500-2599.reference.json
python3 -m tools.unirally_lab.native.zoom_zoo_windows --window start --out artifacts/m4-04/windows/start
python3 -m tools.unirally_lab.native.zoom_zoo_windows --window reward --out artifacts/m4-04/windows/reward
python3 -m tools.unirally_lab.native.zoom_zoo_windows --window up-entry --out artifacts/m4-04/windows/up-entry
python3 -m tools.unirally_lab.native.zoom_zoo_windows --window up-exit --out artifacts/m4-04/windows/up-exit
python3 -m tools.unirally_lab.native.zoom_zoo_windows --window release-entry --out artifacts/m4-04/windows/release-entry
python3 -m tools.unirally_lab.native.zoom_zoo_windows --window release-exit --out artifacts/m4-04/windows/release-exit
```

The replay reports hash to `e67b89be...6d20` and `2cb37d33...a1a2`.
Access-record SHA-256 values, in the window order above, are
`1243dbe5...a269`, `00c6d5d1...1b94`, `270089cb...2eb`,
`5a518f37...305a`, `115c7009...e8a6`, and `69910902...0b3`.
All original captures, ROM bytes and direct memory dumps remain ignored.

## Limits and next experiment

This task freezes a reproducible reference boundary; it does not prove native
continuation readiness. The smallest next prerequisite is a separate reviewed
ZOOM ZOO profile/content decision followed by recovery of the frame-1650
directional contact preprocessing/response branch. That task must pass width
256 and wrap-mask `0x3FFF` as state/content rather than track-name conditionals,
and must derive behavior from new original traces. AI, finish, camera, audio,
result presentation and general track formats remain outside this evidence.
