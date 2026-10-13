import array
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'services/studio-family-engines'),str(ROOT/'services/studio-nexmind-p8'),
             str(ROOT/'vendor/nexmind-god-mode-p8/src')]
from contracts import AdapterBlocked, AdapterReplan
from recorded_narration import recorded_segments
from sound_mix import render_p8_sound_mix
from capability_adapter import bind_family_performer_capabilities, load_current_capability_packet


class RecordedNarrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.audio=self.root/'voice.wav'
        with wave.open(str(self.audio),'wb') as wav:
            wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(48000)
            wav.writeframes(array.array('h',[6000]*4800).tobytes())
        self.segment={'beatId':'b01','text':'Exact supplied words.','path':str(self.audio),
                      'sha256':hashlib.sha256(self.audio.read_bytes()).hexdigest(),
                      'rightsEvidence':{'source':'test fixture','authorization':'internal test'}}
        self.beat={'beat_id':'b01','narration_mode':'VOICEOVER','narration_text':self.segment['text'],
                   'motion_plan_status':'DIRECTED_MOTION_PERFORMANCE','sound_plan_status':'DIRECTED_SOUND',
                   'editorial':{'duration':{'value':30,'rate':30}},'sound_events':[]}
        self.request={'finalBoard':{'schema':'NexMindCanonicalSoundStoryboardV4','beats':[self.beat]},
                      'durationSeconds':1,'executionBindings':{'recordedNarration':{
                          'schema':'StudioRecordedNarrationV1','segments':[self.segment]}}}

    def test_recording_matches_exact_story_and_rejects_rewritten_text(self):
        resolved=recorded_segments(self.request,[self.beat])
        self.assertEqual(resolved['b01']['sha256'],self.segment['sha256'])
        self.beat['narration_text']='Different words.'
        with self.assertRaisesRegex(AdapterBlocked,'b01'):
            recorded_segments(self.request,[self.beat])

    def test_changed_source_bytes_fail_before_render(self):
        self.audio.write_bytes(b'changed bytes')
        with self.assertRaises(AdapterBlocked) as error:recorded_segments(self.request,[self.beat])
        self.assertEqual(error.exception.code,'RECORDED_NARRATION_SOURCE_CHANGED')

    def test_silent_or_missing_beat_cannot_consume_recording(self):
        self.beat['narration_mode']='SILENT'
        with self.assertRaises(AdapterBlocked):recorded_segments(self.request,[self.beat])
        second=deepcopy(self.beat);second.update(beat_id='b02',narration_mode='VOICEOVER')
        self.beat['narration_mode']='VOICEOVER'
        with self.assertRaises(AdapterBlocked):recorded_segments(self.request,[self.beat,second])

    def test_real_mix_uses_recording_at_p8_beat_offset_without_tts(self):
        (self.root/'manifests').mkdir()
        (self.root/'manifests/NEXSTUDIO_SOUND_V2_REGISTRY.json').write_text(json.dumps({'assets':[{
            'assetId':'test.voice','semanticTag':'test.voice','path':'voice.wav','status':'ADMITTED',
            'productionSha256':self.segment['sha256'],'license':'test-fixture'}]}))
        with patch.dict(os.environ,{'STUDIO_SOUND_LIBRARY_ROOT':str(self.root)}),patch('sound_mix.generate_audio') as tts:
            result=render_p8_sound_mix(self.request,self.root/'mix.wav')
        tts.assert_not_called()
        raw=subprocess.check_output(['ffmpeg','-v','error','-i',result['path'],'-f','s16le','-ac','1','-ar','48000','pipe:1'])
        samples=array.array('h');samples.frombytes(raw)
        self.assertEqual(next(i for i,s in enumerate(samples) if s),1920)
        self.assertFalse(any(samples[6721:]))
        self.assertEqual(result['narration'][0]['sourceSha256'],self.segment['sha256'])


class EditorialCapabilityTests(unittest.TestCase):
    def test_editorial_planner_cannot_advertise_trace_flow_or_character_actions(self):
        packet=bind_family_performer_capabilities(load_current_capability_packet(),'EDITORIAL_MOTION')
        self.assertNotIn('TRACE_FLOW',packet['performerOverrides']['SCENE_GRAPH']['supported'])
        self.assertIn('TYPE_REVEAL',packet['performerOverrides']['SCENE_GRAPH']['supported'])
        self.assertTrue(all(not rec['supported'] for name,rec in packet['performerOverrides'].items() if name!='SCENE_GRAPH'))

    def test_other_families_keep_their_current_capabilities(self):
        packet=load_current_capability_packet()
        self.assertIs(bind_family_performer_capabilities(packet,'STICKMAN'),packet)


if __name__=='__main__':unittest.main()
