# Unirally reconstruction and modern port

Status: milestones M0 through M3 are accepted as of 13 September 2026; annotated
tag `m3` identifies the accepted playable-slice state. The native app supports
the identified PAL one-player CRAWLER/DRAGSTER path from race start through a
stable result, using a validated local Classic pack and no original CPU
execution. M4 original-game coverage is beginning with an evidence-backed
[feature inventory](tasks/M4-00.md). See [project state](docs/STATE.md) for the
exact evidence and limitations. No agent scheduler exists.

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
| [Build and validation](docs/BUILD_AND_VALIDATION.md) | Reference emulator, reproducible tooling, test evidence and proposed command interface |
| [Agent workflow](docs/AGENT_WORKFLOW.md) | Task ownership, unattended work, model handoffs, review and integration |
| [Project state](docs/STATE.md) | Current facts, decisions, blockers and next actions |
| [Initial backlog](tasks/README.md) | The first implementation tasks and their dependencies |
| [Task template](tasks/TEMPLATE.md) | A portable work order and handoff record |
| [Evidence template](docs/templates/EVIDENCE.md) | How to record a reverse-engineering finding |
| [Decision template](docs/templates/DECISION.md) | How to preserve an architectural decision |

Human-readable native source is an explicit goal from the first routine
([D-0003](docs/decisions/D-0003-human-readable-native-code.md)). Agents make
routine project decisions autonomously. [D-0004](docs/decisions/D-0004-model-and-usage-budget.md)
sets Sol as the routine OpenAI model, bounded frontier review and usage guardrails.
Tasks stay within their starting provider; platform switches belong to the user.

## Current playable boundary

The accepted Classic profile exact-gates the supported PAL ROM, creates an
ignored 25-entry content pack, and later launches from that pack with the ROM
absent. The SDL3 frontend supplies a bounded 50 Hz PAL scheduler, keyboard and
gamepad mapping, integer-scaled presentation, and a declared rider-art fallback.
Audio is not implemented. Other tracks, riders/opponents, modes, local
multiplayer, menus/progression and public packaging are not accepted native
features; menu labels seen in reference captures are not implementation claims.

## Immediate next step

Complete [M4-00](tasks/M4-00.md), then close the already evidenced
[DRAGSTER loser-result presentation gap](tasks/M4-01.md). The following
[second-track discovery](tasks/M4-02.md) attempts to hold PAL, one player, MIKE
and CRAWLER fixed, but must first observe whether opponent or event rules change
with the track. This sequencing closes a narrow native failure before widening
the reference domain.

C++20, CMake, Python and checksum-pinned SDL3 tooling are established. Commands
marked implemented in [build and validation](docs/BUILD_AND_VALIDATION.md)
exist; the rest remain proposals until a task record demonstrates them. For the
ROM-free baseline run `python3 tools/project.py doctor`, then `bootstrap`,
`build --preset app-debug` and `test --suite synthetic --preset app-debug`.

Original binary inputs, extracted assets and emulator snapshots belong in ignored local storage. Version the extraction procedures, manifests and provenance needed to regenerate them. Use synthetic fixtures for tests that should run without a ROM.
