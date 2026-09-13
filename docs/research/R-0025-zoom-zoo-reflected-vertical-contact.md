# R-0025 — ZOOM ZOO reflected vertical-contact suffix

- Task: [M4-07](../../tasks/M4-07.md)
- Status: worker candidate for independent review; production native behavior
  remains unchanged
- Source: PAL ROM SHA-256
  `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`;
  bsnes `7d5aa1e656b9171524d01b1b22917197d8121cb4`; patch
  `a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885`;
  strict serialization and default options
- Domain: the 36 ordered calls/360 point paths on frames 1683--1700,
  composed with the accepted M4-06 prefix to 102 calls/1,020 points

## Outcome and capture integrity

Two fresh primary captures through frame 1700 are byte-identical at SHA-256
`267ecfbf7223a3c2a9e6844d620feda0c41adb98fd9a5280d10320d3682fab67`.
Each contains 935,313 instructions and 462,784 accesses, with zero unresolved
stores, zero PCs outside ROM and maximum ring use 18,640 of 262,144. The full
order is player then opponent on all 51 frames. The new suffix is exactly 36
calls/360 points: all 18 player calls use only descriptor mask `0x4000`, while
all 18 opponent calls stay in the accepted flat family. No active suffix point
uses `0x8000`, bit zero or a horizontal tile flag.

The exact primary component report hashes to
`aff5212c7e5e523abcc6664ec51d2869be0b330fcdd55fea39b8a6e900eb4aed`.
It independently recomputes all 360 suffix preprocessing tuples and downstream
fields, and re-executes the unchanged M4-06 calculation for the 66-call/660-
point prefix. Captured outputs are comparison oracles, never computational
inputs. The composed result is 102 calls/1,020 points.

## Original reflected preprocessing

The instruction-width and branch inventory was completed before implementing
the equations; its durable checkpoint is [the M4-07 inventory](../inventory/M4-07-reflected-vertical.md).
At `$81:8BE3/$81:8BE9`, 16-bit masks separate `0x8000` and `0x4000`. The reached
`0x4000` path then runs with an 8-bit accumulator. `$81:8C2C--8C3C` chooses the
reflected collision-point x and `$81:8C9E--8CA9` applies the same choice to the
table column:

`column = (~(point_x + (incoming_x & 15))) & 15`.

This is `15 - direct_column` modulo 16. It is observably distinct at frame
1683 point 9, where direct-column lookup would produce table angle 1 but the
reflected column produces table angle 0, matching the capture. The original
reads height first at `$81:8CBB`, decrements it, then subtracts from local y at
`$81:8CCC--8CD3`, preserving wrapped byte penetration. It reads the table angle
at `$81:8CDD` and, because the `0x4000` word is nonzero, byte-negates it with
`EOR #$FF; INC` at `$81:8CE6--8CE8`. The resulting supported angles progress
from zero through +8.

The established ascending reducer remains unchanged: signed-byte comparison,
equal-depth update order, selected descriptor/high-byte predicates and signed
penetration exclusion from correction are all retained. Exact comparison of
each tuple prevents a lossy final summary from hiding a changed nonselected
point.

## Positive-slope response and content

For observed angle `a` in 0..8, `$81:973D--9747` reads shift
`S[a]` from `$00:822B+a` and multiplier `M[a]` from `$00:824B+a`.
`$81:9749--9760` performs signed 16-bit arithmetic shift on incoming vx and
stores the quotient. `$81:9763--9771` multiplies by repeated addition. The
positive path at `$81:9774--977E` retains that product, while the already
accepted negative path transforms it to `-product+1`. Thus the suffix uses:

`vy = u16(arithmetic_shift(vx, S[a]) * M[a])`.

`$81:97B7--97CA` computes `a >> 1`, and `$81:97DB--97E1` adds that contribution
to vx after the response guard:

`vx = u16(vx + (a >> 1))`.

The newly reached indices 6--8 are shifts `04 04 01` and multipliers
`06 07 01`. Their six-byte SHA-256 is
`e32ed598f27c7952d051d67438db3bdced18bf69c6963a5cf1450c8cc8c0c184`.
The independently extracted index-0--8 table payload is 18 bytes with SHA-256
`f5016c76c1f4e60c988c67672b12da1d3b10948934f5f1e8b29135274203e7a1`.
No alternate-table or unobserved coefficient claim is made.

The component compares corrected position, vx/vy, response channels, counters,
previous uncorrected coordinates, surface angle, sentinel and auxiliary state,
selected word/high byte, recontact flag, shifted-velocity scratch and signed
half-angle contribution before accepting caller publication. Unobserved
descriptor combinations, horizontal flags, unsupported/recontact state,
special/mode paths and angles beyond +8 reject explicitly.

## Worker variation

The preregistered variation releases Right for frame 1684 only and restores it
at 1685, retaining every other primary event. Before observing the run, the
only prediction was exact primary state through frame 1683 and first controller
divergence at 1684; contact timing and reconvergence were not predicted.

The first placeholder-identity replay correctly exited 1 while its two fresh
processes agreed. After recording the result, two final fresh processes pass
with sample digest
`5685c085bb62aec5d93515197183d5fa0e3b469bdc19b36bcc568318b64d43eb`,
final state
`037fee6dd7e6003ebca34ab45a16d7b70c95ac554d4d48b68658877df697eb00`
and aggregate A/V
`d25c5f4644f59b3419498f64ec61fb9cd99fd3dadb20dc18de8de60396ee46df`.
Primary-versus-variation comparison intentionally exits 1 at the exact first
divergence frame 1684. The component's positive claim comparison hashes to
`5a6098f913dfb9e9b545aae0fa3e601f220a124cc2654d650a6d0c8f45eaa305`.

Two fresh variation contact captures are byte-identical at
`4161f1de56bfe6bf893ab2a26ce6355d8fdb8109e20aeaf9dd6274a25d7762a9`
and likewise have zero unresolved stores, zero PCs outside ROM and no ring
overflow. Through the bounded frame-1700 cap they exercise the same contact
tuples and branches as primary; this is reported honestly as no new contact
class. Their exact composed component report hashes to
`6550e369d11ca9d5c0683483c9c9ad430824f404a111039a0c4ac3a05cfc96c9`.

## Reproduction

```sh
python3 tools/project.py content zoom-zoo-contract --contract tests/manifests/content/zoom-zoo-reference-contract.json --report artifacts/m4-07/foundation-contract.json
python3 -m tools.unirally_lab.native.freeze_zoom_zoo verify-pair --primary tests/manifests/native/zoom-zoo-primary.reference.json --release tests/manifests/native/zoom-zoo-release-2500-2599.reference.json
python3 -m unittest tests.tooling.test_zoom_zoo_contact tests.tooling.test_zoom_zoo_vertical_contact tests.tooling.test_zoom_zoo_reflected_vertical_contact -v
python3 -m tools.unirally_lab.native.zoom_zoo_contact capture --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --out artifacts/m4-07/primary-1650-1700-a --from-frame 1650 --to-frame 1700
python3 -m tools.unirally_lab.native.zoom_zoo_contact capture --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --out artifacts/m4-07/primary-1650-1700-b --from-frame 1650 --to-frame 1700
python3 -m tools.unirally_lab.native.zoom_zoo_reflected_vertical_contact extract-content --contract tests/manifests/content/zoom-zoo-reference-contract.json --rom "$(cat local/rom-location.txt)" --out artifacts/m4-07/reflected-content
python3 -m tools.unirally_lab.native.zoom_zoo_reflected_vertical_contact verify --access artifacts/m4-07/primary-1650-1700-a/access.json --content artifacts/m4-07/reflected-content --manifest tests/manifests/native/zoom-zoo-reflected-vertical-primary.reference.json --report artifacts/m4-07/primary-component.json
python3 tools/project.py replay compare --manifest tests/manifests/replay/race-crawler-zoom-zoo-right-release-1684.json --runs 2 --artifacts artifacts/m4-07/variation-final/runs --report artifacts/m4-07/variation-final/report.json
python3 -m tools.unirally_lab.native.zoom_zoo_contact capture --manifest tests/manifests/replay/race-crawler-zoom-zoo-right-release-1684.json --out artifacts/m4-07/variation-contact-a --from-frame 1650 --to-frame 1700
python3 -m tools.unirally_lab.native.zoom_zoo_reflected_vertical_contact verify --access artifacts/m4-07/variation-contact-a/access.json --content artifacts/m4-07/reflected-content --manifest tests/manifests/native/zoom-zoo-reflected-vertical-right-release-1684.reference.json --report artifacts/m4-07/variation-component.json
python3 -m tools.unirally_lab.native.zoom_zoo_reflected_vertical_contact compare-inputs --primary artifacts/m4-07/primary-1650-1700-a/samples.json --variation artifacts/m4-07/variation-contact-a/samples.json --report artifacts/m4-07/variation-comparison.json
```

The new research module implements `extract-content`, `verify` and
`compare-inputs`. Capture deliberately reuses the accepted M4-05
`zoom_zoo_contact capture` surface because its complete watch set includes the
preprocessing, reducer, response and caller-publication landmarks needed here.

## Limits

This is bounded captured-argument evaluation, not autonomous recurrence or
production native ZOOM ZOO. Frame 1700 is an observation cap. Horizontal,
`0x8000`, bit-zero and mixed descriptor geometry, later track paths, finish,
AI, camera, presentation, audio and Classic-pack expansion remain outside the
claim. ROM bytes, extracted content, access records and reports remain ignored.
Independent review is required before acceptance.

## Clean candidate validation

Implementation commit `28cafed5768d8970308de92f22f03ade708b4013` passes
the focused M4-05/M4-06/M4-07 suite 29/29. Clean debug and sanitizer runs each
pass 342 Python tests represented by 342 checks, all 20 CTest checks and three
fresh determinism processes at `0be347c529fadda9`. Their reports contain no
failed, missing or skipped required check and hash to
`84c84a33108e31cb7bb936c3c5fa7cc77ada16a0d9f4f1f8a1f1cfab2e571801`
and `7a394aff1ff86ca548f3b9e63d1d4c8a4af311ef4185cac0077f8aa0b633d004`.

The clean M4-03 contract report hashes to
`81a2e00f3597616e361ec9e8959669e2be048eca7e56c5092dd5e6f9f15d52bc`;
the M4-04 pair remains exact. The unchanged 25-entry Classic pack report is
`bfb75ef90cfff187240233790d90b7aa2d18367baa9ecc0681be08d6f426d8cd`.
DRAGSTER finish with restore boundaries 1600/3213/3453/3678 passes all 18
checks at report SHA-256
`63364922428a1666bfc13f55fc18c544829e79700ef2011ada750f2aa5c5b8c3`.
