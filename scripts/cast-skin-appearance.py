"""Rig-bound skin microrelief, anatomical surface detail, and six makeup palettes.

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

PROFILE = 'anatomical-skin-texture-v3'
# Sheer blush, satin eye wash, natural upper/lower lips. Authored in sRGB.
MAKEUP = {
    'F7E1D3': ('fair', 'D78E91', 'A9827A', 'B6757F', 'CF9196', .33, .34),
    'F1D7C8': ('light', 'C9797E', '987261', 'B76C76', 'C78086', .35, .36),
    'E0B48F': ('medium', 'B76D61', '966B55', 'AC6461', 'C47F72', .37, .38),
    'C99A6E': ('tan', 'A65F49', '8D5E44', '9A5450', 'B97065', .40, .40),
    '9E6B4A': ('brown', 'A65F5B', '865A4D', '82434C', 'AD6972', .45, .42),
    '6A4431': ('deep', 'AE626A', '8B5A59', '70404F', '9E6574', .48, .44),
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
    main=material.name=='PEEPS_V2_WARM_SKIN'
    lip_colors=None
    if main:
        if character=='female':
            if lip_hex:
                selected=linear_rgb(lip_hex)
                lip_colors=(tuple(c*.78 for c in selected),selected)
            else:lip_colors=palette['lips']
        else:
            lum=sum(c*w for c,w in zip(tone,(.2126,.7152,.0722)))
            warmth=max(0,min(1,(lum-.45)/.35))
            lip_colors=[tuple(c*(a+(b-a)*warmth) for c,a,b in zip(tone,lo,hi))
                        for lo,hi in (((.45,.34,.50),(.58,.32,.34)),((.55,.42,.60),(.70,.43,.44)))]
    tree=material.node_tree;tree.nodes.clear();s=SurfaceNodes(tree)
    geo=s.node('ShaderNodeNewGeometry','Live skin surface')
    base=s.node('ShaderNodeRGB','Selected complexion');base.outputs[0].default_value=(*tone,1)
    color=base.outputs[0];normal=geo.outputs['Normal'];lipmask=0
    if main:
        rest=s.attr('cast_skin_rest').outputs['Vector']
        regions=s.split(s.attr('cast_skin_regions').outputs['Vector'],'Face oil and nail regions')
        makeup=s.split(s.attr('cast_skin_makeup').outputs['Vector'],'Sheer makeup regions')
        joints=s.split(s.attr('cast_skin_joint').outputs['Vector'],'Joint distance and hand side')
        palm=s.split(s.attr('cast_skin_palm').outputs['Vector'],'Palm chart')
        xyz=s.split(rest,'Rest metres')
        lip=s.attr('lipmask')
        boundary=s.node('ShaderNodeMapRange','Original lip boundary');boundary.interpolation_type='SMOOTHSTEP'
        boundary.inputs['From Min'].default_value=-.040;boundary.inputs['From Max'].default_value=.040
        s.wire(lip.outputs['Fac'],boundary.inputs['Value']);lipmask=boundary.outputs['Result']
        not_lip=s.math('SUBTRACT','Skin outside lip',1,lipmask)
        noise=s.node('ShaderNodeTexNoise','Fine irregular skin relief');noise.inputs['Scale'].default_value=1750
        noise.inputs['Detail'].default_value=2;noise.inputs['Roughness'].default_value=.62;s.wire(rest,noise.inputs['Vector'])
        pores=s.node('ShaderNodeTexVoronoi','Irregular pore spacing');pores.feature='F1';pores.distance='EUCLIDEAN'
        pores.inputs['Scale'].default_value=2350;s.wire(rest,pores.inputs['Vector'])
        porepit=s.gaussian('Recessed pores',pores.outputs['Distance'],.22)
        poreweight=s.math('ADD','Regional pore relief',.65,s.math('MULTIPLY','Face pore density',regions['X'],.50))
        poreweight=s.math('MULTIPLY','No pores on nails',poreweight,s.math('SUBTRACT','Nail exclusion',1,regions['Z']))
        micro=s.math('SUBTRACT','Skin grain and pits',s.math('MULTIPLY','Fine relief metres',noise.outputs['Fac'],.000065),s.math('MULTIPLY','Pore depth metres',porepit,.000120))
        micro=s.math('MULTIPLY','Regional microrelief',micro,poreweight)
        micro=s.math('MULTIPLY','Pores outside lips',micro,not_lip)
        lip_coords=s.node('ShaderNodeVectorMath','Lip striation scale');lip_coords.operation='MULTIPLY'
        s.wire(rest,lip_coords.inputs[0]);lip_coords.inputs[1].default_value=(1800,350,500)
        lip_grain=s.node('ShaderNodeTexNoise','Fine vertical lip striations');lip_grain.inputs['Scale'].default_value=1
        lip_grain.inputs['Detail'].default_value=3;lip_grain.inputs['Roughness'].default_value=.7;s.wire(lip_coords.outputs['Vector'],lip_grain.inputs['Vector'])
        micro=s.math('ADD','Skin and lip microrelief',micro,s.math('MULTIPLY','Lip relief metres',s.math('MULTIPLY','Lip relief mask',lip_grain.outputs['Fac'],lipmask),.000022))
        crease=s.math('MULTIPLY','Joint fold mask',s.gaussian('Fine knuckle folds',joints['X'],.00085),joints['Y'])
        knuckle=s.math('MULTIPLY','Knuckle warmth mask',s.gaussian('Knuckle transition',joints['X'],.0045),joints['Y'])
        # Two curved palmar flexion folds, measured in the local hand chart.
        curve=s.math('MULTIPLY','Palm fold curve',s.math('MULTIPLY','Palm transverse squared',palm['X'],palm['X']),.15)
        fold1=s.gaussian('Distal palm crease',s.math('SUBTRACT','Distal palm coordinate',palm['Y'],s.math('ADD','Distal palm arc',curve,.70)),.021)
        fold2=s.gaussian('Proximal palm crease',s.math('SUBTRACT','Proximal palm coordinate',palm['Y'],s.math('ADD','Proximal palm arc',curve,.43)),.020)
        palm_bounds=s.math('MULTIPLY','Palm domain',s.gaussian('Palm width',s.math('SUBTRACT','Palm centre',palm['X'],.5),.58),palm['Z'])
        palm_fold=s.math('MULTIPLY','Palm crease mask',s.math('MAXIMUM','Palm folds',fold1,fold2),palm_bounds)
        folds=s.math('MAXIMUM','Hand crease mask',crease,palm_fold)
        height=s.math('ADD','Skin micro and anatomy relief',micro,s.attr('cast_skin_anatomy').outputs['Fac'])
        height=s.math('SUBTRACT','Hand crease depth',height,s.math('MULTIPLY','Hand fold metres',folds,.00011))
        nz=surface['neckRestZ']
        neck_domain=s.gaussian('Neck front domain',s.math('SUBTRACT','Neck vertical domain',xyz['Z'],nz+.012),.060)
        neck_domain=s.math('MULTIPLY','Neck lateral domain',neck_domain,s.gaussian('Neck width',xyz['X'],.065))
        nx2=s.math('MULTIPLY','Neck horizontal squared',xyz['X'],xyz['X'])
        arc=s.math('MULTIPLY','Neck fold curvature',nx2,1.4)
        nf=[]
        for offset in (-.001,.019):
            value=s.math('SUBTRACT','Neck fold coordinate',xyz['Z'],s.math('ADD','Natural neck arc',arc,nz+offset))
            nf.append(s.gaussian('Fine neck flexion fold',value,.00070))
        neck_fold=s.math('MULTIPLY','Neck fold mask',s.math('MAXIMUM','Neck folds',*nf),neck_domain)
        # Restrict anterior folds to the front side of the neck.
        front=s.attr('cast_skin_anterior').outputs['Fac']
        neck_fold=s.math('MULTIPLY','Anterior neck folds',neck_fold,front)
        height=s.math('SUBTRACT','Neck fold depth',height,s.math('MULTIPLY','Neck fold metres',neck_fold,.000065))
        bump=s.node('ShaderNodeBump','Micrometre skin and anatomical relief');bump.inputs['Strength'].default_value=.85;bump.inputs['Distance'].default_value=1
        s.wire(height,bump.inputs['Height']);s.wire(normal,bump.inputs['Normal']);normal=bump.outputs['Normal']
        pigment=s.node('ShaderNodeTexNoise','Subsurface pigment variation');pigment.inputs['Scale'].default_value=210
        pigment.inputs['Detail'].default_value=2;pigment.inputs['Roughness'].default_value=.65;s.wire(rest,pigment.inputs['Vector'])
        variation=s.math('ADD','Bounded pigment modulation',.94,s.math('MULTIPLY','Pigment variation range',pigment.outputs['Fac'],.12))
        color=s.mix('Living skin colour variation',1,color,variation,'MULTIPLY')
        mottling=s.node('ShaderNodeTexNoise','Natural broad pigment variation');mottling.inputs['Scale'].default_value=68
        mottling.inputs['Detail'].default_value=2;s.wire(rest,mottling.inputs['Vector'])
        broad=s.math('ADD','Broad pigment bounds',.96,s.math('MULTIPLY','Broad pigment range',mottling.outputs['Fac'],.08))
        color=s.mix('Multiscale skin pigment',1,color,broad,'MULTIPLY')
        pore_color=s.math('SUBTRACT','Pore melanin modulation',1,s.math('MULTIPLY','Pore pigment depth',s.math('MULTIPLY','Pore pigment mask',porepit,not_lip),.22))
        color=s.mix('Subtle pore pigment',1,color,pore_color,'MULTIPLY')
        warmth=tuple(c*k for c,k in zip(tone,(1.07,.94,.93)))
        color=s.mix('Natural joint warmth',s.math('MULTIPLY','Joint warmth weight',knuckle,.28),color,(*warmth,1))
        lum=sum(c*w for c,w in zip(tone,(.2126,.7152,.0722)))
        palm_tone=tuple(c*.85+d*.15 for c,d in zip(tone,linear_rgb('D6AA92')))
        color=s.mix('Natural palmar pigmentation',s.math('MULTIPLY','Palm pigmentation weight',palm['Z'],.18+(1-lum)*.40),color,(*palm_tone,1))
        nails=tuple(c*.35+d*.65 for c,d in zip(tone,linear_rgb('D4ABA2' if lum>.25 else 'B58376')))
        color=s.mix('Natural translucent nail beds',regions['Z'],color,(*nails,1))
        free_edge=s.math('MULTIPLY','Nail distal boundary',s.gaussian('Fine natural nail edge',s.attr('cast_skin_nail').outputs['Fac'],.00085),regions['Z'])
        color=s.mix('Translucent nail free edge',s.math('MULTIPLY','Nail edge opacity',free_edge,.38),color,(*linear_rgb('E4D4CB'),1))
        cavity=s.math('MAXIMUM','Fine fold pigmentation',folds,neck_fold)
        color=s.mix('Soft crease colour',s.math('MULTIPLY','Fold pigment strength',cavity,.065),color,(*[c*.68 for c in tone],1))
        if character=='female':
            color=s.mix('Complexion matched sheer blush',s.math('MULTIPLY','Sheer blush coverage',makeup['X'],palette['blushWeight']),color,(*palette['blush'],1))
            color=s.mix('Complexion matched satin eye wash',s.math('MULTIPLY','Satin eye coverage',makeup['Y'],palette['eyeWeight']),color,(*palette['eye'],1))
        lips=s.mix('Complexion matched lip palette',s.attr('liplo').outputs['Fac'],(*lip_colors[0],1),(*lip_colors[1],1))
        lip_variation=s.math('ADD','Satin lip pigment bounds',.90,s.math('MULTIPLY','Lip fine pigment range',lip_grain.outputs['Fac'],.17))
        lips=s.mix('Lip pigment follows natural striations',1,lips,lip_variation,'MULTIPLY')
        color=s.mix('Original anatomical lip boundary',lipmask,color,lips)
    else:
        rest=s.attr('cast_skin_rest').outputs['Vector']
        grain=s.node('ShaderNodeTexNoise','Exposed skin microrelief');grain.inputs['Scale'].default_value=1750
        grain.inputs['Detail'].default_value=2;s.wire(rest,grain.inputs['Vector'])
        pores=s.node('ShaderNodeTexVoronoi','Exposed skin pores');pores.inputs['Scale'].default_value=2350;s.wire(rest,pores.inputs['Vector'])
        micro=s.math('SUBTRACT','Exposed skin grain and pits',s.math('MULTIPLY','Exposed grain metres',grain.outputs['Fac'],.000035),s.math('MULTIPLY','Exposed pore metres',s.gaussian('Exposed pore pits',pores.outputs['Distance'],.22),.000055))
        bump=s.node('ShaderNodeBump','Exposed skin relief');bump.inputs['Strength'].default_value=.65;bump.inputs['Distance'].default_value=1
        s.wire(micro,bump.inputs['Height']);s.wire(normal,bump.inputs['Normal']);normal=bump.outputs['Normal']
    def diffuse(direction,name):
        dot=s.node('ShaderNodeVectorMath',name+' direction');dot.operation='DOT_PRODUCT'
        s.wire(normal,dot.inputs[0]);dot.inputs[1].default_value=direction
        ramp=s.node('ShaderNodeMapRange',name+' soft falloff');ramp.interpolation_type='SMOOTHSTEP'
        ramp.inputs['From Min'].default_value=-.30;ramp.inputs['From Max'].default_value=.95
        s.wire(dot.outputs['Value'],ramp.inputs['Value']);return ramp.outputs['Result']
    k=diffuse(key,'Broad key');f=diffuse(fill,'Soft fill')
    light=s.math('ADD','Ambient floor',.60,s.math('ADD','Key and fill',s.math('MULTIPLY','Key weight',k,.37),s.math('MULTIPLY','Fill weight',f,.11)))
    ao=s.node('ShaderNodeAmbientOcclusion','Short live contact');ao.only_local=True;ao.samples=32;ao.inputs['Distance'].default_value=.018
    contact=s.math('SUBTRACT','Bounded live contact',1,s.math('MULTIPLY','Contact weight',s.math('SUBTRACT','Contact cavity',1,ao.outputs['AO']),.20))
    color=s.mix('Complexion times surface light',1,color,s.math('MULTIPLY','Single shading factor',light,contact),'MULTIPLY')
    if main:
        # Soft oil response uses the perturbed normal and actual incoming view.
        half=s.node('ShaderNodeVectorMath','Skin sheen half vector');half.operation='ADD'
        half.inputs[0].default_value=key;s.wire(geo.outputs['Incoming'],half.inputs[1])
        norm=s.node('ShaderNodeVectorMath','Normalized sheen direction');norm.operation='NORMALIZE';s.wire(half.outputs['Vector'],norm.inputs[0])
        dot=s.node('ShaderNodeVectorMath','Skin satin response');dot.operation='DOT_PRODUCT';s.wire(normal,dot.inputs[0]);s.wire(norm.outputs[0],dot.inputs[1])
        lobe=s.math('POWER','Broad rough skin lobe',s.math('MAXIMUM','Visible skin lobe',dot.outputs['Value'],0),22)
        oil=s.math('ADD','Regional oil response',.010,s.math('MULTIPLY','T zone sheen',regions['Y'],.018))
        oil=s.math('ADD','Nail satin response',oil,s.math('MULTIPLY','Nail sheen',regions['Z'],.018))
        lip_oil=s.math('ADD','Upper and lower lip finish',.035,s.math('MULTIPLY','Lower lip satin',s.attr('liplo').outputs['Fac'],.095))
        oil=s.math('ADD','Lip satin response',oil,s.math('MULTIPLY','Lip sheen',lipmask,lip_oil))
        if character=='female':
            oil=s.math('ADD','Satin cheek illumination',oil,s.math('MULTIPLY','Sheer cheek highlight',makeup['Z'],.055))
        sheen=s.math('MULTIPLY','Bounded skin sheen',lobe,oil)
        tint=tuple(.65+.35*c for c in tone)
        color=s.mix('Subtle dielectric skin sheen',sheen,color,(*tint,1))
    emission=s.node('ShaderNodeEmission','Skin output');s.wire(color,emission.inputs['Color'])
    output=s.node('ShaderNodeOutputMaterial','Material Output');s.wire(emission.outputs[0],output.inputs['Surface'])
    material['castSkinProfile']=PROFILE;material['castSkinBase']=tone
    if lip_colors:material['castLipColors']=[c for col in lip_colors for c in col]
    return dict(material=material.name,nodes=len(tree.nodes),baseLinear=list(tone),
                contactDistance=.018,contactWeight=.20,fixedSkinColourMasks=False,
                pores=True,poreSpacingMetres=1/2350,
                makeupPalette=palette['name'] if main and character=='female' else None,
                explicitLipOverride=bool(lip_hex) if main and character=='female' else False)


def apply_skin_appearance(scene,character,skin_hex='',native_ear=True,lip_hex=None):
    if character not in ('female','male'):raise ValueError('CAST_INVALID_CHARACTER')
    scene.cycles.samples=max(scene.cycles.samples,64)
    # Emission-based portrait materials do not provide a useful denoising
    # albedo guide: filtering them erases genuine pores and fine creases.
    scene.cycles.use_denoising=False
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
    rotation=scene.camera.matrix_world.to_quaternion()
    key=rotation@Vector((-.48,.45,.75)).normalized();fill=rotation@Vector((.65,.30,.70)).normalized()
    report=dict(profile=PROFILE,shaderCodeSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),character=character,selectedHex=skin_hex or None,
                surface=surface,materials=[],hiddenEarOverlays=[],samples=scene.cycles.samples,denoising=False,
                makeup=palette['name'] if character=='female' else None)
    for name in ('PEEPS_V2_WARM_SKIN','V60_EAR_SKIN','LINEART_SKIN_WHITE'):
        material=bpy.data.materials.get(name)
        if material:report['materials'].append(rebuild_skin(material,tone,key,fill,character,palette,surface,lip_hex))
    if character=='male' and native_ear:
        for ob in bpy.data.objects:
            if ob.name.startswith(('Host.V60_ear_fill','Host.V60_ear_line','Host.V60_ear_inner')):
                ob.hide_render=True;report['hiddenEarOverlays'].append(ob.name)
    if character=='female':
        import runpy
        report['beauty']=runpy.run_path(str(Path(__file__).with_name('cast-female-beauty.py')))['apply_female_beauty'](scene)
    return report
