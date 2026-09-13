# M4-03 independent review

- Candidate: `d116d8f15674df52e5bd7028e6bf5ac47b02d944`
- Base: `9dacdf800325947e9141887934282a494910710d`
- Reviewer: fresh OpenAI Sol/medium session
- Review date: 13 September 2026
- Result: **changes requested**; the coordinator has not accepted M4-03

## Predeclared withheld case

Before capturing or inspecting frame 2000, this review selected the player
collision call at frame 2000 under the frozen replay's Right-only input. The
review used a fresh frame-1999--2001 complete/no-overflow access capture,
derived position, pose/reflection inputs, collision points, decoded source
addresses and returned words from runtime inputs, and compared those words with
a separately regenerated immutable `0xC3` decode. Frame 2000 is not one of the
worker's frozen frames 1700, 2220 or builder frame 2224.

The capture is `complete`, has no failure or truncated PC log, and its maximum
frame delta is 18,692 instructions in a 262,144-entry ring. It retains sample
digest `791a7863...6557b68` and final state `2a843314...a16aeb`.
Its `access.json` SHA-256 is
`4958e0c7c06bf8f823c6274a2755bed7ce3e6480c871b2b3353ddca3a2f24e35`.

The four runtime stores give player x/y `14222/1540`, pose index `452` and a
true reflection flag. Independently reading the pose record at ROM file offset
`1084960` and selector-zero template at `1064095`, without importing
`zoom_zoo_contract.py`, gives these ten points:

`(36,6) (22,5) (36,22) (41,25) (31,25) (44,30) (28,30) (41,35) (31,35) (36,38)`.

The runtime-derived width 256 and byte stride 512 select coarse decoded
offsets `12747,12749,13259,13261`, whose immutable words are `97,98,13,129`.
Applying the observed wrapped quadrant/fine-cell arithmetic gives decoded
addresses
`35893,35891,35901,35901,35899,35909,35907,35909,35907,35909`.
The independently decoded bytes at those addresses give words
`17408,17408,1024,1024,1024,1024,1024,1024,1024,1024`, exactly equal to the
ten values observed in reverse `$81:8B6A` store order. No captured upload or
staging bytes were used as reconstruction input.

## Reproduction

The isolated review checkout initially had no `local/rom-location.txt`; the
first ROM inspection, two decodes and contract invocation therefore each
correctly exited 2 as missing prerequisites. The existing private locator,
pinned core/toolchain and Classic pack were then made available only under the
ignored `local/` runtime area. The successful commands were:

```sh
python3 tools/project.py rom inspect --expect tests/manifests/rom/unirally-pal.json --report artifacts/m4-03-review/rom-inspect.json
python3 tools/project.py content decode --manifest tests/manifests/content/zoom-zoo-reference-inventory.json --out artifacts/m4-03-review/decode-1 --report artifacts/m4-03-review/decode-1-report.json
python3 tools/project.py content decode --manifest tests/manifests/content/zoom-zoo-reference-inventory.json --out artifacts/m4-03-review/decode-2 --report artifacts/m4-03-review/decode-2-report.json
python3 tools/project.py content zoom-zoo-contract --contract tests/manifests/content/zoom-zoo-reference-contract.json --report artifacts/m4-03-review/contract-report.json
python3 -m unittest tests.tooling.test_zoom_zoo_contract -v
python3 tools/project.py access capture --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --out artifacts/m4-03-review/load-1286-1291 --from-frame 1286 --to-frame 1291 --watch-address 0x002115 --watch-address 0x002116 --watch-address 0x002117 --watch-address 0x002118 --watch-address 0x002119 --watch-address 0x00420B --watch-address 0x00420C --watch-address 0x7F0000 --watch-address 0x7F000B --watch-pc 0x82E1A7 --watch-pc 0x82E2CD --watch-pc 0x82E2D8 --watch-pc 0x82E2F5 --watch-pc 0x82E31A --watch-pc 0x82E346 --watch-pc 0x82B7DD --wram-series-range 0x10000 0xC5E9 --timeout 240 --report artifacts/m4-03-review/load-1286-1291-report.json
python3 tools/project.py access capture --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --out artifacts/m4-03-review/withheld-2000 --from-frame 1999 --to-frame 2001 --watch-address 0x0000A5 --watch-address 0x0000A7 --watch-address 0x000F85 --watch-address 0x000F51 --watch-pc 0x818D15 --watch-pc 0x818D0F --watch-pc 0x818D97 --watch-pc 0x818D9C --watch-pc 0x818AA1 --watch-pc 0x818AC0 --watch-pc 0x818B66 --watch-pc 0x818B6A --watch-pc 0x818CBB --watch-pc 0x818CDD --wram-series-range 0 0x20000 --timeout 240 --report artifacts/m4-03-review/withheld-2000-report.json
python3 tools/project.py build --preset app-debug --report artifacts/m4-03-review/build-app-debug.json --task M4-03-review
python3 tools/project.py test --suite synthetic --preset app-debug --artifacts artifacts/m4-03-review/app-debug-rerun/artifacts --report artifacts/m4-03-review/app-debug-rerun/report.json --task M4-03-review
python3 tools/project.py replay compare --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --runs 2 --artifacts artifacts/m4-03-review/zoom-replay/runs --report artifacts/m4-03-review/zoom-replay/report.json --task M4-03-review
python3 tools/project.py content decode --manifest tests/manifests/content/dragster-segment.json --out artifacts/m4-03-review/dragster-decode --report artifacts/m4-03-review/dragster-decode-report.json --task M4-03-review
python3 tools/project.py content pack-inspect --pack local/classic-crawler-dragster.pack --report artifacts/m4-03-review/pack-inspect.json --task M4-03-review
python3 tools/project.py native finish-check --manifest tests/manifests/native/full-race-continuous.case.json --content-pack local/classic-crawler-dragster.pack --save-frame 1600 --save-frame 3213 --save-frame 3453 --save-frame 3678 --preset lab-debug --artifacts artifacts/m4-03-review/native-fresh --report artifacts/m4-03-review/native-fresh/report.json --task M4-03-review --timeout 120
git diff --check 9dacdf800325947e9141887934282a494910710d d116d8f15674df52e5bd7028e6bf5ac47b02d944
```

Observed results and report SHA-256 values:

| Check | Result | Report SHA-256 |
| --- | --- | --- |
| PAL ROM inspection | 10/10 identity fields | `9e19769513a5c8e9eb23adc7e6548c34b3a5bc689e35b1648b62d902c88b2a9a` |
| Decode 1 | 50,665 bytes, `db677015...fdd28` | `0d68011acb58cb2bd0dc0f21fc37e2adbf0fb68fff6a5e6ddd371470feabb679` |
| Decode 2 | same bytes and tracked-shape `decode.json` (`bb15b647...95b`) | `acc378ec7a352ed2f5e1b5fd8eed584c806ba052a268799f21c1a06df84f5c4c` |
| Contract command | 3/3; 24 entries, 406 transfers, 98 gather bytes, 40 collision words | `cf76b22f9f70c48f486c136e2c9046de00a4c051127e3f1f35f5bbb45a8441ff` |
| Focused authored tests | 7/7 | no report requested |
| Load capture | complete/no overflow; access SHA `bc733d1c...cd56c` | `ccf081ee8570eef05775a7916622b4ae16435304fd90f4792b36d490f156a8b1` |
| Withheld capture | complete/no overflow; exact 10/10 independent words | `7f039b861fe761d10ab191a78f5f919dbc144506ca6f6694e7f28f93320fc9d3` |
| ROM-free app-debug | 322/322 | `866502e6e57e4d92a0e0b1af577d042488c74bd9efffe4fd87e410117d6d3ef8` |
| ZOOM ZOO replay | 24/24, exact two-run state and A/V | `5943a8247c0264f26d55af3eeccd161a1e7e8d349a71dd6d48a6126e7bcd671f` |
| DRAGSTER content | 10/10 identities | `47fd557d7cd23ac0f794e553a08b6b89a771b836c05c8158c5fe1a33b3b0a155` |
| Classic pack | 25 entries and every hash | `6e22979eb39abb6602551e6cd8c8cc160a53440f5dbd969e3e29e174e8e7a6f2` |
| M3 full race/restores | 18/18 | `82585a7a36ed326461d8ccca1d6e1eeb26b6410006425e830c2da55febd1e164` |

The fresh load capture exactly reproduces worker hash `bc733d1c...cd56c`.
There are 25 cursor executions, 24 selected loader entries, 203 table-byte
iterations and 406 DMA triggers. Comparing end-of-frame 1291 runtime memory
with the immutable decode finds exactly one changed byte: decoded offset 11,
`0xCF -> 0xE8`. The selected bytes are the declared 24 IDs, followed by the
consumed `0xFF` at `0xC5E7`; the next `0xFF` remains opaque.

One initial full-suite attempt failed 321/322 because the review temporarily
made all of `local/` a symlink outside the worktree, causing an existing
temporary-path containment test to reject its runtime directory (failed report
`bd83266d...1e558`). Replacing that with a real ignored worktree-local
directory and only individual runtime links produced the recorded 322/322
pass. The first native command omitted its required positive `--timeout` and
exited 3 before execution; the exact corrected command above passed 18/18.
Neither is reported as a candidate pass.

## Finding requiring correction

The machine-readable contract accepts contradictory fields that it presents
as part of its validated boundary.

First, `gather_samples[].destination` is never parsed or compared with the
assembled byte count. The following mutation changes the 66-byte runtime range
`0x0437-0x0478` to the two-byte unrelated range `0x0000-0x0001`; the full
ROM-backed command still exits 0 and reports the reference contract passed:

```sh
mkdir -p artifacts/m4-03-review/mutations
cp tests/manifests/content/zoom-zoo-reference-contract.json artifacts/m4-03-review/mutations/wrong-gather-destination.json
perl -0pi -e 's/"destination": "0x0437-0x0478"/"destination": "0x0000-0x0001"/' artifacts/m4-03-review/mutations/wrong-gather-destination.json
python3 tools/project.py content zoom-zoo-contract --contract artifacts/m4-03-review/mutations/wrong-gather-destination.json --report artifacts/m4-03-review/mutations/wrong-gather-destination-report.json
```

The passing report SHA-256 is
`b033c5f200cc42cbf1d17534289ac0236a71b8542bab81b979e739aeefd04295`.
This violates the task's explicit malformed-bound/mutation gate and the Astra
checkpoint's requirement to reject contradictory descriptive runtime bounds.
The validator should bind the observed staging start and require the inclusive
destination length to equal the independently assembled bytes; a CLI-level
mutation test should freeze that rejection.

Second, `identity.sample_digest`, `identity.final_state_sha256` and every
`identity.captures` value are accepted but never checked. Replacing the accepted
sample digest with 64 zeroes also leaves the full ROM-backed command passing
(report `6da63271b00aa2acf5cfd01757c6ff9f5318b6d359f12ad41d44384a7c4d6385`).

```sh
cp tests/manifests/content/zoom-zoo-reference-contract.json artifacts/m4-03-review/mutations/wrong-sample-digest.json
perl -0pi -e 's/"sample_digest": "[0-9a-f]{64}"/"sample_digest": "0000000000000000000000000000000000000000000000000000000000000000"/' artifacts/m4-03-review/mutations/wrong-sample-digest.json
python3 tools/project.py content zoom-zoo-contract --contract artifacts/m4-03-review/mutations/wrong-sample-digest.json --report artifacts/m4-03-review/mutations/wrong-sample-digest-report.json
```

These fields should either be exact-gated as the adjacent core/replay identity
fields are, or removed from the validator's claimed machine-readable identity;
add focused mutations for whichever boundary is chosen.

## Source, regression and hygiene review

The arithmetic implementation is small and readable, uses explicit 8/16-bit
wrapping, preserves LoROM bank crossing for the observed loader pieces, derives
tile directory/table/flag addresses from the ROM, and reconstructs gathers and
collision reads from immutable decoded bytes. The current seven mutation tests
exercise source/ROM metadata, region bounds and payload identity, decoded-only
gathering and collision width/wrapping, but omit both failures above.

The candidate changes only six text source/evidence files. `git diff --check`
passes; no ROM, decoded payload, state, trace or large binary is tracked. The
accepted `tests/manifests/replay`, `docs/map`, `tests/manifests/native` and
`src` tree IDs are identical at base and candidate, as are the DRAGSTER
content, Classic-pack rules, ZOOM ZOO inventory and PAL ROM manifest blobs.
The reproduced replay, DRAGSTER decode, pack inspection and full-race restore
checks give behavioral confirmation that those accepted identities were not
weakened.

No native ZOOM ZOO implementation, general two-track schema, collision meaning,
negative-Y/edge branch, finish/result behavior or cross-platform reference run
was reviewed or is implied. App sanitizers and coverage-map regeneration were
not rerun because the reproducible schema failure already requires a corrected
candidate; the ROM-free debug suite, exact replay, accepted native restores and
the task-specific reference captures all completed.
