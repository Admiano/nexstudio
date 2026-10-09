"""Rig-bound illustrated colour planes and six restrained makeup palettes.

Coordinates and region masks are attached to the original cage before armature
and subdivision evaluation. Nothing uses world position or changes the cage,
shape keys, rig, or semantic lip boundary. Distances are measured in metres.
"""
import math
import hashlib
from pathlib import Path
import os
import bpy
from mathutils import Vector

PROFILE = 'illustrated-colour-planes-v14'
# Sheer blush, satin eye wash, natural upper/lower lips. Authored in sRGB.
MAKEUP = {
    'F7E1D3': ('fair', 'D78E91', 'A9827A', 'B6757F', 'CF9196', .33, .34),
    'F1D7C8': ('light', 'C9797E', '987261', 'B76C76', 'C78086', .35, .36),
    'E0B48F': ('medium', 'B76D61', '966B55', 'AC6461', 'C47F72', .37, .38),
    'C99A6E': ('tan', 'A65F49', '8D5E44', '9A5450', 'B97065', .40, .40),
    '9E6B4A': ('brown', 'A65F5B', '865A4D', '82434C', 'AD6972', .36, .42),
    '6A4431': ('deep', '984C50', '8B5A59', '70404F', '9E6574', .30, .44),
}


def linear_rgb(hx):
    hx = hx.lstrip('#')
    if len(hx) != 6 or any(c not in '0123456789abcdefABCDEF' for c in hx):
        raise ValueError('CAST_INVALID_SKIN_HEX')
    return tuple(c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4
                 for c in (int(hx[i:i + 2], 16) / 255 for i in (0, 2, 4)))


def tone_from_material(material):
    if material.get('castSkinBase') is not None:
        return tuple(material['castSkinBase'])
    mix = material.node_tree.nodes.get('Mix')
    if mix and mix.type == 'MIX':
        return tuple(mix.inputs[7].default_value[:3])
    raise RuntimeError('CAST_SKIN_BASE_NOT_FOUND')


def palette_for(tone):
    # Custom colours inherit the closest palette in linear RGB, retaining their
    # exact base colour. Every predetermined colour resolves to its own row.
    hx = min(MAKEUP, key=lambda h: sum((a - b) ** 2 for a, b in zip(tone, linear_rgb(h))))
    row = MAKEUP[hx]
    return dict(skinHex=hx, name=row[0], blush=linear_rgb(row[1]), eye=linear_rgb(row[2]),
                lips=(linear_rgb(row[3]), linear_rgb(row[4])), blushWeight=row[5], eyeWeight=row[6])


def prepare_surface(body, character):
    required=('cast_skin_rest','cast_skin_regions','cast_skin_makeup','cast_skin_joint',
              'cast_skin_palm','cast_skin_anatomy','cast_skin_nail','cast_skin_anterior')
    if (body.get('castSkinSurfaceProfile') == PROFILE and
        all(body.data.attributes.get(name) for name in required)):
        saved=body['castSkinSurfaceReport']
        return {key:list(value) if key=='attributes' else value for key,value in saved.items()}
    mesh = body.data
    scale = sum(body.matrix_world.to_scale()) / 3
    groups = {g.name: g.index for g in body.vertex_groups}
    weights = [{g.group: g.weight for g in v.groups} for v in mesh.vertices]
    normals = [v.normal.copy() for v in mesh.vertices]
    positions = [v.co.copy() for v in mesh.vertices]
    def center(name):
        gi = groups[name];vs = [v.co for v,w in zip(mesh.vertices,weights) if w.get(gi,0) > .5]
        return sum(vs,Vector()) / len(vs)
    def gauss(v, center, widths):
        return math.exp(-sum(((a-b)/s)**2 for a,b,s in zip(v,center,widths)))
    eyes = [center('joint-'+s+'-eye') for s in ('l','r')]
    neck = center('joint-neck')
    nails = groups['fingernails']
    hand_data = []
    for side,sign in (('l',1),('r',-1)):
        wrist = center('joint-'+side+'-hand')
        index = center('joint-'+side+'-finger-2-1')
        little = center('joint-'+side+'-finger-5-1')
        cross = (little-index).normalized();forward = ((index+little)*.5-wrist).normalized()
        nv = [v.normal for v,w in zip(mesh.vertices,weights) if v.co.x*sign>0 and w.get(nails,0)>.5]
        dorsal = sum(nv,Vector()).normalized()
        joints=[];tips=[]
        for i in range(1,6):
            points=[center('joint-'+side+'-finger-%d-%d'%(i,j)) for j in range(1,5)]
            tips.append((points[3],(points[3]-points[2]).normalized()))
            for j in range(3):
                joints.append((points[j],(points[j+1]-points[j]).normalized()))
        hand_groups={g for name,g in groups.items() if name=='wrist.'+side.upper() or
                     (name.startswith(('finger','metacarpal')) and name.endswith('.'+side.upper()))}
        hand_data.append((sign,wrist,index,little,cross,forward,dorsal,joints,hand_groups,tips))
    def attribute(name,kind):
        old=mesh.attributes.get(name)
        if old and (old.data_type!=kind or old.domain!='POINT'):mesh.attributes.remove(old);old=None
        return old or mesh.attributes.new(name,kind,'POINT')
    rest=attribute('cast_skin_rest','FLOAT_VECTOR')
    regions=attribute('cast_skin_regions','FLOAT_VECTOR') # face, oil, nail
    makeup=attribute('cast_skin_makeup','FLOAT_VECTOR') # cheek, lid, highlight
    joint=attribute('cast_skin_joint','FLOAT_VECTOR') # signed metres, proximity, palm
    chart=attribute('cast_skin_palm','FLOAT_VECTOR') # transverse, longitudinal, palm
    anterior=attribute('cast_skin_anterior','FLOAT')
    nail_detail=attribute('cast_skin_nail','FLOAT')
    nail_extents={}
    for d in hand_data:
        for tip,axis in d[-1]:
            points=[positions[v.index] for v,w in zip(mesh.vertices,weights) if w.get(nails,0)>.5 and v.co.x*d[0]>0 and min(d[-1],key=lambda t:(positions[v.index]-t[0]).length_squared)[0]==tip]
            nail_extents[tuple(tip)]=max(((p-tip).dot(axis) for p in points),default=0)
    anatomy=attribute('cast_skin_anatomy','FLOAT') # broad anatomical relief in metres
    for v,w in zip(mesh.vertices,weights):
        p=positions[v.index];normal=normals[v.index];front=max(0,min(1,(-normal.y-.05)/.8))
        face=max(gauss(p,e+Vector((0,0,.015)),(.070,.055,.093)) for e in eyes)*front
        oil=max(gauss(p,Vector((0,eyes[0].y-.015,eyes[0].z-.022)),(.016,.040,.040)),
                gauss(p,Vector((0,eyes[0].y+.010,eyes[0].z+.044)),(.039,.040,.025)))*front
        cheeks=max(gauss(p,e+Vector((.011 if e.x>0 else -.011,.006,-.025)),(.022,.040,.014)) for e in eyes)*front
        lids=max(gauss(p,e+Vector((.002 if e.x>0 else -.002,0,.008)),(.020,.035,.0090)) for e in eyes)*front
        highlight=max(gauss(p,e+Vector((.014 if e.x>0 else -.014,.003,-.013)),(.020,.040,.009)) for e in eyes)*front
        h=max(0,min(1,(p.z-neck.z)/.085));dx=abs(p.x)-(.018+.040*h)
        ng=math.exp(-((p.z-(neck.z+.017))/.071)**4)*front
        relief=ng*((.0020 if character=='male' else .0011)*math.exp(-(dx/.010)**2)
                   +(.00070 if character=='male' else .00018)*gauss(p,(0,p.y,neck.z+.031),(.012,1,.015))
                   -.0006*gauss(p,(0,p.y,neck.z-.027),(.013,1,.012)))
        rest.data[v.index].vector=p*scale
        regions.data[v.index].vector=(face,oil,w.get(nails,0))
        makeup.data[v.index].vector=(cheeks,lids,highlight)
        anatomy.data[v.index].value=relief*scale
        anterior.data[v.index].value=front
        data=next(d for d in hand_data if p.x*d[0]>=0)
        sign,wrist,index,little,cross,forward,dorsal,joints,hg,tips=data
        hw=min(1,sum(w.get(g,0) for g in hg));palm=max(0,min(1,(.20-normal.dot(dorsal))/.9))*hw
        nearest=min(joints,key=lambda j:(p-j[0]).length_squared)
        delta=p-nearest[0];signed=delta.dot(nearest[1])*scale
        proximity=math.exp(-((delta-nearest[1]*delta.dot(nearest[1])).length/.014)**4)*hw
        joint.data[v.index].vector=(signed,proximity,palm)
        u=(p-index).dot(cross)/max((little-index).length,.01)
        vv=(p-wrist).dot(forward)/max(((index+little)*.5-wrist).length,.01)
        chart.data[v.index].vector=(u,vv,palm)
        tip,axis=min(tips,key=lambda t:(p-t[0]).length_squared)
        nail_detail.data[v.index].value=((p-tip).dot(axis)-nail_extents[tuple(tip)])*scale
    mesh.update()
    report={'coordinateSpace':'rest-surface metres','vertices':len(mesh.vertices),
            'attributes':[a.name for a in (rest,regions,makeup,joint,chart,anatomy,nail_detail,anterior)],
            'neckRestZ':neck.z*scale,'neckScale':scale}
    body['castSkinSurfaceProfile']=PROFILE;body['castSkinSurfaceReport']=report
    return report


class SurfaceNodes:
    def __init__(self,tree):self.t=tree
    def node(self,kind,name):
        n=self.t.nodes.new(kind);n.name=name;n.label=name;return n
    def wire(self,value,socket):
        if isinstance(value,(int,float)):socket.default_value=value
        elif isinstance(value,(tuple,list,Vector)):socket.default_value=value
        else:self.t.links.new(value,socket)
    def math(self,op,name,a,b=None):
        n=self.node('ShaderNodeMath',name);n.operation=op
        self.wire(a,n.inputs[0])
        if b is not None:self.wire(b,n.inputs[1])
        return n.outputs[0]
    def attr(self,name):
        n=self.node('ShaderNodeAttribute',name);n.attribute_name=name;return n
    def split(self,value,name):
        n=self.node('ShaderNodeSeparateXYZ',name);self.wire(value,n.inputs[0]);return n.outputs
    def mix(self,name,factor,a,b,mode='MIX'):
        n=self.node('ShaderNodeMixRGB',name);n.blend_type=mode
        self.wire(factor,n.inputs[0]);self.wire(a,n.inputs[1]);self.wire(b,n.inputs[2]);return n.outputs[0]
    def gaussian(self,name,value,width):
        sq=self.math('MULTIPLY',name+' squared',value,value)
        return self.math('EXPONENT',name,self.math('MULTIPLY',name+' width',sq,-1/(width*width)))


def rebuild_skin(material,tone,key,fill,character,palette,surface,lip_hex):
    """Illustrated colour planes: surface normals guide paint, never skin gloss.

    The original cage and semantic feature boundaries drive this finish.
    No bump, scattering, view-dependent sheen or physical skin shader is used.
    """
    main=material.name=='PEEPS_V2_WARM_SKIN'
    lip_colors=None
    if main:
        if character=='female':
            selected=linear_rgb(lip_hex) if lip_hex else None
            lip_colors=(tuple(c*.78 for c in selected),selected) if selected else palette['lips']
        else:
            lum=sum(c*w for c,w in zip(tone,(.2126,.7152,.0722)))
            warmth=max(0,min(1,(lum-.45)/.35))
            lip_colors=[tuple(c*(a+(b-a)*warmth) for c,a,b in zip(tone,lo,hi))
                        for lo,hi in (((.45,.34,.50),(.58,.32,.34)),((.55,.42,.60),(.70,.43,.44)))]
    tree=material.node_tree;tree.nodes.clear();s=SurfaceNodes(tree)
    geo=s.node('ShaderNodeNewGeometry','Original facial planes')
    base=s.node('ShaderNodeRGB','Selected complexion');base.outputs[0].default_value=(*tone,1)
    color=base.outputs[0];rest=s.attr('cast_skin_rest').outputs['Vector']
    if main:
        regions=s.split(s.attr('cast_skin_regions').outputs['Vector'],'Face and nail regions')
        makeup=s.split(s.attr('cast_skin_makeup').outputs['Vector'],'Drawn colour accents')
        palm=s.split(s.attr('cast_skin_palm').outputs['Vector'],'Palm chart')
        boundary=s.node('ShaderNodeMapRange','Original lip boundary');boundary.interpolation_type='SMOOTHSTEP'
        boundary.inputs['From Min'].default_value=-.040;boundary.inputs['From Max'].default_value=.040
        s.wire(s.attr('lipmask').outputs['Fac'],boundary.inputs['Value']);lipmask=boundary.outputs['Result']
        warmth=tuple(min(1,c*k) for c,k in zip(tone,(1.05,.98,.97)))
        color=s.mix('Restrained cheek colour',s.math('MULTIPLY','Cheek warmth coverage',makeup['X'],.25),color,(*warmth,1))
        if character=='female':
            color=s.mix('Sheer drawn blush',s.math('MULTIPLY','Blush coverage',makeup['X'],palette['blushWeight']*.55),color,(*palette['blush'],1))
            color=s.mix('Soft eyelid wash',s.math('MULTIPLY','Eye wash coverage',makeup['Y'],palette['eyeWeight']*.45),color,(*palette['eye'],1))
        lum=sum(c*w for c,w in zip(tone,(.2126,.7152,.0722)))
        palm_tone=tuple(c*.85+d*.15 for c,d in zip(tone,linear_rgb('D6AA92')))
        color=s.mix('Palmar colour',s.math('MULTIPLY','Palm wash',palm['Z'],.18+(1-lum)*.40),color,(*palm_tone,1))
        nails=tuple(c*.35+d*.65 for c,d in zip(tone,linear_rgb('D4ABA2' if lum>.25 else 'B58376')))
        color=s.mix('Drawn nail beds',regions['Z'],color,(*nails,1))
        lips=s.mix('Upper and lower lip paint',s.attr('liplo').outputs['Fac'],(*lip_colors[0],1),(*lip_colors[1],1))
        color=s.mix('Original anatomical lip boundary',lipmask,color,lips)
    # Very faint pigment texture gives colour a drawn finish without relief.
    grain=s.node('ShaderNodeTexNoise','Fine pigment texture');grain.inputs['Scale'].default_value=950
    grain.inputs['Detail'].default_value=1;s.wire(rest,grain.inputs['Vector'])
    modulation=s.math('ADD','Restrained pigment bounds',.994,s.math('MULTIPLY','Pigment variation',grain.outputs['Fac'],.012))
    color=s.mix('Quiet pigment finish',1,color,modulation,'MULTIPLY')
    def plane(direction,name):
        dot=s.node('ShaderNodeVectorMath',name);dot.operation='DOT_PRODUCT'
        s.wire(geo.outputs['Normal'],dot.inputs[0]);dot.inputs[1].default_value=direction
        return dot.outputs['Value']
    illumination=s.math('ADD','Broad plane balance',s.math('MULTIPLY','Key plane influence',plane(key,'Key plane direction'),.8),s.math('MULTIPLY','Fill plane influence',plane(fill,'Fill plane direction'),.2))
    domain=s.node('ShaderNodeMapRange','Illustrated shade domain');domain.clamp=True
    domain.inputs['From Min'].default_value=-.30;domain.inputs['From Max'].default_value=1
    s.wire(illumination,domain.inputs['Value'])
    ramp=s.node('ShaderNodeValToRGB','Painted shadow midtone and light');ramp.color_ramp.interpolation='EASE'
    stops=[(0,(.72,.65,.66,1)),(.42,(.83,.77,.78,1)),(.73,(.95,.92,.92,1)),(1,(1.02,1.01,1,1))]
    for i,(position,col) in enumerate(stops):
        element=ramp.color_ramp.elements[i] if i<2 else ramp.color_ramp.elements.new(position)
        element.position=position;element.color=col
    s.wire(domain.outputs['Result'],ramp.inputs['Fac'])
    color=s.mix('Complexion with coloured plane shading',1,color,ramp.outputs['Color'],'MULTIPLY')
    ao=s.node('ShaderNodeAmbientOcclusion','Small feature contact');ao.only_local=True;ao.samples=16;ao.inputs['Distance'].default_value=.006
    contact=s.math('SUBTRACT','Restrained contact shading',1,s.math('MULTIPLY','Small contact weight',s.math('SUBTRACT','Feature contact',1,ao.outputs['AO']),.08))
    color=s.mix('Drawn feature separation',1,color,contact,'MULTIPLY')
    emission=s.node('ShaderNodeEmission','Illustrated skin output');s.wire(color,emission.inputs['Color'])
    output=s.node('ShaderNodeOutputMaterial','Material Output');s.wire(emission.outputs[0],output.inputs['Surface'])
    material['castSkinProfile']=PROFILE;material['castSkinBase']=tone
    if lip_colors:material['castLipColors']=[c for col in lip_colors for c in col]
    return dict(material=material.name,nodes=len(tree.nodes),baseLinear=list(tone),
                shader='Illustrated colour planes',physicalSkin=False,subsurfaceWeight=0,
                pores=False,bump=False,viewDependentSheen=False,contactDistance=.006,contactWeight=.08,
                fixedSkinColourMasks=False,makeupPalette=palette['name'] if main and character=='female' else None,
                explicitLipOverride=bool(lip_hex) if main and character=='female' else False)


def apply_portrait_lighting(scene):
    """A single camera-relative studio rig, shared by all complexion choices.

    The target comes from the evaluated head, independent of portrait/thigh
    crop, and update-in-place makes repeated assembly deterministic.
    """
    body=bpy.data.objects['Host.body']
    female=body.get('castSkinCharacter')=='female'
    rig=next((m.object for m in body.modifiers if m.type=='ARMATURE'),None)
    if rig is None:raise RuntimeError('CAST_SKIN_ORIGINAL_RIG_MISSING')
    target=rig.matrix_world@rig.data.bones['head'].head_local
    target.z+=.065
    rotation=scene.camera.matrix_world.to_quaternion()
    specs=[('Key',(-.35,.32,1.1) if female else (-.50,.55,1.0),8 if female else 14,.95 if female else .85,(1,.97,.94)),
           ('Fill',(.18,.04,1.05) if female else (.65,.12,.75),5.5 if female else 4.5,1.15 if female else 1.0,(1,.98,.96)),
           ('Edge',(.48,.46,-.55),5,.65,(1,.95,.88))]
    names={'Cast skin V13 '+x[0] for x in specs}
    for ob in scene.objects:
        if ob.type=='LIGHT' and ob.name not in names:
            if 'castV13OriginalHideRender' not in ob:ob['castV13OriginalHideRender']=ob.hide_render
            ob.hide_render=True
    rows=[]
    for label,offset,power,size,color in specs:
        name='Cast skin V13 '+label;ob=bpy.data.objects.get(name)
        if ob is None:
            data=bpy.data.lights.new(name,'AREA');ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob)
        ob.hide_render=False;ob.data.energy=power;ob.data.shape='DISK';ob.data.size=size;ob.data.color=color
        ob.location=target+rotation@Vector(offset);ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
        rows.append(dict(name=name,energyWatts=power,sizeMetres=size,location=list(ob.location)))
    # Preserve the approved colour transform for the illustrated wardrobe.
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
    if scene.world and scene.world.use_nodes:
        for n in scene.world.node_tree.nodes:
            if n.type=='BACKGROUND':n.inputs['Color'].default_value=(1,.98,.96,1);n.inputs['Strength'].default_value=.10
    return rows


def refine_face_contours(scene):
    rows=[]
    for layer in scene.view_layers:
        for lines in layer.freestyle_settings.linesets:
            if lines.name not in ('HEAD_FEATURES','HEAD_NOSE','HEAD_OUTLINE'):continue
            style=lines.linestyle
            if 'castV13OriginalAlpha' not in style:style['castV13OriginalAlpha']=style.alpha
            if 'castV13OriginalColor' not in style:style['castV13OriginalColor']=list(style.color)
            style.alpha=.72 if lines.name=='HEAD_NOSE' else .78 if lines.name=='HEAD_FEATURES' else .95
            style.color=(.08,.050,.035)
            rows.append(dict(name=lines.name,alpha=style.alpha))
    return rows


def apply_skin_appearance(scene,character,skin_hex='',native_ear=True,lip_hex=None):
    if character not in ('female','male'):raise ValueError('CAST_INVALID_CHARACTER')
    scene.cycles.samples=max(scene.cycles.samples,64)
    # Keep noise in supporting hair/wardrobe quiet; skin has no microrelief.
    scene.cycles.use_denoising=True
    material=bpy.data.materials['PEEPS_V2_WARM_SKIN']
    tone=linear_rgb(skin_hex) if skin_hex else tone_from_material(material)
    if not all(math.isfinite(c) and 0<=c<=1 for c in tone):raise RuntimeError('CAST_INVALID_SKIN_BASE')
    if lip_hex is None:lip_hex=os.environ.get('CAST_LIP_HEX','')
    if lip_hex:linear_rgb(lip_hex)
    palette=palette_for(tone)
    surface=prepare_surface(bpy.data.objects['Host.body'],character)
    skin_names={'PEEPS_V2_WARM_SKIN','V60_EAR_SKIN','LINEART_SKIN_WHITE'}
    for ob in bpy.data.objects:
        if ob.type!='MESH' or ob==bpy.data.objects['Host.body']:continue
        if not any(slot.material and slot.material.name in skin_names for slot in ob.material_slots):continue
        if ob.data.attributes.get('cast_skin_rest'):continue
        attr=ob.data.attributes.new('cast_skin_rest','FLOAT_VECTOR','POINT')
        scale=sum(ob.matrix_world.to_scale())/3
        attr.data.foreach_set('vector',[c*scale for v in ob.data.vertices for c in v.co])
    bpy.data.objects['Host.body']['castSkinCharacter']=character
    lights=apply_portrait_lighting(scene);contours=refine_face_contours(scene)
    rotation=scene.camera.matrix_world.to_quaternion()
    key=rotation@Vector((-.40,.35,1)).normalized();fill=rotation@Vector((.35,.15,1)).normalized()
    report=dict(profile=PROFILE,shaderCodeSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),character=character,selectedHex=skin_hex or None,
                surface=surface,lights=lights,contours=contours,materials=[],hiddenEarOverlays=[],samples=scene.cycles.samples,denoising=True,
                makeup=palette['name'] if character=='female' else None)
    for name in ('PEEPS_V2_WARM_SKIN','V60_EAR_SKIN','LINEART_SKIN_WHITE'):
        material=bpy.data.materials.get(name)
        if material:report['materials'].append(rebuild_skin(material,tone,key,fill,character,palette,surface,lip_hex))
    if character=='male' and native_ear:
        for ob in bpy.data.objects:
            if ob.name.startswith(('Host.V60_ear_fill','Host.V60_ear_line','Host.V60_ear_inner')):
                ob.hide_render=True;report['hiddenEarOverlays'].append(ob.name)
    if character=='female':
        # Keep the authored ear fill, but use restrained complexion-related
        # fold colour instead of black ink around the entire pale ear.
        crease=bpy.data.materials.get('Cast V13 soft ear folds') or bpy.data.materials.new('Cast V13 soft ear folds')
        crease.use_nodes=True;t=crease.node_tree;t.nodes.clear()
        em=t.nodes.new('ShaderNodeEmission');em.inputs['Color'].default_value=(*[c*.22 for c in tone],1)
        out=t.nodes.new('ShaderNodeOutputMaterial');t.links.new(em.outputs[0],out.inputs['Surface'])
        for ob in bpy.data.objects:
            if ob.name.startswith(('Host.V60_ear_line','Host.V60_ear_inner')) and ob.type=='MESH':
                for slot in ob.material_slots:slot.material=crease
            if ob.name in ('Host.V10_ear_L','Host.V10_ear_R'):ob.hide_render=True
        # Obsolete lateral face ribbons sit across the separately authored ear.
        # Restrict removal to their rest-space lateral band, beyond the eyes;
        # retain every vertex, weight and facial-control shape key.
        transparent=bpy.data.materials.get('Cast V13 lateral ink transparent') or bpy.data.materials.new('Cast V13 lateral ink transparent')
        transparent.use_nodes=True;t=transparent.node_tree;t.nodes.clear()
        tr=t.nodes.new('ShaderNodeBsdfTransparent');output=t.nodes.new('ShaderNodeOutputMaterial');t.links.new(tr.outputs[0],output.inputs['Surface'])
        rows=[]
        for name in ('Host.V59_face_art','Host.V59_face_frame'):
            art=bpy.data.objects.get(name)
            if art is None:continue
            slot=next((i for i,m in enumerate(art.data.materials) if m==transparent),None)
            if slot is None:slot=len(art.data.materials);art.data.materials.append(transparent)
            faces=[p for p in art.data.polygons if all(abs(art.data.vertices[i].co.x)>.062 and art.data.vertices[i].co.y>-.135 and art.data.vertices[i].co.z<1.590 for i in p.vertices)]
            for p in faces:p.material_index=slot
            rows.append({'object':name,'hiddenLateralInkPolygons':len(faces)})
        report['lateralInk']=rows
        report['earFolds']={'material':crease.name,'colourLinear':[c*.22 for c in tone]}
        import runpy
        report['beauty']=runpy.run_path(str(Path(__file__).with_name('cast-female-beauty.py')))['apply_female_beauty'](scene)
    return report
