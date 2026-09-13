"""Validate the reference-only ZOOM ZOO content/read-boundary contract.

This module deliberately reconstructs only the bounded M4-03 observations.  It
does not expose ZOOM ZOO to the native game or infer a general track format.
Original and decoded payload bytes remain untracked inputs.
"""

from __future__ import annotations

import hashlib
from typing import Any

from . import provenance, rnc


SCHEMA_VERSION = 1
KIND = "zoom_zoo_reference_contract"
ROM_SHA256 = "a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e"
CORE_COMMIT = "7d5aa1e656b9171524d01b1b22917197d8121cb4"
CORE_PATCH_SHA256 = "a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885"
REPLAY_MANIFEST = "tests/manifests/replay/race-crawler-zoom-zoo-3300.json"
REPLAY_MANIFEST_SHA256 = "acd29bfb72aeaad0791923e22e17a791f5c182220f64b6686dd687984411aefd"
SAMPLE_DIGEST = "791a786370913136e21ed34c841e9a3d892852bf6804e2e0aef21e1df6557b68"
FINAL_STATE_SHA256 = "2a843314d19e60d13dab746541d43ffa9ad84adfe6f95b9cc6d3c45bd9a16aeb"
CAPTURE_SHA256 = {
    "load_1286_1291": "bc733d1c39bda5076f4548897510aa1b9f09bce4baa139e0ad9f0435b94cd56c",
    "gather_1376_1384": "36aeac919fa7f48bccf31fba35d064a0c550096829a96e203bd9244a03fe4b78",
    "sample_1700": "02f497194d481e370ce07935e825edd3a664dc6463ae691567437cc178628285",
    "sample_2220": "fa3e5e2d4352e79391461a09b9219127b133d5c592d6c24f0ff22f82ad794b3a",
    "next_builder_2220": "ecb45a173dafca37d56258162082ec2c3216fad81c79051d243cd4d6c47e71d9",
}
TRACK_LIST_START = 0xC5CF
TRACK_LIST_TERMINATOR = 0xC5E7
COARSE_MAP_OFFSET = 0x000F
SAMPLE_BLOCKS_OFFSET = 0x800F
GATHER_DESTINATION_START = 0x0437
TILE_DIRECTORY_BUS = 0x82B7DD
TABLE_DIRECTORY_BUS = 0x17A000
FLAGS_BASE_BUS = 0x17C4E4


class ContractError(ValueError):
    """The manifest or one of its identity-bound inputs is contradictory."""


def _exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise ContractError(f"{label} fields must be exactly {sorted(expected)}")
    return value


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _bus(value: Any, label: str) -> int:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise ContractError(f"{label} must be a 0x-prefixed bus address")
    try:
        result = int(value, 16)
    except ValueError as exc:
        raise ContractError(f"{label} is not hexadecimal") from exc
    if not 0 <= result <= 0xFFFFFF:
        raise ContractError(f"{label} is outside the 24-bit bus")
    return result


def _inclusive_range(value: Any, label: str) -> tuple[int, int]:
    if not isinstance(value, str) or value.count("-") != 1:
        raise ContractError(f"{label} must be an inclusive 0xSTART-0xEND range")
    start_text, end_text = value.split("-")
    start, end = _bus(start_text, f"{label} start"), _bus(end_text, f"{label} end")
    if start > 0xFFFF or end > 0xFFFF or end < start:
        raise ContractError(f"{label} must be an ascending 16-bit range")
    return start, end


def _validate_gather_destination(sample: dict[str, Any], byte_count: int) -> None:
    start, end = _inclusive_range(sample["destination"], "gather destination")
    if start != GATHER_DESTINATION_START or end - start + 1 != byte_count:
        raise ContractError(
            f"gather destination must begin at 0x{GATHER_DESTINATION_START:04X} "
            f"and contain exactly {byte_count} reconstructed bytes")


def _u16(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 2 > len(data):
        raise ContractError(f"word at 0x{offset:X} is outside its payload")
    return data[offset] | (data[offset + 1] << 8)


def _rom_slice(rom: bytes, bus: int, length: int) -> bytes:
    if not isinstance(length, int) or length <= 0:
        raise ContractError("ROM piece length must be positive")
    offset = provenance.rom_file_offset(bus, len(rom))
    if offset is None or offset + length > len(rom):
        raise ContractError(f"ROM piece 0x{bus:06X}+{length} is unavailable")
    return rom[offset:offset + length]


def _add_lorom(bus: int, amount: int) -> int:
    bank, address = bus >> 16, (bus & 0xFFFF) + amount
    while address >= 0x10000:
        bank += 1
        address -= 0x8000
    return (bank << 16) | address


def validate_manifest(data: Any) -> dict[str, Any]:
    root = _exact_keys(data, {
        "schema_version", "kind", "id", "description", "identity", "source",
        "decoded_regions", "load_contract", "gather_samples",
        "collision_content", "collision_samples", "limits",
    }, "contract")
    if (root["schema_version"], root["kind"], root["id"]) != (
            SCHEMA_VERSION, KIND, "zoom-zoo-reference-v1"):
        raise ContractError("unsupported ZOOM ZOO contract identity")
    identity = _exact_keys(root["identity"], {
        "rom_sha256", "core_commit", "core_patch_sha256", "replay_manifest",
        "replay_manifest_sha256", "sample_digest", "final_state_sha256",
        "captures",
    }, "identity")
    if identity["rom_sha256"] != ROM_SHA256:
        raise ContractError("contract binds the wrong source ROM")
    if (identity["core_commit"], identity["core_patch_sha256"],
            identity["replay_manifest"], identity["replay_manifest_sha256"]) != (
            CORE_COMMIT, CORE_PATCH_SHA256, REPLAY_MANIFEST, REPLAY_MANIFEST_SHA256):
        raise ContractError("core or replay source identity differs")
    if (identity["sample_digest"], identity["final_state_sha256"]) != (
            SAMPLE_DIGEST, FINAL_STATE_SHA256):
        raise ContractError("replay sample or final-state identity differs")
    if identity["captures"] != CAPTURE_SHA256:
        raise ContractError("capture identity inventory differs")
    source = _exact_keys(root["source"], {
        "asset", "bus", "file_offset", "packed_length", "consumed_source_end",
        "rnc_header", "decoded_length", "decoded_sha256", "runtime_base",
        "cursor_word_offset", "cursor_runtime_final",
    }, "source")
    if (_bus(source["bus"], "source.bus"), source["file_offset"],
            source["packed_length"], _bus(source["runtime_base"], "source.runtime_base"),
            source["cursor_word_offset"]) != (0x188183, 0x0C0183, 6599, 0x7F0000, 11):
        raise ContractError("source/runtime bounds differ from the observed asset")
    header = _exact_keys(source["rnc_header"], {
        "magic", "method", "unpacked_length", "packed_length", "unpacked_crc",
        "packed_crc", "leeway", "chunks",
    }, "source.rnc_header")
    if source["packed_length"] != header["packed_length"] + 18:
        raise ContractError("packed object length contradicts its RNC header")
    if source["decoded_length"] != header["unpacked_length"]:
        raise ContractError("decoded length contradicts its RNC header")
    if (source["consumed_source_end"], source["cursor_runtime_final"]) != ("0x189B4A", 0xC5E8):
        raise ContractError("consumed-source or runtime-cursor bound differs")
    regions = root["decoded_regions"]
    if not isinstance(regions, list) or not regions:
        raise ContractError("decoded_regions must be a nonempty list")
    expected_regions = [
        ("header", 0x0000, 0x000F),
        ("coarse-grid-words", 0x000F, 0x8000),
        ("bounded-consumer-data", 0x800F, 0x45C0),
        ("ordered-tile-list", 0xC5CF, 0x0019),
    ]
    prior = 0
    for index, region in enumerate(regions):
        region = _exact_keys(region, {"id", "start", "length", "sha256", "consumer"},
                             f"decoded_regions[{index}]")
        if not isinstance(region["start"], int) or not isinstance(region["length"], int) or region["length"] <= 0:
            raise ContractError("decoded region bounds must be positive integers")
        if region["start"] < prior or region["start"] + region["length"] > source["decoded_length"]:
            raise ContractError("decoded regions overlap or exceed the decoded object")
        if not isinstance(region["consumer"], str) or not region["consumer"]:
            raise ContractError("each decoded region needs an observed consumer")
        if index >= len(expected_regions) or (region["id"], region["start"], region["length"]) != expected_regions[index]:
            raise ContractError("decoded region names/bounds differ from the observed contract")
        prior = region["start"] + region["length"]
    if len(regions) != len(expected_regions):
        raise ContractError("decoded region inventory differs")
    load = _exact_keys(root["load_contract"], {
        "cursor_iterations", "selected_ids", "terminator", "entries",
        "tile_payload", "table_payload", "flags_payload", "transfer_count",
        "transfer_bytes", "transfer_sha256", "transfer_row_format",
    }, "load_contract")
    if load["cursor_iterations"] != len(load["selected_ids"]) + 1:
        raise ContractError("cursor iteration count must include exactly one terminator")
    if load["selected_ids"] != [entry.get("id") for entry in load["entries"]]:
        raise ContractError("selected ids and ordered loader entries differ")
    if load["terminator"] != 0xFF or load["transfer_count"] != 406 or load["transfer_bytes"] != 25984:
        raise ContractError("load cardinality differs from the bounded observation")
    for label in ("tile_payload", "table_payload", "flags_payload"):
        _exact_keys(load[label], {"length", "sha256"}, f"load_contract.{label}")
    if not isinstance(root["gather_samples"], list) or len(root["gather_samples"]) != 2:
        raise ContractError("the contract requires exactly two independent gather samples")
    if [(sample.get("frame"), sample.get("input"), sample.get("builder_frame"))
            for sample in root["gather_samples"]] != [(1700, "Right", 1700), (2220, "Right+Up", 2224)]:
        raise ContractError("gather sample domain differs")
    for sample in root["gather_samples"]:
        sample = _exact_keys(sample, {
            "frame", "input", "builder_frame", "destination", "runs", "expected_sha256",
        }, "gather sample")
        if not isinstance(sample["runs"], list) or not sample["runs"]:
            raise ContractError("gather sample runs must be a nonempty list")
        byte_count = 0
        for run in sample["runs"]:
            run = _exact_keys(run, {"source_x", "step", "words"}, "gather run")
            if (not isinstance(run["source_x"], int) or not isinstance(run["step"], int)
                    or not isinstance(run["words"], int) or run["step"] <= 0 or run["words"] <= 0):
                raise ContractError("gather run offsets, counts and steps must be integers with positive counts and steps")
            byte_count += run["words"] * 2
        _validate_gather_destination(sample, byte_count)
    if not isinstance(root["collision_samples"], list) or len(root["collision_samples"]) != 4:
        raise ContractError("the contract requires both riders at two collision frames")
    if [(sample.get("frame"), sample.get("input"), sample.get("rider"))
            for sample in root["collision_samples"]] != [
                (1700, "Right", "player"), (1700, "Right", "opponent"),
                (2220, "Right+Up", "player"), (2220, "Right+Up", "opponent")]:
        raise ContractError("collision sample domain differs")
    return root


def _validate_regions(contract: dict[str, Any], decoded: bytes) -> None:
    source = contract["source"]
    if len(decoded) != source["decoded_length"] or _sha(decoded) != source["decoded_sha256"]:
        raise ContractError("decoded track identity differs")
    for region in contract["decoded_regions"]:
        start, end = region["start"], region["start"] + region["length"]
        if _sha(decoded[start:end]) != region["sha256"]:
            raise ContractError(f"decoded region identity differs: {region['id']}")


def _validate_load(contract: dict[str, Any], rom: bytes, decoded: bytes) -> dict[str, int]:
    load = contract["load_contract"]
    selected = list(decoded[TRACK_LIST_START:TRACK_LIST_TERMINATOR])
    if selected != load["selected_ids"] or decoded[TRACK_LIST_TERMINATOR] != load["terminator"]:
        raise ContractError("decoded loader cursor bytes differ")
    tile_payload = bytearray()
    table_payload = bytearray()
    flags_payload = bytearray()
    transfer_rows: list[str] = []
    tile_number = 0
    for index, (identifier, expected) in enumerate(zip(selected, load["entries"], strict=True)):
        expected = _exact_keys(expected, {
            "id", "tile_source_bus", "tile_bytes", "tile_count",
            "table_source_bus", "table_bytes", "flags_source_bus", "flags_bytes",
        }, f"load_contract.entries[{index}]")
        directory = _rom_slice(rom, TILE_DIRECTORY_BUS + identifier * 5, 5)
        tile_bus = (directory[0] << 16) | _u16(directory, 1)
        tile_bytes = _u16(directory, 3)
        table_directory = _rom_slice(rom, TABLE_DIRECTORY_BUS + identifier * 4, 4)
        table_bus = (table_directory[2] << 16) | _u16(table_directory, 0)
        tile_count = tile_bytes // 128
        flags_bus = FLAGS_BASE_BUS + ((_u16(table_directory, 0) - 0xA0A4) // 32)
        observed = (identifier, tile_bus, tile_bytes, tile_count, table_bus,
                    tile_bytes // 4, flags_bus, tile_count)
        declared = (expected["id"], _bus(expected["tile_source_bus"], "tile_source_bus"),
                    expected["tile_bytes"], expected["tile_count"],
                    _bus(expected["table_source_bus"], "table_source_bus"), expected["table_bytes"],
                    _bus(expected["flags_source_bus"], "flags_source_bus"), expected["flags_bytes"])
        if observed != declared or tile_bytes == 0 or tile_bytes % 128:
            raise ContractError(f"ordered loader entry {index} differs")
        tile_payload += _rom_slice(rom, tile_bus, tile_bytes)
        table_payload += _rom_slice(rom, table_bus, tile_bytes // 4)
        flags_payload += _rom_slice(rom, flags_bus, tile_count)
        for group_start in range(0, tile_count, 8):
            group_count = min(8, tile_count - group_start)
            group_offset = group_start * 128
            for within in range(group_count):
                destination = 0x2000 + (tile_number // 8) * 0x200 + (tile_number % 8) * 0x20
                top = _add_lorom(tile_bus, group_offset + within * 64)
                bottom = _add_lorom(tile_bus, group_offset + group_count * 64 + within * 64)
                transfer_rows.append(f"{top:06x}:{destination:04x}:64\n")
                transfer_rows.append(f"{bottom:06x}:{destination + 0x100:04x}:64\n")
                tile_number += 1
    for label, payload in (("tile_payload", tile_payload), ("table_payload", table_payload),
                           ("flags_payload", flags_payload)):
        expected = load[label]
        if len(payload) != expected["length"] or _sha(payload) != expected["sha256"]:
            raise ContractError(f"{label} identity differs")
    rows = "".join(transfer_rows).encode()
    if len(transfer_rows) != load["transfer_count"] or sum(int(row.rsplit(":", 1)[1]) for row in transfer_rows) != load["transfer_bytes"]:
        raise ContractError("generated transfer cardinality differs")
    if _sha(rows) != load["transfer_sha256"]:
        raise ContractError("ordered transfer identity differs")
    return {"selected_entries": len(selected), "tiles": tile_number, "transfers": len(transfer_rows)}


def _validate_gather(contract: dict[str, Any], decoded: bytes) -> int:
    compared = 0
    for sample in contract["gather_samples"]:
        sample = _exact_keys(sample, {"frame", "input", "builder_frame", "destination", "runs", "expected_sha256"}, "gather sample")
        if sample["input"] not in ("Right", "Right+Up"):
            raise ContractError("unexpected gather input classification")
        assembled = bytearray()
        for run in sample["runs"]:
            run = _exact_keys(run, {"source_x", "step", "words"}, "gather run")
            if run["words"] <= 0 or run["step"] <= 0:
                raise ContractError("gather run counts and steps must be positive")
            for index in range(run["words"]):
                offset = COARSE_MAP_OFFSET + ((run["source_x"] + index * run["step"]) & 0xFFFF)
                assembled += _u16(decoded, offset).to_bytes(2, "little")
        _validate_gather_destination(sample, len(assembled))
        if _sha(assembled) != sample["expected_sha256"]:
            raise ContractError(f"gather reconstruction differs at builder frame {sample['builder_frame']}")
        compared += len(assembled)
    return compared


def _collision_points(poses: bytes, templates: bytes, pose_index: int, reflected: bool) -> list[list[int]]:
    offset = pose_index * 8
    if offset + 8 > len(poses):
        raise ContractError("collision pose is outside the observed pose table")
    result = [[poses[offset], poses[offset + 1]], [poses[offset + 2], poses[offset + 3]]]
    origin_x, origin_y = poses[offset + 4], poses[offset + 5]
    selector = _u16(poses, offset + 6)
    template = (((selector & 0xFF) << 8) | (selector >> 8)) << 4 & 0xFFFF
    if template + 16 > len(templates):
        raise ContractError("collision template is outside the observed template table")
    result += [[(origin_x + templates[template + index * 2]) & 0xFF,
                (origin_y + templates[template + index * 2 + 1]) & 0xFF] for index in range(8)]
    for point in result:
        if reflected:
            point[0] = (47 - point[0]) & 0xFF
        point[0] = (point[0] + 8) & 0xFF
    return result


def _sample_track(decoded: bytes, points: list[list[int]], x: int, y: int, width: int) -> tuple[list[int], list[int]]:
    if width != 256 or y >= 0x8000 or (x >> 6) + 1 >= width:
        raise ContractError("sample is outside the bounded ZOOM ZOO branch")
    column, row = x >> 6, y >> 6
    upper_left = (((row * width) & 0xFFFF) + column) * 2 & 0xFFFF
    stride = width * 2 & 0xFFFF
    coarse = [upper_left, (upper_left + 2) & 0xFFFF,
              (upper_left + stride) & 0xFFFF, (upper_left + stride + 2) & 0xFFFF]
    blocks = [(_u16(decoded, COARSE_MAP_OFFSET + offset) * 32) & 0xFFFF for offset in coarse]
    boundary_x, boundary_y = 64 - (x & 63), 64 - (y & 63)
    offsets, values = [], []
    for point_x, point_y in points:
        negative = lambda left, right: ((left - right) & 0x80) != 0
        quadrant = (0 if negative(point_x, boundary_x) else 1) + (0 if negative(point_y, boundary_y) else 2)
        fine_x = ((point_x + x) & 0x30) >> 2
        fine_y = (point_y + y) & 0x30
        offset = SAMPLE_BLOCKS_OFFSET + ((blocks[quadrant] + ((fine_x + fine_y) >> 1)) & 0xFFFF)
        offsets.append(offset)
        values.append(_u16(decoded, offset))
    return offsets, values


def _validate_collisions(contract: dict[str, Any], rom: bytes, decoded: bytes) -> int:
    content = _exact_keys(contract["collision_content"], {
        "poses_file_offset", "poses_length", "poses_sha256", "templates_file_offset",
        "templates_length", "templates_sha256", "coarse_width", "coarse_stride",
    }, "collision_content")
    poses = rom[content["poses_file_offset"]:content["poses_file_offset"] + content["poses_length"]]
    templates = rom[content["templates_file_offset"]:content["templates_file_offset"] + content["templates_length"]]
    if _sha(poses) != content["poses_sha256"] or _sha(templates) != content["templates_sha256"]:
        raise ContractError("collision pose/template source identity differs")
    if (content["coarse_width"], content["coarse_stride"]) != (256, 512):
        raise ContractError("collision width/stride differ from the observed branch")
    compared = 0
    for sample in contract["collision_samples"]:
        sample = _exact_keys(sample, {
            "frame", "input", "rider", "position_x", "position_y", "pose_index",
            "reflected", "points", "decoded_offsets", "values",
        }, "collision sample")
        points = _collision_points(poses, templates, sample["pose_index"], sample["reflected"])
        if points != sample["points"]:
            raise ContractError(f"collision points differ at frame {sample['frame']} rider {sample['rider']}")
        offsets, values = _sample_track(decoded, points, sample["position_x"], sample["position_y"], 256)
        if offsets != sample["decoded_offsets"] or values != sample["values"]:
            raise ContractError(f"collision reads differ at frame {sample['frame']} rider {sample['rider']}")
        compared += len(values)
    return compared


def validate(contract_data: Any, rom: bytes) -> dict[str, int]:
    contract = validate_manifest(contract_data)
    if _sha(rom) != ROM_SHA256:
        raise ContractError("source ROM identity differs")
    source = contract["source"]
    bus = _bus(source["bus"], "source.bus")
    header = rnc.parse_header(rnc.lorom_reader(rom), bus >> 16, bus & 0xFFFF)
    if header != source["rnc_header"]:
        raise ContractError("RNC header metadata differs")
    decoded, end = rnc.decompress(rnc.lorom_reader(rom), bus >> 16, bus & 0xFFFF)
    if f"0x{end[0]:02X}{end[1]:04X}" != source["consumed_source_end"]:
        raise ContractError("consumed packed-source end differs")
    _validate_regions(contract, decoded)
    load = _validate_load(contract, rom, decoded)
    return {**load, "gather_bytes": _validate_gather(contract, decoded),
            "collision_words": _validate_collisions(contract, rom, decoded),
            "decoded_bytes": len(decoded)}
