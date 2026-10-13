"""Whiteboard callers use strings; temporary narration must stay on the render disk."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
import wave
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('whiteboard_vo_synth', Path(__file__).resolve().parents[1] / 'engine_sources/whiteboard-board-scenes/vo_synth.py')
voice = importlib.util.module_from_spec(spec)
spec.loader.exec_module(voice)
job_spec = importlib.util.spec_from_file_location('whiteboard_job', Path(__file__).resolve().parents[1] / 'engine_sources/whiteboard-board-scenes/tools/nexstudio_job.py')
job = importlib.util.module_from_spec(job_spec)
job_spec.loader.exec_module(job)


class WhiteboardNarration(unittest.TestCase):
    def test_automatic_word_timing_uses_available_cpus_without_forcing_blas_limits(self):
        observed = {}
        class Model:
            def __init__(self, *args, **kwargs):
                observed.update(threads=kwargs['cpu_threads'], omp=os.environ['OMP_NUM_THREADS'])
            def transcribe(self, *args, **kwargs):
                return [], None
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'WHISPER_CPU_THREADS': 'auto', 'OMP_NUM_THREADS': '16'}), patch.object(voice.os, 'cpu_count', return_value=12), patch.object(voice.os, 'sched_getaffinity', return_value=set(range(12)), create=True), patch.dict(sys.modules, {'faster_whisper': types.SimpleNamespace(WhisperModel=Model)}):
            voice.word_timings(Path('voice.wav'), Path(directory) / 'words.json')
        self.assertEqual(observed, {'threads': 12, 'omp': '16'})

    def test_provider_timings_preserve_script_and_audio_range(self):
        with tempfile.TemporaryDirectory() as directory:
            wav = Path(directory) / 'voice.wav'
            with wave.open(str(wav), 'wb') as audio:
                audio.setnchannels(1); audio.setsampwidth(2); audio.setframerate(24000)
                audio.writeframes(b'\0' * 48000)
            output = Path(directory) / 'words.json'
            heard = [{'word':'A','start':0.1,'end':0.2}, {'word':'soccer','start':0.3,'end':0.5}, {'word':'ball','start':0.6,'end':1.02}]
            self.assertTrue(voice._save_edge_timings(wav, output, 'A soccer ball.', heard))
            words = json.loads(output.read_text())
            self.assertEqual([word['word'] for word in words], ['A','soccer','ball.'])
            self.assertEqual(words[-1]['end'],1.0)
            self.assertFalse(voice._save_edge_timings(wav, output, 'A soccer ball.', heard[:1]))

    def test_timing_failure_does_not_fall_back_to_guessed_timestamps(self):
        args = types.SimpleNamespace(voice_file=None, speed=1.0, voice='emma')
        diagnostic = RuntimeError('STAGE_FAILED: missing timing weights')
        with tempfile.TemporaryDirectory() as directory, patch.object(job, 'sh', side_effect=[subprocess.CompletedProcess([], 0), diagnostic]):
            with self.assertRaisesRegex(RuntimeError, 'NARRATION_ALIGNMENT_FAILED') as failure:
                job.build_voice(args, 'Every soccer ball is inspected.', Path(directory))
            self.assertIs(failure.exception.__cause__, diagnostic)

    def test_string_output_uses_render_directory_and_cleans_temporary_audio(self):
        observed = {}
        class Communicate:
            def __init__(self, text, name, rate, boundary):
                observed.update(text=text, voice=name, rate=rate, boundary=boundary)
            async def stream(self):
                observed['temporary'] = next(Path(directory).glob('*.mp3'))
                yield {'type':'audio','data':b'test audio'}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'voice.wav'
            with patch.dict(sys.modules, {'edge_tts': types.SimpleNamespace(Communicate=Communicate)}), patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as run:
                self.assertEqual(voice.synth_edge('A soccer ball.', str(output), speed=1.5), output)
            self.assertEqual(observed['temporary'].parent, output.parent)
            self.assertFalse(observed['temporary'].exists())
            self.assertEqual(observed['voice'], 'en-US-EmmaMultilingualNeural')
            self.assertEqual(observed['rate'], '+50%')
            self.assertEqual(observed['boundary'], 'WordBoundary')
            self.assertIn(str(output), run.call_args.args[0])

    def test_provider_failure_keeps_diagnostic_and_cleans_temporary_audio(self):
        class Communicate:
            def __init__(self, *args, **kwargs):
                pass
            async def stream(self):
                yield {'type':'audio','data':b''}
                raise OSError('getaddrinfo failed')
        with tempfile.TemporaryDirectory() as directory, patch.dict(sys.modules, {'edge_tts': types.SimpleNamespace(Communicate=Communicate)}):
            with self.assertRaisesRegex(RuntimeError, 'NARRATION_PROVIDER_UNAVAILABLE') as failure:
                voice.synth_edge('A soccer ball.', str(Path(directory) / 'voice.wav'))
            self.assertIn('getaddrinfo failed', str(failure.exception.__cause__))
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == '__main__':
    unittest.main()
