# Working on this project

Read `docs/STATE.md`, the relevant task record, and `docs/AGENT_WORKFLOW.md` before implementation. Consult `docs/PROJECT_PLAN.md` for scope and `docs/BUILD_AND_VALIDATION.md` for acceptance evidence.

- This is currently a planning repository. Build commands, test runners and scheduling described in the documents are proposed interfaces until implemented and recorded as such.
- Keep verified observations, hypotheses and implementation decisions distinct. Support gameplay claims with a ROM identity, addresses or traces, a reproducible experiment and the precise tested domain.
- Preserve original integer arithmetic, ordering and timing when reconstructing behavior. Do not replace unknown mechanics with plausible inventions while describing the result as accurate.
- Work only within the assigned task and ownership boundaries. For concurrent work, each worker uses a separate checkout/worktree; the coordinator owns the shared task registry and integration branch.
- Update the handoff with the actual commit, commands, results, unresolved issues and next experiment. A fresh agent must be able to resume without the previous conversation.
- Treat missing prerequisites and skipped tests as such; never report them as passes. Do not weaken or regenerate expected results merely to make a change pass.
- Keep ROMs, extracted game content, save states, credentials and large generated traces out of tracked files. Inspect the staged diff before committing.
- Local tests, reversible fixes and task-scoped commits may proceed within the user's authorization. This document does not grant authority to spend money, publish, deploy or send messages to other people.

Model-specific entry files should point to this document rather than duplicate project policy. Do not introduce model-specific dependencies into the game or evidence formats.
