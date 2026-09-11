"""65816 opcode lengths and addressing modes under the M and X flags.

Written from the WDC W65C816S instruction set description (opcode matrix and
addressing-mode byte counts) for this project; no emulator table was copied.
Only the immediate forms depend on the processor state: ``#imm`` operands of
accumulator instructions are 8 bits when M=1 and 16 bits when M=0, those of
index instructions follow X. In emulation mode (E=1) the hardware forces
M=X=1, so the pre-instruction ``p`` byte alone determines the length; ``e`` is
carried in the mode for the map, not for decoding. BRK and COP carry a
signature byte, so they are two bytes long.

Addressing-mode codes (``MODES``): the byte count follows each code except
``immM`` (2/3 by M) and ``immX`` (2/3 by X).
"""

from __future__ import annotations

from typing import Final

# Addressing mode -> length (None: depends on M or X).
MODES: Final[dict[str, int | None]] = {
    "imp": 1,        # implied, accumulator, stack (PHA, RTS, XCE ...)
    "imm8": 2,       # fixed 8-bit immediate: SEP, REP, WDM, BRK/COP signature
    "immM": None,    # accumulator immediate: 2 bytes if M=1 else 3
    "immX": None,    # index immediate: 2 bytes if X=1 else 3
    "dp": 2, "dpx": 2, "dpy": 2, "idp": 2, "idpx": 2, "idpy": 2, "ildp": 2, "ildpy": 2, "sr": 2, "isry": 2,
    "rel8": 2, "rel16": 3,
    "abs": 3, "absx": 3, "absy": 3, "iabs": 3, "iabsx": 3, "ilabs": 3,
    "long": 4, "longx": 4,
    "blk": 3,        # MVN/MVP: source and destination bank bytes
}

# Opcode -> (mnemonic, addressing mode). Indexed by opcode value 0x00..0xFF.
TABLE: Final[tuple[tuple[str, str], ...]] = (
    ("BRK", "imm8"), ("ORA", "idpx"), ("COP", "imm8"), ("ORA", "sr"), ("TSB", "dp"), ("ORA", "dp"), ("ASL", "dp"), ("ORA", "ildp"),
    ("PHP", "imp"), ("ORA", "immM"), ("ASL", "imp"), ("PHD", "imp"), ("TSB", "abs"), ("ORA", "abs"), ("ASL", "abs"), ("ORA", "long"),
    ("BPL", "rel8"), ("ORA", "idpy"), ("ORA", "idp"), ("ORA", "isry"), ("TRB", "dp"), ("ORA", "dpx"), ("ASL", "dpx"), ("ORA", "ildpy"),
    ("CLC", "imp"), ("ORA", "absy"), ("INC", "imp"), ("TCS", "imp"), ("TRB", "abs"), ("ORA", "absx"), ("ASL", "absx"), ("ORA", "longx"),
    ("JSR", "abs"), ("AND", "idpx"), ("JSL", "long"), ("AND", "sr"), ("BIT", "dp"), ("AND", "dp"), ("ROL", "dp"), ("AND", "ildp"),
    ("PLP", "imp"), ("AND", "immM"), ("ROL", "imp"), ("PLD", "imp"), ("BIT", "abs"), ("AND", "abs"), ("ROL", "abs"), ("AND", "long"),
    ("BMI", "rel8"), ("AND", "idpy"), ("AND", "idp"), ("AND", "isry"), ("BIT", "dpx"), ("AND", "dpx"), ("ROL", "dpx"), ("AND", "ildpy"),
    ("SEC", "imp"), ("AND", "absy"), ("DEC", "imp"), ("TSC", "imp"), ("BIT", "absx"), ("AND", "absx"), ("ROL", "absx"), ("AND", "longx"),
    ("RTI", "imp"), ("EOR", "idpx"), ("WDM", "imm8"), ("EOR", "sr"), ("MVP", "blk"), ("EOR", "dp"), ("LSR", "dp"), ("EOR", "ildp"),
    ("PHA", "imp"), ("EOR", "immM"), ("LSR", "imp"), ("PHK", "imp"), ("JMP", "abs"), ("EOR", "abs"), ("LSR", "abs"), ("EOR", "long"),
    ("BVC", "rel8"), ("EOR", "idpy"), ("EOR", "idp"), ("EOR", "isry"), ("MVN", "blk"), ("EOR", "dpx"), ("LSR", "dpx"), ("EOR", "ildpy"),
    ("CLI", "imp"), ("EOR", "absy"), ("PHY", "imp"), ("TCD", "imp"), ("JML", "long"), ("EOR", "absx"), ("LSR", "absx"), ("EOR", "longx"),
    ("RTS", "imp"), ("ADC", "idpx"), ("PER", "rel16"), ("ADC", "sr"), ("STZ", "dp"), ("ADC", "dp"), ("ROR", "dp"), ("ADC", "ildp"),
    ("PLA", "imp"), ("ADC", "immM"), ("ROR", "imp"), ("RTL", "imp"), ("JMP", "iabs"), ("ADC", "abs"), ("ROR", "abs"), ("ADC", "long"),
    ("BVS", "rel8"), ("ADC", "idpy"), ("ADC", "idp"), ("ADC", "isry"), ("STZ", "dpx"), ("ADC", "dpx"), ("ROR", "dpx"), ("ADC", "ildpy"),
    ("SEI", "imp"), ("ADC", "absy"), ("PLY", "imp"), ("TDC", "imp"), ("JMP", "iabsx"), ("ADC", "absx"), ("ROR", "absx"), ("ADC", "longx"),
    ("BRA", "rel8"), ("STA", "idpx"), ("BRL", "rel16"), ("STA", "sr"), ("STY", "dp"), ("STA", "dp"), ("STX", "dp"), ("STA", "ildp"),
    ("DEY", "imp"), ("BIT", "immM"), ("TXA", "imp"), ("PHB", "imp"), ("STY", "abs"), ("STA", "abs"), ("STX", "abs"), ("STA", "long"),
    ("BCC", "rel8"), ("STA", "idpy"), ("STA", "idp"), ("STA", "isry"), ("STY", "dpx"), ("STA", "dpx"), ("STX", "dpy"), ("STA", "ildpy"),
    ("TYA", "imp"), ("STA", "absy"), ("TXS", "imp"), ("TXY", "imp"), ("STZ", "abs"), ("STA", "absx"), ("STZ", "absx"), ("STA", "longx"),
    ("LDY", "immX"), ("LDA", "idpx"), ("LDX", "immX"), ("LDA", "sr"), ("LDY", "dp"), ("LDA", "dp"), ("LDX", "dp"), ("LDA", "ildp"),
    ("TAY", "imp"), ("LDA", "immM"), ("TAX", "imp"), ("PLB", "imp"), ("LDY", "abs"), ("LDA", "abs"), ("LDX", "abs"), ("LDA", "long"),
    ("BCS", "rel8"), ("LDA", "idpy"), ("LDA", "idp"), ("LDA", "isry"), ("LDY", "dpx"), ("LDA", "dpx"), ("LDX", "dpy"), ("LDA", "ildpy"),
    ("CLV", "imp"), ("LDA", "absy"), ("TSX", "imp"), ("TYX", "imp"), ("LDY", "absx"), ("LDA", "absx"), ("LDX", "absy"), ("LDA", "longx"),
    ("CPY", "immX"), ("CMP", "idpx"), ("REP", "imm8"), ("CMP", "sr"), ("CPY", "dp"), ("CMP", "dp"), ("DEC", "dp"), ("CMP", "ildp"),
    ("INY", "imp"), ("CMP", "immM"), ("DEX", "imp"), ("WAI", "imp"), ("CPY", "abs"), ("CMP", "abs"), ("DEC", "abs"), ("CMP", "long"),
    ("BNE", "rel8"), ("CMP", "idpy"), ("CMP", "idp"), ("CMP", "isry"), ("PEI", "idp"), ("CMP", "dpx"), ("DEC", "dpx"), ("CMP", "ildpy"),
    ("CLD", "imp"), ("CMP", "absy"), ("PHX", "imp"), ("STP", "imp"), ("JML", "ilabs"), ("CMP", "absx"), ("DEC", "absx"), ("CMP", "longx"),
    ("CPX", "immX"), ("SBC", "idpx"), ("SEP", "imm8"), ("SBC", "sr"), ("CPX", "dp"), ("SBC", "dp"), ("INC", "dp"), ("SBC", "ildp"),
    ("INX", "imp"), ("SBC", "immM"), ("NOP", "imp"), ("XBA", "imp"), ("CPX", "abs"), ("SBC", "abs"), ("INC", "abs"), ("SBC", "long"),
    ("BEQ", "rel8"), ("SBC", "idpy"), ("SBC", "idp"), ("SBC", "isry"), ("PEA", "abs"), ("SBC", "dpx"), ("INC", "dpx"), ("SBC", "ildpy"),
    ("SED", "imp"), ("SBC", "absy"), ("PLX", "imp"), ("XCE", "imp"), ("JSR", "iabsx"), ("SBC", "absx"), ("INC", "absx"), ("SBC", "longx"),
)

assert len(TABLE) == 256

# Processor mode as carried by the coverage files: bit 2 = E, bit 1 = M, bit 0 = X.
MODE_E, MODE_M, MODE_X = 4, 2, 1
P_M, P_X = 0x20, 0x10


def mode_from_flags(p: int, e: int) -> int:
    """Pack the pre-instruction P and E registers into the 3-bit mode."""
    return (MODE_E if e else 0) | (MODE_M if p & P_M else 0) | (MODE_X if p & P_X else 0)


def mode_name(mode: int) -> str:
    return f"{'E' if mode & MODE_E else 'N'}{'m' if mode & MODE_M else 'M'}{'x' if mode & MODE_X else 'X'}"


def instruction_length(opcode: int, mode: int) -> int:
    """Bytes occupied by ``opcode`` executed with the given 3-bit mode."""
    addressing = TABLE[opcode][1]
    fixed = MODES[addressing]
    if fixed is not None:
        return fixed
    if addressing == "immM":
        return 2 if mode & MODE_M else 3
    return 2 if mode & MODE_X else 3


# Control-flow classification of the instruction that *precedes* a
# non-sequential trace step. "interrupt entry" and "unknown" are decided by
# the caller from the target (vector) and the predecessor's location.
FLOW_KINDS: Final[dict[int, str]] = {
    0x20: "JSR", 0xFC: "JSR", 0x22: "JSL",
    0x4C: "JMP", 0x6C: "JMP", 0x7C: "JMP", 0x5C: "JML", 0xDC: "JML",
    0x60: "RTS", 0x6B: "RTL", 0x40: "RTI", 0x00: "BRK", 0x02: "COP",
    0x10: "branch", 0x30: "branch", 0x50: "branch", 0x70: "branch", 0x80: "branch", 0x90: "branch",
    0xB0: "branch", 0xD0: "branch", 0xF0: "branch", 0x82: "branch",
}

# Opcodes whose operand is a code address in the program bank (JSR/JMP abs) or
# a full 24-bit code address (JSL/JML long); other ``abs``/``long`` operands
# are data references in the data bank (abs) or the operand's own bank (long).
CODE_ABS: Final[frozenset[int]] = frozenset({0x20, 0x4C})
CODE_LONG: Final[frozenset[int]] = frozenset({0x22, 0x5C})


def sequential_successor(pc: int, length: int) -> int:
    """The address after an instruction: the program counter wraps within its bank."""
    return (pc & 0xFF0000) | ((pc + length) & 0xFFFF)


def static_reference(opcode: int, operand: bytes, pc: int, data_bank: int) -> tuple[str, int] | None:
    """The address an executed instruction names directly in its operand, if any.

    Returns ``(kind, address)`` with kind ``code`` for JSR/JMP/JSL/JML targets,
    ``data`` for absolute and long data operands; indexed, indirect, direct
    page, stack-relative and relative forms are not resolved (M1-01 scope).
    """
    addressing = TABLE[opcode][1]
    if addressing == "abs":
        target = int.from_bytes(operand[:2], "little")
        if opcode in CODE_ABS:
            return "code", (pc & 0xFF0000) | target
        if opcode == 0xF4:  # PEA pushes the operand value; it names no address
            return None
        return "data", (data_bank << 16) | target
    if addressing == "long":
        target = int.from_bytes(operand[:3], "little")
        return ("code" if opcode in CODE_LONG else "data"), target
    return None
