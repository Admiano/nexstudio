"""Local contract/render regressions; fixtures are not accepted production films."""
from copy import deepcopy
from pathlib import Path
import hashlib
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'services/studio-family-engines'),str(ROOT/'services/studio-nexmind-p8'),
              str(ROOT/'vendor/nexmind-god-mode-p8/src'),str(ROOT/'reports/editorial-motion-enclave-test/python-deps')]
from contracts import AdapterBlocked, AdapterReplan
from canonical import stable
from editorial_adapter import _copy, _render_plan, _camera_binding, _exact_scene_asset, _write_authored_scenes_package, _catalog
from editorial_scene import bind_editorial_scene
from execution_plan import compile_execution_plan, compatibility_board
from nexmind_god_mode.editorial_bindings import validate_beat_bindings, capability_view
from nexmind_god_mode.contracts import ContractViolation
from nexmind_god_mode.storyboard_compiler import StoryboardCompiler
from nexmind_god_mode.storyboard_compiler_v2 import TemporalStoryboardCompiler
from nexmind_god_mode.storyboard_compiler_v3 import PerformanceStoryboardCompiler
from nexmind_god_mode.storyboard_compiler_v4 import SoundStoryboardCompiler
from nexmind_god_mode.live_provider import LiveCreativeModelProvider
from orchestrator import _review_owner
from capability_adapter import _fallback_family_execution_authority

PALETTE={'background':'#F2EDE3','ink':'#222222','surface':'#F2EDE3','primary':'#222222','accent':'#8A401A','secondary':'#666666'}

def text_binding(role,ref,text,placement='LEADING',emphasis='NORMAL'):
    return {'role':role,'kind':'TEXT','semantic_ref':ref,'text':text,'placement':placement,
            'scale':'BODY','tone':'INK','font':'DIDONE','weight':'REGULAR','align':'LEADING','emphasis':emphasis}

def fixture():
    story={'film_thesis':{},'beats':[]};visual={'candidate_id':'visual-test','camera_idea':'Hold the literal argument.', 'beat_treatments':[]}
    art={'candidate_id':'art-test','hero':{'semantic_ref':'clause'},'form_request':{'semantic_parts':['Give water.','THIRSTY']},
         'composition':{},'risk_notes':[],'typography_intent':'Literal clause with a vacancy.','beat_art':[]}
    cinema={'candidate_id':'camera-test','cinema_thesis':'Hold for reading.','attention_strategy':'The same literal clause.',
            'shots':[],'global_rules':[],'risk_notes':[]}
    editorial={'candidate_id':'edit-test','editorial_thesis':'Reading then a deliberate insertion.','project_rate':30,
               'target_duration_frames':90,'rhythm_profile':'BRIEF_AUTHORED','peak_budget':1,'beats':[],
               'final_payoff_hold_frames':12,'risk_notes':[]}
    motion={'candidate_id':'motion-test','executable':True,'actions':[]}
    for i,duration in enumerate((24,30,36)):
        bid='b'+str(i+1);start=sum((24,30,36)[:i])
        story['beats'].append({'beat_id':bid,'purpose':'INTERNAL_NOTE_ONLY','reveal':'Never print this production instruction.',
                              'audience_before':'unsure','audience_after':'clear','narration_mode':'SILENT'})
        visual['beat_treatments'].append({'beat_id':bid,'hero_state':'The same literal clause.','visual_action':'Give the argument time to read.'})
        hero=text_binding('hero description','clause','Give water.',emphasis='MUTED' if i==1 else 'NORMAL')
        support=[{'role':'background rest field','kind':'BACKGROUND','semantic_ref':'field','placement':'FULL_CANVAS','tone':'BACKGROUND'},
                 ({'role':'the unoccupied trailing blank','kind':'VACANCY','semantic_ref':'word-slot','placement':'TRAILING'} if i<2 else
                  text_binding('the fulfilled word slot','word-slot','THIRSTY','TRAILING')),
                 text_binding('mechanic line at reduced weight','caption','Need comes first.','LOWER'),
                 {'role':'intentional silence','kind':'SILENCE','semantic_ref':'silence'},
                 {'role':'held camera','kind':'CAMERA','semantic_ref':'HOLD'}]
        support[2]['scale']='CAPTION'
        art['beat_art'].append({'beat_id':bid,'settled_visual_state':'A readable literal argument with its intentional space.',
            'focal_owner':'clause','supporting_roles':[b['role'] for b in support],'meaning_without_motion':True,
            'display_copy':hero['text'],'hero_binding':hero,'support_bindings':support})
        cinema['shots'].append({'beat_id':bid,'idiom':'STATIC_TABLEAU','shot_scale':'MEDIUM','angle':'FRONTAL','subject_target':'clause',
            'reveal_framing':'INTERNAL_CAMERA_NOTE_ONLY','depth_strategy':'FLAT','camera_atom':{'atom':'HOLD','target':'clause','motivation':'Read the same clause.',
                'intensity':'NONE','start_semantic_state':'same frame','end_semantic_state':'same frame'},
            'transition_relation':'HOLD_CONTINUITY','attention_anchor':'clause','continuity_reason':'Retain the same clause.'})
        editorial['beats'].append({'beat_id':bid,'role':'reading' if i<2 else 'payoff','start':{'value':start,'rate':30},
            'duration':{'value':duration,'rate':30},'action_frame':0 if i==0 else 3,'settle_frame':18 if i==0 else 20 if i==1 else 24,
            'energy':'LOW','stillness_frames':6 if i==0 else 10 if i==1 else 12,'overlap_to_next_frames':0,
            'transition':'HOLD_THROUGH','duration_rationale':'Deliberately allocate the insertion more time.'})
        verbs=[('SETTLE','clause')] if i==0 else [('DE_EMPHASIZE','clause')] if i==1 else [('STATE_CHANGE','clause'),('TYPE_REVEAL','word-slot')]
        for j,(verb,ref) in enumerate(verbs):
            motion['actions'].append({'beat_id':bid,'action_id':bid+'-a'+str(j+1),'performer_class':'SCENE_GRAPH','requested_verb':verb,
                                     'actor':ref,'target':ref,'overlap_policy':'SERIAL_REQUIRED'})
    key=StoryboardCompiler().compile(story,visual,art,{'status':'SUPPORTED'})
    temporal=TemporalStoryboardCompiler().compile(key,cinema,editorial,{})
    performance=PerformanceStoryboardCompiler().compile(temporal,motion)
    final=SoundStoryboardCompiler().compile(performance,{'candidate_id':'sound-test','events':[], 'beat_sound_summary':[]})
    return final

def request(board=None):
    brand={'schema':'StudioBrandExecutionV1','memoryInputSnapshotId':'fixture','memoryInputSnapshotHash':'fixture',
           'brandExecutionHash':'fixture','productionBrandContext':PALETTE}
    return {'schema':'StudioFamilyEngineRequestV1','operation':'BUILD_INTERNAL_REVIEW_EVIDENCE','productionId':'typed-handoff-local-regression',
            'family':'EDITORIAL_MOTION','durationSeconds':3,'aspectRatio':'16:9','brandExecution':brand,'finalBoard':board or fixture()}

def bind(board):
    return bind_editorial_scene(board,PALETTE,lambda b,h: None,_camera_binding)

def update_source(board):
    """Explicitly reauthor a test fixture only; never patch saved production decisions."""
    board['authored_art']['beat_bindings']=[{'beat_id':b['beat_id'],'supporting_roles':deepcopy(b['supporting_assets']),
        **{k:deepcopy(b[k]) for k in ('display_copy','hero_binding','support_bindings')}} for b in board['beats']]

class TypedHandoffTests(unittest.TestCase):
    def test_all_p8_compilers_and_canonical_execution_preserve_exact_art(self):
        board=fixture();before=deepcopy(board);spec=bind(board)
        plan=compile_execution_plan(request(board),board)
        self.assertEqual(compatibility_board(plan),board);self.assertEqual(board,before)
        self.assertEqual(spec['duration'],3);self.assertEqual(spec['sourceBoardHash'],stable(board))
        self.assertEqual(spec['scenes'][-1]['nodes'][1]['kind'],'BACKGROUND')
        self.assertEqual(sum(len(s['nonvisualBindings']) for s in spec['scenes']),6)

    def test_each_support_has_exactly_one_typed_binding(self):
        board=fixture();b=board['beats'][0]
        for mutate in (lambda b:b['support_bindings'].pop(),lambda b:b['support_bindings'].append(deepcopy(b['support_bindings'][0])),
                       lambda b:b['supporting_assets'].append('unknown prop'),lambda b:b['hero_binding'].update(text='Invented copy')):
            candidate=deepcopy(b);mutate(candidate)
            with self.subTest(candidate=candidate),self.assertRaises(ContractViolation):validate_beat_bindings(candidate,required=True)

    def test_no_display_copy_fallback_or_whitespace_rewriting(self):
        with self.assertRaises(AdapterReplan) as caught:_copy({'beat_id':'b01','scene_thesis':'internal planning prose'})
        self.assertEqual(caught.exception.repair_request['invalidate_slots'][0],'art_direction')
        self.assertEqual(_copy({'display_copy':'Water  for\nthe thirsty—now.'}),'Water  for\nthe thirsty—now.')
        self.assertEqual(_copy({'display_copy':''}),'')

    def test_native_and_nonvisual_supports_never_enter_asset_resolver(self):
        with patch.dict(os.environ,{'STUDIO_EDITORIAL_ENGINE_ROOT':str(ROOT/'engines/editorial')}),patch('editorial_adapter._catalog_binding',side_effect=AssertionError('fuzzy lookup')):
            plan=_render_plan(request())
        self.assertEqual(plan['stage'],'STUDIO_P8_TYPED_EDITORIAL');self.assertFalse(plan['adapterTrace']['creativeChoiceIntroduced'])
        self.assertEqual(plan['renderProgram']['assets'],[])

    def test_old_ambiguous_board_returns_to_art_before_catalog_guessing(self):
        board=fixture()
        for beat in board['beats']:
            for key in ('display_copy','hero_binding','support_bindings'):beat.pop(key)
        board['authored_art']={}
        with patch.dict(os.environ,{'STUDIO_EDITORIAL_ENGINE_ROOT':str(ROOT/'engines/editorial')}),patch('editorial_adapter._catalog_binding',side_effect=AssertionError('lookup before handoff validation')):
            with self.assertRaises(AdapterReplan) as caught:_render_plan(request(board))
        self.assertEqual(caught.exception.code,'EDITORIAL_P8_DISPLAY_COPY_MISSING')
        self.assertNotIn('visual_concept',caught.exception.repair_request['invalidate_slots'])

    def test_source_art_tampering_is_not_accepted(self):
        board=fixture();board['beats'][0]['hero_binding']['text']='Different approved-looking copy';board['beats'][0]['display_copy']='Different approved-looking copy'
        with self.assertRaises(AdapterReplan) as caught:bind(board)
        self.assertEqual(caught.exception.code,'EDITORIAL_ART_PROVENANCE_CHANGED')

    def test_missing_audio_or_camera_obligation_routes_to_its_owner(self):
        for kind,ref,slot in [('NARRATION','recording','art_direction'),('SOUND_EVENT','depletion','sound_direction'),('CAMERA','PAN','cinematography')]:
            board=fixture();b=board['beats'][0];binding=b['support_bindings'][-1 if kind=='CAMERA' else -2]
            binding.update(kind=kind,semantic_ref=ref);update_source(board)
            with self.subTest(kind=kind),self.assertRaises(AdapterReplan) as caught:bind(board)
            self.assertEqual(caught.exception.repair_request['invalidate_slots'][0],slot)

    def test_exact_sound_and_narration_bindings_are_not_visual_nodes(self):
        for kind,ref in [('NARRATION','recording'),('SOUND_EVENT','depletion')]:
            board=fixture();b=board['beats'][0];b['support_bindings'][-2].update(kind=kind,semantic_ref=ref)
            if kind=='NARRATION':b['narration_mode']='VOICEOVER';b['narration_text']='Give water.'
            else:b['sound_events']=[{'event_id':'cue','kind':'SFX','semantic_tag':'depletion','optional':False,'sync_target':'b1-a1'}]
            update_source(board);spec=bind(board)
            self.assertEqual(len(spec['scenes'][0]['nodes']),4)
            self.assertIn(kind,[b['kind'] for b in spec['scenes'][0]['nonvisualBindings']])
            if kind=='SOUND_EVENT':self.assertEqual(spec['soundSync']['cue']['end'],.8)

    def test_silence_cannot_hide_audible_events(self):
        board=fixture();board['beats'][0]['sound_events']=[{'kind':'SFX'}]
        with self.assertRaises(AdapterReplan) as caught:bind(board)
        self.assertEqual(caught.exception.code,'EDITORIAL_SILENCE_BINDING_UNRESOLVED')

    def test_unbound_motion_and_fake_changes_are_rejected(self):
        board=fixture();board['beats'][1]['motion_actions'][0]['target']='an invented prop'
        with self.assertRaises(AdapterReplan) as caught:bind(board)
        self.assertEqual(caught.exception.repair_request['invalidate_slots'][0],'motion_performance')
        board=fixture();board['beats'][1]['hero_binding']['emphasis']='NORMAL';update_source(board)
        with self.assertRaises(AdapterReplan) as caught:bind(board)
        self.assertEqual(caught.exception.code,'EDITORIAL_AUTHORED_TRANSITION_MISSING')
        self.assertEqual(caught.exception.repair_request['invalidate_slots'][0],'art_direction')

    def test_vacancy_must_remain_unoccupied(self):
        board=fixture();board['beats'][0]['hero_binding']['placement']='MAIN';update_source(board)
        with self.assertRaises(AdapterReplan) as caught:bind(board)
        self.assertEqual(caught.exception.code,'EDITORIAL_AUTHORED_VACANCY_OCCLUDED')

    def test_exact_asset_binding_does_not_guess_an_icon(self):
        binding={'semantic_ref':'physical cup','asset_id':'not-an-asset','source':'CATALOG'}
        catalog=[{'assetId':'real-asset','label':'physical cup','family':'literal-prop'}]
        self.assertIsNone(_exact_scene_asset(binding,catalog,[],ROOT,'16:9',True))
        binding['asset_id']='real-asset';catalog[0]['family']='icon'
        self.assertIsNone(_exact_scene_asset(binding,catalog,[],ROOT,'16:9',True))

    def test_asset_bytes_and_rights_are_checked_before_packaging(self):
        spec=bind(fixture());node=spec['scenes'][0]['nodes'][0]
        node['assetBinding']={'assetId':'asset','sourcePath':str(ROOT/'package.json'),'sha256':'incorrect','sourceLicense':'test','commercialEligibility':'test'}
        with tempfile.TemporaryDirectory() as temp,self.assertRaises(AdapterBlocked) as caught:
            _write_authored_scenes_package({'authoredScenes':spec},Path(temp))
        self.assertEqual(caught.exception.code,'EDITORIAL_EXACT_ASSET_MISSING_OR_CHANGED')

    def test_installed_literal_asset_binds_to_its_exact_file_hash(self):
        root=ROOT/'engines/editorial';catalog=_catalog(root)
        item=next(a for a in catalog if a['family']=='literal-prop')
        binding={'asset_id':item['assetId'],'source':'CATALOG','semantic_ref':'approved prop'}
        asset=_exact_scene_asset(binding,catalog,[],root,'16:9',True)
        self.assertEqual(asset['assetId'],item['assetId'])
        self.assertEqual(hashlib.sha256(Path(asset['sourcePath']).read_bytes()).hexdigest(),item['sha256'])

    def test_exact_customer_media_id_and_source_hash_are_not_fuzzy(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'object.svg';path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><circle cx="50" cy="50" r="40" fill="#ff3300"/></svg>')
            ref={'assetId':'A','path':str(path),'mimeType':'image/svg+xml','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            binding={'asset_id':'A','source':'CUSTOMER_MEDIA','semantic_ref':'explicit object'}
            asset=_exact_scene_asset(binding,[],[ref],ROOT,'16:9',True)
            self.assertEqual(asset['assetId'],'A')
            ref['sha256']='changed'
            with self.assertRaises(AdapterBlocked):_exact_scene_asset(binding,[],[ref],ROOT,'16:9',True)

    def test_provider_schema_requires_bindings_for_editorial_only(self):
        schema=LiveCreativeModelProvider._schema_for_request('art',{'candidate_budget':1,'editorial_execution_contract':capability_view()})
        required=schema['properties']['candidates']['items']['properties']['beat_art']['items']['required']
        self.assertTrue({'display_copy','hero_binding','support_bindings'}<=set(required))
        other=LiveCreativeModelProvider._schema_for_request('art',{})
        self.assertNotIn('hero_binding',other['properties']['candidates']['items']['properties']['beat_art']['items']['required'])

    def test_temporal_copy_critique_routes_to_art_and_fallback_authority_is_bound(self):
        review={'issues':[{'code':'EDITORIAL_P8_DISPLAY_COPY_MISSING','blocking':True}],'revision_brief':'Fix the final camera payoff.'}
        self.assertEqual(_review_owner(review,'EDITORIAL_RHYTHM',{'VISUAL_CONCEPT','ART_DIRECTION','CINEMATOGRAPHY','EDITORIAL_RHYTHM'}),'ART_DIRECTION')
        self.assertTrue(_fallback_family_execution_authority('EDITORIAL_MOTION').get('authorityId'))

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright=None

@unittest.skipUnless(sync_playwright,'Playwright required for actual browser regression')
class TypedRuntimeTests(unittest.TestCase):
    def test_real_frames_copy_emphasis_blank_insertion_and_repeatable_seek(self):
        spec=bind(fixture());rp={'authoredScenes':spec,'brand':PALETTE}
        with tempfile.TemporaryDirectory() as temp,sync_playwright() as p:
            manifest=_write_authored_scenes_package(rp,Path(temp))
            browser=p.chromium.launch(executable_path=os.environ.get('STUDIO_CHROMIUM_PATH',r'C:\Program Files\Google\Chrome\Application\chrome.exe'),headless=True,args=['--disable-gpu','--no-sandbox'])
            page=browser.new_page(viewport={'width':1280,'height':720});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.set_content(Path(manifest['renderHtml']).read_text(encoding='utf-8'));page.evaluate('() => document.fonts.ready')
            def seek(t):return page.evaluate('(t)=>window.NexFacelessRenderer.seek(t)',t)
            opening=seek(0);initial=page.screenshot();middle=seek(1.6);deemphasized=page.screenshot()
            inserting=seek(2.3);final=seek(2.99);last=page.screenshot()
            self.assertEqual(opening['nodes'][2]['kind'],'VACANCY')
            self.assertAlmostEqual(middle['nodes'][0]['opacity'],.35)
            self.assertNotEqual(initial,deemphasized)
            self.assertLess(len(inserting['nodes'][2]['text']),len('THIRSTY'))
            self.assertEqual(final['nodes'][2]['text'],'THIRSTY')
            self.assertEqual(final['nodes'][0]['text'],'Give water.')
            self.assertNotIn('INTERNAL',page.locator('body').inner_text())
            self.assertNotIn('mechanic line',page.locator('body').inner_text())
            seek(0);seek(1);seek(2.99);self.assertEqual(last,page.screenshot())
            self.assertTrue(final['fontLoaded']);self.assertFalse(final['copyClipped']);self.assertFalse(errors)
            for width,height in [(900,900),(720,1280)]:
                page.set_viewport_size({'width':width,'height':height})
                probe=seek(2.99);self.assertFalse(probe['copyClipped']);self.assertEqual(probe['nodes'][2]['text'],'THIRSTY')
            # The renderer must expose overflow for the capture gate to reject it;
            # it must not silently shrink, clip or discard approved literal copy.
            broken=deepcopy(rp);broken['authoredScenes']['scenes'][-1]['nodes'][-1]['text']='UnbrokenAudienceWord'*100
            bad=_write_authored_scenes_package(broken,Path(temp)/'overflow')
            page.set_content(Path(bad['renderHtml']).read_text(encoding='utf-8'));page.evaluate('() => document.fonts.ready')
            self.assertTrue(seek(2.99)['copyClipped'])
            # Actual decoding of an explicitly selected customer asset, including
            # a one-character ID which cannot work through the old fuzzy resolver.
            asset_path=Path(temp)/'customer.svg';asset_path.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><circle cx="50" cy="50" r="40" fill="#ff3300"/></svg>')
            media={'assetId':'A','path':str(asset_path),'mimeType':'image/svg+xml','sha256':hashlib.sha256(asset_path.read_bytes()).hexdigest()}
            asset_board=fixture()
            for beat in asset_board['beats']:
                beat['hero_binding']={'role':'hero description','kind':'ASSET','semantic_ref':'clause','placement':'LEADING',
                    'asset_id':'A','source':'CUSTOMER_MEDIA','emphasis':'MUTED' if beat['beat_id']=='b2' else 'NORMAL'}
                beat['display_copy']=''
            update_source(asset_board)
            asset_spec=bind_editorial_scene(asset_board,PALETTE,lambda b,h:_exact_scene_asset(b,[],[media],ROOT,'16:9',h),_camera_binding)
            asset_package=_write_authored_scenes_package({'authoredScenes':asset_spec,'brand':PALETTE},Path(temp)/'asset')
            page.set_content(Path(asset_package['renderHtml']).read_text(encoding='utf-8'));seek(2.99)
            page.evaluate('() => Promise.all(Array.from(document.images, img => img.decode()))')
            self.assertEqual(page.locator('img').count(),1)
            self.assertTrue(page.evaluate('() => document.images[0].naturalWidth > 0'))
            self.assertNotIn('hero description',page.locator('body').inner_text())
            # A valid sans-only scene must not fail because an unused Didone
            # face was never requested. Capture also warms the bundled face for
            # future TYPE_REVEAL nodes which begin with empty text.
            sans_board=fixture()
            for beat in sans_board['beats']:
                for b in [beat['hero_binding'],*beat['support_bindings']]:
                    if b['kind']=='TEXT':b['font']='SANS'
            update_source(sans_board);sans_spec=bind(sans_board)
            sans_package=_write_authored_scenes_package({'authoredScenes':sans_spec,'brand':PALETTE},Path(temp)/'sans')
            page.set_content(Path(sans_package['renderHtml']).read_text(encoding='utf-8'));page.evaluate('() => document.fonts.ready')
            self.assertTrue(seek(2.99)['fontLoaded'])
            browser.close()

if __name__=='__main__':unittest.main()
