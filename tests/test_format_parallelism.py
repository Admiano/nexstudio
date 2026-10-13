"""All formats must start before any completes, including real child processes."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'services/studio-family-engines'))
from parallel_aspects import render_aspects

CHILD = '''
import json, pathlib, sys, time
root, aspect, output = pathlib.Path(sys.argv[1]), sys.argv[2], pathlib.Path(sys.argv[3])
start = time.perf_counter()
(root / ('started-' + aspect.replace(':', 'x'))).write_text('started')
deadline = start + 5
while len(list(root.glob('started-*'))) < 3:
    if time.perf_counter() > deadline:
        raise RuntimeError('The three format processes did not overlap')
    time.sleep(0.01)
output.parent.mkdir(parents=True, exist_ok=True)
output.write_bytes(b'format-process-test')
(root / (aspect.replace(':', 'x') + '.json')).write_text(json.dumps({'start': start, 'end': time.perf_counter()}))
'''


class FormatParallelism(unittest.TestCase):
    def test_both_editorial_entrypoints_render_all_formats_together_and_keep_their_gates(self):
        for engine in ['explainer-locks', 'editorial-motion-v2']:
            with self.subTest(engine=engine), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                fixture = root / 'fixtures/test-film'
                fixture.mkdir(parents=True)
                (fixture / 'treatment.json').write_text('{}')
                module_spec = importlib.util.spec_from_file_location(engine.replace('-', '_'), ROOT / 'engine_sources' / engine / 'tools/regression_pack.py')
                pack = importlib.util.module_from_spec(module_spec)
                module_spec.loader.exec_module(pack)
                pack.ROOT = root

                def compile_fixture(treatment, destination):
                    destination.mkdir(parents=True)
                    return {'status': 'PASS'}

                def render(plan, destination, fps):
                    aspect = plan.stem.removeprefix('plan_')
                    subprocess.run([sys.executable, '-c', CHILD, str(root), aspect, str(destination / f'{aspect}.mp4')], check=True)
                    manifest = {'page_errors': [], 'captions_burned': 1, 'native_profile': True,
                                'audio': {'music': {'status': 'BOUND'}, 'loudness': {'integrated_lufs': -16, 'target_lufs': -16, 'true_peak_dbtp': -2, 'ceiling_dbtp': -1}},
                                'authorship': {'codes': [], 'findings': [], 'longest_static_hold_ms': 0},
                                'mp4': str(destination / f'{aspect}.mp4'), 'mp4_sha256': 'test-only'}
                    (destination / f'render_{aspect}.json').write_text(json.dumps(manifest))
                    return manifest

                argv = ['regression_pack.py', '--out', str(root / 'out'), '--fixture', 'test-film']
                with patch.object(sys, 'argv', argv), patch.object(pack, 'compile_fixture', side_effect=compile_fixture) as compiler, patch.object(pack, 'render', side_effect=render), patch.object(pack, 'measure_frames', return_value={'frames': 10, 'blank_ms': 0, 'frozen_longest_ms': 0}):
                    self.assertEqual(pack.main(), 0)
                compiler.assert_called_once()
                report = json.loads((root / 'out/report.json').read_text())
                self.assertEqual(report['failures'], 0)
                self.assertEqual(set(report['films'][0]['aspects']), {'16x9', '1x1', '9x16'})
                events = [json.loads((root / f'{aspect}.json').read_text()) for aspect in ['16x9', '1x1', '9x16']]
                self.assertLess(max(event['start'] for event in events), min(event['end'] for event in events))

    def test_presenter_composition_starts_all_formats_together(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'request.json').write_text(json.dumps({'aspects': ['16:9', '1:1', '9:16']}))
            module_spec = importlib.util.spec_from_file_location('presenter_job_parallel_test', ROOT / 'scripts/presenter-job.py')
            job = importlib.util.module_from_spec(module_spec)
            with patch.object(sys, 'argv', ['presenter-job.py', str(root)]):
                module_spec.loader.exec_module(job)
            try:
                def launch(command, **kwargs):
                    aspect = command[command.index('--aspect') + 1]
                    destination = command[command.index('--out') + 1]
                    subprocess.run([sys.executable, '-c', CHILD, str(root), aspect, str(destination)], check=True)
                with patch.object(job, 'run', side_effect=launch):
                    outputs = job.compose(root / 'frames')
                self.assertEqual(set(outputs), {'16x9', '1x1', '9x16'})
                events = [json.loads((root / f'{aspect}.json').read_text()) for aspect in ['16x9', '1x1', '9x16']]
                self.assertLess(max(event['start'] for event in events), min(event['end'] for event in events))
            finally:
                job.LOG.close()

    def test_both_whiteboard_entrypoints_launch_all_three_child_processes_together(self):
        for engine, subtype in [('whiteboard-board-scenes', 'board-scenes'), ('whiteboard-v3-runtime', 'kinetic')]:
            with self.subTest(engine=engine), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                module_spec = importlib.util.spec_from_file_location(engine.replace('-', '_'), ROOT / 'engine_sources' / engine / 'tools/nexstudio_job.py')
                job = importlib.util.module_from_spec(module_spec)
                module_spec.loader.exec_module(job)
                script, plan, voice, words = [root / name for name in ['script.txt', 'plan.json', 'voice.wav', 'words.json']]
                script.write_text('Clay is shaped into a slab.')
                plan.write_text('{}')
                voice.write_bytes(b'shared-narration')
                words.write_text('[]')
                out = root / 'out'

                def launch(command, **kwargs):
                    aspect = command[command.index('--ratio') + 1]
                    destination = Path(command[command.index('--out-dir') + 1]) / 'video.mp4'
                    return subprocess.run([sys.executable, '-c', CHILD, str(root), aspect, str(destination)], capture_output=True, text=True, check=True)

                argv = ['nexstudio_job.py', '--type', subtype, '--script', str(script), '--aspects', '16:9,1:1,9:16', '--out', str(out), '--job-id', 'test-parallel']
                with patch.object(sys, 'argv', argv), patch.object(job, 'build_voice', return_value=(voice, words)) as synth, patch.object(job, 'build_plan', return_value=plan) as author, patch.object(job, 'sh', side_effect=launch):
                    self.assertEqual(job.main(), 0)
                synth.assert_called_once()
                author.assert_called_once()
                self.assertEqual(set(json.loads((out / 'manifest.json').read_text())['outputs']), {'16:9', '1:1', '9:16'})
                events = [json.loads((root / f'{aspect}.json').read_text()) for aspect in ['16x9', '1x1', '9x16']]
                self.assertLess(max(event['start'] for event in events), min(event['end'] for event in events))
                progress = json.loads((out.parent / 'progress.json').read_text())
                self.assertEqual(progress['aspectsDone'], 3)

    def test_a_failed_format_prevents_success_and_all_requested_formats_still_start(self):
        barrier = threading.Barrier(3, timeout=5)
        started = []

        def render(aspect):
            started.append(aspect)
            barrier.wait()
            if aspect == 'square':
                raise RuntimeError('quality gate rejected square')
            return aspect

        with self.assertRaisesRegex(RuntimeError, 'quality gate rejected square'):
            render_aspects(['landscape', 'square', 'portrait'], render)
        self.assertEqual(set(started), {'landscape', 'square', 'portrait'})


if __name__ == '__main__':
    unittest.main()
