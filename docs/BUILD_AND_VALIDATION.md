# Build, reference execution and validation

This is the M0 implementation specification. The interfaces below do not exist yet.

## Environment and dependencies

Start on the current macOS machine with Linux as the first additional build/test target. Windows is a later release target, unless the user prioritizes it earlier. Test natively on the relevant architecture; cross-compilation alone is not evidence of runtime determinism.

Pin compiler/tool versions, emulator commit and patches, Python dependencies and frontend dependencies in tracked manifests. Keep machine-local paths in ignored configuration. Bootstrap must be idempotent, bounded by timeouts, detect unsupported prerequisites, and avoid modifying global settings merely to get a green run. Store fetched dependencies in a dedicated cache and record their origin/checksum.

Use a headless build with no window/audio requirement for core checks. Containerized Linux is useful for repeatability, but a container must not be a prerequisite for the native macOS tools. Cache downloads/builds; do not redownload or rebuild everything for every agent. Verify the clean-setup path in an isolated environment before describing it as reproducible.

### Reference emulator selection spike

Evaluate a pinned bsnes core for programmatic execution and Mesen Community Edition for investigation. Do not assume either offers every needed headless API out of the box. Prove:

1. Load the supplied ROM and identify its exact bytes.
2. Set deterministic initial persistent memory and reset conditions.
3. Deliver inputs at a defined point and advance a bounded number of updates.
4. Capture memory, relevant registers and trace data without human clicks.
5. Save/restore and repeat the same experiment in fresh processes.
6. Exit with useful status and artifacts on timeout, crash or mismatch.

Select one primary adapter based on this spike. A second emulator is useful to investigate suspected reference errors, not a mandatory full matrix for every change. Interactive debugging can support exploration; automated acceptance must run without an unattended agent steering a GUI.

## Proposed repository shape

| Path | Contents |
| --- | --- |
| `src/core/` | Native simulation with no UI or network dependency |
| `src/app/` | Desktop input/render/audio integration |
| `tools/` | Bootstrap, ROM inspection, extraction, reference adapter and comparison tools |
| `tests/synthetic/` | Authored fixtures and checks runnable without game data |
| `tests/manifests/` | Replay identities, schema, provenance and regeneration instructions |
| `docs/research/` | Validated findings and linked experiments |
| `docs/decisions/` | Architectural decisions and superseded alternatives |
| `tasks/` | Work orders and durable handoffs |
| `local/` | Ignored ROMs, extracted assets, persistent data, private test fixtures and runner state |
| `artifacts/<run-id>/` | Ignored logs, snapshots, traces, reports and visual diffs |

Only planning files currently exist. Add directories when there is an implementation to put in them.

## Stable command contract

Implement a thin repository CLI, tentatively `python3 tools/project.py`, so any model/runtime uses the same entry points. The wrapper should invoke standard tools instead of reimplementing a build system.

| Proposed subcommand | Contract |
| --- | --- |
| `doctor` | Report installed/pinned versions, platform and missing capabilities; no game inputs required |
| `bootstrap` | Prepare isolated dependencies; safe to repeat; emit resolved-version manifest |
| `rom inspect --path <path>` | Hash original input, identify header/mapping/region candidates and emit manifest; do not silently normalize bytes |
| `build --preset <name>` | Configure/build the specified CMake preset and record exact configuration |
| `test --suite synthetic` | Run ROM-free checks and produce machine-readable results |
| `reference capture --case <manifest>` | Reproduce the original run and save identified reference artifacts |
| `compare --case <manifest>` | Run native/reference comparison and emit the first divergence and field summary |
| `verify --task <id>` | Run that task's declared checks, validate required artifacts and report eligibility for review |
| `package --preset <name>` | Later: assemble a runnable build with dependency notices and no unintended local inputs |

All commands must have bounded execution, useful help, noninteractive operation and a `--report <path>` option. Define exit codes for success, failure, missing prerequisites and invalid input. Reports include individual passed/failed/skipped checks. A required skipped check prevents task acceptance even if unrelated checks pass. A bare zero exit status must never conceal missing ROM tests.

Use an agreed JSON report schema containing run ID, task ID, source commit, dirty-diff digest if applicable, tool versions, input hashes, command, elapsed time, check outcomes and artifact hashes/locations. A check result applies only to the exact recorded source/input state.

## ROM and replay identity

The selected region is PAL Unirally. Choose its exact ROM revision before baseline capture. Record SHA-256 and file size, region, mapping and any header handling; retain original and normalized hashes separately if normalization is necessary. Do not infer region solely from the filename or hard-code NTSC timing. Persistent data, configuration and emulator version are part of the experiment.

Each replay manifest records:

- Scenario ID and tested behavior; ROM/emulator identity and adapter schema.
- Initial reset procedure or snapshot hash, SRAM/configuration hashes and RNG state if known.
- Both controllers' inputs, sequence length, timing units and exact injection/sampling point.
- State-field schema, address mapping and signedness/scales; expected events.
- Canonical reference artifact hashes, regeneration command and storage location.
- Native rules/content versions, expected outcomes and any explicitly justified tolerance.

Save states are emulator-version-specific artifacts. Keep a cold-start input path as well, so a state can be regenerated after a tool migration. Large captures remain local/private and content-addressed. Track a compact manifest that lets another authorized host reproduce or obtain them. A missing fixture is a dependency, not a new expected result invented by the worker.

## Comparison and evidence

Compare normalized gameplay state, not whole-memory byte equality between unrelated implementations. Whole-memory snapshots can aid investigation, but native data layout will differ. M1 defines fields and sampling phase: position, velocity, track progress, rider/trick state, timers and race events as actually discovered.

Use exact comparison for discrete and fixed-point gameplay values. Express any tolerance by field, unit and reason before acceptance; don't enlarge it after a failing run without a reviewed explanation. Identify the first divergent update, prior state, inputs, field values and associated original trace window. Reduce failing recordings where useful.

The reference is also software: verify repeatability and confirm critical discoveries with a second experiment or independent inspection. When native and reference differ, do not assume the native implementation is always at fault.

Visual checks compare native-resolution frames using agreed layer/color conventions and separate display scaling. Audio checks need an explicitly aligned sample/capture method and a defined tolerance for backend differences; early milestones can declare audio out of scope. A screenshot match alone is not gameplay equivalence.

### Test progression

| Stage | Checks |
| --- | --- |
| M0 | Clean setup; repeated reference capture; deliberately changed input; comparator/report failure path; timeout and missing-prerequisite handling |
| M1–M2 | Evidence-linked arithmetic/decoding checks; primary and withheld replays; fresh-process repeatability; save/restore continuation |
| M3 | Whole-track replays; boundary inputs around jump/trick/landing; collision edge cases; controls and render capture; sustained bounded run |
| M4 | Coverage by track/mode/player count; AI/RNG seeds; progress persistence; audio; cross-platform replay and release smoke checks |
| M5 | Track import/export round-trip; malformed content and resource limits; texture replacement preserves state hashes; editor create-to-play workflow |
| M6 | Two-client state agreement; reorder/loss/jitter; rollback restoration; version/content mismatch; disconnect and recovery |

Reviewers own at least some withheld input cases. Their expected outputs come from the frozen reference, not the candidate implementation. Add meaningful regressions for discovered mechanics and bugs; avoid tests that merely restate the implementation.

## CI and release evidence

Separate public/ROM-free CI from trusted fixture runs. Public CI can compile and test authored fixtures. A trusted local/private runner uses the supplied ROM and reproduces the differential suite. Required private results must attach to the exact commit being accepted. Untrusted pull requests must not run automatically on a host containing private fixtures or credentials.

If no remote or CI host exists, use the same scripts locally and record their results. Do not describe hosted CI as running until it exists. Integration reruns affected checks on the actual merge candidate; milestones require the broader declared suite. Use sanitizers where supported to expose memory/undefined-behavior defects, alongside replay checks in the release configuration.

Before an unattended run is considered reliable, demonstrate restart after interruption, a failed check reported accurately, and a task resumed from its persisted record. Build success is necessary but cannot substitute for reference comparison.

## Sources and limits

Consulted 10 September 2026; these establish available building blocks, not feasibility of the unimplemented adapter:

- [snesrev/sm](https://github.com/snesrev/sm): its README describes side-by-side execution, frame comparison and mismatch snapshots. This is precedent for differential validation.
- [bsnes](https://github.com/bsnes-emu/bsnes): candidate reference emulator. The project still needs a pinned, tested automation interface.
- [Mesen Community Edition](https://github.com/nesdev-org/MesenCE): multi-system emulator including SNES, with desktop builds. The original [Mesen2 repository](https://github.com/SourMesen/Mesen2) is archived and directs users to this fork; verify APIs against the selected revision.
- [CMake presets](https://cmake.org/cmake/help/latest/manual/cmake-presets.7.html): shared configure/build/test configuration and separate local presets.
- [SDL3 documentation](https://wiki.libsdl.org/SDL3/FrontPage): candidate frontend foundation.
- [GGPO](https://github.com/pond3r/ggpo): rollback implementation to study during the networking spike. No SDK choice or integration is committed by this plan.
