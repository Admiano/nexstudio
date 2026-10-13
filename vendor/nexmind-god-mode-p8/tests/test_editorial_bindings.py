from copy import deepcopy
import unittest
from test_p3_art_storyboard import story, visual, art_candidate
from nexmind_god_mode.art_director import ArtDirector
from nexmind_god_mode.contracts import ContractViolation
from nexmind_god_mode.editorial_bindings import validate_beat_bindings, validate_camera_targets, validate_motion_targets, validate_sound_obligations
from nexmind_god_mode.p3_producer import P3ExecutiveProducer
from nexmind_god_mode.storyboard_compiler import StoryboardCompiler


def candidate():
    art=art_candidate('typed-art','cutaway')
    for beat in art['beat_art']:
        hero={'role':'computer.hero','semantic_ref':'computer.hero','kind':'TEXT','text':'One machine.',
              'placement':'MAIN','scale':'HERO','tone':'INK','font':'SANS','weight':'BOLD','align':'CENTER','emphasis':'NORMAL'}
        supports=[{'role':'background field','semantic_ref':'field','kind':'BACKGROUND','placement':'FULL_CANVAS','tone':'BACKGROUND'},
                  {'role':'deliberate silence','semantic_ref':'silence','kind':'SILENCE'}]
        beat.update(display_copy='One machine.',hero_binding=hero,support_bindings=supports,supporting_roles=[b['role'] for b in supports])
    return art


class Provider:
    def __init__(self,art):self.art=art;self.requests=[]
    def complete(self,task,request):
        self.requests.append((task,deepcopy(request)))
        if task=='art':return {'candidates':[deepcopy(self.art)]}
        if task=='art_review':return {'verdict':'ACCEPT','issues':[],'strengths':['mocked judgment'], 'revision_brief':'','commercial_confidence':'HIGH'}
        raise AssertionError(task)


class EditorialBindingTests(unittest.TestCase):
    def propose(self,art):
        provider=Provider(art)
        brief={'autonomous_revision_context':{'department':'ART_DIRECTION','previous_output':candidate()}}
        out=ArtDirector(provider).propose('test',brief,story(),visual(),{}, {'production_family':'EDITORIAL_MOTION','editorial_asset_inventory':[]})
        return out,provider

    def test_director_requires_typed_contract_before_review(self):
        with self.assertRaisesRegex(ContractViolation,'display_copy'):
            self.propose(art_candidate('old-art','cutaway'))

    def test_director_requests_and_preserves_model_literal_copy(self):
        art=candidate();before=deepcopy(art);out,provider=self.propose(art)
        self.assertEqual(art,before)
        self.assertIn('editorial_execution_contract',provider.requests[0][1])
        board=StoryboardCompiler().compile(story(),visual(),out[0],{'status':'SUPPORTED'})
        self.assertEqual(board['beats'][0]['display_copy'],'One machine.')
        self.assertNotEqual(board['beats'][0]['display_copy'],board['beats'][0]['scene_thesis'])
        self.assertEqual(board['authored_art']['beat_bindings'][0]['hero_binding'],art['beat_art'][0]['hero_binding'])

    def test_reviewer_cannot_accept_a_mechanical_binding_omission(self):
        art=candidate();art['beat_art'][0]['support_bindings'].pop()
        provider=Provider(art);review=P3ExecutiveProducer(provider).review_art('test',{},story(),visual(),art,{'status':'SUPPORTED'})
        self.assertEqual(review['verdict'],'REVISE')
        self.assertTrue(review['issues'][0]['blocking'])
        self.assertEqual(review['issues'][0]['owner_department'],'ART_DIRECTION')

    def test_unavailable_exact_assets_and_sound_tags_are_rejected_by_art(self):
        for binding in [{'role':'background field','kind':'ASSET','semantic_ref':'cup','asset_id':'invented-id','source':'CATALOG','placement':'LOWER','emphasis':'NORMAL'},
                        {'role':'deliberate silence','kind':'SOUND_EVENT','semantic_ref':'uninstalled-tag'}]:
            art=candidate();beat=art['beat_art'][0]
            if binding['kind']=='ASSET':
                binding['role']='extra prop';beat['supporting_roles'].append('extra prop');beat['support_bindings'].append(binding)
            else:beat['support_bindings'][1]=binding
            with self.subTest(binding=binding),self.assertRaises(ContractViolation):self.propose(art)

    def test_art_audio_obligations_cannot_contradict_accepted_story(self):
        art=candidate();art['beat_art'][0]['support_bindings'][1].update(kind='NARRATION',semantic_ref='recording')
        with self.assertRaisesRegex(ContractViolation,'silent Story'):self.propose(art)

    def test_binding_rejects_geometry_and_wrong_field_kind(self):
        art=candidate();beat=art['beat_art'][0]
        beat['support_bindings'][1]['placement']='MAIN'
        with self.assertRaises(ContractViolation):validate_beat_bindings(beat)
        art=candidate();art['beat_art'][0]['hero_binding']['x']=12
        with self.assertRaisesRegex(ContractViolation,'geometry'):self.propose(art)

    def test_camera_cannot_invent_a_target_or_replace_art_copy(self):
        art=candidate();shot={'beat_id':'B1','camera_atom':{'atom':'HOLD','target':'a prose description'}}
        with self.assertRaises(ContractViolation):validate_camera_targets(art,[{'shots':[shot]}])
        shot['camera_atom']['target']='computer.hero';validate_camera_targets(art,[{'shots':[shot]}])
        shot['camera_atom']['atom']='ARC'
        with self.assertRaises(ContractViolation):validate_camera_targets(art,[{'shots':[shot]}])

    def test_motion_requires_real_targets_and_explicit_serial_binding(self):
        board=StoryboardCompiler().compile(story(),visual(),candidate(),{'status':'SUPPORTED'})
        action={'beat_id':'B1','action_id':'a1','actor':'computer.hero','target':'computer.hero','performer_class':'SCENE_GRAPH','requested_verb':'SETTLE','overlap_policy':'HOLD'}
        validate_motion_targets(board,[{'actions':[action]}])
        action['target']='unknown'
        with self.assertRaises(ContractViolation):validate_motion_targets(board,[{'actions':[action]}])
        action['target']='computer.hero';action['requested_verb']='TYPE_REVEAL'
        second={**action,'action_id':'a2'}
        with self.assertRaises(ContractViolation):validate_motion_targets(board,[{'actions':[action,second]}])

    def test_sound_requires_exact_nonoptional_events_and_honors_silence(self):
        board=StoryboardCompiler().compile(story(),visual(),candidate(),{'status':'SUPPORTED'})
        event={'beat_id':'B1','kind':'SFX','semantic_tag':'tick','optional':False}
        with self.assertRaises(ContractViolation):validate_sound_obligations(board,[{'events':[event]}])
        board['beats'][0]['support_bindings'][1].update(kind='SOUND_EVENT',semantic_ref='tick')
        validate_sound_obligations(board,[{'events':[event]}])
        event['optional']=True
        with self.assertRaises(ContractViolation):validate_sound_obligations(board,[{'events':[event]}])

if __name__=='__main__':unittest.main()
