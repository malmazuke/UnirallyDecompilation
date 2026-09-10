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
- Remote: private `git@github.com:malmazuke/UnirallyDecompilation.git`. No recovered code, comparator, scheduler or replay manifest exists yet.
- An unused worktree `.worktrees/native` on branch `task/M0-02-native` (at `7ce358e`, no commits) remains; the user can remove it.

## Scope

Long term: portable game, online multiplayer, custom maps, map creation and high-resolution texture imports.

First implementation milestone: M0 repeatable laboratory. First gameplay feasibility gate: M2 native sequence matching. First playable deliverable: M3 one native track.

## Decisions and proposals

| Item | Status |
| --- | --- |
| PAL baseline | Identified (M0-01); execution behaviour to be confirmed in M0-03 |
| Model-independent repository state and task handoffs | Core process requirement; exercised by independent review sessions in M0-01/M0-02 and five in M0-03 |
| Differential validation against the original | Core accuracy strategy |
| C++20/CMake/Python/SDL3 | C++20, CMake presets and Python tooling validated by M0-02 on macOS and Linux; SDL3 not yet exercised |
| Primary reference emulator and pinned revision | Decided in M0-03: bsnes `7d5aa1e656b9` with laboratory patch, `Strict` state synchronization ([D-0001](decisions/D-0001-reference-emulator.md)) |
| macOS development and Linux validation first | In effect via CI |
| Original behavior plus separately versioned extensions | Proposed architecture |
| Two-player first online prototype | Planning default, later product decision |

## Next work

M0-04 (replay manifest and comparator) is ready: version manifests over the M0-03 samples/script schemas, compare repeated reference runs, perturb a known active input (Start at frame 300) and emit a first-divergence report. See [the task registry](../tasks/README.md) and [M0-04](../tasks/M0-04.md).

Implementation choices should be made through bounded experiments. Remote hosting beyond the private repository, release license/distribution arrangements, online service topology, public accounts/ranking and paid execution budgets remain undecided and do not block M0. A Linux build of the pinned core (ROM-free) is a natural CI addition when convenient.

## Milestone status

M0: M0-00 through M0-03 accepted (see registry for the current state). M1–M6: not started. No game accuracy claims or calendar/cost estimate have been established.

## Handoff

The next agent should read this file, `AGENTS.md`, and the selected task. Reproduce a recorded check first: `python3 tools/project.py doctor && python3 tools/project.py bootstrap && python3 tools/project.py build --preset lab-debug && python3 tools/project.py test --suite synthetic`; with the ROM available also `python3 tools/project.py reference build && python3 tools/project.py reference verify --script tests/manifests/reference/boot-300.json`. Preserve the PAL choice. Update this summary only with observed results and decisions; leave execution details in task records.
