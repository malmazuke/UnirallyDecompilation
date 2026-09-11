# Observed code map: `boot-start-600`

Derived from an instruction-coverage capture of the reference core (bsnes `7d5aa1e656b9`, patch `a719f5ffe222`) on ROM SHA-256 `a1105819d48c04d6…` (2097152 bytes), frames 0–599, 8,514,628 executed instructions (largest frame 18,346, ring 262,144). Coverage file SHA-256 `1e6c02747d7c1003…`.

Regenerate: `python3 tools/project.py coverage capture --manifest tests/manifests/replay/boot-start-600.json --out artifacts/coverage/boot-start-600 && python3 tools/project.py coverage map --coverage artifacts/coverage/boot-start-600/coverage.json --out docs/map/boot-start-600.map.json --summary docs/map/boot-start-600.md`

Only executed instructions and the header vectors classify bytes; nothing is inferred statically. Reads and writes are not tracked (no data-access map). Indexed and indirect operands are not resolved.

## Totals

| Quantity | Value |
| --- | --- |
| Executed opcode bytes | 2,085 |
| Executed operand bytes | 2,563 |
| Unclassified bytes | 2,092,504 |
| Sum (must equal the ROM size) | 2,097,152 of 2,097,152 |
| Executed share of the ROM | 0.222 % |
| Bytes both opcode and operand (counted as opcode) | 0 |
| Distinct instruction addresses (24-bit) | 2,085 |
| Distinct sites (pc, mode, data bank) | 2,506 |
| Sites outside ROM | 3 |
| Addresses executed in more than one mode | 18 |
| Entry points (non-sequential targets) | 353 |
| Non-sequential steps / sequential steps | 1,880,931 / 6,633,696 |
| Unknown edges | 5 |
| Statically referenced addresses | 258 |

## Mode mix

| Mode | Instructions executed | Distinct sites |
| --- | --- | --- |
| NMX | 1,944,452 | 1,035 |
| NMx | 9 | 3 |
| NmX | 4,257,037 | 1,413 |
| Nmx | 2,313,127 | 52 |
| Emx | 3 | 3 |

## Executed bytes per bank

| Bank | Executed bytes | Opcode | Operand | Instruction addresses | Executions |
| --- | --- | --- | --- | --- | --- |
| $00 | 34 | 20 | 14 | 20 | 4,557 |
| $80 | 2,812 | 1,196 | 1,616 | 1,196 | 1,295,369 |
| $82 | 633 | 339 | 294 | 339 | 7,167,125 |
| $83 | 1,169 | 530 | 639 | 530 | 47,325 |

## Edges by kind

| Kind | Steps |
| --- | --- |
| JSR | 108,570 |
| JSL | 289,446 |
| JMP | 13 |
| JML | 1,051 |
| RTS | 108,568 |
| RTL | 289,443 |
| RTI | 350 |
| branch | 1,082,888 |
| interrupt entry | 350 |
| unknown | 252 |

## Vectors

| Vector | Value | Executed | Count | First frame | Modes | Per frame |
| --- | --- | --- | --- | --- | --- | --- |
| native_cop | $00:FFFF | no | 0 | - | - | - |
| native_brk | $00:857F | no | 0 | - | - | - |
| native_abort | $00:FFFF | no | 0 | - | - | - |
| native_nmi | $00:8587 | yes | 350 | 250 | NMX, NmX, Nmx | 0/1/2+ in 250/350/0 frames; exactly one per frame from 250 |
| native_reserved | $00:FFFF | no | 0 | - | - | - |
| native_irq | $00:8583 | no | 0 | - | - | 0/1/2+ in 600/0/0 frames; exactly one per frame from None |
| emu_cop | $00:FFFF | no | 0 | - | - | - |
| emu_reserved | $00:FFFF | no | 0 | - | - | - |
| emu_abort | $00:FFFF | no | 0 | - | - | - |
| emu_nmi | $00:FFFF | no | 0 | - | - | - |
| emu_reset | $00:8858 | yes | 1 | 0 | Emx | - |
| emu_irq_brk | $00:8583 | no | 0 | - | - | 0/1/2+ in 600/0/0 frames; exactly one per frame from None |

## Executed ranges (75)

Maximal runs of consecutive executed byte addresses; `modes` is the union over instructions starting in the run.

| Start | End | Bytes | ROM offset | Instructions | Executions | Modes | First frame |
| --- | --- | --- | --- | --- | --- | --- | --- |
| $00:8587 | $00:859A | 20 | 0x000587 | 13 | 4,550 | NMX, NmX, Nmx | 250 |
| $00:8858 | $00:885A | 3 | 0x000858 | 1 | 1 | Emx | 0 |
| $00:91D1 | $00:91DB | 11 | 0x0011D1 | 6 | 6 | NmX, Nmx, Emx | 0 |
| $80:885B | $80:8890 | 54 | 0x00085B | 18 | 18 | NmX | 18 |
| $80:889A | $80:889C | 3 | 0x00089A | 1 | 1 | NmX | 419 |
| $80:8C41 | $80:8C6C | 44 | 0x000C41 | 20 | 164 | NMX, NmX | 403 |
| $80:8C74 | $80:8CCA | 87 | 0x000C74 | 27 | 27 | NMX, NmX | 403 |
| $80:91DC | $80:9313 | 312 | 0x0011DC | 112 | 262,252 | NmX | 0 |
| $80:9318 | $80:933B | 36 | 0x001318 | 14 | 4,662 | NMX, NmX | 99 |
| $80:937B | $80:93A0 | 38 | 0x00137B | 15 | 15 | NmX | 407 |
| $80:96FD | $80:9718 | 28 | 0x0016FD | 15 | 15 | NMX, NmX | 404 |
| $80:9869 | $80:9880 | 24 | 0x001869 | 11 | 177 | NmX | 103 |
| $80:9885 | $80:98A3 | 31 | 0x001885 | 14 | 124 | NmX | 221 |
| $80:A09A | $80:A1F1 | 344 | 0x00209A | 140 | 1,341 | NMX, NmX | 24 |
| $80:A877 | $80:A8A3 | 45 | 0x002877 | 17 | 34 | NmX | 408 |
| $80:A8A8 | $80:A8D3 | 44 | 0x0028A8 | 17 | 68 | NmX | 98 |
| $80:ABC8 | $80:ABF8 | 49 | 0x002BC8 | 19 | 1,631 | NMX, NmX | 419 |
| $80:ABFC | $80:AC09 | 14 | 0x002BFC | 6 | 1,080 | NMX | 420 |
| $80:AC0D | $80:AC1C | 16 | 0x002C0D | 8 | 1,440 | NMX, NmX | 420 |
| $80:AC20 | $80:AC2D | 14 | 0x002C20 | 6 | 1,080 | NmX | 420 |
| $80:ACD5 | $80:ACDE | 10 | 0x002CD5 | 5 | 8 | NmX | 405 |
| $80:ACE7 | $80:AD09 | 35 | 0x002CE7 | 16 | 18 | NmX | 405 |
| $80:AD0F | $80:AD1E | 16 | 0x002D0F | 6 | 12 | NmX | 407 |
| $80:AD43 | $80:ADCD | 139 | 0x002D43 | 69 | 960 | NMX, NmX | 404 |
| $80:ADD1 | $80:ADE2 | 18 | 0x002DD1 | 9 | 54 | NMX | 404 |
| $80:B08C | $80:B0DB | 80 | 0x00308C | 30 | 360 | NmX | 97 |
| $80:B0F0 | $80:B0F9 | 10 | 0x0030F0 | 8 | 2,800 | NMX, NmX | 250 |
| $80:B612 | $80:B625 | 20 | 0x003612 | 10 | 98,311 | NMX, NmX | 18 |
| $80:B71D | $80:B745 | 41 | 0x00371D | 18 | 4,320 | NMX, NmX | 420 |
| $80:B76F | $80:B7B8 | 74 | 0x00376F | 30 | 5,400 | NMX, NmX | 420 |
| $80:C3BC | $80:C3DB | 32 | 0x0043BC | 16 | 241 | NMX, NmX | 406 |
| $80:C3FE | $80:C403 | 6 | 0x0043FE | 3 | 57 | NmX | 406 |
| $80:C408 | $80:C41A | 19 | 0x004408 | 9 | 171 | NMX, NmX | 406 |
| $80:C41E | $80:C44C | 47 | 0x00441E | 25 | 475 | NMX, NmX | 406 |
| $80:C451 | $80:C455 | 5 | 0x004451 | 4 | 4 | NMX, NmX | 406 |
| $80:C4B8 | $80:C4D8 | 33 | 0x0044B8 | 17 | 225 | NMX, NmX | 406 |
| $80:C4DC | $80:C4FF | 36 | 0x0044DC | 21 | 175 | NMX, NmX | 406 |
| $80:C557 | $80:C56B | 21 | 0x004557 | 11 | 11 | NMX, NmX | 406 |
| $80:D1EC | $80:D209 | 30 | 0x0051EC | 14 | 1,754 | NmX | 258 |
| $80:D20E | $80:D37A | 365 | 0x00520E | 143 | 1,691 | NMX, NmX | 375 |
| $80:EFD4 | $80:F02A | 87 | 0x006FD4 | 48 | 3,648 | NMX | 404 |
| $80:F52B | $80:F53A | 16 | 0x00752B | 7 | 14 | NMX, NmX | 407 |
| $80:F55F | $80:F5DB | 125 | 0x00755F | 49 | 1,224 | NMX, NmX | 228 |
| $80:F610 | $80:F617 | 8 | 0x007610 | 5 | 335 | NmX | 258 |
| $80:F622 | $80:F631 | 16 | 0x007622 | 8 | 2,800 | NmX | 250 |
| $80:F644 | $80:F647 | 4 | 0x007644 | 1 | 350 | NmX | 250 |
| $80:FA60 | $80:FACC | 109 | 0x007A60 | 48 | 3,568 | NMX, NmX | 250 |
| $80:FADF | $80:FB23 | 69 | 0x007ADF | 31 | 877,981 | NMX, NmX | 97 |
| $80:FB27 | $80:FBC4 | 158 | 0x007B27 | 75 | 14,273 | NMX, NmX | 98 |
| $82:8000 | $82:802D | 46 | 0x010000 | 25 | 75 | NMX, Nmx | 97 |
| $82:8035 | $82:8157 | 291 | 0x010035 | 143 | 5,393,347 | NMX, NMx, NmX, Nmx | 29 |
| $82:815F | $82:8160 | 2 | 0x01015F | 2 | 14,586 | NMX, NmX | 29 |
| $82:82A5 | $82:82D8 | 52 | 0x0102A5 | 28 | 838 | NMX, NmX | 42 |
| $82:82DE | $82:82E0 | 3 | 0x0102DE | 2 | 42 | NMX | 42 |
| $82:82E6 | $82:8336 | 81 | 0x0102E6 | 44 | 915,582 | NMX, NmX | 42 |
| $82:B183 | $82:B1AD | 43 | 0x013183 | 26 | 2,466 | NMX, NmX | 24 |
| $82:B1DB | $82:B20A | 48 | 0x0131DB | 26 | 344,497 | NMX, NmX | 24 |
| $82:B296 | $82:B2AB | 22 | 0x013296 | 15 | 495,216 | NmX | 24 |
| $82:B2B0 | $82:B2DC | 45 | 0x0132B0 | 28 | 476 | NMX, NmX | 24 |
| $83:8AF7 | $83:8B17 | 33 | 0x018AF7 | 13 | 13 | NMX, NmX | 403 |
| $83:8B1C | $83:8B5E | 67 | 0x018B1C | 35 | 180 | NMX, NmX | 403 |
| $83:8B62 | $83:8B62 | 1 | 0x018B62 | 1 | 2 | NmX | 403 |
| $83:8B79 | $83:8B92 | 26 | 0x018B79 | 13 | 10,256 | NMX, NmX | 403 |
| $83:90F4 | $83:91CB | 216 | 0x0190F4 | 96 | 10,320 | NMX | 405 |
| $83:91F7 | $83:9215 | 31 | 0x0191F7 | 13 | 13 | NMX | 377 |
| $83:92CC | $83:94CF | 516 | 0x0192CC | 223 | 8,186 | NMX, NmX | 404 |
| $83:9558 | $83:956C | 21 | 0x019558 | 10 | 10 | NMX, NmX | 419 |
| $83:963C | $83:9663 | 40 | 0x01963C | 21 | 432 | NMX, NmX | 404 |
| $83:966F | $83:967B | 13 | 0x01966F | 8 | 318 | NMX, NmX | 404 |
| $83:969F | $83:96B0 | 18 | 0x01969F | 9 | 306 | NMX, NmX | 404 |
| $83:96BE | $83:96FF | 66 | 0x0196BE | 35 | 840 | NMX, NmX | 404 |
| $83:9983 | $83:99B4 | 50 | 0x019983 | 21 | 21 | NMX, NmX | 404 |
| $83:99B8 | $83:99C1 | 10 | 0x0199B8 | 6 | 6 | NMX, NmX | 404 |
| $83:99F6 | $83:9A1D | 40 | 0x0199F6 | 16 | 32 | NmX | 99 |
| $83:FB41 | $83:FB55 | 21 | 0x01FB41 | 10 | 16,390 | NMX | 403 |

## Addresses executed in more than one mode

| Address | Modes | Lengths | Count |
| --- | --- | --- | --- |
| $00:8587 | NMX, NmX, Nmx | [1] | 350 |
| $00:8588 | NMX, NmX, Nmx | [1] | 350 |
| $00:8589 | NMX, NmX, Nmx | [2] | 350 |
| $80:C3C0 | NMX, NmX | [2] | 30 |
| $80:FBC3 | NMX, NmX | [1] | 448 |
| $82:8151 | NMX, NmX | [1] | 7,293 |
| $82:8152 | NMX, NmX | [2] | 7,293 |
| $82:8160 | NMX, NmX | [1] | 7,293 |
| $82:B183 | NMX, NmX | [1] | 6 |
| $82:B184 | NMX, NmX | [1] | 6 |
| $82:B185 | NMX, NmX | [1] | 6 |
| $82:B186 | NMX, NmX | [2] | 6 |
| $82:B1AD | NMX, NmX | [1] | 6 |
| $82:B1DB | NMX, NmX | [1] | 11 |
| $82:B1DC | NMX, NmX | [1] | 11 |
| $82:B1DD | NMX, NmX | [1] | 11 |
| $82:B1DE | NMX, NmX | [2] | 11 |
| $82:B20A | NMX, NmX | [1] | 11 |

## Sites outside ROM

| Address | Region | Mode | Count | First frame |
| --- | --- | --- | --- | --- |
| $00:0199 | wram | NMX | 239 | 404 |
| $00:019C | wram | NMX | 12 | 404 |
| $00:0199 | wram | NMX | 1 | 404 |

## Unknown edges (5)

Steps whose predecessor could not be decoded (outside ROM) or is not a control-flow instruction and whose target is not a vector target.

| From | Region | Decoded | To | Count |
| --- | --- | --- | --- | --- |
| $00:0199 | wram | no | $00:0199 | 227 |
| $00:0199 | wram | no | $00:019C | 12 |
| $00:019C | wram | no | $80:AD79 | 6 |
| $00:019C | wram | no | $83:96FB | 6 |
| $00:0199 | wram | no | $00:0199 | 1 |

## Limits

- Coverage is of this scenario's frames only; an unexecuted byte is unclassified, not data.
- Opcode and operand classification uses the observed M/X flags per site; a byte executed under two decodings is listed under multi-mode addresses.
- Interrupt entries are not traced instructions (R-0002 finding 7); they are recognised by the target being an NMI/IRQ vector target.
- Static references cover absolute (with the observed data bank) and long operands only.
- Per-address detail (with opcode bytes) is an ignored artifact regenerated by the command above; tracked files carry no ROM bytes.
