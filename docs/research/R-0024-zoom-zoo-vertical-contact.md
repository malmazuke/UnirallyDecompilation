# R-0024 — ZOOM ZOO bounded vertical-contact episode

- Task: [M4-06](../../tasks/M4-06.md)
- Status: candidate captured-argument reference research; production native
  behavior is unchanged
- Implementation: `0f33993b12f88fea556f542570cc1e1e45c9fc1a` plus comparison
  hardening `908cde857aa7a67cd2a14e4b8a8c5a5351e05373`
- Source: PAL ROM SHA-256
  `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`;
  bsnes `7d5aa1e656b9171524d01b1b22917197d8121cb4`; patch
  `a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885`;
  strict serialization and default options
- Domain: every ordered player/opponent contact call on primary frames
  1650--1682, and every call preceding the independently observed
  direction/special boundary in the first-Right-at-1653 variation

## Outcome

The primary capture contains exactly 66 calls and 660 point paths. All point
preprocessing tuples, meaningful axis writes, reducer outputs, response
scratch, state changes and caller publications reconstruct exactly from
captured incoming arguments and separately authenticated content. Captured
outputs are comparison oracles only. The primary component report passes with
SHA-256 `f4b38eaf709a44679a30279bc9b2c83136e36526fb3e0469481bbd86dc4f52f6`.

The full inventory classifies 49 calls as compatible and 17 as non-flat, with
no direction/special call in the bounded primary interval. Its compact
classification hashes to
`f480ef6841d9c52de16dfb3203ac1ea1eda0648b55b6478e874472627bae574c`.
The reconstructed response branches comprise 41 continuous calls, 24
unsupported calls and one opponent recontact. Observed winning reducer angles
include flat zero and signed -1 through -5. The internal `0xe0` sentinel is
preserved on unsupported calls and is not treated as a slope.

Two fresh primary captures are byte-identical at SHA-256
`c270cb19d28cab4e07044fcbde8e673f09c3aa79eeb13d3614f9b1e52a080f05`.
Each is complete and nontruncated: 605,370 instructions, 300,346 accesses,
zero unresolved stores, zero PCs outside ROM and maximum instruction-ring use
18,640 of 262,144. The 768 unresolved accesses are non-store residuals and no
claim depends on them.

## Recovered bounded equations

The reducer walks points 1--9 in ascending order after requiring the first
point to be the established empty sentinel. Comparisons reproduce the N flag
after eight-bit subtraction: `N(u8(left - right)) == 0`. A nonempty point can
therefore win the support summary even when its penetration byte is signed
negative. The later BMI excludes such a byte from vertical correction. Equal
values update in point order, so order and ties are observable. Selected-word,
last-winning-angle and selected-high-byte updates retain their distinct
predicates; the latter is not derived from the final word after the fact.

For a supported signed angle `a` in the observed range -5..0, the component
reads shift `S[abs(a)]` from `$00:822b` and multiplier `M[abs(a)]` from
`$00:824b`. The authenticated 12 bytes are
`00 04 04 04 02 04 00 01 02 03 01 05`, SHA-256
`33cde9a32f2ba289253c747ffa9119a006ab4887766cec642ebef4b50acd9f86`.
With signed sixteen-bit arithmetic shift,
`q = arithmetic_shift(vx, S[abs(a)])`; the observed negative-slope path sets
`vy = u16(-(q * M[abs(a)]) + 1)` and
`vx = u16(vx - (abs(a) >> 1))`. This remains active for negative incoming
vertical velocity; there is no earlier sign short-circuit. Position correction
then sets `y = u16(incoming_y - vertical_correction)`.

Unsupported calls increment duration modulo 16 bits, saturate unsupported
count at nine, set the angle sentinel and leave incoming motion otherwise
unchanged before vertical correction. Reacquisition clears both counters.
The sole bounded recontact, opponent frame 1667, is computed from captured
incoming current/previous coordinates: absolute dx 14, absolute half-dy 4,
coarse angle 4 and bucket sentinel `0xffff`. The branch additionally requires
the observed live cartridge option `$77:0750 = 0xc200` and rider selector 2.
Those values are captured reads before overwrite, not captured branch output.

Marker points do not write an axis byte; their captured stale value is retained
only to prove that it was not consumed. Every active vertical point computes
axis zero. Horizontal and direction/special geometry are outside this bounded
family.

## Worker variation

The preregistered variation moves the first Right event from frame 1650 to
1653, retains release at 3299 and leaves every other event unchanged. The only
prediction was exact state through frame 1649 and first input divergence at
1650; contact timing was deliberately not predicted. The exact comparison
passes that claim and hashes to
`9811428723fe63f2b852939ead4d1578fd0de5a46786cbf2bd0d8754b30e05c4`.

Two fresh full replays agree on sample digest
`b17677ef0a910d82fb2cd9b8270328f1cc261a6267e6f373cd0af20dfeee5bbb`,
final state
`d3fbf5dd2d56c941ac1515c1d84aa3f528c29353f8c4ee8cd6e6237afd569951`
and aggregate A/V
`c6d64480ea002c1d69612190cae8d980e83c89b60d34e54f64492fdb132c0f72`.
Fresh contact captures through frame 1700 are byte-identical at
`1965151f925d0917c01f400f2cffd2431db5da39fa664a7bae8def2707b4d21e`:
936,010 instructions, 463,222 accesses, zero unresolved stores, zero PCs
outside ROM and maximum ring use 18,644. The actual first direction/special
boundary is player point 8 at frame 1686, ordinal 72. Thus frames 1650--1685
form a 72-call/720-point vertical episode, reconstructed exactly without any
timing preclaim. The component report hashes to
`1323187dc98f4aa65b47fad7d595744b1d1e51ee2aa325c94be9f7cfcbd215fb`.

## Reproduction and integrity

```sh
python3 -m tools.unirally_lab.native.zoom_zoo_vertical_contact extract-content --contract tests/manifests/content/zoom-zoo-reference-contract.json --rom "$(cat local/rom-location.txt)" --out artifacts/m4-06/content
python3 -m tools.unirally_lab.native.zoom_zoo_contact capture --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --out artifacts/m4-06/primary-1650-1682-a --from-frame 1650 --to-frame 1682
python3 -m tools.unirally_lab.native.zoom_zoo_vertical_contact verify --access artifacts/m4-06/primary-1650-1682-a/access.json --content artifacts/m4-06/content --manifest tests/manifests/native/zoom-zoo-vertical-contact-primary.reference.json --report artifacts/m4-06/final-primary-component.json
python3 -m unittest tests.tooling.test_zoom_zoo_contact tests.tooling.test_zoom_zoo_vertical_contact -v
```

The verifier binds the source ROM/core/patch/replay, exact access capture,
classification, frame/call/point counts, boundary and all static content. The
capture step deliberately reuses the implemented M4-05 capture surface because
its complete watch set contains every M4-06 landmark; the M4-06 module consumes
that access document and does not expose a separate capture subcommand. The
focused tests alter ordered ties, signed penetrations, authenticated slope
coefficients, negative incoming velocity, support loss/reacquisition,
recontact coordinates and live dependencies, manifest identities and malformed
comparison inputs. The exact authored comparison also rejects any sample,
final-state, script or frame-set mismatch.

## Limits

This is captured-argument evaluation, not autonomous recurrence or production
native support. It does not reconstruct direction/special or horizontal
geometry, later track paths, finish, AI, camera, presentation or audio. It does
not expand the Classic pack or alter source serialization, profile/start,
frontend, core or locks. Private ROM bytes, extracted payloads, access logs and
reports remain ignored. Independent review is still required before acceptance.
