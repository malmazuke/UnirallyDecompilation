# R-0027 — bounded ZOOM ZOO position/contact composition

- Status: accepted bounded reference research after independent approval;
  production native behavior remains unchanged

## Scope and identity

This record composes the accepted M4-08 position integrator and M4-05--M4-07
contact equations for both riders on frames 1650--1700. It is reference-only
research: no native gameplay path is added. The seed is the authenticated
end-of-frame 1649 row; the supported PAL ROM SHA-256 is
`a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`
and the pinned core is `7d5aa1e656b9171524d01b1b22917197d8121cb4` with patch
`a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885`.

The preregistration at claim `15da58489df4ccce24a678aa3d98382872036ab1`
froze the combined watch set, the decoded helper hypotheses, and one variation:
release Right only at frame 1666 and restore it at 1667, with exact behavior
predicted through 1665 and controller divergence at 1666 only. It deliberately
made no branch-relevance or reconvergence claim.

## Verified instruction order and helper

The inclusive 68 ROM bytes at `$82:A96F--A9B2` (file `0x01296F`) have SHA-256
`5f3d24df4c743df33e24d2febc24522cd2abe68fe5597ee2abf3ebfac413653c`.
The reached routine executes with 16-bit accumulator and index widths. It:

1. returns unless `$0F4B == 0`;
2. selects rider word `$0547,Y` using `$0FF9` and returns unless it is zero;
3. continues when the N flag from wrapped 16-bit `velocity_y - $0200` is set;
4. starts an addend at 16, and for nonnegative velocity performs five logical
   right shifts then subtracts that quotient; it adds three, updates `$0FAB`,
   and increments transient Y `$A7` once.

All 102 primary and all 102 variation calls reach the increment. Primary
velocity addends are 19×73, 15×8, 14×5, 18×4, 17×4, 13×4, 16×3 and 12×1;
79 inputs are nonnegative and 23 negative. Ordered events establish, for each
rider, helper → position integration → collision-point expansion → track
sampling → contact → caller publication. Each next call consumes the preceding
contact x/y publication and preceding integrator residues.

## Recurrent composition result

Two fresh primary captures are byte-identical at access SHA-256
`f3d0013aa84bfa1d5ab795fe62269745abf93a402d816326c3d2b56ded961465`
and WRAM-series SHA-256
`53c03d228999d3c1fbe5ee22be64a3965a77848e9b8f8adbeaba4374cba3d13d`.
Each contains 953,416 instructions and 471,721 accesses, with zero unresolved
stores, zero non-ROM PCs and a maximum ring delta of 18,640/262,144.

The evaluator seeds x/y/x-residue/y-residue once for both riders, then carries
those eight words through all 102 calls without per-call replacement. It
expands authenticated pose/reflection content, derives every width-256 coarse
and fine source offset, reads all 1,020 sample words, and runs the accepted
direct/reflected vertical preprocessing, reducer and response equations.
Captured positions, residues, sample words and contact outputs are comparison
targets only.

Primary exact results are:

- row SHA-256 `9582292c872f154b917e7973f4b6b2ba8a3a458feaab49d11889f3fe2b9f9c30`;
- sample-word SHA-256 `98e77e32b3540aa98e796edc5d7fb7c0bb2736e44e8e4b3ee1b4cf1827d188dd`;
- source-offset SHA-256 `f24ccd2738300030debe07020d4140f4f8d0d6e8e711b0f8ea3d2a8cd526fa27`;
- position branches x negative/nonnegative 51/51 and y 20/82;
- contact branches continuous 59, reflected-continuous 18, unsupported 24,
  and recontact 1;
- final player `(x=9824,y=1605,xres=12,yres=10)` and opponent
  `(x=7489,y=1520,xres=-4,yres=12)`.

## External fields and limit

The recurrent state is only both riders' x/y/x-residue/y-residue. External
inputs are inventoried at the phase where they enter:

- before Y adjustment: first guard, indexed guard and incoming y velocity;
- position integration: x velocity, surface, guard, unsupported count,
  direction word, mode and track mask;
- sampling: pose and reflection;
- contact: x/y velocity, response A/B/impulse, unsupported count/duration,
  surface angle, angle sentinel, auxiliary flag, mode, special, phase and
  previous x/y;
- live contact dependencies: cartridge option and rider selector.

`response_b` is intentionally not recurrent. In accepted primary evidence the
opponent contact publishes 254 at frame 1661 but the next call receives and
publishes 0 at frame 1662, proving a producer between contact calls. This task
does not claim an autonomous rider update outside the exact frames and reached
paths above.

## Worker variation

The finalized replay runs twice identically: sample
`080d56aa69c5232f1e1acd6745ad49719ed4d0a09af17f9845c4eaa5165c2c2e`,
final state `1211220c12335497ae9b798b0e79da31c244aeef7a44fb492816da8784fd8a4d`,
and A/V `4bbdab1be52f6c05f45521211c9c5318e277c7545e2cf9d139ec5f675cbaa143`.
Two final combined captures are byte-identical at access
`e853375ec890afa527c67cd1abeef8c0a9c8ef6d071ff06d830c2226d230f69c`
and series `335263f2a2f3b763198afb1d0bcfb6f4dadf48c945d30c35c4ce579ed282addc`.

The preregistered prediction holds: the controller differs only at 1666,
composition first differs for the player at 1666, and all evidence is exact
through 1665. Samples first differ at 1670. Opponent composition remains exact
through 1700; player state has not reconverged at 1700. Contact branch choices
differ at 1668, 1671, 1672, 1675, 1677, 1679, 1681 and 1683--1685. The
variation usefully reaches a mixed direct/reflected vertical call at 1683 and,
at 1685, negative incoming y velocity with nonnegative wrapped
velocity-plus-residue. The latter proves the integrator branch is selected by
the wrapped total sign, not velocity sign. Variation final player state is
`(9820,1603,25,24)`; opponent state is unchanged.

## Reproduction and validation

```sh
python3 -m tools.unirally_lab.native.zoom_zoo_composition capture --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --out artifacts/m4-09/primary-a
python3 -m tools.unirally_lab.native.zoom_zoo_composition derive --access artifacts/m4-09/primary-a/access.json --content artifacts/m4-09/content --report artifacts/m4-09/primary-derived.json
python3 -m tools.unirally_lab.native.zoom_zoo_composition verify --access artifacts/m4-09/primary-a/access.json --content artifacts/m4-09/content --manifest tests/manifests/native/zoom-zoo-composition-primary.reference.json --report artifacts/m4-09/primary-verified.json
python3 -m tools.unirally_lab.native.zoom_zoo_composition compare-inputs --primary-access artifacts/m4-09/primary-a/access.json --variation-access artifacts/m4-09/variation-final-a/access.json --content artifacts/m4-09/content --report artifacts/m4-09/variation-comparison.json
python3 -m unittest tests.tooling.test_zoom_zoo_position tests.tooling.test_zoom_zoo_contact tests.tooling.test_zoom_zoo_vertical_contact tests.tooling.test_zoom_zoo_reflected_vertical_contact tests.tooling.test_zoom_zoo_composition -v
```

Focused tests pass 46/46. Clean debug and sanitizer runs each pass 359 Python
tests, 20 CTests and the three-process repeatability check. Frozen contract,
contact, vertical-contact, reflected-contact, position, replay, pack inspection
and native finish/restores at 1600/3213/3453/3678 pass. Key report SHA-256s are
debug `2ad3f45c...ae84f`, sanitizer `fafa0289...80cbd`, replay
`32683322...37a8`, and native finish `18c91074...50ad`.

Non-passes were retained honestly: the preregistration replay with zero digest
placeholders failed its four expected-digest checks while its two fresh runs
agreed; the first clean debug test used an unsuitable whole-directory `local`
symlink and failed two root-containment checks; two frozen capture attempts
ended with `OSError: [Errno 28] No space left on device`; and one frozen
vertical capture was first passed to the general contact verifier and rejected
for a content-schema mismatch. The environment was corrected without changing
expectations, redundant task-owned ignored captures were removed, and every
affected gate was rerun successfully.
