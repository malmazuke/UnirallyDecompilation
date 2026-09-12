# M2-01 movement implementation handoff

Bounded usage checkpoint on `codex/M2-01-movement`, assigned base `3909c1c`,
OpenAI Sol/medium. The session stopped at the recorded 13% boundary. No child,
withheld expectation, broad capture, native update or CPU interpreter was used.

## Implemented checkpoint

`src/core/movement.*` composes the reviewed contact, speed, progress, input and
timer types into one semantic state for both riders. It adds named jump,
pose/animation, quarter-turn, residue/throttle, opponent-continuation and reward
queue state from R-0011-motion. Fixed-order little-endian serialization is 295
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
