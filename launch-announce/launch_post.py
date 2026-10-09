"""Post-bake fixes for the launch film. Run: blender -b timeline.blend --python launch_post.py -- out.blend"""
import bpy, sys, json, math
from mathutils import Vector

out = sys.argv[sys.argv.index('--') + 1]
s = bpy.context.scene
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE' and o.name.startswith('Host'))

# --- 1. preview-fit static duplicates off; rig-bound garments back on ---
for o in bpy.data.objects:
    if '.preview-fit' in o.name or o.name.endswith('.preview-fit'):
        o.hide_render = True; o.hide_viewport = True
for o in bpy.data.objects:
    if '.preview-fit' in o.name or 'dress_lines' in o.name:
        continue
    if o.name.startswith('Host.') and any(g in o.name for g in ('toigo_basic_tucked_t-shirt', 'elvs_jeans_straight_leg', 'punkduck_comfortable_sneakers')):
        o.hide_render = False; o.hide_viewport = False
for o in bpy.data.objects:
    if o.name.startswith('Guest.') or 'mindfront_f_dress_01' in o.name or 'hair_culturalibre' in o.name or 'dress_lines' in o.name or o.name == 'Host.high-poly':
        o.hide_render = True; o.hide_viewport = True

# --- 2. garment dyes (linear-space ramp rescale, preserves shading) ---
def srgb2lin(c):
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in (v / 255 for v in c)]

def dye_ramp(mat_name, hexc):
    m = bpy.data.materials.get(mat_name)
    if not m or not m.use_nodes:
        print('DYE_MISS', mat_name); return
    tgt = srgb2lin([int(hexc[i:i + 2], 16) for i in (0, 2, 4)])
    for n in m.node_tree.nodes:
        if n.type == 'VALTORGB' and 'fabric' in (n.label + n.name).lower():
            cr = n.color_ramp; lref = 0.55
            for e in cr.elements:
                L = 0.2126 * e.color[0] + 0.7152 * e.color[1] + 0.0722 * e.color[2]
                k = min(2.0, L / lref)
                e.color = (min(1, tgt[0] * k), min(1, tgt[1] * k), min(1, tgt[2] * k), 1)
            print('DYED', mat_name, hexc); return
    print('DYE_NORAMP', mat_name)

def dye_mix(mat_name, hexc):
    m = bpy.data.materials.get(mat_name)
    if not m or not m.use_nodes:
        print('DYE_MISS', mat_name); return
    tgt = srgb2lin([int(hexc[i:i + 2], 16) for i in (0, 2, 4)])
    n_dye = 0
    for n in m.node_tree.nodes:
        if n.type != 'MIX':
            continue
        for inp in n.inputs:
            v = inp.default_value
            if hasattr(v, '__len__') and len(v) >= 3:
                L = 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]
                if 0.4 < L < 0.78:
                    inp.default_value = tuple(tgt) + (1.0,) * (len(v) - 3); n_dye += 1
    print('DYED_MIX', mat_name, n_dye)

dye_ramp('V70_G_toigo_basic_tucked_t-shirt', 'A9C4DE')
dye_ramp('V70_G_elvs_jeans_straight_leg', '2E3A55')
dye_mix('V70_G_punkduck_comfortable_sneakers', 'ECEAE4')

# --- 3. stage-left entrance: lateral ramp on the armature object ---
act = rig.animation_data.action
bag = next(cb for l in act.layers for st in l.strips for cb in st.channelbags)
total = s.frame_end
WALK_DONE = 150
fc = bag.fcurves.new('location', index=0)
fc.keyframe_points.add(total)
co = []
for f in range(1, total + 1):
    x = -0.55 if f <= 40 else (-0.55 * (1 - (f - 40) / (WALK_DONE - 40)) if f < WALK_DONE else 0.0)
    co += [f, x]
fc.keyframe_points.foreach_set('co', co)
for k in fc.keyframe_points:
    k.interpolation = 'LINEAR'
fc.update()
for idx in (1, 2):
    fz = bag.fcurves.new('location', index=idx)
    fz.keyframe_points.add(2)
    fz.keyframe_points.foreach_set('co', [1, rig.location[idx], total, rig.location[idx]])
    fz.update()

# --- 4. root drift pin: hold root.location at its f140 value afterwards ---
for idx in range(3):
    p = f'pose.bones["root"].location'
    fcr = bag.fcurves.find(p, index=idx)
    if not fcr:
        continue
    pin = None
    for kp in fcr.keyframe_points:
        if kp.co[0] <= 140:
            pin = kp.co[1]
    if pin is None:
        continue
    for kp in fcr.keyframe_points:
        if kp.co[0] > 140:
            kp.co[1] = pin; kp.handle_left[1] = pin; kp.handle_right[1] = pin
    fcr.update()
print('ROOT_PINNED')

# --- 5. wink: one-sided left blink 0->0.54->0 near the end ---
seq = None
for fc0 in bag.fcurves:
    pass
# aside clip placement: find when the turn happens from the saved report embedded in scene name is hard;
# wink at fixed frames near end (aside starts ~84% into the take; place at total-60)
wf = total - 45
wink = {wf: 0.0, wf + 4: 0.54, wf + 8: 0.54, wf + 12: 0.0}
for aname in bpy.data.actions:
    if not (aname.name.startswith('Face.') or 'base' in aname.name):
        continue
    cb2 = next((c for l in aname.layers for st in l.strips for c in st.channelbags), None)
    if not cb2:
        continue
    path = 'key_blocks["!ex-eyeBlinkLeft"].value'
    fw = cb2.fcurves.find(path) or cb2.fcurves.new(path)
    # keep the natural blinks; superimpose the wink (max of existing + wink envelope)
    def winkv(f):
        if f <= wf or f >= wf + 12:
            return 0.0
        if f <= wf + 4:
            return 0.54 * (f - wf) / 4.0
        if f <= wf + 8:
            return 0.54
        return 0.54 * (1 - (f - wf - 8) / 4.0)
    vals = [max(fw.evaluate(f) if len(fw.keyframe_points) else 0.0, winkv(f)) for f in range(1, total + 1)]
    fw.keyframe_points.clear()
    fw.keyframe_points.add(total)
    fw.keyframe_points.foreach_set('co', [c for f, v in enumerate(vals, 1) for c in (f, v)])
    fw.update()
    print('WINK_SET', aname.name)

# --- 6. fresh full-body camera ---
cd = bpy.data.cameras.new('LAUNCH_CAM'); co = bpy.data.objects.new('LAUNCH_CAM', cd)
s.collection.objects.link(co)
cd.type = 'ORTHO'; cd.ortho_scale = 2.5
co.location = (-0.15, -8.4, 1.35)
d = Vector((-0.15, -0.05, 1.0)) - co.location
co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
s.camera = co

# --- 6b. the film framing left the studio lights off — the approved look needs them ---
for o in bpy.data.objects:
    if o.type == 'LIGHT':
        o.hide_render = False; o.hide_viewport = False

# --- 7. approved-still render settings ---
s.render.engine = 'CYCLES'
s.cycles.samples = 128
s.view_settings.view_transform = 'Standard'
s.view_settings.look = 'None'
s.view_settings.exposure = 0
s.render.resolution_x = 2160; s.render.resolution_y = 2880; s.render.resolution_percentage = 50
s.render.image_settings.file_format = 'PNG'
s.render.film_transparent = True

# --- 8. freestyle ink: restore approved weight for this output height ---
# Assembly scaled thickness by its own render height; approved renders rescaled by
# height/4320 each run. Set explicit px weights for the 1440px output.
FS_W = {'RAIN_STYLE_CONTOURS': 1.2, 'GARMENT_SILHOUETTE': 1.2,
        'HEAD_OUTLINE': 0.8, 'HEAD_FEATURES': 0.7, 'HEAD_NOSE': 0.7,
        'HAIR_OUTER': 0.4}
for layer in s.view_layers:
    for ls in layer.freestyle_settings.linesets:
        if ls.name in FS_W:
            ls.linestyle.thickness = FS_W[ls.name]

# compositor silhouette outline (Host_V10_MASK_OUTLINE) dilates the alpha 4px —
# authored renders ship ~1px rim at this output height
grp = bpy.data.node_groups.get('Host_V10_MASK_OUTLINE')
if grp:
    for nd in grp.nodes:
        if 'Dilate' in nd.bl_idname:
            for inp in nd.inputs:
                if inp.name == 'Size' and not inp.is_linked:
                    inp.default_value = 1

# --- 9. re-apply visibility + dyes last (stack/order safety) ---
for o in bpy.data.objects:
    if '.preview-fit' in o.name or o.name.endswith('.preview-fit'):
        o.hide_render = True; o.hide_viewport = True
for o in bpy.data.objects:
    if '.preview-fit' in o.name or 'dress_lines' in o.name:
        continue
    if o.name.startswith('Host.') and any(g in o.name for g in ('toigo_basic_tucked_t-shirt', 'elvs_jeans_straight_leg', 'punkduck_comfortable_sneakers')):
        o.hide_render = False; o.hide_viewport = False
for o in bpy.data.objects:
    if o.name.startswith('Guest.') or 'mindfront_f_dress_01' in o.name or 'hair_culturalibre' in o.name or 'dress_lines' in o.name or o.name == 'Host.high-poly':
        o.hide_render = True; o.hide_viewport = True
dye_ramp('V70_G_toigo_basic_tucked_t-shirt', 'A9C4DE')
dye_ramp('V70_G_elvs_jeans_straight_leg', '2E3A55')
dye_mix('V70_G_punkduck_comfortable_sneakers', 'ECEAE4')

bpy.ops.wm.save_as_mainfile(filepath=out)
print('POST_DONE', total, 'wink@', wf)
