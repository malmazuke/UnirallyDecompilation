# Unirally reconstruction and modern port

Status: M0 and M1 accepted; M2 native movement implementation underway, 12 September 2026. Reviewed native components exist, but autonomous gameplay equivalence is not yet established. See [project state](docs/STATE.md) for current evidence and the usage-interruption checkpoint. No agent scheduler exists.

The long-term goal is an editable, portable Unirally with online multiplayer, custom tracks, a track editor and high-resolution asset replacements. The first goal is much smaller: reproduce a short sequence of original gameplay in native code, with automated evidence that its state matches the original.

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
sets Sol as the routine model, bounded frontier review and usage guardrails.

## Immediate next step

Resume M2 from [the usage checkpoint](tasks/M2-01-usage-checkpoint.md), finish
pending review, then assemble and validate the autonomous native sequence.

C++20, CMake and Python tooling are established; SDL3 remains unexercised. Commands marked implemented in [build and validation](docs/BUILD_AND_VALIDATION.md) exist; the rest remain proposals until a task record demonstrates them. Quick start: `python3 tools/project.py doctor`, then `bootstrap`, `build --preset lab-debug` and `test --suite synthetic`.

Original binary inputs, extracted assets and emulator snapshots belong in ignored local storage. Version the extraction procedures, manifests and provenance needed to regenerate them. Use synthetic fixtures for tests that should run without a ROM.
