#!/usr/bin/env python3
"""CMU-format BVH -> nexstick V5 vault clip converter.

CMU Graphics Lab mocap is the one large corpus licensed for ALL uses
(including commercial): 'free for all uses', BVH conversion by B. Hahne
(cgspeed). 2548 clips, 144 subjects, 120fps, inches, Y-up, +Z forward.

Output: nexstick vault-format clip dicts —
  {duration, fps, loop, source, license, semantic, tags,
   times[], frames[[22 x xyz]], rootDelta, contacts{l,r}, features}

22-joint order (vault standard):
  root pelvis spine chest neck head
  clavicle_l shoulder_l elbow_l wrist_l
  clavicle_r shoulder_r elbow_r wrist_r
  hip_l knee_l ankle_l toe_l hip_r knee_r ankle_r toe_r
"""
import sys, json, math, re

INCH_M = 0.0254
OUT_FPS = 30.0
# UAL2 vault reference pelvis height (m). The cgspeed CMU rig is an
# underscaled actor (~16" pelvis); scale every converted clip so its pelvis
# sits at the vault's standard height — keeps the retargeted figure identical
# in size to the existing donors.
TARGET_PELVIS_H = 0.877

# ---- BVH parse ----

class Node:
    __slots__ = ('name', 'offset', 'channels', 'children', 'parent', 'is_end')
    def __init__(self, name, offset, parent):
        self.name, self.offset, self.parent = name, offset, parent
        self.channels, self.children, self.is_end = [], [], False

def parse_bvh(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    i = 0
    assert lines[i].startswith('HIERARCHY'); i += 1
    stack = []
    root = None
    chan_order = []
    def read_block(name, parent, i):
        node = Node(name, (0, 0, 0), parent)
        assert lines[i] == '{'; i += 1
        while True:
            l = lines[i]
            if l.startswith('OFFSET'):
                node.offset = tuple(float(x) for x in l.split()[1:4])
            elif l.startswith('CHANNELS'):
                parts = l.split()
                node.channels = parts[2:2 + int(parts[1])]
            elif l.startswith('JOINT'):
                child_name = l.split()[1]
                child, i2 = read_block(child_name, node, i + 1)
                node.children.append(child)
                i = i2
                continue
            elif l.startswith('End Site'):
                end = Node(name + '_end', (0, 0, 0), node)
                end.is_end = True
                assert lines[i + 1] == '{'
                off = lines[i + 2]
                end.offset = tuple(float(x) for x in off.split()[1:4])
                assert lines[i + 3] == '}'
                node.children.append(end)
                i += 4
                continue
            elif l == '}':
                return node, i + 1
            i += 1
    assert lines[i].startswith('ROOT')
    root, i = read_block(lines[i].split()[1], None, i + 1)
    assert lines[i].startswith('MOTION'); i += 1
    nframes = int(lines[i].split()[1]); i += 1
    ftime = float(lines[i].split()[2]); i += 1
    motion = [[float(x) for x in lines[i + k].split()] for k in range(nframes)]
    # channel column map
    cols = {}
    c = 0
    def walk(n):
        nonlocal c
        for ch in n.channels:
            cols[(n.name, ch)] = c; c += 1
        for ch in n.children:
            walk(ch)
    walk(root)
    return root, cols, motion, ftime

# ---- FK ----

def rot(axis, deg):
    r = math.radians(deg); c, s = math.cos(r), math.sin(r)
    if axis == 'Xrotation': return ((1, 0, 0), (0, c, -s), (0, s, c))
    if axis == 'Yrotation': return ((c, 0, s), (0, 1, 0), (-s, 0, c))
    return ((c, -s, 0), (s, c, 0), (0, 0, 1))

def mmul(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))

def mv(m, v):
    return (m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
            m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
            m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2])

def fk_positions(node, vals, cols, parent_rot, parent_pos, out, rots=None):
    pos = tuple(parent_pos[k] + mv(parent_rot, node.offset)[k] for k in range(3))
    rotm = parent_rot
    for ch in node.channels:
        if 'position' in ch:
            ax = 'XYZ'.index(ch[0])
            pos = tuple(pos[k] + mv(rotm, (vals[cols[(node.name, ch)]], 0, 0) if ax == 0 else
                                      (0, vals[cols[(node.name, ch)]], 0) if ax == 1 else
                                      (0, 0, vals[cols[(node.name, ch)]]))[k] for k in range(3))
        else:
            rotm = mmul(rotm, rot(ch, vals[cols[(node.name, ch)]]))
    out[node.name] = pos
    if rots is not None:
        rots[node.name] = rotm
    for ch in node.children:
        fk_positions(ch, vals, cols, rotm, pos, out, rots)

# ---- map CMU -> 22 joints ----

# CMU cgspeed skeleton: Hips> {LHipJoint>LeftUpLeg>LeftLeg>LeftFoot>LeftToeBase,
# RHipJoint>..., LowerBack>Spine>Spine1>{Neck>Neck1>Head, LeftShoulder>LeftArm>
# LeftForeArm>LeftHand, RightShoulder>...}}
def map_frame(pos):
    # clavicle approximations: point 2/3 from chest(Spine1) to arm joint
    def clav(side):
        arm = pos[side + 'Arm']; chest = pos['Spine1']
        return [chest[k] + (arm[k] - chest[k]) * 0.62 for k in range(3)]
    hips = pos['Hips']
    return [
        [0.0, 0.0, 0.0],                                   # root (local frame)
        list(hips),                                        # pelvis
        list(pos['Spine']),                                # spine
        list(pos['Spine1']),                               # chest
        list(pos.get('Neck1', pos['Neck'])),               # neck
        list(pos['Head']),                                 # head
        clav('Left'), list(pos['LeftArm']), list(pos['LeftForeArm']), list(pos['LeftHand']),
        clav('Right'), list(pos['RightArm']), list(pos['RightForeArm']), list(pos['RightHand']),
        list(pos['LeftUpLeg']), list(pos['LeftLeg']), list(pos['LeftFoot']), list(pos['LeftToeBase']),
        list(pos['RightUpLeg']), list(pos['RightLeg']), list(pos['RightFoot']), list(pos['RightToeBase']),
    ]

def contacts_for(frames, times):
    """Foot-plant segments: ankle low and nearly still for >= 0.12s."""
    out = {}
    for side, ai, ti in (('l', 16, 17), ('r', 20, 21)):
        segs = []
        open_start = None
        heights = [min(f[ai][1], f[ti][1]) for f in frames]
        lo = min(heights); hi_thresh = lo + 0.09
        for i, f in enumerate(frames):
            low = min(f[ai][1], f[ti][1]) < hi_thresh
            if low and i + 1 < len(frames):
                v = math.dist(frames[i + 1][ai], f[ai]) / max(1e-6, times[i + 1] - times[i])
                low = v < 0.35
            if low and open_start is None:
                open_start = i
            if not low and open_start is not None:
                if times[i] - times[open_start] >= 0.12:
                    j = (open_start + i) // 2
                    segs.append({'start': round(times[open_start], 4), 'end': round(times[i], 4),
                                 'anchor': [round(frames[j][ti][0], 4), 0.0, round(frames[j][ti][2], 4)]})
                open_start = None
        if open_start is not None and times[-1] - times[open_start] >= 0.12:
            j = (open_start + len(times) - 1) // 2
            segs.append({'start': round(times[open_start], 4), 'end': round(times[-1], 4),
                         'anchor': [round(frames[j][ti][0], 4), 0.0, round(frames[j][ti][2], 4)]})
        out[side] = segs
    return out

def convert(path, name, semantic, tags, scale=INCH_M, fps_in=120.0):
    text = open(path).read()
    root, cols, motion, ftime = parse_bvh(text)
    fps = 1.0 / ftime
    step = max(1, round(fps / OUT_FPS))
    ident = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    # first-frame pelvis height calibrates the actor's unit scale
    p0pos = {}
    fk_positions(root, motion[0], cols, ident, (0, 0, 0), p0pos)
    norm = TARGET_PELVIS_H / max(1e-6, p0pos['Hips'][1] * scale)
    frames, times, roty = [], [], []
    pos0 = None
    for i in range(0, len(motion), step):
        pos = {}
        rots = {}
        fk_positions(root, motion[i], cols, ident, (0, 0, 0), pos, rots)
        rh = rots.get('Head')
        # head joint's world azimuth (deg) — positions alone can't see head yaw
        roty.append(round(math.degrees(math.atan2(rh[0][2], rh[2][2])), 3) if rh else 0.0)
        fr = map_frame(pos)
        if pos0 is None:
            pos0 = [fr[1][0], 0.0, fr[1][2]]
        # local-frame: keep pelvis XZ travel but re-origin to first frame
        for j in range(1, 22):
            fr[j] = [(fr[j][0] - pos0[0]) * scale * norm, fr[j][1] * scale * norm, (fr[j][2] - pos0[2]) * scale * norm]
        fr[0] = [0.0, 0.0, 0.0]
        frames.append([[round(v, 6) for v in jt] for jt in fr])
        times.append(round(i / fps, 6))
    dur = round((len(motion) - 1) / fps, 6)
    # root delta for loop offsets (pelvis XZ drift over the clip)
    delta = [round(frames[-1][1][k] - frames[0][1][k], 6) for k in range(3)]
    delta[1] = 0.0
    return {
        'duration': min(dur, round(times[-1], 6) or dur), 'fps': OUT_FPS, 'loop': False,
        'source': 'cmu-mocap', 'license': 'CMU-free-all-uses',
        'semantic': semantic, 'tags': tags,
        'times': times, 'frames': frames, 'roty': roty,
        'rootDelta': delta, 'contacts': contacts_for(frames, times), 'features': [],
    }

if __name__ == '__main__':
    # usage: bvh_to_vault.py spec.json out.json   spec: [{file,name,semantic,tags}]
    spec = json.load(open(sys.argv[1]))
    clips = {}
    for s in spec:
        clips[s['name']] = convert(s['file'], s['name'], s['semantic'], s.get('tags', []))
        print(s['name'], s['semantic'], 'frames', len(clips[s['name']]['frames']))
    vault = {'version': '5.0.0', 'source': 'CMU Graphics Lab mocap (BVH cgspeed conversion)',
             'fps': OUT_FPS,
             'joints': ['root', 'pelvis', 'spine', 'chest', 'neck', 'head',
                        'clavicle_l', 'shoulder_l', 'elbow_l', 'wrist_l',
                        'clavicle_r', 'shoulder_r', 'elbow_r', 'wrist_r',
                        'hip_l', 'knee_l', 'ankle_l', 'toe_l',
                        'hip_r', 'knee_r', 'ankle_r', 'toe_r'],
             'clips': clips}
    json.dump(vault, open(sys.argv[2], 'w'))
    print('wrote', sys.argv[2], len(clips), 'clips')
