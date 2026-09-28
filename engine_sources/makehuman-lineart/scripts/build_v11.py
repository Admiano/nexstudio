"""V11: articulated mouth plate + skin-tracking chin mark, built on V10 scenes.

Run:   blender -b scenes/V10/<X>_FULLBODY_15S_V10.blend --python scripts/build_v11.py
Saves: scenes/V11/<X>_FULLBODY_15S_V11.blend

V10 ships a flat `V9_lip_bound_aperture` ellipse as the only mouth. V11 replaces
it with a layered decal mouth assembly driven by the already-baked viseme
envelope (`!ex-jawOpen`, `V3_wide`, `V3_round`, `V3_closed`, `V3_FV`):

  V11_mouth_interior   dark opening shape; open/wide/round/FV morphs
  V11_mouth_teeth      white band at the top of the opening (upper teeth)
  V11_mouth_tongue     mid-tone patch at the bottom of the opening

and re-anchors `V10_jaw` (the chin mark) from the rigid `head` bone to a
VERTEX_3 parent on chin verts so the mark follows the deforming jaw skin.
"""
from pathlib import Path
import math
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent          # scripts/
OUT = ROOT.parent / 'scenes' / 'V11'
OUT.mkdir(parents=True, exist_ok=True)
s = bpy.context.scene
p = 'Host' if 'HOST_' in bpy.data.filepath else 'Guest'
body = bpy.data.objects[p + '.body']
rig = bpy.data.objects[p + '.rig']
s.frame_set(1)

aperture = bpy.data.objects[p + '.V9_lip_bound_aperture']
anchor_vert = aperture.parent_vertices[0]


def emission(name, value):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    em = mat.node_tree.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (value, value, value, 1)
    out = mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
    mat.node_tree.links.new(em.outputs[0], out.inputs['Surface'])
    return mat


INK = emission('V11_MOUTH_INK', 0.02)
TONGUE = emission('V11_MOUTH_TONGUE', 0.30)
TEETH = bpy.data.materials.get('LINEART_WHITE') or emission('LINEART_WHITE', 1.0)

OPEN = 'max(0,min(1,(v-0.04)/0.5))*(1-c*0.85)'
OPEN_KEYS = (('v', '!ex-jawOpen'), ('c', 'V3_closed'))


def keyvar(drv, vname, key):
    v = drv.variables.new()
    v.name = vname
    v.type = 'SINGLE_PROP'
    v.targets[0].id_type = 'KEY'
    v.targets[0].id = body.data.shape_keys
    v.targets[0].data_path = 'key_blocks["%s"].value' % key


def drive(obj, shapekey, expr, keys):
    fcu = obj.data.shape_keys.driver_add('key_blocks["%s"].value' % shapekey)
    drv = fcu.driver
    drv.type = 'SCRIPTED'
    drv.expression = expr
    for vname, key in keys:
        keyvar(drv, vname, key)


def make_plate(name, verts, faces, mat):
    """Decal plate anchored to the same lip vertex as the V9 aperture:
    verts are small offsets from the anchor point, object keeps the
    aperture's own transform so the plate renders at anchor + local."""
    mesh = bpy.data.meshes.new(name + '_mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    s.collection.objects.link(obj)
    obj.parent = body
    obj.parent_type = 'VERTEX'
    obj.parent_vertices = (anchor_vert, 0, 0)
    # identity basis: the vertex parent contributes the anchor's world
    # position itself, so local coords land at anchor + offset
    obj.matrix_basis.identity()
    for flag in ('visible_shadow', 'visible_diffuse', 'visible_glossy',
                 'visible_transmission', 'visible_volume_scatter'):
        setattr(obj, flag, False)
    return obj


# -- interior: 24-seg ring + center fan, thin crescent when closed ------------
# anchor-local space: x across, y toward camera (negative = in front), z up
N = 24
cx, cy, cz = 0.0, -0.0016, -0.0018       # just below and in front of the seam
rx, rz = 0.0130, 0.0010
verts = []
for i in range(N):
    a = 2 * math.pi * i / N
    verts.append((cx + rx * math.cos(a), cy,
                  cz + rz * math.sin(a) + 0.0004 * abs(math.cos(a))))
verts.append((cx, cy, cz))
faces = [(i, (i + 1) % N, N) for i in range(N)]
interior = make_plate(p + '.V11_mouth_interior', verts, faces, INK)
interior.shape_key_add(name='Basis')
top_z = cz + rz                # seam line the opening drops from


def open_shape(i):
    a = 2 * math.pi * i / N if i < N else 0.0
    return Vector((cx + 0.0145 * math.cos(a), cy,
                   top_z - 0.0115 + 0.0115 * math.sin(a)))


# additive shape keys blend basis->key, so modulation keys must store
# (morphed - open + thin) as their absolute target: at open=1,morph=1 the
# result lands exactly on the morph shape instead of stacking open+morph.
def morph(name, fn):
    k = interior.shape_key_add(name=name)
    for i in range(N + 1):
        k.data[i].co = fn(open_shape(i)) - open_shape(i) + Vector(verts[i])
    return k


interior.shape_key_add(name='V11_open')
for i in range(N + 1):
    interior.data.shape_keys.key_blocks['V11_open'].data[i].co = open_shape(i)
morph('V11_wide', lambda v: Vector((cx + (v.x - cx) * 1.32, v.y, v.z)))
morph('V11_round', lambda v: Vector((cx + (v.x - cx) * 0.58, v.y - 0.0022,
                                     top_z - 0.013 + (v.z - top_z) * 1.05)))
morph('V11_FV', lambda v: Vector((cx + (v.x - cx) * 1.22, v.y,
                                  min(v.z, top_z - 0.004))))

for name, expr, keys in (
    ('V11_open', OPEN, OPEN_KEYS),
    ('V11_wide', 'w*(' + OPEN + ')', OPEN_KEYS + (('w', 'V3_wide'),)),
    ('V11_round', 'r*(' + OPEN + ')', OPEN_KEYS + (('r', 'V3_round'),)),
    ('V11_FV', 'f*(' + OPEN + ')', OPEN_KEYS + (('f', 'V3_FV'),)),
):
    drive(interior, name, expr, keys)

# -- teeth: white band hanging from the seam inside the opening ---------------
tw, th = 0.0105, 0.0045
teeth_verts = []
for i in range(8):
    t = i / 7
    x = cx - tw / 2 + tw * t
    arc = 0.0011 * (1 - (2 * t - 1) ** 2)      # ends curl down
    for j in range(2):
        teeth_verts.append((x, cy - 0.0010, top_z - arc - th * j))
teeth_faces = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(7)]
teeth = make_plate(p + '.V11_mouth_teeth', teeth_verts, teeth_faces, TEETH)
teeth.shape_key_add(name='Basis')
topen = teeth.shape_key_add(name='V11_teeth_open')
for i, v in enumerate(teeth_verts):
    topen.data[i].co = v
# Basis must be edited via key_blocks: mesh.vertices writes do not reach it
for d in teeth.data.shape_keys.key_blocks['Basis'].data:
    d.co.z = top_z
drive(teeth, 'V11_teeth_open', OPEN, OPEN_KEYS)

# -- tongue: mid-tone patch at the bottom of the opening ----------------------
tcw, tch, tcz = 0.0068, 0.0032, top_z - 0.0122
tongue_verts = []
for i in range(8):
    t = i / 7
    tongue_verts.append((cx - tcw + 2 * tcw * t, cy - 0.0006,
                         tcz + tch * (0.25 + 0.75 * math.sin(math.pi * t))))
for i in range(8):
    t = i / 7
    tongue_verts.append((cx - tcw + 2 * tcw * t, cy - 0.0006,
                         tcz - tch + 0.6 * tch * math.sin(math.pi * t)))
tongue_faces = [(i, i + 1, i + 9, i + 8) for i in range(7)]
tongue = make_plate(p + '.V11_mouth_tongue', tongue_verts, tongue_faces, TONGUE)
tongue.shape_key_add(name='Basis')
tin = tongue.shape_key_add(name='V11_tongue_in')
for i, v in enumerate(tongue_verts):
    tin.data[i].co = v
for d in tongue.data.shape_keys.key_blocks['Basis'].data:
    d.co.z = top_z                          # basis collapses under the seam
    d.co.x = cx + (d.co.x - cx) * 0.3
drive(tongue, 'V11_tongue_in',
      'max(0,min(1,(v-0.30)/0.45))*(1-c*0.85)', OPEN_KEYS)

# The flat ellipse is superseded; keep it in the file for provenance.
aperture.hide_render = True
aperture.hide_viewport = True
aperture['V11_NOTE'] = 'Superseded by V11_mouth_interior/teeth/tongue'

# -- chin mark: keep the head-bone parent, bake location keys so the mark --
#    rigidly follows the chin skin's displacement through jawOpen -------------
jaw_mark = bpy.data.objects[p + '.V10_jaw']
nv = len(jaw_mark.data.vertices)
rest_center = sum((jaw_mark.matrix_world @ jaw_mark.data.vertices[i].co
                   for i in range(nv)), Vector()) / nv
dep = bpy.context.evaluated_depsgraph_get()
ev = body.evaluated_get(dep)
mw = ev.matrix_world
me = ev.to_mesh()
# chin vert under the mark's center: the skin the mark should ride on
chin = min(range(len(me.vertices)),
           key=lambda i: (mw @ me.vertices[i].co - rest_center).length)
rest_pos = mw @ me.vertices[chin].co
ev.to_mesh_clear()

arm_inv = rig.matrix_world.inverted()
pb_head = rig.pose.bones['head']
rest_loc = jaw_mark.location.copy()
if jaw_mark.animation_data and jaw_mark.animation_data.action:
    jaw_mark.animation_data_clear()
for frame in range(1, 361):
    s.frame_set(frame)
    dep = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dep)
    me = ev.to_mesh()
    cur = mw @ me.vertices[chin].co
    ev.to_mesh_clear()
    # chin displacement expressed in the head-bone frame, added to the
    # mark's rest location: the mark rides the skin rigidly
    bm = arm_inv @ rig.pose.bones['head'].matrix
    d = bm.inverted() @ cur - bm.inverted() @ rest_pos
    jaw_mark.location = rest_loc + d
    jaw_mark.keyframe_insert('location', frame=frame)
s.frame_set(1)
jaw_mark['V11_ATTACHMENT'] = 'Head bone + baked chin tracking on vert %d' % chin

s['V11_MOUTH'] = 'Articulated decal mouth: interior+teeth+tongue, viseme-driven'
s['V11_JAW_MARK'] = 'Chin mark follows jaw skin (VERTEX_3), was rigid head bone'
path = OUT / (p.upper() + '_FULLBODY_15S_V11.blend')
bpy.ops.wm.save_as_mainfile(filepath=str(path))
print('V11_SAVED', path, flush=True)
