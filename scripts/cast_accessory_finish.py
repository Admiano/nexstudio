"""Illustrated accessory surfaces and stable, capped mesh tubing. Blender 5.2."""
import math
import bpy
from mathutils import Vector

def linear_color(hexcode):
    rgb=[int(hexcode.lstrip('#')[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb)

def finish_material(name,hexcode,kind='matte'):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes=True;nt=m.node_tree;nt.nodes.clear();n=nt.nodes;l=nt.links
    geo=n.new('ShaderNodeNewGeometry');dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=Vector((-.45,-.7,.55)).normalized();l.new(geo.outputs['Normal'],dot.inputs[0])
    shade=n.new('ShaderNodeMapRange');shade.clamp=True
    shade.inputs['From Min'].default_value=-.7;shade.inputs['From Max'].default_value=.9
    shade.inputs['To Min'].default_value=.58 if kind=='metal' else .76
    shade.inputs['To Max'].default_value=1.04
    l.new(dot.outputs['Value'],shade.inputs['Value'])
    mult=n.new('ShaderNodeMixRGB');mult.blend_type='MULTIPLY';mult.inputs[0].default_value=1;mult.inputs[1].default_value=(*linear_color(hexcode),1);l.new(shade.outputs[0],mult.inputs[2])
    ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.008;ao.samples=8
    contact=n.new('ShaderNodeMapRange');contact.inputs['From Min'].default_value=0;contact.inputs['From Max'].default_value=1;contact.inputs['To Min'].default_value=.72;contact.inputs['To Max'].default_value=1;l.new(ao.outputs['AO'],contact.inputs['Value'])
    mul2=n.new('ShaderNodeMixRGB');mul2.blend_type='MULTIPLY';mul2.inputs[0].default_value=1;l.new(mult.outputs[0],mul2.inputs[1]);l.new(contact.outputs[0],mul2.inputs[2]);color=mul2.outputs[0]
    if kind in ('metal','pearl','glass'):
        h=n.new('ShaderNodeVectorMath');h.operation='DOT_PRODUCT';h.inputs[1].default_value=Vector((-.3,-.85,.43)).normalized();l.new(geo.outputs['Normal'],h.inputs[0])
        positive=n.new('ShaderNodeMath');positive.operation='MAXIMUM';positive.inputs[1].default_value=0;l.new(h.outputs['Value'],positive.inputs[0])
        power=n.new('ShaderNodeMath');power.operation='POWER';power.inputs[1].default_value=40 if kind=='metal' else 18 if kind=='pearl' else 70;l.new(positive.outputs[0],power.inputs[0])
        add=n.new('ShaderNodeMixRGB');add.blend_type='ADD';add.inputs[0].default_value=.25 if kind=='metal' else .11 if kind=='pearl' else .07;l.new(color,add.inputs[1]);l.new(power.outputs[0],add.inputs[2]);color=add.outputs[0]
    if kind in ('leather','silk','velvet'):
        noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1600 if kind=='leather' else 2200;noise.inputs['Detail'].default_value=1
        texture=n.new('ShaderNodeMapRange');texture.inputs['To Min'].default_value=.95;texture.inputs['To Max'].default_value=1.025;l.new(noise.outputs['Fac'],texture.inputs['Value'])
        grain=n.new('ShaderNodeMixRGB');grain.blend_type='MULTIPLY';grain.inputs[0].default_value=1;l.new(color,grain.inputs[1]);l.new(texture.outputs[0],grain.inputs[2]);color=grain.outputs[0]
    emission=n.new('ShaderNodeEmission');l.new(color,emission.inputs['Color']);out=n.new('ShaderNodeOutputMaterial');l.new(emission.outputs[0],out.inputs[0]);m.diffuse_color=(*linear_color(hexcode),1)
    m['accessory_finish']='illustrated-v17';m['finish_kind']=kind
    return m

def make_tube(name,points,radius,material,closed=False,collection=None,sides=12):
    P=[Vector(p) for p in points];verts=[];faces=[];last=None
    for i,p in enumerate(P):
        tangent=(P[(i+1)%len(P)]-P[(i-1)%len(P)] if closed else P[min(i+1,len(P)-1)]-P[max(i-1,0)]).normalized()
        # Parallel transport avoids a visible seam when a link tangent is vertical.
        axis=last-tangent*last.dot(tangent) if last is not None else Vector((0,0,1)).cross(tangent)
        if axis.length<1e-6:axis=Vector((1,0,0)).cross(tangent)
        axis.normalize();other=tangent.cross(axis).normalized();last=axis
        rr=radius[i] if isinstance(radius,(list,tuple)) else radius
        verts.extend(p+rr*(math.cos(2*math.pi*j/sides)*axis+math.sin(2*math.pi*j/sides)*other) for j in range(sides))
    for i in range(len(P) if closed else len(P)-1):
        for j in range(sides):faces.append((i*sides+j,((i+1)%len(P))*sides+j,((i+1)%len(P))*sides+(j+1)%sides,i*sides+(j+1)%sides))
    if not closed:faces.extend([tuple(reversed(range(sides))),tuple((len(P)-1)*sides+j for j in range(sides))])
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.materials.append(material);mesh.update()
    for polygon in mesh.polygons:polygon.use_smooth=True
    obj=bpy.data.objects.new(name,mesh);(collection or bpy.context.scene.collection).objects.link(obj)
    obj['accessory_detail']='v17';return obj

def fit_neck_attachment(objects,rig):
    """Bind rest-space jewellery to the helper-free, subdivided skin surface."""
    body=bpy.data.objects['Host.body']
    full=next((o for o in bpy.data.objects if o.name.startswith('Cast accessory skin target V17') and o.type=='MESH'),body)
    for obj in objects:
        if obj.type!='MESH':continue
        mw=obj.matrix_world.copy();obj.parent=None;obj.matrix_world=mw
        obj.data.transform(mw);obj.matrix_world.identity()
        modifier=obj.modifiers.new('V17 matched skin surface','SURFACE_DEFORM');modifier.target=full
        bpy.context.view_layer.objects.active=obj;obj.select_set(True)
        bpy.ops.object.surfacedeform_bind(modifier=modifier.name)
        obj.select_set(False)
        if not modifier.is_bound:raise RuntimeError('ACCESSORY_SURFACE_BINDING_FAILED')
        obj['accessory_attachment']='bound helper-free skin surface'
