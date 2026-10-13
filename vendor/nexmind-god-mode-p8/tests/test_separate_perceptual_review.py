from __future__ import annotations

import base64, hashlib, io, json, os, shutil, subprocess, sys, unittest, wave
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from nexmind_god_mode.live_provider import LiveCreativeModelProvider, RoleRouter
from nexmind_god_mode.provider import ProviderError
FFMPEG=shutil.which('ffmpeg')


def evidence():
    bio=io.BytesIO()
    with wave.open(bio,'wb') as wav:
        wav.setnchannels(2); wav.setsampwidth(2); wav.setframerate(48000)
        wav.writeframes(b'\x01\x00\x01\x00'*4800)
    raw=bio.getvalue()
    return {'production_id':'P','multimodal_evidence':{'media_set_sha256':'original-media-set','perceptual_media':{
        'temporalFrames':[{'timestampSeconds':0,'sha256':'frame-sha','dataUrl':'data:image/png;base64,AAAA'}],
        'referenceVisuals':[{'sourceId':'reference-1','sha256':'reference-sha','dataUrl':'data:image/png;base64,BBBB'}],
        'audio':{'sha256':hashlib.sha256(raw).hexdigest(),'mimeType':'audio/wav','sampleRate':48000,'channels':2,'dataUrl':'data:audio/wav;base64,'+base64.b64encode(raw).decode()}
    }}}


def sample_output(schema):
    if 'enum' in schema:return schema['enum'][0]
    kind=schema.get('type')
    if kind=='object':return {key:sample_output(schema['properties'][key]) for key in schema.get('required',[])}
    if kind=='array':return [sample_output(schema['items']) for _ in range(schema.get('minItems',0))]
    if kind=='boolean':return True
    if kind in {'number','integer'}:return schema.get('minimum',0)
    if kind=='string':return 'observed fixture content'
    raise AssertionError(schema)


class FakeResponse:
    def __init__(self,data):self.data=data;self.headers={}
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self):return json.dumps(self.data).encode()


class SeparatePerceptualTests(unittest.TestCase):
    def setUp(self):
        self.env=patch.dict(os.environ,{'NEXMIND_REVIEW_MODEL':'test-multimodal','NEXMIND_REVIEW_PROVIDER':'gateway','NEXMIND_REVIEW_BASE_URL':'https://gateway.invalid/v1','NEXMIND_REVIEW_API_MODE':'chat_completions_prompt_json','NEXMIND_REVIEW_INPUT_MODALITIES':'images,audio','NEXMIND_REVIEW_AUDIO_INPUT_MODE':'chat_input_audio','NEXMIND_REVIEW_MULTIMODAL_REVIEW_MODE':'separate','NEXMIND_API_KEY':'synthetic-key'},clear=True)
        self.env.start();self.addCleanup(self.env.stop)
        self.provider=LiveCreativeModelProvider(max_retries=0)
        self.calls=[];self.audio_unavailable=False;self.fail_audio=False;self.bad_model=False;self.fail_synthesis=False;self.invalid_audio=False;self.repair_synthesis=False

    def respond(self,request,**kwargs):
        body=json.loads(request.data);self.calls.append(body)
        content=body['messages'][1]['content']
        text=content if isinstance(content,str) else content[0]['text']
        has_audio=isinstance(content,list) and any(part['type']=='input_audio' for part in content)
        has_images=isinstance(content,list) and any(part['type']=='image_url' for part in content)
        self.assertFalse(has_audio and has_images,'gateway rejects mixed native media')
        if has_audio and self.fail_audio:raise ProviderError('upstream audio rejected')
        system=body['messages'][0]['content']
        schema=json.loads(system.split('JSON Schema (including required fields, enums, types, and additionalProperties rules): ',1)[1].split(' SCHEMA REPAIR MODE:',1)[0].split(' JSON SYNTAX REPAIR MODE:',1)[0])
        output=sample_output(schema)
        if has_audio and self.audio_unavailable:output['available']=False
        if has_audio and self.invalid_audio:output['available']='yes'
        if not has_audio and not has_images and self.fail_synthesis:raise ProviderError('synthesis rejected')
        if not has_audio and not has_images and self.repair_synthesis and 'SCHEMA REPAIR MODE' not in system:output.pop('verdict')
        return FakeResponse({'id':'request-'+str(len(self.calls)),'model':'wrong-model' if self.bad_model else body['model'],'choices':[{'message':{'content':json.dumps(output)}}]})

    def test_both_roles_inspect_native_media_then_synthesize_without_mixed_payload(self):
        request=evidence();original=json.dumps(request)
        with patch('urllib.request.urlopen',side_effect=self.respond):
            for task in ('final_producer','perceptual_auditor'):self.provider.complete(task,request)
        self.assertEqual(len(self.calls),6)
        for offset in (0,3):
            visual,audio,synthesis=self.calls[offset:offset+3]
            self.assertEqual([x['type'] for x in visual['messages'][1]['content']],['text','image_url','image_url'])
            self.assertIn('native image attachments',visual['messages'][1]['content'][0]['text'])
            self.assertEqual([x['type'] for x in audio['messages'][1]['content']],['text','input_audio'])
            safe=json.loads(synthesis['messages'][1]['content'])
            self.assertEqual(set(safe['perceptual_observations']['stages']),{'images','audio'})
            metadata=safe['multimodal_evidence']['perceptual_delivery_metadata']
            self.assertEqual(metadata['temporal_frames'][0]['sha256'],'frame-sha')
            self.assertEqual(metadata['audio'][0]['sha256'],request['multimodal_evidence']['perceptual_media']['audio']['sha256'])
            self.assertNotIn('data:image/',json.dumps(synthesis));self.assertNotIn('data:audio/',json.dumps(synthesis))
            self.assertEqual(len(safe['perceptual_observations']['bindings']),2)
        self.assertNotIn('craft_scores',json.dumps(self.calls[3:]))
        self.assertEqual(json.dumps(request),original)
        self.assertEqual([x['task'] for x in self.provider.perceptual_delivery_dicts()],['final_producer','perceptual_auditor'])
        self.assertTrue(all(x['media_set_sha256']=='original-media-set' for x in self.provider.perceptual_delivery_dicts()))

    def test_missing_media_blocks_before_any_network_call(self):
        request=evidence();del request['multimodal_evidence']['perceptual_media']['audio']
        with patch('urllib.request.urlopen',side_effect=self.respond),self.assertRaisesRegex(ProviderError,'PERCEPTUAL_INPUTS_NOT_DELIVERED'):
            self.provider.complete('final_producer',request)
        self.assertEqual(self.calls,[])

    def test_failed_or_unavailable_audio_never_records_complete_delivery(self):
        for flag in ('fail_audio','audio_unavailable','invalid_audio','fail_synthesis'):
            with self.subTest(flag=flag):
                self.calls=[];setattr(self,flag,True)
                with patch('urllib.request.urlopen',side_effect=self.respond),self.assertRaises(ProviderError):
                    self.provider.complete('perceptual_auditor',evidence())
                self.assertEqual(self.provider.perceptual_delivery_dicts(),[])
                setattr(self,flag,False)

    def test_observation_model_mismatch_blocks_before_synthesis(self):
        self.bad_model=True
        with patch('urllib.request.urlopen',side_effect=self.respond),self.assertRaisesRegex(ProviderError,'MODEL_FAMILY_MISMATCH'):
            self.provider.complete('final_producer',evidence())
        self.assertEqual(len(self.calls),1);self.assertEqual(self.provider.perceptual_delivery_dicts(),[])

    def test_synthesis_schema_repair_retains_both_observations_without_native_media(self):
        self.repair_synthesis=True
        with patch('urllib.request.urlopen',side_effect=self.respond):self.provider.complete('perceptual_auditor',evidence())
        self.assertEqual(len(self.calls),4)
        repair=json.loads(self.calls[-1]['messages'][1]['content'])
        self.assertEqual(set(repair['original_request']['perceptual_observations']['stages']),{'images','audio'})
        self.assertNotIn('data:audio/',json.dumps(repair));self.assertNotIn('data:image/',json.dumps(repair))
        self.assertEqual(len(self.provider.perceptual_delivery_dicts()),1)

    def test_gateway_can_disable_idempotency_header_without_losing_audit_hashes(self):
        self.repair_synthesis=True
        def respond(request,**kwargs):
            self.assertIsNone(request.get_header('Idempotency-key'))
            return self.respond(request,**kwargs)
        with patch.dict(os.environ,{'NEXMIND_SEND_IDEMPOTENCY_KEY':'false'}),patch('urllib.request.urlopen',side_effect=respond):
            self.provider.complete('perceptual_auditor',evidence())
        self.assertEqual(len(self.calls),4)
        self.assertTrue(all(len(audit.request_hash)==64 for audit in self.provider.audits))

    def test_configured_reasoning_uses_low_for_inspections_and_high_for_judgment(self):
        self.repair_synthesis=True
        with patch.dict(os.environ,{'NEXMIND_PROMPT_JSON_SEND_REASONING':'true'}),patch('urllib.request.urlopen',side_effect=self.respond):
            self.provider.complete('perceptual_auditor',evidence())
        self.assertEqual([call['reasoning_effort'] for call in self.calls],['low','low','high','high'])

    @unittest.skipUnless(FFMPEG,'ffmpeg required')
    def test_48khz_stereo_review_audio_is_converted_and_bound_to_original(self):
        request=evidence();original=json.dumps(request)
        route=replace(RoleRouter().resolve('final_producer'),audio_sample_rate=16000)
        with patch.dict(os.environ,{'STUDIO_FFMPEG_BIN':FFMPEG}):
            normalized=self.provider._normalize_review_audio(request,route)
        audio=normalized['multimodal_evidence']['perceptual_media']['audio']
        with wave.open(io.BytesIO(base64.b64decode(audio['dataUrl'].split(',',1)[1])),'rb') as wav:
            self.assertEqual((wav.getframerate(),wav.getnchannels(),wav.getsampwidth()),(16000,1,2))
            self.assertEqual(wav.getnframes(),1600)
        self.assertEqual(audio['sourceSha256'],request['multimodal_evidence']['perceptual_media']['audio']['sha256'])
        self.assertNotEqual(audio['sourceSha256'],audio['sha256'])
        self.assertEqual(json.dumps(request),original)

    @unittest.skipUnless(FFMPEG,'ffmpeg required')
    def test_production_mp3_evidence_is_delivered_as_native_16khz_wav(self):
        request=evidence();audio=request['multimodal_evidence']['perceptual_media']['audio']
        raw=base64.b64decode(audio['dataUrl'].split(',',1)[1])
        mp3=subprocess.run([FFMPEG,'-v','error','-i','pipe:0','-f','mp3','pipe:1'],input=raw,capture_output=True,check=True).stdout
        audio.update({'mimeType':'audio/mpeg','sha256':hashlib.sha256(mp3).hexdigest(),'dataUrl':'data:audio/mpeg;base64,'+base64.b64encode(mp3).decode()})
        with patch.dict(os.environ,{'STUDIO_FFMPEG_BIN':FFMPEG,'NEXMIND_REVIEW_AUDIO_SAMPLE_RATE':'16000'}),patch('urllib.request.urlopen',side_effect=self.respond):
            self.provider.complete('perceptual_auditor',request)
        content=self.calls[1]['messages'][1]['content'][1]['input_audio']
        self.assertEqual(content['format'],'wav')
        with wave.open(io.BytesIO(base64.b64decode(content['data'])),'rb') as wav:
            self.assertEqual((wav.getframerate(),wav.getnchannels()),(16000,1))
            self.assertLess(wav.getnframes(),4800)
        delivery=self.provider.perceptual_delivery_dicts()[0]
        self.assertEqual(delivery['source_audio_sha256'],audio['sha256'])
        self.assertNotEqual(delivery['audio_sha256'],audio['sha256'])

    def test_registry_and_role_override_resolve_media_transport_configuration(self):
        with patch.dict(os.environ,{'NEXMIND_FINAL_EXECUTIVE_PRODUCER_MODEL':'pinned','NEXMIND_FINAL_EXECUTIVE_PRODUCER_INPUT_MODALITIES':'images,audio','NEXMIND_FINAL_EXECUTIVE_PRODUCER_AUDIO_INPUT_MODE':'chat_input_audio','NEXMIND_FINAL_EXECUTIVE_PRODUCER_MULTIMODAL_REVIEW_MODE':'separate','NEXMIND_FINAL_EXECUTIVE_PRODUCER_AUDIO_SAMPLE_RATE':'16000'}):
            route=RoleRouter().resolve('final_producer');self.assertEqual((route.multimodal_review_mode,route.audio_sample_rate),('separate',16000))
        registry=[{'provider':'test','model':'registry-model','capabilities':['multimodal_commercial_taste'],'input_modalities':['images','audio'],'audio_input_mode':'chat_input_audio','multimodal_review_mode':'separate','audio_sample_rate':16000}]
        with patch.dict(os.environ,{'NEXMIND_MODEL_REGISTRY_JSON':json.dumps(registry)},clear=True):
            route=RoleRouter().resolve('final_producer');self.assertEqual((route.multimodal_review_mode,route.audio_sample_rate),('separate',16000))


if __name__=='__main__':unittest.main(verbosity=2)
