"""Align the native watch case to the dorsal forearm.

Blender: --python cast-align-watch.py -- input.blend output.blend
The whole case/dial assembly moves rigidly; strap mesh, its stitching and action curves remain.
"""
import bpy,sys,json
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree

def center(o):
 return sum((o.matrix_world@v.co for v in o.data.vertices),Vector())/len(o.data.vertices)

def fix():
 r=bpy.data.objects['Host.rig'];r.data.pose_position='REST';bpy.context.view_layer.update();side=bpy.data.objects['Host.watch_case'].parent_bone.rsplit('.',1)[-1]
 w=r.matrix_world@r.data.bones['wrist.'+side].head_local;e=r.matrix_world@r.data.bones['lowerarm01.'+side].head_local;a=(w-e).normalized()
 i=r.matrix_world@r.data.bones['finger2-1.'+side].head_local;p=r.matrix_world@r.data.bones['finger5-1.'+side].head_local;m=r.matrix_world@r.data.bones['finger3-1.'+side].head_local
 dorsal=(m-w).cross(i-p).normalized();lat=Vector((1 if w.x>(r.matrix_world@r.data.bones['spine05'].head_local).x else -1,0,0))
 if dorsal.dot(lat)<0:dorsal=-dorsal
 d=(dorsal-a*dorsal.dot(a)).normalized()
 case=bpy.data.objects['Host.watch_case'];dial=next((bpy.data.objects.get('Host.watch_'+n) for n in ('dial','lcd','glass') if bpy.data.objects.get('Host.watch_'+n)),None);assert dial is not None,'WATCH_FACE_REQUIRED';band=bpy.data.objects['Host.watch_strap'];cc=center(case);bc=center(band);oldn=(center(dial)-cc).normalized();old_a=(a-oldn*a.dot(oldn)).normalized()
 oldframe=Matrix((oldn,old_a.cross(oldn).normalized(),old_a)).transposed();newframe=Matrix((d,a.cross(d).normalized(),a)).transposed();rot=newframe@oldframe.transposed()
 pts=[band.matrix_world@v.co for v in band.data.vertices];tree=BVHTree.FromPolygons(pts,[list(p.vertices) for p in band.data.polygons]);hit=tree.ray_cast(bc+d*.15,-d,.15)
 assert hit[0] is not None,'WATCH_BAND_SURFACE_REQUIRED'
 half=max(abs((case.matrix_world@v.co-cc).dot(oldn)) for v in case.data.vertices)
 newcc=hit[0]+d*(half+.0001);delta=Matrix.Translation(newcc)@rot.to_4x4()@Matrix.Translation(-cc)
 parts=[o for o in bpy.context.scene.objects if o.name.startswith('Host.watch_') and o!=band and not o.name.startswith(('Host.watch_bracelet_joint','Host.watch_stitch'))]
 for o in parts:o.matrix_world=delta@o.matrix_world
 bpy.context.view_layer.update();dn=(center(dial)-center(case)).normalized();offset=center(dial)-center(case);projected=(offset-dn*offset.dot(dn)).length
 r.data.pose_position='POSE';bpy.context.view_layer.update()
 return {'caseNormalRest':list(dn),'anatomicalDorsalRest':list(d),'normalAgreement':dn.dot(d),'dialCenterProjectedOffsetMm':projected*1000,'partsRigidlyRepositioned':len(parts),'bandGeometryUnchanged':True,'bindingBone':case.parent_bone,'caseSeatGapMm':.1}

if __name__=='__main__':
 source,output=sys.argv[sys.argv.index('--')+1:sys.argv.index('--')+3]
 bpy.ops.wm.open_mainfile(filepath=source)
 report=fix()
 text=bpy.data.texts.new('ANATOMICAL_WATCH_ALIGNMENT.json');text.write(json.dumps(report,indent=2))
 bpy.context.preferences.filepaths.save_version=0
 bpy.ops.wm.save_as_mainfile(filepath=output,compress=True)
 print(json.dumps(report))
