"""Measure approved v3/v6 geometry corrections; run with Blender --background."""
import bpy,json,numpy as np
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'engine_sources/makehuman-lineart'
targets={'female':['Host.hair_culturalibre_hair_01'],'male':['Host.eyebrow001','Host.high-poly','Host.teeth_base','Host.V11_mouth_interior']}
out={'sourceVersion':'bf88447b8f898bea078c44b9202cfe2b7ff13be5','characters':{}}
def array(seq):
    x=np.zeros(len(seq)*3,dtype=np.float32);seq.foreach_get('co',x);return x.reshape(-1,3)
def snapshot(names):
    d={}
    for n in names:
        o=bpy.data.objects[n];d[n]={'vertices':array(o.data.vertices),'shapeKeys':{k.name:array(k.data) for k in o.data.shape_keys.key_blocks} if o.data.shape_keys else {},'hideRender':o.hide_render,'passIndex':o.pass_index}
    return d
for sex,ver in [('female','v3'),('male','v6')]:
    bpy.ops.wm.open_mainfile(filepath=str(root/f'presenters_v1/scenes/NEXSTUDIO_V1_{sex.upper()}.blend'))
    before=snapshot(targets[sex])
    bpy.ops.wm.open_mainfile(filepath=str(root/f'NexStudio_Presenter_Reference/characters/NEXSTUDIO_V1_{sex.upper()}_{ver}.blend'))
    after=snapshot(targets[sex]);changes=[];bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
    transforms=[];drivers=[]
    if sex=='male':
        for n in ['Host.teeth_base']+[f'Host.ink_hair_lock_{i}' for i in range(4)]:
            o=bpy.data.objects[n];transforms.append({'name':n,'basis':[float(x) for row in o.matrix_basis for x in row],'onlyHair':'quiff' if 'hair_lock' in n else None})
        o=bpy.data.objects['Host.teeth_base'];curves=[]
        for f in o.animation_data.drivers:
            d=f.driver;curves.append({'dataPath':f.data_path,'index':f.array_index,'type':d.type,'expression':d.expression,'variables':[{'name':v.name,'type':v.type,'targets':[{'idType':t.id_type,'idName':t.id.name if t.id else None,'dataPath':t.data_path,'boneTarget':t.bone_target,'transformType':t.transform_type,'transformSpace':t.transform_space} for t in v.targets]} for v in d.variables]})
        drivers=[{'name':o.name,'drivers':curves}]
    for n in targets[sex]:
        a,b=before[n],after[n]
        def delta(x,y):
            assert x.shape==y.shape
            d=y-x;indices=np.where(np.any(np.abs(d)>1e-8,axis=1))[0]
            return [[int(i),*map(float,d[i])] for i in indices]
        changes.append({'name':n,'vertexCount':len(a['vertices']),'vertices':delta(a['vertices'],b['vertices']),'shapeKeys':{k:delta(a['shapeKeys'][k],v) for k,v in b['shapeKeys'].items()},'hideRender':b['hideRender'],'passIndex':b['passIndex']})
    out['characters'][sex]={'file':f'NEXSTUDIO_V1_{sex.upper()}_{ver}.blend','objects':changes,'transforms':transforms,'drivers':drivers}
p=root/'presenters_v1/approved-polish.json';p.write_text(json.dumps(out,separators=(',',':'))+'\n');print('APPROVED_CORRECTIONS_SAVED',p,p.stat().st_size)
