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

**Approve corrected candidate
`e730aaa52f176ed4e7dd564c985b8d9d64c9d5b8`; no material finding remains.**
Initial candidate `de521766e9c7a3c22890fec0e959e1060b640306` was returned because
one qualifying withheld case exposed an exact player-velocity divergence on a
full landing. The correction fixes that ordering defect, validates the new
serialized binary fields and closes the state audit from the authentic
continuous-Right capture. The corrected candidate passes the disclosed
regression, the retained material case and a fresh post-fix replacement.

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
two native processes and all 94 declared restore boundaries. Report SHA-256 is
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

## Correction re-review preregistration

Corrected candidate `e730aaa52f176ed4e7dd564c985b8d9d64c9d5b8` was supplied after
the initial review. Before inspecting, building or executing its implementation,
I selected one fresh replacement for the failed initial case:
`m4-14-rereview-neutral-2288-2304-b-2305-2319`. It removes Right through
the primary's later 2304 full landing, then applies Right+B across the 2305 mode
entry. Prediction before capture: the changed approach and launch will produce a
different full-landing/mode sequence, exercise the corrected later-contact code
away from the disclosed 2076 regression, and retain a qualifying recovery plus
at least 200 subsequent updates through 3299. Two fresh original captures and a
new freeze must qualify before any corrected native evaluation.

## Correction assessment

R1 is correctly fixed by limiting the magnitude-28 vertical-to-horizontal
conversion to continued contact where the prior unsupported count is below
nine. The source path `$81:92FE–9309` sends the nine-update full landing directly
to correction. The disclosed regression now matches all 423 bytes over 1,650
updates, repeats in a second native process and restores at all 69 frozen
boundaries, including 2075/2076. A focused authored case independently preserves
velocity across a magnitude-28 full landing and verifies that airtime clears.

R2 is fixed for both riders. Deserialization now rejects values above one in all
five binary surface fields, with a corruption check for every rider/field pair.
The check executes before restored state can affect an update.

R3 is closed in [R-0033](../docs/research/R-0033-sustained-traversal.md). I
independently checked the private `continuous-read-audit` against the primary:
all 1,651 whole-WRAM hashes match, 30,355,912 instructions completed below the
ring bound, and the aggregate has no unresolved stores, non-ROM PCs, resolution
conflicts or dropped resolutions. The producer-region audit reports zero
unresolved accesses. The documentation maps newly reached gameplay reads to
serialized fields, rebuilt scratch or authenticated static/constant inputs and
explicitly discards the old Right+Up audit. Its output-side audio/presentation
limit is appropriately outside this simulation claim.

The frozen recovery interpretation meets the task wording. It was declared
before native tuning and uses authenticated state and writers: after mode entry
at 1992 and exit at 1993, the primary progress transition count rises from -35
to -32, then a full player landing occurs at 2185 with nonzero horizontal
velocity (-214). The run retains another 1,114 updates through 3299, including
later mode entries, exits and full landings. Repeated returns make this local
resumed progress rather than monotonic obstacle clearance or track completion,
which the contract and research record state explicitly. The criterion does not
shorten the required continuous-Right horizon or substitute an earlier case.

The fresh post-fix case qualified before corrected native evaluation. Original
rows SHA-256 is
`a6b5d32a7756cf7715e9f7d73793c541509cb35d1308f5495e646ded0b613c93`;
its reference files are byte-identical at SHA-256
`55df365eeb7968ed913e23c622f11852731707fc47d0a4d94b6dfc0f97c93b66`.
It changes the primary 2304 landing to 2305 at angle -18 and replaces the later
landing/mode sequence through frame 3299. It qualifies recovery at 2185 with
1,114 subsequent updates and matches all 423 bytes in two native processes plus
all 96 restore boundaries. Corrected report SHA-256 is
`d69ad8e7f3998df6428760d3312dda81f0a162b92421e2ef3ca91ff47faa2b1b`.

Corrected report SHA-256 values are
`685aa0f7647e877969892cb8d84efc50278407a4fddb29b8da1ee30ed23cb2f9`
for primary,
`d84a11517a882ed492be0996eb3e48d2ab1633b3610f3e45bbe8534fb30f7824`
for the disclosed 2076 regression, and
`a946195519f41d7c64c9a3a8f617a381edbb0d9c8879a625bf027e96cdd3b713`
for the retained late material case. The inert negative also remains exact. The
corrected review binary SHA-256 is
`5f6e73c258f18e98b795709eb5a3d103fd55af84e9371cfa296377c65364388d`.

On the corrected candidate, `ctest --test-dir build/app-debug
--output-on-failure` passes 21/21 and the sustained/trial tooling command passes
6/6. ROM inspection passes all ten identity fields and the PAL internal checksum.
Primary's corrected denied-reference run executes all 1,651 states while the
same sandbox denies both repository reference and ROM reads; removing one
required static content file fails. Source, linkage and binary-string inspection
also show no emulator, ROM or reference fallback path.

Primary reports the broad matrix passing after correction: app-debug and
app-sanitize each pass 403 checks with no skip, missing fixture or failure; all
11 broad commands pass; and 24 debug/sanitize differential and restore commands
cover M4-12 primary plus three cases, M4-13 primary plus four cases, and M4-14
primary plus the disclosed and retained review cases. Integration, private-origin
synchronization and hosted CI remain pending at this review commit.

Approval is limited to the authentic end-1649 seed, the continuous-Right primary
and reviewed Right/neutral/B variations through 3299, both riders, the 423-byte
state and authenticated static content. It does not establish full-track support,
monotonic progress, frontend/presentation/audio behavior or private Linux
differential execution.
