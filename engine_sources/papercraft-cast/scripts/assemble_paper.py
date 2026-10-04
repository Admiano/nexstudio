import bpy, sys, os
from mathutils import Vector

A = "/home/ubuntu/paper-lab/assets"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT   = argv[0] if len(argv) > 0 else "/tmp/assembled.png"
HAIR  = argv[1] if len(argv) > 1 else "elvscurly_bob1.obj"
SKIN  = argv[2] if len(argv) > 2 else "young_lightskinned_female_diffuse.png"
BODY  = argv[3] if len(argv) > 3 else "female1605.obj"
GAR   = argv[4] if len(argv) > 4 else "Worn_out_sweater.obj"
GTEX  = argv[5] if len(argv) > 5 else "Worn_out_sweater_diffuse.png"
HCOL  = float(argv[6]) if len(argv) > 6 else 0.28  # hair brightness
HTEX  = argv[7] if len(argv) > 7 else None         # hair texture (painted strands)
HTINT = float(argv[8]) if len(argv) > 8 else None  # tint strength on hair tex

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def imp(fname):
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=os.path.join(A, fname))
    new = [o for o in bpy.data.objects if o not in before]
    return new[0] if new else None

def paper_mat(name, color=None, tex=None, rough=0.92, tint=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Roughness"].default_value = rough
    bs.inputs["Specular IOR Level"].default_value = 0.25
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 320.0
    noise.inputs["Detail"].default_value = 2.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.14
    bump.inputs["Distance"].default_value = 0.0009
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bs.inputs["Normal"])
    # crease darkening: concave folds catch darker fibre
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.72, 0.70, 0.68, 1)
    ramp.color_ramp.elements[1].position = 0.55
    ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(geo.outputs["Pointiness"], ramp.inputs["Fac"])
    mult = nt.nodes.new("ShaderNodeMixRGB")
    mult.blend_type = 'MULTIPLY'
    mult.inputs[0].default_value = 1.0
    nt.links.new(ramp.outputs["Color"], mult.inputs[2])
    if tex:
        img = nt.nodes.new("ShaderNodeTexImage")
        img.image = bpy.data.images.load(os.path.join(A, tex))
        src_out = img.outputs["Color"]
        if tint:
            tmix = nt.nodes.new("ShaderNodeMixRGB")
            tmix.blend_type = 'MULTIPLY'
            tmix.inputs[0].default_value = 1.0
            tmix.inputs[2].default_value = (*tint, 1.0)
            nt.links.new(src_out, tmix.inputs[1])
            src_out = tmix.outputs["Color"]
        nt.links.new(src_out, mult.inputs[1])
    else:
        mult.inputs[1].default_value = (*color, 1.0)
    nt.links.new(mult.outputs["Color"], bs.inputs["Base Color"])
    nt.links.new(bs.outputs["BSDF"], out.inputs["Surface"])
    return m

def setup(ob, name, color=None, tex=None, rough=0.92, tint=None):
    if not ob:
        return
    for p in ob.data.polygons:
        p.use_smooth = False
    ob.data.materials.append(paper_mat(name, color, tex, rough, tint=tint))

body  = imp(BODY);                    setup(body,  "skin",  tex=SKIN)
suit  = imp(GAR);                     setup(suit,  "cloth", tex=GTEX)
hair  = imp(HAIR)
if HTEX:
    _tint = (HTINT, HTINT*0.85, HTINT*0.72) if HTINT else None
    setup(hair, "hair", tex=HTEX, rough=0.6, tint=_tint)
else:
    setup(hair, "hair", color=(HCOL, HCOL*0.72, HCOL*0.42), rough=0.6)
eyes  = imp("low-poly.obj")
eb    = imp("eyebrow001.obj")
for ob in (body, suit, hair, eyes, eb):
    if ob:
        ob.scale = (0.2, 0.2, 0.2)        # MH assets are decimeter-scale
bpy.context.view_layer.update()

# auto-seat the hair on the head: authored offsets differ per asset
bvs0 = [body.matrix_world @ v.co for v in body.data.vertices]
head_top0 = sorted(v.z for v in bvs0)[int(len(bvs0) * 0.995)]
head_cx0 = sum(v.x for v in bvs0 if v.z > head_top0 - 0.15) / \
           max(1, sum(1 for v in bvs0 if v.z > head_top0 - 0.15))
head_front0 = min(v.y for v in bvs0)
if hair:
    hvs0 = [hair.matrix_world @ v.co for v in hair.data.vertices]
    h_z = sorted(v.z for v in hvs0)
    hair_top = h_z[int(len(h_z) * 0.98)]                # crown of the piece
    hair_cx = sum(v.x for v in hvs0) / len(hvs0)
    hair_front = min(v.y for v in hvs0)
    dz = (head_top0 + 0.035) - hair_top                 # crown sits just over scalp
    dx = head_cx0 - hair_cx
    dy = (head_front0 - 0.015) - hair_front             # front locks skim the brow
    dy = max(-0.06, min(0.06, dy))                      # clamp: styles vary
    hair.location += Vector((dx, dy, dz))
    print(f"hair shift dx={dx:.3f} dy={dy:.3f} dz={dz:.3f}")
bpy.context.view_layer.update()

# bounds: whole character
dg = bpy.context.evaluated_depsgraph_get()
allv = []
for ob in (body, suit, hair):
    ev = ob.evaluated_get(dg)
    allv += [ev.matrix_world @ v.co for v in ev.to_mesh().vertices]
    ev.to_mesh_clear()
zs = sorted(v.z for v in allv)
top_z = zs[-1]
cx = sum(v.x for v in allv) / len(allv)
cy = sum(v.y for v in allv) / len(allv)
head_z = zs[int(len(zs) * 0.985)]
chest_z = zs[int(len(zs) * 0.86)]
# aim at the face, not the garment: bust framing from head landmarks
_face_top = sorted(v.z for v in bvs0)[int(len(bvs0) * 0.995)]
target = Vector((cx, cy, _face_top - 0.34))

eye_centers = []
mouth_c = None
if eyes:
    eyes.hide_render = True
    bvs = [body.matrix_world @ v.co for v in body.data.vertices]
    # sockets measured via screen-space probes; proportional to this head:
    # z = head_top - 0.64*(head_top-chin); x = cx -0.075 / cx +0.055
    _top = sorted(v.z for v in bvs)[int(len(bvs) * 0.995)]
    _hv = [v for v in bvs if v.z > _top - 0.35]
    _fr = min(v.y for v in _hv)
    _fv = [v for v in _hv if v.y < _fr + 0.05]
    _chin = sorted(v.z for v in _fv)[int(len(_fv) * 0.10)]
    _ez = _top - 0.60 * (_top - _chin)
    for xoff in (-0.065, 0.065):
        eye_centers.append(Vector((head_cx0 + xoff, 0.0, _ez)))
    mband = [v for v in bvs if head_z - 0.16 < v.z < head_z - 0.09 and abs(v.x - cx) < 0.022]
    if mband:
        deep = max(mband, key=lambda v: v.y)
        mouth_c = Vector((deep.x, deep.y - 0.004, deep.z))
print("bbox top", round(top_z, 2), "head_z", round(head_z, 2), "c", round(cx, 2), round(cy, 2))

# seamless cyclorama: big floor + wall
bpy.ops.mesh.primitive_plane_add(size=40, location=(cx, cy + 4, -0.6))
floor = bpy.context.object
floor.name = "Floor"
floor.data.materials.append(paper_mat("set_floor", color=(0.90, 0.88, 0.85)))
bpy.ops.mesh.primitive_plane_add(size=30, location=(cx, cy + 2.6, 1.0), rotation=(1.5708, 0, 0))
wall = bpy.context.object
wall.name = "BackWall"
wmat = bpy.data.materials.new("set_wall")
wmat.use_nodes = True
ntw = wmat.node_tree
pb = ntw.nodes.get("Principled BSDF")
pb.inputs["Roughness"].default_value = 0.95
pb.inputs["Specular IOR Level"].default_value = 0.2
tex = ntw.nodes.new("ShaderNodeTexCoord")
sep = ntw.nodes.new("ShaderNodeSeparateXYZ")
ramp = ntw.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (0.62, 0.60, 0.57, 1)
ramp.color_ramp.elements[1].color = (0.95, 0.93, 0.90, 1)
ntw.links.new(tex.outputs["Generated"], sep.inputs[0])
ntw.links.new(sep.outputs["Z"], ramp.inputs[0])
ntw.links.new(ramp.outputs[0], pb.inputs["Base Color"])
wall.data.materials.append(wmat)

def area(name, loc, energy, size, color, tgt):
    d = bpy.data.lights.new(name, 'AREA')
    d.energy = energy; d.shape = 'DISK'; d.size = size; d.color = color
    o = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(tgt) - o.location).to_track_quat('-Z', 'Y').to_euler()

area("key",  (cx - 1.4, cy - 2.2, top_z + 0.6), 215, 1.4, (1.0, 0.95, 0.89), target)
area("fill", (cx + 1.7, cy - 1.3, head_z),       50, 1.6, (0.93, 0.96, 1.0), target)
area("rim",  (cx + 0.6, cy + 1.6, top_z + 0.5), 170, 1.0, (1.0, 1.0, 1.0),   target)

sc.world = bpy.data.worlds.new("W")
sc.world.use_nodes = True
bg = sc.world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.88, 0.87, 0.85, 1)
bg.inputs["Strength"].default_value = 0.35

# raycast: snap eye/lip pieces onto the actual face surface along the view ray
def surface_point(center, cam_loc):
    direction = (center - cam_loc).normalized()
    hit, loc, nrm, *_ = sc.ray_cast(bpy.context.evaluated_depsgraph_get(), cam_loc, direction)
    return (loc - direction * 0.003) if hit else center

# lip plate: flat disc just behind the mouth opening, faces -Y
mp = mouth_c if mouth_c else Vector((cx, cy - 0.055, head_z - 0.125))
bpy.ops.mesh.primitive_uv_sphere_add(segments=16, location=(mp.x, mp.y, mp.z))
lip = bpy.context.object
lip.name = "LipPlate"
lip.scale = (0.055, 0.006, 0.018)
bpy.context.view_layer.update()
lip.data.materials.append(paper_mat("lip", color=(0.55, 0.30, 0.28)))

_eye_spots = list(eye_centers)

cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
bpy.context.collection.objects.link(cam)
sc.camera = cam
cam.data.lens = 85
cam.location = Vector((cx, cy - 3.4, _face_top - 0.30))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()

if os.environ.get("PAPER_DEBUG_MARKERS"):
    from bpy_extras.object_utils import world_to_camera_view
    bpy.context.view_layer.update()
    print("PROBES name px py | world")
    probes = []
    for zi in (1.38, 1.40, 1.42, 1.44, 1.46):
        for xi in (-0.06, -0.04, -0.02, 0.04, 0.06, 0.08):
            probes.append((f"x{xi}z{zi}", Vector((xi, -0.28, zi))))
    for nm, w in probes:
        ndc = world_to_camera_view(sc, cam, w)
        print(f"PROBE {nm} {ndc.x*720:.0f} {ndc.y*900:.0f}")
    import sys; sys.exit(0)

# painted eye details: flat ovals ON the face surface (like the reference),
# placed at the local rim surface around each detected socket
_dark = "dark" in SKIN.lower() or "african" in SKIN.lower()
sclera_mat = paper_mat("sclera", color=(0.52,0.42,0.34) if _dark else (0.80,0.77,0.72), rough=0.75)
iris_mat   = paper_mat("iris",   color=(0.10, 0.07, 0.05), rough=0.4)
brow_mat   = paper_mat("brow",   color=(0.14, 0.09, 0.05), rough=0.9)
bvs_w = [body.matrix_world @ v.co for v in body.data.vertices]
face_y_all = []
for i, cc in enumerate(_eye_spots):
    near_y = sorted(v.y for v in bvs_w
                    if (v.x - cc.x) ** 2 + (v.z - cc.z) ** 2 < 0.05 ** 2)
    face_y = (min(near_y) + 0.001) if near_y else (cc.y - 0.006)
    face_y_all.append(face_y)
# seat the authored eyebrow mesh: centered between the eyes, just above them
if eb and _eye_spots:
    evs_e = [eb.matrix_world @ v.co for v in eb.data.vertices]
    e_lo = Vector((min(v.x for v in evs_e), min(v.y for v in evs_e), min(v.z for v in evs_e)))
    e_hi = Vector((max(v.x for v in evs_e), max(v.y for v in evs_e), max(v.z for v in evs_e)))
    ex_mid = sum(c.x for c in _eye_spots) / len(_eye_spots)
    ez_mid = sum(c.z for c in _eye_spots) / len(_eye_spots)
    brow_target_y = min(face_y_all) - 0.004 if face_y_all else -0.30
    eb.location += Vector((ex_mid - (e_lo.x + e_hi.x) / 2,
                           brow_target_y - (e_lo.y + e_hi.y) / 2,
                           (ez_mid + 0.022) - e_lo.z))
    for p in eb.data.polygons:
        p.use_smooth = False
    eb.data.materials.append(paper_mat("brows", tex="eyebrow001.png", rough=0.8))
    print(f"eyebrow seated at z={ez_mid + 0.022:.3f}")
for i, cc in enumerate(_eye_spots):
    face_y = face_y_all[i]
    print(f"eye{i} center={tuple(round(x,3) for x in cc)} face_y={round(face_y,3)}")
    if _dark:
        # papercraft almond: one dark painted oval, like the reference figures
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20,
            location=(cc.x, face_y, cc.z + 0.003))
        s = bpy.context.object
        s.name = f"EyeAlmond{i}"
        s.scale = (0.016, 0.003, 0.0085)
        s.data.materials.append(iris_mat)
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20,
            location=(cc.x, face_y, cc.z + 0.003))
        s = bpy.context.object
        s.name = f"EyeWhite{i}"
        s.scale = (0.015, 0.003, 0.0085)
        s.data.materials.append(sclera_mat)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16,
            location=(cc.x, face_y - 0.0025, cc.z + 0.002))
        ir = bpy.context.object
        ir.name = f"Iris{i}"
        ir.scale = (0.007, 0.0015, 0.0075)
        ir.data.materials.append(iris_mat)
    pass  # brows come from the authored mesh seated below

sc.render.engine = 'CYCLES'
sc.cycles.samples = 48
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 4
sc.render.resolution_x = 720; sc.render.resolution_y = 900
sc.render.resolution_percentage = 100
sc.render.filepath = OUT
sc.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)
print("WROTE", OUT)
