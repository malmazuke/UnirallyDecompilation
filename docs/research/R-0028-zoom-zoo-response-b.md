# R-0028 — bounded ZOOM ZOO inter-contact response-B recurrence

- Status: worker candidate; bounded reference research awaiting independent
  review; production native behavior remains unchanged

## Scope and identity

This record removes both riders' `response_b` words from M4-09's per-call
captured inputs on frames 1650--1700. It seeds those two words once at the end
of frame 1649, executes the reached inter-contact producer for each ordered
rider call, compares pose consumption and publication, and supplies the
computed values to the accepted position/contact composition. Velocity, pose
and all other inventoried contact fields remain captured external inputs. This
is a bounded ten-word recurrence, not autonomous ZOOM ZOO gameplay.

The supported PAL ROM SHA-256 is
`a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`.
The pinned bsnes core is `7d5aa1e656b9171524d01b1b22917197d8121cb4`
with patch
`a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885`;
the local library used for capture has SHA-256
`a0823616c3fecc7aa3da2a1ab5a2a64501293283b1871432ba2579da6ba7559f`.

The preregistration at claim `087660809f66c4c8d5a2468421ef306b0ff3a7f0`
froze the full watch set, writer/phase/width hypotheses and one variation:
release Right only at frame 1668 and restore it at 1669, predicting exact
evidence through 1667 and controller divergence at 1668 only. It deliberately
made no producer relevance or reconvergence claim.

## Instruction-derived producer

The inclusive 347 ROM bytes at `$82:A49F--A5F9` (file `0x01249F`) have SHA-256
`92c1eda01ff0d0fe27d8e5a6f6744216c86105457f53410e0f133aa148531c96`.
The routine starts with `REP #$30`, so its predicates use 16-bit accumulator
and index semantics. It tests `$0F1B/$0F1D`, the signed absolute value of
surface angle `$0F17` against 30, and the signed wrapped result of
`unsupported_count - 9`. It then changes to an 8-bit accumulator with
`SEP #$20` before the byte replacement paths. Guards `$0F49/$0F89` and the
nonzero `$0F23/$0F5D` paths preserve the incoming value by reaching the common
return without a store.

The reached positive byte path at `$82:A562--A568` computes the low byte as
`0xFE + $031D,Y` and writes only `$0F57`; the existing high byte is therefore
preserved. The symmetric low path at `$82:A507--A50D` computes
`2 - $031D,Y` but is not reached in this domain. The clear at
`$82:A5B4--A5B9` first executes `REP #$20`, then writes a 16-bit zero. Tests
exercise both byte formulas, wrapping, high-byte preservation, word clear and
no-write preservation without asserting that the unreached byte path occurred
in the capture.

Ordered events establish the data flow. Motion loads persistent `$0BB7/$0BB9`
to scratch `$0F57`; only the rider selected by phase `$0302` invokes the
producer; pose consumes `$0F57` at `$83:F00D`; motion publishes the word; and
the later contact routine reads and republishes it. Phase value 1 selects the
player as active and value 0 selects the opponent. The inactive rider preserves
its recurrent word. No later captured response-B value is used as an input.

## Capture and recurrence result

Two fresh primary captures are byte-identical at access SHA-256
`f8488406dc6efb29fa09918c6425416c6d9d8184a9e5ea2c2394d14904b25bcd`
and WRAM-series SHA-256
`53c03d228999d3c1fbe5ee22be64a3965a77848e9b8f8adbeaba4374cba3d13d`.
Each contains 953,416 instructions and 471,721 accesses, with zero unresolved
stores, zero non-ROM PCs, no truncation and a maximum ring delta of
18,640/262,144. Two fresh variation captures likewise agree at access
`e2e526937b2c9ccc20d9183c5af76f9bde1456ddb7535db9d83904edc8de6f54`
and series
`1f5f269efb0cf7de0e22a0bf77045ed395bce9692f0c2b0ff2534304451077d9`.
Each contains 953,406 instructions and 471,830 accesses with the same complete,
nontruncated and resolved-store properties.

The end-1649 response-B seed is player 0 and opponent 254. Across 102 ordered
calls, 51 inactive calls preserve, 42 active calls take the low-angle/count
16-bit clear, six active opponent calls at frames 1650, 1652, 1654, 1656, 1658
and 1660 take the reached `0xFE + control` byte path, and three calls take the
zero-pair 16-bit clear. Active counts are player 25 and opponent 26. The
opponent's frame-1661 inactive call preserves and publishes 254; its frame-1662
active call then takes the zero-pair word clear, proving the observed 254-to-0
transition from an ordered writer rather than an inferred zero.

The external producer-input inventory is `$0F1B`, `$0F1D`, surface angle,
unsupported count, `$0F49`, `$0F89`, `$0F23`, `$0F5D` and indexed control.
Inputs behind a short-circuiting branch are recorded as unavailable rather than
invented. Both riders finish with response B zero. All 102 pose-consumed,
motion-publication, contact-input and contact-output comparison targets match.
The primary recurrent-row SHA-256 is
`0a6ba3b5d1fc8bc3c33e0a6f022d47fa0a91965a1b60c1f4f5b176055fc337ba`.

Supplying those computed words to the accepted M4-09 composition preserves all
102 calls and all 1,020 sample words/source offsets. Its sample-word and source
SHA-256s remain `98e77e32b3540aa98e796edc5d7fb7c0bb2736e44e8e4b3ee1b4cf1827d188dd`
and `f24ccd2738300030debe07020d4140f4f8d0d6e8e711b0f8ea3d2a8cd526fa27`.
Final player state is `(x=9824,y=1605,xres=12,yres=10)` and opponent state is
`(x=7489,y=1520,xres=-4,yres=12)`.

## Worker variation

The finalized replay repeats twice with sample digest
`f616369d41063af61b8cc567c1d2ca4b3c2748b117cb25a67826a271a6705d32`,
final-state SHA-256
`201a4bbd64e6080ef4ffab95505133af0614eda640935514005cfeb53935e1bc`
and A/V digest
`c17eefd127b41505016e982357c7626d6cfcbc1903d51e94fdb9dfc4cb65f082`.
The preregistered prediction holds: controller state differs only at frame 1668
and all evidence is exact through 1667.

The full accepted composition first differs for the player at 1668 and its
sample words first differ at 1672. The response-B producer row first differs at
1669 because an external producer input/phase row changes, but its computed
response-B value never differs. Opponent composition stays exact and player
composition has not reconverged by frame 1700. Variation final player state is
`(9822,1604,11,19)`; opponent state is unchanged. Variation recurrent rows have
SHA-256
`4af08474d82d8784c99fb5c3d8872c393ef43abcb56f612536dbeb848bf8a8d4`.
This is an honest negative relevance result for response B: the input is useful
for composition coverage, but does not perturb this component's output.

## Integrity and reproduction

The exact-bound authored manifests reject changes to their canonical document
digests. The recurrence-chain validator and ROM-free tests reject or change
seed/rider swaps, wrong active phase, an omitted writer, per-call reseeding,
captured response substitution, producer/contact reordering, byte/word width,
high-byte preservation and clear mutations.

```sh
python3 -m tools.unirally_lab.native.zoom_zoo_response_b capture --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --out artifacts/m4-10/primary-a
python3 -m tools.unirally_lab.native.zoom_zoo_response_b derive --access artifacts/m4-10/primary-a/access.json --content artifacts/m4-10/content --report artifacts/m4-10/primary-derived.json
python3 -m tools.unirally_lab.native.zoom_zoo_response_b verify --access artifacts/m4-10/primary-a/access.json --content artifacts/m4-10/content --manifest tests/manifests/native/zoom-zoo-response-b-primary.reference.json --report artifacts/m4-10/primary-verified.json
python3 -m tools.unirally_lab.native.zoom_zoo_response_b compare-inputs --primary-access artifacts/m4-10/primary-a/access.json --variation-access artifacts/m4-10/variation-a/access.json --content artifacts/m4-10/content --report artifacts/m4-10/variation-comparison.json
python3 -m unittest tests.tooling.test_zoom_zoo_position tests.tooling.test_zoom_zoo_contact tests.tooling.test_zoom_zoo_vertical_contact tests.tooling.test_zoom_zoo_reflected_vertical_contact tests.tooling.test_zoom_zoo_composition tests.tooling.test_zoom_zoo_response_b -v
python3 tools/project.py build --preset app-debug --clean --report artifacts/m4-10/app-debug-build.json --task M4-10 --timeout 180
python3 tools/project.py test --suite synthetic --preset app-debug --artifacts artifacts/m4-10/app-debug-test-final --report artifacts/m4-10/app-debug-test-final.json --task M4-10 --timeout 180 --test-timeout 30
python3 tools/project.py build --preset app-sanitize --clean --report artifacts/m4-10/app-sanitize-build.json --task M4-10 --timeout 180
python3 tools/project.py test --suite synthetic --preset app-sanitize --artifacts artifacts/m4-10/app-sanitize-test-final --report artifacts/m4-10/app-sanitize-test-final.json --task M4-10 --timeout 180 --test-timeout 30
python3 tools/project.py replay compare --manifest tests/manifests/replay/race-crawler-zoom-zoo-right-release-1668.json --runs 2 --artifacts artifacts/m4-10/variation-replay-final --report artifacts/m4-10/variation-replay-final.json --task M4-10 --timeout 180
python3 tools/project.py content zoom-zoo-contract --contract tests/manifests/content/zoom-zoo-reference-contract.json --report artifacts/m4-10/zoom-zoo-contract.json --task M4-10
python3 tools/project.py content pack-inspect --pack '/Users/markfeaver/Projects/Unirally Decompilation/local/classic-crawler-dragster.pack' --report artifacts/m4-10/pack-inspect.json --task M4-10
python3 tools/project.py native finish-check --manifest tests/manifests/native/full-race-continuous.case.json --content-pack '/Users/markfeaver/Projects/Unirally Decompilation/local/classic-crawler-dragster.pack' --save-frame 1600 --save-frame 3213 --save-frame 3453 --save-frame 3678 --preset lab-debug --artifacts artifacts/m4-10/native-finish --report artifacts/m4-10/native-finish/report.json --task M4-10 --timeout 180
```

The primary and variation reference manifests have canonical document digests
`6d5d4b0f1dae3b83e8c85b8d289b95d9e1a47eeb79089fd0d34382a50a5e6684`
and `eee84520ac15a32fc7f8b23cfc5d76a14a71f25a6b5d696c5aa2f16f804a8f8d`.
Their tracked file SHA-256s are
`f4fe1270b4cb6f99a9aa09b4e4336b510f9e994dd15b949a5b4aafad00fbda34`
and `f01bd23efd0d124a7f4c9efcb9805bc3042a9abfdf929a624f6d20f4243cdee8`.

Focused M4-05--M4-10 tests pass 51/51. Clean app-debug and app-sanitize
candidates each pass 364 Python tests, 20 CTests and three-process
repeatability. Their final report SHA-256s are
`8f31092b6099feb27fc4a61a8b0b847e4b6e7cc465976741eb852ff55b3623c3`
and `f70476b91a096b2ebf98682192edc99eb5c89077aaeed998238c44b073d39cf3`.
The finalized worker replay passes all 24 required checks with report
`1ae31a481ed37c627344cbed25b5f0cbadca7798ec8f3a9045dca89678357403`.
The frozen ZOOM ZOO contract passes 3/3 with report
`5d8c55a32f2a55b5c072b825195a2102ab86dda8931ca8d764e91e455c1f9286`.
The 25-entry Classic pack passes 3/3 with report
`5b31ef4a736510c730ec32334784cff98a627c0c99b0605b604241d3089f29a1`.
DRAGSTER finish plus restores at 1600/3213/3453/3678 pass 18/18 with report
`22b14bd22d3204c96525b561ac78eab81ddd4a1e06fe47a89f32d52f07e74a02`.

Non-passes are retained honestly. The first replay command used the unsupported
`--out` option and exited at argument validation. The correctly invoked
preregistration replay then failed its four intentional zero-digest
expectations while its two fresh processes agreed; after recording those
observations the manifest was finalized and rerun. The first combined captures
showed that indexed controls `$031D/$031F` and side guards `$1003/$1005` were
missing from the exact watch list. Those incomplete task-owned ignored captures
were deleted, the additive inventory and capture surface were corrected, and
all four captures above were freshly repeated before derivation. No expected
result was weakened or regenerated merely to pass. The first clean debug build
correctly reported the missing isolated toolchain; the pinned bootstrap was
installed and both clean build/test presets were rerun. The first native
finish invocation placed its report outside its fresh artifacts directory and
was rejected at argument validation; the corrected report path then passed all
18 required checks.
