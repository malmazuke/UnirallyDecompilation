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

## Correction re-review — candidate `3eb0879`

- Correction candidate: `3eb0879` (`Document corrected presentation gate
  commands`)
- Diff reviewed: `65b49fa..3eb0879`
- Reviewer: fresh sequential OpenAI Codex Sol/medium session
- Worktree/branch: `.worktrees/m3-02-rereview`,
  `review/M3-02-native-presentation-correction`
- Date: 12 September 2026 AEST
- Verdict: **returned with one material identity-binding finding; not approved**

### Material finding: top-level presentation contract identities are ignored

`native presentation-check` hashes the supplied manifest and validates the
Classic pack independently, but `load_contract` does not validate or consume
the manifest's `profile_id`, `source_rom_sha256`, `sampling_phase`,
`state_fields`, or `logical_entries`. Consequently it does not bind the
manifest's declared source identity to the pack it actually renders.

I copied the tracked manifest and changed only `source_rom_sha256` from the
accepted PAL identity to sixty-four zeroes. With the unchanged valid pack and
unchanged identity-bound fixtures, the checker exited **0**, wrote report
status `passed`, and passed all seven visual cases. The mutated manifest
SHA-256 is
`c015c129796631d11797256fef9f0546af4a0e249a0d48ffdee3b99e6ccca78c`;
the passing report SHA-256 is
`3ca53ee61afc175e01fdf680c22b181a70d2e7b6875e6286bc3db9af451930da`.

Reproduction:

```text
cp tests/manifests/presentation/classic-crawler-dragster-v1.json artifacts/m3-02-rereview-wrong-source-manifest.json
# Change only source_rom_sha256 to 64 zeroes.
python3 tools/project.py native presentation-check \
  --manifest artifacts/m3-02-rereview-wrong-source-manifest.json \
  --fixtures artifacts/m3-02-rereview-fixtures \
  --content-pack artifacts/m3-02-rereview.pack \
  --preset lab-debug \
  --artifacts artifacts/m3-02-rereview-wrong-source-pass \
  --report artifacts/m3-02-rereview-wrong-source-pass/report.json \
  --timeout 120 --task M3-02-review
```

This contradicts the required manifest/identity-bound durable gate. Validate
the frozen top-level contract fields and require the declared source/profile/
logical-entry identities to agree with the accepted Classic pack and command
domain. Add a ROM-free authored mutation showing that an altered source
identity fails rather than merely changing the manifest hash recorded in the
report.

### Returned findings otherwise verified

1. The tracked debug and sanitizer visual checks each ran seven cases. Frame
   3678 rendered the result at `ResultLoading`/`PlayerWon` update 225 with
   962/57,344 mismatches (1.677595%) under the unchanged 15% gate; frame 3679
   remained 961/57,344 (1.675851%). The authored update-224 boundary remains a
   race presentation and the focused native test passed under both presets.
2. Changing only the frame-2000 player `pose.reflected` byte from one to zero
   made the direct runner exit 1 with `unsupported Classic rider
   pose/reflection combination` and no output. The unmodified supported state
   rendered successfully.
3. Sanitizer runs with camera X `INT32_MIN` and `INT32_MAX` completed without a
   diagnostic. Camera overflow/underflow, fractional and trailing-text values,
   plus scroll 32768/-32769, each exited 1 before creating output.
4. The tracked checker passed all seven cases in both presets. Tightening only
   frame 1600's threshold to 0.1% exited 1 at 36/26,656; substituting a different
   image or state fixture exited 3 on its SHA-256 before rendering. Report
   SHA-256 values are debug `94703e9d...f44b`, sanitizer
   `8990742d...9e2`, threshold `549995a8...8368`, image mutation
   `cdab7d31...6e2f`, and state mutation `d7566dd5...99e`.
5. The pack rebuilt deterministically as 154,030 bytes, SHA-256
   `5c1fc5b...1529`, with 25 logical entries. The pack records now consistently
   say thirteen gameplay plus twelve presentation entries.

### Continuation, failure paths, suites and hygiene

Pack-backed `native finish-check` passed under debug and sanitizer: two fresh
processes, gameplay/finish equality, and exact prefix/suffix continuation at
1600, 2000, 2400, 3213, 3453 and 3678. Report SHA-256 values are
`a2f1cb7f...e806` and `fd1f105c...a25a`. Moving the ROM locator aside and
running frame 3678 from only the validated pack produced
`b5cf1100...fbbb`, byte-identical to the normal checker output; the locator was
restored. A separately truncated pack was rejected by `pack-inspect` with exit
3 and by the C++ runner with exit 1, without output.

Sequential full synthetic runs passed all 300 required records under both
debug and sanitizer, with report SHA-256 values `800a00ca...432e` and
`b76e231b...8aa`; focused `presentation|content_pack` CTests passed 2/2 in
each preset. An earlier attempt to run the two full suites concurrently is not
acceptance evidence: both failed two tooling checks because they raced on the
shared `build/lab-failure-probe` directory. Those failed reports were retained,
the generated probe build was moved aside, and the valid reruns were strictly
sequential.

The correction changes no movement structures or serialization source.
Finish/restore equality and the renderer's authored before/after serialization
check passed. `git diff --check 65b49fa..3eb0879` passed; the 14-file diff is
text-only and adds no tracked ROM, pack, state, capture, or rendered image.

## Second correction response — contract identity seam

The checker now validates every top-level field against the one supported
presentation contract, including exact source/profile, sampling schema/phase,
state fields, logical entries and omissions. New explicit Classic pack
profile/start/rules declarations are cross-checked against the independently
validated pack and its entry inventory before build or render.
The exact seven-case array is digest-pinned as well, preventing a shortened or
self-consistently replaced suite.

ROM-free subtests mutate every formerly ignored declaration independently.
Each returns invalid input with report status `failed` and no visual result;
the reviewer's exact all-zero source mutation now fails at
`source_rom_sha256`. The unmodified seven visual expectations and all gameplay/
pack identities are preserved. Fresh independent re-review is still required;
this response does not approve or accept M3-02.

## Identity correction re-review — candidate `8acfac7`

- Correction candidate: `8acfac7` (`Record presentation identity evidence`)
- Diff reviewed: `0bca7bf..8acfac7`
- Reviewer: fresh sequential OpenAI Codex session
- Worktree/branch: `.worktrees/m3-02-identity-review`,
  `review/M3-02-identity-correction`
- Date: 12 September 2026 AEST
- Verdict: **approved; the returned identity-binding finding is corrected**

### Independent identity and failure-path reproductions

The exact prior attack, changing only `source_rom_sha256` to sixty-four zeroes,
now exits 3 with report status `failed`, no `visual_results`, and no build or
render artifact. Its report SHA-256 is `8d4ce286...96321`. Independent changes
to `profile_id`, `sampling_schema`, and the ordering of `state_fields` behaved
the same. Unknown and missing top-level keys and a Boolean `schema_version`
were also rejected as invalid input. Reordering, omitting, or substituting one
of the seven reference cases was rejected by the independently recomputed case
digest `384e6411...1cae5`; none reached build or render.

The constants are program-owned literals, not copied from the supplied
manifest at runtime. `load_contract` requires the exact closed set of
top-level keys, exact Python types, ordered identity arrays and values. The
canonical case array is separately pinned. `validate_pack_binding` then
compares the independently validated pack's source ROM, profile, semantic
start and rules identities to those fixed declarations and requires every
contract logical entry to occur in the pack. The underlying pack validator
also requires the complete exact 25-entry inventory, canonical offsets, sizes,
hashes and payloads.

I independently flipped each binary pack identity in turn (source, rules,
profile and semantic start) and replaced one same-width logical entry ID. All
five commands exited 3 before build/render, wrote failed reports without
`visual_results`, and named the corresponding incompatibility. Report SHA-256
values are source `b94b4c5c...b70d`, rules `9f9ecc5a...9e5d`, profile
`31e60873...704a`, start `4f7f6664...207c`, and logical inventory
`4f323130...bb1c`.

Changing one byte in the first bound state and, independently, the first PNG
made the checker exit 3 before rendering, with no native image artifact and no
`visual_results`; report SHA-256 values are `739d32b9...bf77` and
`3643b9f1...53a0`. Fixture hashes are checked after the native build step, so
these two fixture attacks do perform an incremental build check; no renderer
process is started.

### Genuine contract, earlier corrections and regression checks

The genuine 154,030-byte pack remains SHA-256 `5c1fc5b0...1529`. Debug and
sanitizer `native presentation-check` runs both passed the same seven exact
cases: 36/26,656, 697/50,176, 279/50,176, 445/50,176, 653/50,176,
962/57,344 and 961/57,344 mismatches, under the unchanged 2%, 2%, 2%, 3%, 3%,
15% and 15% limits. Their report SHA-256 values are `b52dda12...2289` and
`be9e7cd5...d45f`.

The earlier five corrections remain intact and covered: frame 3678 takes the
result presentation path; the frame-2000 false-reflection state exits 1 with
no output; sanitizer renders at both signed 32-bit camera extremes with no
diagnostic; scroll 32768 exits 1 with no output; the tracked visual command is
the gate exercised above; and the content record still states 25 total / 12
presentation entries. The identity-only diff does not touch the C++ renderer,
movement serialization, pack inventory documentation, frozen fixtures or
thresholds.

The focused ROM-free presentation unit module passed 3/3. Sequential full
debug and sanitizer synthetic reruns each passed 278 Python records, 19 CTests
and three-process repeatability; report SHA-256 values are
`ac6797e6...2d1a` and `4fddc8ba...006`. The first sanitizer-suite invocation
was correctly reported as failed because that fresh worktree did not yet have
a sanitizer build; after the explicit sanitizer build passed (report
`3df0808b...9ce3`), the fresh sequential rerun above passed. This missing
prerequisite is not counted as a pass.

`git diff --check 0bca7bf..8acfac7` passed. The six-file correction diff is
text-only and contains no ROM, pack, state, capture, fixture, or rendered
image. No acceptance baseline or expected digest was regenerated. I found no
remaining material issue in the assigned identity-correction scope.
