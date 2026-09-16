#!/usr/bin/env python3
"""Build the water-to-thirsty benchmark fixture from the reference voice-over.

Inputs: the reference VO wav and its word alignment (faster-whisper output).
Outputs under fixtures/water-to-thirsty/: per-beat audio slices, per-beat
character alignments in the ElevenLabs `with-timestamps` shape, and the
treatment JSON (a hand-authored stand-in for a NexMind P8 treatment decision).

    python3 tools/build_water_fixture.py <vo.wav> <words.json>
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'fixtures' / 'water-to-thirsty'

# Word index ranges (inclusive) of the reference alignment per narrated beat.
# The recording is cut mid-sentence after word 84, so the film ends on b09 and
# b10 is an unvoiced payoff.
BEAT_WORDS = {
    'b01': (0, 12),
    'b02': (13, 18),
    'b03': (19, 33),
    'b04': (34, 43),
    'b05': (44, 48),
    'b06': (49, 56),
    'b07': (57, 69),
    'b08': (70, 74),
    'b09': (75, 80),
}


def slice_audio(src: Path, start_ms: int, end_ms: int, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(src), '-ss', f'{start_ms / 1000:.3f}', '-to', f'{end_ms / 1000:.3f}',
                    '-ac', '1', '-ar', '24000', '-sample_fmt', 's16', str(out)], check=True)


def alignment(words, offset_ms: int):
    chars, starts, ends = [], [], []
    for i, w in enumerate(words):
        tok = w['word']
        s, e = w['start_ms'] - offset_ms, max(w['end_ms'], w['start_ms'] + 60) - offset_ms
        n = len(tok)
        for k, ch in enumerate(tok):
            chars.append(ch)
            starts.append(round((s + (e - s) * k / n) / 1000, 3))
            ends.append(round((s + (e - s) * (k + 1) / n) / 1000, 3))
        if i < len(words) - 1:
            nxt = words[i + 1]['start_ms'] - offset_ms
            chars.append(' ')
            starts.append(round(e / 1000, 3))
            ends.append(round(max(e, nxt) / 1000, 3))
    return {'alignment': {'characters': chars, 'character_start_times_seconds': starts, 'character_end_times_seconds': ends}}


def treatment(narrations):
    def unit(text, role, anchor, stress=(), **kw):
        u = {'text': text, 'role': role, 'anchor_word': anchor, 'emphasis': kw.pop('emphasis', 0.8 if role == 'hero' else 0.45),
             'semantic_role': kw.pop('semantic_role', 'statement' if role == 'hero' else 'qualifier')}
        if stress:
            u['stress'] = list(stress)
        u.update(kw)
        return u

    beats = [
        {
            'beat_id': 'b01', 'beat_type': 'HOOK', 'pattern': 'PROGRESSIVE_HERO_BUILD', 'dominant_layer': 'HYBRID',
            'narration': narrations['b01'], 'energy': 0.62, 'complexity': 0.4,
            'display_units': [unit('Sell water', 'hero', 'sell', ['water'], emphasis=0.95),
                              unit('to the thirsty.', 'hero', 'thirsty', ['thirsty'], emphasis=0.9)],
            'illustration': {
                'form': 'OBJECT_STAGE', 'persist_to': 'b02',
                'entities': [{'id': 'vessel', 'kind': 'object', 'glyph': 'VESSEL', 'size': 'hero'},
                             {'id': 'thirst', 'kind': 'signal', 'glyph': 'RING', 'size': 'support', 'params': {'rings': 3}}],
                'relations': [{'type': 'emits_to', 'source': 'thirst', 'target': 'vessel'}],
                'program': [{'op': 'DRAW', 'target': 'vessel', 'at': {'word': 'sell'}, 'duration_ms': 640},
                            {'op': 'FILL', 'target': 'vessel', 'at': {'word': 'water'}, 'duration_ms': 900, 'from': 0.0, 'to': 0.82},
                            {'op': 'EMIT', 'target': 'thirst', 'at': {'word': 'thirsty'}, 'duration_ms': 1100}],
            },
        },
        {
            'beat_id': 'b02', 'beat_type': 'SETUP', 'pattern': 'QUIET_SUPPORT_AFTER_HERO', 'dominant_layer': 'HYBRID',
            'narration': narrations['b02'], 'energy': 0.35, 'complexity': 0.25,
            'display_units': [unit('What this really means', 'support', 'What', emphasis=0.4),
                              unit('is simple.', 'hero', 'simple', ['simple'], emphasis=0.85)],
            'illustration': {
                'form': 'OBJECT_STAGE', 'carry': {'from_beat': 'b01', 'entities': ['vessel']},
                'entities': [{'id': 'vessel', 'kind': 'object', 'glyph': 'VESSEL', 'size': 'support'}],
                'program': [{'op': 'SETTLE', 'target': 'vessel', 'at': {'word': 'means'}, 'duration_ms': 520},
                            {'op': 'DIM', 'target': 'vessel', 'at': {'word': 'simple'}, 'duration_ms': 480, 'from': 1.0, 'to': 0.55}],
            },
        },
        {
            'beat_id': 'b03', 'beat_type': 'CONTRAST', 'pattern': 'HERO_TO_EVIDENCE_HANDOFF', 'dominant_layer': 'ILLUSTRATION',
            'narration': narrations['b03'], 'energy': 0.58, 'complexity': 0.55,
            'display_units': [unit("Don't convince people", 'hero', 'convince', ['convince'], emphasis=0.9),
                              unit("to want what they don't already want.", 'support', 'want', emphasis=0.5)],
            'illustration': {
                'form': 'RELATIONSHIP',
                'entities': [{'id': 'pitch', 'kind': 'agent', 'glyph': 'ICON', 'size': 'support', 'label': 'your pitch', 'asset_ref': 'icon.communication.send'},
                             {'id': 'people', 'kind': 'group', 'glyph': 'NODE', 'size': 'hero', 'label': 'people', 'params': {'count': 3}}],
                'relations': [{'type': 'points_at', 'source': 'pitch', 'target': 'people'}],
                'program': [{'op': 'CONNECT', 'target': 'pitch->people', 'at': {'word': 'convince'}, 'duration_ms': 700},
                            {'op': 'STRIKE', 'target': 'pitch->people', 'at': {'word': 'not'}, 'duration_ms': 420},
                            {'op': 'DIM', 'target': 'pitch', 'at': {'word': 'already'}, 'duration_ms': 480, 'from': 1.0, 'to': 0.45}],
            },
        },
        {
            'beat_id': 'b04', 'beat_type': 'EXPLANATION', 'pattern': 'PROCESS_RAIL', 'dominant_layer': 'HYBRID',
            'narration': narrations['b04'], 'energy': 0.6, 'complexity': 0.6,
            'display_units': [unit('Understand what people are', 'support', 'understand', emphasis=0.45),
                              unit('already searching for.', 'hero', 'searching', ['searching'], emphasis=0.9)],
            'illustration': {
                'form': 'CALLOUT_LENS', 'persist_to': 'b06',
                'entities': [{'id': 'q1', 'kind': 'state', 'glyph': 'PILL', 'size': 'support', 'label': 'searching for'},
                             {'id': 'q2', 'kind': 'state', 'glyph': 'PILL', 'size': 'support', 'label': 'struggling with'},
                             {'id': 'q3', 'kind': 'state', 'glyph': 'PILL', 'size': 'support', 'label': 'looking for answers'},
                             {'id': 'lens', 'kind': 'signal', 'glyph': 'LENS', 'size': 'hero'}],
                'relations': [{'type': 'scans', 'source': 'lens', 'target': 'q1'}],
                'program': [{'op': 'DRAW', 'target': 'lens', 'at': {'word': 'understand'}, 'duration_ms': 560},
                            {'op': 'TRAVEL', 'target': 'lens', 'at': {'word': 'searching'}, 'duration_ms': 520, 'params': {'over': ['q1']}},
                            {'op': 'INK', 'target': 'q1', 'at': {'word': 'searching'}, 'duration_ms': 420}],
            },
        },
        {
            'beat_id': 'b05', 'beat_type': 'EXPLANATION', 'pattern': 'PROCESS_RAIL', 'dominant_layer': 'HYBRID',
            'narration': narrations['b05'], 'energy': 0.62, 'complexity': 0.6,
            'display_units': [unit('What they are', 'support', 'what', emphasis=0.4),
                              unit('struggling with.', 'hero', 'struggling', ['struggling'], emphasis=0.9)],
            'illustration': {
                'form': 'CALLOUT_LENS', 'carry': {'from_beat': 'b04', 'entities': ['q1', 'q2', 'q3', 'lens']}, 'persist_to': 'b06',
                'entities': [{'id': 'q1', 'kind': 'state', 'glyph': 'PILL', 'size': 'support', 'label': 'searching for'},
                             {'id': 'q2', 'kind': 'state', 'glyph': 'PILL', 'size': 'support', 'label': 'struggling with'},
                             {'id': 'q3', 'kind': 'state', 'glyph': 'PILL', 'size': 'support', 'label': 'looking for answers'},
                             {'id': 'lens', 'kind': 'signal', 'glyph': 'LENS', 'size': 'hero'}],
                'relations': [{'type': 'scans', 'source': 'lens', 'target': 'q1'}],
                'program': [{'op': 'TRAVEL', 'target': 'lens', 'at': {'word': 'struggling'}, 'duration_ms': 560, 'params': {'over': ['q1', 'q2']}},
                            {'op': 'DIM', 'target': 'q1', 'at': {'word': 'struggling'}, 'duration_ms': 400, 'from': 1.0, 'to': 0.5},
                            {'op': 'INK', 'target': 'q2', 'at': {'word': 'struggling'}, 'duration_ms': 420}],
            },
        },
        {
            'beat_id': 'b06', 'beat_type': 'EXPLANATION', 'pattern': 'PROCESS_RAIL', 'dominant_layer': 'HYBRID',
            'narration': narrations['b06'], 'energy': 0.66, 'complexity': 0.6,
            'display_units': [unit('Where they are actively', 'support', 'where', emphasis=0.4),
                              unit('looking for answers.', 'hero', 'looking', ['answers'], emphasis=0.92)],
            'illustration': {
                'form': 'CALLOUT_LENS', 'carry': {'from_beat': 'b05', 'entities': ['q1', 'q2', 'q3', 'lens']},
                'entities': [{'id': 'q1', 'kind': 'state', 'glyph': 'PILL', 'size': 'support', 'label': 'searching for'},
                             {'id': 'q2', 'kind': 'state', 'glyph': 'PILL', 'size': 'support', 'label': 'struggling with'},
                             {'id': 'q3', 'kind': 'state', 'glyph': 'PILL', 'size': 'support', 'label': 'looking for answers'},
                             {'id': 'lens', 'kind': 'signal', 'glyph': 'LENS', 'size': 'hero'}],
                'relations': [{'type': 'scans', 'source': 'lens', 'target': 'q1'}],
                'program': [{'op': 'TRAVEL', 'target': 'lens', 'at': {'word': 'looking'}, 'duration_ms': 560, 'params': {'over': ['q2', 'q3']}},
                            {'op': 'DIM', 'target': 'q2', 'at': {'word': 'looking'}, 'duration_ms': 400, 'from': 1.0, 'to': 0.5},
                            {'op': 'INK', 'target': 'q3', 'at': {'word': 'answers'}, 'duration_ms': 420}],
            },
        },
        {
            'beat_id': 'b07', 'beat_type': 'CONTRAST', 'pattern': 'CONTRAST_RECONFIGURATION', 'dominant_layer': 'ILLUSTRATION',
            'narration': narrations['b07'], 'energy': 0.6, 'complexity': 0.55,
            'display_units': [unit('Most marketing fails', 'hero', 'Most', ['fails'], emphasis=0.9),
                              unit('creating demand from thin air.', 'support', 'create', emphasis=0.5)],
            'illustration': {
                'form': 'STATE_TRANSFORMATION',
                'entities': [{'id': 'air', 'kind': 'state', 'glyph': 'NODE', 'size': 'support', 'label': 'thin air', 'params': {'dashed': True}},
                             {'id': 'demand', 'kind': 'state', 'glyph': 'PILL', 'size': 'hero', 'label': 'demand'}],
                'relations': [{'type': 'transforms_into', 'source': 'air', 'target': 'demand'}],
                'program': [{'op': 'DRAW', 'target': 'air', 'at': {'word': 'tries'}, 'duration_ms': 480},
                            {'op': 'CONNECT', 'target': 'air->demand', 'at': {'word': 'create'}, 'duration_ms': 720},
                            {'op': 'STRIKE', 'target': 'demand', 'at': {'word': 'air'}, 'duration_ms': 420}],
            },
        },
        {
            'beat_id': 'b08', 'beat_type': 'EMPHASIS', 'pattern': 'CONTROLLED_EMPTY_SPACE', 'dominant_layer': 'FIGURE',
            'narration': narrations['b08'], 'energy': 0.4, 'complexity': 0.3,
            'display_units': [unit('The hard way.', 'hero', 'hard', ['hard'], emphasis=0.85)],
            'figure': {'valence': -0.6, 'arousal': 0.25, 'posture': 'standing', 'energy': 0.3, 'formality': 0.5, 'facing': 'TOWARD_TEXT',
                       'justification': 'The sentence is about the marketer worn down by pushing uphill; a still, deflated figure carries that state.'},
        },
        {
            'beat_id': 'b09', 'beat_type': 'EXPLANATION', 'pattern': 'HERO_TO_EVIDENCE_HANDOFF', 'dominant_layer': 'ILLUSTRATION',
            'narration': narrations['b09'], 'energy': 0.66, 'complexity': 0.55,
            'display_units': [unit('It burns', 'hero', 'burns', ['burns'], emphasis=0.9),
                              unit('money, time and energy.', 'support', 'money', emphasis=0.5)],
            'illustration': {
                'form': 'DATA_VISUAL',
                'entities': [{'id': 'money', 'kind': 'evidence', 'glyph': 'BAR', 'size': 'support', 'label': 'money'},
                             {'id': 'time', 'kind': 'evidence', 'glyph': 'BAR', 'size': 'support', 'label': 'time'},
                             {'id': 'energy', 'kind': 'evidence', 'glyph': 'BAR', 'size': 'support', 'label': 'energy'}],
                'program': [{'op': 'INK', 'target': 'money', 'at': {'word': 'money'}, 'duration_ms': 260},
                            {'op': 'GROW', 'target': 'money', 'at': {'word': 'money'}, 'duration_ms': 620, 'from': 1.0, 'to': 0.18},
                            {'op': 'INK', 'target': 'time', 'at': {'word': 'time'}, 'duration_ms': 260},
                            {'op': 'GROW', 'target': 'time', 'at': {'word': 'time'}, 'duration_ms': 620, 'from': 1.0, 'to': 0.22},
                            {'op': 'INK', 'target': 'energy', 'at': {'word': 'energy'}, 'duration_ms': 260},
                            {'op': 'GROW', 'target': 'energy', 'at': {'word': 'energy'}, 'duration_ms': 620, 'from': 1.0, 'to': 0.15}],
            },
        },
        {
            'beat_id': 'b10', 'beat_type': 'PAYOFF', 'pattern': 'PAYOFF_LOCKUP', 'dominant_layer': 'HYBRID',
            'narration': '', 'min_duration_ms': 3400, 'energy': 0.5, 'complexity': 0.35,
            'display_units': [unit('Sell water to the thirsty.', 'hero', None, ['water', 'thirsty'], emphasis=1.0, semantic_role='punch')],
            'illustration': {
                'form': 'OBJECT_STAGE',
                'entities': [{'id': 'vessel', 'kind': 'object', 'glyph': 'VESSEL', 'size': 'hero'},
                             {'id': 'thirst', 'kind': 'signal', 'glyph': 'RING', 'size': 'support', 'params': {'rings': 3}}],
                'relations': [{'type': 'emits_to', 'source': 'thirst', 'target': 'vessel'}],
                'program': [{'op': 'DRAW', 'target': 'vessel', 'at': {'offset_ms': 0}, 'duration_ms': 520},
                            {'op': 'FILL', 'target': 'vessel', 'at': {'offset_ms': 700}, 'duration_ms': 900, 'from': 0.0, 'to': 0.82},
                            {'op': 'EMIT', 'target': 'thirst', 'at': {'offset_ms': 1500}, 'duration_ms': 1100}],
            },
        },
    ]
    for b in beats:
        for u in b['display_units']:
            if u.get('anchor_word') is None:
                del u['anchor_word']
    return {
        'schema': 'NexStudioEditorialTreatmentV2',
        'film_id': 'fixture-water-to-thirsty',
        'note': 'Hand-authored stand-in for a NexMind P8 treatment decision over the reference voice-over. '
                'Every creative choice is P8\'s; the compiler resolves geometry and time only.',
        'aspects': ['9x16', '1x1', '16x9'],
        'fps': 30,
        'brand': {'ink': '#111111', 'paper': '#f6f5f1', 'accent': '#1f6bff', 'finish': 'EDITORIAL_FLAT'},
        'typography': {'reveal': 'WORD_CASCADE', 'tonal_ink': 0.42, 'min_visual_share': 0.6},
        'voice': {'source': 'RECORDED', 'segments': {bid: {'alignment_path': f'voice/{bid}.alignment.json', 'audio_path': f'voice/{bid}.wav'} for bid in BEAT_WORDS}},
        'media_library': [],
        'beats': beats,
    }


def main() -> None:
    vo, words_path = Path(sys.argv[1]), Path(sys.argv[2])
    words = json.loads(words_path.read_text())['words']
    OUT.mkdir(parents=True, exist_ok=True)
    narrations = {}
    ids = list(BEAT_WORDS)
    for i, bid in enumerate(ids):
        a, b = BEAT_WORDS[bid]
        seg = words[a:b + 1]
        prev_end = words[a - 1]['end_ms'] if a > 0 else 0
        next_start = words[b + 1]['start_ms'] if b + 1 < len(words) else seg[-1]['end_ms'] + 400
        start = (prev_end + seg[0]['start_ms']) // 2 if a > 0 else 0
        end = (seg[-1]['end_ms'] + next_start) // 2
        slice_audio(vo, start, end, OUT / 'voice' / f'{bid}.wav')
        (OUT / 'voice' / f'{bid}.alignment.json').write_text(json.dumps(alignment(seg, start), indent=0))
        narrations[bid] = ' '.join(w['word'] for w in seg)
    (OUT / 'treatment.json').write_text(json.dumps(treatment(narrations), indent=1) + '\n')
    print(json.dumps(narrations, indent=1))


if __name__ == '__main__':
    main()
