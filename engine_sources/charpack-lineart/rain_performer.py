"""Rain rig as a front-facing presenter (Synthesia-style avatar).

usage: blender -b <file> --python rain_performer.py -- <score.json|-> <outdir>
         [still] [bust|waist|closeup] [f0 f1]

score.json: {"fps":24,"segments":[{"t":[t0,t1],"text":"...","intent":"wave|explain|
             emphasis|question|ack|think|none","mood":"smile|neutral|serious",
             "energy":0..1}]}  -- '-' or missing file = built-in demo score.

Deterministic: every control is a python curve seeded by segment index.
Gesture scheduling follows the VITA front-facing grammar:
  stillness_first, deliberate-gesture budget (<=2 / 10s, >=3.0s spacing),
  avoid_repeat_last_n=3, flow lag torso->shoulder->upper arm->forearm->wrist,
  hands subordinate to face (gestures shift off big expression changes),
  hand-safety (hands stay below the chin / out of the face zone).
"""
import bpy, sys, math, os, time, json, random
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index('--') + 1:]
SCORE = argv[0]; OUT = argv[1]
STILL = 'still' in argv
FRAME = 'waist'
for m in ('bust', 'waist', 'closeup'):
    if m in argv: FRAME = m
nums = [a for a in argv[2:] if a.lstrip('-').isdigit()]
F0 = int(nums[0]) if len(nums) > 0 else 0
FPS = 24
scene = bpy.context.scene

# ---------- rig adapter (Rain CloudRig, FK controls) ----------
rig = bpy.data.objects['RIG-rain']
B = dict(head='FK-Head', neck='FK-Neck', chest='FK-Chest', spine='FK-Spine', pelvis='MSTR-Pelvis',
         jaw='MSTR-Jaw', upperarm='FK-Upperarm.{S}', forearm='FK-Forearm.{S}', hand='FK-Hand.{S}',
         thigh='FK-Thigh.{S}', shin='FK-Shin.{S}', foot='FK-Foot.{S}',
         finger='FK-{F}{N}.{S}', thumb='FK-Thumb{N}.{S}')
FC = dict(lid_upper='ACT-Eyelid_Upper.{S}', lid_close=-0.030, brow='MSTR-Eyebrow.{S}', brow_up=0.012,
          eyes='TGT-Eyes', gaze=0.10, mouth='MSTR-Mouth', lip_bot='MSTR-LowerLip', lip_top='MSTR-UpperLip',
          lip_open=0.016, corner='ACT-Lips_Corner.{S}', corner_up=0.008, jaw_sign=-1, jaw_deg=20)
FINGERS = ('Index', 'Middle', 'Ring', 'Pinky')
INK = ('hair', 'eyebrow', 'eyelash', 'shoe', 'jeans', 'eyedot', 'gums', 'tongue', 'teeth',
       'viewport_black', 'hairband', 'laces')
HAND_SCALE = float(os.environ.get('HAND_SCALE', 0.92))
HEAD_SCALE = float(os.environ.get('HEAD_SCALE', 1.22))
PALM_THIN = float(os.environ.get('PALM_THIN', 0.65))

def lin(h):
    r, g, b = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    f = lambda c: c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4
    return (f(r), f(g), f(b), 1)
PAPER = lin('#F6F3EC'); INKC = lin('#232220'); ACCENT = lin('#2E5EAA')

def flat(mat, rgba):
    nt = mat.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = rgba
    o = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(em.outputs[0], o.inputs[0])
for m in bpy.data.materials:
    if not m.node_tree or m.grease_pencil: continue
    n = m.name.lower()
    if m.name == 'MAT-rain.top': flat(m, ACCENT)
    elif any(k.lower() in n for k in INK): flat(m, INKC)
    else: flat(m, PAPER)
for name in ('GEO-rain-eye_cornea', 'GEO-rain-scarf'):
    o = bpy.data.objects.get(name)
    if o: o.hide_render = True
for o in bpy.data.objects:
    if o.type == 'LIGHT': o.hide_render = True
    if o.type == 'MESH':
        for md in o.modifiers:
            if md.type == 'SUBSURF': md.render_levels = min(md.render_levels, 1)

# mouth seam: lower-lip faces get a paper material so the seam renders as a border line
def split_lips():
    ob = bpy.data.objects.get('GEO-rain-head')
    if not ob: return
    me = ob.data
    gidx = [g.index for g in ob.vertex_groups if g.name.startswith('DEF-Lip_Bot_')]
    if not gidx: return
    lipmat = bpy.data.materials.new('LipPaper'); lipmat.use_nodes = True; flat(lipmat, PAPER)
    me.materials.append(lipmat); li = len(me.materials) - 1
    w = [0.0] * len(me.vertices)
    for v in me.vertices:
        for g in v.groups:
            if g.group in gidx: w[v.index] = max(w[v.index], g.weight)
    for p in me.polygons:
        if sum(w[i] for i in p.vertices) / len(p.vertices) > 0.45:
            p.material_index = li
if not os.environ.get('NOLIPS'): split_lips()

# ---------- strip shipped animation, force FK ----------
def strip_actions(idb):
    ad = idb.animation_data if idb else None
    if not ad: return
    ad.action = None
    for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
for o in bpy.data.objects:
    strip_actions(o)
    if o.type == 'MESH': strip_actions(o.data.shape_keys)
pb = rig.pose.bones.get('Properties_IKFK')
if pb:
    for k in ('ik_arm_left', 'ik_arm_right', 'ik_leg_left', 'ik_leg_right', 'ik_spine',
              'ik_fingers_left', 'ik_fingers_right'):
        if k in pb.keys(): pb[k] = type(pb[k])(0)
pb = rig.pose.bones.get('Properties_Character_Rain')
if pb and 'Scarf' in pb.keys(): pb['Scarf'] = type(pb['Scarf'])(False)

# ---------- palm proportions (rest space, same as render_lineart_gp) ----------
body = bpy.data.objects.get('GEO-rain-body')
if body and PALM_THIN < 1.0:
    bw2w = body.matrix_world
    for suf in ('.L', '.R'):
        wrist = rig.matrix_world @ rig.data.bones['FK-Hand' + suf].head_local
        mcp = rig.matrix_world @ rig.data.bones['FK-Middle1' + suf].head_local
        thumb = rig.matrix_world @ rig.data.bones['FK-Thumb1' + suf].head_local
        palm_dir = (mcp - wrist).normalized()
        width_dir = palm_dir.cross(palm_dir.cross(thumb - wrist)).normalized()
        thick_dir = palm_dir.cross(width_dir).normalized()
        plane_p = wrist + palm_dir * ((mcp - wrist).length * 0.5)
        gi = {g.index: 1.0 for g in body.vertex_groups if g.name.startswith('DEF-Hand' + suf)}
        for g in body.vertex_groups:
            if any(g.name.startswith('DEF-' + f + suf) for f in FINGERS + ('Thumb',)):
                gi[g.index] = 0.7
        for v in body.data.vertices:
            w = min(1.0, sum(g.weight * gi[g.group] for g in v.groups if g.group in gi))
            if w <= 0.0: continue
            cw = bw2w @ v.co
            v.co = bw2w.inverted() @ (cw - thick_dir * (cw - plane_p).dot(thick_dir) * (1.0 - PALM_THIN) * w)

# ---------- bone helpers ----------
def bone(key, S='L', F='Index', N=1):
    pb = rig.pose.bones.get(B[key].format(S=S, F=F, N=N))
    if pb is None: print('MISSING bone', B[key].format(S=S, F=F, N=N))
    return pb
def fbone(key, S='L'):
    pb = rig.pose.bones.get(FC[key].format(S=S))
    if pb is None: print('MISSING face bone', FC[key].format(S=S))
    return pb
def upd(): bpy.context.view_layer.update()

def rots(ops):
    upd()
    for pb, rl in ops:
        if pb is None: continue
        p = pb.matrix.translation.copy()
        R = Matrix.Identity(4)
        for axis, deg in rl:
            if deg: R = Matrix.Rotation(math.radians(deg), 4, axis) @ R
        pb.matrix = Matrix.Translation(p) @ R @ Matrix.Translation(-p) @ pb.matrix
def brots(pb, rl):
    """rotate a bone about its OWN current axes (X=flex, Y=twist, Z=abduct) in rig space."""
    if pb is None: return
    upd()
    M = pb.matrix; p = M.translation.copy()
    R = Matrix.Identity(4)
    for axis, deg in rl:
        if not deg: continue
        ax = (M.to_3x3() @ Vector((1, 0, 0) if axis == 'X' else (0, 1, 0) if axis == 'Y' else (0, 0, 1))).normalized()
        R = Matrix.Rotation(math.radians(deg), 4, ax) @ R
    pb.matrix = Matrix.Translation(p) @ R @ Matrix.Translation(-p) @ M
def local_rot(pb, x=0, y=0, z=0):
    if pb is None: return
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (math.radians(x), math.radians(y), math.radians(z))
def local_loc(pb, x=0, y=0, z=0):
    if pb is None: return
    pb.location = (x, y, z)

# ---------- hand poses ----------
HAND = {
 'rest_thigh': dict(curl=((8, 16, 10), (12, 22, 12), (16, 26, 14), (20, 30, 16)), spread=(-4, -1, 2, 5), thumb=(6, 4)),
 'relaxed':    dict(curl=((12, 22, 12), (16, 28, 16), (20, 32, 18), (26, 36, 20)), spread=(-3, 0, 3, 6), thumb=(10, 6)),
 'present':    dict(curl=((0, 4, 2), (3, 8, 4), (8, 12, 6), (12, 16, 8)), spread=(-9, -3, 4, 10), thumb=(-8, -2)),
 'open':       dict(curl=((0, 2, 0), (0, 3, 0), (4, 6, 2), (8, 10, 4)), spread=(-12, -4, 5, 13), thumb=(-14, -4)),
 'point_soft': dict(curl=((0, 3, 2), (30, 42, 28), (36, 46, 32), (40, 50, 34)), spread=(-4, 0, 2, 4), thumb=(8, 14)),
}
def lerp(a, b, u): return a + (b - a) * u
def hand_pose(S, pa, pb_, u, sgn):
    A, Bp = HAND[pa], HAND[pb_]
    for i, F in enumerate(FINGERS):
        for N in (1, 2, 3):
            c = lerp(A['curl'][i][N - 1], Bp['curl'][i][N - 1], u)
            sp = lerp(A['spread'][i], Bp['spread'][i], u) if N == 1 else 0
            local_rot(bone('finger', S, F, N), x=c, z=sgn * sp)
    for N in (1, 2):
        local_rot(bone('thumb', S, N=N), x=lerp(A['thumb'][N - 1], Bp['thumb'][N - 1], u))

# ---------- base pose: front-facing stand ----------
# arms hang at the sides (v26 line-art numbers); hands rest on thighs, back of hand out
ARM_SIDE = dict(uaY=82, uaZ=-13, faX=-15, faZ=-5, hX=-6, hY=30, hZ=-3)
def base_pose():
    for pb_ in rig.pose.bones: pb_.matrix_basis = Matrix.Identity(4)
    upd()
    rots([(bone('pelvis'), [('Z', 1.0)])])
    ops_ua, ops_fa, ops_h = [], [], []
    for S in ('L', 'R'):
        sgn = 1 if S == 'L' else -1
        ops_ua.append((bone('upperarm', S), [('Y', sgn * ARM_SIDE['uaY']), ('Z', sgn * ARM_SIDE['uaZ'])]))
        ops_fa.append((bone('forearm', S), [('X', ARM_SIDE['faX']), ('Z', sgn * ARM_SIDE['faZ'])]))
        ops_h.append((bone('hand', S), [('X', ARM_SIDE['hX']), ('Y', ARM_SIDE['hY']), ('Z', sgn * ARM_SIDE['hZ'])]))
    rots(ops_ua); rots(ops_fa); rots(ops_h)
    for S in ('L', 'R'):
        sgn = 1 if S == 'L' else -1
        hand_pose(S, 'rest_thigh', 'rest_thigh', 0, sgn)
        bone('hand', S).scale = (HAND_SCALE,) * 3
    rots([(bone('spine'), [('X', -2)])])
    rots([(bone('chest'), [('X', -1)])])
    bone('head').scale = (HEAD_SCALE,) * 3
    upd()
base_pose()

# ---------- score ----------
DEMO = {"fps": 24, "segments": [
    {"t": [0.0, 2.8],   "text": "Hey, I'm Rain.", "intent": "wave", "mood": "smile", "energy": 0.9},
    {"t": [3.0, 7.2],   "text": "Today I'll show you how the presenter system works.",
     "intent": "explain", "mood": "neutral", "energy": 0.8},
    {"t": [7.4, 10.2],  "text": "Here's the thing, though.", "intent": "none", "mood": "neutral", "energy": 0.5},
    {"t": [10.5, 13.2], "text": "Gestures stay deliberate — never flailing.",
     "intent": "emphasis", "mood": "serious", "energy": 0.85},
    {"t": [13.4, 16.0], "text": "Want to see it in action?", "intent": "question", "mood": "smile", "energy": 0.7},
    {"t": [16.2, 20.8], "text": "It listens to the pacing, holds stillness between beats, and lets the face lead.",
     "intent": "none", "mood": "neutral", "energy": 0.5},
    {"t": [21.0, 23.4], "text": "Alright — let's go.", "intent": "ack", "mood": "smile", "energy": 0.8}]}
score = DEMO if SCORE in ('-', '') or not os.path.exists(SCORE) else json.load(open(SCORE))
SEGS = score['segments']; FPS = score.get('fps', 24)
T_END = SEGS[-1]['t'][1] + 0.4
F1 = int(nums[1]) if len(nums) > 1 else int(T_END * FPS)

# ---------- speech: syllable + viseme plan per segment ----------
VIS = {'A': (1.0, 0.0, 0.6), 'E': (0.55, 0.35, 0.5), 'O': (0.7, -0.35, 0.3),
       'M': (0.0, 0.0, 0.0), 'F': (0.35, -0.1, 0.9)}
def segment_syllables(seg, seed):
    """deterministic syllable stream filling the segment; stress on first + every ~1.2s."""
    t0, t1 = seg['t']; dur = t1 - t0
    n = max(3, round(len(seg.get('text', '')) / 4.4))
    n = min(n, int(dur / 0.11))
    rng = random.Random(seed)
    out = []; t = t0 + 0.12; last_stress = -9
    vp = ['A', 'E', 'O', 'A', 'M', 'F', 'E', 'O', 'A', 'E']
    for i in range(n):
        d = 0.09 + 0.05 * rng.random()
        stress = 1 if (i == 0 or t - last_stress > 1.15) else 0
        if stress: last_stress = t
        out.append((t, d, vp[(i + seed) % len(vp)] if i % 5 else 'A', stress))
        t += d + 0.015 + 0.05 * rng.random() + (0.12 if rng.random() < 0.12 else 0)
        if t > t1 - 0.1: break
    return out
SYL = []
for i, s in enumerate(SEGS):
    if s.get('intent') != 'listen':
        SYL += [(o, d, v, st, i) for (o, d, v, st) in segment_syllables(s, i * 7 + 1)]
def speaking_seg(t):
    for i, s in enumerate(SEGS):
        if s['t'][0] <= t <= s['t'][1] and s.get('intent') != 'listen':
            return i
    return None

def mouth_state(t):
    j = w = l = 0.0; wsum = 0.0
    for o, d, v, s, si in SYL:
        c = o + d * 0.45; sig = d * 0.55
        k = math.exp(-((t - c) / sig) ** 2)
        J, W, Lp = VIS[v]; amp = 0.75 + 0.35 * s
        j += k * J * amp; w += k * W; l += k * Lp; wsum += k
    if wsum < 1e-6: return 0.0, 0.0, 0.0
    return min(1, j / max(wsum, 0.8)), w / max(wsum, 0.8), min(1, l / max(wsum, 0.8))

# ---------- semantic director: intent -> scheduled gestures (VITA grammar) ----------
INTENT_MAP = {'wave': 'wave', 'explain': 'present', 'emphasis': 'emphasis',
              'question': 'question', 'ack': 'ack', 'think': 'think', 'none': None}
def auto_intent(seg):
    if 'intent' in seg: return seg['intent']
    tx = seg.get('text', '')
    if tx.strip().endswith('?'): return 'question'
    if tx.strip().endswith('!'): return 'emphasis'
    return 'explain' if seg.get('energy', 0.7) > 0.5 else 'none'

# gesture shape vectors: (ua Y,Z deltas, fa X,Z, hand X,Y,Z) + hand pose target + face adds
GESTV = {
 'present':  dict(ua=(34, -14), fa=(-52, 8),  h=(-10, -80, 0), hp='present', both=0.25),
 'emphasis': dict(ua=(26, -10), fa=(-44, 5),  h=(-8, -60, 0),  hp='present', both=0.0),
 'question': dict(ua=(30, -12), fa=(-50, 6),  h=(-6, -68, 0),  hp='open',    both=0.4),
 'ack':      dict(ua=(16, -6),  fa=(-26, 3),  h=(-4, -40, 0),  hp='relaxed', both=0.0),
 'wave':     dict(ua=(58, -18), fa=(-105, 2), h=(-8, -85, 0),  hp='open',    both=0.0),
}
if os.environ.get('GESTV'):
    GESTV.update(json.loads(os.environ['GESTV']))
if os.environ.get('FORCEG'):
    _fk, _fa = os.environ['FORCEG'].split(',')
    for i, s in enumerate(SEGS): s['intent'] = 'none'
MIN_GAP = 3.0; MAX_PER_10S = 2; AVOID_REPEAT_N = 3
def direct():
    cands = []
    for i, s in enumerate(SEGS):
        kind = INTENT_MAP.get(auto_intent(s))
        if not kind or kind == 'think': continue
        stress = [o for o, d, v, st, si in SYL if si == i and st]
        anchor = (stress[0] - 0.22) if stress else s['t'][0] + 0.4
        cands.append([anchor, kind, i, s.get('energy', 0.7)])
    sched = []; last_t = -9; kinds = []
    for c in cands:
        t0, kind, si, en = c
        if t0 - last_t < MIN_GAP:
            t0 = last_t + MIN_GAP  # slide, never closer
        if t0 > SEGS[si]['t'][1] - 0.5: continue
        # budget: max 2 in any 10s window
        if sum(1 for e in sched if e[0] > t0 - 10.0) >= MAX_PER_10S: continue
        if kind in kinds[-AVOID_REPEAT_N:]:
            kind = 'present' if kind != 'present' else 'emphasis'
        # hands subordinate to face: big mood change at segment start -> gesture waits
        if SEGS[si]['t'][0] > t0 - 0.5 and SEGS[si].get('mood', 'neutral') != 'neutral':
            t0 += 0.45
        side = ('L', 'R')[(len(sched) + si) % 2]
        dur = 0.95 + 0.55 * en
        sched.append((t0, kind, dur, side, si, en))
        last_t = t0; kinds.append(kind)
    return sched
GEST = direct()
if os.environ.get('FORCEG'):
    _fk, _fa = os.environ['FORCEG'].split(',')
    GEST = [(1.0, _fk, 4.0, _fa, 0, 0.9)]
print('GESTURES', [(round(g[0], 2), g[1], g[3]) for g in GEST])

def smooth(t): t = max(0, min(1, t)); return t * t * (3 - 2 * t)
def ease_out_back(t, s=1.4):
    t = max(0, min(1, t)); t -= 1
    return t * t * ((s + 1) * t + s) + 1
def bump(t, t0, dur):
    u = (t - t0) / dur
    return 0 if u < 0 or u > 1 else math.sin(math.pi * u)

def gesture(t):
    """active gesture -> (amp, kind, u, side, seg_i) or None; ant->stroke->hold->release."""
    best = (0.0, None, 0.0, None, 0)
    for t0, kind, dur, side, si, en in GEST:
        u = t - t0
        if u < 0 or u > dur: continue
        ant = 0.12; stroke = 0.30; rel = 0.42; hold = dur - ant - stroke - rel
        if hold < 0.05: continue
        if u < ant: a = -0.10 * math.sin(math.pi * u / ant)
        elif u < ant + stroke: a = ease_out_back((u - ant) / stroke, 1.2)
        elif u < ant + stroke + hold: a = 1.0 - 0.06 * (u - ant - stroke) / hold
        else: a = 0.94 * (1 - smooth((u - ant - stroke - hold) / rel))
        if abs(a) > abs(best[0]): best = (a, kind, u, side, si)
    return best

# ---------- idle: breathing, weight, gaze, blink ----------
rng_idle = random.Random(11)
BLINKS = [0.4]
while BLINKS[-1] < T_END + 2: BLINKS.append(BLINKS[-1] + 2.6 + rng_idle.random() * 2.2)
SACCADES = [1.2]
while SACCADES[-1] < T_END + 2: SACCADES.append(SACCADES[-1] + 1.8 + rng_idle.random() * 2.6)

def blink(t):
    b = 0.0
    for tb in BLINKS:
        u = t - tb
        if 0 <= u < 0.07: b = max(b, smooth(u / 0.07))
        elif 0.07 <= u < 0.20: b = max(b, 1 - smooth((u - 0.07) / 0.13))
    return b

def gaze(t):
    """eyes on camera; brief seeded glances off and back."""
    x = 0.0; z = -0.03
    for i, ts in enumerate(SACCADES):
        dx = (0.28 if i % 2 else -0.28) * (1 if i % 3 else 0.5)
        k = bump(t, ts, 0.5)
        x += dx * k; z += (0.12 if i % 4 == 1 else -0.06) * k
    return x, z

MOOD = {'neutral': dict(corner=0.12, brow=0.0, lid=0.0),
        'smile':   dict(corner=0.75, brow=0.15, lid=0.0),
        'serious': dict(corner=0.02, brow=-0.25, lid=0.15)}
def face_base(t):
    """mood of the active segment, eased 0.5s in from the previous segment's."""
    mi = 0
    for i, s in enumerate(SEGS):
        if s['t'][0] - 0.35 <= t: mi = i
    m = MOOD[SEGS[mi].get('mood', 'neutral')]
    d = t - (SEGS[mi]['t'][0] - 0.35)
    if 0 <= d < 0.5 and mi > 0:
        pm = MOOD[SEGS[mi - 1].get('mood', 'neutral')]
        u = smooth(d / 0.5)
        return {k: lerp(pm[k], m[k], u) for k in m}
    return m

def head_state(t):
    si = speaking_seg(t)
    yaw = 1.6 * math.sin(t * 0.55)
    pitch = 1.2 * math.sin(t * 0.9)
    roll = 1.0 * math.sin(t * 0.42)
    if si is not None:
        for o, d, v, s, sii in SYL:
            if sii == si and s: pitch += 4.0 * bump(t, o - 0.06, 0.4)
        if SEGS[si].get('intent') == 'question' or auto_intent(SEGS[si]) == 'question':
            roll += 3.5 * smooth(min(1, (t - SEGS[si]['t'][0]) / 0.8))
            pitch -= 1.5
        if SEGS[si].get('intent') == 'think':
            yaw += 10 * bump(t, SEGS[si]['t'][0] + 0.4, 1.4); pitch -= 2 * bump(t, SEGS[si]['t'][0] + 0.4, 1.4)
    # acknowledge gestures also nod the head
    for t0, kind, dur, side, sii, en in GEST:
        if kind in ('ack', 'wave'):
            pitch += 5 * bump(t, t0 + 0.05, 0.5)
        if kind == 'question':
            roll += 2.5 * bump(t, t0 + 0.1, dur - 0.3)
    return yaw, pitch, roll

def brows(t):
    up = face_base(t)['brow']
    si = speaking_seg(t)
    if si is not None:
        for o, d, v, s, sii in SYL:
            if sii == si and s: up += 0.5 * bump(t, o - 0.10, 0.45)
    for t0, kind, dur, side, sii, en in GEST:
        if kind == 'question': up += 0.45 * bump(t, t0 + 0.05, dur - 0.3)
    return max(-0.4, min(1, up))

def breathe(t): return 0.45 * math.sin(t * 1.85)

# ---------- per-frame apply ----------
def apply(t):
    base_pose()
    yaw, pitch, roll = head_state(t)
    fb = face_base(t)
    rots([(bone('pelvis'), [('X', 0.4 * math.sin(t * 0.31))])])
    rots([(bone('chest'), [('X', breathe(t)), ('Z', 0.7 * math.sin(t * 0.23))])])
    rots([(bone('neck'), [('Z', yaw * 0.3), ('X', pitch * 0.3)])])
    rots([(bone('head'), [('Z', yaw * 0.7), ('X', pitch * 0.7), ('Y', roll)])])
    # face
    jaw, width, lip = mouth_state(t)
    b = blink(t); gx, gz = gaze(t); br = brows(t)
    for S in ('L', 'R'):
        local_loc(fbone('lid_upper', S), y=FC['lid_close'] * (b + fb['lid'] * 0.6))
        local_loc(fbone('brow', S), y=FC['brow_up'] * br)
        local_loc(fbone('corner', S), y=FC['corner_up'] * (fb['corner'] + 0.25 * max(0, width)))
    local_loc(fbone('eyes'), x=FC['gaze'] * gx, z=FC['gaze'] * gz)
    m = fbone('mouth'); m.scale = (1 + 0.22 * width, 1, 1)
    local_loc(fbone('lip_bot'), y=-FC['lip_open'] * lip)
    local_loc(fbone('lip_top'), y=FC['lip_open'] * 0.35 * jaw)
    j = bone('jaw'); local_rot(j, x=FC['jaw_sign'] * FC['jaw_deg'] * jaw)
    # gesture: torso leads, upper arm +2f, forearm +4f, wrist +6f (24fps flow lag)
    a, kind, u, side, gsi = gesture(t)
    if kind:
        G = GESTV[kind]
        # 'both' = probability the gesture runs two-handed (seeded per event)
        two_handed = kind != 'wave' and G['both'] > 0 and \
            random.Random((gsi + 1) * 31 + (1 if side == 'L' else 2)).random() < G['both']
        sides = ('L', 'R') if two_handed else (side,)
        for S in sides:
            sgn = 1 if S == 'L' else -1
            amp = a * (0.6 if S != side else 1.0)
            # flow lag per chain link: upper arm -> forearm +4f -> wrist +7f
            lag_f = max(0, min(1, (u - 0.10) / 0.34)); lag_w = max(0, min(1, (u - 0.17) / 0.34))
            af = amp * (0.5 + 0.5 * lag_f); aw = amp * (0.4 + 0.6 * lag_w)
            rots([(bone('upperarm', S), [('Z', sgn * G['ua'][0] * amp), ('Y', sgn * G['ua'][1] * amp)])])
            fX = G['fa'][0] * af
            if kind == 'emphasis':  # small beat down at stroke end
                fX += -14 * amp * bump(u, 0.42, 0.22)
            rots([(bone('forearm', S), [('X', fX), ('Z', sgn * G['fa'][1] * af)])])
            hw = [ ('Y', sgn * G['h'][1] * aw), ('X', G['h'][0] * aw), ('Z', sgn * G['h'][2] * aw)]
            if kind == 'wave' and u > 0.42:
                hw[2] = ('Z', sgn * (G['h'][2] * aw + 16 * math.sin(2 * math.pi * 2.6 * (u - 0.42)) * amp))
            brots(bone('hand', S), hw)
            hand_pose(S, 'relaxed', G['hp'], max(0, min(1, aw / 0.9)), sgn)
        # hand safety: keep the gesturing hand below the chin / out of the face zone
        hw_pos = rig.matrix_world @ bone('hand', side).matrix.translation
        chin_z = (rig.matrix_world @ bone('jaw').matrix.translation).z
        if hw_pos.z > chin_z - 0.10:
            rots([(bone('forearm', side), [('X', -(hw_pos.z - (chin_z - 0.10)) * 220)])])
        upd()
    upd()

# ---------- line art ----------
gd = bpy.data.grease_pencils.new('LineArt'); gp = bpy.data.objects.new('LineArt', gd)
scene.collection.objects.link(gp)
gd.layers.new('Lines'); lm = bpy.data.materials.new('LineInk')
bpy.data.materials.create_gpencil_data(lm); gd.materials.append(lm)
lm.grease_pencil.color = INKC
mod = gp.modifiers.new('LineArt', 'LINEART'); mod.source_type = 'SCENE'
mod.target_layer = 'Lines'; mod.target_material = lm
mod.use_crease = True; mod.crease_threshold = math.radians(130)
mod.use_intersection = True; mod.use_material = True; mod.use_edge_overlap = True
for a in ('thickness', 'line_thickness'):
    if hasattr(mod, a): setattr(mod, a, 5)

# ---------- camera ----------
cd = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cd)
scene.collection.objects.link(cam); scene.camera = cam
head_w = rig.matrix_world @ bone('head').matrix.translation
SPAN = {'closeup': 0.45, 'bust': 0.65, 'waist': 1.05}[FRAME]
zc = head_w.z - {'closeup': 0.06, 'bust': 0.16, 'waist': 0.32}[FRAME]
cd.lens = 58; cd.sensor_fit = 'VERTICAL'
dist = (SPAN / 2) / math.tan(cd.angle / 2)
cam.location = (0, -dist, zc); cam.rotation_euler = (math.radians(89.5), 0, 0)
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1280; scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGBA'
scene.view_settings.view_transform = 'Standard'; scene.view_settings.look = 'None'
scene.frame_set(F0); scene.render.fps = FPS
if hasattr(scene, 'eevee'): scene.eevee.taa_render_samples = 4

os.makedirs(OUT, exist_ok=True)
for f in range(F0, F1 + 1):
    t = f / FPS
    t0 = time.time(); apply(t); tp = time.time() - t0
    scene.render.filepath = os.path.join(OUT, 'rain_%04d.png' % f)
    t0 = time.time(); bpy.ops.render.render(write_still=True)
    print('FRAME', f, 'pose %.1fs render %.1fs' % (tp, time.time() - t0), flush=True)
    if STILL: break
print('DONE')
