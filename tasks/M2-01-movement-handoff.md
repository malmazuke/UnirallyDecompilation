# M2-01 movement implementation handoff

Continuation baseline (12 September 2026): Codex seven-day window 17% used,
83% remaining, reset 19 September 2026 08:22 AEST. This session's discretionary
implementation ceiling is 27% used under D-0004; the final 20% remains reserved.
No reset credit was redeemed. Incoming coordinator is independently reviewing
the preserved state/seed checkpoint before implementation.

Bounded usage checkpoint on `codex/M2-01-movement`, assigned base `3909c1c`,
OpenAI Sol/medium. The session stopped at the recorded 13% boundary. No child,
withheld expectation, broad capture, native update or CPU interpreter was used.

## Implemented checkpoint

`src/core/movement.*` composes the reviewed contact, speed, progress, input and
timer types into one semantic state for both riders. It adds named jump,
pose/animation, quarter-turn, residue/throttle, opponent-continuation and reward
queue state from R-0011-motion. The initial fixed-order little-endian serialization was 295
bytes, begins `URMV0001` plus LE u32 frame, rejects invalid flags, phases,
cursors, truncation and trailing data, and round-trips independently of host
struct layout. Contact velocity and speed modifier state are not duplicated.

`tools/unirally_lab/native/prepare.py` accepts only the approved single seed
observation: WRAM `f87f42dd...fdf`, cartridge RAM `77441088...9eb`, report
`2e187dc5...49c`, PAL ROM identity, frame1533, exact sizes, feature total0 and
event1 weight4. It extracts semantic fields and writes ignored
`seed.bin`, `content/` and `runtime.json` only from the complete named12-file
static inventory. The actual observation imports with canonical SHA-256
`1264e64d82314ae5c276515a81202d65aab5ff2b801c5de26548e750d000fdbb`;
frame, player input, x and throttle agree with frozen primary frame1533.

## Commands and results

The first build returned exit2 because this worktree had no isolated toolchain.
After bootstrap, debug build passed. Targeted commands:

```
python3 tools/project.py bootstrap --timeout 120 --report artifacts/movement-checkpoint-bootstrap.json
python3 tools/project.py build --preset lab-debug --timeout 120 --report artifacts/movement-checkpoint-build.json
local/toolchain/cmake-3.31.10-darwin-arm64/bin/ctest --test-dir build/lab-debug -R '^movement_state_roundtrip$' --output-on-failure
python3 -m unittest tests.tooling.test_native_prepare
python3 -m py_compile tools/unirally_lab/native/prepare.py
```

Debug build and targeted CTest passed (1/1). Python preparation unittest
passed2/2; py_compile passed. Code checkpoint:476834d9767dc55dbb3de26a4e44fa5e42903d87. Direct import of the approved artifacts produced the digest
above. A hand-written direct check first used byte107 for throttle rather than
its actual byte117; that assertion, not implementation output, failed. No
gameplay expectation changed.

## Limitations and exact next step

No movement update or gameplay agreement is claimed. The complete ignored
runtime and tracked `primary.case.json` were not generated before the usage
boundary, so the all12-file runtime path still needs an end-to-end run. Review
should compare Python-produced bytes through the C++ decoder, especially the
three zero-at-seed displacement-history fields whose persistent addresses were
not stated in R-0011-motion. Then generate the runtime/case binding and implement
frame1534 in recovered order. Record the first primary divergence without
opening either withheld series.

## Independent continuation review

The incoming coordinator found and corrected two checkpoint defects before
movement implementation. The three pose displacement-history words were
silently written as zero; ROM loads/writebacks at `$82:8AE0-$8AF8` /
`$82:8DE0-$8FF2` and `$82:8FE8-$9000` / `$82:92CE-$92E0` establish persistent
player addresses `$7E:211E/$2122/$2126` and opponent addresses
`$7E:2120/$2124/$2128`. All six are zero in the approved frame-1533 dump, so
the initial canonical seed digest remained `1264e64d...fdbb`; authored nonzero sentinels
now prove that the importer reads them rather than assuming them.

Static preparation previously accepted arbitrary same-sized content. It now
requires the frozen SHA-256 for every file and validates every input plus the
repository-relative output contract before creating the runtime. Added the
previously missing speed-table content manifest for ROM offsets `0x051B` and
`0x0524`. All five content decodes passed against the PAL ROM, the complete
runtime regenerated with hash `c271d520...cd0`, and tracked
`primary.case.json` binds that runtime plus the unchanged primary replay and
expectation hashes. Python preparation tests pass 3/3; debug build and CTest
pass; the Python-produced approved seed was decoded and byte-for-byte
round-tripped by the C++ test executable. A subsequent inventory pass found
that nonzero current reflection at `$0BA7/$0BA9` was also absent. The canonical
format is therefore superseded by a 297-byte version before update
implementation. Withheld cases remain unopened.

The corrected seed is 297 bytes, SHA-256
`1c133b99c3395e440ce2d580b9a7eefa131015ec519a16bd50109e94fe09d5d9`;
the regenerated runtime metadata is
`e8d2898408d369b2ed1b9ca91a8891acb88d938fb49d96c05e1ef94d78a4fe89`.
The new semantic update and `movement_runner` implement decoded input, phase
and counter recurrence, the source-derived countdown/brake-release launch,
horizontal throttle, reviewed speed clamp, signed `/32` integration and timer.
The authored first-update test matches frame 1534 exactly. A full primary run
uses only seed, static files and controller masks, is identical across two fresh
processes, and matches all 13 projected fields through frame 1631. Its first
divergence is the predicted coupled boundary at frame 1632: native player speed
448 versus reference 449 after opponent progress leads. Report:
`artifacts/m2-01-movement/horizontal-primary-297/report.json`. This is a
diagnostic checkpoint, not gameplay acceptance; opponent jump/contact,
reward/AI feedback, pose and marker progress remain to be composed. Usage at
this checkpoint is 19% of the seven-day window (baseline 17%, ceiling 27%).

## Autonomous movement checkpoint at the 25% usage guard

Code checkpoint: `fdbf397` (`Compose autonomous native movement update`).
The update now composes the reviewed sampler, progress, flat contact, speed,
input/timer, jump, pose/rolling, quarter-turn, reward and opponent-AI contracts.
Primary comparison passes all 13 fields for all 1,466 computed frames and both
fresh native processes are byte-identical. Cadence-17, first run after the
primary fix, also passes in full. Reports are
`artifacts/m2-01-movement/ai-feature-primary/report.json` and
`artifacts/m2-01-movement/final-withheld-cadence-17/report.json`.

Release-2347 initially exposed neutral coasting. Source access and disassembly
established two independent operations: friction flag 1 at `$82:A8A7–A8C8`,
and active-phase low-speed damping at `$82:A5FA–A61E` for nonzero magnitude
below 64. After implementing both, required fields agree through frame 2787.
Frame 2788 then differs only in displacement (native 0, original 3). The full
release WRAM capture local to the research worktree shows the causal boundary:
idle pose first diverges at 2762 and contact y at 2786. Focused access SHA-256
prefixes are `27ea8d928d5a11df`, `bcc1b4a2e70a3723`,
`daeef08a7f497d74` and `02c8827cd17a80e6`. The original writes the excluded
idle fields `$0F35/$0F37/$0F75…$0F7F` throughout `$82:A0B7–A237`; native state
does not yet contain them. Do not approximate the one-frame displacement.

The full ROM-free synthetic suite passes 273/273 and sanitizer movement tests
pass 2/2 with no diagnostics. Reports:
`checkpoint-synthetic.json`, `checkpoint-sanitize-build.json`. A broad `rg`
before formal unsealing accidentally printed a few isolated withheld expected
lines; no series was deliberately inspected or used for primary tuning, but
this is a recorded process deviation. Formal withheld runs occurred only after
the complete primary pass. No reset credit was redeemed. Usage moved from 17%
to 25% against the documented 27% ceiling.

Exact next work: recover the bounded idle-pose routine `$82:A0B7–A237`, extend
the canonical seed with only future-affecting semantic fields (all zero at the
current seed must still be imported from their established storage), add
authored arithmetic/serialization tests, then rerun release-2347. Only after it
passes should a fresh independent reviewer test the exact candidate and own an
additional withheld variation. M2-01 remains active, not accepted.
