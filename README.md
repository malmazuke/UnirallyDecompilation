# Unirally reconstruction and modern port

Status: milestones M0 through M3 are accepted as of 13 September 2026; annotated
tag `m3` identifies the accepted playable-slice state. The native app supports
the identified PAL one-player CRAWLER/DRAGSTER path from race start through a
stable result, using a validated local Classic pack and no original CPU
execution. M4 original-game coverage has accepted the DRAGSTER loser result and
a bounded ZOOM ZOO reference chain through position, sampling, contact,
response-B and vertical-velocity recurrence; this is research evidence, not a
second playable track. M4-12 has since accepted 200 experimental native updates
for both riders with zero later captured runtime inputs. M4-13 is prepared for
player support loss, landing and recovery; implementation has not started. See
[project state](docs/STATE.md) for the exact accepted boundary and
[the compact handoff](tasks/NEXT_SESSION.md) for current work. No agent
scheduler exists.

The long-term goal is an editable, portable Unirally with online multiplayer,
custom tracks, a track editor and high-resolution asset replacements. The first
playable investment gate is complete: one bounded original track is reproduced
in native code with automated state, continuation, presentation and desktop
checks. This is not yet full-game coverage.

Progress belongs in source control and reproducible experiments, so work can move between models, people and agent runtimes without depending on a particular chat history.

## Read first

| Document | Purpose |
| --- | --- |
| [Project plan](docs/PROJECT_PLAN.md) | Scope, architecture, milestones and criteria for advancing |
| [Build and validation](docs/BUILD_AND_VALIDATION.md) | Reference emulator, reproducible tooling, test evidence and implemented/proposed command inventory |
| [Agent workflow](docs/AGENT_WORKFLOW.md) | Task ownership, unattended work, model handoffs, review and integration |
| [Project state](docs/STATE.md) | Current facts, decisions, blockers and next actions |
| [Next session](tasks/NEXT_SESSION.md) | Astra/medium trial startup, scope and automatic review |
| [Reassessment handover](docs/REASSESSMENT_HANDOVER.md) | Historical stopping boundary after M4-11 and remaining unknowns |
| [Initial backlog](tasks/README.md) | The first implementation tasks and their dependencies |
| [Track investigation starts here](tasks/M4-02.md) | Bounded second-track discovery; continue with [the content/read contract](tasks/M4-03.md) rather than assuming a universal track format |
| [Task template](tasks/TEMPLATE.md) | A portable work order and handoff record |
| [Evidence template](docs/templates/EVIDENCE.md) | How to record a reverse-engineering finding |
| [Decision template](docs/templates/DECISION.md) | How to preserve an architectural decision |

Human-readable native source is an explicit goal from the first routine
([D-0003](docs/decisions/D-0003-human-readable-native-code.md)). Agents make
routine project decisions autonomously. [D-0004](docs/decisions/D-0004-model-and-usage-budget.md)
sets Sol as the routine OpenAI model and defines task-specific M4-12/M4-13 Astra/medium trial
exceptions, automatic Sol review and usage reserve.
[D-0006](docs/decisions/D-0006-capability-driven-work.md) defines capability-sized
tasks and staged validation.
Tasks stay within their starting provider; platform switches belong to the user.

## Current playable boundary

The accepted Classic profile exact-gates the supported PAL ROM, creates an
ignored 25-entry content pack, and later launches from that pack with the ROM
absent. The SDL3 frontend supplies a bounded 50 Hz PAL scheduler, keyboard and
gamepad mapping, integer-scaled presentation, and a declared rider-art fallback.
Audio is not implemented. Other tracks, riders/opponents, modes, local
multiplayer, menus/progression and public packaging are not accepted native
features; menu labels seen in reference captures are not implementation claims.

## Current work

Fast-moving status and next-work guidance live in
[project state](docs/STATE.md) and [the compact handoff](tasks/NEXT_SESSION.md).
Completed task records remain the durable evidence trail; do not infer native
support from a reference-research task.

C++20, CMake, Python and checksum-pinned SDL3 tooling are established. Commands
marked implemented in [build and validation](docs/BUILD_AND_VALIDATION.md)
exist; the rest remain proposals until a task record demonstrates them. For the
ROM-free baseline run `python3 tools/project.py doctor`, then `bootstrap`,
`build --preset app-debug` and `test --suite synthetic --preset app-debug`.

Original binary inputs, extracted assets and emulator snapshots belong in ignored local storage. Version the extraction procedures, manifests and provenance needed to regenerate them. Use synthetic fixtures for tests that should run without a ROM.
