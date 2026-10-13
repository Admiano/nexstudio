from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'services/studio-family-engines'))
sys.path.insert(0,str(ROOT/'services/studio-nexmind-p8'))
from contracts import AdapterReplan
from editorial_authored_page import bind_authored_page
from execution_plan import compile_execution_plan, compatibility_board, validate_execution_plan
from contracts import AdapterBlocked
from orchestrator import attach_authored_art
from nexmind_god_mode.showrunner_p8 import NexMindSupremeShowrunnerP8


def fixture():
    art={'form_request':{'representation':'The authored body copy is exactly: ‘Many tasks / fill the day. / Choose  and give it time. / Let one thing / hold attention.’ ONE later fills that vacancy.',
        'required_operations':['scroll at constant rate','halt on the vacancy','re-break around the insertion']},'typography_intent':'A single authored page.'}
    beats=[]
    for bid,start,duration,verb in [('read',0,2,'REFRAME_CONTENT'),('halt',2,1,'SETTLE'),('insert',3,1,'TYPE_REVEAL'),('rest',4,2,'SETTLE')]:
        beats.append({'beat_id':bid,'editorial':{'start':{'value':start*30,'rate':30},'duration':{'value':duration*30,'rate':30},'action_frame':0,'settle_frame':25},
            'motion_actions':[{'action_id':'action-'+bid,'performer_class':'SCENE_GRAPH','requested_verb':verb}],
            'motion_plan_status':'DIRECTED_MOTION_PERFORMANCE','sound_plan_status':'DIRECTED_SOUND',
            'camera':{'camera_atom':{'atom':'TRACK' if bid=='read' else 'HOLD'}},
            'supporting_assets':['uniform text block','paper field'],
            'sound_events':([{'event_id':'click','kind':'SFX','sync_target':'line break in read'}] if bid=='read' else
                [{'event_id':'impact','kind':'SFX','sync_target':'ONE lands into authored vacancy'}] if bid=='insert' else [])})
    sr=NexMindSupremeShowrunnerP8('fixture',{'topic':'A page'})
    sr.state['decisions']['art_direction']={'payload':{'art_direction':art}}
    return {'productionId':'fixture','checkpoint':{'state':sr.state},'finalBoard':{'schema':'NexMindCanonicalSoundStoryboardV4','beats':beats}}


class AuthoredPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=fixture()
        cls.sr=NexMindSupremeShowrunnerP8(cls.result['productionId'],cls.result['checkpoint']['state']['brief'])
        cls.sr.state=deepcopy(cls.result['checkpoint']['state'])

    def board(self):
        return attach_authored_art(self.sr,self.result['finalBoard'])

    def test_recovered_copy_uses_accepted_art_without_changing_decisions(self):
        before=deepcopy(self.sr.state)
        board=self.board()
        self.assertEqual(self.sr.state,before)
        self.assertEqual(board['beats'],self.result['finalBoard']['beats'])
        page=bind_authored_page(board)
        self.assertEqual(len(page['lines']),5)
        self.assertEqual(page['lines'][2],'Choose  and give it time.')
        self.assertEqual((page['scrollEnd'],page['arrival'],page['duration']),(2,3,6))
        self.assertEqual(page['soundSync']['impact']['at'],3)
        self.assertEqual(len(page['supportBindings']),sum(len(b['supporting_assets']) for b in board['beats']))

    def test_compilation_keeps_exact_art_and_rejects_hash_tampering(self):
        brand={'schema':'StudioBrandExecutionV1','memoryInputSnapshotId':'test','memoryInputSnapshotHash':'abc','brandExecutionHash':'abc'}
        plan=compile_execution_plan({'productionId':'test','family':'EDITORIAL_MOTION','brandExecution':brand},self.board())
        reconstructed=compatibility_board(plan)
        self.assertEqual(reconstructed['authored_art'],self.board()['authored_art'])
        self.assertEqual(bind_authored_page(reconstructed)['lines'],bind_authored_page(self.board())['lines'])
        plan['boardMetadata']['authored_art']['typography_intent']='tampered'
        with self.assertRaises(AdapterBlocked): validate_execution_plan(plan)

    def test_unbound_prop_is_not_silently_dropped(self):
        board=self.board();board['beats'][0]['supporting_assets'].append('golden trophy')
        with self.assertRaises(AdapterReplan) as caught: bind_authored_page(board)
        self.assertEqual(caught.exception.code,'EDITORIAL_SUPPORT_BINDING_UNAVAILABLE')

    def test_ambiguous_vacancy_fails_closed(self):
        board=self.board()
        form=board['authored_art']['form_request']
        form['representation']=form['representation'].replace('Many tasks /','Many  tasks /')
        with self.assertRaises(AdapterReplan): bind_authored_page(board)

    def test_non_page_art_retains_existing_asset_path(self):
        board=self.board();board['authored_art']={}
        self.assertIsNone(bind_authored_page(board))

    def test_canonical_timing_wins_over_old_prose(self):
        board=self.board()
        board['beats'][2]['settled_state']='A stale note says 5.5 seconds.'
        self.assertEqual(bind_authored_page(board)['arrival'],3)

    def test_named_insertion_cue_binds_to_same_visual_event(self):
        board=self.board()
        board['beats'][2]['sound_events'][0]['sync_target']='the instant ONE appears in the authored vacancy and the surrounding lines re-break'
        page=bind_authored_page(board)
        self.assertEqual(page['soundSync']['impact']['at'],page['arrival'])


if __name__=='__main__': unittest.main()
