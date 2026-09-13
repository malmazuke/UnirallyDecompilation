"""Freeze and verify the M4-04 reference-only ZOOM ZOO riding projection.

This module never runs native gameplay. ``capture-seed`` repeats the original
to end-of-frame 1649 in a fresh private SRAM directory. ``freeze`` accepts two
fresh complete replay captures and two seed reports, checks their frozen
source identities, and writes an additive projection without changing the
accepted replay manifests or expectations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any

from ..reference.bsnes import BsnesCore, DEFAULT_OPTIONS
from ..reference.worker import capture_fields, inputs_for_frame
from ..replay.manifest import derive_script, range_fields, script_equivalent, validate_manifest


ROOT = Path(__file__).resolve().parents[3]
ROM_SHA256 = "a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e"
CORE_COMMIT = "7d5aa1e656b9171524d01b1b22917197d8121cb4"
CORE_PATCH_SHA256 = "a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885"
CORE_LIBRARY_SHA256 = "1cdb99db7ac58ee8c0b9d53128ad01320154fd46dc3a00d294a4fbd2be3e889b"
INITIAL_FRAME = 1649
FIRST_UPDATE_FRAME = 1650
LAST_FRAME = 3299

CASES = {
    "race-crawler-zoom-zoo-3300-riding-fields": {
        "source": "tests/manifests/replay/race-crawler-zoom-zoo-3300.json",
        "source_sha256": "acd29bfb72aeaad0791923e22e17a791f5c182220f64b6686dd687984411aefd",
        "sample_digest": "791a786370913136e21ed34c841e9a3d892852bf6804e2e0aef21e1df6557b68",
        "final_state_sha256": "2a843314d19e60d13dab746541d43ffa9ad84adfe6f95b9cc6d3c45bd9a16aeb",
        "field_manifest_sha256": "e6a02eeaa053f86ffb93211e26a68a1229a1d9b5ae4c882404d3518eaa8a7426",
        "av_digest": "dc7ca8ff6db1c2bbef17efd639c74f0d238a93f920e3b8f72b1c5ad80b1be22a",
        "rows_sha256": "84bed2b15a26d4d4afbc8d27ad74a10375cd1d6dce7980a7fc4fe49118118aae",
    },
    "race-crawler-zoom-zoo-3300-release-2500-2599-riding-fields": {
        "source": "tests/manifests/replay/race-crawler-zoom-zoo-3300-release-2500-2599.json",
        "source_sha256": "66399d29b7da16bb52111dc93ada2b62aa14cbf10db4a2644dcbd85bb2c88ff7",
        "sample_digest": "c253de4bce372be26b0457fa870b72c7a1acddb953a3ecf9ee187006ad55d63e",
        "final_state_sha256": "00bf36ed74988b785f96c9e21116b2920915d85a81896b275255961d0330127d",
        "field_manifest_sha256": "628822f86755880d0d27ac494c121b6aae9c1760044ee2ced02e889299d5db3e",
        "av_digest": "5f5388daccf78c191cb5875475ffbcfb2b06db8c829665f9260da4c83f3b012e",
        "rows_sha256": "5558632ae2c8f9f9c262e53851e33b71e771b1acb3ba786c914f03e426a40949",
    },
}

# Exact replay-field surface. Descriptions may improve without changing the
# capture protocol, but missing, duplicated, renamed or resized ranges fail.
EXPECTED_RANGES = [
    ("phase_counters", 0x0300, 3), ("input_images_axes", 0x0311, 10),
    ("pose_indices", 0x0411, 4), ("positions", 0x0415, 8),
    ("fractional_residues", 0x0401, 8), ("velocities", 0x04BB, 8),
    ("jump_phase", 0x04C3, 6), ("orientations", 0x04CB, 4),
    ("contact_previous_x", 0x04D7, 4), ("contact_previous_y", 0x04DB, 4),
    ("contact_auxiliary", 0x04DF, 4), ("contact_angle_sentinels", 0x04EB, 4),
    ("contact_counts", 0x054B, 4), ("contact_previous_counts", 0x054F, 4),
    ("surface_angles", 0x0B6E, 4), ("contact_selected_high", 0x0B72, 4),
    ("contact_response_b", 0x0BB3, 8), ("pose_history", 0x0B5A, 36),
    ("reflection_flags", 0x0BA7, 4), ("throttles", 0x0BEB, 4),
    ("jump_state", 0x0BDB, 14), ("reward_cooldown", 0x0CA7, 2),
    ("reward_queue", 0x0CEB, 32), ("reward_cursors", 0x0D11, 4),
    ("opponent_ai", 0x0C6F, 14), ("quarter_state", 0x0D25, 32),
    ("track_wrap_mask", 0x0D4F, 2), ("pose_idle_state", 0x0E77, 30),
    ("reflected_orientations", 0x0DE9, 4), ("timer", 0x0E19, 20),
    ("contact_selected_words", 0x0E9F, 4), ("rolling_flags", 0x0EA3, 4),
    ("finish_flags", 0x0EFF, 4), ("finish_delay_counter", 0x0F0F, 2),
    ("jump_latches", 0x0D39, 6), ("progress", 0x0FC1, 16),
    ("learned_weight", 0x2102, 1), ("countdown", 0x11C5, 2),
    ("reward_boosts", 0x11DB, 8), ("quarter_counts", 0x1203, 16),
    ("global_update_counters", 0x127F, 2), ("quarter_initialized", 0x136B, 4),
]


def _p(name: str, field: str, offset: int, length: int, signed: bool = False) -> dict[str, Any]:
    return {"name": name, "field": field, "offset": offset, "length": length, "signed": signed}


PROJECTION = [
    _p("contact_phase", "phase_counters", 0, 1), _p("progress_phase", "phase_counters", 2, 1),
    _p("joy1l_image", "input_images_axes", 0, 1), _p("joy1h_image", "input_images_axes", 2, 1),
    _p("axis_v", "input_images_axes", 4, 1), _p("axis_h", "input_images_axes", 8, 1),
    _p("player_pose", "pose_indices", 0, 2), _p("opponent_pose", "pose_indices", 2, 2),
    _p("player_x", "positions", 0, 2), _p("opponent_x", "positions", 2, 2),
    _p("player_y", "positions", 4, 2), _p("opponent_y", "positions", 6, 2),
    _p("player_x_residue", "fractional_residues", 0, 2, True), _p("opponent_x_residue", "fractional_residues", 2, 2, True),
    _p("player_y_residue", "fractional_residues", 4, 2, True), _p("opponent_y_residue", "fractional_residues", 6, 2, True),
    _p("player_vx", "velocities", 0, 2, True), _p("opponent_vx", "velocities", 2, 2, True),
    _p("player_vy", "velocities", 4, 2, True), _p("opponent_vy", "velocities", 6, 2, True),
    _p("player_reflected", "reflection_flags", 0, 2), _p("opponent_reflected", "reflection_flags", 2, 2),
    _p("player_contact_count", "contact_counts", 0, 2), _p("opponent_contact_count", "contact_counts", 2, 2),
    _p("player_contact_duration", "progress", 0, 2), _p("opponent_contact_duration", "progress", 2, 2),
    _p("player_surface_angle", "surface_angles", 0, 2, True), _p("opponent_surface_angle", "surface_angles", 2, 2, True),
    _p("player_selected_word", "contact_selected_words", 0, 2), _p("opponent_selected_word", "contact_selected_words", 2, 2),
    _p("player_progress_marker", "progress", 4, 2), _p("opponent_progress_marker", "progress", 6, 2),
    _p("player_transition_count", "progress", 8, 2), _p("opponent_transition_count", "progress", 10, 2),
    _p("player_progress_tag", "progress", 12, 2), _p("opponent_progress_tag", "progress", 14, 2),
    _p("player_throttle", "throttles", 0, 2, True), _p("opponent_throttle", "throttles", 2, 2, True),
    _p("countdown", "countdown", 0, 2),
    _p("timer_minutes", "timer", 0, 2), _p("timer_tens_seconds", "timer", 4, 2),
    _p("timer_seconds", "timer", 8, 2), _p("timer_tenths", "timer", 12, 2),
    _p("timer_frames", "timer", 16, 2), _p("track_wrap_mask", "track_wrap_mask", 0, 2),
    _p("queue_read_cursor", "reward_cursors", 0, 1), _p("queue_write_cursor", "reward_cursors", 2, 1),
    _p("reward_cooldown", "reward_cooldown", 0, 2), _p("learned_event_one_weight", "learned_weight", 0, 1),
    _p("player_finished", "finish_flags", 0, 2), _p("opponent_finished", "finish_flags", 2, 2),
    _p("finish_delay_counter", "finish_delay_counter", 0, 2),
]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _script_sha(manifest: dict[str, Any]) -> str:
    raw = (json.dumps(derive_script(manifest), indent=2, sort_keys=True) + "\n").encode()
    return sha(raw)


def _manifest_identity(manifest: dict[str, Any]) -> str:
    return sha(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode())


def _source_contract(manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = validate_manifest(manifest)
    case = CASES.get(manifest["scenario_id"])
    if case is None:
        raise ValueError("manifest is outside the two M4-04 ZOOM ZOO cases")
    source_path = ROOT / case["source"]
    source_raw = source_path.read_bytes()
    if sha(source_raw) != case["source_sha256"]:
        raise ValueError("accepted source replay manifest identity differs")
    source = validate_manifest(json.loads(source_raw))
    if manifest["rom"] != source["rom"] or manifest["core"] != source["core"]:
        raise ValueError("ROM/core/options differ from the accepted source case")
    if manifest["inputs"] != source["inputs"] or script_equivalent(derive_script(manifest), derive_script(source)):
        raise ValueError("controller schedule or run protocol differs from the accepted source case")
    if manifest["expected"] != source["expected"] or manifest["expected"] != {
            "sample_digest": case["sample_digest"], "final_state_sha256": case["final_state_sha256"]}:
        raise ValueError("whole-state expectation differs from the accepted source case")
    actual_ranges = [(item["name"], item["start"], item["length"]) for item in range_fields(manifest)]
    if actual_ranges != EXPECTED_RANGES:
        raise ValueError("field declaration inventory differs from the M4-04 contract")
    return manifest, case


def project_sample(sample: dict[str, Any]) -> list[int]:
    values = []
    for item in PROJECTION:
        raw = bytes.fromhex(sample["fields"][item["field"]])
        piece = raw[item["offset"]:item["offset"] + item["length"]]
        if len(piece) != item["length"]:
            raise ValueError(f"projected field is truncated: {item['name']}")
        values.append(int.from_bytes(piece, "little", signed=item["signed"]))
    return values


def _validate_run(manifest: dict[str, Any], case: dict[str, Any], run: dict[str, Any]) -> None:
    if run["script"]["sha256"] != _script_sha(manifest):
        raise ValueError("reference input script differs from the field manifest")
    if run["fields"] != range_fields(manifest):
        raise ValueError("reference field declarations differ from the field manifest")
    if (run["sample_digest"] != case["sample_digest"]
            or run["final"]["state_sha256"] != case["final_state_sha256"]
            or run["av_digest"] != case["av_digest"]):
        raise ValueError("reference whole-state or A/V identity differs from the accepted case")
    if run["rom"]["sha256"] != ROM_SHA256:
        raise ValueError("reference ROM identity differs")
    if (run["core"]["sha256"] != CORE_LIBRARY_SHA256
            or run["core"]["serialization_method"] != "Strict"
            or run["core"]["options"] != DEFAULT_OPTIONS):
        raise ValueError("reference core binary, options or serialization method differ")
    frames = run["frames"]
    if [item.get("frame") for item in frames] != list(range(LAST_FRAME + 1)):
        raise ValueError("reference frames must be exactly 0..3299 without loss or duplication")
    expected_names = {name for name, _start, _length in EXPECTED_RANGES}
    expected_lengths = {name: length for name, _start, length in EXPECTED_RANGES}
    for sample in frames:
        fields = sample.get("fields")
        if not isinstance(fields, dict) or set(fields) != expected_names:
            raise ValueError(f"reference field row keys differ at frame {sample.get('frame')}")
        for name, value in fields.items():
            if not isinstance(value, str) or len(value) != 2 * expected_lengths[name]:
                raise ValueError(f"reference field row width differs at frame {sample['frame']}: {name}")


def _seed_inventory() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    def add(name: str, address: int, width: int = 2, signed: bool = False, memory: str = "wram") -> None:
        items.append({"name": name, "memory": memory, "address": address, "width": width, "signed": signed})
    for name, address in [("contact_phase",0x300),("progress_phase",0x302),("joy1l",0x311),("joy1h",0x313),("axis_v",0x315),("axis_h",0x319),("animation_counter",0x4c7),("boost_counter",0x127f)]:
        add(name,address,1)
    rider_words = [
        ("x",0x415),("y",0x419),("vx",0x4bb),("vy",0x4bf),("x_residue",0x401),("y_residue",0x405),
        ("pose",0x411),("reflected",0xba7),("orientation",0x4cb),("reflected_orientation",0xde9),
        ("contact_count",0x54b),("previous_contact_count",0x54f),("contact_duration",0xfc1),
        ("previous_uncorrected_x",0x4d7),("previous_uncorrected_y",0x4db),("surface_angle",0xb6e),
        ("angle_sentinel",0x4eb),("contact_auxiliary",0x4df),("selected_word",0xe9f),("selected_high",0xb72),
        ("response_a",0xbb3),("response_b",0xbb7),("orientation_impulse",0xd35),("previous_x_displacement",0xbbb),
        ("jump_pending",0xd39),("jump_impulse_phase",0x4c3),("jump_baseline",0xbdb),("jump_previous_input",0xbe3),
        ("animation_phase",0xb62),("animation_increment",0xb6a),("pose_previous_x",0xb5a),("pose_previous_y",0xb5e),
        ("displacement_remainder",0xb66),("target_orientation",0xb76),("rolling",0xea3),
        ("progress_marker",0xfc5),("transition_count",0xfc9),("progress_tag",0xfcd),
        ("quarter_previous",0xd25),("forward_turns",0x1203),("reverse_turns",0x1207),("forward_quarters",0x120b),("reverse_quarters",0x120f),
        ("quarter_initialized",0x136b),("quarter_reflected_at_start",0x33f),("throttle",0xbeb),("prior_brake",0xd41),
        ("horizontal_boost",0x11d9),("vertical_boost",0x11df),("base_speed_cap",0x343),("small_motion_counter",0xc77),
    ]
    signed_names = {"vx","vy","x_residue","y_residue","surface_angle","response_a","response_b","orientation_impulse","animation_increment","displacement_remainder","throttle"}
    for rider in range(2):
        for name, address in rider_words:
            add(("player_" if rider == 0 else "opponent_") + name, address + 2*rider, signed=name in signed_names)
    for index, address in enumerate((0xe19,0xe1d,0xe21,0xe25,0xe29)):
        add(("timer_minutes","timer_tens_seconds","timer_seconds","timer_tenths","timer_frames")[index],address)
    for name,address in [("countdown",0x11c5),("ai_impulse_countdown",0xc6f),("ai_trick_selector",0xc75),("ai_suppression_counter",0x1277),("reward_cooldown",0xca7)]: add(name,address)
    add("queue_read_cursor",0xd11,1); add("queue_write_cursor",0xd13,1); add("learned_event_one_weight",0x2102,1)
    add("learned_feature_total",0x825,2,False,"cartridge_ram")
    return items


SEED_INVENTORY = _seed_inventory()


def _values(memory: dict[str, bytes]) -> dict[str, int]:
    result = {}
    for item in SEED_INVENTORY:
        raw = memory[item["memory"]]
        piece = raw[item["address"]:item["address"] + item["width"]]
        if len(piece) != item["width"]:
            raise ValueError(f"seed field is outside {item['memory']}: {item['name']}")
        result[item["name"]] = int.from_bytes(piece, "little", signed=item["signed"])
    return result


def capture_seed(manifest_path: Path, samples_path: Path, out: Path) -> dict[str, Any]:
    manifest_raw = manifest_path.read_bytes()
    manifest, case = _source_contract(json.loads(manifest_raw))
    if manifest["scenario_id"] != "race-crawler-zoom-zoo-3300-riding-fields":
        raise ValueError("the continuation seed must use the accepted primary case")
    samples_raw = samples_path.read_bytes()
    samples = json.loads(samples_raw)
    _validate_run(manifest, case, samples)
    if out.exists() and any(out.iterdir()):
        raise ValueError("refusing to overwrite a nonempty seed capture directory")
    rom = Path((ROOT / "local/rom-location.txt").read_text().strip())
    library = Path(samples["core"]["library"])
    if sha(rom.read_bytes()) != ROM_SHA256 or sha(library.read_bytes()) != samples["core"]["sha256"]:
        raise ValueError("ROM or core library identity differs from the replay capture")
    out.mkdir(parents=True, exist_ok=True)
    script = derive_script(manifest)
    with tempfile.TemporaryDirectory(prefix="fresh-seed-", dir=out) as system_dir:
        core = BsnesCore(library, Path(system_dir), script.get("core_options"))
        try:
            core.load(rom); core.set_serialization_method("Strict")
            for frame in range(INITIAL_FRAME + 1):
                for port, buttons in inputs_for_frame(script, frame).items(): core.set_inputs(port, buttons)
                core.run_frame()
            wram, cartridge = core.wram(), core.cartridge_ram()
            pid = __import__("os").getpid()
        finally:
            core.unload()
    expected = samples["frames"][INITIAL_FRAME]
    if sha(wram) != expected["wram_sha256"] or capture_fields(wram, range_fields(manifest)) != expected["fields"]:
        raise ValueError("fresh end-1649 WRAM differs from the complete replay capture")
    (out / "wram.bin").write_bytes(wram); (out / "cartridge-ram.bin").write_bytes(cartridge)
    report = {
        "schema_version": 1, "kind": "zoom_zoo_end_1649_seed", "scenario_id": manifest["scenario_id"],
        "after_frame": INITIAL_FRAME, "process_pid": pid, "rom_sha256": ROM_SHA256,
        "core_library_sha256": samples["core"]["sha256"], "manifest_sha256": sha(manifest_raw),
        "manifest_identity": _manifest_identity(manifest), "script_sha256": _script_sha(manifest),
        "samples_sha256": sha(samples_raw), "reference_sample_digest": samples["sample_digest"],
        "wram": {"size": len(wram), "sha256": sha(wram)},
        "cartridge_ram": {"size": len(cartridge), "sha256": sha(cartridge)},
        "inventory": SEED_INVENTORY, "values": _values({"wram": wram, "cartridge_ram": cartridge}),
        "queue_sha256": sha(wram[0x0ceb:0x0d0b]),
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def _validate_seeds(seeds: list[dict[str, Any]], initial_sample: dict[str, Any], manifest: dict[str, Any], core_library_sha256: str) -> dict[str, Any]:
    seed_manifest = validate_manifest(json.loads((ROOT / "tests/manifests/replay/race-crawler-zoom-zoo-3300-riding-fields.json").read_bytes()))
    if len(seeds) != 2 or seeds[0].get("process_pid") == seeds[1].get("process_pid"):
        raise ValueError("two distinct fresh end-1649 seed processes are required")
    exact = ("schema_version","kind","scenario_id","after_frame","rom_sha256","core_library_sha256","manifest_identity","script_sha256","reference_sample_digest","wram","cartridge_ram","inventory","values","queue_sha256")
    for seed in seeds:
        if seed.get("schema_version") != 1 or seed.get("kind") != "zoom_zoo_end_1649_seed" or seed.get("after_frame") != INITIAL_FRAME:
            raise ValueError("seed metadata differs from the end-1649 contract")
        if seed.get("rom_sha256") != ROM_SHA256 or seed.get("wram",{}).get("size") != 0x20000 or seed.get("cartridge_ram",{}).get("size") != 0x2000:
            raise ValueError("seed memory identity or size differs")
        if seed.get("core_library_sha256") != core_library_sha256:
            raise ValueError("seed core-library identity differs from the replay capture")
        if seed.get("scenario_id") != seed_manifest["scenario_id"] or seed.get("manifest_identity") != _manifest_identity(seed_manifest) or seed.get("script_sha256") != _script_sha(seed_manifest):
            raise ValueError("seed manifest or controller-script identity differs")
        if seed.get("reference_sample_digest") != CASES[seed_manifest["scenario_id"]]["sample_digest"]:
            raise ValueError("seed replay capture identity differs")
        if not isinstance(seed.get("samples_sha256"),str) or len(seed["samples_sha256"]) != 64:
            raise ValueError("seed samples-file identity is missing")
        if seed.get("wram",{}).get("sha256") != initial_sample["wram_sha256"]:
            raise ValueError("seed WRAM differs from the projected end-1649 row")
        if seed.get("inventory") != SEED_INVENTORY or set(seed.get("values",{})) != {item["name"] for item in SEED_INVENTORY}:
            raise ValueError("seed inventory is missing, duplicated or contradictory")
    if any(seeds[0].get(key) != seeds[1].get(key) for key in exact):
        raise ValueError("fresh end-1649 WRAM/cartridge observations differ")
    return {key: seeds[0][key] for key in exact if key not in ("schema_version","kind","scenario_id","after_frame")}


def freeze(manifest: dict[str, Any], first: dict[str, Any], second: dict[str, Any], seeds: list[dict[str, Any]]) -> dict[str, Any]:
    manifest, case = _source_contract(manifest)
    _validate_run(manifest, case, first); _validate_run(manifest, case, second)
    if first["process"]["pid"] == second["process"]["pid"]:
        raise ValueError("reference replay processes must be distinct")
    for key in ("sample_digest","av_digest","initial"):
        if first[key] != second[key]: raise ValueError(f"fresh reference {key} differs")
    if first["final"] != second["final"]: raise ValueError("fresh reference final states differ")
    for left, right in zip(first["frames"], second["frames"], strict=True):
        if left["fields"] != right["fields"]: raise ValueError(f"reference fields differ at frame {left['frame']}")
    rows = [[sample["frame"]] + project_sample(sample) for sample in first["frames"] if sample["frame"] >= INITIAL_FRAME]
    columns = ["frame"] + [item["name"] for item in PROJECTION]
    rows_sha = sha(json.dumps(rows, separators=(",",":"), ensure_ascii=True).encode())
    return {
        "schema_version": 1, "kind": "zoom_zoo_riding_reference_projection", "scenario_id": manifest["scenario_id"],
        "accepted_source_manifest": case["source"], "accepted_source_manifest_sha256": case["source_sha256"],
        "rom_sha256": ROM_SHA256, "core_commit": CORE_COMMIT, "core_patch_sha256": CORE_PATCH_SHA256,
        "reference_sample_digest": first["sample_digest"], "reference_av_digest": first["av_digest"],
        "reference_final_state_sha256": first["final"]["state_sha256"],
        "initial_frame": INITIAL_FRAME, "first_update_frame": FIRST_UPDATE_FRAME, "last_frame": LAST_FRAME,
        "projection": PROJECTION, "columns": columns, "rows_sha256": rows_sha,
        "seed": _validate_seeds(seeds, first["frames"][INITIAL_FRAME], manifest, first["core"]["sha256"]), "rows": rows,
    }


def verify_projection(document: dict[str, Any], require_frozen: bool = False) -> None:
    if document.get("schema_version") != 1 or document.get("kind") != "zoom_zoo_riding_reference_projection":
        raise ValueError("projection schema or kind differs")
    if document.get("scenario_id") not in CASES or document.get("projection") != PROJECTION:
        raise ValueError("projection identity or metadata differs")
    if document.get("columns") != ["frame"] + [item["name"] for item in PROJECTION]:
        raise ValueError("projection columns differ")
    rows = document.get("rows")
    if not isinstance(rows, list) or [row[0] for row in rows if isinstance(row,list) and row] != list(range(INITIAL_FRAME,LAST_FRAME+1)):
        raise ValueError("projection frames are missing, duplicated or out of order")
    if any(not isinstance(row,list) or len(row) != len(PROJECTION)+1 or any(type(value) is not int for value in row) for row in rows):
        raise ValueError("projection row width or value type differs")
    if document.get("rows_sha256") != sha(json.dumps(rows,separators=(",",":"),ensure_ascii=True).encode()):
        raise ValueError("projection row digest differs")
    seed = document.get("seed")
    if not isinstance(seed,dict) or seed.get("inventory") != SEED_INVENTORY or set(seed.get("values",{})) != {item["name"] for item in SEED_INVENTORY}:
        raise ValueError("projection seed inventory differs")
    if require_frozen:
        case=CASES[document["scenario_id"]]
        expected={"accepted_source_manifest":case["source"],"accepted_source_manifest_sha256":case["source_sha256"],
                  "rom_sha256":ROM_SHA256,"core_commit":CORE_COMMIT,"core_patch_sha256":CORE_PATCH_SHA256,
                  "reference_sample_digest":case["sample_digest"],"reference_av_digest":case["av_digest"],
                  "reference_final_state_sha256":case["final_state_sha256"],"replay_manifest_sha256":case["field_manifest_sha256"],
                  "rows_sha256":case["rows_sha256"],"initial_frame":INITIAL_FRAME,"first_update_frame":FIRST_UPDATE_FRAME,"last_frame":LAST_FRAME}
        if any(document.get(key)!=value for key,value in expected.items()):
            raise ValueError("projection frozen identity metadata differs")
        if seed.get("wram")!={"size":0x20000,"sha256":"9c80a52a47706929c2a4a08a012799eb1163c3a6ccfd985e9be3cacae78d805e"} or seed.get("cartridge_ram")!={"size":0x2000,"sha256":"cdd747a31846cfa03de238c622ea3154b396ef9d9d4541e2d6854b15866b7867"}:
            raise ValueError("projection frozen seed identity differs")


def verify_pair(primary: dict[str, Any], release: dict[str, Any], require_frozen: bool = True) -> dict[str, Any]:
    verify_projection(primary,require_frozen); verify_projection(release,require_frozen)
    if primary["scenario_id"] != "race-crawler-zoom-zoo-3300-riding-fields" or release["scenario_id"] != "race-crawler-zoom-zoo-3300-release-2500-2599-riding-fields":
        raise ValueError("projection pair has the wrong cases or order")
    if primary["seed"] != release["seed"]:
        raise ValueError("projection pair does not share the repeated end-1649 seed")
    first_divergence = None
    differing_fields: list[str] = []
    for left,right in zip(primary["rows"],release["rows"],strict=True):
        if left != right:
            first_divergence=left[0]
            differing_fields=[primary["columns"][i] for i in range(1,len(left)) if left[i]!=right[i]]
            break
    if first_divergence != 2500:
        raise ValueError(f"release perturbation first divergence must be frame 2500, got {first_divergence}")
    required={"joy1h_image","axis_h","player_x","player_x_residue","player_vx","player_vy","player_throttle"}
    if not required <= set(differing_fields):
        raise ValueError("frame-2500 input and original motion response are incomplete")
    finish_columns=[primary["columns"].index(name) for name in ("player_finished","opponent_finished","finish_delay_counter")]
    if any(row[index] != 0 for document in (primary,release) for row in document["rows"] for index in finish_columns):
        raise ValueError("finish/result transition occurs inside the riding projection")
    return {"first_divergence":first_divergence,"differing_fields":differing_fields,"finish_transition":False}


def _write_projection(path: Path, result: dict[str, Any]) -> None:
    if path.exists(): raise ValueError("output already exists; freeze into a new path and compare it")
    rows = result.pop("rows")
    text = json.dumps(result,indent=2)[:-2] + ',\n  "rows": [\n'
    text += ',\n'.join('    '+json.dumps(row,separators=(",",":")) for row in rows)
    text += '\n  ]\n}\n'; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest="command",required=True)
    capture = sub.add_parser("capture-seed"); capture.add_argument("--manifest",type=Path,required=True); capture.add_argument("--samples",type=Path,required=True); capture.add_argument("--out",type=Path,required=True)
    freezing = sub.add_parser("freeze"); freezing.add_argument("--manifest",type=Path,required=True); freezing.add_argument("--samples",type=Path,nargs=2,required=True); freezing.add_argument("--seeds",type=Path,nargs=2,required=True); freezing.add_argument("--out",type=Path,required=True)
    verify = sub.add_parser("verify"); verify.add_argument("--projection",type=Path,required=True)
    pair = sub.add_parser("verify-pair"); pair.add_argument("--primary",type=Path,required=True); pair.add_argument("--release",type=Path,required=True)
    args = parser.parse_args()
    try:
        if args.command == "capture-seed":
            result=capture_seed(args.manifest,args.samples,args.out); print(f"captured end-1649 WRAM {result['wram']['sha256']}; cartridge RAM {result['cartridge_ram']['sha256']}")
        elif args.command == "freeze":
            manifest_raw=args.manifest.read_bytes(); result=freeze(json.loads(manifest_raw),*(json.loads(path.read_bytes()) for path in args.samples),[json.loads(path.read_bytes()) for path in args.seeds]); result["replay_manifest_sha256"]=sha(manifest_raw); _write_projection(args.out,result); print(f"frozen {LAST_FRAME-INITIAL_FRAME+1} rows: {args.out}; sha256 {sha(args.out.read_bytes())}")
        elif args.command == "verify":
            verify_projection(json.loads(args.projection.read_bytes()),True); print(f"verified {args.projection}")
        else:
            result=verify_pair(json.loads(args.primary.read_bytes()),json.loads(args.release.read_bytes()));print(json.dumps(result,sort_keys=True))
    except (OSError,ValueError,KeyError,TypeError,IndexError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__": raise SystemExit(main())
