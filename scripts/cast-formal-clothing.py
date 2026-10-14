"""Opt-in SceneBam production formalwear from the six real Blender donor refits.

Never modify the canonical character scene, silently substitute an older
performer, or accept a missing garment/tie mapping. Only use fitted, rigged
source garments from the 2026-10-13 production assembly proof artifact.

The source .blend files must be installed in CAST_FORMAL_SCENE_DIR under:
  <variant>/<variant>-production-assembled.blend
"""
from __future__ import annotations
import os
import math
from pathlib import Path
import bpy
from mathutils import Vector

VARIANTS = {
    'female-double-breasted':'female',
    'female-statement':'female',
    'male-jacket-tie':'male',
    'male-double-breasted':'male',
    'male-navy-classic':'male',
    'male-dinner-jacket':'male',
}
SUIT_PREFIX = 'SCENEBAM_FORMAL_'
def _hex(value):
    if len(value)!=6 or any(x not in '0123456789abcdefABCDEF' for x in value):
        raise RuntimeError('CAST_FORMAL_HEX_INVALID')
    return tuple(int(value[i:i+2],16)/255 for i in (0,2,4))+(1,)

def _connected_islands(mesh):
    parent=list(range(len(mesh.vertices)))
    def find(k):
        while parent[k]!=k:
            parent[k]=parent[parent[k]]
            k=parent[k]
        return k
    for poly in mesh.polygons:
        verts=poly.vertices
        for v in verts[1:]:
            a,b=find(verts[0]),find(v)
            if a!=b: parent[b]=a
    islands={}
    for poly in mesh.polygons:
        key=find(poly.vertices[0])
        islands.setdefault(key,[]).append(poly.index)
    return list(islands.values())

def _tint_material(source,name,color):
    mat=source.copy()
    mat.name=name
    if not mat.use_nodes:
        raise RuntimeError('CAST_FORMAL_UV_MATERIAL_REQUIRED')
    nodes,links=mat.node_tree.nodes,mat.node_tree.links
    emission=next((n for n in nodes if n.type=='EMISSION'),None)
    if emission is None or not emission.inputs['Color'].is_linked:
        raise RuntimeError('CAST_FORMAL_UV_EMISSION_MISSING')
    upstream=emission.inputs['Color'].links[0].from_socket
    mix=nodes.new('ShaderNodeMixRGB')
    mix.name='SceneBam fabric tint / original donor texture preserved'
    mix.blend_type='COLOR'
    mix.inputs['Fac'].default_value=.97
    mix.inputs['Color2'].default_value=color
    links.new(upstream,mix.inputs['Color1'])
    links.new(mix.outputs['Color'],emission.inputs['Color'])
    return mat

def _classify_garment(mesh,world,tie_expected):
    # Disconnected donor OBJ islands retain separate topology for tie/lapels.
    # Reject an uncertain tie rather than recolor a shirt or fake a texture.
    islands=_connected_islands(mesh)
    # The approved cast may sit at a nonzero x offset; derive the donor's own
    # midline from its mesh rather than assuming the camera's -.42 coordinate.
    all_x=[(world@v.co).x for v in mesh.vertices]
    midline=(min(all_x)+max(all_x))*.5
    scores=[]
    for faces in islands:
        inds=set(v for i in faces for v in mesh.polygons[i].vertices)
        pos=[world@mesh.vertices[i].co for i in inds]
        xs=[p.x for p in pos];ys=[p.y for p in pos];zs=[p.z for p in pos]
        xlo,xhi=min(xs),max(xs);zlo,zhi=min(zs),max(zs)
        cx=(xlo+xhi)*.5;cz=(zlo+zhi)*.5
        # Frontal mid-chest, narrow, elongated accessory instead of a jacket.
        w=xhi-xlo;h=zhi-zlo
        if 1.16<cz<1.66 and abs(cx-midline)<.12 and .015<w<.10 and .075<h<.45 and len(faces)>=70:
            scores.append((len(faces),w,h,cx,cz,faces))
    # Tie connected-component candidates are ordered by narrowness then area.
    tie_faces=[]
    if tie_expected and scores:
        scores.sort(key=lambda x:(x[1]/max(x[2],.001),x[0]))
        tie_faces=scores[0][-1]
    if tie_expected and not tie_faces:
        # Diagnostic only: fail closed and report actual authored geometry ranges.
        table=[]
        for faces in islands:
            ids=set(v for i in faces for v in mesh.polygons[i].vertices)
            if not ids:continue
            pts=[world@mesh.vertices[i].co for i in ids]
            xmin,xmax=min(p.x for p in pts),max(p.x for p in pts)
            ymin,ymax=min(p.y for p in pts),max(p.y for p in pts)
            zmin,zmax=min(p.z for p in pts),max(p.z for p in pts)
            table.append(dict(faces=len(faces),x=[round(xmin,3),round(xmax,3)],
                y=[round(ymin,3),round(ymax,3)],
                z=[round(zmin,3),round(zmax,3)]))
        table.sort(key=lambda x:x['faces'],reverse=True)
        print('FORMAL_TIE_ISLAND_DIAGNOSTIC',variant if 'variant' in globals() else '?',table[:30],flush=True)
        raise RuntimeError('CAST_FORMAL_TIE_TOPOLOGY_NOT_IDENTIFIED')
    tie_ids=set(tie_faces)
    # Do not recolor the original designer's white shirt, collar, pockets and
    # other small trim meshes. Keep their genuine UV image material untouched.
    suit_ids=set()
    garment_region=[]
    for faces in islands:
        if any(p in tie_ids for p in faces):continue
        verts=set(v for i in faces for v in mesh.polygons[i].vertices)
        points=[world@mesh.vertices[i].co for i in verts]
        width=max(p.x for p in points)-min(p.x for p in points)
        low=min(p.z for p in points)
        # Actual fabric panels are large, full-width jacket or lower garment.
        if len(faces)>=350 and (width>.22 or low<1.16):
            suit_ids.update(faces)
            garment_region.append(len(faces))
    trim_ids=set(range(len(mesh.polygons)))-suit_ids-tie_ids
    if len(suit_ids)<300 or (tie_expected and len(tie_ids)<70):
        raise RuntimeError('CAST_FORMAL_INSUFFICIENT_COLOR_REGIONS')
    return suit_ids,tie_ids,trim_ids,len(islands)

def install_formal(scene,variant,suit_hex,tie_hex=''):
    if not variant:return {'enabled':False}
    character=os.environ.get('CAST_CHARACTER','')
    if VARIANTS.get(variant)!=character:
        raise RuntimeError('CAST_FORMAL_GENDER_VARIANT_MISMATCH')
    target=_hex(suit_hex)
    tie_target=_hex(tie_hex) if tie_hex else None
    if character=='male' and not tie_target:
        raise RuntimeError('CAST_FORMAL_TIE_COLOR_REQUIRED')
    if character=='female' and tie_target:
        raise RuntimeError('CAST_FORMAL_TIE_COLOR_NOT_APPLICABLE')
    root=Path(os.environ.get('CAST_FORMAL_SCENE_DIR','engine_sources/makehuman-lineart/out/cast-formals')).resolve()
    source=root/variant/(variant+'-production-assembled.blend')
    if not source.is_file() or source.stat().st_size<1_000_000:
        raise RuntimeError('CAST_FORMAL_VERIFIED_SOURCE_NOT_INSTALLED:'+str(source))
    rig=bpy.data.objects.get('Host.rig')
    body=bpy.data.objects.get('Host.body')
    if not rig or not body or len(rig.data.bones)!=163:
        raise RuntimeError('CAST_FORMAL_PRODUCTION_RIG_MISSING')
    source_name=SUIT_PREFIX+variant.upper().replace('-','_')
    with bpy.data.libraries.load(str(source),link=False) as (src,dst):
        if source_name not in src.objects or 'Host.rig' not in src.objects:
            raise RuntimeError('CAST_FORMAL_DONOR_OBJECTS_MISSING')
        dst.objects=[source_name,'Host.rig']
    garment=next((o for o in dst.objects if o and o.type=='MESH'),None)
    donor_rig=next((o for o in dst.objects if o and o.type=='ARMATURE'),None)
    if not garment or not donor_rig or garment.get('donorCC0') is not True:
        raise RuntimeError('CAST_FORMAL_DONOR_PROVENANCE_INVALID')
    if len(donor_rig.data.bones)!=len(rig.data.bones):
        raise RuntimeError('CAST_FORMAL_RIG_COUNT_MISMATCH')
    rest_error=0.
    for bone in rig.data.bones:
        other=donor_rig.data.bones.get(bone.name)
        if not other:raise RuntimeError('CAST_FORMAL_BONE_MISSING:'+bone.name)
        for a,b in zip(bone.matrix_local,other.matrix_local):
            rest_error=max(rest_error,max(abs(x-y) for x,y in zip(a,b)))
    if rest_error>1e-4:raise RuntimeError('CAST_FORMAL_REST_MISMATCH:'+str(rest_error))
    if not any(m.type=='ARMATURE' for m in garment.modifiers):
        raise RuntimeError('CAST_FORMAL_ARMATURE_MODIFIER_MISSING')
    if len(garment.data.vertices)<1000 or len(garment.vertex_groups)<20:
        raise RuntimeError('CAST_FORMAL_WEIGHTS_MISSING')
    # Keep garment position relative to donor rig, then place it into the
    # *current assembled cast* rig's local space (not the donor scene world).
    local_to_donor_rig=donor_rig.matrix_world.inverted() @ garment.matrix_world
    for mod in garment.modifiers:
        if mod.type=='ARMATURE':mod.object=rig
    garment.parent=rig
    garment.matrix_world=rig.matrix_world @ local_to_donor_rig
    scene.collection.objects.link(garment)
    garment.name='SCENEBAM_PRODUCTION_'+variant.replace('-','_')
    if donor_rig.users==0:bpy.data.objects.remove(donor_rig,do_unlink=True)
    # Hide only the original outfit/proxies; retain hands, head, skin, hair,
    # accessories, original facial performance and all original action data.
    original=['Host.mindfront_f_dress_11'] if character=='female' else [
        'Host.elvs_male_shirt_untucked_bd1','Host.mindfront_male_trousers_2']
    hidden=[]
    for ob in scene.objects:
        if ob==garment or ob.type!='MESH':continue
        refs=[str(ob.get(n) or '') for n in ('castFitSource','castGarmentSource','castGarmentProxySource')]
        covered=any(ob.name==n or ob.name.startswith(n+'.') or any(r.startswith(n) for r in refs) for n in original)
        if character=='female' and (ob.name.startswith('Host.V64_dress_lines') or ob.name.startswith('Host.V26_garment')):
            covered=True
        if covered:
            ob.hide_render=True
            hidden.append(ob.name)
    marks=bpy.data.collections.get('V26_GARMENT_MARKS')
    if marks:
        for ob in marks.objects:ob.hide_render=True
    source_mat=garment.active_material
    if not source_mat or not source_mat.use_nodes or not any(n.type=='TEX_IMAGE' and n.image for n in source_mat.node_tree.nodes):
        raise RuntimeError('CAST_FORMAL_ORIGINAL_PACKED_UV_TEXTURE_MISSING')
    # Every source is a real UV-mapped suit. Distinct shirt/collar islands must
    # retain their original white/patterned material as the suit is recolored.
    suit_ids,tie_ids,trim_ids,islands=_classify_garment(garment.data,garment.matrix_world,character=='male')
    # A rig digest alone cannot catch a garment shifted sideways off the actor.
    # Compare physical head/torso root placement in current world coordinates.
    chest_z=1.24
    def centre_at_height(ob):
        coords=[ob.matrix_world@v.co for v in ob.data.vertices]
        band=[p.x for p in coords if abs(p.z-chest_z)<.10]
        if not band:return None
        return (min(band)+max(band))*.5
    body_centre=centre_at_height(body)
    cloth_centre=centre_at_height(garment)
    if body_centre is None or cloth_centre is None or abs(body_centre-cloth_centre)>.12:
        raise RuntimeError('CAST_FORMAL_GARMENT_BODY_ALIGNMENT_FAILED:'+str([body_centre,cloth_centre]))
    suit_mat=_tint_material(source_mat,'SCENEBAM_SUIT_'+suit_hex,target)
    suit_index=len(garment.data.materials)
    garment.data.materials.append(suit_mat)
    tie_index=-1
    if tie_target:
        tie_mat=_tint_material(source_mat,'SCENEBAM_TIE_'+tie_hex,tie_target)
        tie_index=len(garment.data.materials)
        garment.data.materials.append(tie_mat)
    for poly in garment.data.polygons:
        poly.material_index=tie_index if poly.index in tie_ids else suit_index if poly.index in suit_ids else 0
    garment['scenebamWardrobeSource']='repo_production_assembly'
    garment['scenebamFormalVariant']=variant
    garment['scenebamSuitHex']=suit_hex
    garment['scenebamTieHex']=tie_hex
    bpy.context.view_layer.update()
    return {'enabled':True,'variant':variant,'source':str(source),'rigRestMaxError':rest_error,
            'garmentVertices':len(garment.data.vertices),'tieFaces':len(tie_ids),
            'suitFaces':len(suit_ids),'untintedShirtAndTrimFaces':len(trim_ids),'components':islands,'hiddenLegacyOutfit':hidden,
            'suitHex':suit_hex,'tieHex':tie_hex,'sourceVerified':True}
