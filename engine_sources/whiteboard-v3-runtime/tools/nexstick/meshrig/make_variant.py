"""Character-variant builder — Blender-side. Opens the rigged MakeHuman
.blend and writes a new variant .blend: silhouette reshape driven by the
mesh's own bone vertex-groups (no external body files needed), plus
primitive garment/hair meshes auto-weighted onto the armature.

Run inside Blender:
    blender -b <rig.blend> --python make_variant.py -- \
        --variant female|suit|slim --out <out.blend>

Variant specs (silhouette deltas — the look lives in Freestyle contour):
    female: narrower shoulders/arms, wider hips, slight bust, hair bob
    suit:   shoulder pads, jacket waist, straight trousers legs
    slim:   uniformly leaner limbs/torso (teen-ish read)
"""
import bpy
import argparse
import sys
from mathutils import Vector, kdtree

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument('--variant', required=True)
ap.add_argument('--out', required=True)
a = ap.parse_args(argv)

arm = bpy.data.objects['MH_RIG']
mesh = bpy.data.objects['MH_BODY']

# vertex-group region masks: group name -> lateral/vertical scale factor
REGIONS = {
    'female': {
        'scale': 0.96,
        'regions': [
            # proximal groups only — forearms/hands/shins/feet keep shape
            (['clavicle.l', 'clavicle.r', 'upperarm01.l', 'upperarm01.r'],
             (0.84, 1.0, 1.0)),
            (['upperleg01.l', 'upperleg01.r'], (1.16, 1.0, 1.0)),
            (['spine02'], (0.92, 1.0, 1.0)),
        ],
        'hair': 'bob',
    },
    'suit': {
        'scale': 1.0,
        'regions': [
            (['clavicle.l', 'clavicle.r'], (1.10, 1.0, 1.06)),
            (['spine02', 'spine05'], (1.06, 1.0, 1.04)),
            (['upperleg01.l', 'upperleg01.r'], (1.05, 1.0, 1.0)),
        ],
        'hair': 'crop',
    },
    'slim': {
        'scale': 0.94,
        'regions': [
            (['upperarm01.l', 'upperarm01.r'], (0.86, 1.0, 1.0)),
            (['upperleg01.l', 'upperleg01.r'], (0.90, 1.0, 1.0)),
            (['spine02'], (0.92, 1.0, 1.0)),
        ],
        'hair': 'crop',
    },
}
spec = REGIONS[a.variant]

# global height scale about the root
for v in mesh.data.vertices:
    v.co *= spec['scale']

# region-weighted lateral reshapes (X = lateral, Y = up, Z = front/back)
vgi = {g.name.lower(): g.index for g in mesh.vertex_groups}
for names, (sx, sy, sz) in spec['regions']:
    for nm in names:
        gi = vgi.get(nm)
        if gi is None:
            continue
        for v in mesh.data.vertices:
            w = next((g.weight for g in v.groups if g.group == gi), 0.0)
            if w <= 0:
                continue
            f = w ** 0.7          # soften toward region edges
            v.co.x *= 1 + (sx - 1) * f
            v.co.y *= 1 + (sy - 1) * f
            v.co.z *= 1 + (sz - 1) * f


def _bone_head(nm):
    return arm.matrix_world @ arm.data.bones[nm].head_local


def _bone_tail(nm):
    return arm.matrix_world @ arm.data.bones[nm].tail_local


def _attach(o):
    o.parent = arm
    mod = o.modifiers.new('arm', 'ARMATURE')
    mod.object = arm
    return o


def _copy_weights(o, source):
    # each garment vert inherits the blend weights of the nearest body vert,
    # so clothing deforms with the body it covers (sleeves bend at the elbow)
    kd = kdtree.KDTree(len(source.data.vertices))
    mw = source.matrix_world
    for i, v in enumerate(source.data.vertices):
        kd.insert(mw @ v.co, i)
    kd.balance()
    gname = {g.index: g.name for g in source.vertex_groups}
    omw = o.matrix_world
    for v in o.data.vertices:
        _co, idx, _d = kd.find(omw @ v.co)
        for g in source.data.vertices[idx].groups:
            vg = o.vertex_groups.get(gname[g.group]) or \
                o.vertex_groups.new(name=gname[g.group])
            vg.add([v.index], g.weight, 'REPLACE')


def _limb_r(bone):
    gi = vgi.get(bone.lower())
    if gi is None:
        return None
    a, b = _bone_head(bone), _bone_tail(bone)
    d = b - a
    dn = d.normalized()
    rs = []
    for v in mesh.data.vertices:
        w = next((g.weight for g in v.groups if g.group == gi), 0.0)
        if w <= 0.4:
            continue
        p = mesh.matrix_world @ v.co
        t = (p - a).dot(dn)
        if 0 <= t <= d.length:
            rs.append(((p - a) - dn * t).length)
    return max(rs) if rs else None


def _tube(name, bone, r_head, r_tail, t0=0.0, t1=1.0):
    a, b = _bone_head(bone), _bone_tail(bone)
    d = b - a
    p0 = a + d * t0
    p1 = a + d * t1
    dd = p1 - p0
    bpy.ops.mesh.primitive_cone_add(
        vertices=14, radius1=r_head, radius2=r_tail, depth=dd.length,
        location=(p0 + p1) / 2)
    o = bpy.context.active_object
    o.name = name
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = dd.to_track_quat('Z', 'Y')
    bpy.ops.object.transform_apply(rotation=True)
    _attach(o)
    _copy_weights(o, mesh)
    return o


def _region_pts(names, wmin=0.4):
    gis = [vgi[n] for n in names if n in vgi]
    return [mesh.matrix_world @ v.co for v in mesh.data.vertices
            if any(g.group in gis and g.weight > wmin for g in v.groups)]


def _shell(name, a, b, rings, nseg=18):
    # open-ended tube following an axis; `rings` = [(t, rx, ry)] — each ring
    # gets many verts so nearest-body weights deform it like skin. Rest pose
    # is near-vertical so the fixed X/Y basis tracks lateral/front-back.
    import math
    d = b - a
    L = d.length
    dn = d.normalized()
    u = dn.cross(Vector((0, 1, 0)))
    if u.length < 0.1:
        u = dn.cross(Vector((1, 0, 0)))
    u = u.normalized()
    v = dn.cross(u).normalized()
    verts = []
    for t, rx, ry in rings:
        for i in range(nseg):
            ang = 2 * math.pi * i / nseg
            p = a + dn * (t * L) + u * math.cos(ang) * rx \
                + v * math.sin(ang) * ry
            verts.append(p)
    faces = []
    for r in range(len(rings) - 1):
        for i in range(nseg):
            j = (i + 1) % nseg
            r0, r1 = r * nseg, (r + 1) * nseg
            faces.append((r0 + i, r0 + j, r1 + j, r1 + i))
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in verts], [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    _attach(o)
    _copy_weights(o, mesh)
    return o


def _band(name, center, rx, ry, h):
    # thin garment band hugging the body — renders its edge loops as a
    # garment line (collar / hem / cuff) with minimal deformable surface
    _shell(name, center - Vector((0, 0, h / 2)),
           center + Vector((0, 0, h / 2)),
           [(0.0, rx, ry), (1.0, rx, ry)], nseg=22)


def _band_at(name, bone, t, grow=1.10):
    # band wrapped around a bone at fraction t along it
    a, b = _bone_head(bone), _bone_tail(bone)
    c = a + (b - a) * t
    pts = _region_pts([bone.lower()], 0.25)
    rx = max((abs((p - c).x) for p in pts), default=0.5) * grow
    ry = max((abs((p - c).y) for p in pts), default=0.5) * grow
    _band(name, c, rx, ry, 0.18)


def _jacket():
    # garment lines only: collar band at the neck, hem band at the hips.
    # A full torso shell deforms badly under pose; thin bands stay honest.
    _band_at('COLLAR', 'neck01', 0.3, 1.25)
    _band_at('HEM', 'root', 0.75, 1.10)


def _suit():
    _jacket()
    for s in ('.L', '.R'):
        ru = _limb_r('upperarm01' + s) or 0.9
        rf = _limb_r('lowerarm01' + s) or 0.8
        _tube('SLEEVE_U' + s, 'upperarm01' + s, ru * 1.55, ru * 1.30)
        _tube('SLEEVE_F' + s, 'lowerarm01' + s, rf * 1.45, rf * 1.25)
        rt = _limb_r('upperleg01' + s) or 1.2
        rs = _limb_r('lowerleg01' + s) or 0.9
        _tube('PANT_U' + s, 'upperleg01' + s, rt * 1.22, rs * 1.28,
              t0=0.35)
        _tube('PANT_L' + s, 'lowerleg01' + s, rs * 1.24, rs * 1.18)


_garments = {'suit': _suit}
if a.variant in _garments:
    _garments[a.variant]()


def _add_uv(name, loc, scale, parent_bone):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=16, ring_count=12, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    # armature deform via the bone's vertex group (rigid ride)
    o.parent = arm
    vg = o.vertex_groups.new(name=parent_bone)
    vg.add(range(len(o.data.vertices)), 1.0, 'REPLACE')
    mod = o.modifiers.new('arm', 'ARMATURE')
    mod.object = arm
    return o


def _hair(style):
    # measure the head-group extent so the cap sizes itself to the rig
    gi = vgi.get('head')
    pts = [mesh.matrix_world @ v.co for v in mesh.data.vertices
           if any(g.group == gi and g.weight > 0.4 for g in v.groups)]
    if not pts:
        return None
    xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    cz = (min(zs) + max(zs)) / 2
    rx, ry, rz = (max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2, \
        (max(zs) - min(zs)) / 2
    if style == 'bob':
        # chin-length bob: fuller cap reaching below the ears
        o = _add_uv('HAIR', Vector((cx, cy + ry * 0.22, cz + rz * 0.12)),
                    (rx * 1.32, ry * 1.20, rz * 1.30), 'head')
        for v in o.data.vertices:
            # local frame = world frame: -Y is face-forward, Z is up
            if v.co.y < -ry * 0.55:           # clear the face opening
                v.co.y = -ry * 0.55
            if v.co.z < -rz * 1.35:           # trim to jaw length
                v.co.z = -rz * 1.35
    else:
        # short crop: cap just over the skull top
        o = _add_uv('HAIR', Vector((cx, cy + ry * 0.24, cz + rz * 0.24)),
                    (rx * 1.16, ry * 1.10, rz * 0.95), 'head')
        for v in o.data.vertices:
            if v.co.y < -ry * 0.55:
                v.co.y = -ry * 0.55
            if v.co.z < -rz * 0.55:           # sits on top, ears free
                v.co.z = -rz * 0.55
    return o


_hair(spec['hair'])
mesh.data.update()

# freestyle: keep line settings for the new objects (scene-level, inherited)
bpy.ops.wm.save_as_mainfile(filepath=a.out)
print('VARIANT', a.variant, '->', a.out)
