# Project state

Updated: 10 September 2026.

## Current facts

- Target baseline: **PAL Unirally (European/Australian version)**. Identified in M0-01: headerless 2 MiB LoROM FastROM image, country code 0x02 (Europe), internal checksum verified, SHA-256 `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`. See [R-0001](research/R-0001-rom-identity.md). PAL timing and mapping under execution remain unverified.
- The ROM stays outside the repository; ignored `local/rom-location.txt` holds its path and `python3 tools/project.py rom inspect --expect tests/manifests/rom/unirally-pal.json` verifies a copy.
- `tools/project.py` implements `rom inspect`, `doctor`, `bootstrap`, `build --preset` and `test --suite synthetic` with JSON reports (schema 1) and exit codes 0/1/2/3/4 for success, failure, missing prerequisite, invalid input and timeout.
- Pinned CMake 3.31.10 and Ninja 1.13.2 are fetched as digest-verified wheel archives into ignored `local/toolchain/`; bootstrap is idempotent. No dependency is installed globally.
- `src/lab/` is a synthetic C++20 determinism probe, not game code. Its 1000-step state hash `0be347c529fadda9` is identical on macOS arm64 (AppleClang, Homebrew clang, with sanitizers) and Linux x86_64 (GCC 13.3, with sanitizers).
- ROM-free CI (`.github/workflows/synthetic.yml`) runs on `ubuntu-24.04` and `macos-15` for pushes to `main` and `task/**`; both are green at the M0-02 candidate. No private-fixture runner exists.
- Remote: private `git@github.com:malmazuke/UnirallyDecompilation.git`. No emulator adapter, recovered code, scheduler or reference capture exists yet.
- An unused worktree `.worktrees/native` on branch `task/M0-02-native` (at `7ce358e`, no commits) remains; the user can remove it.

## Scope

Long term: portable game, online multiplayer, custom maps, map creation and high-resolution texture imports.

First implementation milestone: M0 repeatable laboratory. First gameplay feasibility gate: M2 native sequence matching. First playable deliverable: M3 one native track.

## Decisions and proposals

| Item | Status |
| --- | --- |
| PAL baseline | Identified (M0-01); execution behaviour to be confirmed in M0-03 |
| Model-independent repository state and task handoffs | Core process requirement; exercised by two independent review sessions in M0-01/M0-02 |
| Differential validation against the original | Core accuracy strategy |
| C++20/CMake/Python/SDL3 | C++20, CMake presets and Python tooling validated by M0-02 on macOS and Linux; SDL3 not yet exercised |
| Primary reference emulator and pinned revision | Open; decide through M0-03 |
| macOS development and Linux validation first | In effect via CI |
| Original behavior plus separately versioned extensions | Proposed architecture |
| Two-player first online prototype | Planning default, later product decision |

## Next work

M0-03 (reference adapter spike) is ready once M0-02 is integrated: evaluate a pinned bsnes core and Mesen Community Edition for headless load, deterministic reset, bounded input delivery, capture and restore, then pin one. M0-04 (replay manifest and comparator) follows. See [the task registry](../tasks/README.md).

Implementation choices should be made through bounded experiments. Remote hosting beyond the private repository, release license/distribution arrangements, online service topology, public accounts/ranking and paid execution budgets remain undecided and do not block M0.

## Milestone status

M0: M0-00 and M0-01 accepted; M0-02 in review (see registry for the current state). M1–M6: not started. No game accuracy claims or calendar/cost estimate have been established.

## Handoff

The next agent should read this file, `AGENTS.md`, and the selected task. Reproduce a recorded check first: `python3 tools/project.py doctor && python3 tools/project.py bootstrap && python3 tools/project.py build --preset lab-debug && python3 tools/project.py test --suite synthetic`. Preserve the PAL choice. Update this summary only with observed results and decisions; leave execution details in task records.
