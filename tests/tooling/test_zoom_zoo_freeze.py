"""ROM-free integrity checks for the additive M4-04 reference freezer."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from unirally_lab.native.freeze_zoom_zoo import (  # noqa: E402
    CASES, CORE_LIBRARY_SHA256, EXPECTED_RANGES, PROJECTION, SEED_INVENTORY, _manifest_identity, _source_contract,
    _write_projection, freeze, sha, verify_pair, verify_projection,
)
from unirally_lab.reference.bsnes import DEFAULT_OPTIONS  # noqa: E402
from unirally_lab.replay.manifest import derive_script, range_fields  # noqa: E402


class ZoomZooFreezeTests(unittest.TestCase):
    def fixture(self):
        path = ROOT / "tests/manifests/replay/race-crawler-zoom-zoo-3300-riding-fields.json"
        manifest = json.loads(path.read_text())
        case = CASES[manifest["scenario_id"]]
        fields = {name: "00" * length for name, _start, length in EXPECTED_RANGES}
        frames = [{"frame": frame, "wram_sha256": "seed-wram" if frame == 1649 else "wram", "fields": fields}
                  for frame in range(3300)]
        script_raw = (json.dumps(derive_script(manifest), indent=2, sort_keys=True) + "\n").encode()
        first = {
            "script": {"sha256": hashlib.sha256(script_raw).hexdigest()}, "fields": range_fields(manifest),
            "sample_digest": case["sample_digest"], "av_digest": case["av_digest"], "initial": {"wram_sha256":"initial","cartridge_ram_sha256":"initial-sram"},
            "rom": {"sha256": manifest["rom"]["sha256"]}, "core": {"serialization_method":"Strict","options":DEFAULT_OPTIONS,"sha256":CORE_LIBRARY_SHA256},
            "process": {"pid": 1}, "final": {"state_sha256":case["final_state_sha256"]}, "frames": frames,
        }
        second = dict(first); second["process"]={"pid":2}; second["frames"]=[dict(item) for item in frames]
        values = {item["name"]: 0 for item in SEED_INVENTORY}
        seed = {"schema_version":1,"kind":"zoom_zoo_end_1649_seed","scenario_id":manifest["scenario_id"],"after_frame":1649,
                "process_pid":3,"rom_sha256":manifest["rom"]["sha256"],"core_library_sha256":CORE_LIBRARY_SHA256,
                "manifest_identity":_manifest_identity(manifest),"script_sha256":hashlib.sha256(script_raw).hexdigest(),
                "reference_sample_digest":case["sample_digest"],"samples_sha256":"a"*64,
                "wram":{"size":0x20000,"sha256":"seed-wram"},"cartridge_ram":{"size":0x2000,"sha256":"sram"},
                "inventory":SEED_INVENTORY,"values":values,"queue_sha256":"queue"}
        seed2=copy.deepcopy(seed);seed2["process_pid"]=4
        return manifest,first,second,[seed,seed2]

    def test_tracked_manifests_preserve_accepted_scripts_and_whole_state(self):
        for path in sorted((ROOT / "tests/manifests/replay").glob("race-crawler-zoom-zoo-3300*riding-fields.json")):
            manifest,case=_source_contract(json.loads(path.read_text()))
            source=json.loads((ROOT/case["source"]).read_text())
            self.assertEqual(manifest["inputs"],source["inputs"])
            self.assertEqual(manifest["expected"],source["expected"])

    def test_freeze_is_complete_and_seed_bound(self):
        manifest,first,second,seeds=self.fixture();result=freeze(manifest,first,second,seeds)
        self.assertEqual([row[0] for row in result["rows"]],list(range(1649,3300)))
        self.assertTrue(all(len(row)==len(PROJECTION)+1 for row in result["rows"]))
        verify_projection(result)

    def test_wrong_script_core_options_or_manifest_source_fails(self):
        manifest,first,second,seeds=self.fixture();first["script"]["sha256"]="wrong"
        with self.assertRaisesRegex(ValueError,"input script"): freeze(manifest,first,second,seeds)
        manifest,first,second,seeds=self.fixture();second["core"]["options"]={"Some Option":"changed"}
        with self.assertRaisesRegex(ValueError,"core binary, options"): freeze(manifest,first,second,seeds)
        manifest,first,second,seeds=self.fixture();manifest["inputs"]["controllers"][0]["events"][0]["to"]+=1
        with self.assertRaisesRegex(ValueError,"controller schedule"): freeze(manifest,first,second,seeds)
        manifest,first,second,seeds=self.fixture();second["rom"]["sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"ROM identity"): freeze(manifest,first,second,seeds)
        manifest,first,second,seeds=self.fixture();second["sample_digest"]="0"*64
        with self.assertRaisesRegex(ValueError,"whole-state or A/V identity"): freeze(manifest,first,second,seeds)
        manifest,first,second,seeds=self.fixture();second["av_digest"]="0"*64
        with self.assertRaisesRegex(ValueError,"whole-state or A/V identity"): freeze(manifest,first,second,seeds)
        manifest,first,second,seeds=self.fixture();second["core"]["sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"core binary"): freeze(manifest,first,second,seeds)

    def test_missing_duplicate_frame_and_field_width_fail(self):
        manifest,first,second,seeds=self.fixture();second["frames"].pop(100)
        with self.assertRaisesRegex(ValueError,"exactly 0..3299"): freeze(manifest,first,second,seeds)
        manifest,first,second,seeds=self.fixture();second["frames"][100]["frame"]=99
        with self.assertRaisesRegex(ValueError,"exactly 0..3299"): freeze(manifest,first,second,seeds)
        manifest,first,second,seeds=self.fixture();mutated=dict(second["frames"][50]["fields"]);mutated["positions"]="00";second["frames"][50]["fields"]=mutated
        with self.assertRaisesRegex(ValueError,"row width"): freeze(manifest,first,second,seeds)

    def test_missing_or_contradictory_seed_fails(self):
        manifest,first,second,seeds=self.fixture();seeds[1]["process_pid"]=seeds[0]["process_pid"]
        with self.assertRaisesRegex(ValueError,"distinct fresh"): freeze(manifest,first,second,seeds)
        manifest,first,second,seeds=self.fixture();del seeds[1]["values"][next(iter(seeds[1]["values"]))]
        with self.assertRaisesRegex(ValueError,"seed inventory"): freeze(manifest,first,second,seeds)
        manifest,first,second,seeds=self.fixture();seeds[1]["cartridge_ram"]["sha256"]="changed"
        with self.assertRaisesRegex(ValueError,"observations differ"): freeze(manifest,first,second,seeds)
        manifest,first,second,seeds=self.fixture();seeds[1]["core_library_sha256"]="changed"
        with self.assertRaisesRegex(ValueError,"core-library identity"): freeze(manifest,first,second,seeds)

    def test_projection_metadata_rows_and_digest_are_verified(self):
        manifest,first,second,seeds=self.fixture();result=freeze(manifest,first,second,seeds)
        for mutation, message in [
            (lambda d:d["projection"][0].update(length=2),"metadata"),
            (lambda d:d["rows"].pop(),"frames"),
            (lambda d:d["rows"][0].pop(),"row width"),
            (lambda d:d.update(rows_sha256="wrong"),"row digest"),
        ]:
            with self.subTest(message=message):
                candidate=copy.deepcopy(result);mutation(candidate)
                with self.assertRaisesRegex(ValueError,message):verify_projection(candidate)

    def test_output_refuses_overwrite(self):
        manifest,first,second,seeds=self.fixture();result=freeze(manifest,first,second,seeds)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"projection.json";path.write_text("existing")
            with self.assertRaisesRegex(ValueError,"already exists"):_write_projection(path,result)

    def test_pair_verifier_binds_exact_boundary_response_and_no_finish(self):
        manifest,first,second,seeds=self.fixture();primary=freeze(manifest,first,second,seeds)
        release=copy.deepcopy(primary);release["scenario_id"]="race-crawler-zoom-zoo-3300-release-2500-2599-riding-fields"
        index=2500-1649
        for name in ("joy1h_image","axis_h","player_x","player_x_residue","player_vx","player_vy","player_throttle"):
            release["rows"][index][release["columns"].index(name)]+=1
        release["rows_sha256"]=sha(json.dumps(release["rows"],separators=(",",":")).encode())
        self.assertEqual(verify_pair(primary,release,False)["first_divergence"],2500)
        release["rows"][index-1][1]+=1;release["rows_sha256"]=sha(json.dumps(release["rows"],separators=(",",":")).encode())
        with self.assertRaisesRegex(ValueError,"frame 2500"):verify_pair(primary,release,False)


if __name__ == "__main__": unittest.main()
