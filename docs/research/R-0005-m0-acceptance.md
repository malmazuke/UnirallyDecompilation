# R-0005 — M0 acceptance: gate-by-gate evidence, re-run on the candidate commit

- Status: observed and independently reproduced (single host, 11 September 2026); CI on the candidate observed green after submission
- Related task/decision: [M0-06](../../tasks/M0-06.md); assembles [R-0001](R-0001-rom-identity.md), [R-0002](R-0002-reference-adapter-determinism.md), [R-0003](R-0003-replay-comparator.md), [R-0004](R-0004-resumable-execution.md) and [D-0001](../decisions/D-0001-reference-emulator.md)
- Tested domain and excluded cases: whether each M0 gate in [the project plan](../PROJECT_PLAN.md) and [build and validation](../BUILD_AND_VALIDATION.md) has an observation behind it, and whether the recorded checks still hold on this candidate. Nothing here is a gameplay claim, and nothing here is new laboratory behaviour: every mechanism was established in R-0001 to R-0004 and is re-observed. Excluded: Linux execution of the pinned core, Windows, the cycle-accurate PPU profile, concurrent workers, and every M1 question.
- ROM hash, emulator revision/configuration and adapter version: ROM SHA-256 `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e` (R-0001); bsnes `7d5aa1e656b9` with patch `a719f5ffe222…`, options `bsnes.DEFAULT_OPTIONS`, `Strict` synchronization, built library SHA-256 `a3803962890d…` on this host; reference script schema 1, samples schema 2, replay manifest schema 1, report schema 1.
- Machine and tool identity: macOS 15.7.2, arm64, Apple clang 17.0.0 (clang-1700.4.4.1), Python 3.14.3, git 2.50.1; isolated CMake 3.31.10 and Ninja 1.13.2 from `tools/locks/toolchain.json`; system ninja absent (the isolated toolchain is used). Linux evidence is GitHub-hosted `ubuntu-24.04` CI only, and is ROM-free.
- Addresses: work RAM offsets are offsets into the 131072-byte block (`$7E0000 + offset`); ROM offsets are file offsets.
- Input/reset/snapshot identity and hashes: the tracked manifests in `tests/manifests/replay/` and scripts in `tests/manifests/reference/`; cold start unless stated.
- Experiment source commit and exact command: worktree `.worktrees/m0-06` on `task/M0-06-acceptance-report`, candidate `abb8c60` (the M0-06 code change; the records that cite it follow it). Every command below is `python3 tools/project.py <args> --report artifacts/m0-06/final/<name>.json --task M0-06`, driven by the ignored `artifacts/m0-06/evidence.sh`; every one of those reports records commit `abb8c60` with `dirty` false (the failing-test report is the deliberate exception, see gate 8).
- Artifact location, hashes and regeneration procedure: ignored `artifacts/m0-06/final/` (reports, samples, derived scripts, work RAM dumps, divergence reports, worker logs) and the ignored drivers `artifacts/m0-06/evidence.sh`, `interrupt.py` and `mutation-probes.py`. Report SHA-256 prefixes are given per gate; regenerate with `bash artifacts/m0-06/evidence.sh` on a host holding the ROM.

## Observation

### The re-run on the candidate

Eighteen recorded checks were re-run once on `abb8c60`, plus the interruption and failing-test experiments. Every exit code and every digest matched the record it came from; nothing had to be adjusted.

| Command (abridged) | Report | Exit | Observed |
| --- | --- | --- | --- |
| `doctor` | `1226774e` | 0 | required capabilities present; `system_ninja` `missing` (optional, isolated toolchain used) |
| `bootstrap` (repeat) | `50921936` | 0 | both tools `source=cache` |
| `build --preset lab-debug` | `8f272257` | 0 | configure 0.2 s, build 0.6 s |
| `test --suite synthetic` | `610c5a44` | 0 | **118/118** checks, `110 tests run, 110 records, 0 failed; runner exit 0`; probe hash `0be347c529fadda9` in 3 fresh processes |
| `rom inspect --expect tests/manifests/rom/unirally-pal.json` | `5b7d3790` | 0 | 10/10 identity fields |
| `rom inspect --path /nonexistent.sfc` | `a4b047c4` | 2 | `rom_available: missing` |
| `reference build` (repeat) | `e00528cd` | 0 | `patch_applied` `a719f5ffe222`, incremental |
| `reference verify --script …/boot-300.json --runs 3` | `bb8c1ac9` | 0 | sample digest **`f210eecacf63cbeb…`** ×3, final state `df4fb430e731dfe1…`, A/V `edfa4f8e92b24dc0…`, core reports PAL |
| `reference restore-check --script …/boot-300-every-5.json --save-after 70` | `cbbc6271` | 1 | only the required `save_does_not_perturb` failed, first differing frame **71**; restore fidelity checks passed; `restore_av_identical` failed as informational |
| `replay validate --manifest …/boot-start-600.json` | `a5c7b1eb` | 0 | manifest, lock and ROM identity |
| `replay compare --manifest …/boot-start-600.json` | `6dd2ceb9` | 0 | **`583d1ec544ec61a2…`** in both runs, final state `1a6fbf6d24c532ff…`, 600 common frames, worker pids 16578/16592, comparator 16573 |
| `… --against …-start-removed.json` | `d4544275` | 1 | first divergence **frame 300** in `wram_sha256`, `wram_0000_0200`; prior sample 299; localized to **one** byte **`0x00073`** (`0x10`/`0x00`), 0 differing registers; identical final states |
| `… --against …-start-moved-310.json` | `fbb758f5` | 1 | same frame, same single byte |
| `replay run --manifest …/unreachable.json --timeout 3` | `34665668` | 4 | `reference_run: timeout`, 3.005 s |
| `replay compare --manifest …/unreachable.json --timeout 3` | `64494ce8` | 4 | `run1: timeout`, `fields_identical: skipped` |
| `replay run --manifest …-from-state-150.json` | `e984a5f7` | 2 | `run_origin_available: missing` (the state is not in this worktree) |
| `replay compare --manifest …/boot-start-600.json --rom /nonexistent.sfc` | `efbf7f3b` | 2 | `rom_available: missing` |
| `replay validate` on a truncated manifest | `4ddeb473` | 3 | `replay_manifest_valid: failed`, no traceback |
| `replay run` on a copy with a wrong `expected.sample_digest` | `89eb964e` | 1 | `run_sample_digest_matches_expected: failed` — observed `583d1ec544ec61a2…`, manifest `0000…` |

Interruption (ignored `artifacts/m0-06/interrupt.py`, which matches live workers by the `--samples-out` path in their argv as R-0004 G2 requires, so no other session's worker can be hit):

- Worker `SIGKILL`ed while it ran (report `8ba48aa5`): parent exit **1**, `run1: failed`, `fields_identical: skipped`, no `comparisons` and no `divergence` key, and **no samples file on disk**.
- The same command re-run into the same artifacts directory (report `ef174bb6`): exit **0**, `583d1ec544ec61a2…` in both of two fresh workers.

Failed-check reporting (report `64315af9`, produced in a scratch detached worktree at `abb8c60` that has since been removed and pruned): a file with a failing assertion, a failing subtest among two, an erroring test and a passing test makes `test --suite synthetic` exit **1** with 4 failed of 122 checks — each failing test named individually, the subtest carrying its parameters (`…test_a_subtest_failure_must_also_be_reported (n=2)`), the passing sibling still recorded as passing, `python_tooling_tests: 114 tests run, 114 records, 3 failed; runner exit 1`, and `source.dirty` true with the new file in `untracked_files`.

### Gate-by-gate evidence

Gates 1–5 are the M0 row of [the test progression](../BUILD_AND_VALIDATION.md); 6–8 are the unattended-operation preconditions in the same document; 9–12 are the M0 row of [the milestone table](../PROJECT_PLAN.md). "Re-run" means observed again on `abb8c60` today.

| # | Gate | Evidence | Verdict |
| --- | --- | --- | --- |
| 1 | Clean setup | M0-02: fresh `git clone` into scratch with no `local/` at `6b48da5` — `doctor`, `bootstrap` (downloaded), `bootstrap` again (cache only), `build`, `test` 44/44, `dirty` false; reviewer confirmed by timestamp search that nothing was written outside the clone. M0-03 and M0-04: five more clean clones built the pinned core from the lock. M0-05 and M0-06: a worktree holding only the repository and `local/rom-location.txt` bootstrapped the toolchain (2.2 s) and built the core (14.6 s) from the records. Re-run: `doctor`, `bootstrap` repeat, `build`, `reference build` repeat | **Met** |
| 2 | Repeated reference capture | R-0002 finding 1 and R-0003 finding 1. Re-run: three fresh worker processes of `boot-300` give `f210eecacf63cbeb…` and final state `df4fb430e731dfe1…`; two fresh workers of `boot-start-600` give `583d1ec544ec61a2…` and `1a6fbf6d24c532ff…` on 600 frames with distinct pids, none of them the comparator's; `--runs 3` recorded in R-0003 finding 1 and M0-05 attempt 6 | **Met** |
| 3 | Deliberately changed input | R-0003 findings 2–4. Re-run: removing and moving the Start press at frames 300–305 both give exit 1 with the first divergence at frame 300, the prior sample at 299, both sides' inputs at 299 and 300, and a localization to the single work RAM byte `0x00073` (`0x10` held, `0x00` not). Two independent reviewers with their own withheld perturbations (port 1, Start+A, Start+B+Y, `up`, Start+L+R, two-controller combinations, sparse sampling) agreed with manual frame-by-frame comparisons | **Met** |
| 4 | Comparator/report failure path | Re-run: an unreadable manifest exits 3 with no traceback; an absent ROM and an absent state exit 2 with `missing`; a wrong `expected.sample_digest` exits 1; an absent restore-check report exits 2 with `missing` (R-0003 finding 5, not in this re-run; reproduced by the M0-06 reviewer); a genuinely failing required check (`save_does_not_perturb` at save point 70) exits 1 and names the first differing frame. A run that cannot complete records `fields_identical: skipped`, never a pass. ROM-free: 40 invalid manifests rejected as `ManifestError`, and the stubbed-worker tests map every worker outcome to its exit code | **Met** |
| 5 | Timeout and missing-prerequisite handling | Re-run: `replay run` and `replay compare` on the unreachable manifest are killed after 3.0 s, recorded as `timeout`, exit 4; missing ROM and missing state exit 2. Distinctness of timeout, failure and missing prerequisite is asserted ROM-free (`test_toolchain.BoundedRunnerTests`, including that a timeout kills grandchildren) | **Met** |
| 6 | Restart after interruption | R-0004 finding 3 and M0-05 review 1. Re-run: a `SIGKILL`ed worker leaves exit 1, an explicit `run1: failed`, no samples file and no divergence key, and the re-run reproduces `583d1ec544ec61a2…`. Not re-run today but recorded twice (worker and reviewer): a `SIGKILL`ed parent writes no report at all, while its worker survives about a second and writes samples into the dead run's directory (**gap G2**), and an explicit `--artifacts` directory is never cleaned (**gap G3**) | **Met, with G2/G3 open** |
| 7 | A failed check reported accurately | Re-run: the deliberate failing-test file makes the suite exit 1 with 4 failed of 122 checks, each named. The defect this gate exists for was real and is fixed: until M0-04 review 1, three erroring subtests were reported as 101/101 passes, because the runner dropped subtest failures and `test` ignored the runner's exit status. It is now covered by tests in `test_native_reports.py` and re-demonstrated here | **Met** |
| 8 | A task resumed from its persisted record | Three independent instances. (a) M0-05: a fresh session of a *different model*, given only the portable prompt and a worktree with `local/rom-location.txt`, reproduced every M0-04 digest, exit code and the divergence byte from the records alone, then completed a scoped follow-up. (b) M0-05 review 1: a fresh session on its own clone did the same on the exact candidate. (c) This task: a fresh session reproduced the whole M0 evidence set from `AGENTS.md`, `docs/STATE.md` and the task records, with nothing copied but the ROM path. Not demonstrated: a different *provider or runtime* | **Met** |
| 9 | Clean build on local macOS and Linux | macOS: local, this host, re-run today. Linux: GitHub `ubuntu-24.04` only — no local Linux machine has been used. M0-02 CI run 34469566942 built and tested `lab-debug` and `lab-sanitize` there with the same probe hash `0be347c529fadda9` as macOS; every later candidate's CI run is green. The pinned reference core has **never** been built or run on Linux | **Met for the build and the synthetic suite; the reference side is macOS-only** |
| 10 | Synthetic checks | Re-run: 118/118 on this host at `abb8c60`, `source.dirty` false. At writing time CI had not run on the candidate and this gate was listed as outstanding. After submission: CI run 34561514855 on the branch head `eb82701` (code identical to `abb8c60`) green on `ubuntu-24.04` and `macos-15`, 118 checks, `110 tests run, 110 records, 0 failed; runner exit 0` on both (observed by the coordinator and the reviewer) | **Met** (closed by the CI run on the candidate) |
| 11 | Identical repeated reference playback | Same evidence as gate 2 | **Met** |
| 12 | Intentionally altered input detected | Same evidence as gate 3 | **Met** |

The reference-emulator spike's six numbered requirements in [build and validation](../BUILD_AND_VALIDATION.md) are each met by R-0002 and D-0001: load and identify the ROM bytes (the adapter reports the loaded SHA-256 and it equals the manifest); deterministic initial persistent memory and reset (entropy `None`, a private empty save directory per run, initial WRAM and cartridge-RAM digests folded into the sample digest); inputs at a defined point over a bounded number of updates (`input_polls` equals the frame count; Start at 300 first shows at frame 300); capture without human clicks (per-frame WRAM, a 26-byte register block, video, audio, declared ranges and a trace ring); save/restore repeated in fresh processes (exact at all 898 save points of both tracked scripts under `Strict`, with the perturbing points reported, not hidden); and useful status and artifacts on timeout, crash or mismatch (exit codes 0/1/2/3/4 with a per-check report).

### Observed effort behind M0-01 to M0-05

From each task's handoff. "Worker" is the implementing session including its own fix rounds; review sessions are counted separately and only some recorded a duration.

| Task | Worker time | Review rounds | Recorded review time | Rounds that returned material findings |
| --- | --- | --- | --- | --- |
| M0-01 | ~25 min | 1 | not recorded | 0 (minor defects fixed before integration) |
| M0-02 | ~2 h (2 rounds of fixes) | 2 | not recorded | 1 |
| M0-03 | ~4 h 20 min (1 h 45 first candidate + 45 + 40 + 25 + 45 min of fixes) | 5 | 12, 11, 7, 20 min (review 5 not recorded) | 4 |
| M0-04 | ~2 h (1 h 30 + 30 min of fixes) | 2 | 10 min (review 2 not recorded) | 1 |
| M0-05 | ~1 h 10 min | 1 | not recorded | 0 (one minor finding, now M0-06's follow-up) |
| **Total** | **~9 h 55 min** | **11** | **≥1 h** (6 of 11 sessions recorded no duration) | **6 of 11** |

Two ratios are worth carrying forward, both from a small sample of five tasks on one host by two models: **fix rounds after the first candidate cost roughly as much as the first candidate itself** (M0-03: 1 h 45 min then 2 h 35 min; M0-04: 1 h 30 min then 30 min), and **more than half of all review rounds returned a material finding** that changed the implementation or an evidence claim. The five review rounds of M0-03 are the outlier and the reason: each one found a real defect in how the *check itself* was defined (a restore comparison measured against the wrong sample; a patch carried a build artifact; held input was lost across a state; sparse sampling hid transient perturbations), not in the emulator.

## Interpretation

Every M0 gate has at least one observation behind it, and the observations reproduce today on the candidate commit: the re-run produced the recorded digests and exit codes with no adjustment. At writing time the single outstanding item was CI on this exact commit, and M0 acceptance was blocked on it rather than described as "accepted pending CI"; that run (34561514855) has since been observed green on both platforms, so every gate is met.

What M0 does **not** establish, and should not be read as establishing: nothing about the game. No work RAM byte has a gameplay meaning (`$7E0073` is a byte that follows the Start bit during one part of the boot sequence and is otherwise uninterpreted); no native simulation exists; `src/lab` is a determinism probe, not recovered code. The laboratory's own reach is also narrower than the command surface suggests: the reference side runs on one host and one OS, its per-frame comparison covers work RAM and the CPU register block only, and a divergence confined to unsampled state that reconverges before the last frame would not be seen.

What would falsify this record: any command in the table above producing a different exit code or digest at `abb8c60` on a host with the same ROM and toolchain; a gate marked met whose cited record does not contain the observation claimed for it; or CI failing on this candidate.

## Independent check

Review 1 of M0-06 (fresh session, own clone with only the ROM path provided, candidate `eb82701`, 11 September 2026) bootstrapped and built the core itself (library bytes differ from this host's, behaviour digests identical, as R-0002's limits say) and audited every gate's citation against R-0001 to R-0004, D-0001 and the task records: no claim was unsupported. It reproduced the re-run table (118 checks, `583d1ec544ec61a2…`, `f210eecacf63cbeb…`, frame 300 and byte `0x00073` for both perturbations, exits 4/4/2/2/2/3/1 and the `save_does_not_perturb` failure at 70), added two cases of its own (the state origin regenerated and run: `a5a669d2671de7ab…`; its restore-check report moved away: exit 2 `run_origin_restore_check: missing`), ran the 39 `test_replay.py` tests in a worktree with no `local/`, and caught six mutations of the `consistent` expression with the new test (the three above and `all`→`any`, `==`→`<=`, one side only). The effort figures were traced line by line to the handoffs. Two minor corrections are folded in above: six, not five, of the eleven review sessions recorded no duration; the absent-restore-check case belongs to R-0003, not to this re-run. Verdict: approve. Details in [M0-06](../../tasks/M0-06.md).

Before that review this record was submitted unreviewed. The evidence it assembles has been independently reproduced many times: M0-01 by 1 reviewer, M0-02 by 2, M0-03 by 5, M0-04 by 2 and M0-05 by 1, each a fresh session on its own clone, together with the M0-05 worker (a different model) reproducing M0-04 from the records alone. The re-run recorded here is this session's own and is not an independent check of itself.

The M0-06 follow-up test was checked against three mutations of the expression it covers (`consistent_with_first_runs` forced true, and either of its two clauses dropped); each was caught by the named test, and the unmutated file is green (ignored `artifacts/m0-06/mutation-probes.py`).

## Implementation consequence

- M0's acceptance rests on `abb8c60` plus the records that follow it. A later change to the toolchain lock, the pinned core, the patch or the manifests invalidates the digests quoted here and needs its own re-run, not an edit of this table.
- The estimate basis in [the project plan](../PROJECT_PLAN.md) is the effort table above. It is five tasks on one host; it is a starting figure to revise, not a forecast.
- Gaps G1–G7 of R-0004 remain the process conditions on concurrency; G2 and G3 are the two that this record re-observed.
- The `divergence_localized: failed` branch is now covered ROM-free (`tests/tooling/test_replay.py::StubbedCompareTests::test_an_inconsistent_localization_is_failed_not_passed`), closing M0-05 review 1's minor finding 1. Suite 117 → 118 checks, 109 → 110 Python tests.

## Supersession

None. This record cites R-0001 to R-0004 rather than restating them; where a number here differs from an earlier record, the earlier record's phase or domain is quoted with it.
