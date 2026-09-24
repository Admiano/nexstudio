"""V10: stable mask outline and rig-following interior ink from V9 MakeHuman scenes."""
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
s=bpy.context.scene
p='Host' if 'HOST_' in bpy.data.filepath else 'Guest'
body=bpy.data.objects[p+'.body']
rig=bpy.data.objects[p+'.rig']
garment=bpy.data.objects[p+('.female_elegantsuit01' if p=='Host' else '.male_elegantsuit01')]
layer=s.view_layers[0]

# Only render topological open edges on the garment with Freestyle. Its moving
# silhouette/contour detectors are excluded from the line set entirely.
s.render.use_freestyle=True
layer.use_freestyle=True
border_sources=bpy.data.collections.new(p+'_V10_FIXED_GARMENT_BORDERS')
s.collection.children.link(border_sources)
border_sources.objects.link(garment)
line=layer.freestyle_settings.linesets[0]
line.collection=border_sources
line.select_by_collection=True
line.select_border=True
for name in ('silhouette','contour','external_contour','suggestive_contour',
             'crease','ridge_valley','material_boundary','edge_mark'):
    setattr(line,'select_'+name,False)
for modifier in line.linestyle.geometry_modifiers:
    modifier.use=False

# ID masks correspond to the actually visible, deformed skin, clothes, shoes.
# Their union gives one clean exterior. Inside that exterior, separate cloth
# and shoe masks yield only the boundary between visible materials.
layer.use_pass_object_index=True
for ob in bpy.data.objects:
    if ob.name.startswith(p+'.') and ob.type=='MESH':ob.pass_index=0
body.pass_index=1
legs=bpy.data.objects.get(p+'.lineart_lower_legs')
if legs:legs.pass_index=1
garment.pass_index=2
for side in ('L','R'):
    bpy.data.objects[p+'.lineart_shoe.'+side].pass_index=3

tree=bpy.data.node_groups.new(p+'_V10_MASK_OUTLINE','CompositorNodeTree')
s.compositing_node_group=tree
nodes=tree.nodes
links=tree.links
render=nodes.new('CompositorNodeRLayers')
render.location=(-900,200)
def math_node(operation,a,b,label):
    n=nodes.new('ShaderNodeMath')
    n.operation=operation
    n.use_clamp=True
    n.label=label
    links.new(a,n.inputs[0]);links.new(b,n.inputs[1])
    return n.outputs[0]
def spread(mask,pixels,label):
    n=nodes.new('CompositorNodeDilateErode')
    n.inputs['Type'].default_value='Steps'
    n.inputs['Size'].default_value=pixels
    n.label=label
    links.new(mask,n.inputs['Mask'])
    return n.outputs['Mask']
masks=[]
for i,label in enumerate(('Skin','Clothing','Shoes'),1):
    m=nodes.new('CompositorNodeIDMask')
    m.inputs['Index'].default_value=i
    m.inputs['Anti-Alias'].default_value=True
    m.label=label+' visible ID'
    links.new(render.outputs['Object Index'],m.inputs['ID value'])
    masks.append(m.outputs['Alpha'])
visible=math_node('MAXIMUM',masks[0],masks[1],'Visible skin or clothes')
visible=math_node('MAXIMUM',visible,masks[2],'Visible character union')
outer=math_node('SUBTRACT',spread(visible,2,'Exterior width'),visible,'Outer ring')
for label,mask in zip(('Clothing','Shoes'),masks[1:]):
    ring=math_node('SUBTRACT',spread(mask,2,label+' border'),mask,label+' boundary')
    inside=math_node('MULTIPLY',ring,visible,label+' internal only')
    outer=math_node('MAXIMUM',outer,inside,'Combined clean ink')
mix=nodes.new('ShaderNodeMix')
mix.data_type='RGBA'
mix.blend_type='MIX'
mix.inputs[7].default_value=(.008,.008,.008,1)
links.new(outer,mix.inputs[0])
links.new(render.outputs['Image'],mix.inputs[6])
tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
output=nodes.new('NodeGroupOutput')
links.new(mix.outputs['Result'],output.inputs['Image'])

# Freestyle previously created the nostril, ear, and chin marks indirectly.
# They now live on the head. Jaw depth is bounded against all 360 face poses
# so the line remains visible during jawOpen without a per-frame transform.
s.frame_set(1)
dep=bpy.context.evaluated_depsgraph_get()
evaluated=body.evaluated_get(dep)
face_z=1.53 if p=='Host' else 1.60
scale=.54/720
ink=bpy.data.materials.get('V10_STABLE_FACE_INK') or bpy.data.materials.new('V10_STABLE_FACE_INK')
ink.use_nodes=True
ink.node_tree.nodes.clear()
em=ink.node_tree.nodes.new('ShaderNodeEmission')
em.inputs['Color'].default_value=(.005,.005,.005,1)
out=ink.node_tree.nodes.new('ShaderNodeOutputMaterial')
ink.node_tree.links.new(em.outputs[0],out.inputs['Surface'])

marks={
 'Host':{
  'nose_L':[(341,364),(344,362),(347,363),(351,365)],
  'nose_R':[(369,365),(372,363),(375,362),(379,364)],
  'ear_L':[(262,331),(267,341),(265,351),(268,361),(270,372)],
  'ear_R':[(457,331),(453,341),(455,351),(452,361),(450,372)],
  'jaw':[(299,423),(311,439),(335,451),(360,455),(385,451),(409,439),(421,423)],
 },
 'Guest':{
  'nose_L':[(336,361),(338,359),(340,361)],
  'nose_mid_L':[(345,367),(350,369),(354,368)],
  'nose_mid_R':[(365,368),(370,369),(374,367)],
  'nose_R':[(379,361),(381,359),(383,361)],
  'ear_L':[(250,311),(256,323),(253,335),(258,348),(263,359)],
  'ear_R':[(469,311),(463,323),(466,335),(461,348),(456,359)],
  'jaw':[(285,427),(295,443),(318,463),(343,476),(360,479),
         (377,476),(402,463),(425,443),(435,427)],
 },
}[p]

def surface_point(x,y,jaw=False):
    wx=s.camera.location.x+(x-360)*scale
    wz=face_z+(360-y)*scale
    start=evaluated.matrix_world.inverted()@Vector((wx,-5.,wz))
    direction=evaluated.matrix_world.inverted().to_3x3()@Vector((0,1,0))
    ok,co,normal,face=evaluated.ray_cast(start,direction)
    if not ok:raise RuntimeError(('face projection failed',p,x,y))
    return Vector((co.x,co.y-.003,co.z))

for name,points in marks.items():
    width=(2.25 if name.startswith('nose') else (2.1 if name=='jaw' else 1.55))*scale
    verts=[]
    for j,(x,y) in enumerate(points):
        ax,ay=points[max(0,j-1)];bx,by=points[min(len(points)-1,j+1)]
        tangent=Vector((bx-ax,by-ay)).normalized()
        perpendicular=Vector((-tangent.y,tangent.x))
        for sign in (-1,1):
            verts.append(surface_point(x+sign*perpendicular.x*width/scale/2,
                                       y+sign*perpendicular.y*width/scale/2,
                                       jaw=name=='jaw'))
    faces=[(2*j,2*j+1,2*j+3,2*j+2) for j in range(len(points)-1)]
    mesh=bpy.data.meshes.new(p+'.V10_'+name+'_mesh')
    mesh.from_pydata(verts,[],faces)
    mesh.materials.append(ink)
    obj=bpy.data.objects.new(p+'.V10_'+name,mesh)
    s.collection.objects.link(obj)
    obj.matrix_world=body.matrix_world.copy()
    world=obj.matrix_world.copy()
    obj.parent=rig
    obj.parent_type='BONE'
    obj.parent_bone='head'
    obj.matrix_world=world
    obj.visible_shadow=False
    obj.visible_diffuse=False
    obj.visible_glossy=False
    obj.visible_transmission=False
    obj.visible_volume_scatter=False
    obj['V10_ATTACHMENT']='Head bone; face-surface origin at frame 1'

# A jaw-open shape can bring the chin skin ~4 cm toward the camera at some
# visemes. Fixed-depth or nearest-surface projections either hide or smear the
# ink. Test every frame and give each existing vertex only the extra front
# clearance it needs over the full 15-second action.
jaw=bpy.data.objects[p+'.V10_jaw']
clearance=[0.0 for _ in jaw.data.vertices]
for frame in range(1,361):
    s.frame_set(frame)
    dep=bpy.context.evaluated_depsgraph_get()
    evaluated_body=body.evaluated_get(dep)
    inverse=evaluated_body.matrix_world.inverted()
    direction=inverse.to_3x3()@Vector((0,1,0))
    for i,vertex in enumerate(jaw.data.vertices):
        world=jaw.matrix_world@vertex.co
        origin=inverse@Vector((world.x,-5.,world.z))
        ok,co,normal,face=evaluated_body.ray_cast(origin,direction)
        if not ok:continue
        surface=(evaluated_body.matrix_world@co).y
        clearance[i]=max(clearance[i],world.y-surface+.004)
s.frame_set(1)
for i,shift in enumerate(clearance):
    jaw.data.vertices[i].co.y-=shift
jaw['V10_ATTACHMENT']='Head bone; front clearance checked against all 360 deformed poses'
jaw['V10_MAX_EXTRA_CLEARANCE_M']=round(max(clearance),5)

s.frame_set(1)
s.cycles.samples=12
s['V10_OUTLINE']='Stable ID-mask silhouette, topological garment borders, surface-bound face ink'
s['V10_SOURCE']='V9 rig, dialogue, gesture and clothing detail retained'
path=ROOT/(p.upper()+'_FULLBODY_15S_V10.blend')
bpy.ops.wm.save_as_mainfile(filepath=str(path))
print('V10_SAVED',path,flush=True)
