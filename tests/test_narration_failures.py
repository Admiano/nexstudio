"""Voice recovery and dispatch failure reporting, without calling the provider."""
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine_sources/explainer-locks/tools"))
import generate_voice

spec = importlib.util.spec_from_file_location("site_job_runner", ROOT / "services/studio-family-engines/site_job_runner.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class NarrationFailures(unittest.TestCase):
    def test_automatic_alignment_uses_available_cpus_and_preserves_native_settings(self):
        observed = {}
        class Model:
            def __init__(self, *args, **kwargs):
                observed.update(threads=kwargs['cpu_threads'], mkl=os.environ['MKL_NUM_THREADS'])
            def transcribe(self, *args, **kwargs):
                return [], None
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'WHISPER_PYTHON': '', 'WHISPER_CPU_THREADS': 'auto', 'MKL_NUM_THREADS': '16'}), patch.object(generate_voice.os, 'cpu_count', return_value=12), patch.object(generate_voice.os, 'sched_getaffinity', return_value=set(range(12)), create=True), patch.dict(sys.modules, {'faster_whisper': types.SimpleNamespace(WhisperModel=Model)}):
            generate_voice.align(Path('voice.wav'), Path(directory) / 'alignment.json')
        self.assertEqual(observed, {'threads': 12, 'mkl': '16'})

    def test_explicit_cpu_override_is_not_capped_to_cpu_count(self):
        with patch.dict(os.environ, {'WHISPER_CPU_THREADS': '64'}), patch.object(generate_voice.os, 'cpu_count', return_value=2):
            self.assertEqual(generate_voice._cpu_threads('WHISPER_CPU_THREADS'), 64)

    def test_kokoro_auto_keeps_native_thread_defaults(self):
        observed = {}
        class Options:
            intra_op_num_threads = 0
            inter_op_num_threads = 0
        def session(*args, **kwargs):
            observed['options'] = kwargs['sess_options']
            return object()
        pipe = types.SimpleNamespace(create=lambda *args, **kwargs: ([0.0] * 24, 24000))
        kokoro = types.SimpleNamespace(from_session=lambda *args: pipe)
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / 'model.onnx'
            voices = Path(directory) / 'voices.bin'
            model.touch(); voices.touch()
            with patch.dict(os.environ, {'KOKORO_CPU_THREADS': 'auto', 'KOKORO_MODEL_PATH': str(model), 'KOKORO_VOICES_PATH': str(voices)}), patch.dict(sys.modules, {
                'onnxruntime': types.SimpleNamespace(SessionOptions=Options, InferenceSession=session),
                'kokoro_onnx': types.SimpleNamespace(Kokoro=kokoro),
                'soundfile': types.SimpleNamespace(write=lambda *args: None),
            }):
                self.assertEqual(generate_voice._synth_kokoro('Test', {'kokoro': 'af_heart', 'lang': 'a'}, Path(directory) / 'voice.wav'), 0.001)
        self.assertEqual(observed['options'].intra_op_num_threads, 0)
        self.assertEqual(observed['options'].inter_op_num_threads, 0)

    def test_inline_alignment_limits_mkl_threads_too(self):
        observed = {}
        class Model:
            def __init__(self, *args, **kwargs):
                observed.update(threads=kwargs["cpu_threads"], mkl=os.environ["MKL_NUM_THREADS"], omp=os.environ["OMP_NUM_THREADS"])
            def transcribe(self, *args, **kwargs):
                return [], None
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"WHISPER_PYTHON": "", "WHISPER_CPU_THREADS": "1", "MKL_NUM_THREADS": "16", "OMP_NUM_THREADS": "16"}), patch.dict(sys.modules, {"faster_whisper": types.SimpleNamespace(WhisperModel=Model)}):
            self.assertEqual(generate_voice.align(Path("voice.wav"), Path(directory) / "alignment.json"), 0)
        self.assertEqual(observed, {"threads": 1, "mkl": "1", "omp": "1"})

    def test_alignment_failure_preserves_underlying_diagnostic(self):
        failure = subprocess.CompletedProcess([], 1, stderr="Model loading failed: insufficient memory")
        stderr = io.StringIO()
        with patch.dict(os.environ, {"WHISPER_PYTHON": "alignment-python", "WHISPER_CPU_THREADS": "1"}), patch.object(generate_voice.subprocess, "run", return_value=failure) as run, patch.object(generate_voice.sys, "stderr", stderr):
            with self.assertRaisesRegex(RuntimeError, "NARRATION_ALIGNMENT_FAILED"):
                generate_voice.align(Path("voice.wav"), Path("alignment.json"))
        self.assertEqual(run.call_args.args[0][-1], "1")
        self.assertEqual(run.call_args.kwargs["env"]["MKL_NUM_THREADS"], "1")
        self.assertIn("Model loading failed: insufficient memory", stderr.getvalue())

    def test_transient_failure_retries_same_voice_then_encodes(self):
        failure = subprocess.CompletedProcess([], 1, stderr="aiohttp.client_exceptions.WSServerHandshakeError: 403, message='Invalid response status'")
        success = subprocess.CompletedProcess([], 0)
        duration = subprocess.CompletedProcess([], 0, stdout="4.2\n")
        with tempfile.TemporaryDirectory() as directory, patch.object(generate_voice.subprocess, "run", side_effect=[failure, success, success, duration]) as run, patch.object(generate_voice.time, "sleep") as sleep:
            self.assertEqual(generate_voice._synth_edge("A team builds a rocket.", {"edge": "en-US-EmmaMultilingualNeural"}, Path(directory) / "voice.wav"), 4.2)
            self.assertEqual(run.call_args_list[0].args[0], run.call_args_list[1].args[0])
            self.assertIn("en-US-EmmaMultilingualNeural", run.call_args_list[1].args[0])
            self.assertEqual(run.call_args_list[2].args[0][0], "ffmpeg")
            sleep.assert_called_once_with(1)

    def test_persistent_provider_failure_is_bounded(self):
        failure = subprocess.CompletedProcess([], 1, stderr="WSServerHandshakeError: 403")
        with tempfile.TemporaryDirectory() as directory, patch.object(generate_voice.subprocess, "run", return_value=failure) as run, patch.object(generate_voice.time, "sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "NARRATION_PROVIDER_UNAVAILABLE"):
                generate_voice._synth_edge("Test.", {"edge": "emma"}, Path(directory) / "voice.wav")
            self.assertEqual(run.call_count, 3)
            self.assertEqual(sleep.call_count, 2)

    def test_permanent_failure_does_not_retry(self):
        failure = subprocess.CompletedProcess([], 1, stderr="Invalid voice")
        with tempfile.TemporaryDirectory() as directory, patch.object(generate_voice.subprocess, "run", return_value=failure) as run, patch.object(generate_voice.time, "sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "NARRATION_PROVIDER_UNAVAILABLE"):
                generate_voice._synth_edge("Test.", {"edge": "bad"}, Path(directory) / "voice.wav")
            self.assertEqual(run.call_count, 1)
            sleep.assert_not_called()

    def test_timeouts_are_retried(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(generate_voice.subprocess, "run", side_effect=subprocess.TimeoutExpired("edge_tts", 90)) as run, patch.object(generate_voice.time, "sleep"):
            with self.assertRaisesRegex(RuntimeError, "NARRATION_PROVIDER_UNAVAILABLE"):
                generate_voice._synth_edge("Test.", {"edge": "emma"}, Path(directory) / "voice.wav")
            self.assertEqual(run.call_count, 3)

    def test_runner_reports_voice_failure_and_ignores_old_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            job = Path(directory)
            log = job / "job.log"
            log.write_text("--- P8 dispatch 00:00 ---\nedge_tts WSServerHandshakeError: 403")
            code, message = runner._engine_failure(job, 1)
            self.assertEqual(code, "NARRATION_PROVIDER_UNAVAILABLE")
            self.assertIn("selected voice", message)
            log.write_text(log.read_text() + "\n--- P8 dispatch 00:01 ---\nunrelated error")
            self.assertEqual(runner._engine_failure(job, 1), ("ENGINE_EXIT_NONZERO", "engine exited 1 with no outputs"))
            log.write_text("--- P8 dispatch 00:02 ---\nNARRATION_PROVIDER_UNAVAILABLE: emma")
            self.assertEqual(runner._engine_failure(job, 1)[0], "NARRATION_PROVIDER_UNAVAILABLE")
            log.write_text("--- P8 dispatch 00:03 ---\nNARRATION_ALIGNMENT_FAILED: timing failed")
            self.assertEqual(runner._engine_failure(job, 1)[0], "NARRATION_ALIGNMENT_FAILED")
            log.write_text("--- P8 dispatch 00:04 ---\nmkl_malloc: failed to allocate memory\nNARRATION_ALIGNMENT_FAILED")
            self.assertEqual(runner._engine_failure(job, 1)[0], "RENDER_MEMORY_UNAVAILABLE")
            log.write_text("--- P8 dispatch 00:05 ---\nWHITEBOARD_V3_EXECUTION_BODY_MISSING: runtime")
            code, message = runner._engine_failure(job, 1)
            self.assertEqual(code, "ENGINE_RUNTIME_MISSING")
            self.assertIn("narration is saved", message)
            log.write_text("--- P8 dispatch 00:06 ---\nWHITEBOARD_LANGUAGE_DATA_MISSING: WordNet")
            self.assertEqual(runner._engine_failure(job, 1)[0], "WHITEBOARD_LANGUAGE_DATA_MISSING")


if __name__ == "__main__":
    unittest.main()
