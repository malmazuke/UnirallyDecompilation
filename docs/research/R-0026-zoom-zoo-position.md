# R-0026 — ZOOM ZOO position integration and residue recurrence

- Task: [M4-08](../../tasks/M4-08.md)
- Status: review candidate; production native behavior is unchanged
- Source: PAL ROM SHA-256
  `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`;
  bsnes `7d5aa1e656b9171524d01b1b22917197d8121cb4`; patch
  `a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885`;
  strict serialization and default options
- Domain: 102 ordered player/opponent calls to `$82:A627--A6F7` on frames
  1650--1700, recurrent from one authenticated end-1649 seed

## Outcome and capture integrity

The implementation commit is
`e590babdb3d3408f69c29808029cb78fdc61df82`. Two fresh primary captures are
byte-identical: access SHA-256
`a53e6617baaf476e5d45c13ff60ec7ef2bfb677c5d6dfd0fe169ad919d915c2f`
and work-RAM series SHA-256
`53c03d228999d3c1fbe5ee22be64a3965a77848e9b8f8adbeaba4374cba3d13d`.
Each contains 953,416 instructions and 471,721 accesses, zero unresolved
stores, zero PCs outside ROM and maximum ring use 18,640 of 262,144. The
1,163 unresolved reads are retained and reported; none supplies a computed
value. No capture overflow or truncation occurred.

Both captures independently authenticate the same end-of-frame 1649 seed:
player `(x=9200, y=1561, rx=-1, ry=22)`, opponent
`(x=8248, y=1452, rx=-24, ry=-1)`. Its complete 0x2200-byte row hashes to
`064dea0e95ffdf1b11fc20d94fe7084a48ede5027ae6e270fd916d617d2be9f4`.
The track mask is `0x3fff` throughout the declared frames. The 209 original
routine bytes at ROM offset `0x12627` hash to
`1b6497ea4306faa243c685f0f23b9ac7d22232db57ce3299f4627bbc22291adc`.

The component propagates all four residues from that seed and exactly matches
every captured wrapped total, magnitude, quotient, residue, integrated x/y,
slope-tail y and caller publication for all 102 calls. Its canonical row SHA
is `aaf2eb99f1a4f80024947a7a65908f91d671efe17ecb0b4c6065bec762551bfe`;
the complete report hashes to
`e6a787e8cebf9f77cfdf37f3126485974230c06125fbb29904aabeca186d1254`.
Position, velocity and contact state are explicit captured inputs, not claims
of autonomous movement.

## Original integer order

For each axis the reached 16-bit path is:

`total = u16(velocity + incoming_residue)`

If `total` is negative, the original takes its two's-complement magnitude,
uses logical shifts for unsigned division by 32, then restores the signs of
both quotient and remainder. Otherwise it divides the nonnegative total
directly. Thus the signed result truncates toward zero and the remainder has
the dividend's sign. Position addition wraps to 16 bits. X then applies
`position &= 0x3fff`; Y does not. The capture includes a positive velocity plus
negative residue crossing to total -10 and therefore proves that the total's
sign selects the arithmetic path. A negative-velocity/nonnegative-total
crossing is not reached and rejects rather than being invented.

The post-integration Y tail preserves the instruction order: zero surface;
nonzero guard; signed `(unsupported_count - 2) >= 0`; direction high bit;
negative vertical velocity (`-1`); nonzero mode (`+1`); otherwise `+4`.
Primary reaches 68 zero-surface calls, 20 ordinary `+4` calls and 14 negative
velocity `-1` calls. No wrap boundary is crossed in this episode; wrap and
mask order are instruction-derived and mutation-tested, not presented as a
captured wrap-crossing observation.

## `$82:A6E9` provenance

The earlier access record left the direct-page operand of `ADC $A7` unresolved.
The dedicated capture records every routine instruction, `$A7`, and the
accumulator at both `$82:A6E9` and `$82:A6EB`. On each reached `+4` call, the
same call's integrated Y is produced at `$82:A6B9` (or `$82:A69B` on the
negative-total route), the accumulator entering `$82:A6E9` is exactly 4, and
the accumulator before `$82:A6EB` is `u16(producer + 4)`. The verifier requires
this ordered producer/register relation. There is no guessed or default value.

## Worker variation

The preregistered replay releases Right only at frame 1662 and restores it at
1663. Before execution, only exact agreement through 1661 and first controller
divergence at 1662 were predicted; contact timing and reconvergence were left
open. The placeholder run correctly failed only its four zero expected-digest
checks while its two fresh processes agreed. After recording the observation,
two final fresh processes pass 24/24 with sample digest
`b56fe4c2c8dc87ed554b1467852a314fd762dbb83da3242c74109de8a8770661`,
final state `1b603f9b09199904c9ec358bf73d400eca70e0cf34e6e4c5206cfd0c63e3965d`
and aggregate A/V
`25f54d563d71d8e05092c59bad4cd677d4bacffb5377b063803aeccba8c43234`.
Primary-versus-variation replay comparison intentionally exits 1 with its
first WRAM/register divergence at 1662.

Two fresh variation captures are byte-identical at access SHA-256
`95cfe9601e44fdea27e327cc2b431383b9ecfe28aeadb039d84b8cf2a005d426`
and work-RAM series SHA-256
`a747635dd38af85363c9029915b4319993d437f7af22bbf720674a8dd15dca20`.
Each records 953,516 instructions, 471,815 accesses, zero unresolved stores,
zero PCs outside ROM and no overflow. The same seed independently closes all
102 calls at row SHA
`5ace936f8d5126dfa703b97af0a13f267976b21ee291c7a8866d64d8594f3028`;
the report is
`33c85f3a3d2186d2e16598b04eee50c093130209d250247af3d5224d63bc4b70`.

Controller `$0313` differs only at frame 1662. The player component first
differs at 1662 and remains different through the frame-1700 cap; the opponent
remains exact. The first slope-tail branch difference is frame 1678, with
branch differences at 1678--1681 and 1685. Variation newly reaches four
`unsupported_count_at_least_two` calls on 1678--1681; frame 1685 changes from
primary `+4` to zero-surface. These unpredicted timings are reported by the
comparison whose SHA is
`195c1bb7abb8f68cc5a20d89711ba7f11f4f07b2ccc245db9976a8ba8e6a639a`.

## Integrity and limits

Focused mutations reject changed source/capture/routine/series identities,
bad seed, reseeding, rider-chain swaps, call loss/order changes, missing or
changed branch evidence and incomplete producers. Arithmetic tests distinguish
signed magnitude/division/remainder order, post-add masking and slope-tail
guard/adjustment order. The authored manifests bind the complete row and branch
digests, so removing an adjustment or changing an observed intermediate fails.

This is bounded reference research. It does not implement native ZOOM ZOO,
autonomous contact/motion, later track regions, a captured wrap crossing,
finish, AI, camera, presentation, audio or Classic-pack expansion. ROM bytes,
routine bytes, work-RAM series, captures and reports remain ignored.

## Reproduction

```sh
python3 -m tools.unirally_lab.native.zoom_zoo_position capture --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --out artifacts/m4-08/primary-fresh-a
python3 -m tools.unirally_lab.native.zoom_zoo_position extract-routine --rom "$(cat local/rom-location.txt)" --out artifacts/m4-08/routine
python3 -m tools.unirally_lab.native.zoom_zoo_position verify --access artifacts/m4-08/primary-fresh-a/access.json --manifest tests/manifests/native/zoom-zoo-position-primary.reference.json --report artifacts/m4-08/primary-component.json
python3 tools/project.py replay compare --manifest tests/manifests/replay/race-crawler-zoom-zoo-right-release-1662.json --runs 2 --artifacts artifacts/m4-08/variation-final/runs --report artifacts/m4-08/variation-final/report.json
python3 -m tools.unirally_lab.native.zoom_zoo_position capture --manifest tests/manifests/replay/race-crawler-zoom-zoo-right-release-1662.json --out artifacts/m4-08/variation-capture-a
python3 -m tools.unirally_lab.native.zoom_zoo_position verify --access artifacts/m4-08/variation-capture-a/access.json --manifest tests/manifests/native/zoom-zoo-position-right-release-1662.reference.json --report artifacts/m4-08/variation-component.json
python3 -m tools.unirally_lab.native.zoom_zoo_position compare-inputs --primary-access artifacts/m4-08/primary-fresh-a/access.json --variation-access artifacts/m4-08/variation-capture-a/access.json --report artifacts/m4-08/variation-comparison.json
python3 -m unittest tests.tooling.test_zoom_zoo_position tests.tooling.test_zoom_zoo_contact tests.tooling.test_zoom_zoo_vertical_contact tests.tooling.test_zoom_zoo_reflected_vertical_contact -v
```

## Validation and non-passes

Clean implementation commit `e590bab` passes the focused M4-05--M4-08 suite
37/37. Debug and sanitizer each pass all 350 Python tests, all 20 CTest checks
and three fresh determinism processes at `0be347c529fadda9`; their reports bind
clean source, contain no failed/missing/skipped checks and hash to
`bc16a3776db34825ad7322190524da42bebc87cbef493afe0805069feccc39af`
and `a6d5ac7130763759ef5e6f599c0fdff1e8e8a02e70e1d284ef6b0a415c801a46`.
The M4-03 contract, frozen M4-05/M4-06/M4-07 components, unchanged 25-entry
pack and DRAGSTER finish plus restore boundaries 1600/3213/3453/3678 pass at
report hashes `8b3d2d4c...a768f`, `01cc1b5c...ac70`,
`f4b38eaf...52f6`, `aff5212c...4aed`, `fc1050a9...8b17` and
`30fe00c7...0763` respectively. Their full values are
`8b3d2d4c79596f3d255fcc873052047060e64cf3560ad2676aabbbb23b7a768f`,
`01cc1b5cc27c7c03b20825f4f1daa4eddf86c7514a5c5e3b258548812fadac70`,
`f4b38eaf709a44679a30279bc9b2c83136e36526fb3e0469481bbd86dc4f52f6`,
`aff5212c7e5e523abcc6664ec51d2869be0b330fcdd55fea39b8a6e900eb4aed`,
`fc1050a9662925b16f8abcf855c30d7a07e6ffb19589b3032a6dfa16543e8b17`
and `30fe00c7f8b9ce1b87d3928d947a63cc79cc69d560aa95d78051f7eb06360763`.

The first build correctly reported the absent worktree-local toolchain. The
first synthetic run consequently skipped five native-report tests and reported
the native build missing; neither is counted as a pass. After configuring the
ignored local toolchain, clean runs passed. The initial contract attempt
without the ignored ROM locator likewise reported missing before the final
pass. The zero-placeholder replay and intentional primary/variation comparison
failures described above are retained. No provider block, reset or spending
occurred. Independent review remains required before acceptance.
