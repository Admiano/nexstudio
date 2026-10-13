"""Regression tests for the pre-Editorial/pre-Sound storyboard review boundary."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT.parents[1] / 'services/studio-nexmind-p8'), str(ROOT / 'tests')]

import orchestrator
from nexmind_god_mode.p3_producer import P3ExecutiveProducer
from nexmind_god_mode.storyboard_compiler import StoryboardCompiler
from nexmind_god_mode.storyboard_compiler_v4 import SoundStoryboardCompiler
from nexmind_god_mode.showrunner_p2 import ProducerGateError
from test_p3_art_storyboard import (
    story, visual, art_candidate, seed_p2, DynamicProvider, IllustrationFormResolver,
    INDEX, NexMindSupremeShowrunnerP3, CreativeCouncilP3, ArtDirector,
    ArtShowrunnerDecisionIntelligence,
)


def issue(code, owner='VISUAL_CONCEPT', blocking=True):
    return {'code': code, 'owner_department': owner, 'blocking': blocking,
            'message': 'Pending department field.', 'required_fix': f'Resolve {code}.'}


def review(issues, verdict='REVISE', confidence='MEDIUM'):
    return {'verdict': verdict, 'issues': deepcopy(issues), 'strengths': ['Coherent settled states'],
            'revision_brief': 'Resolve the sound and timing fields.', 'commercial_confidence': confidence}


class ReplyProvider:
    def __init__(self, reply):
        self.reply = deepcopy(reply)
        self.requests = []

    def complete(self, task, request):
        self.requests.append((task, deepcopy(request)))
        return deepcopy(self.reply)


class StoryboardReviewScopeTests(unittest.TestCase):
    def setUp(self):
        self.board = StoryboardCompiler().compile(story(), visual(), art_candidate('A', 'cutaway'), {})

    def run_review(self, payload, board=None):
        self.provider = ReplyProvider(payload)
        return P3ExecutiveProducer(self.provider).review_storyboard(
            'P', {}, story(), visual(), art_candidate('A', 'cutaway'),
            self.board if board is None else board, {'status': 'PASS'})

    def test_prompt_names_actual_pending_fields_and_downstream_owners(self):
        self.run_review(review([], verdict='ACCEPT'))
        context = self.provider.requests[0][1]['stage_context']
        self.assertEqual(context['stage'], 'KEY_STATE_STORYBOARD')
        self.assertEqual(context['pending_fields']['vo_span'], ['B1', 'B2', 'B3'])
        self.assertEqual(context['pending_fields']['sound_intent'], ['B1', 'B2', 'B3'])
        self.assertEqual(context['field_owners']['vo_span'], 'EDITORIAL_RHYTHM')
        self.assertEqual(context['field_owners']['sound_intent'], 'SOUND_DIRECTION')

    def test_confirmed_placeholder_only_review_advances_without_rewriting_board(self):
        payload = review([issue('SOUND_INTENT_UNRESOLVED_ON_ALL_BEATS'),
                          issue('VO_SPAN_OBJECT_EMPTY_ON_ALL_BEATS')])
        original = deepcopy(self.board)
        result = self.run_review(payload)
        self.assertEqual(result['verdict'], 'ACCEPT')
        self.assertEqual(result['revision_brief'], '')
        self.assertTrue(all(x['blocking'] is False for x in result['issues']))
        self.assertEqual(len(result['deferred_department_checks']), 2)
        self.assertTrue(result['deferred_department_checks'][0]['original_issue']['blocking'])
        self.assertEqual(original, self.board)
        self.assertTrue(payload['issues'][0]['blocking'])

    def test_mixed_real_defect_still_blocks_and_routes_only_to_its_owner(self):
        real = issue('ON_SCREEN_COPY_CONTRADICTION', owner='ART_DIRECTION')
        real['required_fix'] = 'Make the highlighted words match the visible line.'
        result = self.run_review(review([issue('SOUND_INTENT_UNRESOLVED_ON_ALL_BEATS'), real]))
        self.assertEqual(result['verdict'], 'REVISE')
        self.assertEqual(orchestrator._key_storyboard_review_owner(result), 'ART_DIRECTION')
        self.assertEqual(result['revision_brief'], 'Resolve the current key-state defects only: Make the highlighted words match the visible line.')
        self.assertTrue(result['issues'][1]['blocking'])

    def test_all_known_placeholder_codes_are_scoped(self):
        codes = ['KEY_STATE_SOUND_PENDING', 'SOUND_DIRECTIVE_UNRESOLVED_IN_STORYBOARD',
                 'SOUND_DIRECTOR_UNRESOLVED_ALL_BEATS', 'SOUND_INTENT_UNRESOLVED_ON_ALL_BEATS',
                 'KEY_STATE_TIMING_PENDING', 'VO_SPAN_OBJECT_EMPTY_ON_ALL_BEATS', 'VO_SPAN_OBJECTS_EMPTY']
        for code in codes:
            with self.subTest(code=code):
                self.assertEqual(self.run_review(review([issue(code)]))['verdict'], 'ACCEPT')

    def test_authored_sound_contradiction_is_not_a_missing_plan(self):
        result = self.run_review(review([issue('SOUND_BRIEF_CONTRADICTION')]))
        self.assertEqual(result['verdict'], 'REVISE')
        self.assertNotIn('deferred_department_checks', result)

    def test_impossible_recording_fit_still_blocks(self):
        result = self.run_review(review([issue('RECORDING_DURATION_EXCEEDS_BRIEF')]))
        self.assertEqual(result['verdict'], 'REVISE')

    def test_supplied_spans_are_not_treated_as_pending(self):
        board = deepcopy(self.board)
        for beat in board['beats']:
            beat['vo_span'] = {'duration_seconds': 2}
        result = self.run_review(review([issue('VO_SPAN_OBJECT_EMPTY_ON_ALL_BEATS')]), board)
        self.assertEqual(result['verdict'], 'REVISE')
        self.assertNotIn('deferred_department_checks', result)

    def test_missing_fields_are_not_the_compilers_expected_placeholders(self):
        for field, code in [('vo_span', 'VO_SPAN_OBJECT_EMPTY_ON_ALL_BEATS'),
                            ('sound_intent', 'SOUND_INTENT_UNRESOLVED_ON_ALL_BEATS')]:
            with self.subTest(field=field):
                board = deepcopy(self.board)
                del board['beats'][0][field]
                self.assertEqual(self.run_review(review([issue(code)]), board)['verdict'], 'REVISE')

    def test_later_storyboard_never_defers_key_state_placeholders(self):
        board = deepcopy(self.board)
        board['schema'] = 'NexMindCanonicalSoundStoryboardV4'
        result = self.run_review(review([issue('SOUND_INTENT_UNRESOLVED_ON_ALL_BEATS')]), board)
        self.assertEqual(result['verdict'], 'REVISE')
        self.assertNotIn('deferred_department_checks', result)

    def test_unknown_code_missing_metadata_and_wrong_beat_stay_strict(self):
        missing = issue('KEY_STATE_SOUND_PENDING')
        del missing['blocking']
        wrong = issue('KEY_STATE_SOUND_PENDING')
        wrong['beat_ids'] = ['NONEXISTENT']
        for finding in [issue('SOUND_IS_WRONG'), missing, wrong]:
            with self.subTest(finding=finding):
                self.assertEqual(self.run_review(review([finding]))['verdict'], 'REVISE')

    def test_low_confidence_and_reject_are_never_promoted(self):
        for verdict, confidence in [('REVISE', 'LOW'), ('REJECT', 'HIGH')]:
            with self.subTest(verdict=verdict):
                result = self.run_review(review([issue('KEY_STATE_SOUND_PENDING')], verdict, confidence))
                self.assertEqual(result['verdict'], verdict)

    def test_advisory_story_or_visual_finding_cannot_hijack_real_art_repair(self):
        for advisory in [issue('STORY_INTERNAL_CONTRADICTION', 'STORY', False),
                         issue('OPTIONAL_VISUAL_POLISH', 'VISUAL_CONCEPT', False)]:
            result = review([advisory, issue('WEAK_SETTLED_STATE', 'ART_DIRECTION')])
            self.assertEqual(orchestrator._key_storyboard_review_owner(result), 'ART_DIRECTION')

    def test_legacy_issue_without_blocking_metadata_retains_owner(self):
        result = review([{'code': 'WEAK_SETTLED_STATE', 'owner_department': 'ART_DIRECTION'}])
        self.assertEqual(orchestrator._key_storyboard_review_owner(result), 'ART_DIRECTION')

    def test_sound_completion_gate_still_blocks_unresolved_plans(self):
        result = SoundStoryboardCompiler().gate(self.board)
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(result['missing_sound_beats'], ['B1', 'B2', 'B3'])

    def test_council_commits_rehearsal_but_cannot_grant_final_lock(self):
        class PendingProvider(DynamicProvider):
            def complete(self, task, request):
                if task == 'storyboard_review':
                    return review([issue('KEY_STATE_SOUND_PENDING'), issue('KEY_STATE_TIMING_PENDING')])
                return super().complete(task, request)

        provider = PendingProvider()
        sr = NexMindSupremeShowrunnerP3('P', {'topic': 'An existing machine explained'})
        s, v = seed_p2(sr)
        council = CreativeCouncilP3(sr, ArtDirector(provider), IllustrationFormResolver.from_file(INDEX),
                                    P3ExecutiveProducer(provider), ArtShowrunnerDecisionIntelligence(provider), StoryboardCompiler())
        selected = council.select_art(s, v, council.develop_art(s, v))
        result = council.compile_and_review_storyboard(s, v, selected)
        self.assertEqual(result['review']['verdict'], 'ACCEPT')
        self.assertEqual(sr.p3_ready_gate()['status'], 'PASS')
        with self.assertRaises(ProducerGateError) as error:
            sr.creative_lock()
        self.assertIn('sound_direction', error.exception.args[0]['missing_decisions'])
        self.assertIn('editorial_rhythm', error.exception.args[0]['missing_decisions'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
