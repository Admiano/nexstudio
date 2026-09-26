import bpy, json, math, sys

# Bake every action in the opened .blend into the NexStick 22-joint vault
# format. Blender: meters, z-up, character faces -y. Ours: y-up, +z fwd.
# Args after '--': blend_path(out_json, armature_name, name_prefix)

argv = sys.argv[sys.argv.index('--') + 1:]
OUT, ARM_NAME, PREFIX = argv[0], argv[1], argv[2]

arm = bpy.data.objects[ARM_NAME]
scene = bpy.context.scene

MAP = [
    ('root', 'root.x'), ('pelvis', 'spine_01.x'), ('spine', 'spine_02.x'),
    ('chest', 'spine_03.x'), ('neck', 'neck.x'), ('head', 'head.x'),
    ('clavicle_l', 'shoulder.l'), ('shoulder_l', 'arm.l'),
    ('elbow_l', 'forearm.l'), ('wrist_l', 'hand.l'),
    ('clavicle_r', 'shoulder.r'), ('shoulder_r', 'arm.r'),
    ('elbow_r', 'forearm.r'), ('wrist_r', 'hand.r'),
    ('hip_l', 'thigh.l'), ('knee_l', 'leg.l'),
    ('ankle_l', 'foot.l'), ('toe_l', 'toes_01.l'),
    ('hip_r', 'thigh.r'), ('knee_r', 'leg.r'),
    ('ankle_r', 'foot.r'), ('toe_r', 'toes_01.r'),
]
JOINTS = [n for n, _ in MAP]
FPS = 24.0

def conv(v):
    return [v.x, v.z, -v.y]

# head-forward local axis: whichever world axis of the head bone points
# nearest -y (character forward) in the current pose.
def head_axis():
    pb = arm.pose.bones['head.x']
    m3 = (arm.matrix_world @ pb.matrix).to_3x3()
    import mathutils
    best, bestd = None, -2.0
    for ax in range(3):
        for s in (1.0, -1.0):
            d = m3.col[ax] * s
            score = d.normalized().dot(mathutils.Vector((0, -1, 0)))
            if score > bestd:
                bestd, best = score, (ax, s)
    return best

HEAD_AX = head_axis()

def head_fwd(pb):
    m3 = (arm.matrix_world @ pb.matrix).to_3x3()
    ax, s = HEAD_AX
    return (m3.col[ax] * s).normalized()

def roty_of(pb):
    d = head_fwd(pb)
    # our azimuth: atan2(fx, fz) in (x_lat, z_fwd) plane
    return math.degrees(math.atan2(d.x, -d.y))

out = {'version': '5.0.0', 'source': 'nex-performance-carrier-blend',
       'fps': FPS, 'joints': JOINTS, 'clips': {}}

if not arm.animation_data:
    arm.animation_data_create()

for action in sorted(bpy.data.actions, key=lambda a: a.name):
    name = action.name
    if name.startswith('cs_'):
        continue
    arm.animation_data.action = action
    f0, f1 = (int(round(action.frame_range[0])),
              int(round(action.frame_range[1])))
    if f1 <= f0:
        f1 = f0 + 1
    times, frames, rotys = [], [], []
    root_first = None
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        fr = []
        for jn, bn in MAP:
            pb = arm.pose.bones.get(bn)
            if pb is None:
                fr.append([0, 0, 0]); continue
            w = arm.matrix_world @ pb.head
            fr.append([round(c, 5) for c in conv(w)])
        frames.append(fr)
        times.append(round((f - f0) / FPS, 4))
        hb = arm.pose.bones.get('head.x')
        rotys.append(round(roty_of(hb), 3) if hb else 0.0)
        if root_first is None:
            root_first = fr[0]
    root_delta = [round(frames[-1][0][i] - frames[0][0][i], 5) for i in range(3)]
    name_up = name.upper().replace('@', '_').replace(' ', '_')
    if not name_up.startswith(PREFIX):
        name_up = PREFIX + name_up
    semantic = name_up.lower()
    loop = any(k in name_up for k in
               ('WALK', 'RUN', 'CYCLE', 'CRAWL', 'JACK', 'CARDIO', 'CARRY'))
    out['clips'][name_up] = {
        'duration': round((f1 - f0) / FPS, 4), 'fps': FPS,
        'loop': loop, 'source': 'nex-performance-carrier',
        'license': 'NexMind internal — authored rig',
        'semantic': semantic, 'tags': [semantic],
        'times': times, 'frames': frames, 'roty': rotys,
        'rootDelta': root_delta,
    }
    print('BAKED', name_up, len(frames), 'frames')

with open(OUT, 'w') as fh:
    json.dump(out, fh)
print('WROTE', OUT, len(out['clips']), 'clips')
