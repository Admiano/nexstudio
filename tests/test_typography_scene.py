from copy import deepcopy
from pathlib import Path
import sys, unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'services/studio-family-engines'))
from canonical import stable
from contracts import AdapterBlocked
from typography_scene import bind_typography_scene
from execution_plan import compile_execution_plan, compatibility_board, validate_execution_plan

def fixture():
    board={'schema':'NexMindCanonicalSoundStoryboardV4','authored_art':{'form_request':{'semantic_parts':['paper field','the sentence Read slowly.']}},'beats':[
        {'beat_id':'read','editorial':{'start':{'value':0,'rate':30},'duration':{'value':60,'rate':30}},
         'motion_plan_status':'DIRECTED_MOTION_PERFORMANCE','sound_plan_status':'DIRECTED_SOUND',
         'motion_actions':[{'action_id':'resolve','performer_class':'SCENE_GRAPH','requested_verb':'REVEAL'}],
         'camera':{'camera_atom':{'atom':'HOLD'}},'supporting_assets':['paper'],
         'sound_events':[{'event_id':'tick','kind':'SFX','sync_target':'read action_frame 2'}]}]}
    contract={'schema':'StudioTypographySceneGraphV1','sourceBoardHash':stable(board),'nodes':[
        {'id':'paper','kind':'paper','sourcePart':'paper field','x':0,'y':0,'width':1,'height':1,'color':'#F2EDE3','opacity':1,'grain':.04},
        {'id':'sentence','kind':'text','sourcePart':'the sentence Read slowly.','text':'Read slowly.','font':'didone','fontSize':.1,'x':.15,'y':.25,'width':.7,'height':.2,'color':'#222222','opacity':1,'blur':8}],
        'tracks':[{'nodeId':'sentence','property':'blur','keys':[{'time':0,'value':8,'ease':'linear'},{'time':1,'value':0,'ease':'hold'}]}],
        'supportBindings':[{'beatId':'read','sourceLabel':'paper','nodeIds':['paper']}],
        'actionBindings':[{'actionId':'resolve','nodeIds':['sentence']}],
        'soundSync':{'tick':{'sourceBeatId':'read','syncTarget':'read action_frame 2','at':2/30,'end':.5,'fadeOut':.1}}}
    return board,contract

class TypographyTests(unittest.TestCase):
    def test_generic_copy_and_canonical_authority_roundtrip(self):
        board,contract=fixture();before=deepcopy(board)
        result=bind_typography_scene(board,contract)
        self.assertEqual(result['duration'],2);self.assertEqual(board,before)
        request={'productionId':'test','family':'EDITORIAL_MOTION','executionBindings':{'typographyScene':contract},
                 'brandExecution':{'schema':'StudioBrandExecutionV1','memoryInputSnapshotId':'test','memoryInputSnapshotHash':'a','brandExecutionHash':'b'}}
        plan=compile_execution_plan(request,board)
        self.assertEqual(compatibility_board(plan),board)
        plan['executionBindings']['typographyScene']['nodes'][1]['x']=.2
        with self.assertRaises(AdapterBlocked):validate_execution_plan(plan)

    def test_rejects_omissions_invented_copy_and_unsupported_execution(self):
        board,contract=fixture()
        for mutate in [lambda c:c['nodes'][1].update(text='Invented'),lambda c:c.update(actionBindings=[]),
                       lambda c:c.update(supportBindings=[]),lambda c:c['tracks'][0].update(property='rotation'),
                       lambda c:c['nodes'][0].update(kind='icon'),lambda c:c['nodes'][1].update(x=.8),
                       lambda c:c['soundSync']['tick'].update(at=.1),lambda c:c['soundSync']['tick'].update(fadeOut=1)]:
            candidate=deepcopy(contract);mutate(candidate)
            with self.subTest(contract=candidate),self.assertRaises(AdapterBlocked):bind_typography_scene(board,candidate)

    def test_source_and_contract_tampering(self):
        board,c=fixture();c['contractHash']=stable(c);bind_typography_scene(board,c)
        c['nodes'][1]['opacity']=.5
        with self.assertRaises(AdapterBlocked):bind_typography_scene(board,c)
        board,c=fixture();board['beats'][0]['editorial']['duration']['value']=90
        with self.assertRaises(AdapterBlocked):bind_typography_scene(board,c)

    def test_no_contract_keeps_existing_port(self):
        self.assertIsNone(bind_typography_scene({},None))

    def test_sound_frame_rounding_resolves_to_exact_sample_timeline(self):
        board,c=fixture();c['soundSync']['tick']['at']=.0667
        self.assertEqual(bind_typography_scene(board,c)['soundSync']['tick']['at'],2/30)

if __name__=='__main__': unittest.main()
