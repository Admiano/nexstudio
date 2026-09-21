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

from editorial_plan_compiler.atmosphere import (  # noqa: E402
    DEPTH_COUNT, DEPTH_MAX_OVERLAP, DEPTH_PLANE, MIN_INK_CONTRAST, _overlap_frac, content_boxes, contrast, film_atmosphere, hero_box,
)
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
                # Provenance law: an admitted accent must carry a license class, sha256 and a real file.
                assert a['license'] and a['sha256'] and Path(a['path']).exists()
                if a.get('trim_ms'):
                    assert a['trim_ms'] <= 1500
                assert 0 <= a['beat_at_ms'] <= b['duration_ms']
        if p['music']['path'] is None:
            assert p['music']['status'].startswith('SILENT')
        else:
            assert p['music']['status'] == 'BOUND_CC0' and p['music']['license'].startswith('CC0')
            assert p['music']['sha256'] and Path(p['music']['path']).exists()


def test_op_events_offer_sound_candidates(plans):
    """Illustration ops offer semantic sound candidates; EMIT/TRACE/COUNT/DRAW accents may bind."""
    events = {a['event'] for p in plans.values() for b in p['beats'] for a in b['sound']['accents']}
    # Only assert what the spacing/strength caps allow: at least one op-driven event family binds.
    op_events = events & {'EMIT_CONFIRM', 'LINE_DRAW', 'COUNT_TICK', 'LOUPE_TRAVEL'}
    assert op_events, 'no op-driven accent bound in any aspect'


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
                assert l['kind'] in {'panel', 'hairline', 'plane', 'dotgrid', 'spotlight', 'bloom', 'depth'}, l


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


def test_colour_registry_resolves_brand_and_emoji_natively():
    from editorial_plan_compiler.illustration import IllustrationRegistry
    reg = IllustrationRegistry()
    for asset_id in ('brand.logos.claude-icon', 'emoji.fluent.brain', 'icon.icon-park-color.robot'):
        r = reg.resolve(asset_id, 'test')
        assert Path(r['path']).exists() and r['license'] and r.get('colour') == 'native', asset_id


@pytest.fixture(scope='module')
def collage_plans(tmp_path_factory):
    fx = ROOT / 'fixtures' / 'promo-collage' / 'treatment.json'
    return compile_film(json.loads(fx.read_text()), tmp_path_factory.mktemp('collage'), base_dir=fx.parent)


def test_product_collage_emits_motion_profile_and_kinetic_captions(collage_plans, plans):
    assert collage_plans['gate']['status'] == 'PASS', collage_plans['gate']['failures']
    for p in collage_plans['plans'].values():
        assert p['captions_policy'] == 'kinetic'
        m = p['motion']
        assert m['entrance'] == 'pop' and m['transition'] == 'scale_through' and m['camera_push'] > 0
        assert not any(L['kind'] == 'panel' for b in p['beats'] for L in b['composition']['background']['layers'])
        for b in p['beats']:
            il = b.get('illustration')
            if not il:
                continue
            for e in il['entities']:
                if e['glyph'] == 'CHIP' and e['label']:
                    # inside label starts clear of the icon peg and ends before the tag-pill third
                    lb, bb = e['label']['bbox'], e['bbox']
                    assert lb['x'] >= bb['x'] + bb['w'] * 0.32 and lb['x'] + lb['w'] <= bb['x'] + bb['w'] * 0.64
    for p in plans.values():
        assert p['captions_policy'] == 'burned' and p['motion']['entrance'] == 'settle'


def test_wrap_cells_keeps_a_single_line_when_shares_fit():
    from editorial_plan_compiler.illustration import IllustrationRegistry, IllustrationSolver
    from editorial_plan_compiler.contracts import IllustrationEntity
    s = IllustrationSolver('16x9', (1920, 1080), IllustrationRegistry(), {}, {}, None)
    ents = [IllustrationEntity(id=f'e{i}', kind='object', glyph='NODE', size='support') for i in range(3)]
    cells = s._wrap_cells({'x': 0.0, 'y': 0.0, 'w': 1200.0, 'h': 300.0}, ents, False)
    assert len({round(c['y']) for c in cells.values()}) == 1, 'unlabelled row must not wrap'


# ---------------------------------------------------------------- authored, not generated

def test_entity_labels_are_nouns_not_captions(treatment):
    for label, code in (('the reply', 'ENTITY_LABEL_ARTICLE'), ('very long label here', 'ENTITY_LABEL_LONG'),
                        ('lose customers', 'ENTITY_LABEL_ECHO')):
        bad = copy.deepcopy(treatment)
        beat = next(b for b in bad['beats'] if b.get('illustration'))
        beat['illustration']['entities'][0]['label'] = label
        with pytest.raises(TreatmentError) as e:
            FilmTreatment.parse(bad)
        assert e.value.code == code, label


def test_one_colour_pack_per_film(tmp_path):
    fx = ROOT / 'fixtures' / 'promo-collage' / 'treatment.json'
    bad = json.loads(fx.read_text())
    ent = next(e for b in bad['beats'] if b.get('illustration') for e in b['illustration']['entities']
               if (e.get('asset_ref') or '').startswith('emoji.fluent.'))
    ent['asset_ref'] = 'icon.icon-park-color.robot'
    out = compile_film(bad, tmp_path, base_dir=fx.parent)
    assert out['gate']['status'] == 'FAIL'
    assert any(f.startswith('ASSET_PACK_MIX:emoji.fluent!=') and f.endswith('icon.icon-park-color.robot') for f in out['gate']['failures'])


def test_no_free_floating_arcs_and_collage_links_are_uniform(collage_plans, plans):
    for p in list(collage_plans['plans'].values()) + list(plans.values()):
        assert not any(L['kind'] == 'arc' for b in p['beats'] for L in b['composition']['background']['layers'])
    for p in collage_plans['plans'].values():
        for b in p['beats']:
            il = b.get('illustration')
            if not il:
                continue
            for r in il['relations']:
                if r['path']:
                    assert r.get('thin') and r.get('dots') and not r.get('arrow'), r['id']
                    assert r['length'] >= 28.0, r['id']


def test_synthesized_ops_wait_for_the_authored_draw(collage_plans, plans):
    for p in list(collage_plans['plans'].values()) + list(plans.values()):
        for b in p['beats']:
            il = b.get('illustration')
            if not il:
                continue
            draw_end = {o['target']: o['end_ms'] for o in il['ops'] if o['op'] == 'DRAW'}
            for o in il['ops']:
                if o.get('synthesized') and o['op'] != 'DRAW' and o['target'] in draw_end:
                    assert o['start_ms'] >= draw_end[o['target']], (b['beat_id'], o)


# ---------------------------------------------------------------- item 7: anti-generated gates (compiler side)

def _collage_treatment():
    fx = ROOT / 'fixtures' / 'promo-collage' / 'treatment.json'
    return json.loads(fx.read_text()), fx.parent


def _beat_with_relations(t):
    return next(b for b in t['beats'] if b.get('illustration') and b['illustration'].get('relations'))


def test_housing_without_content_is_refused_but_a_worded_chip_is_content():
    t, _ = _collage_treatment()
    beat = _beat_with_relations(t)
    tile = next(e for e in beat['illustration']['entities'] if e['glyph'] == 'TILE')
    bad = copy.deepcopy(t)
    ent = next(e for e in _beat_with_relations(bad)['illustration']['entities'] if e['id'] == tile['id'])
    ent.pop('asset_ref', None)
    ent['label'] = 'memory'
    with pytest.raises(TreatmentError) as e:
        FilmTreatment.parse(bad)
    assert e.value.code == 'CHASSIS_EMPTY' and tile['id'] in e.value.detail
    ok = copy.deepcopy(t)
    ent = next(e for e in _beat_with_relations(ok)['illustration']['entities'] if e['id'] == tile['id'])
    ent.pop('asset_ref', None)
    ent['glyph'] = 'CHIP'
    ent['label'] = 'memory'
    FilmTreatment.parse(ok)


def test_connector_endpoints_land_before_the_stroke_completes(tmp_path):
    from editorial_plan_compiler.illustration import ENTER_MS
    from editorial_plan_compiler.timing import LEAD_IN_MS
    t, base = _collage_treatment()
    beat = _beat_with_relations(t)
    rel = beat['illustration']['relations'][0]
    rid = f"{rel['source']}->{rel['target']}"
    # Anchor the connector early with a short stroke: the solver pulls both bodies' entrances forward
    # so the line never completes on an absent rim, and the plan proves it.
    beat['illustration']['program'] = [o for o in beat['illustration']['program'] if o['target'] != rid]
    beat['illustration']['program'].insert(0, {'op': 'CONNECT', 'target': rid, 'at': {'offset_ms': 300}, 'duration_ms': 200})
    out = compile_film(t, tmp_path / 'ok', base_dir=base)
    assert not any(f.startswith('CONNECTOR_BEFORE_ENDPOINT') for f in out['gate']['failures']), out['gate']['failures']
    for p in out['plans'].values():
        il = next(b for b in p['beats'] if b['beat_id'] == beat['beat_id'])['illustration']
        r = next(r for r in il['relations'] if r['id'] == rid)
        if r.get('stub'):
            continue
        ends = {e['id']: e['enter_ms'] + e['enter_duration_ms'] for e in il['entities']}
        assert r['enter_ms'] + r['enter_duration_ms'] >= max(ends[rel['source']], ends[rel['target']]), (r, ends)
    # A stroke that must finish before any body can have landed has no schedule: the gate names it.
    assert LEAD_IN_MS + 120 < LEAD_IN_MS // 5 + ENTER_MS
    beat['illustration']['program'][0] = {'op': 'CONNECT', 'target': rid, 'at': {'offset_ms': 0}, 'duration_ms': 120}
    out = compile_film(t, tmp_path / 'bad', base_dir=base)
    assert out['gate']['status'] == 'FAIL'
    assert any(f.endswith(f':CONNECTOR_BEFORE_ENDPOINT:{rid}') for f in out['gate']['failures']), out['gate']['failures']


def test_stub_links_carry_no_program(collage_plans):
    # Bodies laid out rim-to-rim get no connector stroke, so nothing is programmed onto that link and
    # the beat says so in a warning rather than leaving an op with no target on stage.
    seen = 0
    for aspect, p in collage_plans['plans'].items():
        for b in p['beats']:
            il = b.get('illustration')
            if not il:
                continue
            stubs = {r['id'] for r in il['relations'] if r.get('stub')}
            seen += len(stubs)
            assert not any(o['target'] in stubs for o in il['ops']), (aspect, b['beat_id'])
            for rid in stubs:
                assert f'CONNECTOR_STUB_ADJACENT:{rid}' in b['gate']['warnings'], (aspect, b['beat_id'])
    assert seen >= 1, 'fixture no longer exercises the stub path'


# ---------------------------------------------------------------- item 3: device chassis for customer media

from editorial_plan_compiler.chassis import (  # noqa: E402
    CHASSIS, PHONE_AR, PORTRAIT_AR, TILT_MAX_DEG, TILT_MIN_DEG, chassis_aspect, housing, resolve_chassis, resolve_tilt,
)
from editorial_plan_compiler.contracts import MOTION_PROFILES  # noqa: E402


def test_chassis_is_inferred_from_aspect_and_kind_and_authored_choice_wins():
    assert resolve_chassis('SCREENSHOT', 720, 2200) == 'phone'
    assert resolve_chassis('VIDEO', 720, 1280) == 'phone'
    assert resolve_chassis('SCREENSHOT', 1600, 1000) == 'shot'
    assert resolve_chassis('VIDEO', 1280, 720) == 'shot'
    assert resolve_chassis('IMAGE', 1200, 1200) == 'shot'
    assert resolve_chassis('DOCUMENT', 1000, 1300) == 'card'
    assert resolve_chassis('DOCUMENT', 1300, 1000) == 'card'
    # Just under / over the portrait threshold.
    assert resolve_chassis('IMAGE', int(PORTRAIT_AR * 1000) - 5, 1000) == 'phone'
    assert resolve_chassis('IMAGE', int(PORTRAIT_AR * 1000) + 5, 1000) == 'shot'
    for c in CHASSIS:
        assert resolve_chassis('VIDEO', 1280, 720, c) == c
    with pytest.raises(ValueError):
        resolve_chassis('VIDEO', 1280, 720, 'tablet')
    # A handset is a fixed object: the slab keeps the device ratio whatever the upload's.
    assert chassis_aspect('phone', 720 / 2200) == PHONE_AR
    assert chassis_aspect('shot', 1.6) == 1.6
    assert chassis_aspect('browser', 1.0) == 1.0


def test_tilt_is_profile_driven_deterministic_and_alternates_sign():
    collage = MOTION_PROFILES['PRODUCT_COLLAGE']
    flat = MOTION_PROFILES['EDITORIAL_FLAT']
    a = resolve_tilt('upload-a', collage)
    assert a == resolve_tilt('upload-a', collage)
    assert TILT_MIN_DEG <= abs(a) <= TILT_MAX_DEG
    signs = {resolve_tilt(f'asset-{i}', collage) > 0 for i in range(24)}
    assert signs == {True, False}
    assert resolve_tilt('upload-a', flat) == 0.0
    assert resolve_tilt('upload-a', collage, size='support') == 0.0
    assert resolve_tilt('upload-a', collage, authored=-4.5) == -4.5
    assert resolve_tilt('upload-a', collage, authored=40) == 14.0
    for prof in MOTION_PROFILES.values():
        assert 'media_tilt' in prof
    h = housing('VIDEO', 720, 1280, 'clip', collage)
    assert h == {'chassis': 'phone', 'tilt': resolve_tilt('clip', collage)}


@pytest.fixture(scope='module')
def matrix_plans(tmp_path_factory):
    fx = ROOT / 'fixtures' / 'media-matrix' / 'treatment.json'
    return compile_film(json.loads(fx.read_text()), tmp_path_factory.mktemp('matrix'), base_dir=fx.parent)


def _media_entities(plan):
    for b in plan['beats']:
        il = b.get('illustration')
        if il:
            for e in il['entities']:
                if e.get('media'):
                    yield b, e
        if b.get('media'):
            yield b, None


def test_media_matrix_houses_every_upload_in_every_aspect(matrix_plans):
    assert matrix_plans['gate']['status'] == 'PASS', matrix_plans['gate']['failures']
    for aspect, p in matrix_plans['plans'].items():
        seen = {}
        for b, e in _media_entities(p):
            md = e['media'] if e else b['media']
            bbox = e['bbox'] if e else b['media']['bbox']
            assert md['chassis'] in CHASSIS
            assert isinstance(md['tilt'], (int, float))
            seen[md['asset_id']] = (md['chassis'], md['tilt'], md['kind'])
            # The slab's box keeps the housing ratio, not the raw upload's.
            src = md['source_size']
            want = chassis_aspect(md['chassis'], src['w'] / src['h'])
            assert abs(bbox['w'] / bbox['h'] - want) < 0.03, (aspect, md['asset_id'], bbox)
            # Housed media never leaves the frame.
            assert bbox['x'] >= 0 and bbox['y'] >= 0
            assert bbox['x'] + bbox['w'] <= p['canvas']['w'] + 1 and bbox['y'] + bbox['h'] <= p['canvas']['h'] + 1
        assert seen['tall_shot'][0] == 'phone'
        assert seen['portrait_clip'] == ('phone', seen['portrait_clip'][1], 'VIDEO')
        assert seen['wide_ui'][0] == 'shot'
        assert seen['square_photo'][0] == 'shot'
        assert seen['square_clip'][0] == 'browser'   # authored override
        assert seen['wide_clip'][0] == 'shot'        # beat-level media is housed too
        # Heroes float (profile tilt); every hero slab has a non-zero, bounded tilt.
        for aid in ('tall_shot', 'wide_ui', 'square_photo', 'portrait_clip'):
            assert 0 < abs(seen[aid][1]) <= TILT_MAX_DEG, (aspect, aid, seen[aid])
    # Housing is a pure function of the asset, so every aspect lands the same slab the same way.
    per_aspect = [{md['asset_id']: (md['chassis'], md['tilt']) for _, e in _media_entities(p) for md in [e['media'] if e else _['media']]}
                  for p in matrix_plans['plans'].values()]
    assert all(pa == per_aspect[0] for pa in per_aspect)


def test_live_video_inside_a_housing_keeps_its_trim(matrix_plans):
    p = matrix_plans['plans']['16x9']
    trims = {e['media']['asset_id']: e['media']['trim'] for _, e in _media_entities(p) if e and e['media']['kind'] == 'VIDEO'}
    assert trims['portrait_clip'] == {'start': 0.3, 'end': 3.9}
    assert trims['square_clip'] == {'start': 0.2, 'end': 3.8}


def test_flanking_chips_shed_tags_before_a_tall_hero_gives_up_its_column(matrix_plans):
    # The treatment's own entities are shared across aspects: shedding tags in one field must not leak.
    fx = json.loads((ROOT / 'fixtures' / 'media-matrix' / 'treatment.json').read_text())
    authored = {e['id']: e.get('params', {}).get('tags') for b in fx['beats'] if b.get('illustration') for e in b['illustration']['entities']}
    assert authored['c1'] and authored['ch']
    kept = {}
    for aspect, p in matrix_plans['plans'].items():
        for b in p['beats']:
            if b['beat_id'] != 'b01':
                continue
            ents = {e['id']: e for e in b['illustration']['entities']}
            kept[aspect] = bool(ents['c1']['params'].get('tags'))
            assert ents['c1']['label']['fit']['status'] == 'FIT'
    assert kept['16x9'] and kept['9x16'], kept
    assert not kept['1x1'], kept


# ---------------------------------------------------------------- item 4: semantic concept ladder, asset preflight

from editorial_plan_compiler.illustration import IllustrationRegistry, TreatmentError as _IllTreatmentError  # noqa: E402
from editorial_plan_compiler.lexicon import ABSTRACT, AssetFinder, NounLexicon  # noqa: E402

LADDER = ROOT / 'fixtures' / 'concept-ladder' / 'treatment.json'
PACK = 'icon.icon-park-color'


@pytest.fixture(scope='module')
def finder():
    reg = IllustrationRegistry()
    return AssetFinder(reg.items, NounLexicon(), reg.quarantined), reg


@pytest.fixture(scope='module')
def ladder_plans(tmp_path_factory):
    return compile_film(json.loads(LADDER.read_text()), tmp_path_factory.mktemp('ladder'), base_dir=LADDER.parent)


def _ladder_entities(p):
    for b in p['beats']:
        for e in (b['illustration']['entities'] if b.get('illustration') else []):
            if e.get('params', {}).get('resolution'):
                yield b, e


def test_lexicon_is_vendored_with_provenance_and_walks_meaning_not_spelling():
    info = json.loads((ROOT / 'assets' / 'community' / 'lexicon' / 'info.json').read_text())
    assert info['license'] == 'WordNet 3.0 License' and info['synsets'] > 80000 and len(info['sha256']) == 64
    lx = NounLexicon()
    assert lx.lemma('almonds') == 'almond'
    assert 'nut' in {l for lv in lx.hypernym_levels('almond') for l in lv}
    assert 'bike' in lx.synonyms('bicycle')
    # Abstract ancestors end a walk instead of answering for it.
    assert not any(l in ABSTRACT for lv in lx.hypernym_levels('almond') for l in lv)
    # Only the senses the corpus actually uses are walked: 'sugar' never becomes money, then bread.
    assert 'bread' not in {l for lv in lx.hypernym_levels('sugar') for l in lv}
    assert 'word' not in {l for lv in lx.hypernym_levels('loan') for l in lv}
    # A stand-in word must mean the concept when read on its own: 'bike' does, 'word' (password) does not.
    assert 'word' not in lx.synonyms('password') and 'bill' in lx.synonyms('invoice')
    # Untagged lemmas walk their thing-naming sense first: a wrench is a tool before it is an injury.
    assert 'spanner' in lx.synonyms('wrench') and 'harm' not in {l for lv in lx.hypernym_levels('wrench') for l in lv}


def test_ladder_walks_exact_synonym_hypernym_composite_typographic_numeric_in_order(finder):
    f, _ = finder
    by = {c: f.resolve(c, PACK, True, True) for c in ('camera', 'invoice', 'savings', 'almond', 'kubernetes cluster', '12%', '$4.2M')}
    assert by['camera'].via == 'exact' and by['camera'].asset_ref == f'{PACK}.camera'
    assert by['invoice'].via == 'synonym' and by['invoice'].path == ['invoice', 'bill']
    # An ancestor's mark stands alone only where the housing already names the concept (a labelled
    # CHIP); a TILE draws it beside the word so the viewer can read back to the concept.
    assert by['savings'].via == 'composite' and by['savings'].asset_ref == f'{PACK}.funds' and by['savings'].word == 'savings'
    named = f.resolve('savings', PACK, True, True, named=True)
    assert named.via == 'hypernym' and named.asset_ref == f'{PACK}.funds' and named.word is None and named.path == ['savings', 'fund']
    # A stand-in must read as the concept on its own: 'agreement' (sense 6) is no subscription, so
    # the word is set rather than a handshake drawn.
    assert f.resolve('subscription', PACK, True, True).via == 'typographic'
    # Composite keeps the concept: the ancestor's mark plus the concept's own name.
    assert by['almond'].via == 'composite' and by['almond'].asset_ref == f'{PACK}.nut' and by['almond'].word == 'almond'
    assert by['kubernetes cluster'].via == 'typographic' and by['kubernetes cluster'].asset_ref is None and by['kubernetes cluster'].word == 'kubernetes cluster'
    assert by['12%'].via == 'numeric' and by['12%'].word == '12%'
    assert by['$4.2M'].via == 'numeric'
    # Every answer carries its semantic path back to the concept.
    for r in by.values():
        assert r.concept in (r.path[:1] or [r.concept])
    d = by['almond'].as_dict()
    assert d == {'concept': 'almond', 'via': 'composite', 'asset_ref': f'{PACK}.nut', 'word': 'almond', 'path': ['almond', 'nut']}


def test_ladder_never_substitutes_an_unrelated_mark(finder):
    f, reg = finder
    # A common noun never takes a brand logo, however exact the spelling.
    apple = f.resolve('apple', PACK, True, True)
    assert reg.items[apple.asset_ref]['family'] != 'brand'
    # A proper name does.
    assert f.resolve('Apple', None, True, False).via == 'exact' and f.resolve('Apple', None, True, False).asset_ref.startswith('brand.')
    # Nothing in the ladder answers with an asset the concept has no lexical path to.
    for c in ('sugar', 'churn', 'latency', 'pantry'):
        r = f.resolve(c, PACK, True, True)
        assert r.via in ('typographic',) and r.asset_ref is None, (c, r)
    # A housing that cannot typeset and has nothing to draw is unresolved, never a stand-in.
    r = f.resolve('churn', PACK, False, True)
    assert r.via == 'unresolved' and r.asset_ref is None and r.word is None


def test_ladder_stays_inside_the_film_colour_pack(finder):
    f, reg = finder
    for c in ('camera', 'invoice', 'almond', 'truck'):
        r = f.resolve(c, PACK, True, True)
        if r.asset_ref:
            assert r.asset_ref.startswith(PACK + '.'), (c, r)
            assert reg.items[r.asset_ref]['colour'] == 'native'
    other = f.resolve('pizza', 'emoji.fluent', True, True)
    assert other.via == 'exact' and other.asset_ref == 'emoji.fluent.pizza'


def test_concept_ladder_fixture_resolves_every_rung_identically_in_every_aspect(ladder_plans):
    assert ladder_plans['gate']['status'] == 'PASS', ladder_plans['gate']['failures']
    per_aspect = []
    for aspect, p in ladder_plans['plans'].items():
        rungs = {}
        for b, e in _ladder_entities(p):
            r = e['params']['resolution']
            rungs[e['id']] = (r['via'], r['asset_ref'], e['params'].get('word'), e['params'].get('word_kind'))
            # The entity carries exactly what its resolution says.
            assert (e.get('asset') or {}).get('id') == r['asset_ref']
            if r['via'] in ('composite', 'typographic', 'numeric'):
                assert e['params']['word'] == r['word']
            else:
                assert 'word' not in e['params']
            if r['via'] == 'numeric':
                assert e['params']['word_kind'] == 'numeric'
        assert {v[0] for v in rungs.values()} >= {'exact', 'synonym', 'hypernym', 'composite', 'typographic', 'numeric'}, rungs
        per_aspect.append(rungs)
    assert all(r == per_aspect[0] for r in per_aspect)


def test_concept_contract_needs_a_housing_and_refuses_an_unresolvable_icon(tmp_path):
    t = json.loads(LADDER.read_text())
    bad = copy.deepcopy(t)
    ent = bad['beats'][0]['illustration']['entities'][0]
    ent['glyph'] = 'CARD'
    with pytest.raises(TreatmentError) as e:
        FilmTreatment.parse(bad)
    assert e.value.code == 'CONCEPT_ON_UNHOUSED_GLYPH'
    # ICON cannot typeset: a concept with no drawable meaning fails the compile, it is not guessed.
    icon = copy.deepcopy(t)
    ent = icon['beats'][0]['illustration']['entities'][1]
    ent['glyph'] = 'ICON'
    ent['concept'] = 'churn'
    ent.pop('asset_ref', None)
    with pytest.raises(TreatmentError) as e:
        compile_film(icon, tmp_path / 'icon', base_dir=LADDER.parent)
    assert e.value.code == 'CONCEPT_UNRESOLVED' and 'churn' in e.value.detail


def test_preflight_quarantine_is_recorded_and_refused(tmp_path):
    pf = json.loads((ROOT / 'assets' / 'community' / 'preflight.json').read_text())
    assert pf['checked'] > 18000 and pf['quarantined_count'] == len(pf['quarantined']) > 0
    assert set(pf['reasons']) <= {'UNDERPAINT', 'OVERFLOW', 'PARSE', 'RENDER_FAIL', 'VIEWBOX', 'SCRIPT', 'FOREIGN_OBJECT', 'EXTERNAL_REF', 'EXTERNAL_IMAGE'}
    reg = IllustrationRegistry()
    ref = sorted(pf['quarantined'])[0]
    assert ref in reg.items and ref in reg.quarantined
    with pytest.raises(_IllTreatmentError) as e:
        reg.resolve(ref, "b01")
    assert e.value.code == 'ASSET_QUARANTINED'
    # The ladder never offers a quarantined mark either.
    f = AssetFinder(reg.items, NounLexicon(), reg.quarantined)
    for ref in pf['quarantined']:
        label = ' '.join(reg.items[ref]['id'].split('.')[-1].split('-'))
        r = f.resolve(label, None, True, False)
        assert r.asset_ref != ref, (label, r)


# ---------------------------------------------------------------- item 5: music library, groove, layered sfx, bus mix

from editorial_plan_compiler.groove import ON_GRID_MS, fit_phase, groove_stagger  # noqa: E402
from editorial_plan_compiler.sound import (  # noqa: E402
    GLYPH_TEXTURE, LAYER_OFFSET_MS, MIX, TEXTURES, bind_film_music,
)


def test_music_library_is_broad_measured_and_rights_clean():
    from editorial_plan_compiler.sound import COMMUNITY_MANIFEST
    beds = [a for a in json.loads(COMMUNITY_MANIFEST.read_text())['assets'] if a['kind'] == 'music']
    assert len(beds) >= 100
    for b in beds:
        assert b['license'].startswith('CC0') and b['source']['url'] and b['sha256']
        assert Path(COMMUNITY_MANIFEST.parent / b['path']).exists()
        assert 60 <= b['bpm'] <= 170 and 0 <= b['grid_offset_ms'] < 60000 / b['bpm']
        assert 0.0 <= b['energy'] <= 1.0 and b['lufs'] < 0 and b['duration_s'] > 30
        assert b['moods']
    from editorial_plan_compiler.contracts import FILM_MOODS
    assert {m for b in beds for m in b['moods']} <= set(FILM_MOODS)
    # every authored mood has a real pool to pick from, not a single bed
    for mood in FILM_MOODS:
        assert sum(1 for b in beds if mood in b['moods']) >= 5, mood


def test_music_pick_is_contextual_and_deterministic():
    a = bind_film_music('film-a', 'calm', 30000, 0.3)
    b = bind_film_music('film-a', 'calm', 30000, 0.3)
    assert a == b
    assert a['status'] == 'BOUND_CC0' and 'calm' in a['moods'] and a['duration_s'] * 1000 >= 30000
    # energy narrows the pool to a shortlist of the nearest beds
    assert len(a['shortlist']) <= 3 and a['pool'] > 50
    hot = bind_film_music('film-a', 'calm', 30000, 0.9)
    assert hot['energy'] >= a['energy']
    # a different mood request lands in a different pool
    assert 'driving' in bind_film_music('film-a', 'driving', 30000, 0.6)['moods']
    # the bed trim normalises the mastering level of the source
    assert -30 <= a['gain_db'] <= -10 and abs((a['gain_db'] + a['lufs']) - (-35.0)) < 0.11


def test_groove_snaps_stagger_and_fits_phase():
    # 90 bpm → eighth = 333ms, sextuplet = 111ms: 100ms authored stagger snaps to the sextuplet
    assert groove_stagger(100, 90) == (111, 'sextuplet')
    # too far from any subdivision: authored value kept
    assert groove_stagger(80, 89) == (80, None)
    assert groove_stagger(90, None) == (90, None)
    beats = [{'start_ms': 0, 'duration_ms': 4000, 'illustration': {'entities': [
        {'enter_ms': 400 + i * 500, 'enter_duration_ms': 100} for i in range(6)], 'relations': []},
        'media': None, 'data': None, 'transition': None}]
    fit = fit_phase({'bpm': 120, 'grid_offset_ms': 0, 'path': 'x.mp3'}, beats)
    assert fit['status'] == 'PHASED' and fit['landings'] == 6
    # 120bpm eighths are 250ms: every 500ms landing sits on the grid once the phase is right
    assert fit['on_grid'] == 6 and fit['mean_drift_ms'] <= ON_GRID_MS
    assert fit_phase({'bpm': None, 'path': 'x.mp3'}, beats)['status'] == 'NO_GRID'


def test_collage_plan_carries_groove_layers_and_buses(collage_plans):
    for aspect, p in collage_plans['plans'].items():
        m = p['music']
        assert m['groove']['status'] == 'PHASED' and m['start_offset_ms'] == m['groove']['start_offset_ms']
        assert m['groove']['bpm'] == m['bpm'] and m['energy_request'] is not None
        assert p['mix'] == MIX and p['motion']['stagger_ms'] == m['groove']['stagger_ms']
        for b in p['beats']:
            for a in b['sound']['accents']:
                roles = [L['role'] for L in a['layers']]
                assert 'body' in roles and len(roles) == len(set(roles))
                for L in a['layers']:
                    assert L['license'] and L['sha256'] and Path(L['path']).exists()
                    assert L['offset_ms'] == LAYER_OFFSET_MS[L['role']]
                    assert a['film_at_ms'] + L['offset_ms'] >= 0
                if a['texture']:
                    assert a['texture'] in TEXTURES
                    if TEXTURES[a['texture']]['transient']:
                        assert 'transient' in roles, a
    # the collage lands tiles with the glass texture (click over pop), not a bare pop
    textures = {a['texture'] for p in collage_plans['plans'].values() for b in p['beats'] for a in b['sound']['accents']}
    assert 'glass' in textures
    assert set(GLYPH_TEXTURE.values()) <= set(TEXTURES)


# ---------------------------------------------------------------- atmosphere (designed background)

def test_atmosphere_is_derived_from_the_palette_and_flips_polarity():
    light = film_atmosphere({'ink': '#191512', 'paper': '#f2f1ee', 'accent': '#e8a317'})
    dark = film_atmosphere({'ink': '#f1ede6', 'paper': '#15130f', 'accent': '#f0a35a'})
    assert light['theme'] == 'light' and dark['theme'] == 'dark'
    assert light['field'] == '#f2f1ee' and dark['field'] == '#15130f'
    # the dark variant leans harder on vignette and grain (a dark field hides both)
    assert dark['vignette_opacity'] > light['vignette_opacity'] and dark['grain_opacity'] > light['grain_opacity']
    # bloom is the accent pulled toward the paper, never a raw brand colour
    assert light['bloom'] not in ('#e8a317', '#f2f1ee') and dark['bloom'] not in ('#f0a35a', '#15130f')
    # housing surfaces follow the field: light housing is lighter than the field on both polarities,
    # dark housing is the contrasting surface
    for a in (light, dark):
        assert contrast(a['housing']['light'], a['field']) < contrast(a['housing']['dark'], a['field'])
    # no accent: a warm neutral bloom is derived rather than reusing ink
    plain = film_atmosphere({'ink': '#0e0e0e', 'paper': '#f7f7f5', 'accent': None})
    assert plain['bloom'] not in ('#0e0e0e', '#f7f7f5')
    assert film_atmosphere({'ink': '#191512', 'paper': '#f2f1ee', 'accent': '#e8a317'}) == light  # deterministic


def test_low_contrast_brand_fails_the_film_gate():
    fx = ROOT / 'fixtures' / 'promo-collage' / 'treatment.json'
    t = json.loads(fx.read_text())
    t['brand'] = {**t['brand'], 'ink': '#8a8683', 'paper': '#f2f1ee'}
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        r = compile_film(t, Path(d), base_dir=fx.parent)
    assert any(f.startswith('BRAND_CONTRAST:') for f in r['gate']['failures'])
    assert contrast('#8a8683', '#f2f1ee') < MIN_INK_CONTRAST


def test_collage_beats_carry_a_hero_bloom_and_far_plane_depth(collage_plans):
    for aspect, p in collage_plans['plans'].items():
        W, H = p['canvas']['w'], p['canvas']['h']
        assert p['atmosphere']['theme'] == 'light'
        prev = None
        for b in p['beats']:
            layers = b['composition']['background']['layers']
            kinds = [L['kind'] for L in layers]
            assert 'glow' not in kinds and kinds.count('bloom') == 1
            bloom = next(L for L in layers if L['kind'] == 'bloom')
            hero = hero_box(b, b['composition']['safe_area'])
            # the light sits on the beat's hero, and starts where the previous beat left it
            assert abs(bloom['at']['x'] - (hero['x'] + hero['w'] / 2)) < 1
            assert bloom['from'] == (prev if prev else bloom['at'])
            prev = bloom['at']
            depth = [L for L in layers if L['kind'] == 'depth']
            assert len(depth) <= DEPTH_COUNT[1]
            content = content_boxes(b)
            for d in depth:
                assert DEPTH_PLANE[0] <= d['plane'] <= DEPTH_PLANE[1] and d['blur_px'] > 0
                assert d['shape'] in ('disc', 'tile') and d['tint'] in (0, 1)
                assert 0 < d['opacity'] < 0.3
                # far-plane shapes never sit under the content
                assert all(_overlap_frac(d['bbox'], c) <= DEPTH_MAX_OVERLAP for c in content), (aspect, b['beat_id'])


def test_dark_variant_compiles_with_the_same_grammar():
    fx = ROOT / 'fixtures' / 'promo-collage-dark' / 'treatment.json'
    light_fx = ROOT / 'fixtures' / 'promo-collage' / 'treatment.json'
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        r = compile_film(json.loads(fx.read_text()), Path(d), base_dir=fx.parent)
    assert r['gate']['status'] == 'PASS'
    with tempfile.TemporaryDirectory() as d:
        light = compile_film(json.loads(light_fx.read_text()), Path(d), base_dir=light_fx.parent)
    for aspect, p in r['plans'].items():
        assert p['atmosphere']['theme'] == 'dark' and p['atmosphere']['shadow_rgb'] == [0, 0, 0]
        lp = light['plans'][aspect]
        # identical geometry, identical glyph vocabulary — only the atmosphere and surfaces change
        for b, lb in zip(p['beats'], lp['beats']):
            if b['illustration']:
                assert [e['glyph'] for e in b['illustration']['entities']] == [e['glyph'] for e in lb['illustration']['entities']]
                assert [e['bbox'] for e in b['illustration']['entities']] == [e['bbox'] for e in lb['illustration']['entities']]
            kinds = lambda bt: {L['kind'] for L in bt['composition']['background']['layers']}  # noqa: E731
            assert kinds(b) == kinds(lb)
