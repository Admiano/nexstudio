"""Full-body papercraft render of a generated GLB.
Usage: blender -b --python render_fullbody.py -- IN.glb CONCEPT.png OUT.png DECIMATE"""
import bpy, sys, os
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def rp(p):
    return p if os.path.isabs(p) else os.path.join(ROOT, p)
GLB, CONCEPT, OUT = rp(argv[0]), rp(argv[1]), rp(argv[2])
DEC = float(argv[3]) if len(argv) > 3 else 0.05
# optional figure box inside the concept image (u0 v0 u1 v1)
UBOX = [float(x) for x in argv[4:8]] if len(argv) >= 8 else None
KRAFT = os.path.join(ROOT, "assets", "kraft") + "/"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for ob in meshes:
    for p in ob.data.polygons: p.use_smooth = False

vs = [ob.matrix_world @ v.co for ob in meshes for v in ob.data.vertices]
lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
c0 = (lo + hi) / 2
sc0 = 1.75 / (hi.z - lo.z)
for ob in meshes:
    ob.scale = (sc0,)*3
    ob.location = (-c0.x*sc0, -c0.y*sc0, -lo.z*sc0)
bpy.context.view_layer.update()

img_col = bpy.data.images.load(KRAFT + "Paper001_1K-JPG_Color.jpg")
img_nrm = bpy.data.images.load(KRAFT + "Paper001_1K-JPG_NormalGL.jpg")
img_nrm.colorspace_settings.name = 'Non-Color'
img_con = bpy.data.images.load(CONCEPT)

def paperize(mat):
    if not mat or not mat.use_nodes: return
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not bsdf: return
    bsdf.inputs['Roughness'].default_value = 0.93
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = 0.15
    tc = nt.nodes.new('ShaderNodeTexCoord')
    ptex = nt.nodes.new('ShaderNodeTexImage'); ptex.image = img_con
    uvn = nt.nodes.new('ShaderNodeUVMap'); uvn.uv_map = "projUV"
    if UBOX:
        um = nt.nodes.new('ShaderNodeMapping')
        um.vector_type = 'POINT'
        um.inputs['Location'].default_value = (UBOX[0], UBOX[1], 0)
        um.inputs['Scale'].default_value = (UBOX[2]-UBOX[0], UBOX[3]-UBOX[1], 1)
        nt.links.new(uvn.outputs['UV'], um.inputs['Vector'])
        nt.links.new(um.outputs['Vector'], ptex.inputs['Vector'])
    else:
        nt.links.new(uvn.outputs['UV'], ptex.inputs['Vector'])
    ktex = nt.nodes.new('ShaderNodeTexImage'); ktex.image = img_col
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (2,2,2)
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], ktex.inputs['Vector'])
    # contrast S-curve + saturation on the projected concept (kills baked softness)
    hs = nt.nodes.new('ShaderNodeHueSaturation')
    hs.inputs['Saturation'].default_value = 1.14
    hs.inputs['Value'].default_value = 1.02
    nt.links.new(ptex.outputs['Color'], hs.inputs['Color'])
    scurve = nt.nodes.new('ShaderNodeRGBCurve')
    cc = scurve.mapping.curves[3]
    cc.points.new(0.28, 0.18); cc.points.new(0.72, 0.82)
    scurve.mapping.update()
    nt.links.new(hs.outputs['Color'], scurve.inputs['Color'])
    m1 = nt.nodes.new('ShaderNodeMixRGB'); m1.blend_type='MULTIPLY'; m1.inputs[0].default_value=0.7
    nt.links.new(scurve.outputs['Color'], m1.inputs[1])
    nt.links.new(ktex.outputs['Color'], m1.inputs[2])
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (0.38,0.34,0.30,1); ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[1].color = (1,1,1,1);          ramp.color_ramp.elements[1].position = 0.45
    m2 = nt.nodes.new('ShaderNodeMixRGB'); m2.blend_type='MULTIPLY'; m2.inputs[0].default_value=1.0
    nt.links.new(m1.outputs['Color'], m2.inputs[1])
    nt.links.new(geo.outputs['Pointiness'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], m2.inputs[2])
    aon = nt.nodes.new('ShaderNodeAmbientOcclusion')
    aon.inputs['Distance'].default_value = 0.028
    aon.inputs['Color'].default_value = (0.52,0.45,0.38,1)
    m3 = nt.nodes.new('ShaderNodeMixRGB'); m3.blend_type='MULTIPLY'; m3.inputs[0].default_value=1.0
    nt.links.new(m2.outputs['Color'], m3.inputs[1])
    nt.links.new(aon.outputs['Color'], m3.inputs[2])
    # darken the rear third (back plate / silhouette rims) toward darker kraft
    sep2 = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep2.inputs[0])
    mp2 = nt.nodes.new('ShaderNodeMapRange')
    mp2.inputs['From Min'].default_value = -0.10
    mp2.inputs['From Max'].default_value = 0.30
    mp2.inputs['To Min'].default_value = 0.0
    mp2.inputs['To Max'].default_value = 1.0
    mp2.clamp = True
    nt.links.new(sep2.outputs['Y'], mp2.inputs['Value'])
    bk = nt.nodes.new('ShaderNodeMixRGB'); bk.blend_type='MULTIPLY'
    bk.inputs[2].default_value = (0.42,0.36,0.28,1)
    nt.links.new(mp2.outputs['Result'], bk.inputs[0])
    nt.links.new(m3.outputs['Color'], bk.inputs[1])
    nt.links.new(bk.outputs['Color'], bsdf.inputs['Base Color'])
    ntex = nt.nodes.new('ShaderNodeTexImage'); ntex.image = img_nrm
    nt.links.new(mp.outputs['Vector'], ntex.inputs['Vector'])
    nmap = nt.nodes.new('ShaderNodeNormalMap'); nmap.inputs['Strength'].default_value = 0.65
    nt.links.new(ntex.outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])

# strip ground/backdrop slabs: faces whose world normal is ~±Z
import bmesh
for ob in meshes:
    bm = bmesh.new(); bm.from_mesh(ob.data)
    mw3 = ob.matrix_world.to_3x3()
    kill = []
    for f in bm.faces:
        c = f.calc_center_median()
        if not (-0.27 < c.z < -0.19):
            continue
        if abs((mw3 @ f.normal).z) > 0.9 or abs(c.x) > 0.45 or abs(c.y) > 0.45:
            kill.append(f)
    for f in kill: bm.faces.remove(f)
    bm.to_mesh(ob.data); bm.free()
    print("stripped", len(kill), "slab faces")
for ob in meshes:
    dec = ob.modifiers.new("facet", 'DECIMATE'); dec.decimate_type='COLLAPSE'; dec.ratio = DEC
    uvp = ob.modifiers.new("proj", 'UV_PROJECT')
    if not ob.data.materials:
        m = bpy.data.materials.new("paper"); m.use_nodes=True
        ob.data.materials.append(m)
    for m in ob.data.materials: paperize(m)

bpy.context.view_layer.update()
bvs = []
dg = bpy.context.evaluated_depsgraph_get()
for ob in meshes:
    bvs += [ob.matrix_world @ v.co for v in ob.evaluated_get(dg).to_mesh().vertices]
lo = Vector((min(v.x for v in bvs), min(v.y for v in bvs), min(v.z for v in bvs)))
hi = Vector((max(v.x for v in bvs), max(v.y for v in bvs), max(v.z for v in bvs)))
cx, cy = (lo.x+hi.x)/2, (lo.y+hi.y)/2
top, bot = hi.z, lo.z
mid = (top+bot)/2

def plane(name, loc, size, rot=(0,0,0)):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc, rotation=rot)
    return bpy.context.object
floor = plane("Floor", (cx, cy+3, bot-0.005), 40)
wall = plane("Wall", (cx, cy+2.5, mid+1.0), 40, rot=(1.5708,0,0))
for pl in (floor, wall):
    mat = bpy.data.materials.new("wallm"); mat.use_nodes=True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
    bsdf.inputs['Roughness'].default_value = 1.0
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (0.64,0.62,0.58,1)
    ramp.color_ramp.elements[1].color = (0.96,0.94,0.91,1)
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    pl.data.materials.append(mat)

def area(name, loc, energy, size, color):
    ld = bpy.data.lights.new(name,'AREA'); ld.energy=energy; ld.shape='DISK'; ld.size=size; ld.color=color
    o = bpy.data.objects.new(name, ld); bpy.context.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector((cx,cy,mid+0.2))-o.location).to_track_quat('-Z','Y').to_euler()
area("Key",(cx-1.2,cy-1.8,top+0.3),120,1.4,(1.0,0.92,0.82))
area("Fill",(cx+1.5,cy-1.2,mid),30,1.2,(0.88,0.92,1.0))
area("Rim",(cx+0.4,cy+1.4,top+0.3),38,0.7,(1.0,0.95,0.90))
bpy.context.scene.world = bpy.data.worlds.new("w"); bpy.context.scene.world.use_nodes=True
bgn = bpy.context.scene.world.node_tree.nodes['Background']
bgn.inputs[0].default_value = (0.90,0.89,0.86,1); bgn.inputs[1].default_value = 0.3

# square-ish ortho projector covering figure from front
bpy.ops.object.camera_add()
projcam = bpy.context.object
projcam.data.type = 'ORTHO'
projcam.data.ortho_scale = (hi.z-lo.z) * 1.02
projcam.location = (cx, lo.y - 3.0, mid)
projcam.rotation_euler = (Vector((cx,cy,mid)) - projcam.location).to_track_quat('-Z','Y').to_euler()
for ob in meshes:
    if not ob.data.uv_layers:
        ob.data.uv_layers.new(name="projUV")
    uvp = ob.modifiers.get("proj")
    uvp.uv_layer = "projUV"
    uvp.projector_count = 1
    uvp.projectors[0].object = projcam
    uvp.aspect_x = (hi.z-lo.z)/(hi.x-lo.x)
    uvp.aspect_y = 1.0

bpy.ops.object.camera_add()
cam = bpy.context.object; cam.data.lens = 62
target = Vector((cx, cy, mid+0.02))
cam.location = (cx, cy-3.4, mid+0.12)
cam.rotation_euler = (target-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.context.scene.camera = cam

sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples=96; sc.cycles.use_denoising=True; sc.cycles.max_bounces=4
sc.render.resolution_x=720; sc.render.resolution_y=1100
sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("WROTE", OUT)
