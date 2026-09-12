"""Authored arithmetic boundaries, not original gameplay expectations."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from unirally_lab.native.speed_research.contract import SpeedState, SpeedContext, update_speed


def context(**changes):
    values = dict(rider=1, skip=0, drag=0, pose_byte=64, start_override=0,
                  ai_mode=1, player_progress=0, opponent_progress=0, ai_adjustment=0,
                  adjustment_limit=96, base_cap=448, counter=3, friction=2, cartridge_mode=0)
    return SpeedContext(**(values | changes))


def update(state, **changes):
    return update_speed(state, context(**changes), bytes([3] * 9), [4] * 9)


class SpeedResearchTests(unittest.TestCase):
    def test_caps_use_boost_before_counter_decay(self):
        result = update(SpeedState(600, 1000, 128, 10, 0))
        self.assertEqual(result, SpeedState(512, 832, 124, 9, 0))
        result = update(SpeedState((-600) & 65535, (-1000) & 65535, 128, 10, 0))
        self.assertEqual(result, SpeedState((-512) & 65535, (-832) & 65535, 124, 9, 0))

    def test_counter_mask_and_decay_underflow(self):
        self.assertEqual(update(SpeedState(400, 0, 128, 0, 0), counter=2).boost, 128)
        self.assertEqual(update(SpeedState(400, 0, 3, 0, 0)).boost, 3)

    def test_progress_increment_precedes_cap_and_limit_is_exclusive(self):
        state = SpeedState(600, 0, 0, 0, 0)
        first = update(state, rider=0, opponent_progress=1)
        self.assertEqual((first.horizontal, first.progress_adjustment), (448, 1))
        first.horizontal = 600
        second = update(first, rider=0, opponent_progress=1)
        self.assertEqual((second.horizontal, second.progress_adjustment), (449, 2))
        state.progress_adjustment = 95
        self.assertEqual(update(state, rider=0, opponent_progress=1).progress_adjustment, 95)

    def test_progress_difference_and_decrement_wrap_like_words(self):
        state = SpeedState(500, 0, 0, 0, 0)
        wrapped = update(state, rider=0, player_progress=65535, opponent_progress=0)
        self.assertEqual(wrapped.progress_adjustment, 1)
        ahead = update(state, rider=0, player_progress=1)
        self.assertEqual((ahead.progress_adjustment, ahead.horizontal), (0, 448))

    def test_start_override_bypasses_adjustment_but_not_decay(self):
        result = update(SpeedState(600, 1000, 128, 10, 12), rider=0,
                        opponent_progress=10, start_override=256)
        self.assertEqual(result, SpeedState(488, 808, 124, 9, 12))

    def test_fast_decay_precedes_cap_without_modifying_velocity_directly(self):
        result = update(SpeedState(600, 0, 32, 0, 0), pose_byte=176)
        self.assertEqual((result.horizontal, result.boost), (456, 12))

    def test_signed_friction_preserves_original_negative_one_boundary(self):
        self.assertEqual(update(SpeedState(65535, 0, 0, 0, 0), friction=1).horizontal, 65535)
        self.assertEqual(update(SpeedState(1, 0, 0, 0, 0), friction=1).horizontal, 0)

    def test_skip_and_explicit_unsupported_mode(self):
        state = SpeedState(600, 1000, 128, 10, 12)
        self.assertEqual(update(state, skip=1, cartridge_mode=2), state)
        with self.assertRaises(ValueError):
            update(state, cartridge_mode=2)


class SpeedEvidenceTests(unittest.TestCase):
    def test_mode_requires_one_known_read_with_correct_location_and_width(self):
        from unirally_lab.native.speed_research.probe import cartridge_mode
        row = [50, 0x82a81a, 'read', 0x77074a, 2, 0x1200]
        valid = [(50, 'r', row)]
        self.assertEqual(cartridge_mode(valid, 40, 60), 0)
        malformed = [[], valid + valid]
        for index, value in [(3, 0x770750), (4, 1), (5, None), (5, False), (5, -1), (5, 65536)]:
            changed = row.copy()
            changed[index] = value
            malformed.append([(50, 'r', changed)])
        for events in malformed:
            with self.subTest(events=events), self.assertRaises(ValueError):
                cartridge_mode(events, 40, 60)
