import bpy,sys,os,time
from bpy_extras.object_utils import world_to_camera_view
S=bpy.context.scene
S.render.resolution_percentage=100; S.render.image_settings.file_format='PNG'
mod=os.environ.get('MOD')
if mod: exec(open(mod).read())
rig=bpy.data.objects['Host.rig']; cam=S.camera
d=sys.argv[-1]; os.makedirs(d,exist_ok=True); tag=os.environ.get('TAG','x')
for f in [int(x) for x in os.environ['FR'].split(',')]:
    t=time.time(); S.frame_set(f)
    h=rig.matrix_world@rig.pose.bones['head'].head
    top=rig.matrix_world@rig.pose.bones['head'].tail
    c=world_to_camera_view(S,cam,h*float(os.environ.get("CA","0.75"))+top*(1-float(os.environ.get("CA","0.75")))); ht=0.075*S.render.resolution_x/S.render.resolution_y
    w=float(os.environ.get("CW","0.05"))
    S.render.use_border=True; S.render.use_crop_to_border=True
    S.render.border_min_x=c.x-w; S.render.border_max_x=c.x+w
    S.render.border_min_y=c.y-w*S.render.resolution_x/S.render.resolution_y*1.2; S.render.border_max_y=c.y+w*S.render.resolution_x/S.render.resolution_y*1.0
    S.render.filepath='%s/%s_%04d.png'%(d,tag,f); bpy.ops.render.render(write_still=True); print('FACE',f,round(time.time()-t,1),flush=True)
