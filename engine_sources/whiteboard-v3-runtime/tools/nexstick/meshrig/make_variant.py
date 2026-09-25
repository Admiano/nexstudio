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
from mathutils import Vector

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
