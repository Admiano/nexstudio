"""Measure retargeted Mixamo clips on a presenter rig and write their library entries.

Usage: blender -b scene.blend --python cast-mixamo-landmarks.py -- [out.json]
Every clip in the Mixamo library is retargeted, played on the rig and measured
from the wrists: the active window (frames), which hands move, and
onset/stroke/apex/release like the original clips. Categories come from
mixamo.categories in gesture-clips.json (keyword -> category, first match wins);
entries already present keep any hand-edited category or frames.
"""
import bpy,sys,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(Path(__file__).resolve().parent))
import cast_mixamo_retarget as MX
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
LP=ROOT/'engine_sources/makehuman-lineart/character_system/gesture-clips.json';LIB=json.loads(LP.read_text())
cfg=LIB['mixamo'];lib=MX.load(ROOT/cfg['library']);rest_frame=LIB['idle']['ranges'][0][0]
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE' and o.animation_data and o.animation_data.action and o.animation_data.action.name==LIB['source']['action'])
src,slot0=rig.animation_data.action,rig.animation_data.action_slot;scene=bpy.context.scene
scene.frame_set(rest_frame);rest={w:(rig.matrix_world@rig.pose.bones[w].head).copy() for w in('wrist.L','wrist.R')}
def category(c):
    text=(c['name']+' '+c['description']).lower()
    for kw,cat in cfg['categories']:
        if re.search(r'\b'+kw+r'\b',text):return cat
    return 'expressive'
out={}
for key,c in sorted(lib['clips'].items()):
    vals=MX.retarget(rig,lib,key,rest_frame,scene,cfg.get('gain'))
    act=bpy.data.actions.new('mxprobe');sl=act.slots.new(id_type='OBJECT',name=rig.name)
    cb=act.layers.new('L').strips.new(type='KEYFRAME').channelbag(sl,ensure=True)
    for (p,i),v in vals.items():
        fc=cb.fcurves.new(p,index=i);fc.keyframe_points.add(len(v));fc.keyframe_points.foreach_set('co',[x for f,y in enumerate(v,1) for x in(f,y)])
    rig.animation_data.action=act;rig.animation_data.action_slot=sl
    n=c['frames'];disp={w:[] for w in rest};pos={w:[] for w in rest}
    for f in range(1,n+1):
        scene.frame_set(f)
        for w in rest:p=rig.matrix_world@rig.pose.bones[w].head;pos[w].append(p.copy());disp[w].append((p-rest[w]).length)
    rig.animation_data.action=src;rig.animation_data.action_slot=slot0;bpy.data.actions.remove(act)
    peak={w:max(d) for w,d in disp.items()}
    hands='both' if min(peak.values())>.6*max(peak.values()) else ('left' if peak['wrist.L']>peak['wrist.R'] else 'right')
    tot=[max(disp[w][f] for w in rest) for f in range(n)]
    spd=[max((pos[w][f+1]-pos[w][f]).length for w in rest) for f in range(n-1)]+[0]
    top=max(spd) or 1;moving=[f for f in range(n) if spd[f]>.25*top]
    cat=category(c)
    if cat=='idle' or not moving:a,b=1,n
    else:a,b=max(1,moving[0]+1-6),min(n,moving[-1]+1+8)
    mf=int(cfg.get('maxFrames',0))
    if cat!='idle' and mf and b-a+1>mf:
        ap=max(range(a-1,b),key=lambda f:tot[f])+1;a=max(a,min(ap-mf//2,b-mf+1));b=a+mf-1
    m2=[f for f in range(a-1,b) if spd[f]>.25*top] or [a-1]
    entry={'mixamo':key,'frames':[a,b],'hands':hands,'category':cat,
           'onset':m2[0]-(a-1),'stroke':max(range(a-1,b),key=lambda f:spd[f])-(a-1),
           'apex':max(range(a-1,b),key=lambda f:tot[f])-(a-1),'release':m2[-1]-(a-1),
           'reachCm':round(100*max(peak.values()),1),'peakSpeed':round(top*scene.render.fps,2),
           'tempo':round(min(1,cfg.get('maxHandSpeed',99)/(top*scene.render.fps)),3),'source':f"Mixamo: {c['name']} ({c['description']})"}
    old=LIB['clips'].get('mx_'+key,{})
    for k in('category','frames'):
        if old.get('locked') and k in old:entry[k]=old[k]
    out['mx_'+key]=entry;print('LANDMARK',key,json.dumps(entry),flush=True)
for k in [k for k in LIB['clips'] if k.startswith('mx_') and k not in out]:del LIB['clips'][k]
LIB['clips'].update(out)
(Path(args[0]) if args else LP).write_text(json.dumps(LIB,indent=2)+'\n')
print('MIXAMO_LANDMARKS',len(out),flush=True)
