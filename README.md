# Unirally reconstruction and modern port

Status: M0 laboratory in progress, 10 September 2026. The selected PAL ROM has been identified (see `docs/research/R-0001-rom-identity.md`) and a reproducible toolchain, synthetic native build and structured test reports exist. No game code has been recovered and no agent scheduler exists.

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

## Immediate next step

Execute the M0 environment and reproducibility milestone in the backlog. It must establish a repeatable build, a known ROM identity, deterministic emulator playback, and a resumable agent task before broad decompilation begins.

The implementation defaults are proposals: C++20 for the simulation, CMake for builds, Python for research tooling and SDL3 for the desktop shell. M0 should validate these choices on this machine and a Linux runner before locking versions. Commands marked implemented in [build and validation](docs/BUILD_AND_VALIDATION.md) exist; the rest remain proposals until a task record demonstrates them. Quick start: `python3 tools/project.py doctor`, then `bootstrap`, `build --preset lab-debug` and `test --suite synthetic`.

Original binary inputs, extracted assets and emulator snapshots belong in ignored local storage. Version the extraction procedures, manifests and provenance needed to regenerate them. Use synthetic fixtures for tests that should run without a ROM.
