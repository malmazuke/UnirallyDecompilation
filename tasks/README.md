# Initial backlog

The coordinator maintains the status registry below. Work orders further below define the planned outcomes. Individual task records carry execution details and handoffs.

| Task | Status | Record |
| --- | --- | --- |
| M0-00 | accepted | [Repository setup](M0-00.md) |
| M0-01 | planned: ROM path supplied; user paused execution | Not dispatched |
| M0-02 | planned: paused by user before implementation | [Laboratory bootstrap](M0-02.md) |
| M0-03 through M0-06 | planned | Waiting for prerequisites |
| M1–M6 | planned | See milestone definitions |

## M0 — repeatable laboratory

| ID | Outcome | Dependencies | Acceptance criteria |
| --- | --- | --- | --- |
| M0-00 | Local Git baseline and task records | None | Initialize `main` if absent; commit reviewed planning files; verify ignores; create scoped task records and coordinator registry; no remote required |
| M0-01 | PAL ROM identity manifest | Supplied local ROM path | Preserve original bytes; record SHA-256/size/header handling/region evidence; reject an unexpected revision; store manifest and local input arrangement |
| M0-02 | Reproducible native/tooling bootstrap | M0-00 | Implement `doctor`, `bootstrap`, build preset and report schema; synthetic executable/tests build on macOS and Linux; demonstrate clean setup and idempotent rerun; record dependency versions |
| M0-03 | Automated reference adapter spike | M0-00, M0-01 | Compare candidate integration effort; implement reset, bounded input delivery, capture and restore; repeat a cold-start run three times in fresh processes with identical sampled outputs; pin the chosen adapter/core |
| M0-04 | Replay manifest and comparator foundation | M0-02, M0-03 | Version manifests; compare repeated reference runs; deliberately perturb a known active input to produce a detectable difference; emit first-divergence report; fail clearly on missing inputs/timeout; state fields may initially be raw diagnostic ranges |
| M0-05 | Resumable execution and review pilot | M0-02, M0-04 | Fresh agent session reproduces a task baseline and completes a bounded follow-up from the handoff alone; exercise interrupted-run recovery and failed-test reporting; independent review then exact-candidate verification; record gaps before wider concurrency |
| M0-06 | M0 acceptance report | M0-00 through M0-05 | Evidence for every M0 gate; machine/tool identities and reproducible commands; missing checks explicitly block acceptance; update next-stage estimates from observed effort |

M0-02 and M0-03 can run independently once their prerequisites are met, with different owned paths and an agreed report contract. Don't force parallelism if one host or a shared toolchain makes it unreliable. M0-05 can use a second session of the same model; actual cross-provider portability is only demonstrated when a second provider/runtime reproduces the task.

The synthetic executable in M0-02 is infrastructure validation, not game progress. M0-04 proves comparison/reporting works, not that the native game matches anything yet. M0-05 does not need a custom scheduler; a coordinator and durable records suffice to test the process.

## M1–M3 — refine after the laboratory works

| ID | Outcome | Dependencies | Acceptance criteria |
| --- | --- | --- | --- |
| M1-01 | Observed code/data map for the selected scenario | M0 | Trace-driven map with processor-mode context, entry points and coverage limitations; unexecuted bytes remain unclassified |
| M1-02 | Validated player-state schema and update timing | M1-01 | Locate relevant writes; validate position/speed/trick/timer interpretations with controlled inputs; define the exact capture phase and PAL cadence |
| M1-03 | Minimal track/asset decode | M1-01 | Decode one representative segment and needed rider frames; compare against original runtime rendering/collision use; record compression/offset provenance |
| M2-01 | Native movement/trick experiment | M1-02, required M1-03 data | Freeze primary and withheld reference cases before tuning; exact gameplay-field agreement; explicit arithmetic and observed update order; useful mismatch reports |
| M2-02 | State restore and portability check | M2-01 | Fresh-process and restore/continue hashes agree; same native replay agrees on macOS and Linux; document full serialized-state inventory |
| M3-01 | One complete playable native track | M2, expanded track decode | Native gameplay, controls, minimal renderer and completion; whole-track comparisons plus real play; declared remaining visual/audio omissions |

For M2 withheld cases, include at least two variations not used to develop the routine: for example a different trick timing and a different landing/acceleration sequence, chosen after the game behavior is observed. Do not decide numeric tolerances by looking at candidate errors.

M4–M6 stay at milestone level in [the project plan](../docs/PROJECT_PLAN.md) until their prerequisites provide enough evidence to create useful work orders.
