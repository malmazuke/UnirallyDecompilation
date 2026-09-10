# R-0002 — Reference adapter: headless determinism, input delivery and save/restore on the PAL ROM

Task: [M0-03](../../tasks/M0-03.md). Decision: [D-0001](../decisions/D-0001-reference-emulator.md). Recorded 10 September 2026.

## Domain

Verified observations about the laboratory's reference execution, not about the game. Everything below was measured on macOS 15.7.2 arm64 (Apple clang 17.0.0) with:

- ROM: PAL Unirally, SHA-256 `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e` (R-0001), no copier header.
- Core: bsnes commit `7d5aa1e656b9` + `tools/unirally_lab/reference/patches/bsnes-lab-exports.patch` (SHA-256 `27758024c1aa…`), libretro target, options in `tools/unirally_lab/reference/bsnes.py::DEFAULT_OPTIONS` (`bsnes_entropy=None`, fast PPU/DSP, no run-ahead, no overclock).
- Scripts: `tests/manifests/reference/boot-300.json` (300 frames, no input), `boot-start-600.json` (Start held on controller 1 for frames 300–305), `unreachable.json` (10^9 frames).
- Sampling: after every frame, SHA-256 of the 131072-byte work RAM, the 26-byte CPU register block (PC, A, X, Y, S, D, DB, P, E, MDR, V/H counter, field, WAI, STP), SHA-256 of the XRGB8888 frame buffer and of the 48 kHz stereo audio batch. The run's "sample digest" is a SHA-256 over the initial WRAM/cartridge-RAM digests and every frame's WRAM digest and register block.

## Findings

1. **Cold start is repeatable across processes.** Three fresh `worker.py` processes running `boot-300` produced sample digest `f210eecacf63cbeb…`, video/audio digest `edfa4f8e92b24dc0…` and final serialized-state SHA-256 `8e0af6be66113714…` (290423 bytes). A clean clone of the repository that cloned the pinned bsnes commit itself, applied the patch and rebuilt the core reproduced the same three digests. Report: `artifacts/m0-03/verify.json` (local) and the clean-clone report listed in the task record.
2. **Power-on state.** With entropy `None`, WRAM is all zeros at power-on (WRAM digest at frame 0 recorded in the samples); cartridge RAM (8192 bytes present for this ROM) starts from the core's allocation fill when no save file exists (`initial.cartridge_ram_sha256` = `7d2c7ac4888bfd75…`). The core writes `<ROM base name>.srm` to its save directory at unload and reads it back at the next load; with a shared directory, run 2 diverged from run 1 at frame 228. Every run therefore gets a private, empty save directory, and the initial cartridge-RAM digest is part of the sample digest.
3. **Serialized state.** Before the patch, two states from identical runs differed in exactly 8 bytes at offsets 542–549, inside bsnes' `Random` state, because the generator is seeded from `clock()` even when entropy is `None` (the generator's output is then unused). The adapter reseeds with `(0, 0)` after load; states from identical runs are now byte-identical.
4. **Saving does not perturb.** A run that serializes after frame 149 and continues has the same sample digest and final state as the uninterrupted run, although bsnes runs its threads to a synchronization point before serializing.
5. **Restore is exact for memory and registers.** Restoring that state in a fresh process and running frames 150–299 gave identical WRAM and registers on all 150 sampled frames and the same final state (`8e0af6be…`). The video digest of the first restored frame and the audio digests of all following frames differ from the uninterrupted run: the frame buffer and the resampler state are not part of the serialized state. Comparisons must therefore not span a restore for video/audio.
6. **Input delivery.** Start held for frames 300–305 produced the first WRAM difference against the no-input run at frame 300 itself, and two repetitions were identical. Start held for frames 200–205 produced no WRAM difference within 600 frames (the game does not react at that point of its boot sequence; the reason is not investigated here). `input_polls` equals the frame count: the core polls once per frame.
7. **Trace window.** The instruction hook counted 4,368,042 executed CPU instructions in 300 frames and 8,514,629 in 600; the last 64 pre-instruction register snapshots are recorded in every samples file.
8. **Bounded execution.** `unreachable.json` under `--timeout 3` is killed after 3.0 s; the report records the run as `timeout` and the command exits 4. No partial samples file is produced.
9. **Throughput.** 300 frames with full sampling take about 0.7 s of worker time (about 1.7 ms per frame including the 128 KiB hash); 600 frames 1.3 s.

## Limits

- Measured on one host and one core build. The library bytes differ between two builds of the same source (debug information embeds absolute paths), so reproducibility is claimed for behaviour (sample digests), not for the binary.
- No Linux run of the core yet; CI remains ROM-free.
- The fast PPU/DSP profile is the reference; the cycle-accurate profile was not run.
- Frame-granular input only. Nothing here identifies any gameplay field; that is M1.
