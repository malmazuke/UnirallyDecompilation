# R-0029 — bounded ZOOM ZOO vertical-velocity recurrence

- Status: worker candidate; bounded reference research awaiting independent
  review; production native behavior remains unchanged

## Scope and identity

This record removes both riders' vertical-velocity words from M4-10's per-call
captured inputs on frames 1650--1700. It seeds `$04BF/$04C1` once at end-1649,
executes the reached jump, gravity and vertical-cap paths in their observed
order, feeds the result through position integration and accepted contact, and
uses the contact result as the next same-rider velocity. Computed velocity and
the accepted computed response B are injected into the position/contact
composition. Horizontal velocity, pose/reflection, jump/control state, cap
modifier state and remaining contact state stay external inputs. This is a
bounded twelve-word recurrence, not autonomous ZOOM ZOO gameplay.

The supported PAL ROM SHA-256 is
`a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`.
The pinned bsnes core is `7d5aa1e656b9171524d01b1b22917197d8121cb4`
with patch
`a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885`.
The final local core library has SHA-256
`e59bf88d4fc922c9fe3b5438e65ff3a6909d24e1628f0f87141c8de17699a91b`.
Preregistration commit `3074725384790eb411f778e4c0a49f448361c5a9`
froze the full watch surface and the frame-1672 release prediction before new
results.

## Original routines and order

The inclusive `$82:A81A--A872` vertical-cap bytes hash to
`abfe21846d6e3d2f91bc649e510db6d5616fb5d7ea879192ec1aa5b8e72aac31`
(89 bytes). `$82:A8C9--A96E`, including jump dispatch and body, hashes to
`2a21e360ddac360508870de522d2a779c6e75bfdb21f46645690728302077078`
(166 bytes). The 68 gravity bytes at `$82:A96F--A9B2` retain accepted hash
`5f3d24df4c743df33e24d2febc24522cd2abe68fe5597ee2abf3ebfac413653c`.

Ordered events establish the actual bounded phase sequence as persistent load,
active-rider jump (or inactive preserve), gravity, vertical cap, position
integration, motion publication, contact load/response and contact publication.
Thus gravity precedes the cap in this episode; neither planning prose nor the
earlier DRAGSTER component was allowed to override the ordered ZOOM ZOO trace.
Phase `$0302=1` selects player and `0` selects opponent, yielding 51 active
jump calls and 51 inactive preserves.

All active calls pass the indexed inhibit, `$0F41`, `$0F5D` and direction-bit
guards. Held phase and jump latch are zero. Five calls preserve a previous
nonzero jump input and 46 see neutral input; all 51 publish the observed current
input to `$0FA5`, and none writes vertical velocity. Inputs following an
unreached branch remain unavailable in the model and tests.

The gravity predicate is the N flag from wrapped 16-bit `vy - 0x0200`. Every
call reaches the writer. For 23 negative inputs the addend is `0x10 + 3`; for
79 nonnegative inputs it performs five logical right shifts and adds
`0x10 - (vy >> 5) + 3`, all modulo 65536. The observed addend distribution is
19×73, 15×8, 14×5, 18×4, 17×4, 13×4, 16×3 and 12×1.

All 102 calls take ordinary cartridge mode. The cap is
`(extra >> 1) + 0x0300`, with extra 0--128 and caps 768--832. Its positive and
negative tests use wrapped subtraction signs; all bounded velocities preserve,
so there is no cap velocity store. The adjacent vertical-boost decrement writes
28 times and rejects wrapped underflow. Authored cases cover positive and
negative clamping, underflow, word semantics and unsupported cartridge modes
without claiming those clamp stores occurred in the primary capture.

## Capture, recurrence and composition

Two fresh primary captures are byte-identical at access SHA-256
`0bf7d3fbae726c20585a281f628ba42c72d9cff4405ee7c2d3fcd518df68467c`
and WRAM-series SHA-256
`53c03d228999d3c1fbe5ee22be64a3965a77848e9b8f8adbeaba4374cba3d13d`.
Each contains 953,416 instructions and 471,721 accesses. Two final fresh
variation captures agree at
`cc68b84031db523ef9a0ee50ce8956c50f4b69f89e24661746142d2d20b2e731`
and `62b24483d7f83eecfcee35077146b6238a9667a1deccb2734bb9db6aee5b3afd`,
with 953,403 instructions and 471,724 accesses. Every capture is complete and
nontruncated, has zero unresolved stores, zero non-ROM PCs and maximum ring use
18,640/262,144. The retained 1,163 unresolved reads never supply a computed
value.

The seed is player 0 and opponent 65458 (-78). All 102 rows match motion load,
jump publication, gravity write, cap result, integrator read, motion
publication, contact input/output and final persistent publication without a
later captured-velocity input. Corrected evidence rows hash to
`a158706a1003744fca35510b55dacd5185e45cb7c11e8615450c32198cbf79b2`;
final velocity is player 241 and opponent 0.

Computed velocity and response B preserve all 102 calls, 1,020 sample words
and source offsets. Sample/source hashes remain
`98e77e32b3540aa98e796edc5d7fb7c0bb2736e44e8e4b3ee1b4cf1827d188dd`
and `f24ccd2738300030debe07020d4140f4f8d0d6e8e711b0f8ea3d2a8cd526fa27`.
Both response-B words finish zero; final position/residue remains player
`(9824,1605,12,10)` and opponent `(7489,1520,-4,12)`.

## Worker variation

The finalized replay releases Right only at frame 1672 and restores it at
1673. Two fresh processes agree at sample digest
`66c45999667bda235318f90ca883ba56046a86dc8f999100fd0d287b2f410fe2`,
final state
`037fee6dd7e6003ebca34ab45a16d7b70c95ac554d4d48b68658877df697eb00`
and A/V digest
`d25c5f4644f59b3419498f64ec61fb9cd99fd3dadb20dc18de8de60396ee46df`.
The preregistered claim holds: exact through 1671 and controller divergence at
1672 only.

The full player composition first differs at 1672 and is still different at
1700; opponent composition remains exact. No sample word, response-B value or
vertical-velocity stage/result differs. The only final recurrent-position
difference is player x residue 11 rather than 12. This is an honest negative
relevance result for vertical velocity. Corrected variation evidence rows hash
to `4ef7dc607af6f2ba0a88c5a10137bda52393a08df635d553bb282384a27b3545`;
the comparison digest is
`4e09d547d3da9d00d2cf9effa40e58bfea34daea3f9d03044d6b6da67183b1ba`.

## Integrity, reproduction and limits

Exact-bound captures/manifests and ROM-free mutations cover source, seed,
rider/order, reseeding, captured substitution, phase/order, missing writer,
cap signed predicates, jump short-circuits, gravity shift/arithmetic and writer
width. Any changed capture event also changes the bound access identity.

Correction `f7ff0e39b8169be64da44dc1ebfb3fa2afd304fc` closes the independent
review's semantic-enforcement finding without recollection or arithmetic
changes. Every call now binds the single complete width-two `$83:F00D` pose
read to computed response B; those 102 `pose_consumed` values produce corrected
response evidence digest
`a40099baffbc778a0715de02100bf886e55c4c901bd259b80cf418175a86ac9e`.
All seven motion/contact boundary events must be complete width-two accesses.
The evaluator asserts the actual jump, gravity, cap/boost, integration, motion
publication, contact-response and final-publication sequence. It enumerates
every write overlapping `$0FAB` across each complete frame, classifies each
exactly once, and binds sequence, PC, width and value into the evidence rows.
The unchanged captures contain 102 motion scratch loads, 102 gravity writes,
zero cap writes, 102 contact scratch loads and 77 reached `$81:970B` contact
response writes, with no other `$0FAB` writer.

The preregistration replay intentionally ran while its expected sample and
final-state digests were still zero. Its four expected-digest checks failed,
while the two fresh processes agreed on samples, final state and A/V; those
observations were then frozen in the authored replay. A preliminary variation
capture made under the same placeholder identity likewise failed only its two
expected-digest checks, while still writing a complete, nontruncated capture.
It was not used as either of the two final variation captures. During additive
tool development, three derive attempts also rejected rather than silently
continuing: an initially misnamed residue field, the accepted M4-10 exact
access-identity boundary, and an incorrect long-read/register association were
fixed in the implementation. No expected result was weakened or regenerated
to conceal these non-passes.

```sh
python3 -m tools.unirally_lab.native.zoom_zoo_vertical_velocity capture --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --out artifacts/m4-11/primary-a
python3 -m tools.unirally_lab.native.zoom_zoo_vertical_velocity derive --access artifacts/m4-11/primary-a/access.json --content artifacts/m4-11/content --report artifacts/m4-11/primary-derived.json
python3 -m tools.unirally_lab.native.zoom_zoo_vertical_velocity verify --access artifacts/m4-11/primary-a/access.json --content artifacts/m4-11/content --manifest tests/manifests/native/zoom-zoo-vertical-velocity-primary.reference.json --report artifacts/m4-11/primary-verified.json
python3 -m tools.unirally_lab.native.zoom_zoo_vertical_velocity compare-inputs --primary-access artifacts/m4-11/primary-a/access.json --variation-access artifacts/m4-11/variation-final-a/access.json --content artifacts/m4-11/content --report artifacts/m4-11/variation-comparison.json
python3 -m unittest tests.tooling.test_zoom_zoo_position tests.tooling.test_zoom_zoo_contact tests.tooling.test_zoom_zoo_vertical_contact tests.tooling.test_zoom_zoo_reflected_vertical_contact tests.tooling.test_zoom_zoo_composition tests.tooling.test_zoom_zoo_response_b tests.tooling.test_zoom_zoo_vertical_velocity -v
```

This does not recover horizontal velocity, recurrent pose/reflection,
jump/control state, alternate cap modes, later track regions, finish, AI,
camera, presentation, audio or Classic-pack support. Original ROM bytes,
extracted content, captures and reports remain ignored. Independent review is
required before acceptance; final clean regression evidence is recorded in the
task handoff.
