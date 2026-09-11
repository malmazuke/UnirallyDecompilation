"""Minimal PPU data helpers for the runtime comparison: planar tile decoding,
CGRAM colour conversion as the pinned core's libretro target performs it,
tile-map layer and sprite rendering, PNG read/write and pixel comparison.

What the renderer omits is stated by ``OMITTED``; the comparison report
carries that list. It is not a PPU: no windows, colour math, mosaic, per-
scanline HDMA register changes, BG3, offset-per-tile or interlace.
"""

from __future__ import annotations

import struct
import zlib

OMITTED = (
    "windows and colour math (the GO letters and the fixed-colour effect of HDMA channels 5 and 6)",
    "BG3 (the HUD text layer) and its priority",
    "per-scanline HDMA register changes (scroll values are the last CPU register writes before the frame)",
    "mosaic, interlace, offset-per-tile, sprite-per-line limits and the OAM address reset at vblank",
    "sprite priority relative to background priority bits beyond the mode-1 base order",
)

SCREEN_WIDTH = 256
SCREEN_HEIGHT = 224


# ------------------------------------------------------------------ tiles

def decode_tile_4bpp(data: bytes, offset: int) -> list[int]:
    """64 pixel values of the 32-byte planar 4bpp tile at ``offset`` (row-major)."""
    px = [0] * 64
    for y in range(8):
        p0 = data[offset + 2 * y]
        p1 = data[offset + 2 * y + 1]
        p2 = data[offset + 16 + 2 * y]
        p3 = data[offset + 17 + 2 * y]
        for x in range(8):
            bit = 7 - x
            px[y * 8 + x] = ((p0 >> bit) & 1) | (((p1 >> bit) & 1) << 1) | (((p2 >> bit) & 1) << 2) | (((p3 >> bit) & 1) << 3)
    return px


def decode_tile_2bpp(data: bytes, offset: int) -> list[int]:
    px = [0] * 64
    for y in range(8):
        p0 = data[offset + 2 * y]
        p1 = data[offset + 2 * y + 1]
        for x in range(8):
            bit = 7 - x
            px[y * 8 + x] = ((p0 >> bit) & 1) | (((p1 >> bit) & 1) << 1)
    return px


# ------------------------------------------------------------------ colours

def channel8(v: int) -> int:
    """One 5-bit channel to 8 bits as the libretro target's palette does (replicate, gamma 1.5 below half)."""
    x = ((v << 3) | (v >> 2)) & 0xFF
    x16 = (x << 8) | x
    if x16 <= 32767:
        x16 = int(32767 * ((x16 / 32767.0) ** 1.5))
    return x16 >> 8


def cgram_rgb(word: int, order: str = "bgr") -> tuple[int, int, int]:
    """CGRAM word (0bbbbbgggggrrrrr) to the 8-bit RGB the core outputs; ``order`` selects
    which 5-bit field is treated as red by the target's palette (calibrated against the frame image)."""
    a = word & 31
    b = (word >> 5) & 31
    c = (word >> 10) & 31
    if order == "bgr":       # SNES field order: red is the low field
        r, g, bl = a, b, c
    else:                    # the target indexes with red as the high field
        r, g, bl = c, b, a
    return channel8(r), channel8(g), channel8(bl)


def palette_from_cgram(cgram: bytes, order: str = "bgr") -> list[tuple[int, int, int]]:
    return [cgram_rgb(cgram[2 * i] | (cgram[2 * i + 1] << 8), order) for i in range(256)]


# ------------------------------------------------------------------ layers

class Layer:
    """RGB pixels plus an opaque mask and a per-pixel priority flag for one screen-sized layer."""

    def __init__(self, width: int = SCREEN_WIDTH, height: int = SCREEN_HEIGHT) -> None:
        self.width = width
        self.height = height
        self.index = bytearray(width * height)        # colour index (0 = transparent)
        self.priority = bytearray(width * height)

    def opaque(self, x: int, y: int) -> bool:
        return self.index[y * self.width + x] != 0


def render_bg(vram: bytes, map_base: int, map_wide: bool, map_tall: bool, tile_base: int, bpp: int, tiles16: bool,
              hofs: int, vofs: int, width: int = SCREEN_WIDTH, height: int = SCREEN_HEIGHT) -> Layer:
    """Render a background layer into colour indices.

    ``map_base`` and ``tile_base`` are VRAM byte offsets; the tile map is 32x32 entries per
    screen, with a second screen to the right when ``map_wide`` and below when ``map_tall``
    (SC register bits). Entries: tile 0-9, palette 10-12, priority 13, hflip 14, vflip 15."""
    layer = Layer(width, height)
    tile_bytes = 8 * bpp
    tile_px = 16 if tiles16 else 8
    map_w = 64 if map_wide else 32
    map_h = 64 if map_tall else 32
    cache: dict[int, list[int]] = {}

    def tile_pixels(n: int) -> list[int]:
        t = cache.get(n)
        if t is None:
            off = (tile_base + (n & 0x3FF) * tile_bytes) & 0xFFFF
            if off + tile_bytes > len(vram):
                t = [0] * 64
            else:
                t = decode_tile_4bpp(vram, off) if bpp == 4 else decode_tile_2bpp(vram, off)
            cache[n] = t
        return t

    for sy in range(height):
        # The PPU draws the first visible line as line 1, so a background row is vofs + y + 1
        # (calibrated: the +1 removes the one-line offset against the frame image, R-0008).
        py = (sy + vofs + 1) & (map_h * tile_px - 1)
        my = py // tile_px
        for sx in range(width):
            px = (sx + hofs) & (map_w * tile_px - 1)
            mx = px // tile_px
            # screen quadrant of the entry
            screen = 0
            ex, ey = mx, my
            if mx >= 32:
                screen += 1
                ex -= 32
            if my >= 32:
                screen += 2 if map_wide else 1
                ey -= 32
            entry_off = (map_base + screen * 0x800 + (ey * 32 + ex) * 2) & 0xFFFF
            entry = vram[entry_off] | (vram[entry_off + 1] << 8)
            tile = entry & 0x3FF
            pal = (entry >> 10) & 7
            pri = (entry >> 13) & 1
            hflip = (entry >> 14) & 1
            vflip = (entry >> 15) & 1
            ix = px % tile_px
            iy = py % tile_px
            if hflip:
                ix = tile_px - 1 - ix
            if vflip:
                iy = tile_px - 1 - iy
            if tiles16:
                tile = (tile + (ix >> 3) + ((iy >> 3) << 4)) & 0x3FF
                ix &= 7
                iy &= 7
            v = tile_pixels(tile)[iy * 8 + ix]
            if v:
                layer.index[sy * width + sx] = (pal << bpp) + v if bpp == 4 else (pal << 2) + v
                layer.priority[sy * width + sx] = pri
    return layer


def parse_oam(oam: bytes) -> list[dict]:
    """The 128 sprites of a 544-byte OAM image (low table then high table)."""
    out = []
    for i in range(128):
        b = oam[4 * i:4 * i + 4]
        hi = (oam[512 + (i >> 2)] >> ((i & 3) * 2)) & 3
        out.append({"index": i, "x": b[0] | ((hi & 1) << 8), "y": b[1], "tile": b[2] | ((b[3] & 1) << 8),
                    "palette": (b[3] >> 1) & 7, "priority": (b[3] >> 4) & 3, "hflip": (b[3] >> 6) & 1, "vflip": (b[3] >> 7) & 1,
                    "large": (hi >> 1) & 1})
    return out


OBJ_SIZES = {0: (8, 16), 1: (8, 32), 2: (8, 64), 3: (16, 32), 4: (16, 64), 5: (32, 64), 6: (16, 32), 7: (16, 32)}


def render_sprites(vram: bytes, oam: bytes, obsel: int, width: int = SCREEN_WIDTH, height: int = SCREEN_HEIGHT) -> Layer:
    """Render the sprites of an OAM image: colour index 128 + palette*16 + pixel; lower OAM index in front."""
    layer = Layer(width, height)
    small, large = OBJ_SIZES[(obsel >> 5) & 7]
    name_base = (obsel & 7) << 14
    name_select = (((obsel >> 3) & 3) + 1) << 13
    cache: dict[int, list[int]] = {}

    def tile_pixels(n: int) -> list[int]:
        t = cache.get(n)
        if t is None:
            off = (name_base + (n & 0xFF) * 32 + (name_select if n & 0x100 else 0)) & 0xFFFF
            t = decode_tile_4bpp(vram, off) if off + 32 <= len(vram) else [0] * 64
            cache[n] = t
        return t

    for spr in reversed(parse_oam(oam)):
        size = large if spr["large"] else small
        x0 = spr["x"]
        if x0 >= 256:
            x0 -= 512
        y0 = spr["y"]
        if y0 >= height and y0 < 256 - size:
            continue
        if y0 >= 256 - size:
            y0 -= 256
        tiles = size // 8
        for ty in range(tiles):
            for tx in range(tiles):
                ttx = tiles - 1 - tx if spr["hflip"] else tx
                tty = tiles - 1 - ty if spr["vflip"] else ty
                n = (spr["tile"] & 0x100) | (((spr["tile"] & 0xFF) + ttx + (tty << 4)) & 0xFF)
                px = tile_pixels(n)
                for iy in range(8):
                    sy = y0 + ty * 8 + iy
                    if not 0 <= sy < height:
                        continue
                    for ix in range(8):
                        sx = x0 + tx * 8 + ix
                        if not 0 <= sx < width:
                            continue
                        rx = 7 - ix if spr["hflip"] else ix
                        ry = 7 - iy if spr["vflip"] else iy
                        v = px[ry * 8 + rx]
                        if v:
                            layer.index[sy * width + sx] = 128 + (spr["palette"] << 4) + v
                            layer.priority[sy * width + sx] = spr["priority"]
    return layer


def compose(palette: list[tuple[int, int, int]], backdrop: int, layers: list[tuple[Layer, int]],
            width: int = SCREEN_WIDTH, height: int = SCREEN_HEIGHT) -> bytes:
    """Front-to-back composition: ``layers`` are (layer, priority value) drawn in the order given, later on top
    of earlier; a layer entry whose pixel priority differs from the given value is skipped for that pass."""
    out = bytearray(width * height * 3)
    bd = palette[backdrop]
    for i in range(width * height):
        out[3 * i:3 * i + 3] = bytes(bd)
    for layer, pri in layers:
        for i in range(width * height):
            v = layer.index[i]
            if v and layer.priority[i] == pri:
                out[3 * i:3 * i + 3] = bytes(palette[v])
    return bytes(out)


# ------------------------------------------------------------------ PNG

def read_png(data: bytes) -> tuple[int, int, bytes]:
    """8-bit RGB or RGBA, non-interlaced PNG to (width, height, RGB bytes)."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG file")
    pos = 8
    idat = b""
    width = height = 0
    channels = 3
    while pos < len(data):
        n = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + n]
        pos += 12 + n
        if kind == b"IHDR":
            width, height, depth, ctype, _c, _f, interlace = struct.unpack(">IIBBBBB", body)
            if depth != 8 or ctype not in (2, 6) or interlace:
                raise ValueError("only 8-bit RGB/RGBA non-interlaced PNG is supported")
            channels = 3 if ctype == 2 else 4
        elif kind == b"IDAT":
            idat += body
    raw = zlib.decompress(idat)
    stride = width * channels
    prev = bytearray(stride)
    out = bytearray()
    p = 0
    for _y in range(height):
        f = raw[p]
        row = bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        for i in range(stride):
            a = row[i - channels] if i >= channels else 0
            b = prev[i]
            c = prev[i - channels] if i >= channels else 0
            if f == 1:
                row[i] = (row[i] + a) & 0xFF
            elif f == 2:
                row[i] = (row[i] + b) & 0xFF
            elif f == 3:
                row[i] = (row[i] + ((a + b) >> 1)) & 0xFF
            elif f == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pred = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                row[i] = (row[i] + pred) & 0xFF
        prev = row
        if channels == 4:
            out += bytes(v for px in range(width) for v in row[4 * px:4 * px + 3])
        else:
            out += row
    return width, height, bytes(out)


def write_png(width: int, height: int, rgb: bytes) -> bytes:
    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    rows = b"".join(b"\x00" + rgb[y * width * 3:(y + 1) * width * 3] for y in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))


# ------------------------------------------------------------------ compare

def compare(a: bytes, b: bytes, width: int, rect: tuple[int, int, int, int]) -> tuple[int, int, bytes]:
    """Pixel-for-pixel comparison of two RGB images over ``rect`` (x, y, w, h): returns
    (mismatches, pixels compared, diff image of the rectangle: white where different)."""
    x0, y0, w, h = rect
    mism = 0
    diff = bytearray(w * h * 3)
    for y in range(h):
        for x in range(w):
            i = ((y0 + y) * width + x0 + x) * 3
            same = a[i:i + 3] == b[i:i + 3]
            if not same:
                mism += 1
                diff[(y * w + x) * 3:(y * w + x) * 3 + 3] = b"\xff\xff\xff"
    return mism, w * h, bytes(diff)


def side_by_side(images: list[bytes], width: int, height: int) -> bytes:
    """Concatenate equally sized RGB images horizontally."""
    out = bytearray()
    for y in range(height):
        for img in images:
            out += img[y * width * 3:(y + 1) * width * 3]
    return bytes(out)
