"""Extract rig-independent motion from Mixamo FBX downloads.

Usage: blender -b --python cast-mixamo-extract.py -- manifest.json fbx_dir out.json.gz
For every mapped Mixamo bone and frame this stores the world-space rotation
relative to the bone's rest (a "delta"), plus each bone's rest direction and the
palm side vector. cast-gesture-timeline.py turns these into Host.rig channels for
whichever presenter it is building, so one library serves every body.
"""
import bpy,sys,json,gzip,re
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:];manifest,fbx_dir,out=json.loads(Path(args[0]).read_text()),Path(args[1]),args[2]
P='mixamorig:'
CHAIN={'Spine':'Spine1','Spine1':'Spine2','Spine2':'Neck','Neck':'Head','Head':'HeadTop_End'}
for s in('Left','Right'):
    CHAIN.update({f'{s}Shoulder':f'{s}Arm',f'{s}Arm':f'{s}ForeArm',f'{s}ForeArm':f'{s}Hand',f'{s}Hand':f'{s}HandMiddle1'})
    for f in('Thumb','Index','Middle','Ring','Pinky'):
        for i in(1,2,3):CHAIN[f'{s}Hand{f}{i}']=f'{s}Hand{f}{i+1}'
lib={'fps':24,'rest':None,'clips':{}}
for fn,meta in sorted(manifest.items()):
    if not (fbx_dir/fn).exists():continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(fbx_dir/fn))
    arm=next(o for o in bpy.data.objects if o.type=='ARMATURE');act=arm.animation_data.action
    a,b=(int(round(x)) for x in act.frame_range);sc=bpy.context.scene
    mw=arm.matrix_world;bones=[k for k in CHAIN if P+k in arm.data.bones]
    rest={k:(mw@arm.data.bones[P+k].matrix_local).to_quaternion() for k in bones}
    if lib['rest'] is None:
        head=lambda k:mw@arm.data.bones[P+k].head_local
        r={k:{'dir':[round(x,5) for x in (head(CHAIN[k])-head(k)).normalized()]} for k in bones}
        for s in('Left','Right'):
            r[f'{s}Hand']['side']=[round(x,5) for x in (head(f'{s}HandPinky1')-head(f'{s}HandIndex1')).normalized()]
        lib['rest']=r
    q={k:[] for k in bones}
    for f in range(a,b+1):
        sc.frame_set(f)
        for k in bones:
            d=(mw@arm.pose.bones[P+k].matrix).to_quaternion()@rest[k].inverted()
            q[k].extend(round(x,4) for x in d)
    key=re.sub(r'\.fbx$','',fn)
    lib['clips'][key]={'name':meta['name'],'description':meta['description'],'mixamoId':meta['id'],'frames':b-a+1,'q':q}
    print('EXTRACT',key,b-a+1,flush=True)
with gzip.open(out,'wt') as fh:json.dump(lib,fh,separators=(',',':'))
print('MIXAMO_LIBRARY',len(lib['clips']),flush=True)
