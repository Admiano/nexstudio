import bpy,sys,os,time
S=bpy.context.scene
S.render.resolution_percentage=int(os.environ.get('PCT','50'))
S.render.image_settings.file_format='PNG'
mod=os.environ.get("MOD")
if mod: exec(open(mod).read())
d=sys.argv[-1]; os.makedirs(d,exist_ok=True)
for f in [int(x) for x in os.environ['FR'].split(',')]:
    t=time.time(); S.frame_set(f); S.render.filepath='%s/%s_%04d.png'%(d,os.environ.get("TAG","la"),f)
    bpy.ops.render.render(write_still=True); print('LA',f,round(time.time()-t,1),flush=True)
