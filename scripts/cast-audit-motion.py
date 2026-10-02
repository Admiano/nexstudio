"""Inspect an assembled reference scene across its original continuous action.

Usage: blender -b assembled.blend --python cast-audit-motion.py -- character start end step output.json
Run with the original CAST_* / GARMS environment supplied by the assembly.
"""
import bpy,sys,os,json,math,hashlib,struct
from mathutils.bvhtree import BVHTree
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:];character,start,end,step,output=args;start,end,step=map(int,(start,end,step));os.environ['CAST_CHARACTER']=character
namespace={'__name__':'cast_fit_audit'}
exec(compile(Path(__file__).with_name('cast-fit-posed-clothing.py').read_text(),'cast-fit-posed-clothing.py','exec'),namespace)
fit=namespace['fit_posed_clothing'];scene=bpy.context.scene
invalid=[ob.name for ob in bpy.data.objects if ob.name.startswith('Host.') and not ob.hide_render and ob.parent_type=='BONE' and (ob.parent is None or ob.parent.type!='ARMATURE' or ob.parent_bone not in ob.parent.data.bones)]
if invalid:raise RuntimeError('INVALID_VISIBLE_BONE_PARENT:'+str(invalid))
sources=[ob for ob in bpy.data.objects if ob.type=='MESH' and (ob.name=='Host.body' or (ob.name.startswith('Host.') and not ob.hide_render and not ob.get('castFitSource')) or ob.get('castFitOriginalHideRender') is not None)]
def digest(ob):return hashlib.sha256(b''.join(struct.pack('ddd',*v.co) for v in ob.data.vertices)).hexdigest()
before={ob.name:digest(ob) for ob in sources};rows=[];counts=[]
ribbons=[ob for ob in sources if ob.get('castRibbonBinding')]
max_ribbon_distance=0
for frame in range(start,end+1,step):
 scene.frame_set(frame);report=fit(scene);deps=bpy.context.evaluated_depsgraph_get();vertices=0
 for ob in sources:
  ev=ob.evaluated_get(deps);mesh=ev.to_mesh()
  try:
   vertices+=len(mesh.vertices)
   if any(not all(math.isfinite(c) for c in v.co) for v in mesh.vertices):raise RuntimeError('NONFINITE:'+ob.name)
  finally:ev.to_mesh_clear()
 counts.append((len(bpy.data.objects),len(bpy.data.meshes)))
 if counts[-1]!=counts[0]:raise RuntimeError('FIT_ACCUMULATION')
 ribbon_distances={}
 for ribbon in ribbons:
  garment=bpy.data.objects[ribbon['castGarmentSource']];ev=garment.evaluated_get(deps);mesh=ev.to_mesh()
  tree=BVHTree.FromPolygons([ev.matrix_world@v.co for v in mesh.vertices],[list(p.vertices) for p in mesh.polygons]);ev.to_mesh_clear()
  re=ribbon.evaluated_get(deps);rm=re.to_mesh()
  try:
   distance=max(tree.find_nearest(re.matrix_world@v.co)[3] for v in list(rm.vertices)[::8])
   if distance>0.012:raise RuntimeError('RIBBON_DETACHED:'+ribbon.name+':'+str(distance))
   ribbon_distances[ribbon.name]=distance;max_ribbon_distance=max(max_ribbon_distance,distance)
  finally:re.to_mesh_clear()
 rows.append({'frame':frame,'finiteVertices':vertices,'fittedObjects':len(report),'ribbonSurfaceDistances':ribbon_distances})
if before!={ob.name:digest(ob) for ob in sources}:raise RuntimeError('SOURCE_MUTATED')
Path(output).write_text(json.dumps({'character':character,'boundRibbonsChecked':len(ribbons),'maximumRibbonSurfaceDistance':max_ribbon_distance,'frames':rows,'sourceMeshHashes':before,'sourceMeshesUnchanged':True,'objectCountsStable':True,'visibleBoneParentsValid':True},indent=2)+'\n')
print('MOTION_AUDIT_OK',character,len(rows),len(sources),flush=True)
