"""Authored native process protocol checks; these do not run gameplay."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from unirally_lab.native import protocol
from unirally_lab.native.compare import NativeOutputError


def output():
    rows = [f"{frame} " + " ".join(['0'] * 13) + " " + (protocol.STATE_MAGIC + frame.to_bytes(4, "little") + b"\x01\x00").hex() for frame in range(10, 13)]
    return protocol.HEADER + '\n' + '\n'.join(rows) + '\n'


class NativeProtocolTests(unittest.TestCase):
    def test_input_stream_includes_both_ports_and_no_reference_values(self):
        manifest = {'inputs': {'controllers': [
            {'port': 0, 'events': [{'from': 10, 'to': 11, 'buttons': ['right', 'b']}]},
            {'port': 1, 'events': [{'from': 12, 'to': 12, 'buttons': ['left', 'a']}]},
        ]}}
        self.assertEqual(protocol.input_text(manifest, 10, 12), '11 129 0\n12 0 320\n')

    def test_complete_output_and_hashes_use_canonical_bytes(self):
        rows, states = protocol.parse_output(output(), 10, 12)
        self.assertEqual([row[0] for row in rows], [10, 11, 12])
        self.assertEqual(states[-1], protocol.STATE_MAGIC + (12).to_bytes(4, 'little') + b'\x01\x00')
        self.assertEqual(protocol.state_digests(states)['canonical_state_bytes'], 14)
        changed = copy.deepcopy(states)
        changed[1] = changed[1][:-1] + b'\x01'
        self.assertNotEqual(protocol.state_digests(states)['state_series_sha256'],
                            protocol.state_digests(changed)['state_series_sha256'])
        self.assertEqual(protocol.state_digests(states)['final_state_sha256'],
                         protocol.state_digests(changed)['final_state_sha256'])

    def test_malformed_or_incomplete_output_is_a_producer_failure(self):
        valid = output()
        lines = valid.splitlines()
        state = (protocol.STATE_MAGIC + (11).to_bytes(4, 'little') + b'\x01\x00').hex()
        malformed = ['', valid.replace(protocol.HEADER, 'v2'), '\n'.join(lines[:-1]),
                     valid + lines[-1] + '\n', valid.replace('11 ', '12 ', 1),
                     valid.replace(state, '0100'), valid.replace(state, 'FF'),
                     valid.replace(state, '01000b0'), valid.replace('10 0 ', '10 1_000 '),
                     valid.replace('10 0 ', '10 ')]
        for text in malformed:
            with self.subTest(text=text), self.assertRaises(NativeOutputError):
                protocol.parse_output(text, 10, 12)
