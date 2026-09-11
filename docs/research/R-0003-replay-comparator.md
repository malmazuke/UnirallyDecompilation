# R-0003 — Replay manifests and comparator: repeated runs, a perturbed input and its localization

- Status: observed (single host; independent review pending)
- Related task/decision: [M0-04](../../tasks/M0-04.md); builds on [D-0001](../decisions/D-0001-reference-emulator.md) and [R-0002](R-0002-reference-adapter-determinism.md)
- Tested domain and excluded cases: laboratory behaviour of `python3 tools/project.py replay validate|run|compare` on the PAL ROM with the tracked manifests in `tests/manifests/replay/`. Nothing here interprets any work RAM byte as a gameplay field; the ranges are raw diagnostics. Excluded: Linux, the cycle-accurate PPU profile, save points inside the perturbing region 29–96, sub-frame input timing.
- ROM hash, emulator revision/configuration and adapter version: ROM SHA-256 `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e` (R-0001); bsnes `7d5aa1e656b9` with patch `a719f5ffe222…`, options as `bsnes.DEFAULT_OPTIONS`, `Strict` synchronization; reference samples schema 2; replay manifest schema 1; macOS 15.7.2 arm64, Apple clang 17.0.0, Python 3.14.3.
- Addresses: work RAM offsets are given as offsets into the 131072-byte block, i.e. `$7E0000 + offset`; nothing about the code that reads or writes them is claimed.
- Input/reset/snapshot identity and hashes: cold start unless stated; state after frame 150 of `tests/manifests/reference/boot-start-600.json`, SHA-256 `893f08b82864a5cd…`, validated by `reference restore-check --save-after 150` (all three required checks passed).
- Experiment source commit and exact command: recorded in the M0-04 task record (attempt table and handoff); commands are the manifests' `regeneration_command` values.
- Artifact location, hashes and regeneration procedure: ignored `artifacts/m0-04/` (reports, samples, derived scripts, work RAM dumps, divergence reports) and `local/states/boot-start-600-150/`; report digests are listed in the task handoff.

## Observation

Sampling per frame as in R-0002 (work RAM digest, 26-byte CPU register block, video and audio digests) plus the declared range `wram_0000_0200` (raw bytes at offsets `0x0000`–`0x01FF`).

1. **Repeated fresh-process runs of one manifest are identical.** `replay compare --manifest tests/manifests/replay/boot-start-600.json` ran the manifest in two worker processes (distinct PIDs, neither the comparator's) and found all three declared fields identical on all 600 frames, identical final serialized states (`1a6fbf6d24c532ff…`) and identical video/audio digests; sample digest `583d1ec544ec61a2…` in both. `--runs 3` gave the same digest in a third process. Exit 0. The same held for the state origin: two fresh restores of the state after frame 150 sampled identically on frames 151–599 (449 frames, sample digest `a5a669d2671de7ab…`) and their final state equals the cold-start final state `1a6fbf6d24c532ff…`.
2. **A removed known-active input is detected at the frame it was first applied.** Against `boot-start-600-start-removed` (no input at all) the first divergence is frame 300 in `wram_sha256` and `wram_0000_0200`; the register block is identical on that frame. Exit 1. The divergence report carries the prior sample (frame 299, identical on both sides), the inputs on both sides at frames 299 and 300 (`{"0": ["start"], "1": []}` versus none), the differing bytes of the declared range and the trace windows recorded at the end of both runs.
3. **Localization.** Re-running both sides in fresh processes to the end of frame 300 (`--stop-after-frame 300 --wram-dump-out`) and diffing the full 131072-byte work RAM dumps found exactly **one differing byte**: offset `0x0073` (`$7E0073`) holds `0x10` with Start held and `0x00` without. This is the same byte R-0002 finding 5 saw lost across a restore before gamepad state was serialized. The CPU registers at the end of frame 300 are identical, the instruction counts to the end of frame 300 are identical (4,381,713) and the last 64 pre-instruction register snapshots are identical on both sides.
4. **Extent of the perturbation.** Over the whole 600-frame samples the work RAM digest differs only on frames 300–305, exactly the frames on which Start is held; the declared range shows only offset `0x0073` differing on each of them (`0x10` versus `0x00`); registers, video and audio digests never differ; the final serialized states are byte-identical. For the moved variant (`boot-start-600-start-moved-310`, Start on frames 310–315) the first divergence is again frame 300 and the differing frames are 300–305 (`0x10` on the left only) and 310–315 (`0x10` on the right only), with identical final states. Within the tested domain the Start press at 300–305 therefore leaves no work RAM trace after the last frame on which it is held; whether the whole emulator state also reconverges before frame 599 was not sampled (only the final serialized state is compared).
5. **Bounded execution and clear failures.** `replay run` and `replay compare` on `tests/manifests/replay/unreachable.json` with `--timeout 3` are killed after 3.0 s, record the run as `timeout` and exit 4; the comparison check is recorded as `skipped`, not passed. A ROM path that does not exist gives `rom_available: missing`, exit 2. A state-origin manifest whose state file is absent gives `origin_available: missing` with the regeneration command in the detail, exit 2; one whose restore-check report is absent gives `origin_restore_check: missing`, exit 2. A manifest whose `expected.sample_digest` differs from the observed run fails `sample_digest_matches_expected`, exit 1. A structurally invalid or absent manifest exits 3 for all three subcommands.
6. **Trace count phase.** Samples schema 2 reads the trace before the final serialize: 8,514,628 instructions at the end of frame 599 and 8,514,634 after the synchronizing final serialize (R-0002 finding 7 quoted the latter); 4,368,039 and 4,368,044 for the 300-frame script.
7. **Throughput.** 600 frames with per-frame full-WRAM hashing and a 512-byte range capture take 1.34 s of worker time; a 301-frame localization re-run with a WRAM dump 0.72 s; a complete `compare --against` with localization 4.2 s.

## Interpretation

The comparator does what M0-04 asks of it: it distinguishes identical fresh-process runs from a run whose input differs, reports the first differing frame with the surrounding evidence and localizes the difference to a byte. The single differing byte at `$7E0073` on exactly the frames Start is held is consistent with the game copying the latched joypad word into work RAM every frame without acting on it during that part of its boot sequence, but this record makes no claim about the code; M1 will trace the writer. That the removed and moved variants both diverge first at frame 300 shows that the comparison is ordered by frame and stops at the first difference rather than at the largest one.

What would falsify the laboratory claims: a repeated run diverging (finding 1), or a divergence report whose frame or byte disagrees with a manual diff of the samples. A different perturbation (another button, another port, another frame) may well touch more than one byte; only Start at 300–305 and 310–315 was measured.

## Independent check

None yet beyond the two variants (removed and moved) agreeing on the first frame and the byte, and the localization re-run agreeing with the first runs' samples (`consistent_with_first_runs`). The reviewer should run an own perturbation (another frame, another port, a second button) and check the reported frame against a manual comparison of the samples files.

## Implementation consequence

- A replay manifest (schema 1) is the unit of reference execution from M0-04 on; `replay run` derives the reference script from it, and a state origin must name a restore-check report that passed the three required checks for that exact script and state.
- Comparisons are ordered by frame over the declared fields and stop at the first difference; the final serialized state is compared separately; video/audio digests are informational.
- The localization re-run uses `--stop-after-frame`, which leaves the script and its digest unchanged, so it applies to state origins too.

## Supersession

None. R-0002 finding 7's instruction counts remain correct for their phase (after the final serialize); finding 6 above records the phase difference.
