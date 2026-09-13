# M4-10 independent review

- Candidate: `5520ab87c6ea4329601ea3b2f2e572bf1ad7a1a2`
- Reviewed range: `087660809f66c4c8d5a2468421ef306b0ff3a7f0..5520ab87c6ea4329601ea3b2f2e572bf1ad7a1a2`
- Review branch/worktree: `review/M4-10-response-b`, `.worktrees/m4-10-response-b-review`
- Verdict: **approved without a material finding**

## Scope and source audit

I read `AGENTS.md`, `docs/STATE.md`, `docs/AGENT_WORKFLOW.md`,
`docs/PROJECT_PLAN.md`, `docs/BUILD_AND_VALIDATION.md`, `tasks/M4-10.md`,
`tasks/M4-09.md`, R-0027, R-0011 acceptance, R-0011 contact and R-0011
motion, then inspected the complete nine-file, 1,082-line additive diff. It
changes no `src/`, accepted evidence/tooling/manifests/replays/projections,
serialization, pack/profile/start/frontend, core/lock, `docs/STATE.md`, task
registry or next-session file. `git diff --check` passes.

The supported PAL ROM is
`a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`.
An independent raw-ROM read confirms that `$82:A49F--A5F9` is 347 bytes with
SHA-256 `92c1eda01ff0d0fe27d8e5a6f6744216c86105457f53410e0f133aa148531c96`.
The decoded instruction and ordered-access audit agrees with the candidate:
16-bit initial predicates and clears, `SEP #$20` before the reached byte
replacement, preserved high byte on `$82:A568`, `REP #$20` before the word
clear at `$82:A5B9`, active phase 1 for player and 0 for opponent, inactive
preservation, and motion load -> active producer -> pose `$83:F00D` read ->
motion publication -> contact entry/output order. The accepted end-1649 seed
is player 0/opponent 254.

Running both authored verifies and the worker comparison on the candidate's
ignored captures passes. All ordinals 0--101 cover 51 calls per rider. Active
counts are player 25/opponent 26. Writer counts are 51 inactive preserves, 42
low-angle/count word clears, six reached `0xFE + control` low-byte writes and
three zero-pair word clears. All 102 producer results, 102 pose reads, motion
publications, contact entries and independently computed contact outputs agree.
The opponent frame-1661 output 254 is preserved through its inactive call and
the frame-1662 active zero-pair word writer supplies contact input 0.

Computed response B composes with M4-09 for all 102 calls and 1,020 sample
words/source offsets. The primary sample digests remain
`98e77e32...7d188dd` and `f24ccd27...526fa27`; the final eight words remain
player `(9824,1605,12,10)` and opponent `(7489,1520,-4,12)`. Both response-B
words finish at zero. No captured later response-B value becomes a recurrence
input.

## Private frame-1670 case

I chose release Right at frame 1670 only and restore it at 1671. The choice and
prediction were recorded under ignored `local/review/m4-10-response-b-review/`
before inspecting evaluator rows or any capture result. The mandatory task-file
read had already displayed the worker handoff summary, so this is not claimed
as blind to that summary; the release frame and all reviewer result expectations
were independently selected before the review experiment.

Prediction: controller divergence only at 1670; player composition first differs
at 1670; opponent remains exact and the player remains divergent at 1700;
response-B entry/output never differs; sample words first differ at 1674 and a
producer evidence row first differs at 1671. The controller, composition,
opponent, persistence and response-B predictions hold. The two timing
predictions are honestly falsified: samples first differ at 1672 and the first
producer row difference is player frame 1675.

Two final fresh access captures in this review worktree are byte-identical at
SHA-256 `6446664720732ea47bb7937eabc23a5982b6acc3e61491b061fbb9b7a32913b9`;
their WRAM series is
`78656aeb01d54915cbbd8537861b005a480acd66cbc35861a002b20474d9d0f3`.
Each has 953,494 instructions, 471,786 accesses, zero unresolved stores, zero
non-ROM PCs, no truncation and maximum ring delta 18,640/262,144. Independent
evaluation again passes all 102 calls/pose reads and 1,020 samples. The private
final eight words are player `(9824,1605,1,28)` and unchanged opponent
`(7489,1520,-4,12)`; both response-B words finish zero. The private full replay
passes 24/24 with sample digest `69963c5d...876b5b2`, final-state digest
`44247474...be312d62` and report SHA-256
`2d7503b5d651787a7fcd90e3cb4304581e6ac4c95138357b57ab9bebcd80df2c`.

Capture command (run twice after finalizing the private replay expectation):

```sh
python3 -c 'from pathlib import Path; import subprocess,sys; from tools.unirally_lab.native.zoom_zoo_response_b import WATCH_ADDRESSES,WATCH_PCS; manifest="local/review/m4-10-response-b-review/race-crawler-zoom-zoo-right-release-1670.json"; status=0
for name in ("capture-final-a","capture-final-b"):
 out=Path("local/review/m4-10-response-b-review")/name; cmd=[sys.executable,"tools/project.py","access","capture","--manifest",manifest,"--out",str(out),"--from-frame","1649","--to-frame","1700","--wram-series-range","0","0x2200","--timeout","180","--report",str(out/"report.json")]; [cmd.extend(["--watch-address",hex(a)]) for a in WATCH_ADDRESSES]; [cmd.extend(["--watch-pc",hex(p)]) for p in WATCH_PCS]; status |= subprocess.run(cmd).returncode
raise SystemExit(status)'
```

## Adversarial checks

The ignored `adversarial.py` derives the real primary 102-row chain, changes
one dependency at a time and calls the candidate validator. Seed, rider, omitted
writer, phase, per-call reseed, captured substitution, order, byte-to-word
width, high-byte replacement and clear-value mutations all reject. Separate
authored calls confirm `0xAB00 -> 0xABFF` on the reached low-byte writer and
`0xABFE -> 0` on a word clear. The tracked focused suite independently exact-
binds both manifests and repeats representative mutations.

```sh
python3 local/review/m4-10-response-b-review/adversarial.py
python3 -m unittest tests.tooling.test_zoom_zoo_position tests.tooling.test_zoom_zoo_contact tests.tooling.test_zoom_zoo_vertical_contact tests.tooling.test_zoom_zoo_reflected_vertical_contact tests.tooling.test_zoom_zoo_composition tests.tooling.test_zoom_zoo_response_b -v
```

Result: adversarial 11/11 checks pass; focused tests pass 51/51.

## Regression evidence

```sh
python3 tools/project.py build --preset app-debug --clean --report local/review/m4-10-response-b-review/app-debug-build.json --task M4-10-review --timeout 180
python3 tools/project.py test --suite synthetic --preset app-debug --artifacts local/review/m4-10-response-b-review/app-debug-test-rerun --report local/review/m4-10-response-b-review/app-debug-test-rerun.json --task M4-10-review --timeout 180 --test-timeout 30
python3 tools/project.py build --preset app-sanitize --clean --report local/review/m4-10-response-b-review/app-sanitize-build.json --task M4-10-review --timeout 180
python3 tools/project.py test --suite synthetic --preset app-sanitize --artifacts local/review/m4-10-response-b-review/app-sanitize-test --report local/review/m4-10-response-b-review/app-sanitize-test.json --task M4-10-review --timeout 180 --test-timeout 30
python3 tools/project.py replay compare --manifest tests/manifests/replay/race-crawler-zoom-zoo-right-release-1668.json --runs 2 --artifacts local/review/m4-10-response-b-review/worker-replay --report local/review/m4-10-response-b-review/worker-replay.json --task M4-10-review --timeout 180
python3 tools/project.py content zoom-zoo-contract --contract tests/manifests/content/zoom-zoo-reference-contract.json --report local/review/m4-10-response-b-review/zoom-zoo-contract.json --task M4-10-review
python3 tools/project.py content pack-inspect --pack '/Users/markfeaver/Projects/Unirally Decompilation/local/classic-crawler-dragster.pack' --report local/review/m4-10-response-b-review/pack-inspect.json --task M4-10-review
python3 tools/project.py native finish-check --manifest tests/manifests/native/full-race-continuous.case.json --content-pack '/Users/markfeaver/Projects/Unirally Decompilation/local/classic-crawler-dragster.pack' --save-frame 1600 --save-frame 3213 --save-frame 3453 --save-frame 3678 --preset lab-debug --artifacts artifacts/m4-10-review-native-finish --report artifacts/m4-10-review-native-finish/report.json --task M4-10-review --timeout 180
```

Both clean app presets pass 364 Python tests, 20 CTests and three-process
repeatability (387 report checks, no failure/missing/skip/timeout). Final debug
report SHA-256 is `50b67584...f2ce0e13f`; sanitizer is
`0c79dfbf...bf95e827`. Worker replay passes 24/24; frozen ZOOM ZOO contract and
Classic pack each pass 3/3; DRAGSTER finish plus four restore boundaries passes
18/18.

Non-passes are retained. Initial capture attempts correctly reported the
missing isolated core; I attached the ignored task-local pinned core build and
reran. Preregistration captures intentionally failed zero digest expectations,
then two captures with mistyped full digest suffixes also failed only those two
expectations; neither was counted as a pass. The final pair above passes. The
first adversarial invocation had an import-path error and was fixed only in the
ignored harness. The first debug suite ran before the required empty
`artifacts/` directory existed and reported two tooling-test failures; after
creating that prerequisite the unchanged exact candidate passed all 364 tests.
The first native finish invocation used a report directory outside the command's
required `artifacts/` root and was rejected at argument validation; the exact
rerun above passed. No test or expected candidate result was weakened.

Private ROM bytes, extracted content, captures, builds and reports remain
ignored. No candidate implementation was modified. Independent review finds no
material defect and approves the candidate for coordinator integration and
hosted CI.
