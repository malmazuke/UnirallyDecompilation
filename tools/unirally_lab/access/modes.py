"""65816 effective addresses, access kinds, widths and stored values per opcode.

Written for this project from the WDC W65C816S data sheet's description of
the addressing modes (effective-address formation, direct-page and stack
behaviour in emulation mode, block moves). The emulation-mode corner cases
were checked against the pinned core's implementation
(``processor/wdc65816/memory.cpp`` and ``instructions-*.cpp`` of bsnes
``7d5aa1e656b9``), which is the reference this record describes; no table
was copied from it. On this ROM only three instructions ever execute in
emulation mode (R-0006 finding 6), so those cases are exercised by the
ROM-free tests only.

Rules (``regs`` are the pre-instruction registers the trace entry carries):

- Direct page ``dp``, ``dp,X``, ``dp,Y`` and the pointer of ``(dp)``,
  ``(dp),Y``: address ``(D + dp [+ index]) & $FFFF`` in bank 0; in emulation
  mode with ``DL = 0`` the sum wraps within the direct page
  (``D | ((dp + index) & $FF)``) and so does every further byte of the
  operand. The pointer of ``(dp,X)`` in emulation mode with ``DL != 0`` keeps
  the high byte of ``D + dp`` and wraps the low byte. The three pointer bytes
  of ``[dp]`` and ``[dp],Y`` and the operand of ``PEI`` never page-wrap.
- Absolute ``abs``, ``abs,X``, ``abs,Y``: ``(DBR << 16) + abs [+ index]``
  modulo 2^24, so indexed and multi-byte operands cross into the next bank.
  Long ``long``, ``long,X``: the 24-bit operand plus the index modulo 2^24.
- Stack relative ``sr`` and the pointer of ``(sr),Y``: ``(S + sr) & $FFFF``
  in bank 0, no page wrap.
- Pushes write at ``S`` downwards, pulls read from ``S + 1`` upwards. In
  emulation mode the 6502-era forms (PHA PHX PHY PHP PHB PHK PLA PLX PLY PLP
  JSR abs RTS RTI BRK COP) stay within page 1 (the low byte of S wraps);
  the 65816-only forms (PHD PLD PLB PEA PEI PER JSL JSR (abs,X) RTL) do not.
  A multi-byte push is one access at its lowest address (little-endian:
  the low byte lands lowest), a pull likewise.
- Block moves MVN/MVP: the first operand byte is the destination bank, the
  second the source bank; every traced re-execution moves one byte from
  ``src:X`` to ``dst:Y``.
- Widths: accumulator operands follow M, index operands follow X, both
  forced to 8 bits in emulation mode; pointer fetches are 16 or 24 bits.
- Stored values come from the register named by the instruction (A, X, Y,
  P, DBR, PB, D, or the operand for PEA/PER, the return address for calls),
  masked to the width. Loaded values may be taken from the *next* trace
  entry's register (LDA/LDX/LDY, pulls, indirect jumps and returns); they
  are ``None`` when no next entry is available.

An access is ``(kind, address, width, value, wrap)``; ``wrap`` says how the
bytes after the first are addressed: 0 linear in the 24-bit space, 1 wrapping
within the 64 KiB bank of the address, 2 wrapping within its 256-byte page.
Indirect forms whose pointer content is not in the registers are returned as
*deferred* items ``(pointer_address, pointer_width, pointer_wrap, add_index,
use_dbr, kind, width, value)``; ``resolve`` turns a deferred item and its
pointer value into the access.
"""

from __future__ import annotations

from typing import Final

from ..coverage.opcodes import TABLE

# Access kinds.
READ, WRITE, RMW, PUSH, PULL, BLOCK_READ, BLOCK_WRITE = range(7)
KIND_NAMES: Final = ("read", "write", "rmw", "push", "pull", "block_read", "block_write")
KIND_BY_NAME: Final = {n: i for i, n in enumerate(KIND_NAMES)}

# Wrap rules for the bytes after the first.
WRAP_LINEAR, WRAP_BANK, WRAP_PAGE = 0, 1, 2

# Addressing modes (names as in coverage.opcodes.MODES) -> index for compact keys.
ADDRESSING: Final = ("imp", "imm8", "immM", "immX", "dp", "dpx", "dpy", "idp", "idpx", "idpy", "ildp", "ildpy", "sr", "isry",
                     "rel8", "rel16", "abs", "absx", "absy", "iabs", "iabsx", "ilabs", "long", "longx", "blk")
ADDRESSING_INDEX: Final = {n: i for i, n in enumerate(ADDRESSING)}
INDIRECT_MODES: Final = frozenset({"idp", "idpx", "idpy", "ildp", "ildpy", "isry"})

# Mnemonic classes. ``reg`` names the register whose value is stored (writes,
# pushes) or loaded (reads with a next-entry value).
_LOADS: Final = {"LDA": "a", "LDX": "x", "LDY": "y"}
_READS_M: Final = frozenset({"ADC", "AND", "BIT", "CMP", "EOR", "ORA", "SBC"})
_READS_X: Final = frozenset({"CPX", "CPY"})
_STORES: Final = {"STA": "a", "STX": "x", "STY": "y", "STZ": "zero"}
_RMW: Final = frozenset({"ASL", "DEC", "INC", "LSR", "ROL", "ROR", "TSB", "TRB"})
_INDEX_WIDTH: Final = frozenset({"LDX", "LDY", "STX", "STY", "CPX", "CPY"})
# Pushes: mnemonic -> (register, width in bytes or "m"/"x", page-1 wrap in emulation mode)
_PUSHES: Final = {"PHA": ("a", "m", True), "PHX": ("x", "x", True), "PHY": ("y", "x", True), "PHP": ("p", 1, True),
                  "PHB": ("b", 1, True), "PHK": ("pb", 1, True), "PHD": ("d", 2, False)}
_PULLS: Final = {"PLA": ("a", "m", True), "PLX": ("x", "x", True), "PLY": ("y", "x", True), "PLP": ("p", 1, True),
                 "PLB": ("b", 1, False), "PLD": ("d", 2, False)}


def _width(flag8: bool) -> int:
    return 1 if flag8 else 2


def _mask(value: int, width: int) -> int:
    return value & ((1 << (8 * width)) - 1)


def _direct(d: int, offset: int, e: int) -> tuple[int, int]:
    """Direct-page address and wrap rule for ``D + offset``."""
    if e and (d & 0xFF) == 0:
        return d | (offset & 0xFF), WRAP_PAGE
    return (d + offset) & 0xFFFF, WRAP_BANK


def _push_address(s: int, n: int, e: int, page: bool) -> tuple[int, int]:
    if e and page:
        return (s & 0xFF00) | ((s - n + 1) & 0xFF), WRAP_PAGE
    return (s - n + 1) & 0xFFFF, WRAP_BANK


def _pull_address(s: int, e: int, page: bool) -> tuple[int, int]:
    if e and page:
        return (s & 0xFF00) | ((s + 1) & 0xFF), WRAP_PAGE
    return (s + 1) & 0xFFFF, WRAP_BANK


def byte_addresses(address: int, width: int, wrap: int) -> list[int]:
    """The 24-bit addresses of every byte of an access."""
    if wrap == WRAP_LINEAR:
        return [(address + k) & 0xFFFFFF for k in range(width)]
    if wrap == WRAP_BANK:
        return [(address & 0xFF0000) | ((address + k) & 0xFFFF) for k in range(width)]
    return [(address & 0xFFFF00) | ((address + k) & 0xFF) for k in range(width)]


def decode(opcode: int, operand: bytes, pc: int, a: int, x: int, y: int, s: int, d: int, b: int, p: int, e: int,
           nxt: tuple[int, int, int, int, int, int, int, int, int] | None = None) -> tuple[list[tuple], list[tuple]]:
    """Accesses and deferred indirect items of one executed instruction.

    ``nxt`` is the next trace entry as ``(pc, a, x, y, s, d, b, p, e)`` or None.
    Returns ``(accesses, deferred)``; see the module docstring for the shapes.
    """
    mnemonic, addressing = TABLE[opcode]
    m8 = bool(e or (p & 0x20))
    x8 = bool(e or (p & 0x10))
    if x8:
        x &= 0xFF
        y &= 0xFF
    accesses: list[tuple] = []
    deferred: list[tuple] = []

    # ------------------------------------------------ data operand forms
    kind = None
    width = 0
    value = None
    if mnemonic in _LOADS:
        kind, width = READ, _width(x8 if mnemonic in _INDEX_WIDTH else m8)
        if nxt is not None:
            value = _mask((nxt[1], nxt[2], nxt[3])[("a", "x", "y").index(_LOADS[mnemonic])], width)
    elif mnemonic in _READS_M:
        kind, width = READ, _width(m8)
    elif mnemonic in _READS_X:
        kind, width = READ, _width(x8)
    elif mnemonic in _STORES:
        kind, width = WRITE, _width(x8 if mnemonic in _INDEX_WIDTH else m8)
        reg = _STORES[mnemonic]
        value = 0 if reg == "zero" else _mask({"a": a, "x": x, "y": y}[reg], width)
    elif mnemonic in _RMW:
        kind, width = RMW, _width(m8)

    if kind is not None and addressing not in ("imp", "immM", "immX", "imm8"):
        if addressing == "dp":
            addr, wrap = _direct(d, operand[0], e)
            accesses.append((kind, addr, width, value, wrap))
        elif addressing == "dpx":
            addr, wrap = _direct(d, operand[0] + x, e)
            accesses.append((kind, addr, width, value, wrap))
        elif addressing == "dpy":
            addr, wrap = _direct(d, operand[0] + y, e)
            accesses.append((kind, addr, width, value, wrap))
        elif addressing == "abs":
            accesses.append((kind, ((b << 16) + int.from_bytes(operand[:2], "little")) & 0xFFFFFF, width, value, WRAP_LINEAR))
        elif addressing == "absx":
            accesses.append((kind, ((b << 16) + int.from_bytes(operand[:2], "little") + x) & 0xFFFFFF, width, value, WRAP_LINEAR))
        elif addressing == "absy":
            accesses.append((kind, ((b << 16) + int.from_bytes(operand[:2], "little") + y) & 0xFFFFFF, width, value, WRAP_LINEAR))
        elif addressing == "long":
            accesses.append((kind, int.from_bytes(operand[:3], "little"), width, value, WRAP_LINEAR))
        elif addressing == "longx":
            accesses.append((kind, (int.from_bytes(operand[:3], "little") + x) & 0xFFFFFF, width, value, WRAP_LINEAR))
        elif addressing == "sr":
            accesses.append((kind, (s + operand[0]) & 0xFFFF, width, value, WRAP_BANK))
        elif addressing == "idp":
            paddr, pwrap = _direct(d, operand[0], e)
            accesses.append((READ, paddr, 2, None, pwrap))
            deferred.append((paddr, 2, pwrap, 0, True, kind, width, value))
        elif addressing == "idpx":
            if e and (d & 0xFF):
                base = (d + operand[0]) & 0xFFFF
                paddr, pwrap = (base & 0xFF00) | ((base + x) & 0xFF), WRAP_PAGE
            else:
                paddr, pwrap = _direct(d, operand[0] + x, e)
            accesses.append((READ, paddr, 2, None, pwrap))
            deferred.append((paddr, 2, pwrap, 0, True, kind, width, value))
        elif addressing == "idpy":
            paddr, pwrap = _direct(d, operand[0], e)
            accesses.append((READ, paddr, 2, None, pwrap))
            deferred.append((paddr, 2, pwrap, y, True, kind, width, value))
        elif addressing == "ildp":
            paddr = (d + operand[0]) & 0xFFFF
            accesses.append((READ, paddr, 3, None, WRAP_BANK))
            deferred.append((paddr, 3, WRAP_BANK, 0, False, kind, width, value))
        elif addressing == "ildpy":
            paddr = (d + operand[0]) & 0xFFFF
            accesses.append((READ, paddr, 3, None, WRAP_BANK))
            deferred.append((paddr, 3, WRAP_BANK, y, False, kind, width, value))
        elif addressing == "isry":
            paddr = (s + operand[0]) & 0xFFFF
            accesses.append((READ, paddr, 2, None, WRAP_BANK))
            deferred.append((paddr, 2, WRAP_BANK, y, True, kind, width, value))
        return accesses, deferred

    # ------------------------------------------------ stack forms
    if mnemonic in _PUSHES:
        reg, w, page = _PUSHES[mnemonic]
        width = _width(m8) if w == "m" else _width(x8) if w == "x" else w
        value = _mask({"a": a, "x": x, "y": y, "p": p, "b": b, "pb": pc >> 16, "d": d}[reg], width)
        addr, wrap = _push_address(s, width, e, page)
        accesses.append((PUSH, addr, width, value, wrap))
    elif mnemonic in _PULLS:
        reg, w, page = _PULLS[mnemonic]
        width = _width(m8) if w == "m" else _width(x8) if w == "x" else w
        if nxt is not None:
            value = _mask({"a": nxt[1], "x": nxt[2], "y": nxt[3], "p": nxt[7], "b": nxt[6], "d": nxt[5]}[reg], width)
        addr, wrap = _pull_address(s, e, page)
        accesses.append((PULL, addr, width, value, wrap))
    elif mnemonic == "PEA":
        addr, wrap = _push_address(s, 2, e, False)
        accesses.append((PUSH, addr, 2, int.from_bytes(operand[:2], "little"), wrap))
    elif mnemonic == "PER":
        rel = int.from_bytes(operand[:2], "little", signed=True)
        addr, wrap = _push_address(s, 2, e, False)
        accesses.append((PUSH, addr, 2, (pc + 3 + rel) & 0xFFFF, wrap))
    elif mnemonic == "PEI":
        accesses.append((READ, (d + operand[0]) & 0xFFFF, 2, None, WRAP_BANK))
        addr, wrap = _push_address(s, 2, e, False)
        accesses.append((PUSH, addr, 2, None, wrap))
    elif mnemonic == "JSR" and addressing == "abs":
        addr, wrap = _push_address(s, 2, e, True)
        accesses.append((PUSH, addr, 2, (pc + 2) & 0xFFFF, wrap))
    elif mnemonic == "JSR":  # (abs,X): the return address is pushed before the pointer is read
        addr, wrap = _push_address(s, 2, e, False)
        accesses.append((PUSH, addr, 2, (pc + 2) & 0xFFFF, wrap))
        ptr = (pc & 0xFF0000) | ((int.from_bytes(operand[:2], "little") + x) & 0xFFFF)
        accesses.append((READ, ptr, 2, None if nxt is None else nxt[0] & 0xFFFF, WRAP_BANK))
    elif mnemonic == "JSL":
        addr, wrap = _push_address(s, 3, e, False)
        accesses.append((PUSH, addr, 3, ((pc >> 16) << 16) | ((pc + 3) & 0xFFFF), wrap))
    elif mnemonic == "RTS":
        addr, wrap = _pull_address(s, e, True)
        accesses.append((PULL, addr, 2, None if nxt is None else (nxt[0] - 1) & 0xFFFF, wrap))
    elif mnemonic == "RTL":
        addr, wrap = _pull_address(s, e, False)
        accesses.append((PULL, addr, 3, None if nxt is None else (nxt[0] & 0xFF0000) | ((nxt[0] - 1) & 0xFFFF), wrap))
    elif mnemonic == "RTI":
        addr, wrap = _pull_address(s, e, True)
        accesses.append((PULL, addr, 1, None if nxt is None else nxt[7], wrap))
        addr2, wrap2 = _pull_address(s + 1, e, True)
        if e:
            accesses.append((PULL, addr2, 2, None if nxt is None else nxt[0] & 0xFFFF, wrap2))
        else:
            accesses.append((PULL, addr2, 3, None if nxt is None else nxt[0] & 0xFFFFFF, wrap2))
    elif mnemonic in ("BRK", "COP"):
        if e:
            addr, wrap = _push_address(s, 2, e, True)
            accesses.append((PUSH, addr, 2, (pc + 2) & 0xFFFF, wrap))
            addr2, wrap2 = _push_address(s - 2, 1, e, True)
            accesses.append((PUSH, addr2, 1, p & 0xFF, wrap2))
        else:
            addr, wrap = _push_address(s, 3, e, True)
            accesses.append((PUSH, addr, 3, ((pc >> 16) << 16) | ((pc + 2) & 0xFFFF), wrap))
            addr2, wrap2 = _push_address(s - 3, 1, e, True)
            accesses.append((PUSH, addr2, 1, p & 0xFF, wrap2))
    # ------------------------------------------------ indirect jumps
    elif addressing == "iabs":  # JMP (abs): pointer in bank 0
        accesses.append((READ, int.from_bytes(operand[:2], "little"), 2, None if nxt is None else nxt[0] & 0xFFFF, WRAP_BANK))
    elif addressing == "ilabs":  # JML [abs]: 24-bit pointer in bank 0
        accesses.append((READ, int.from_bytes(operand[:2], "little"), 3, None if nxt is None else nxt[0] & 0xFFFFFF, WRAP_BANK))
    elif addressing == "iabsx":  # JMP (abs,X): pointer in the program bank
        ptr = (pc & 0xFF0000) | ((int.from_bytes(operand[:2], "little") + x) & 0xFFFF)
        accesses.append((READ, ptr, 2, None if nxt is None else nxt[0] & 0xFFFF, WRAP_BANK))
    # ------------------------------------------------ block moves
    elif addressing == "blk":
        dst, src = operand[0], operand[1]
        accesses.append((BLOCK_READ, (src << 16) | x, 1, None, WRAP_BANK))
        accesses.append((BLOCK_WRITE, (dst << 16) | y, 1, None, WRAP_BANK))
    return accesses, deferred


def resolve_with_bank(item: tuple, pointer: int, dbr: int) -> tuple:
    """Effective access of a deferred item: ``(kind, address, width, value, wrap)``."""
    _paddr, pwidth, _pwrap, index, use_dbr, kind, width, value = item[:8]
    if use_dbr:
        address = ((dbr << 16) + (pointer & 0xFFFF) + index) & 0xFFFFFF
    else:
        address = ((pointer & 0xFFFFFF) + index) & 0xFFFFFF
    return kind, address, width, value, WRAP_LINEAR


def kind_name(kind: int) -> str:
    return KIND_NAMES[kind]
