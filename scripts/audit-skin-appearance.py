"""Verify texture, palette, explicit lip overrides, and stable animated anatomy."""
import bpy,hashlib,struct,json,sys,runpy,math
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:];character,output=args
module=runpy.run_path(str(Path(__file__).with_name('cast-skin-appearance.py')))
scene=bpy.context.scene
def identity():
    h=hashlib.sha256()
    for ob in sorted((o for o in bpy.data.objects if o.type=='MESH'),key=lambda o:o.name):
        h.update(ob.name.encode())
        for v in ob.data.vertices:
            h.update(struct.pack('ddd',*v.co))
            for g in v.groups:h.update(struct.pack('if',g.group,g.weight))
        for uv in ob.data.uv_layers:
            for d in uv.data:h.update(struct.pack('ff',*d.uv))
        if ob.data.shape_keys:
            for key in ob.data.shape_keys.key_blocks:
                h.update(key.name.encode())
                for v in key.data:h.update(struct.pack('ddd',*v.co))
    for ob in (o for o in bpy.data.objects if o.type=='ARMATURE'):
        for bone in ob.data.bones:
            h.update(bone.name.encode());h.update(struct.pack('dddddd',*bone.head_local,*bone.tail_local))
    return h.hexdigest()
before=identity();counts=(len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.actions))
records=[]
for hx in ('F7E1D3','F1D7C8','E0B48F','C99A6E','9E6B4A','6A4431'):
    report=module['apply_skin_appearance'](scene,character,hx)
    expected=module['linear_rgb'](hx)
    assert module['palette_for'](expected)['skinHex']==hx
    assert report['makeup']==module['MAKEUP'][hx][0] if character=='female' else report['makeup'] is None
    assert all(row['pores'] for row in report['materials'])
    for row in report['materials']:
        assert all(abs(a-b)<1e-7 for a,b in zip(row['baseLinear'],expected))
    nodes=[len(bpy.data.materials[r['material']].node_tree.nodes) for r in report['materials']]
    module['apply_skin_appearance'](scene,character,hx)
    assert nodes==[len(bpy.data.materials[r['material']].node_tree.nodes) for r in report['materials']]
    records.append(report)
if character=='female':
    custom=module['apply_skin_appearance'](scene,character,'6A4431',lip_hex='B3202A')
    assert custom['materials'][0]['explicitLipOverride']
    actual=bpy.data.materials['PEEPS_V2_WARM_SKIN']['castLipColors'][3:]
    assert all(abs(a-b)<1e-6 for a,b in zip(actual,module['linear_rgb']('B3202A')))
body=bpy.data.objects['Host.body']
rest_before=[tuple(a.vector) for a in body.data.attributes['cast_skin_rest'].data]
frames=[]
for frame in range(1,999,17):
    scene.frame_set(frame);deps=bpy.context.evaluated_depsgraph_get()
    ob=bpy.data.objects['Host.body'];ev=ob.evaluated_get(deps);mesh=ev.to_mesh()
    try:
        assert all(math.isfinite(c) for v in mesh.vertices for c in v.co)
    finally:ev.to_mesh_clear()
    frames.append(frame)
assert rest_before==[tuple(a.vector) for a in body.data.attributes['cast_skin_rest'].data],'TEXTURE_COORDINATES_CHANGED'
assert before==identity(),'SOURCE_IDENTITY_CHANGED'
assert counts==(len(bpy.data.objects),len(bpy.data.meshes),len(bpy.data.actions))
result={'character':character,'sourceIdentityHash':before,'sourceIdentityUnchanged':True,'objectsMeshesActionsUnchanged':True,'reapplicationStable':True,'textureCoordinatesStable':True,'weightsAndUVsUnchanged':True,'explicitLipOverrideVerified':character=='female','finitePoseFrames':frames,'palettes':records}
Path(output).write_text(json.dumps(result,indent=2)+'\n')
print('SKIN_APPEARANCE_AUDIT_PASS',character,len(frames),'poses',len(records),'tones')
