"""Ensure the optional reviewer profile never changes creative or audio-review roles."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor/nexmind-god-mode-p8/src'))
from nexmind_god_mode.live_provider import RoleRouter
from nexmind_god_mode.provider import ProviderError


class SpaceBunnyReviewerRoutingTests(unittest.TestCase):
    def test_profile_changes_all_department_reviews_without_changing_other_roles(self):
        raw=subprocess.check_output(['node','-e',
            "console.log(JSON.stringify(require('./scripts/configure-space-bunny-reviewer.cjs').updates()))"],cwd=ROOT,text=True)
        settings=json.loads(raw)
        profile=json.loads((ROOT/'config/nexmind/space-bunny-department-reviewer.json').read_text())
        settings.update({'NEXMIND_CREATIVE_MODEL':'configured-creative',
                         'NEXMIND_REVIEW_MODEL':'configured-selection',
                         'NEXMIND_REVIEW_INPUT_MODALITIES':'images,audio',
                         'NEXMIND_REVIEW_AUDIO_INPUT_MODE':'chat_input_audio'})
        for prefix in ('NEXMIND_FINAL_EXECUTIVE_PRODUCER','NEXMIND_PERCEPTUAL_AUDITOR'):
            settings.update({prefix+'_MODEL':'configured-audio-reviewer',prefix+'_INPUT_MODALITIES':'images,audio',
                             prefix+'_AUDIO_INPUT_MODE':'chat_input_audio'})
        with patch.dict(os.environ,settings,clear=True):
            router=RoleRouter()
            for task in router.ROLE_NAMES:
                route=router.resolve(task)
                if task in profile['tasks']:
                    self.assertEqual((route.provider,route.model,route.api_key_env),
                                     ('openrouter','stealth/space-bunny-alpha','OPENROUTER_API_KEY'))
                    self.assertEqual(route.input_modalities,('images',))
                elif task in profile['excludedTasks']:
                    self.assertEqual(route.model,'configured-audio-reviewer')
                elif task in router.CREATIVE_TASKS:
                    self.assertEqual(route.model,'configured-creative')
                else:
                    self.assertEqual(route.model,'configured-selection')

    def test_space_bunny_profile_cannot_claim_native_audio_readiness(self):
        with patch.dict(os.environ,{
            'NEXMIND_FINAL_EXECUTIVE_PRODUCER_MODEL':'stealth/space-bunny-alpha',
            'NEXMIND_FINAL_EXECUTIVE_PRODUCER_INPUT_MODALITIES':'images',
        },clear=True):
            with self.assertRaisesRegex(ProviderError,'missing=audio'):
                RoleRouter().resolve('final_producer')


if __name__=='__main__':unittest.main()
