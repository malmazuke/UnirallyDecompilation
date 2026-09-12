# M2-01 movement implementation — semantic autonomous update

Status: claimed by movement_impl (Sol/medium), after reviewer finished.
Provider: OpenAI. Coordinator Astra (current-session exception); worker Sol,
medium reasoning, compact fresh context. No additional child workers.
Base: `f6ca7f1c6e90aad896f5694a4493b13ff101e509`, branch
`codex/M2-01-movement`, isolated `.worktrees/m2-01-movement`.
Same work-session quota baseline3%, discretionary boundary13%, reserve20%;
checkpoint at least every10min and before expensive experiments. No purchases.

## Outcome and ownership

Implement actual C++20 autonomous movement from the single end1533 seed, using
only controller inputs and static content thereafter. All13 frozen player fields
must eventually agree over1534–2999 and the original two withheld scenarios.
Component probes using captured call arguments cannot satisfy this task.

Worker owns new `src/core/movement*`, necessary core/test CMake registration,
`tests/native/movement*`, new `tools/unirally_lab/native/prepare.py`, new authored
preparation tests, new `tests/manifests/native/*.case.json` descriptors, source
guide additions and this task's worker handoff. Shared main registry/STATE and
existing component implementations are coordinator-owned. Report a demonstrated
component defect with a minimal reproducer rather than silently changing it.

Read AGENTS/STATE/workflow, M2-01, R-0010, all R-0011 research, and the component
headers/handoffs. Motion research9b840a8 plus completed handoffc025318 is approved;
speed68fcdd9 is independently approved. Input/contact/sampling/progress approved
as recorded in M2-01A. Exact combined local component suite7ce2ba5 passed259/259;
final integration candidatef6ca7f1 is in final checks/CI. No gameplay acceptance.

## Interfaces and evidence

Use the semantic state inventory and exact ordering in R-0011-motion. Share one
ContactMotion/RiderContactState and SpeedModifiers per rider; no duplicate
velocity state or persisted register scratch dictionaries. Track phase, GO,
residues, timer, opponent AI/reward queue and SRAM-derived learned state. Preserve
source-derived integer semantics and reject unsupported domains explicitly.

Runner target: `build/<preset>/src/core/movement_runner`. CLI:
`movement_runner --seed <canonical.bin> --content-dir <dir> --inputs <text>`.
Protocol and static filenames/sizes are in tasks/M2-01A-motion-handoff.md and
native/protocol.py. Emit initial row plus contiguous updates, magic
unirally-movement-v1, frame +13 decimal projections +canonical hex. Canonical
state begins URMV0001 and LEu32 frame; serialize explicit semantic fields only.

Prepare ignored local/native/dragster/runtime.json: schema1, rom_sha256,
seed{path,sha256,frame1533}, content_dir and complete files{name,size,sha256}.
Paths repository-relative; static directory contains ONLY the agreed12 files.
Validate original seed WRAM/SRAM identities and content provenance. Preparation
may use the original emulator; the native executable/comparison execution may
not. Preparation must have a documented reproducible command, bounded original
execution, and no silently assumed SRAM/seed values.

New primary.case.json uses schema_version1, kind native_movement_case and
replay/expected/runtime each {path,sha256}, binding existing frozen primary
replay/expected files and generated runtime metadata. Coordinator CLI command
candidate20d3816 implements this interface and is independently reviewed
separately; merge that branch only after coordinator supplies approval.

Existing ignored source artifacts can be read in .worktrees/m2-01a-motion,
m2-01a-contact, m2-01a-speed, m2-01 and m2-01-sampling-review. Each has its own
local fixture/cache paths. Reproduce a recorded baseline and verify identities;
do not copy build trees with absolute CMake paths. Bootstrap locally if needed.

## Work sequence and checks

First establish semantic seed serialization and one-frame ordering. Compare
primary initial/early rows to local frozen primary; record the first differing
field and original writer/order before correcting. Expand to all1466 updates.
No per-frame oracle, event schedule fitted to frame numbers, original CPU
interpreter, replayed scratch inputs or changed expected results are permitted.

Use focused authored arithmetic/state/protocol tests and debug/sanitizer builds.
Add complete state round-trip/determinism coverage. Record exact commands,
source/input hashes, attempted hypotheses and limitations. Inspect staged diff
before a task-scoped commit. Independent review is required before acceptance.

Keep both withheld expected series unopened during development. Submit a fixed
primary implementation first; coordinator/reviewer then runs withheld tests and
an independently chosen variation. If a new internal dependency appears, record
its smallest reproducer for coordinator scope amendment. No user choice is
needed for ordinary implementation/research decisions.

## Active first implementation session

Dispatch base3909c1c6519b96100d21e1e581c18c1f81fce827 includes reviewed command
758363c and combined components. Its worktree has the earlier ready work order;
this root claim is canonical. Worker owns a new tasks/M2-01-movement-handoff.md
in its branch in addition to the paths above. Parent remains owner of this
assignment record. First bounded checkpoint: semantic state/serialization and
validated single-seed preparation; then one native update if quota allows.
Do not attempt a full uncheckpointed rewrite. Current quota10% used; whole-run
boundary13% still applies. No recursive workers. Coordinator handles PR2 CI and
review integration while this independent implementation proceeds.
