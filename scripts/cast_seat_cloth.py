"""Seated skirt drape: simulate skirts as cloth through a stand-to-sit, with pre-roll.

    blender -b timeline.blend --python scripts/cast_seat_cloth.py -- out.blend END_FRAME \
        [--chair seats.json] [--seat-frame N] [--seat-height 0.45]

The timeline must start standing so the cloth settles before the sit. Garments with
`castFabric` materials whose vertices mostly follow leg bones are treated as skirts:
everything above the hips stays skinned (pinned), the skirt below hangs free. Left/right
leg weights are averaged so the goal shape is one sheet across both legs, and the body
mask under the garment is switched off so the hidden body collides (it stays covered).
With --chair, the chair from cast_chair.py is placed under the seated pelvis as a collider.
"""
import bpy,sys,json
from pathlib import Path

def _arg(argv,name,default=None):
    return argv[argv.index(name)+1] if name in argv else default

def setup(chair=None,seat_frame=1,seat_height=.45,end=250):
    s=bpy.context.scene;rig=bpy.data.objects['Host.rig'];body=bpy.data.objects['Host.body']
    if chair:
        sys.path.insert(0,str(Path(__file__).resolve().parent));import cast_chair
        s.frame_set(seat_frame);bpy.context.view_layer.update();pv=rig.matrix_world@rig.pose.bones['root'].head
        cj=json.load(open(chair));cast_chair.place(cj['source'],cj['seats'][0],(pv.x,pv.y),seat_height=seat_height,collide=True)
    c=body.modifiers.new('castSeatCollision','COLLISION')
    while body.modifiers.find(c.name)>1:body.modifiers.move(body.modifiers.find(c.name),body.modifiers.find(c.name)-1)
    body.collision.thickness_outer=.006;body.collision.cloth_friction=1
    hipz=(rig.matrix_world@rig.data.bones['upperleg01.L'].head_local).z;done=[]
    for o in [o for o in bpy.data.objects if o.type=='MESH' and not o.hide_render and any(m and m.get('castFabric') for m in o.data.materials)]:
        names={g.index:g.name for g in o.vertex_groups};pin=o.vertex_groups.new(name='castSeatPin');legv=0
        for v in o.data.vertices:
            tot=sum(g.weight for g in v.groups) or 1;leg=sum(g.weight for g in v.groups if 'leg' in names[g.group])/tot
            legv+=leg>.5;z=(o.matrix_world@v.co).z
            pin.add([v.index],max(0,min(1,(z-(hipz+.02))/.10)) if leg>.2 else 1.0,'REPLACE')
        if legv<50:o.vertex_groups.remove(pin);continue
        mk=body.modifiers.get('Delete.'+o.name.removeprefix('Host.'))
        if mk:mk.show_render=mk.show_viewport=False
        gi={g.name:g for g in o.vertex_groups}
        for n,gl in gi.items():
            if not n.endswith('.L') or not any(k in n for k in('leg','foot','toe')):continue
            gr=gi.get(n[:-2]+'.R')
            if not gr:continue
            for v in o.data.vertices:
                w={e.group:e.weight for e in v.groups};m=(w.get(gl.index,0)+w.get(gr.index,0))/2
                if m>0:gl.add([v.index],m,'REPLACE');gr.add([v.index],m,'REPLACE')
        cl=o.modifiers.new('castSeatCloth','CLOTH');o.modifiers.move(o.modifiers.find(cl.name),o.modifiers.find('Armature')+1)
        st=cl.settings;st.quality=6;st.mass=.25;st.tension_stiffness=st.compression_stiffness=12;st.shear_stiffness=6
        # stiff enough to span knee to knee instead of wrapping each thigh
        st.bending_stiffness=3;st.air_damping=1.5;st.effector_weights.gravity=1
        # let the fabric give a little as the hips flex so the hem stays near the knees
        for fr,v in ((1,0.0),(max(2,seat_frame-72),0.0),(seat_frame,-0.12)):
            st.shrink_min=v;st.keyframe_insert('shrink_min',frame=fr)
        st.vertex_group_mass='castSeatPin';st.pin_stiffness=1
        cl.collision_settings.distance_min=.006;cl.collision_settings.collision_quality=3
        cl.point_cache.frame_start=1;cl.point_cache.frame_end=end;done.append(o.name)
    return done

def bake(end):
    s=bpy.context.scene
    for f in range(1,end+1):s.frame_set(f)
    for o in bpy.data.objects:
        m=o.modifiers.get('castSeatCloth')
        if m:
            with bpy.context.temp_override(point_cache=m.point_cache,object=o):bpy.ops.ptcache.bake_from_cache()

if __name__=='__main__':
    a=sys.argv[sys.argv.index('--')+1:];out,end=a[0],int(a[1])
    done=setup(_arg(a,'--chair'),int(_arg(a,'--seat-frame',1)),float(_arg(a,'--seat-height',.45)),end)
    print('CAST_SEAT_CLOTH',json.dumps(done),flush=True)
    bake(end);bpy.ops.wm.save_as_mainfile(filepath=out);print('CAST_SEAT_CLOTH_DONE',flush=True)
