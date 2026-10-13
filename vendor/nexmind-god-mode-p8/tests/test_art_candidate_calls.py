"""Art transport splitting must preserve complete competition and review gates."""
from copy import deepcopy
import unittest
from test_p3_art_storyboard import (
    ArtDirector, CreativeCouncilP3, DynamicProvider, IllustrationFormResolver, INDEX,
    NexMindSupremeShowrunnerP3, P3ExecutiveProducer, ArtShowrunnerDecisionIntelligence,
    StoryboardCompiler, art_candidate, seed_p2, story, visual,
)
from nexmind_god_mode.contracts import ContractViolation
from nexmind_god_mode.live_provider import LiveCreativeModelProvider
from nexmind_god_mode.provider import ProviderError


class ArtCandidateCallsTests(unittest.TestCase):
    def test_three_complete_candidates_keep_instructions_and_get_individual_reviews(self):
        provider=DynamicProvider()
        sr=NexMindSupremeShowrunnerP3('P',{'topic':'explain the device','duration_s':45})
        s,v=seed_p2(sr)
        council=CreativeCouncilP3(sr,ArtDirector(provider),IllustrationFormResolver.from_file(INDEX),
            P3ExecutiveProducer(provider),ArtShowrunnerDecisionIntelligence(provider),StoryboardCompiler())
        result=council.develop_art(s,v)
        requests=[r for task,r in provider.calls if task=='art']
        self.assertEqual(len(requests),3)
        for index,request in enumerate(requests):
            self.assertEqual(request['candidate_budget'],1)
            self.assertEqual(request['candidate_total'],3)
            self.assertEqual(request['candidate_index'],index+1)
            self.assertEqual(request['beats'],s['beats'])
            self.assertEqual(request['visual_concept'],v)
            self.assertEqual(request['instruction']['must'],requests[0]['instruction']['must'])
            self.assertEqual(len(request['previous_candidate_summaries']),index)
            self.assertTrue(all('beat_art' not in c for c in request['previous_candidate_summaries']))
            schema=LiveCreativeModelProvider._schema_for_request('art',request)
            self.assertEqual(schema['properties']['candidates']['minItems'],1)
            self.assertEqual(schema['properties']['candidates']['maxItems'],1)
        self.assertCountEqual([r['art_candidate']['candidate_id'] for task,r in provider.calls if task=='art_review'],
                              ['A1','A2','A3'])
        self.assertTrue(result['diversity']['meaningfully_diverse'])
        selected=council.select_art(s,v,result)
        self.assertIn(selected['candidate']['candidate_id'],[
            row['candidate']['candidate_id'] for row in result['reviewed'] if row['review']['verdict']=='ACCEPT'])
        self.assertEqual(sr.state['decisions']['art_direction']['payload']['art_direction'],selected['candidate'])
        self.assertEqual(len(result['reviewed']),3)

    def test_distinct_ids_do_not_bypass_semantic_competition(self):
        class DuplicateSystemProvider:
            def complete(self,task,request):
                return {'candidates':[art_candidate('A'+str(request['candidate_index']),'cutaway')]}
        with self.assertRaises(ContractViolation):
            ArtDirector(DuplicateSystemProvider()).propose('P',{},story(),visual(),{}, {})

    def test_partial_generation_never_reaches_review_or_commit(self):
        class FailingProvider(DynamicProvider):
            def complete(self,task,request):
                if task=='art' and request['candidate_index']==2:
                    raise ProviderError('upstream timeout')
                return super().complete(task,request)
        provider=FailingProvider()
        sr=NexMindSupremeShowrunnerP3('P',{'topic':'device'})
        s,v=seed_p2(sr)
        before=deepcopy(sr.state['decisions'])
        council=CreativeCouncilP3(sr,ArtDirector(provider),IllustrationFormResolver.from_file(INDEX),
            P3ExecutiveProducer(provider),ArtShowrunnerDecisionIntelligence(provider),StoryboardCompiler())
        with self.assertRaises(ProviderError):council.develop_art(s,v)
        self.assertEqual(sr.state['decisions'],before)
        self.assertFalse(any(task=='art_review' for task,_ in provider.calls))

    def test_combined_response_is_rejected_instead_of_silently_truncated(self):
        class CombinedProvider:
            def complete(self,task,request):
                return {'candidates':[art_candidate('A1','cutaway'),art_candidate('A2','macro')]}
        with self.assertRaises(ContractViolation):
            ArtDirector(CombinedProvider()).propose('P',{},story(),visual(),{}, {})


if __name__=='__main__':unittest.main()
