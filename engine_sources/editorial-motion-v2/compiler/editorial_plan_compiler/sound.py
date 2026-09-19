"""Semantic sound binding against NexStudio Sound Library V2.

Sound explains, punctuates or embodies a visible event. Every accent here is
bound to a specific compiled motion event; nothing is sprinkled. Silence is the
default and QUIET beats stay silent. Selectable assets only, rotated by
deterministic hash so the same plan always binds the same files.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

REGISTRY_REL = 'manifests/NEXSTUDIO_SOUND_V2_REGISTRY.json'
MAX_ACCENTS_PER_BEAT = 3
MIN_ACCENT_GAP_MS = 220

# Visible event -> semantic tag family (structural, never topic-based).
EVENT_TAGS = {
    'WORD_PROMOTION': ('type.tick', 'type.pluck'),
    'KEYWORD_HIT': ('type.tick',),
    'LABEL_INVERT': ('type.pluck',),
    'PHRASE_REPLACE': ('motion.ui.contract',),
    'SPATIAL_RECONFIGURE': ('motion.ui.expand',),
    'EVIDENCE_LAND': ('impact.soft.medium', 'impact.plate.light'),
    'DATA_LAND': ('impact.generic.light',),
    'TRANSITION_CARRIER': ('motion.ui.expand', 'motion.ui.contract', 'legacy.paper.rustle.light'),
    'LINE_DRAW': ('whiteboard.marker.line', 'type.scratch', 'whiteboard.pencil.write'),
    'EMIT_CONFIRM': ('ui.confirm', 'legacy.ui.confirm.chime'),
    'COUNT_TICK': ('legacy.ui.level.tick', 'ui.switch.tactile'),
    'LOUPE_TRAVEL': ('legacy.ui.navigation.swipe', 'motion.ui.contract'),
}
GAIN_DB = {'type': -16.0, 'motion': -18.0, 'impact': -14.0, 'ui': -19.0, 'legacy': -18.0, 'whiteboard': -20.0, 'foley': -20.0}


def library_root() -> Optional[Path]:
    env = os.environ.get('NEXSTUDIO_SOUND_LIBRARY_ROOT', '').strip()
    candidates = [Path(env)] if env else []
    here = Path(__file__).resolve()
    candidates.append(here.parents[2] / 'sound-library')
    candidates.append(here.parents[4] / 'engines' / 'sound' / 'NexStudio_Sound_Library_V2_Production')
    for c in candidates:
        if (c / REGISTRY_REL).exists():
            return c
    return None


class SoundLibrary:
    def __init__(self, root: Path):
        self.root = root
        reg = json.loads((root / REGISTRY_REL).read_text())
        self.version = reg.get('version')
        self.status = reg.get('status')
        self.by_tag: Dict[str, List[Dict[str, Any]]] = {}
        for a in reg['assets']:
            if a.get('selectable') and a.get('status') == 'ADMITTED':
                self.by_tag.setdefault(a['semanticTag'], []).append(a)
        for v in self.by_tag.values():
            v.sort(key=lambda a: a['assetId'])

    def pick(self, tags: tuple, seed: str) -> Optional[Dict[str, Any]]:
        pool = [a for t in tags for a in self.by_tag.get(t, [])]
        if not pool:
            return None
        h = int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16)
        return pool[h % len(pool)]


def bind_beat_sound(lib: Optional[SoundLibrary], film_id: str, beat_id: str, beat_offset_ms: int, dominant_layer: str,
                    energy: float, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """``candidates`` are visible events: {event, at_ms, strength}. Returns bound accents and the silences kept."""
    if dominant_layer == 'QUIET':
        return {'accents': [], 'silenced': [c['event'] for c in candidates], 'reason': 'QUIET_BEAT_STAYS_SILENT'}
    if lib is None:
        return {'accents': [], 'silenced': [c['event'] for c in candidates], 'reason': 'SOUND_LIBRARY_MISSING'}
    ordered = sorted(candidates, key=lambda c: (-c.get('strength', 0.5), c['at_ms']))
    chosen: List[Dict[str, Any]] = []
    silenced: List[str] = []
    for i, c in enumerate(ordered):
        tags = EVENT_TAGS.get(c['event'])
        if not tags or len(chosen) >= MAX_ACCENTS_PER_BEAT:
            silenced.append(c['event']); continue
        if c['event'] == 'TRANSITION_CARRIER' and energy < 0.5:
            silenced.append(c['event']); continue
        if any(abs(c['at_ms'] - x['beat_at_ms']) < MIN_ACCENT_GAP_MS for x in chosen):
            silenced.append(c['event']); continue
        asset = lib.pick(tags, f'{film_id}:{beat_id}:{c["event"]}:{i}')
        if not asset:
            silenced.append(c['event']); continue
        chosen.append({
            'event': c['event'],
            'beat_at_ms': int(c['at_ms']),
            'film_at_ms': int(beat_offset_ms + c['at_ms']),
            'asset_id': asset['assetId'],
            'semantic_tag': asset['semanticTag'],
            'path': str(lib.root / asset['path']),
            'sha256': asset['productionSha256'],
            'license': asset['license'],
            'duration_s': asset['durationSeconds'],
            'gain_db': GAIN_DB.get(asset['family'], -16.0) + (2.0 if c.get('strength', 0.5) > 0.9 else 0.0),
        })
    chosen.sort(key=lambda a: a['beat_at_ms'])
    return {'accents': chosen, 'silenced': silenced, 'reason': None}


COMMUNITY_MANIFEST = Path(__file__).resolve().parents[2] / 'assets' / 'community' / 'manifest.json'


def bind_film_music(film_id: str) -> Dict[str, Any]:
    """Music bed binding: one rights-clean (CC0) bed per film, picked by deterministic hash.

    The renderer mixes it under the voice with sidechain ducking. When no community
    music manifest is vendored the slot stays silent rather than shipping unlicensed audio."""
    silent = {'slot': 'BACKGROUND_MUSIC', 'status': 'SILENT_NO_RIGHTS_CLEAN_BED', 'duck_under_voice_db': -14, 'path': None}
    if not COMMUNITY_MANIFEST.exists():
        return silent
    beds = [a for a in json.loads(COMMUNITY_MANIFEST.read_text()).get('assets', [])
            if a.get('kind') == 'music' and a.get('license', '').startswith('CC0') and (COMMUNITY_MANIFEST.parent / a['path']).exists()]
    if not beds:
        return silent
    pick = beds[int(hashlib.sha256(film_id.encode()).hexdigest(), 16) % len(beds)]
    path = str(COMMUNITY_MANIFEST.parent / pick['path'])
    return {'slot': 'BACKGROUND_MUSIC', 'status': 'BOUND_CC0', 'path': path, 'sha256': pick['sha256'], 'license': pick['license'],
            'gain_db': -19.0, 'duck_under_voice_db': -14.0, 'loop': True, 'fade_in_ms': 700, 'fade_out_ms': 1600}


def community_surface(kind: str, path_fragment: str) -> Optional[Dict[str, Any]]:
    """Resolve a vendored CC0 surface/texture asset by manifest path fragment."""
    if not COMMUNITY_MANIFEST.exists():
        return None
    for a in json.loads(COMMUNITY_MANIFEST.read_text()).get('assets', []):
        if a.get('kind') == kind and path_fragment in a.get('path', '') and (COMMUNITY_MANIFEST.parent / a['path']).exists():
            return {'path': str(COMMUNITY_MANIFEST.parent / a['path']), 'sha256': a['sha256'], 'license': a['license']}
    return None
