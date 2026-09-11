"""Register-level port of the decompressor the ROM runs at ``$81:B8E2``.

The routine unpacks assets whose directory entry carries the $80 flag (the
directory at ``[$4F]``, default ``$82:B332``, 5-byte entries: bank|flag,
address, length). Its input starts with an ``RNC\\x01`` header (Rob Northen
ProPack, method 1: 4-byte magic, big-endian unpacked and packed lengths, two
CRCs, a leeway byte and the chunk count); the ROM uses only the chunk count at
offset 0x11 and starts the bit stream at offset 0x12.

The port mirrors the original's state (``$82``/``$84`` source pointer and
bank, ``$86`` destination offset, ``$8F`` 16-bit window, ``$91`` next word,
``$93`` bits left in it, the code tables at ``$0200``) instruction group by
instruction group so that its arithmetic, bank wrapping and bit order are the
original's, not a re-derivation from the format description:

- ``$BB60`` peeks the little-endian word at the source pointer (straddling a
  bank end as $bank:$FFFF/$bank+1:$8000);
- ``$BA6B`` returns the low ``n`` bits of the window and shifts ``n`` bits in
  from the next word (LSB first), refilling the next word from the stream
  (``$82 += 2`` with the LoROM wrap) whenever it is exhausted;
- ``$BACD`` reads a 5-bit symbol count and 4-bit code lengths and assigns
  canonical codes (increment ``$8000 >> (L-1)`` per symbol of length ``L``),
  storing each as (mask, bit-reversed code) pairs at the table base and
  (length << 8 | symbol) 0x40 bytes above;
- ``$BA17`` scans the pairs in symbol order for ``window & mask == code``,
  consumes the code and returns the symbol, or for symbols >= 2 the value
  ``(1 << (s-1)) | next (s-1) bits`` (the table at ``$81:BA4B``);
- ``$B996`` copies a literal run of bytes from the source pointer in chunks
  that stop at the bank end, then re-synchronises the window (keep its low
  ``$93`` bits, refill the rest from the word now at the pointer);
- ``$B94B`` copies ``length + 2`` bytes from ``distance + 1`` bytes back in
  the output (distance 0 repeats the previous byte);
- per chunk: three tables (bases ``$20``, ``$A0``, ``$120``), a 16-bit
  command count, then literal, (copy, literal) x (count - 1).

The code tables start zeroed here; in the original they hold whatever work
RAM ``$0200``-``$03FF`` held before, which only matters if a scan ran past the
valid pairs (a complete prefix code never does).
"""

from __future__ import annotations

from typing import Callable

MASK = tuple((1 << k) - 1 for k in range(17))      # $81:BAAB
BASE = tuple(1 << k for k in range(16))              # $81:BA4B
HEADER_LENGTH = 0x12

Reader = Callable[[int, int], int]


def lorom_reader(rom: bytes) -> Reader:
    """Byte at ``bank:offset`` under the LoROM rule (offsets below $8000 mirror the upper half)."""
    size = len(rom)

    def read(bank: int, off: int) -> int:
        return rom[((((bank & 0x7F) << 15) | (off & 0x7FFF)) % size)]
    return read


def flat_reader(data: bytes, bank: int = 0, base: int = 0x8000) -> Reader:
    """Reader over a flat buffer placed at ``bank:base`` (for ROM-free tests); bytes past the end read 0."""
    def read(b: int, off: int) -> int:
        if b < bank:
            return 0
        i = ((b - bank) << 15) + (off - base)
        return data[i] if 0 <= i < len(data) else 0
    return read


def parse_header(read: Reader, bank: int, addr: int) -> dict:
    hdr = bytes(read(bank, (addr + k) & 0xFFFF) for k in range(HEADER_LENGTH))
    return {
        "magic": hdr[:3].decode("latin-1"), "method": hdr[3],
        "unpacked_length": int.from_bytes(hdr[4:8], "big"), "packed_length": int.from_bytes(hdr[8:12], "big"),
        "unpacked_crc": int.from_bytes(hdr[12:14], "big"), "packed_crc": int.from_bytes(hdr[14:16], "big"),
        "leeway": hdr[16], "chunks": hdr[17],
    }


class Decompressor:
    def __init__(self, read: Reader, src_bank: int, src_addr: int, table: bytes | None = None) -> None:
        self.read = read
        self.r82 = src_addr & 0xFFFF
        self.r84 = src_bank
        self.tab = bytearray(0x200) if table is None else bytearray(table)
        self.out = bytearray(0x10000)
        self.r86 = 0
        self.r8F = 0
        self.r91 = 0
        self.r93 = 0
        self.max_out = 0

    # ---- source pointer ($82/$84)
    def adv(self, n: int) -> None:
        """``$82 += n`` with the routine's wrap: on carry ``ORA #$8000`` and ``INC $84``."""
        a = self.r82 + n
        if a >= 0x10000:
            a = (a & 0xFFFF) | 0x8000
            self.r84 += 1
        self.r82 = a

    def peek16(self) -> int:  # $BB60
        lo = self.read(self.r84, self.r82)
        hi = self.read(self.r84 + 1, 0x8000) if self.r82 == 0xFFFF else self.read(self.r84, self.r82 + 1)
        return lo | (hi << 8)

    # ---- table at $0200 via [$88],Y
    def tget(self, y: int) -> int:
        return self.tab[y] | (self.tab[y + 1] << 8)

    def tput(self, y: int, v: int) -> None:
        self.tab[y] = v & 0xFF
        self.tab[y + 1] = (v >> 8) & 0xFF

    # ---- bit reader ($BA6B)
    def getbits(self, n: int) -> int:
        if n == 0:
            raise ValueError("the original never requests zero bits")
        y = n
        result = self.r8F & MASK[n]
        a = self.r91
        x = self.r93
        if x == 0:
            self.adv(2)
            a = self.peek16()
            x = 16
        while True:
            carry = a & 1
            a >>= 1
            self.r8F = (self.r8F >> 1) | (carry << 15)
            y -= 1
            if y == 0:
                x -= 1
                self.r93 = x
                self.r91 = a
                return result
            x -= 1
            if x == 0:
                self.adv(2)
                a = self.peek16()
                x = 16

    # ---- code table ($BACD)
    def build(self, t: int) -> None:
        a1 = t
        n = self.getbits(5)
        if n == 0:
            return
        for i in range(n):
            self.tput(2 * i, self.getbits(4))
        r97 = 0
        r99 = 0x8000
        for length in range(1, 17):
            y = 0
            for _ in range(n):
                if self.tget(y) == length:
                    self.tput(a1, MASK[length])
                    a1 += 2
                    a = r97
                    r9d = r97
                    for _ in range(length):
                        carry = (r9d >> 15) & 1
                        r9d = (r9d << 1) & 0xFFFF
                        a = (a >> 1) | (carry << 15)
                    a >>= 16 - length
                    self.tput(a1, a)
                    a1 += 2
                    self.tput(a1 + 0x3C, (length << 8) | (y >> 1))
                    r97 = (r97 + r99) & 0xFFFF
                y += 2
            r99 >>= 1

    # ---- symbol decode ($BA17)
    def decode(self, t: int) -> int:
        x = self.r8F
        y = t
        while (x & self.tget(y)) != self.tget(y + 2):
            y += 4
            if y >= 0x200:
                raise ValueError("no code matches the window; the original would scan into stale work RAM")
        info = self.tget(y + 2 + 0x3E)
        length = info >> 8
        symbol = info & 0xFF
        self.getbits(length)
        if symbol < 2:
            return symbol
        return self.getbits(symbol - 1) | BASE[symbol - 1]

    # ---- output
    def wr(self, off: int, v: int) -> None:
        off &= 0xFFFF
        self.out[off] = v
        if off + 1 > self.max_out:
            self.max_out = off + 1

    def run(self) -> bytes:
        self.adv(0x11)
        chunks = self.read(self.r84, self.r82)
        self.adv(1)
        self.r8F = self.peek16()
        self.r93 = 0
        self.getbits(2)
        while True:
            self.build(0x20)
            self.build(0xA0)
            self.build(0x120)
            commands = self.getbits(16)
            self.literal()
            while True:
                commands = (commands - 1) & 0xFFFF
                if commands == 0:
                    break
                self.copy()
                self.literal()
            chunks = (chunks - 1) & 0xFF
            if chunks == 0:
                return bytes(self.out[:self.max_out])

    def copy(self) -> None:  # $B94B
        distance = self.decode(0xA0)
        src = (self.r86 - distance - 1) & 0xFFFF
        a = (self.decode(0x120) + 2) & 0xFFFF
        odd = a & 1
        words = a >> 1
        y = 0
        if distance == 0:
            b = self.out[src]
            for _ in range(words):
                self.wr(self.r86 + y, b)
                self.wr(self.r86 + y + 1, b)
                y += 2
        else:
            for _ in range(words):
                self.wr(self.r86 + y, self.out[(src + y) & 0xFFFF])
                self.wr(self.r86 + y + 1, self.out[(src + y + 1) & 0xFFFF])
                y += 2
        if odd:
            self.wr(self.r86 + y, self.out[(src + y) & 0xFFFF])
            y += 1
        self.r86 = (self.r86 + y) & 0xFFFF

    def literal(self) -> None:  # $B996
        remaining = self.decode(0x20)
        if remaining == 0:
            return
        while True:
            a = (0x10000 - self.r82) & 0xFFFF
            if not a < remaining:
                a = remaining
            odd = a & 1
            words = a >> 1
            y = 0
            for _ in range(words):
                self.wr(self.r86 + y, self.read(self.r84, self.r82 + y))
                self.wr(self.r86 + y + 1, self.read(self.r84, self.r82 + y + 1))
                y += 2
            if odd:
                self.wr(self.r86 + y, self.read(self.r84, self.r82 + y))
                y += 1
            self.adv(y)
            self.r86 = (self.r86 + y) & 0xFFFF
            remaining = (remaining - y) & 0xFFFF
            if remaining == 0:
                break
        # $B9E6: re-synchronise the window after the raw bytes
        self.r91 = 0
        a = self.peek16()
        for _ in range(self.r93):
            carry = (a >> 15) & 1
            a = (a << 1) & 0xFFFF
            self.r91 = ((self.r91 << 1) | carry) & 0xFFFF
        self.r8F = (MASK[self.r93] & self.r8F) | a


def decompress(read: Reader, bank: int, addr: int) -> tuple[bytes, tuple[int, int]]:
    """Unpack the asset at ``bank:addr``; returns the bytes and the source pointer after the last word read."""
    d = Decompressor(read, bank, addr)
    out = d.run()
    return out, (d.r84, d.r82)
