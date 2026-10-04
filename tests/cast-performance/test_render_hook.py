import unittest,runpy,tempfile,json,hashlib,wave
from pathlib import Path
R=Path(__file__).resolve().parents[2]
H=runpy.run_path(str(R/'scripts/cast-performance-render-hook.py'))
class MasterIdentity(unittest.TestCase):
 def setUp(self):
  self.request=json.loads((Path(__file__).resolve().parent/'fixtures/male-host-request.json').read_text());self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'request.json'
  audio=self.path.parent/'whole-master.wav'
  with wave.open(str(audio),'wb') as wav:
   wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(16000);wav.writeframes(b'\0\0'*163200)
  self.request['masterAudio'].update(path=str(audio),duration=10.2,sha256=hashlib.sha256(audio.read_bytes()).hexdigest())
 def tearDown(self):self.temp.cleanup()
 def call(self,sex='male'):
  self.path.write_text(json.dumps(self.request));return H['verified_request'](self.path,sex)
 def test_whole_recording_accepted(self):self.assertEqual(self.call()['duration'],10.2)
 def test_modified_audio_rejected(self):
  self.request['masterAudio']['sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'HASH_MISMATCH'):self.call()
 def test_incorrect_recording_duration_rejected(self):
  self.request['masterAudio']['duration']=12
  with self.assertRaisesRegex(ValueError,'DURATION_MISMATCH'):self.call()
 def test_missing_audio_rejected(self):
  self.request['masterAudio']['path']=str(self.path.parent/'absent.wav')
  with self.assertRaisesRegex(ValueError,'NOT_AVAILABLE'):self.call()
 def test_wrong_native_character_rejected(self):
  with self.assertRaisesRegex(ValueError,'CHARACTER_MISMATCH'):self.call('female')
 def test_uncertified_seated_preview_rejected(self):
  self.request['actors'][0]['posture']='seated'
  with self.assertRaisesRegex(ValueError,'SEATED_REQUIRES_CERTIFIED'):self.call()
 def test_nonfinite_gaze_target_rejected(self):
  self.request['targets']={'screen':[0,float('nan'),1]}
  with self.assertRaisesRegex(ValueError,'FINITE'):self.call()
if __name__=='__main__':unittest.main()
