"""A review must repair its causal owner and re-enter that pipeline stage."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT.parents[1]/'services/studio-nexmind-p8')]
import orchestrator as o
from nexmind_god_mode.provider import ProviderError
from nexmind_god_mode.showrunner_p8 import NexMindSupremeShowrunnerP8
from nexmind_god_mode.p45_producer import P45ExecutiveProducer
from test_p3_art_storyboard import story,visual,art_candidate,StoryboardCompiler
from test_p45_cinema_editorial import cinema_candidate,editorial_candidate


def review(issues):
    return {'verdict':'REVISE','issues':deepcopy(issues),'strengths':['Preserve the successful rhythm'],
            'revision_brief':'Preserve Story, Art, rhythm and payoff. Rewrite cinematography b07-b09.',
            'commercial_confidence':'HIGH'}


def camera_issue():
    return {'blocking':True,'area':'SCENE_GRAPH_BINDING / CINEMATOGRAPHY',
            'issue':'Editorial matches the flat Art system, but committed camera depth stages a second plane.',
            'required_fix':'Rewrite cinematography depth_strategy and reveal_framing to match the bound plane.'}


def seeded_state():
    sr=NexMindSupremeShowrunnerP8('routing-test',{'topic':'device','duration_s':45})
    a=art_candidate('A1','cutaway')
    board=StoryboardCompiler().compile(story(),visual(),a,{})
    # Contract-shaped local continuation fixture; no generated production is edited.
    payloads={'film_thesis':{'story':story()},'visual_concept':visual(),
              'art_direction':{'art_direction':a,'form_resolution':{}},
              'storyboard':{'storyboard':board},'cinematography':{'cinematography':cinema_candidate('C1')}}
    sr.state['decisions']={slot:{'payload':deepcopy(payload),'proposal_id':slot,'status':'COMMITTED_BY_SHOWRUNNER'}
                           for slot,payload in payloads.items()}
    o._ensure_repair_state(sr,{department:2 for department in o.DEPARTMENT_ORDER})
    sr.state['autonomous_creative_repair']['attempts']['CINEMATOGRAPHY']=1
    return sr


class DepartmentReviewRoutingTests(unittest.TestCase):
    def test_legacy_blocking_area_beats_preservation_and_advisory_words(self):
        r=review([{'blocking':False,'owner_department':'ART_DIRECTION','issue':'Optional art polish'},camera_issue()])
        r['revision_brief']+=' Editorial rhythm timing pacing duration continuity. '*30
        self.assertEqual(o._review_owner(r,'EDITORIAL_RHYTHM',{'ART_DIRECTION','CINEMATOGRAPHY','EDITORIAL_RHYTHM'}),'CINEMATOGRAPHY')

    def test_explicit_blocking_owner_has_priority_over_another_issue_code(self):
        r=review([{'blocking':True,'code':'MISSING_TEMPORAL_DIRECTION'},
                  {**camera_issue(),'owner_department':'CINEMATOGRAPHY'}])
        self.assertEqual(o._review_owner(r,'EDITORIAL_RHYTHM'),'CINEMATOGRAPHY')

    def test_advisory_only_owner_cannot_redirect_reject_repair(self):
        r=review([{'blocking':False,'owner_department':'CINEMATOGRAPHY','area':'CINEMATOGRAPHY'}])
        self.assertEqual(o._review_owner(r,'EDITORIAL_RHYTHM'),'EDITORIAL_RHYTHM')

    def test_upstream_repair_uses_committed_camera_anchor_and_keeps_unrelated_decisions(self):
        sr=seeded_state()
        sr.state['decisions']['editorial_rhythm']={'payload':{'editorial_rhythm':editorial_candidate('E-approved')}}
        before=deepcopy(sr.state['decisions'])
        r=review([camera_issue(),{'blocking':False,'area':'SOUND','required_fix':'Select a sound later'}])
        owner=o._schedule_candidate_review_repair(sr,'EDITORIAL_RHYTHM',[
            {'candidate':editorial_candidate('E-rejected'),'review':r}])
        self.assertEqual(owner,'CINEMATOGRAPHY')
        context=sr.state['brief']['autonomous_revision_context']
        self.assertEqual(context['previous_output'],before['cinematography']['payload']['cinematography'])
        self.assertEqual(context['issues'],[camera_issue()])
        self.assertEqual(context['sticky_requirements'],[camera_issue()['required_fix']])
        self.assertEqual(context['source_review'],r)
        self.assertEqual(context['source_department'],'EDITORIAL_RHYTHM')
        self.assertFalse(context['rejected_candidates'][0]['binding_to_repair_anchor'])
        self.assertNotIn('cinematography',sr.state['decisions'])
        for slot in ('film_thesis','visual_concept','art_direction','storyboard','editorial_rhythm'):
            self.assertEqual(sr.state['decisions'][slot],before[slot])

    def test_owner_comes_only_from_strongest_rejected_candidate(self):
        sr=seeded_state()
        r=review([camera_issue()])
        weaker=review([{'blocking':True,'owner_department':'ART_DIRECTION','severity':'CRITICAL'},
                       {'blocking':True,'severity':'CRITICAL'}])
        owner=o._schedule_candidate_review_repair(sr,'EDITORIAL_RHYTHM',[
            {'candidate':editorial_candidate('E-weak'),'review':weaker},
            {'candidate':editorial_candidate('E-best'),'review':r}])
        self.assertEqual(owner,'CINEMATOGRAPHY')
        self.assertIn('art_direction',sr.state['decisions'])

    def test_editorial_only_defect_keeps_editorial_anchor(self):
        sr=seeded_state()
        candidate=editorial_candidate('E-rhythm')
        r=review([{'blocking':True,'area':'EDITORIAL_RHYTHM','required_fix':'Extend the settled hold duration.'}])
        self.assertEqual(o._schedule_candidate_review_repair(sr,'EDITORIAL_RHYTHM',[
            {'candidate':candidate,'review':r}]),'EDITORIAL_RHYTHM')
        self.assertEqual(sr.state['brief']['autonomous_revision_context']['previous_output'],candidate)
        self.assertIn('cinematography',sr.state['decisions'])

    def test_owner_attempt_limit_still_applies(self):
        sr=seeded_state()
        sr.state['autonomous_creative_repair']['attempts']['CINEMATOGRAPHY']=2
        before=deepcopy(sr.state)
        with self.assertRaises(o.CreativeRepairBudgetExhausted) as error:
            o._schedule_candidate_review_repair(sr,'EDITORIAL_RHYTHM',[
                {'candidate':editorial_candidate('E'),'review':review([camera_issue()])}])
        self.assertEqual(error.exception.department,'CINEMATOGRAPHY')
        self.assertEqual(sr.state,before)

    def test_real_orchestrator_reenters_camera_instead_of_using_stale_editorial_inputs(self):
        sr=seeded_state()
        before=deepcopy(sr.state['decisions'])
        phases=[]
        rejected={'reviewed':[{'candidate':editorial_candidate('E'),'review':review([camera_issue()])}],
                  'diversity':{'meaningfully_diverse':True}}
        with patch.object(o,'load_current_capability_packet',return_value={'performerOverrides':{}}), \
             patch.object(o,'bind_family_performer_capabilities',side_effect=lambda packet,family:packet), \
             patch.object(o,'build_capability_graph',return_value={'current_authorities':{}}), \
             patch.object(o,'load_current_sound_records',return_value=[]), \
             patch.object(o,'_calibration_registry',return_value=None), \
             patch.object(o.CreativeCouncilP45,'develop_editorial',return_value=rejected) as editorial, \
             patch.object(o.CreativeCouncilP45,'develop_cinema',side_effect=ProviderError('test-stop-at-camera')) as camera:
            result=o.run_full_p8({'productionId':'routing-test','durationSeconds':45,'family':'EXPLAINER'},
                provider=object(),progress=lambda phase,payload:phases.append(phase),_continuation_state=sr.state)
        editorial.assert_called_once()
        camera.assert_called_once()
        self.assertEqual(phases[-2:],['EDITORIAL_RHYTHM','CINEMATOGRAPHY'])
        self.assertEqual(result['resumeStage'],'CINEMATOGRAPHY')
        state=result['checkpoint']['state']
        self.assertEqual(state['brief']['autonomous_revision_context']['department'],'CINEMATOGRAPHY')
        self.assertEqual(state['brief']['autonomous_revision_context']['previous_output'],before['cinematography']['payload']['cinematography'])
        for slot in ('film_thesis','visual_concept','art_direction','storyboard'):
            self.assertEqual(state['decisions'][slot],before[slot])

    def test_review_prompts_require_blocking_causal_owner(self):
        class Reply:
            def __init__(self):self.requests=[]
            def complete(self,task,request):
                self.requests.append(request)
                return {**review([]),'verdict':'ACCEPT'}
        provider=Reply()
        producer=P45ExecutiveProducer(provider)
        producer.review_cinema('P',{},story(),visual(),art_candidate('A','cutaway'),cinema_candidate('C'))
        producer.review_editorial('P',{},story(),cinema_candidate('C'),editorial_candidate('E'),{})
        producer.review_temporal_storyboard('P',{},story(),{}, {})
        for request in provider.requests:
            law=' '.join(request['instruction']['causal_owner_law'])
            self.assertIn('owner_department',law)
            self.assertIn('CINEMATOGRAPHY',law)
            self.assertIn('EDITORIAL_RHYTHM',law)

    def test_rejected_camera_candidate_reenters_art_when_art_owns_the_blocker(self):
        sr=seeded_state()
        before=deepcopy(sr.state['decisions'])
        sr.state['decisions'].pop('cinematography')
        rejected={'reviewed':[{'candidate':cinema_candidate('C-rejected'),
            'review':review([{'blocking':True,'owner_department':'ART_DIRECTION',
                'required_fix':'Repair the typed hero binding in the committed Art candidate.'}])}],
            'diversity':{'meaningfully_diverse':True}}
        with patch.object(o,'load_current_capability_packet',return_value={'performerOverrides':{}}), \
             patch.object(o,'bind_family_performer_capabilities',side_effect=lambda packet,family:packet), \
             patch.object(o,'build_capability_graph',return_value={'current_authorities':{}}), \
             patch.object(o,'load_current_sound_records',return_value=[]), \
             patch.object(o,'_calibration_registry',return_value=None), \
             patch.object(o.CreativeCouncilP45,'develop_cinema',return_value=rejected) as camera, \
             patch.object(o.CreativeCouncilP3,'develop_art',side_effect=ProviderError('test-stop-at-art')) as art:
            result=o.run_full_p8({'productionId':'routing-test','durationSeconds':45,'family':'EXPLAINER'},
                provider=object(),_continuation_state=sr.state)
        camera.assert_called_once()
        art.assert_called_once()
        self.assertEqual(result['resumeStage'],'ART_DIRECTION')
        state=result['checkpoint']['state']
        self.assertEqual(state['brief']['autonomous_revision_context']['previous_output'],before['art_direction']['payload']['art_direction'])
        for slot in ('film_thesis','visual_concept'):
            self.assertEqual(state['decisions'][slot],before[slot])


if __name__=='__main__':unittest.main()
