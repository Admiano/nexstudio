"""Rebuild existing selections after the illustrated skin/clothing passes."""
import os,sys,runpy
from pathlib import Path
import bpy

def apply_accessory_quality(scene,character,source_directory=None):
    root=Path(__file__).resolve().parent
    if str(root) not in sys.path:sys.path.insert(0,str(root))
    rig=bpy.data.objects['Host.rig'];frame=scene.frame_current;position=rig.data.pose_position
    neck=os.environ.get('CAST_NECK',os.environ.get('NECK','none'))
    watch=os.environ.get('CAST_WATCH',os.environ.get('WATCH','none'))
    if neck not in ['','none','fine','pendant','pearls','choker','scarf']:raise ValueError('ACCESSORY_NECK_STYLE_INVALID')
    if watch not in ['','none','analog','digital','smart','chrono','dress']:raise ValueError('ACCESSORY_WATCH_STYLE_INVALID')
    from cast_accessory_earrings import apply_earrings
    report={'profile':'illustrated-accessories-v17','neck':neck if character=='female' else None,'watch':watch if character=='male' else None}
    try:
        rig.data.pose_position='REST';scene.frame_set(1);bpy.context.view_layer.update()
        full=next((o for o in bpy.data.objects if o.name.startswith('Cast accessory skin target V17') and o.type=='MESH'),None)
        if full is None:
            full=bpy.data.objects['Host.body'].copy();full.name='Cast accessory skin target V17'
            for modifier in list(full.modifiers):
                if modifier.type=='MASK' and modifier.name!='Hide helpers':full.modifiers.remove(modifier)
            scene.collection.objects.link(full);full.hide_render=True;full['castAccessoryInternalTarget']=True
        for modifier in full.modifiers:
            if modifier.type=='SUBSURF':modifier.levels=modifier.render_levels
        bpy.context.view_layer.update()
        for ob in list(bpy.data.objects):
            if ob.name.startswith(('Host.V62_','Host.watch_','Host.V17_ear_')):bpy.data.objects.remove(ob,do_unlink=True)
        before={ob.name for ob in bpy.data.objects}
        if character=='female':
            dress=next((o for o in bpy.data.objects if o.type=='MESH' and not o.hide_render and o.name.startswith('Host.') and any(k in o.name for k in ['f_dress','cocktail_dress','qipao'])),None)
            if dress is None:raise RuntimeError('ACCESSORY_GARMENT_TARGET_MISSING')
            os.environ.update(NECK=neck,DOBJ=dress.name)
            runpy.run_path(str(root/'cast_accessory_neck.py'))
            earstyle={'long':'hoop','bob':'bar','bangs':'stud','bun':'statement','braid':'drop'}[os.environ.get('CAST_HAIR_STYLE','long')]
            report['earrings']=apply_earrings(earstyle)
        else:
            os.environ['WATCH']=watch;runpy.run_path(str(root/'cast_accessory_watch.py'))
        report['parts']=[ob.name for ob in bpy.data.objects if ob.name not in before]
        report['vertices']=sum(len(bpy.data.objects[n].data.vertices) for n in report['parts'] if bpy.data.objects[n].type=='MESH')
        return report
    finally:
        rig.data.pose_position=position;scene.frame_set(frame);bpy.context.view_layer.update()
