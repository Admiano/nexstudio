"""Still Open Peeps figure resolution from a P8 figure directive.

Selection scores the artwork's authored emotion/posture vectors against the
directive's continuous values (valence, arousal, energy, formality). Tag words
in the library metadata are never consulted — topic words do not choose people.
The result is an exact, hashed part list the renderer composes verbatim.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from .contracts import Brand, FigureDirective

PEEPS = Path(__file__).resolve().parents[2] / 'assets' / 'peeps'
INDEX = json.loads((PEEPS / 'parts-index.json').read_text())
SEMANTICS = json.loads((PEEPS / 'semantics.json').read_text())
PARTS: Dict[str, Dict[str, Dict[str, Any]]] = {group: {p['id']: p for p in items} for group, items in INDEX['parts'].items()}

# Novelty faces/heads are excluded from editorial casting by default.
EXCLUDED_FACES = {'monster', 'cyclops', 'angry-with-fang', 'blank', 'eating-happy', 'with-mask-calm', 'with-mask-cheers', 'with-mask-smile'}
EXCLUDED_POSES = {'standing-robot-dance-1', 'standing-robot-dance-2', 'standing-robot-dance-3', 'standing-polka-dots', 'sitting-bike'}
EXCLUDED_HEADS = {'bear', 'doctor-nurse-2', 'doctor-nurse-3'}

# Open Peeps garment colours -> editorial palette roles. Skin (#d08b5b) is remapped to the chosen tone.
GARMENT_SOURCE = ['#9ddadb', '#ffcf77', '#8fa7df', '#78e185', '#9fd8e5', '#e86bbb', '#fdea6b', '#ec7495', '#ba98de', '#ff8181', '#ff6c6c', '#c93305', '#d6b370', '#ecdcbf', '#e8e1e1', '#e6e6e6']
GREYS = ['#d9d9d7', '#bfbfbd', '#e6e6e4', '#cfcfcd']


def _hash(seed: str) -> float:
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _score_face(face_id: str, d: FigureDirective) -> float:
    m = SEMANTICS['face'].get(face_id)
    if not m or face_id in EXCLUDED_FACES:
        return -1
    return 1 - (0.62 * abs(m['valence'] - d.valence) / 2 + 0.38 * abs(m['arousal'] - d.arousal))


def _score_pose(pose_id: str, d: FigureDirective) -> float:
    m = SEMANTICS['pose'].get(pose_id)
    if not m or pose_id in EXCLUDED_POSES or m['posture'] != d.posture:
        return -1
    return 1 - (0.55 * abs(m['energy'] - d.energy) + 0.45 * abs(m['formality'] - d.formality))


def _pick(candidates: List[tuple], seed: str) -> str:
    """Best score wins; near-ties (within 0.04) rotate deterministically by seed so a film is not one face."""
    ranked = sorted(candidates, key=lambda x: (-x[0], x[1]))
    top = [c for c in ranked if c[0] >= ranked[0][0] - 0.04]
    return top[int(_hash(seed) * len(top)) % len(top)][1]


def resolve_figure(d: FigureDirective, beat_id: str, film_id: str, brand: Brand, facing_left: bool) -> Dict[str, Any]:
    seed = f'{film_id}:{beat_id}'
    face = _pick([(_score_face(f, d), f) for f in PARTS['face']], seed + ':face')
    pose = _pick([(_score_pose(p, d), p) for p in PARTS['pose']], seed + ':pose')
    heads = [h for h in PARTS['head'] if h not in EXCLUDED_HEADS]
    head = heads[int(_hash(seed + ':head') * len(heads)) % len(heads)]
    tones = SEMANTICS['skinTones']['palette']
    tone = tones[int(_hash(seed + ':skin') * len(tones)) % len(tones)]
    comp = INDEX['compositions'][d.posture]

    palette = {SEMANTICS['skinTones']['source']: tone, '#000000': brand.ink, '#221e1f': brand.ink, '#231f20': brand.ink}
    order = sorted(GARMENT_SOURCE, key=lambda c: _hash(seed + c))
    for i, src in enumerate(order):
        if i == 0 and brand.accent:
            palette[src] = brand.accent
        else:
            palette[src] = GREYS[i % len(GREYS)]

    parts = []
    for slot, part_id in (('body', pose), ('head', head), ('face', face)):
        p = PARTS['pose' if slot == 'body' else slot][part_id]
        frame = comp['slots'][slot]
        parts.append({
            'slot': slot,
            'part_id': part_id,
            'file': p['file'],
            'sha256': _sha(PEEPS / p['file']),
            'frame': {'x': frame['x'], 'y': frame['y'], 'w': frame['width'], 'h': frame['height']},
            'source_size': {'w': p['width'], 'h': p['height']},
        })
    x0 = min(pt['frame']['x'] for pt in parts)
    y0 = min(pt['frame']['y'] for pt in parts)
    x1 = max(pt['frame']['x'] + pt['frame']['w'] for pt in parts)
    y1 = max(pt['frame']['y'] + pt['frame']['h'] for pt in parts)
    face_meta = SEMANTICS['face'][face]
    pose_meta = SEMANTICS['pose'][pose]
    return {
        'library': 'OPEN_PEEPS',
        'still': True,
        'framing': 'FULL_BODY',
        'posture': d.posture,
        'composition': {'view_box': [x0, y0, x1 - x0, y1 - y0], 'aspect': round((x1 - x0) / (y1 - y0), 4)},
        'parts': parts,
        'palette': palette,
        'mirror': facing_left,
        'facing': d.facing,
        'emotion': {'face': face, 'label': face_meta['emotion'], 'valence': face_meta['valence'], 'arousal': face_meta['arousal']},
        'pose': {'id': pose, 'energy': pose_meta['energy'], 'formality': pose_meta['formality']},
        'justification': d.justification,
        'directive': {'valence': d.valence, 'arousal': d.arousal, 'energy': d.energy, 'formality': d.formality},
    }
