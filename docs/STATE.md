# Project state

Updated: 10 September 2026.

## Current facts

- Planning documents, a task backlog, templates and ignore rules exist.
- Target baseline: **PAL Unirally (European/Australian version)**, selected by the user. Exact revision/hash and timing remain unverified.
- The user supplied a local PAL ROM path, recorded in ignored `local/rom-location.txt`. The ROM has not been inspected or copied.
- No recovered code, executable, emulator adapter, implemented command wrapper, CI, scheduler or test results exist yet.
- A local Git repository is initialized. The user supplied `git@github.com:malmazuke/UnirallyDecompilation.git`; it is private and was empty on inspection.
- Planning baseline `7ce358e` was pushed to the private origin. An implementation worker was started and then interrupted at the user's request before it wrote files or ran a build. No agents or background builds are running.

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

**Paused by the user due to available credits. Do not start building or resume agents until the user asks to resume.** M0-00 repository setup is complete. M0-01 now has a supplied ROM path but has not begun. M0-02 has empty task branches/worktrees only; no implementation, dependency installation or build was performed. See [the task registry](../tasks/README.md).

Implementation choices should be made through bounded experiments. Remote hosting, release license/distribution arrangements, online service topology, public accounts/ranking, and paid execution budgets can be decided when they affect the next work assignment. They do not block writing or reviewing this plan.

## Milestone status

M0: paused after repository setup. M1–M6: not started. No game accuracy claims or calendar/cost estimate have been established.

## Handoff

The next agent should read this file, `AGENTS.md`, and the selected task. Treat all documented CLI commands as specifications until implemented. Preserve the PAL choice. Update this summary only with observed results and decisions; leave execution details in task records.
