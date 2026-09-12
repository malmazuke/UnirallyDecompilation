# Sol coordinator handover — start M2-02 native continuation

Prepared after M2-01 integrated through PR4 as `f33155e`. Reviewed gameplay
source is `245765d` plus the semantics-neutral portable index correction
`e8f2c69`; the exact documentation-complete PR head is `07049bb`. Start from the
current `main` head; do not restart M2-01 implementation.

## Operating instructions

Use OpenAI Sol with medium reasoning under D-0004. Keep one active child by
default and use a separate worktree for review. The user lifted the percentage
guardrail for the M2-01 completion session; that did not authorize purchases,
reset redemption, publication, or a provider switch. Re-establish any future
session limit from the user's current instruction rather than reviving the old
295-byte checkpoint's limit.

Read AGENTS.md, docs/STATE.md, docs/AGENT_WORKFLOW.md,
docs/BUILD_AND_VALIDATION.md, tasks/M2-01.md, and this file. Make ordinary task
and experiment choices autonomously. Original ROMs, extracted content, save
states and large traces remain ignored local inputs.

## M2-01 result — do not repeat

M2-01's autonomous native movement candidate uses a333-byte canonical semantic
state and13 identity-bound static content files. Seed SHA-256 is
`7cd034fcdee04e8f306712707c01c05ae02a50f2e91668127a7c3ef64492b4ab`;
runtime metadata SHA-256 is
`a38d58f2295c5be0569e83b4d77d995eceb031b5ff93118123af06002ab637da`.
The runtime is regenerable with `tools/unirally_lab/native/prepare.py`; extracted
bytes are not tracked.

Primary, cadence-17 and release-2347 each match all13 required projections for
all1,466 updates from frames1534–2999. Each comparison uses two fresh native
processes and verifies identical canonical state. The ROM-free suite passes
273/273; debug and sanitizer movement CTests pass2/2. Independent review first
found a source-translation defect in the idle-pose zero crossing, then approved
its correction and two reviewer-owned boundary variations. A later GCC
`-Wsign-conversion` failure was corrected by indexing the same `<64` table with
`std::size_t`; independent review confirmed it is semantics-neutral and repeated
all movement evidence.

Coordinator merge candidate `7c952a5` passed the same local checks and all three
native comparisons. Exact PR head `e8f2c69` passed macOS15 and Ubuntu24.04 CI,
including Linux sanitizers, in runs34674325394 and34674327012. The earlier
run34674260023 is a retained failed experiment: GCC rejected an unsigned-to-span
index conversion. No gameplay expectation, manifest, seed or content changed.
Detailed failures, commands and report locations are in
tasks/M2-01-movement-handoff.md and tasks/M2-01.md.

## Next ready work

M2-02 owns native state restore and portability. Create or finalize its work
order from the M2 gate in docs/PROJECT_PLAN.md before dispatch. Its minimum
acceptance scope is:

- serialize at a documented frame, restore in a fresh native process, and prove
  that the continuation state hashes and required projections equal an
  uninterrupted run;
- exercise more than one restore boundary, including one near a future-affecting
  idle/contact/AI transition rather than only a quiescent frame;
- reproduce the same native replay and continuation evidence on macOS and Linux;
- audit the complete serialized-state inventory and reject malformed,
  incompatible, truncated and trailing-byte states;
- retain useful first-divergence reports, ROM-free authored checks, independent
  exact-candidate review and coordinator integration CI.

Start from accepted `main`, not the old movement worktree. Reuse the reviewed
`MovementState` serialization and runner protocol; do not add per-frame reference
state, an original CPU interpreter or hidden platform-dependent state. A format
revision must be explicit and must preserve or deliberately reject the M2-01
333-byte schema with a documented reason.

M2 is not accepted until M2-02 passes. Rendering, a playable frontend and
full-track coverage remain M3 work.
