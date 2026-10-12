"""Audit genuine PR66 Hunyuan GLB; read-only source and reproducible renders."""
import bpy,sys,json,hashlib
from pathlib import Path
from mathutils import Vector
a=sys.argv[sys.argv.index('--')+1:]
glb,source_blend,out=map(Path,a[:3]);out.mkdir(parents=True,exist_ok=True)
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source_blend.resolve()),load_ui=False)
scene_source={'source_name_verified':any('SOURCE_PR66_casual30_UNMODIFIED' in o.name for o in bpy.data.objects),'mesh_names':[o.name for o in bpy.data.objects if o.type=='MESH']}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(glb.resolve()))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
vnum=sum(len(o.data.vertices) for o in meshes)
assert vnum>10000,'GLB geometry missing'
verts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
lo=Vector(tuple(min(v[i] for v in verts) for i in range(3)))
hi=Vector(tuple(max(v[i] for v in verts) for i in range(3)))
mid=(lo+hi)/2;H=(hi-lo).z
import bmesh
topology=[]
for o in meshes:
 bm=bmesh.new();bm.from_mesh(o.data)
 topology.append({'mesh':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'boundaries':sum(e.is_boundary for e in bm.edges),'nonmanifold':sum(not e.is_manifold for e in bm.edges),'shape_keys':len(o.data.shape_keys.key_blocks) if o.data.shape_keys else 0,'armature':bool(o.find_armature())})
 bm.free()
sc=bpy.context.scene
cam=bpy.data.objects.new('QA camera',bpy.data.cameras.new('QA camera'))
bpy.context.collection.objects.link(cam);sc.camera=cam
cam.data.type='ORTHO'
sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='STUDIO'
sc.display.shading.color_type='MATERIAL'
sc.display.shading.show_shadows=True
sc.display.shading.show_cavity=True
sc.display.shading.cavity_type='BOTH'
sc.display.shading.curvature_ridge_factor=1.
sc.display.shading.curvature_valley_factor=1.
sc.render.resolution_x=720;sc.render.resolution_y=950
sc.render.image_settings.file_format='PNG'
def shot(name,x,y,z,head=False):
 target=Vector((mid.x,mid.y,hi.z-H*.16)) if head else mid
 cam.location=(x,y,z)
 cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
 cam.data.ortho_scale=H*(.50 if head else 1.18)
 sc.render.filepath=str((out/('PR66_'+name+'.png')).resolve())
 bpy.ops.render.render(write_still=True)
 print('RENDERED',name,flush=True)
d=H*2.7
shot('front',mid.x,mid.y-d,mid.z)
shot('threeq',mid.x+d*.48,mid.y-d*.87,mid.z)
shot('profile',mid.x+d,mid.y,mid.z)
shot('head3q',mid.x+d*.48,mid.y-d*.87,mid.z+H*.33,True)
sc.render.filepath=''
bpy.ops.wm.save_as_mainfile(filepath=str((out/'PR66_UNMODIFIED_QA.blend').resolve()))
report={'source_glb_sha256':sha(glb),'source_blend_sha256':sha(source_blend),'original_scene':scene_source,'total_vertices':vnum,'mesh_topology':topology,'original_geometry_untouched':True,'render_engine':'Workbench','assessment':'geometry only; appearance and motion not approved'}
(out/'PR66_AUDIT.json').write_text(json.dumps(report,indent=2))
print('SUCCESS original PR66 audited',vnum,flush=True)
