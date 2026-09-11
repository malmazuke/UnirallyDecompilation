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
