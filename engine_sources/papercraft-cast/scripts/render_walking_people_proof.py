#!/usr/bin/env python3
"""Render-only, non-destructive QA for WalkingPeoplepack2024.fbx.

No proprietary raw mesh, derivative .blend, or source textures are exported.
Outputs Blender-rendered PNGs and a metadata JSON only.
"""
import bpy, sys, os, json, hashlib, math
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'assets/walking-people-pack/WalkingPeoplepack2024.fbx'
TEX=SOURCE.parent
OUT=Path(os.getenv('WALKING_PROOF_OUTPUT',str(ROOT/'walking-proof-output')))
OUT.mkdir(parents=True,exist_ok=True)
assert SOURCE.exists(),f'Original source missing: {SOURCE}'

def bounds(obs):
    pts=[ob.matrix_world@Vector(v) for ob in obs if ob.type=='MESH' for v in ob.bound_box]
    if not pts:return Vector((0,0,0)), Vector((1,1,2))
    return Vector([min(p[i] for p in pts) for i in range(3)]),Vector([max(p[i] for p in pts) for i in range(3)])

def colorize_paper(mat):
    mat=mat.copy()
    mat.name='PAPER_VIEW_'+mat.name
    mat.use_nodes=True
    bsdf=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if not bsdf:return mat
    bsdf.inputs['Roughness'].default_value=.93
    bsdf.inputs['Metallic'].default_value=0.
    nodes=mat.node_tree.nodes
    noise=nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value=185.
    bump=nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value=.07
    bump.inputs['Distance'].default_value=.001
    mat.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height'])
    mat.node_tree.links.new(bump.outputs['Normal'],bsdf.inputs['Normal'])
    return mat

def show_paper(originals,clones,enabled):
    for obj in originals: obj.hide_render=enabled
    for obj in clones: obj.hide_render=not enabled

def camera_and_lights(mn,mx):
    scene=bpy.context.scene
    center=(mn+mx)*.5
    ext=mx-mn
    size=max(ext.z,ext.x*1.5,ext.y*1.5,.02)
    camd=bpy.data.cameras.new('QA orthographic camera')
    cam=bpy.data.objects.new('QA orthographic camera',camd)
    scene.collection.objects.link(cam)
    camd.type='ORTHO';camd.ortho_scale=size*1.24
    scene.camera=cam
    scene.render.engine='BLENDER_WORKBENCH' if os.getenv('NEX_FAST_PREVIEW') else 'BLENDER_EEVEE'
    if os.getenv('NEX_FAST_PREVIEW'):
        scene.display.shading.light='STUDIO'
        scene.display.shading.color_type='MATERIAL'
        scene.display.shading.show_cavity=True
    scene.render.resolution_x=440 if os.getenv('NEX_FAST_PREVIEW') else 640;scene.render.resolution_y=540 if os.getenv('NEX_FAST_PREVIEW') else 720
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    world=bpy.data.worlds.new('Warm studio') if not scene.world else scene.world
    scene.world=world;world.use_nodes=True
    world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.22,.19,.16,1)
    for idx,v in enumerate((Vector((1.6,-2,2.7)),Vector((-1.3,1.5,1.9)))):
        d=bpy.data.lights.new('Softbox_%d'%idx,'AREA')
        o=bpy.data.objects.new('Softbox_%d'%idx,d);scene.collection.objects.link(o)
        o.location=center+v*size*.9
        o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
        d.energy=(820 if idx==0 else 530)*size*size
        d.size=size*1.2
    return cam,center,size

def render(cam,center,size,tag):
    scene=bpy.context.scene
    angles={
      'FRONT': Vector((0,-1,.1)),
      'THREE_QUARTER':Vector((1,-1,.25)),
      'PROFILE':Vector((1,0,.25))}
    rendered=[]
    for name,d in angles.items():
        cam.location=center+d.normalized()*size*2.8
        cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        path=OUT/(tag+'_'+name+'.png')
        scene.render.filepath=str(path)
        bpy.ops.render.render(write_still=True)
        rendered.append(path.name)
    return rendered

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SOURCE),use_anim=True)
originals=list(bpy.context.scene.objects)
meshes=[o for o in originals if o.type=='MESH']
armatures=[o for o in originals if o.type=='ARMATURE']
if not meshes:raise RuntimeError('No mesh objects imported from original FBX')
images=[]
textures={p.name.lower():p for p in TEX.glob('gihapeopletex*.jpg')}
for image in bpy.data.images:
    if not image.has_data or not image.filepath or not Path(bpy.path.abspath(image.filepath)).exists():
        target=Path(image.filepath.replace('\\','/')).name.lower()
        if target in textures:
            image.filepath=str(textures[target]);image.reload()
    images.append({'name':image.name,'file_name':Path(image.filepath.replace('\\','/')).name,'loaded':bool(image.has_data)})
source_min,source_max=bounds(meshes)
cam,center,size=camera_and_lights(source_min,source_max)
source_pngs=render(cam,center,size,'SOURCE')
clones=[]
for ob in meshes:
    c=ob.copy();c.data=ob.data.copy();c.name='PAPER_CANDIDATE_'+ob.name
    bpy.context.scene.collection.objects.link(c)
    c.matrix_world=ob.matrix_world.copy()
    if c.parent:
        world=c.matrix_world.copy();c.parent=None;c.matrix_world=world
    if len(c.data.polygons)>180:
        dec=c.modifiers.new('Faceted paper candidate','DECIMATE')
        dec.ratio=.34 if len(c.data.polygons)>20000 else .63
    for polygon in c.data.polygons: polygon.use_smooth=False
    thick=c.modifiers.new('Paper sheet thickness','SOLIDIFY')
    thick.thickness=max((source_max.z-source_min.z)*.0016,.00012)
    thick.offset=-.6
    for slot in c.material_slots:
        if slot.material:slot.material=colorize_paper(slot.material)
    clones.append(c)
show_paper(originals,clones,True)
paper_pngs=render(cam,center,size,'PAPER_TEST')
report={
  'source_fbx':'WalkingPeoplepack2024.fbx',
  'source_github_branch':'devin/1791589734-walking-people-pack',
  'source_bytes':SOURCE.stat().st_size,
  'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
  'meshes':len(meshes),
  'mesh_info':[{'name':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons)} for o in meshes],
  'armatures':[{'name':o.name,'bones':len(o.data.bones)} for o in armatures],
  'found_textures':[p.name for p in textures.values()],
  'import_images':images,
  'render_files':source_pngs+paper_pngs,
  'source_modified':False,
  'rig_test':'NOT TESTED',
  'character_partition':'NOT CERTIFIED: object count does not necessarily equal character count',
  'visual_gate':'UNAPPROVED: human review required',
  'redistribution':'PNG renders and report only; do not publish original mesh or textures'
}
(OUT/'WALKING_PACK_AUDIT.json').write_text(json.dumps(report,indent=2))
print('NEX_WALKING_PACK_AUDIT',json.dumps({k:v for k,v in report.items() if k not in ('mesh_info','import_images')}))
