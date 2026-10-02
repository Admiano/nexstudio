"""Render a continuous QA sequence from the assembled original action.

Called by cast-render-assembled.py with --motion-proof START END STEP.
Every sampled frame is evaluated from the source rig before bounded fitting.
Output is a proxy sequence for defect inspection, not production video.
"""
import json,math,hashlib
from pathlib import Path
import bpy
index=args.index('--motion-proof');start,end,step=map(int,args[index+1:index+4])
if not (1<=start<end<=998 and 1<=step<=3):raise ValueError('CAST_MOTION_PROOF_RANGE')
scene=bpy.context.scene
sequence=output_file.parent/(output_file.stem+'-frames');sequence.mkdir(parents=True,exist_ok=True)
scene.render.resolution_percentage=25
scene.cycles.samples=16
scene.cycles.use_denoising=True
# The renderer already scaled outlines for the 50% still. Match proxy pixels.
for layer in scene.view_layers:
    for lines in layer.freestyle_settings.linesets:lines.linestyle.thickness*=0.5
if scene.compositing_node_group:
    for node in scene.compositing_node_group.nodes:
        if node.type=='DILATEERODE':node.inputs['Size'].default_value=1
sources=[o for o in bpy.data.objects if o.type=='MESH' and (o.get('castFitOriginalHideRender') is not None or o.name in [x.split('=')[0] for x in __import__('os').environ.get('GARMS','').split(';')])]
def digest(obj):
    return hashlib.sha256(b''.join(__import__('struct').pack('ddd',*v.co) for v in obj.data.vertices)).hexdigest()
original={o.name:digest(o) for o in sources}
records=[];counts=[]
for ordinal,frame in enumerate(range(start,end+1,step)):
    scene.frame_set(frame)
    report=fit_posed_clothing(scene)
    deps=bpy.context.evaluated_depsgraph_get()
    for obj in sources:
        ev=obj.evaluated_get(deps);mesh=ev.to_mesh()
        try:
            if any(not all(math.isfinite(c) for c in v.co) for v in mesh.vertices):raise RuntimeError('CAST_MOTION_NONFINITE:'+obj.name)
        finally:ev.to_mesh_clear()
    counts.append((len(bpy.data.objects),len(bpy.data.meshes)))
    if ordinal and counts[-1]!=counts[0]:raise RuntimeError('CAST_MOTION_FIT_OBJECT_ACCUMULATION')
    scene.render.filepath=str(sequence/f'{ordinal:04}.png');bpy.ops.render.render(write_still=True)
    records.append({'frame':frame,'fit':report})
    print('CAST_MOTION_FRAME',ordinal,frame,flush=True)
if original!={o.name:digest(o) for o in sources}:raise RuntimeError('CAST_MOTION_SOURCE_MUTATED')
metadata={'start':start,'end':end,'step':step,'fps':scene.render.fps/scene.render.fps_base/step,'frameCount':len(records),'sourceMeshesUnchanged':True,'objectCountsStable':True,'records':records}
(sequence/'verification.json').write_text(json.dumps(metadata,indent=2)+'\n')
print('CAST_MOTION_COMPLETE',json.dumps({k:v for k,v in metadata.items() if k!='records'}),flush=True)
