"""Face-identity feasibility v2: drawn-feature + structural morphs on the
canonical Host head.

Task 01 lesson: deforming only the 3D head leaves the illustrated face looking
like the same person — identity in this style lives in the drawn ink layers
(V59_face_art/frame: eye lines, brow lines, nose contour, lip lines, jawline).
v2 therefore applies TWO deformation systems, both baked as additive id_<name>
shape keys (composed with the !ex-*/V3_*/A_*/E_* performance keys untouched):

  1. STRUCTURAL field (body, high-poly, lineart_*, V10_*): gaussian landmark
     fields for skull width, forehead height, face thirds, jawline/chin,
     cheekbones, ear position.
  2. FEATURE transforms (V59_face_art/frame, lineart_pupil.L/R, eyebrow001,
     eyelashes01): per-feature rigid-ish transforms — each drawn feature is
     segmented by landmark proximity and transformed (scale / shear / rotate /
     translate) independently: eye size+spacing+tilt, brow thickness+arch+
     height+angle, nose width+length+tip, lip width+fullness+height, ear size.

  Mouth pieces (V9/V11 vertex-parented + teeth_base): evaluated at their
  effective world positions so they deform WITH the lip field instead of
  rigidly tracking one vertex — resolves the Task 01 mouth tear while keeping
  viseme shape keys intact (they're on separate meshes).

Non-destructive: input .blend is never saved over; output goes to --out.

Run:  blender -b <canonical.blend> --python scripts/experiments/face-identity-morphs.py -- \
        --variants scripts/experiments/face-identities.json --out out/<g>.blend \
        --render-dir out/<g> [--identity <name>]
"""
import bpy, json, os, sys, math
import numpy as np
from mathutils import Matrix, Vector

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

# Participant groups.
STRUCT_PAT = ("body", "high-poly", "lineart_")          # gated to head region
FEAT_PAT = ("V59_face_art", "V59_face_frame", "eyebrow", "eyelashes",
            "lineart_pupil")                             # drawn feature layers
SMALL_PAT = ("V10_",)                                    # tiny bone-parented marks
MOUTH_PAT = ("V9_", "V11_", "teeth_base")                # coherent mouth pieces

def which_group(n):
    s = n[len(PRE):]
    if any(s.startswith(p) for p in MOUTH_PAT): return "mouth"
    if any(s.startswith(p) for p in FEAT_PAT):  return "feat"
    if any(s.startswith(p) for p in SMALL_PAT): return "small"
    if any(s.startswith(p) for p in STRUCT_PAT): return "struct"
    return None

def participating():
    out = []
    for n in bpy.data.objects.keys():
        if not n.startswith(PRE): continue
        o = bpy.data.objects[n]
        if o.type != 'MESH': continue
        g = which_group(n)
        if g: out.append((o, g))
    return out

# ---------- helpers ----------
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

def group_box(name):
    m = vg_mask(BODY, name)
    if m is None: return None
    pts = bw[m > 0.1]
    return pts.min(0), pts.max(0), pts.mean(0)

lips = group_box('lips'); jaw = group_box('jaw'); ears = group_box('ears')
mouthC = lips[2].copy()
chinC = np.array([0, jaw[0][1], jaw[0][2]])
strip = hw[(np.abs(hw[:,0]) < 0.02) & (hw[:,2] > mouthC[2] + 0.008) & (hw[:,2] < mouthC[2] + 0.045)]
noseC = strip[np.argmin(strip[:,1])] if len(strip) else np.array([0, hw[:,1].min(), mouthC[2] + 0.03])
eyeL = np.array(RIG.matrix_world @ RIG.pose.bones['eye.L'].head)
eyeR = np.array(RIG.matrix_world @ RIG.pose.bones['eye.R'].head)
eyeC = (eyeL + eyeR) / 2
browC = eyeC + np.array([0, -0.004, 0.030])
jawpts = bw[vg_mask(BODY,'jaw') > 0.1]
jawL = jawpts[np.argmax(jawpts[:,0])]; jawR = jawpts[np.argmin(jawpts[:,0])]
below = hw[hw[:,2] < eyeL[2] - 0.01]
cheekL = below[np.argmax(below[:,0] - below[:,1]*0.3)]
cheekR = below[np.argmax(-below[:,0] - below[:,1]*0.3)]
earC = ears[2] if ears is not None else headC.copy()
foreheadZ = head_max[2] - 0.015

def gauss(p, c, r):
    d = np.linalg.norm(p - c) / r
    return math.exp(-d*d*2.2)

# ---------- STRUCTURAL field (tagged; order-independent) ----------
def build_fields(P):
    """Return list of (tag, center, radius, fn). Mouth-region fields tagged
    'mouth' so coherent mouth pieces get them and nothing double-applies."""
    F = []
    add = lambda tag, c, r, fn: F.append((tag, np.array(c, float), r, fn))
    if P.get("head_width"):
        add("struct", headC, 0.16, lambda v,c: np.array([(v[0]-c[0])*P["head_width"], 0, 0]))
    if P.get("face_len"):
        c0 = np.array([0, mouthC[1]+0.01, mouthC[2]])
        add("struct", c0, 0.11, lambda v,c: np.array([0, 0, (v[2]-c[2])*P["face_len"] if v[2] < eyeL[2]+0.015 else 0]))
    if P.get("forehead"):
        add("struct", np.array([0, headC[1], foreheadZ]), 0.10,
            lambda v,c: np.array([0, 0, (v[2]-eyeL[2])*P["forehead"] if v[2] > eyeL[2] else 0]))
    if P.get("jaw_width"):
        for j, s in ((jawL, 1), (jawR, -1)):
            add("struct", j, 0.060, lambda v,c: np.array([s*P["jaw_width"] * max(0.0, 1.0 - abs(v[2]-c[2])/0.10), 0, 0]))
    if P.get("chin"):
        add("struct", chinC, 0.050, lambda v,c: np.array([0, -P["chin"], -abs(P["chin"])*0.4]))
    if P.get("chin_len"):
        add("struct", chinC, 0.050, lambda v,c: np.array([0, 0, -P["chin_len"]]))
    if P.get("nose_len"):
        add("mouth", noseC, 0.020, lambda v,c: np.array([0, -P["nose_len"], -P["nose_len"]*0.15]))
    if P.get("nose_width"):
        c0 = noseC + np.array([0,0,0.004])
        add("mouth", c0, 0.020, lambda v,c: np.array([(v[0]-c[0])*P["nose_width"], 0, 0]))
    if P.get("cheek"):
        for cch, s in ((cheekL, 1), (cheekR, -1)):
            add("struct", cch, 0.050, lambda v,c: np.array([s*P["cheek"]*0.5, -P["cheek"], 0]))
    if P.get("eye_spacing"):
        add("struct", eyeL, 0.020, lambda v,c: np.array([P["eye_spacing"], 0, 0]))
        add("struct", eyeR, 0.020, lambda v,c: np.array([-P["eye_spacing"], 0, 0]))
    if P.get("eye_size"):
        for e in (eyeL, eyeR):
            add("struct", e, 0.020, lambda v,c: np.array([(v[0]-c[0])*P["eye_size"], (v[1]-c[1])*P["eye_size"]*0.6, (v[2]-c[2])*P["eye_size"]]))
    if P.get("brow_height"):
        add("struct", browC, 0.030, lambda v,c: np.array([0, 0, P["brow_height"]]))
    # lip_full / lip_width / mouth_pos are feature transforms (feat_delta /
    # lip_vec), not struct fields — do not add them here or they double-apply.
    return F

def field(p, feats):
    t = np.zeros(3)
    for tag, c, r, fn in feats:
        w = gauss(p, c, r)
        if w < 0.01: continue
        t += fn(p, c) * w
    return t

# ---------- FEATURE transforms on the drawn layers ----------
# Segmentation is vertex-group driven where the art layers carry muscle groups
# (oculi*/orbicularis03-04 = eyes, lips/oris*/levator = mouth/nose-adjacent),
# tightened by small position gates. Brows/lashes are their own meshes and are
# transformed as whole features (L/R split by x sign).
def vg_weight_map(ob, patterns):
    """Per-vertex max weight across groups matching any substring pattern."""
    gis = [g.index for g in ob.vertex_groups if any(p in g.name for p in patterns)]
    w = np.zeros(len(ob.data.vertices))
    if not gis: return w
    for v in ob.data.vertices:
        for gr in v.groups:
            if gr.group in gis and gr.weight > w[v.index]: w[v.index] = gr.weight
    return w

def seg_weights(ob, vw):
    """Feature segment weights for a drawn-layer mesh."""
    n = len(vw)
    segs = {}
    eye_vg = vg_weight_map(ob, ('oculi', 'orbicularis03', 'orbicularis04'))
    lip_vg = vg_weight_map(ob, ('oris', 'lips'))
    nose_vg = vg_weight_map(ob, ('levator',))
    # position gates keep muscle verts on the right feature
    zcut = (eyeC[2] + mouthC[2]) / 2
    # Hard radial gates: a vert must be NEAR its anchor to join a feature, so
    # vgroup claims can't pull stray strokes across the face.
    def hardgate(pts, c, rin, rout):
        return np.clip(1.0 - (np.linalg.norm(pts - c, axis=1) - rin) / (rout - rin), 0, 1)
    segs['eyeL'] = np.maximum(eye_vg * np.array([1.0 if p[0] > 0 and p[2] > zcut else 0 for p in vw]),
                              np.array([gauss(p, eyeL, 0.016) for p in vw])) * hardgate(vw, eyeL, 0.022, 0.034)
    segs['eyeR'] = np.maximum(eye_vg * np.array([1.0 if p[0] < 0 and p[2] > zcut else 0 for p in vw]),
                              np.array([gauss(p, eyeR, 0.016) for p in vw])) * hardgate(vw, eyeR, 0.022, 0.034)
    segs['lips'] = np.maximum(lip_vg * np.array([1.0 if p[2] < zcut else 0 for p in vw]),
                              np.array([gauss(p, mouthC, 0.018) for p in vw])) * hardgate(vw, mouthC, 0.024, 0.038)
    segs['nose'] = np.maximum(nose_vg,
                              np.array([gauss(p, noseC, 0.016) * (1.0 if abs(p[0]) < 0.025 and mouthC[2] < p[2] < eyeC[2] else 0) for p in vw]))
    segs['earL'] = np.array([gauss(p, np.array([abs(head_min[0]), earC[1], earC[2]]), 0.030) for p in vw]) if ears is not None else np.zeros(n)
    segs['earR'] = np.array([gauss(p, np.array([-abs(head_min[0]), earC[1], earC[2]]), 0.030) for p in vw]) if ears is not None else np.zeros(n)
    # keep the strongest single claim per vertex so features never fight
    order = ['eyeL', 'eyeR', 'lips', 'nose', 'earL', 'earR']
    W = np.stack([segs[k] for k in order])
    keep = np.argmax(W, 0)
    for j, k in enumerate(order):
        segs[k] = np.where(keep == j, W[j], 0.0)
    # tiny claims are where stray strokes live — snap them to zero so small
    # edge verts can't fly off and leave jagged marks on the cheek/eye rim
    for k in order:
        segs[k][segs[k] < 0.12] = 0.0
    return segs

def lip_vec(p, P):
    """Lip feature translation shared by drawn lips, body lip verts and the
    vertex-parented mouth pieces — keeps the whole mouth region coherent."""
    t = np.zeros(3)
    if P.get("lip_width"): t += np.array([math.copysign(P["lip_width"], p[0] or 1), 0, 0])
    if P.get("lip_full"):  t += np.array([0, -P["lip_full"]*0.5, (p[2]-mouthC[2])*P["lip_full"]])
    if P.get("mouth_pos"): t += np.array([0, 0, P["mouth_pos"]])
    return t

# ---------- feature RE-DRAW: retarget art verts onto per-identity curves ----
# Scaling the same stroke tops out at "same person, different proportions".
# Distinct people need different DRAWN shapes: each art vert is moved to the
# nearest point on a parametric target curve in the feature's local frame.
def _eye_curve(shape, w, h):
    """Closed eye-outline polyline in local (x: -w..w, z: -h..h) coords."""
    ts = np.linspace(0, 2*math.pi, 64)
    if shape == 'round':
        x = w*np.cos(ts); z = h*np.sin(ts)
    elif shape == 'narrow':
        x = w*np.cos(ts); z = h*np.sin(ts)*0.55
    elif shape == 'upturned':
        x = w*np.cos(ts); z = h*np.sin(ts)*(0.6 + 0.4*(np.cos(ts)*-1+1)/2)
        z = z + x*0.35
    elif shape == 'downturned':
        x = w*np.cos(ts); z = h*np.sin(ts)*(0.6 + 0.4*(np.cos(ts)+1)/2)
        z = z - x*0.35
    else:  # almond (default lens)
        x = w*np.cos(ts); z = h*np.sin(ts)*0.75*(1.0 - 0.15*np.cos(2*ts))
    return np.stack([x, z], 1)

def retarget_eyes(vw, segs, P):
    """Move eye-region art verts onto the target eye curve shape."""
    d = np.zeros_like(vw)
    shape = P.get('eye_shape')
    if not shape: return d
    for e, sgn, seg in ((eyeL, 1.0, 'eyeL'), (eyeR, -1.0, 'eyeR')):
        w = segs[seg]
        idx = np.where(w > 0.05)[0]
        if not len(idx): continue
        pts = vw[idx]
        # current bbox → target curve with the identity's aspect
        hw_ = max(0.004, (pts[:,0].max()-pts[:,0].min())/2)
        hh_ = max(0.003, (pts[:,2].max()-pts[:,2].min())/2)
        ew_ = hw_ * (1.0 + P.get('eye_w', 0) + P.get('eye_size', 0))
        eh_ = hh_ * (1.0 + P.get('eye_h', 0) + P.get('eye_size', 0))
        cc = pts.mean(0)
        C = _eye_curve(shape, ew_, eh_)
        tilt = P.get('eye_tilt', 0) * 0.35
        Ct = C.copy(); Ct[:,1] += sgn * C[:,0] * tilt
        Ct[:,0] += cc[0]; Ct[:,1] += cc[2]
        for k, i in enumerate(idx):
            p = vw[i]
            j = np.argmin((Ct[:,0]-p[0])**2 + (Ct[:,1]-p[2])**2)
            tgt = np.array([Ct[j,0], p[1], Ct[j,1]])
            dd = (tgt - p) * w[i]
            n = np.linalg.norm(dd)
            if n > 0.0035: dd *= 0.0035 / n   # cap: avoid angular kinks on the eye rim
            d[i] += dd
    return d

def retarget_lips(vw, segs, P):
    """Reshape the drawn mouth line: width + corner raise/drop + fullness."""
    d = np.zeros_like(vw)
    lw = P.get('lip_width'); cr = P.get('lip_corner'); lf = P.get('lip_shape_z')
    if not (lw or cr or lf): return d
    w = segs['lips']; idx = np.where(w > 0.05)[0]
    if not len(idx): return d
    pts = vw[idx]; cc = mouthC.copy()
    half = max(0.006, (pts[:,0].max()-pts[:,0].min())/2)
    for k, i in enumerate(idx):
        p = vw[i]
        xn = np.clip((p[0]-cc[0])/half, -1, 1)
        t = np.zeros(3)
        if lw: t += np.array([xn*lw, 0, 0])
        if cr: t += np.array([0, 0, cr*(xn*xn)])
        if lf: t += np.array([0, 0, lf*(1-xn*xn)*math.copysign(1, p[2]-cc[2] or 1)])
        d[i] += t * w[i]
    return d

def feat_delta(vw, P, segs, name):
    d = np.zeros_like(vw)
    if any(P.get(k) for k in ("eye_size", "eye_w", "eye_h", "eye_spacing", "eye_tilt", "eye_depth")):
        for e, sgn, seg in ((eyeL, 1, 'eyeL'), (eyeR, -1, 'eyeR')):
            w = segs[seg]
            for i, p in enumerate(vw):
                wi = w[i]
                if wi < 0.03: continue
                t = np.zeros(3)
                ew = P.get("eye_size", 0) + P.get("eye_w", 0)
                eh = P.get("eye_size", 0) + P.get("eye_h", 0)
                t += np.array([(p[0]-e[0])*ew, 0, (p[2]-e[2])*eh])
                if P.get("eye_depth"): t += np.array([0, P["eye_depth"], 0])
                if P.get("eye_spacing"): t += np.array([sgn*P["eye_spacing"], 0, 0])
                if P.get("eye_tilt"):   t += np.array([0, 0, sgn*(p[0]-e[0])*P["eye_tilt"]])
                d[i] += t * wi
    if P.get("nose_width") or P.get("nose_len") or P.get("nose_tip"):
        w = segs['nose']
        for i, p in enumerate(vw):
            wi = w[i]
            if wi < 0.03: continue
            t = np.zeros(3)
            if P.get("nose_width"): t += np.array([(p[0]-noseC[0])*P["nose_width"], 0, 0])
            if P.get("nose_len"):   t += np.array([0, -P["nose_len"]*0.4, -P["nose_len"]])
            if P.get("nose_tip"):
                tipw = math.exp(-(((p[2]-noseC[2])/0.012)**2)*2.2)
                t += np.array([0, -P["nose_tip"]*tipw, -abs(P["nose_tip"])*tipw*0.3])
            d[i] += t * wi
    if P.get("lip_width") or P.get("lip_full") or P.get("mouth_pos"):
        w = segs['lips']
        for i, p in enumerate(vw):
            wi = w[i]
            if wi < 0.03: continue
            d[i] += lip_vec(p, P) * wi
    if (P.get("ear_size") or P.get("ear_pos")) and ears is not None:
        for sgn, seg in ((1, 'earL'), (-1, 'earR')):
            w = segs[seg]
            c = np.array([sgn*abs(head_min[0]), earC[1], earC[2]])
            for i, p in enumerate(vw):
                wi = w[i]
                if wi < 0.03: continue
                t = np.zeros(3)
                if P.get("ear_size"): t += np.array([(p[0]-c[0])*P["ear_size"], (p[2]-c[2])*P["ear_size"], 0])
                if P.get("ear_pos"):  t += np.array([0, 0, P["ear_pos"]])
                d[i] += t * wi
    return d

# Brow mesh transforms: eyebrow001 carries the drawn brow strokes; eyelashes01
# the lash lines. Whole-mesh, L/R split by x sign, about per-side anchors.
def brow_delta(ob, vw, P):
    if not any(P.get(k) for k in ("brow_thick", "brow_arch", "brow_height", "brow_angle")):
        return np.zeros_like(vw)
    d = np.zeros_like(vw)
    for i, p in enumerate(vw):
        sgn = 1.0 if p[0] >= 0 else -1.0
        c = np.array([sgn*0.030, browC[1], browC[2]])
        t = np.zeros(3)
        if P.get("brow_thick"): t += np.array([0, 0, (p[2]-c[2])*P["brow_thick"]])
        if P.get("brow_arch"):  t += np.array([0, 0, -((p[0]-sgn*0.006)/0.030)**2 * P["brow_arch"] * 0.012])
        if P.get("brow_height"):t += np.array([0, 0, P["brow_height"]])
        if P.get("brow_angle"): t += np.array([0, 0, (p[0]-c[0])*P["brow_angle"]])
        d[i] += t
    return d

def lash_delta(vw, P):
    if not any(P.get(k) for k in ("eye_size", "eye_w", "eye_h", "eye_spacing", "eye_tilt")):
        return np.zeros_like(vw)
    d = np.zeros_like(vw)
    ew = P.get("eye_size", 0) + P.get("eye_w", 0)
    eh = P.get("eye_size", 0) + P.get("eye_h", 0)
    for i, p in enumerate(vw):
        e = eyeL if p[0] >= 0 else eyeR
        sgn = 1.0 if p[0] >= 0 else -1.0
        t = np.zeros(3)
        t += np.array([(p[0]-e[0])*ew, 0, (p[2]-e[2])*eh])
        if P.get("eye_spacing"):t += np.array([sgn*P["eye_spacing"], 0, 0])
        if P.get("eye_tilt"):   t += np.array([0, 0, sgn*(p[0]-e[0])*P["eye_tilt"]])
        d[i] += t
    return d

# ---------- apply ----------
variants = json.load(open(a.variants))
meshes = participating()
print("PARTICIPATING", [(o.name, g) for o, g in meshes])

def vertex_parent_offset(ob):
    """World-space offset a vertex-parented object's verts sit at. matrix_world
    is stale for vertex parents in background mode, so derive it from the
    parent object's actual vertex position(s)."""
    if ob.parent_type not in ('VERTEX', 'VERTEX_3') or ob.parent is None:
        return None
    pv = ob.parent_vertices[:3]
    pw = world_verts(ob.parent)
    if ob.parent_type == 'VERTEX':
        return pw[pv[0]]
    return pw[list(pv)].mean(0)

for ob, grp in meshes:
    M = np.array(ob.matrix_world); inv = np.linalg.inv(M)
    vp_off = vertex_parent_offset(ob)
    if vp_off is not None:
        # effective world pos = parent-vertex offset + local coords
        lv = np.array([v.co[:] for v in ob.data.vertices])
        vw = lv + vp_off
    else:
        lv = None
        vw = world_verts(ob)
    short = ob.name[len(PRE):]
    is_art = short.startswith("V59_face")
    is_brow = short.startswith("eyebrow")
    is_lash = short.startswith("eyelashes") or short.startswith("lineart_pupil")
    segs = seg_weights(ob, vw) if is_art else None
    if grp == "struct":
        gate = bmask.copy() if ob is BODY else np.clip(1.0 - np.linalg.norm(vw - headC, axis=1) / 0.20, 0, 1)
    else:
        gate = np.ones(len(vw))
    for name, P in variants["variants"].items():
        feats = build_fields(P)
        d_struct = np.array([field(p, feats) for p in vw])
        if is_art:
            d_extra = feat_delta(vw, P, segs, name) + retarget_eyes(vw, segs, P) + retarget_lips(vw, segs, P)
        elif is_brow:
            d_extra = brow_delta(ob, vw, P)
        elif is_lash:
            d_extra = lash_delta(vw, P)
        else:
            d_extra = 0.0
        if grp in ("struct", "mouth") and any(P.get(k) for k in ("lip_width", "lip_full", "mouth_pos")):
            # body lip verts + V9/V11/teeth move WITH the drawn lip line
            w_lip = np.array([gauss(p, mouthC, 0.020) for p in vw])
            d_extra = d_extra + np.array([lip_vec(p, P) * w_lip[i] for i, p in enumerate(vw)])
        deltas = (d_struct + d_extra) * gate[:, None]
        if not np.abs(deltas).max() > 1e-9:
            continue
        sk = ob.shape_key_add(name="id_" + name, from_mix=False)
        if vp_off is not None:
            local = lv + deltas   # vertex-parented: world delta maps 1:1 to local
        else:
            local = (np.c_[vw + deltas, np.ones(len(vw))] @ inv.T)[:, :3]
        for i, key_v in enumerate(sk.data):
            if np.abs(deltas[i]).max() > 1e-9:
                key_v.co = local[i]

os.makedirs(os.path.dirname(a.out), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=a.out)
print("SAVED", a.out)

# ---------- renders: baseline + variants, front + 3/4 ----------
if a.render_dir:
    S = bpy.context.scene
    cam = bpy.data.cameras.new("FACEID_CAM"); cam.type = 'ORTHO'; cam.ortho_scale = 0.24; cam.clip_start = 0.01
    cob = bpy.data.objects.new("FACEID_CAM", cam); S.collection.objects.link(cob)
    S.camera = cob
    S.render.resolution_x = 640; S.render.resolution_y = 760; S.render.resolution_percentage = 100
    S.render.image_settings.file_format = 'PNG'
    S.render.engine = 'CYCLES'; S.cycles.samples = 32; S.cycles.use_denoising = True
    S.cycles.device = 'CPU'
    aim = headC.copy()
    def point(cam_obj, target):
        d = (np.array(target) - np.array(cam_obj.location))
        d = Vector(d / np.linalg.norm(d))
        cam_obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    shots = []
    shots.append(("baseline", None))
    for name in variants["variants"].keys():
        shots.append(("id_" + name, "id_" + name))
    # The canonical "look" is stored as NONZERO key values (browUp, mouthSmile,
    # browInnerUp, $md-* demographics). Preserve them — only id_* keys toggle.
    base_vals = {}
    for ob2, _ in meshes:
        if ob2.data.shape_keys:
            base_vals[ob2.name] = {kb.name: kb.value for kb in ob2.data.shape_keys.key_blocks}
    def set_key(name):
        for ob2, _ in meshes:
            ks = ob2.data.shape_keys
            if ks is None: continue
            for kb in ks.key_blocks:
                if kb.name == name:
                    kb.value = 1.0
                elif kb.name.startswith("id_"):
                    kb.value = 0.0
                else:
                    kb.value = base_vals[ob2.name].get(kb.name, kb.value)
    views = {"front": (aim + Vector((0, -1.4, 0.02)), aim),
             "threeq": (aim + Vector((0.42, -1.32, 0.02)), aim)}
    os.makedirs(a.render_dir, exist_ok=True)
    for sname, key in shots:
        set_key(key)
        bpy.context.view_layer.update()
        for vname, (pos, tgt) in views.items():
            cob.location = pos
            point(cob, tgt)
            S.render.filepath = os.path.join(a.render_dir, f"{sname}_{vname}.png")
            bpy.ops.render.render(write_still=True)
            print("RENDER", S.render.filepath)
