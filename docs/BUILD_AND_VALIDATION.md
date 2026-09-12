# Build, reference execution and validation

This is the M0 implementation specification. Commands marked implemented in the stable-command table exist in `tools/project.py`; the separately listed research modules use `python3 -m`. Other commands remain proposals until a task record shows them running.

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

Directories are added when there is an implementation to put in them. Present after M0-02: `tools/`, `tests/tooling/` (Python checks for the tooling itself), `tests/synthetic/`, `tests/manifests/rom/`, `docs/research/`, `src/lab/` (a synthetic determinism probe used to validate the toolchain and reports; it is not game code), `.github/workflows/` (ROM-free CI) and `tools/locks/` (pinned tool artifacts). Added by M0-03: `tools/unirally_lab/reference/` and `tests/manifests/reference/` (reference scripts). Added by M0-04: `tools/unirally_lab/replay/`, `tools/unirally_lab/compare/` and `tests/manifests/replay/` (replay manifests); local-only states and their restore-check reports live under ignored `local/states/`. Added by M1-01: `tools/unirally_lab/coverage/` (trace drain, 65816 opcode table, LoROM mapping, map derivation) and `docs/map/` (tracked observed code maps and summaries per scenario). Added by M1-02: `tools/unirally_lab/access/` (65816 effective-address decoder, streaming access derivation, capture and query commands), `tests/manifests/fields/` (validated field declarations) and `docs/state/` (the player-state schema).

M2-01's blocked component checkpoint adds `src/core/` (collision-point
expansion, spatial sampling and progress recurrence), `tests/native/` (four
ROM-free authored C++ checks plus two ROM-dependent probe executables),
`tools/unirally_lab/native/` (reference-freeze utility and isolated component
probes), and `tests/manifests/native/` (frozen reference projections and static
content provenance). These components do not implement a rider update or a
complete simulation. See [R-0010](research/R-0010-native-movement.md) and the
[source guide](../src/core/README.md) for exact units and supported bounds.

## Stable command contract

Implement a thin repository CLI, tentatively `python3 tools/project.py`, so any model/runtime uses the same entry points. The wrapper should invoke standard tools instead of reimplementing a build system.

| Subcommand | Status | Contract |
| --- | --- | --- |
| `doctor` | implemented (M0-02) | Report installed/pinned versions, platform and missing capabilities; no game inputs required |
| `bootstrap` | implemented (M0-02) | Prepare isolated dependencies from `tools/locks/toolchain.json`; safe to repeat; emit resolved-version manifest under ignored `local/toolchain/` |
| `rom inspect --path <path>` | implemented (M0-01) | Hash original input, identify header/mapping/region candidates and emit manifest; do not silently normalize bytes; `--expect` rejects another revision |
| `build --preset <name>` | implemented (M0-02) | Configure/build the specified CMake preset with the isolated toolchain and record exact configuration in `build/<preset>/lab-build-info.json` |
| `test --suite synthetic` | implemented (M0-02) | Run ROM-free checks (Python tooling tests, ctest, fresh-process repeatability) and produce machine-readable results |
| `reference build|run|verify|restore-check` | implemented (M0-03) | Build the pinned core from `tools/locks/emulators.json`; run a reference script in a fresh worker process; repeat it in fresh processes; save, restore and compare the continuation (D-0001) |
| `replay validate|run|compare --manifest <manifest>` | implemented (M0-04) | Validate a replay manifest (schema 1, ROM-free); reproduce its reference run in a fresh process; compare fresh-process runs of one manifest (or two manifests) on the declared fields and emit the first divergence with prior sample, inputs, field values, a work RAM localization and trace windows. Supersedes the proposed `reference capture --case` / `compare --case` for the reference side; native/reference comparison is added when native code exists (M2) |
| `coverage capture --manifest <manifest> --out <dir> [--ring N] [--frame-image N ...]` | implemented (M1-01) | Run a replay manifest in a fresh worker process with the core's instruction trace ring drained once per frame (the pinned core and patch are unchanged); write `coverage.json` (per executed site: 24-bit pc, E/M/X mode, data bank, count, first frame; per consecutive site pair: count), the usual samples, optional PNG frame dumps, and check that the run's digests equal the manifest's, that no frame exceeded the ring, that the instruction totals agree and that the first instruction is the emulation reset vector target |
| `coverage map --coverage <file> --out <map> [--summary <md>] [--detail <json>] [--baseline <map>]` | implemented (M1-01) | Derive the tracked code map from a coverage file and the ROM at `local/rom-location.txt`: opcode/operand byte classification under the observed modes, LoROM offsets, executed ranges per bank, vectors with execution counts, entry points with edge kinds, static absolute/long references, sites outside ROM; with `--baseline`, what this scenario executes that another does not. Tracked outputs carry no ROM bytes; `--detail` writes the per-address (opcode-bearing) artifact under ignored `artifacts/` |
| `access capture --manifest <manifest> --out <dir> [--from-frame N] [--to-frame N] [--watch-address A ...] [--watch-pc P ...] [--wram-series-range START LENGTH [--wram-series-every N]] [--frame-image N ...]` | implemented (M1-02) | Run a replay manifest in a fresh worker process and derive, from the unchanged trace ring and the ROM bytes at each pc, every instruction's memory accesses over the frame window (D-0002): effective address, kind (read, write, rmw, push, pull, block_read, block_write), width, stored value; aggregated per (pc, mode, addressing, kind, width, address) for work RAM and registers and per (pc, mode, addressing, kind) with an address range for ROM reads; indirect pointers and work RAM code resolved from recorded stores or the frame's work RAM images and labelled, the residual counted per (pc, addressing); per-frame value logs of watched addresses, register logs at watched pcs, a DMA/HDMA parameter log, an optional binary work RAM series (every frame of the run on the stride); `access.json` (schema 1) and the usual samples; checks that the run's digests equal the manifest's, that no frame exceeded the ring and that the instruction totals agree |
| `access query --access <dir>/access.json (--address A | --pc P) [--kind K] [--json]` | implemented (M1-02) | List the access records covering an address (work RAM mirrors match, multi-byte spans included) and/or made by a pc, with the writer and reader pcs; exit 1 when nothing matches, 2 without the file, 3 for bad arguments |
| `content provenance --access <dir>/access.json --out <dir> [--from-frame N] [--to-frame N]` | implemented (M1-03) | From an access record: every MDMAEN store expanded per enabled channel (frame, sequence, pc, direction, transfer mode, B-bus register, A-bus bank/address and region, size, ROM file offset) paired with the VRAM/CGRAM/OAM address in effect when the record watched `$2115`-`$2117`, `$2121`, `$2102`/`$2103`; every block move through `$00:0199` from its watched register log (grouped by the count register: source/destination offsets, length, destination bank, source banks or the ROM range); the VRAM and CGRAM bytes written through the data ports when `$2118`/`$2119`/`$2122` were watched; `provenance.json` (schema 1); checks that the MDMAEN count equals the record's `dma_triggers` and (optional) that every pairable transfer was paired |
| `content decode --manifest <manifest> --out <dir> [--rom P] [--wram-dump P]` | implemented (M1-03) | Decode every item of a content manifest (schema 1: `raw` pieces by file offset and length, or `rnc` by source bank/address through the port of the ROM's `$81:B8E2` decompressor) from the ROM, write the bytes to the ignored output directory, and check length and SHA-256 against the manifest; with a work RAM dump, compare items that carry `runtime.work_ram_offset` byte for byte, tolerating only the listed `known_runtime_writes`; exit 1 on a mismatch, 2 without ROM/manifest/dump, 3 for an invalid manifest |
| `content compare --manifest <manifest> --access <access.json> [--access <more>] --frame N --frame-image <png> --oam-dump <wram.bin> --scroll-dump <wram.bin> --out <dir> [--rect X Y W H] [--upload-frame N] [--bg1-scroll H V] [--bg2-scroll H V] [--colour-order bgr|rgb] [--max-mismatch-fraction F]` | implemented (M1-03) | Rebuild VRAM, CGRAM and OAM as the original had them at frame N (decoded items at their VRAM/CGRAM positions; ROM-to-VRAM DMAs and the tilemap staging DMAs of the record replayed with the previous frame's work RAM series; CGRAM/OAM port writes from the watch logs; scroll from the HDMA tables in the dump), render BG1, BG2 and sprites with the core's colour conversion, and compare pixel for pixel with the frame image over the rectangle; writes the render, the diff and a side-by-side PNG; reports the mismatch count and the omitted PPU features; fails only when `--max-mismatch-fraction` is exceeded |
| `native compare --manifest <native case> [--from-frame N] [--to-frame N]` | command implemented/reviewed (PR3); movement runner and prepared runtime still required | Build and run two fresh native processes, validate identity-bound seed/content/reference, complete rows and canonical-state determinism, and report first field divergence. Requires fresh artifacts directory; missing runner/runtime exits2. Command tests use authored producer stubs, not gameplay evidence |
| `verify --task <id>` | proposed | Run that task's declared checks, validate required artifacts and report eligibility for review |
| `package --preset <name>` | proposed | Later: assemble a runnable build with dependency notices and no unintended local inputs |

All commands must have bounded execution, useful help, noninteractive operation and a `--report <path>` option. Exit codes as implemented: 0 success, 1 check failure, 2 missing prerequisite, 3 invalid input, 4 timeout. Reports include individual passed/failed/skipped checks. A required skipped check prevents task acceptance even if unrelated checks pass. A bare zero exit status must never conceal missing ROM tests.

Use an agreed JSON report schema containing run ID, task ID, source commit, dirty-diff digest if applicable, tool versions, input hashes, command, elapsed time, check outcomes and artifact hashes/locations. A check result applies only to the exact recorded source/input state. The schema is implemented in `tools/unirally_lab/report.py` (schema version 1): each check has an outcome of `passed`, `failed`, `skipped`, `missing` or `timeout` and a `required` flag; a run's `status` is `passed` only when every required check passed.

## Isolated native research modules (M2-01 component checkpoint)

These are invoked with `python3 -m tools.unirally_lab.native.<module>`, outside
the stable CLI. They do not provide `tools/project.py native compare`.

| Module | Implemented contract and limits |
| --- | --- |
| `freeze_reference --manifest <replay> --samples <first> <second> --out <new file>` | Administrative reference-only projection of two matching fresh-process captures; refuses overwriting an existing output. Dedicated freeze commit precedes native computation. This utility emits a projection rather than a standard check report; it does not validate a native result |
| `probe_sampling --access <capture> --content-manifest <manifest> --content <dir> --probe <sampling_probe> --coarse-width 1024 --report <json>` | Identity-checks the primary capture/static content and compares ten sample words per call for both riders on frames 1534–2999. Incoming position/pose arguments come from the capture. Emits report and native stdout artifact; agreement validates only this component |
| `probe_progress --sampling-output <native.txt> --sampling-report <report> --series <wram.bin> --series-access <capture> --content-manifest <manifest> --content <table.bin> --probe <progress_probe> --report <json>` | Validates native sample-output identity and primary series provenance; seeds progress once at 1533 and compares marker/tag/count/rejection for both riders through 2999. Explicit phase and 15-byte state round-trip every frame. Samples still depend on captured positions/poses; this is not autonomous movement or M2-02 acceptance |

The two probes report execution/protocol failure as 1, missing files as 2,
invalid experiment input as 3, and timeout as 4. Their exact regeneration and
validation commands and artifact identities are in R-0010. Extracted tables
and original captures stay ignored; missing content is a prerequisite failure.
The existing `build --preset lab-debug` and `test --suite synthetic` commands
include the authored tests in `tests/native/` and Python tooling checks without
a ROM. `build --preset lab-sanitize` builds the same C++ component tests with
sanitizers. The latest clean-source local suite passed 211 checks; the sampler
checkpoint passed both CI platforms, while the final component candidate's CI
and independent review are recorded by the coordinator. Full gameplay gates
remain unrun, and component output hashes are not full movement-state hashes.

## ROM and replay identity

The selected region is PAL Unirally. Choose its exact ROM revision before baseline capture. Record SHA-256 and file size, region, mapping and any header handling; retain original and normalized hashes separately if normalization is necessary. Do not infer region solely from the filename or hard-code NTSC timing. Persistent data, configuration and emulator version are part of the experiment.

Each replay manifest records (implemented as `tests/manifests/replay/*.json`, schema 1, validated by `tools/unirally_lab/replay/manifest.py`; complete native replay execution remains proposed; M2-01 has reference projections and component-content manifests only):

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
