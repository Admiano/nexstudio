"""Restore fitted oral anatomy and remove obsolete ear/hair interference.

Uses the original MakeHuman dental mesh and semantic oral helpers. Body
coordinates, shape keys, animation curves, and bones remain unchanged.
"""
import bpy,math,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector

PROFILE='anatomical-mouth-v13'
MODULE_SHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

def shaped_coordinates(ob):
    keys=ob.data.shape_keys
    if not keys:return np.array([v.co[:] for v in ob.data.vertices])
    basis=np.array([v.co[:] for v in keys.key_blocks[0].data]);result=basis.copy()
    for key in keys.key_blocks[1:]:
        if key.name.startswith('$') and key.value:
            result+=(np.array([v.co[:] for v in key.data])-basis)*key.value
    return result

def group_indices(ob,name):
    g=ob.vertex_groups[name].index
    return [v.index for v in ob.data.vertices if any(w.group==g and w.weight>.5 for w in v.groups)]

def oral_material(kind,character):
    name='Cast V12 '+kind;mat=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes=True;t=mat.node_tree;t.nodes.clear();out=t.nodes.new('ShaderNodeOutputMaterial');p=t.nodes.new('ShaderNodeBsdfPrincipled')
    palettes={
        'male':{'enamel':((.76,.72,.63,1),.25,.035,.70),'gingiva':((.25,.09,.095,1),.37,.14,.65),'tongue':((.30,.10,.105,1),.38,.17,.70),'oral mucosa':((.20,.07,.075,1),.48,.08,.70)},
        'female':{'enamel':((.76,.72,.63,1),.25,.035,.70),'gingiva':((.25,.065,.073,1),.37,.14,.32),'tongue':((.30,.080,.095,1),.38,.17,.32),'oral mucosa':((.095,.013,.022,1),.48,.08,.13)}
    }
    color,rough,sss,emission=palettes[character][kind]
    p.inputs['Base Color'].default_value=color;p.inputs['Roughness'].default_value=rough;p.inputs['Subsurface Weight'].default_value=sss
    p.inputs['Subsurface Radius'].default_value=(.001,.0004,.00025)
    p.inputs['Coat Weight'].default_value=.13 if kind=='enamel' else .08;p.inputs['Coat Roughness'].default_value=.25
    geo=t.nodes.new('ShaderNodeNewGeometry');ao=t.nodes.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.012;ao.samples=32
    ramp=t.nodes.new('ShaderNodeMapRange');ramp.inputs['To Min'].default_value=.30 if kind=='enamel' else (.85 if character=='male' else .20);ramp.inputs['To Max'].default_value=1;t.links.new(ao.outputs['AO'],ramp.inputs['Value'])
    tint=t.nodes.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1;tint.inputs[1].default_value=color;t.links.new(ramp.outputs[0],tint.inputs[2])
    t.links.new(tint.outputs[0],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=emission
    if kind=='enamel':
        texture=t.nodes.new('ShaderNodeTexNoise');texture.inputs['Scale'].default_value=2200;texture.inputs['Detail'].default_value=2
        bump=t.nodes.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.000008;bump.inputs['Strength'].default_value=.18;t.links.new(texture.outputs['Fac'],bump.inputs['Height']);t.links.new(bump.outputs['Normal'],p.inputs['Normal'])
    elif kind=='tongue':
        tc=t.nodes.new('ShaderNodeTexCoord');grain=t.nodes.new('ShaderNodeTexVoronoi');grain.inputs['Scale'].default_value=1600;t.links.new(tc.outputs['Object'],grain.inputs['Vector'])
        bump=t.nodes.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.000045;bump.inputs['Strength'].default_value=.32;t.links.new(grain.outputs['Distance'],bump.inputs['Height']);t.links.new(bump.outputs['Normal'],p.inputs['Normal'])
    t.links.new(p.outputs[0],out.inputs['Surface']);mat['castFacialProfile']=PROFILE;return mat

def new_bound_object(name,coordinates,faces,body,weights):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(coordinates,[],faces);mesh.update();ob=bpy.data.objects.new(name,mesh);body.users_collection[0].objects.link(ob)
    ob.parent=body.parent;ob.matrix_world=body.matrix_world.copy()
    for bone,rows in weights.items():
        group=ob.vertex_groups.new(name=bone)
        for i,w in rows:group.add([i],w,'REPLACE')
    arm=ob.modifiers.new('Original oral rig','ARMATURE');arm.object=body.parent
    smooth=ob.modifiers.new('Dental surface refinement','SUBSURF');smooth.levels=smooth.render_levels=2
    for face in mesh.polygons:face.use_smooth=True
    # Same ID as the skin so the compositor's exterior outline doesn't trace the lip line.
    ob.pass_index=body.pass_index
    ob['castFacialProfile']=PROFILE;return ob

def gingival_clearance(ob):
    """Keep the lower gum base inside the facial envelope without moving crowns."""
    keys=ob.data.shape_keys
    if keys.key_blocks.get('Gingival clearance'):return
    gum={i for p in ob.data.polygons if p.material_index==1 for i in p.vertices}
    enamel={i for p in ob.data.polygons if p.material_index==0 for i in p.vertices}
    basis=keys.key_blocks[0];neck=min(basis.data[i].co.z for i in enamel)
    key=ob.shape_key_add(name='Gingival clearance',from_mix=False);key.value=1
    for i in gum:
        point=key.data[i];depth=max(0,min(1,(neck-point.co.z)/.009))
        point.co.y+=.002+.008*depth
    ob['gingivalClearanceMaximumMetres']=.010

def articulation_keys(ob,body,character,arch):
    ob.shape_key_add(name='Basis',from_mix=False)
    recess=ob.shape_key_add(name='Closed lip seal',from_mix=False)
    for p in recess.data:p.co.y+=.012
    d=recess.driver_add('value').driver;d.expression='max(0,min(1,(.075-jaw)/.060))';v=d.variables.new();v.name='jaw';v.targets[0].id_type='KEY';v.targets[0].id=body.data.shape_keys;v.targets[0].data_path='key_blocks["!ex-jawOpen"].value'
    # The inherited facial jaw shape opens farther than its existing jaw
    # bone. Match the lower arch/tongue to that authored articulation, without
    # changing the original rig or action.
    if character in ('male','female'):
        key=ob.shape_key_add(name='Authored jaw articulation',from_mix=False)
        dz=-.004 if arch=='upper' else -.030 if arch=='lower' else -.020
        for p in key.data:p.co.z+=dz
        d=key.driver_add('value').driver;d.expression='max(0,min(1,jaw/.35))' if arch=='upper' else 'max(0,min(1,jaw))';v=d.variables.new();v.name='jaw';v.targets[0].id_type='KEY';v.targets[0].id=body.data.shape_keys;v.targets[0].data_path='key_blocks["!ex-jawOpen"].value'
    visibility=ob.driver_add('hide_render').driver;visibility.expression='jaw < .03 and upper < .065 and lower < .065 and fv < .05'
    for name,key_name in [('jaw','!ex-jawOpen'),('upper','A_upperUp'),('lower','A_lowerDown'),('fv','V3_FV')]:
        v=visibility.variables.new();v.name=name;v.targets[0].id_type='KEY';v.targets[0].id=body.data.shape_keys;v.targets[0].data_path='key_blocks["'+key_name+'"].value'
    exclude=bpy.data.collections.get('NO_HEAD_OUTLINE')
    if exclude and ob.name not in exclude.objects:exclude.objects.link(ob)

def restore_oral_anatomy(scene,character):
    body=bpy.data.objects['Host.body'];source=bpy.data.objects.get('Guest.teeth_base');guest=bpy.data.objects.get('Guest.body')
    if source is None or len(source.data.vertices)<3000 or guest is None:raise RuntimeError('CAST_ORIGINAL_DENTAL_ANATOMY_MISSING')
    for name in ['Host.teeth_base','Host.V11_mouth_interior','Host.V11_mouth_teeth','Host.V11_mouth_tongue']:
        ob=bpy.data.objects.get(name)
        if ob:ob.hide_render=True
    existing=[o for o in scene.objects if o.get('castFacialProfile') in (PROFILE,'anatomical-mouth-v12') and o.name.startswith('Cast V12 oral')]
    if existing:
        for kind in ('enamel','gingiva','tongue','oral mucosa'):
            oral_material(kind,character)
        for ob in existing:
            ob.pass_index=body.pass_index
            ob['castFacialProfile']=PROFILE
            if ob.name=='Cast V12 oral lower':gingival_clearance(ob)
        return {'reused':True,'objects':[o.name for o in existing]}
    target_co=shaped_coordinates(body);source_co=shaped_coordinates(guest);enamel=oral_material('enamel',character);gums=oral_material('gingiva',character);tongue_mat=oral_material('tongue',character);rows=[]
    # The source has 32 discrete crowns and one gingival component. Fit each
    # arch against corresponding semantic helper vertices, in body rest space.
    for bone,helper,label in [('head','helper-upper-teeth','upper'),('jaw','helper-lower-teeth','lower')]:
        ids=group_indices(body,helper);A=np.column_stack((source_co[ids],np.ones(len(ids))));transform=np.linalg.lstsq(A,target_co[ids],rcond=None)[0]
        sg=source.vertex_groups[bone].index;verts=[v.index for v in source.data.vertices if any(g.group==sg and g.weight>.5 for g in v.groups)];lookup={v:i for i,v in enumerate(verts)}
        coords=np.column_stack((np.array([source.data.vertices[i].co[:] for i in verts]),np.ones(len(verts))))@transform
        faces=[p for p in source.data.polygons if all(i in lookup for i in p.vertices)]
        ob=new_bound_object('Cast V12 oral '+label,coords.tolist(),[[lookup[i] for i in p.vertices] for p in faces],body,{bone:[(i,1) for i in range(len(verts))]})
        ob.data.materials.append(enamel);ob.data.materials.append(gums);articulation_keys(ob,body,character,label)
        for new,old in zip(ob.data.polygons,faces):new.material_index=1 if all(i<1852 for i in old.vertices) else 0
        if label=='lower':gingival_clearance(ob)
        rows.append({'object':ob.name,'vertices':len(verts),'crowns':16,'bone':bone,'fitRMSMetres':float(np.sqrt(np.mean((A@transform-target_co[ids])**2)))})
    ids=group_indices(body,'helper-tongue');lookup={v:i for i,v in enumerate(ids)};faces=[p for p in body.data.polygons if all(i in lookup for i in p.vertices)];weights={}
    rig_names=set(body.parent.data.bones.keys())
    for old,i in lookup.items():
        for g in body.data.vertices[old].groups:
            name=body.vertex_groups[g.group].name
            if name in rig_names:weights.setdefault(name,[]).append((i,g.weight))
    tongue_coords=target_co[ids].copy();tip=float(tongue_coords[:,1].min());back=float(tongue_coords[:,1].max());top=float(np.percentile(tongue_coords[:,2],65))
    for p in tongue_coords:
        frontness=max(0,min(1,(back-p[1])/(back-tip)));upper=max(0,min(1,(p[2]-(top-.004))/.004))
        p[2]-=.0006*math.exp(-(p[0]/.0012)**2)*frontness*upper
    tongue=new_bound_object('Cast V12 oral tongue',tongue_coords.tolist(),[[lookup[i] for i in p.vertices] for p in faces],body,weights);tongue.data.materials.append(tongue_mat);articulation_keys(tongue,body,character,'tongue')
    rows.append({'object':tongue.name,'vertices':len(ids),'bones':list(weights),'anatomicalSource':'Host.body helper-tongue'})
    # Interior faces are independently coloured; the outer lip and face retain
    # their selected complexion and lipstick material.
    lip_ids=group_indices(body,'lips');lip_points=target_co[lip_ids];low=lip_points[:,2].min();high=lip_points[:,2].max();width=max(abs(lip_points[:,0]));front=lip_points[:,1].min()
    marks=body.data.attributes.get('freestyle_face') or body.data.attributes.new('freestyle_face','BOOLEAN','FACE')
    mucosa=oral_material('oral mucosa',character);slot=len(body.data.materials);body.data.materials.append(mucosa);inside=0;lip_set=set(lip_ids)
    for p in body.data.polygons:
        q=target_co[list(p.vertices)].mean(axis=0)
        # The underside of the lower lip also turns away from the camera.
        # It remains exterior lip tissue, even when it falls inside this box.
        if not any(i in lip_set for i in p.vertices) and abs(q[0])<width*1.22 and low-.004<q[2]<high+.004 and front+.005<q[1]<front+.060 and p.normal.y>.15:
            p.material_index=slot;marks.data[p.index].value=True;inside+=1
    for layer in scene.view_layers:
        for lines in layer.freestyle_settings.linesets:
            if lines.name=='FACE_FINE':lines.show_render=False # exclusively the obsolete V11 mouth aperture
            if lines.name in ('HEAD_OUTLINE','HEAD_FEATURES'):
                lines.select_by_face_marks=True;lines.face_mark_negation='EXCLUSIVE';lines.face_mark_condition='ONE'
    # Remove the original painted lip ribbon from both sexes, using each
    # assembled mouth's own rest coordinates rather than a female-only box.
    transparent=bpy.data.materials.get('CAST_LIP_ART_TRANSPARENT') or bpy.data.materials.new('CAST_LIP_ART_TRANSPARENT');transparent.use_nodes=True;t=transparent.node_tree;t.nodes.clear();tr=t.nodes.new('ShaderNodeBsdfTransparent');out=t.nodes.new('ShaderNodeOutputMaterial');t.links.new(tr.outputs[0],out.inputs[0]);ink=[]
    # Facial artwork already includes the fitted $ morphs in its cage.
    basis=np.array([v.co[:] for v in body.data.vertices]);lip_basis=basis[lip_ids];lo=lip_basis[:,2].min()-.003;hi=lip_basis[:,2].max()+.003;w=max(abs(lip_basis[:,0]))+.004
    for name in ['Host.V59_face_art','Host.V59_face_frame']:
        art=bpy.data.objects.get(name)
        if not art:continue
        faces=[p for p in art.data.polygons if all(abs(art.data.vertices[i].co.x)<w and art.data.vertices[i].co.y<-.09 and lo<art.data.vertices[i].co.z<hi for i in p.vertices)]
        slot=next((i for i,m in enumerate(art.data.materials) if m==transparent),None)
        if slot is None:slot=len(art.data.materials);art.data.materials.append(transparent)
        for p in faces:p.material_index=slot
        ink.append({'object':name,'lipPolygons':len(faces)})
    return {'objects':rows,'teeth':32,'tongue':True,'interiorPolygons':inside,'lipInkRemoved':ink,'legacyMouthStrokeDisabled':True,'lowerGingivalClearanceMaximumMetres':.010,'closedLipVisibilityGuard':{'jawBelow':.03,'upperBelow':.065,'lowerBelow':.065,'fvBelow':.05},'originalBodyCoordinatesUnchanged':True}

def refine_ear_and_hair(scene,character):
    hidden=[]
    if character=='male':
        for name in ['Host.V10_ear_L','Host.V10_ear_R']:
            ob=bpy.data.objects.get(name)
            if ob:ob.hide_render=True;hidden.append(name)
    body=bpy.data.objects['Host.body'];coords=shaped_coordinates(body);earids=group_indices(body,'ears');ears=coords[earids];low=ears[:,2].min();cut=float(ears[:,2].mean())-.003
    correction=None
    if character=='male' and not body.data.shape_keys.key_blocks.get('Cast V12 balanced ears'):
        key=body.shape_key_add(name='Cast V12 balanced ears',from_mix=False);key.value=1
        for side in [-1,1]:
            points=ears[ears[:,0]*side>0];cz=float(points[:,2].mean());root=float(min(abs(p[0]) for p in points));span=float(max(abs(p[0]) for p in points))-root
            for i in earids:
                if coords[i,0]*side<=0:continue
                p=Vector(coords[i]);fall=max(0,min(1,(abs(p.x)-root)/(span*.55)));fall=fall*fall*(3-2*fall)
                key.data[i].co.x-=side*(abs(p.x)-root)*.12*fall;key.data[i].co.z-=(p.z-cz)*.07*fall
        correction={'name':key.name,'maximumFlareReduction':.12,'maximumHeightReduction':.07,'symmetric':True}
    elif character=='male':correction={'name':'Cast V12 balanced ears','reused':True}
    source=bpy.data.objects.get('Host.hair_elvs_maxwell_hair');masked=0;trimmed=0
    if character=='male' and source and not source.hide_render:
        # Only the isolated lower temple extensions of the quiff. Hair behind
        # the head and intentional long/swept/braided styles remain intact.
        def unwanted(p):return abs(p.x)>.042 and p.y<.008 and p.z<cut
        group=source.vertex_groups.get('Cast clean temple ends') or source.vertex_groups.new(name='Cast clean temple ends')
        group.add(list(range(len(source.data.vertices))),1,'REPLACE')
        for v in source.data.vertices:
            if unwanted(v.co):group.remove([v.index]);masked+=1
        mod=source.modifiers.get('Cast clean temple ends') or source.modifiers.new('Cast clean temple ends','MASK');mod.vertex_group=group.name
        with bpy.context.temp_override(object=source,active_object=source):bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0)
        for ob in scene.objects:
            if ob.type!='CURVES' or ob.get('castGroomProfile')!='fibre-groom-v11':continue
            radii=ob.data.attributes.get('radius')
            for c in ob.data.curves:
                pts=[ob.data.position_data[i].vector for i in range(c.first_point_index,c.first_point_index+c.points_length)]
                if any(unwanted(source.matrix_world.inverted()@(ob.matrix_world@p)) for p in pts):
                    for i in range(c.first_point_index,c.first_point_index+c.points_length):radii.data[i].value=0
                    trimmed+=1
    return {'hiddenLegacyEarInk':hidden,'quiffCarrierVerticesMasked':masked,'quiffStrayCurvesRemoved':trimmed,'templeCutRestZ':float(cut),'earCorrection':correction,'originalEarCagePreserved':True}

def apply_facial_refinement(scene,character):
    return {'profile':PROFILE,'codeSHA256':MODULE_SHA256,'mouth':restore_oral_anatomy(scene,character),'ear':refine_ear_and_hair(scene,character)}
