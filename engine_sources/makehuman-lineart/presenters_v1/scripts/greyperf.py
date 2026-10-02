import bpy,sys,os
from mathutils import Vector
S=bpy.context.scene
exec(open(os.environ['MOD']).read())
S.render.engine='BLENDER_WORKBENCH'; S.render.use_freestyle=False
S.display.shading.light='STUDIO'; S.display.shading.color_type=os.environ.get('CT','MATERIAL')
S.render.resolution_x=540; S.render.resolution_y=720; S.render.resolution_percentage=100; S.render.image_settings.file_format='PNG'
for o in bpy.data.objects:
    if o.type in ('GPENCIL','GREASEPENCIL'): o.hide_render=True
rig=bpy.data.objects['Host.rig']; S.frame_set(1)
c=rig.matrix_world@rig.pose.bones['spine03'].head+Vector((0,0,-0.1))
cams={}
for v,off in {'front':Vector((0,-2.8,0.05)),'side':Vector((-2.6,-1.1,0.05))}.items():
    cam=bpy.data.objects.new('GC_'+v,bpy.data.cameras.new('GC_'+v)); S.collection.objects.link(cam); cam.data.lens=40
    cam.location=c+off; cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler(); cams[v]=cam
d=sys.argv[-1]
f0,f1=[int(x) for x in os.environ.get('FRR','0-0').split('-')]
for f in ([int(x) for x in os.environ['FRL'].split(',')] if os.environ.get('FRL') else range(f0,f1+1)):
    S.frame_set(f)
    for v,cam in cams.items():
        os.makedirs(d+'/'+v,exist_ok=True); S.camera=cam; S.render.filepath='%s/%s/f_%04d.png'%(d,v,f)
        bpy.ops.render.render(write_still=True)
    print('GF',f,flush=True)
