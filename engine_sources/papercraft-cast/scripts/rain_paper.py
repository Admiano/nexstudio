"""Papercraft render of the Rain rig — paperize its own materials, decimate
into facets, studio bust framing."""

import bpy, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]
DECIMATE = float(argv[1]) if len(argv) > 1 else 0.15
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KRAFT = os.path.join(ROOT, "assets", "kraft") + "/"

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "assets", "rain", "rain_v3.2.blend"))

img_col = bpy.data.images.load(KRAFT + "Paper001_1K-JPG_Color.jpg")
img_nrm = bpy.data.images.load(KRAFT + "Paper001_1K-JPG_NormalGL.jpg")
img_nrm.colorspace_settings.name = 'Non-Color'

HIDE = {'GEO-rain-body_nomask', 'GEO-rain-eyes_viewport', 'GEO-rain-eye_cornea'}
for ob in bpy.data.objects:
    if ob.name in HIDE or ob.type == 'GPENCIL' or ob.type == 'GREASEPENCIL':
        ob.hide_render = True
        ob.hide_set(True)


def paperize(mat, ao=True):
    if not mat or not mat.use_nodes:
        return
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not bsdf:
        return
    bsdf.inputs['Roughness'].default_value = 0.93
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = 0.2
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = img_col
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (4, 4, 4)
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], tex.inputs['Vector'])
    kmix = nt.nodes.new('ShaderNodeMixRGB'); kmix.blend_type = 'MULTIPLY'
    kmix.inputs[0].default_value = 0.55
    kmix.inputs[2].default_value = (1.0, 0.97, 0.92, 1)   # warm it slightly
    src_link = bsdf.inputs['Base Color'].links[0].from_socket if bsdf.inputs['Base Color'].links else None
    if src_link:
        nt.links.new(src_link, kmix.inputs[1])
        mix2 = nt.nodes.new('ShaderNodeMixRGB'); mix2.blend_type = 'MULTIPLY'
        mix2.inputs[0].default_value = 0.35
        nt.links.new(kmix.outputs['Color'], mix2.inputs[1])
        nt.links.new(tex.outputs['Color'], mix2.inputs[2])
        feed = mix2
        if mat and 'skin' in mat.name.lower() or (mat and 'body' in mat.name.lower()):
            warm = nt.nodes.new('ShaderNodeMixRGB'); warm.blend_type = 'MULTIPLY'
            warm.inputs[0].default_value = 0.35
            warm.inputs[2].default_value = (0.94, 0.78, 0.62, 1)
            nt.links.new(feed.outputs['Color'], warm.inputs[1])
            feed = warm
    else:
        nt.links.new(bsdf.inputs['Base Color'].default_value and tex.outputs['Color'] or tex.outputs['Color'], kmix.inputs[1])
        feed = kmix
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.34, 0.30, 0.26, 1)
    ramp.color_ramp.elements[1].position = 0.4
    ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    mix = nt.nodes.new('ShaderNodeMixRGB'); mix.blend_type = 'MULTIPLY'; mix.inputs[0].default_value = 1.0
    nt.links.new(feed.outputs['Color'], mix.inputs[1])
    nt.links.new(geo.outputs['Pointiness'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], mix.inputs[2])
    if ao:
        aon = nt.nodes.new('ShaderNodeAmbientOcclusion')
        aon.inputs['Distance'].default_value = 0.012
        aon.inputs['Color'].default_value = (0.62, 0.55, 0.48, 1)
        aomix = nt.nodes.new('ShaderNodeMixRGB'); aomix.blend_type = 'MULTIPLY'
        aomix.inputs[0].default_value = 1.0
        aomix.inputs[2].default_value = (1, 1, 1, 1)
        nt.links.new(mix.outputs['Color'], aomix.inputs[1])
        nt.links.new(aon.outputs['Color'], aomix.inputs[2])
        nt.links.new(aomix.outputs['Color'], bsdf.inputs['Base Color'])
    else:
        nt.links.new(mix.outputs['Color'], bsdf.inputs['Base Color'])
    ntex = nt.nodes.new('ShaderNodeTexImage'); ntex.image = img_nrm
    nt.links.new(mp.outputs['Vector'], ntex.inputs['Vector'])
    nmap = nt.nodes.new('ShaderNodeNormalMap'); nmap.inputs['Strength'].default_value = 0.5
    nt.links.new(ntex.outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])


meshes = [o for o in bpy.data.objects if o.type == 'MESH' and not ob.hide_render]
targets = []
for ob in bpy.data.objects:
    if ob.type != 'MESH' or ob.hide_render:
        continue
    targets.append(ob)
    for p in ob.data.polygons:
        p.use_smooth = False
    for m in list(ob.modifiers):
        if m.type == 'SUBSURF':
            ob.modifiers.remove(m)
    dec = ob.modifiers.new("facet", 'DECIMATE')
    dec.decimate_type = 'COLLAPSE'
    if 'head' in ob.name or ob.name == 'GEO-rain-body':
        dec.ratio = max(DECIMATE, 0.45)
    elif 'eyes' in ob.name or 'gums' in ob.name:
        dec.ratio = 0.7
    else:
        dec.ratio = DECIMATE
    tri = ob.modifiers.new("tri", 'TRIANGULATE')
    if ob.name != 'GEO-rain-body':
        sol = ob.modifiers.new("paper_edge", 'SOLIDIFY')
        sol.thickness = 0.0025
        sol.offset = -0.6
        sol.use_rim = True
        sol.thickness_clamp = 0.35
    is_eye = ('eyes' in ob.name or 'cornea' in ob.name)
    if 'eyes' in ob.name:
        dark = bpy.data.materials.new("paper_eye")
        dark.use_nodes = True
        dn = dark.node_tree
        dn.nodes.clear()
        em = dn.nodes.new('ShaderNodeEmission')
        em.inputs['Color'].default_value = (0.035, 0.028, 0.024, 1)
        em.inputs['Strength'].default_value = 0.55
        outn = dn.nodes.new('ShaderNodeOutputMaterial')
        dn.links.new(em.outputs[0], outn.inputs[0])
        for i in range(len(ob.data.materials)):
            ob.data.materials[i] = dark
        if not len(ob.data.materials):
            ob.data.materials.append(dark)
    else:
        for m in ob.data.materials:
            paperize(m, ao=('cornea' not in ob.name and 'gums' not in ob.name))

# drop arms from T-pose: rotate arm-region verts around shoulder pivots
import math
from mathutils import Matrix
body = bpy.data.objects.get('GEO-rain-body')
if body:
    for sgn in (-1, 1):
        piv = Vector((sgn * 0.13, 0.0, 1.30))
        R = Matrix.Rotation(math.radians(sgn * 62), 4, 'Y')
        for v in body.data.vertices:
            w = body.matrix_world @ v.co
            if abs(w.x) > 0.16 and 1.02 < w.z < 1.46:
                blend = min(1.0, (abs(w.x) - 0.16) / 0.10)   # soften near shoulder
                Ri = Matrix.Rotation(math.radians(sgn * 62 * blend), 4, 'Y')
                w2 = piv + Ri @ (w - piv)
                v.co = body.matrix_world.inverted() @ w2
    print("arms dropped")

bpy.context.view_layer.update()
bvs = []
for ob in targets:
    bvs += [ob.matrix_world @ v.co for v in ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh().vertices]
lo = Vector((min(v.x for v in bvs), min(v.y for v in bvs), min(v.z for v in bvs)))
hi = Vector((max(v.x for v in bvs), max(v.y for v in bvs), max(v.z for v in bvs)))
cx, cy = (lo.x + hi.x) / 2, (lo.y + hi.y) / 2
top = hi.z

def plane(name, loc, size, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc, rotation=rot)
    return bpy.context.object

plane("Floor", (cx, cy + 4, lo.z - 0.02), 40)
wall = plane("Wall", (cx, cy + 2.0, 1.0), 25, rot=(1.5708, 0, 0))
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
    d = (Vector((cx, cy, 1.45)) - lo2.location).to_track_quat('-Z', 'Y')
    lo2.rotation_euler = d.to_euler()

area("Key", (cx - 1.0, cy - 1.6, top + 0.5), 90, 1.1, (1.0, 0.92, 0.82))
area("Fill", (cx + 1.4, cy - 1.0, 1.45), 22, 1.0, (0.88, 0.92, 1.0))
area("Rim", (cx + 0.5, cy + 1.3, top + 0.4), 70, 0.9, (1.0, 0.97, 0.93))
bpy.context.scene.world = bpy.data.worlds.new("w")
bpy.context.scene.world.use_nodes = True
bg = bpy.context.scene.world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.90, 0.89, 0.86, 1)
bg.inputs[1].default_value = 0.3

bpy.ops.object.camera_add()
cam = bpy.context.object
cam.data.lens = 74
target = Vector((cx, cy, top - 0.285))
cam.location = (cx, cy - 1.10, top - 0.22)
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 64
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 4
sc.view_settings.exposure = 0.0
sc.render.resolution_x = 720
sc.render.resolution_y = 900
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("WROTE", OUT)
