"""Match the male preset to its actual hair asset before grooming.

Some saved review scenes used a Maxwell/quiff mesh under another style label.
Fail closed if the correct source asset is unavailable; never silently label
that quiff as crop, cornrows, swept hair or afro.
"""
import bpy,runpy,os,math,json
from pathlib import Path
from mathutils import Vector

ASSETS={'afro':'afro01','crop':'short01','quiff':'elvs_maxwell_hair','braids':'elvs_braided_rows','swept':'elvs_grump_hair'}

def ensure_hair_selection(scene,character,style,colour=None,dye=''):
    if character!='male':return {'checked':False,'reason':'female saved presets already use distinct source assets'}
    candidates=[o for o in scene.objects if o.type=='MESH' and o.name.startswith('Host.hair_') and not o.hide_render]
    if style=='bald':
        hidden=[]
        for ob in scene.objects:
            if ob.name.startswith('Host.hair_') or ob.get('castGroomProfile') or ob.get('castGroomBinding') or ob.name.startswith('Host.ink_hair_lock_'):
                ob.hide_render=True;hidden.append(ob.name)
        return {'checked':True,'style':style,'visibleHair':0,'hidden':hidden}
    expected=ASSETS[style];correct=next((o for o in candidates if o.name.startswith('Host.hair_'+expected)),None)
    if correct:return {'checked':True,'style':style,'asset':expected,'sourceHair':correct.name,'repaired':False}
    root=Path(__file__).resolve().parents[1];assets=root/'engine_sources/makehuman-lineart/assets'
    match=next(iter(assets.glob('*/hair/'+expected+'/'+expected+'.mhclo')),None)
    if match is None:raise RuntimeError('CAST_HAIR_ASSET_STYLE_MISMATCH:'+style+':'+expected)
    fit=runpy.run_path(str(root/'engine_sources/makehuman-lineart/scripts/mhclo_fit.py'))
    body=bpy.data.objects['Host.body'];rig=bpy.data.objects['Host.rig'];oldframe=scene.frame_current;oldpose=rig.data.pose_position
    lights={o:o.data.energy for o in scene.objects if o.type=='LIGHT'}
    bg=scene.world.node_tree.nodes.get('Background');strength=bg.inputs['Strength'].default_value if bg else None
    oldsource=candidates[0] if candidates else bpy.data.objects['Host.hair_elvs_maxwell_hair']
    if colour is None:
        # Native review files pass their saved palette explicitly. Server
        # renders already provide CAST_HAIR_HEX in the fixed configuration.
        colour=os.environ.get('CAST_HAIR_HEX') or '30251E'
    try:
        rig.data.pose_position='REST';scene.frame_set(1);bpy.context.view_layer.update()
        points,_=fit['fit'](str(match),fit['shaped_coords'](body));_,_,objpath=fit['load_mhclo'](str(match));verts,faces=fit['load_obj'](objpath)
        if len(verts)!=len(points):raise RuntimeError('CAST_HAIR_SOURCE_TOPOLOGY_MISMATCH')
        mesh=bpy.data.meshes.new('Cast V18 '+expected);inverse=oldsource.matrix_world.inverted();mesh.from_pydata([inverse@p for p in points],[],faces);mesh.update()
        for poly in mesh.polygons:poly.use_smooth=True
        ob=bpy.data.objects.new('Host.hair_'+expected,mesh);scene.collection.objects.link(ob);ob.parent=rig;ob.matrix_world=oldsource.matrix_world.copy();ob['originalAssetName']=expected
        material=bpy.data.materials.get('LINEART_HAIR_PAPER') or oldsource.data.materials[0];mesh.materials.append(material)
        head=ob.vertex_groups.new(name='head');head.add(list(range(len(mesh.vertices))),1,'REPLACE')
        arm=ob.modifiers.new('Armature','ARMATURE');arm.object=rig
        ss=ob.modifiers.new('Subsurf','SUBSURF');ss.levels=ss.render_levels=1
        for source in candidates:source.hide_render=True;source.hide_viewport=True
        for obj in list(scene.objects):
            if obj.get('castGroomProfile') or obj.get('castGroomBinding'):
                bpy.data.objects.remove(obj,do_unlink=True)
            elif obj.name.startswith('Host.ink_hair_lock_'):obj.hide_render=True
        # Groom construction uses the existing V16 fibre shader and guide
        # field, with restored OBJ corner UVs on the correct original asset.
        os.environ['HDYE']=dye
        groom=runpy.run_path(str(Path(__file__).with_name('cast-hair-groom.py')))
        report=groom['apply_hair_groom'](scene,character,style,colour,density=.55)
        for light in list(scene.objects):
            if light.type=='LIGHT' and light not in lights:bpy.data.objects.remove(light,do_unlink=True)
        for light,energy in lights.items():light.data.energy=energy
        if bg:bg.inputs['Strength'].default_value=strength
        return {'checked':True,'style':style,'asset':expected,'sourceHair':ob.name,'repaired':True,'sourceVertices':len(mesh.vertices),'groom':report}
    finally:
        rig.data.pose_position=oldpose;scene.frame_set(oldframe);bpy.context.view_layer.update()
