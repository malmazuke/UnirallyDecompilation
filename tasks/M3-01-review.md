# M3-01 independent review — native finish and full-race state

- Review status: **corrected re-review returned for a signed boundary mismatch**
- Submitted head inspected: `f985bebb9ca0d8f9e420c4e9cef8374cefc23b16`
- Behavioral candidate returned: `ee87a71273dc6b7a717d1d5348c742284a4ab204`
- Reference freezes: `dcbc896b14a4ae8d715d437894f55474b6a7e186` and
  `c5f2b681525e8ddc44d38fd4f3ce264bfeaffff2`
- Review checkout: `review/M3-01-native-finish` in `.worktrees/m3-01-review`
- Reviewer/runtime: fresh OpenAI Codex, no child agent; Codex CLI `0.153.4`
- Quota: started at the user-supplied 47% used in the seven-day Codex window;
  stop threshold 54%. No later percentage was exposed to this session, so it
  is recorded as unknown rather than assumed. No reset or credits were redeemed.

## Decision

Return M3-01 without approving `ee87a712`: a reviewer-owned input frozen from
two fresh reference processes differs from the native result at frame 3227.
The mismatch is in the exact required `speed` projection: reference 1, native
0. It is transient (both are 0 at 3228), but it is a material failure of the
task's exact full-race agreement and boundary-input criterion. This review did
not edit the candidate implementation.

The added case releases Right for crossing frame 3213 only. Relative to the
accepted continuous case, the reference first differs at 3213 in the controller
image, horizontal axis, throttle and speed. It keeps the observed player finish
at 3213, opponent finish at 3214, stored times 3357/3358, winner outcome and
3214--3453 delay. The changed post-finish tail reaches speed 37 at 3226, then
reference 1 at 3227 and 0 at 3228. The candidate's generic `< 40` branch in
`apply_finish_slowdown` produces 0 directly at 3227. The exact correction is
left to the implementation owner.

## Freeze and input audit

Both reference-freeze commits precede the behavioral commit in the ancestry
path, in this order:

```text
dcbc896 Freeze M3 native finish reference state
c5f2b68 Freeze full-race native gameplay projections
ee87a71 Implement native full-race finish continuation
```

`git diff 0bc4938..ee87a71` is empty for both accepted 12,000-frame replay
manifests, all three M2 case/expectation pairs, `tools/locks/emulators.json` and
the reference patch directory. The two M3-00 replay files differ from their
earlier preregistration commit `135ae38` only by the expected sample/final-state
digests added during accepted M3-00 evidence; their controller events did not
change. `git diff --check db0ce93..f985beb` passed.

The reviewer-owned additive files are:

- `tests/manifests/replay/race-crawler-dragster-12000-review-release-3213-fields.json`
- `tests/manifests/native/full-race-review-release-3213.reference.json`
- `tests/manifests/native/full-race-review-release-3213.expected.json`
- `tests/manifests/native/full-race-review-release-3213.case.json`

The prediction in the replay manifest was written before reference execution.
Two distinct pinned-bsnes processes then agreed over 12,000 frames, including
A/V, with sample digest
`ea96f0fdf6c26072b40478e36f23ff3cda7e955bfebbcd4487f1825c390ac2a7`
and final state
`c7f7e7a68b705b828175a7f6d2a5dccf1e992e6ebd8f0c69d98a82fdb79ce8de`.
A focused frames-3212--3214 access capture has SHA-256
`53c5797c61b3e797ad1ad563bd055d1e2813f09c7d283e1e2f143fd85437d16b`,
zero unresolved stores, and independently fixes the player flag write at 3213
and stored player centiseconds 3357. The 1,921-row frozen gameplay projection
has SHA-256
`ac367372f2881f07f3c3e9ff8eb763070432210202bf819ee358f5fae4a6f690`.

## Exact defect reproduction

With the identity-bound ignored runtime restored at
`local/native/dragster-idle/`, run:

```sh
python3 tools/project.py native finish-check \
  --manifest tests/manifests/native/full-race-review-release-3213.case.json \
  --save-frame 3213 --save-frame 3214 \
  --save-frame 3225 --save-frame 3226 \
  --save-frame 3227 --save-frame 3228 \
  --artifacts artifacts/m3-01-review-low-speed-native \
  --report artifacts/m3-01-review-low-speed-native/report.json \
  --timeout 180
```

Observed exit 1. Both native processes complete and are byte-identical to each
other. `gameplay_and_finish_identical` fails with this first divergence:

```json
{"frame":3227,"differences":[{"field":"speed","frozen":1,"native":0}]}
```

Native frame 3226 agrees at speed 37, displacement 1 and position 25354;
frame 3227 agrees on position 25354 and displacement 0, isolating the mismatch
to speed. The failed report SHA-256 is
`49967991af545a3bf9ebad1cd0a3254481e5b385ec519dc22908ca21ead6e7b1`.
Because comparison fails before the command's restore loop, the save-frame
arguments are not reported as passes; the accepted-case restores below cover
the serialization boundary independently.

## Submitted-head reproduction

Before adding reviewer files, the following ran at clean submitted head
`f985beb` and recorded `source.dirty=false`:

- Continuous `native finish-check`, save frames
  3212/3213/3214/3453/3454: all required checks pass; report SHA-256
  `e15f2d6b155f6ae66fcb62a7f9d2a00de79048ecba3526affcd8e069904013b1`.
- Release-3000--3299 `native finish-check`, save frames
  3213/3214/3317/3318/3319/3558/3559: all required checks pass; report
  `ebeb3dd1b425d7d6b8580e6b3b06451a0b319e39545f6a2b3a40fc00a9da4ccc`.
- M2 primary, cadence-17 and release-2347 compares: pass with report hashes
  `208c64eb...ec51e`, `2786056e...d87c`, and `4f735efb...9331`.
- M2 primary restore at 1631/2200 and release restore at 2761/2787: pass with
  report hashes `c220d322...4fc5` and `9a706a8b...9442`.
- Debug and sanitizer synthetic suites: each passes 288/288 (268 Python,
  17 CTest and three-process hash `0be347c529fadda9`). Sanitizer report SHA-256
  is `61b55dc46b2283ee8520f3d101b7a130839cf796cccae85ce482ef0826a0ca6d`.

No required check in those submitted-head runs was skipped.

## Source review

The V1/V2 layout is an explicit field-by-field little-endian encoding; it does
not serialize C++ struct layout, pointers or padding, and its reader rejects
truncation, trailing bytes, non-binary flags, invalid enums and delay values
over 240. V1 stays exactly 333 bytes before a finish and the parser permits only
a one-way change to 369-byte V2. Finish state is a member of `MovementState`;
no mutable hidden global was added. The runner receives only the seed, static
content and controller stream. Frozen reference rows remain in the Python
validator and are not passed to the native executable.

Update ordering is readable and matches the two submitted freezes: snapshot
timer, react to an existing player finish on the following update, override
derived horizontal axes, run ordinary rider updates, apply finish slowdown,
advance timer/rewards/progress, then record new crossings. The separate early
return after displayed delay 240 preserves the next-update transition. The
source documents measured units and ROM ranges, but the hard-coded seven-entry
low-speed tail plus broad fallback is visibly narrower than the nearby-input
domain; the reviewer case demonstrates that the fallback is not exact.

The full-race divergence report is sufficient to identify this defect by exact
frame, field and frozen/native values. It is less diagnostic than the accepted
M2 report because it omits the prior sample, current input and canonical-byte
offsets; improve that as an advisory follow-up if the correction needs more
than the isolated speed-tail reproduction above.

## Required correction and re-review

Recover and implement the positive-speed low-tail rule exercised by incoming
speed 37 so frame 3227 remains 1 and frame 3228 reaches 0, without adding this
single pair as an unexplained special case. Add a focused authored regression,
then run the reviewer-owned case, both submitted full-race cases/restores, the
five M2 regressions, and debug/sanitizer suites on the corrected behavioral
commit. A fresh sequential reviewer should approve that exact corrected commit.

## Corrected sequential re-review

- Re-review decision: **return for one exact signed arithmetic boundary**
- Exact submitted head: `073bb9d19263947a26b82a0972c576db43f20666`
- Behavioral correction: `d0d5cfbc2966ea274108b681c78a04413962cefc`
  versus returned-review base `e62f296fb8a85ddbf2652f9900e1e5aadb88a98d`
- Review checkout: `review/M3-01-native-finish-correction` in
  `.worktrees/m3-01-rereview`
- Reviewer/runtime: fresh sequential OpenAI Codex session, no child agent. The
  executable on PATH reports Codex CLI `0.46.0`, not the requested `0.153.4`;
  the runtime did not expose a separately verifiable model identifier. The
  user-supplied quota baseline was 50% used with a 54% stop threshold; no later
  percentage was exposed, and no credits/reset were redeemed.

### Decision

Return the corrected behavioral commit without changing its implementation.
The positive reviewer-owned case and every requested regression pass, and the
correction does replace the enumerated seven-value tail with ordered arithmetic.
However, its newly public and documented signed helper does not exactly match
the cited PAL routine at velocity `-10`.

At PAL `$83:E91A` the negative path executes `CMP #$FFF6` followed by `BPL` to
the store. Consequently signed `-10` is stored unchanged; only values below
`-10` receive `ADC #10`. The positive path uses `CMP #10` / `BMI`, so positive
`10` does become zero. Candidate `speed_toward_zero` instead tests
`speed <= -amount`, making `-10 -> 0`. This asymmetry is an original integer
boundary and must be preserved under D-0003. It is also inside the correction's
asserted surface: `movement.hpp` documents signed 16-bit input/output, the
implementation says it reproduces `$83:E90D-$83:E932`, and the new authored
test calls the negative side while describing the arithmetic as general.

Reproduce the source-side result against the built exact-head test executable:

```sh
lldb --batch \
  -o 'breakpoint set -n main' -o run \
  -o 'expr -- (unsigned short)unirally::finish_speed_toward_zero((unsigned short)65526)' \
  -o 'expr -- (short)unirally::finish_speed_toward_zero((unsigned short)65525)' \
  build/lab-debug/tests/native/movement_update_tests
```

Observed values are `0` for input bit-pattern 65526 (`-10`) and `-1` for
65525 (`-11`). Inspect the identity-verified PAL bytes at LoROM file offset
`0x01E91A`:

```sh
rom_path=$(sed -n '1p' local/rom-location.txt)
xxd -g1 -s 0x1e91a -l 27 "$rom_path"
```

They decode as `LDA $04BB; BPL positive; CMP #$FFF6; BPL store; CLC;
ADC #10; ... positive: CMP #10; BMI store; SEC; SBC #10; store $04BB`.
The ROM identity check passed all 10 expected identity fields for PAL SHA-256
`a1105819...1fd4`.

### Correction and baseline audit

`git diff e62f296..d0d5cfb` changes only code, authored tests, diagnostics and
records. No replay manifest, native case, reference projection or expected row
changes in that range, and `git diff --check` passes. The correction removes the
per-speed table and orders its ten-unit pre-adjustment before ordinary limiting,
then conditionally removes 24 units without crossing zero. The new incoming-37
full-update assertion is meaningful: the returned implementation's `<40`
fallback would produce zero directly, while the test requires `37 -> 1 -> 0`.
The finish divergence enhancement also preserves the prior sample and previous
and current inputs, and its command-layer regression passes. The missing `-10`
boundary is the only defect found in the corrected diff.

### Exact-head validation

All successful reports below record source `073bb9d`, `dirty: false`, zero
failed/missing/skipped/timeout checks:

- Reviewer release-3213 finish check, restores
  3213/3214/3225/3226/3227/3228: 24 passed; report SHA-256
  `60e204786665f25fb427ac4ca144f347d9e12d18a2981700a64844ecb241da06`.
- Continuous finish check, restores 3212/3213/3214/3453/3454: 21 passed;
  `39454aced801493dde6fdd91c72bcc2ee38727d767e1d3f41d37df1cf25212c1`.
- Release-3000--3299 finish check, restores
  3213/3214/3317/3318/3319/3558/3559: 27 passed;
  `6ed7717cf4fbfaf91b22bbf1727a767a03a1399a7eefa7aee24a000015c9f9fe`.
- M2 primary, cadence-17 and release-2347 comparisons: six passed each;
  report hashes `1ab93583...19c1`, `dcd4d099...186b`, and
  `08d994b9...6c3a`.
- M2 primary restores 1631/2200 and release restores 2761/2787: ten passed
  each; report hashes `6f419211...25c0` and `8d82dfd0...2781`.
- Debug and sanitizer synthetic suites: 288/288 each (268 Python, 17 CTest,
  three fresh-process repeatability), hashes `a57a4f2d...cbe9` and
  `dc8eab94...6abb`. No sanitizer finding occurred.

The first debug build correctly reported the missing isolated toolchain and was
rerun after successful pinned bootstrap. An attempted concurrent launch of the
two original finish checks produced two `ninja` recompaction failures because
both commands reconfigured the same build directory; both cases were then rerun
sequentially into the clean passing reports above. Neither failed attempt is
reported as a gameplay pass.

### Required correction

Preserve the PAL negative equality boundary in the general helper and add the
missing authored assertion for signed `-10` (neighboring `-9` and `-11` are
useful guards). Rerun the focused CTest and debug/sanitizer suites; the frozen
positive full-race cases need no expectation change. Submit the new behavioral
commit for another fresh sequential review.
