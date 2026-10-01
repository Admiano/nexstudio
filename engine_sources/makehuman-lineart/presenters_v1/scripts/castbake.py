# Cast plate baker: renders per-component alpha layers for the NexStudio avatar builder.
# Usage: SCN=<scene> JB=<job> OUT=<dir> [W=1440 H=2160 FR=27] blender --background --python scripts/castbake.py
# Runs from presenters_v1/ (needs scripts/* on relative path + PV1 env).
#
# Camera + render recipe mirror render_presenter_alpha_v2.py exactly (shipped
# thigh-up framing, camera-facing, frame 27) so preview plates ARE the shipped
# characters. Bake at 2x the 720x1080 canvas and downscale in castpack for
# clean edges.
#
# Isolation strategy: hide_render/hide_viewport do NOT reliably suppress meshes
# here (bone/vertex-parented objects leak - Host.high-poly renders regardless).
# Deletion is airtight, so each option reloads the scene and deletes every mesh
# outside its keep set, except modifier targets the kept meshes still need
# (hair SHRINKWRAPs onto body + dress_01, dress_lines SURFACE_DEFORMs to proxy).
import bpy, os, sys

PV1  = os.environ.get('PV1', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JB   = os.environ['JB']
OUT  = os.environ.get('OUT', os.path.join(PV1, 'castbake'))
W    = int(os.environ.get('W', '1440'))
H    = int(os.environ.get('H', '2160'))
FRAME= int(os.environ.get('FR', '27'))
SCN  = os.environ['SCN']
os.makedirs(OUT, exist_ok=True)

# env keys the pipeline scripts read; cleared before every exec
_ENV_KEYS = ('FACE','STONE','LIPC','HCOL','HDYE','NECK','WATCH','HAIR','HPK','DRESS','DOBJ','DCOL','MG','NDROP','DYZ0','DYZ1','DYK','HHOLE','DMINISL','WTILT','WSEATM')

def _reset_env():
    for k in _ENV_KEYS:
        os.environ.pop(k, None)
    os.environ['PV1'] = PV1

def _sc(name, **env):
    _reset_env()
    for k, v in env.items():
        os.environ[k] = str(v)
    p = os.path.join(PV1, 'scripts', name)
    g = {'__name__': '__main__', '__file__': p}
    exec(compile(open(p).read(), p, 'exec'), g)

def _lin(hexs):
    _l = lambda c: (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return [_l(int(hexs.lstrip('#')[i:i+2], 16) / 255) for i in (0, 2, 4)]

def _load():
    bpy.ops.wm.open_mainfile(filepath=SCN)
    S = bpy.context.scene
    S.render.film_transparent = True
    S.render.resolution_x, S.render.resolution_y = W, H
    S.render.resolution_percentage = 100
    # shipped plate framing (render_presenter_alpha_v2.py): thigh-up, facing
    # camera, presenter right-of-centre with the left half clear
    cam = S.camera
    cam.location = (-0.42, -5.0, 1.325)
    cam.rotation_euler = (1.5707963, 0, 0)
    cam.data.ortho_scale = 1.25 * max(1.0, W / H)
    S.cycles.samples = 12
    S.cycles.use_adaptive_sampling = True
    S.cycles.use_denoising = True
    S.frame_set(FRAME)
    bpy.context.view_layer.update()
    for ls in S.view_layers[0].freestyle_settings.linesets:
        ls.linestyle.thickness = max(0.5, ls.linestyle.thickness * H / 4320.0)
    ng = S.compositing_node_group
    if ng is not None:
        for node in ng.nodes:
            if node.type == 'DILATEERODE':
                native = node.inputs['Size'].default_value
                node.inputs['Size'].default_value = max(1, round(native * H / 2160))

def _match(name, patterns):
    return any(name == p or (p.endswith('*') and name.startswith(p[:-1])) for p in patterns)

def _aux(kept):
    # modifier targets + parent meshes the kept objects still evaluate against
    aux = set()
    for ko in kept:
        for m in getattr(ko, 'modifiers', []):
            for a in ('object', 'target', 'mirror_object'):
                t = getattr(m, a, None)
                if t is not None and t.type == 'MESH' and t not in kept:
                    aux.add(t)
        p = ko.parent
        while p is not None:
            if p.type == 'MESH' and p not in kept:
                aux.add(p)
            p = p.parent
    return aux

def _iso(keep, extra_aux=()):
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    kept = [o for o in meshes if _match(o.name, keep)]
    aux = _aux(kept) | {o for o in meshes if _match(o.name, extra_aux) and o not in kept}
    for o in meshes:
        if o in kept:
            o.hide_render = o.hide_viewport = False
        elif o in aux:
            o.hide_render = o.hide_viewport = True
            o.visible_camera = False   # evaluated but never paints a pixel
        else:
            bpy.data.objects.remove(o)
    bpy.context.view_layer.update()
    print('ISO kept:', [o.name for o in kept], 'aux:', [o.name for o in aux])

def _shot(name):
    bpy.context.scene.render.filepath = os.path.join(OUT, name + '.png')
    bpy.ops.render.render(write_still=True)
    print('SHOT', name)

def _del_pref(pref):
    for o in [o for o in bpy.data.objects if pref in o.name]:
        bpy.data.objects.remove(o)

# keep sets = the scene's own visible default (verified via hide-state probe)
FEM_BODY = ['Host.body', 'Host.high-poly', 'Host.eyebrow001', 'Host.eyelashes01',
    'Host.teeth_base', 'Host.lineart_pupil.L', 'Host.lineart_pupil.R',
    'Host.lineart_lower_legs', 'Host.lineart_shoe.L', 'Host.lineart_shoe.R',
    'Host.V10_ear_L', 'Host.V10_ear_R', 'Host.V10_jaw', 'Host.V10_nose_L', 'Host.V10_nose_R',
    'Host.V11_mouth_interior', 'Host.V11_mouth_teeth', 'Host.V11_mouth_tongue',
    'Host.V59_face_art', 'Host.V59_face_frame',
    'Host.V60_ear_fill_R', 'Host.V60_ear_inner_R', 'Host.V60_ear_line_R', 'Host.V7_crown_detail']
MALE_BODY = ['Host.body', 'Host.high-poly', 'Host.eyebrow001', 'Host.teeth_base',
    'Host.lineart_lower_legs', 'Host.V10_ear_L', 'Host.V10_ear_R', 'Host.V11_mouth_interior',
    'Host.V59_face_art', 'Host.V59_face_frame',
    'Host.V60_ear_fill_R', 'Host.V60_ear_inner_R', 'Host.V60_ear_line_R']
EARRING = ['Host.V60_earring_R', 'Host.V60_earring_rim_R']
WATCH   = ['Host.watch_*']

SKINS = {'fair':'F7E1D3', 'light':'F1D7C8', 'medium':'E0B48F', 'tan':'C99A6E', 'brown':'9E6B4A', 'deep':'6A4431'}
HCOLS = {'auburn':'9A4A2E', 'raven':'1C1714', 'brownd':'3B2418', 'blonde':'D8B77A', 'silver':'B9B8B5'}

# (mesh, peek): 'swept' bakes identical to long (its peek only strokes a
# hairline) and the hidden afro mesh reads as a smooth cap on her and sits at
# the female head position (off-frame) on him - neither is offered. Real style
# variety needs the MH asset library, which is not on this machine.
FEM_HAIRS = {
  'long':  ('Host.hair_culturalibre_hair_01', None),
  'bun':   ('Host.hair_culturalibre_hair_01', 'bun'),
  'braid': ('Host.hair_culturalibre_hair_01', 'french_braid'),
}
MALE_HAIRS = {
  'quiff': ('Host.hair_elvs_maxwell_hair', None),
}
FEM_OUTFITS = {
  'sheath':  ['Host.mindfront_f_dress_11', 'Host.V64_dress_lines'],
  'dress01': ['Host.mindfront_f_dress_01'],
  'suit':    ['Host.female_elegantsuit01'],
}
MALE_PARTS = {
  'top':    ['Host.elvs_male_shirt_untucked_bd1', 'Host.V64_dress_lines'],
  'bottom': ['Host.mindfront_male_trousers_2', 'Host.V64_dress_lines.001'],
  'shoes':  ['Host.mindfront_shoes_monk_strap_male', 'Host.V64_dress_lines.002'],
}
NECKS   = ['fine', 'pendant', 'pearls', 'choker', 'scarf']
WATCHES = ['dress', 'analog', 'chrono', 'smart', 'digital']

HAND_VG = ('hand', 'finger', 'wrist', 'nail', 'metac')

def _hand_vg(name):
    return any(k in name.lower() for k in HAND_VG)

def hands_job(prefix):
    # Hands sit in front of the garments at the talking frame, so they need
    # their own plate drawn over the outfit. rest = the body with hand verts
    # deleted, leaving every occluding garment in place.
    for sk, hexv in SKINS.items():
        _load()
        body = bpy.data.objects['Host.body']
        _sc('skintone.py', STONE=hexv)
        _shot(f'{prefix}_hands_{sk}.full')
        dup = body.copy()
        dup.data = body.data.copy()
        dup.name = 'Host.body_nohands'
        bpy.context.collection.objects.link(dup)
        vg = {g.index for g in dup.vertex_groups if _hand_vg(g.name)}
        bpy.context.view_layer.objects.active = dup
        dup.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        for v in dup.data.vertices:
            if any(g.group in vg for g in v.groups):
                v.select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.delete(type='VERT')
        bpy.ops.object.mode_set(mode='OBJECT')
        dup.select_set(False)
        body.hide_render = True
        bpy.context.view_layer.update()
        _shot(f'{prefix}_hands_{sk}.rest')

def bodies(prefix, keep):
    for face in (0, 1, 2):
        _load()
        if face:
            _sc('facevar.py', FACE=face)
        for sk, hexv in SKINS.items():
            _sc('skintone.py', STONE=hexv)
            _iso(keep)
            _shot(f'{prefix}_body_f{face}_{sk}')

def _delete(keep):
    for o in [o for o in bpy.data.objects if o.type == 'MESH' and _match(o.name, keep)]:
        bpy.data.objects.remove(o)
    bpy.context.view_layer.update()

# Difference-keyed plates: the component bakes as full.minus.rest, and castpack
# keeps only the pixels where removing it changed the image - so hair behind
# the head, an earring behind hair, or a watch under a cuff never reaches the
# plate (the isolated render can't see occluders once they're hidden).
HAIR_COMP_EXTRA = ['Host.hp_*', 'Host.ink_hair_lock*']

def hairs(prefix, table, earring):
    for style, (mesh, peek) in table.items():
        _load()
        for ck, hexv in HCOLS.items():
            _del_pref('Host.hp_')
            if peek:
                _sc('hairpeek.py', HAIR=peek, HCOL=hexv, HPK='1')
            _sc('haircol.py', HCOL=hexv)
            _shot(f'{prefix}_hair_{style}_{ck}.full')
        # hair rest: earring still present so the diff only isolates hair
        _delete([mesh] + HAIR_COMP_EXTRA)
        _shot(f'{prefix}_hair_{style}.rest')
        if earring:
            # one earring plate per style (the pairing is authored per
            # hairstyle); rest needs hair present, so reload the look
            _load()
            if peek:
                _sc('hairpeek.py', HAIR=peek, HCOL=HCOLS['silver'], HPK='1')
            _sc('haircol.py', HCOL=HCOLS['silver'])
            _shot(f'{prefix}_earring_{style}.full')
            _delete(EARRING)
            _shot(f'{prefix}_earring_{style}.rest')

def outfits_fem():
    for name, keep in FEM_OUTFITS.items():
        _load()
        _iso(keep)
        _shot(f'fem_outfit_{name}')

def parts_male():
    for name, keep in MALE_PARTS.items():
        _load()
        _iso(keep)
        _shot(f'male_{name}')

def necks():
    for n in NECKS:
        _load()
        _sc('neck.py', NECK=n)
        _shot(f'fem_neck_{n}.full')
        _delete(['Host.V62_*'])
        _shot(f'fem_neck_{n}.rest')

def watches():
    for w in WATCHES:
        _load()
        _sc('watch.py', WATCH=w)
        _shot(f'male_watch_{w}.full')
        _delete(WATCH)
        _shot(f'male_watch_{w}.rest')

def lips(prefix, body):
    cols  = ['', 'B3202A', '8A2A4E', 'E0664F', 'B8826F']
    names = ['rose', 'crimson', 'plum', 'coral', 'nude']
    for face in (0, 1, 2):
        _load()
        if face:
            _sc('facevar.py', FACE=face)
        _sc('skintone.py', STONE='F1D7C8')
        _iso(body)
        _shot(f'{prefix}_lipbase_f{face}')
        for nm, c in zip(names, cols[1:]):
            _sc('lip.py', LIPC=c)
            _shot(f'{prefix}_lip_f{face}_{nm}')

jobs = {
  'fem_body':   lambda: bodies('fem', FEM_BODY),
  'male_body':  lambda: bodies('male', MALE_BODY),
  'fem_hands':  lambda: hands_job('fem'),
  'male_hands': lambda: hands_job('male'),
  'fem_hair':   lambda: hairs('fem', FEM_HAIRS, True),
  'male_hair':  lambda: hairs('male', MALE_HAIRS, False),
  'fem_outfit': outfits_fem,
  'male_parts': parts_male,
  'fem_neck':   necks,
  'male_watch': watches,
  'fem_lips':   lambda: lips('fem', FEM_BODY),
  'male_lips':  lambda: lips('male', MALE_BODY),
}
jobs[JB]()
print('CASTBAKE DONE', JB)
