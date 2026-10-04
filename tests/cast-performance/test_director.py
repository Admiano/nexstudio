import sys,unittest,runpy,json,copy,math
from pathlib import Path
R=Path(__file__).resolve().parents[2];F=Path(__file__).resolve().parent/'fixtures';sys.path.insert(0,str(R/'scripts'))
import nex_performance_guards as g
D=runpy.run_path(str(R/'scripts/cast-performance-director.py'))
class Boundaries(unittest.TestCase):
 def setUp(self):self.actor={'actor_id':'x','script':'One short sentence.','script_beats':[{'start':0,'end':1,'text':'One short sentence.'}],'speech':{'duration':1,'timing_authority':'MASTER_AUDIO'}}
 def test_valid_master(self):self.assertEqual(g.pg_actor_errors(self.actor),[])
 def test_beat_overrun(self):self.actor['script_beats'][0]['end']=6;self.assertTrue(g.pg_actor_errors(self.actor))
 def test_missing_alignment(self):self.actor.pop('script_beats');self.assertTrue(g.pg_actor_errors(self.actor))
 def test_incomplete_alignment(self):self.actor['speech']['word_segments']=[{'word':'One','start':0,'end':.2}];self.assertTrue(g.pg_actor_errors(self.actor))
 def test_mismatched_words(self):self.actor['speech']['word_segments']=[{'word':x,'start':i*.2,'end':(i+1)*.2} for i,x in enumerate(['One','wrong','sentence'])];self.assertTrue(g.pg_actor_errors(self.actor))
 def test_nan_duration(self):self.actor['speech']['duration']=float('nan');self.assertTrue(g.pg_actor_errors(self.actor))
 def test_infinite_duration(self):self.actor['speech']['duration']=float('inf');self.assertTrue(g.pg_actor_errors(self.actor))
 def test_nan_segment(self):self.actor['script_beats'][0]['start']=float('nan');self.assertTrue(g.pg_actor_errors(self.actor))
 def test_zero_duration(self):self.actor['speech']['duration']=0;self.assertTrue(g.pg_actor_errors(self.actor))
 def test_bool_duration(self):self.actor['speech']['duration']=True;self.assertTrue(g.pg_actor_errors(self.actor))
 def test_action_overrun(self):self.actor['high_level_actions']=[{'start':.5,'end':2}];self.assertTrue(g.pg_actor_errors(self.actor))
 def test_silence_priority_in_both_orders(self):
  e=[{'start':0,'end':2,'viseme':'AH'},{'start':.5,'end':1,'viseme':'REST','hard_override':True}]
  for seq in [e,e[::-1]]:self.assertEqual(g.pg_sample_viseme(seq,.75)['viseme'],'REST')
 def test_listener_priority(self):self.assertEqual(g.pg_sample_viseme([{'start':0,'end':2,'viseme':'AH'}],.5,False)['intensity'],0)
 def test_half_open_end(self):self.assertEqual(g.pg_sample_viseme([{'start':0,'end':1,'viseme':'AH'}],1)['viseme'],'REST')
 def test_latest_viseme_wins(self):self.assertEqual(g.pg_sample_viseme([{'start':0,'end':2,'viseme':'AH'},{'start':.5,'end':1,'viseme':'MBP'}],.75)['viseme'],'MBP')
 def test_invalid_viseme(self):
  with self.assertRaises(ValueError):g.pg_sample_viseme([{'start':0,'end':1,'viseme':'NOT_A_PHONE'}],.5)
 def test_attention_nonfinite(self):self.assertEqual(g.pg_attention({'headYaw':float('nan')},{'head_yaw':15})['status'],'FAIL_CLOSED')
 def test_attention_root_rejected(self):self.assertEqual(g.pg_attention({'rootTranslation':1},{'head_yaw':15})['status'],'FAIL_CLOSED')
 def test_attention_limit(self):self.assertEqual(g.pg_attention({'headYaw':16},{'head_yaw':15})['status'],'FAIL_CLOSED')
 def test_attention_valid(self):self.assertEqual(g.pg_attention({'headYaw':8},{'head_yaw':15})['status'],'PASS')
 def test_complete_host_and_podcast(self):
  for name in ['female-host','male-host','podcast']:
   req=json.loads((F/f'{name}-request.json').read_text());a=D['compile_scene'](req);b=D['compile_scene'](req)
   self.assertEqual(a,b);self.assertEqual(a['duration'],req['masterAudio']['duration']);self.assertFalse(a['sourceAudioRetimed'])
   for actor in a['actors']:
    self.assertTrue(all(0<=e['start']<e['end']<=a['duration'] for e in actor['speech']))
    for x,y in actor['speaker_rest_windows']:
     self.assertEqual(g.pg_sample_viseme(actor['speech'],(x+y)/2)['viseme'],'REST')
 def test_unaligned_native_actor_rejected(self):
  r=json.loads((F/'male-host-request.json').read_text());r['actors'][0]['speech']['viseme_segments']=[]
  with self.assertRaises(ValueError):D['compile_scene'](r)
 def test_partial_phoneme_coverage_rejected(self):
  r=json.loads((F/'male-host-request.json').read_text());r['actors'][0]['speech']['viseme_segments']=r['actors'][0]['speech']['viseme_segments'][:1]
  with self.assertRaisesRegex(ValueError,'INCOMPLETE_NATIVE_PHONEME'):D['compile_scene'](r)
 def test_native_estimated_word_fallback_rejected(self):
  r=json.loads((F/'male-host-request.json').read_text());r['actors'][0]['speech']['word_segments']=[]
  with self.assertRaisesRegex(ValueError,'NATIVE_WORD_ALIGNMENT_REQUIRED'):D['compile_scene'](r)
 def test_unknown_turn_actor(self):
  r=json.loads((F/'podcast-request.json').read_text());r['turns'][0]['actor_id']='unknown'
  with self.assertRaises(ValueError):D['compile_scene'](r)
 def test_unknown_native_character(self):
  r=json.loads((F/'male-host-request.json').read_text());r['actors'][0]['character']='invented'
  with self.assertRaises(ValueError):D['compile_scene'](r)
 def test_short_master_rejected(self):
  r=json.loads((F/'male-host-request.json').read_text());r['masterAudio']['duration']=1
  with self.assertRaises(ValueError):D['compile_scene'](r)
 def test_master_hash_required(self):
  r=json.loads((F/'male-host-request.json').read_text());r['masterAudio'].pop('sha256')
  with self.assertRaises(ValueError):D['compile_scene'](r)
 def test_native_overlap_requires_admission(self):
  r=json.loads((F/'podcast-request.json').read_text());r['turns'][1]['start']=r['turns'][0]['end']-.1
  with self.assertRaisesRegex(ValueError,'NATIVE_OVERLAP_REQUIRES'):D['compile_scene'](r)
 def test_native_turn_floor_cue_requires_admission(self):
  r=json.loads((F/'podcast-request.json').read_text());r['turns'][1]['floor_cue']='soft_interrupt'
  with self.assertRaisesRegex(ValueError,'NATIVE_FLOOR_CUE_REQUIRES'):D['compile_scene'](r)
 def test_native_explicit_floor_cue_requires_admission(self):
  r=json.loads((F/'podcast-request.json').read_text());r['floor_cues']=[{'actor_id':'B','time':1,'duration':.3,'type':'soft_interrupt'}]
  with self.assertRaisesRegex(ValueError,'NATIVE_FLOOR_CUE_REQUIRES'):D['compile_scene'](r)
if __name__=='__main__':unittest.main()
