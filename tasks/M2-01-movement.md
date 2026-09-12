# M2-01 movement implementation — semantic autonomous update

Status: independently approved at `245765d`; coordinator integration in progress.
Provider: OpenAI. Implementation and review used Sol/medium under D-0004. No
additional child workers.
Base: `f6ca7f1c6e90aad896f5694a4493b13ff101e509`, branch
`codex/M2-01-movement`, isolated `.worktrees/m2-01-movement`.
The user explicitly lifted the session percentage ceiling on 12 September 2026;
the OpenAI provider, checkpoint, no-purchase and no-credit rules remain unchanged.

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

## 12 September 2026 continuation checkpoint

The independently audited 297-byte seed and static-content boundary now drive a
semantic two-rider update. Two fresh processes agree and all 13 required fields
match for primary frames 1534–2999. The first formal withheld executions were
made only after that primary pass: cadence-17 also matches through 2999;
release-2347 matches through 2787, then differs at 2788 only in displacement
(native 0, original 3). A prior broad `rg` accidentally displayed isolated
withheld JSON lines; it did not drive an implementation change, but the process
deviation is recorded and prevents claiming perfectly sealed coordinator
independence.

Focused original access captures identify release coasting damping at
`$82:A5FA–A61E`: on the active phase a nonzero flat-surface velocity with
magnitude below 64 moves one unit toward zero before `$82:A8A7–A8C8` friction.
After speed reaches zero, the original enters the previously excluded idle-pose
machine, writing `$0F35/$0F37/$0F75/$0F77/$0F79/$0F7B/$0F7D/$0F7F`; its pose
feedback changes y/contact and produces the required displacement 3 at 2788.
Those persistent fields and arithmetic are not yet in canonical state. The next
bounded prerequisite is to recover `$82:A0B7–A237`, add only its future-affecting
semantic state, and rerun release-2347 before exact-candidate review.

## 12 September 2026 idle-pose closure

The bounded source review recovered `$82:A0B7-$82:A236` and the preceding
`$81:8625-$81:8672` damping path. The semantic state now contains nine
future-affecting words per rider, all imported from established persistent
addresses. The canonical seed is333 bytes, SHA-256
`7cd034fcdee04e8f306712707c01c05ae02a50f2e91668127a7c3ef64492b4ab`.
The runtime adds the identity-bound64-byte signed table from ROM file offset
`0x1B4`; runtime metadata SHA-256 is
`a38d58f2295c5be0569e83b4d77d995eceb031b5ff93118123af06002ab637da`.

Release-2347 now passes all13 fields for every update through2999, as do the
unchanged primary and cadence-17 cases; every command uses two fresh processes
and the canonical states are byte-identical. Reports are
`idle-release-4/report.json`, `idle-primary-final/report.json`, and
`idle-cadence-final/report.json` under ignored `artifacts/m2-01-movement/`.
The ROM-free synthetic suite passes273/273 and sanitizer movement tests pass2/2.

## Exact-candidate review

Independent review initially blocked `17e13cf`: zero velocity at references9–31
and32–57 incorrectly remained zero instead of being forced to−1 and+1 by
`$82:A201–A20C`. Candidate `245765d` corrects both branches and adds the
reviewer-owned boundary cases. The same reviewer then approved that exact clean
commit from a separate checkout after passing273/273 synthetic checks, debug
and sanitizer movement CTests2/2, preparation tests3/3, and all1,466 frames of
primary, cadence-17 and release-2347 with deterministic fresh processes. Frozen
expectations and manifests were unchanged. Reviewer reports remain ignored under
the review checkout's `artifacts/m2-final-review-*` paths; portable commands,
input identities and results are also recorded in the worker handoff.
