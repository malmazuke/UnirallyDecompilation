"""Provenance inventory from an access record (M1-02 schema 1): every DMA
trigger with its channel parameters and, when the record watched the PPU
address ports, the B-bus destination in effect; every block move through the
work RAM routine when the record watched its pc; the port-written VRAM and
CGRAM bytes when the data ports were watched.

Pairing rule: a DMA started at (frame, seq) uses the last watched write to
``$2116``/``$2117`` (VMADD), ``$2115`` (VMAIN), ``$2121`` (CGADD) or
``$2102``/``$2103`` (OAMADD) with a smaller sequence number in the same
frame; without such a write in the frame the destination is ``None``. Watches
are matched on the register offset in any bank mirror ($00-$3F, $80-$BF).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

BBUS_NAMES = {0x04: "OAMDATA", 0x18: "VMDATAL", 0x19: "VMDATAH", 0x22: "CGDATA", 0x80: "WMDATA"}
LOG_FIELDS = ("seq", "pc", "kind", "address", "width", "value")


def rom_file_offset(address: int, size: int = 0x200000) -> int | None:
    bank = address >> 16
    off = address & 0xFFFF
    if off >= 0x8000 and (bank <= 0x6F or 0x80 <= bank <= 0xEF):
        return (((bank & 0x7F) << 15) | (off & 0x7FFF)) % size
    return None


def _is_wram(address: int) -> bool:
    bank = address >> 16
    off = address & 0xFFFF
    return bank in (0x7E, 0x7F) or (off < 0x2000 and (bank <= 0x3F or 0x80 <= bank <= 0xBF))


def _register_writes(doc: dict[str, Any], offsets: set[int]) -> dict[int, list[tuple[int, int, int, int]]]:
    """Per frame: sorted (seq, register offset, width, value) of watched writes to the given register offsets."""
    out: dict[int, list[tuple[int, int, int, int]]] = defaultdict(list)
    for key, frames in doc.get("watch_addresses", {}).items():
        a = int(key)
        bank = a >> 16
        off = a & 0xFFFF
        if off not in offsets or not (bank <= 0x3F or 0x80 <= bank <= 0xBF):
            continue
        for f, per in frames.items():
            for seq, _pc, _kind, address, width, value in per.get("w", []):
                if value is None:
                    continue
                out[int(f)].append((seq, address & 0xFFFF, width, value))
    for f in out:
        out[f].sort()
    return out


class PortState:
    """Track VMADD/VMAIN/CGADD/OAMADD from watched writes in sequence order."""

    def __init__(self) -> None:
        self.vmadd: int | None = None
        self.vmain: int | None = None
        self.cgadd: int | None = None
        self.oamadd: int | None = None

    def apply(self, off: int, width: int, value: int) -> None:
        if off == 0x2116:
            self.vmadd = value & 0xFFFF if width == 2 else ((self.vmadd or 0) & 0xFF00) | (value & 0xFF)
        elif off == 0x2117:
            self.vmadd = ((self.vmadd or 0) & 0x00FF) | ((value & 0xFF) << 8)
        elif off == 0x2115:
            self.vmain = value & 0xFF
        elif off == 0x2121:
            self.cgadd = value & 0xFF
        elif off == 0x2102:
            self.oamadd = value & 0x1FF if width == 2 else ((self.oamadd or 0) & 0x100) | (value & 0xFF)
        elif off == 0x2103:
            self.oamadd = ((self.oamadd or 0) & 0xFF) | ((value & 1) << 8)


def dma_inventory(doc: dict[str, Any], from_frame: int | None = None, to_frame: int | None = None) -> list[dict[str, Any]]:
    """One row per (MDMAEN store, enabled channel) with the destination in effect when it was started."""
    writes = _register_writes(doc, {0x2115, 0x2116, 0x2117, 0x2121, 0x2102, 0x2103})
    rows = []
    for frame, seq, pc, reg, value, channels in doc["dma_log"]:
        if reg != "MDMAEN":
            continue
        if (from_frame is not None and frame < from_frame) or (to_frame is not None and frame > to_frame):
            continue
        st = PortState()
        for s, off, width, v in writes.get(frame, []):
            if s > seq:
                break
            st.apply(off, width, v)
        for c, r in channels.items():
            dmap = r["DMAP"]
            size = r["DAS"] or 0x10000
            a = r["A1T"]
            bb = 0x2100 | r["BBAD"]
            dest: dict[str, Any] = {"b_bus": bb, "b_bus_name": BBUS_NAMES.get(r["BBAD"], "$21%02X" % r["BBAD"])}
            if r["BBAD"] in (0x18, 0x19):
                dest.update({"vmadd": st.vmadd, "vmain": st.vmain})
            elif r["BBAD"] == 0x22:
                dest.update({"cgadd": st.cgadd})
            elif r["BBAD"] == 0x04:
                dest.update({"oamadd": st.oamadd})
            rows.append({
                "frame": frame, "seq": seq, "pc": pc, "channel": int(c), "dmap": dmap,
                "direction": "B->A" if dmap & 0x80 else "A->B", "transfer_mode": dmap & 7, "fixed": bool(dmap & 8), "decrement": bool(dmap & 0x10),
                "a_bus": a, "a_bus_bank": a >> 16, "a_bus_address": a & 0xFFFF, "a_bus_region": "wram" if _is_wram(a) else ("rom" if rom_file_offset(a) is not None else "other"),
                "rom_file_offset": rom_file_offset(a), "size": size, **dest,
            })
    return rows


def block_moves(doc: dict[str, Any], pc: int = 0x000199) -> list[dict[str, Any]]:
    """Transfers through the work RAM block-move site from its watched register log.

    Consecutive executions with A decreasing by one belong to one MVN/MVP; the first
    entry's A is the byte count minus one, its X/Y the source/destination offsets, and
    the second entry's DBR (set by the instruction itself) the destination bank. The
    source bank comes from the record's resolved block-read keys at that pc."""
    log = doc.get("watch_pcs", {}).get(str(pc))
    if not log:
        return []
    src_banks: dict[int, set[int]] = defaultdict(set)
    kinds = doc["kind_names"]
    for row in doc["accesses"]:
        if row[0] == pc and kinds[row[3]] == "block_read":
            src_banks[row[6] & 0xFFFF].add(row[6] >> 16)
    out: list[dict[str, Any]] = []
    cur: dict[str, Any] | None = None
    prev_a = None
    for frame, a, x, y, _s, _d, b, _p, _e in log:
        if cur is not None and cur["frame"] == frame and prev_a not in (None, 0) and a == prev_a - 1:
            cur["length"] += 1
            if cur["destination_bank"] is None:
                cur["destination_bank"] = b
        else:
            cur = {"frame": frame, "source_offset": x, "destination_offset": y, "length": 1, "count_register": a,
                   "caller_dbr": b, "destination_bank": None, "source_banks": None}
            out.append(cur)
        prev_a = a
    for t in out:
        banks: set[int] = set()
        for k in range(t["length"]):
            banks |= src_banks.get((t["source_offset"] + k) & 0xFFFF, set())
        t["source_banks"] = sorted(banks)
        t["complete"] = t["length"] == t["count_register"] + 1
    return out


def port_images(doc: dict[str, Any], from_frame: int | None = None, to_frame: int | None = None) -> dict[str, Any]:
    """VRAM and CGRAM bytes written through the data ports (needs watches on $2115-$2119, $2121, $2122)."""
    writes = _register_writes(doc, {0x2115, 0x2116, 0x2117, 0x2118, 0x2119, 0x2121, 0x2122})
    vram = bytearray(0x10000)
    vwritten = bytearray(0x10000)
    cgram = bytearray(512)
    cwritten = bytearray(512)
    st = PortState()
    cg_latch = False
    for frame in sorted(writes):
        if (from_frame is not None and frame < from_frame) or (to_frame is not None and frame > to_frame):
            continue
        for _seq, off, width, value in writes[frame]:
            if off in (0x2115, 0x2116, 0x2117, 0x2121):
                st.apply(off, width, value)
                if off == 0x2121:
                    cg_latch = False
                    if width == 2:   # 16-bit store: the high byte lands on $2122
                        _cg_write(cgram, cwritten, st, (value >> 8) & 0xFF, cg_latch)
                        cg_latch = True
                continue
            if off == 0x2122:
                _cg_write(cgram, cwritten, st, value & 0xFF, cg_latch)
                cg_latch = not cg_latch
                if not cg_latch:
                    st.cgadd = ((st.cgadd or 0) + 1) & 0xFF
                continue
            if st.vmadd is None:
                continue
            vmain = st.vmain if st.vmain is not None else 0x80
            step = (1, 32, 128, 128)[vmain & 3]
            if off == 0x2118:
                if width == 2:
                    _v_write(vram, vwritten, st.vmadd, 0, value & 0xFF)
                    _v_write(vram, vwritten, st.vmadd, 1, (value >> 8) & 0xFF)
                    st.vmadd = (st.vmadd + step) & 0xFFFF
                else:
                    _v_write(vram, vwritten, st.vmadd, 0, value & 0xFF)
                    if not vmain & 0x80:
                        st.vmadd = (st.vmadd + step) & 0xFFFF
            elif off == 0x2119:
                _v_write(vram, vwritten, st.vmadd, 1, value & 0xFF)
                if vmain & 0x80:
                    st.vmadd = (st.vmadd + step) & 0xFFFF
    return {"vram": bytes(vram), "vram_ranges": _ranges(vwritten), "cgram": bytes(cgram), "cgram_ranges": _ranges(cwritten)}


def _v_write(vram: bytearray, written: bytearray, vmadd: int, half: int, v: int) -> None:
    i = ((vmadd * 2) + half) & 0xFFFF
    vram[i] = v
    written[i] = 1


def _cg_write(cgram: bytearray, written: bytearray, st: PortState, v: int, latch: bool) -> None:
    i = (((st.cgadd or 0) * 2) + (1 if latch else 0)) & 511
    cgram[i] = v
    written[i] = 1


def _ranges(written: bytearray) -> list[list[int]]:
    out = []
    i = 0
    n = len(written)
    while i < n:
        if written[i]:
            j = i
            while j < n and written[j]:
                j += 1
            out.append([i, j - i])
            i = j
        else:
            i += 1
    return out


def summary(doc: dict[str, Any], rows: list[dict[str, Any]], moves: list[dict[str, Any]]) -> dict[str, Any]:
    by_target: dict[str, int] = defaultdict(int)
    bytes_by_target: dict[str, int] = defaultdict(int)
    paired = 0
    pairable = 0
    for r in rows:
        key = f"{r['b_bus_name']} from {r['a_bus_region']}"
        by_target[key] += 1
        bytes_by_target[key] += r["size"]
        if r["b_bus_name"] in ("VMDATAL", "VMDATAH", "CGDATA", "OAMDATA"):
            pairable += 1
            if r.get("vmadd") is not None or r.get("cgadd") is not None or r.get("oamadd") is not None:
                paired += 1
    triggers = doc["residual"]["dma_triggers"]
    return {
        "mdmaen_stores": sum(1 for e in doc["dma_log"] if e[3] == "MDMAEN"),
        "record_dma_triggers": triggers,
        "channel_transfers": len(rows),
        "transfers_by_target": dict(sorted(by_target.items())),
        "bytes_by_target": dict(sorted(bytes_by_target.items())),
        "destinations_paired": paired, "destinations_pairable": pairable,
        "block_moves": len(moves), "block_move_bytes": sum(m["length"] for m in moves),
        "block_move_frames": sorted({m["frame"] for m in moves}),
        "block_move_executions_logged": len(doc.get("watch_pcs", {}).get("409", [])),
    }
