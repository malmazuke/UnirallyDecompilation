# R-0014 — Classic content pack and semantic playable start

- Task: [M3-02A](../../tasks/M3-02A.md)
- Status: implementation candidate; independent review pending
- ROM: accepted PAL SHA-256 `a1105819...fd4e`
- Pack rules: `tests/manifests/content/classic-crawler-dragster-pack.json`

## Pre-implementation freeze

At accepted behavioral base `dbe146a`, the first attempt to reproduce the
M3-01 reviewer case correctly failed because the isolated toolchain was absent.
After the required bootstrap, the reviewer-owned release-at-3213 case and
fresh-process restores at 3226/3227/3228 passed all 15 checks (ignored report
SHA-256 `99e1ae50...aaae`).

Source inspection then enumerated every static-content read by
`movement_runner`: thirteen files populate track sampling, flat contact,
progress, pose/displacement/idle pose, rotation reward/class and speed decay.
The runner reads them once before the initial state is emitted. There are no
other static-content reads; the controller stream and canonical state are
separate runtime inputs. Logical IDs and the semantic start were frozen in
commit `d0fa9ed` before pack code was added.

## Extraction and inspection

Two clean extractions of the exact 2 MiB ROM produced byte-identical 86,485-byte
packs with SHA-256 `0b9a0557...343f`. Each has thirteen entries; their offsets,
sizes and SHA-256 values appear in ignored inspection report
`artifacts/m3-02a-inspect-a.json` (`effe63db...c1b`). A deliberately truncated
ROM returned invalid input before creating the requested output (`8ab1d047...97f`).
A simulated interruption after file flush but before rename returned failure,
removed the temporary file and left no output (`6d77e559...976`).

Header, schema, source identity, extraction-rules identity, logical-ID table and
first payload mutations each returned invalid input with the responsible
failure. Their ignored reports are `artifacts/m3-02a-mutation-*.json`. The
native reader also rejects the payload mutation directly; the stable native
command rejects it before build/process execution (`27f334a4...45af`). Authored
ROM-free tests construct deterministic synthetic packs and cover round trip,
logical lookup, atomic interruption, wrong source identity, all six mutation
classes, duplicate/missing/extra entries and stable-command exit codes.

## ROM-independent execution and start state

Pack-backed execution of the reviewer-owned finish case passed two fresh
processes and restores 3226/3227/3228 (`bb677932...b1b4`). With
`local/rom-location.txt` temporarily pointing to a nonexistent path, the
continuous case passed exact gameplay/finish comparison and restores at
3213/3453 (`75a4f09f...599`). Its report input inventory contains the tracked
case/reference inputs, native binary, generated Classic pack and controller
stream, and no ROM, WRAM, SRAM, imported seed or loose content path.

The public `classic.crawler.dragster.race-start.v1` constructor assigns named
`MovementState` fields and deterministically serializes to the accepted
333-byte `URMV0001` SHA-256 `7cd034fc...b4ab`. The private imported seed is used
only by a focused equality check and the accepted differential cases; it is not
needed by pack-backed execution and no seed bytes are tracked.

These observations cover one ROM, one tour/track/rider pair and the accepted
M3-01 input domain. Presentation content remains M3-02 and general starts,
other tracks/modes and distribution clearance are not established here.
