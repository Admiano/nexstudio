"""Board-sections render mode — the whiteboard-crypto form.

Evidence model (from frame analysis of the reference):
  * Each beat is its own full-frame scene — a still shot, no camera
    movement of any kind. When the next beat opens, the previous scene's
    ink fades off the paper as the new title letters in.
  * Each scene composes a vignette: hand-lettered title at its top, a hero
    element at its centre, satellites (objects, chips, captions) arranged
    around it. A human figure appears only in scenes that ask for one.
  * Multi-accent ink: black lettering/art + accent colors on fills, marks.
  * Ending: "Thanks" + a heart draws centred on the empty board.

Beats map 1:1 to scenes.
"""
from __future__ import annotations

import math
import re
import svg_paths
import random

from PIL import Image, ImageDraw

import whiteboard_pil_adapter as wbp
import v3_board_renderer as v3r
from v3_board_renderer import (
    _draw_strokes, _map_scale, _palette, _group_world_bounds,
    _composite_frame, _overlay_hand, _SLICE_SPAN, _arc,
)
from v3_board_renderer import text_strokes, text_width

WIPE_SECONDS = 0.7
THANKS_SECONDS = 1.8
CELL_SECONDS = 0.42
END_HOLD = 1.4
MAX_SECTIONS_PER_BOARD = 3

# extra accent channels layered on the plan palette (reference ink colors)
_ACCENTS = {
    'a_orange': (232, 131, 58, 255),
    'a_blue': (59, 123, 212, 255),
    'a_green': (79, 157, 105, 255),
    'a_red': (208, 69, 62, 255),
    'a_yellow': (229, 184, 58, 255),
    'a_purple': (149, 117, 205, 255),
}
# per-section title swash colors in storyboard mode (pastel highlight
# bands behind each numbered heading, like the reference storyboard)
_SWASH = ('a_blue', 'a_green', 'a_yellow', 'a_purple')
# stroke-color channel remap for this mode: icon detail/fill strokes take
# real accent hues instead of the neutral plan accent
_REMAP = {'accent': 'a_orange', 'accfill': 'a_blue', 'accdeep': 'a_blue'}


def _colors(plan):
    cols = dict(_palette(plan))
    acc = cols.get('accent')
    for k, v in _ACCENTS.items():
        cols[k] = v
    # plan accent (brand-authored or --accent) still wins for 'accent'
    if acc and acc[:3] not in ((51, 51, 51), (17, 17, 17)):
        cols['a_orange'] = acc
    # authored hex tones on role dicts register as named channels
    for b in (plan.get('beats') or []):
        sc = b.get('scene') or {}
        roles = ([sc.get('heroRole')]
                 + list(sc.get('supportingRoles') or []))
        for r in roles:
            if isinstance(r, dict):
                t = str(r.get('tone') or '')
                if re.match(r'^#[0-9a-fA-F]{6}$', t):
                    cols[t] = (int(t[1:3], 16), int(t[3:5], 16),
                               int(t[5:7], 16), 255)
    # kit glyph tones that are literal hex register the same way — the
    # manifest pins a hue ('#F7931A' = bitcoin orange) that the plan's
    # brand accent must not override, unlike the a_* channels
    import v3_board_renderer as _v3r
    for _glyphs in _v3r._kits().values():
        for _meta in _glyphs.values():
            _t = str(_meta.get('tone') or '')
            if re.match(r'^#[0-9a-fA-F]{6}$', _t):
                cols[_t] = (int(_t[1:3], 16), int(_t[3:5], 16),
                            int(_t[5:7], 16), 255)
    return cols


_VIGNETTES: dict = {}


def _vignette(frame: Image.Image, ratio: str) -> Image.Image:
    """Reference-style paper vignette — fixed camera-light edge darkening
    (~18% at the corners), applied to the composed frame."""
    m = _VIGNETTES.get(ratio)
    if m is None:
        vw, vh = wbp.RATIO_SIZES[ratio]
        g = Image.radial_gradient('L').resize((vw, vh))
        m = g.point(lambda v: max(0, 255 - int(0.42 * max(0, v - 110))))
        _VIGNETTES[ratio] = Image.merge('RGB', (m, m, m))
    from PIL import ImageChops
    return ImageChops.multiply(frame.convert('RGB'), _VIGNETTES[ratio])


def _remap_col(col):
    return _REMAP.get(col, col)


_INKY = {'ink', 'inkfill', 'pale', 'paper', 'bg'}


def _remap_strokes(strokes):
    out = []
    for s in strokes:
        c = _remap_col(s[1])
        fl = s[3] if len(s) > 3 else False
        # colored fills become flat color masses — the reference's saturated
        # fills — while ink/paper fills keep the scribble-hatch look
        if fl and fl != 'solid' and c not in _INKY:
            fl = 'solid'
        out.append(tuple([s[0], c, s[2], fl] + list(s[4:])))
    return out


def _wobble_line(p0, p1, n=30, wob=8.0, seed=3):
    rnd = random.Random(seed)
    pts = []
    for i in range(n + 1):
        q = i / n
        x = p0[0] + (p1[0] - p0[0]) * q
        y = p0[1] + (p1[1] - p0[1]) * q
        # perpendicular jitter, tapered at both ends
        f = math.sin(q * math.pi) ** 0.5
        dx = -(p1[1] - p0[1])
        dy = (p1[0] - p0[0])
        L = math.hypot(dx, dy) or 1.0
        x += rnd.uniform(-wob, wob) * f * dx / L
        y += rnd.uniform(-wob, wob) * f * dy / L
        pts.append((x, y))
    return pts


def _bubble_box(center, w, h, tail_to):
    """Rounded speech bubble (absolute strokes): box + tail to speaker."""
    x0, y0 = center[0] - w / 2, center[1] - h / 2
    x1, y1 = center[0] + w / 2, center[1] + h / 2
    r = min(h * 0.32, w * 0.14)
    seg = []
    seg += _arc(x0 + r, y0 + r, r, r, 90, 180, 8)          # TL
    seg += [(x1 - r, y0)]
    seg += _arc(x1 - r, y0 + r, r, r, 0, 90, 8)            # TR
    seg += [(x1, y1 - r)]
    seg += _arc(x1 - r, y1 - r, r, r, -90, 0, 8)           # BR
    seg += [(x0 + r, y1)]
    seg += _arc(x0 + r, y1 - r, r, r, 180, 270, 8)         # BL
    seg += [(x0, y0 + r)]
    tail = [(center[0] - w * 0.16, y1), (tail_to[0], tail_to[1]),
            (center[0] + w * 0.02, y1)]
    return [(seg, 'ink', 1.0, False, True),
            (tail, 'ink', 0.9, False, True)]


def _edge_pt(bb, toward):
    """Point where a rect's edge faces a target — arrow anchor points."""
    cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    dx, dy = toward[0] - cx, toward[1] - cy
    if dx == 0 and dy == 0:
        return (cx, cy)
    hw, hh = (bb[2] - bb[0]) / 2, (bb[3] - bb[1]) / 2
    k = min(hw / abs(dx) if dx else 1e9, hh / abs(dy) if dy else 1e9)
    return (cx + dx * k * 0.94, cy + dy * k * 0.94)


def _curved_arrow(p0, p1):
    """A gently bent arrow p0->p1 in world space — the reference's
    connective tissue between actors and objects."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1.0
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    bend = L * 0.18
    cx_, cy_ = mx - dy / L * bend, my + dx / L * bend
    pts = [((1 - q) ** 2 * p0[0] + 2 * (1 - q) * q * cx_ + q * q * p1[0],
            (1 - q) ** 2 * p0[1] + 2 * (1 - q) * q * cy_ + q * q * p1[1])
           for q in (i / 26.0 for i in range(27))]
    ang = math.atan2(p1[1] - cy_, p1[0] - cx_)
    hl = min(30.0, L * 0.18)
    h1 = [p1, (p1[0] + hl * math.cos(ang + 2.55),
               p1[1] + hl * math.sin(ang + 2.55))]
    h2 = [p1, (p1[0] + hl * math.cos(ang - 2.55),
               p1[1] + hl * math.sin(ang - 2.55))]
    return [(pts, 'a_orange', 1.5, False, True),
            (h1, 'a_orange', 1.5, False, True),
            (h2, 'a_orange', 1.5, False, True)]


def _heart_strokes(center, size):
    pts = []
    for i in range(41):
        a = i / 40 * 2 * math.pi
        x = 16 * math.sin(a) ** 3
        y = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
        pts.append((center[0] + x * size / 34, center[1] - y * size / 34))
    return [(pts, 'a_red', 1.6, True, True)]


def _section_label(beat):
    label = str(beat.get('heroRole') or '').strip()
    if not label:
        sid = str(beat.get('beat_id') or '')
        label = sid.split('_', 1)[-1].replace('_', ' ')
    return label.title()


from pathlib import Path as _Path
_PC_DIR = _Path(__file__).resolve().parent / 'assets' / 'paper_cast'
_PC_CACHE: dict = {}

import sys as _sys
_sys.path.insert(0, str(_Path(__file__).resolve().parent
                        / 'tools' / 'paper_cast'))
try:
    import line_cast as _line_cast
except Exception:
    _line_cast = None


def _papercast_strokes(cast_id):
    """Paper-cast figure -> unit-space strokes (~260 tall, feet at 0) —
    ONE continuous body silhouette plus face/garment detail strokes,
    traced from the merged masses (line_cast) rather than per-part
    outlines."""
    if cast_id in _PC_CACHE:
        return _PC_CACHE[cast_id]
    p = _PC_DIR / f'{cast_id}.svg'
    if not p.exists():
        _PC_CACHE[cast_id] = None
        return None
    if _line_cast is None:
        _PC_CACHE[cast_id] = None
        return None
    st = []
    for pts, det in _line_cast.figure_strokes(p, height=260.0):
        if len(pts) > 1:
            st.append((pts, 'ink', 0.55 if det else 1.35, det == 'fill', False))
    _PC_CACHE[cast_id] = st or None
    return _PC_CACHE[cast_id]


# role word -> paper-cast member
_CAST_MAP = {
    'parent': 'parent', 'mother': 'parent', 'father': 'parent',
    'mom': 'parent', 'dad': 'parent',
    'child': 'child', 'kid': 'child', 'baby': 'toddler', 'toddler': 'toddler',
    'investor': 'executive', 'executive': 'executive', 'boss': 'executive',
    'manager': 'executive', 'ceo': 'executive', 'founder': 'executive',
    'doctor': 'healthcare-worker', 'nurse': 'healthcare-worker',
    'patient': 'healthcare-worker', 'medic': 'healthcare-worker',
    'surgeon': 'healthcare-worker', 'clinician': 'healthcare-worker',
    'teacher': 'teacher', 'professor': 'teacher', 'instructor': 'teacher',
    'student': 'student', 'pupil': 'student', 'teen': 'student',
    'worker': 'office-worker', 'employee': 'office-worker',
    'staff': 'office-worker', 'employer': 'office-worker',
    'builder': 'builder', 'construction': 'builder',
    'technician': 'technician', 'engineer': 'technician',
    'mechanic': 'technician',
    'customer': 'customer', 'shopper': 'customer', 'buyer': 'customer',
    'client': 'customer', 'consumer': 'customer',
    'helper': 'support-helper', 'assistant': 'support-helper',
    'salesperson': 'salesperson', 'seller': 'salesperson',
    'dealer': 'salesperson', 'landlord': 'salesperson',
    'friend': 'peer-friend', 'partner': 'peer-friend',
    'colleague': 'peer-friend', 'neighbor': 'peer-friend',
    'mentor': 'mentor', 'coach': 'mentor', 'elder': 'mentor',
    'senior': 'mentor', 'grandma': 'mentor', 'grandpa': 'mentor',
    'analyst': 'analyst', 'scientist': 'analyst', 'banker': 'analyst',
    'reporter': 'field-reporter', 'journalist': 'field-reporter',
    'presenter': 'presenter', 'speaker': 'presenter', 'host': 'presenter',
    'artist': 'creator', 'designer': 'creator', 'writer': 'creator',
    'developer': 'creator',
    'chef': 'support-helper', 'driver': 'office-worker',
    'pilot': 'technician', 'farmer': 'builder', 'guard': 'executive',
    'soldier': 'executive', 'politician': 'executive',
    'voter': 'customer', 'citizen': 'customer', 'tourist': 'customer',
    'athlete': 'builder', 'miner': 'builder', 'hacker': 'technician',
    'thief': 'technician', 'regulator': 'executive',
    'competitor': 'peer-friend', 'agent': 'office-worker',
    'audience': 'customer', 'viewer': 'customer', 'reader': 'student',
    'crowd': 'customer', 'team': 'office-worker', 'people': 'customer',
    'person': 'presenter', 'man': 'customer', 'woman': 'customer',
    'guy': 'customer', 'user': 'office-worker',
}


def _papercast_for(label):
    low = str(label).lower()
    for w, cid in _CAST_MAP.items():
        if w in low.split() or (len(w) > 4 and w in low):
            return cid
    return None


_AGENT_WORDS = {
    'investor','trader','doctor','nurse','patient','customer','consumer',
    'user','shopper','buyer','seller','worker','employee','manager','boss',
    'founder','ceo','student','teacher','child','mother','father','parent',
    'driver','pilot','farmer','scientist','developer','engineer','designer',
    'artist','audience','viewer','reader','team','crowd','people','person',
    'man','woman','guy','kid','baby','elder','senior','client','partner',
    'competitor','regulator','hacker','guard','soldier','politician','voter',
    'citizen','tourist','neighbor','friend','colleague','staff','agent',
    'mom','dad','grandma','grandpa','coach','athlete','chef','writer',
    'analyst','banker','miner','farmer','nurse','surgeon','technician',
    'customer','employee','employer','landlord','tenant','buyer','dealer',
}


def _agent_word(beat):
    text = (str(beat.get('heroRole') or '') + ' ' +
            str(beat.get('beat_id') or '') + ' ' +
            str(beat.get('narration') or '')).lower()
    toks = re.findall(r"[a-z']+", text)
    for w in toks:
        if w in _AGENT_WORDS:
            return w
    return None


def _person_item(label, beat_i):
    """A situational human figure — paper-cast member when the role maps,
    open-peeps otherwise — labeled under."""
    pcid = _papercast_for(label)
    st = _papercast_strokes(pcid) if pcid else None
    cast = None
    if st is None:
        pose = v3r._pose_for_label(label)
        cast = v3r._cast_spec_for(label, pose)
        st = v3r._strokes_for('person', pose, 1, cast)
    slot = {'icon': 'person', 'label': label, 'cast': cast,
            'facing': 1, 'center': (0, 0), 'size': 1.0}
    gs = [('icon', st, (0, 0), 1.0, slot)]
    gs.append(('ground', v3r._ground_shadow_strokes(),
               (0, 0.52), 1.0, slot))
    lbl = label.replace('_', ' ').title()
    tw_ = text_width(lbl, 0.16)
    cap = text_strokes(lbl, (-tw_ / 2, 0.56), 0.16, 'ink', 0.95)
    if cap:
        gs.append(('caption', [(p, c, ws, f, False)
                               for p, c, ws, f, *_ in cap],
                   (0, 0), 1.0, slot))
    xs = [q[0] for g in gs for s_ in g[1] for q in s_[0] if len(q) > 1]
    ys = [q[1] for g in gs for s_ in g[1] for q in s_[0] if len(q) > 1]
    b = (min(xs) if xs else -0.4, min(ys) if ys else -0.5,
         max(xs) if xs else 0.4, max(ys) if ys else 0.5)
    return {'groups': [(g, 0.0, 1.0) for g in gs],
            'bounds': b, 'label': label, 'w': b[2] - b[0],
            'h': b[3] - b[1], 'bi': beat_i}


def _is_person_item(it):
    return any(g[4] is not None and g[4].get('icon') in ('person', 'agent')
               for g, _s, _e in it['groups'])


def _bundle_scene_groups(scene, plan, ratio, beat=None):
    """_scene_groups minus the zone headline, merged into element bundles
    (icon+caption, person+prop cluster) — same model the journey uses."""
    groups = v3r._scene_groups(scene, plan, ratio)
    merged = []          # list of items {groups:[(g,s,e)], label}
    person_key = None
    for g, s, e in groups:
        if g[0] in ('headline',):
            continue
        slot = g[4]
        key = (id(slot) if slot is not None else ('free', len(merged)))
        placed = None
        if slot is not None:
            placed = next((it for it in merged if it['key'] == key), None)
        if placed is None:
            # relation arrows/solo marks attach to the previous element
            if g[0] == 'arrow' and merged:
                merged[-1]['groups'].append((g, s, e))
                continue
            placed = {'key': key, 'groups': [], 'label':
                      (slot or {}).get('label', '') if slot else ''}
            merged.append(placed)
        placed['groups'].append((g, s, e))
    # merge each prop cluster into its nearest person cluster
    # (interaction composition) — multi-person scenes pair by proximity.
    # Storyboard quadrants keep items separate so each element draws and
    # places as its own vignette satellite.
    persons = [it for it in merged if _is_person_item(it)]
    sb_merge_off = (plan.get('board_layout') == 'storyboard')
    if persons and len(merged) > len(persons) and not sb_merge_off:
        def _cx(it):
            xs = [q[0] for g, _s, _e in it['groups']
                  for st in g[1] for q in st[0] if len(q) > 1]
            return sum(xs) / len(xs) if xs else 0.0
        # running caption floor per person — each merged caption stacks
        # below whatever sits lowest so labels never share a baseline
        cap_floor = {}
        for p in persons:
            pc = next((g3 for g3 in p['groups'] if g3[0][0] == 'caption'),
                      None)
            cap_floor[id(p)] = (
                max(p_[1] for st in pc[0][1] for p_ in st[0] if len(p_) > 1)
                if pc is not None else None)
        for it in list(merged):
            if _is_person_item(it):
                continue
            host = min(persons,
                       key=lambda p: abs(_cx(p) - _cx(it)))
            for g, s, e in it['groups']:
                if g[0] == 'caption':
                    # chip boxes stay beside their own icon inside the
                    # cluster; plain labels stack under the figure
                    is_chip = bool(g[4] and g[4].get('chip'))
                    drop = g[2][1] * 0.6 + g[3] * 0.4
                    floor_ = cap_floor.get(id(host))
                    if floor_ is not None and not is_chip:
                        cmin = min(p_[1] for st in g[1]
                                   for p_ in st[0] if len(p_) > 1)
                        cmax0 = max(p_[1] for st in g[1]
                                    for p_ in st[0] if len(p_) > 1)
                        drop = floor_ - cmin + 10.0
                        cap_floor[id(host)] = (cmax0 + drop
                                               + (cmax0 - cmin) * 0.5)
                    st2 = [([(p_[0], p_[1] + drop) for p_ in st[0]
                             if len(p_) > 1],) + tuple(st[1:])
                           for st in g[1]]
                    host['groups'].append(
                        ((g[0], st2, g[2], g[3], g[4]), s, e))
                else:
                    host['groups'].append((g, s, e))
            merged.remove(it)
    # upgrade authored people to the paper-cast figure their label maps to
    for it in merged:
        if _is_person_item(it):
            # the animated mocap figure owns this slot — keep its group
            # strokeless so the drawn icon doesn't fight the overlay
            if any(g[4] is scene.get('_fm_slot')
                   or g[4] is scene.get('_fm2_slot')
                   for g, _s, _e in it['groups']):
                continue
            lbl = ''
            for g, _s, _e in it['groups']:
                if g[4] and g[4].get('label'):
                    lbl = g[4]['label']
                    break
            cid = _papercast_for(lbl)
            if cid:
                st = _papercast_strokes(cid)
                if st:
                    ng = []
                    for g, s, e in it['groups']:
                        if g[0] == 'icon':
                            ng.append((('icon', st, (0, 0), 1.0, g[4]),
                                       s, e))
                        else:
                            ng.append((g, s, e))
                    it['groups'] = ng
                    xs_ = [q[0] for s_ in st for q in s_[0]
                           if len(q) > 1]
                    ys_ = [q[1] for s_ in st for q in s_[0]
                           if len(q) > 1]
                    if xs_ and ys_:
                        it['bounds'] = (min(xs_), min(ys_),
                                        max(xs_), max(ys_))
                    it['w'] = it['bounds'][2] - it['bounds'][0]
                    it['h'] = it['bounds'][3] - it['bounds'][1]
    # character situations: the narration names an actor but no figure was
    # drawn — inject a situational peep (the reference is full of them)
    if not any(_is_person_item(it) for it in merged):
        w = _agent_word(beat or {})
        if w:
            merged.insert(0, _person_item(w, 0))
    # text only where it's intended: figures get name labels; authored
    # chip/label elements keep theirs; everything else draws bare
    for it in merged:
        if not _is_person_item(it):
            keep = any(g[0] == 'caption' and g[4] and g[4].get('chip')
                       for g, _s, _e in it['groups'])
            if not keep:
                it['groups'] = [ge for ge in it['groups']
                                if ge[0][0] != 'caption']
    # the reference idiom is still figures + clean items — motion-mark
    # scribbles read as noise here, so this mode drops them
    for it in merged:
        it['groups'] = [ge for ge in it['groups'] if ge[0][0] != 'marks']
    # long captions -> speech bubble wrapping the text
    for it in merged:
        for gi, (g, s, e) in enumerate(it['groups']):
            if g[0] == 'caption' and len(str(it['label']).split()) >= 5:
                bb = _group_world_bounds(g)
                cw_, ch_ = bb[2] - bb[0], bb[3] - bb[1]
                bc = ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2)
                art = next((gb for gb in it['groups'] if gb[0][0] == 'icon'),
                           None)
                tail = (bc[0], bc[1] + ch_ * 2.2)
                if art is not None:
                    ab = _group_world_bounds(art[0])
                    tail = (bc[0] + (ab[0] - bc[0]) * 0.15, ab[1])
                pad = ch_ * 0.9
                bstr = _bubble_box(bc, cw_ + pad * 2, ch_ + pad * 1.6, tail)
                it['groups'][gi] = (
                    ('caption', bstr + list(g[1]), g[2], g[3], g[4]), s, e)
    return merged


def _build(plan, ratio):
    """Precompute boards/sections/items/timing; cached per plan+ratio."""
    cache = plan.setdefault('_bs_flow', {})
    if ratio in cache:
        return cache[ratio]
    beats = plan['beats']
    scenes = plan['sceneSpecs']
    vw, vh = wbp.RATIO_SIZES[ratio]
    scale = _map_scale(ratio)
    W, H = vw / scale, vh / scale
    m = 0.045 * W
    board_rect = (-W / 2 + m, -H / 2 + m * 1.4, W - 2 * m, H - 2 * m * 1.6)

    sections = []
    for bi, (beat, scene) in enumerate(zip(beats, scenes)):
        merged = _bundle_scene_groups(scene, plan, ratio, beat)
        for it in merged:
            b = None
            for g, _s, _e in it['groups']:
                gb = _group_world_bounds(g)
                if gb[0] >= gb[2] and g[4] and g[4].get('sprite'):
                    # animated-sprite slots carry no strokes — size the item
                    # from the slot's box so placement doesn't collapse it
                    sh = max(30.0, float(g[3] or 60.0)) * 0.5
                    gb = (g[2][0] - sh, g[2][1] - sh,
                          g[2][0] + sh, g[2][1] + sh)
                b = gb if b is None else (min(b[0], gb[0]), min(b[1], gb[1]),
                                          max(b[2], gb[2]), max(b[3], gb[3]))
            it['bounds'] = b
        sections.append({'beat': beat, 'bi': bi, 'items': merged,
                         'label': _section_label(beat)})

    # One layout under a locked camera (no pans, zooms, or drift): every
    # beat composes its own full-frame scene; the previous scene's ink
    # fades off as the next opens. `board_layout: 'storyboard'` is a
    # TREATMENT, not a different layout — the beat still owns the whole
    # frame, but its title gets the numbered pastel swash, a subtitle line,
    # and a bottom quote caption, storyboard-panel style.
    storyboard = str(plan.get('board_layout') or '') == 'storyboard'
    del board_rect
    nsec = len(sections)
    m2 = 0.04 * W
    bx0, by0 = -W / 2 + m2, -H / 2 + m2 * 1.15
    bw, bh = W - 2 * m2, H - 2 * m2 * 1.45
    board_rect = (bx0, by0, bw, bh)
    header = bh * (0.15 if storyboard else 0.10)
    ax0, ay0, aw, ah = bx0, by0 + header, bw, bh - header
    rw_, rh_ = aw, ah
    regions = [(ax0, ay0, rw_, rh_)] * nsec
    divs = []
    if storyboard:
        # yellow corner rays flanking the masthead (the reference's accent
        # doodles) — the only persistent board chrome; no panel dividers
        for k, (rcx_, dirx) in enumerate(((ax0 + aw * 0.012, 1),
                                          (ax0 + aw * 0.988, -1))):
            for j in range(3):
                a_ = math.radians(-25 - j * 30)
                x0_, y0_ = rcx_, by0 + header * 0.72
                seg = [(x0_ + math.cos(a_) * dirx * 16,
                        y0_ + math.sin(a_) * 16),
                       (x0_ + math.cos(a_) * dirx * 38,
                        y0_ + math.sin(a_) * 38)]
                divs.append((('divider', [(seg, 'a_yellow', 1.4, False,
                                           True)], (0, 0), 1.0, None),
                             0.25 + j * 0.08, 0.45 + j * 0.08))
    uid = 0

    # board title drawn once, top-left — the persistent anchor text
    raw = str(plan.get('title') or plan.get('production_id')
              or 'WHITEBOARD')
    raw = re.sub(r'(?i)^nexmind_(whiteboard|diagram|kinetic)_?v?\d*_?',
                 '', raw)
    raw = re.sub(r'(?i)_?(demo|reel|v\d+)$', '', raw).strip('_ ')
    title = raw.replace('_', ' ').title() or 'WHITEBOARD'
    first_t0 = sections[0]['beat']['start_seconds']
    if storyboard:
        # storyboard headline: big centered title across the top strip with
        # a yellow underline swash (the reference's masthead)
        th_ = min(header * 0.58, 110.0)
        tw_ = text_width(title, th_)
        if tw_ > bw * 0.92:
            th_ *= bw * 0.92 / tw_
            tw_ = text_width(title, th_)
        tx_ = bx0 + bw / 2 - tw_ / 2
        ty_ = by0 + header * 0.10
        title_st = text_strokes(title, (tx_, ty_), th_, 'ink', 1.15)
        und = _wobble_line((tx_ + tw_ * 0.02, ty_ + th_ * 1.15),
                           (tx_ + tw_ * 0.98, ty_ + th_ * 1.15),
                           n=32, wob=1.8, seed=9)
        title_st = title_st + [(und, 'a_yellow', 2.2, False, True)]
    else:
        th_ = min(header * 0.62, 96.0)
        tw_ = text_width(title, th_)
        if tw_ > bw * 0.24:
            th_ *= bw * 0.24 / tw_
        title_st = text_strokes(title, (bx0 + bw * 0.012,
                                        by0 + header * 0.16),
                                th_, 'ink', 1.15)
    title_item = {'groups': [(('plabel',
        [(p, c, ws, False, True) for p, c, ws, *_ in title_st],
        (0, 0), 1.0, None), first_t0, first_t0 + 1.6)],
        'kind': 'title', 'uid': -1, 'fade': None,
        'bounds2': (bx0, by0, bx0 + bw, by0 + header)}

    for si, sec in enumerate(sections):
        t0 = sec['beat']['start_seconds']
        t1 = t0 + float(sec['beat'].get('duration_seconds', 3.0))
        sec['t_window'] = (t0, t1)
        dur = t1 - t0
        rx, ry, rw, rh = regions[si]
        sec['region'] = (rx, ry, rw, rh)
        placed_bounds = []            # each scene lays out from a clean
                                      # frame — no carryover from prior
                                      # scenes' placements
        # per-section title — lettered at the top of the region it owns;
        # storyboard mode puts a pastel swash band behind the numbered
        # heading and an optional one-line subtitle under it
        ttl = str(sec['beat'].get('title') or sec.get('label') or '').strip()
        sw_col = _SWASH[si % len(_SWASH)]
        title_h = 0.0
        if ttl:
            th2 = min(rh * (0.15 if storyboard else 0.115), 120.0)
            if text_width(ttl, th2) > rw * 0.8:
                th2 *= rw * 0.8 / text_width(ttl, th2)
            tts = text_strokes(ttl, (rx + rw * 0.05, ry + rh * 0.05),
                               th2, 'ink', 1.2)
            tts += [([(px + th2 * 0.045, py + th2 * 0.02)
                      for px, py in s[0]], s[1], s[2], s[3], s[4])
                    for s in list(tts)]
            if storyboard:
                tw2 = text_width(ttl, th2)
                bx_0 = rx + rw * 0.05 - th2 * 0.22
                band = [(bx_0, ry + rh * 0.05 - th2 * 0.15),
                        (bx_0 + tw2 + th2 * 0.5,
                         ry + rh * 0.05 - th2 * 0.15),
                        (bx_0 + tw2 + th2 * 0.5,
                         ry + rh * 0.05 + th2 * 1.25),
                        (bx_0, ry + rh * 0.05 + th2 * 1.25),
                        (bx_0, ry + rh * 0.05 - th2 * 0.15)]
                # swash band inks first, then the heading letters on it
                tts = [(band, sw_col, 1.0, 'solid', True)] + tts
                sub = str(sec['beat'].get('subtitle') or '').strip()
                if sub:
                    sh2 = th2 * 0.40
                    tts += text_strokes(sub, (rx + rw * 0.05,
                                              ry + rh * 0.05 + th2 * 1.5),
                                        sh2, 'ink', 0.9)
            sec['title_st'] = tts
            title_h = (th2 * 1.32 + rh * 0.02 if storyboard
                       else th2 * 1.5 + rh * 0.04)
        # bottom caption strip (storyboard quote line) is reserved so items
        # never land on it
        cap = str(sec['beat'].get('caption') or '').strip()
        cap_h = rh * 0.13 if (storyboard and cap) else 0.0
        # content rect inside the region, clear of its title strip
        cx0 = rx + rw * 0.05
        cy0 = ry + (rh * 0.03 if storyboard else rh * 0.04) + title_h
        cw = rw * 0.90
        ch = (ry + rh * 0.985 if storyboard else ry + rh * 0.97) - cy0 - cap_h
        sec['content'] = (cx0, cy0, cw, ch)
        items = sec['items']
        k = len(items)
        # figure strips claim the scene edges before any item lands so
        # satellites keep clear of where a drawn figure will stand — but
        # only when the beat actually stages a person item; a figure never
        # appears on its own
        fsc = scenes[sec['bi']] if sec['bi'] < len(scenes) else {}
        has_person = any(_is_person_item(it) for it in items)
        fm_bounds = {}
        if has_person and fsc.get('figureMotion'):
            fm_bounds['fm'] = (cx0, cy0 + ch * 0.03,
                               cx0 + cw * 0.32, cy0 + ch * 0.99)
            placed_bounds.append(fm_bounds['fm'])
        if has_person and fsc.get('figureMotion2'):
            fm_bounds['fm2'] = (cx0 + cw * 0.68, cy0 + ch * 0.03,
                                cx0 + cw, cy0 + ch * 0.99)
            placed_bounds.append(fm_bounds['fm2'])
        # scene separation: everything this scene places fades off the
        # paper as the next scene opens
        nxt_t0 = (beats[sec['bi'] + 1]['start_seconds']
                  if sec['bi'] + 1 < len(beats) else None)
        sec['fade'] = ((nxt_t0 - 0.15, nxt_t0 + 0.45)
                       if nxt_t0 is not None
                       else (t1, t1 + WIPE_SECONDS * 0.8))
        if not k:
            sec['items2'] = []
            continue
        # title draws first, then items ink one at a time in beat order
        lead = min(0.9, dur * 0.15) if ttl else 0.0
        slot_dur = max(0.35, (dur - lead) / k)
        rcx, rcy = cx0 + cw / 2, cy0 + ch / 2
        # vignette composition: heaviest element is the hero at the centre;
        # the rest ring it as satellites. Placement order is by weight but
        # draw order stays authored.
        weights = []
        for j, it in enumerate(items):
            person = _is_person_item(it)
            aw_ = next((float(g[4]['wgt']) for g, _s, _e in it['groups']
                        if g[4] and g[4].get('wgt')), 1.0)
            weights.append((1.9 if person else (1.35 if j == 0 else 0.78))
                           * aw_)
        p_order = sorted(range(k), key=lambda j: -weights[j])
        sat_pts = [
            (rcx, rcy),
            (cx0 + cw * 0.27, cy0 + ch * 0.30),
            (cx0 + cw * 0.73, cy0 + ch * 0.30),
            (cx0 + cw * 0.25, cy0 + ch * 0.72),
            (cx0 + cw * 0.75, cy0 + ch * 0.72),
            (rcx, cy0 + ch * 0.18),
            (rcx, cy0 + ch * 0.84),
            (cx0 + cw * 0.12, cy0 + ch * 0.52),
            (cx0 + cw * 0.88, cy0 + ch * 0.52),
            (rcx, cy0 + ch * 0.52),
        ]
        placed = [None] * k
        pt_i = 1   # index 0 is the hero's centre — satellites start at 1
        hero_bb = None
        for j in p_order:
            it = items[j]
            uid += 1
            person = _is_person_item(it)
            b = it['bounds']
            w = max(30.0, b[2] - b[0])
            h = max(30.0, b[3] - b[1])
            bcx, bcy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
            hero = (j == p_order[0])
            # hero fills ~60% of the region, satellites ~30% — a tight size
            # band keeps every element at a readable, uniform weight
            fw = cw * ((0.55 if storyboard else 0.60) if hero
                       else (0.40 if person else
                             (0.36 if storyboard else 0.32)))
            fh = ch * ((0.85 if storyboard else 0.66) if hero
                       else (0.62 if person else
                             (0.52 if storyboard else 0.34)))
            bo2 = min(fw / w, fh / h)
            if hero:
                cands = [sat_pts[0]]
            else:
                # satellites anchor adjacent to the hero's edges first —
                # the reference's composed scene — then fall back to the
                # wider ring when the close spots are blocked
                anchors = []
                if hero_bb is not None:
                    hx0, hy0, hx1, hy1 = hero_bb
                    hcx, hcy = (hx0 + hx1) / 2, (hy0 + hy1) / 2
                    gap = cw * 0.055
                    anchors = [
                        (hx0 - gap - w * bo2 / 2, hcy - rh * 0.10),
                        (hx1 + gap + w * bo2 / 2, hcy - rh * 0.10),
                        (hx0 - gap - w * bo2 / 2, hcy + rh * 0.16),
                        (hx1 + gap + w * bo2 / 2, hcy + rh * 0.16),
                        (hcx, hy1 + gap + h * bo2 / 2),
                        (hcx, hy0 - gap - h * bo2 / 2),
                    ]
                cands = anchors + sat_pts[pt_i:] + sat_pts[:pt_i]
                pt_i = (pt_i % (len(sat_pts) - 1)) + 1
            pad = cw * 0.05
            best = None
            for px, py in cands:
                scale = 1.0
                for _try in range(8):
                    bb = (px - w * bo2 * scale / 2, py - h * bo2 * scale / 2,
                          px + w * bo2 * scale / 2, py + h * bo2 * scale / 2)
                    hit = (bb[0] < cx0 + cw * 0.02 or bb[2] > cx0 + cw * 0.98
                           or bb[1] < cy0 + ch * 0.02
                           or bb[3] > cy0 + ch * 0.98)
                    for ob in placed_bounds:
                        if not (bb[2] + pad <= ob[0] or bb[0] - pad >= ob[2]
                                or bb[3] + pad <= ob[1]
                                or bb[1] - pad >= ob[3]):
                            hit = True
                            break
                    if not hit:
                        break
                    scale *= 0.87
                if best is None or scale > best[2]:
                    best = (px, py, scale)
                    if scale >= 0.98:
                        break
            px, py, scale = best
            bo2 *= scale
            sx, sy = px, py
            it['bounds2'] = (sx - w * bo2 / 2, sy - h * bo2 / 2,
                             sx + w * bo2 / 2, sy + h * bo2 / 2)
            placed_bounds.append(it['bounds2'])
            if hero:
                hero_bb = it['bounds2']
            it['uid'] = uid
            it['fade'] = None
            moved = []
            flip = (person and sx > rcx and
                    not any((g[4] or {}).get('facing', 1) < 0
                            for g, _s, _e in it['groups']))
            # organic tilt: art sits at a slight random angle (the
            # reference's hand-placed look); text stays level for legibility
            tang = (((uid * 2654435761) % 1000) / 1000 - 0.5) * 0.06
            tca, tsa = math.cos(tang), math.sin(tang)

            def _tilt(x, y):
                return (sx + (x - sx) * tca - (y - sy) * tsa,
                        sy + (x - sx) * tsa + (y - sy) * tca)
            for g, s, e in it['groups']:
                kind, strokes, center, size, slot = g
                # captions/labels stay unmirrored — text must read left->right
                gflip = flip and kind not in ('caption', 'plabel')
                tilt = kind not in ('caption', 'plabel')
                st2 = []
                for st in strokes:
                    if len(st) > 4 and st[4]:
                        st2.append((
                            [(_tilt(sx + ((bcx - px_) if gflip
                                          else (px_ - bcx)) * bo2,
                                    sy + (py_ - bcy) * bo2)
                              if tilt else
                              (sx + ((bcx - px_) if gflip
                                     else (px_ - bcx)) * bo2,
                               sy + (py_ - bcy) * bo2))
                             for px_, py_ in st[0]],) + tuple(st[1:]))
                    elif gflip:
                        st2.append((([(-q[0], q[1])
                                      if len(q) > 1 else q
                                      for q in st[0]]),) + tuple(st[1:]))
                    else:
                        st2.append(st)
                mc = (sx + ((bcx - center[0]) if gflip
                            else (center[0] - bcx)) * bo2,
                      sy + (center[1] - bcy) * bo2)
                if tilt:
                    mc = _tilt(*mc)
                moved.append(((kind, _remap_strokes(st2), mc,
                               size * bo2, slot), s, e))
            it['groups'] = moved
            # the element inks across its slice of the beat, after the
            # title — paused tail: drawing uses ~85% of the slot so the hand
            # breathes between elements like the reference's pacing
            it0 = t0 + lead + j * slot_dur
            it1 = it0 + slot_dur
            itd = it0 + slot_dur * 0.85
            it['groups'] = [
                (g, it0 + _SLICE_SPAN.get(g[0], (0.0, 1.0))[0]
                    * (itd - it0),
                 it0 + _SLICE_SPAN.get(g[0], (0.0, 1.0))[1]
                    * (itd - it0))
                for g, _s, _e in it['groups']]
            it['t_window'] = (it0, it1)
            it['kind'] = 'elem'
            fm_slot = (scenes[sec['bi']].get('_fm_slot')
                       if sec['bi'] < len(scenes) else None)
            fm2_slot = (scenes[sec['bi']].get('_fm2_slot')
                        if sec['bi'] < len(scenes) else None)
            for fkey, fslot in (('fm', fm_slot), ('fm2', fm2_slot)):
                if (fslot is not None and fkey not in sec
                        and any(g[4] is fslot
                                for g, _s, _e in it['groups'])):
                    fx0, fy0, fx1, fy1 = it['bounds2']
                    # the claimed slot left an empty group — give the figure
                    # its region-edge strip when the bounds stay degenerate
                    if fx1 - fx0 < cw * 0.16 or fy1 - fy0 < ch * 0.28:
                        strip = fm_bounds.get(fkey)
                        if strip is not None:
                            fx0, fy0, fx1, fy1 = strip
                        else:
                            fx0, fy0 = cx0, cy0 + ch * 0.03
                            fx1, fy1 = cx0 + cw * 0.32, cy0 + ch * 0.99
                        it['bounds2'] = (fx0, fy0, fx1, fy1)
                        if placed_bounds:
                            placed_bounds[-1] = it['bounds2']
                    fy0 = max(fy0, cy0)
                    # feet land on the drawn ground shadow, not the cell floor
                    gnd = next((g[2] for g, _s, _e in it['groups']
                                if g[0] == 'ground'), None)
                    if gnd is not None:
                        fy1 = gnd[1] + rh * 0.02
                    sec[fkey] = {'bounds2': (fx0, fy0, fx1, fy1),
                                 't0': it0 - t0,
                                 'facing': fslot.get('facing', 1)}
                    # the slot's caption anchors under the figure's feet,
                    # not the degenerate point the slot occupied; multiple
                    # captions stack downward instead of sharing a baseline
                    fbx = sec[fkey]['bounds2']
                    cfloor = fbx[3]
                    for g2, s2, e2 in it['groups']:
                        if g2[0] != 'caption':
                            continue
                        cb = _group_world_bounds(g2)
                        cdx = (fbx[0] + fbx[2]) / 2 - (cb[0] + cb[2]) / 2
                        cdy = cfloor + (cb[3] - cb[1]) * 0.25 - cb[1]
                        g2[1][:] = [
                            ([(p_[0] + cdx, p_[1] + cdy)
                              for p_ in st2[0]],) + tuple(st2[1:])
                            for st2 in g2[1]]
                        cfloor = cb[3] + cdy + (cb[3] - cb[1]) * 0.35
                        it['bounds2'] = (min(it['bounds2'][0], cb[0] + cdx),
                                         min(it['bounds2'][1], cb[1] + cdy),
                                         max(it['bounds2'][2], cb[2] + cdx),
                                         max(it['bounds2'][3], cb[3] + cdy))
                        if placed_bounds:
                            placed_bounds[-1] = it['bounds2']
            placed[j] = it
        # connective tissue: people and tagged props get a curved arrow to
        # the hero — the reference's actor->object / tag->object links
        hero_it = placed[p_order[0]] if p_order and placed else None
        if hero_it is not None and hero_it.get('bounds2'):
            hc = ((hero_it['bounds2'][0] + hero_it['bounds2'][2]) / 2,
                  (hero_it['bounds2'][1] + hero_it['bounds2'][3]) / 2)
            arrows = 0
            for it in placed:
                if (it is None or it is hero_it or it.get('bounds2') is None
                        or arrows >= 2):
                    continue
                wants = (_is_person_item(it)
                         or any(g[4] and g[4].get('chip')
                                for g, _s, _e in it['groups']))
                if not wants:
                    continue
                sb = it['bounds2']
                sc_ = ((sb[0] + sb[2]) / 2, (sb[1] + sb[3]) / 2)
                p0 = _edge_pt(sb, hc)
                p1 = _edge_pt(hero_it['bounds2'], sc_)
                if math.hypot(p1[0] - p0[0], p1[1] - p0[1]) < cw * 0.10:
                    continue
                arr = _curved_arrow(p0, p1)
                i0_, i1_ = it['t_window']
                it['groups'].append((
                    ('arrow', arr, (0, 0), 1.0, None),
                    i0_ + (i1_ - i0_) * 0.86,
                    i0_ + (i1_ - i0_) * 1.06))
                arrows += 1
        # gap-fill: sparse regions get a sparkle doodle in their emptiest
        # corner — the reference never leaves dead zones
        doodles = []
        if k:
            occ = 0.0
            for it in placed:
                if it is not None and it.get('bounds2'):
                    b = it['bounds2']
                    occ += max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
            for strip in fm_bounds.values():
                occ += (strip[2] - strip[0]) * (strip[3] - strip[1]) * 0.4
            if occ < cw * ch * 0.38:
                corners = [(cx0 + cw * 0.13, cy0 + ch * 0.14),
                           (cx0 + cw * 0.87, cy0 + ch * 0.14),
                           (cx0 + cw * 0.13, cy0 + ch * 0.86),
                           (cx0 + cw * 0.87, cy0 + ch * 0.86)]

                def _far(pt):
                    d = 1e9
                    for ob in placed_bounds:
                        ocx, ocy = (ob[0] + ob[2]) / 2, (ob[1] + ob[3]) / 2
                        d = min(d, math.hypot(pt[0] - ocx, pt[1] - ocy))
                    return d
                spot = max(corners, key=_far)
                s_ = rh * 0.05
                uid += 1
                ds, de = t0 + dur * 0.80, t0 + dur * 0.97
                doodles.append({
                    'groups': [(('marks', _sparkle(spot, s_), (0, 0), 1.0,
                                 None), ds, de)],
                    'bounds2': (spot[0] - s_, spot[1] - s_,
                                spot[0] + s_, spot[1] + s_),
                    'uid': uid, 'fade': None, 'kind': 'elem',
                    't_window': (ds, de)})
                placed_bounds.append(doodles[-1]['bounds2'])
        fade = sec['fade']
        for it in placed:
            if it is not None:
                it['fade'] = fade
        for d in doodles:
            d['fade'] = fade
        sec['items2'] = [it for it in placed if it is not None] + doodles
        # storyboard quote caption: centered at the bottom of the quadrant
        # with a swash-colored wobble underline, inking late in the beat
        if storyboard and cap:
            ch_ = rh * 0.078
            cw_ = text_width(cap, ch_)
            if cw_ > rw * 0.92:
                ch_ *= rw * 0.92 / cw_
                cw_ = text_width(cap, ch_)
            cxs = rx + rw / 2 - cw_ / 2
            cys = ry + rh * 0.97 - ch_ * 1.5
            cst = text_strokes(cap, (cxs, cys), ch_, 'ink', 1.0)
            und2 = _wobble_line((cxs + cw_ * 0.04, cys + ch_ * 1.35),
                                (cxs + cw_ * 0.96, cys + ch_ * 1.35),
                                n=24, wob=1.6, seed=si * 13 + 5)
            cst.append((und2, sw_col, 1.9, False, True))
            uid += 1
            ct0 = t1 - dur * 0.24
            sec['items2'].append({
                'groups': [(('plabel', cst, (0, 0), 1.0, None),
                            ct0, t1 - dur * 0.02)],
                'bounds2': (cxs, cys, cxs + cw_, cys + ch_ * 1.4),
                'uid': uid, 'fade': fade, 'kind': 'elem',
                't_window': (ct0, t1 - dur * 0.02)})

    out_sections = sections
    all_items = [it for sec in out_sections for it in sec['items2']]

    total_beats_end = beats[-1]['start_seconds'] + beats[-1]['duration_seconds']
    # ending: scenes mode fades the last scene off then inks "Thanks" +
    # heart on the empty board; storyboard mode just holds the completed
    # board (the finished quadrants ARE the ending image)
    th_cx, th_cy = bx0 + bw * 0.42, by0 + bh * 0.52
    th_h = rh_ * 0.30
    th_w = text_width('Thanks', th_h)
    if th_w > rw_ * 0.72:
        th_h *= rw_ * 0.72 / th_w
        th_w = text_width('Thanks', th_h)
    th = text_strokes('Thanks', (th_cx - th_w / 2, th_cy - th_h / 2),
                      th_h, 'ink', 1.3)
    hx = th_cx + th_w / 2 + th_h * 0.62
    if hx + th_h * 0.5 > bx0 + bw:
        hx = th_cx - th_w / 2 - th_h * 0.62
    heart = _heart_strokes((hx, th_cy + th_h * 0.02), th_h * 0.8)
    ending = {
        'wipe_t0': total_beats_end,
        'thanks_t0': total_beats_end + WIPE_SECONDS,
        'montage_t0': total_beats_end + WIPE_SECONDS + THANKS_SECONDS,
        'thanks': [('thanks', th, (0, 0), 1.0, None),
                   ('heart', heart, (0, 0), 1.0, None)],
        'montage': [],
        'dur': WIPE_SECONDS + THANKS_SECONDS + END_HOLD,
    }
    flow = {'sections': out_sections, 'items': all_items,
            'title_item': title_item, 'ending': ending,
            'dividers': divs, 'persist': False,
            'board_rect': board_rect,
            'total_beats_end': total_beats_end}
    cache[ratio] = flow
    return flow


def _sparkle(c, s):
    """4-point star doodle in world space."""
    pts = [(c[0], c[1] - s), (c[0] + s * 0.3, c[1] - s * 0.3),
           (c[0] + s, c[1]), (c[0] + s * 0.3, c[1] + s * 0.3),
           (c[0], c[1] + s), (c[0] - s * 0.3, c[1] + s * 0.3),
           (c[0] - s, c[1]), (c[0] - s * 0.3, c[1] - s * 0.3),
           (c[0], c[1] - s)]
    return [(pts, 'a_yellow', 1.0, False, True)]


def _travel_tip(flow, ratio, cam, zoom, t):
    """Between draw actions the hand glides to the next element's start —
    the reference's visible hand travel instead of a teleport."""
    segs = []

    def _wpt(g, st, idx):
        q = st[0][idx]
        if len(st) > 4 and st[4]:
            return q
        return (g[2][0] + q[0] * g[3], g[2][1] + q[1] * g[3])

    def _add(groups):
        for g, s, e in groups:
            if s is None or e is None:
                continue
            sts = [st for st in g[1] if st and st[0]]
            if not sts:
                continue
            segs.append((s, e, _wpt(g, sts[0], 0), _wpt(g, sts[-1], -1)))
    _add(flow['title_item']['groups'])
    for it in flow['items']:
        _add(it['groups'])
    for dg, s, e in flow.get('dividers') or []:
        sts = [st for st in dg[1] if st and st[0]]
        if sts:
            segs.append((s, e, sts[0][0][0], sts[-1][0][-1]))
    for sec in flow['sections']:
        if sec.get('title_st') and sec.get('t_window'):
            st_ = sec['title_st']
            segs.append((sec['t_window'][0], sec['t_window'][0] + 1.1,
                         st_[0][0][0], st_[-1][0][-1]))
    prev, nxt = None, None
    for s, e, p0, p1 in segs:
        if e <= t and (prev is None or e > prev[0]):
            prev = (e, p1)
        if s > t and (nxt is None or s < nxt[0]):
            nxt = (s, p0)
    if nxt is None:
        return None
    if prev is None or prev[0] >= nxt[0]:
        tip_w = nxt[1]
    else:
        f = wbp._ease(wbp._clamp((t - prev[0]) / max(0.05, nxt[0] - prev[0])))
        tip_w = (prev[1][0] + (nxt[1][0] - prev[1][0]) * f,
                 prev[1][1] + (nxt[1][1] - prev[1][1]) * f)
    sx, sy = wbp._map_point(tip_w, cam, ratio, zoom)
    # off-view travel means the hand is out of frame — it re-enters with the
    # next in-view element rather than pinning to the edge
    vw, vh = wbp.RATIO_SIZES[ratio]
    if not (-40 <= sx <= vw + 40 and -40 <= sy <= vh + 40):
        return None
    return (sx, sy)


def _camera_at(flow, ratio, t):
    """Locked camera — the whole board stays framed edge to edge for the
    entire video. No pans, no zoom, no drift."""
    vw, vh = wbp.RATIO_SIZES[ratio]
    base = _map_scale(ratio)
    bx, by, bw, bh = flow['board_rect']
    full_z = min(vw * 0.97 / bw, vh * 0.97 / bh) / base
    return (bx + bw / 2, by + bh / 2), full_z


def ending_seconds(plan, ratio):
    return _build(plan, ratio)['ending']['dur']


def render_board_frame(plan: dict, ratio: str, t: float):
    """Locked camera on the region canvas — the whole board is framed
    edge to edge for the entire render."""
    flow = _build(plan, ratio)
    colors = _colors(plan)
    vw, vh = wbp.RATIO_SIZES[ratio]
    cam, zoom = _camera_at(flow, ratio, t)
    seed = 11
    layer = Image.new('RGBA', (vw, vh), (0, 0, 0, 0))
    tip = None
    t_end = flow['total_beats_end']
    pal = wbp._pal(plan)

    def draw_groups(groups, base_seed, onto=None):
        nonlocal tip
        tgt = layer if onto is None else onto
        for g, s, e in groups:
            p = wbp._ease(wbp._clamp((t - s) / max(0.05, e - s)))
            if p <= 0:
                continue
            t2 = _draw_strokes(tgt, g[1], g[2], g[3], cam, colors,
                               ratio, p, base_seed, zoom)
            if t2 and onto is None \
                    and -40 <= t2[0] <= vw + 40 and -40 <= t2[1] <= vh + 40:
                tip = t2

    def draw_full(groups, tgt):
        for g, _s, _e in groups:
            _draw_strokes(tgt, g[1], g[2], g[3], cam, colors,
                          ratio, 1.0, 0, zoom)

    persist = bool(flow.get('persist'))
    if t < t_end:
        fade_layers = []
        ti = flow['title_item']
        if t >= ti['groups'][0][1]:
            draw_groups(ti['groups'], seed)
        for dg, ds, de in flow.get('dividers') or []:
            dp = wbp._ease(wbp._clamp((t - ds) / max(0.05, de - ds)))
            if dp > 0:
                t2 = _draw_strokes(layer, dg[1], dg[2], dg[3], cam,
                                   colors, ratio, dp, seed + 3, zoom)
                if t2 and -40 <= t2[0] <= vw + 40 \
                        and -40 <= t2[1] <= vh + 40:
                    tip = t2
        for it in flow['items']:
            fade = it.get('fade')
            if fade is not None and t >= fade[1]:
                continue                     # fully faded off
            if fade is not None and t >= fade[0]:
                # fading out: draw complete ink onto its own layer
                fl = Image.new('RGBA', (vw, vh), (0, 0, 0, 0))
                draw_full(it['groups'], fl)
                p = wbp._clamp((t - fade[0]) / max(0.05, fade[1] - fade[0]))
                fade_layers.append((fl, int(255 * (1.0 - p))))
                continue
            draw_groups(it['groups'], seed + it['uid'] * 7)
        frame = _composite_frame(
            plan, ratio, cam, [(layer, 255)] + fade_layers, seed)
        spec_list = plan.get('sceneSpecs') or []
        for sec in flow['sections']:
            if not (sec.get('t_window') and sec['t_window'][0] <= t
                    and (persist or t < sec['t_window'][1] + 0.2)):
                continue
            if not (sec.get('fm') or sec.get('fm2')):
                continue
            scene_ = spec_list[sec['bi']] \
                if sec['bi'] < len(spec_list) else None
            if scene_ is None:
                continue
            for fkey in ('fm', 'fm2'):
                if not sec.get(fkey):
                    continue
                b2 = sec[fkey]['bounds2']
                # the figure is a protagonist, not a thumbnail — floor its
                # size at ~55% of the scene height
                fh = max(b2[3] - b2[1],
                         (sec['region'][3] if sec.get('region') else 300.0)
                         * 0.55)
                b2 = (b2[0], b2[3] - fh, b2[2], b2[3])
                scene_['_fm' + fkey[2:] + '_anchor'] = {
                    'center': ((b2[0] + b2[2]) / 2, (b2[1] + b2[3]) / 2),
                    'size': fh, 'facing': sec[fkey]['facing']}
                # the figure exists only inside its own scene — it exits
                # when the scene closes, never persisting into the next
                scene_['_fm' + fkey[2:] + '_window'] = (
                    sec[fkey]['t0'],
                    1e9 if persist else
                    sec['t_window'][1] - sec['t_window'][0] + 0.15)
            # the figure lives only inside its scene — the fm window ends
            # with the scene so it steps off as the scene fades
            frame = v3r._figure_motion_overlay(
                frame, scene_, plan, ratio, cam, zoom,
                t - sec['beat']['start_seconds'])
            # while a figure is being drawn the hand rides its outline tip —
            # but only when it's actually on the view screen: a figure
            # tracing in another region must not teleport the hand off-frame
            ft = scene_.pop('_fm_tip', None) or scene_.pop('_fm2_tip', None)
            if ft is not None and -40 <= ft[0] <= vw + 40 \
                    and -40 <= ft[1] <= vh + 40:
                tip = ft
        # section titles: a scene's title inks in as it opens and fades off
        # with the rest of that scene's ink
        for sec_ in flow['sections']:
            if not (sec_.get('title_st') and sec_.get('t_window')
                    and sec_['t_window'][0] <= t):
                continue
            sf = sec_.get('fade')
            alpha = 255
            if sf is not None and t >= sf[0]:
                if t >= sf[1]:
                    continue
                alpha = int(255 * (1.0 - wbp._clamp(
                    (t - sf[0]) / max(0.05, sf[1] - sf[0]))))
            tlayer = Image.new('RGBA', (vw, vh), (0, 0, 0, 0))
            p = wbp._ease(wbp._clamp(
                (t - sec_['t_window'][0]) / 1.1))
            if p <= 0:
                continue
            t2 = _draw_strokes(tlayer, sec_['title_st'], (0.0, 0.0), 1.0,
                               cam, colors, ratio, p,
                               seed + 71 + sec_['bi'] * 13, zoom)
            if alpha < 255:
                tlayer.putalpha(tlayer.split()[3].point(
                    lambda v: int(v * alpha / 255)))
            frame.paste(tlayer, (0, 0), tlayer)
            if t2 and sec_['t_window'][0] <= t <= sec_['t_window'][0] + 1.2 \
                    and -40 <= t2[0] <= vw + 40 and -40 <= t2[1] <= vh + 40:
                tip = t2
        if tip is None:
            tip = _travel_tip(flow, ratio, cam, zoom, t)
        return _vignette(_overlay_hand(frame, tip, ratio, t * 8 + seed),
                         ratio)

    # -------- ending --------
    ending = flow['ending']
    rel = t - t_end
    draw_full(flow['title_item']['groups'], layer)
    if persist:
        # storyboard: the finished quadrants ARE the ending — every stroke
        # and figure holds in place, the hand leaves the board
        for dg, _s, _e in flow.get('dividers') or []:
            _draw_strokes(layer, dg[1], dg[2], dg[3], cam, colors,
                          ratio, 1.0, seed + 3, zoom)
        for it in flow['items']:
            draw_full(it['groups'], layer)
        frame = _composite_frame(plan, ratio, cam, [(layer, 255)], seed)
        spec_list = plan.get('sceneSpecs') or []
        for sec in flow['sections']:
            if not (sec.get('t_window') and sec['t_window'][0] <= t):
                continue
            if not (sec.get('fm') or sec.get('fm2')):
                continue
            scene_ = spec_list[sec['bi']] \
                if sec['bi'] < len(spec_list) else None
            if scene_ is None:
                continue
            for fkey in ('fm', 'fm2'):
                if not sec.get(fkey):
                    continue
                b2 = sec[fkey]['bounds2']
                fh = max(b2[3] - b2[1],
                         (sec['region'][3] if sec.get('region') else 300.0)
                         * 0.55)
                b2 = (b2[0], b2[3] - fh, b2[2], b2[3])
                scene_['_fm' + fkey[2:] + '_anchor'] = {
                    'center': ((b2[0] + b2[2]) / 2, (b2[1] + b2[3]) / 2),
                    'size': fh, 'facing': sec[fkey]['facing']}
                scene_['_fm' + fkey[2:] + '_window'] = (sec[fkey]['t0'],
                                                       1e9)
            frame = v3r._figure_motion_overlay(
                frame, scene_, plan, ratio, cam, zoom,
                t - sec['beat']['start_seconds'])
        for sec_ in flow['sections']:
            if sec_.get('title_st'):
                _draw_strokes(frame, sec_['title_st'], (0.0, 0.0), 1.0,
                              cam, colors, ratio, 1.0,
                              seed + 71 + sec_['bi'] * 13, zoom)
        return _vignette(_overlay_hand(frame, None, ratio,
                                       t * 8 + seed), ratio)
    # scenes mode: the last scene has faded off; Thanks + heart draw
    # centred on the empty board
    # during the wipe window the outgoing scene's ink finishes its fade
    fade_layers = []
    for it in flow['items']:
        fade = it.get('fade')
        if fade is not None and fade[0] <= t < fade[1]:
            fl = Image.new('RGBA', (vw, vh), (0, 0, 0, 0))
            draw_full(it['groups'], fl)
            p = wbp._clamp((t - fade[0]) / max(0.05, fade[1] - fade[0]))
            fade_layers.append((fl, int(255 * (1.0 - p))))
    frame = _composite_frame(plan, ratio, cam,
                             [(layer, 255)] + fade_layers, seed)
    tt = rel - WIPE_SECONDS
    if tt > 0:
        elayer = Image.new('RGBA', (vw, vh), (0, 0, 0, 0))
        for gi, g in enumerate(ending['thanks']):
            p = wbp._ease(wbp._clamp(
                (tt - gi * 0.9) / max(0.2, THANKS_SECONDS - 0.9)))
            if p > 0:
                t2 = _draw_strokes(elayer, g[1], g[2], g[3], cam, colors,
                                   ratio, p, seed + 40 + gi, zoom)
                if t2:
                    tip = t2
        frame.paste(elayer, (0, 0), elayer)
    if tip is None:
        tip = _travel_tip(flow, ratio, cam, zoom, t)
    return _vignette(_overlay_hand(frame, tip, ratio, t * 8 + seed), ratio)
