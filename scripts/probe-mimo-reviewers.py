"""Synthetic conformance through P8's actual provider; no customer media is used."""
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/nexmind-god-mode-p8/src'))
from nexmind_god_mode.live_provider import RoleRouter, LiveCreativeModelProvider

spec = importlib.util.spec_from_file_location('boot_fixture', ROOT / 'scripts/nexmind-runtime-boot-probe.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


def digest(url):
    return hashlib.sha256(base64.b64decode(url.split(',', 1)[1])).hexdigest()


def main():
    output = Path(sys.argv[1])
    profile = json.loads((ROOT / 'config/nexmind/mimo-reviewers.json').read_text())
    router = RoleRouter()
    provider = LiveCreativeModelProvider(timeout_s=90, max_retries=1)
    result = {'checkedAt': datetime.now(timezone.utc).isoformat(), 'status': 'BLOCKED',
              'model': profile['model'], 'probes': [], 'routes': []}
    try:
        for task in profile['departmentTasks'] + profile['finalTasks']:
            route = router.resolve(task)
            if (route.model, route.provider, route.base_url, route.api_key_env) != (
                    profile['model'], profile['provider'], profile['baseUrl'], profile['apiKeyEnv']):
                raise RuntimeError('Profile route mismatch: ' + task)
            result['routes'].append({'task': task, 'role': route.role, 'model': route.model,
                                     'provider': route.provider, 'audioInputMode': route.audio_input_mode})
        request = {
            'production_id': 'SYNTHETIC_REVIEWER_CONFORMANCE',
            'brief': {'topic': 'Synthetic typography execution readiness check'},
            'execution_capabilities': {'available_performer_verbs': ['TYPE_REVEAL'],
                                       'available_support_bindings': []},
            'candidate': {'candidate_id': 'SYNTHETIC_ART',
                          'composition': {'supporting_roles': ['waterline rule']},
                          'execution_directives': ['TRACE_FLOW animates the waterline rule']},
            'review_instruction': 'Judge execution readiness against the supplied capabilities. '
                                  'A supporting role must have an available binding and a performer verb must be available. '
                                  'Identify each unsupported requirement as a blocking issue. Do not approve an unexecutable plan.'
        }
        answer = provider._complete_on_route('art_review', request, router.resolve('art_review'))
        issues = ' '.join(json.dumps(issue).lower() for issue in answer['issues'] if issue['blocking'])
        if answer['verdict'] not in {'REVISE', 'REJECT'} or 'trace_flow' not in issues or 'waterline' not in issues:
            raise RuntimeError('Unsupported-plan rejection failed: ' + json.dumps(answer))
        result['probes'].append({'task': 'art_review', 'status': 'PASS', 'answer': answer})
        print('PASS: department contract and unsupported-plan rejection', flush=True)
        media_set = hashlib.sha256((digest(fixture.PNG) + digest(fixture.AUDIO)).encode()).hexdigest()
        request = {'production_id': 'SYNTHETIC_REVIEWER_CONFORMANCE',
                   'brief': {'topic': 'Synthetic runtime conformance fixture; judge only supplied media.'},
                   'multimodal_evidence': {'status': 'COMPLETE', 'media_set_sha256': media_set,
                       'perceptual_media': {'temporalFrames': [{'timestampSeconds': 0, 'sha256': digest(fixture.PNG), 'dataUrl': fixture.PNG}],
                           'audio': {'sha256': digest(fixture.AUDIO), 'mimeType': 'audio/wav', 'sampleRate': 16000,
                                     'channels': 1, 'dataUrl': fixture.AUDIO}}}}
        for task in profile['finalTasks']:
            answer = provider._complete_separate_review(task, request, router.resolve(task))
            delivery = provider.perceptual_delivery_dicts()[-1]
            observations = {stage['modality']: stage['result'] for stage in delivery['stages']}
            visual = ' '.join(x['description'] for x in observations['images']['observations']).lower()
            audio = ' '.join(x['description'] for x in observations['audio']['observations']).lower()
            if 'green' not in visual or not any(x in visual for x in ('purple', 'magenta')):
                raise RuntimeError(task + ': synthetic image perception failed: ' + visual)
            if not (ROOT / 'scripts/fixtures/nexmind-boot-speech.wav').exists():
                raise RuntimeError('Spoken audio fixture is missing')
            if sum(word in audio for word in ('copper', 'violet', 'river')) < 2:
                raise RuntimeError(task + ': synthetic speech perception failed: ' + audio)
            result['probes'].append({'task': task, 'status': 'PASS', 'answer': answer, 'delivery': delivery})
            print('PASS: ' + task + ' native image/audio inspection and contract synthesis', flush=True)
        result['status'] = 'PASS'
    except Exception as error:
        result['error'] = str(error)[:1600]
        print('BLOCKED: ' + result['error'], flush=True)
    finally:
        result['audits'] = provider.audit_dicts()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return 0 if result['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
