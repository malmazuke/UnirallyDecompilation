import unittest

from unirally_lab.finish.analyze import AnalysisError, analyze


def samples(digest, changed=False):
    frames = []
    for frame in range(3):
        value = "01" if changed and frame == 2 else "00"
        frames.append({"frame": frame, "wram_sha256": value, "registers": {}, "fields": {"axis": value}})
    return {"sample_digest": digest, "frames": frames}


def access(player, opponent, first, last):
    fields = ["pc", "kind", "address", "width", "count", "first_frame", "last_frame", "values"]
    rows = [
        [0x81823B, 1, 0x0EFF, 2, 1, player, player, [1]],
        [0x81823B, 1, 0x0F01, 2, 1, opponent, opponent, [1]],
        [0x83E81D, 1, 0x0F0F, 2, 2, first, last, [1, 2]],
        [0x818AA1, 0, 0x7F0010, 2, 3, 0, 2, None],
    ]
    return {"access_fields": fields, "accesses": rows, "frames": {"start": 3000, "end": 3679}}


class FinishAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.contract = {
            "samples": {"continuous": "a", "variation": "b"}, "first_divergence_frame": 2,
            "finish": {"player_address": 0x0EFF, "opponent_address": 0x0F01,
                       "flag_writer_pc": 0x81823B, "counter_address": 0x0F0F,
                       "counter_writer_pc": 0x83E81D, "counter_updates": 2,
                       "continuous": {"player_frame": 10, "opponent_frame": 11,
                                      "counter_first": 11, "counter_last": 12},
                       "variation": {"player_frame": 20, "opponent_frame": 11,
                                     "counter_first": 20, "counter_last": 21}},
            "coverage_delta": {"baseline_scenario": "short", "bytes_only_here": 4,
                               "bytes_only_in_baseline": 0, "new_ranges": 1, "new_entry_points": 2},
            "content_delta": {"channel_transfers": 1, "block_moves": 0, "block_move_bytes": 0,
                              "destinations_pairable": 1, "destinations_paired": 1},
            "decoded_track_length": 32,
        }
        self.coverage = {"compared_to": {"baseline_scenario": "short", "bytes_only_here": 4,
                                          "bytes_only_in_baseline": 0, "new_ranges": [{}],
                                          "new_entry_points": [{}, {}]}}
        self.content = {"items": [{"id": "track-data", "expected": {"length": 32}}]}
        self.provenance = {"summary": {"channel_transfers": 1, "block_moves": 0, "block_move_bytes": 0,
                                        "destinations_pairable": 1, "destinations_paired": 1}}

    def run_analysis(self):
        return analyze(self.contract, samples("a"), samples("b", True), access(10, 11, 11, 12),
                       access(20, 11, 20, 21), self.coverage, self.content, self.provenance)

    def test_exact_contract_passes(self):
        result = self.run_analysis()
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["decoded_track_suffix_reads"]["outside_decoded_track"], 0)

    def test_changed_finish_frame_fails(self):
        self.contract["finish"]["continuous"]["player_frame"] = 9
        result = self.run_analysis()
        self.assertEqual(result["status"], "failed")
        self.assertEqual([c for c in result["checks"] if c["outcome"] == "failed"][0]["name"],
                         "continuous_player_finish_frame")

    def test_missing_writer_is_invalid(self):
        bad = access(10, 11, 11, 12)
        bad["accesses"][0][0] = 0x81823C
        with self.assertRaises(AnalysisError):
            analyze(self.contract, samples("a"), samples("b", True), bad, access(20, 11, 20, 21),
                    self.coverage, self.content, self.provenance)

    def test_track_read_outside_decoded_block_fails(self):
        bad = access(10, 11, 11, 12)
        bad["accesses"][-1][2] = 0x7F0020
        result = analyze(self.contract, samples("a"), samples("b", True), bad, access(20, 11, 20, 21),
                         self.coverage, self.content, self.provenance)
        self.assertEqual(result["status"], "failed")

    def test_changed_digest_and_coverage_fail(self):
        self.contract["samples"]["continuous"] = "wrong"
        self.contract["coverage_delta"]["bytes_only_here"] = 5
        result = self.run_analysis()
        failures = {check["name"] for check in result["checks"] if check["outcome"] == "failed"}
        self.assertEqual(result["status"], "failed")
        self.assertEqual(failures, {"continuous_sample_digest", "coverage_bytes_only_here"})

    def test_changed_provenance_totals_fail(self):
        self.provenance["summary"]["channel_transfers"] = 0
        self.provenance["summary"]["destinations_paired"] = 0
        result = self.run_analysis()
        failures = {check["name"] for check in result["checks"] if check["outcome"] == "failed"}
        self.assertEqual(result["status"], "failed")
        self.assertEqual(failures, {"content_channel_transfers", "content_destinations_paired"})


if __name__ == "__main__":
    unittest.main()
