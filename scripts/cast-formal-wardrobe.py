"""Rig-preserving formal wardrobe import for the SceneBam production cast.

This runs inside the regular cast-render-assembled.py pipeline, AFTER original
character assembly and fitting. It fails closed on missing garments, incompatible
rigs, or non-separable suit/tie materials. No concept art is substituted.
"""
import bpy, os, re
from pathlib import Path
from mathutils import Vector

LOOKS={
 'female-double-breasted','female-statement','male-jacket-tie',
 'male-double-breasted','male-navy-classic','male-dinner-jacket'
}

def _linear(hexstr):
    assert re.fullmatch(r'[A-Fa-f0-9]{6}',hexstr)
    raw=[int(hexstr[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4 for v in raw)

def _role(material):
    # The independent material roles must be recorded on the SOURCE garment.
    # Name inspection is for actionable errors only, never a guessed recolor.
    return (material.get('scenebamColorRole') or '').lower()

def _recolor(material,colour,role):
    # Make garment material single-user; never mutate the existing host.
    mat=material.copy()
    mat.name='SCENEBAM_FORMAL_'+role.upper()+'_'+colour
    mat.diffuse_color=(*_linear(colour),1)
    mat.use_nodes=True
    nodes=mat.node_tree.nodes
    material_nodes=[n for n in nodes if n.type in ('BSDF_PRINCIPLED','EMISSION')]
    if not material_nodes:
        raise RuntimeError('FORMAL_MATERIAL_SHADER_UNSUPPORTED:'+material.name)
    # For independent wardrobe coloration, the role-owned node color is
    # overridden, retaining the other graph nodes, geometry and silhouette.
    for node in material_nodes:
        field='Base Color' if node.type=='BSDF_PRINCIPLED' else 'Color'
        if not node.inputs.get(field):
            continue
        input_socket=node.inputs[field]
        # Texture-driven materials require authoring an explicit color-mask
        # palette interface rather than silently ignoring the user's color.
        if input_socket.is_linked:
            raise RuntimeError('FORMAL_MATERIAL_TINT_INPUT_LINKED:'+material.name)
        input_socket.default_value=(*_linear(colour),1)
    mat['scenebamColorRole']=role
    mat['scenebamHex']=colour
    return mat

def apply_formal_wardrobe(scene,character,look,suit_hex,tie_hex):
    if not look:
        return {'enabled':False}
    if look not in LOOKS or not look.startswith(character+'-'):
        raise RuntimeError('FORMAL_LOOK_INVALID')
    root=Path(os.environ.get('SCENEBAM_FORMAL_ASSET_ROOT') or
              Path(os.environ.get('CAST_PROJECT_ROOT',Path(__file__).resolve().parents[1]))/
              'engine_sources/makehuman-lineart/out/scenebam-formal')
    source=root/(look+'.blend')
    if not source.is_file():
        raise RuntimeError('FORMAL_PRODUCTION_ASSET_NOT_INSTALLED:'+str(source))
    rig=bpy.data.objects.get('Host.rig')
    body=bpy.data.objects.get('Host.body')
    if rig is None or body is None or len(rig.data.bones)!=163:
        raise RuntimeError('FORMAL_LIVE_BASE_RIG_INVALID')
    name='SCENEBAM_FORMAL_'+look.upper().replace('-','_')
    with bpy.data.libraries.load(str(source),link=False) as (available,loaded):
        if name not in available.objects or 'Host.rig' not in available.objects:
            raise RuntimeError('FORMAL_SOURCE_MISSING:'+name)
        loaded.objects=[name,'Host.rig']
    garment=next((ob for ob in loaded.objects if ob and ob.type=='MESH'),None)
    donor_rig=next((ob for ob in loaded.objects if ob and ob.type=='ARMATURE'),None)
    if not garment or not donor_rig:
        raise RuntimeError('FORMAL_MESH_OR_RIG_MISSING')
    if len(donor_rig.data.bones)!=163 or any(b.name not in donor_rig.data.bones for b in rig.data.bones):
        raise RuntimeError('FORMAL_BONE_LAYOUT_MISMATCH')
    drift=max(abs(a-b) for b in rig.data.bones for rowA,rowB in zip(b.matrix_local,donor_rig.data.bones[b.name].matrix_local) for a,b in zip(rowA,rowB))
    if drift>=1e-4:
        raise RuntimeError('FORMAL_REST_POSE_MISMATCH:'+str(drift))
    if len(garment.vertex_groups)<20 or len(garment.data.vertices)<1000 or not any(m.type=='ARMATURE' for m in garment.modifiers):
        raise RuntimeError('FORMAL_GARMENT_NOT_RIGGED')
    roles={}
    for index,material in enumerate(garment.data.materials):
        if material is None:
            continue
        role=_role(material)
        if role in ('suit','tie'):
            roles.setdefault(role,[]).append(index)
    # Without explicit distinct roles, the UI must not advertise an
    # independent tie picker: a whole-mesh recolor would be misleading.
    if not roles.get('suit') or not roles.get('tie') or set(roles['suit']) & set(roles['tie']):
        raise RuntimeError('FORMAL_SUIT_TIE_ROLE_CERTIFICATION_MISSING:'+name)
    garment.data=garment.data.copy()
    for role,colour in (('suit',suit_hex),('tie',tie_hex)):
        for index in roles[role]:
            garment.data.materials[index]=_recolor(garment.data.materials[index],colour,role)
    source_matrix=garment.matrix_world.copy()
    for modifier in garment.modifiers:
        if modifier.type=='ARMATURE':
            modifier.object=rig
    garment.parent=rig
    garment.matrix_world=source_matrix
    scene.collection.objects.link(garment)
    garment.name=name
    garment['scenebamFormalLook']=look
    garment['scenebamIndependentSuitTie']=True
    if donor_rig.users==0:
        bpy.data.objects.remove(donor_rig,do_unlink=True)
    # Hide (do not destroy) the casual default garment and its derived ink /
    # fit proxies. The production body, bones, hair and skin stay untouched.
    originals=['Host.mindfront_f_dress_11'] if character=='female' else [
        'Host.elvs_male_shirt_untucked_bd1','Host.mindfront_male_trousers_2']
    hidden=[]
    for ob in scene.objects:
        if ob.type!='MESH' or ob==garment:
            continue
        refs=[ob.name,ob.get('castFitSource') or '',ob.get('castGarmentSource') or '',
              ob.get('castGarmentProxySource') or '']
        if any(any(str(ref)==original or str(ref).startswith(original+'.') for original in originals) for ref in refs):
            ob.hide_render=True
            hidden.append(ob.name)
        if character=='female' and ob.name.startswith(('Host.V64_dress_lines','Host.V26_garment')):
            ob.hide_render=True
            hidden.append(ob.name)
    marks=bpy.data.collections.get('V26_GARMENT_MARKS')
    if marks:
        for ob in marks.objects:
            ob.hide_render=True
    scene.frame_set(scene.frame_current)
    bpy.context.view_layer.update()
    return {'enabled':True,'look':look,'suitHex':suit_hex,'tieHex':tie_hex,
            'materialRoles':{k:len(v) for k,v in roles.items()},
            'sourceScene':str(source),'rigRestMaxError':drift,
            'hiddenOriginalGarments':hidden,'vertexCount':len(garment.data.vertices)}
