"""Face-identity feasibility: additive identity morphs on the canonical Host head.

Run:  blender -b <canonical.blend> --python scripts/experiments/face-identity-morphs.py -- \
        --variants scripts/experiments/face-variants.json --out out/faceid/<gender>.blend \
        --render-dir out/faceid/<gender>

Non-destructive by construction: the input .blend is never saved over; every
identity is ONE additive shape key (id_<name>) per participating mesh, so the
existing !ex-*/V3_*/E_*/A_* performance keys compose with it unchanged.
"""
import bpy, json, os, sys, math
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
import argparse
ap = argparse.ArgumentParser()
ap.add_argument("--variants", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--render-dir", default=None)
ap.add_argument("--prefix", default="Host")
a = ap.parse_args(argv)

PRE = a.prefix + "."
BODY = bpy.data.objects[PRE + "body"]
RIG = bpy.data.objects[PRE + "rig"]

# Meshes that must receive the same delta field to stay registered with the
# morphed head: skin clone(s), the drawn face layers, brow/lash strips and the
# tiny bone-parented ear/nose/jaw mark meshes. Vertex-parented mouth pieces
# (V9/V11) and shrinkwrapped hair follow automatically.
PART_PAT = ("body", "high-poly", "lineart_", "V59_face", "eyebrow", "eyelashes", "V10_")
def participating():
    out = []
    for n in bpy.data.objects.keys():
        if not n.startswith(PRE): continue
        o = bpy.data.objects[n]
        if o.type != 'MESH': continue
        if any(n[len(PRE):].startswith(p) for p in PART_PAT):
            out.append(o)
    return out

# ---------- landmark anchors (world space) ----------
def vg_mask(obj, name):
    if name not in obj.vertex_groups: return None
    gi = obj.vertex_groups[name].index
    w = np.zeros(len(obj.data.vertices))
    for v in obj.data.vertices:
        for g in v.groups:
            if g.group == gi: w[v.index] = g.weight
    return w

def world_verts(obj):
    M = np.array(obj.matrix_world)
    v4 = np.empty((len(obj.data.vertices), 4)); v4[:, :3] = [v.co[:] for v in obj.data.vertices]; v4[:, 3] = 1
    return (v4 @ M.T)[:, :3]

bmask = vg_mask(BODY, 'head')
bw = world_verts(BODY)
hw = bw[bmask > 0.1]
head_min, head_max = hw.min(0), hw.max(0)
headC = (head_min + head_max) / 2
headC[2] = head_min[2] + 0.62 * (head_max[2] - head_min[2])  # brow-ish height

def group_box(name):
    m = vg_mask(BODY, name)
    if m is None: return None
    pts = bw[m > 0.1]
    return pts.min(0), pts.max(0), pts.mean(0)

lips = group_box('lips'); jaw = group_box('jaw'); ears = group_box('ears')
mouthC = lips[2]; chinC = np.array([0, jaw[0][1], jaw[0][2]])  # front-lowest jaw
strip = hw[(np.abs(hw[:,0]) < 0.02) & (hw[:,2] > mouthC[2] + 0.008) & (hw[:,2] < mouthC[2] + 0.045)]
noseC = strip[np.argmin(strip[:,1])] if len(strip) else np.array([0, hw[:,1].min(), mouthC[2] + 0.03])
eyeL = np.array(RIG.matrix_world @ RIG.pose.bones['eye.L'].head)
eyeR = np.array(RIG.matrix_world @ RIG.pose.bones['eye.R'].head)
browC = (eyeL + eyeR) / 2 + np.array([0, -0.006, 0.028])
below = hw[hw[:,2] < eyeL[2] - 0.01]
cheekL = below[np.argmax(below[:,0] - below[:,1]*0.3)]
cheekR = below[np.argmax(-below[:,0] - below[:,1]*0.3)]
jawpts = bw[vg_mask(BODY,'jaw') > 0.1]
jawL = jawpts[np.argmax(jawpts[:,0])]; jawR = jawpts[np.argmin(jawpts[:,0])]

def gauss(p, c, r):
    d = np.linalg.norm(p - c) / r
    return math.exp(-d*d*2.2)

# ---------- feature delta field ----------
def build_feats(P):
    F = []
    if P.get("head_width"): F.append((headC, 0.16, lambda v,c: np.array([(v[0]-c[0])*P["head_width"], 0, 0])))
    if P.get("face_len"):
        c0 = np.array([0, mouthC[1]+0.01, mouthC[2]])
        F.append((c0, 0.11, lambda v,c: np.array([0, 0, (v[2]-c[2])*P["face_len"] if v[2] < eyeL[2]+0.015 else 0])))
    if P.get("jaw_width"):
        for j in (jawL, jawR):
            F.append((j, 0.035, lambda v,c: np.array([math.copysign(P["jaw_width"], c[0] or 1), 0, 0])))
    if P.get("chin"):       F.append((chinC, 0.028, lambda v,c: np.array([0, -P["chin"], -abs(P["chin"])*0.4])))
    if P.get("chin_len"):   F.append((chinC, 0.030, lambda v,c: np.array([0, 0, -P["chin_len"]])))
    if P.get("nose_len"):   F.append((noseC, 0.020, lambda v,c: np.array([0, -P["nose_len"], -P["nose_len"]*0.15])))
    if P.get("nose_width"):
        c0 = noseC + np.array([0,0,0.004])
        F.append((c0, 0.020, lambda v,c: np.array([(v[0]-c[0])*P["nose_width"], 0, 0])))
    if P.get("cheek"):
        for cch in (cheekL, cheekR):
            F.append((cch, 0.032, lambda v,c: np.array([math.copysign(P["cheek"]*0.5, c[0] or 1), -P["cheek"], 0])))
    if P.get("eye_spacing"):
        F.append((eyeL, 0.020, lambda v,c: np.array([P["eye_spacing"], 0, 0])))
        F.append((eyeR, 0.020, lambda v,c: np.array([-P["eye_spacing"], 0, 0])))
    if P.get("eye_size"):
        for e in (eyeL, eyeR):
            F.append((e, 0.020, lambda v,c: np.array([(v[0]-c[0])*P["eye_size"], (v[1]-c[1])*P["eye_size"]*0.6, (v[2]-c[2])*P["eye_size"]])))
    if P.get("brow_height"):F.append((browC, 0.030, lambda v,c: np.array([0, 0, P["brow_height"]])))
    if P.get("lip_full"):   F.append((mouthC, 0.020, lambda v,c: np.array([(v[0]-c[0])*P["lip_full"]*0.4, -P["lip_full"]*0.55, (v[2]-c[2])*P["lip_full"]*0.5])))
    if P.get("ears"):
        c0 = ears[2]
        F.append((c0, 0.05, lambda v,c: np.array([(v[0]-c[0])*P["ears"], 0, (v[2]-c[2])*P["ears"]*0.5])))
    return F

def field(p, feats):
    t = np.zeros(3)
    for c, r, fn in feats:
        w = gauss(p, c, r)
        if w < 0.01: continue
        t += fn(p, c) * w
    return t

variants = json.load(open(a.variants))
meshes = participating()
print("PARTICIPATING", [o.name for o in meshes])

for ob in meshes:
    M = np.array(ob.matrix_world); inv = np.linalg.inv(M)
    vw = world_verts(ob)
    if ob.name in (PRE+"body", PRE+"high-poly") or ob.name.startswith(PRE+"lineart_"):
        if ob is BODY:
            gate = bmask.copy()
        else:
            gate = np.clip(1.0 - np.linalg.norm(vw - headC, axis=1) / 0.20, 0, 1)
    else:
        gate = np.ones(len(vw))
    for name, P in variants["variants"].items():
        feats = build_feats(P)
        # Keep the mouth region rigid for structural fields: the V9/V11 mouth
        # interior pieces are vertex-parented to one body vert, so deforming
        # lips/jaw corners opens a gap and the white interior shows through.
        # Only the dedicated lip_full field is allowed to move mouth verts.
        # (teeth/interior meshes are excluded from PART_PAT entirely so nothing
        # can poke them through the closed lips.)
        has_lip = bool(P.get("lip_full"))
        if has_lip and P["lip_full"]:
            lip_feats = feats[-1:]   # lip_full is appended last in build_feats
            other = feats[:-1]
        else:
            lip_feats, other = [], feats
        suppress = np.array([1.0 - gauss(p, mouthC, 0.040) for p in vw])
        d_other = np.array([field(p, other) for p in vw]) * suppress[:, None]
        d_lip = np.array([field(p, lip_feats) for p in vw]) if lip_feats else 0.0
        deltas = (d_other + d_lip) * gate[:, None]
        if not np.abs(deltas).max() > 1e-9:
            continue
        sk = ob.shape_key_add(name="id_" + name, from_mix=False)
        local = (np.c_[vw + deltas, np.ones(len(vw))] @ inv.T)[:, :3]
        for i, key_v in enumerate(sk.data):
            if np.abs(deltas[i]).max() > 1e-9:
                key_v.co = local[i]

os.makedirs(os.path.dirname(a.out), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=a.out)
print("SAVED", a.out)

# ---------- renders: baseline + variants, front + 3/4 ----------
if a.render_dir:
    from mathutils import Matrix
    S = bpy.context.scene
    cam = bpy.data.cameras.new("FACEID_CAM"); cam.type = 'ORTHO'; cam.ortho_scale = 0.24; cam.clip_start = 0.01
    cob = bpy.data.objects.new("FACEID_CAM", cam); S.collection.objects.link(cob)
    S.camera = cob
    S.render.resolution_x = 640; S.render.resolution_y = 760; S.render.resolution_percentage = 100
    S.render.image_settings.file_format = 'PNG'
    if S.render.engine == 'CYCLES':
        S.cycles.samples = 32; S.cycles.use_denoising = True
    aim = headC.copy(); aim[2] -= 0.02
    views = {"front": np.array([0, -0.9, 0]), "threeq": np.array([math.sin(math.radians(35))*0.9, -math.cos(math.radians(35))*0.9, 0.02])}
    tags = ["baseline"] + ["id_" + n for n in variants["variants"]]
    os.makedirs(a.render_dir, exist_ok=True)
    for tag in tags:
        for ob in meshes:
            if ob.data.shape_keys:
                for kb in ob.data.shape_keys.key_blocks:
                    if kb.name.startswith("id_"): kb.value = 1.0 if kb.name == tag else 0.0
        for vn, off in views.items():
            p = aim + off
            f = (aim - p); f = f / np.linalg.norm(f)
            up = np.array([0,0,1.0]); r = np.cross(f, up); u = np.cross(r, f)
            m = Matrix(((r[0],u[0],-f[0]),(r[1],u[1],-f[1]),(r[2],u[2],-f[2])))
            cob.location = p
            cob.rotation_mode = 'QUATERNION'; cob.rotation_quaternion = m.to_quaternion()
            fp = os.path.join(a.render_dir, f"{tag}_{vn}.png")
            S.render.filepath = fp; bpy.ops.render.render(write_still=True)
            print("RENDER", fp, flush=True)
