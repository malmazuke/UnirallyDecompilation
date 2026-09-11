# R-0004 — Resumable execution: reproducing a baseline from the records, interrupted runs and failed-test reporting

- Status: observed (single host; independent review pending)
- Related task/decision: [M0-05](../../tasks/M0-05.md); exercises the process in [the agent workflow](../AGENT_WORKFLOW.md) and the tooling of [R-0003](R-0003-replay-comparator.md), [R-0002](R-0002-reference-adapter-determinism.md) and [D-0001](../decisions/D-0001-reference-emulator.md)
- Tested domain and excluded cases: the laboratory process itself — whether a fresh session with no conversation history reproduces the M0-04 baseline from the committed records, how `python3 tools/project.py replay compare` behaves when it or its worker is killed, and whether `test --suite synthetic` reports a failing test truthfully. Excluded: Linux (CI is ROM-free and the core has not been built there), two workers running at the same time, any scheduler, and every gameplay question.
- ROM hash, emulator revision/configuration and adapter version: ROM SHA-256 `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e` (R-0001); bsnes `7d5aa1e656b9` with patch `a719f5ffe222…`, `Strict` synchronization; reference samples schema 2; replay manifest schema 1; macOS 15.7.2 arm64, Apple clang 17.0.0, Python 3.14.3.
- Addresses: work RAM offsets are offsets into the 131072-byte block (`$7E0000 + offset`).
- Input/reset/snapshot identity and hashes: the tracked manifests in `tests/manifests/replay/`; cold start unless stated.
- Experiment source commit and exact command: worktree `.worktrees/m0-05` on `task/M0-05-resumable-pilot`, base `09b495f`; commands in the M0-05 attempt table.
- Artifact location, hashes and regeneration procedure: ignored `artifacts/m0-05/` (`baseline/`, `interrupt/`, `failing-test/`, `final/`, `mutation-probes.py`); report digests are listed in the M0-05 handoff.

## Observation

### 1. The records alone were enough to reproduce the baseline

The worktree contained the repository and `local/rom-location.txt`; no toolchain, core, state, artifact or report was copied from the coordinator's checkout. Working only from `AGENTS.md`, `docs/STATE.md` and the M0-04 handoff, the session ran `doctor`, `bootstrap` (pinned CMake/Ninja fetched and verified, 2.4 s), `build --preset lab-debug`, `test --suite synthetic` (106/106, `98 tests run, 98 records, 0 failed; runner exit 0`) and `reference build` (the pinned core cloned from GitHub, patched and built in 14.9 s), then every command in the handoff's "exact next experiment". Every prediction held: `reference verify` gave `f210eecacf63cbeb…` / `df4fb430e731dfe1…` in three fresh processes; `replay compare` of `boot-start-600` exit 0 with `583d1ec544ec61a2…` / `1a6fbf6d24c532ff…` in two distinct worker processes; against `boot-start-600-start-removed` exit 1 with the first divergence at frame 300 and the single work RAM byte `0x00073` (`0x10` versus `0x00`); `unreachable` under `--timeout 3` exit 4; the state-origin manifest exit 2 with its regeneration command in the detail. Nothing in the handoff had to be guessed or asked for. The only friction is recorded as gap G1 below.

### 2. `replay compare`'s post-run wiring is now covered without the ROM

M0-04 review 2 noted that everything `cmd_compare` does *after* the worker returns had only ROM-bound evidence. `tests/tooling/test_replay.py::StubbedCompareTests` runs the command in process with `reference.commands.run_bounded` replaced by a stub that stands in for the worker: it computes samples from the derived script alone, holding `0x10` at work RAM offset `0x73` exactly while `start` is pressed on port 0 (the shape R-0003 measured), and can report a chosen PID, a video/audio tag that leaves work RAM and the final state untouched, a timeout, a missing executable, a non-zero exit or an unreadable samples file. The prerequisites are stubbed to name a core library and a ROM that do not exist, so a run that reached the real worker could only report `missing` — `test_without_the_stub_the_worker_cannot_load_a_core` asserts exactly that (exit 2, `run1: missing`, `fields_identical: skipped`, the absent library named in the worker log).

Eleven tests (109 Python tests in the suite, up from 98; 117 synthetic checks, up from 106) cover: identical runs (exit 0, `fresh_processes` listing two distinct worker PIDs); `fresh_processes` failing when two workers report the same PID, when a worker reports the comparator's PID, and when a PID is absent, while the field comparison still passes; `av_identical` required for a cold start (a video/audio difference alone makes the command exit 1) and optional after a restore (the same difference leaves exit 0 and the check marked `informational after a restore`); the divergence report (frame, prior sample, both sides' inputs at the divergence frame and the one before it, trace windows, and a localization that finds the single differing byte `0x00073`), written to `divergence.json` and listed in the report's artifacts; `--no-localize` (two worker calls, no re-runs); a timed-out or crashed localization re-run leaving the verdict at exit 1 with `divergence_localized: skipped`; the mapping of worker outcomes to exit codes (timeout 4, missing executable 2, crash 1, unreadable samples 1), each with `fields_identical: skipped` and no comparison in the report; per-pair check names and the first divergence under `--runs 3`; and `expected` digests checked for every run.

No production code changed: `reference.commands._prepare` and `reference.commands.run_bounded` were already module attributes the test can replace, so no seam had to be added to `tools/unirally_lab/replay/commands.py`. That the file needs nothing local was checked directly: in a detached worktree with no `local/` directory at all (no ROM, no core, no toolchain) `test_replay.py` runs 38 tests and `test_reference.py` 32, both green.

Eight mutations of `replay/commands.py` were each caught by the named test (`artifacts/m0-05/mutation-probes.py`): `fresh` forced true; `av_required` forced false and forced true; the localization re-runs made required; an incomplete run reported as a plain failure instead of its own status; `if args.localize` disabled; the divergence report not written; the `expected` comparison forced true.

### 3. Interrupted runs

Measured on `boot-start-600` (artifacts and reports in `artifacts/m0-05/interrupt/`):

- **A worker killed (`SIGKILL`) while it runs.** The parent exits 1 and records `run1: failed` with the worker's exit status and log; `fields_identical` is `skipped`, and the report contains no `comparisons` and no `divergence` key at all. The worker writes its samples file only after the run completes, so the artifacts directory holds the derived script, the fields file and the worker log but **no samples file**: there is no partial sample set to mistake for a result. Re-running the handoff command into the same artifacts directory gives exit 0 and `583d1ec544ec61a2…` in both fresh processes.
- **The parent `replay compare` killed (`SIGKILL`) while a worker runs.** No report file is written at all — absence, not a half-written verdict. The worker is started in its own session (so that a timeout can kill a whole process group), which means it **survives its parent**: right after the kill the worker was still running, and about half a second later it wrote `run1-samples.json` into the artifacts directory that no live process was any longer reading. Re-running the handoff command into the same directory gives exit 0 and the recorded digests. This orphan is gap G2.
- **The bounded runner's own kill.** The same command under `--timeout 0.3` records `run1: timeout`, `fields_identical: skipped` and exits 4, as R-0003 finding 5 recorded for the unreachable manifest — timeout, failure and missing prerequisite stay distinct.
- **A stale divergence report is not removed.** A divergent comparison writes `divergence.json` into its artifacts directory; a later identical comparison into the *same* directory exits 0, records `divergence: null` and lists only the script and the two samples files as its artifacts, but the earlier `divergence.json` is still on disk. The report is unambiguous; the directory is not. Gap G3.

### 4. Failed-test reporting

A scratch worktree at the same commit with a deliberately failing test file (a failing assertion, a failing subtest among two, an erroring test and a passing test in the same file) makes `python3 tools/project.py test --suite synthetic` exit 1 with `status=failed`, 4 failed checks of 121: one record per failing test **named individually**, the failing subtest carrying its parameters (`…test_a_subtest_failure_must_also_be_reported (n=2)`) and its traceback, plus `python_tooling_tests: failed — 113 tests run, 113 records, 3 failed; runner exit 1`. The passing test in the same file is still reported as passing, and `source.dirty` is true with the new file named in `untracked_files`. The M0-02 defect that review 1 of M0-04 found (erroring subtests counted as passes) does not recur. The scratch worktree was removed and pruned afterwards.

## Interpretation

The durable records carried the work: a session with no access to the previous conversation reproduced every recorded digest, exit code and divergence byte, and then completed a follow-up that the records had scoped for it. What made that possible was concrete and repeatable — the handoff named exact commands with their expected exit codes and digest prefixes, every ignored artifact had either a regeneration command or a manifest, and the prerequisite commands (`bootstrap`, `build`, `reference build`) were listed in the order they must run.

For interruption, the important property is that the comparator's result exists only in the report, which is written once at the end: a killed run leaves either an explicit failure record or no record at all, never a plausible-looking partial verdict. The weak point is not the verdict but the *directory* — files from a dead run, whether left by an orphaned worker or by an earlier divergence, persist beside the next run's files. That is harmless while one worker runs with the default per-run artifacts directory and matters as soon as two runs share an explicit `--artifacts` path.

What would falsify these claims: a killed run producing a report that passes; a partial samples file being read as a result; or a failing test that the suite reports as a pass.

## Process gaps observed, before two workers are allowed to run concurrently

| ID | Gap | Evidence | Suggested handling |
| --- | --- | --- | --- |
| G1 | The task registry (`tasks/README.md`) still says M0-05 is `ready: … not claimed` while `tasks/M0-05.md` says `claimed`. Two coordinator-owned files carry the same fact | Both files at `bb70b20` | One of the two is the claim; the other should point at it. With concurrent workers a stale registry row is how two dispatches of one task happen |
| G2 | A worker started with `start_new_session=True` survives the death of its parent and keeps running the core, writing into the parent's artifacts directory after the parent is gone | R-0004 finding 3, `artifacts/m0-05/interrupt/parent-killed*` | Before reassigning a task whose heartbeat is stale, check for live `reference/worker.py` processes (the workflow already says to confirm the former worker is stopped). A recorded worker PID per run exists in every report; a coordinator can use it |
| G3 | An explicit `--artifacts` directory is never cleaned, so a stale `divergence.json` (or samples from an orphan) sits beside a later passing run's files | R-0004 finding 3, `artifacts/m0-05/interrupt/stale-divergence/` | Treat the report, not the directory, as the result; prefer the default per-run directory (`artifacts/replay/<run-id>/`) and give each attempt its own path when a directory is named explicitly |
| G4 | The heartbeat and checkpoint fields of a task record are prose in the record itself, so a checkpoint is only visible as a commit. Nothing records that a worker is alive between commits | `tasks/M0-05.md` "Claim/lease/heartbeat/checkpoint location"; this session's checkpoints are commits | Adequate for one worker. For two, the workflow's own requirement of atomic claims and a lease store under ignored runtime state should be implemented before, not after, the second worker starts |
| G5 | The handoff does not state the runtime prerequisites a fresh session needs beyond the commands: network access (to fetch the pinned wheels and to clone the core), roughly 15 s of core build, and the ROM path arrangement | Finding 1; `reference build` clones from GitHub | Add a short "runtime needs" line to the handoff template: network, expected wall time, fixture arrangement |
| G6 | Localization re-runs of a divergence between two repetitions of the *same* manifest execute that same manifest on both sides, so they cannot reproduce the divergence and report zero differing bytes while `divergence_localized` passes | `test_three_runs_name_every_pair_and_report_the_first_divergence` | Small and contained: the verdict still comes from the required field comparison and the localization check is optional. Worth a note in the report's detail when there is no `--against` |
| G7 | CI is ROM-free, so no automated check covers any command that needs the core; the ROM-bound evidence is a human re-run on one host | `.github/workflows/synthetic.yml`; M0-03/M0-04/M0-05 evidence | Known and accepted for M0. The stubbed-worker tests narrow it: the comparator's wiring is now checked on both CI platforms |

None of these blocks a second worker on an independent task; G1 and G4 should be settled before two workers can be dispatched from the same queue.

## Independent check

Pending: an independent session must reproduce the candidate commit (baseline commands, the stubbed-worker tests, the two interruption experiments and the deliberate failing test) and the CI run on that commit.

## Implementation consequence

- The stubbed worker is the pattern for covering command wiring that would otherwise need the ROM: replace `reference.commands.run_bounded`, name prerequisites that cannot load, and assert that the real worker reports `missing` in the same fixture.
- A `replay compare` result is the report, not the artifacts directory. Consumers should read the report's `artifacts` list rather than the directory listing.
- A stale heartbeat requires checking for live worker processes before reassigning a task's files (G2).

## Supersession

Supersedes nothing. If a scheduler with atomic claims and leases is implemented, G1 and G4 are answered by it and this record's gap table should be linked from that decision.
