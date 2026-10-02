# Cast plate baker v4: bakes the CANONICAL preset catalog as full-scene
# renders with a cryptomatte object pass. The packer splits each render into
# component plates by object id, so every shipped pixel is one the authored
# render itself produced - no solo-render artifacts, no occlusion math of
# our own. The base render of each look doubles as ground truth.
#
# Emits OUT/plates.json: plate stem -> {src: render stem, keep: [obj names]}
# (keep=[] means the render ships whole, e.g. body plates).
#
# Usage: LOOK=<look_id> [OUT=dir W=1440 H=2160 FR=27]
#        blender -b scenes/BASE_V58.blend --python scripts/castbake3.py
# Env follows presets.sh: source env.sh first, then the look sets its own
# HAIR/EST/SIDES/TUCK/MG/etc exactly as style() / male_look() do.
import bpy, os, re

PV1  = os.environ.get('PV1', os.path.dirname(os.path.abspath(__file__)))
OUT  = os.environ.get('OUT', os.path.join(os.path.dirname(PV1), 'castbake3'))
W    = int(os.environ.get('W', '1440'))
H    = int(os.environ.get('H', '2160'))
FRAME= int(os.environ.get('FR', '27'))
LOOK = os.environ['LOOK']
VARIANT = os.environ.get('VARIANT', '').strip().lower()
os.makedirs(OUT, exist_ok=True)

RND = ('MESH', 'CURVE', 'SURFACE', 'FONT', 'META')
_TRACK = {}

def step(name):
    pre = set(bpy.data.objects)
    p = os.path.join(PV1, name)
    exec(compile(open(p).read(), p, 'exec'), {'__name__': '__main__', '__file__': p})
    new = [o.name for o in set(bpy.data.objects) - pre]
    _TRACK[name] = new
    print('STEP', name, '+%d objects' % len(new))
    return new

def _vis(pat):
    rx = re.compile(pat)
    return [o.name for o in bpy.data.objects
            if rx.match(o.name) and o.type in RND and not o.hide_render]

def _hide(names):
    for n in names:
        o = bpy.data.objects.get(n)
        if o:
            o.hide_render = o.hide_viewport = True

def shot(name, hide=()):
    # full-scene render; hide= only drops objects of OTHER variants (e.g. the
    # four other neck pieces while one is rendered). Crypto + depth go to
    # z_<name>.exr for the packer's object-level split.
    S = bpy.context.scene
    hidden = []
    for n in hide:
        o = bpy.data.objects.get(n)
        if o is not None and o.type in RND and not o.hide_render:
            o.hide_render = o.hide_viewport = True
            hidden.append(n)
    if _ZFO is not None:
        _ZFO.file_name = 'z_%s' % name
    S.render.filepath = os.path.join(OUT, name + '.png')
    bpy.ops.render.render(write_still=True)
    for n in hidden:
        bpy.data.objects[n].hide_render = bpy.data.objects[n].hide_viewport = False
    print('SHOT', name)

PLATES = {}

def emit(src, stem, keep):
    PLATES[stem] = {'src': src, 'keep': sorted(keep)}

def _names(pat):
    rx = re.compile(pat)
    return [o.name for o in bpy.data.objects
            if rx.match(o.name) and o.type in RND and not o.hide_render]

_ZFO = None   # compositor File Output node carrying depth + cryptomatte

def _setup():
    global _ZFO
    S = bpy.context.scene
    S.render.film_transparent = True
    S.render.resolution_x, S.render.resolution_y = W, H
    S.render.resolution_percentage = 100
    cam = S.camera
    cam.location = (-0.42, -5.0, 1.325)
    cam.rotation_euler = (1.5707963, 0, 0)
    cam.data.ortho_scale = 1.25 * max(1.0, W / H)
    S.cycles.samples = 12
    S.cycles.use_adaptive_sampling = True
    S.cycles.use_denoising = True
    S.frame_set(FRAME)
    bpy.context.view_layer.update()
    vl = S.view_layers[0]
    for l in vl.freestyle_settings.linesets:
        l.linestyle.thickness = max(0.5, l.linestyle.thickness * H / 4320.0)
    ng = S.compositing_node_group
    if ng is not None:
        for node in ng.nodes:
            if node.type == 'DILATEERODE':
                node.inputs['Size'].default_value = max(1, round(node.inputs['Size'].default_value * H / 2160))
    # depth pass -> multilayer EXR via File Output. The packer resolves
    # occlusion per pixel against earlier-layer depth, so every shot emits one.
    vl.use_pass_z = True
    vl.use_pass_cryptomatte_object = True
    if ng is not None:
        rl = ng.nodes.new('CompositorNodeRLayers')
        rl.name = '_z_rlayers'
        fo = ng.nodes.new('CompositorNodeOutputFile')
        fo.name = '_z_out'
        fo.directory = OUT
        fo.save_as_render = False
        fo.file_name = 'z_unused'
        fo.file_output_items.new('FLOAT', 'z')
        ng.links.new(rl.outputs['Depth'], fo.inputs['z'])
        for ci, pas in (('crypto', 'CryptoObject00'), ('crypto2', 'CryptoObject01'),
                        ('crypto3', 'CryptoObject02')):
            if pas in rl.outputs:
                fo.file_output_items.new('RGBA', ci)
                ng.links.new(rl.outputs[pas], fo.inputs[ci])
        print('RLOUT', sorted(s.name for s in rl.outputs))
        _ZFO = fo

HAND_VG = ('hand', 'finger', 'wrist', 'nail', 'metac')
SKINS_LIST = [('fair', 'F7E1D3'), ('light', 'F1D7C8'), ('medium', 'E0B48F'),
              ('tan', 'C99A6E'), ('brown', '9E6B4A'), ('deep', '6A4431')]

def run_hands(prefix, char):
    # hands are body-mesh verts, not objects: dup the body, delete non-hand
    # verts, holdout everything else. The open cut seam gets a freestyle
    # boundary stroke, so seam screen positions go to a sidecar and the
    # packer feathers the plate alpha around them.
    import bmesh, json
    from bpy_extras.object_utils import world_to_camera_view
    base = {'DBTN': '0', 'EST': 'none', 'TUCK': '0', 'SIDES': '1', 'FACE': '0',
            'MG': '', 'HAIR': '', 'HCOL': '', 'HDYE': '', 'WATCH': '',
            'STONE': '', 'LIPC': '', 'DOBJ': 'Host.body'}
    os.environ.update(base)
    steps = []   # rig pose at the talking frame needs no chain steps
    for s in steps:
        step(s)
    body = bpy.data.objects['Host.body']
    rig = body.parent
    # keep verts weighted to any bone under wrist.L / wrist.R — covers palm,
    # fingers, wrist regardless of how the vertex groups are named
    bone_names = set()
    for root in ('wrist.L', 'wrist.R'):
        b = rig.data.bones.get(root)
        if b is None:
            continue
        bone_names.add(b.name)
        for ch in b.children_recursive:
            bone_names.add(ch.name)
    vg = {g.index for g in body.vertex_groups if g.name in bone_names}
    keep_idx = {v.index for v in body.data.vertices
                if any(g.group in vg and g.weight > 0.5 for g in v.groups)}
    print('hands: %d body verts' % len(keep_idx))
    # no mask/render needed: the hands plate is a hull-clipped region of the
    # body plate (the body render already carries exact authored hands).
    # Hull = projected wrist+finger pose-bone head/tail positions per side.
    S = bpy.context.scene
    cam = S.camera
    sx, sy = S.render.resolution_x, S.render.resolution_y
    S.frame_set(27)
    bpy.context.view_layer.update()
    hulls = {'L': [], 'R': []}
    for pb in rig.pose.bones:
        if pb.name not in bone_names:
            continue
        side = 'L' if pb.name.endswith('.L') else 'R'
        for co in (pb.head, pb.tail):
            ndc = world_to_camera_view(S, cam, rig.matrix_world @ co)
            hulls[side].append([round(ndc.x * sx, 1),
                                round((1.0 - ndc.y) * sy, 1)])
    json.dump(hulls, open(os.path.join(OUT, '%s_hands.hull.json' % prefix), 'w'))
    print('hands hull L=%d R=%d' % (len(hulls['L']), len(hulls['R'])))

FACES = [('f0', '0'), ('f1', '1'), ('f2', '2')]
LIP_VARIANTS = [('red', 'B3202A'), ('berry', '8A2A4E'), ('coral', 'E0664F'), ('nude', 'B8826F')]

def run_body(prefix, char):
    # Body plates = the chassis render verbatim: full chain, then every object
    # that is not the body is hidden outright (not holdout - a holdout garment
    # would matte out the wrist flesh and forearm edges the plate needs).
    # Covers all skin tones and face variants. The authored male earring stays
    # (it is part of his base look); hers are per-style plates.
    if char == 'male':
        os.environ.update({'DBTN': '0', 'EST': 'none', 'TUCK': '0', 'SIDES': '1',
                           'FACE': '0', 'MG': '', 'HAIR': '', 'HCOL': '', 'HDYE': '',
                           'WATCH': '', 'STONE': '', 'LIPC': '', 'DOBJ': 'Host.body'})
        step('malerelax_pre.py'); step('male2.py'); step('malebrow.py'); step('facealign.py')
        step('garm.py'); step('hairswap.py'); step('modLS.py'); step('ear2.py')
        step('strands.py'); step('lip.py'); step('skintone.py'); step('haircol.py')
        step('garmall.py'); step('facerestore.py'); step('facevar.py')
        step('hairpeek.py'); step('malerelax.py')
    else:
        os.environ.update({'SIDES': '1', 'TUCK': '1', 'EST': 'hoop', 'HR': '0.011',
                           'SNX': '24', 'SNZ': '4', 'DRESS': 'mindfront_f_dress_11',
                           'DCOL': '2B3A5C', 'DMINISL': '0', 'FACE': '0', 'NECK': '',
                           'HAIR': '', 'HCOL': '', 'HDYE': '', 'LIPC': '', 'STONE': ''})
        step('dressswap.py'); step('hairswap.py'); step('modLS.py'); step('ear2.py')
        step('strands.py'); step('lip.py'); step('facevar.py'); step('neck.py')
        step('skintone.py'); step('dressart.py'); step('haircol.py'); step('hairpeek.py')
    S = bpy.context.scene
    chain = {n for lst in _TRACK.values() for n in lst}
    extra = set(_vis(r'Host\.watch_.*')) | set(_vis(r'Host\.hair_'))
    if char == 'male':
        # his hoop is part of the authored base - keep V60/V61; the rest of the
        # V6x jewelry set is hers and stays out
        extra |= set(_vis(r'Host\.V(6[2-9]|[7-9]\d).*'))
    else:
        extra |= set(_vis(r'Host\.V6\d.*'))
    # leftover base-scene garments are not body either (lineart_* stays: those
    # strokes are part of the chassis render)
    extra |= set(_vis(r'Host\.(?!lineart_).*(dress|shirt|trouser|jeans|pant|skirt|sweater|polo|sneaker|shoe|top|blazer|tee).*'))
    extra |= set(_vis(r'Host\.V26_.*'))          # garment detail strokes (darts, folds, creases) - they sit on clothes, not skin
    # his hoop is built by ear2.py (tracked as chain) but authored into every
    # male look - let it ride with the body
    ear_ok = set(_vis(r'Host\.V60_earring.*') + _vis(r'Host\.V61_.*')) \
             if char == 'male' else set()
    keep = [o.name for o in bpy.data.objects
            if o.type in RND and not o.hide_render
            and (o.name not in chain or o.name in ear_ok)
            and o.name not in extra]
    print('body keep:', keep)
    hidden = []
    for o in bpy.data.objects:
        if o.type in RND and not o.hide_render and o.name not in keep:
            o.hide_render = o.hide_viewport = True
            hidden.append(o.name)
    # the body plate is the whole chassis: garment Delete.* masks (which hide
    # skin under clothes in dressed renders) come off for the nude render.
    # 'Hide helpers' stays - those verts are helper markers, not skin.
    body = bpy.data.objects['Host.body']
    off_masks = [m for m in body.modifiers
                 if m.type == 'MASK' and m.vertex_group.startswith('Delete.')]
    for m in off_masks:
        m.show_render = False
    lip_inputs = None
    lip_defaults = None
    if char == 'female':
        lip_inputs = [i for i in bpy.data.materials['PEEPS_V2_WARM_SKIN'].node_tree.nodes['Mix.002'].inputs
                      if i.enabled and i.type == 'RGBA']
        lip_defaults = [tuple(i.default_value) for i in lip_inputs]
    requested_skins = [x.strip() for x in os.environ.get('BODY_SKINS', '').split(',') if x.strip()]
    body_skins = SKINS_LIST if not requested_skins else [x for x in SKINS_LIST if x[0] in requested_skins]
    if requested_skins and len(body_skins) != len(set(requested_skins)):
        raise ValueError('unknown BODY_SKINS value: %s' % ','.join(requested_skins))
    for fkey, fnum in FACES:
        os.environ['FACE'] = fnum
        step('facevar.py')
        for sname, shex in body_skins:
            os.environ['STONE'] = shex
            step('skintone.py')
            if _ZFO is not None:
                _ZFO.file_name = 'z_%s_body_%s_%s' % (prefix, fkey, sname)
            S.render.filepath = os.path.join(
                OUT, '%s_body_%s_%s.png' % (prefix, fkey, sname))
            bpy.ops.render.render(write_still=True)
        # Lip patches are rendered against one canonical skin; castpack4 turns
        # the deterministic pixel delta into a transparent patch. This removes
        # the old rename hack and gives Coral a real authored preview.
        if char == 'female':
            os.environ['STONE'] = 'E0B48F'
            step('skintone.py')
            for lname, lhex in LIP_VARIANTS:
                os.environ['LIPC'] = lhex
                step('lip.py')
                S.render.filepath = os.path.join(OUT, 'fem_liprender_%s_%s.png' % (fkey, lname))
                bpy.ops.render.render(write_still=True)
            for sock, value in zip(lip_inputs, lip_defaults):
                sock.default_value = value
            os.environ['LIPC'] = ''
    for n in hidden:
        bpy.data.objects[n].hide_render = bpy.data.objects[n].hide_viewport = False

FEM_COLORS = [('auburn', '', ''), ('black', '1C1714', ''), ('brown', '3B2418', ''),
              ('blonde', 'D8B77A', ''), ('silver', 'B9B8B5', '')]
MALE_COLORS = [('black', '1C1714', ''), ('blonde', 'C9A366', ''), ('brown', '5A3A24', ''),
               ('dye', '141212', '8A1F3C'), ('grey', '8F9096', '')]
FEM_DRESS_COLORS = {'navy': '2B3A5C', 'burgundy': '6B2233', 'sage': '7C8C6A', 'emerald': '1F5C4A', 'rose': 'B87A7F'}
MALE_TOP_COLORS = {'navy': '2E3A55', 'ivory': 'EDEBE6', 'blue': 'A9C4DE', 'burgundy': '6B2E2E', 'cream': 'D8CFBE'}

FEM_STYLE_ENV = {
    'long':  {},
    'bob':   {'HAIR': 'toigo_blunt_bob', 'EST': 'bar', 'TZT': '0.015', 'BARW': '0.0021', 'SMIN': '9'},
    'bangs': {'HAIR': 'toigo_blunt_bob_with_bangs', 'EST': 'stud', 'STR': '0.0052', 'TZT': '0.0', 'EY': '0.0'},
    'bun':   {'HAIR': 'rehmanpolanski_hair_bun_brown', 'SIDES': '1,-1', 'TUCK': '0', 'EST': 'hoop', 'HR': '0.016'},
    'braid': {'HAIR': 'elvs_french_braid_variation', 'EST': 'drop', 'SNX': '10', 'SNZ': '3', 'SW': '2.4', 'HLW': '2.6'},
}
FEM_LOOKS = {
    'fem_long':  dict(style='long',  dress='mindfront_f_dress_11',          dcol='2B3A5C', dminisl='0',   plate='sheath',  necks=True),
    'fem_bob':   dict(style='bob',   dress='mindfront_f_dress_09',          dcol='6B2233', dminisl='0',   plate='maxi'),
    'fem_bangs': dict(style='bangs', dress='mindfront_f_dress_07',          dcol='7C8C6A', dminisl='0',   plate='column'),
    'fem_bun':   dict(style='bun',   dress='punkduck_black_cocktail_dress', dcol='1F5C4A', dminisl='0',   plate='cocktail'),
    'fem_braid': dict(style='braid', dress='punkduck_middle_length_qipao',  dcol='B87A7F', dminisl='200', plate='qipao'),
}
MALE_LOOKS = {
    'male_O1': dict(hair='afro01',            hstyle='afro',   mg='namuhekam_male_polo_shirt=2E3A55,mindfront_male_trousers_1=3A3A40,mindfront_shoes_oxford_male=3A2A20'),
    'male_O2': dict(hair='short01',           hstyle='crop',   mg='toigo_basic_tucked_t-shirt=EDEBE6,elvs_jeans_straight_leg=2E3A55,punkduck_comfortable_sneakers=ECEAE4'),
    'male_O3': dict(hair='elvs_maxwell_hair', hstyle='quiff',  mg='elvs_male_shirt_untucked_bd1=A9C4DE,mindfront_male_trousers_2=B59A6E,mindfront_shoes_monk_strap_male=4A2E1E'),
    'male_O4': dict(hair='elvs_braided_rows', hstyle='braids', mg='mindfront_knitted_sweater_01=6B2E2E,punkduck_male_classic_jeans=3A4660,culturalibre_sneakers=E8E6E0'),
    'male_O5': dict(hair='elvs_grump_hair',   hstyle='swept',  mg='toigo_fisherman_sweater=D8CFBE,toigo_wool_pants=3A3A40,mindfront_shoes_oxford_male=3A2A20'),
    # watch plates bake per outfit: the seat detection in watch.py moves the
    # strap below the cuff on long sleeves, so each outfit needs its own set
    'male_watch_o1': dict(hair='elvs_maxwell_hair', hstyle='_watch',
                          mg='namuhekam_male_polo_shirt=2E3A55,mindfront_male_trousers_1=3A3A40,mindfront_shoes_oxford_male=3A2A20', watchrun=True),
    'male_watch_o2': dict(hair='elvs_maxwell_hair', hstyle='_watch',
                          mg='toigo_basic_tucked_t-shirt=EDEBE6,elvs_jeans_straight_leg=2E3A55,punkduck_comfortable_sneakers=ECEAE4', watchrun=True),
    'male_watch_o3': dict(hair='elvs_maxwell_hair', hstyle='_watch',
                          mg='elvs_male_shirt_untucked_bd1=A9C4DE,mindfront_male_trousers_2=B59A6E,mindfront_shoes_monk_strap_male=4A2E1E', watchrun=True),
    'male_watch_o4': dict(hair='elvs_maxwell_hair', hstyle='_watch',
                          mg='mindfront_knitted_sweater_01=6B2E2E,punkduck_male_classic_jeans=3A4660,culturalibre_sneakers=E8E6E0', watchrun=True),
    'male_watch_o5': dict(hair='elvs_maxwell_hair', hstyle='_watch',
                          mg='toigo_fisherman_sweater=D8CFBE,toigo_wool_pants=3A3A40,mindfront_shoes_oxford_male=3A2A20', watchrun=True),
}
MALE_WATCHES = ['analog', 'digital', 'smart', 'chrono', 'dress']
FEM_NECKS = ['fine', 'pendant', 'pearls', 'choker', 'scarf']

def run_fem(style, dress, dcol, dminisl, plate, necks=False):
    if VARIANT:
        if VARIANT not in FEM_DRESS_COLORS: raise ValueError('unknown female dress colour '+VARIANT)
        dcol = FEM_DRESS_COLORS[VARIANT]
    env = {'SIDES': '1', 'TUCK': '1', 'EST': 'hoop', 'HR': '0.011', 'SNX': '24', 'SNZ': '4',
           'DRESS': dress, 'DCOL': dcol, 'DMINISL': dminisl, 'FACE': '0',
           'NECK': '', 'HCOL': '', 'HDYE': '', 'LIPC': '', 'STONE': ''}
    env.update(FEM_STYLE_ENV[style])
    os.environ.update(env)
    os.environ['STONE'] = 'E0B48F'      # medium - matches fem_body_f0_medium
    # female.py chain, instrumented: dressswap -> hairswap -> modLS -> ear2 ->
    # strands -> lip -> facevar -> neck -> skintone -> dressart -> haircol -> hairpeek
    dnew = step('dressswap.py')
    hnew = step('hairswap.py')
    lnew = step('modLS.py')
    step('ear2.py')
    snew = step('strands.py')
    step('lip.py'); step('facevar.py'); step('neck.py'); step('skintone.py')
    anw = step('dressart.py')
    pk  = step('hairpeek.py')
    _hide(_vis(r'Host\.V26_.*'))      # authored to zero pixels on every look
    _hide(_vis(r'Host\.V62_.*'))      # default neckwear is not part of a look
    hair_names = _names(r'Host\.(hair_|hp_|ink_hair)')
    body_names = _names(r'Host\.(body|high-poly|lineart|eyelash|eyebrow|V59|teeth|inner|cornea|iris|pupil|tongue).*')
    # the authored full render is itself the ground truth: a composite of the
    # extracted plates must reproduce this frame pixel-for-pixel
    suffix = ('_' + VARIANT) if VARIANT else ''
    look_src = 'fem_look_%s%s' % (style, suffix)
    shot(look_src)
    emit(look_src, 'fem_outfit_%s%s' % (plate, suffix),
          set(dnew + anw) | set(_names(r'Host\.V64_.*')))
    if VARIANT:
        return
    emit(look_src, 'fem_earring_%s' % style,
          _names(r'Host\.(V60_earring|V61_)'))
    emit('fem_look_%s' % style, 'fem_hair_%s_%s' % (style, FEM_COLORS[0][0]), hair_names)
    PLATES['fem_bodyset'] = {'src': 'fem_look_%s' % style, 'keep': sorted(body_names)}
    for nm, hx, dye in FEM_COLORS[1:]:
        os.environ['HCOL'] = hx
        os.environ['HDYE'] = dye
        step('haircol.py')
        shot('fem_hair_%s_%s' % (style, nm))
        emit('fem_hair_%s_%s' % (style, nm), 'fem_hair_%s_%s' % (style, nm), hair_names)
    if necks:
        prev = []
        for n in FEM_NECKS:
            _hide(prev)
            os.environ['NECK'] = n
            nw = step('neck.py')
            keep = set(nw) | set(_vis(r'Host\.V62_.*'))
            shot('fem_neck_%s' % n, hide=prev)
            emit('fem_neck_%s' % n, 'fem_neck_%s' % n, keep)
            prev = list(keep)

def run_male(hair, hstyle, mg, watchrun=False):
    if VARIANT:
        if VARIANT not in MALE_TOP_COLORS: raise ValueError('unknown male top colour '+VARIANT)
        parts = mg.split(',')
        top_name = parts[0].split('=', 1)[0]
        parts[0] = top_name + '=' + MALE_TOP_COLORS[VARIANT]
        mg = ','.join(parts)
    env = {'DBTN': '0', 'EST': 'none', 'TUCK': '0', 'SIDES': '1', 'FACE': '0',
           'MG': mg, 'HAIR': hair, 'HCOL': '', 'HDYE': '', 'WATCH': '',
           'STONE': 'E0B48F', 'LIPC': '', 'DOBJ': 'Host.body'}
    os.environ.update(env)
    # modM.py chain, instrumented
    step('malerelax_pre.py'); step('male2.py'); step('malebrow.py'); step('facealign.py')
    gnew = step('garm.py')
    hnew = step('hairswap.py')
    lnew = step('modLS.py')
    step('ear2.py')
    snew = step('strands.py')
    step('lip.py'); step('skintone.py')
    step('haircol.py')
    ganw = step('garmall.py')
    step('facerestore.py'); step('facevar.py')
    pk = step('hairpeek.py')
    step('malerelax.py')
    _hide(_vis(r'Host\.V26_.*'))      # same - stray dress-detail strokes
    hair_objs = _vis(r'Host\.hair_') + _vis(r'Host\.hp_')
    garm_objs = _vis(r'Host\.(?!lineart_).*(dress|shirt|trouser|jeans|pant|skirt|sweater|polo|sneaker|shoe|top|blazer|tee).*')
    if watchrun:
        suffix = LOOK.rsplit('_', 1)[1]          # o1..o5
        prev = []
        for wt in MALE_WATCHES:
            _hide(prev)
            os.environ['WATCH'] = wt
            wnew = step('watch.py')
            keep = set(wnew) | set(_vis(r'Host\.watch_.*'))
            shot('male_watch_%s_%s' % (suffix, wt), hide=prev)
            emit('male_watch_%s_%s' % (suffix, wt),
                  'male_watch_%s_%s' % (suffix, wt), keep)
            prev = list(keep)
        return
    hair_names = _names(r'Host\.(hair_|hp_|ink_hair)')
    body_names = _names(r'Host\.(body|high-poly|lineart|eyelash|eyebrow|V59|teeth|inner|cornea|iris|pupil|tongue|V60|V61).*')
    kind = LOOK.rsplit('_', 1)[1].lower()
    suffix = ('_' + VARIANT) if VARIANT else ''
    look_src = 'male_look_%s%s' % (kind, suffix)
    shot(look_src)
    emit(look_src, 'male_outfit_%s%s' % (kind, suffix), set(gnew + ganw))
    if VARIANT:
        return
    emit(look_src, 'male_hair_%s_%s' % (hstyle, MALE_COLORS[0][0]), hair_names)
    PLATES['male_bodyset'] = {'src': 'male_look_%s' % LOOK.rsplit('_', 1)[1].lower(),
                              'keep': sorted(body_names)}
    for nm, hx, dye in MALE_COLORS[1:]:
        os.environ['HCOL'] = hx
        os.environ['HDYE'] = dye
        step('haircol.py')
        shot('male_hair_%s_%s' % (hstyle, nm))
        emit('male_hair_%s_%s' % (hstyle, nm), 'male_hair_%s_%s' % (hstyle, nm), hair_names)

_setup()
if LOOK in FEM_LOOKS:
    run_fem(**FEM_LOOKS[LOOK])
elif LOOK in MALE_LOOKS:
    run_male(**MALE_LOOKS[LOOK])
elif LOOK == 'fem_hands':
    run_hands('fem', 'female')
elif LOOK == 'male_hands':
    run_hands('male', 'male')
elif LOOK == 'fem_body':
    run_body('fem', 'female')
elif LOOK == 'male_body':
    run_body('male', 'male')
import json
_p = os.path.join(OUT, 'plates.json')
_existing = json.load(open(_p)) if os.path.exists(_p) else {}
_existing.update(PLATES)
json.dump(_existing, open(_p, 'w'), indent=0)
print('CASTBAKE3 DONE', LOOK)
