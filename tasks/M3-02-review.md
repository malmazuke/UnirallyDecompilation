# M3-02 independent review — native presentation contract

- Candidate: `083a8d0c7a3919e7c648db2fbe81cdef2bdd9742`
- Diff reviewed: `88c0c8144bfe244babecfc5344d0dc05f9dc39ac..083a8d0c7a3919e7c648db2fbe81cdef2bdd9742`
- Reviewer: fresh OpenAI Codex Sol/medium session
- Worktree/branch: `.worktrees/m3-02-review`, `review/M3-02-native-presentation`
- Date: 12 September 2026 AEST
- Verdict: **returned with material findings; not approved**

## Findings

### 1. The result-transition neighbor is one frame late in native presentation

The reviewer-owned withheld case is frame 3678, immediately before the frozen
stable-result case 3679. I captured its reference image directly from a fresh
pinned-core run of the frozen continuous replay; I did not derive it from the
candidate renderer. The capture passed the accepted ROM/core/replay, sample and
final-state identities and had no trace-ring overflow or unresolved access.

The exact native frame-3678 state is `URMV0002` SHA-256
`9e6776e9dff764d0adc1651ff53cd43a46983d71f190242bf806e3f4d54cec56`.
It is still `ResultLoading`, so `render_dragster_headless` takes the race path.
The resulting PPM is byte-identical to the candidate's frame-3453 PPM
(`3ff60cbe...ddbf`) even though the original has already displayed the result
screen. The full-frame comparison is **57,280 / 57,344 mismatched pixels
(99.8884%)**; over the race comparison rectangle it is 50,112 / 50,176
(99.8724%). The reference PNG SHA-256 is
`9dfb6cfef4b6540b1acf8af34146e47f175d8ed04ad7345a52faa85bdf765589`.

Reproduction:

```text
python3 tools/project.py access capture --manifest tests/manifests/replay/race-crawler-dragster-12000-continuous-right-fields.json --out artifacts/m3-02-review/withheld-3678-reference --from-frame 3678 --to-frame 3678 --frame-image 3678 --ring 262144 --task M3-02-review
build/lab-debug/src/core/presentation_runner --content-pack artifacts/m3-02-review/review.pack --state artifacts/m3-02-review/finish-debug/state-3678.bin --out artifacts/m3-02-review/native-03678.ppm --camera-x 24434 --bg1-scroll-x 24434 --bg1-scroll-y 208 --bg2-scroll-x 12217 --bg2-scroll-y 104
```

Capture access SHA-256:
`91ce740192a0df1c1074d0c9bd555a873aabf8d9f32ff4562387306816c14d11`.
The candidate needs an explicit, evidenced presentation transition boundary;
keying the result composition only from the current native finish phase does
not reproduce this neighboring frame.

### 2. The frozen reflection field is ignored instead of mapped or rejected

The presentation contract lists both riders' `reflected` fields, and the task
requires pose/orientation mapping with unsupported mappings rejected. In
`presentation.cpp`, `rider_frame_for_pose` is called only for validation and
its selection is discarded. `render_rider` then applies fixed geometry and
attributes independent of the state's reflection bit.

I changed only the player `pose.reflected` byte in the valid frame-2000
canonical state from 1 to 0. Deserialization accepted the state, the renderer
exited 0, and the result was byte-identical to the original render:

```text
original state  9d12034bc4123f9966b371ab7f7efe969005644d17b261bcbf71d460b38ec547
mutated state   86a6297cdc21d9267dbc9732ccc2cc964dc97e0e95d5925a738aa78c438c8cfa
original PPM    5026f0fd076bb16bfd934ec67ab59357be5fa7a7959dfcf21df6311aa92a74c9
mutated PPM     5026f0fd076bb16bfd934ec67ab59357be5fa7a7959dfcf21df6311aa92a74c9
cmp exit        0
```

This seam can silently render a contradictory pose/orientation combination.
The supported combinations should either use the reflection selection in OBJ
composition or fail closed, with an authored test proving the behavior.

### 3. An accepted camera argument causes signed-overflow UB, and the sanitizer process still exits 0

`presentation_runner` parses `--camera-x` with `std::stoi` into an unrestricted
`int`. `presentation.cpp:759` subtracts it in signed `int`. The sanitizer build
accepts `-2147483648`, reports overflow, writes output and exits successfully:

```text
build/lab-sanitize/src/core/presentation_runner --content-pack artifacts/m3-02-review/review.pack --state artifacts/m3-02-review/finish-debug/state-2000.bin --out artifacts/m3-02-review/extreme-camera.ppm --camera-x -2147483648 --bg1-scroll-x 7138 --bg1-scroll-y 208 --bg2-scroll-x 3569 --bg2-scroll-y 104
```

Observed stderr:

```text
src/core/presentation.cpp:759:61: runtime error: signed integer overflow: 8029 - -2147483648 cannot be represented in type 'int'
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior src/core/presentation.cpp:759:61
```

Observed exit: `0`. This violates the project's undefined-arithmetic and useful
failure-path requirements. Bound presentation inputs before narrowing and do
the coordinate arithmetic in a type that cannot overflow over the accepted
domain. A sanitizer diagnostic must not be reported as successful execution.

### 4. The visual acceptance driver is not a durable command or test seam

The tracked contract contains the six cases and limits, but no tracked command
loads that manifest, obtains the bound private fixtures, invokes the runner and
fails on an image mismatch. The handoff names a private driver and its report
but gives no command or path. Consequently the synthetic suite does not test
the exact result scroll 82, exact header, retained-VMADD chronology or six
visual thresholds. The authored result test exercises one visible pixel and
the split source indirectly, but carries no frozen reference image/hash.

This gap explains why the suite passes despite findings 1--3. The correction
should make the six-case comparison a reproducible repository command with
structured success/failure reports and authored ROM-free failure-path tests;
private image/state inputs may remain ignored and identity-bound.

### 5. Pack documentation understates the final inventory

The extractor, Python inspector and C++ reader correctly bind **25** entries
(13 gameplay plus 12 presentation). `docs/content/classic-pack-v1.md` instead
says eleven presentation spans and a twenty-four-entry inventory. This is a
record correction, not the reason for the return, but it must be fixed before
handoff because the exact inventory is the runtime compatibility boundary.

## Reproductions that passed

### Pack extraction, inspection and corruption

```text
python3 tools/project.py content pack --out artifacts/m3-02-review/review.pack --report artifacts/m3-02-review/pack.json --task M3-02-review
python3 tools/project.py content pack-inspect --pack artifacts/m3-02-review/review.pack --print --report artifacts/m3-02-review/inspect.json --task M3-02-review
```

The independently extracted 154,030-byte pack is byte-identical to the worker
pack: SHA-256
`5c1fc5b00747621ccd2c0a1f6f34cf6ba290c8808e6bb1d92b8c0ad4b0df1529`.
Inspection passed the schema, source/rules/profile/start identities, canonical
layout and all 25 exact entry identities. The rules identity is
`70712c470db436ad95b02d3a6d51f737be7bb5b27689ca0d99a8297bac31d768`.

For an independent corruption I changed the logical ID
`presentation.result.classic.palette-tail.v1` without changing table size or
payload. `pack-inspect` exited 3 with `Classic pack logical entry inventory is
incompatible`; the direct C++ runner exited 1 with `Classic pack required
logical entry is missing`. The mutated pack SHA-256 is
`ea16f69302ea9fe3de64396329f9e5d08d57318761c90ca194b8301e3609a6e6`.

### Six frozen visual cases

I generated fresh native states at 1600, 2000, 2400, 3213 and 3453 through the
pack-backed finish runner, used the recorded exact state at 3679, converted the
identity-bound reference PNG fixtures independently to RGB PPM, invoked the
candidate runner once per case, and counted RGB pixel inequality within each
frozen rectangle. All counts exactly reproduce the candidate report:

| Frame | Mismatches / pixels | Fraction | Frozen limit | Result |
| ---: | ---: | ---: | ---: | --- |
| 1600 | 36 / 26,656 | 0.135054% | 2% | pass |
| 2000 | 697 / 50,176 | 1.389110% | 2% | pass |
| 2400 | 279 / 50,176 | 0.556043% | 2% | pass |
| 3213 | 445 / 50,176 | 0.886878% | 3% | pass |
| 3453 | 653 / 50,176 | 1.301419% | 3% | pass |
| 3679 | 961 / 57,344 | 1.675851% | 15% | pass |

The native PPM hashes exactly match the candidate report. Inspection of the
implementation and cited capture confirms the corrected retained-VRAM source/
destination split, `PLAYER     TIME` header, and final scroll value 82. The
merged `$00210E`/`$80210E` capture has SHA-256
`ad0dbcf1746874ddb73e9644c909add831ea9b5e51aeada94b57a2e44a8e04e8`:
the earlier unbanked writes at sequences 23/24 publish 78/0 and the later
banked writes at 798/799 publish 82/0. The code uses OBSEL `$63`'s observed
size selection correctly in the record as 16-by-16 small / 32-by-32 large;
the eleven result objects are explicitly omitted within the frozen result
threshold. The separate race objects use their observed 64-by-64 composition.
BG1 gathers from the decoded track rather than a captured staging upload.

### ROM independence and gameplay invariance

With `local/rom-location.txt` moved aside, the pack-only result runner emitted
SHA-256
`b5cf1100f278a74c7690662bfd4600e458e2693547b9a92b84133715ff75fbbb`,
identical to the normal run. The locator was restored immediately.

This command passed two fresh processes, exact gameplay/finish comparison and
prefix/suffix continuation at every requested boundary, including withheld
3678:

```text
python3 tools/project.py native finish-check --manifest tests/manifests/native/full-race-continuous.case.json --content-pack artifacts/m3-02-review/review.pack --save-frame 1600 --save-frame 2000 --save-frame 2400 --save-frame 3213 --save-frame 3453 --save-frame 3678 --preset lab-debug --artifacts artifacts/m3-02-review/finish-debug --report artifacts/m3-02-review/finish-debug/report.json --timeout 600 --task M3-02-review
```

Report SHA-256:
`7e14e8bf10e603a66524f8a8fafed3a291a6f616b5adeac57c2235f9ef960560`.
The six generated state hashes match the candidate's recorded identities.
Rendering did not change any state file; the public renderer takes its movement
state by const reference, and the focused authored test also checks before/
after canonical serialization.

### Debug and sanitizer checks

Both debug and sanitizer builds passed. Focused `presentation|content_pack`
CTest selection passed 2/2 under each preset. The full sanitizer synthetic
suite passed 275 Python checks, 19 CTests and three-process repeatability;
report SHA-256
`22972590c2bd4a0b88e984bac191d0a9878c38e5d29e7b63c1993f377ab85047`.
These passes do not cover the accepted extreme camera argument, reflection
mutation, withheld transition frame or private visual thresholds.

## Diff and content hygiene

`git diff --check 88c0c81..083a8d0` passed. The full 14-file diff was reviewed;
`git diff --numstat` reports text additions/deletions only and no binary file.
The candidate adds no ROM, extracted payload, pack, state, capture or rendered
image to Git. Generated review packs, images, states, captures and reports are
ignored under `artifacts/`; ROM and local dependencies remain under ignored
`local/`. The worktree had no tracked modification before this report.

## Required correction/re-review

Define and test the exact transition-frame presentation rule, consume or reject
reflection combinations rather than ignoring them, validate/narrow runner
numeric inputs without UB, and add a durable identity-bound six-case comparison
command with failure reports. Correct the pack inventory documentation. Re-run
the six frozen cases plus frame 3678 (or document and evidence a corrected
adjacent boundary), the three mutations above, pack/ROM independence,
finish/restore invariants and debug/sanitizer checks on the correction commit.

## Candidate correction response

The task worker reproduced every finding and returned a corrected candidate
without changing gameplay serialization or any frozen threshold:

1. Frame 3678 is explicitly bound as `ResultLoading`/`PlayerWon` update 225,
   when the original result is already visible; update 224 remains a race frame.
2. All observed rider combinations are reflected. Contradictory false values
   now fail closed, including the reviewer's exact frame-2000 mutation.
3. Camera subtraction is performed in 64 bits and clipped before narrowing;
   both 32-bit extremes are sanitizer-clean and scroll overflow is rejected.
4. `native presentation-check` now runs all seven identity-bound private cases,
   reports thresholds structurally, and has ROM-free pass/fail/parser tests.
5. Pack records now consistently close on 25 total / 12 presentation entries.

Fresh re-review is required; this response does not approve or accept M3-02.
