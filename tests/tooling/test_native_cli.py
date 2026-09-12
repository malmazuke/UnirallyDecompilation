"""Authored native process protocol checks; these do not run gameplay."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from unirally_lab.native import protocol
from unirally_lab.native.compare import NativeOutputError


def state_bytes(frame):
    return protocol.STATE_MAGIC + frame.to_bytes(4, "little") + bytes(319) + b"\x01\x00"


def output_range(first=10, last=12):
    rows = [f"{frame} " + " ".join(['0'] * 13) + " " + state_bytes(frame).hex()
            for frame in range(first, last + 1)]
    return protocol.HEADER + '\n' + '\n'.join(rows) + '\n'


def output():
    return output_range()


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
        self.assertEqual(states[-1], state_bytes(12))
        self.assertEqual(protocol.state_digests(states)['canonical_state_bytes'], 333)
        changed = copy.deepcopy(states)
        changed[1] = changed[1][:-1] + b'\x01'
        self.assertNotEqual(protocol.state_digests(states)['state_series_sha256'],
                            protocol.state_digests(changed)['state_series_sha256'])
        self.assertEqual(protocol.state_digests(states)['final_state_sha256'],
                         protocol.state_digests(changed)['final_state_sha256'])

    def test_malformed_or_incomplete_output_is_a_producer_failure(self):
        valid = output()
        lines = valid.splitlines()
        state = state_bytes(11).hex()
        malformed = ['', valid.replace(protocol.HEADER, 'v2'), '\n'.join(lines[:-1]),
                     valid + lines[-1] + '\n', valid.replace('11 ', '12 ', 1),
                     valid.replace(state, '0100'), valid.replace(state, 'FF'),
                     valid.replace(state, '01000b0'), valid.replace('10 0 ', '10 1_000 '),
                     valid.replace('10 0 ', '10 ')]
        for text in malformed:
            with self.subTest(text=text), self.assertRaises(NativeOutputError):
                protocol.parse_output(text, 10, 12)


class NativeCommandTests(unittest.TestCase):
    """Authored orchestration checks: the native producer is explicitly stubbed."""
    def setUp(self):
        import tempfile
        import json
        import hashlib
        from unirally_lab.native import commands
        from unirally_lab.procs import RunResult
        self.commands, self.Result = commands, RunResult
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.art = self.root / 'artifacts' / 'case'
        self.content = self.root / 'local' / 'content'
        self.content.mkdir(parents=True)
        self.seed = self.root / 'local' / 'seed.bin'
        self.seed.write_bytes(state_bytes(10))
        self.binary = self.root / 'build/lab-debug/src/core/movement_runner'
        self.binary.parent.mkdir(parents=True)
        self.binary.write_bytes(b'authored producer placeholder')
        self.reference = {'schema_version': 1, 'kind': 'frozen_reference_projection',
            'projection': copy.deepcopy(commands.compare.PROJECTION),
            'diagnostic_only': copy.deepcopy(commands.compare.DIAGNOSTIC),
            'columns': commands.compare.COLUMNS.copy(), 'initial_frame': 10,
            'first_update_frame': 11, 'last_frame': 12,
            'rows': [[frame] + [0] * 13 for frame in range(10, 13)],
            'rom_sha256': 'a' * 64}
        self.replay = {'inputs': {'controllers': [{'port': 0, 'events': []}, {'port': 1, 'events': []}]}}
        def binding(path):
            return {'path': str(path.relative_to(self.root)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        self.binding = binding
        files = []
        for name, size in commands.STATIC_SIZES.items():
            path = self.content / name
            path.write_bytes(bytes(size))
            files.append({'name': name, 'size': size, 'sha256': binding(path)['sha256']})
        self.runtime = {'schema_version': 1, 'rom_sha256': 'a' * 64,
            'seed': {**binding(self.seed), 'frame': 10},
            'content_dir': 'local/content', 'files': files}
        self.runtime_path = self.root / 'local/runtime.json'
        self.runtime_path.write_text(json.dumps(self.runtime))
        self.replay_path = self.root / 'replay.json'; self.replay_path.write_text('{}')
        self.expected_path = self.root / 'expected.json'; self.expected_path.write_text('{}')
        self.case = {'schema_version': 1, 'kind': 'native_movement_case',
            'replay': binding(self.replay_path), 'expected': binding(self.expected_path),
            'runtime': binding(self.runtime_path)}
        self.case_path = self.root / 'case.json'
        self.case_path.write_text(json.dumps(self.case))
        self.restore_invocations = 0

    def invoke(self, outputs=None, *, build=None, rebuild=True, producer_hook=None, **overrides):
        import argparse
        import contextlib
        import io
        import json
        from unittest.mock import patch
        args = argparse.Namespace(manifest=str(self.case_path), artifacts=str(self.art),
            report=None, preset='lab-debug', timeout=10, task='authored-test',
            from_frame=None, to_frame=None)
        for key, value in overrides.items(): setattr(args, key, value)
        outputs = outputs or [self.Result([], 0, output(), '', 0)] * 2
        build = build or self.Result([], 0, '', '', 0)
        def authored_build(*args):
            if build.returncode == 0 and rebuild:
                self.binary.write_bytes(b'authored rebuilt producer')
            return build
        output_iterator = iter(outputs)
        def authored_producer(*args, **kwargs):
            if producer_hook:
                producer_hook()
            return next(output_iterator)
        with patch.object(self.commands, 'ROOT', self.root), \
             patch.object(self.commands.compare, 'load_reference', return_value=(self.reference, self.replay)), \
             patch.object(self.commands, 'build_runner', side_effect=authored_build) as builder, \
             patch.object(self.commands, 'run_bounded', side_effect=authored_producer) as runner, \
             contextlib.redirect_stderr(io.StringIO()):
            code = self.commands.cmd_compare(args)
        report = self.art / 'report.json'
        return code, json.loads(report.read_text()) if report.exists() else None, builder, runner

    def invoke_restore(self, outputs=None, *, build=None, rebuild=True,
                       producer_hook=None, **overrides):
        import argparse
        import contextlib
        import io
        import json
        from unittest.mock import patch
        self.restore_invocations += 1
        art = self.root / 'artifacts' / f'restore-{self.restore_invocations}'
        args = argparse.Namespace(manifest=str(self.case_path), artifacts=str(art),
            report=None, preset='lab-debug', timeout=10, task='authored-restore-test',
            save_frame=[11])
        for key, value in overrides.items(): setattr(args, key, value)
        outputs = outputs or [
            self.Result([], 0, output_range(10, 12), '', 0),
            self.Result([], 0, output_range(10, 11), '', 0),
            self.Result([], 0, output_range(11, 12), '', 0),
        ]
        build = build or self.Result([], 0, '', '', 0)
        def authored_build(*args):
            if build.returncode == 0 and rebuild:
                self.binary.write_bytes(b'authored rebuilt restore producer')
            return build
        output_iterator = iter(outputs)
        def authored_producer(*args, **kwargs):
            if producer_hook:
                producer_hook()
            return next(output_iterator)
        with patch.object(self.commands, 'ROOT', self.root), \
             patch.object(self.commands.compare, 'load_reference', return_value=(self.reference, self.replay)), \
             patch.object(self.commands, 'build_runner', side_effect=authored_build) as builder, \
             patch.object(self.commands, 'run_bounded', side_effect=authored_producer) as runner, \
             contextlib.redirect_stderr(io.StringIO()):
            code = self.commands.cmd_restore_check(args)
        report = art / 'report.json'
        return code, json.loads(report.read_text()) if report.exists() else None, builder, runner, art

    def test_two_processes_receive_only_runtime_inputs_and_hash_canonical_state(self):
        code, rep, builder, runner = self.invoke()
        self.assertEqual(code, 0)
        self.assertEqual(runner.call_count, 2)
        self.assertEqual(rep['fresh_processes'], 2)
        self.assertTrue(rep['comparison']['identical'])
        self.assertEqual(rep['run1']['final_state_sha256'], rep['run2']['final_state_sha256'])
        for call in runner.call_args_list:
            argv = call.args[0]
            self.assertEqual(argv, [str(self.binary), '--seed', str(self.seed),
                '--content-dir', str(self.content), '--inputs', str(self.art / 'inputs.txt')])
        self.assertEqual(builder.call_count, 1)

    def test_bad_identity_and_missing_input_do_not_start_producer(self):
        self.seed.write_bytes(b'changed')
        code, _, builder, runner = self.invoke()
        self.assertEqual(code, 3); builder.assert_not_called(); runner.assert_not_called()
        import shutil
        shutil.rmtree(self.art)
        self.seed.unlink()
        code, _, builder, runner = self.invoke()
        self.assertEqual(code, 2); builder.assert_not_called(); runner.assert_not_called()

    def test_projection_match_does_not_hide_nondeterministic_internal_state(self):
        lines = output().splitlines()
        lines[-1] = lines[-1][:-2] + '01'
        changed = '\n'.join(lines) + '\n'
        code, rep, _, _ = self.invoke([self.Result([], 0, output(), '', 0), self.Result([], 0, changed, '', 0)])
        self.assertEqual(code, 1)
        self.assertTrue(rep['comparison']['identical'])
        self.assertFalse(next(c for c in rep['checks'] if c['name']=='native_fresh_process_repeatability')['outcome']=='passed')

    def test_first_divergence_and_prior_input_survive_command_layer(self):
        changed = output().replace('11 0 ', '11 1 ', 1)
        code, rep, _, _ = self.invoke([self.Result([], 0, changed, '', 0)] * 2)
        self.assertEqual(code, 1)
        self.assertEqual(rep['comparison']['first_divergence']['frame'], 11)
        self.assertEqual(rep['comparison']['first_divergence']['prior_sample']['frame'], 10)

    def test_truncation_wrong_seed_crash_and_timeout_cannot_pass(self):
        import shutil
        bad_seed = output().replace(self.seed.read_bytes().hex(), (self.seed.read_bytes()[:-1] + b'\x02').hex())
        for result, expected in [(self.Result([], 0, '\n'.join(output().splitlines()[:-1]), '', 0), 1),
                (self.Result([], 0, bad_seed, '', 0), 1),
                (self.Result([], -9, output(), 'killed', 0), 1),
                (self.Result([], None, output(), '', 10, timed_out=True), 4)]:
            with self.subTest(expected=expected, result=result):
                if self.art.exists(): shutil.rmtree(self.art)
                code, _, _, runner = self.invoke([result])
                self.assertEqual(code, expected); self.assertEqual(runner.call_count, 1)

    def test_build_failure_and_invalid_window_do_not_start_producer(self):
        code, _, _, runner = self.invoke(build=self.Result([], 2, '', 'missing compiler', 0))
        self.assertEqual(code, 2); runner.assert_not_called()
        import shutil
        shutil.rmtree(self.art)
        code, _, builder, runner = self.invoke(from_frame=12, to_frame=11)
        self.assertEqual(code, 3); builder.assert_not_called(); runner.assert_not_called()

    def test_output_collision_and_nonfinite_timeout_reject_before_writing(self):
        code, _, builder, runner = self.invoke(report=str(self.art / 'inputs.txt'))
        self.assertEqual(code, 3); builder.assert_not_called(); runner.assert_not_called()
        code, _, _, runner = self.invoke(report=str(self.art / 'run1.txt/report.json'))
        self.assertEqual(code, 3); runner.assert_not_called()
        code, _, _, runner = self.invoke(timeout=float('nan'))
        self.assertEqual(code, 3); runner.assert_not_called()
        self.assertFalse(self.art.exists())


    def test_noop_build_cannot_reuse_a_stale_native_executable(self):
        code, _, _, runner = self.invoke(rebuild=False)
        self.assertEqual(code, 2)
        self.assertFalse(self.binary.exists())
        runner.assert_not_called()

    def test_content_added_by_first_process_blocks_second_process(self):
        def mutate():
            (self.content / 'producer-cache.bin').write_bytes(b'unbound')
        code, _, _, runner = self.invoke(producer_hook=mutate)
        self.assertEqual(code, 1)
        self.assertEqual(runner.call_count, 1)

    def test_restore_check_uses_fresh_prefix_and_suffix_processes(self):
        code, rep, builder, runner, art = self.invoke_restore()
        self.assertEqual(code, 0)
        self.assertEqual(builder.call_count, 1)
        self.assertEqual(runner.call_count, 3)
        self.assertEqual(rep['fresh_processes'], 3)
        self.assertEqual(rep['save_frames'], [11])
        self.assertEqual(rep['boundaries']['11']['saved_state_bytes'], 333)
        self.assertEqual((art / 'state-11.bin').read_bytes(), state_bytes(11))
        calls = runner.call_args_list
        self.assertEqual(calls[0].args[0][1:3], ['--seed', str(self.seed)])
        self.assertEqual(calls[1].args[0][1:3], ['--seed', str(self.seed)])
        self.assertEqual(calls[2].args[0][1:3], ['--seed', str(art / 'state-11.bin')])

    def test_restore_check_rejects_invalid_boundaries_before_build(self):
        for frames in ([10], [12], [11, 11], []):
            with self.subTest(frames=frames):
                code, _, builder, runner, _ = self.invoke_restore(save_frame=frames)
                self.assertEqual(code, 3)
                builder.assert_not_called()
                runner.assert_not_called()

    def test_restore_check_rejects_changed_prefix_and_suffix_state(self):
        changed_prefix = output_range(10, 11).replace(
            state_bytes(11).hex(), state_bytes(11)[:-2].hex() + '0200')
        code, rep, _, runner, _ = self.invoke_restore([
            self.Result([], 0, output(), '', 0),
            self.Result([], 0, changed_prefix, '', 0)])
        self.assertEqual(code, 1); self.assertEqual(runner.call_count, 2)
        self.assertTrue(any(c['name']=='native_output' for c in rep['checks']))

        changed_suffix = output_range(11, 12).replace(
            state_bytes(12).hex(), state_bytes(12)[:-2].hex() + '0200')
        code, rep, _, runner, _ = self.invoke_restore([
            self.Result([], 0, output(), '', 0),
            self.Result([], 0, output_range(10, 11), '', 0),
            self.Result([], 0, changed_suffix, '', 0)])
        self.assertEqual(code, 1); self.assertEqual(runner.call_count, 3)
        self.assertFalse(next(c for c in rep['checks'] if c['name']=='continuation_11_identical')['outcome']=='passed')
        divergence = rep['boundaries']['11']['first_divergence']
        self.assertEqual(divergence['frame'], 12)
        self.assertEqual(divergence['prior_frame'], 11)
        self.assertEqual(divergence['canonical_byte_offsets'], [331])

    def test_restore_check_rejects_malformed_boundary_state(self):
        wrong_frame = output_range(10, 11).replace(
            state_bytes(11).hex(), state_bytes(10).hex())
        wrong_width = output_range(10, 11).replace(
            state_bytes(11).hex(), (state_bytes(11) + b'\x00').hex())
        for prefix in (wrong_frame, wrong_width):
            with self.subTest(prefix=prefix[-32:]):
                code, _, _, runner, _ = self.invoke_restore([
                    self.Result([], 0, output(), '', 0),
                    self.Result([], 0, prefix, '', 0)])
                self.assertEqual(code, 1); self.assertEqual(runner.call_count, 2)

    def test_restore_check_rehashes_inputs_between_processes(self):
        mutated = False
        def mutate_once():
            nonlocal mutated
            if not mutated:
                (self.content / 'producer-cache.bin').write_bytes(b'unbound')
                mutated = True
        code, rep, _, runner, _ = self.invoke_restore(producer_hook=mutate_once)
        self.assertEqual(code, 1); self.assertEqual(runner.call_count, 1)
        self.assertTrue(any(c['name']=='native_output' for c in rep['checks']))

    def test_restore_check_rejects_report_outside_artifacts(self):
        code, _, builder, runner, _ = self.invoke_restore(
            report=str(self.root / 'outside.json'))
        self.assertEqual(code, 3); builder.assert_not_called(); runner.assert_not_called()

    def test_restore_check_propagates_crash_timeout_and_build_failure(self):
        for result, expected in ((self.Result([], -9, '', 'crash', 0), 1),
                                 (self.Result([], None, '', '', 10, timed_out=True), 4)):
            with self.subTest(expected=expected):
                code, rep, _, runner, _ = self.invoke_restore([result])
                self.assertEqual(code, expected); self.assertEqual(runner.call_count, 1)
                self.assertEqual(rep['fresh_processes'] if 'fresh_processes' in rep else 0, 0)
        code, _, _, runner, _ = self.invoke_restore(
            build=self.Result([], 2, '', 'missing compiler', 0))
        self.assertEqual(code, 2); runner.assert_not_called()
