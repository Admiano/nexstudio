#!/usr/bin/env python3
# Cast plate packer v4: splits castbake3's full-scene renders into component
# plates by cryptomatte object id (z_<src>.exr; crypto*.RGBA = id/coverage
# pairs). A pixel ships iff the authored render itself attributed it to the
# plate's objects. Freestyle ink (which carries no id) ships when it sits over
# a kept surface or overhangs kept content onto empty background - ink over a
# foreign surface (face strokes under hair, strokes behind garments) dies.
# Renders are 1440x2160; plates ship 720x1080.
import os, glob, json
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation, binary_closing, distance_transform_edt
import OpenEXR, Imath

NEW = os.environ.get('BAKE_OUT', '/home/ubuntu/work/castbake3')
DST = os.environ.get('PLATE_DST', '/home/ubuntu/repos/nexstudio/public/cast')
WORK = os.environ.get('PLATE_WORK', '/home/ubuntu/work/castplates_v4')
CW, CH = 720, 1080

os.makedirs(WORK, exist_ok=True)
os.makedirs(DST, exist_ok=True)
shipped = set()

PLATES = json.load(open(os.path.join(NEW, 'plates.json')))

# ---------------------------------------------------------------- crypto
def _id_float(hexs):
    return np.uint32(int(hexs, 16)).view(np.float32)

_exrcache = {}

def exr_meta_and_channels(path):
    if path in _exrcache:
        return _exrcache[path]
    f = OpenEXR.File(path)
    man = {}
    for p in f.parts:
        for k in p.header.keys():
            if k.startswith('cryptomatte') and k.endswith('/manifest'):
                v = p.header[k]
                s = v.decode() if isinstance(v, bytes) else str(v)
                for name, hexs in json.loads(s).items():
                    man[name] = _id_float(hexs)
    pairs = []
    top = None
    for p in f.parts:
        pname = p.name() if callable(p.name) else p.name
        if pname.startswith('crypto'):
            cn = p.channels
            for a, b in (('r', 'g'), ('b', 'a')):
                ia = '%s.%s' % (pname, a); cb = '%s.%s' % (pname, b)
                if ia in cn and cb in cn:
                    pairs.append((np.asarray(cn[ia].pixels), np.asarray(cn[cb].pixels)))
            if top is None and '%s.r' % pname in cn:
                top = np.asarray(cn['%s.r' % pname].pixels)
    out = (man, pairs, top)
    _exrcache[path] = out
    return out

def owned_masks(src, keepnames):
    """per-pixel: mask of px owned by keep objects; primary id image."""
    man, pairs, top = exr_meta_and_channels(os.path.join(NEW, 'z_%s.exr' % src))
    keepids = {man[n] for n in keepnames if n in man}
    missing = [n for n in keepnames if n not in man]
    if missing:
        print('  WARN no crypto id for', missing[:6], '(%d)' % len(missing))
    m = np.zeros(top.shape if top is not None else pairs[0][0].shape, bool)
    for idc, cov in pairs:
        m |= (cov > 0) & np.isin(idc, list(keepids) or [np.float32(-1)])
    return m, keepids, top

INK = 140

def extract(src, keep, ink_rescue=True):
    """plate RGBA from full render <src>. keep=[] -> whole render."""
    png = np.array(Image.open(os.path.join(NEW, src + '.png')).convert('RGBA'))
    if not keep:
        return png
    m, keepids, top = owned_masks(src, keep)
    out = png.copy()
    if ink_rescue:
        ink = (png[..., 3] > 0) & (png[..., :3].sum(2) < INK)
        # ink over a kept surface, or hanging onto kept content from empty bg
        m |= ink & np.isin(top, list(keepids))
        m |= ink & (top == 0) & binary_dilation(m, iterations=4)
    out[..., 3] = np.where(m, png[..., 3], 0)
    return out

def ship(stem, rgba):
    im = Image.fromarray(rgba).resize((CW, CH), Image.LANCZOS)
    im.save(os.path.join(WORK, stem + '.png'))
    im.save(os.path.join(DST, stem + '.png'))
    shipped.add(stem)

# ---------------------------------------------------------------- lips (v2 reuse)
LIP_RENAMES = {'rose': 'red', 'crimson': 'berry', 'plum': 'coral', 'coral': 'nude'}
for f in sorted(os.listdir(DST)):
    if f.endswith('.png') and f[:-4].startswith('fem_lip_f'):
        parts = f[:-4].split('_')
        new = 'fem_lip_%s_%s.png' % (parts[2], LIP_RENAMES.get(parts[3], parts[3]))
        im = Image.open(os.path.join(DST, f)).convert('RGBA')
        im.save(os.path.join(WORK, new))
        shipped.add(new[:-4])

# ---------------------------------------------------------------- bodies (whole nude renders)
for png in sorted(glob.glob(os.path.join(NEW, '*_body_f*_*.png'))):
    stem = os.path.basename(png)[:-4]
    ship(stem, np.array(Image.open(png).convert('RGBA')))
print('bodies shipped')

# ---------------------------------------------------------------- plate extraction
for stem, spec in sorted(PLATES.items()):
    if stem.endswith('_bodyset'):
        continue
    ship(stem, extract(spec['src'], spec['keep']))
    print('plate', stem, '<-', spec['src'])

# ---------------------------------------------------------------- hands
# body-owned px in the look render, clipped to (bone hull U garment holes U
# edge notches near the hands). rgb comes from the matching nude body render.
def bone_hull(hulls):
    mask = np.zeros((CH * 2, CW * 2), bool)
    for side in ('L', 'R'):
        pts = np.array(hulls.get(side, []), float)
        if len(pts) >= 3:
            canvas = Image.fromarray(mask.astype('uint8') * 255)
            ImageDraw.Draw(canvas).polygon([tuple(p) for p in pts], fill=255)
            mask |= np.array(canvas) > 0
    return mask

SKINS = ['fair', 'light', 'medium', 'tan', 'brown', 'deep']
FEM_KIND_LOOK = {'sheath': 'long', 'maxi': 'bob', 'column': 'bangs',
                 'cocktail': 'bun', 'qipao': 'braid'}
for ch_ in ('fem', 'male'):
    hull_path = os.path.join(NEW, '%s_hands.hull.json' % ch_)
    if not os.path.exists(hull_path):
        continue
    if '%s_bodyset' % ch_ not in PLATES:
        print('no %s bodyset yet - hands skipped' % ch_)
        continue
    hull2x = bone_hull(json.load(open(hull_path)))
    handzone = binary_dilation(hull2x, iterations=160)
    bodyset = PLATES['%s_bodyset' % ch_]['keep']
    kinds = FEM_KIND_LOOK if ch_ == 'fem' else {k: k for k in ('o1', 'o2', 'o3', 'o4', 'o5')}
    for kind, look in kinds.items():
        src = '%s_look_%s' % (ch_, look)
        if not os.path.exists(os.path.join(NEW, 'z_%s.exr' % src)):
            continue
        ga2x, _, _ = owned_masks(src, PLATES['%s_outfit_%s' % (ch_, kind)]['keep'])
        holes = binary_closing(ga2x, iterations=30) & ~ga2x
        notches = (binary_closing(ga2x, iterations=30) & ~binary_dilation(ga2x, iterations=4)) & handzone
        region = hull2x | holes | notches
        bm, bodyids, top = owned_masks(src, bodyset)
        # hand px = where the renderer attributes the surface to the body,
        # inside the hand region - covers palms over cloth and bare fingers alike
        handpx = bm & region
        png2k = np.array(Image.open(os.path.join(NEW, src + '.png')).convert('RGBA'))
        ink = (png2k[..., 3] > 0) & (png2k[..., :3].sum(2) < INK)
        handpx |= ink & region & np.isin(top, list(bodyids))
        for s in SKINS:
            body = np.array(Image.open(os.path.join(
                NEW, '%s_body_f0_%s.png' % (ch_, s))).convert('RGBA'))
            out = body.copy()
            fade = np.clip(distance_transform_edt(handpx) / 6.0, 0.0, 1.0)
            out[..., 3] = (body[..., 3] * handpx * fade).astype('uint8')
            fn = '%s_hands_%s_%s.png' % (ch_, kind, s)
            im = Image.fromarray(out).resize((CW, CH), Image.LANCZOS)
            im.save(os.path.join(WORK, fn)); im.save(os.path.join(DST, fn))
            shipped.add(fn[:-4])
print('hands shipped')

# ---------------------------------------------------------------- stale sweep
keep_files = set(shipped) | {n[:-4] for n in os.listdir(WORK) if n.endswith('.png')}
for f in os.listdir(DST):
    stem = f[:-4]
    if not f.endswith('.png'):
        continue
    if stem in keep_files:
        continue
    os.remove(os.path.join(DST, f))
    print('stale', f)
print('castpack4 done: %d plates' % len(shipped))
