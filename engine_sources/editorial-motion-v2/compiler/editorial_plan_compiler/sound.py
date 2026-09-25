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
COMMUNITY_MANIFEST = Path(__file__).resolve().parents[2] / 'assets' / 'community' / 'manifest.json'
# A foley loop is an atmosphere, not a hit — accents trim to this budget so a long loop never outruns its event.
ACCENT_TRIM_MS = 1500
MAX_ACCENTS_PER_BEAT = 3
MIN_ACCENT_GAP_MS = 220

# Visible event -> semantic tag family. Authored tags only: every accent in this
# category is built by our own synth bank (craft / synth / foley), never the UI library.
# Order matters — the first tag is the intended sound; the rest are its authored variants.
EVENT_TAGS = {
    'WORD_PROMOTION': ('synth.tick', 'craft.paper.tap'),
    'KEYWORD_HIT': ('craft.paper.tap', 'synth.tick'),
    'LABEL_INVERT': ('synth.click', 'craft.paper.tap'),
    'PHRASE_REPLACE': ('craft.paper.rustle', 'synth.swish'),
    'SPATIAL_RECONFIGURE': ('craft.paper.rustle', 'craft.paper.page'),
    'EVIDENCE_LAND': ('craft.paper.tap', 'synth.thock'),
    'DATA_LAND': ('synth.thock', 'synth.tick'),
    'TRANSITION_CARRIER': ('craft.paper.page', 'craft.paper.rustle'),
    'LINE_DRAW': ('foley.write.pencil', 'foley.write.chalk', 'synth.swish'),
    # INK is a write moment: foley only — no synthetic tick may out-vote the texture.
    'INK_WRITE': ('foley.write.chalk', 'foley.write.pencil', 'foley.write.blackboard'),
    'EMIT_CONFIRM': ('foley.chime', 'synth.shimmer'),
    'COUNT_TICK': ('craft.paper.tap', 'synth.click'),
    'LOUPE_TRAVEL': ('craft.paper.rustle', 'synth.swish'),
    # Furniture arrival / sweeps: paper landing on paper — the category's fabric.
    'ELEMENT_LAND': ('craft.paper.tap', 'synth.pop'),
    'TRANSITION_SWEEP': ('craft.paper.page', 'synth.whoosh'),
    'WIPE_SWEEP': ('craft.paper.page', 'synth.shimmer'),
    'COUNT_RISE': ('synth.riser', 'synth.shimmer'),
    'FIGURE_STEP': ('craft.paper.step', 'craft.paper.tap'),
}
GAIN_DB = {'type': -16.0, 'motion': -18.0, 'impact': -14.0, 'ui': -19.0, 'legacy': -18.0, 'whiteboard': -20.0, 'foley': -18.0, 'synth': -16.0, 'craft': -19.0, 'amb': -27.0}

# What a shown thing sounds like: a landed entity whose concept is in the map takes its foley
# as the accent body instead of the structural landing sound. Concepts unknown to the map keep
# the event's structural pick — the fabric sound.
CONCEPT_FOLEY = {
    'rain': 'foley.water.drop', 'water': 'foley.water.drop', 'sea': 'foley.water.drop', 'ocean': 'foley.water.drop',
    'river': 'foley.water.drop', 'wave': 'foley.water.drop', 'drop': 'foley.water.drop', 'rain-cloud': 'foley.water.drop',
    'seed': 'foley.grow', 'sprout': 'foley.grow', 'grow': 'foley.grow', 'leaf': 'foley.grow', 'flower': 'foley.grow',
    'tree': 'foley.grow', 'root': 'foley.grow', 'plant': 'foley.grow', 'bud': 'foley.grow', 'branch': 'foley.grow',
    'moon': 'foley.sparkle', 'moon-full': 'foley.sparkle', 'moon-half': 'foley.sparkle', 'moon-crescent': 'foley.sparkle',
    'star': 'foley.sparkle', 'stars': 'foley.sparkle', 'night': 'foley.sparkle', 'sparkle': 'foley.sparkle',
    'sun': 'foley.chime', 'sunrise': 'foley.chime', 'dawn': 'foley.chime', 'light': 'foley.chime', 'bulb': 'foley.chime',
    'idea': 'foley.chime', 'fire': 'foley.chime',
    'heart': 'foley.heart', 'love': 'foley.heart', 'life': 'foley.heart', 'baby': 'foley.heart',
    'clock': 'foley.alarm', 'alarm': 'foley.alarm', 'wake': 'foley.alarm', 'morning': 'foley.alarm', 'time': 'foley.alarm',
    'car': 'foley.engine', 'bus': 'foley.engine', 'train': 'foley.engine', 'drive': 'foley.engine',
    'rocket': 'foley.engine', 'engine': 'foley.engine', 'machine': 'foley.engine', 'factory': 'foley.engine',
}
# The air a scene stands in: the first matching tag wins the beat's ambience slot.
SCENE_AMB = {
    'amb.rain': {'rain', 'rain-cloud', 'storm', 'thunder'},
    'amb.water': {'water', 'sea', 'ocean', 'river', 'wave', 'boat', 'sailboat', 'fish', 'lake'},
    'amb.crickets': {'night', 'moon', 'moon-full', 'moon-half', 'moon-crescent', 'star', 'stars', 'moonlight', 'owl'},
    'amb.birds': {'bird', 'dawn', 'sunrise', 'morning', 'spring', 'forest'},
    'amb.fire': {'fire', 'campfire', 'candle'},
    'amb.wind': {'wind', 'sky', 'cloud', 'mountain', 'hill', 'flag', 'kite', 'leaf'},
}
BACKDROP_AMB = {'night': 'amb.crickets', 'deep': 'amb.water', 'slate': 'amb.crickets', 'sky': 'amb.wind', 'water': 'amb.water'}


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
        self._merge_community_foley()

    def _merge_community_foley(self) -> None:
        """Owner-supplied foley lives in the community manifest, not the sound library — merge it under its
        semantic tags so `pick` can choose it. Engine-root-relative paths become absolute here."""
        if not COMMUNITY_MANIFEST.exists():
            return
        root = COMMUNITY_MANIFEST.parents[2]
        for a in json.loads(COMMUNITY_MANIFEST.read_text())['assets']:
            if not a.get('semantic_tag'):
                continue
            self.by_tag.setdefault(a['semantic_tag'], []).append({
                'assetId': a['id'], 'semanticTag': a['semantic_tag'], 'path': str(root / a['path']),
                'productionSha256': a['sha256'], 'license': a['license'],
                'durationSeconds': a.get('duration_s', 0.0), 'family': a.get('family', 'foley'),
            })
            self.by_tag[a['semantic_tag']].sort(key=lambda x: x['assetId'])

    def pick(self, tags: tuple, seed: str) -> Optional[Dict[str, Any]]:
        # First tag with assets wins: the tuple is an ordered preference, not a pool —
        # so the event's intended sound can't be out-voted by a fallback.
        for t in tags:
            pool = self.by_tag.get(t, [])
            if pool:
                h = int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16)
                return pool[h % len(pool)]
        return None


# Layered accent design. Every landing is three sounds, not one: a transient that gives the
# hit its edge, the body (the event's semantic pick above) that gives it weight, and — for
# resonant housings — a short tail. The texture is the glyph's material, so a glossy tile
# clicks, a soft chip thocks, a counter ticks and rings, a stroke swishes: one vocabulary
# heard the way it is seen. Layers ride the same slot, so the ≤3 accents / ≥220ms law is
# unchanged; they are offsets inside one accent.
# Every housing is a paper object now: cards and tiles tap and rustle, badges and chips land
# with a soft thock under a paper tail. Only numerals keep metal; strokes keep their drawn line.
TEXTURES = {
    'paper': {'transient': ('craft.paper.tap',), 'tail': ('craft.paper.rustle',)},
    'soft': {'transient': ('synth.thock',), 'tail': ('craft.paper.rustle',)},
    'metal': {'transient': ('synth.tick',), 'tail': ('synth.shimmer',)},
    'stroke': {'transient': ('synth.swish',), 'tail': ()},
}
GLYPH_TEXTURE = {
    'TILE': 'paper', 'CARD': 'paper', 'FRAME': 'paper', 'MEDIA': 'paper', 'LENS': 'paper',
    'CHIP': 'paper', 'PILL': 'paper', 'BADGE': 'soft', 'STICKY': 'paper', 'CALLOUT': 'paper', 'NODE': 'paper', 'VESSEL': 'paper', 'ICON': 'paper',
    'COUNTER': 'metal', 'RING': 'metal', 'DONUT': 'metal', 'MARK_CIRCLE': 'metal', 'CHART_LINE': 'metal', 'BAR': 'metal', 'BURST': 'metal',
    'ARROW': 'stroke', 'UNDERLINE': 'stroke', 'BRACKET': 'stroke', 'PROHIBIT': 'stroke', 'CONNECTOR': 'stroke',
}
# Events whose body takes texture layers; the rest (type hits, whooshes, risers) are single sounds by design.
LAYERED_EVENTS = {'ELEMENT_LAND': 'paper', 'EVIDENCE_LAND': 'paper', 'DATA_LAND': 'metal', 'EMIT_CONFIRM': 'metal', 'COUNT_TICK': 'metal'}
LAYER_OFFSET_MS = {'transient': -8, 'body': 0, 'tail': 45}
LAYER_GAIN_DB = {'transient': -3.0, 'body': 0.0, 'tail': -8.0}
TAIL_TRIM_MS = 700


def _layer(lib: SoundLibrary, role: str, asset: Dict[str, Any], gain_db: float, trim_ms: Optional[int]) -> Dict[str, Any]:
    return {
        'role': role, 'asset_id': asset['assetId'], 'semantic_tag': asset['semanticTag'], 'path': str(lib.root / asset['path']),
        'sha256': asset['productionSha256'], 'license': asset['license'], 'duration_s': asset['durationSeconds'],
        'gain_db': round(gain_db + LAYER_GAIN_DB[role], 1), 'offset_ms': LAYER_OFFSET_MS[role], 'trim_ms': trim_ms,
    }


def bind_beat_sound(lib: Optional[SoundLibrary], film_id: str, beat_id: str, beat_offset_ms: int, dominant_layer: str,
                    energy: float, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """``candidates`` are visible events: {event, at_ms, strength, glyph?}. Returns bound accents and the silences kept.

    An accent is one slot on the SFX bus at ``beat_at_ms``; its ``layers`` are the transient / body /
    tail sounds mixed around that moment. The top-level asset fields describe the body so older
    readers still see one sound per accent."""
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
        # A landing entity with a known sound plays its own foley — water plips, a sprout
        # sproings — in front of the fabric tap it would otherwise take.
        concept_foley = CONCEPT_FOLEY.get(str(c.get('concept') or '').lower())
        if concept_foley and c['event'] in ('ELEMENT_LAND', 'EVIDENCE_LAND'):
            tags = (concept_foley,) + tags
        if c['event'] == 'TRANSITION_CARRIER' and energy < 0.5:
            silenced.append(c['event']); continue
        if any(abs(c['at_ms'] - x['beat_at_ms']) < MIN_ACCENT_GAP_MS for x in chosen):
            silenced.append(c['event']); continue
        seed = f'{film_id}:{beat_id}:{c["event"]}:{i}'
        asset = lib.pick(tags, seed)
        if not asset:
            silenced.append(c['event']); continue
        gain = GAIN_DB.get(asset['family'], -16.0) + (2.0 if c.get('strength', 0.5) > 0.9 else 0.0)
        trim = int(min(asset['durationSeconds'] * 1000, ACCENT_TRIM_MS)) if asset['durationSeconds'] else None
        layers = [_layer(lib, 'body', asset, gain, trim)]
        texture = None
        if c['event'] in LAYERED_EVENTS:
            texture = GLYPH_TEXTURE.get(c.get('glyph') or '', LAYERED_EVENTS[c['event']])
            recipe = TEXTURES[texture]
            tr = lib.pick(recipe['transient'], seed + ':transient') if recipe['transient'] else None
            if tr:
                layers.insert(0, _layer(lib, 'transient', tr, gain, None))
            tl = lib.pick(recipe['tail'], seed + ':tail') if recipe['tail'] else None
            if tl:
                layers.append(_layer(lib, 'tail', tl, gain, int(min(tl['durationSeconds'] * 1000, TAIL_TRIM_MS)) if tl['durationSeconds'] else None))
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
            'gain_db': gain,
            'trim_ms': trim,
            'texture': texture,
            'layers': layers,
        })
    chosen.sort(key=lambda a: a['beat_at_ms'])
    return {'accents': chosen, 'silenced': silenced, 'reason': None}


AMBIENCE_FADE_MS = 620
AMBIENCE_GAIN_DB = GAIN_DB['amb']


def bind_beat_ambience(lib: Optional[SoundLibrary], film_id: str, beat_id: str,
                       concepts: List[str], backdrop_tones: List[str], duration_ms: int) -> Optional[Dict[str, Any]]:
    """The air a beat stands in: one quiet loop picked from what the scene shows — rain over a
    rain-cloud, crickets under a night diorama, water at the sea. Entities outrank backdrop
    tones; the first map hit wins so the loudest story sound is the one heard."""
    if lib is None or not duration_ms:
        return None
    tag = None
    for amb, keys in SCENE_AMB.items():
        if any(str(c).lower() in keys for c in concepts):
            tag = amb
            break
    if tag is None:
        for tone in backdrop_tones:
            if tone in BACKDROP_AMB:
                tag = BACKDROP_AMB[tone]
                break
    if tag is None:
        return None
    asset = lib.pick((tag,), f'{film_id}:{beat_id}:ambience')
    if not asset:
        return None
    return {
        'tag': tag,
        'asset_id': asset['assetId'],
        'path': str(lib.root / asset['path']),
        'sha256': asset['productionSha256'],
        'license': asset['license'],
        'duration_s': asset['durationSeconds'],
        'gain_db': AMBIENCE_GAIN_DB,
        'fade_ms': AMBIENCE_FADE_MS,
        'loop': True,
    }


COMMUNITY_MANIFEST = Path(__file__).resolve().parents[2] / 'assets' / 'community' / 'manifest.json'
# Bus law the renderer executes: per-bus trims, the ducking shape and the master ceiling. The
# voice is the film; music and effects are mixed to it, never the other way around.
MIX = {
    'target_lufs': -16.0,          # integrated loudness of the master (streaming/social delivery)
    'true_peak_dbtp': -1.0,        # master ceiling
    'buses': {
        'voice': {'highpass_hz': 80, 'compressor': {'threshold_db': -20, 'ratio': 2.0, 'attack_ms': 8, 'release_ms': 120}, 'trim_db': 0.0},
        'sfx': {'compressor': {'threshold_db': -18, 'ratio': 3.0, 'attack_ms': 3, 'release_ms': 90}, 'trim_db': 0.0},
        'music': {'highpass_hz': 40, 'trim_db': 0.0,
                  # bed drops by floor_db when the voice sits window_db above the sidechain threshold
                  'duck': {'threshold': 0.1, 'window_db': 12, 'attack_ms': 30, 'release_ms': 450, 'floor_db': -8.0}},
    },
    'limiter': {'attack_ms': 5, 'release_ms': 50},
}


ENERGY_SHORTLIST = 3
# Where a bed sits before ducking: a -16 LUFS master trimmed by -19 dB, the level the mix was tuned at.
MUSIC_BED_LUFS = -35.0


def bind_film_music(film_id: str, mood: Optional[str] = None, duration_ms: Optional[int] = None,
                    energy: Optional[float] = None) -> Dict[str, Any]:
    """Music bed binding: one rights-clean (CC0) bed per film, chosen by context then hash.

    Beds carry measured ``bpm`` / ``grid_offset_ms`` / ``energy`` / ``lufs`` and curated ``moods``
    (``tools/vendor_music.py``). The pool narrows in order: an authored film ``mood`` keeps beds
    carrying it; a film short enough to fit inside a bed keeps only covering beds so no loop seam
    is heard; then the beds nearest the film's spoken ``energy`` (mean beat energy) form a
    shortlist, and a deterministic hash of the film id picks among them. Same film, same bed.

    The renderer plays the bed from ``start_offset_ms`` (set by the groove fit so its beat grid
    meets the film's landings) on its own bus, ducked under the voice. When no community music
    manifest is vendored the slot stays silent rather than shipping unlicensed audio."""
    silent = {'slot': 'BACKGROUND_MUSIC', 'status': 'SILENT_NO_RIGHTS_CLEAN_BED', 'duck_under_voice_db': MIX['buses']['music']['duck']['floor_db'], 'path': None}
    if not COMMUNITY_MANIFEST.exists():
        return silent
    beds = [a for a in json.loads(COMMUNITY_MANIFEST.read_text()).get('assets', [])
            if a.get('kind') == 'music' and a.get('license', '').startswith('CC0') and (COMMUNITY_MANIFEST.parent / a['path']).exists()]
    if not beds:
        return silent
    pool_size = len(beds)
    if mood:
        matched = [b for b in beds if mood in (b.get('moods') or [])]
        if matched:
            beds = matched
    if duration_ms:
        covering = [b for b in beds if float(b.get('duration_s') or 0) * 1000 >= duration_ms]
        if covering:
            beds = covering
    if energy is not None and all(b.get('energy') is not None for b in beds):
        beds = sorted(beds, key=lambda b: (abs(float(b['energy']) - energy), b['id']))[:ENERGY_SHORTLIST]
    pick = beds[int(hashlib.sha256(film_id.encode()).hexdigest(), 16) % len(beds)]
    path = str(COMMUNITY_MANIFEST.parent / pick['path'])
    # Beds are mastered anywhere from -8 to -22 LUFS; the trim brings each to the same level under the voice.
    gain_db = MUSIC_BED_LUFS - float(pick['lufs']) if pick.get('lufs') is not None else -19.0
    gain_db = round(max(-30.0, min(-10.0, gain_db)), 1)
    return {'slot': 'BACKGROUND_MUSIC', 'status': 'BOUND_CC0', 'path': path, 'sha256': pick['sha256'], 'license': pick['license'],
            'asset_id': pick['id'], 'title': pick.get('title'), 'moods': pick.get('moods'), 'bpm': pick.get('bpm'), 'grid_offset_ms': pick.get('grid_offset_ms'),
            'energy': pick.get('energy'), 'lufs': pick.get('lufs'), 'duration_s': pick.get('duration_s'),
            'mood_request': mood, 'energy_request': None if energy is None else round(energy, 3), 'pool': pool_size, 'shortlist': [b['id'] for b in beds],
            'gain_db': gain_db, 'duck_under_voice_db': MIX['buses']['music']['duck']['floor_db'], 'loop': True, 'fade_in_ms': 700, 'fade_out_ms': 1600,
            'start_offset_ms': 0, 'groove': None}


def community_surface(kind: str, path_fragment: str) -> Optional[Dict[str, Any]]:
    """Resolve a vendored CC0 surface/texture asset by manifest path fragment."""
    if not COMMUNITY_MANIFEST.exists():
        return None
    for a in json.loads(COMMUNITY_MANIFEST.read_text()).get('assets', []):
        if a.get('kind') == kind and path_fragment in a.get('path', '') and (COMMUNITY_MANIFEST.parent / a['path']).exists():
            return {'path': str(COMMUNITY_MANIFEST.parent / a['path']), 'sha256': a['sha256'], 'license': a['license']}
    return None
