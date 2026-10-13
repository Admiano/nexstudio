import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'services/studio-family-engines'))
sys.path.insert(0,str(ROOT/'services/studio-nexmind-p8'))
sys.path.insert(0,str(ROOT/'vendor/nexmind-god-mode-p8/src'))
from capability_adapter import load_current_sound_records
from sound_mix import _registry, _root
from nexmind_god_mode.sound_resources import SoundResourceRegistry


class CurrentSoundInventoryTests(unittest.TestCase):
    def inventory(self,root,status='ADMITTED',digest=None):
        (root/'manifests').mkdir();(root/'production').mkdir()
        data=b'authorized-test-asset';(root/'production/click.wav').write_bytes(data)
        item={'assetId':'test.click','semanticTag':'ui.click','path':'production/click.wav',
            'productionSha256':digest or hashlib.sha256(data).hexdigest(),'license':'CC0-1.0','status':status,'selectable':True}
        (root/'manifests/NEXSTUDIO_SOUND_V2_REGISTRY.json').write_text(json.dumps({'assets':[item]}))

    def test_planner_and_mixer_use_same_installed_asset_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.inventory(root)
            with patch.dict(os.environ,{'STUDIO_SOUND_LIBRARY_ROOT':str(root)}):
                planner=SoundResourceRegistry(load_current_sound_records()).resolve('ui.click')
                mixer=_registry(root)['ui.click'][0]
            self.assertEqual(planner['asset_id'],mixer['assetId'])
            self.assertEqual(planner['sha256'],mixer['productionSha256'])
            self.assertEqual(planner['production_file'],mixer['resolvedPath'])

    def test_inherited_admission_is_preserved_in_both_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.inventory(root,'INHERITED_ADMITTED')
            with patch.dict(os.environ,{'STUDIO_SOUND_LIBRARY_ROOT':str(root)}):
                self.assertEqual(len(load_current_sound_records()),1)
            self.assertEqual(len(_registry(root)['ui.click']),1)

    def test_changed_bytes_cannot_be_advertised_as_authorized(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.inventory(root,digest='0'*64)
            with patch.dict(os.environ,{'STUDIO_SOUND_LIBRARY_ROOT':str(root)}):
                with self.assertRaisesRegex(ValueError,'CURRENT_SOUND_ASSET_HASH_CHANGED'):
                    load_current_sound_records()

    def test_installer_parent_path_resolves_same_inventory_in_both_ports(self):
        with tempfile.TemporaryDirectory() as temp:
            parent=Path(temp);root=parent/'installed';root.mkdir();self.inventory(root)
            with patch.dict(os.environ,{'STUDIO_SOUND_LIBRARY_ROOT':str(parent)}):
                self.assertEqual(_root(),root)
                self.assertEqual(load_current_sound_records()[0]['productionFile'],str(root/'production/click.wav'))


if __name__=='__main__': unittest.main()
