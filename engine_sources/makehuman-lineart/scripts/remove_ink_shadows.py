"""Keep lifted facial ink visible without casting duplicate lines on skin."""
import bpy

p='Host' if 'HOST_' in bpy.data.filepath else 'Guest'
marks=[o for o in bpy.data.objects if o.name.startswith(p+'.V10_') and o.type=='MESH']
for obj in marks:
    obj.visible_shadow=False
    obj.visible_diffuse=False
    obj.visible_glossy=False
    obj.visible_transmission=False
    obj.visible_volume_scatter=False
assert len(marks)==(5 if p=='Host' else 7)
bpy.ops.wm.save_mainfile()
print('FACE_INK_SHADOWS_DISABLED',p,len(marks),flush=True)
