import bpy
_r=bpy.data.objects['Host.rig']
_ref=_r.copy(); _ref.data=_r.data.copy(); _ref.name='Ref.rig'
for _c in _r.users_collection: _c.objects.link(_ref)
_ref.hide_render=_ref.hide_viewport=True
