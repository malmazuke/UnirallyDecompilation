# Project state

Updated: 11 September 2026.

## Current facts

- Target baseline: **PAL Unirally (European/Australian version)**. Identified in M0-01: headerless 2 MiB LoROM FastROM image, country code 0x02 (Europe), internal checksum verified, SHA-256 `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`. See [R-0001](research/R-0001-rom-identity.md). PAL timing and mapping under execution remain unverified.
- The ROM stays outside the repository; ignored `local/rom-location.txt` holds its path and `python3 tools/project.py rom inspect --expect tests/manifests/rom/unirally-pal.json` verifies a copy.
- `tools/project.py` implements `rom inspect`, `doctor`, `bootstrap`, `build --preset` and `test --suite synthetic` with JSON reports (schema 1) and exit codes 0/1/2/3/4 for success, failure, missing prerequisite, invalid input and timeout.
- Pinned CMake 3.31.10 and Ninja 1.13.2 are fetched as digest-verified wheel archives into ignored `local/toolchain/`; bootstrap is idempotent. No dependency is installed globally.
- `src/lab/` is a synthetic C++20 determinism probe, not game code. Its 1000-step state hash `0be347c529fadda9` is identical on macOS arm64 (AppleClang, Homebrew clang, with sanitizers) and Linux x86_64 (GCC 13.3, with sanitizers).
- ROM-free CI (`.github/workflows/synthetic.yml`) runs on `ubuntu-24.04` and `macos-15` for pushes to `main` and `task/**`; both are green at the M0-02 candidate. No private-fixture runner exists.
- Reference adapter (M0-03, [D-0001](decisions/D-0001-reference-emulator.md), [R-0002](research/R-0002-reference-adapter-determinism.md)): a pinned **bsnes** libretro core (commit `7d5aa1e656b9`, tracked patch `tools/unirally_lab/reference/patches/`) driven from Python in fresh worker processes; `python3 tools/project.py reference build|run|verify|restore-check`. On this ROM three fresh processes give identical per-frame work RAM, registers, video and audio (memory/register sample digest `f210eecacf63cbeb…` for `tests/manifests/reference/boot-300.json`); the core reports PAL; inputs are delivered per frame; a save/restore in a fresh process continues identically at every save point of both tracked scripts, while saving at boot-sequence points 29–96 (with holes) perturbs the run, which `restore-check` detects. Video/audio are not restorable. Mesen Community Edition is pinned as an investigation tool only.
- Replay manifests and comparator (M0-04, [R-0003](research/R-0003-replay-comparator.md)): `tests/manifests/replay/*.json` (manifest schema 1: scenario, ROM and core identity, cold-start or validated-state origin, both controllers' frame-timed inputs, declared fields, regeneration command, expected digests) drive `python3 tools/project.py replay validate|run|compare`. Every reference execution is a separate worker process (reference samples schema 2 adds declared work RAM ranges, a stop frame, a WRAM dump and process identity; the M0-03 sample digest is unchanged). On this ROM two fresh runs of `boot-start-600` are identical (sample digest `583d1ec544ec61a2…`); removing or moving the Start press at frames 300–305 is reported as a first divergence at frame 300 and localized to one work RAM byte, `$7E0073` (`0x10` held, `0x00` not), with identical final states; absent ROM/state/evidence exit 2, an unreachable manifest exits 4, invalid manifests exit 3. Two independent reviews with their own withheld perturbations agreed with manual frame-by-frame comparisons. A state is a valid origin only with its restore-check report at the same save point.
- The Python test runner now records failing subtests and `test --suite synthetic` fails when the runner does (a defect since M0-02 that let three erroring subtests read as 101/101 was found by the first M0-04 review). The suite has 117 checks, 109 Python tests.
- Resumable execution (M0-05, [R-0004](research/R-0004-resumable-execution.md)): a fresh session of a different model (Claude Opus 5 as a worker under the Fable 5.1 coordinator), given only the portable prompt and a worktree holding the repository and `local/rom-location.txt`, bootstrapped the toolchain, built the pinned core and reproduced every M0-04 digest, exit code and the divergence byte from the records alone; an independent reviewer then did the same from its own clone. `replay compare`'s post-run wiring (`fresh_processes`, the cold-start/restore `av_identical` rule, optional localization, the divergence report, worker outcome to exit code) is covered ROM-free by stubbed-worker tests that cannot load a core; eleven of twelve mutations tried by worker and reviewer were caught. A `SIGKILL`ed worker gives exit 1 with `fields_identical: skipped` and no samples file; a `SIGKILL`ed parent leaves no report while its worker survives about a second and writes samples into the dead run's directory; a re-run reproduces the recorded outcome. A deliberate failing test makes the suite exit 1 with each failing test named. Process gaps G1–G7 are recorded in R-0004.
- Concurrency decision (coordinator, from R-0004): two workers may run at the same time only on tasks with disjoint owned paths, each in its own worktree or clone, with the claim written into the task record and the registry row in the same commit (G1) and a check for live `reference/worker.py` processes, matched by the `--samples-out` path in their argv, before any stale task is reassigned (G2). No lease store exists (G4), so two workers are never dispatched from the same queue entry, and each attempt uses its own artifacts directory (G3).
- Remote: private `git@github.com:malmazuke/UnirallyDecompilation.git`. No recovered code or scheduler exists yet.
- An unused worktree `.worktrees/native` on branch `task/M0-02-native` (at `7ce358e`, no commits) remains; the user can remove it.

## Scope

Long term: portable game, online multiplayer, custom maps, map creation and high-resolution texture imports.

First implementation milestone: M0 repeatable laboratory. First gameplay feasibility gate: M2 native sequence matching. First playable deliverable: M3 one native track.

## Decisions and proposals

| Item | Status |
| --- | --- |
| PAL baseline | Identified (M0-01); execution behaviour to be confirmed in M0-03 |
| Model-independent repository state and task handoffs | Core process requirement; exercised by independent review sessions in M0-01/M0-02, five in M0-03, two in M0-04, and in M0-05 by a worker of a different model plus one review, all from the records alone |
| Differential validation against the original | Core accuracy strategy |
| C++20/CMake/Python/SDL3 | C++20, CMake presets and Python tooling validated by M0-02 on macOS and Linux; SDL3 not yet exercised |
| Primary reference emulator and pinned revision | Decided in M0-03: bsnes `7d5aa1e656b9` with laboratory patch, `Strict` state synchronization ([D-0001](decisions/D-0001-reference-emulator.md)) |
| macOS development and Linux validation first | In effect via CI |
| Original behavior plus separately versioned extensions | Proposed architecture |
| Two-player first online prototype | Planning default, later product decision |
| Two concurrent workers | Allowed under the M0-05 conditions above (disjoint paths, own worktree, claim in record and registry together, orphan check); a shared queue needs a lease store first |

## Next work

M0-06 (M0 acceptance report) is ready: gate-by-gate evidence for M0 with identities and reproducible commands, unmet gates blocking acceptance, next-stage estimates revised from the observed effort, and one small test follow-up from the M0-05 review (the `divergence_localized: failed` branch has no test). See [the task registry](../tasks/README.md) and [M0-06](../tasks/M0-06.md). Small non-blocking notes from M0-05: `divergence_localized` should say in its detail that without `--against` the re-runs cannot reproduce a divergence between repetitions (G6); the handoff template should carry a runtime-needs line (G5, added to M0-06's record).

Implementation choices should be made through bounded experiments. Remote hosting beyond the private repository, release license/distribution arrangements, online service topology, public accounts/ranking and paid execution budgets remain undecided and do not block M0. A Linux build of the pinned core (ROM-free) is a natural CI addition when convenient.

## Milestone status

M0: M0-00 through M0-05 accepted (see registry for the current state). M1–M6: not started. No game accuracy claims or calendar/cost estimate have been established.

## Handoff

The next agent should read this file, `AGENTS.md`, and the selected task. Reproduce a recorded check first: `python3 tools/project.py doctor && python3 tools/project.py bootstrap && python3 tools/project.py build --preset lab-debug && python3 tools/project.py test --suite synthetic` (117 checks); with the ROM available also `python3 tools/project.py reference build && python3 tools/project.py reference verify --script tests/manifests/reference/boot-300.json` and `python3 tools/project.py replay compare --manifest tests/manifests/replay/boot-start-600.json` (exit 0, sample digest `583d1ec544ec61a2…`). Preserve the PAL choice. Update this summary only with observed results and decisions; leave execution details in task records.
