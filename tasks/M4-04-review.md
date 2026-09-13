# M4-04 independent review

- Candidate: `b4e7c0fb31a5610d1842e35d8fc835df9618b29a`
- Base: `22d951cdfad44db037e32e55aba8ff4ceeb951d9`
- Implementation commit: `7de0cd1018b04d944b40412454f5489e9aa09c6b`
- Reviewer: fresh OpenAI Sol/medium session
- Review date: 13 September 2026
- Result: **changes requested**; the coordinator has not accepted M4-04

## Outcome

The reference behavior, state identities, one-frame perturbation response and
representative regressions reproduce. Both tracked projections verify, their
pair first diverges at frame 2500 in the seven declared input/motion fields,
and two new runs of each field-bearing case preserve the accepted controller,
whole-state, final-state and A/V identities. Two independent end-1649 seed
captures also reproduce the candidate's full WRAM, cartridge RAM and reward
queue hashes.

The candidate nevertheless does not meet its freeze/verifier integrity gate.
The public verifier accepts synchronized changes to the tracked seed's claimed
field values and provenance metadata. This lets the machine-readable candidate
boundary contradict the frozen memory observation while `verify-pair` exits 0.
A focused correction must exact-bind the complete frozen seed object and add
mutations for its values and provenance fields.

## Candidate reproduction

The two projection files have SHA-256 values
`130e4631a7785b3839a3ba9a8b3d59d15a0773711450fdc769632c57a3d92766`
and
`90adf082f2410251dff4ec50431dfe557a2552fb94d0f6b9737a0d0285fba247`.
Each standalone `freeze_zoom_zoo verify` passed. `verify-pair` passed with
first divergence 2500, differing fields `joy1h_image`, `axis_h`, `player_x`,
`player_x_residue`, `player_vx`, `player_vy` and `player_throttle`, and no
finish transition. The task's ten focused ROM-free tests pass.

The additive replay manifests hash to `e6a02eea...a7426` and
`628822f8...db3e`. Their inputs and expected whole-state objects equal the
accepted M4-02 source manifests byte-for-byte at the JSON-object level; the
accepted source files retain hashes `acd29bfb...1aefd` and
`66399d29...8ff7`. Fresh reproduction results were:

| Case | Result | sample / final / A/V | report SHA-256 |
| --- | --- | --- | --- |
| primary | 24/24, distinct worker PIDs | `791a7863...57b68` / `2a843314...6aeb` / `dc7ca8f...be22a` | `f0d1ce01408c15933f06d553b670bcdde81904467e9902bff05dd63636a56db3` |
| release 2500--2599 | 24/24, distinct worker PIDs | `c253de4b...d63e` / `00bf36ed...127d` / `5f5388da...012e` | `d767168d42f9f28340986eee488e1db859631ebdf484fff54c0176185b41cd97` |

Two more fresh `capture-seed` processes, PIDs 26974 and 27061, agree at
WRAM `9c80a52a...d805e`, cartridge RAM `cdd747a3...867` and reward queue
`66687aad...2925`. Their reports hash to `7bee324e...8743` and
`1c6464fa...32c3`. The 124-item inventory names memory, address, width and
signedness explicitly. The replay fields are sampled after `retro_run`; their
ranges, little-endian interpretation and bounded meanings agree with R-0010,
R-0011, R-0021 and the narrow ordered-access evidence. Uncertain contact and
progress words remain provisional rather than receiving invented semantics.

The accepted M4-03 content contract also passes 3/3: 50,665 decoded bytes,
24 ordered entries, 406 transfers, 98 gather bytes and 40 collision words
(`2ba3bc6c...ffc9`).

## Reviewer-owned withheld Up release

Before execution, this review chose the Up-release boundary and changed only
the ignored manifest's event end from frame 2259 to frame 2260. The
predeclared prediction was first input divergence at frame 2260 in JOY1H and
the vertical-axis image; downstream motion/contact response was deliberately
left to observation.

The first discovery run retained the primary expectation and correctly failed
only its sample-digest gate, observing new sample digest
`43bafd2f282f09ad3e4648da5dbe42f2db5474517cb1580b088751e32030c938`.
It retained final serialized state `2a843314...6aeb` and aggregate A/V
`dc7ca8ff...be22a`. After putting that observed sample identity in the ignored
manifest, two new worker processes (PIDs 25490 and 25546) passed 24/24 and
agreed on all 3,300 field rows, final state and A/V; report SHA-256
`d9dce1f9...5a55`.

A separate fresh primary/withheld comparison agrees through frame 2259 and
first diverges exactly at frame 2260. The only declared differences at that
frame are whole-WRAM SHA and `input_images_axes`: `$0313` is `0x01/0x09` and
`$0315` is `0x01/0x00` for primary/withheld. Player x/y, residues, velocities,
pose, jump state, rolling state, contact angle/descriptor and every other
declared field are equal. At frame 2261 the complete WRAM hashes and all
declared fields reconverge and remain equal; final state and aggregate A/V are
also equal. Thus the exact downstream response in the tested domain is an
explicit **lack of retained gameplay or A/V response** beyond the one-frame
input image. The expected behavioral comparison exits 1 because it found this
predeclared divergence; its report hashes to `88a4e6d5...5dd0`.

Fresh 2259--2261 access captures for each side are complete, nontruncated and
well below the 262,144-entry ring. They have 54,686 versus 54,685 instructions,
27,169 accesses each, no unresolved stores and no PCs outside ROM. Their access
records hash to `5beeb613...8902` and `c0951431...474b`; reports hash to
`59a65e44...af2` and `70996fa0...55be`. They corroborate the one-frame input
path difference without exposing a sampled position, velocity, pose, jump or
contact-state difference.

Commands used for the withheld case were the ordinary `replay run`, two-run
`replay compare`, primary-versus-ignored-manifest `replay compare
--no-localize`, and two three-frame `access capture` commands. All manifests,
samples, access logs and reports remain ignored under
`artifacts/m4-04-review/withheld-up-release-2261/`.

## Finding requiring correction

### R1 — Exact-bind the complete frozen seed, not only its shape and memory hashes

`verify_projection(..., require_frozen=True)` exact-checks the projection rows,
top-level ROM/core/replay identities, and the seed's WRAM/SRAM hashes. For the
seed object itself it checks only that `inventory` equals `SEED_INVENTORY` and
that `values` has the expected key set. It does not verify any value in
`seed.values`, `queue_sha256`, `core_library_sha256`, `manifest_identity`,
`script_sha256`, `reference_sample_digest` or `rom_sha256`.

The following reviewer mutation changed both tracked documents' claimed
end-1649 player x from the observed 9200 to 65535 and changed the reward-queue
hash to 64 zeroes. `verify-pair` still exited 0 and printed the ordinary frame
2500 success object:

```python
import json
from pathlib import Path
from subprocess import run
import sys

source = Path("tests/manifests/native")
primary = json.loads((source / "zoom-zoo-primary.reference.json").read_text())
release = json.loads((source / "zoom-zoo-release-2500-2599.reference.json").read_text())
for document in (primary, release):
    document["seed"]["values"]["player_x"] = 65535
    document["seed"]["queue_sha256"] = "0" * 64
Path("artifacts/m4-04-review/mutated-primary.json").write_text(json.dumps(primary))
Path("artifacts/m4-04-review/mutated-release.json").write_text(json.dumps(release))
result = run([
    sys.executable, "-m", "tools.unirally_lab.native.freeze_zoom_zoo",
    "verify-pair", "--primary", "artifacts/m4-04-review/mutated-primary.json",
    "--release", "artifacts/m4-04-review/mutated-release.json",
])
raise SystemExit(result.returncode)
```

This is not harmless free-form commentary: `seed.values` is the candidate
continuation state that R-0022 describes as machine-readable evidence, and the
mutated player x directly contradicts the same document's initial projection
row. The current pair-equality check only proves that both bad copies agree.

The smallest correction is to exact-bind a canonical digest of the complete
frozen seed object (the current canonical SHA-256 is
`d16d7576d556ac09adf842a890d68498db858c3f1c771fcfa499d181a398bc45`),
or equivalently exact-check every seed field against constants derived from the
two fresh captures. Add focused tests showing that changes to a seed value,
queue hash and at least one source-provenance identity fail standalone
`verify` and `verify-pair`. Retain the existing requirement that both cases
share exactly the same seed. No reference recapture or projection-row change
is indicated by this finding.

## First native-blocker challenge

The evidence supports the candidate's behavioral ordering with one wording
qualification. The literal current executable prerequisite is earlier: the
Classic profile contains no ZOOM ZOO content, so native execution cannot yet
reach this update. Conditional on supplying the observed content, the first
reference-demonstrated post-boundary mismatch is indeed frame 1650's sampling
configuration: original `$81:8AA1/$81:8AC0` snapshots use width 256/stride 512,
while `src/core/movement.cpp` passes 1024. Native integration also lacks the
observed `$0D4F=0x3FFF` mask, but frame-1650 x is below that wrap boundary, so
the evidence does not establish an earlier numerical divergence from it.

After a width/content correction, descriptor `0x5800` is a valid next blocker:
its `0x4000` bit is rejected by the native `(descriptor & 0xC001) == 0` guard.
This review therefore accepts R-0022's ordering as a bounded readiness analysis,
not as proof that width is the first literal launch failure or that all future
dependencies are inventoried.

## Regression and hygiene review

Commands and results:

```sh
python3 -m unittest tests.tooling.test_zoom_zoo_freeze tests.tooling.test_zoom_zoo_windows -v
python3 -m tools.unirally_lab.native.freeze_zoom_zoo verify --projection tests/manifests/native/zoom-zoo-primary.reference.json
python3 -m tools.unirally_lab.native.freeze_zoom_zoo verify --projection tests/manifests/native/zoom-zoo-release-2500-2599.reference.json
python3 -m tools.unirally_lab.native.freeze_zoom_zoo verify-pair --primary tests/manifests/native/zoom-zoo-primary.reference.json --release tests/manifests/native/zoom-zoo-release-2500-2599.reference.json
python3 tools/project.py build --preset lab-debug --report artifacts/m4-04-review/build-lab-debug.json --task M4-04-review
python3 tools/project.py test --suite synthetic --preset lab-debug --artifacts artifacts/m4-04-review/synthetic-debug/artifacts --report artifacts/m4-04-review/synthetic-debug/report.json --task M4-04-review --timeout 240 --test-timeout 60
python3 tools/project.py content zoom-zoo-contract --contract tests/manifests/content/zoom-zoo-reference-contract.json --report artifacts/m4-04-review/zoom-zoo-contract-report.json --task M4-04-review
python3 tools/project.py content pack-inspect --pack '/Users/markfeaver/Projects/Unirally Decompilation/local/classic-crawler-dragster.pack' --report artifacts/m4-04-review/pack-report.json --task M4-04-review
python3 tools/project.py native finish-check --manifest tests/manifests/native/full-race-continuous.case.json --content-pack '/Users/markfeaver/Projects/Unirally Decompilation/local/classic-crawler-dragster.pack' --save-frame 1600 --save-frame 3213 --save-frame 3453 --save-frame 3678 --preset lab-debug --artifacts artifacts/m4-04-review/native-finish --report artifacts/m4-04-review/native-finish/report.json --task M4-04-review --timeout 180
git diff --check 22d951cdfad44db037e32e55aba8ff4ceeb951d9 b4e7c0fb31a5610d1842e35d8fc835df9618b29a
```

`lab-debug` builds and the ROM-free suite passes 335/335 (report
`bc80a5e4...5855`). The unchanged Classic pack passes 3/3
(`ff5ee337...ed42`), and DRAGSTER full race plus restores at
1600/3213/3453/3678 pass 18/18 (`66828233...ff2b`). `git diff --check` passes.

The first replay attempt correctly reported the pinned core missing before the
review worktree's ignored dependency links were installed. The first M4-03
contract invocation supplied an unsupported `--timeout` argument and exited 2
before execution; the exact corrected command above passed. Neither attempt is
reported as a candidate pass.

The candidate changes only the ten declared reference/test/document paths.
There is no `src/` change, native implementation, Classic pack/profile/start
change, frontend/presentation change or canonical serialization change. No ROM,
state, trace, decoded payload, image, pack or other original/generated binary
is tracked. The projection files contain integers and identities rather than
original content bytes. Sanitizer and app presets were not rerun because the
reproducible verifier failure already requires correction; the focused tests,
ROM-free debug suite, both original reference cases, M4-03 content contract,
pack reader and four-boundary native restore path all completed.
