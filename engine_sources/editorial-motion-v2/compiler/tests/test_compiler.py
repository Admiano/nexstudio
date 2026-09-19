"""Authority + compiler gates on the hand-authored fixture treatment.

Run from the package dir: ``python3 -m pytest -q compiler/tests``.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
ROOT = PKG.parent
sys.path.insert(0, str(PKG))

from editorial_plan_compiler.compiler import HERO_SUPPORT_MIN_RATIO, PLAN_SCHEMA, compile_film  # noqa: E402
from editorial_plan_compiler.contracts import FilmTreatment, TreatmentError  # noqa: E402
from editorial_plan_compiler.figures import EXCLUDED_FACES  # noqa: E402
from editorial_plan_compiler.sound import MAX_ACCENTS_PER_BEAT, MIN_ACCENT_GAP_MS  # noqa: E402
from editorial_plan_compiler.timing import (  # noqa: E402
    EXIT_MS, LAND_SETTLE_MS, MIN_HOLD_MS, beat_clock, find_landing, synthesise_alignment, words_from_alignment,
)
from editorial_plan_compiler.typefit import _face, fit_text, measure, wrap  # noqa: E402

FIXTURE = ROOT / 'fixtures' / 'reply-speed.treatment.json'
ASPECTS = ('9x16', '1x1', '16x9')


def _overlap(a, b):
    return max(0.0, min(a['x'] + a['w'], b['x'] + b['w']) - max(a['x'], b['x'])) * \
        max(0.0, min(a['y'] + a['h'], b['y'] + b['h']) - max(a['y'], b['y']))


@pytest.fixture(scope='module')
def treatment():
    return json.loads(FIXTURE.read_text())


@pytest.fixture(scope='module')
def result(treatment, tmp_path_factory):
    return compile_film(treatment, tmp_path_factory.mktemp('work'), base_dir=FIXTURE.parent)


@pytest.fixture(scope='module')
def plans(result):
    return result['plans']


# ---------------------------------------------------------------- timing

def test_alignment_groups_characters_into_words():
    al = synthesise_alignment('Speed is not a feature.', 'seed')
    words = words_from_alignment(al)
    assert [w.text for w in words] == ['Speed', 'is', 'not', 'a', 'feature.']
    assert all(w.end_ms > w.start_ms for w in words)
    assert all(b.start_ms >= a.end_ms for a, b in zip(words, words[1:]))


def test_fixture_alignment_is_deterministic_and_seeded():
    a = synthesise_alignment('Forty-one conversations. Six answered.', 'x:b05')
    b = synthesise_alignment('Forty-one conversations. Six answered.', 'x:b05')
    c = synthesise_alignment('Forty-one conversations. Six answered.', 'x:b06')
    assert a == b and a != c and a['fixture'] is True


def test_landing_finds_anchor_and_prefix():
    words = words_from_alignment(synthesise_alignment('It is respect, truly.', 's'))
    assert find_landing(words, 'respect') == 2
    assert find_landing(words, 'truly') == 3
    assert find_landing(words, 'missing') is None


def test_beat_clock_leaves_room_for_settle_hold_and_exit():
    al = synthesise_alignment('Start replying in seconds.', 's')
    clock = beat_clock('b', ['FREE TO TRY', 'Start replying in seconds'], [None, 'Start'], al, 'FIXTURE', min_duration_ms=1400)
    assert clock.landing_source[1] == 'WORD'
    assert clock.duration_ms >= max(clock.landings_ms) + LAND_SETTLE_MS + MIN_HOLD_MS + EXIT_MS
    assert clock.landings_ms == sorted(clock.landings_ms)


def test_beat_clock_without_alignment_lands_proportionally():
    clock = beat_clock('b', ['one', 'two'], [None, None], None, 'NONE', min_duration_ms=2000)
    assert clock.landing_source == ['PROPORTIONAL', 'PROPORTIONAL']
    assert clock.landings_ms[0] < clock.landings_ms[1] < clock.duration_ms


# ---------------------------------------------------------------- typefit

def test_wrap_never_breaks_inside_a_word():
    face = _face('hero', '800')
    width = measure('Extraordinarily', face, 100, -0.02) - 1
    assert wrap('Extraordinarily long', face, 100, width, -0.02) is None
    lines = wrap('Most small businesses lose customers', face, 100, measure('Most small businesses', face, 100, -0.02) + 1, -0.02)
    assert lines and all(measure(l, face, 100, -0.02) <= measure('Most small businesses', face, 100, -0.02) + 1 for l in lines)


def test_fit_preserves_authored_lines():
    fit = fit_text('Speed is not a feature.', {'x': 0, 'y': 0, 'w': 900, 'h': 600}, 'hero', '800', (1080, 1080), authored_lines=['Speed is not', 'a feature.'])
    assert fit.lines == ['Speed is not', 'a feature.']
    assert fit.status == 'FIT'


# ---------------------------------------------------------------- contracts

def test_contract_rejects_foreign_schema(treatment):
    bad = copy.deepcopy(treatment)
    bad['schema'] = 'Other'
    with pytest.raises(TreatmentError) as e:
        FilmTreatment.parse(bad)
    assert e.value.code == 'TREATMENT_SCHEMA_MISMATCH'


def test_contract_rejects_unjustified_figure(treatment):
    bad = copy.deepcopy(treatment)
    fig_beat = next(b for b in bad['beats'] if b.get('figure'))
    fig_beat['figure']['justification'] = ''
    with pytest.raises(TreatmentError) as e:
        FilmTreatment.parse(bad)
    assert e.value.code == 'FIGURE_UNJUSTIFIED' and e.value.beat_id == fig_beat['beat_id']


def test_contract_rejects_invented_copy_paths(treatment):
    bad = copy.deepcopy(treatment)
    bad['beats'][0]['display_units'][0]['text'] = '   '
    with pytest.raises(TreatmentError) as e:
        FilmTreatment.parse(bad)
    assert e.value.code == 'DISPLAY_UNIT_EMPTY'


def test_contract_rejects_unknown_aspect_and_media(treatment):
    bad = copy.deepcopy(treatment)
    bad['aspects'] = ['4x3']
    with pytest.raises(TreatmentError) as e:
        FilmTreatment.parse(bad)
    assert e.value.code == 'ASPECT_UNKNOWN'
    bad = copy.deepcopy(treatment)
    next(b for b in bad['beats'] if b.get('media'))['media']['asset_id'] = 'ghost'
    with pytest.raises(TreatmentError) as e:
        FilmTreatment.parse(bad)
    assert e.value.code == 'MEDIA_ASSET_NOT_IN_LIBRARY'


def test_missing_media_file_fails_instead_of_substituting(treatment, tmp_path):
    bad = copy.deepcopy(treatment)
    bad['media_library'][0]['path'] = 'assets/does-not-exist.png'
    with pytest.raises(TreatmentError) as e:
        compile_film(bad, tmp_path, base_dir=FIXTURE.parent)
    assert e.value.code == 'MEDIA_ASSET_FILE_MISSING'


# ---------------------------------------------------------------- compiled plans

def test_fixture_compiles_all_three_aspects_pass(result):
    assert result['gate']['status'] == 'PASS', result['gate']['failures']
    assert list(result['plans']) == list(ASPECTS)
    for a in ASPECTS:
        assert result['plans'][a]['schema'] == PLAN_SCHEMA


def test_plans_are_native_not_scaled(plans):
    for a, p in plans.items():
        for b in p['beats']:
            c = b['composition']
            assert c['native_profile'] is True and c['derived_by_scaling'] is False
            assert c['authority'] == 'NATIVE_THREE_ASPECT_COMPOSITION_AUTHORITY_V2'
    fam = {a: {b['composition']['layout_family'] for b in p['beats']} for a, p in plans.items()}
    assert fam['9x16'].isdisjoint(fam['16x9']) and fam['1x1'].isdisjoint(fam['16x9'])


def test_every_beat_holds_readably_and_hold_follows_all_arrivals(plans):
    for p in plans.values():
        for b in p['beats']:
            hw = b['ensemble']['hold_window']
            assert hw['end_ms'] - hw['start_ms'] >= MIN_HOLD_MS, b['beat_id']
            typ = b['typography']
            arrivals = [e['end_ms'] for e in typ['events'] + typ['performance_events'] if e['unit_index'] != -1]
            for ch in ('media', 'figure'):
                if b[ch]:
                    arrivals.append(b[ch]['enter_ms'] + b[ch]['enter_duration_ms'])
            assert hw['start_ms'] >= max(arrivals), b['beat_id']
            assert hw['end_ms'] <= b['transition']['start_ms'], b['beat_id']
            hold = next(e for e in typ['events'] if e['event'] == 'HOLD')
            assert (hold['start_ms'], hold['end_ms']) == (hw['start_ms'], hw['end_ms'])


def test_text_blocks_never_collide_or_leave_text_zone(plans):
    for p in plans.values():
        for b in p['beats']:
            blocks = b['typography']['blocks']
            zone = b['composition']['text_zone']
            for bl in blocks:
                bb = bl['bbox']
                assert bb['x'] >= zone['x'] - 1 and bb['y'] >= zone['y'] - 1, (b['beat_id'], bl['text'])
                assert bb['x'] + bb['w'] <= zone['x'] + zone['w'] + 1 and bb['y'] + bb['h'] <= zone['y'] + zone['h'] + 1, (b['beat_id'], bl['text'])
                assert bl['fit']['status'] == 'FIT', (b['beat_id'], bl['text'])
            for i, x in enumerate(blocks):
                for y in blocks[i + 1:]:
                    same_replace = x.get('replace_partner') == y['unit_index'] and y.get('replace_partner') == x['unit_index']
                    assert same_replace or _overlap(x['bbox'], y['bbox']) == 0, (b['beat_id'], x['text'], y['text'])


def test_hero_dominates_support(plans):
    for p in plans.values():
        for b in p['beats']:
            heroes = [bl for bl in b['typography']['blocks'] if bl['role'] == 'hero']
            supports = [bl for bl in b['typography']['blocks'] if bl['role'] in ('support', 'label')]
            if heroes and supports:
                assert max(h['fit']['font_px'] for h in heroes) >= HERO_SUPPORT_MIN_RATIO * max(s['fit']['font_px'] for s in supports), b['beat_id']


def test_display_copy_is_authored_verbatim(treatment, plans):
    by_id = {b['beat_id']: b for b in treatment['beats']}
    for p in plans.values():
        for b in p['beats']:
            authored = [' '.join(u['text'].split()) for u in by_id[b['beat_id']]['display_units']]
            compiled = [' '.join(bl['text'].split()) for bl in b['typography']['blocks']]
            assert sorted(compiled) == sorted(authored), b['beat_id']
            for bl in b['typography']['blocks']:
                assert ' '.join(' '.join(bl['fit']['lines']).split()) == ' '.join(bl['text'].split())


def test_phrase_replace_only_with_a_partner(plans):
    for p in plans.values():
        for b in p['beats']:
            stage_b = {bl['unit_index'] for bl in b['typography']['blocks'] if bl['style'] == 'replace_stage_b'}
            reps = [e for e in b['typography']['events'] if e['event'] == 'PHRASE_REPLACE']
            assert {e['unit_index'] for e in reps} == stage_b, b['beat_id']
            if stage_b:
                a = next(bl for bl in b['typography']['blocks'] if bl['style'] == 'replace_stage_a')
                assert a['exit_ms'] == reps[0]['start_ms']
    assert any(bl['style'] == 'replace_stage_b' for p in plans.values() for b in p['beats'] for bl in b['typography']['blocks'])


def test_every_unit_has_a_reveal(plans):
    for p in plans.values():
        for b in p['beats']:
            revealed = {e['unit_index'] for e in b['typography']['events'] if e['unit_index'] >= 0}
            assert revealed == {bl['unit_index'] for bl in b['typography']['blocks']}, b['beat_id']


def test_media_is_governed_evidence_with_provenance(treatment, plans):
    for p in plans.values():
        beats = {b['beat_id']: b for b in p['beats']}
        for tb in treatment['beats']:
            b = beats[tb['beat_id']]
            if not tb.get('media'):
                assert b['media'] is None or b['media']['carried_from'], tb['beat_id']
                continue
            m = b['media']
            assert m['asset_id'] == tb['media']['asset_id'] and m['sha256'] and m['original_sha256']
            assert Path(m['path']).exists()
            zone = b['composition']['visual_zone']
            assert _overlap(m['bbox'], zone) == pytest.approx(m['bbox']['w'] * m['bbox']['h'])
            for bl in b['typography']['blocks']:
                assert _overlap(bl['bbox'], m['bbox']) == 0, (tb['beat_id'], bl['text'])
            if tb['media'].get('persist_to'):
                nxt = beats[tb['media']['persist_to']]
                assert nxt['media']['asset_id'] == m['asset_id']
                assert b['transition']['mode'] == 'EVIDENCE_PERSISTENCE'
        vid = next(m for m in p['provenance']['media_assets'] if m['kind'] == 'VIDEO')
        assert vid['normalised'] and vid['render_codec'] == 'vp9' and vid['render_sha256'] != vid['original_sha256']


def test_figure_is_still_full_body_and_justified(plans):
    seen = False
    for p in plans.values():
        for b in p['beats']:
            if not b['figure']:
                continue
            seen = True
            f = b['figure']
            assert f['still'] is True and f['framing'] == 'FULL_BODY'
            assert f['justification'] and f['emotion'] and f['pose']
            assert f['parts'] and all(part['sha256'] and (ROOT / 'assets' / 'peeps' / part['file']).exists() for part in f['parts'])
            assert next(part['part_id'] for part in f['parts'] if part['slot'] == 'face') not in EXCLUDED_FACES
            for bl in b['typography']['blocks']:
                assert _overlap(bl['bbox'], f['bbox']) == 0, (b['beat_id'], bl['text'])
    assert seen


def test_sound_is_semantic_admitted_and_spaced(plans):
    for p in plans.values():
        for b in p['beats']:
            acc = b['sound']['accents']
            assert len(acc) <= MAX_ACCENTS_PER_BEAT
            times = sorted(a['beat_at_ms'] for a in acc)
            assert all(y - x >= MIN_ACCENT_GAP_MS for x, y in zip(times, times[1:])), b['beat_id']
            for a in acc:
                assert a['license'] == 'CC0-1.0' and a['sha256'] and Path(a['path']).exists()
                assert 0 <= a['beat_at_ms'] <= b['duration_ms']
        if p['music']['path'] is None:
            assert p['music']['status'].startswith('SILENT')
        else:
            assert p['music']['status'] == 'BOUND_CC0' and p['music']['license'].startswith('CC0')
            assert p['music']['sha256'] and Path(p['music']['path']).exists()


def test_provenance_declares_roles_and_no_certification(plans):
    for p in plans.values():
        prov = p['provenance']
        assert prov['creative_authority'] == 'NEXMIND_P8' and prov['renderer_role'] == 'EXECUTION_ONLY'
        assert prov['voice_timing'] == 'FIXTURE' and prov['commercial_certification'] is False
        assert prov['authorities'] and prov['treatment_sha256']
        assert all(s['source'] == 'FIXTURE' and s['evidence']['audio_is_placeholder'] for s in p['voice']['segments'])


def test_captions_follow_narration_in_order(treatment, plans):
    p = plans['9x16']
    spoken = ' '.join(c['text'] for c in p['captions'])
    assert spoken == ' '.join(' '.join(b['narration'].split()) for b in treatment['beats'])
    starts = [c['start_ms'] for c in p['captions']]
    assert starts == sorted(starts) and all(c['end_ms'] > c['start_ms'] for c in p['captions'])
    beats = {b['beat_id']: b for b in p['beats']}
    for c in p['captions']:
        b = beats[c['beat_id']]
        assert b['start_ms'] <= c['start_ms'] and c['end_ms'] <= b['start_ms'] + b['duration_ms']


def test_compile_is_deterministic(treatment, result, tmp_path):
    again = compile_film(treatment, tmp_path, base_dir=FIXTURE.parent)
    strip = lambda p: json.dumps(p, sort_keys=True, default=str)  # noqa: E731
    for a in ASPECTS:
        x, y = copy.deepcopy(result['plans'][a]), copy.deepcopy(again['plans'][a])
        for plan in (x, y):
            plan['voice'] = None
            for m in plan['provenance']['media_assets']:
                m['render_path'] = None
            for b in plan['beats']:
                if b['media']:
                    b['media']['path'] = None
        assert strip(x) == strip(y)


# ---------------------------------------------------------------- ElevenLabs route (fixture transport, no key)

def test_elevenlabs_route_converts_recorded_response(tmp_path):
    import base64
    import hashlib
    text = 'Speed is not a feature.'
    al = synthesise_alignment(text, 'route')
    fixture_dir = tmp_path / 'fx'
    fixture_dir.mkdir()
    (fixture_dir / f'{hashlib.sha256(text.encode()).hexdigest()[:16]}.json').write_text(json.dumps({
        'audio_base64': base64.b64encode(b'RIFF' + b'\0' * 64).decode(), 'alignment': al}))
    out = tmp_path / 'voice.mp3'
    req = {'schema': 'NexStudioAudioProviderRequestV1', 'kind': 'TTS', 'payload': {'text': text, 'voiceId': 'v1'}, 'outputPath': str(out)}
    env = {**os.environ, 'ELEVENLABS_TRANSPORT': f'fixture:{fixture_dir}'}
    env.pop('ELEVENLABS_API_KEY', None)
    cp = subprocess.run([sys.executable, str(ROOT / 'voice' / 'elevenlabs_route.py')], input=json.dumps(req), text=True, capture_output=True, env=env)
    assert cp.returncode == 0, cp.stderr
    meta = json.loads(cp.stdout.strip().splitlines()[-1])
    assert Path(meta['audioPath']).exists()
    rec = json.loads(Path(meta['providerEvidence']['alignmentPath']).read_text())
    assert [w.text for w in words_from_alignment(rec['alignment'])] == text.split()
    assert meta['rightsEvidence']['commercialUseAllowed'] is True


def test_elevenlabs_route_refuses_without_key(tmp_path):
    req = {'schema': 'NexStudioAudioProviderRequestV1', 'kind': 'TTS', 'payload': {'text': 'x', 'voiceId': 'v1'}, 'outputPath': str(tmp_path / 'o.mp3')}
    env = {k: v for k, v in os.environ.items() if k not in ('ELEVENLABS_API_KEY', 'ELEVENLABS_TRANSPORT')}
    cp = subprocess.run([sys.executable, str(ROOT / 'voice' / 'elevenlabs_route.py')], input=json.dumps(req), text=True, capture_output=True, env=env)
    assert cp.returncode != 0 and 'ELEVENLABS_API_KEY_MISSING' in (cp.stderr + cp.stdout)


# ---------------------------------------------------------------- schemas

jsonschema = pytest.importorskip('jsonschema')
SCHEMA_DIR = ROOT / 'schema'


def _validate(schema, doc):
    return sorted(jsonschema.Draft7Validator(schema).iter_errors(doc), key=str)


def test_treatment_schema_accepts_fixture_and_rejects_unknown_pattern(treatment):
    from editorial_plan_compiler import schemas
    assert _validate(schemas.treatment_schema(), treatment) == []
    bad = copy.deepcopy(treatment)
    bad['beats'][0]['pattern'] = 'TOPIC_KEYWORD_ROUTE'
    assert _validate(schemas.treatment_schema(), bad)


def test_plan_schema_accepts_every_aspect_and_rejects_scaled_aspect(plans):
    from editorial_plan_compiler import schemas
    ps = schemas.plan_schema()
    for a in ASPECTS:
        assert _validate(ps, plans[a]) == [], a
    scaled = copy.deepcopy(plans['1x1'])
    scaled['beats'][0]['composition']['derived_by_scaling'] = True
    assert _validate(ps, scaled)
    certified = copy.deepcopy(plans['1x1'])
    certified['provenance']['commercial_certification'] = True
    assert _validate(ps, certified)


def test_checked_in_schema_files_match_generator():
    from editorial_plan_compiler import schemas
    for name, fn in schemas.ALL.items():
        on_disk = json.loads((SCHEMA_DIR / name).read_text())
        assert on_disk == fn(), f'{name} is stale: python3 -m editorial_plan_compiler.schemas'


# ---------------------------------------------------------------- v4 stage + ambient

def test_every_beat_draws_a_stage(plans):
    for p in plans.values():
        for b in p['beats']:
            bg = b['composition']['background']
            assert bg['layers'], f"{b['beat_id']} has no stage layers"
            for l in bg['layers']:
                assert l['kind'] in {'panel', 'hairline', 'plane', 'dotgrid', 'spotlight'}, l


def test_no_beat_opens_empty(plans):
    """First visible content (chrome, entity or first word) inside the lead-in window."""
    from editorial_plan_compiler.timing import LEAD_IN_MS
    for p in plans.values():
        for b in p['beats']:
            firsts = [w['start_ms'] for w in b['words']]
            firsts += [e['start_ms'] for e in b['typography']['events'] if e['unit_index'] >= 0]
            if b['illustration']:
                firsts += [e['enter_ms'] for e in b['illustration']['entities']]
            if b['media']:
                firsts.append(b['media']['chrome_ms'] if b['media']['chrome_ms'] is not None else b['media']['enter_ms'])
            if b['data']:
                firsts.append(b['data']['chrome_ms'] if b['data']['chrome_ms'] is not None else b['data']['enter_ms'])
            if b['figure']:
                firsts.append(b['figure']['enter_ms'])
            assert min(firsts) <= LEAD_IN_MS + 640, (b['beat_id'], min(firsts))


def test_registry_merges_aev1_and_community_icons():
    from editorial_plan_compiler.illustration import IllustrationRegistry
    reg = IllustrationRegistry()
    assert any(i.startswith('icon.') for i in reg.items), 'community icons not loaded'
    resolved = reg.resolve('icon.lucide.check', 'test')
    assert Path(resolved['path']).exists() and resolved['license']
    # authored AEV1 assets still resolve
    aev = next(k for k in reg.items if not k.startswith('icon.'))
    assert reg.resolve(aev, 'test')['path']


def test_music_bed_rights_clean_and_deterministic(plans):
    for p in plans.values():
        m = p['music']
        assert m['status'] == 'BOUND_CC0' and m['license'].startswith('CC0'), m
        assert Path(m['path']).exists()
        assert m['duck_under_voice_db'] < 0 and m['gain_db'] < 0
