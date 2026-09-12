# Native comparison command implementation

Base main claim bb9dda9, merged reviewed input/timer/comparator branch at the
parent of this submission. Worktree `.worktrees/m2-01-native-cli`, branch
`codex/M2-01-native-cli`. Coordinator wrote protocol.py and three authored tests;
`python3 -m unittest discover -s tests/tooling -p test_native_cli.py` passes.
No command is registered or implemented yet; no native gameplay has been run.

Agreed motion-worker process interface:
`movement_runner --seed <canonical.bin> --content-dir <dir> --inputs <text>`.
Input contains only contiguous decimal `frame port0_mask port1_mask`, standard
libretro button order, starting seed.frame+1. Stdout header is
`unirally-movement-v1`, then initial and every update row:
`frame <13 projected integer fields> <canonical_state_hex>`.
Canonical state starts with eight ASCII bytes URMV0001, then little-endian u32
frame and explicit semantic payload. Same bytes are accepted as seed. Protocol
parser validates header, row count/order, numeric tokens, state magic/frame and
constant byte width. Caller must also require emitted initial state equals seed
and run approved compare_rows to validate all projected values/initial projection.

Motion worker prepares ignored `local/native/dragster/runtime.json`: schema1,
rom_sha256, seed {path,sha256,frame:1533}, content_dir, files [{name,size,sha256}],
plus provenance extras. Paths relative to repository root. Tracked native case
will bind replay/expected paths and runtime metadata path/hash once generated.
Runtime preparation and canonical seed importer belong to motion worker; static
filenames are enumerated there. No ROM/emulator dependency should remain in
comparison execution once seed/content exist. Missing fixtures are exit2.

Remaining command work: strict case/runtime/content/seed identity validation;
ensure current CMake preset's movement_runner is rebuilt with standard bounded
build helpers; run twice in fresh processes with only seed/static content/inputs;
parse, require exact initial seed, compare every field, hash canonical state
bytes and emit standard report with input/binary/source hashes and first
divergence. Preserve exit0/1/2/3/4 semantics and narrowed reporting windows.
Reject failed, malformed, truncated or nondeterministic producer output; never
hide failure via reference fallback. Avoid report paths overwriting inputs.
Authored command tests may stub the producer and must be labelled accordingly.
No expected row/path may be passed to the native process. Withheld output stays
sealed until full native routine is fixed. Native cases/public command are not
accepted merely by passing these protocol tests.

## Resumed command submission (Astra coordinator)

Implemented `python3 tools/project.py native compare --manifest <case.json>`
with optional preset, from/to frame, timeout, artifacts and report. Output uses
a fresh directory under repository artifacts/; if only --report is supplied,
its parent is that fresh directory. Reports cannot overwrite internal artifacts.
No ROM or reference execution occurs in this command.

Case schema1/kind `native_movement_case` binds `replay`, `expected`, and `runtime`,
each `{path, sha256}`, repository-relative paths. Runtime follows the previously
agreed schema and exact 12-file static inventory; unbound content entries reject.
`movement_runner` is built at `build/<preset>/src/core/movement_runner` through
the existing bounded build command. Two fresh processes receive only canonical
seed, static content directory and controller input file. Complete rows, exact
initial seed, all projected fields and canonical states are validated; content,
seed, binary and other inputs are rehashed after execution. Exit codes0/1/2/3/4
retain success/failure/missing/invalid/timeout meanings.

Ten authored CLI/protocol tests pass, including no-reference process argv,
first divergence, invisible state nondeterminism, altered seed, truncated output,
crash/timeout, invalid identity/window and artifact collision. Producer/build are
stubbed in command tests; these do not prove native execution or gameplay.
The first full synthetic run had240 Python tests pass but exited2 because this
worktree had no isolated toolchain/build. Bootstrap/build and a final complete
suite follow; missing checks are not treated as passes. Early authored fixture
failures were an absent two-port controller declaration and a macOS resolved-path
expectation; corrected only test setup, no expected gameplay outputs changed.

Preparation and native runner remain unimplemented. The movement worker should
produce the agreed runtime.json and a primary.case.json binding existing frozen
primary.replay.json/primary.expected.json hashes, without changing either file.
Do not open withheld expectations before fixing the full native implementation.
Independent command review and real primary/withheld executions remain required.
