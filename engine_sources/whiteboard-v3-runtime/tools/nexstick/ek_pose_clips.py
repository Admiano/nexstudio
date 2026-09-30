#!/usr/bin/env python3
"""Exercise-motion vault builder.

Everkinetic/workout-guide (github.com/bryllim/workout-guide, upstream
github.com/everkinetic/data) catalogs 302 exercises, each with canonical
start/mid/end pose illustrations — licensed CC BY-SA 4.0 (commercial use
allowed with attribution + share-alike). MediaPipe cannot keypoint the
stylized art, so the canonical poses are authored here as joint-angle
keyposes, forward-kinematics'd into our 22-joint vault skeleton, and
interpolated into looping rep cycles.

Output: compiled/exercise_vault_v5.json — same vault contract as
cmu_motion_vault_v5.json, merged in cmu_sampler at load time.

Angles: degrees. pitch is rotation in the sagittal plane, + toward +z
(character faces +z). Limb pitch 0 = straight down; spine pitch 0 = straight
up. swing abducts toward ±x. Feet/ankles land near y=0 when standing.
"""
import json, math, sys, os

# MUST match cmu_motion_vault_v5.json's joints order exactly — the sampler
# zips frame rows by the merged vault's joint list; a different order
# crosses left/right joints and the skeleton comes apart.
JOINTS = ['root', 'pelvis', 'spine', 'chest', 'neck', 'head',
          'clavicle_l', 'shoulder_l', 'elbow_l', 'wrist_l',
          'clavicle_r', 'shoulder_r', 'elbow_r', 'wrist_r',
          'hip_l', 'knee_l', 'ankle_l', 'toe_l',
          'hip_r', 'knee_r', 'ankle_r', 'toe_r']

# adult-average skeleton, meters, y-up (matches vault pelvis height)
L = dict(thigh=0.42, shin=0.43, spine=0.15, chest=0.16, neck=0.10,
         head=0.24, uarm=0.28, farm=0.27, hip_w=0.095, sh_w=0.19,
         ankle_h=0.075, toe=0.17)

def d(p, s, up):
    """bone direction from pitch (deg from vertical) + frontal swing."""
    p, s = math.radians(p), math.radians(s)
    y = math.cos(p) * math.cos(s)
    z = math.sin(p) * math.cos(s)
    x = math.sin(s)
    return [x, y if up else -y, z]

def add(a, b, k=1.0):
    return [a[0] + b[0] * k, a[1] + b[1] * k, a[2] + b[2] * k]

def fk(spec):
    """spec -> {joint: [x,y,z]}. Keys: pelvis=[x,y,z], torso_pitch,
    head_pitch, leg(l|r)=(thigh_pitch, shin_pitch, swing), foot_pitch,
    arm(l|r)=(uarm_pitch, farm_pitch, swing)."""
    p = dict(pelvis=[0, 0.877, 0], torso_pitch=0, head_pitch=None,
             legL=(0, 0, 0), legR=(0, 0, 0), foot_pitch=0,
             armL=(0, 0, 0), armR=(0, 0, 0), sh_swing=0)
    p.update(spec)
    j = {}
    j['root'] = [0, 0, 0]
    j['pelvis'] = list(p['pelvis'])
    # The back curves: a real bend distributes along the column — the
    # lumbar end stays planted, the bend accumulates toward the neck.
    # One rigid rod for the whole torso is what reads as a hinge.
    tp = p['torso_pitch']
    j['spine'] = add(j['pelvis'], d(tp * 0.42, 0, up=True), L['spine'])
    j['chest'] = add(j['spine'], d(tp * 0.74, 0, up=True), L['chest'])
    j['neck'] = add(j['chest'], d(tp, 0, up=True), L['neck'])
    hd = d(p['head_pitch'] if p['head_pitch'] is not None
           else tp, 0, up=True)
    j['head'] = add(j['neck'], hd, L['head'])
    for s, sgn in (('l', -1), ('r', 1)):
        j[f'clavicle_{s}'] = add(j['chest'], [sgn * 0.09, 0.02, 0])
        j[f'shoulder_{s}'] = add(j['clavicle_' + s], [sgn * 0.10, -0.02, 0])
        a3 = tuple(p['arm' + s.upper()]) + (0, 0, 0)
        ua, fa, sw = a3[0], a3[1], a3[2]
        ad = d(ua, sgn * sw, up=False)
        j[f'elbow_{s}'] = add(j[f'shoulder_{s}'], ad, L['uarm'])
        fd = d(fa, sgn * sw, up=False)
        j[f'wrist_{s}'] = add(j[f'elbow_{s}'], fd, L['farm'])
        l3 = tuple(p['leg' + s.upper()]) + (0, 0, 0)
        th, sh, lw = l3[0], l3[1], l3[2]
        j[f'hip_{s}'] = add(j['pelvis'], [sgn * L['hip_w'], -0.02, 0])
        thd = d(th, sgn * lw, up=False)
        j[f'knee_{s}'] = add(j[f'hip_{s}'], thd, L['thigh'])
        shd = d(sh, sgn * lw, up=False)
        j[f'ankle_{s}'] = add(j[f'knee_{s}'], shd, L['shin'])
        j[f'toe_{s}'] = add(j[f'ankle_{s}'],
                            [0, -0.03, 0.16] if p['foot_pitch'] == 0
                            else d(p['foot_pitch'], 0, up=False), 1 if p['foot_pitch'] else 1)
        if p['foot_pitch'] != 0:
            j[f'toe_{s}'] = add(j[f'ankle_{s}'], d(p['foot_pitch'], 0, up=False), L['toe'] * 0.85)
    return j

def pose(**kw):
    return kw

# ---- canonical exercise keyposes (authored against Everkinetic frames) ----
# conventions: standing upright = pelvis [0,0.877,0], torso_pitch 0,
# limbs straight down. Forward = +z.
K = {
    # ---- standing family (upright, feet planted ~z 0) ----
    'EX_SQUAT': [  # stand -> hips-back parallel squat (arms counterbalance fwd)
        dict(pelvis=[0, 0.877, 0], legL=(4, 4), legR=(4, 4),
             armL=(5, 5), armR=(5, 5)),
        dict(pelvis=[0, 0.60, -0.24], torso_pitch=32, legL=(52, 16),
             legR=(52, 16), armL=(80, 80), armR=(80, 80), head_pitch=18),
    ],
    'EX_DEADLIFT': [  # hinged grip -> lockout
        dict(pelvis=[0, 0.64, -0.18], torso_pitch=55, legL=(32, 6),
             legR=(32, 6), armL=(22, 24), armR=(22, 24), head_pitch=45),
        dict(pelvis=[0, 0.877, 0], torso_pitch=0, legL=(2, 2), legR=(2, 2),
             armL=(6, 6), armR=(6, 6), head_pitch=0),
    ],
    'EX_LUNGE': [  # split stance drop (front knee ~90, back knee down)
        dict(pelvis=[0, 0.86, 0], legL=(35, 8), legR=(-30, -45),
             armL=(8, 8), armR=(8, 8), torso_pitch=4),
        dict(pelvis=[0, 0.62, 0.06], legL=(68, 22), legR=(-38, -85),
             armL=(8, 8), armR=(8, 8), torso_pitch=6),
    ],
    'EX_JUMPING_JACK': [  # closed -> star (jump)
        dict(pelvis=[0, 0.877, 0], torso_pitch=0, legL=(2, 2), legR=(2, 2),
             armL=(2, 2), armR=(2, 2)),
        dict(pelvis=[0, 0.93, 0], torso_pitch=0, legL=(4, 4, 22),
             legR=(4, 4, 22), armL=(8, 8, 135), armR=(8, 8, 135),
             head_pitch=-6),
    ],
    'EX_OVERHEAD_PRESS': [  # rack (forearms up) -> lockout (arms up)
        dict(pelvis=[0, 0.877, 0], torso_pitch=0, legL=(3, 3), legR=(3, 3),
             armL=(62, 170), armR=(62, 170), head_pitch=0),
        dict(pelvis=[0, 0.89, 0], torso_pitch=0, legL=(3, 3), legR=(3, 3),
             armL=(172, 178), armR=(172, 178), head_pitch=-6),
    ],
    'EX_KETTLEBELL_SWING': [  # hinge (bell between knees) -> float
        dict(pelvis=[0, 0.66, -0.14], torso_pitch=48, legL=(36, 8),
             legR=(36, 8), armL=(34, 36), armR=(34, 36), head_pitch=42),
        dict(pelvis=[0, 0.877, 0], torso_pitch=-6, legL=(3, 3), legR=(3, 3),
             armL=(72, 72), armR=(72, 72), head_pitch=-8),
    ],
    'EX_BICEP_CURL': [  # arms hang -> forearms curl up
        dict(pelvis=[0, 0.877, 0], torso_pitch=0, legL=(3, 3), legR=(3, 3),
             armL=(6, 8), armR=(6, 8)),
        dict(pelvis=[0, 0.877, 0], torso_pitch=0, legL=(3, 3), legR=(3, 3),
             armL=(8, 130), armR=(8, 130)),
    ],
    # ---- prone family (face-down, head +z; legs extend -z) ----
    'EX_PUSH_UP': [  # top plank -> chest low (straight body line)
        dict(pelvis=[0, 0.52, 0.30], torso_pitch=62, legL=(-58, -60),
             legR=(-58, -60), armL=(16, 18), armR=(16, 18),
             head_pitch=60, foot_pitch=135),
        dict(pelvis=[0, 0.36, 0.30], torso_pitch=66, legL=(-56, -58),
             legR=(-56, -58), armL=(14, 88), armR=(14, 88),
             head_pitch=60, foot_pitch=135),
    ],
    'EX_PLANK': [  # forearm plank hold (forearms flat forward)
        dict(pelvis=[0, 0.44, 0.30], torso_pitch=64, legL=(-60, -62),
             legR=(-60, -62), armL=(18, 82), armR=(18, 82),
             head_pitch=55, foot_pitch=135),
        dict(pelvis=[0, 0.43, 0.30], torso_pitch=64, legL=(-60, -62),
             legR=(-60, -62), armL=(18, 82), armR=(18, 82),
             head_pitch=55, foot_pitch=135),
    ],
    'EX_MOUNTAIN_CLIMBER': [  # plank + alternating knee drive under chest
        dict(pelvis=[0, 0.52, 0.30], torso_pitch=62, legL=(35, -35),
             legR=(-58, -60), armL=(16, 18), armR=(16, 18),
             head_pitch=60, foot_pitch=135),
        dict(pelvis=[0, 0.52, 0.30], torso_pitch=62, legL=(-58, -60),
             legR=(35, -35), armL=(16, 18), armR=(16, 18),
             head_pitch=60, foot_pitch=135),
    ],
    'EX_BEAR_CRAWL': [  # quadruped, contralateral step
        dict(pelvis=[0, 0.55, 0.10], torso_pitch=76, legL=(50, -55),
             legR=(72, -70), armL=(15, 18), armR=(45, 40),
             head_pitch=55, foot_pitch=120),
        dict(pelvis=[0, 0.55, 0.14], torso_pitch=76, legL=(72, -70),
             legR=(50, -55), armL=(45, 40), armR=(15, 18),
             head_pitch=55, foot_pitch=120),
    ],
    'EX_DOWNWARD_DOG': [  # inverted-V hold: hips high, hands+feet planted
        dict(pelvis=[0, 0.88, 0.10], torso_pitch=105, legL=(-42, -44),
             legR=(-42, -44), armL=(32, 34), armR=(32, 34),
             head_pitch=100, foot_pitch=110),
        dict(pelvis=[0, 0.90, 0.10], torso_pitch=105, legL=(-42, -44),
             legR=(-42, -44), armL=(32, 34), armR=(32, 34),
             head_pitch=100, foot_pitch=110),
    ],
    'EX_BURPEE': [  # stand -> plank -> squat-tuck -> stand
        dict(pelvis=[0, 0.877, 0], torso_pitch=0, legL=(3, 3), legR=(3, 3),
             armL=(4, 4), armR=(4, 4)),
        dict(pelvis=[0, 0.52, 0.30], torso_pitch=62, legL=(-58, -60),
             legR=(-58, -60), armL=(16, 18), armR=(16, 18),
             head_pitch=60, foot_pitch=135),
        dict(pelvis=[0, 0.52, -0.10], torso_pitch=38, legL=(62, 25),
             legR=(62, 25), armL=(60, 90), armR=(60, 90), head_pitch=25),
    ],
    # ---- supine family (face-up, head -z; legs bent, feet planted +z) ----
    'EX_SIT_UP': [  # flat -> crunch to knees
        dict(pelvis=[0, 0.12, 0.25], torso_pitch=-84, legL=(42, -30),
             legR=(42, -30), armL=(-160, -165), armR=(-160, -165),
             head_pitch=-80, foot_pitch=15),
        dict(pelvis=[0, 0.30, 0.25], torso_pitch=-28, legL=(42, -30),
             legR=(42, -30), armL=(80, 78), armR=(80, 78),
             head_pitch=-22, foot_pitch=15),
    ],
    'EX_GLUTE_BRIDGE': [  # flat -> hips driven up
        dict(pelvis=[0, 0.12, 0.25], torso_pitch=-84, legL=(42, -30),
             legR=(42, -30), armL=(-165, -170), armR=(-165, -170),
             head_pitch=-84, foot_pitch=15),
        dict(pelvis=[0, 0.44, 0.25], torso_pitch=-52, legL=(35, -25),
             legR=(35, -25), armL=(-165, -170), armR=(-165, -170),
             head_pitch=-70, foot_pitch=15),
    ],
    # ---- hanging / support family ----
    'EX_PULL_UP': [  # dead hang (feet dangle) -> chin over bar
        dict(pelvis=[0, 1.02, 0], torso_pitch=-4, legL=(-8, -10),
             legR=(-8, -10), armL=(-172, -176), armR=(-172, -176),
             head_pitch=-8),
        dict(pelvis=[0, 1.32, 0], torso_pitch=-8, legL=(-14, -14),
             legR=(-14, -14), armL=(-165, -75), armR=(-165, -75),
             head_pitch=-15),
    ],
    'EX_DIP': [  # support (arms straight at sides, knees bent) -> low
        dict(pelvis=[0, 0.95, 0], torso_pitch=4, legL=(28, 58),
             legR=(28, 58), armL=(-8, -6), armR=(-8, -6), head_pitch=0),
        dict(pelvis=[0, 0.74, 0], torso_pitch=10, legL=(34, 68),
             legR=(34, 68), armL=(-12, 58), armR=(-12, 58), head_pitch=6),
    ],
    'EX_BIRD_DOG': [  # quadruped -> opposite arm+leg extended
        dict(pelvis=[0, 0.52, 0.10], torso_pitch=80, legL=(58, -60),
             legR=(58, -60), armL=(22, 24), armR=(22, 24),
             head_pitch=55, foot_pitch=120),
        dict(pelvis=[0, 0.52, 0.10], torso_pitch=80, legL=(58, -60),
             legR=(-168, -170), armL=(22, 24), armR=(-170, -172),
             head_pitch=55, foot_pitch=120),
    ],
}

# ballistic clips overshoot their end pose instead of easing dead to it
BALLISTIC = {'EX_KETTLEBELL_SWING', 'EX_BURPEE', 'EX_JUMPING_JACK',
             'EX_SIT_UP', 'EX_MOUNTAIN_CLIMBER'}

def build():
    clips = {}
    fps = 30
    for name, keys in K.items():
        seg_t = 0.55  # per keyframe transition
        n_keys = len(keys)
        cyc = 2 * (n_keys - 1) * seg_t   # out-and-back rep
        n_reps = 2                     # two visibly-different reps per clip
        dur = cyc * n_reps
        n = max(8, int(dur * fps))
        frames = []
        times = []
        for i in range(n + 1):
            t = i / fps
            rep = int(t / cyc)
            # humans never hit the same rep twice: deterministic per-rep
            # amplitude/tempo wobble, seeded by clip name + rep index
            seed = sum(ord(c) for c in name) + rep * 37
            amp = 1 + 0.045 * math.sin(seed * 1.71)
            tempo = 1 + 0.05 * math.sin(seed * 0.97)
            tt = t * tempo
            # ping-pong through keyposes for a rep cycle
            pos = (tt / seg_t) % (2 * (n_keys - 1))
            if pos > n_keys - 1:
                pos = 2 * (n_keys - 1) - pos
            i0 = int(pos)
            i1 = min(i0 + 1, n_keys - 1)
            w = pos - i0
            # ease at keyframe ends; ballistic moves carry momentum
            # through the extended pose (slight overshoot, snaps back)
            w = w * w * (3 - 2 * w)
            if name in BALLISTIC:
                w += 0.09 * math.sin(math.pi * w)
            w *= amp
            A = fk(keys[i0])
            B = fk(keys[i1])
            fr = []
            for jn in JOINTS:
                a, b = A[jn], B[jn]
                fr.append([round(a[0] + (b[0] - a[0]) * w, 4),
                           round(a[1] + (b[1] - a[1]) * w, 4),
                           round(a[2] + (b[2] - a[2]) * w, 4)])
            frames.append(fr)
            times.append(round(t, 4))
        clips[name] = dict(
            duration=round(dur, 4), fps=fps, loop=True, reps=n_reps,
            source='nexstudio:ek-canonical-poses (Everkinetic keypose study)',
            license='CC BY-SA 4.0 — Bryl Lim / Everkinetic (pose reference)',
            semantic=name.lower(), tags=['exercise', 'canonical', 'keypose'],
            times=times, frames=frames, rootDelta=[0, 0, 0],
            contacts={'l': [], 'r': []}, features={})
    return {'version': '5.0.0-exercise-poses',
            'source': 'bryllim/workout-guide + everkinetic/data (CC BY-SA 4.0)',
            'fps': fps, 'joints': JOINTS, 'clips': clips}

if __name__ == '__main__':
    out = build()
    dst = sys.argv[1] if len(sys.argv) > 1 else 'compiled/exercise_vault_v5.json'
    json.dump(out, open(dst, 'w'))
    print('wrote', len(out['clips']), 'exercise clips ->', dst)
