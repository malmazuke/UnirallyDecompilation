# D-0002 — Observing reads, writes and stored values without changing the pinned core

- Status: decided (coordinator, 11 September 2026); revisit if the fallback condition below is met
- Related tasks: [M1-02](../../tasks/M1-02.md) (implements the tool as its part A), [M1-03](../../tasks/M1-03.md) (consumes it); builds on [M1-01](../../tasks/M1-01.md) and [R-0006](../research/R-0006-observed-code-map.md)
- Affects: every task that needs to know which instruction accesses which address, what value it stores, and how data reaches the PPU (DMA parameters, block moves)

## Problem

M1-01's coverage map records executed instructions only; the trace carries no memory accesses (R-0006, "Reads and writes are not tracked"). M1-02 must locate the writers of player-state bytes and M1-03 must see how track and asset data in banks above $83 (which never execute) reach work RAM and video RAM. `docs/STATE.md` left the choice of first experiment to the coordinator: a bus-access capture in the core patch, or work RAM differencing between controlled inputs.

## Options considered

1. **Bus hook in the core patch.** A function pointer called from `Bus::read`/`Bus::write` (which the CPU, DMA and HDMA all go through) with aggregation in C++. Exact and complete: indirect pointers, DMA engine reads, stack and every register write are observed with the current pc. Cost: the tracked patch changes, so `patch_sha256` in `tools/locks/emulators.json` and in all seven replay and reference manifests changes; under the M1-01 fallback procedure every recorded digest must be re-run, shown unchanged and confirmed by an independent reviewer; per-access volume is roughly three times the instruction count (about 150 million events for the race scenario), so the aggregation must be written in C++ rather than drained into Python; the core takes a small per-access cost.
2. **Trace-derived accesses from the unchanged ring.** Every ring entry already records the pre-instruction A, X, Y, S, D, DBR, P and E (22-byte entry, R-0006 finding 1). With the opcode and operand bytes read from the ROM at the pc, the effective address of direct-page, absolute, long, indexed, stack-relative and stack-push/pull accesses and of block moves (MVN/MVP: X = source offset, Y = destination offset, DBR = destination bank while the instruction re-executes) is exact, and the value stored by STA/STX/STY/STZ and pushes is exact (from the register in the same entry, with the width given by M/X). Loads can take their value from the next entry's register. What it cannot resolve: the pointer contents of indirect modes (`(dp)`, `[dp]`, `(dp,X)`, `(dp),Y`, `[dp],Y`, `(abs)`, `(abs,X)`), the operand bytes of code executing from work RAM (the block-move routine at `$00:0199`), DMA engine reads (not instructions; but the DMA parameters are stores with known values), and VRAM/CGRAM/OAM contents (the core exports work RAM and cartridge RAM only). Cost: a Python decoder per instruction during the per-frame drain (M1-01's drain costs 25 s for the race scenario; a decoder is expected to multiply that by a few, still minutes), an addressing-mode table for all 256 opcodes with ROM-free tests, and additive worker options. No baseline changes.
3. **Work RAM differencing only.** Controlled-input runs with per-frame work RAM dumps identify *which bytes* respond to an input (the M0-04 method, already used for `$7E0073` and `$7E0313`) but not *which instruction* writes them or with what arithmetic; M1-02's acceptance needs the writers.

## Decision

Option 2 first, combined with option 3 for candidate discovery. M1-02 builds the trace-derived access record (part A) with the residual reported explicitly per (pc, addressing mode): unresolved accesses are counted, never guessed. Indirect accesses may be resolved from the end-of-frame work RAM only when the record shows the pointer bytes were not written during that frame, and such resolutions are labelled as end-of-frame resolutions. The operand bytes of the work RAM routine at `$00:0199` are read from the end-of-frame work RAM the same way, with the same label.

Fallback: if a task's acceptance criterion cannot be met because of the residual (a validated field written only through an indirect pointer that changes within the frame, or M1-03 needing VRAM contents beyond what the frame image and the DMA parameters show), the coordinator opens a separate task for option 1 under the procedure recorded in M1-01 (patch, lock and every manifest's `patch_sha256` change in one explained commit, every recorded digest re-run and shown unchanged, reviewer confirmation). Workers do not change the patch inside M1-02 or M1-03.

## Rationale

No manifest, lock, schema or digest changes; the reviewer's job stays the same as in M1-01 (byte-identical fresh captures, synthetic-ROM tests, spot checks against the samples' trace window). The stored values at the DMA registers `$43x2`–`$43x6` (39 static references to `$00:4302` in the race map) and the X/Y series at the block-move site give M1-03 the ROM source addresses of what is uploaded, which is the information it needs first. The per-instruction Python cost is bounded by restricting the derivation to a frame window when the whole run is not needed.

## Consequences

- The access record is a laboratory artifact (ignored `artifacts/`), regenerated by a recorded command; tracked outputs carry addresses, counts, frames and values of stores to registers, never ROM bytes.
- Field names in `docs/state/` and any `tests/manifests/fields/` file are the interface M2 builds on; M1-02 owns their first version and the coordinator serializes later changes.
- The residual categories (unresolved indirect, work RAM code operands, DMA engine reads, VRAM contents) are listed in every access-record summary so a reader sees what the record cannot show.
