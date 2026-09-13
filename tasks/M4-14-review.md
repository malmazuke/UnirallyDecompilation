# M4-14 independent review

## Assignment and preregistration

- Candidate: `de521766e9c7a3c22890fec0e959e1060b640306`.
- Reviewer: OpenAI `gpt-5.6-sol` / medium, isolated checkout
  `.worktrees/m4-14-review`, branch `review/M4-14-sustained-traversal`.
- Review scope: independently freeze two untuned post-1649 controller
  variations before candidate evaluation; reproduce the sustained primary and
  variations; inspect recovery, state completeness, native arithmetic, update
  ordering, serialization, fallback boundaries and readability; run the focused
  21 CTests and sustained tooling checks.

The candidate native implementation and behavior were not inspected or executed
in this checkout before the following cases were chosen. Reading the submitted
task and research claims preceded selection so the variations could target the
declared later contact, mode and recovery boundaries.

Both cases retain the authentic end-1649 seed, neutral controller 1, continuous
Right outside the declared changes and initial end-3299 horizon:

1. `m4-14-review-neutral-2037-2052-b-2053-2067` removes Right across the
   submitted first later horizontal-contact window, then applies a 15-update
   Right+B jump. Prediction before capture: the changed incoming horizontal
   state and launch will alter the later surface/landing sequence while still
   reaching a reference-defined recovery with at least 200 subsequent updates.
2. `m4-14-review-b-2171-2185` applies a 15-update Right+B jump across the
   submitted primary recovery/full-landing window. Prediction before capture:
   the launch will replace or delay that recovery and force a distinct later
   landing/mode path, followed by at least 200 updates of resumed progress.

If a reference case has no qualifying recovery plus 200 subsequent updates by
3299, its same controller variation will be extended rather than replaced or
shortened. Qualification and two-process freezing precede any native evaluation.

Reference qualification showed that the second preregistered B pulse was inert
apart from controller bookkeeping: it preserved the primary landing, mode and
guard series. It is retained as negative evidence but cannot satisfy independent
generalization. Before capturing or natively evaluating a replacement, I chose
`m4-14-review-neutral-2698-2713-b-2714-2728`: remove Right across the later
2712 landing and apply Right+B across the 2729 landing. Prediction: the changed
approach and launch should materially alter the late landing/mode sequence and
still leave at least 200 updates after reference-defined recovery. This choice
was informed by the frozen primary transition inventory, not native source or
the implementation failure in the first case.

## Verdict

**Return candidate `de521766e9c7a3c22890fec0e959e1060b640306` for
correction.** One qualifying withheld case exposes an exact player-velocity
divergence on a full landing. The candidate primary and one material late
variation pass, but they do not cover that branch. State-completeness evidence
also needs to be consolidated from the corrected continuous-Right access audit,
and the new serialized binary fields lack the validation used by the existing
state schema.

## Initial findings

### R1 — magnitude-28 full landing applies an extra continued-contact conversion

The qualifying neutral-then-B case matches through frame 2075 and first differs
at end-2076, canonical byte offset 20 (`player.motion.velocity_x`). Native
produces 7 while the original produces 48; both had velocity X 44 and velocity Y
-21 at end-2075. The original performs a full landing at 2076 after nine
unsupported updates. Candidate `resolve_vertical_contact` runs the full-landing
matrix and then also runs the separate magnitude-28 vertical-to-horizontal
conversion intended for continued contact. The submitted primary does not reach
this combination.

Reproduction:

```sh
python3 -m tools.unirally_lab.native.zoom_zoo_sustained compare \
  --reference artifacts/m4-14-review/neutral-then-b-a.json \
  --repeat artifacts/m4-14-review/neutral-then-b-b.json \
  --contract tests/manifests/native/zoom-zoo-sustained-review-neutral-then-b.freeze.json \
  --binary build/app-debug/src/core/zoom_zoo_runner \
  --content-dir ../m4-14-sustained-traversal/artifacts/m4-14/content \
  --out artifacts/m4-14-review/neutral-then-b-report.json
```

Result: `first divergence at 2076, byte offsets [20]`. This withheld case is now
a disclosed regression. A fresh replacement must be selected after the fix; it
cannot itself count as untuned correction evidence.

### R2 — appended binary state fields accept invalid restore values

All reference values of `SurfaceTransition.mode`, `tile_mode`,
`leading_support`, `tile_pose` and `tile_pose_enabled` are binary, and mode and
leading support affect the next update. `deserialize_zoom_zoo` reads all five as
unvalidated 16-bit integers. For example, a 423-byte state with byte 395 changed
from 0/1 to 2 is accepted and then changes mode-sensitive idle decay before the
field is cleared. Existing movement and reflection flags reject values above one.
Validate these restored binary fields and add a malformed-state check.

### R3 — candidate record does not yet close state completeness

The candidate research record says the whole-horizon read-site completeness
assessment is pending. The first `full-read-audit` used the old replay manifest,
whose Up input at 2200–2259 differs from the accepted continuous-Right scenario,
so its later sites cannot establish the submitted domain. I independently
checked the replacement `continuous-read-audit`: all 1,651 end-1649..3299 WRAM
hashes equal the primary capture, its access result is complete across
30,355,912 instructions, and it reports no failure, unresolved store, non-ROM PC
or resolution conflict. The corrected candidate should document its comparison
of those authentic read sites with the 423-byte state and guarded constants.

## Independent evidence

The two fresh primary captures reproduce frozen rows SHA-256
`dce7c14b80c66e4bd831cff3733c6cba02d1c4c40cefd96ae2760bf6d4fa74de`.
The candidate then matches all 423 bytes over 1,650 updates and every declared
fresh-process restore; report SHA-256 is
`d01706de21b8838d39316e82a2e0bd8af43a889f0a5d393761cab64ff0d26783`.

The first withheld case repeats with rows SHA-256
`daa745484c975dd2bb9fa362d0e1fcfb32bfffb7018345f5605a3338b2ad9934`,
changes state and guard rows through frame 3299, has 17 player landings and 35
mode entry/exit pairs, and qualifies recovery at 2817 with 482 later updates. It
fails natively as R1.

The initially selected B2171–2185 case repeats with rows SHA-256
`171058c0833816584d27e41996e02e9da9825a001d31f6a892b2f8fb123e90d3`,
but differs from primary only in controller/input bookkeeping and preserves all
landing, mode and guard rows. It is inert negative evidence and is excluded from
generalization even though native comparison passes.

The late replacement repeats with rows SHA-256
`4bb857f7c3eb42f4f0be71faef953b7bcceb03483b9487320e83681c9852d761`.
It changes the later player landings from primary's 2729/2810/2836 sequence to
2728/2815/2843 and changes the subsequent landing and mode series through 3299.
It qualifies recovery at 2185 with 1,114 later updates and matches all 423 bytes,
two native processes and all 88 declared restore boundaries. Report SHA-256 is
`aba37dfbaf52a85d126762adbf9d653d14186f6fcbe3446607993faffb1705`.

The review binary SHA-256 is
`f0e14b7c04707c25546182177cb42fb33e80b015e3ad2dc74c549e692d188811`.
Every compare authenticates the ROM/core/manifest identities and copies only the
seed, controller rows and hash-checked static content into the native temporary
directory. The runner links only `libc++` and `libSystem`; source and binary
inspection found no ROM, repository, reference or emulator fallback path.

## Commands and results

- Six independent original captures for the two qualifying cases and one inert
  case ran in separate processes; every pair was byte-identical. Each contract
  was frozen before that case's native evaluation.
- `python3 tools/project.py build --preset app-debug` passed.
- Primary and the late material variation matched 1,650 updates, 423 bytes per
  state, two native processes and all reference-selected restores. The first
  material variation failed at frame 2076 as R1.
- `ctest --test-dir build/app-debug --output-on-failure` passed 21/21.
- `python3 -m unittest tests.tooling.test_zoom_zoo_sustained
  tests.tooling.test_zoom_zoo_trial` passed 6/6.
- An extra attempted module name `tests.tooling.test_zoom_zoo_player_landing`
  does not exist and produced an import error; it is not counted as a check.

Broad debug/sanitizer and integration gates remain intentionally deferred to the
primary until the initial findings are corrected. M4-14 is not approved at this
candidate.
