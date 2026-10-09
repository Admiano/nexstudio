import bpy, math, sys, os
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
out_png = argv[0] if argv else '/tmp/rain_gp.png'
crop_bottom_frac = float(argv[1]) if len(argv) > 1 else 0.42
EYELID_DROP = float(argv[2]) if len(argv) > 2 else -0.007
PUPIL_SCALE = float(argv[3]) if len(argv) > 3 else 2.4
HEAD_TILT   = float(argv[4]) if len(argv) > 4 else 3.0
UA_ANGLE    = float(argv[5]) if len(argv) > 5 else 80.0
PRONATE     = float(argv[6]) if len(argv) > 6 else 32.0
BROW_THIN   = float(argv[7]) if len(argv) > 7 else 0.62
LIP_W       = float(argv[8]) if len(argv) > 8 else 0.4
LIP_TICK    = float(argv[9]) if len(argv) > 9 else 1.0
LIP_SEAM_WHITE = (argv[10] == '1') if len(argv) > 10 else True
FACE_ONLY   = len(argv) > 11 and argv[11] == 'face'
HANDS_ONLY  = len(argv) > 11 and argv[11] == 'hands'
LIP_OCC     = int(argv[12]) if len(argv) > 12 else 1
SMILE_UP    = float(argv[13]) if len(argv) > 13 else 0.0075
SMILE_OUT   = float(argv[14]) if len(argv) > 14 else 0.003
LIP_TUBE    = float(argv[15]) if len(argv) > 15 else 0.0022
HAIR_GREY   = float(argv[16]) if len(argv) > 16 else 0.30
HAIR_CREASE = float(argv[17]) if len(argv) > 17 else 173.0   # deg; lower = fewer strand lines
HAND_CREASE = float(argv[18]) if len(argv) > 18 else 145.0
PONY_SWING  = float(argv[19]) if len(argv) > 19 else 55.0    # deg, ponytail toward screen-left shoulder
ELBOW_BEND  = float(argv[20]) if len(argv) > 20 else -17.0
ARM_SLIM    = float(argv[21]) if len(argv) > 21 else 0.007   # m, normal-inset of arm skin
FORE_TWIST  = float(argv[22]) if len(argv) > 22 else 0.3     # share of pronation done by forearm
WRIST_LEAN  = float(argv[23]) if len(argv) > 23 else 0.0     # deg, hand leans toward thigh off the forearm line
PALM_THIN   = float(argv[24]) if len(argv) > 24 else 0.65    # palm depth scale, rest space (1 = off)
HAND_SCALE  = float(argv[25]) if len(argv) > 25 else 0.92    # uniform whole-hand scale (1 = off)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1120
scene.render.resolution_y = 1520
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'Standard'

world = bpy.data.worlds.new('W')
world.use_nodes = True
bg = world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.945, 0.925, 0.875, 1.0)
bg.inputs[1].default_value = 1.0
scene.world = world

CHAR_PREFIX = 'GEO-'
meshes = [o for o in scene.objects if o.type == 'MESH' and o.name.startswith(CHAR_PREFIX) and not o.hide_render]
for o in list(meshes):
    if 'cornea' in o.name.lower():
        o.hide_render = True
meshes = [o for o in meshes if not o.hide_render]
print('CHAR MESHES', len(meshes), flush=True)

def _lin(v):
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
def _L(*rgb):
    return tuple(_lin(v) for v in rgb)

COLOR_MAP = {
    'body': _L(0.985,0.985,0.985), 'teeth': _L(0.985,0.985,0.985), 'eyes': _L(0.985,0.985,0.985),
    'gums': _L(0.05,0.05,0.06), 'tongue': _L(0.05,0.05,0.06),
    'hair': _L(HAIR_GREY,HAIR_GREY,HAIR_GREY+0.02), 'hairband': _L(0.17,0.17,0.19),
    'eyebrow': _L(0.05,0.05,0.06), 'eyelash': _L(0.05,0.05,0.06), 'eyedot': _L(0.05,0.05,0.06),
    'top': _L(0.24,0.34,0.62), 'scarf': _L(0.93,0.92,0.86),
    'jeans': _L(0.25,0.25,0.28), 'shoes': _L(0.12,0.12,0.14),
    'laces': _L(0.80,0.80,0.82), 'socks': _L(0.9,0.9,0.9), 'metal': _L(0.5,0.5,0.55),
    'hands': _L(0.985,0.985,0.985), 'viewport_white': _L(0.985,0.985,0.985),
    'viewport_black': _L(0.05,0.05,0.06), 'viewport_blue': _L(0.15,0.3,0.45),
}
_default_col = _L(0.6,0.6,0.62)
def make_flat(mat):
    name = mat.name.lower()
    col = _default_col
    for k,c in COLOR_MAP.items():
        if k in name:
            col = c; break
    mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (*col, 1.0)
    em.inputs['Strength'].default_value = 1.0
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])

seen = set()
for o in meshes:
    for s in o.material_slots:
        m = s.material
        if m and m.name not in seen:
            seen.add(m.name); make_flat(m)

# ink material for mesh-material lips + GP strokes
ink = bpy.data.materials.new('MAT-ink')
ink.use_nodes = True
nt = ink.node_tree; nt.nodes.clear()
o_out = nt.nodes.new('ShaderNodeOutputMaterial')
o_em = nt.nodes.new('ShaderNodeEmission')
# seam faces stay skin-white: they only mark a material boundary the line art traces as one line
o_em.inputs['Color'].default_value = (*COLOR_MAP['body'], 1.0) if LIP_SEAM_WHITE else (0.04,0.04,0.05,1.0)
nt.links.new(o_em.outputs['Emission'], o_out.inputs['Surface'])

# mouth seam faces -> ink material
ink2 = ink.copy(); ink2.name = 'MAT-ink-bot'
# Upper-lip and lower-lip contact faces get two different (skin-white) materials, so the
# line art traces exactly the contact line between them as one continuous stroke.
for o in meshes:
    top_groups = [g.index for g in o.vertex_groups if g.name.startswith('DEF-Lip_Top_Bot')]
    bot_groups = [g.index for g in o.vertex_groups if g.name.startswith('DEF-Lip_Bot_Top')]
    if not top_groups or not bot_groups:
        continue
    me = o.data
    def _w(v, groups):
        return max([g.weight for g in v.groups if g.group in groups], default=0.0)
    side = {}
    for p in me.polygons:
        wt = sum(_w(me.vertices[vi], top_groups) for vi in p.vertices) / len(p.vertices)
        wb_ = sum(_w(me.vertices[vi], bot_groups) for vi in p.vertices) / len(p.vertices)
        if max(wt, wb_) < LIP_W:
            continue
        side[p.index] = 1 if wt >= wb_ else -1
    edge_faces = {}
    for p in me.polygons:
        for ek in p.edge_keys:
            edge_faces.setdefault(ek, []).append(p.index)
    if not me.attributes.get('freestyle_edge'):
        me.attributes.new('freestyle_edge', 'BOOLEAN', 'EDGE')
    fe = me.attributes['freestyle_edge'].data
    nmark = 0
    # rim of the upper lip: boundary edges of the top-lip-underside region whose outside face
    # faces the camera (-Y) -> the visible closed-mouth line
    for e in me.edges:
        fs = edge_faces.get(tuple(sorted(e.vertices)), [])
        if len(fs) != 2:
            continue
        a, b = side.get(fs[0], 0), side.get(fs[1], 0)
        if (a == 1) == (b == 1):
            continue
        outside = me.polygons[fs[1] if a == 1 else fs[0]]
        if outside.normal.y < -0.35:
            fe[e.index].value = True; nmark += 1
    print('LIP SEAM EDGES MARKED', nmark, [m.type for m in o.modifiers], flush=True)
    xs = sorted(set(round(me.vertices[vi].co.x, 3) for e in me.edges if fe[e.index].value for vi in e.vertices))
    print('LIP X RANGE', xs[:3], xs[-3:], len(xs), flush=True)

# collection of char meshes as the line-art source
char_col = bpy.data.collections.new('charcol')
scene.collection.children.link(char_col)
for o in meshes:
    char_col.objects.link(o)
bpy.context.view_layer.update()

# GP line art via the official operator (wires layer+material+modifier)
added = False
for fix in range(3):
    try:
        if fix == 1:
            bpy.ops.object.mode_set(mode='OBJECT')
        elif fix == 2:
            bpy.context.view_layer.objects.active = meshes[0]
            meshes[0].select_set(True)
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.grease_pencil_add(type='LINEART_COLLECTION', location=(0,0,0))
        added = True
        break
    except Exception as e:
        print('gpadd attempt', fix, 'fail', str(e)[:120])
if not added:
    raise RuntimeError('grease_pencil_add failed')
gpo = bpy.context.active_object
gpd = gpo.data
la = None
for m in gpo.modifiers:
    if m.type == 'LINEART':
        la = m
la.source_collection = char_col
la.use_contour = True
la.use_crease = True
la.use_material = True
la.use_edge_mark = False
la.use_intersection = False
for prop, val in (('radius', 0.003), ('opacity', 1.0)):
    try:
        setattr(la, prop, val)
    except Exception as e:
        print('prop fail', prop, e)
# second pass: edge marks only (the lip seam), allowed to show through one occluder so the
# rim of the upper lip stays one continuous line where the lower lip overlaps it at the corners
try:
    la2 = gpo.modifiers.new('LipSeam', 'LINEART')
    la2.source_type = 'COLLECTION'
    la2.source_collection = char_col
    la2.target_layer = la.target_layer
    la2.target_material = la.target_material
    la2.use_contour = False; la2.use_crease = False; la2.use_material = False
    la2.use_intersection = False; la2.use_loose = False
    la2.use_edge_mark = True
    la2.use_multiple_levels = True
    la2.level_start = 0; la2.level_end = LIP_OCC
    la2.radius = 0.003; la2.opacity = 1.0
    print('lip seam modifier ok', flush=True)
except Exception as e:
    print('lip seam modifier fail', e, flush=True)
    la.use_edge_mark = True
try:
    for gm in gpd.materials:
        if gm:
            gm.line_color = (0.03,0.03,0.04,1.0)
    print('gp ink set')
except Exception as e:
    print('gpmat fail', e)

def detail_pass(name, col, crease_deg, radius):
    """extra line-art pass: creases only, tighter threshold, on a sub-collection"""
    m = gpo.modifiers.new(name, 'LINEART')
    m.source_type = 'COLLECTION'; m.source_collection = col
    m.target_layer = la.target_layer; m.target_material = la.target_material
    m.use_contour = False; m.use_material = False; m.use_edge_mark = False
    m.use_intersection = False; m.use_loose = False
    m.use_crease = True; m.crease_threshold = math.radians(crease_deg)
    m.use_crease_on_smooth = True
    m.radius = radius; m.opacity = 1.0
    return m

# hair strands: the hair is sculpted with strand ridges; trace them
hair_col = bpy.data.collections.new('haircol'); scene.collection.children.link(hair_col)
for o in meshes:
    if 'hair_' in o.name.lower():
        hair_col.objects.link(o)
try:
    detail_pass('HairStrands', hair_col, HAIR_CREASE, 0.002)
    print('hair pass ok', flush=True)
except Exception as e:
    print('hair pass fail', e, flush=True)

# arms: the rig's arms are chunky for her frame; thin them (and the palms a little) along the
# normal in rest space, before the armature deforms them.
body = scene.objects.get('GEO-rain-body')
if body and ARM_SLIM > 0:
    sl = body.vertex_groups.new(name='armslim')
    arm_ids = {g.index: 1.0 for g in body.vertex_groups
               if g.name.startswith(('DEF-Forearm', 'DEF-COR-Forearm'))}
    for g in body.vertex_groups:
        if g.name.startswith(('DEF-Upperarm', 'DEF-COR-Upperarm')):
            arm_ids[g.index] = 0.6
        elif g.name.startswith('DEF-Hand'):
            arm_ids[g.index] = 0.9
    for v in body.data.vertices:
        w = min(1.0, sum(g.weight * arm_ids[g.group] for g in v.groups if g.group in arm_ids))
        if w > 0.0:
            sl.add([v.index], w, 'REPLACE')
    ds = body.modifiers.new('armslim', 'DISPLACE')
    ds.direction = 'NORMAL'; ds.strength = -ARM_SLIM; ds.mid_level = 0.0; ds.vertex_group = 'armslim'
    body.modifiers.move(len(body.modifiers) - 1, body.modifiers.find('Armature'))

# palms: the rig's palm is ~0.63x as deep as it is wide (canon is ~0.35); pull the
# palm+finger skin toward the palm plane in rest space so the depth ratio lands right.
if body and PALM_THIN < 1.0:
    rig_ob = bpy.data.objects.get('RIG-rain')
    bw2w = body.matrix_world
    for suf in ('.L', '.R'):
        wrist = rig_ob.matrix_world @ rig_ob.data.bones['FK-Hand' + suf].head_local
        mcp = rig_ob.matrix_world @ rig_ob.data.bones['FK-Middle1' + suf].head_local
        thumb = rig_ob.matrix_world @ rig_ob.data.bones['FK-Thumb1' + suf].head_local
        palm_dir = (mcp - wrist).normalized()
        width_dir = palm_dir.cross(palm_dir.cross(thumb - wrist)).normalized()
        thick_dir = palm_dir.cross(width_dir).normalized()
        plane_p = wrist + palm_dir * ((mcp - wrist).length * 0.5)
        gi = {g.index: 1.0 for g in body.vertex_groups if g.name.startswith('DEF-Hand' + suf)}
        for g in body.vertex_groups:
            if any(g.name.startswith('DEF-' + f + suf) for f in ('Index', 'Middle', 'Ring', 'Pinky', 'Thumb')):
                gi[g.index] = 0.7
        for v in body.data.vertices:
            w = min(1.0, sum(g.weight * gi[g.group] for g in v.groups if g.group in gi))
            if w <= 0.0: continue
            cw = bw2w @ v.co
            d = (cw - plane_p).dot(thick_dir)
            v.co = bw2w.inverted() @ (cw - thick_dir * d * (1.0 - PALM_THIN) * w)

# hands: knuckle / nail creases. Body copy masked to the hand+finger weights.
if body:
    hc = body.copy(); hc.data = body.data.copy(); hc.name = 'GEO-rain-handdetail'
    scene.collection.objects.link(hc)
    me = hc.data
    vg = hc.vertex_groups.new(name='handmask')
    hand_groups = [g.index for g in hc.vertex_groups
                   if g.name.startswith('DEF-Hand') or any(g.name.startswith('DEF-' + f) for f in
                      ('Index', 'Middle', 'Ring', 'Pinky', 'Thumb'))]
    fore_groups = [g.index for g in hc.vertex_groups if g.name.startswith('DEF-Forearm')]
    def _hw(v):
        return min(1.0, sum(g.weight for g in v.groups if g.group in hand_groups))
    def _fw(v):
        return sum(g.weight for g in v.groups if g.group in fore_groups)
    # mask reaches up the forearm so the copy's open edge sits far from the hand ...
    ids = [v.index for v in me.vertices if _hw(v) > 0.02 or _fw(v) > 0.35]
    vg.add(ids, 1.0, 'REPLACE')
    # ... and 'handfade' pushes only the hand outward; toward the open edge the copy sinks
    # inside the body, so the edge itself is never visible (no wrist "cuff" line).
    fade = hc.vertex_groups.new(name='handfade')
    for v in me.vertices:
        w = _hw(v)
        if w > 0.0:
            fade.add([v.index], w * w, 'REPLACE')
    for m in list(hc.modifiers):
        if m.type in ('MASK', 'VERTEX_WEIGHT_MIX'):
            hc.modifiers.remove(m)
    mk = hc.modifiers.new('handmask', 'MASK'); mk.vertex_group = 'handmask'
    hc.modifiers.move(len(hc.modifiers) - 1, 0)
    d1 = hc.modifiers.new('skinin', 'DISPLACE'); d1.direction = 'NORMAL'; d1.strength = -0.0009; d1.mid_level = 0.0
    d2 = hc.modifiers.new('skinout', 'DISPLACE'); d2.direction = 'NORMAL'; d2.strength = 0.0012; d2.mid_level = 0.0
    d2.vertex_group = 'handfade'
    hand_col = bpy.data.collections.new('handcol'); scene.collection.children.link(hand_col)
    hand_col.objects.link(hc)
    char_col.objects.link(hc)
    # renders coplanar with the body in the same white -> invisible fill, only its creases ink
    try:
        detail_pass('HandDetail', hand_col, HAND_CREASE, 0.0018)
        print('hand pass ok', len(ids), flush=True)
    except Exception as e:
        print('hand pass fail', e, flush=True)

def wb(objs):
    lo = Vector((1e9,)*3); hi = Vector((-1e9,)*3)
    for o in objs:
        for c in o.bound_box:
            v = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, v)); hi = Vector(map(max, hi, v))
    return lo, hi

# ---- posing: relaxed arms + light smile ----
arm = [o for o in scene.objects if o.type == 'ARMATURE'][0]
pb = arm.pose.bones

def set_bone_pos(name, xyz):
    b = pb.get(name)
    if not b: return
    M = b.matrix.copy()
    M.translation = Vector(xyz)
    b.matrix = M

def move_bone(name, dx, dy, dz):
    b = pb.get(name)
    if not b: return
    M = b.matrix.copy()
    M.translation += Vector((dx, dy, dz))
    b.matrix = M
    bpy.context.view_layer.update()

def rot_world(b, axis, angle):
    M = b.matrix.copy()
    p = M.to_translation()
    R = Matrix.Rotation(angle, 4, axis)
    b.matrix = Matrix.Translation(p) @ R @ Matrix.Translation(-p) @ M
    bpy.context.view_layer.update()

def upd():
    bpy.context.view_layer.update()

# arms: FK (no IK stretch) -> true bone lengths. Upper arm hangs ~vertical,
# forearm slightly forward+in, shoulders dropped from the T-pose shrug.
props = pb.get('Properties_IKFK')
if props:
    props['ik_arm_left'] = 0.0; props['ik_arm_right'] = 0.0
    props['ik_stretch_arms'] = 0.0
upd()

def aim_bone(b, want):
    """minimal rotation about the bone head so head->tail points along `want` (roll kept)"""
    d0 = (b.tail - b.head).normalized()
    q = d0.rotation_difference(want.normalized())
    M = b.matrix.copy(); p = M.to_translation()
    b.matrix = Matrix.Translation(p) @ q.to_matrix().to_4x4() @ Matrix.Translation(-p) @ M
    upd()

def roll_bone(b, angle):
    d = (b.tail - b.head).normalized()
    M = b.matrix.copy(); p = M.to_translation()
    b.matrix = Matrix.Translation(p) @ Matrix.Rotation(angle, 4, d) @ Matrix.Translation(-p) @ M
    upd()

for side, s in (('.L', 1.0), ('.R', -1.0)):
    ua = pb.get('FK-Upperarm' + side)
    if ua:
        rot_world(ua, 'Y', s * math.radians(UA_ANGLE))  # hang down, slight outward lean
        rot_world(ua, 'X', math.radians(-4))        # tiny backward drift at elbow
        upd()
        print('ARM', side, 'ua', tuple(round(x, 3) for x in (ua.tail - ua.head).normalized()), flush=True)
    fa = pb.get('FK-Forearm' + side)
    if fa:
        # forearm: near-vertical, ELBOW_BEND deg forward of the upper arm, a touch outward
        ud = (ua.tail - ua.head).normalized()
        fwd = math.radians(-ELBOW_BEND)
        want = Vector((ud.x + s * 0.02, ud.y - math.sin(fwd), ud.z)).normalized()
        aim_bone(fa, want)
        print('ARM', side, 'fa', tuple(round(x, 3) for x in (fa.tail - fa.head).normalized()), flush=True)
        # pronation lives mostly in the forearm (radius roll), not at the wrist joint
        roll_bone(fa, s * math.radians(PRONATE * FORE_TWIST))

# ponytail: swing it over the (screen-left) shoulder so it reads from the front
pt = pb.get('FK-Hair_Ponytail2')
if pt and PONY_SWING > 0:
    d0 = (pt.tail - pt.head).normalized()
    sw = math.radians(PONY_SWING)
    target = Vector((-math.sin(sw) * 0.45, -0.12, -math.cos(sw * 0.5))).normalized()
    q = d0.rotation_difference(target)
    M = pt.matrix.copy(); p = M.to_translation()
    pt.matrix = Matrix.Translation(p) @ q.to_matrix().to_4x4() @ Matrix.Translation(-p) @ M
    upd()
    for n, a in (('FK-Hair_Ponytail3', -12), ('FK-Hair_Ponytail4', -10)):
        b = pb.get(n)
        if b:
            rot_world(b, 'X', math.radians(a)); upd()
    print('PONYTAIL tip', tuple(round(c, 3) for c in (arm.matrix_world @ pb['FK-Hair_Ponytail4'].tail)), flush=True)

# mouth: corners out+up only (no top-lip corner push -> keeps one clean seam)
move_bone('ACT-Lips_Corner.L',  SMILE_OUT, 0.0, SMILE_UP)
move_bone('ACT-Lips_Corner.R', -SMILE_OUT, 0.0, SMILE_UP)
jb = pb.get('MSTR-Jaw')
if jb:
    jM = jb.matrix.copy()
    jb.matrix = jM @ Matrix.Rotation(-0.018, 4, 'X')

# eyes: upper lids lowered (kills the wide stare), outer brows eased up
move_bone('ACT-Eyelid_Upper.L', 0.0, 0.0, EYELID_DROP)
move_bone('ACT-Eyelid_Upper.R', 0.0, 0.0, EYELID_DROP)
move_bone('ACT-Eyelid_Lower.L', 0.0, 0.0, 0.0015)
move_bone('ACT-Eyelid_Lower.R', 0.0, 0.0, 0.0015)
for side in ('.L', '.R'):
    move_bone('GRP-Eyebrow_3' + side, 0.0, 0.0, 0.002)
    move_bone('GRP-Eyebrow_4' + side, 0.0, 0.0, 0.003)

# head: slight tilt + nod, still front-facing
hd = pb.get('FK-Head')
if hd:
    rot_world(hd, 'Y', math.radians(HEAD_TILT))
    rot_world(hd, 'X', math.radians(3))
upd()

# eyebrows: thin the strip (scale thickness about the per-slice centre, keeps the arch)
eb = scene.objects.get('GEO-rain-eyebrows')
if eb and BROW_THIN < 1.0:
    me = eb.data
    slices = {}
    for v in me.vertices:
        slices.setdefault(round(v.co.x / 0.006), []).append(v)
    for vs in slices.values():
        zc = sum(v.co.z for v in vs) / len(vs)
        for v in vs:
            v.co.z = zc + (v.co.z - zc) * BROW_THIN
    me.update()
    upd()

# pupils: shrink each dot about its own centre (object-scale slid them off the eye)
ed = scene.objects.get('GEO-rain-eye_dots')
if ed:
    me = ed.data
    groups = {}
    for v in me.vertices:
        groups.setdefault(v.co.x > 0, []).append(v)
    def _scale(pts):
        idx = {}
        for i, p in enumerate(pts):
            idx.setdefault(p.co.x > 0, []).append(i)
        for ids in idx.values():
            c = sum((pts[i].co for i in ids), Vector()) / len(ids)
            for i in ids:
                pts[i].co = c + (pts[i].co - c) * PUPIL_SCALE
    _scale(me.vertices)
    if me.shape_keys:
        for kb in me.shape_keys.key_blocks:
            _scale(kb.data)
    me.update()
    upd()

# hands: relaxed hang. Work in hand-local terms so the pose survives pronation.
def bdir(b):
    return (b.tail - b.head).normalized()

def rot_axis(b, axis, angle):
    M = b.matrix.copy()
    p = M.to_translation()
    R = Matrix.Rotation(angle, 4, axis.normalized())
    b.matrix = Matrix.Translation(p) @ R @ Matrix.Translation(-p) @ M
    bpy.context.view_layer.update()

for side, s in (('.L', 1.0), ('.R', -1.0)):
    hb = pb.get('FK-Hand' + side)
    if not hb: continue
    if HAND_SCALE != 1.0:
        # whole-hand scale (palm + fingers); preserved through the matrix posing below
        hs = Matrix.Scale(HAND_SCALE, 4)
        hb.matrix = hb.matrix @ hs
        bpy.context.view_layer.update()
    palm_local = hb.matrix.to_3x3().inverted() @ Vector((-s, 0.0, 0.0))   # palm faces thigh now
    # pronate ~35 deg about the hand's own axis -> back of hand turns toward camera
    rot_axis(hb, bdir(hb), s * math.radians(PRONATE * (1.0 - FORE_TWIST)))
    # slight ulnar drift: fingertips lean toward thigh
    palm = (hb.matrix.to_3x3() @ palm_local).normalized()
    rot_axis(hb, bdir(hb).cross(palm), math.radians(-3))
    # wrist straight: hand continues the forearm line (tiny lean toward the thigh), keeping roll
    fa = pb.get('FK-Forearm' + side)
    if fa:
        fdir = bdir(fa)
        want = (Matrix.Rotation(math.radians(WRIST_LEAN), 3, fdir.cross(Vector((-s, 0.0, 0.0))).normalized()) @ fdir).normalized()
        print('WRIST', side, 'fdir', tuple(round(x, 3) for x in fdir), 'hdir0', tuple(round(x, 3) for x in bdir(hb)), flush=True)
        aim_bone(hb, want)
        print('WRIST', side, 'hdir1', tuple(round(x, 3) for x in bdir(hb)), flush=True)
    palm = (hb.matrix.to_3x3() @ palm_local).normalized()
    # fingers: gentle graded curl toward the palm, pinky most
    curl = {'Index': (10, 16, 12), 'Middle': (12, 20, 14), 'Ring': (20, 30, 20), 'Pinky': (24, 34, 24)}
    for fing, angs in curl.items():
        for i, a in zip((1, 2, 3), angs):
            fb = pb.get('FK-%s%d%s' % (fing, i, side))
            if fb:
                f = bdir(fb)
                rot_axis(fb, f.cross(palm), math.radians(a))
    # thumb: fold in toward the fingers and drop so it lies along the thigh front
    for i, a in ((1, 28), (2, 18)):
        fb = pb.get('FK-Thumb%d%s' % (i, side))
        if fb:
            t = bdir(fb)
            rot_axis(fb, t.cross(bdir(hb)), math.radians(a))

# mouth line: read the edge-marked upper-lip rim from the posed, evaluated head mesh and
# draw it as one ink tube (a curve with bevel) sitting just in front of the lips
if LIP_TUBE:
    dg = bpy.context.evaluated_depsgraph_get()
    head = scene.objects.get('GEO-rain-head')
    if head:
        ev = head.evaluated_get(dg)
        em = ev.to_mesh()
        attr = em.attributes.get('freestyle_edge')
        pts = []
        if attr:
            M = ev.matrix_world
            segs = [(M @ em.vertices[e.vertices[0]].co, M @ em.vertices[e.vertices[1]].co)
                    for e in em.edges if attr.data[e.index].value]
            print('EVAL LIP EDGES', len(segs), flush=True)
            if segs:
                # chain: walk from the leftmost endpoint through nearest neighbours
                verts = {}
                for a, b in segs:
                    ka, kb = tuple(round(c, 5) for c in a), tuple(round(c, 5) for c in b)
                    verts.setdefault(ka, set()).add(kb); verts.setdefault(kb, set()).add(ka)
                # the rim runs left->right; order its vertices by x
                raw = [Vector(k) for k in sorted(verts, key=lambda k: k[0])]
                # merge the dense corner clusters, then smooth so the line reads as one stroke
                pts = []
                for v in raw:
                    if pts and abs(v.x - pts[-1][-1].x) < 0.002:
                        pts[-1].append(v)
                    else:
                        pts.append([v])
                pts = [sum(g, Vector()) / len(g) for g in pts]
                for _ in range(2):
                    pts = [pts[0]] + [(pts[i-1] + 2*pts[i] + pts[i+1]) / 4 for i in range(1, len(pts)-1)] + [pts[-1]]
                print('LIP CHAIN', len(pts), ' '.join('(%.3f,%.3f,%.4f)' % (v.x, v.y, v.z) for v in pts), flush=True)
        ev.to_mesh_clear()
        if len(pts) >= 3:
            cu = bpy.data.curves.new('LipLine', 'CURVE'); cu.dimensions = '3D'
            cu.bevel_depth = LIP_TUBE; cu.bevel_resolution = 4; cu.fill_mode = 'FULL'
            sp = cu.splines.new('NURBS'); sp.points.add(len(pts) - 1)
            for p, v in zip(sp.points, pts):
                p.co = (v.x, v.y - 0.004, v.z, 1.0)
            sp.use_endpoint_u = True; sp.order_u = 3
            lip_mat = bpy.data.materials.new('MAT-lipline'); lip_mat.use_nodes = True
            nt2 = lip_mat.node_tree; nt2.nodes.clear()
            oo = nt2.nodes.new('ShaderNodeOutputMaterial'); ee = nt2.nodes.new('ShaderNodeEmission')
            ee.inputs['Color'].default_value = (0.03, 0.03, 0.04, 1.0)
            nt2.links.new(ee.outputs['Emission'], oo.inputs['Surface'])
            cu.materials.append(lip_mat)
            lo_obj = bpy.data.objects.new('LipLine', cu); scene.collection.objects.link(lo_obj)
    # the tube replaces the line-art seam pass
    try:
        la2.level_end = 0; la2.use_edge_mark = False
    except Exception:
        pass

lo, hi = wb([o for o in meshes if 'ponytail' not in o.name.lower() and 'hair_strand' not in o.name.lower()])
center = (lo + hi) / 2
h = hi.z - lo.z
z_lo_view = lo.z + h * crop_bottom_frac
span = hi.z - z_lo_view
cx = center.x; cy_c = center.y
zc = (z_lo_view + hi.z) / 2
if FACE_ONLY:
    scene.render.resolution_x = 700
    scene.render.resolution_y = 700
    span = 0.34
    zc = hi.z - 0.25
if HANDS_ONLY:
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 600
    span = 0.36
    hz = arm.matrix_world @ pb['FK-Hand.L'].head
    zc = hz.z - 0.05

cam_data = bpy.data.cameras.new('Cam'); cam_data.lens = 60
cam_data.sensor_fit = 'VERTICAL'
cam = bpy.data.objects.new('Cam', cam_data); scene.collection.objects.link(cam)
vfov = cam_data.angle
dist = (span/2) / math.tan(vfov/2) * 1.08
cam.location = Vector((cx, cy_c - dist, zc))
cam.rotation_euler = (Vector((cx, cy_c, zc)) - cam.location).to_track_quat('-Z','Y').to_euler()
scene.camera = cam
scene.render.filepath = out_png
if os.environ.get('NO_RENDER'):
    raise SystemExit
bpy.ops.render.render(write_still=True)
print('WROTE', out_png)