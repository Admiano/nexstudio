"""Refine authored female cosmetics/accessories without replacing facial geometry.

The source lip ribbon is made transparent by polygon; eyes and hairline keep
all their original geometry, keys, and weights. Earrings retain bone parenting.
"""
import math
import bpy
from mathutils import Vector

PROFILE='female-beauty-v10'


def remove_lip_ink():
    transparent=bpy.data.materials.get('CAST_LIP_ART_TRANSPARENT')
    if not transparent:
        transparent=bpy.data.materials.new('CAST_LIP_ART_TRANSPARENT');transparent.use_nodes=True
        tree=transparent.node_tree;tree.nodes.clear()
        shader=tree.nodes.new('ShaderNodeBsdfTransparent');output=tree.nodes.new('ShaderNodeOutputMaterial')
        tree.links.new(shader.outputs[0],output.inputs['Surface'])
    rows=[]
    for name in ('Host.V59_face_art','Host.V59_face_frame'):
        ob=bpy.data.objects.get(name)
        if not ob:continue
        # Original facial artwork is in rest cage coordinates. The mouth ribbon
        # occupies a disjoint region below the nose, never the eyelid/hairline.
        faces=[p for p in ob.data.polygons if all(abs(ob.data.vertices[i].co.x)<.030 and
               ob.data.vertices[i].co.y<-.09 and 1.465<ob.data.vertices[i].co.z<1.505 for i in p.vertices)]
        if not faces:continue
        slot=next((i for i,m in enumerate(ob.data.materials) if m==transparent),None)
        if slot is None:slot=len(ob.data.materials);ob.data.materials.append(transparent)
        for p in faces:p.material_index=slot
        rows.append(dict(object=name,transparentLipPolygons=len(faces)))
    return rows


def gold_material(scene):
    material=bpy.data.materials.get('CAST_BRUSHED_GOLD_V10')
    if not material:material=bpy.data.materials.new('CAST_BRUSHED_GOLD_V10')
    material.use_nodes=True;tree=material.node_tree;tree.nodes.clear()
    def mathnode(op,a,b):
        node=tree.nodes.new('ShaderNodeMath');node.operation=op
        for value,socket in zip((a,b),node.inputs):
            if isinstance(value,(int,float)):socket.default_value=value
            else:tree.links.new(value,socket)
        return node.outputs[0]
    normal=tree.nodes.new('ShaderNodeNewGeometry')
    # Curved reflection bands, tinted like warm 18k gold, track the camera.
    # The approved Cast lighting is emission based, so these analytical studio
    # reflections do not introduce lights that change the rest of the portrait.
    key=scene.camera.matrix_world.to_quaternion()@Vector((-.38,.62,.70)).normalized()
    dot=tree.nodes.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT'
    tree.links.new(normal.outputs['Normal'],dot.inputs[0]);dot.inputs[1].default_value=key
    fac=mathnode('ADD',mathnode('MULTIPLY',dot.outputs['Value'],.5),.5)
    ramp=tree.nodes.new('ShaderNodeValToRGB');ramp.name='Warm gold studio reflections';ramp.color_ramp.interpolation='EASE'
    colors=[(0,(.075,.035,.009,1)),(.30,(.25,.12,.027,1)),(.51,(.62,.34,.095,1)),(.67,(.88,.62,.25,1)),(.80,(1,.88,.62,1)),(.92,(.65,.39,.13,1)),(1,(.96,.78,.44,1))]
    cr=ramp.color_ramp;cr.elements.remove(cr.elements[1]);cr.elements[0].position=0;cr.elements[0].color=colors[0][1]
    for pos,color in colors[1:]:cr.elements.new(pos).color=color
    tree.links.new(fac,ramp.inputs['Fac'])
    output=tree.nodes.new('ShaderNodeOutputMaterial');em=tree.nodes.new('ShaderNodeEmission')
    tree.links.new(ramp.outputs['Color'],em.inputs['Color']);tree.links.new(em.outputs[0],output.inputs['Surface'])
    material['castBeautyProfile']=PROFILE
    return material


def pearl_material(scene,gold):
    material=bpy.data.materials.get('CAST_PEARL_V10')
    if not material:material=gold.copy();material.name='CAST_PEARL_V10'
    ramp=material.node_tree.nodes.get('Warm gold studio reflections')
    colors=[(.35,.33,.30,1),(.58,.55,.50,1),(.79,.76,.69,1),(.91,.88,.81,1),(1,.98,.92,1),(.87,.84,.78,1),(.98,.96,.90,1)]
    for element,color in zip(ramp.color_ramp.elements,colors):element.color=color
    for node in material.node_tree.nodes:
        if node.type=='VECT_MATH' and node.operation=='DOT_PRODUCT':node.inputs[1].default_value=scene.camera.matrix_world.to_quaternion()@Vector((-.38,.62,.70)).normalized()
    return material


def refine_other_earrings(scene,gold):
    rows=[]
    for side in ('R','L'):
        all_parts=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Host.V61_ear_') and o.name.endswith('_'+side)]
        for ob in all_parts:
            if '_rim_' in ob.name or '_hi_' in ob.name:ob.hide_render=True
        parts=[o for o in all_parts if '_rim_' not in o.name and '_hi_' not in o.name]
        if not parts:continue
        pivot=bpy.data.objects.get('Host.V61_ear_post_'+side) or bpy.data.objects.get('Host.V61_ear_pearl_'+side)
        fill=bpy.data.objects.get('Host.V60_ear_fill_'+side)
        if not pivot or not fill:raise RuntimeError('CAST_EARRING_LOBE_NOT_FOUND')
        if not pivot.get('castBeautyProfile'):
            reference=pivot.matrix_world.copy();inverse=reference.inverted()
            pts=[inverse@(fill.matrix_world@v.co) for v in fill.data.vertices]
            low=min(v.z for v in pts);lobe=[v for v in pts if v.z<low+.003]
            anchor=sum(lobe,Vector())/len(lobe);anchor.y-=.0012;anchor.z+=.0020
            center=sum((v.co for v in pivot.data.vertices),Vector())/len(pivot.data.vertices)
            if 'pearl' in pivot.name:center.z+=.001 # original post lies just above pearl centre
            delta=reference.to_3x3()@(anchor-center)
            for ob in parts:
                # Preserve each style's assembly and bone attachment, translating
                # the complete accessory by one shared lobe-derived displacement.
                world=ob.matrix_world.copy();world.translation+=delta;ob.matrix_world=world
                center_part=sum((v.co for v in ob.data.vertices),Vector())/len(ob.data.vertices)
                factors=(.65,.65,1) if '_bar_' in ob.name else (.72,.72,.72) if '_pearl_' in ob.name else (.82,.82,.92) if '_drop_' in ob.name else (1,1,1)
                for v in ob.data.vertices:
                    q=v.co-center_part;v.co=center_part+Vector(tuple(a*b for a,b in zip(q,factors)))
                for p in ob.data.polygons:p.use_smooth=True
                ob.data.update();ob['castBeautyProfile']=PROFILE;ob['castLobeDisplacement']=list(delta)
        for ob in parts:
            ob.data.materials.clear();ob.data.materials.append(pearl_material(scene,gold) if '_pearl_' in ob.name else gold)
            rows.append(dict(object=ob.name,style='pearl' if '_pearl_' in ob.name else 'bar' if '_bar_' in ob.name else 'teardrop' if '_drop_' in ob.name else 'attachment',bone=ob.parent_bone,blackRim=False,displacementWorldAtAssembly=list(ob.get('castLobeDisplacement',[]))))
    return rows


def refine_earrings(scene):
    material=gold_material(scene);rows=[]
    rings=[o for o in bpy.data.objects if o.name.startswith('Host.V60_earring') and 'rim' not in o.name and o.type=='MESH']
    for ob in rings:
        for child in ob.children:
            if 'rim' in child.name:child.hide_render=True
        # Cache the authored rest hoop and location so reapplying does not shrink
        # or slide the accessory. Preserve its original head-bone transform.
        if not ob.get('castBeautyProfile'):
            side=ob.name[-1] if ob.name.endswith(('_R','_L')) else None
            fill=bpy.data.objects.get('Host.V60_ear_fill_'+side if side else 'Host.V60_ear_fill')
            if fill:
                inv=ob.matrix_world.inverted()
                points=[inv@(fill.matrix_world@v.co) for v in fill.data.vertices]
                low=min(p.z for p in points)
                lobe=[p for p in points if p.z<low+.003]
                anchor=sum(lobe,Vector())/len(lobe)
                # Top of the hoop passes into the visible lobe, on its front
                # surface. The previous hoop sat 16 mm behind the drawn ear.
                anchor.y-=.0012;anchor.z+=.0016
            else:
                anchor=Vector((0,-.015,.012))
            ob['castEarringAnchor']=list(anchor)
            statement=max(v.co.z for v in ob.data.vertices)>.014
            rx,rz,wire=(.0105,.0135,.00095) if statement else (.0070,.0090,.00085)
            ob['castEarringSize']=[rx,rz,wire]
            center=anchor-Vector((0,0,rz))
            if len(ob.data.vertices)!=480:raise RuntimeError('CAST_UNEXPECTED_HOOP_TOPOLOGY')
            for i in range(48):
                a=2*math.pi*i/48;c=center+Vector((math.cos(a)*rx,0,math.sin(a)*rz))
                for j in range(10):
                    t=2*math.pi*j/10;n=Vector((math.cos(a)*math.cos(t)*rx/rz,math.sin(t),math.sin(a)*math.cos(t))).normalized()
                    ob.data.vertices[i*10+j].co=c+n*wire
            for p in ob.data.polygons:p.use_smooth=True
            ob.data.update();ob['castBeautyProfile']=PROFILE
        ob.data.materials.clear();ob.data.materials.append(material)
        rx,rz,wire=ob.get('castEarringSize',[.007,.009,.00085])
        rows.append(dict(object=ob.name,style='hoop',bone=ob.parent_bone,anchorLocal=list(ob['castEarringAnchor']),wireMetres=wire,outerSizeMetres=[2*(rx+wire),2*(rz+wire)],blackRim=False))
    rows.extend(refine_other_earrings(scene,material))
    return rows


def refine_mouth(scene):
    # The old vertex-parented painted aperture floats in front of the animated
    # teeth. Let the original rigged oral anatomy supply the speaking aperture.
    overlay=bpy.data.objects.get('Host.V11_mouth_interior')
    if overlay:overlay.hide_render=True
    teeth=bpy.data.objects.get('Host.teeth_base')
    if not teeth:return dict(hiddenPaintedInterior=bool(overlay),nativeTeeth=False)
    material=bpy.data.materials.get('CAST_NATURAL_IVORY_V10')
    if not material:material=bpy.data.materials.new('CAST_NATURAL_IVORY_V10')
    material.use_nodes=True;t=material.node_tree;t.nodes.clear()
    geo=t.nodes.new('ShaderNodeNewGeometry');dot=t.nodes.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT'
    t.links.new(geo.outputs['Normal'],dot.inputs[0]);dot.inputs[1].default_value=scene.camera.matrix_world.to_quaternion()@Vector((-.48,.45,.75)).normalized()
    light=t.nodes.new('ShaderNodeMapRange');light.clamp=True
    light.inputs['From Min'].default_value=-.4;light.inputs['From Max'].default_value=1
    light.inputs['To Min'].default_value=.84;light.inputs['To Max'].default_value=1
    t.links.new(dot.outputs['Value'],light.inputs['Value'])
    ao=t.nodes.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.012;ao.samples=32
    contact=t.nodes.new('ShaderNodeMapRange');contact.inputs['To Min'].default_value=.78;contact.inputs['To Max'].default_value=1
    t.links.new(ao.outputs['AO'],contact.inputs['Value'])
    factor=t.nodes.new('ShaderNodeMath');factor.operation='MULTIPLY'
    t.links.new(light.outputs['Result'],factor.inputs[0]);t.links.new(contact.outputs['Result'],factor.inputs[1])
    ivory=t.nodes.new('ShaderNodeMixRGB');ivory.blend_type='MULTIPLY';ivory.inputs[0].default_value=1
    ivory.inputs[1].default_value=(.89,.86,.80,1);t.links.new(factor.outputs[0],ivory.inputs[2])
    em=t.nodes.new('ShaderNodeEmission');out=t.nodes.new('ShaderNodeOutputMaterial')
    t.links.new(ivory.outputs[0],em.inputs['Color']);t.links.new(em.outputs[0],out.inputs['Surface'])
    teeth.data.materials.clear();teeth.data.materials.append(material)
    return dict(hiddenPaintedInterior=bool(overlay),nativeTeeth=True,liveOralContact=True)


def apply_female_beauty(scene):
    return dict(profile=PROFILE,lipArt=remove_lip_ink(),earrings=refine_earrings(scene),mouth=refine_mouth(scene))
