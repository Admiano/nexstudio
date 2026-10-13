"""MiMo replaces all ten review roles while preserving directors and selection."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/nexmind-god-mode-p8/src'))
from nexmind_god_mode.live_provider import LiveCreativeModelProvider, RoleRouter


class MiMoReviewerRoutingTests(unittest.TestCase):
    def test_all_review_roles_change_without_changing_directors_or_selection(self):
        raw = subprocess.check_output(['node', '-e',
            "console.log(JSON.stringify(require('./scripts/configure-mimo-reviewers.cjs').updates()))"],
            cwd=ROOT, text=True)
        settings = json.loads(raw)
        profile = json.loads((ROOT / 'config/nexmind/mimo-reviewers.json').read_text())
        baseline = {'NEXMIND_CREATIVE_MODEL': 'configured-director',
                    'NEXMIND_REVIEW_MODEL': 'configured-selection',
                    'NEXMIND_REVIEW_INPUT_MODALITIES': 'images,audio',
                    'NEXMIND_REVIEW_AUDIO_INPUT_MODE': 'chat_input_audio'}
        for prefix in (profile['departmentPrefix'], *profile['finalPrefixes']):
            baseline.update({prefix + '_MODEL': 'cyberouter/inkling',
                             prefix + '_INPUT_MODALITIES': 'images,audio',
                             prefix + '_AUDIO_INPUT_MODE': 'chat_input_audio'})
        with patch.dict(os.environ, baseline, clear=True):
            router = RoleRouter()
            before = {task: router.resolve(task) for task in router.ROLE_NAMES}
        with patch.dict(os.environ, {**baseline, **settings}, clear=True):
            router = RoleRouter()
            for task in router.ROLE_NAMES:
                route = router.resolve(task)
                self.assertNotIn('inkling', route.model)
                if task in profile['departmentTasks'] + profile['finalTasks']:
                    self.assertEqual((route.model, route.provider, route.base_url, route.api_key_env),
                        (profile['model'], 'vercel', 'https://ai-gateway.vercel.sh/v1', 'VERCEL_AI_GATEWAY_API_KEY'))
                    self.assertEqual(route.api_mode, 'chat_completions_prompt_json')
                    self.assertEqual(route.reasoning, 'high')
                else:
                    self.assertEqual(route, before[task])
                if task in profile['finalTasks']:
                    self.assertEqual(set(route.input_modalities), {'audio', 'images'})
                    self.assertEqual(route.audio_input_mode, 'chat_file_audio')
                    self.assertEqual(route.multimodal_review_mode, 'separate')
                    self.assertEqual(route.audio_sample_rate, 16000)

    def test_final_roles_use_vercel_native_file_audio_without_changing_bytes(self):
        settings = json.loads(subprocess.check_output(['node', '-e',
            "console.log(JSON.stringify(require('./scripts/configure-mimo-reviewers.cjs').updates()))"],
            cwd=ROOT, text=True))
        url = 'data:audio/wav;base64,UklGRg=='
        with patch.dict(os.environ, settings, clear=True):
            router = RoleRouter()
            for task in ('final_producer', 'perceptual_auditor'):
                part = LiveCreativeModelProvider._audio_content({'data_url': url}, router.resolve(task))
                self.assertEqual(part, {'type': 'file', 'file': {'file_data': url, 'filename': 'audio.wav'}})


if __name__ == '__main__':
    unittest.main()
