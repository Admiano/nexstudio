"""Preserve the approved geometry, shaders and jaw-driven teeth after assembly."""
import json,os,sys
from pathlib import Path
import bpy
from mathutils import Matrix,Vector
source=Path(os.environ['PV1']);character=os.environ['CAST_CHARACTER']
approved=json.loads((source.parent/'approved-polish.json').read_text())['characters'][character]
for c in approved['transforms']:
    if c['onlyHair'] and c['onlyHair']!=os.environ['CAST_HAIR_STYLE']:continue
    obj=bpy.data.objects[c['name']];obj.matrix_basis=Matrix([c['basis'][i:i+4] for i in range(0,16,4)])
for c in approved['objects']:
    if character=='female' and os.environ['CAST_HAIR_STYLE']!='long':continue
    obj=bpy.data.objects.get(c['name'])
    if obj is None or len(obj.data.vertices)!=c['vertexCount']:raise RuntimeError('APPROVED_CHARACTER_TOPOLOGY_MISMATCH:'+c['name'])
    for i,x,y,z in c['vertices']:obj.data.vertices[i].co+=Vector((x,y,z))
    for name,deltas in c['shapeKeys'].items():
        key=obj.data.shape_keys.key_blocks.get(name) if obj.data.shape_keys else None
        if key is None:raise RuntimeError('APPROVED_SHAPE_KEY_MISSING:'+name)
        for i,x,y,z in deltas:key.data[i].co+=Vector((x,y,z))
    obj.pass_index=c['passIndex'];obj.hide_render=c['hideRender'];obj.data.update()
for record in approved['drivers']:
    obj=bpy.data.objects[record['name']]
    for r in record['drivers']:
        driver=obj.driver_add(r['dataPath'],r['index']).driver;driver.type=r['type'];driver.expression=r['expression']
        for v in list(driver.variables):driver.variables.remove(v)
        for variable in r['variables']:
            v=driver.variables.new();v.name=variable['name'];v.type=variable['type']
            for t,saved in zip(v.targets,variable['targets']):
                t.id_type=saved['idType'];t.id=bpy.data.objects['Host.body'].data.shape_keys if saved['idType']=='KEY' else bpy.data.objects[saved['idName']]
                t.data_path=saved['dataPath'];t.bone_target=saved['boneTarget'];t.transform_type=saved['transformType'];t.transform_space=saved['transformSpace']
reference=source.parent.parent/'NexStudio_Presenter_Reference';scene_file=reference/'characters'/approved['file']
names=['PEEPS_V2_WARM_SKIN','V60_EAR_SKIN','LINEART_HAIR_PAPER'];old_materials={n:bpy.data.materials[n] for n in names}
with bpy.data.libraries.load(str(scene_file),link=False) as (available,incoming):incoming.materials=list(names)
for name,material in zip(names,incoming.materials):
    if material is None:raise RuntimeError('APPROVED_MATERIAL_MISSING:'+name)
    old=old_materials[name]
    if name=='LINEART_HAIR_PAPER':
        for nn in ('Mix','Mix.001','Map Range','Map Range.001','Map Range.002','Math.002'):
            src=old.node_tree.nodes.get(nn);dst=material.node_tree.nodes.get(nn)
            if src and dst:
                for a,b in zip(src.inputs,dst.inputs):
                    if not a.is_linked and hasattr(a,'default_value') and hasattr(b,'default_value'):b.default_value=a.default_value
    for obj in bpy.data.objects:
        if obj.type=='MESH':
            for slot in obj.material_slots:
                if slot.material==old:slot.material=material
    old.name=name+'.ungraded-source';material.name=name
def run(name):
    p=source/name;exec(compile(p.read_text(),str(p),'exec'),globals())
run('skintone.py')
if character=='female':run('lip.py')
else:
    frame=bpy.data.objects.get('Host.V59_face_frame')
    if frame:frame.hide_render=True
    if os.environ['CAST_HAIR_STYLE']=='bald':
        for obj in bpy.data.objects:
            if obj.name.startswith('Host.') and 'hair' in obj.name.lower():obj.hide_render=True
    if os.environ['CAST_HAIR_STYLE']=='quiff':
        for i in range(4):
            lock=bpy.data.objects.get(f'Host.ink_hair_lock_{i}')
            if lock:lock.hide_render=False
sys.path.insert(0,str(reference/'scripts'));import render_shaded as shading
approved_top=None
if character=='male':
    with bpy.data.libraries.load(str(scene_file),link=False) as (available,incoming):incoming.materials=['V70_G_elvs_male_shirt_untucked_bd1']
    approved_top=incoming.materials[0]
for material in bpy.data.materials:
    if material==approved_top:continue
    if approved_top and material.name=='V70_G_elvs_male_shirt_untucked_bd1' and os.environ.get('CAST_QUALITY_PILOT')!='1':
        # v6 softened this shirt's authored armpit shading before the grade.
        for name in ('Map Range','Map Range.002','Map Range.003'):
            original=approved_top.node_tree.nodes[name];current=material.node_tree.nodes[name]
            for field in ('To Min','To Max'):current.inputs[field].default_value=original.inputs[field].default_value
    if material.name.startswith(('V63_DRESS_','V70_G_')) and material.use_nodes:
        preset = shading.CLOTH
        if os.environ.get('CAST_QUALITY_PILOT') == '1':
            # Short-range contact shade follows the current pose. Preserve
            # the approved palette and leave skin/hair/ink grading untouched.
            preset = dict(shading.CLOTH, occlusion=0.20, distance=0.035, highlight=0.04)
        shading.grade(material,preset,1.0)
os.environ['FACE']=os.environ['CAST_FACE'];run('facevar.py')

if os.environ.get('CAST_QUALITY_PILOT') == '1':
    detail=bpy.data.materials.get('PEEPS_V2_HAIR_DETAIL')
    if detail and detail.use_nodes and os.environ.get('HCOL'):
        # Strand ink follows the selected hair palette, rather than retaining
        # the purple accent of the unrelated source material.
        hx=os.environ['HCOL'].lstrip('#')
        srgb=[int(hx[i:i+2],16)/255 for i in (0,2,4)]
        linear=[c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4 for c in srgb]
        detail.node_tree.nodes['Emission'].inputs['Color'].default_value=(*[c*0.40 for c in linear],1)
