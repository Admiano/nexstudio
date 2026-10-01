# Cast plate baker v3: bakes the CANONICAL preset catalog as holdout-isolated
# component plates. One Blender process per look; every shot renders the fully
# built look with all non-component objects marked holdout - so each plate
# carries exactly the pixels that component covers in the real render
# (occluders matte instead of shade, but still cast shadows).
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

_FRE = {
    'hair':   ('HAIR_LOCKS', 'HAIR_OUTER'),
    'dress':  ('RAIN_STYLE_CONTOURS', 'GARMENT_SILHOUETTE'),
    'outfit': ('RAIN_STYLE_CONTOURS', 'GARMENT_SILHOUETTE'),
}

def shot(name, keep, fre=()):
    keep = set(keep)
    S = bpy.context.scene
    ls = S.view_layers[0].freestyle_settings.linesets
    had = {}
    if fre is None:
        pass                                  # authored lineset state
    elif fre:
        for l in ls:
            had[l.name] = l.show_render
            l.show_render = l.name in fre
    else:
        for l in ls:
            had[l.name] = l.show_render
            l.show_render = l.show_render and l.name in fre
    touched = []
    for o in bpy.data.objects:
        if o.type not in RND or o.hide_render:
            continue
        if o.name not in keep and not o.is_holdout:
            o.is_holdout = True
            touched.append(o.name)
    S.render.filepath = os.path.join(OUT, name + '.png')
    bpy.ops.render.render(write_still=True)
    for n in touched:
        bpy.data.objects[n].is_holdout = False
    for l in ls:
        if l.name in had:
            l.show_render = had[l.name]
    print('SHOT', name, 'keep', len(keep))

def _setup():
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
    for l in S.view_layers[0].freestyle_settings.linesets:
        l.linestyle.thickness = max(0.5, l.linestyle.thickness * H / 4320.0)
    ng = S.compositing_node_group
    if ng is not None:
        for node in ng.nodes:
            if node.type == 'DILATEERODE':
                node.inputs['Size'].default_value = max(1, round(node.inputs['Size'].default_value * H / 2160))

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

FEM_COLORS = [('auburn', '', ''), ('black', '1C1714', ''), ('brown', '3B2418', ''),
              ('blonde', 'D8B77A', ''), ('silver', 'B9B8B5', '')]
MALE_COLORS = [('black', '1C1714', ''), ('blonde', 'C9A366', ''), ('brown', '5A3A24', ''),
               ('dye', '141212', '8A1F3C'), ('grey', '8F9096', '')]

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
    env = {'SIDES': '1', 'TUCK': '1', 'EST': 'hoop', 'HR': '0.011', 'SNX': '24', 'SNZ': '4',
           'DRESS': dress, 'DCOL': dcol, 'DMINISL': dminisl, 'FACE': '0',
           'NECK': '', 'HCOL': '', 'HDYE': '', 'LIPC': '', 'STONE': ''}
    env.update(FEM_STYLE_ENV[style])
    os.environ.update(env)
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
    hair_keep  = set(hnew + lnew + snew + pk) | set(_vis(r'Host\.hair_'))
    ear_keep   = set(_vis(r'Host\.V60_earring.*') + _vis(r'Host\.V61_.*'))
    dress_keep = set(dnew + anw)
    _hide(_vis(r'Host\.V62_.*'))          # default neckwear is not part of a look
    for nm, hx, dye in FEM_COLORS:
        os.environ['HCOL'] = hx
        os.environ['HDYE'] = dye
        step('haircol.py')
        shot('fem_hair_%s_%s' % (style, nm), hair_keep, _FRE['hair'])
    shot('fem_earring_%s' % style, ear_keep)
    shot('fem_outfit_%s' % plate, dress_keep, _FRE['dress'])
    if necks:
        prev = []
        for n in FEM_NECKS:
            _hide(prev)
            os.environ['NECK'] = n
            nw = step('neck.py')
            keep = set(nw) | set(_vis(r'Host\.V62_.*'))
            shot('fem_neck_%s' % n, keep)
            prev = list(keep)

def run_male(hair, hstyle, mg, watchrun=False):
    env = {'DBTN': '0', 'EST': 'none', 'TUCK': '0', 'SIDES': '1', 'FACE': '0',
           'MG': mg, 'HAIR': hair, 'HCOL': '', 'HDYE': '', 'WATCH': '',
           'STONE': '', 'LIPC': '', 'DOBJ': 'Host.body'}
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
    if watchrun:
        suffix = LOOK.rsplit('_', 1)[1]          # o1..o5
        prev = []
        for wt in MALE_WATCHES:
            _hide(prev)
            os.environ['WATCH'] = wt
            wnew = step('watch.py')
            keep = set(wnew) | set(_vis(r'Host\.watch_.*'))
            shot('male_watch_%s_%s' % (suffix, wt), keep)
            prev = list(keep)
        return
    outfit_keep = set(gnew + ganw)
    hair_keep = set(hnew + lnew + snew + pk) | set(_vis(r'Host\.hair_'))
    for nm, hx, dye in MALE_COLORS:
        os.environ['HCOL'] = hx
        os.environ['HDYE'] = dye
        step('haircol.py')
        shot('male_hair_%s_%s' % (hstyle, nm), hair_keep, _FRE['hair'])
    shot('male_outfit_%s' % hstyle if False else 'male_outfit_%s' % LOOK.rsplit('_', 1)[1].lower(), outfit_keep, _FRE['outfit'])

_setup()
if LOOK in FEM_LOOKS:
    run_fem(**FEM_LOOKS[LOOK])
elif LOOK in MALE_LOOKS:
    run_male(**MALE_LOOKS[LOOK])
elif LOOK == 'fem_hands':
    run_hands('fem', 'female')
elif LOOK == 'male_hands':
    run_hands('male', 'male')
print('CASTBAKE3 DONE', LOOK)
