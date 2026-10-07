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

from copy import deepcopy
import math
import re
import random
import textwrap

from PIL import Image

import whiteboard_pil_adapter as wbp
import v3_board_renderer as v3r
import sb_activity
import sb_cast
from v3_board_renderer import (
    _draw_strokes, _map_scale, _palette, _group_world_bounds,
    _composite_frame, _overlay_hand, _SLICE_SPAN, _arc, _ease_inv,
)
from v3_board_renderer import text_strokes, text_width
from v3_board_renderer import (font_text_strokes, font_text_width,
                               font_metrics, font_ink_box)

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
    for k, v in v3r.SVG_TONES.items():
        if k not in cols:
            cols[k] = v + (255,)
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
    for _t in ((sb_cast.FILL, sb_cast.SHADE) + sb_cast.SHIRTS + sb_cast.TONES
               + sb_activity.TONES):
        cols[_t] = (int(_t[1:3], 16), int(_t[3:5], 16), int(_t[5:7], 16), 255)
    return cols


_VIGNETTES: dict = {}


def _vignette(frame: Image.Image, ratio: str) -> Image.Image:
    """Reference-style paper vignette — fixed camera-light edge darkening
    (~18% at the corners), applied to the composed frame."""
    m = _VIGNETTES.get(ratio)
    if m is None:
        vw, vh = wbp.RATIO_SIZES[ratio]
        g = Image.radial_gradient('L').resize((vw, vh))
        m = g.point(lambda v: max(0, 255 - int(0.16 * max(0, v - 150))))
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


def _sb_role_indices(items, raw_roles):
    """Scene-role index each item was built from (items skip label-less
    roles, so list position is not the role index). Falls back to list
    position unless every item maps to a distinct role of its label."""
    def lab(r):
        return str(r.get('label') or '') if isinstance(r, dict) else str(r)
    ris = [next((g[4]['_ri'] for g, _s, _e in it['groups']
                 if g[4] and '_ri' in g[4]), None) for it in items]
    ok = (None not in ris and len(set(ris)) == len(ris)
          and all(ri < len(raw_roles)
                  and lab(raw_roles[ri]) == str(it.get('label') or '')
                  for ri, it in zip(ris, items)))
    return ris if ok else list(range(len(items)))


def _bundle_scene_groups(scene, plan, ratio, beat=None):
    """_scene_groups minus the zone headline, merged into element bundles
    (icon+caption, person+prop cluster) — same model the journey uses."""
    groups = v3r._scene_groups(scene, plan, ratio)
    merged = []          # list of items {groups:[(g,s,e)], label}
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
    sb_merge_off = (plan.get('board_layout') in ('storyboard', 'grid'))
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


# ---------------------------------------------------------------------------
# storyboard-panel machinery: each beat is a full-frame scene composed as a
# left-to-right narrative chain (object -> arrow -> actor -> context), with
# micro-annotations pinned to elements, expression overlays on figures, and
# procedurally drawn special glyphs (divider, crowd, stack-list,
# chart-journey). All coords inside _sb_glyph are item-local (the normal
# placement transform moves them).
# ---------------------------------------------------------------------------
_SB_GLYPHS = ('divider', 'crowd', 'stack-list', 'chart-journey', 'quantity-chart')


def _abs5(st):
    """Mark every stroke absolute (world coords, no slot transform)."""
    return [(s[0], s[1], s[2], s[3], True) for s in st]


def _sb_glyph(name, box, meta):
    """Procedural strokes for special storyboard elements. The box is the
    item's placed world bounds; strokes return absolute (flag 5 True)."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    st = []
    if name == 'divider':
        cx = (x0 + x1) / 2
        nseg = 7
        for i in range(nseg):
            ya = y0 + h * i / nseg
            yb = y0 + h * (i + 0.62) / nseg
            st.append((_wobble_line((cx, ya), (cx, yb), n=6,
                                    wob=w * 0.10, seed=i * 7 + 3),
                       'ink', 0.55, False, False))
        return _abs5(st)
    if name == 'crowd':
        n = 5
        fw = w / n
        for i in range(n):
            cx = x0 + fw * (i + 0.5)
            r = fw * 0.21
            hy = y0 + r
            st.append((v3r._ellipse(cx, hy, r, r, 14),
                       'ink', 0.8, False, False))
            body_top = hy + r * 0.85
            body_h = (y1 - body_top) * 0.92
            st.append((v3r._rounded_rect(cx, body_top + body_h / 2,
                                         fw * 0.62, body_h,
                                         fw * 0.26),
                       'ink', 0.8, False, False))
        return _abs5(st)
    if name == 'stack-list':
        rows = [str(r) for r in (meta.get('rows') or [])]
        n = max(1, len(rows))
        rh_ = h / n
        for i, rtxt in enumerate(rows):
            cy_ = y0 + rh_ * (i + 0.5)
            # hand-drawn card — four wobble lines, not a UI rounded-rect
            rx0, ry0_, rx1, ry1_ = (x0 + w * 0.02, cy_ - rh_ * 0.42,
                                   x0 + w * 0.98, cy_ + rh_ * 0.42)
            for ei, (q0, q1) in enumerate((((rx0, ry0_), (rx1, ry0_)),
                                           ((rx1, ry0_), (rx1, ry1_)),
                                           ((rx1, ry1_), (rx0, ry1_)),
                                           ((rx0, ry1_), (rx0, ry0_)))):
                st.append((_wobble_line(q0, q1, n=9, wob=rh_ * 0.05,
                                        seed=i * 17 + ei * 5 + 2),
                           'ink', 0.85, False, False))
            lh = rh_ * 0.46
            tw_ = text_width(rtxt, lh)
            if tw_ > w * 0.86:
                lh *= w * 0.86 / tw_
                tw_ = text_width(rtxt, lh)
            for s_ in text_strokes(rtxt, (x0 + w / 2 - tw_ / 2,
                                          cy_ - lh * 0.72),
                                   lh, 'ink', 0.85):
                st.append((s_[0], s_[1], s_[2], False, False))
        return _abs5(st)
    if name == 'chart-journey':
        # peak -> valley -> strong recovery, ending in an arrowhead
        pk = (x0 + w * 0.30, y0 + h * 0.10)
        vl = (x0 + w * 0.55, y0 + h * 0.74)
        md = (x0 + w * 0.78, y0 + h * 0.34)
        en = (x1, y0 + h * 0.10)
        pts = [(x0, y0 + h * 0.78), pk, vl, md, en]
        for i in range(len(pts) - 1):
            st.append((_wobble_line(pts[i], pts[i + 1], n=18,
                                    wob=w * 0.014, seed=i * 11 + 7),
                       'ink', 1.1, False, False))
        ang = math.atan2(en[1] - md[1], en[0] - md[0])
        ah = w * 0.05
        st.append(([(en[0], en[1]),
                    (en[0] - ah * math.cos(ang - 0.5),
                     en[1] - ah * math.sin(ang - 0.5))],
                   'ink', 1.1, False, False))
        st.append(([(en[0], en[1]),
                    (en[0] - ah * math.cos(ang + 0.5),
                     en[1] - ah * math.sin(ang + 0.5))],
                   'ink', 1.1, False, False))
        return _abs5(st)
    return _abs5(st)


def _sb_expr_strokes(name, b2, col='a_red'):
    """World-space expression overlay for a figure: emotion halo, thought
    bubble, or exclamation marks."""
    x0, y0, x1, y1 = b2
    w, h = x1 - x0, y1 - y0
    cx = (x0 + x1) / 2
    if name == 'halo':
        return [(v3r._ellipse(cx, (y0 + y1) / 2, w * 0.66, h * 0.56, 26),
                 col, 1.0, 'wash', True)]
    if name == 'thinking':
        cy = y0 - h * 0.10
        st = [(v3r._ellipse(cx + dx, cy + dy, r, r * 0.78, 14),
               'ink', 0.7, False, True)
              for dx, dy, r in ((0.0, 0.0, w * 0.17),
                                (w * 0.14, -h * 0.02, w * 0.12),
                                (-w * 0.14, -h * 0.01, w * 0.12),
                                (w * 0.04, -h * 0.09, w * 0.13))]
        st.append((v3r._ellipse(cx - w * 0.22, cy + h * 0.20, w * 0.045,
                                w * 0.045, 10), 'ink', 0.7, False, True))
        st.append((v3r._ellipse(cx - w * 0.30, cy + h * 0.32, w * 0.030,
                                w * 0.030, 10), 'ink', 0.7, False, True))
        return st
    if name == 'exclaim':
        cy = y0 - h * 0.04
        d = w * 0.05
        return [([(cx - d, cy - h * 0.10), (cx - d * 1.3, cy + h * 0.02)],
                 'ink', 1.5, False, True),
                (v3r._ellipse(cx - d * 1.4, cy + h * 0.07, d * 0.5,
                              d * 0.5, 10), 'ink', 1.5, 'wash', True),
                ([(cx + d, cy - h * 0.12), (cx + d * 0.7, cy)],
                 'ink', 1.5, False, True),
                (v3r._ellipse(cx + d * 0.6, cy + h * 0.06, d * 0.5,
                              d * 0.5, 10), 'ink', 1.5, 'wash', True)]
    return []


def _sb_annotate(text, b2, side, lh):
    """World-space micro-annotation text pinned to an element's edge or
    corner (ur/dr/ul/dl tuck the label off that corner). Returns
    (strokes, bounds)."""
    lines = str(text).split('\n')
    st = []
    lw_max = max(text_width(ln, lh) for ln in lines)
    n = len(lines)
    cxm = (b2[0] + b2[2]) / 2 - lw_max / 2
    if side == 'right':
        x, ys = b2[2] + lh * 0.4, b2[1] + lh * 0.1
    elif side == 'left':
        x, ys = b2[0] - lh * 0.4 - lw_max, b2[1] + lh * 0.1
    elif side == 'ur':
        x, ys = b2[2] + lh * 0.4, b2[1] - lh * 0.45
    elif side == 'dr':
        x, ys = b2[2] + lh * 0.4, b2[3] - lh * 1.2 * n + lh * 0.35
    elif side == 'ul':
        x, ys = b2[0] - lh * 0.4 - lw_max, b2[1] - lh * 0.45
    elif side == 'dl':
        x, ys = b2[0] - lh * 0.4 - lw_max, b2[3] - lh * 1.2 * n + lh * 0.35
    elif side == 'above':
        x, ys = cxm, b2[1] - lh * 1.2 * n - lh * 0.25
    else:  # below
        x, ys = cxm, b2[3] + lh * 0.35
    for i, ln in enumerate(lines):
        y = ys + i * lh * 1.2
        for s_ in text_strokes(ln, (x, y), lh, 'ink', 0.85):
            st.append((s_[0], s_[1], s_[2], False, True))
    bb = ((min(q[0] for s_ in st for q in s_[0]),
           min(q[1] for s_ in st for q in s_[0]),
           max(q[0] for s_ in st for q in s_[0]),
           max(q[1] for s_ in st for q in s_[0])) if st else b2)
    return st, bb


def _sb_arrow(p0, p1):
    """Short straight hand-drawn arrow between chain neighbours."""
    pts = _wobble_line(p0, p1, n=14, wob=2.6, seed=int(p0[0]) % 97 + 3)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    ah = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) * 0.24
    a1 = [(p1[0], p1[1]),
          (p1[0] - ah * math.cos(ang - 0.5), p1[1] - ah * math.sin(ang - 0.5))]
    a2 = [(p1[0], p1[1]),
          (p1[0] - ah * math.cos(ang + 0.5), p1[1] - ah * math.sin(ang + 0.5))]
    return [(pts, 'ink', 0.8, False, True), (a1, 'ink', 0.8, False, True),
            (a2, 'ink', 0.8, False, True)]


# ---------------------------------------------------------------------------
# storyboard scene composer
# ---------------------------------------------------------------------------
_SB_FT = 'hand-bold'
_SB_FL = 'hand'


def _sb_text(lines, x, y_top, size, font, align='center', color='ink'):
    """Multi-line font lettering. align='center' centres each line on x,
    'left' starts each line at x. Returns (strokes, ink bounds)."""
    asc, desc = font_metrics(size, font)
    lh = (asc + desc) * 0.80
    st, bb = [], None
    for i, ln in enumerate(lines):
        w = font_text_width(ln, size, font)
        x0 = x - w / 2 if align == 'center' else x
        y = y_top + i * lh
        st += font_text_strokes(ln, (x0, y), size, color, font)
        b = font_ink_box(ln, (x0, y), size, font)
        bb = b if bb is None else (min(bb[0], b[0]), min(bb[1], b[1]),
                                   max(bb[2], b[2]), max(bb[3], b[3]))
    return st, bb


def _sb_text_dims(lines, size, font):
    """(width, ink height, ink top offset) of a text block."""
    _st, bb = _sb_text(lines, 0.0, 0.0, size, font, 'left')
    return bb[2] - bb[0], bb[3] - bb[1], bb[1]


def _sb_repeat_art(art, count):
    """Draw small counted things separately, up to nine representatives."""
    n = min(9, max(1, int(count or 1)))
    if n == 1 or not art:
        return art
    bb = _sb_bounds(st[0] for st in art)
    if bb is None:
        return art
    width = max(1.0, bb[2] - bb[0])
    out = []
    for k in range(n):
        dx = (k - (n - 1) / 2) * width * 1.12
        out.extend(([(x + dx, y) for x, y in st[0]],) + tuple(st[1:])
                   for st in art)
    return out


def _sb_item_art(it, count=1):
    """An item's drawable art in world coords (labels/captions/marks and
    ground shadows dropped — the composer draws its own)."""
    out = []
    for g, _s, _e in it['groups']:
        kind, strokes, center, size, _slot = g
        if kind not in ('icon', 'glyph'):
            continue
        for st in strokes:
            pts = st[0]
            if not pts or len(pts) < 2 or len(pts[0]) < 2:
                continue
            ab = len(st) > 4 and st[4]
            wp = (list(pts) if ab else
                  [(center[0] + q[0] * size, center[1] + q[1] * size)
                   for q in pts])
            fl = st[3] if len(st) > 3 else False
            if fl is True or (isinstance(fl, float)
                              and not isinstance(fl, bool)):
                sp = fl if isinstance(fl, float) else 0.075
                fl = ('hatch', sp * (1.0 if ab else size))
            out.append((wp, st[1], st[2], fl))
    return _sb_repeat_art(out, count)


def _sb_bounds(pts_iter):
    xs, ys = [], []
    for pts in pts_iter:
        for q in pts:
            xs.append(q[0])
            ys.append(q[1])
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def _sb_fit(art, box):
    """Scale art uniformly into box: centred horizontally, feet on the box
    bottom. Returns (absolute strokes, placed ink bounds)."""
    ab = _sb_bounds(a[0] for a in art)
    if ab is None:
        return [], box
    aw, ah = max(1e-6, ab[2] - ab[0]), max(1e-6, ab[3] - ab[1])
    k = min((box[2] - box[0]) / aw, (box[3] - box[1]) / ah)
    ox = (box[0] + box[2]) / 2 - (ab[0] + ab[2]) / 2 * k
    oy = box[3] - ab[3] * k
    out = []
    for pts, col, ws, fl in art:
        c = _remap_col(col)
        if isinstance(fl, tuple):
            fl = 'solid' if c not in _INKY else float(fl[1] * k)
        elif fl and fl not in ('solid', 'wash') and c not in _INKY:
            fl = 'solid'
        out.append(([(ox + q[0] * k, oy + q[1] * k) for q in pts],
                    c, ws, fl, True))
    return out, (ox + ab[0] * k, oy + ab[1] * k,
                 ox + ab[2] * k, oy + ab[3] * k)


def _sb_art_aspect(art):
    ab = _sb_bounds(a[0] for a in art)
    if ab is None:
        return 1.0
    return max(0.2, (ab[2] - ab[0]) / max(1e-6, ab[3] - ab[1]))


def _sb_swash_poly(x0, y0, x1, y1, seed):
    """Irregular highlighter swash: wobbling long edges, rounded ends."""
    rnd = random.Random(seed)
    h = y1 - y0
    pts = []
    n = 16
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        pts.append((x, y0 + rnd.uniform(-0.06, 0.06) * h))
    for a in range(1, 8):
        ang = -math.pi / 2 + math.pi * a / 8
        pts.append((x1 + math.cos(ang) * h * 0.30,
                    (y0 + y1) / 2 + math.sin(ang) * h / 2))
    for i in range(n, -1, -1):
        x = x0 + (x1 - x0) * i / n
        pts.append((x, y1 + rnd.uniform(-0.06, 0.06) * h))
    for a in range(1, 8):
        ang = math.pi / 2 + math.pi * a / 8
        pts.append((x0 + math.cos(ang) * h * 0.30,
                    (y0 + y1) / 2 + math.sin(ang) * h / 2))
    pts.append(pts[0])
    return pts


def _sb_blob(cx, cy, rx, ry, seed, n=22, jit=0.05):
    rnd = random.Random(seed)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = 1.0 + rnd.uniform(-jit, jit)
        pts.append((cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r))
    pts.append(pts[0])
    return pts


def _sb_crowd(box, seed=5):
    """A composed group of small grey silhouettes of varied heights."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    n = 5
    st = []
    hs = (0.92, 1.0, 0.80, 0.96, 0.86)
    fw = w / n
    for i in range(n):
        cx = x0 + fw * (i + 0.5)
        fh = h * hs[i]
        top = y1 - fh
        r = min(fw * 0.26, fh * 0.17)
        hy = top + r
        head = _sb_blob(cx, hy, r, r, seed + i * 3, 16, 0.04)
        bt = hy + r * 1.25
        bw = fw * 0.40
        body = [(cx - bw, y1)]
        for a in range(0, 11):
            ang = math.pi + math.pi * a / 10
            body.append((cx + math.cos(ang) * bw,
                         bt + bw * 0.9 + math.sin(ang) * bw * 0.9))
        body.append((cx + bw, y1))
        body.append(body[0])
        for shp in (head, body):
            st.append((shp, 'pale', 1.0, 'solid', True))
            st.append((shp, 'ink', 0.8, False, True))
    return st


def _sb_stack(box, rows, sw_col, seed=3):
    """A hand-drawn stack of labelled cards with a pastel paper behind."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    n = max(1, len(rows))
    st = []
    off = w * 0.05
    back = [(x0 + off, y0 + off), (x1, y0 + off), (x1, y1),
            (x0 + off, y1), (x0 + off, y0 + off)]
    st.append((back, sw_col, 0.40, 'swash', True))
    rh_ = (h - off) / n
    fs = rh_ * 0.52
    for rtxt in rows:
        tw_ = font_text_width(rtxt, fs, _SB_FT)
        if tw_ > (w - off) * 0.80:
            fs *= (w - off) * 0.80 / tw_
    for i, rtxt in enumerate(rows):
        ry0, ry1 = y0 + rh_ * i, y0 + rh_ * (i + 1)
        rx0, rx1 = x0, x1 - off
        st.append(([(rx0, ry0), (rx1, ry0), (rx1, ry1), (rx0, ry1),
                    (rx0, ry0)], 'paper', 1.0, 'solid', True))
        for ei, (q0, q1) in enumerate((((rx0, ry0), (rx1, ry0)),
                                       ((rx1, ry0), (rx1, ry1)),
                                       ((rx1, ry1), (rx0, ry1)),
                                       ((rx0, ry1), (rx0, ry0)))):
            st.append((_wobble_line(q0, q1, n=9, wob=rh_ * 0.03,
                                    seed=seed + i * 17 + ei * 5),
                       'ink', 1.0, False, True))
        _dw, dh, dtop = _sb_text_dims([rtxt], fs, _SB_FT)
        ty = (ry0 + ry1) / 2 - dh / 2 - dtop
        tst, _bb = _sb_text([rtxt], rx0 + (rx1 - rx0) * 0.09, ty, fs,
                            _SB_FT, 'left')
        st += tst
    return st


def _sb_divider(x, y0, y1):
    st = []
    seg = (y1 - y0) / 13
    y = y0
    i = 0
    while y + seg * 0.55 <= y1:
        st.append((_wobble_line((x, y), (x, y + seg * 0.55), n=4, wob=1.2,
                                seed=i * 7 + 3), 'ink', 0.7, False, True))
        y += seg
        i += 1
    return st


_SB_JOURNEY = [(0.0, 0.62), (0.24, 0.0), (0.33, 0.30), (0.37, 0.24),
               (0.46, 0.64), (0.50, 0.57), (0.57, 1.0), (0.64, 0.62),
               (0.68, 0.70), (0.79, 0.30), (0.83, 0.38), (1.0, 0.0)]
_SB_ANCH = {'peak': (0.24, 0.0), 'valley': (0.57, 1.0), 'rise': (0.79, 0.30)}


def _sb_quantity_chart(box, chart):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    values = chart['values']
    maximum = max(v['value'] for v in values)
    left, floor, top = x0 + w * 0.10, y0 + h * 0.78, y0 + h * 0.13
    width = (x1 - left) / len(values)
    fs = min(h * 0.055, width * 0.13)
    base = [([(left, top), (left, floor), (x1, floor)],
             'ink', 1.0, False, True)]
    text, _ = _sb_text([f"0 {chart['unit']}"], left, floor + fs,
                       fs, _SB_FT, 'left')
    base += text
    bars = []
    for i, value in enumerate(values):
        cx = left + width * (i + 0.5)
        y = floor - (floor - top) * value['value'] / maximum
        half = width * 0.24
        rect = (cx - half, y, cx + half, floor)
        outline = [(rect[0], y), (rect[2], y), (rect[2], floor),
                   (rect[0], floor), (rect[0], y)]
        strokes = [(outline, 'a_blue', 0.7, 'swash', True),
                   (outline, 'ink', 1.0, False, True)]
        text, _ = _sb_text([f"{value['value']:g}"], cx, y - fs * 1.6,
                           fs, _SB_FT, 'center')
        strokes += text
        lines = textwrap.wrap(value['label'], width=max(
            8, int(width * 0.86 / (fs * 0.65))), break_long_words=False)
        label_size = min(
            fs, fs * width * 0.86 / max(
                font_text_width(line, fs, _SB_FT) for line in lines),
            h * 0.09 / max(1, len(lines)) / 1.15)
        text, _ = _sb_text(lines, cx, floor + fs * 2.5,
                           label_size, _SB_FT, 'center')
        strokes += text
        bars.append((value, strokes, rect))
    return base, bars


def _sb_chart(box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    pts = [(x0 + u * w, y0 + v * h) for u, v in _SB_JOURNEY]
    st = []
    for i in range(len(pts) - 1):
        st.append((_wobble_line(pts[i], pts[i + 1], n=10, wob=w * 0.004,
                                seed=i * 11 + 7), 'ink', 1.15, False, True))
    en, md = pts[-1], pts[-2]
    ang = math.atan2(en[1] - md[1], en[0] - md[0])
    ah = w * 0.045
    for sgn in (-1, 1):
        st.append(([en, (en[0] - ah * math.cos(ang + sgn * 0.5),
                         en[1] - ah * math.sin(ang + sgn * 0.5))],
                   'ink', 1.15, False, True))
    segs = []
    for a_, b_ in zip(pts, pts[1:]):
        for ti in range(6):
            q0 = (a_[0] + (b_[0] - a_[0]) * ti / 6,
                  a_[1] + (b_[1] - a_[1]) * ti / 6)
            q1 = (a_[0] + (b_[0] - a_[0]) * (ti + 1) / 6,
                  a_[1] + (b_[1] - a_[1]) * (ti + 1) / 6)
            segs.append((min(q0[0], q1[0]) - 3, min(q0[1], q1[1]) - 3,
                         max(q0[0], q1[0]) + 3, max(q0[1], q1[1]) + 3))
    return st, segs


def _sb_expr(name, fb, col):
    """Expression overlay for a figure's box (head at the top)."""
    x0, y0, x1, y1 = fb
    w, h = x1 - x0, y1 - y0
    cx = (x0 + x1) / 2
    if name == 'halo':
        return [(_sb_blob(cx, y0 + h * 0.42, max(w * 0.85, h * 0.36),
                          h * 0.52, 9, 24, 0.03), col, 0.26, 'swash', True)]
    if name == 'thinking':
        r = h * 0.075
        bx, by = x1 + r * 0.9, y0 - r * 0.4
        st = [(_sb_blob(bx, by, r * 1.35, r, 4, 18, 0.10),
               'ink', 0.8, False, True)]
        st.append((_sb_blob(cx + w * 0.28, y0 + h * 0.02, r * 0.24,
                            r * 0.24, 6, 10, 0.0), 'ink', 0.8, False, True))
        st.append((_sb_blob(cx + w * 0.40, y0 - h * 0.03, r * 0.36,
                            r * 0.36, 7, 10, 0.0), 'ink', 0.8, False, True))
        return st
    if name == 'exclaim':
        st = []
        for i, dx in enumerate((-0.10, 0.02, 0.14)):
            xa = x1 + w * dx
            ya = y0 - h * 0.02 + abs(dx) * h * 0.2
            st.append(([(xa - w * 0.02, ya), (xa, ya + h * 0.09)],
                       'a_red', 1.3, False, True))
            st.append((_sb_blob(xa + w * 0.005, ya + h * 0.12, h * 0.008,
                                h * 0.008, i, 8, 0.0),
                       'a_red', 1.3, False, True))
        return st
    return []


def _sb_ovl(a, b, pad=0.0):
    return not (a[2] + pad <= b[0] or b[2] + pad <= a[0]
                or a[3] + pad <= b[1] or b[3] + pad <= a[1])


def _sb_wrap(text, cap=14):
    """Split a label into lines: explicit newlines win; otherwise long
    single lines break at word boundaries near `cap` characters."""
    out = []
    for ln in text.split('\n'):
        ws, cur = ln.split(), ''
        for w in ws:
            if cur and len(cur) + 1 + len(w) > cap:
                out.append(cur)
                cur = w
            else:
                cur = (cur + ' ' + w).strip()
        if cur:
            out.append(cur)
    return out[:3]


def _sb_boxfit(e, cx, yb, wmax, hmax):
    """Largest box of e's aspect inside wmax x hmax, centred on cx, feet on
    yb."""
    eh = min(hmax, wmax / max(0.2, e['aspect']))
    ew = eh * e['aspect']
    e['box'] = (cx - ew / 2, yb - eh, cx + ew / 2, yb)


def _sb_cast_unit(cast):
    """Shrink cast boxes to the scene's smallest figure unit (box height
    over its activity scale) so every person is drawn at one size."""
    units = [(e['box'][3] - e['box'][1]) / max(0.2, e['rel'])
             for e in cast if e.get('box')]
    if len(units) < 2:
        return
    u = min(units)
    for e in cast:
        x0, y0, x1, y1 = e['box']
        eh = u * e['rel']
        if y1 - y0 > eh * 1.02:
            ew = eh * e['aspect']
            cx = (x0 + x1) / 2
            e['box'] = (cx - ew / 2, y1 - eh, cx + ew / 2, y1)


def _sb_outfit(m, *words):
    """Costume for the role words plus the cast member's look (sex,
    child, hair, beard) from the plan role."""
    ck = str(m.get('cast_key') or '').split('#')[0]
    return dict(sb_cast.outfit_for(*words, ck or None),
                **sb_cast.look_for(m))


def _sb_close_gaps(sol, gap=0.35):
    """Pull apart-spread blocks of a picture together, in order, so no gap
    between them is wider than `gap` x the typical element height. Elements
    that overlap or touch move together, so contacts are kept."""
    hs = sorted(e['box'][3] - e['box'][1] for e in sol)
    tall = hs[len(hs) // 2]
    blocks = []
    for e in sorted(sol, key=lambda e: e['box'][0]):
        if blocks and e['box'][0] <= blocks[-1][1]:
            blocks[-1][0].append(e)
            blocks[-1][1] = max(blocks[-1][1], e['box'][2])
        else:
            blocks.append([[e], e['box'][2]])
    shift = 0.0
    for prev, cur in zip(blocks, blocks[1:]):
        left = min(e['box'][0] for e in cur[0]) - shift
        shift += max(0.0, left - prev[1] - gap * tall)
        cur[1] -= shift
        for e in cur[0]:
            b = e['box']
            e['box'] = (b[0] - shift, b[1], b[2] - shift, b[3])


def _sb_fill(group, rect, lane, unit=None, art_cap=0.72, person_cap=0.78,
             k_max=6.0, apply=True, close_gaps=True, rewrap=True):
    """Scale a composed picture up about its own centre so it fills its
    space, then centre it there. Relative sizes, contacts and order are
    kept; label lanes under each element are reserved. With people in it,
    `unit` (one figure unit for the whole reel) sets the scale instead, so
    the cast keeps one size. -> the largest figure unit this picture could
    take, or None without people."""
    sol = [e for e in group if e.get('box') and e['kind'] != 'divider']
    if not sol:
        return None
    x0, y0, x1, y1 = rect
    w, h = x1 - x0, y1 - y0
    # graph columns are spaced by the relation chain, not decoration —
    # pulling them together collapses the diagram
    if close_gaps:
        _sb_close_gaps(sol)
    ux0 = min(e['box'][0] for e in sol)
    ux1 = max(e['box'][2] for e in sol)
    uy0 = min(e['box'][1] for e in sol)
    uy1 = max(e['box'][3] for e in sol)
    lane_b = max(lane(e) for e in sol)
    # a wide union on a tall rect is width-bound: scale can't grow, so
    # elements stay small with void between and around them. Re-wrap the
    # row into the row count whose re-packed union best matches the rect's
    # aspect, so the picture actually fills the space. (graph compositions
    # keep their relation-driven columns.)
    if apply and close_gaps and rewrap and len(sol) >= 3:
        avail_h = h - lane_b
        rect_aspect = w / max(1.0, avail_h)
        union_aspect = (ux1 - ux0) / max(1.0, uy1 - uy0)
        # never rewrap a composition whose elements touch: contacts are
        # intentional groupings (a rider on a mount, hands joined)
        contact = any(
            a['box'][2] > b['box'][0] and a['box'][0] < b['box'][2] and
            a['box'][3] > b['box'][1] and a['box'][1] < b['box'][3]
            for i, a in enumerate(sol) for b in sol[i + 1:])
        if union_aspect > rect_aspect * 1.3 and not contact:
            xs = sorted(sol, key=lambda e: (e['box'][0] + e['box'][2]) / 2)

            def _aspect_after(nrows):
                per = -(-len(xs) // nrows)
                rows = [r for r in
                        (xs[i * per:(i + 1) * per] for i in range(nrows))
                        if r]
                rw = max(max(e['box'][2] for e in r) -
                         min(e['box'][0] for e in r) for r in rows)
                rh = (sum(max(e['box'][3] for e in r) -
                          min(e['box'][1] for e in r) for r in rows)
                      + lane_b * (len(rows) - 1))
                return rw / max(1.0, rh)

            best = min(range(2, min(4, len(xs)) + 1),
                       key=lambda r: abs(_aspect_after(r) - rect_aspect))
            if abs(_aspect_after(best) - rect_aspect) < \
                    abs(union_aspect - rect_aspect) * 0.85:
                per = -(-len(xs) // best)
                rows = [r for r in
                        (xs[i * per:(i + 1) * per] for i in range(best))
                        if r]
                # stack the rows as blocks centred on the band: positions
                # come from real row heights + lane gaps, so rows can
                # never land on each other
                r_unions = [(min(e['box'][0] for e in r),
                             min(e['box'][1] for e in r),
                             max(e['box'][2] for e in r),
                             max(e['box'][3] for e in r)) for r in rows]
                total = (sum(u[3] - u[1] for u in r_unions)
                         + lane_b * (len(rows) - 1))
                y = y0 + max(0.0, (avail_h - total) / 2)
                for row, (rx0, ry0, rx1, ry1) in zip(rows, r_unions):
                    tx = x0 + w / 2 - (rx0 + rx1) / 2
                    ty = y - ry0
                    y += (ry1 - ry0) + lane_b
                    for e in row:
                        b = e['box']
                        e['box'] = (b[0] + tx, b[1] + ty,
                                    b[2] + tx, b[3] + ty)
                ux0 = min(e['box'][0] for e in sol)
                ux1 = max(e['box'][2] for e in sol)
                uy0 = min(e['box'][1] for e in sol)
                uy1 = max(e['box'][3] for e in sol)
    k = min(w * 0.94 / max(1.0, ux1 - ux0),
            (h * 0.92 - lane_b) / max(1.0, uy1 - uy0), k_max)
    for e in sol:
        # a figure drawn inside a big apparatus (a mountain, a building)
        # is that apparatus's picture and may take nearly the full height
        cap = (0.95 if e['kind'] == 'person' and e['rel'] > 1.6 else
               person_cap if e['kind'] == 'person' else art_cap) * h
        eh = e['box'][3] - e['box'][1]
        if e['kind'] not in ('quantity-chart', 'chart-journey'):
            k = min(k, cap / max(1.0, eh))
    # a union wider or taller than its space must shrink to fit, not just
    # shift — but never below a legible floor
    k = max(0.55, k)
    fus = [e['figure_unit'] for e in sol
           if e['kind'] == 'person' and e.get('figure_unit')]
    room = min(fus) * k if fus else None
    if not apply:
        return room
    ucx, ucy = (ux0 + ux1) / 2, (uy0 + uy1) / 2
    ncx = x0 + w / 2
    ncy = y0 + (h - lane_b) / 2
    for e in sol:
        b = e['box']
        e['box'] = (ncx + (b[0] - ucx) * k, ncy + (b[1] - ucy) * k,
                    ncx + (b[2] - ucx) * k, ncy + (b[3] - ucy) * k)
        if e.get('figure_unit'):
            e['figure_unit'] *= k
    # one shared figure size for the reel: people resize on their own
    # centre to the reel's unit instead of dragging the whole picture's
    # scale down (a single small figure in a diagram must not collapse
    # the composition around it)
    if fus and unit is not None:
        for e in sol:
            if e['kind'] != 'person' or not e.get('figure_unit'):
                continue
            b = e['box']
            eh = max(1e-6, b[3] - b[1])
            kp = max(0.5, min(1.25, unit / eh))
            if abs(kp - 1.0) < 1e-3:
                continue
            pcx = (b[0] + b[2]) / 2
            e['box'] = (pcx - (pcx - b[0]) * kp, b[3] - eh * kp,
                        pcx + (b[2] - pcx) * kp, b[3])
            e['figure_unit'] *= kp
    # a big scale-up may carry an edge out of the rect (a tall roof above
    # the band top, a wide backdrop past the side); nudge it back inside
    nx0 = min(e['box'][0] for e in sol)
    ny0 = min(e['box'][1] for e in sol)
    nx1 = max(e['box'][2] for e in sol)
    ny1 = max(e['box'][3] for e in sol)
    pad = min(w, h) * 0.02
    dx = (max(0.0, x0 + pad - nx0) if nx0 < x0 + pad else
          min(0.0, x1 - pad - nx1) if nx1 > x1 - pad else 0.0)
    dy = (max(0.0, y0 + pad - ny0) if ny0 < y0 + pad else
          min(0.0, y1 - ny1) if ny1 > y1 else 0.0)
    if dx or dy:
        for e in sol:
            b = e['box']
            e['box'] = (b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy)
    return room


def _sb_layout(lay, els, L, R, band_t, band_b, labh, gap, labw=None,
               edges=()):
    """Non-row compositions. Sets e['box'] on every element and returns
    True, or False to fall back to the shared-baseline row."""
    Wc, band_h = R - L, band_b - band_t
    sol = [e for e in els if e['kind'] != 'divider']
    n = len(sol)
    lane = lambda e: (labh(e) + gap) if e['label'] else 0.0  # noqa: E731
    labw = labw or (lambda e: 0.0)
    if lay == 'graph' and n >= 2:
        _sb_graph_layout(sol, edges, L, R, band_t, band_b, lane)
        return True
    if lay == 'story' and n >= 2:
        cells: dict = {}
        for e in sol:
            cells.setdefault(int(e['m'].get('moment') or 0), []).append(e)
        cols = [cells[k] for k in sorted(cells)]
        pad = Wc * 0.012
        cast = [e for e in sol if e['kind'] == 'person']
        # the tallest activity picture sets one figure scale for the scene
        r_top = min(1.0, 1.0 / (0.92 * max([e['rel'] for e in cast]
                                            or [1.0])))

        def top_of(e):
            return (min(1.05, 1.04 * e['rel'] * r_top)
                    if e['kind'] == 'person' else 0.78)

        def need(e, rh):
            # a cell is as wide as its drawing or its label, whichever
            # wins; a person's strokes run wider than the nominal figure
            # aspect (gestures, props), so its slot gets the extra room
            art = e['aspect'] * rh * (top_of(e) / 0.9 * 1.18
                                      if e['kind'] == 'person' else 0.60)
            return max(art, (labw(e) + pad) if e['label'] else 0.0)

        def plan_rows(nr):
            per = -(-len(cols) // nr)
            rs = [cols[i:i + per] for i in range(0, len(cols), per)]
            gy = band_h * 0.07 if len(rs) > 1 else 0.0
            rh = (band_h - gy * (len(rs) - 1)) / len(rs)
            gx = Wc * 0.04
            fits = all(sum(need(e, rh) for c in rc for e in c)
                       + gx * (len(rc) - 1) <= Wc for rc in rs)
            return rs, gy, rh, gx, fits

        choice = None
        for nr in range(1, min(3, len(cols)) + 1):
            if nr == 1 and len(cols) > 3:
                continue
            choice = plan_rows(nr)
            if choice[4]:
                break
        rows, gapy, row_h, gapx, _fit = choice
        for ri, rc in enumerate(rows):
            yb = band_t + row_h * (ri + 1) + gapy * ri
            wts = [[need(e, row_h) for e in c] for c in rc]
            tot = Wc - gapx * (len(rc) - 1)
            k = min(2.1, tot / max(1e-6, sum(map(sum, wts))))
            used_w = k * sum(map(sum, wts)) + gapx * (len(rc) - 1)
            x = L + (Wc - used_w) / 2
            for c, wc in zip(rc, wts):
                for e, w0 in zip(c, wc):
                    e['row'] = ri
                    w_ = w0 * k
                    _sb_boxfit(e, x + w_ / 2, yb - lane(e), w_ * 0.9,
                               row_h * top_of(e) - lane(e))
                    x += w_
                x += gapx
        _sb_cast_unit(cast)
        return True
    if lay == 'focus' and n >= 2:
        hero = next((e for e in sol if e['focus']),
                    next((e for e in sol if e['kind'] == 'person'), sol[0]))
        if hero['kind'] == 'quantity-chart':
            # the chart is the picture: it takes most of the board and the
            # supporting drawings share the remaining strip beside it
            # (landscape) or under it (square, portrait)
            rest = [e for e in sol if e is not hero]
            wide = Wc > band_h * 1.5
            if wide:
                cw_ = Wc * 0.68
                hero['aspect'] = cw_ / band_h
                hero['box'] = (L, band_t, L + cw_, band_b)
                sx0, sw_ = L + cw_ + Wc * 0.04, Wc - cw_ - Wc * 0.04
                rh_ = band_h / len(rest)
                for k_, e in enumerate(rest):
                    _sb_boxfit(e, sx0 + sw_ / 2,
                               band_t + rh_ * (k_ + 1) - lane(e),
                               sw_ * 0.8, rh_ * 0.82 - lane(e))
            else:
                ch_ = band_h * 0.70
                hero['aspect'] = Wc / ch_
                hero['box'] = (L, band_t, R, band_t + ch_)
                sh_ = band_h - ch_ - band_h * 0.04
                cw_ = Wc / len(rest)
                for k_, e in enumerate(rest):
                    _sb_boxfit(e, L + cw_ * (k_ + 0.5), band_b - lane(e),
                               cw_ * 0.8, sh_ - lane(e))
            return True
        hi_ = sol.index(hero)
        pre, post = sol[:hi_], sol[hi_ + 1:]
        hw = Wc * (0.46 if pre and post else 0.54)
        side = (Wc - hw) / (2 if pre and post else 1)
        hx0 = L + (side if pre else 0.0)
        _sb_boxfit(hero, hx0 + hw / 2, band_b - lane(hero), hw * 0.9,
                   band_h - lane(hero))
        for grp, x0 in ((pre, L), (post, hx0 + hw)):
            if not grp:
                continue
            cw = side / len(grp)
            for k_, e in enumerate(grp):
                _sb_boxfit(e, x0 + cw * (k_ + 0.5), band_b - lane(e),
                           cw * 0.78, band_h * 0.55 - lane(e))
        return True
    if lay == 'stair' and n >= 3:
        cw = Wc / n
        rise = band_h * 0.20
        for i, e in enumerate(sol):
            yb = band_b - lane(e) - rise * i / (n - 1)
            _sb_boxfit(e, L + cw * (i + 0.5), yb, cw * 0.78,
                       band_h - rise - lane(e))
        return True
    if lay == 'before_after' and n >= 2:
        half = n // 2
        sides = ([e for e in sol if e['m'].get('side') == 'before'],
                 [e for e in sol if e['m'].get('side') == 'after'])
        if not (sides[0] and sides[1]):
            sides = (sol[:half], sol[half:])
        else:
            a0 = sol.index(sides[1][0])
            for i, e in enumerate(sol):
                if e['m'].get('side') not in ('before', 'after'):
                    sides[0 if i < a0 else 1].append(e)
            sides = tuple(sorted(g, key=sol.index) for g in sides)
        hw = Wc * 0.43
        for si_, grp in enumerate(sides):
            x0 = L + (0 if si_ == 0 else Wc - hw)
            for e in grp:
                e['ba_side'] = si_
            cw = hw / len(grp)
            for i, e in enumerate(grp):
                _sb_boxfit(e, x0 + cw * (i + 0.5), band_b - lane(e),
                           cw * 0.86, band_h * 0.94 - lane(e))
        return True
    if lay == 'cycle' and n >= 3:
        cx, cy = (L + R) / 2, band_t + band_h * 0.44
        rx, ry = Wc * 0.30, band_h * 0.30
        sz = min(band_h * 0.32, Wc * 0.18)
        for i, e in enumerate(sol):
            a = -math.pi / 2 + 2 * math.pi * i / n
            px, py = cx + rx * math.cos(a), cy + ry * math.sin(a)
            h_ = sz - (lane(e) if e['label'] else 0) * 0.5
            _sb_boxfit(e, px, py + h_ / 2, sz * 1.2, h_)
        return True
    if lay == 'reaction' and n >= 2:
        hero = next((e for e in sol if e['kind'] != 'person'), None)
        ppl = [e for e in sol if e is not hero]
        if hero is None or not ppl:
            return False
        hw = Wc * 0.30
        _sb_boxfit(hero, (L + R) / 2, band_b - lane(hero), hw,
                   band_h * 0.72 - lane(hero))
        left, right = ppl[::2], ppl[1::2]
        sw_ = (Wc - hw) / 2
        for grp, x0 in ((left, L), (right, R - sw_)):
            if not grp:
                continue
            cw = sw_ / len(grp)
            for i, e in enumerate(grp):
                _sb_boxfit(e, x0 + cw * (i + 0.5), band_b - lane(e),
                           cw * 0.8, band_h * 0.78 - lane(e))
        return True
    return False


_SB_TOUCH = {'reach', 'offer', 'point', 'climb', 'dig'}
_SB_PREPS = {'to', 'into', 'onto', 'in', 'inside', 'through', 'toward',
             'towards', 'until', 'across', 'via', 'over', 'from', 'for',
             'by', 'with', 'at', 'on', 'of'}


def _sb_graph_layout(sol, edges, L, R, band_t, band_b, lane):
    """Diagram composition: things placed in columns by how far along the
    scene's chain of relations they sit (a -> b puts b right of a),
    contrasted things stacked in one column, loose things filling the
    emptiest column, the most-linked thing drawn largest. At most four
    things share a column; long chains fold onto a second tier. Every
    person is drawn at one height."""
    Wc, band_h = R - L, band_b - band_t
    n = len(sol)
    ix = {id(e): i for i, e in enumerate(sol)}
    ed = [(ix[id(a)], ix[id(b)], k) for a, b, k in edges
          if id(a) in ix and id(b) in ix and a is not b]
    depth = [0] * n
    for _ in range(n):
        moved = False
        for a, b, k in ed:
            if k != 'vs' and depth[a] + 1 > depth[b] and depth[a] + 1 < n:
                depth[b] = depth[a] + 1
                moved = True
        if not moved:
            break
    for a, b, k in ed:
        if k == 'vs':
            depth[b] = depth[a]
    linked = {i for a, b, _k in ed for i in (a, b)}
    levels = sorted({depth[i] for i in linked}) or [0]
    cols = [[i for i in sorted(linked) if depth[i] == d] for d in levels]
    for i in range(n):
        if i in linked:
            continue
        room = [c for c in range(len(cols)) if len(cols[c]) < 4]
        # loose things spread across the sheet: a scene with few links
        # must not collapse into one dense column — new columns first
        # (up to four, one per element) before filling the emptiest
        if not room or len(cols) < min(4, n):
            cols.append([i])
            continue
        near = min(room, key=lambda c: (len(cols[c]), min(
            abs(j - i) for j in cols[c]) if cols[c] else 0))
        cols[near].append(i)
    split = []
    for c in cols:
        while len(c) > 4:
            split.append(c[:4])
            c = c[4:]
        split.append(c)
    cols = [c for c in split if c]
    ncol = len(cols)
    deg = [sum(1 for a, b, _k in ed if i in (a, b)) for i in range(n)]
    hero = max(range(n), key=lambda i: (deg[i], sol[i]['kind'] != 'person',
                                         -i))
    tiers = 1 if ncol <= 5 else 2
    per = -(-ncol // tiers)
    th = band_h / tiers
    lab_cap = th * 0.22
    lane_ = lambda e: min(lane(e), lab_cap)  # noqa: E731
    cells = {}
    ypos = {}
    for c, mem in enumerate(cols):
        mem.sort(key=lambda i: (sum(ypos.get(a, 0.5) for a, b, _k in ed
                                    if b == i)
                                / max(1, sum(1 for a, b, _k in ed
                                             if b == i)), i))
        t_, c_ = divmod(c, per)
        ncols_t = min(per, ncol - t_ * per)
        colw = Wc / ncols_t
        cx = (L + colw * (c_ + 0.5)) if t_ % 2 == 0 else (
            R - colw * (c_ + 0.5))
        wt = [1.6 if sol[i]['kind'] == 'person' else 1.0 for i in mem]
        y_ = band_t + t_ * th
        for r, i in enumerate(mem):
            ypos[i] = (r + 0.5) / len(mem)
            ch = th * wt[r] / sum(wt)
            cells[i] = (cx, y_, colw, ch)
            y_ += ch
    ppl = [i for i in range(n) if sol[i]['kind'] == 'person']
    ph = min([cells[i][3] * 0.86 - lane_(sol[i]) for i in ppl]
             + [band_h * 0.72]) if ppl else 0.0
    for i in range(n):
        e = sol[i]
        cx, top, colw, ch = cells[i]
        lb = lane_(e)
        if e['kind'] == 'person':
            hmax = ph * e['rel']
            wmax = colw * 0.8
        else:
            wf, hf = (0.70, 0.92) if i == hero else (0.66, 0.9)
            hmax = max(ch * hf - lb, ch * 0.4)
            if i != hero:
                hmax = min(hmax, th * 0.6)
            wmax = colw * wf
        _sb_boxfit(e, cx, top + ch * 0.96 - lb, wmax, hmax)
        b = e['box']
        blk = (b[3] - b[1]) + lb
        dy = (top + (ch - blk) / 2) - b[1]
        e['box'] = (b[0], b[1] + dy, b[2], b[3] + dy)


def _sb_graph_edge(pb, cb, Wc, kind, obst=()):
    """A relation link between two drawn things: arrow a -> b, a
    two-headed arrow for 'stands for', a crossed arrow for a denial."""
    ax, ay = (pb[0] + pb[2]) / 2, (pb[1] + pb[3]) / 2
    bx, by = (cb[0] + cb[2]) / 2, (cb[1] + cb[3]) / 2
    dx, dy = bx - ax, by - ay
    d = math.hypot(dx, dy)
    if d < 1e-6:
        return None, None
    ux, uy = dx / d, dy / d

    def exit_t(b, cx, cy, sgn):
        ts = []
        for c0, c1, u, cc in ((b[0], b[2], ux, cx), (b[1], b[3], uy, cy)):
            if abs(u) > 1e-9:
                ts.append(max((c0 - cc) / (sgn * u), (c1 - cc) / (sgn * u)))
        return min(ts) if ts else 0.0
    m = Wc * 0.016
    t0 = exit_t(pb, ax, ay, 1) + m
    t1 = d - exit_t(cb, bx, by, -1) - m
    if t1 - t0 < Wc * 0.025:
        return None, None
    p0 = (ax + ux * t0, ay + uy * t0)
    p1 = (ax + ux * t1, ay + uy * t1)
    ah = min(Wc * 0.018, (t1 - t0) * 0.3)
    span = t1 - t0

    def bez(off):
        cx_ = (p0[0] + p1[0]) / 2 - uy * off
        cy_ = (p0[1] + p1[1]) / 2 + ux * off
        return [((1 - q) ** 2 * p0[0] + 2 * (1 - q) * q * cx_
                 + q * q * p1[0],
                 (1 - q) ** 2 * p0[1] + 2 * (1 - q) * q * cy_
                 + q * q * p1[1]) for q in (i / 24 for i in range(25))]

    def clear(pts_):
        return not any(o[0] < x < o[2] and o[1] < y < o[3]
                       for x, y in pts_[2:-2] for o in obst)
    path = bez(0.0)
    if not clear(path):
        for f in (0.22, -0.22, 0.4, -0.4, 0.6, -0.6):
            cand = bez(span * f)
            if clear(cand):
                path = cand
                break
    rnd = random.Random(int(p0[0]) % 89 + 5)
    pts = [(x + rnd.uniform(-1.1, 1.1), y + rnd.uniform(-1.1, 1.1))
           for x, y in path]
    pts[0], pts[-1] = path[0], path[-1]
    end_ang = math.atan2(path[-1][1] - path[-3][1],
                         path[-1][0] - path[-3][0])
    start_ang = math.atan2(path[0][1] - path[2][1], path[0][0] - path[2][0])

    def head(tip, ang):
        return [[(tip[0], tip[1]),
                 (tip[0] - ah * math.cos(ang + s_ * 0.5),
                  tip[1] - ah * math.sin(ang + s_ * 0.5))]
                for s_ in (-1, 1)]
    col = 'a_red' if kind in ('not', 'vs') else 'ink'
    st = [(pts, col, 0.85, False, True)]
    if kind != 'vs':
        st += [(h, col, 0.85, False, True) for h in head(p1, end_ang)]
    if kind in ('backs', 'is'):
        st += [(h, col, 0.85, False, True) for h in head(p0, start_ang)]
    mid = path[len(path) // 2]
    if kind in ('not', 'vs'):
        r_ = Wc * 0.012
        st += [([(mid[0] - r_, mid[1] - r_), (mid[0] + r_, mid[1] + r_)],
                'a_red', 1.0, False, True),
               ([(mid[0] - r_, mid[1] + r_), (mid[0] + r_, mid[1] - r_)],
                'a_red', 1.0, False, True)]
    return st, (mid, abs(ux) >= abs(uy))


def _sb_link(pb, cb, Wc):
    """Short arrow from box pb toward box cb along their centre line."""
    ax, ay = (pb[0] + pb[2]) / 2, (pb[1] + pb[3]) / 2
    bx, by = (cb[0] + cb[2]) / 2, (cb[1] + cb[3]) / 2
    dx, dy = bx - ax, by - ay
    d = math.hypot(dx, dy)
    if d < 1e-6:
        return None
    ux, uy = dx / d, dy / d

    def exit_t(b, cx, cy, sgn):
        ts = []
        for c0, c1, u, cc in ((b[0], b[2], ux, cx), (b[1], b[3], uy, cy)):
            if abs(u) > 1e-9:
                ts.append(max((c0 - cc) / (sgn * u), (c1 - cc) / (sgn * u)))
        return min(ts) if ts else 0.0
    m = Wc * 0.014
    t0 = exit_t(pb, ax, ay, 1) + m
    t1 = d - exit_t(cb, bx, by, -1) - m
    if t1 - t0 < Wc * 0.02:
        return None
    cap = Wc * 0.075
    if t1 - t0 > cap:
        mid = (t0 + t1) / 2
        t0, t1 = mid - cap / 2, mid + cap / 2
    return _sb_arrow((ax + ux * t0, ay + uy * t0), (ax + ux * t1, ay + uy * t1))


_SB_ATTACH = ('on', 'in', 'beside', 'held', 'under', 'worn', 'activity',
              'behind')
# worn things the face itself draws, and worn things that sit on the head
_SB_EYEWEAR = re.compile(r'\b(glasses|spectacles|goggles|sunglasses|'
                         r'eyeglasses|monocle)\b', re.I)
_SB_HEADWEAR = re.compile(r'\b(hat|cap|helmet|crown|hood|bonnet|beret|'
                          r'headband|headphones|headset|wig)\b', re.I)
_SB_MARKS = ('flow', 'motion', 'puffs', 'cross', 'drips', 'sparkle', 'rain',
             'heat', 'up', 'down')


def _sb_activity(e, fb, flip, shirt, si, qa):
    """Compose a person element's narrated activity (apparatus + posed
    figure + partner art) into box fb -> (body strokes, mark strokes) or
    None when the element has no activity."""
    spec = e['m'].get('activity')
    if not isinstance(spec, dict):
        return None
    part = next((kd for kd in e.get('kids', ())
                 if kd['att'] in ('activity', 'held')
                 and str(kd['m'].get('label') or '')
                 == str(spec.get('partner') or '')), None)
    if part is not None:
        part['drawn'] = True
    back = [kd for kd in e.get('kids', ()) if kd['att'] == 'behind']
    for kd in back:
        kd['drawn'] = True
    role_arts, role_kids = {}, {}
    for rname, rlab in (spec.get('roles') or {}).items():
        kd = next((kd for kd in e.get('kids', ()) if kd['att'] == 'activity'
                   and kd is not part and not kd.get('drawn')
                   and str(kd['m'].get('label') or '') == str(rlab)), None)
        if kd is not None and kd['art']:
            role_arts[rname] = kd['art']
            role_kids[rname] = kd
            kd['drawn'] = True
    got = sb_activity.compose(spec, part['art'] if part else None,
                              e['emo'], e['fit'], shirt, flip,
                              [kd['art'] for kd in back if kd['art']],
                              role_arts,
                              [kd['m'].get('size') or 1.08
                               for kd in back if kd['art']])
    if got is None:
        qa.append({'beat': si, 'check': 'activity-undrawn',
                   'severity': 'fail', 'detail':
                   f'{e["m"].get("label")!r}: {spec.get("schema")}'})
        return None
    strokes, marks, anch, meta = got
    pins = [([anch[k], anch[k]], 'ink', 0.0, False)
            for k in ('hand_n', 'hand_f')]
    pb = meta.get('partner_bounds')
    if pb:
        pins += [([p, p], 'ink', 0.0, False)
                 for p in ((pb[0], pb[1]), (pb[2], pb[3]))]
    fit_st, _fb = _sb_fit(strokes + marks + pins, fb)
    hw = fit_st[len(strokes) + len(marks)][0][0]
    if pb:
        first, last = fit_st[len(strokes) + len(marks) + 2:][:2]
        e['partner_bounds'] = tuple(first[0][0]) + tuple(last[0][0])
    fit_st = fit_st[:len(strokes) + len(marks)]
    e['hand_w'] = hw
    e['act_meta'] = meta
    err = sb_activity.contact_error(meta)
    if err > 0.08:
        qa.append({'beat': si, 'check': 'activity-contact',
                   'severity': 'fail', 'detail':
                   f'{e["m"].get("label")!r} {meta["schema"]}: limb misses '
                   f'its contact by {err:.2f} figure heights'})
    if part is not None and not meta['placed']:
        qa.append({'beat': si, 'check': 'activity-partner',
                   'severity': 'info' if meta['kind'] else 'warn', 'detail':
                   f'{spec.get("partner")!r} drawn by the apparatus only'})
    hidden = {str(m_.get('label') or '') for m_ in e.get('hidden', ())}
    for rname, ok in sorted((meta.get('roles') or {}).items()):
        if not ok and str(spec['roles'][rname]) in hidden:
            qa.append({'beat': si, 'check': 'activity-role',
                       'severity': 'info', 'detail':
                       f'{spec["roles"][rname]!r} ({rname}) drawn as the '
                       'panel setting'})
        elif not ok:
            qa.append({'beat': si, 'check': 'activity-role',
                       'severity': 'fail', 'detail':
                       f'{e["m"].get("label")!r} {meta["schema"]}: '
                       f'{spec["roles"][rname]!r} ({rname}) not drawn '
                       'in the picture'})
        elif rname in role_kids:
            role_kids[rname]['ink'] = _sb_bounds(s_[0] for s_ in fit_st)
    if part is not None and meta['placed']:
        part['ink'] = _sb_bounds(s_[0] for s_ in fit_st)
    qa.append({'beat': si, 'check': 'activity', 'severity': 'info',
               'detail': f'{e["m"].get("label")!r} {meta["schema"]}'
               f'/{meta["kind"] or "-"} via {meta["via"]} '
               f'contact {err:.3f}'})
    return fit_st[:len(strokes)], fit_st[len(strokes):]


def _sb_kid_box(att, hb, aspect, hand=None, act='', flip=False, label=''):
    """Box for an element composed onto its host's ink box hb: a held
    prop sized for the arm pose (a cup at the lips, a shovel to the
    ground), a seat under the hips, a worn thing on the head or body."""
    x0, y0, x1, y1 = hb
    w, h = x1 - x0, y1 - y0
    if att == 'held' and hand and act == 'dig':
        kh = h * sb_cast.PROP_SCALE['dig']
        cx, bot = hand[0], y1
    elif att == 'held' and hand:
        kh = h * sb_cast.PROP_SCALE.get(act, 0.36)
        cx, bot = hand[0], hand[1] + kh * 0.45
    elif att == 'under':
        kh = min(h * 0.40, w * 0.9 / max(0.3, aspect))
        cx, bot = x0 + w * (0.62 if flip else 0.38), y1
    elif att == 'worn' and _SB_HEADWEAR.search(label):
        kh = min(h * 0.16, w * 0.55 / max(0.3, aspect))
        cx, bot = x0 + w * 0.5, y0 + kh * 0.55
    elif att == 'worn':
        kh = min(h * 0.24, w * 0.45 / max(0.3, aspect))
        cx, bot = x0 + w * 0.5, y0 + h * 0.62
    elif att == 'in':
        kh = min(h * 0.42, w * 0.42 / max(0.3, aspect))
        cx, bot = (x0 + x1) / 2, y0 + h * 0.55 + kh / 2
    elif att == 'beside':
        kh = h * 0.55
        cx, bot = x1 + kh * aspect * 0.55, y1
    else:
        kh = min(h * 0.50, w * 0.65 / max(0.3, aspect))
        cx, bot = x0 + w * 0.62, y0 + kh * 0.30
    kw = kh * aspect
    return (cx - kw / 2, bot - kh, cx + kw / 2, bot)


def _sb_vmark(kind, a, b=None, col=None, seed=1):
    """Story detail strokes around ink box a (flow runs a -> b)."""
    x0, y0, x1, y1 = a
    w, h = x1 - x0, y1 - y0
    st = []
    if kind == 'flow' and b is not None:
        p0 = (x1 + w * 0.04, y0 + h * 0.30)
        p1 = (b[0] - (b[2] - b[0]) * 0.04, b[1] + (b[3] - b[1]) * 0.30)
        d = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        cxm = ((p0[0] + p1[0]) / 2, min(p0[1], p1[1]) - d * 0.22)
        r = max(3.4, d * 0.016)
        n = max(6, min(12, int(d / (r * 5))))
        for i in range(1, n):
            t = i / n
            qx = (1 - t) ** 2 * p0[0] + 2 * t * (1 - t) * cxm[0] + t * t * p1[0]
            qy = (1 - t) ** 2 * p0[1] + 2 * t * (1 - t) * cxm[1] + t * t * p1[1]
            st.append((_sb_blob(qx, qy, r, r, seed + i, 8, 0.12),
                       col or 'a_yellow', 1.0, 'solid', True))
        return st
    if kind == 'motion':
        for i, v in enumerate((0.32, 0.50, 0.68)):
            ln = w * (0.22 if i == 1 else 0.15)
            xa = x0 - w * 0.06
            st.append((_wobble_line((xa - ln, y0 + h * v), (xa, y0 + h * v),
                                    n=6, wob=0.8, seed=seed + i),
                       'ink', 0.9, False, True))
        return st
    if kind == 'puffs':
        for i in range(3):
            r = h * (0.06 + 0.035 * i)
            cx = x0 + w * (0.55 + 0.16 * i)
            cy = y0 - h * (0.02 + 0.15 * i) - r
            for k_, (dx, dy, rr) in enumerate(((-0.55, 0.15, 0.62),
                                               (0.0, -0.1, 0.8),
                                               (0.55, 0.15, 0.62))):
                blob = _sb_blob(cx + dx * r, cy + dy * r, rr * r * 1.1,
                                rr * r, seed + i * 3 + k_, 14, 0.10)
                st.append((blob, col or 'pale', 1.0, 'solid', True))
                st.append((blob, 'ink', 0.55, False, True))
        return st
    if kind == 'cross':
        ix, iy = w * 0.10, h * 0.10
        st.append((_wobble_line((x0 + ix, y0 + iy), (x1 - ix, y1 - iy),
                                n=10, wob=1.4, seed=seed), col or 'a_red',
                   2.4, False, True))
        st.append((_wobble_line((x1 - ix, y0 + iy), (x0 + ix, y1 - iy),
                                n=10, wob=1.4, seed=seed + 1), col or 'a_red',
                   2.4, False, True))
        return st
    if kind == 'drips':
        for i, u in enumerate((0.35, 0.52, 0.68)):
            cx, cy = x0 + w * u, y1 + h * (0.06 + 0.04 * (i % 2))
            r = h * 0.035
            drop = [(cx, cy - r * 2.2)] + [
                (cx + math.cos(t) * r, cy + math.sin(t) * r)
                for t in [-0.35 + (math.pi + 0.7) * k / 10 for k in range(11)]
            ] + [(cx, cy - r * 2.2)]
            st.append((drop, col or 'a_yellow', 1.0, 'solid', True))
            st.append((drop, 'ink', 0.7, False, True))
        return st
    if kind == 'sparkle':
        for i, (u, v) in enumerate(((-0.06, 0.05), (1.06, 0.12),
                                    (0.98, -0.08))):
            cx, cy, r = x0 + w * u, y0 + h * v, h * (0.05 + 0.015 * i)
            st.append(([(cx - r, cy), (cx + r, cy)], col or 'a_yellow', 1.6,
                       False, True))
            st.append(([(cx, cy - r), (cx, cy + r)], col or 'a_yellow', 1.6,
                       False, True))
        return st
    if kind == 'rain':
        for i in range(5):
            xa = x0 + w * (0.12 + 0.19 * i)
            ya = y0 - h * (0.10 + 0.07 * (i % 2))
            st.append(([(xa, ya), (xa - w * 0.04, ya + h * 0.09)],
                       col or 'a_blue', 1.5, False, True))
        return st
    if kind == 'heat':
        for i in range(3):
            xa = x0 + w * (0.28 + 0.22 * i)
            pts = [(xa + math.sin(k * 1.3) * w * 0.025,
                    y0 - h * 0.04 - k * h * 0.035) for k in range(7)]
            st.append((pts, col or 'a_orange', 1.4, False, True))
        return st
    if kind in ('up', 'down'):
        up = kind == 'up'
        xa, xb = x1 + w * 0.04, x1 + w * 0.22
        ya, yb = (y0 + h * 0.45, y0 + h * 0.05) if up else (
            y0 + h * 0.05, y0 + h * 0.45)
        return _sb_colorize(_sb_arrow((xa, ya), (xb, yb)),
                            col or ('a_green' if up else 'a_red'))
    return st


def _sb_colorize(strokes, col):
    return [(st[0], col) + tuple(st[2:]) for st in strokes]


_SB_PREFIX = re.compile(r'^\s*(before|after|then|now)\s*[:\-]\s*', re.I)
_SB_LSTOP = {'the', 'a', 'an', 'of', 'and', 'to', 'in', 'on', 'is', 'are',
             'its', 'it', 'for', 'with'}


def _sb_words(text):
    out = set()
    for w in re.findall(r'[a-z]+', str(text or '').lower()):
        if w in _SB_LSTOP or len(w) < 3:
            continue
        out.add(w[:-1] if w.endswith('s') and len(w) > 3 else w)
    return out


_SB_SETTINGS = (
    ('river', r'\b(rivers?|riverbanks?|streams?|lakes?|ponds?|fish\w*|dams?|'
              r'creeks?|shores?|beavers?)\b'),
    ('city', r'\b(city|cities|downtown|traffic|commut\w*|streets?|lanes?|'
             r'bus(es)?|skyline)\b'),
    ('road', r'\b(roads?|highways?|cars?|drivers?|bicycles?|bridges?|'
             r'trucks?|trains?)\b'),
    ('forest', r'\b(forests?|woods|woodlands?|pines?|trees?|wol(f|ves)|'
               r'deer|campfires?|logs?|seedlings?|willows?|rangers?)\b'),
    ('field', r'\b(farm\w*|fields?|crops?|orchards?|hillsides?|harvest\w*|'
              r'bush(es)?|meadows?|grass|pastures?|cherr\w*)\b'),
    ('ward', r'\b(hospitals?|clinics?|wards?|patients?|nurses?|doctors?|'
             r'beds?|staff)\b'),
    ('sea', r'\b(seas?|oceans?|waves?|coasts?|ships?|boats?|sailors?|'
            r'reefs?|lighthouses?|harbou?rs?|beach\w*|lifeboats?)\b'),
    ('cafe', r'\b(kitchens?|cafes?|baristas?|coffee|cups?|mugs?|roast\w*|'
             r'filters?|grind\w*)\b'),
)
_SB_ON_WATER = re.compile(
    r'\b(boats?|ships?|lifeboats?|canoes?|kayaks?|rafts?|yachts?|ferr(y|ies)|'
    r'piers?|docks?|jett(y|ies)|wharf|swim\w*|rows?|rowing|fish\w*|'
    r'ducks?|swans?|whales?|dolphins?)\b', re.I)
_SB_OUTDOOR = ('river', 'city', 'road', 'forest', 'field', 'sea')


def _sb_word_cues(grp, wt, a_, b_, win1, mo_win, log):
    """Each drawing of a sentence starts when its own word is spoken and
    draws until the next one starts; drawings whose word is not heard
    keep their even share of the sentence."""
    heard = [(w[0], float(w[1])) for w in wt
             if a_ - 1.5 <= float(w[1]) < b_ + 1.0]
    cue = {}
    for e in grp:
        roles = [e] + list(e.get('kids', ()))
        words = re.findall(r"[a-z0-9']+", ' '.join(
            str(role['it'].get(k) or '') for role in roles
            for k in ('label', 'annotate', 'cast_key')).lower())
        for tok, at in heard:
            if tok in words or tok.rstrip('s') in words:
                cue[id(e)] = max(a_, min(at, b_ - 0.3))
                break
    if not cue:
        return
    order = sorted(grp, key=lambda e: cue.get(id(e), mo_win[id(e)][0]))
    starts = [cue.get(id(e), mo_win[id(e)][0]) for e in order]
    for k, e in enumerate(order):
        s0 = max(starts[k], starts[k - 1] + 0.25) if k else starts[k]
        starts[k] = s0
        nxt = starts[k + 1] if k + 1 < len(order) else b_
        mo_win[id(e)] = (s0, min(win1, max(s0 + 0.35,
                                          min(nxt, s0 + 1.0))))
        log.append((str(e['it'].get('label') or ''), round(s0, 2),
                    cue.get(id(e))))


def _sb_water_patch(bb):
    """Two short wave strokes under a thing that sits on water."""
    x0, _, x1, y1 = bb
    pw = (x1 - x0) * 0.35
    out = []
    for k in range(2):
        y = y1 + 3 + k * 6
        a, b = x0 - pw * (1 - 0.4 * k), x1 + pw * (1 - 0.4 * k)
        n = max(3, int((b - a) / 14))
        out.append(([(a + (b - a) * i / n, y + (2.2 if i % 2 else -2.2))
                     for i in range(n + 1)], 'a_blue', 0.9, False, True))
    return out


def _sb_panel_layout(sol, L, R, band_t, band_b, lane, labw, progressive=False,
                     figure_unit=None):
    """Story panels: one framed picture per narrated moment. Everyone in a
    panel stands on its floor at one figure unit; people in contact close
    the gap, a lap sitter sits on the host's lap. -> {moment: rect}."""
    cells: dict = {}
    for e in sol:
        cells.setdefault(int(e['m'].get('moment') or 0), []).append(e)
    ks = sorted(cells)
    Wc, bh = R - L, band_b - band_t
    unit_limit = figure_unit

    def lap_host(e, es):
        lab = str(e['m'].get('lap_of') or '')
        return next((o for o in es if o is not e and o['kind'] == 'person'
                     and str(o['m'].get('label') or '') == lab), None) \
            if lab else None

    def touching(a, b):
        for x, y in ((a, b), (b, a)):
            t = x['m'].get('touch') or ()
            if any(str(y['m'].get(key) or '') in t
                   for key in ('label', 'cast_key', 'group')):
                return True
        return False

    def fill(rect, es, apply):
        x0, y0, x1, y1 = rect
        pad = 0.05 * min(x1 - x0, y1 - y0)
        flow = [e for e in es if lap_host(e, es) is None]
        lanes = max([lane(e) for e in flow] + [0.0])
        floor = y1 - pad - lanes
        avail = floor - (y0 + pad * 1.6)

        def rel(e):
            return e['rel'] if e['kind'] == 'person' else max(
                0.16, float(e['m'].get('size') or 0.34)) * 1.25
        def widths(row, unit):
            hs = [unit * rel(e) for e in row]
            # a person's strokes (gestures, props) run wider than the
            # nominal figure aspect — space for the ink, not the slot
            ws = [max(h * e['aspect'] * (1.18 if e['kind'] == 'person'
                                         else 1.0), labw(e) * 1.04)
                  for h, e in zip(hs, row)]
            gaps = [-0.14 * min(wa, wb) if touching(a, b)
                    else (x1 - x0) * 0.04
                    for a, b, wa, wb in zip(row, row[1:], ws, ws[1:])]
            return hs, ws, gaps

        available = x1 - x0 - 2 * pad

        def fit(row, floor_y, cap=None):
            """Largest figure unit `row` can stand on `floor_y`."""
            av = floor_y - (y0 + pad * 1.6)
            u = min(av / max([rel(e) for e in row] + [1.0]),
                    (0.64 if progressive else 0.40) * bh)
            if cap is not None:
                u = min(u, cap)
            hs, ws, gaps = widths(row, u)
            if sum(ws) + sum(gaps) > available:
                low, high = 0.0, u
                for _ in range(24):
                    middle = (low + high) / 2
                    _, mw, mg = widths(row, middle)
                    if sum(mw) + sum(mg) > available:
                        high = middle
                    else:
                        low = middle
                u = low
                hs, ws, gaps = widths(row, u)
            return u, hs, ws, gaps

        # one figure unit for the whole board, whatever the panel grid
        u, hs, ws, gaps = fit(flow, floor, unit_limit)
        front = flow
        back_floor = floor
        back = ()
        if progressive:
            # a cell that cannot fit one row stands on two levels: wide
            # backdrop art rises to a shared horizon behind the people,
            # so the floor keeps its figure unit on tall boards
            tied = set()
            for a in flow:
                for b in flow:
                    if a is not b and (touching(a, b) or touching(b, a)):
                        tied.update((id(a), id(b)))
                act = a['m'].get('activity') or {}
                for nm in (act.get('partner'), a['m'].get('target')):
                    if nm is None:
                        continue
                    for o in flow:
                        if str(nm) in (str(o['m'].get('label') or ''),
                                       str(o['m'].get('cast_key') or ''),
                                       str(o.get('ri'))):
                            tied.add(id(o))
            cand = [e for e in flow
                    if e['kind'] == 'art' and id(e) not in tied
                    and e['aspect'] >= 0.85 and rel(e) >= 0.5]
            if cand and len(cand) < len(flow):
                keep = [e for e in flow if e not in cand]
                u_f, hs_f, ws_f, gaps_f = fit(keep, floor, unit_limit)
                if u_f > u * 1.12:
                    bf = floor - max(hs_f or [u_f]) * 0.5
                    u_b, hs_b, ws_b, gaps_b = fit(cand, bf)
                    if u_b >= u_f * 0.30:
                        front, back_floor = keep, bf
                        back = (cand, u_b, hs_b, ws_b, gaps_b)
                        u, hs, ws, gaps = u_f, hs_f, ws_f, gaps_f
        tot = sum(ws) + sum(gaps)
        k = min(1.0, (x1 - x0 - 2 * pad) / max(1e-6, tot))
        # a row that only fits by crushing to slivers stands on two
        # levels instead: the first half takes a raised floor
        if k < 0.60 and not back and len(flow) > 2:
            half = (len(flow) + 1) // 2
            keep, cand2 = flow[half:], flow[:half]
            u_f, hs_f, ws_f, gaps_f = fit(keep, floor, unit_limit)
            bf = floor - max(hs_f or [u_f]) * 0.55
            u_b, hs_b, ws_b, gaps_b = fit(cand2, bf)
            if u_b > 0:
                front, back_floor = keep, bf
                back = (cand2, u_b, hs_b, ws_b, gaps_b)
                u, hs, ws, gaps = u_f, hs_f, ws_f, gaps_f
                tot = sum(ws) + sum(gaps)
                k = min(1.0, (x1 - x0 - 2 * pad) / max(1e-6, tot))
        if not apply:
            return u * k
        if back:
            cand_, u_b, hs_b, ws_b, gaps_b = back
            tot_b = sum(ws_b) + sum(gaps_b)
            kb = min(1.0, (x1 - x0 - 2 * pad) / max(1e-6, tot_b))
            x = x0 + (x1 - x0 - tot_b * kb) / 2
            for i, (e, h, w) in enumerate(zip(cand_, hs_b, ws_b)):
                h, w = h * kb, w * kb
                aw = h * e['aspect']
                cx = x + w / 2
                bottom = back_floor
                if e['m'].get('label', '').split()[-1:] == ['window']:
                    bottom -= u_b * 0.6
                e['box'] = (cx - aw / 2, bottom - h, cx + aw / 2, bottom)
                e['figure_unit'] = u_b * kb
                e['on_back'] = True
                x += w + (gaps_b[i] * kb if i < len(gaps_b) else 0.0)
        x = x0 + (x1 - x0 - tot * k) / 2
        cxs = []
        for i, (e, h, w) in enumerate(zip(front, hs, ws)):
            h, w = h * k, w * k
            aw = h * e['aspect']
            cx = x + w / 2
            bottom = floor
            if e['kind'] == 'art' and e['m'].get('label', '').split()[-1:] \
                    == ['window']:
                bottom -= u * 0.6
            e['box'] = (cx - aw / 2, bottom - h, cx + aw / 2, bottom)
            e['figure_unit'] = u * k
            cxs.append(cx)
            x += w + (gaps[i] * k if i < len(gaps) else 0.0)
        mid = sum(cxs) / max(1, len(cxs))
        for e, cx in zip(front, cxs):
            if e['kind'] != 'person':
                continue
            gaze = e['m'].get('face_to')
            peer = next((o for o in flow if o is not e and gaze
                         and gaze in (o['m'].get('label'),
                                      o['m'].get('cast_key'))), None)
            if peer is None:
                peer = next((o for o in flow if o is not e and touching(e, o)),
                            None)
            tx = ((peer['box'][0] + peer['box'][2]) / 2 if peer is not None
                  else mid if len(flow) > 1 else (x0 + x1) / 2)
            e['face'] = 1 if tx >= cx else -1
            if abs(tx - cx) < 1.0:
                e['face'] = 1 if cx < (x0 + x1) / 2 else -1
        for helper in flow:
            if not (helper['m'].get('activity') or {}).get('shared_partner'):
                continue
            primary = next((e for e in flow if e is not helper
                            and helper['m'].get('shared_with') in (
                                e['m'].get('cast_key'), e['m'].get('label'))),
                           None)
            if primary is None or not primary.get('preview') \
                    or not helper.get('preview'):
                continue
            p, q = primary['preview'], helper['preview']
            if not p['partner']:
                continue
            primary['face'], helper['face'] = 1, -1
            pb, qb = p['bounds'], q['bounds']
            target = primary['box'][0] + (
                p['partner'][2] - pb[0]) / (pb[2] - pb[0]) * (
                    primary['box'][2] - primary['box'][0])
            hand = helper['box'][0] + (
                qb[2] - q['hand'][0]) / (qb[2] - qb[0]) * (
                    helper['box'][2] - helper['box'][0])
            dx = target - hand
            helper['box'] = tuple(v + dx if i % 2 == 0 else v
                                  for i, v in enumerate(helper['box']))
        for e in es:
            host = lap_host(e, es)
            if host is None or not host.get('box'):
                continue
            hb = host['box']
            hh = hb[3] - hb[1]
            h = hh * min(0.62, e['rel'] / max(0.2, host['rel']) * 0.85)
            w = h * e['aspect']
            f = host.get('face', 1)
            cx = (hb[0] + hb[2]) / 2 + f * (hb[2] - hb[0]) * 0.22
            yb = hb[3] - hh * (0.42 if e['m'].get('held') else 0.30)
            e['box'] = (cx - w / 2, yb - h, cx + w / 2, yb)
            e['figure_unit'] = host['figure_unit']
            e['face'] = f
            e['on_lap'] = host
        return u * k

    if progressive:
        rect = (L, band_t, R, band_b)
        limits = [fill(rect, cells[k_], False) for k_ in ks]
        if figure_unit is not None:
            limits.append(figure_unit)
        unit_limit = min(limits)
        for k_ in ks:
            fill(rect, cells[k_], True)
            for e in cells[k_]:
                e['panel'] = k_
        return {k_: rect for k_ in ks}
    best = None
    for nr in (1, 2):
        if nr > len(ks):
            break
        nc = -(-len(ks) // nr)
        g = Wc * 0.022
        pw = (Wc - g * (nc - 1)) / nc
        ph = (bh - g * (nr - 1)) / nr
        rects = {}
        for i, k_ in enumerate(ks):
            r_, c_ = divmod(i, nc)
            in_row = min(nc, len(ks) - r_ * nc)
            xo = L + (Wc - (pw * in_row + g * (in_row - 1))) / 2
            rects[k_] = (xo + c_ * (pw + g), band_t + r_ * (ph + g),
                         xo + c_ * (pw + g) + pw, band_t + r_ * (ph + g) + ph)
        score = min(fill(rects[k_], cells[k_], False) for k_ in ks)
        if best is None or score > best[0] * 1.08:
            best = (score, rects)
    rects = best[1]
    for k_ in ks:
        fill(rects[k_], cells[k_], True)
        for e in cells[k_]:
            e['panel'] = k_
    return rects


# room furniture drawn on a panel's back wall, by place kind
_SB_ROOM_PIECES = {
    'kitchen': ('cabinet', 'window', 'shelf'),
    'bedroom': ('window_night', 'frame', 'lamp'),
    'living': ('window', 'frame', 'lamp'),
    'home': ('window', 'frame'),
    'store': ('shelves', 'shelves', 'sign'),
    'office': ('window', 'clock'),
    'classroom': ('board', 'clock'),
    'outdoor': ('tree', 'sun', 'tree'),
    'street': ('house', 'tree'),
}


def _sb_room(kind, rect, floor, solid, seed):
    """Back-wall and floor strokes for one story panel, placed only in
    free paper inside the panel."""
    x0, y0, x1, y1 = rect
    pw, ph = x1 - x0, y1 - y0
    pad = 0.05 * min(pw, ph)
    rnd = random.Random(seed)

    def seg(a, b, col='pale', w=0.9, sd=0):
        return (_wobble_line(a, b, n=5, wob=0.7, seed=seed + sd), col, w,
                False, True)

    def box(bx0, by0, bx1, by1, col='pale', w=0.9, sd=0):
        return [seg((bx0, by0), (bx1, by0), col, w, sd),
                seg((bx1, by0), (bx1, by1), col, w, sd + 1),
                seg((bx1, by1), (bx0, by1), col, w, sd + 2),
                seg((bx0, by1), (bx0, by0), col, w, sd + 3)]

    def clear(bb):
        return all(not (bb[0] - 6 < B[2] and B[0] < bb[2] + 6
                        and bb[1] - 6 < B[3] and B[1] < bb[3] + 6)
                   for B in solid)

    st = [seg((x0 + pad * 0.5, floor + 2), (x1 - pad * 0.5, floor + 2),
              'ink', 0.9, 99)]
    wall = floor - (y0 + pad)
    base_u = min(pw * 0.22, wall * 0.42)
    pieces = _SB_ROOM_PIECES.get(
        kind, ('window', 'frame', 'clock') if kind else ())
    for n_, pk in enumerate(pieces):
        slots = []
        for factor in (1.0, 0.72, 0.52):
            u = base_u * factor
            xs = [x0 + pad + u * 0.1, x1 - pad - u * 1.1,
                  (x0 + x1) / 2 - u / 2]
            slots.extend((tx, u) for tx in xs[n_:] + xs[:n_])
        for tx, u in slots:
            ty = y0 + pad * 1.2
            if pk in ('tree', 'lamp', 'house', 'shelves'):
                ty = floor - u * (1.5 if pk == 'shelves' else 1.2)
            h_ = u * (1.5 if pk == 'shelves' else 1.2
                      if pk in ('tree', 'lamp', 'house') else 0.8)
            bb = (tx, ty, tx + u, ty + h_)
            if not clear(bb) or bb[1] < y0 + 2:
                continue
            p_ = []
            if pk in ('window', 'window_night'):
                p_ += box(tx, ty, tx + u, ty + h_, sd=n_ * 10)
                p_.append(seg((tx + u / 2, ty), (tx + u / 2, ty + h_),
                              sd=n_ * 10 + 5))
                p_.append(seg((tx, ty + h_ / 2), (tx + u, ty + h_ / 2),
                              sd=n_ * 10 + 6))
                if pk == 'window_night':
                    mx, my, mr = tx + u * 0.72, ty + h_ * 0.24, u * 0.09
                    p_.append(([(mx + mr * math.cos(a), my + mr * math.sin(a))
                                for a in [i * 0.3 for i in range(22)]],
                               'a_yellow', 0.9, False, True))
            elif pk == 'cabinet':
                p_ += box(tx, ty, tx + u * 0.48, ty + h_ * 0.8, sd=n_ * 10)
                p_ += box(tx + u * 0.52, ty, tx + u, ty + h_ * 0.8,
                          sd=n_ * 10 + 4)
            elif pk == 'shelf':
                p_.append(seg((tx, ty + h_ * 0.7), (tx + u, ty + h_ * 0.7),
                              sd=n_ * 10))
                for j in range(3):
                    jx = tx + u * (0.12 + 0.3 * j)
                    p_ += box(jx, ty + h_ * 0.38, jx + u * 0.16,
                              ty + h_ * 0.7, sd=n_ * 10 + 3 + j)
            elif pk == 'frame':
                p_ += box(tx + u * 0.15, ty, tx + u * 0.85, ty + h_ * 0.8,
                          sd=n_ * 10)
                p_.append(seg((tx + u * 0.25, ty + h_ * 0.65),
                              (tx + u * 0.5, ty + h_ * 0.3), sd=n_ * 10 + 5))
                p_.append(seg((tx + u * 0.5, ty + h_ * 0.3),
                              (tx + u * 0.75, ty + h_ * 0.65),
                              sd=n_ * 10 + 6))
            elif pk == 'lamp':
                p_.append(seg((tx + u / 2, ty + h_ * 0.3),
                              (tx + u / 2, ty + h_), sd=n_ * 10))
                p_.append(([(tx + u * 0.25, ty + h_ * 0.3),
                            (tx + u * 0.38, ty), (tx + u * 0.62, ty),
                            (tx + u * 0.75, ty + h_ * 0.3),
                            (tx + u * 0.25, ty + h_ * 0.3)], 'a_yellow', 0.9,
                           False, True))
            elif pk == 'shelves':
                for j in range(4):
                    yy = ty + h_ * (0.25 * j + 0.2)
                    p_.append(seg((tx, yy), (tx + u, yy), sd=n_ * 10 + j))
                    for q in range(3):
                        qx = tx + u * (0.08 + 0.3 * q)
                        p_ += box(qx, yy - h_ * 0.12, qx + u * 0.2, yy,
                                  sd=n_ * 10 + 20 + j * 3 + q)
                p_.append(seg((tx, ty + h_ * 0.08), (tx, ty + h_ + 1),
                              sd=n_ * 10 + 40))
                p_.append(seg((tx + u, ty + h_ * 0.08), (tx + u, ty + h_ + 1),
                              sd=n_ * 10 + 41))
            elif pk == 'sign':
                p_ += box(tx, ty, tx + u, ty + h_ * 0.35, 'a_red', 0.9,
                          n_ * 10)
            elif pk == 'clock':
                cx_, cy_, cr = tx + u / 2, ty + h_ * 0.4, u * 0.2
                p_.append(([(cx_ + cr * math.cos(a), cy_ + cr * math.sin(a))
                            for a in [i * 0.3 for i in range(22)]], 'pale',
                           0.9, False, True))
                p_.append(seg((cx_, cy_), (cx_, cy_ - cr * 0.7), sd=n_))
                p_.append(seg((cx_, cy_), (cx_ + cr * 0.5, cy_), sd=n_ + 1))
            elif pk == 'board':
                p_ += box(tx - u * 0.3, ty, tx + u * 1.3, ty + h_ * 0.8,
                          'a_green', 0.9, n_ * 10)
            elif pk == 'tree':
                p_.append(seg((tx + u / 2, ty + h_), (tx + u / 2,
                              ty + h_ * 0.45), 'ink', 0.9, n_))
                p_.append(([(tx + u / 2 + u * 0.4 * math.cos(a),
                             ty + h_ * 0.3 + u * 0.35 * math.sin(a))
                            for a in [i * 0.3 for i in range(22)]],
                           'a_green', 0.9, False, True))
            elif pk == 'sun':
                cx_, cy_, cr = tx + u / 2, ty + h_ * 0.3, u * 0.16
                p_.append(([(cx_ + cr * math.cos(a), cy_ + cr * math.sin(a))
                            for a in [i * 0.3 for i in range(22)]],
                           'a_yellow', 0.9, False, True))
            elif pk == 'house':
                p_ += box(tx, ty + h_ * 0.4, tx + u, ty + h_, sd=n_ * 10)
                p_.append(seg((tx, ty + h_ * 0.4), (tx + u / 2, ty),
                              sd=n_ * 10 + 5))
                p_.append(seg((tx + u / 2, ty), (tx + u, ty + h_ * 0.4),
                              sd=n_ * 10 + 6))
            if p_:
                solid.append(bb)
                st += p_
                break
    rnd.random()
    return st


def _sb_setting_kind(scn, beat):
    """Where the beat happens — declared `scene.setting`, else the place
    its narration names most ('none' disables the backdrop)."""
    s = str(scn.get('setting') or '').lower().strip()
    if s:
        return '' if s == 'none' else s
    txt = ' '.join(str(beat.get(k) or '') for k in ('narration', 'caption'))
    best, n_best = '', 0
    for kind, pat in _SB_SETTINGS:
        n = len(re.findall(pat, txt, re.I))
        if n > n_best:
            best, n_best = kind, n
    return best


def _sb_setting(kind, txt, L, R, band_t, base, floor, boxes, seed):
    """Backdrop strokes for a setting, drawn only into free paper: every
    piece is dropped where it would touch an element, label, arrow, mark,
    title or caption, so the context never interferes with the story."""
    rnd = random.Random(seed)
    Wc = R - L
    solid = [bx[1] for bx in boxes]
    labels = [bx[1] for bx in boxes if bx[2] != 'el' and bx[2] != 'rider'
              and bx[2] != 'chart']

    def clear(bb, pad, against):
        return not any(bb[0] - pad < B[2] and B[0] < bb[2] + pad
                       and bb[1] - pad < B[3] and B[1] < bb[3] + pad
                       for B in against)

    def line(y, against, col='ink', w=1.0, wob=1.2, seg=26, dash=False):
        out = []
        n = seg
        xs = [L + Wc * i / n for i in range(n + 1)]
        for i in range(n):
            if dash and i % 2:
                continue
            p0, p1 = (xs[i], y), (xs[i + 1] + (0 if dash else 1.5), y)
            if not clear((p0[0], y - 3, p1[0], y + 3), 4.0, against):
                continue
            out.append((_wobble_line(p0, p1, n=4, wob=wob, seed=seed + i),
                        col, w, False, True))
        return out

    def piece(strokes, pad=6.0):
        bb = _sb_bounds(s_[0] for s_ in strokes)
        if bb and bb[1] >= band_t - 2 and clear(bb, pad, solid):
            solid.append(bb)
            return strokes
        return []

    def slots(n, y_hint):
        xs = [L + Wc * (i + 0.5) / n for i in range(n)]
        rnd.shuffle(xs)
        return xs

    st = []
    under = [b for b in labels]
    if kind in ('river', 'field', 'forest', 'road', 'city', 'ward', 'cafe',
                'sea'):
        st += line(base + 2, under, 'ink', 1.0)
    lane = max(8.0, floor - base)
    if kind in ('road', 'city'):
        y2 = base + lane * 0.95
        st += line(y2, labels, 'ink', 1.0)
        st += line((base + y2) / 2, labels, 'pale', 0.9, dash=True, seg=30)
    h_band = base - band_t
    if kind == 'city':
        for x in slots(9, base):
            bw = Wc * rnd.uniform(0.045, 0.07)
            bh = h_band * rnd.uniform(0.28, 0.5)
            x0, y0 = x - bw / 2, base - bh
            bl = [(_wobble_line((x0, base), (x0, y0), n=5, wob=0.8,
                                seed=seed + int(x)), 'pale', 0.9, False, True),
                  (_wobble_line((x0, y0), (x0 + bw, y0), n=5, wob=0.8,
                                seed=seed + int(x) + 1), 'pale', 0.9, False,
                   True),
                  (_wobble_line((x0 + bw, y0), (x0 + bw, base), n=5, wob=0.8,
                                seed=seed + int(x) + 2), 'pale', 0.9, False,
                   True)]
            for r_ in range(2):
                for c_ in range(2):
                    wx = x0 + bw * (0.22 + 0.36 * c_)
                    wy = y0 + bh * (0.16 + 0.22 * r_)
                    bl.append(([(wx, wy), (wx + bw * 0.2, wy),
                                (wx + bw * 0.2, wy + bh * 0.1),
                                (wx, wy + bh * 0.1), (wx, wy)],
                               'pale', 0.7, False, True))
            st += piece(bl)
    if kind in ('forest', 'river'):
        for x in slots(10, base)[:6 if kind == 'forest' else 3]:
            th = h_band * rnd.uniform(0.22, 0.36)
            tw = th * 0.5
            tree = [([(x, base), (x, base - th * 0.25)], 'ink', 0.9, False,
                     True)]
            for t_ in range(3):
                yb_ = base - th * (0.22 + 0.24 * t_)
                ww = tw * (1.0 - 0.25 * t_) / 2
                tree.append(([(x - ww, yb_), (x, yb_ - th * 0.36),
                              (x + ww, yb_), (x - ww, yb_)], 'a_green',
                             0.9, False, True))
            st += piece(tree)
    if kind in ('field', 'forest', 'river'):
        for x in slots(14, base)[:7]:
            g = []
            for d in (-1, 0, 1):
                hh = h_band * rnd.uniform(0.04, 0.07)
                g.append(([(x + d * 5, base), (x + d * 9, base - hh)],
                          'a_green', 0.9, False, True))
            st += piece(g, 3.0)
    if kind == 'field':
        pts = [(L + Wc * i / 40, base - h_band * (0.30 + 0.12 * math.sin(
            math.pi * i / 40 * 1.6 + 0.4))) for i in range(41)]
        run = []
        for a, b in zip(pts, pts[1:]):
            if clear((min(a[0], b[0]), min(a[1], b[1]) - 2, max(a[0], b[0]),
                      max(a[1], b[1]) + 2), 6.0, solid):
                run.append(a)
            else:
                if len(run) > 2:
                    st.append((run + [a], 'a_green', 0.9, False, True))
                run = []
        if len(run) > 2:
            st.append((run, 'a_green', 0.9, False, True))
    if kind in ('ward', 'cafe'):
        if kind == 'cafe':
            st += line(base + lane * 0.45, labels, 'pale', 0.9)
    if kind in _SB_OUTDOOR:
        sunny = re.search(r'\b(sun\w*|drought|hot|summer|dry|heat)\b', txt,
                          re.I)
        for x in (R - Wc * 0.08, L + Wc * 0.08, R - Wc * 0.25,
                  L + Wc * 0.25, (L + R) / 2):
            y = band_t + h_band * 0.10
            if sunny:
                r = h_band * 0.07
                sp = [(_sb_blob(x, y, r, r, seed + 3, 16, 0.04), 'a_yellow',
                       1.0, False, True)]
                for a in range(8):
                    an = a * math.pi / 4
                    sp.append(([(x + math.cos(an) * r * 1.4,
                                 y + math.sin(an) * r * 1.4),
                                (x + math.cos(an) * r * 1.9,
                                 y + math.sin(an) * r * 1.9)],
                               'a_yellow', 1.0, False, True))
            else:
                r = h_band * 0.05
                sp = [(_sb_blob(x + dx * r, y + dy * r, rr * r * 1.2, rr * r,
                                seed + k, 14, 0.06), 'pale', 0.9, False,
                       True) for k, (dx, dy, rr) in enumerate(
                           ((-1.0, 0.2, 0.8), (0.0, -0.2, 1.1),
                            (1.1, 0.2, 0.8)))]
            got = piece(sp, 10.0)
            if got:
                st += got
                break
    return st


def _sb_scene(sec, si, plan, W, H, t0, t1, fade, uid, figure_unit=None,
              fill_unit=None, band_floor=None, pre_groups=None):
    """Compose one storyboard scene; fills sec['title_st'/'items2'] and
    returns the next uid."""
    beat = sec['beat']
    items = sec['items']
    sw_col = _SWASH[si % len(_SWASH)]
    mx = W * 0.065
    Wc = W - 2 * mx
    L, R = -W / 2 + mx, W / 2 - mx
    top = -H / 2 + H * 0.075 + (H * 0.10 if si == 0 else 0)
    audit = []
    boxes = []                      # (name, box, tag)

    tst, title_bb = [], (L, top, L, top)
    sec['title_st'] = tst

    # ---- caption ------------------------------------------------------
    cap = str(beat.get('caption') or '').strip()
    cs = H * 0.058
    cap_st, cap_bb = [], None
    cap_top = H / 2 - H * 0.07
    if cap:
        # the caption must live inside the frame-safe edge: shrink to
        # the font floor, then wrap at a balanced word split
        safe_w = W * 0.92
        while font_text_width(cap, cs, _SB_FL) > safe_w and cs > H * 0.03:
            cs *= 0.95
        lines = [cap]
        if font_text_width(cap, cs, _SB_FL) > safe_w:
            ws_ = cap.split()
            if len(ws_) > 1:
                k_ = min(range(1, len(ws_)),
                         key=lambda k: abs(
                             font_text_width(' '.join(ws_[:k]), cs, _SB_FL)
                             - font_text_width(' '.join(ws_[k:]), cs,
                                               _SB_FL)))
                lines = [' '.join(ws_[:k_]), ' '.join(ws_[k_:])]
        cw_, chh, ctop = _sb_text_dims(lines, cs, _SB_FL)
        cy = H / 2 - H * 0.105 - chh - ctop
        cap_st, cap_bb = _sb_text(lines, 0.0, cy, cs, _SB_FL, 'center')
        uy = cap_bb[3] + H * 0.018
        und = _wobble_line((cap_bb[0] + cw_ * 0.02, uy),
                           (cap_bb[2] - cw_ * 0.02, uy),
                           n=22, wob=1.4, seed=si * 13 + 5)
        cap_st.append((und, sw_col, 2.3, False, True))
        cap_bb = (cap_bb[0], cap_bb[1], cap_bb[2], uy + 3)
        cap_top = cap_bb[1]
        boxes.append(('caption', cap_bb, 'caption'))

    band_t = title_bb[3] + H * 0.055
    if band_floor is not None:
        band_t = max(band_t, band_floor)
    band_b = cap_top - H * 0.065
    band_h = band_b - band_t
    sec['content'] = (L, band_t, Wc, band_h)

    # ---- element model -------------------------------------------------
    scn = beat.get('scene') or {}
    raw_roles = ([scn.get('heroRole') or {}]
                 + list(scn.get('supportingRoles') or []))
    ris = _sb_role_indices(items, raw_roles)
    meta = [(raw_roles[ri] if ri < len(raw_roles) else {}) for ri in ris]
    meta = [dict(m) if isinstance(m, dict) else {'label': str(m)}
            for m in meta]
    qa = plan.setdefault('_sb_qa', [])
    cap_words = _sb_words(beat.get('caption'))
    nar_sents = re.split(r'(?<=[.!?])\s+', str(beat.get('narration') or ''))
    role_words = [_sb_words(' '.join([str(m.get('label') or ''),
                                      str(m.get('icon') or '')]))
                  for m in meta]
    for j, m in enumerate(meta):
        ant = str(m.get('annotate') or '').strip()
        pm = _SB_PREFIX.match(ant)
        if pm:
            side = pm.group(1).lower()
            m.setdefault('side', 'before' if side in ('before', 'then')
                         else 'after')
            ant = ant[pm.end():].strip()
        aw = _sb_words(ant)
        if ant and aw and scn.get('layout') != 'graph' and (
                aw <= role_words[j] or aw <= cap_words):
            qa.append({'beat': si, 'check': 'label-redundant',
                       'severity': 'info', 'detail': ant})
            ant = ''
        if ant and aw and not (aw & role_words[j]):
            owners = [i for i, rw in enumerate(role_words)
                      if i != j and aw & rw]
            if owners:
                qa.append({'beat': si, 'check': 'label-misbound',
                           'severity': 'fail', 'detail':
                           f'"{ant}" on {m.get("label")!r} names '
                           f'{meta[owners[0]].get("label")!r}'})
        m['annotate'] = ant
        if not m.get('narration'):
            lw = _sb_words(m.get('label'))
            m['narration'] = next((x for x in nar_sents
                                   if lw & _sb_words(x)), '')
    els = []
    story = str(scn.get('mode') or '') == 'story'
    sec['story_hidden'] = []
    for j, it in enumerate(items):
        m = meta[j]
        if m.get('charted'):
            continue
        if story and (m.get('place') or m.get('surface')
                      or m.get('body_part') or m.get('absorbed')
                      or m.get('worn')):
            # drawn as the panel's room, a floor, a body or a posture
            sec['story_hidden'].append(m)
            continue
        gl = m.get('glyph') or ''
        person = any((g[4] or {}).get('icon') == 'person'
                     for g, _s, _e in it['groups'] if g[4])
        kind = (gl if gl in _SB_GLYPHS else
                ('person' if person else 'art'))
        count = max(1, int(m.get('count') or 1))
        art = [] if gl in _SB_GLYPHS else _sb_item_art(it, count)
        emo, n_body, act_rel, preview = '', 0, 1.0, None
        if kind == 'person':
            emo = sb_cast.emotion_for(dict(m, label=it.get('label', '')))
            body, marks, _hb = sb_cast.figure(
                emo, False, m.get('action', ''),
                sb_cast.shirt_for(m.get('shirt') or m.get('cast_key')
                                  or m.get('label') or it.get('label')
                                  or m.get('concept')),
                outfit=_sb_outfit(m, m.get('outfit'), m.get('label'),
                                  it.get('label'), m.get('concept')))
            art = body + marks
            n_body = len(body)
            bb_ = _sb_bounds(s[0] for s in art)
            act_rel = (bb_[3] - bb_[1]) / sb_cast.H
            spec = m.get('activity')
            partner = next((
                _sb_item_art(items[k], int(mk.get('count') or 1))
                for k, mk in enumerate(meta)
                if mk.get('label') == spec.get('partner')
                and mk.get('to') == ris[j]
                and mk.get('attach') in ('activity', 'held')), None) \
                if isinstance(spec, dict) else None
            pv = sb_activity.compose(
                spec, partner, emo, _sb_outfit(
                    m, m.get('outfit'), m.get('label'), it.get('label'),
                    m.get('concept')),
                sb_cast.shirt_for(m.get('shirt') or m.get('cast_key') or m.get('label')
                                  or it.get('label') or m.get('concept')),
                backdrop=[
                    _sb_item_art(items[k]) for k, mk in enumerate(meta)
                    if mk.get('attach') == 'behind'
                    and mk.get('to') == ris[j]
                    and mk.get('label') in (spec.get('setting') or ())],
                role_arts={rn: _sb_item_art(
                               items[k], int(mk.get('count') or 1))
                           for rn, rl in
                           (spec.get('roles') or {}).items()
                           for k, mk in enumerate(meta)
                           if mk.get('attach') == 'activity'
                            and mk.get('to') == ris[j]
                           and mk.get('label') == rl},
                backdrop_sizes=[
                    mk.get('size') or 1.08 for mk in meta
                    if mk.get('attach') == 'behind'
                    and mk.get('to') == ris[j]
                    and mk.get('label') in (spec.get('setting') or ())]) \
                if isinstance(spec, dict) else None
            if pv is not None:
                # the layout box holds the whole activity picture
                art, n_body = pv[0] + pv[1], len(pv[0])
                ab_ = _sb_bounds(a_[0] for a_ in art)
                preview = {'bounds': ab_, 'hand': pv[2]['hand_n'],
                           'partner': pv[3].get('partner_bounds')}
                act_rel = (ab_[3] - ab_[1]) / sb_activity.H
            elif m.get('activity_miss'):
                qa.append({'beat': si, 'check': 'activity-missing',
                           'severity': 'fail', 'detail':
                           f'{m.get("label")!r} {m["activity_miss"]}s: '
                           'no body schema'})
        if kind in ('person', 'art') and not art:
            continue
        expr = (m.get('bubble') or '') if kind == 'person' else (
            m.get('expression') or '')
        head = 1.0
        aspect = {'stack-list': 1.30, 'crowd': 1.55, 'chart-journey': 1.7,
                  'quantity-chart': 1.7,
                  'divider': 0.0}.get(kind)
        if aspect is None:
            aspect = _sb_art_aspect(art) / head
        rel = {'stack-list': 0.92, 'crowd': 0.60, 'person': 1.0,
               'quantity-chart': 1.0,
               'chart-journey': 1.0, 'divider': 1.0}.get(
                   kind, 0.88 if j == 0 else 0.74)
        if kind == 'person':
            # one cast scale: the box grows/shrinks with the apparatus;
            # a child is a smaller version of the same figure
            rel = act_rel * (sb_cast.CHILD_SCALE
                             if sb_cast.look_for(m)['child'] else 1.0)
        ant = str(m.get('annotate') or '').strip()
        els.append({'j': j, 'ri': ris[j], 'it': it, 'm': m, 'kind': kind,
                    'art': art,
                    'drawn_count': min(count, 9),
                    'emo': emo, 'n_body': n_body,
                    'preview': preview,
                    'focus': bool(m.get('focus')),
                    'aspect': aspect, 'rel': rel, 'head': head,
                    'expr': expr, 'halo': m.get('halo') or '',
                    'rider': m.get('on_chart') or '',
                    'label': _sb_wrap(ant) if ant else [],
                    'rows': [str(r) for r in (m.get('rows') or [])]})
    by_j = {e['ri']: e for e in els}

    def _ref(r):
        if isinstance(r, int):
            return by_j.get(r)
        r = str(r or '').lower().strip()
        return next((e for e in els
                     if r in (str(e['it'].get('label', '')).lower(),
                              str(e['m'].get('label', '')).lower())), None)

    for e in list(els):
        att = str(e['m'].get('attach') or '').lower()
        if att not in _SB_ATTACH or e['kind'] not in ('art', 'person'):
            continue
        host = _ref(e['m'].get('to', 0))
        if (host is None or host is e or host.get('kid_of')
                or e.get('kids') or host['kind'] == 'divider'):
            qa.append({'beat': si, 'check': 'attach-unresolved',
                       'severity': 'warn', 'detail': e['it'].get('label')})
            continue
        host.setdefault('kids', []).append(e)
        e['kid_of'], e['att'] = host, att
        if att == 'beside':
            host['aspect'] *= 1.55
        elif att == 'held':
            host['aspect'] *= 1.25
        if e['label'] and not host['label']:
            host['label'] = e['label']
        els.remove(e)
    rel_ = str(scn.get('relation') or '').lower().strip().replace(
        '-', '_').replace(' ', '_')
    words_ = ' '.join([str(beat.get('title') or ''),
                       str(beat.get('caption') or '')]
                      + [' '.join(e['label']) for e in els]).lower()
    n_ppl = sum(1 for e in els if e['kind'] == 'person')
    if not rel_:
        if any(e['kind'] == 'chart-journey' for e in els):
            rel_ = 'journey'
        elif re.search(r'\b(before|after|then vs now|used to)\b', words_):
            rel_ = 'before_after'
        elif re.search(r'\b(cycle|loop|repeat|flywheel|circular)\b',
                       words_) and len(els) >= 3:
            rel_ = 'cycle'
        elif n_ppl >= 2 and len(els) - n_ppl >= 1:
            rel_ = 'reaction'
        elif (any(e['kind'] == 'divider' for e in els)
              and any(e['kind'] == 'crowd' for e in els)):
            rel_ = 'contrast'
        elif sum(1 for e in els if e['kind'] != 'divider') <= 2:
            rel_ = 'focus'
        else:
            rel_ = 'sequence'
    if rel_ != 'contrast':
        els = [e for e in els if e['kind'] != 'divider']
    sec['divider'] = any(e['kind'] == 'divider' for e in els)
    if rel_ == 'focus':
        solid = [e for e in els if e['kind'] != 'divider']
        hero = next((e for e in solid if e['focus']),
                    next((e for e in solid if e['kind'] == 'person'),
                         solid[0] if solid else None))
        for e in solid:
            e['rel'] = 1.0 if e is hero else 0.55
            e['mid'] = e is not hero
    lay = {'focus': 'focus', 'before_after': 'before_after',
           'cycle': 'cycle', 'reaction': 'reaction',
           'group_reaction': 'reaction', 'comparison': 'row',
           'contrast': 'row', 'journey': 'journey',
           'story': 'story'}.get(rel_, 'row')
    if lay == 'journey' and not any(e['kind'] == 'chart-journey'
                                    for e in els):
        lay = 'row'
    lay = str(scn.get('layout') or lay)
    prev_lay = plan.setdefault('_sb_layouts', {}).get(si - 1)
    if lay == 'row' and rel_ not in ('contrast', 'comparison') \
            and prev_lay == 'row' and not scn.get('layout') \
            and len(els) >= 2:
        lay = 'stair' if len(els) >= 3 else 'focus'
    elif lay == 'focus' and prev_lay == 'focus' and not scn.get('layout') \
            and len(els) >= 2:
        lay = 'row'
    if story:
        lay = 'panels'
    sec['relation'] = rel_
    # label size follows the canvas: on a narrow (tall) sheet a label
    # sized to full height can never fit under its element
    ls = max(17.0, H * 0.050 * min(1.0, W / 900.0))
    g_edges, g_meta = [], []
    if lay == 'graph':
        top_of_ = {}
        for e in els:
            stack_ = [(e, e)]
            while stack_:
                x_, top_ = stack_.pop()
                top_of_[x_['ri']] = top_
                stack_.extend((kd, top_) for kd in x_.get('kids', ()))
        for ge in (scn.get('graph') or {}).get('edges') or []:
            a_, b_ = top_of_.get(ge.get('from')), top_of_.get(ge.get('to'))
            if a_ is None or b_ is None or a_ is b_:
                qa.append({'beat': si, 'check': 'relation-dropped',
                           'severity': 'fail',
                           'detail': f"{ge.get('text')}: an end is not drawn"})
                continue
            kind_ = str(ge.get('kind') or 'flow')
            g_edges.append((a_, b_, kind_))
            g_meta.append((a_, b_, kind_, str(ge.get('text') or ''),
                           int(ge.get('moment') or 0)))
        if len(g_edges) < 2:
            lay = 'story'

    def _labw(e, size):
        return (_sb_text_dims(e['label'], size, _SB_FL)[0]
                if e['label'] else 0.0)

    def _labh(e, size):
        return (_sb_text_dims(e['label'], size, _SB_FL)[1]
                if e['label'] else 0.0)

    chart_segs = []
    journey = any(e['kind'] == 'chart-journey' for e in els)
    lab_gap = H * 0.028
    if journey:
        ch_e = next(e for e in els if e['kind'] == 'chart-journey')
        riders = [e for e in els if e['rider']]
        others = [e for e in els if e is not ch_e and not e['rider']
                  and e['kind'] != 'divider']
        divs = [e for e in els if e['kind'] == 'divider']
        cwj = Wc * (0.60 if others else 0.92)
        rider_h = band_h * 0.42
        lane_b = max([_labh(e, ls) for e in riders if e['rider'] == 'valley']
                     + [0.0]) + lab_gap
        cb = (L + (Wc * 0.08 if riders and riders[0]['label'] else 0.0),
              band_t + rider_h, L + cwj, band_b - lane_b)
        ch_e['box'] = cb
        ch_e['st'], chart_segs = _sb_chart(cb)
        for e in riders:
            u, v = _SB_ANCH.get(e['rider'], _SB_ANCH['peak'])
            px_, py_ = cb[0] + u * (cb[2] - cb[0]), cb[1] + v * (cb[3] - cb[1])
            fh = rider_h * 0.86
            fw = fh * e['aspect']
            e['box'] = (px_ - fw / 2, py_ - fh * e['head'],
                        px_ + fw / 2, py_ + fh * 0.04)
            e['pt'] = (px_, py_)
        xcol0 = cb[2] + Wc * 0.09
        for e in divs:
            e['box'] = (cb[2] + Wc * 0.045 - 1, band_t,
                        cb[2] + Wc * 0.045 + 1, band_b)
        if others:
            colw = (R - xcol0) / len(others)
            for i, e in enumerate(others):
                lh_ = _labh(e, ls)
                hmax = band_h - (lh_ + lab_gap if lh_ else 0) - band_h * 0.04
                eh = min(hmax * e['rel'], colw * 0.9 / max(0.2, e['aspect'])
                         * 1.0)
                ew = eh * e['aspect']
                cx_ = xcol0 + colw * (i + 0.5)
                blk = eh + (lh_ + lab_gap if lh_ else 0)
                yb = band_t + (band_h - blk) / 2 + eh
                e['box'] = (cx_ - ew / 2, yb - eh, cx_ + ew / 2, yb)
    elif lay == 'panels' and els:
        sec['composition'] = scn.get('composition')
        sec['panels'] = _sb_panel_layout(
            els, L, R, band_t, band_b,
            lambda e: (_labh(e, ls) + lab_gap) if e['label'] else 0.0,
            lambda e: _labw(e, ls),
            progressive=scn.get('composition') == 'stage',
            figure_unit=figure_unit)
        sec['figure_unit'] = min(
            [e['figure_unit'] for e in els if e.get('figure_unit')
             and e['kind'] == 'person'] or [0.0])
        # a lap sitter is drawn over its host
        for e in [e for e in els if e.get('on_lap')]:
            els.remove(e)
            els.insert(els.index(e['on_lap']) + 1, e)
    elif not _sb_layout(lay, els, L, R, band_t, band_b,
                        lambda e: _labh(e, ls), lab_gap,
                        lambda e: _labw(e, ls), g_edges):
        lay = 'row'
        row = [e for e in els]
        n_l = max([len(e['label']) for e in row] + [0])
        for _it in range(8):
            lane = (max([_labh(e, ls) for e in row] + [0.0]) + lab_gap
                    if n_l else 0.0)
            gaps = []
            for a_, b_ in zip(row, row[1:]):
                dv = 'divider' in (a_['kind'], b_['kind'])
                gaps.append(Wc * (0.04 if dv else 0.085))
            hr = (band_h - lane) * 0.96
            for _s in range(40):
                cols = [(0.0 if e['kind'] == 'divider' else
                         max(e['aspect'] * e['rel'] * hr,
                             _labw(e, ls) + Wc * 0.01)) for e in row]
                if sum(cols) + sum(gaps) <= Wc or hr < band_h * 0.25:
                    break
                hr *= 0.96
            if sum(cols) + sum(gaps) <= Wc:
                break
            ls *= 0.92
        tot = sum(cols) + sum(gaps)
        x = -tot / 2
        yb = band_t + (band_h - (hr + lane)) / 2 + hr
        for i, e in enumerate(row):
            cxw = cols[i]
            if e['kind'] == 'divider':
                e['box'] = (x - 1, yb - hr, x + 1, yb + lane)
            else:
                eh = e['rel'] * hr
                ew = e['aspect'] * eh
                cx_ = x + cxw / 2
                yb_e = yb - (hr - eh) / 2 if e.get('mid') else yb
                e['box'] = (cx_ - ew / 2, yb_e - eh, cx_ + ew / 2, yb_e)
            x += cxw + (gaps[i] if i < len(gaps) else 0.0)

    for e in els:
        kids_, stack_ = [], list(e.get('kids', ()))
        while stack_:
            kd_ = stack_.pop()
            kids_.append(kd_['att'])
            stack_.extend(kd_.get('kids', ()))
        b_ = e.get('box')
        if not b_ or not kids_:
            continue
        over = 0.34 * kids_.count('on') + (0.10 if 'held' in kids_ else 0.0)
        h_ = b_[3] - b_[1]
        room = b_[1] - band_t
        if over and room < h_ * over:
            k_ = (b_[3] - band_t) / (h_ * (1 + over))
            cxm = (b_[0] + b_[2]) / 2
            w_ = (b_[2] - b_[0]) * k_
            e['box'] = (cxm - w_ / 2, b_[3] - h_ * k_, cxm + w_ / 2, b_[3])
    touch_pairs = set()
    if not journey and lay in ('row', 'focus', 'stair', 'story'):
        for e in els:
            act_ = str(e['m'].get('action') or '')
            if act_ not in _SB_TOUCH or not e.get('box') or (
                    e['kind'] != 'person' and not e['m'].get('target')):
                continue
            tgt = (_ref(e['m'].get('target'))
                   if e['m'].get('target') is not None else None)
            if tgt is None:
                i_ = els.index(e)
                tgt = next((o for o in els[i_ + 1:] + els[:i_][::-1]
                            if o['kind'] == 'art' and o.get('box')), None)
            if tgt is None or tgt is e or not tgt.get('box'):
                continue
            e['m'].setdefault('target', tgt['ri'])
            pb_, tb_ = e['box'], tgt['box']
            hw_ = max(tb_[2] - tb_[0], _labw(tgt, ls)) / 2
            tc_ = (tb_[0] + tb_[2]) / 2
            tb_ = (tc_ - hw_, tb_[1], tc_ + hw_, tb_[3])
            gap_ = Wc * 0.012
            if (pb_[0] + pb_[2]) < (tb_[0] + tb_[2]):
                dx_ = (tb_[0] - gap_) - pb_[2]
                lo_ = max((o['box'][2] + gap_ for o in els
                           if o is not e and o.get('box')
                           and o['box'][2] <= pb_[0] + 1), default=L)
                dx_ = max(dx_, lo_ - pb_[0])
            else:
                dx_ = (tb_[2] + gap_) - pb_[0]
                hi_ = min((o['box'][0] - gap_ for o in els
                           if o is not e and o.get('box')
                           and o['box'][0] >= pb_[2] - 1), default=R)
                dx_ = min(dx_, hi_ - pb_[2])
            if dx_ * ((tb_[0] + tb_[2]) - (pb_[0] + pb_[2])) > 0:
                e['box'] = (pb_[0] + dx_, pb_[1], pb_[2] + dx_, pb_[3])
            if act_ == 'climb' and e['kind'] == 'person':
                # a climber stands on the rungs, part way up the thing
                pb_, tb0 = e['box'], tgt['box']
                side = 1 if (pb_[0] + pb_[2]) < (tb0[0] + tb0[2]) else -1
                ox = (pb_[2] - pb_[0]) * 0.45 * side
                up = (tb0[3] - tb0[1]) * 0.35
                e['box'] = (pb_[0] + ox, pb_[1] - up, pb_[2] + ox,
                            pb_[3] - up)
            touch_pairs.add(frozenset((id(e), id(tgt))))
    # every picture fills the space it owns: a moment fills its panel,
    # any other scene fills the band
    if not journey and not any(e['kind'] == 'quantity-chart' for e in els):
        lane_of = (lambda e: (_labh(e, ls) + lab_gap)  # noqa: E731
                   if e['label'] else 0.0)
        if lay == 'panels' and sec.get('panels'):
            sx0_, sy0_ = -W / 2 + W * 0.03, -H / 2 + H * 0.035
            groups_ = [([e for e in els if e.get('panel') == k_],
                        (max(rect_[0], sx0_), max(rect_[1], sy0_),
                         min(rect_[2], -sx0_), min(rect_[3], -sy0_)))
                       for k_, rect_ in sec['panels'].items()]
            rooms = [r_ for r_ in (_sb_fill(g_, rect_, lane_of, apply=False)
                                   for g_, rect_ in groups_) if r_]
            sec['fill_rooms'] = rooms
            unit_ = min(rooms + ([fill_unit] if fill_unit else [])) \
                if rooms else fill_unit
            for g_, rect_ in groups_:
                _sb_fill(g_, rect_, lane_of, unit=unit_, rewrap=False)
        else:
            _sb_fill(els, (L, band_t, R, band_b), lane_of,
                     close_gaps=(lay != 'graph'),
                     rewrap=(lay not in ('graph', 'story', 'panels')))
    if journey:
        lay = 'journey'
    plan['_sb_layouts'][si] = lay
    sec['layout'] = lay

    # ---- strokes, labels, arrows --------------------------------------
    win0, win1 = t0 + 0.04, max(t0 + 0.5, t1 - 0.12)
    setting = ('' if journey or lay in ('cycle', 'stair', 'graph', 'panels')
               else _sb_setting_kind(scn, beat))
    set_w = None
    if setting:
        set_w = (win0, win0 + min(1.0, 0.12 * (win1 - win0)))
        win0 = set_w[1]
    draw_els = [e for e in els]
    slot = slot0 = (win1 - win0) / max(1, len(draw_els))
    pos = {id(e): i for i, e in enumerate(draw_els)}
    for e in draw_els:
        for kd in e.get('kids', ()):
            pos[id(kd)] = pos[id(e)]
    all_els = draw_els + [kd for e in draw_els for kd in e.get('kids', ())]

    def _mref(r, moment=None):
        candidates = [e for e in all_els if moment is None
                      or e['m'].get('moment') == moment]
        if isinstance(r, int):
            return next((e for e in candidates if e['ri'] == r), None)
        r = str(r or '').lower().strip()
        return next((e for e in candidates
                     if r in (str(e['it'].get('label', '')).lower(),
                              str(e['m'].get('label', '')).lower(),
                              str(e['m'].get('cast_key', '')).lower(),
                              str(e['m'].get('group', '')).lower())), None)

    mark_at = {}
    flow_pairs = set()
    for mk in scn.get('marks') or []:
        kind_ = str(mk.get('type') or '').lower()
        if scn.get('composition') == 'stage' and kind_ in (
                'flow', 'up', 'down'):
            continue
        moment = mk.get('moment') if scn.get('composition') == 'stage' else None
        a_ = _mref(mk.get('from', mk.get('on', 0)), moment)
        b_ = _mref(mk.get('to'), moment) if kind_ == 'flow' else None
        if kind_ not in _SB_MARKS or a_ is None or (
                kind_ == 'flow' and b_ is None):
            qa.append({'beat': si, 'check': 'mark-unresolved',
                       'severity': 'warn', 'detail': str(mk)})
            continue
        last = max(pos[id(a_)], pos[id(b_)] if b_ is not None else -1)
        mark_at.setdefault(last, []).append((kind_, a_, b_, mk.get('color')))
        if b_ is not None:
            flow_pairs.add(frozenset((id(a_.get('kid_of') or a_),
                                      id(b_.get('kid_of') or b_))))
    out_items = []
    arrows_ = sec['qa_arrows'] = []
    prev = None
    mo_at = [float(m_.get('at') or 0.0) for m_ in scn.get('moments') or []
             if isinstance(m_, dict)]
    mo_win = {}
    box_moments = {}
    cues_ = sec['qa_cues'] = []
    mom_span = {}
    if lay in ('story', 'graph', 'panels') and len(mo_at) >= 2:
        # each moment draws while its sentence is being said
        span_ = win1 - win0
        edges = [win0 + span_ * f_ for f_ in mo_at] + [win1]
        wt_ = beat.get('word_times') or []
        narr_ = str(beat.get('narration') or '')
        if wt_ and len(wt_) == len(narr_.split()):
            offs, c_ = [], 0
            for w_ in narr_.split():
                offs.append(c_ / max(1, len(narr_)))
                c_ += len(w_) + 1
            for k_, f_ in enumerate(mo_at):
                i_ = next((i for i, o in enumerate(offs) if o >= f_ - 1e-3),
                          len(offs) - 1)
                edges[k_] = min(win1 - 0.5, max(win0, float(wt_[i_][1])))
            edges[0] = win0
        for k_ in range(len(mo_at)):
            grp = [e for e in draw_els
                   if int(e['m'].get('moment') or 0) == k_]
            a_ = edges[k_]
            b_ = max(a_ + 0.5, edges[k_ + 1])
            mom_span[k_] = (a_, b_)
            for g_, e in enumerate(grp):
                w_ = (b_ - a_) / len(grp)
                mo_win[id(e)] = (a_ + g_ * w_, a_ + (g_ + 1) * w_)
            _sb_word_cues(grp, beat.get('word_times') or [], a_, b_,
                          win1, mo_win, cues_)
    # element ground known before anything draws — padded to anticipate
    # the ink growth kids/marks add around the placed box, so a mark may
    # not cross ground a coming element will stand on either
    el_all = []
    for e in draw_els:
        b2_ = e.get('box')
        if b2_ is None:
            el_all.append((e['it'].get('label', '?'), None))
            continue
        pw_ = (b2_[2] - b2_[0]) * 0.12
        ph_ = (b2_[3] - b2_[1]) * 0.15
        el_all.append((e['it'].get('label', '?'),
                       (b2_[0] - pw_, b2_[1] - ph_,
                        b2_[2] + pw_, b2_[3] + ph_)))
    for n_, e in enumerate(draw_els):
        box_start = len(boxes)
        uid += 1
        i0, i1 = mo_win.get(id(e), (win0 + n_ * slot0,
                                    win0 + (n_ + 1) * slot0))
        slot = i1 - i0
        groups = []
        b = e['box']
        cap_h = H * (0.68 if e['m'].get('activity') else 0.52)
        if e['kind'] == 'person' and b[3] - b[1] > cap_h:
            k_ = cap_h / (b[3] - b[1])
            cx_ = (b[0] + b[2]) / 2
            hw_ = (b[2] - b[0]) * k_ / 2
            b = e['box'] = (cx_ - hw_, b[3] - (b[3] - b[1]) * k_,
                            cx_ + hw_, b[3])
        lwsize = min(150.0, max(80.0, (b[3] - b[1]) * 0.55))
        fig_b = b
        mark_st = []
        if e['kind'] == 'divider':
            art_st = _sb_divider((b[0] + b[2]) / 2, b[1], b[3])
            e['_div_st'] = art_st
            lwsize = 1.0
        elif e['kind'] == 'quantity-chart':
            art_st, bars = _sb_quantity_chart(b, e['m']['chart'])
            lwsize = 1.0
            fig_b = b
            search_from = 0
            wt = [(w['word'], w['start']) if isinstance(w, dict)
                  else (w[0], w[1])
                  for w in beat.get('word_times') or []]
            for value, strokes, rect in bars:
                found = next((j for j in range(search_from, len(wt))
                              if str(wt[j][0]).strip('.,!?').lower()
                              == str(value['word']).lower()), None)
                if found is not None:
                    said = float(wt[found][1])
                    search_from = found + 1
                else:
                    fractions = scn.get('moments') or []
                    fraction = (fractions[value['moment']].get('at', 0.0)
                                if value['moment'] < len(fractions) else 0.0)
                    said = win0 + (win1 - win0) * fraction
                start = max(win0, said)
                end = min(win1, start + max(0.35, (win1 - start) * 0.14))
                groups.append((('quantity', strokes, (0, 0), 1.0, None),
                               start, end))
                sec.setdefault('qa_quantities', []).append({
                    'label': value['label'], 'value': value['value'],
                    'source': value['source'], 'unit': value['unit'],
                    'bounds': rect, 'start': start, 'said': said})
                cues_.append((value['label'], start, said))
            i0, slot = win0, min(1.0, win1 - win0)
        elif e['kind'] == 'chart-journey':
            art_st = e['st']
            fig_b = b
        elif e['kind'] == 'crowd':
            art_st = _sb_crowd(b, seed=si * 5 + 1)
        elif e['kind'] == 'stack-list':
            art_st = _sb_stack(b, e['rows'], sw_col, seed=si * 7 + 3)
            lwsize = 90.0
        else:
            fb = (b[0], b[3] - (b[3] - b[1]) / e['head'], b[2], b[3])
            if e['kind'] == 'person':
                flip = (b[0] + b[2]) / 2 > W * 0.12
                act = str(e['m'].get('action') or '')
                tgt = _ref(e['m'].get('target')) if e['m'].get(
                    'target') is not None else None
                if tgt is not None and tgt is not e and tgt.get('box'):
                    flip = (tgt['box'][0] + tgt['box'][2]) < (b[0] + b[2])
                if e.get('face'):
                    flip = e['face'] < 0
                if any(kd['att'] == 'held' for kd in e.get('kids', ())):
                    act = act or 'hold'
                e['flip'], e['act'] = flip, act
                e['fit'] = _sb_outfit(
                    e['m'], e['m'].get('outfit'), e['m'].get('label'),
                    e['label'], e['m'].get('concept'))
                kids = e.get('kids', ())
                if any(kd['att'] == 'worn' and _SB_EYEWEAR.search(
                        str(kd['m'].get('label') or '')) for kd in kids):
                    e['fit'] = dict(e['fit'], glasses=True)
                e['stance'] = str(e['m'].get('stance') or 'stand')
                e['seat'] = not any(kd['att'] == 'under' for kd in kids)
                e['engaged'] = act in sb_cast.ENGAGED or (
                    tgt is not None and tgt is not e)
                shirt = sb_cast.shirt_for(
                    e['m'].get('shirt') or e['m'].get('cast_key')
                    or e['m'].get('label')
                    or e['m'].get('concept'))
                e['hidden'] = sec.get('story_hidden') or ()
                got = _sb_activity(e, fb, flip, shirt, si, qa)
                if got is not None:
                    art_st, mark_st = got
                else:
                    body, marks, _hb = sb_cast.figure(
                        e['emo'], flip, act, shirt,
                        outfit=e['fit'], engaged=e['engaged'],
                        stance=e['stance'], seat=e['seat'])
                    fit_st, _fb = _sb_fit(body + marks, fb)
                    art_st, mark_st = fit_st[:len(body)], fit_st[len(body):]
                fig_b = _sb_bounds(s_[0] for s_ in art_st)
            else:
                art_st, fig_b = _sb_fit(e['art'], fb)
            if e['kind'] == 'person':
                gy = fig_b[3]
                gw = (fig_b[2] - fig_b[0]) * 0.55
                gx = (fig_b[0] + fig_b[2]) / 2
                art_st.append((_wobble_line((gx - gw, gy + 2),
                                            (gx + gw, gy + 2), n=8, wob=1.0,
                                            seed=uid), 'pale', 1.0, False,
                               True))
        if e['halo'] and e['kind'] == 'person':
            groups.append((('marks', _sb_expr('halo', fig_b, e['halo']),
                            (0, 0), 1.0, None), i0, i0 + slot * 0.20))
        groups.append((('icon', art_st, (0, 0), lwsize, None),
                       i0 + slot * 0.08, i0 + slot * 0.62))
        if mark_st:
            groups.append((('marks', mark_st, (0, 0), lwsize, None),
                           i0 + slot * 0.62, i0 + slot * 0.72))
            eb = _sb_bounds(s_[0] for s_ in mark_st)
            fig_b = (min(fig_b[0], eb[0]), min(fig_b[1], eb[1]),
                     max(fig_b[2], eb[2]), max(fig_b[3], eb[3]))
        if e['expr'] and e['kind'] == 'person':
            ex = _sb_expr(e['expr'], fig_b, e['halo'] or 'a_red')
            groups.append((('marks', ex, (0, 0), 100.0, None),
                           i0 + slot * 0.62, i0 + slot * 0.72))
            eb = _sb_bounds(s_[0] for s_ in ex)
            if eb:
                fig_b = (min(fig_b[0], eb[0]), min(fig_b[1], eb[1]),
                         max(fig_b[2], eb[2]), max(fig_b[3], eb[3]))
        for kn, kd in enumerate(e.get('kids', ())):
            hand = None
            klab = str(kd['m'].get('label') or '')
            if kd['att'] == 'worn' and e['kind'] == 'person' \
                    and _SB_EYEWEAR.search(klab):
                # the face draws the glasses; the kid is the eye band
                hh_ = (fig_b[3] - fig_b[1]) * 0.30
                kd['ink'] = (fig_b[0], fig_b[1], fig_b[2], fig_b[1] + hh_)
                continue
            if kd['att'] in ('activity', 'behind') or kd.get('drawn'):
                # drawn inside the activity picture (or absorbed by it)
                kd['ink'] = kd.get('ink') or fig_b
                continue
            if kd['att'] == 'held' and e.get('hand_w'):
                hand = e['hand_w']
            elif kd['att'] == 'held' and e['kind'] == 'person':
                u, v = sb_cast.hand_uv(e['emo'], e.get('flip', False),
                                       e.get('act', ''), e.get('fit'),
                                       e.get('engaged'),
                                       e.get('stance', 'stand'),
                                       e.get('seat', True))
                hand = (fig_b[0] + u * (fig_b[2] - fig_b[0]),
                        fig_b[1] + v * (fig_b[3] - fig_b[1]))
            kb0 = _sb_kid_box(kd['att'], fig_b, kd['aspect'], hand,
                              e.get('act', ''), e.get('flip', False), klab)
            if kd['kind'] == 'person':
                kbody, kmarks, _kh = sb_cast.figure(
                    kd['emo'], (kb0[0] + kb0[2]) / 2 > 0,
                    kd['m'].get('action', ''),
                    sb_cast.shirt_for(kd['m'].get('shirt') or kd['m'].get('cast_key')
                                      or kd['m'].get('label')
                                      or kd['m'].get('concept')),
                    outfit=_sb_outfit(kd['m'], kd['m'].get('outfit'),
                                      kd['m'].get('label'),
                                      kd['m'].get('concept')))
                kst, kb = _sb_fit(kbody + kmarks, kb0)
            else:
                kst, kb = _sb_fit(kd['art'], kb0)
            if not kst:
                continue
            ka = i0 + slot * (0.60 + 0.05 * kn)
            groups.append((('icon', kst, (0, 0), max(70.0, lwsize * 0.6),
                            None), ka, ka + slot * 0.10))
            kd['ink'] = kb
            fig_b = (min(fig_b[0], kb[0]), min(fig_b[1], kb[1]),
                     max(fig_b[2], kb[2]), max(fig_b[3], kb[3]))
        e['ink'] = (fig_b if e['kind'] not in ('divider',) else b)
        tag = ('rider' if e['rider'] else
               ('chart' if e['kind'] == 'chart-journey' else 'el'))
        boxes.append((e['it'].get('label', '?'), e['ink'], tag,
                      e['kind']))
        if setting in ('river', 'sea') and tag == 'el' \
                and e['kind'] != 'person' \
                and _SB_ON_WATER.search(str(e['it'].get('label') or '')):
            groups.append((('marks', _sb_water_patch(e['ink']), (0, 0),
                            100.0, None), i0 + slot * 0.80, i0 + slot * 0.95))
        # arrows only where the scene states a relation: a stated cycle
        # closes its loop, a before/after crosses its sides; flow marks and
        # graph edges draw their own. Adjacency alone never draws an arrow.
        if prev is not None and frozenset((id(prev), id(e))) in (
                flow_pairs | touch_pairs):
            pass
        elif (not journey and prev is not None
                and lay in ('cycle', 'before_after')
                and (lay != 'before_after'
                     or prev.get('ba_side') != e.get('ba_side'))):
            ast = _sb_link(prev['ink'], e['ink'], Wc)
            if ast:
                groups.insert(0, (('arrow', ast, (0, 0), 90.0, None),
                                  i0, i0 + slot * 0.10))
                boxes.append(('arrow', _sb_bounds(s_[0] for s_ in ast),
                              'arrow'))
                arrows_.append(lay)
            if lay == 'cycle' and n_ == len(draw_els) - 1:
                ast = _sb_link(e['ink'], draw_els[0]['ink'], Wc)
                if ast:
                    groups.append((('arrow', ast, (0, 0), 90.0, None),
                                   i0 + slot * 0.98, i1))
                    boxes.append(('arrow', _sb_bounds(s_[0] for s_ in ast),
                                  'arrow'))
                    arrows_.append(lay)
        prev = e
        # label: fixed slot for its element
        if e['label']:
            lw_, lh_, ltop = _sb_text_dims(e['label'], ls, _SB_FL)
            ib = e['ink']
            if e['rider'] == 'valley':
                px_, py_ = e['pt']
                lx, ly, al = px_, py_ + lab_gap * 0.8, 'center'
            elif e['rider'] == 'peak':
                lx = ib[0] - Wc * 0.012 - lw_
                ly = (ib[1] + ib[3]) / 2 - lh_ / 2
                al = 'left'
            elif e['rider']:
                lx = ib[2] + Wc * 0.012
                ly = (ib[1] + ib[3]) / 2 - lh_ / 2
                al = 'left'
            elif e.get('on_back'):
                # a backdrop's label rides above it, clear of the floor
                lx, ly, al = (ib[0] + ib[2]) / 2, \
                    ib[1] - lab_gap * 0.4 - lh_ + ltop, 'center'
            else:
                # anchor under the drawn ink, not the layout slot — a
                # graph cell is taller than its glyph and would drop the
                # label onto the shared bottom row away from its icon
                lx, ly, al = (ib[0] + ib[2]) / 2, ib[3] + lab_gap, 'center'
                if any(mk_[0] == 'drips' and mk_[1] is e
                       for v_ in mark_at.values() for mk_ in v_):
                    ly += (ib[3] - ib[1]) * 0.12
            lst, lbb = _sb_text(e['label'], lx, ly - ltop, ls, _SB_FL, al)
            # a label stays inside the paper — slide it back on frame
            dx_ = (max(-W / 2 + W * 0.025 - lbb[0], 0.0)
                   or min(0.0, W / 2 - W * 0.025 - lbb[2]))
            if dx_:
                lst = [(tuple((px + dx_, py) for px, py in s[0]),)
                       + tuple(s[1:]) for s in lst]
                lbb = (lbb[0] + dx_, lbb[1], lbb[2] + dx_, lbb[3])
            l1 = 0.86 if n_ in mark_at else 0.98
            groups.append((('plabel', lst, (0, 0), 1.0, None),
                           i0 + slot * 0.72, i0 + slot * l1))
            boxes.append(('label:' + ' '.join(e['label']), lbb, 'label'))
            e['lab_box'] = lbb
            e['_lab_st'] = lst
        for mi, (kind_, a_, b_, mcol) in enumerate(mark_at.get(n_, ())):
            ab_ = a_.get('ink') or a_.get('box')
            bb_ = (b_.get('ink') or b_.get('box')) if b_ is not None else None
            if ab_ is None or (b_ is not None and bb_ is None):
                continue
            if bb_ is not None and (bb_[0] + bb_[2]) < (ab_[0] + ab_[2]):
                mst = _sb_vmark(kind_, bb_, ab_, mcol, seed=uid + mi)
            else:
                mst = _sb_vmark(kind_, ab_, bb_, mcol, seed=uid + mi)
            mb_ = _sb_bounds(q[0] for q in mst)
            dx = max(-W / 2 + W * 0.025 - mb_[0],
                     min(0.0, W / 2 - W * 0.025 - mb_[2]))
            mst = [(tuple((px + dx, min(H / 2 - H * 0.03,
                                      max(py, band_t + 4.0)))
                          for px, py in q[0]),)
                   + tuple(q[1:]) for q in mst]
            if not mst:
                continue
            refs = set()
            for r_ in (a_, b_):
                while r_ is not None:
                    refs.add(r_['it'].get('label', '?'))
                    r_ = r_.get('kid_of')
            mb_ = _sb_bounds(q[0] for q in mst)
            hit_ = next((bx[0] for bx in boxes if bx[2] not in
                         ('mark', 'title', 'caption')
                         and bx[0] not in refs
                         and str(bx[0]).removeprefix('label:') not in refs
                         and bx[1][0] < mb_[2] and mb_[0] < bx[1][2]
                         and bx[1][1] < mb_[3] and mb_[1] < bx[1][3]), None)
            if hit_ is None:
                # an element drawn later still owns its spot — a mark may
                # not cross ground a coming element will stand on either
                hit_ = next((nm for nm, b2_ in el_all
                             if b2_ is not None and nm not in refs
                             and b2_[0] < mb_[2] and mb_[0] < b2_[2]
                             and b2_[1] < mb_[3] and mb_[1] < b2_[3]),
                            None)
            if hit_ is not None:
                qa.append({'beat': si, 'check': 'mark-dropped',
                           'severity': 'info',
                           'detail': f'{kind_} would cross {hit_}'})
                continue
            groups.append((('marks', mst, (0, 0), 100.0, None),
                           i0 + slot * 0.87, i0 + slot * 0.98))
            if kind_ == 'flow':
                arrows_.append('flow')
            boxes.append(('mark:' + kind_, _sb_bounds(q[0] for q in mst),
                          'mark', refs))
        moment = int(e['m'].get('moment') or 0)
        moment_fade = fade
        if sec.get('composition') == 'stage' and moment + 1 in mom_span:
            end = mom_span[moment + 1][0]
            moment_fade = (end - 0.12, end)
        for bx in boxes[box_start:]:
            box_moments[id(bx[1])] = moment
        out_items.append({'groups': groups, 'bounds2': e['ink'],
                          'uid': uid, 'fade': moment_fade, 'kind': 'elem',
                          't_window': (i0, i1),
                          'moment': moment,
                          'label': e['it'].get('label', '')})
    for helper in draw_els:
        act = helper['m'].get('activity') or {}
        if not act.get('shared_partner'):
            continue
        primary = next((e for e in draw_els if e is not helper
                        and e['m'].get('moment') == helper['m'].get('moment')
                        and helper['m'].get('shared_with') in (
                            e['m'].get('cast_key'), e['m'].get('label'))), None)
        prop = primary.get('partner_bounds') if primary else None
        hand = helper.get('hand_w')
        if prop and hand:
            dx = max(prop[0] - hand[0], hand[0] - prop[2], 0.0)
            dy = max(prop[1] - hand[1], hand[1] - prop[3], 0.0)
            height = helper['box'][3] - helper['box'][1]
            if math.hypot(dx, dy) <= height * 0.08:
                qa.append({'beat': si, 'check': 'shared-contact',
                           'severity': 'info', 'detail':
                           f'{helper["m"]["label"]}: both carriers touch '
                           f'{act["shared_partner"]}'})
            else:
                qa.append({'beat': si, 'check': 'shared-contact',
                           'severity': 'fail', 'detail':
                           f'{helper["m"]["label"]}: does not touch '
                           f'{act["shared_partner"]}'})
        else:
            qa.append({'beat': si, 'check': 'shared-contact',
                       'severity': 'fail', 'detail':
                       f'{act["shared_partner"]}: shared prop not drawn'})
        for name, label in (act.get('shared_roles') or {}).items():
            drawn = primary is not None and any(
                kid['m'].get('label') == label and kid.get('ink')
                for kid in primary.get('kids', ()))
            if not drawn:
                qa.append({'beat': si, 'check': 'activity-role',
                           'severity': 'fail', 'detail':
                           f'{helper["m"]["label"]}: {label} ({name}) '
                           'missing from shared activity'})
    wt_all = beat.get('word_times') or []
    link_pts = {}
    for a_, b_, kind_, text_, k_ in g_meta:
        obst_ = [bx[1] for bx in boxes if bx[2] in ('el', 'label')
                 and bx[1] not in (a_['ink'], b_['ink'])
                 and not _sb_ovl(bx[1], a_['ink'], 4.0)
                 and not _sb_ovl(bx[1], b_['ink'], 4.0)]
        ast, geo = _sb_graph_edge(a_['ink'], b_['ink'], Wc, kind_, obst_)
        if not ast:
            qa.append({'beat': si, 'check': 'relation-dropped',
                       'severity': 'warn',
                       'detail': f'{text_}: ends too close to link'})
            continue
        drawn = max(mo_win.get(id(a_), (win0, win0))[1],
                    mo_win.get(id(b_), (win0, win0))[1])
        ms_ = mom_span.get(k_, (win0, win1))
        v_ = (re.findall(r'[a-z]+', text_.lower()) or [''])[0]
        said = next((float(w[1]) for w in wt_all
                     if ms_[0] - 0.3 <= float(w[1]) <= ms_[1] + 0.3
                     and str(w[0]).lower().strip('.,!?') .startswith(v_[:4])
                     and v_), None)
        te0 = min(win1 - 0.4, max(drawn - 0.15, said if said else ms_[0]))
        te1 = min(win1, te0 + 0.7)
        groups = [(('arrow', ast, (0, 0), 90.0, None), te0, te0 + 0.4)]
        arrows_.append('edge:' + kind_)
        ab_ = _sb_bounds(q[0] for q in ast)
        lk_ = f'link{len(link_pts)}'
        link_pts[lk_] = [p_ for q in ast for p_ in q[0]]
        boxes.append((lk_, ab_, 'link',
                      {a_['it'].get('label', '?'), b_['it'].get('label', '?')}))
        if text_.lower() in _SB_PREPS:
            text_ = ''
        if kind_ == 'not' and text_:
            text_ = 'no ' + text_
        if text_ and kind_ != 'is':
            (mx, my), horiz = geo
            es = ls * 0.72
            lines_ = _sb_wrap(text_, 12)
            lw_, lh_, ltop = _sb_text_dims(lines_, es, _SB_FL)
            spots = ([(mx, my - lh_ - H * 0.012, 'center'),
                      (mx, my + H * 0.012, 'center')] if horiz else
                     [(mx + Wc * 0.012, my - lh_ / 2, 'left'),
                      (mx - Wc * 0.012 - lw_, my - lh_ / 2, 'left')])
            for lx, ly, al in spots:
                x0_ = lx - lw_ / 2 if al == 'center' else lx
                tb_ = (x0_, ly, x0_ + lw_, ly + lh_)
                if any(_sb_ovl(tb_, bx[1], 2.0) for bx in boxes
                       if bx[2] in ('el', 'label', 'rider', 'chart')):
                    continue
                col_ = 'a_red' if kind_ in ('not', 'vs') else 'ink'
                lst, lbb = _sb_text(lines_, lx, ly - ltop, es, _SB_FL, al,
                                    col_)
                groups.append((('plabel', lst, (0, 0), 1.0, None),
                               te0 + 0.3, te1))
                boxes.append(('label:' + text_, lbb, 'label', {lk_}))
                break
        uid += 1
        out_items.append({'groups': groups, 'bounds2': ab_, 'uid': uid,
                          'fade': fade, 'kind': 'elem',
                          't_window': (te0, te1), 'label': ''})
    sec['qa_panels'] = []
    for k_, rect in sorted((sec.get('panels') or {}).items()):
        mine = [e for e in all_els if e.get('panel', e.get(
            'kid_of', {}).get('panel')) == k_ and e.get('ink')]
        places_ = scn.get('places') or []
        kind_ = str(places_[k_] if k_ < len(places_) else '')
        feet_ = [e['box'][3] for e in mine if e.get('box')
                 and not e.get('on_lap')]
        fl_ = max(feet_) if feet_ else rect[3] - H * 0.05
        solid_ = [e['ink'] for e in mine] + [e['lab_box'] for e in mine
                                             if e.get('lab_box')]
        # no panel border: moments read as scenes on open paper, not boxes
        fr_ = []
        room_ = _sb_room(kind_, rect, fl_, solid_,
                         si * 131 if sec.get('composition') == 'stage'
                         else si * 131 + k_ * 17)
        backs = [e['box'] for e in mine
                 if e.get('on_back') and e.get('box')]
        for hy in sorted({round(b[3]) for b in backs}):
            hx0 = min(b[0] for b in backs if round(b[3]) == hy) - 8
            hx1 = max(b[2] for b in backs if round(b[3]) == hy) + 8
            # a pale shelf line under the raised level so it reads as
            # ground, not things floating in the air
            room_.append((_wobble_line((hx0, hy + 2), (hx1, hy + 2),
                                       n=5, wob=0.7, seed=si * 131 + hy),
                          'pale', 0.8, False, True))
        a_ = mom_span.get(k_, (win0, win1))[0]
        room_fade = fade
        if sec.get('composition') == 'stage' and k_ + 1 in mom_span:
            end = mom_span[k_ + 1][0]
            room_fade = (end - 0.12, end)
        uid += 1
        out_items.insert(0, {'groups': [
            (('marks', fr_, (0, 0), 100.0, None), a_, a_ + 0.25),
            (('marks', room_, (0, 0), 100.0, None), a_ + 0.1, a_ + 0.45)],
            'bounds2': rect, 'uid': uid, 'fade': room_fade, 'kind': 'elem',
            'moment': k_,
            't_window': (a_, a_ + 0.45), 'label': 'panel'})
        boxes.append((f'panel{k_}', rect, 'panel'))
        sec['qa_panels'].append({'moment': k_, 'place': kind_,
                                 'pieces': len(room_) - 1,
                                 'rect': rect})
        if k_ == 0 and scn.get('moments') \
                and sec.get('composition') != 'stage':
            moment = scn['moments'][k_]
            phrase = str(moment.get('text') or '').strip()
            if not phrase:
                phrase = str(next((ev.get('phrase') for ev in
                                   scn.get('events') or []
                                   if ev.get('phrase')), '')).strip()
            if phrase:
                phrase = phrase.rstrip('.')
                size = H * 0.039
                maxw = Wc * 0.28
                lines = _sb_wrap(phrase, 21)
                while (max(font_text_width(line, size, _SB_FL)
                           for line in lines) > maxw and size > H * 0.028):
                    size *= 0.94
                tw, th, ttop = _sb_text_dims(lines, size, _SB_FL)
                margin = H * 0.012
                art = [e['ink'] for e in mine if e.get('ink')]
                if not art:
                    continue
                ax0 = min(b[0] for b in art)
                ax1 = max(b[2] for b in art)
                ay = (min(b[1] for b in art) + max(b[3] for b in art)) / 2
                def place(x, y):
                    return (min(R - tw - margin, max(L + margin, x)),
                            min(band_b - th - margin,
                                max(band_t + band_h * 0.18, y)))
                candidates = [
                    place(ax1 + margin * 2, ay - th / 2),
                    place(ax0 - tw - margin * 2, ay - th / 2),
                    place(ax1 + margin * 2, ay - th * 1.5),
                    place(ax0 - tw - margin * 2, ay - th * 1.5),
                    place(ax1 + margin * 2, ay - th * 2),
                    place(ax0 - tw - margin * 2, ay - th * 2),
                ]
                obstacles = [e['ink'] for e in draw_els if e.get('ink')]
                obstacles += [e['lab_box'] for e in draw_els
                              if e.get('lab_box')]
                def collision(xy):
                    x, y = xy
                    bb = (x - margin, y - margin,
                          x + tw + margin, y + th + margin)
                    return sum(max(0, min(bb[2], ob[2]) - max(bb[0], ob[0]))
                               * max(0, min(bb[3], ob[3]) - max(bb[1], ob[1]))
                               for ob in obstacles)
                x, y = min(candidates, key=collision)
                if collision((x, y)) < tw * th * 0.08:
                    notes, nb = _sb_text(lines, x, y - ttop, size,
                                         _SB_FL, 'left')
                    start = mom_span.get(k_, (win0, win1))[0]
                    phrase_words = re.findall(r"[a-z0-9']+", phrase.lower())
                    start = next((float(w[1]) for w in
                                  beat.get('word_times') or []
                                  if phrase_words and w[0] == phrase_words[0]
                                  and start - 0.2 <= float(w[1]) <= win1),
                                 start)
                    uid += 1
                    note_end = mom_span.get(k_, (win0, win1))[1]
                    note_fade = ((note_end - 0.18, note_end)
                                 if sec.get('composition') == 'stage' else fade)
                    out_items.append({
                        'groups': [(('plabel', notes, (0, 0), 1.0, None),
                                    start, min(win1, start + 0.85))],
                        'bounds2': nb, 'uid': uid, 'fade': note_fade,
                        'kind': 'elem', 't_window': (start, note_end),
                        'label': 'callout'})
                    boxes.append(('callout', nb, 'label'))
    sec['relations_drawn'] = len(g_meta)
    sec['setting'] = setting
    if setting:
        grounded = [e['box'] for e in draw_els
                    if e['kind'] not in ('divider',) and e.get('box')]
        base = (sorted(b_[3] for b_ in grounded)[len(grounded) // 2]
                if grounded else band_b)
        floor_ = max([bx[1][3] for bx in boxes if bx[2] == 'label']
                     + [base + H * 0.05])
        floor_ = min(floor_ + H * 0.02, cap_top - H * 0.03)
        sst = _sb_setting(setting, str(beat.get('narration') or ''), L, R,
                          band_t, base, floor_, list(boxes), seed=si * 97 + 11)
        if sst:
            uid += 1
            out_items.insert(0, {'groups': [(('marks', sst, (0, 0), 100.0,
                                              None), set_w[0], set_w[1])],
                                 'bounds2': _sb_bounds(q[0] for q in sst),
                                 'uid': uid, 'fade': fade, 'kind': 'elem',
                                 't_window': set_w, 'label': 'setting'})
        sec['qa_setting'] = (setting, len(sst))
    # scene wash: the sheet itself picks up a whisper of the scene's accent
    # — the board is no longer one flat colour; each scene shifts subtly
    # toward its own pastel tint
    wpoly = [(-W / 2, -H / 2), (W / 2, -H / 2), (W / 2, H / 2),
             (-W / 2, H / 2), (-W / 2, -H / 2)]
    uid += 1
    out_items.insert(0, {'groups': [(('marks',
                                     [(wpoly, sw_col, 0.13, 'sheet', True)],
                                     (0, 0), 100.0, None), t0, t0 + 0.9)],
                         'bounds2': (-W / 2, -H / 2, W / 2, H / 2),
                         'uid': uid, 'fade': fade, 'kind': 'elem',
                         't_window': (t0, t0 + 0.9), 'label': 'wash'})
    if cap_st:
        uid += 1
        cap_tokens = [w for w in re.findall(r"[a-z0-9']+", cap.lower())
                      if w not in ('a', 'an', 'the', 'and', 'in', 'of')]
        spoken = beat.get('word_times') or []
        ct0 = next((float(w[1]) for w in spoken
                    if cap_tokens and w[0] == cap_tokens[0]
                    and float(w[1]) >= mom_span.get(
                        max(mom_span, default=0), (win0, win1))[0] - 0.3),
                   mom_span.get(max(mom_span, default=0),
                                (win1 - 1.0, win1))[0])
        ct0 = min(win1 - 0.45, max(win0, ct0))
        out_items.append({'groups': [(('plabel', cap_st, (0, 0), 90.0, None),
                                      ct0, min(win1, ct0 + 0.85))],
                          'bounds2': cap_bb, 'uid': uid, 'fade': fade,
                          'kind': 'elem', 't_window': (
                              ct0, min(win1, ct0 + 0.85))})
    sec['items2'] = out_items

    # ---- audit: pairwise overlap + frame containment ------------------
    # people drawn in contact (a hug, a lap) overlap by design
    contact_ = set()
    for e in els:
        lab_ = e['it'].get('label', '?')
        if e.get('on_lap'):
            contact_.add(frozenset((lab_, e['on_lap']['it'].get('label'))))
        for t_ in e['m'].get('touch') or ():
            o_ = next((o for o in els if o is not e and o.get('panel')
                       == e.get('panel') and t_ in
                       (o['m'].get('label'), o['m'].get('cast_key'),
                        o['m'].get('group'))), None)
            if o_ is not None:
                contact_.add(frozenset((lab_, o_['it'].get('label', '?'))))
    # a divider belongs in the free space between the things it
    # separates — when ink grew past a slot and swallowed its spot,
    # re-center the divider (art, box, label) in what is still free
    inked = sorted((e for e in draw_els if e.get('ink')),
                   key=lambda e: (e['ink'][0] + e['ink'][2]) / 2)
    for di, e in enumerate(inked):
        if e['kind'] != 'divider' or not e.get('_div_st'):
            continue
        left = next((o for o in reversed(inked[:di])
                     if o['kind'] != 'divider'), None)
        right = next((o for o in inked[di + 1:]
                      if o['kind'] != 'divider'), None)
        if left is None or right is None:
            continue
        f0 = left['ink'][2] + W * 0.008
        f1 = right['ink'][0] - W * 0.008
        cx = (e['ink'][0] + e['ink'][2]) / 2
        if f0 >= f1 or f0 <= cx <= f1:
            continue
        dx_ = (f0 + f1) / 2 - cx
        old_ink, old_lab = e['ink'], e.get('lab_box')
        e['_div_st'][:] = _sb_shift_strokes(e['_div_st'], dx_, 0.0)
        e['box'] = (e['box'][0] + dx_, e['box'][1],
                    e['box'][2] + dx_, e['box'][3])
        e['ink'] = (old_ink[0] + dx_, old_ink[1],
                    old_ink[2] + dx_, old_ink[3])
        if old_lab:
            e['lab_box'] = (old_lab[0] + dx_, old_lab[1],
                            old_lab[2] + dx_, old_lab[3])
            if e.get('_lab_st'):
                e['_lab_st'][:] = _sb_shift_strokes(
                    e['_lab_st'], dx_, 0.0)
        for bi, bx in enumerate(boxes):
            if bx[1] == old_ink:
                boxes[bi] = (bx[0], e['ink']) + bx[2:]
            elif old_lab and bx[1] == old_lab:
                boxes[bi] = (bx[0], e['lab_box']) + bx[2:]
    # a label may sit on nothing but its own element: stagger a colliding
    # label a line lower, then shrink it — the audit and QA boxes below
    # see the final resting positions
    for _round in range(4):
        moved = False
        for e in draw_els:
            lbb = e.get('lab_box')
            lst_ = e.get('_lab_st')
            if not lbb or not lst_:
                continue
            hits = [bx for bx in boxes
                    if bx[1] is not lbb and bx[1] is not e.get('ink')
                    and bx[2] not in ('title', 'caption', 'panel')
                    and _sb_ovl(lbb, bx[1], 2.0)]
            if not hits:
                continue
            dy_ = max(h[1][3] for h in hits) - lbb[1] + H * 0.006
            # a label that can't fit under the band may take the empty
            # lane above the caption — anywhere but on top of ink
            cap_ = next((bx[1] for bx in boxes if bx[2] == 'caption'),
                        None)
            if lbb[3] + dy_ <= band_b + H * 0.01 or (
                    cap_ is not None
                    and lbb[3] + dy_ <= cap_[1] - H * 0.006):
                lst_[:] = _sb_shift_strokes(lst_, 0.0, dy_)
                nb = (lbb[0], lbb[1] + dy_, lbb[2], lbb[3] + dy_)
            else:
                # no room below: try sliding past the hit sideways
                cands = []
                for h in hits:
                    cands += [h[1][0] - lbb[2] - W * 0.006,
                              h[1][2] - lbb[0] + W * 0.006]
                pick = next((d for d in sorted(cands, key=abs)
                             if -W / 2 + W * 0.025 <= lbb[0] + d
                             and lbb[2] + d <= W / 2 - W * 0.025
                             and not any(_sb_ovl(
                                 (lbb[0] + d, lbb[1],
                                  lbb[2] + d, lbb[3]), h[1], 2.0)
                                 for h in hits)), None)
                # a sideways slide must not detach the label from its
                # own element — keep the label centre over its ink span
                ink_ = e.get('ink')
                if pick is not None and ink_:
                    _lcx = (lbb[0] + lbb[2]) / 2 + pick
                    _iw = ink_[2] - ink_[0]
                    if not (ink_[0] - 0.15 * _iw <= _lcx
                            <= ink_[2] + 0.15 * _iw):
                        pick = None
                if pick is not None:
                    lst_[:] = _sb_shift_strokes(lst_, pick, 0.0)
                    nb = (lbb[0] + pick, lbb[1],
                          lbb[2] + pick, lbb[3])
                    e['lab_box'] = nb
                    for bi, bx in enumerate(boxes):
                        if bx[1] is lbb:
                            boxes[bi] = (bx[0], nb) + bx[2:]
                            break
                    moved = True
                    continue
                lcx = (lbb[0] + lbb[2]) / 2
                lcy = (lbb[1] + lbb[3]) / 2
                for li, st_ in enumerate(lst_):
                    pts = [(lcx + (px - lcx) * 0.85,
                            lcy + (py - lcy) * 0.85)
                           for px, py in st_[0]]
                    lst_[li] = (pts,) + tuple(st_[1:])
                nb = _sb_bounds(s_[0] for s_ in lst_)
            e['lab_box'] = nb
            for bi, bx in enumerate(boxes):
                if bx[1] is lbb:
                    boxes[bi] = (bx[0], nb) + bx[2:]
                    break
            moved = True
        if not moved:
            break
    back_names = {e['it'].get('label', '?') for e in els
                  if e.get('on_back')}
    fx0, fy0, fx1, fy1 = (-W / 2 + W * 0.025, -H / 2 + H * 0.03,
                          W / 2 - W * 0.025, H / 2 - H * 0.03)
    boxes = [bx if len(bx) == 4 else bx + (set(),) for bx in boxes]
    for i in range(len(boxes)):
        na, A, ta, ra = boxes[i]
        if A[0] < fx0 or A[1] < fy0 or A[2] > fx1 or A[3] > fy1:
            audit.append(('off-frame', na))
        for jj in range(i + 1, len(boxes)):
            nb, B, tb, rb = boxes[jj]
            # a zero-area box is an undrawn marker (stage tableau roles
            # keep only a slot note) — nothing visible to collide with
            if B[2] - B[0] < 1.0 or B[3] - B[1] < 1.0:
                continue
            if na in back_names or nb in back_names:
                # a back-row backdrop sits behind the front row by design
                continue
            if sec.get('composition') == 'stage' and (
                    id(A) in box_moments and id(B) in box_moments
                    and box_moments[id(A)] != box_moments[id(B)]):
                continue
            if {ta, tb} in ({'rider', 'chart'}, {'rider'}) \
                    or 'panel' in (ta, tb):
                continue
            if (ta == 'mark' and (nb in ra
                    or str(nb).removeprefix('label:') in ra)) \
                    or (tb == 'mark' and (na in rb
                        or str(na).removeprefix('label:') in rb)):
                continue
            # an edge word and a mark touching the same node co-locate by
            # design — they annotate the same corner of the diagram
            if ta == 'mark' and tb == 'label' and any(
                    lr & ra for _n, _b, _t, lr in boxes
                    if _t == 'link' and _n in rb):
                continue
            if tb == 'mark' and ta == 'label' and any(
                    lr & rb for _n, _b, _t, lr in boxes
                    if _t == 'link' and _n in ra):
                continue
            if ta == tb == 'mark' and ra & rb:
                continue
            if 'mark' in (ta, tb) and 'arrow' in (ta, tb):
                continue
            if 'link' in (ta, tb):
                if ta == tb or na in rb or nb in ra or 'mark' in (ta, tb):
                    continue
                pts_, O_ = (link_pts[na], B) if ta == 'link' else (
                    link_pts[nb], A)
                if any(O_[0] + 2 < x < O_[2] - 2 and O_[1] + 2 < y < O_[3] - 2
                       for x, y in pts_):
                    audit.append((na, nb))
                continue
            if tb == 'label' and ta == 'chart' or ta == 'label' and tb == 'chart':
                lb = A if ta == 'label' else B
                if any(_sb_ovl(lb, sg) for sg in chart_segs):
                    audit.append((na, nb))
                continue
            if _sb_ovl(A, B, 2.0) and frozenset((na, nb)) not in contact_:
                audit.append((na, nb))
    sec['qa_content'] = (L, band_t, L + Wc, band_b)
    sec['qa_marks'] = [bx[0] for bx in boxes if bx[2] == 'mark']
    if audit:
        plan.setdefault('_sb_audit', []).append({'beat': si,
                                                 'issues': audit})
    sec['qa_boxes'] = [(bx[0], bx[1], bx[2]) for bx in boxes]
    sec['qa_els'] = [{'label': e['it'].get('label', ''), 'kind': e['kind'],
                      'emo': e['emo'], 'ink': e.get('ink'),
                      'figure_unit': e.get('figure_unit'),
                      'icon': next((g[4].get('icon') for g, _s, _e in
                                    e['it']['groups'] if g[4]
                                    and g[4].get('icon') is not None), None),
                      'role': e['m'], 'kid': bool(e.get('kid_of')),
                      'drawn_count': e.get('drawn_count', 1),
                      'in_activity': e.get('att') in ('activity', 'behind')
                      or bool(e.get('drawn')),
                      'act_meta': e.get('act_meta'),
                      'lab_box': e.get('lab_box'),
                      'panel': e.get('panel', (e.get('kid_of') or {}).get(
                          'panel')),
                      'on_lap': bool(e.get('on_lap')),
                      'label_text': ' '.join(e['label'] or [])}
                     for e in all_els]
    _sb_pen_budget(sec, t0, t1, fade, pre=pre_groups)
    return uid


def _sb_pen_budget(sec, t0, t1, fade, pre=None):
    """The hand draws everything, one group at a time: serialize the
    scene's ink in authored order so no two groups are on the board at
    once, and give each group a window long enough to read as drawn
    (a stroke needs ~55ms of pen time). Groups stay anchored at or after
    their authored cue — narration is never drawn early, only queued
    behind the previous stroke. Everything must finish before the
    scene's fade starts."""
    units = []
    for pi, (g, s, e) in enumerate(pre or []):
        units.append(('pre', len(g[1]), pi))
    if sec.get('title_st'):
        units.append(('title', len(sec['title_st']), None))
    for it in sec.get('items2') or []:
        for gi, (g, s, e) in enumerate(it['groups']):
            units.append(('g', len(g[1]), (it, gi)))
    if not units:
        return
    end_b = max(t0 + 0.4, (fade[0] - 0.10) if fade else t1)
    cursor = t0 + 0.12
    # a tail-pinned group (the scene caption, authored to ink late in the
    # beat) keeps its window; everything before it compresses into the
    # room that remains so nothing overlaps it
    last_o = None
    lkind, _ln, lref = units[-1]
    if lkind == 'g':
        last_o = lref[0]['groups'][lref[1]][1]
    elif lkind == 'pre':
        last_o = pre[lref][1]
    def _assign(unit, s, e):
        kind, _n, ref = unit
        if kind == 'title':
            sec['title_window'] = (s, e)
        elif kind == 'pre':
            g, _s0, _e0 = pre[ref]
            pre[ref] = (g, s, e)
        else:
            it, gi = ref
            g, _s0, _e0 = it['groups'][gi]
            it['groups'][gi] = (g, s, e)

    pinned = None
    if last_o is not None and last_o > t0 + (t1 - t0) * 0.55:
        pinned = units[-1]
        units = units[:-1]
        end_b = min(end_b, last_o - 0.05)
    needs = [min(2.4, max(0.28, n * 0.055)) for _k, n, _r in units]
    avail = end_b - cursor
    scale = min(1.0, avail / sum(needs)) if needs else 1.0
    for (kind, n, ref), need in zip(units, needs):
        w = max(0.14, need * scale)
        s_o = (ref[0]['groups'][ref[1]][1] if kind == 'g'
               else (pre[ref][1] if kind == 'pre' else cursor))
        s = max(cursor, min(s_o, end_b - w))
        e = s + w
        _assign((kind, n, ref), s, e)
        cursor = e
    if pinned is not None:
        kind, n, ref = pinned
        if kind == 'g':
            _g, s_o, e_o = ref[0]['groups'][ref[1]]
        elif kind == 'pre':
            _g, s_o, e_o = pre[ref]
        else:
            s_o, e_o = cursor, cursor + 0.5
        s = max(cursor, s_o)
        e = s + max(0.14, min((e_o or s_o + 0.5) - s_o, 1.2))
        e = min(e, max(s + 0.14, (fade[0] - 0.02) if fade else t1))
        _assign(pinned, s, e)
    for it in sec.get('items2') or []:
        if it['groups']:
            it['t_window'] = (min(x[1] for x in it['groups']),
                              max(x[2] for x in it['groups']))


def _sb_shift_strokes(strokes, dx, dy):
    out = []
    for st in strokes:
        if len(st) > 4 and st[4]:
            pts = [(p[0] + dx, p[1] + dy) for p in st[0]]
            st = (pts,) + tuple(st[1:])
        out.append(st)
    return out


def _sb_shift_rect(b, dx, dy):
    if (isinstance(b, (list, tuple)) and len(b) >= 4
            and all(isinstance(v, (int, float)) for v in b[:4])):
        return (b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy)
    return b


def _sb_shift_groups(groups, dx, dy):
    out = []
    for g, s, e in groups:
        g = (g[0], _sb_shift_strokes(g[1], dx, dy),
             (g[2][0] + dx, g[2][1] + dy), g[3], g[4])
        out.append((g, s, e))
    return out


def _sb_shift_section(sec, dx, dy):
    """Move a scene composed in a small centred frame into its cell on the
    board by translating every piece of geometry _sb_scene emitted."""
    for it in sec.get('items2') or []:
        it['bounds2'] = _sb_shift_rect(it.get('bounds2'), dx, dy)
        it['groups'] = _sb_shift_groups(it['groups'], dx, dy)
    sec['title_st'] = _sb_shift_strokes(sec.get('title_st') or [], dx, dy)
    for k in ('content', 'qa_content'):
        if sec.get(k):
            sec[k] = _sb_shift_rect(sec[k], dx, dy)
    if sec.get('qa_boxes'):
        sec['qa_boxes'] = [(bx_[0], _sb_shift_rect(bx_[1], dx, dy))
                           + tuple(bx_[2:]) for bx_ in sec['qa_boxes']]
    for p_ in sec.get('qa_panels') or []:
        if isinstance(p_, dict) and p_.get('rect'):
            p_['rect'] = _sb_shift_rect(p_['rect'], dx, dy)
    for e_ in sec.get('qa_els') or []:
        for k_ in ('ink', 'lab_box'):
            if e_.get(k_):
                e_[k_] = _sb_shift_rect(e_[k_], dx, dy)
    for q_ in sec.get('qa_quantities') or []:
        if q_.get('bounds'):
            q_['bounds'] = _sb_shift_rect(q_['bounds'], dx, dy)
    if isinstance(sec.get('panels'), dict):
        sec['panels'] = {k_: _sb_shift_rect(r_, dx, dy)
                         for k_, r_ in sec['panels'].items()}
    for fk in ('fm', 'fm2'):
        if isinstance(sec.get(fk), dict):
            sec[fk]['bounds2'] = _sb_shift_rect(sec[fk]['bounds2'], dx, dy)


def _build(plan, ratio):
    """Precompute boards/sections/items/timing; cached per plan+ratio."""
    cache = plan.setdefault('_bs_flow', {})
    if ratio in cache:
        return cache[ratio]
    v3r.configure_art(plan)
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
    # board_layout: 'grid' is the storyboard treatment composed onto a
    # sheet of cells — one panel per beat, drawn in turn and kept on the
    # paper, so the finished quadrants are the final image (the reference
    # look). board_layout: 'storyboard' keeps the full-frame behaviour.
    layout_ = str(plan.get('board_layout') or '')
    storyboard = layout_ in ('storyboard', 'grid')
    grid = layout_ == 'grid'
    del board_rect
    nsec = len(sections)
    m2 = 0.04 * W
    bx0, by0 = -W / 2 + m2, -H / 2 + m2 * 1.15
    bw, bh = W - 2 * m2, H - 2 * m2 * 1.45
    board_rect = (bx0, by0, bw, bh)
    header = bh * 0.10
    ax0, ay0, aw, ah = bx0, by0 + header, bw, bh - header
    rw_, rh_ = aw, ah
    regions = [(ax0, ay0, rw_, rh_)] * nsec
    if grid and nsec > 1:
        # square-ish sheet of cells, row-major; a short final row's cells
        # stretch to fill the width like a comic's last panel
        gcols = 2 if nsec <= 4 else (3 if aw >= ah else 2)
        grows = (nsec + gcols - 1) // gcols
        gch = ah / grows
        ggap = min(aw, ah) * 0.030
        regions = []
        for gi_ in range(nsec):
            gr_ = gi_ // gcols
            gn_ = min(gcols, nsec - gr_ * gcols)
            gc_ = gi_ - gr_ * gcols
            gcw = aw / gn_
            regions.append((ax0 + gc_ * gcw + ggap,
                            ay0 + gr_ * gch + ggap,
                            gcw - 2 * ggap, gch - 2 * ggap))
    divs = []
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
        # one masthead title for the whole board, centred, with the
        # reference's squiggle underline — per-scene headings are dropped
        th_ = min(header * 0.58, 88.0)
        tw_ = text_width(title, th_)
        if tw_ > bw * 0.80:
            th_ *= bw * 0.80 / tw_
            tw_ = text_width(title, th_)
        tx_ = bx0 + bw / 2 - tw_ / 2
        title_st = text_strokes(title, (tx_, by0 + header * 0.10),
                                th_, 'ink', 1.15)
        und0 = _wobble_line((tx_ + tw_ * 0.02, by0 + header * 0.10
                             + th_ * 1.28),
                            (tx_ + tw_ * 0.98, by0 + header * 0.10
                             + th_ * 1.28), n=30, wob=2.0, seed=7)
        title_st.append((und0, 'a_yellow', 2.6, False, True))
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

    if grid and nsec > 1:
        # hand-ruled separators up front with the masthead so the sheet
        # reads as one page of panels before the first scene inks
        gcols = 2 if nsec <= 4 else (3 if aw >= ah else 2)
        grows = (nsec + gcols - 1) // gcols
        gch = ah / grows
        gsep = []
        for gr_ in range(grows):
            gn_ = min(gcols, nsec - gr_ * gcols)
            gcw = aw / gn_
            gy0_, gy1_ = ay0 + gr_ * gch, ay0 + (gr_ + 1) * gch
            for gc_ in range(1, gn_):
                gx_ = ax0 + gc_ * gcw
                gsep.append((_wobble_line(
                    (gx_, gy0_ + gch * 0.03), (gx_, gy1_ - gch * 0.03),
                    n=18, wob=1.1, seed=gr_ * 31 + gc_), 'ink', 1.4,
                    False, True))
            if gr_:
                gsep.append((_wobble_line(
                    (ax0 + aw * 0.02, gy0_), (ax0 + aw * 0.98, gy0_),
                    n=40, wob=1.3, seed=gr_ * 97), 'ink', 1.4, False, True))
        divs.append((('marks', gsep, (0.0, 0.0), 1.0, None),
                     max(0.0, first_t0 - 0.3), first_t0 + 0.7))

    story_units, story_rooms = [], []
    if storyboard:
        for si, sec in enumerate(sections):
            scene = sec['beat'].get('scene') or {}
            if scene.get('composition') != 'stage':
                continue
            start = sec['beat']['start_seconds']
            end = start + float(sec['beat'].get('duration_seconds', 3.0))
            probe = deepcopy(sec)
            if grid:
                # cast/room sizes are probed at cell scale so the whole
                # sheet shares one figure unit
                pw_ = min(r_[2] for r_ in regions)
                ph_ = min(r_[3] for r_ in regions)
                _sb_scene(probe, si, deepcopy(plan), pw_, ph_ * 0.82,
                          start, end, (end, end + 0.5), 0)
            else:
                _sb_scene(probe, si, deepcopy(plan), W, H, start, end,
                          (end, end + 0.5), 0)
            if probe.get('figure_unit'):
                story_units.append(probe['figure_unit'])
            story_rooms += probe.get('fill_rooms') or []
    story_unit = min(story_units) if story_units else None
    # one cast size for the whole reel: the tightest picture sets it
    story_fill = min(story_rooms) if story_rooms else None

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
        # per-section title — lettered at the top of the region it owns.
        # Storyboard (non-grid) scenes draw NO numbered swash heading —
        # the reel's masthead already titles the film; only the scene's
        # one-line descriptor stays at the top, in plain ink
        ttl = str(sec['beat'].get('title') or sec.get('label') or '').strip()
        sw_col = _SWASH[si % len(_SWASH)]
        title_h = 0.0
        num_st = []
        lead_w = 0.0
        th2 = 0.0
        if storyboard and not grid:
            sub = str(sec['beat'].get('subtitle') or '').strip()
            if sub:
                sh_ = min(rh * 0.06, 44.0)
                if text_width(sub, sh_) > rw * 0.86:
                    sh_ *= rw * 0.86 / text_width(sub, sh_)
                sec['title_st'] = text_strokes(
                    sub, (rx + rw * 0.05, ry + rh * 0.05), sh_, 'ink', 0.9)
                title_h = sh_ * 2.1
        elif ttl:
            th2 = min(rh * (0.15 if grid else
                            (0.105 if storyboard else 0.115)),
                      120.0 if grid else 78.0)
            if storyboard and nsec > 1:
                # "1. Heading" — the number stays on the paper, the title
                # sits on the swash, matching the reference panels; the
                # whole line shrinks to the cell width as one unit
                ttl = re.sub(r'^\s*\d+\s*[.)]\s*', '', ttl) or ttl
                num_w = text_width(f'{si + 1}.', th2)
                gap_ = th2 * 0.30
                tot = num_w + gap_ + text_width(ttl, th2)
                if tot > rw * 0.90:
                    th2 *= rw * 0.90 / tot
                    num_w = text_width(f'{si + 1}.', th2)
                    gap_ = th2 * 0.30
                num_st = text_strokes(f'{si + 1}.',
                                      (rx + rw * 0.05, ry + rh * 0.05),
                                      th2, 'ink', 1.2)
                lead_w = num_w + gap_
            elif text_width(ttl, th2) > rw * 0.8:
                th2 *= rw * 0.8 / text_width(ttl, th2)
            tts = text_strokes(ttl, (rx + rw * 0.05 + lead_w, ry + rh * 0.05),
                               th2, 'ink', 1.2)
            tts += [([(px + th2 * 0.045, py + th2 * 0.02)
                      for px, py in s[0]], s[1], s[2], s[3], s[4])
                    for s in list(tts)]
            if storyboard:
                tw2 = text_width(ttl, th2)
                bx_0 = rx + rw * 0.05 + lead_w - th2 * 0.22
                band = [(bx_0, ry + rh * 0.05 - th2 * 0.15),
                        (bx_0 + tw2 + th2 * 0.5,
                         ry + rh * 0.05 - th2 * 0.15),
                        (bx_0 + tw2 + th2 * 0.5,
                         ry + rh * 0.05 + th2 * 1.25),
                        (bx_0, ry + rh * 0.05 + th2 * 1.25),
                        (bx_0, ry + rh * 0.05 - th2 * 0.15)]
                # swash band inks first, then the heading letters on it
                tts = [(band, sw_col, 1.0, 'solid', True)] + tts
            sec['title_st'] = num_st + tts
            title_h = (th2 * 1.32 + rh * 0.02 if storyboard
                       else th2 * 1.5 + rh * 0.04)
            sub = str(sec['beat'].get('subtitle') or '').strip()
            if storyboard and sub:
                # the panel's one-line description under its swash heading
                sh_ = th2 * 0.52
                if text_width(sub, sh_) > rw * 0.86:
                    sh_ *= rw * 0.86 / text_width(sub, sh_)
                sec['title_st'] += text_strokes(
                    sub, (rx + rw * 0.05, ry + rh * 0.05 + th2 * 1.42),
                    sh_, 'ink', 0.9)
                title_h += sh_ * 1.9
        # bottom caption strip (storyboard quote line) is reserved so items
        # never land on it
        cap = str(sec['beat'].get('caption') or '').strip()
        cap_h = rh * 0.13 if (storyboard and cap) else 0.0
        cap_bb = None
        if storyboard and cap:
            # resolve the caption's real text bounds now so annotations may
            # use the strip's free corners while never touching the quote
            ch_ = rh * 0.078
            cw_ = text_width(cap, ch_)
            if cw_ > rw * 0.92:
                ch_ *= rw * 0.92 / cw_
                cw_ = text_width(cap, ch_)
            cap_bb = (rx + rw / 2 - cw_ / 2, ry + rh * 0.955 - ch_ * 1.5,
                      rx + rw / 2 + cw_ / 2, ry + rh * 0.955 - ch_ * 0.1)
            sec['_cap'] = cap_bb
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
        # scene separation: everything this scene places fades off the
        # paper as the next scene opens — except on a grid sheet, where a
        # scene's ink persists inside its cell for the whole reel
        sec['fade'] = (None if grid else
                       ((nxt_t0 - 0.15, nxt_t0 + 0.45)
                        if nxt_t0 is not None
                        else (t1, t1 + WIPE_SECONDS * 0.8)))
        if not k:
            sec['items2'] = []
            continue
        if storyboard:
            if grid:
                # compose the scene in a small centred frame sized to the
                # cell's inner area (below its numbered heading), then
                # shift the finished picture home into the cell
                top_room = title_h if ttl else rh * 0.04
                fr_ = (rx + rw * 0.015, ry + top_room + rh * 0.012,
                       rw * 0.97, rh - top_room - rh * 0.027)
                probe = deepcopy(sec)
                cell_tts = sec.get('title_st') or []
                uid = _sb_scene(probe, si, plan, fr_[2], fr_[3], t0, t1,
                                sec['fade'], uid,
                                figure_unit=story_unit,
                                fill_unit=story_fill)
                _sb_shift_section(probe, fr_[0] + fr_[2] / 2,
                                  fr_[1] + fr_[3] / 2)
                probe['title_st'] = cell_tts
                sec.clear()
                sec.update(probe)
            else:
                keep_tts = sec.get('title_st') or []
                uid = _sb_scene(sec, si, plan, W, H, t0, t1, sec['fade'],
                                uid, figure_unit=story_unit,
                                fill_unit=story_fill,
                                band_floor=(ry + rh * 0.05 + title_h
                                            + rh * 0.015
                                            if title_h else None),
                                pre_groups=(title_item['groups']
                                            if si == 0 else None))
                if keep_tts:
                    sec['title_st'] = keep_tts
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
        if storyboard:
            # authored order IS the narrative chain — no weight sort
            p_order = list(range(k))
        else:
            p_order = sorted(range(k), key=lambda j: -weights[j])
        # storyboard chain geometry: proportional slots left to right with
        # arrow gaps between them
        _SB_W = {'divider': 0.14, 'stack-list': 1.30, 'chart-journey': 1.55,
                 'crowd': 1.15}
        if storyboard:
            # the compiler strips custom role fields — pull them straight
            # from the beat's roles (index-aligned with items)
            scn = sec['beat'].get('scene') or {}
            raw_roles = ([scn.get('heroRole') or {}]
                         + list(scn.get('supportingRoles') or []))
            sb_meta = [(raw_roles[ri] if ri < len(raw_roles) else {})
                       for ri in _sb_role_indices(items, raw_roles)]
        else:
            sb_meta = [next((g[4] for g, _s, _e in it['groups'] if g[4]),
                            {}) or {}
                       for it in items]
        # scene archetype: the layout follows what the scene IS, not one
        # fixed template — 'journey' scenes center on their chart, 'focus'
        # scenes stage 1-2 elements large, 'chain' scenes read L->R
        sb_slots = []
        if storyboard:
            sb_gls = [m.get('glyph') or '' for m in sb_meta]
            rider = [bool(m.get('on_chart')) for m in sb_meta]
            arch = ('journey' if 'chart-journey' in sb_gls
                    else ('focus' if k <= 2 else 'chain'))

            def _hfrac(j):
                gl = sb_gls[j]
                if rider[j]:
                    return 0.34 if arch == 'journey' else 0.52
                if gl in _SB_W:
                    return {'divider': 0.80, 'crowd': 0.42,
                            'stack-list': 0.82,
                            'chart-journey': 0.80}[gl]
                return 0.78 if _is_person_item(items[j]) else 0.62

            if arch == 'journey':
                # the chart IS the panel: big canvas left-of-centre, riders
                # stand on it, remaining elements stack in a right column
                cj = sb_gls.index('chart-journey')
                col = [j for j in range(k) if not rider[j]
                       and sb_gls[j] != 'divider' and j != cj]
                ncol = max(1, len(col))
                for j in range(k):
                    if rider[j]:
                        sb_slots.append((cx0 + cw * 0.40, cw * 0.18,
                                         0.56, _hfrac(j)))
                    elif j == cj:
                        sb_slots.append((cx0, cw * 0.60, 0.60,
                                         _hfrac(j)))
                    elif sb_gls[j] == 'divider':
                        sb_slots.append((cx0 + cw * 0.615, cw * 0.05,
                                         0.58, _hfrac(j)))
                    else:
                        ci = col.index(j)
                        sb_slots.append((cx0 + cw * 0.69, cw * 0.30,
                                         0.14 + 0.76 * (ci + 0.5) / ncol,
                                         min(0.62, 0.80 / ncol)))
            elif arch == 'focus':
                for j in range(k):
                    x0f = (cx0 + cw * (0.06 + 0.50 * j) if k == 2
                           else cx0 + cw * 0.20)
                    sb_slots.append((x0f, cw * (0.42 if k == 2 else 0.60),
                                     0.50, min(0.72, _hfrac(j) + 0.10)))
            else:
                # annotation-aware chain: an element's label lives in the
                # gap trailing it, so the gap must reserve the label's real
                # width (a label that can't fit anywhere gets dropped —
                # better a reserved lane than a dropped annotation)
                lh0 = rh * 0.052
                wts = [_SB_W.get(sb_gls[j], 1.0) for j in range(k)]
                gap_px = []
                for j in range(k):
                    ant_ = str(sb_meta[j].get('annotate') or '').strip()
                    lw_ = (max(text_width(ln, lh0)
                               for ln in ant_.split('\n'))
                           if ant_ else 0.0)
                    gap_px.append(max(cw * 0.07, lw_ + lh0 * 1.0))
                rem = cw - sum(gap_px)
                if rem < cw * 0.45:    # over-labelled: shrink gaps, keep
                    rem = cw * 0.45    # elements legible; labels shrink
                    sc = (cw - rem) / sum(gap_px)
                    gap_px = [g * sc for g in gap_px]
                sf = rem / sum(wts)
                xcur = cx0
                for j in range(k):
                    wd = wts[j] * sf
                    sb_slots.append((xcur, wd, 0.56, _hfrac(j)))
                    xcur += wd + gap_px[j]
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
            meta_ = sb_meta[j]
            glyph = meta_.get('glyph') or ''
            if storyboard and glyph in _SB_GLYPHS:
                # procedural element: the box only sizes placement — world-
                # space strokes are appended after position is known
                # (absolute strokes; icon group strokes are emptied).
                # The divider's box is tall/thin so it scales by height.
                nb = ((-8.0, -50.0, 8.0, 50.0) if glyph == 'divider'
                      else (-50.0, -50.0, 50.0, 50.0))
                it['bounds'] = nb
                it['groups'] = [
                    (((g[0], [], g[2], g[3], g[4]) if g[0] == 'icon'
                      else g), s, e)
                    for g, s, e in it['groups']]
            b = it['bounds']
            w = max(30.0, b[2] - b[0])
            h = max(30.0, b[3] - b[1])
            bcx, bcy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
            hero = (j == p_order[0] and not storyboard)
            # hero fills ~60% of the region, satellites ~30% — a tight size
            # band keeps every element at a readable, uniform weight.
            # Storyboard chains size each element to its own slot.
            if storyboard:
                sx0, swd, cfr, hfr = sb_slots[j]
                fh = ch * hfr
                fw = swd * 0.94
            else:
                fw = cw * (0.60 if hero
                           else (0.40 if person else 0.32))
                fh = ch * (0.66 if hero
                           else (0.62 if person else 0.34))
            bo2 = min(fw / w, fh / h)
            if hero:
                cands = [sat_pts[0]]
            elif storyboard:
                sx0, swd, cfr, _hfr = sb_slots[j]
                px_, py_ = sx0 + swd / 2, cy0 + ch * cfr
                anch = meta_.get('on_chart')
                if anch:
                    # anchor to a point on an already-placed chart-journey
                    # element (world coords read off its placed box)
                    for oj in range(k):
                        oit = items[oj]
                        if (oit is not it and oit.get('bounds2') and
                                (sb_meta[oj].get('glyph') or '')
                                == 'chart-journey'):
                            bx0_, by0_, bx1_, by1_ = oit['bounds2']
                            bw_, bh_ = bx1_ - bx0_, by1_ - by0_
                            anch_map = {
                                'peak': (bx0_ + bw_ * 0.30,
                                         by0_ + bh_ * 0.10),
                                'valley': (bx0_ + bw_ * 0.55,
                                           by0_ + bh_ * 0.74),
                                'rise': (bx0_ + bw_ * 0.78,
                                         by0_ + bh_ * 0.34),
                            }
                            if anch in anch_map:
                                ax_, ay_ = anch_map[anch]
                                px_, py_ = ax_, ay_ - h * bo2 / 2 - 4
                                it['_anch_pt'] = (ax_, ay_)
                            break
                cands = [(px_, py_)]
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
        # the hero — the reference's actor->object / tag->object links.
        # Storyboard chains link consecutive elements instead.
        hero_it = (None if storyboard
                   else (placed[p_order[0]] if p_order and placed
                         else None))
        if storyboard:
            # strip per-item captions — panels carry micro-annotations and
            # the bottom quote, not under-element name labels
            for it in placed:
                if it is not None:
                    it['groups'] = [ge for ge in it['groups']
                                    if ge[0][0] != 'caption']
            vis = [it for it in placed
                   if it is not None and it.get('bounds2')]
            meta_of = {id(items[j]): sb_meta[j] for j in range(k)}
            # the title band is off-limits to annotations; so is the
            # quote caption's actual text box (its strip corners are free)
            placed_bounds.append((cx0, cy0 - rh * 0.20, cx0 + cw, cy0))
            if sec.get('_cap'):
                placed_bounds.append(sec['_cap'])
            # procedural glyphs draw in world coords over their placed box
            for it in vis:
                gl = (meta_of.get(id(it)) or {}).get('glyph') or ''
                if gl in _SB_GLYPHS:
                    i0_, i1_ = it['t_window']
                    gen = _sb_glyph(gl, it['bounds2'],
                                    meta_of.get(id(it)) or {})
                    if gen:
                        it['groups'].append(
                            (('glyph', gen, (0, 0), 1.0, None),
                             i0_, i0_ + (i1_ - i0_) * 0.82))
            # annotation obstacles: a chart-journey item blocks by its real
            # polyline SEGMENTS (padded), not its whole bounding box — the
            # panel whitespace inside the chart frame stays usable
            chart_boxes = {}
            for it in vis:
                if (meta_of.get(id(it)) or {}).get('glyph') == 'chart-journey':
                    bx = it['bounds2']
                    w_, h_ = bx[2] - bx[0], bx[3] - bx[1]
                    pts = [(bx[0], bx[1] + h_ * 0.78),
                           (bx[0] + w_ * 0.30, bx[1] + h_ * 0.10),
                           (bx[0] + w_ * 0.55, bx[1] + h_ * 0.74),
                           (bx[0] + w_ * 0.78, bx[1] + h_ * 0.34),
                           (bx[2], bx[1] + h_ * 0.10)]
                    # subdivide each leg into thin sub-boxes — a diagonal
                    # segment's whole bbox would wall off half the panel
                    segpad = 4.0
                    segs = []
                    for a_, b_ in zip(pts, pts[1:]):
                        for ti in range(6):
                            t0_, t1_ = ti / 6.0, (ti + 1) / 6.0
                            q0 = (a_[0] + (b_[0] - a_[0]) * t0_,
                                  a_[1] + (b_[1] - a_[1]) * t0_)
                            q1 = (a_[0] + (b_[0] - a_[0]) * t1_,
                                  a_[1] + (b_[1] - a_[1]) * t1_)
                            segs.append(
                                (min(q0[0], q1[0]) - segpad,
                                 min(q0[1], q1[1]) - segpad,
                                 max(q0[0], q1[0]) + segpad,
                                 max(q0[1], q1[1]) + segpad))
                    chart_boxes[it['bounds2']] = segs
            audit_boxes = [[it.get('label', '?'), it['bounds2'],
                            meta_of.get(id(it)) or {}] for it in vis]
            # chain arrows: consecutive elements link left to right
            gl_of = {id(it): (meta_of.get(id(it)) or {}).get('glyph', '')
                     for it in vis}
            for a_, b_ in zip(vis, vis[1:]):
                if 'divider' in (gl_of.get(id(a_)), gl_of.get(id(b_))):
                    continue
                # riders sit ON the chart — arrows to/from them are noise
                if ((meta_of.get(id(a_)) or {}).get('on_chart')
                        or (meta_of.get(id(b_)) or {}).get('on_chart')):
                    continue
                ba, bb_ = a_['bounds2'], b_['bounds2']
                pa = (ba[2] + cw * 0.012, (ba[1] + ba[3]) / 2)
                pb = (bb_[0] - cw * 0.012, (bb_[1] + bb_[3]) / 2)
                if pb[0] - pa[0] < cw * 0.02:
                    continue
                i0_, i1_ = b_['t_window']
                b_['groups'].insert(0, (
                    ('arrow', _sb_arrow(pa, pb), (0, 0), 1.0, None),
                    i0_, i0_ + (i1_ - i0_) * 0.30))
            # expression overlays + micro-annotations (world coords)
            for it in vis:
                meta_ = meta_of.get(id(it)) or {}
                i0_, i1_ = it['t_window']
                expr = meta_.get('expression') or ''
                halo = meta_.get('halo') or ''
                b2 = it['bounds2']
                extra = []
                if expr:
                    extra += _sb_expr_strokes(expr, b2)
                if extra:
                    it['groups'].append((('marks', extra, (0, 0), 1.0,
                                          None),
                                         i0_ + (i1_ - i0_) * 0.30,
                                         i0_ + (i1_ - i0_) * 0.62))
                if halo:
                    # wash goes behind the figure, drawn first
                    it['groups'].insert(0, (
                        ('marks', _sb_expr_strokes('halo', b2, halo),
                         (0, 0), 1.0, None),
                        i0_, i0_ + (i1_ - i0_) * 0.40))
                ant = str(meta_.get('annotate') or '').strip()
                if ant:
                    chosen = None
                    # riders get an extra anchor: just under their own
                    # point on the line (the trough/peak whitespace)
                    sides = ['right', 'above', 'ur', 'dr',
                             'left', 'below', 'ul', 'dl']
                    if meta_.get('on_chart') and it.get('_anch_pt'):
                        sides = sides[:6] + ['ptbelow'] + sides[6:]
                    # hard no-collision rule: 9 anchors x 3 sizes; a label
                    # that can't land clean is dropped + flagged — never
                    # drawn overlapping
                    for lsc in (1.0, 0.84, 0.68):
                        lh = rh * 0.052 * lsc
                        for side in sides:
                            if side == 'ptbelow':
                                px_, py_ = it['_anch_pt']
                                st_, abb = _sb_annotate(
                                    ant, (px_ - 1, py_ + lh * 0.3,
                                          px_ + 1, py_ + lh * 0.3),
                                    'below', lh)
                            else:
                                st_, abb = _sb_annotate(ant, b2, side, lh)
                            if not st_:
                                continue
                            pad2 = 5.0
                            hit = False
                            for ob in placed_bounds:
                                subs = chart_boxes.get(ob) or (ob,)
                                for sb2 in subs:
                                    if not (abb[2] + pad2 <= sb2[0]
                                            or abb[0] - pad2 >= sb2[2]
                                            or abb[3] + pad2 <= sb2[1]
                                            or abb[1] - pad2 >= sb2[3]):
                                        hit = True
                                        break
                                if hit:
                                    break
                            if (abb[0] < cx0 or abb[2] > cx0 + cw
                                    or abb[1] < cy0 + lh * 0.15
                                    or abb[3] > cy0 + ch + cap_h):
                                hit = True
                            if not hit:
                                chosen = (st_, abb)
                                break
                        if chosen is not None:
                            break
                    if chosen is None:
                        st_, abb = [], b2
                        plan.setdefault('_sb_audit', []).append(
                            {'beat': sec['bi'], 'dropped_label': ant})
                    else:
                        st_, abb = chosen
                    if st_:
                        it['groups'].append((
                            ('plabel', st_, (0, 0), 1.0, None),
                            i0_ + (i1_ - i0_) * 0.68,
                            i0_ + (i1_ - i0_) * 1.02))
                        placed_bounds.append(abb)
                        audit_boxes.append(['label:' + ant, abb, meta_])
            # collision audit: every drawn box — elements AND labels —
            # must be pairwise-clean. Riders intentionally overlap their
            # chart and each other (they stand ON the line).
            audit = []
            for ia in range(len(audit_boxes)):
                for ib in range(ia + 1, len(audit_boxes)):
                    na, A, ma = audit_boxes[ia]
                    nb, B, mb = audit_boxes[ib]
                    if ma is mb and not na.startswith('label:'):
                        continue
                    chart_pair = (
                        (ma.get('on_chart') and mb.get('on_chart'))
                        or (ma.get('on_chart')
                            and mb.get('glyph') == 'chart-journey')
                        or (mb.get('on_chart')
                            and ma.get('glyph') == 'chart-journey'))
                    if chart_pair:
                        continue
                    ov = not (A[2] <= B[0] or B[2] <= A[0]
                              or A[3] <= B[1] or B[3] <= A[1])
                    if ov:
                        audit.append((na, nb))
            if audit:
                flow_audit = plan.setdefault('_sb_audit', [])
                flow_audit.append({'beat': sec['bi'], 'overlaps': audit})
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
            cys = ry + rh * 0.955 - ch_ * 1.5
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

    if storyboard and not grid:
        fade_start, fade_end = sections[0]['fade']
        if len(sections) > 1:
            fade_end = sections[1]['t_window'][0]
        title_item['fade'] = (fade_start, fade_end)
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
    if storyboard:
        fs_ = th_h * 0.95
        th_w = font_text_width('Thanks', fs_, _SB_FT)
        _dw, dh_, dt_ = _sb_text_dims(['Thanks'], fs_, _SB_FT)
        th, _bb = _sb_text(['Thanks'], th_cx, th_cy - dh_ / 2 - dt_, fs_,
                           _SB_FT, 'center')
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
            'dividers': divs, 'persist': grid, 'storyboard': storyboard,
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
            tw0, tw1 = (sec.get('title_window')
                        or (sec['t_window'][0], sec['t_window'][0] + 1.1))
            segs.append((tw0, tw1,
                         st_[0][0][0], st_[-1][0][-1]))
    prev, nxt = None, None
    for s, e, p0, p1 in segs:
        if e <= t and (prev is None or e > prev[0]):
            prev = (e, p1)
        if s > t and (nxt is None or s < nxt[0]):
            nxt = (s, p0)
    if nxt is None:
        return None
    if prev is not None and nxt[0] - prev[0] > 1.2 \
            and t - prev[0] > 0.35 and nxt[0] - t > 0.55:
        return None                  # long hold: the hand steps off
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
    wbp._pal(plan)

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
        tf_ = ti.get('fade')
        if t >= ti['groups'][0][1] and (tf_ is None or t < tf_[1]):
            if tf_ is not None and t >= tf_[0]:
                # masthead easing off the paper with the opening scene
                tfl = Image.new('RGBA', (vw, vh), (0, 0, 0, 0))
                draw_full(ti['groups'], tfl)
                fade_layers.append((tfl, int(255 * (1.0 - wbp._clamp(
                    (t - tf_[0]) / max(0.05, tf_[1] - tf_[0]))))))
            else:
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
            tw0, tw1 = (sec_.get('title_window')
                        or (sec_['t_window'][0], sec_['t_window'][0] + 1.1))
            p = wbp._ease(wbp._clamp(
                (t - tw0) / max(0.05, tw1 - tw0)))
            if p <= 0:
                continue
            t2 = _draw_strokes(tlayer, sec_['title_st'], (0.0, 0.0), 1.0,
                               cam, colors, ratio, p,
                               seed + 71 + sec_['bi'] * 13, zoom)
            if alpha < 255:
                tlayer.putalpha(tlayer.split()[3].point(
                    lambda v: int(v * alpha / 255)))
            frame.paste(tlayer, (0, 0), tlayer)
            if t2 and tw0 <= t <= tw1 + 0.12 \
                    and -40 <= t2[0] <= vw + 40 and -40 <= t2[1] <= vh + 40:
                tip = t2
        if tip is None:
            tip = _travel_tip(flow, ratio, cam, zoom, t)
        return _vignette(_overlay_hand(frame, tip, ratio, t * 8 + seed),
                         ratio)

    # -------- ending --------
    ending = flow['ending']
    rel = t - t_end
    if not flow.get('storyboard') or persist:
        # scenes mode and grid sheets both end on the whole board — the
        # masthead stays; only storyboard's masthead left with its opening
        # scene, so its ending card starts from cleared paper
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


def pen_spans(plan: dict, ratio: str) -> list:
    """Every pen-down interval on the board timeline as absolute
    [start, end, length_px] — mirrors render_board_frame's draw schedule
    (strokes take equal shares of each eased group window) so marker foley
    sounds exactly while ink goes down."""
    flow = _build(plan, ratio)
    out = []

    def add(g, s, e):
        strokes = g[1]
        n = len(strokes)
        k = float(g[3] or 1.0) if len(g) > 3 else 1.0
        for j, st in enumerate(strokes):
            a, b = j / n, (j + 1) / n
            if len(st) > 3 and st[3] and not (len(st) > 4 and st[4]):
                a += 0.38 / n
            pts = st[0]
            ln = sum(math.hypot(q[0] - p[0], q[1] - p[1])
                     for p, q in zip(pts, pts[1:]))
            if not (len(st) > 4 and st[4]):
                ln *= k
            out.append([s + (e - s) * _ease_inv(a),
                        s + (e - s) * _ease_inv(b), round(ln, 1)])

    for g, s, e in flow['title_item']['groups']:
        add(g, s, e)
    for g, s, e in flow.get('dividers') or []:
        add(g, s, e)
    for it in flow['items']:
        fade = it.get('fade')
        for g, s, e in it['groups']:
            if fade is not None and s >= fade[0]:
                continue
            add(g, s, e)
    for sec in flow['sections']:
        if sec.get('title_st') and sec.get('t_window'):
            t0 = sec['t_window'][0]
            add(('title', sec['title_st'], (0, 0), 1.0), t0, t0 + 1.1)
    t0 = flow['total_beats_end'] + WIPE_SECONDS
    for gi, g in enumerate(flow['ending']['thanks']):
        add(g, t0 + gi * 0.9, t0 + gi * 0.9 + max(0.2, THANKS_SECONDS - 0.9))
    return sorted(sp for sp in out if sp[1] > sp[0])
