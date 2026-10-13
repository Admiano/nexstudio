import array,hashlib,json,os,subprocess,sys,tempfile,unittest,wave
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'services/studio-family-engines'))
from sound_mix import render_p8_sound_mix

class SampleSyncTests(unittest.TestCase):
    def exercise_mix(self,kind):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'manifests').mkdir();asset=root/'tick.wav'
            with wave.open(str(asset),'wb') as w:
                w.setnchannels(2);w.setsampwidth(2);w.setframerate(48000);w.writeframes(array.array('h',[12000,12000]*24000).tobytes())
            digest=hashlib.sha256(asset.read_bytes()).hexdigest()
            (root/'manifests/NEXSTUDIO_SOUND_V2_REGISTRY.json').write_text(json.dumps({'assets':[{'assetId':'test.tick','semanticTag':'ui.tick','path':'tick.wav','productionSha256':digest,'license':'CC0','status':'ADMITTED'}]}))
            board={'schema':'NexMindCanonicalSoundStoryboardV4','beats':[{'beat_id':'b','motion_plan_status':'DIRECTED_MOTION_PERFORMANCE','sound_plan_status':'DIRECTED_SOUND',
                   'editorial':{'duration':{'value':60,'rate':30}},'sound_events':[{'event_id':'s','kind':kind,'semantic_tag':'ui.tick','intensity':'SOFT','ducking':'NONE','sync_target':'b action_frame 2','resource':{'status':'AUTHORIZED_ASSET','asset_id':'test.tick','sha256':digest}}]}]}
            request={'finalBoard':board,'durationSeconds':2,'resolvedSoundSyncTargets':{'s':{'sourceBeatId':'b','syncTarget':'b action_frame 2','at':2/30,'end':.2,'fadeOut':.03}}}
            generated={'path':str(asset),'durationSeconds':.5,'routeId':'TEST_LOCAL','rightsEvidence':{'license':'CC0','testFixture':True}}
            with patch.dict(os.environ,{'STUDIO_SOUND_LIBRARY_ROOT':str(root)}),patch('sound_mix.generate_audio',return_value=generated):
                mix=render_p8_sound_mix(request,root/'mix.wav')
            raw=subprocess.run(['ffmpeg','-v','error','-i',mix['path'],'-f','s16le','-ac','1','-ar','48000','pipe:1'],check=True,capture_output=True).stdout
            samples=array.array('h');samples.frombytes(raw)
            self.assertEqual(next(i for i,s in enumerate(samples) if s),3200)
            self.assertFalse(any(samples[9600:]))
            self.assertGreater(abs(samples[8100]),abs(samples[9500]))
            metadata=(mix['music'] if kind=='MUSIC_CUE' else mix['events'])[0]
            self.assertEqual(metadata['end'],.2)
            if kind=='SFX':self.assertEqual(metadata['assetSha256'],digest)

    def test_real_mix_sample_alignment_end_and_fade(self):
        self.exercise_mix('SFX')

    def test_music_honors_native_silence_boundary_and_sample_timing(self):
        self.exercise_mix('MUSIC_CUE')

if __name__=='__main__':unittest.main()
