# M4-12 independent review

## Assignment and preregistration

- Candidate: `43198c6242ae2d55d025704522f947f88d2ed84e`
- Reviewer: OpenAI `gpt-5.6-sol` / medium, isolated checkout
  `.worktrees/m4-12-review`, branch `review/M4-12-native-zoom-zoo`.
- Review scope: inspect the native dependency closure and exact integer/data-flow
  implementation; reproduce the primary evidence; run two independently selected
  Right/neutral cases from the authentic end-1649 seed through frame 1849, each
  with two fresh original processes, exact native comparison and fresh-process
  restores at 1700, 1804 and 1823.
- Candidate native behavior had not been executed or compared in this checkout
  when the cases below were selected. Reading the submitted task/research claim
  preceded selection, as required to identify relevant transition boundaries.

The two cases were frozen before evaluation:

1. `m4-12-review-delayed-right-1650-1660` replaces primary Right with neutral
   for frames 1650--1660, then restores Right. Prediction: this changes the
   player throttle/velocity producer early enough to alter subsequent movement
   and contact state; exact transition timing is deliberately not preclaimed.
2. `m4-12-review-neutral-1818-1826` replaces primary Right with neutral across
   the submitted 1823 landing and 1824 boost-tile boundary, then restores Right.
   Prediction: this changes the active horizontal-input producer and should
   exercise a different throttle/landing/boost continuation. Exact branch and
   persistence are left to the authentic reference result.

Both cases preserve the primary seed, horizon, opponent inputs and all excluded
mode guards. A failed capture, native rejection or byte mismatch will be retained
as review evidence rather than tuned away.

## Verdict

**Return `43198c6242ae2d55d025704522f947f88d2ed84e` with one
acceptance-blocking semantic finding.** The primary and one material transition
variation pass, and the runtime boundary is honestly limited to the experimental
Right/neutral interval. The other reviewer-owned case demonstrates that the
native wrong-direction producer omits an original velocity gate. This is a
future-affecting canonical field, so M4-12's exact generalization criterion is
not met.

### R1 — missing signed horizontal-velocity gate advances the wrong-direction counter

`update_zoom_zoo` increments `reflection0.wrong_direction_counter` whenever the
marker and horizontal direction agree. The original routine at PAL
`$82:9715--$82:979D` first reads signed horizontal velocity at `$0FA9`: values
from -16 through +15 branch to the clear at `$82:979A`; only values outside that
band reach the marker/direction test. Candidate lines 1074--1078 have the latter
test but omit the velocity predicate.

The delayed-Right case provides a minimal observed consequence. Frames
1650--1660 are neutral, leaving incoming player horizontal velocity zero when
Right resumes on frame 1661. Both fresh original processes leave the counter at
zero on 1661 and first increment it on the next player-active update, frame
1663. Candidate `43198c6` writes one on frame 1661. Serialized byte offset 361
(zero based), the low byte of `reflection0.wrong_direction_counter`, is the
only first-divergence byte. The candidate remains one ahead at every subsequent
player-active update through frame 1849: original 94, native 95. Native
comparison therefore fails at 1661. Fresh native processes restored from the
authentic original states at 1700, 1804 and 1823 each reproduce the remaining
suffix, which narrows the defect to the missing transition producer rather than
serialization or continuation.

Required correction: preserve the original signed 16-bit comparisons/order at
`$82:971A--$82:9725`, clear the counter for the central velocity band, and add a
focused boundary regression. Because this case has now informed the correction,
a fresh independently preregistered withheld case is required on re-review.

## Independent cases and exact identities

The case manifests were committed at `6c4a3b4a931c2f57381007372a5defd48aee54cd`
before candidate execution. The authenticated PAL ROM is
`a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`;
the bsnes core is
`e59bf88d4fc922c9fe3b5438e65ff3a6909d24e1628f0f87141c8de17699a91b`.
The independently built runner is
`29f612c08cd0c3a57a3a37e940b3072d35976c0aa8cb1352c3ac92fa6f17f970`.

| Case | Canonical case SHA-256 | Fresh reference file SHA-256 | Rows SHA-256 | Native/restores |
| --- | --- | --- | --- | --- |
| delayed Right 1650--1660 | `6af5b58a26475f4bf91504a84035c05f8ca1780f1f874c628efd8968f9b290cc` | both `7adb8a0e1bf1e489dd8e1e41bf8858f3c334aded86a1416c47486e607972cbf0` | `89b8cc552b9e1c87d792993d85022c05e6e98ae016f7ea079b4c1d96b92c9108` | fails frame 1661; authentic restores at 1700/1804/1823 pass |
| neutral 1818--1826 | `55293a6b561ce9de574acbecd8433881555b77e02088d4c91a80d9fa99f1c17f` | both `4570aacb59c3f34ced0c2acfb17ebedddc0a75240a686f31e9e9fe6a6e4c70b9` | `cc2f3b82c39d6f9b2c87dc745dd0c027298037931ab251f2af3668609c1016a0` | exact 395 bytes through 1849; restores 1700/1804/1823 pass |

The second case is not inert. At frame 1819, compared with the primary, neutral
clears player throttle from 432 to zero, changes horizontal velocity 482 to 477,
clears `drive_pose_enabled` from one to zero and clears the wrong-direction
counter from 85 to zero. It changes movement/contact/pose state through 1849 and
therefore satisfies the required material producer/branch variation.

## Source, data-flow and boundary inspection

The 395-byte `URZZ0001` state contains the prior 333-byte semantic movement
state, two explicit 30-byte reflection/control records, opponent horizontal and
the retained opponent OAM byte. The runner reads one seed, controller rows and
the 18 authenticated static files. It has no emulator/ROM/reference linkage and
the comparison copies only those inputs into a fresh native directory. The
landing matrices are fixed pre-race data extracted at frame 1297, before the
first race update at 1377; their manifest binds 1,512 bytes and SHA-256. Guard
capture checks the declared excluded-mode words and retained OAM byte on every
reference frame. No later dynamic captured state enters a continuous native
run.

The native update explicitly rejects controls outside Right/neutral, states
outside 1649--1849 and unrecovered branches. The production frontend has no ZOOM
ZOO dispatch. Those limits agree with the stated experimental scope. The passing
landing variation materially changes movement yet stays within this boundary,
so the claim is neither a disguised primary replay nor a full-track claim.
R1 shows that the dependency inventory contains the counter and its velocity
input but the recovered producer semantics are incomplete.

I inspected the vertical-contact reducer and landing transform as integer
operations. It uses explicit 16-bit wrapping, byte-width auxiliary-duration
increment, signed arithmetic shift, and floor-like negative middle-product
selection before doubling. The focused native tests cover those edge semantics.
No reference expectation, ROM bytes, capture, save state or generated gameplay
artifact is added to the tracked review commit.

## Commands and results

- `python3 tools/project.py rom inspect --expect tests/manifests/rom/unirally-pal.json`
  — passed all 10 identity fields and the internal checksum.
- `python3 tools/project.py build --preset app-debug` — passed from source in
  this checkout.
- Four `python3 -m tools.unirally_lab.native.zoom_zoo_trial capture --case ...`
  commands — two fresh processes per case; each pair is byte-identical.
- Two `zoom_zoo_trial compare` commands against the independently built runner
  — landing case passed all rows/restores; delayed case failed at frame 1661.
  Separate fresh-process suffix checks from original states passed delayed-case
  restores at 1700, 1804 and 1823.
- Primary comparison against submitted fresh `trial-primary-{c,d}.json` passed
  200 updates, 395 bytes and all three restores, rows SHA-256
  `a0f39c3b22f9e5c5ca62331281126a2a4df6b8d712881ad910e4329015ab1947`.
- Focused foundation plus trial tooling: 63/63 Python tests passed. Direct CTest:
  21/21 passed.
- `python3 tools/project.py test --suite synthetic --preset app-debug --timeout
  180 --test-timeout 30 ...` — passed 376/376 Python tests, 21/21 CTests and
  three-process repeatability; no skips or failures.

Ignored review evidence is under `artifacts/m4-12-review`. The failed native
series SHA-256 is
`0f0e53b0bb9e42bb29ec36e324a00df462b8e3b2c9154881e077ea6ae423bc0d`;
the delayed restore report SHA-256 is
`930fcc2b23f54c299a4539e21a9530378586e4a4acda7cb4ed41ae98d53bdb99`.
