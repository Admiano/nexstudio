import bpy,os,sys
exec(open(os.environ['PV1']+'/'+os.environ['MODF']).read())
for _vl in bpy.context.scene.view_layers:
    for _l in _vl.freestyle_settings.linesets:
        if _l.collection: _l.collection.use_fake_user=True
bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[-1],compress=True)
print('SAVED',sys.argv[-1])
