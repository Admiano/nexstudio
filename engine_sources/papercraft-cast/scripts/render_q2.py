"""Papercraft v2 — Quaternius base rendered as folded kraft paper.
Per-material paper tints, real kraft texture+bump, Solidify edge thickness,
stronger crease shading, bust framing."""

import bpy, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
GLB, OUT = argv[0], argv[1]
KRAFT = "/home/ubuntu/paper-lab/assets/paper001/"
A = "/home/ubuntu/paper-lab/assets/"

# palette: material-name fragment -> (tint rgb, kraft-strength)
PAL = {
    'Skin':       ((0.80, 0.60, 0.44), 0.55),   # kraft tan
    'Skin_Darker':((0.62, 0.45, 0.34), 0.55),
    'Hair':       ((0.16, 0.19, 0.28), 0.45),   # navy paper
    'Eyebrows':   ((0.20, 0.16, 0.12), 0.35),
    'Eye':        ((0.10, 0.09, 0.08), 0.25),   # near-black almond
    'LightBrown': ((0.72, 0.60, 0.42), 0.55),   # khaki uniform
    'LightBlue':  ((0.42, 0.50, 0.58), 0.50),
    'Shirt':      ((0.72, 0.60, 0.42), 0.55),
    'Pants':      ((0.45, 0.44, 0.40), 0.50),
    'White':      ((0.93, 0.91, 0.86), 0.5),
    'Red_Dark':   ((0.55, 0.22, 0.16), 0.5),
    'Socks':      ((0.85, 0.82, 0.76), 0.5),
}
DEFAULT = ((0.80, 0.72, 0.60), 0.5)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)

img_col = bpy.data.images.load(KRAFT + "Paper001_1K-JPG_Color.jpg")
img_nrm = bpy.data.images.load(KRAFT + "Paper001_1K-JPG_NormalGL.jpg")
img_nrm.colorspace_settings.name = 'Non-Color'


def kraftize(mat, tint, kstr):
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not bsdf:
        return
    bsdf.inputs['Roughness'].default_value = 0.95
    bsdf.inputs['Specular IOR Level'].default_value = 0.18
    # kraft texture * tint
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img_col
    tex.extension = 'REPEAT'
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (3, 3, 3)
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], tex.inputs['Vector'])
    tintn = nt.nodes.new('ShaderNodeMixRGB'); tintn.blend_type = 'MULTIPLY'
    tintn.inputs[0].default_value = 1.0
    tintn.inputs[1].default_value = (*tint, 1.0)
    nt.links.new(tex.outputs['Color'], tintn.inputs[2])
    kraftmix = tintn
    # crease darkening — deeper + tighter than v1
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.42, 0.38, 0.34, 1)
    ramp.color_ramp.elements[1].position = 0.38
    ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    mix = nt.nodes.new('ShaderNodeMixRGB'); mix.blend_type = 'MULTIPLY'; mix.inputs[0].default_value = 1.0
    nt.links.new(kraftmix.outputs['Color'], mix.inputs[1])
    nt.links.new(geo.outputs['Pointiness'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], mix.inputs[2])
    nt.links.new(mix.outputs['Color'], bsdf.inputs['Base Color'])
    # paper normal map
    ntex = nt.nodes.new('ShaderNodeTexImage'); ntex.image = img_nrm
    nt.links.new(mp.outputs['Vector'], ntex.inputs['Vector'])
    nmap = nt.nodes.new('ShaderNodeNormalMap'); nmap.inputs['Strength'].default_value = 0.55
    nt.links.new(ntex.outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])


meshes = [o for o in bpy.data.objects if o.type == 'MESH' and 'Icosphere' not in o.name]
import random, math
random.seed(7)

def split_by_material(ob):
    """Separate a mesh into per-material objects, return the new pieces."""
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='MATERIAL')
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.select_set(False)
    return [o for o in bpy.context.selected_objects if o.type == 'MESH']

pieces = []
for ob in list(meshes):
    pieces += split_by_material(ob)

head_pieces = [o for o in pieces if 'Head' in o.name]
for hp in head_pieces:
    for mi, m in enumerate(hp.data.materials):
        if not m:
            continue
        if 'Eye' in m.name and 'brow' not in m.name.lower():
            # squash the blocky eye into an almond in WORLD space, then map back
            fv = sorted({v for p in hp.data.polygons if p.material_index == mi for v in p.vertices})
            if fv:
                ws = [hp.matrix_world @ hp.data.vertices[v].co for v in fv]
                cen = Vector((sum(v.x for v in ws)/len(ws),
                              sum(v.y for v in ws)/len(ws),
                              sum(v.z for v in ws)/len(ws)))
                inv = hp.matrix_world.inverted()
                for vi, w in zip(fv, ws):
                    dv = w - cen
                    w.x = cen.x + dv.x * 1.15
                    w.z = cen.z + dv.z * 0.55
                    w.y = cen.y + dv.y - 0.004
                    hp.data.vertices[vi].co = inv @ w
        if 'Eyebrow' in m.name:
            fv = sorted({v for p in hp.data.polygons if p.material_index == mi for v in p.vertices})
            if fv:
                ws = [hp.matrix_world @ hp.data.vertices[v].co for v in fv]
                cen = Vector((sum(v.x for v in ws)/len(ws),
                              sum(v.y for v in ws)/len(ws),
                              sum(v.z for v in ws)/len(ws)))
                inv = hp.matrix_world.inverted()
                for vi, w in zip(fv, ws):
                    dv = w - cen
                    w.x = cen.x + dv.x * 1.05
                    w.z = cen.z + dv.z * 0.45
                    hp.data.vertices[vi].co = inv @ w
for ob in pieces:
    for p in ob.data.polygons:
        p.use_smooth = False
    # imperfect assembly: each paper piece slightly rotated around its own center
    ob.rotation_euler = (math.radians(random.uniform(-0.9, 0.9)),
                         math.radians(random.uniform(-0.9, 0.9)),
                         math.radians(random.uniform(-0.6, 0.6)))
    for m in ob.data.materials:
        if not m:
            continue
        tint, kstr = next((PAL[k] for k in PAL if k in m.name), DEFAULT)
        kraftize(m, tint, kstr)
meshes = pieces

for ob in [o for o in bpy.data.objects if 'Icosphere' in o.name]:
    bpy.data.objects.remove(ob)

# locate eye material faces -> place dark almond paper eyes
head = next((o for o in meshes if 'Head' in o.name), None)
eye_spots = []
if head:
    for i, m in enumerate(head.data.materials):
        if m and 'Eye' in m.name:
            vs = [head.matrix_world @ p.center for p in head.data.polygons
                  if p.material_index == i]
            if vs:
                # cluster into left/right by x
                vs.sort(key=lambda v: v.x)
                mid = vs[len(vs)//2].x
                left = [v for v in vs if v.x < mid]; right = [v for v in vs if v.x >= mid]
                for grp in (left, right):
                    if grp:
                        c = Vector((sum(v.x for v in grp)/len(grp),
                                    sum(v.y for v in grp)/len(grp),
                                    sum(v.z for v in grp)/len(grp)))
                        eye_spots.append(c)

eye_mat = bpy.data.materials.new("eye_paper"); eye_mat.use_nodes = True
eb = next(n for n in eye_mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
eb.inputs['Base Color'].default_value = (0.07, 0.055, 0.045, 1)
eb.inputs['Roughness'].default_value = 0.9
for i, c in enumerate(eye_spots):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=12, ring_count=8)
    o = bpy.context.object; o.name = f"EyeAlmond{i}"
    o.scale = (0.032, 0.006, 0.020)
    o.location = (c.x, c.y - 0.004, c.z)
    for p in o.data.polygons: p.use_smooth = True
    o.data.materials.append(eye_mat)
    print(f"almond{i} at {tuple(round(x,3) for x in c)}")

bpy.context.view_layer.update()
bvs = []
for ob in meshes:
    bvs += [ob.matrix_world @ v.co for v in ob.data.vertices]
lo = Vector((min(v.x for v in bvs), min(v.y for v in bvs), min(v.z for v in bvs)))
hi = Vector((max(v.x for v in bvs), max(v.y for v in bvs), max(v.z for v in bvs)))
cx, cy = (lo.x + hi.x) / 2, (lo.y + hi.y) / 2
top = hi.z
head_z = top - 0.25 * (top - lo.z)

def plane(name, loc, size, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc, rotation=rot)
    return bpy.context.object

plane("Floor", (cx, cy + 4, lo.z - 0.02), 40)
wall = plane("Wall", (cx, cy + 2.6, 1.0), 30, rot=(1.5708, 0, 0))
mat = bpy.data.materials.new("wall"); mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
bsdf.inputs['Roughness'].default_value = 1.0
tc = nt.nodes.new('ShaderNodeTexCoord')
sep = nt.nodes.new('ShaderNodeSeparateXYZ')
ramp = nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color = (0.66, 0.64, 0.60, 1)
ramp.color_ramp.elements[1].color = (0.96, 0.94, 0.91, 1)
nt.links.new(tc.outputs['Generated'], sep.inputs[0])
nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
wall.data.materials.append(mat)

def area(name, loc, energy, size, color):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.shape = 'DISK'
    ld.size = size; ld.color = color
    lo2 = bpy.data.objects.new(name, ld); bpy.context.collection.objects.link(lo2)
    lo2.location = loc
    d = (Vector((cx, cy, head_z)) - lo2.location).to_track_quat('-Z', 'Y')
    lo2.rotation_euler = d.to_euler()

area("Key", (cx - 1.2, cy - 1.9, top + 0.7), 120, 1.3, (1.0, 0.92, 0.82))
area("Fill", (cx + 1.6, cy - 1.2, head_z), 30, 1.2, (0.88, 0.92, 1.0))
area("Rim", (cx + 0.5, cy + 1.5, top + 0.6), 95, 1.0, (1.0, 0.97, 0.93))
bpy.context.scene.world = bpy.data.worlds.new("w")
bpy.context.scene.world.use_nodes = True
bg = bpy.context.scene.world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.90, 0.89, 0.86, 1)
bg.inputs[1].default_value = 0.32

if head_pieces:
    hvs = [v.co for o in head_pieces for v in o.data.vertices]
    hvs_w = [o.matrix_world @ v.co for o in head_pieces for v in o.data.vertices]
    ffront = min(v.y for v in hvs_w)
    front_vs = [v for v in hvs_w if v.y < ffront + 0.06]
    nose_z = sorted(v.z for v in front_vs)[int(len(front_vs)*0.5)]
    lip_z = nose_z - 0.06
    lip_mat = bpy.data.materials.new("lip"); lip_mat.use_nodes = True
    lb = next(n for n in lip_mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    lb.inputs['Base Color'].default_value = (0.62, 0.42, 0.38, 1)
    lb.inputs['Roughness'].default_value = 0.9
    bpy.ops.mesh.primitive_cube_add(location=(cx, ffront - 0.006, lip_z))
    lip = bpy.context.object; lip.name = "LipPlate"
    lip.scale = (0.045, 0.004, 0.010)
    lip.rotation_euler[0] = -0.1
    for p in lip.data.polygons: p.use_smooth = False
    lip.data.materials.append(lip_mat)

bpy.ops.object.camera_add()
cam = bpy.context.object
cam.data.lens = 85
target = Vector((cx, cy, top - 0.44))
cam.location = (cx, cy - 2.2, top - 0.40)
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 64
sc.view_settings.exposure = -0.1
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 4
sc.render.resolution_x = 720
sc.render.resolution_y = 900
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("WROTE", OUT)
