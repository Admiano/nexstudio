# MakeHuman .mhclo fitting helpers for the presenters_v1 pipeline.
# A .mhclo file describes a proxy mesh as references into the hm08 base
# mesh: each vertex line is `v1 v2 v3 w1 w2 w3 dx dy dz` where the fitted
# position is the weighted interpolation of the three referenced body
# vertices plus a small offset scaled by the body's actual proportions.
# `l_shear_*` assets carry their own anchor measurements; `x/y/z_scale`
# assets measure span lengths on the reference base mesh instead.
import os, glob
from mathutils import Vector

MH_ROOT = os.environ.get('MH_ROOT', '/home/ubuntu/mh_assets')


def asset(kind, name):
    hits = sorted(glob.glob(os.path.join(MH_ROOT, '*', kind, name, name + '.mhclo')))
    hits += sorted(glob.glob(os.path.join(MH_ROOT, kind, name, name + '.mhclo')))
    if not hits and kind != 'clothes':
        hits = sorted(glob.glob(os.path.join(MH_ROOT, '*', 'clothes', name, name + '.mhclo')))
    if not hits:
        raise FileNotFoundError('no mhclo for %s/%s under %s' % (kind, name, MH_ROOT))
    return hits[0]


def shaped_coords(body):
    mw = body.matrix_world.copy()
    keys = body.data.shape_keys
    if not keys:
        return [mw @ v.co for v in body.data.vertices]
    basis = keys.key_blocks[0].data
    targets = [k for k in keys.key_blocks[1:] if k.name.startswith('$') and k.value]
    result = []
    for i, vertex in enumerate(basis):
        co = vertex.co.copy()
        for key in targets:
            co += (key.data[i].co - vertex.co) * key.value
        result.append(mw @ co)
    return result


def _parse(path):
    refs = []
    sc = {}
    obj_file = None
    inverts = False
    for line in open(path):
        p = line.split()
        if not p:
            continue
        k = p[0]
        if k == 'verts':
            inverts = True
            continue
        if k == 'delete_verts':
            inverts = False
            continue
        if inverts:
            if (k[0].isdigit() or k[0] == '-') and len(p) >= 9:
                refs.append(((int(p[0]), int(p[1]), int(p[2])),
                             (float(p[3]), float(p[4]), float(p[5])),
                             (float(p[6]), float(p[7]), float(p[8]))))
            elif k.isdigit():
                # unweighted clothing vertex: one line index per obj vertex,
                # welded 1:1 to the named body vertex
                i = int(k)
                refs.append(((i, i, i), (1.0, 0.0, 0.0), (0.0, 0.0, 0.0)))
            continue
        if k == 'obj_file':
            obj_file = p[1]
        elif k in ('x_scale', 'y_scale', 'z_scale'):
            sc[k[0]] = (int(p[1]), int(p[2]), float(p[3]))
        elif k in ('l_shear_x', 'l_shear_y', 'l_shear_z'):
            sc.setdefault('shear', {})[k[-1]] = (int(p[1]), int(p[2]), float(p[3]), float(p[4]))
    return sc, refs, obj_file


def load_mhclo(path):
    sc, refs, obj_file = _parse(path)
    objp = os.path.join(os.path.dirname(path), obj_file) if obj_file else None
    return sc, refs, objp


def load_obj(objp):
    verts, faces = [], []
    for line in open(objp):
        if line.startswith('v '):
            verts.append(tuple(map(float, line.split()[1:4])))
        elif line.startswith('f '):
            faces.append(tuple(int(t.split('/')[0]) - 1 for t in line.split()[1:]))
    return verts, faces


def fit(path, W):
    sc, refs, _ = _parse(path)
    if 'x' in sc:
        sx = abs(W[sc['x'][0]].x - W[sc['x'][1]].x) / sc['x'][2]
        sy = abs(W[sc['y'][0]].z - W[sc['y'][1]].z) / sc['y'][2]
        sz = abs(W[sc['z'][0]].y - W[sc['z'][1]].y) / sc['z'][2]
    else:
        sh = sc.get('shear', {})
        sx = abs(W[sh['x'][0]][0] - W[sh['x'][1]][0]) / abs(sh['x'][2] - sh['x'][3])
        sy = abs(W[sh['y'][0]][2] - W[sh['y'][1]][2]) / abs(sh['y'][2] - sh['y'][3])
        sz = abs(W[sh['z'][0]][1] - W[sh['z'][1]][1]) / abs(sh['z'][2] - sh['z'][3])
    return [W[a] * u + W[b] * v + W[c] * w + Vector((dx * sx, -dz * sz, dy * sy))
            for (a, b, c), (u, v, w), (dx, dy, dz) in refs], refs
