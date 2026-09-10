# Project state

Updated: 10 September 2026.

## Current facts

- Planning documents, a task backlog, templates and ignore rules exist.
- Target baseline: **PAL Unirally (European/Australian version)**, selected by the user. Exact revision/hash and timing remain unverified.
- No ROM is present in this project directory and none has been inspected in this work.
- No recovered code, executable, emulator adapter, implemented command wrapper, CI, scheduler or test results exist yet.
- A local Git repository is initialized. The user supplied `git@github.com:malmazuke/UnirallyDecompilation.git`; it is private and was empty on inspection.
- No background run, model session, external publication or paid service has been started by this planning work.

## Scope

Long term: portable game, online multiplayer, custom maps, map creation and high-resolution texture imports.

First implementation milestone: M0 repeatable laboratory. First gameplay feasibility gate: M2 native sequence matching. First playable deliverable: M3 one native track.

## Decisions and proposals

| Item | Status |
| --- | --- |
| PAL baseline | User selected; exact ROM revision is an input to M0-01 |
| Model-independent repository state and task handoffs | Core process requirement |
| Differential validation against the original | Core accuracy strategy |
| C++20/CMake/Python/SDL3 | Proposed; validate through M0-02 and record a decision |
| Primary reference emulator and pinned revision | Open; decide through M0-03 |
| macOS development and Linux validation first | Planning default |
| Original behavior plus separately versioned extensions | Proposed architecture |
| Two-player first online prototype | Planning default, later product decision |

## Next work

The user authorized continuation. M0-00 and M0-02 are in progress; see [the task registry](../tasks/README.md). M0-01 needs the user's local PAL ROM path before capture-dependent tasks can finish. Toolchain setup proceeds independently.

Implementation choices should be made through bounded experiments. Remote hosting, release license/distribution arrangements, online service topology, public accounts/ranking, and paid execution budgets can be decided when they affect the next work assignment. They do not block writing or reviewing this plan.

## Milestone status

M0: in progress. M1–M6: not started. No game accuracy claims or calendar/cost estimate have been established.

## Handoff

The next agent should read this file, `AGENTS.md`, and the selected task. Treat all documented CLI commands as specifications until implemented. Preserve the PAL choice. Update this summary only with observed results and decisions; leave execution details in task records.
