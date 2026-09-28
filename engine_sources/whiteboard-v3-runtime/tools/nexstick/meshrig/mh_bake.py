"""Mesh-sprite baker — Blender-side. Renders transparent Freestyle line-art
PNG frames of the MakeHuman rig driven by a motion-vault clip.

Run inside Blender:
    blender -b <rig.blend> --python mh_bake.py -- \
        --vault <vault.json> --clip <CLIP> --out <dir> \
        [--start 0] [--end N] [--res 300x400] [--cam side|front|three] \
        [--mirror]

Retargeting: vault supplies joint POSITIONS (meters, Y-up). Per driven bone:
COPY_LOCATION to the joint empty + DAMPED_TRACK toward the child joint, plus
a ONE-TIME scale factor = vault segment length / bone rest length, so every
frame lands on the joints without per-frame rubber-banding. Undriven bones
(fingers, face, sub-segment, head/neck) rigidly follow their parents.
"""
import bpy, json, argparse, sys, math
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument('--vault', required=True)
ap.add_argument('--clip', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--start', type=int, default=0)
ap.add_argument('--end', type=int, default=-1)
ap.add_argument('--res', default='300x400')
ap.add_argument('--cam', default='side')
ap.add_argument('--mirror', action='store_true')
ap.add_argument('--fps', type=float, default=24.0)
a = ap.parse_args(argv)

v = json.load(open(a.vault)); J = v['joints']
c = v['clips'][a.clip]
nfr = len(c['frames'])
end = nfr - 1 if a.end < 0 else min(a.end, nfr - 1)
scene = bpy.context.scene
arm = bpy.data.objects['MH_RIG']; mesh = bpy.data.objects['MH_BODY']

S = 10.0
def J3(n, fr):
    p = c['frames'][fr][J.index(n)]; return Vector((p[0] * S, -p[2] * S, p[1] * S))

_DELTA = None
def anchor(fr):
    global _DELTA
    _DELTA = arm.data.bones['root'].matrix_local.translation - J3('pelvis', fr)
def jp(spec, fr): return J3(spec, fr) + _DELTA

BONES = {
 'root': ('pelvis', None),
 'spine05': ('pelvis', 'spine'),
 'spine02': ('chest', 'neck'),
}
for side, sfx in (('l', '.L'), ('r', '.R')):
    BONES.update({
     f'clavicle{sfx}': (f'clavicle_{side}', f'shoulder_{side}'),
     f'upperarm01{sfx}': (f'shoulder_{side}', f'elbow_{side}'),
     f'lowerarm01{sfx}': (f'elbow_{side}', f'wrist_{side}'),
     f'upperleg01{sfx}': (f'hip_{side}', f'knee_{side}'),
     f'lowerleg01{sfx}': (f'knee_{side}', f'ankle_{side}'),
     f'foot{sfx}': (f'ankle_{side}', f'toe_{side}'),
    })

emp = {}
def empty(name):
    o = bpy.data.objects.new(name, None); o.empty_display_size = 0.3
    scene.collection.objects.link(o); return o
for bn, (hs, ds) in BONES.items():
    eh = empty('e_h_' + bn); emp[bn] = [eh, None]
    pb = arm.pose.bones[bn]
    cl = pb.constraints.new('COPY_LOCATION'); cl.target = eh
    cl.target_space = 'WORLD'; cl.owner_space = 'WORLD'; cl.use_offset = False
    if ds:
        ed = empty('e_d_' + bn); emp[bn][1] = ed
        st = pb.constraints.new('DAMPED_TRACK'); st.target = ed; st.track_axis = 'TRACK_Y'

_K_DONE = False
def calibrate(fr):
    for bn, (hs, ds) in BONES.items():
        if not ds: continue
        bd = arm.data.bones[bn]
        k = max((jp(ds, fr) - jp(hs, fr)).length / max(bd.length, 1e-4), 0.2)
        arm.pose.bones[bn].scale = (1.0, k, 1.0)
def pose_frame(fr):
    global _K_DONE
    if _DELTA is None: anchor(fr)
    if not _K_DONE:
        calibrate(fr); _K_DONE = True
    for bn, (hs, ds) in BONES.items():
        emp[bn][0].location = jp(hs, fr)
        if ds: emp[bn][1].location = jp(ds, fr)

# --- render setup ---
for o in list(bpy.data.objects):
    if o.name != 'MH_BODY' and o.type in ('MESH', 'LIGHT'):
        bpy.data.objects.remove(o)
for p in mesh.data.polygons: p.use_smooth = True
mat = bpy.data.materials.new('hold'); mat.use_nodes = True
nt = mat.node_tree; nt.nodes.clear()
outn = nt.nodes.new('ShaderNodeOutputMaterial')
hold = nt.nodes.new('ShaderNodeHoldout')
nt.links.new(hold.outputs['Holdout'], outn.inputs['Surface'])
if mesh.data.materials: mesh.data.materials[0] = mat
else: mesh.data.materials.append(mat)
scene.render.engine = 'BLENDER_EEVEE'
scene.render.use_freestyle = True
rw, rh = (int(x) for x in a.res.split('x'))
scene.render.resolution_x = rw; scene.render.resolution_y = rh
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
vl = scene.view_layers[0]; vl.use_freestyle = True
ls = vl.freestyle_settings.linesets[0] if vl.freestyle_settings.linesets else vl.freestyle_settings.linesets.new('ls')
ls.select_silhouette = True; ls.select_border = True; ls.select_contour = True
ls.select_crease = False
ls.linestyle.thickness = max(rw, rh) / 230.0

camd = bpy.data.cameras.new('cam'); camd.type = 'ORTHO'
camd.ortho_scale = 17.0
cam = bpy.data.objects.new('cam', camd); scene.collection.objects.link(cam)
if a.cam == 'side':
    cam.location = (26, 0.3, 0.5)
elif a.cam == 'front':
    cam.location = (0.0, -26, 0.5)
else:
    cam.location = (10, -24, 1.0)
cam.rotation_euler = (Vector((0, 0, 0.5)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

import os
os.makedirs(a.out, exist_ok=True)
for fr in range(a.start, end + 1):
    pose_frame(fr); scene.frame_set(fr); bpy.context.view_layer.update()
    scene.render.filepath = os.path.join(a.out, 'f%04d.png' % fr)
    bpy.ops.render.render(write_still=True)
meta = {'clip': a.clip, 'frames': end + 1, 'fps': a.fps, 'sourceFps': float(c['fps']),
        'res': [rw, rh], 'cam': a.cam}
json.dump(meta, open(os.path.join(a.out, 'meta.json'), 'w'))
print('BAKED', a.clip, 'frames', end + 1 - a.start)
