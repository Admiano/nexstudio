"""One tone-derived skin treatment on the approved rig and native male ears."""
import math
import bpy
from mathutils import Vector

PROFILE='tone-derived-skin-v1'

def linear_rgb(hx):
    hx=hx.lstrip('#')
    if len(hx)!=6 or any(c not in '0123456789abcdefABCDEF' for c in hx):
        raise ValueError('CAST_INVALID_SKIN_HEX')
    srgb=[int(hx[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4 for c in srgb)

def tone_from_material(material):
    if material.get('castSkinBase') is not None:
        return tuple(material['castSkinBase'])
    mix=material.node_tree.nodes.get('Mix')
    if mix and mix.type=='MIX':
        return tuple(mix.inputs[7].default_value[:3])
    raise RuntimeError('CAST_SKIN_BASE_NOT_FOUND')

def rebuild_skin(material,tone,key,fill,character):
    lip_colors=None
    if material.name=='PEEPS_V2_WARM_SKIN':
        if character=='male':
            luminance=sum(c*w for c,w in zip(tone,(0.2126,0.7152,0.0722)))
            warmth=max(0,min(1,(luminance-0.45)/0.35))
            lip_colors=[tuple(c*(a+(b-a)*warmth) for c,a,b in zip(tone,lo,hi))
                        for lo,hi in (((0.45,0.34,0.50),(0.58,0.32,0.34)),((0.55,0.42,0.60),(0.70,0.43,0.44)))]
        elif material.get('castLipColors') is not None:
            lip_colors=[tuple(material['castLipColors'][:3]),tuple(material['castLipColors'][3:])]
        else:
            original=material.node_tree.nodes.get('Mix.002')
            if original:lip_colors=[tuple(original.inputs[i].default_value[:3]) for i in (6,7)]
    tree=material.node_tree;tree.nodes.clear()
    def node(kind,name):
        n=tree.nodes.new(kind);n.name=name;n.label=name;return n
    def mathnode(op,name,a=None,b=None):
        n=node('ShaderNodeMath',name);n.operation=op
        for i,v in enumerate((a,b)):
            if v is None:continue
            if isinstance(v,(int,float)):n.inputs[i].default_value=v
            else:tree.links.new(v,n.inputs[i])
        return n.outputs[0]
    geo=node('ShaderNodeNewGeometry','Live skin surface')
    base=node('ShaderNodeRGB','Selected complexion');base.outputs[0].default_value=(*tone,1)
    surface_color=base.outputs[0]
    if lip_colors:
        blush=node('ShaderNodeAttribute','Anatomical cheek warmth');blush.attribute_name='blush'
        warm=node('ShaderNodeMixRGB','Subtle tone-relative cheek warmth');warm.inputs[2].default_value=(*[c*k for c,k in zip(tone,(1.03,0.94,0.95))],1)
        tree.links.new(surface_color,warm.inputs[1]);tree.links.new(mathnode('MULTIPLY','Cheek warmth weight',blush.outputs['Fac'],0.18),warm.inputs[0])
        mask=node('ShaderNodeAttribute','Original lip mask');mask.attribute_name='lipmask'
        lipmask=node('ShaderNodeMapRange','Original lip boundary');lipmask.interpolation_type='SMOOTHSTEP'
        lipmask.inputs['From Min'].default_value=-0.025;lipmask.inputs['From Max'].default_value=0.025
        tree.links.new(mask.outputs['Fac'],lipmask.inputs['Value'])
        lower=node('ShaderNodeAttribute','Original lip contour');lower.attribute_name='liplo'
        lip=node('ShaderNodeMixRGB','Preserved lip palette')
        lip.inputs[1].default_value=(*lip_colors[0],1);lip.inputs[2].default_value=(*lip_colors[1],1)
        tree.links.new(lower.outputs['Fac'],lip.inputs[0])
        combined=node('ShaderNodeMixRGB','Skin and lip colour')
        tree.links.new(lipmask.outputs['Result'],combined.inputs[0]);tree.links.new(warm.outputs[0],combined.inputs[1]);tree.links.new(lip.outputs[0],combined.inputs[2])
        surface_color=combined.outputs[0]
        material['castLipColors']=[c for color in lip_colors for c in color]
    def diffuse(direction,name):
        dot=node('ShaderNodeVectorMath',name+' direction');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=direction
        tree.links.new(geo.outputs['Normal'],dot.inputs[0])
        ramp=node('ShaderNodeMapRange',name+' soft falloff');ramp.interpolation_type='SMOOTHSTEP'
        ramp.inputs['From Min'].default_value=-0.30;ramp.inputs['From Max'].default_value=0.95
        tree.links.new(dot.outputs['Value'],ramp.inputs['Value'])
        return ramp.outputs['Result']
    k=diffuse(key,'Broad key');f=diffuse(fill,'Soft fill')
    illumination=mathnode('ADD','Key and fill',mathnode('MULTIPLY','Key weight',k,0.35),mathnode('MULTIPLY','Fill weight',f,0.11))
    illumination=mathnode('ADD','Ambient floor',illumination,0.62)
    ao=node('ShaderNodeAmbientOcclusion','Short live contact');ao.only_local=True;ao.samples=32;ao.inputs['Distance'].default_value=0.018
    crevice=mathnode('SUBTRACT','Contact cavity',1,ao.outputs['AO'])
    contact=mathnode('SUBTRACT','Bounded contact',1,mathnode('MULTIPLY','Contact weight',crevice,0.16))
    factor=mathnode('MULTIPLY','Single shading factor',illumination,contact)
    color=node('ShaderNodeMixRGB','Complexion times surface light');color.blend_type='MULTIPLY';color.inputs[0].default_value=1
    tree.links.new(surface_color,color.inputs[1]);tree.links.new(factor,color.inputs[2])
    emission=node('ShaderNodeEmission','Skin output');tree.links.new(color.outputs[0],emission.inputs['Color'])
    output=node('ShaderNodeOutputMaterial','Material Output');tree.links.new(emission.outputs[0],output.inputs['Surface'])
    material['castSkinProfile']=PROFILE;material['castSkinBase']=tone
    return {'material':material.name,'nodes':len(tree.nodes),'baseLinear':list(tone),'contactDistance':0.018,'contactWeight':0.16,'fixedSkinColourMasks':False}

def apply_skin_appearance(scene,character,skin_hex='',native_ear=True):
    scene.cycles.samples=max(scene.cycles.samples,32)
    body_material=bpy.data.materials['PEEPS_V2_WARM_SKIN']
    tone=linear_rgb(skin_hex) if skin_hex else tone_from_material(body_material)
    if not all(math.isfinite(c) and 0<=c<=1 for c in tone):raise RuntimeError('CAST_INVALID_SKIN_BASE')
    # Camera-relative illumination preserves the screen-space portrait setup.
    rotation=scene.camera.matrix_world.to_quaternion()
    key=rotation@Vector((-0.48,0.45,0.75)).normalized()
    fill=rotation@Vector((0.65,0.30,0.70)).normalized()
    report={'profile':PROFILE,'character':character,'selectedHex':skin_hex or None,'materials':[],'hiddenEarOverlays':[]}
    for name in ('PEEPS_V2_WARM_SKIN','V60_EAR_SKIN','LINEART_SKIN_WHITE'):
        material=bpy.data.materials.get(name)
        if material:report['materials'].append(rebuild_skin(material,tone,key,fill,character))
    if character=='male' and native_ear:
        for ob in bpy.data.objects:
            if ob.name.startswith(('Host.V60_ear_fill','Host.V60_ear_line','Host.V60_ear_inner')):
                ob.hide_render=True;report['hiddenEarOverlays'].append(ob.name)
    return report
