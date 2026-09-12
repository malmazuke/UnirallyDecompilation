# M2-01A motion worker handoff

Worktree `.worktrees/m2-01a-motion`, branch `codex/M2-01A-motion`.
Base `ba71142a6d766216772360949dd8c04760fa9ffe`.
Research candidate `228286b4ba6d805fd67ccd8858ab562a69c3693b`; review fixes
`03322c0` (evidence guards/import), `2e32232` (reward signed rotation),
`9b840a8` (pose cancellation). No acceptance is asserted here. Coordinator owns
M2-01A acceptance and the transition back to M2-01. No withheld movement series
has been opened. ROM/content/WRAM/SRAM/access traces stay ignored.

## Recovered contract and evidence

Read [R-0011-motion](../docs/research/R-0011-motion.md). It records the exact
GO transition from end1533, opponent marker-driven jump, active-phase input and
quarter tracking, pose/contact publication order, /32 signed displacement,
reward queue latency and the learned feature total that suppresses later jumps.
The reward word128 is read from the identified ROM table, never fitted to speed.
Address dictionaries exist only in isolated research tools. They are not an
emulator-shaped native runtime or autonomous movement acceptance.

The primary model matches231780 output values over1533–2999; the independent
preregistered player-Right release matches26538 over1533–1700. Initial smaller
1576–1618 captures verified the jump prediction. Expanded captures were needed
for GO, the landing reward, and later AI feedback. Their byte identities are:

| Ignored artifact under `artifacts/m2-01a-motion/` | SHA-256 |
| --- | --- |
| `final-primary/access.json` | `2a487346b5bb2dd1760dc2e3a0aef63f4b9117a823f145b3e03a763ddf4f4547` |
| `final-variation/access.json` | `e51e31885c68851dc7536f8625beb102ee7c6589f72a9f1ef5afa5af2ccaf279` |
| `seed-context/report.json` | `2e187dc5cba609ffc8ad611eeeaffd857528f13677cf2167c13bd3b6f685d49c` |
| `seed-context/wram.bin` | `f87f42ddfcdae3010bef8da6823216664f655cb5fcdb54af8b7bbd7876605fdf` |
| `seed-context/cartridge.bin` | `774410886d8e20e123924251c49230fb94a3bfb51438497ea070ba3421b889eb` |

ROM SHA-256 is `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`.
Pinned bsnes source `7d5aa1e656b9171524d01b1b22917197d8121cb4`, patch
`a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885`,
local library `e24fd249295358319f022519daba37569bfb7ef3fa25da578cd6d19fdd29efa8`.
Seed capture uses an empty private save directory and confirms the entire1533
WRAM digest against the fresh primary execution, plus actual8KiB cartridge RAM.
It establishes feature total0 and event1weight4 without an inferred SRAM seed.

## Reproduction

Run from this worktree. `local/rom-location.txt` points outside the repository.
All output arguments below are ignored artifacts and can be replaced with fresh
paths; do not overwrite frozen expectations. Each capture saves `command.json`.

```sh
python3 tools/project.py doctor --report artifacts/m2-01a-motion/baseline/doctor.json
python3 tools/project.py bootstrap --report artifacts/m2-01a-motion/baseline/bootstrap.json
python3 tools/project.py build --preset lab-debug --report artifacts/m2-01a-motion/baseline/build.json
python3 tools/project.py test --suite synthetic --report artifacts/m2-01a-motion/baseline/suite.json
python3 tools/project.py replay compare --manifest tests/manifests/replay/race-crawler-dragster-3000-fields.json --artifacts artifacts/m2-01a-motion/baseline/replay --report artifacts/m2-01a-motion/baseline/replay.json
python3 -m tools.unirally_lab.native.motion_research.capture --out artifacts/m2-01a-motion/final-primary --from-frame 1533 --to-frame 2999
python3 -m tools.unirally_lab.native.motion_research.capture --manifest tests/manifests/native/contact-research/motion/release-before-jump.json --out artifacts/m2-01a-motion/final-variation --from-frame 1533 --to-frame 1700
python3 -m tools.unirally_lab.native.motion_research.probe --capture artifacts/m2-01a-motion/final-primary --report artifacts/m2-01a-motion/final-primary-report.json
python3 -m tools.unirally_lab.native.motion_research.probe --capture artifacts/m2-01a-motion/final-variation --report artifacts/m2-01a-motion/final-variation-report.json
python3 -m tools.unirally_lab.native.motion_research.seed_context --samples artifacts/m2-01a-motion/baseline/replay/run1-samples.json --out artifacts/m2-01a-motion/seed-context
python3 tools/project.py content decode --manifest tests/manifests/native/contact-research/motion/motion-tables.content.json --out artifacts/m2-01a-motion/content
python3 -m unittest discover -s tests/tooling -p test_native_motion_contracts.py -v
```

Base doctor/bootstrap/build/suite passed211checks/199Python. Fresh primary replay
compared two processes: sample digest `72f618f2f7e3416eac64d38f882471b1a9ebee25018ed76143360a92cdd99b1f`,
final state `0f3cc38bd5d644012f0c7afbbfaaec772cf3df5b520cbc0c5c7312d84ab322e3`;
A/V and all declared fields identical. Also reproduced the R0010 isolated sampler
against existing read-only M2-01 access/content:29320 words, report
`baseline/sampling.json`. The command used this worktree's debug sampling_probe,
`--coarse-width 1024`, prior `.worktrees/m2-01/artifacts/m2-01/sampling-access/access.json`
and `content-expanded`, and tracked `movement-sampling.content.json`.

Failed attempts matter: first replay command's `--out` was invalid (exit3);
`--artifacts` is correct. Early full pose probe lacked in-frame `$0E7B/$0FE3`
watches; adding watches fixed stale inputs without changing arithmetic. AI with
feature total held0 failed from1648; evolving the recovered reward feedback fixed
it. Hardware-register writes must not alias WRAM `$7E:2102`. Unresolved observed
writes remain unknown and throw if a model consumes them. Candidate228286b failed
the standard suite because of a Python module-path difference hidden by direct
unittest execution.03322c0 fixed it (222checks/210Python pass). Review additionally
found the source-derived reward negative-boost and pose exact-cancellation
corners; both now have authored regressions and explicit source explanations.

## Native protocol agreed with coordinator (next phase, not implemented here)

Proposed runner command:
`movement_runner --seed <canonical.bin> --content-dir <static-dir> --inputs <text>`.
Input text contains contiguous `frame port0_mask port1_mask` lines, decimal u16
libretro-order button masks, starting one frame after the seed. No expected file,
expected row or captured per-frame call argument may enter runtime input.

Standard output starts `unirally-movement-v1`, then one line per frame:
`frame <13 decimal projections> <canonical_state_hex>`, including the initial
seed row. Projection order is coordinator compare.py's declared order:
joy1l_image, joy1h_image, axis_v, axis_h, pos_x, displacement_x, throttle, speed,
timer_minutes, timer_tens_seconds, timer_seconds, timer_tenths, timer_frames.
Canonical bytes begin eight ASCII bytes `URMV0001`, little-endian u32 frame,
then explicit semantic state. The comparator validates the header/frame and
requires the initial emitted bytes equal the seed exactly. It computes SHA-256
from each decoded canonical payload; native runtime need not implement SHA-256.
No padding, pointer, host endian value or unspecified C++ object bytes may enter
serialization. Exact payload size will follow the native semantic inventory.

Preparation will write ignored `local/native/dragster/runtime.json`:
`schema_version:1`, `rom_sha256`, `seed:{path,sha256,frame:1533}`, `content_dir`,
and `files:[{name,size,sha256}]` covering all static files. Paths are repository
relative. Provenance also binds original seed WRAM/SRAM, reference samples,
manifest/core and transformation version. The preparation command/seed byte
size are not implemented yet and must be recorded when the next phase creates
them. The coordinator's tracked primary.case.json will bind replay/expected
identities and runtime metadata without exposing expected rows to the runner.

Static filenames agreed with component owners:

| Filename | Bytes | Source contract |
| --- | ---: | --- |
| track-data.bin | 33815 | movement-sampling.content.json |
| collision-poses.bin | 32768 | movement-sampling.content.json |
| collision-templates.bin | 17249 | movement-sampling.content.json |
| progress-transitions.bin | 80 | movement-progress.content.json |
| tile-tables.bin | 640 | contact-research/contact/tile-tables.content.json |
| tile-flags.bin | 20 | contact-research/contact/tile-tables.content.json |
| speed-masks.bin | 9 | R0011-speed, ROM0x051B |
| speed-decrements.bin | 18 | R0011-speed, ROM0x0524 |
| pose-slopes.bin | 128 | contact-research/motion/motion-tables.content.json |
| displacement-table.bin | 512 | same motion manifest |
| rotation-reward.bin | 2 | same motion manifest; event1 only |
| rotation-class.bin | 1 | same motion manifest; event1 only |

Native state will embed unique ContactMotion/RiderContactState records; speed
operates on those same velocity references and a SpeedModifiers record. Motion
owns semantic jump/residue/throttle/animation/quarter and AI/reward state, without
register-shaped scratch persistence. Future worker ownership proposed by root:
movement.* plus runner, seed importer and movement tests here; speed_limits.*
by coordinator; flat_contact.* and stable compare CLI by contact worker. Shared
registry/build integration remain coordinator-owned until explicitly assigned.

## Remaining work and next action

Research review is in progress. Finish exact final candidate checks and attach
report hashes, then coordinator integrates accepted contracts and continues
M2-01 native assembly. The primary gameplay closure and declared guarded domain
are supported; arbitrary AI modes, moving braking, unrelated rewards/tricks,
tracks and general input variants are not. Frozen withheld native comparison
and cross-platform/sanitizer movement validation remain future acceptance work.
No internal dependency or this checkpoint requires user intervention.

## Final checkpoint after usage interruption

Coordinator recovered the previous reviewer’s final approval at9b840a8 in
`.worktrees/m2-01-sampling-review/artifacts/motion-review/REVIEW.md`: all four
findings closed; six independent tests including196608 integrator combinations
pass. Approval is scoped research, not native gameplay.

Re-ran on9b840a8 with only this handoff draft dirty (source stable throughout):
`python3 tools/project.py test --suite synthetic --report artifacts/m2-resume/motion-final-suite.json`
passes224/224 checks,212 Python tests; no failed/missing/skipped checks.
Report SHA256 `031946d6a892c3417b6636be295c714ca32b43cb5e988b0eb1f5247f0f9a11f1`.
Re-ran the documented probe on final-primary and final-variation captures with
reports `artifacts/m2-resume/primary-probe.json` and `variation-probe.json`:
231780 and26538 values match, zero mismatches. Report hashes respectively
`e962b6a1227d0ce9a5ab41a9dabec30eca093a0ebef019f3be79797d821be05d` and
`815f1e16bc414d72db9a56b5f616c887f1774aaa72115f50d9bf3cbcc752fc5c`.
This reused hash-identified captures already independently reproduced by the
reviewer; it is not a new original capture. Only documentation changes follow
that source candidate. Next: integrate the contract and implement semantic native
movement with the already agreed protocol, preserving primary-domain guards.
