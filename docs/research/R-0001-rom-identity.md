# R-0001 — Identity of the selected PAL Unirally ROM

- Status: independently verified
- Related task/decision: [M0-01](../../tasks/M0-01.md)
- Tested domain and excluded cases: static file inspection only. Region, mapping and timing are read from the cartridge header and are not confirmed by execution. No emulator was used.
- ROM hash, emulator revision/configuration and adapter version: SHA-256 `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`, 2,097,152 bytes; no emulator; `unirally_lab` 0.1.0.
- Addresses: file offsets. With no copier header they equal ROM-data offsets. Under LoROM mapping file offset 0x7FC0 corresponds to CPU bus address $00:FFC0; this correspondence is the standard mapping assumption and not yet observed.
- Input/reset/snapshot identity and hashes: not applicable.
- Experiment source commit and exact command: task branch `task/M0-01-rom-identity`; `python3 tools/project.py rom inspect --path <rom> --manifest-out tests/manifests/rom/unirally-pal.json --report artifacts/m0-01/rom-inspect.json --task M0-01`.
- Artifact location, hashes and regeneration procedure: tracked manifest [`tests/manifests/rom/unirally-pal.json`](../../tests/manifests/rom/unirally-pal.json); local report under ignored `artifacts/m0-01/`. Regenerate with the command above on any host holding the same file.

## Observation

The user-supplied file `Unirally (Europe).sfc` measures exactly 2 MiB, so it has no 512-byte copier header. Hashes over the whole file:

| Hash | Value |
| --- | --- |
| SHA-256 | `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e` |
| SHA-1 | `d39ec113ef153ec9b7bacf12ed4a47f1a6d63a06` |
| MD5 | `2209427113f6535329c8b17ebab8a2e5` |
| CRC32 | `d8583ed7` |

The internal header is at file offset 0x7FC0; the HiROM location 0xFFC0 holds only 0xFF bytes.

| Field | Value |
| --- | --- |
| Title | `UNIRALLY` (padded with spaces to 21 bytes) |
| Map mode | 0x30 (LoROM, FastROM) |
| Cartridge type | 0x02 (ROM with RAM and battery, by the usual table) |
| ROM size code | 0x0B (2 MiB) |
| RAM size code | 0x03 (8 KiB) |
| Country code | 0x02 (Europe; PAL video standard by the usual table) |
| Developer code | 0x33 (extended header present) |
| Extended header | maker code `01`, game code `4L  `, subtype 0x00 |
| Version | 0x00 |
| Checksum complement / checksum | 0x752C / 0x8AD3, XOR is 0xFFFF |
| Computed byte-sum checksum | 0x8AD3, equal to the header value |
| Emulation-mode RESET vector | 0x8858 |
| Native NMI / IRQ / BRK vectors | 0x8587 / 0x8583 / 0x857F |

A zip archive beside the file, `Unirally (Europe).zip` (SHA-256 `3df7c3a292dbe8d7957577bdf5b3bd2ea461af673e4c623a44cc076286bb7e63`, 1,091,026 bytes, archive comment `TORRENTZIPPED-83EBB1D4`), contains a single member of the same name whose decompressed bytes have the identical SHA-256. The tool consumes the `.sfc`; the zip is provenance only.

The file's SHA-256 was identical before and after inspection. The tool opens the file read-only and never writes to it.

## Interpretation

The image is a headerless, checksum-consistent European (PAL) LoROM FastROM cartridge dump with 8 KiB battery-backed RAM, version 0. The TorrentZip packaging and filename follow the No-Intro naming convention, which suggests a database-verified dump, but no external database lookup was performed in this task; the identity recorded here is what was observed. Any later work must reference this SHA-256, not the filename.

Falsification: if execution under a reference emulator shows non-PAL timing behaviour or a different mapping, the header interpretation is wrong for this cartridge and this record must be superseded.

## Independent check

Three independent computations agree: the ad hoc read-only shell inspection recorded in the M0-01 task attempts table, the implemented tool, and an independent reviewer in a fresh agent session who decoded the header bytes with its own code and recomputed all hashes. The reviewer also confirmed the reset vector target at file offset 0x0858 begins with opcode 0x4C (JMP absolute), which is plausible code; this is an observation, not yet a traced execution.

## Implementation consequence

- All manifests, replays and evidence records reference ROM SHA-256 `a1105819…fd4e`.
- `rom inspect --expect tests/manifests/rom/unirally-pal.json` rejects any other file with exit code 1 and a per-field mismatch list, and reports a missing file with exit code 2.
- Local arrangement: the ROM stays outside the repository. Ignored `local/rom-location.txt` holds its absolute path; the tool uses it when `--path` is omitted. Another authorized host obtains the identical file privately, writes its own `local/rom-location.txt`, and runs the `--expect` command to verify the copy.
- 8 KiB SRAM implies persistent data is part of every reference experiment identity (see build and validation).

## Supersession

None.
