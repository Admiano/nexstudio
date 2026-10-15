"""SceneBam V21 production Cast formalwear adapter.

Called in the native wardrobe selection phase after the original V3/V6
character assembly, BEFORE the shared finish, fabric, details and pose fit.
Imports geometry proven on the production-assembled female V3/male V6 cast rig,
preserving Host.rig, shape keys and all original performance actions.

Requires the independently packaged, SHA256-pinned assets. We deliberately fail
closed if a suit/tie separation is missing; never paint a costume-shaped patch.
"""
import bpy
import os
import re
from statistics import median
from pathlib import Path

KINDS = {
    "female-double-breasted", "female-statement",
    "male-jacket-tie", "male-double-breasted",
    "male-navy-classic", "male-dinner-jacket",
}
# Face counts here are from the six real Blender 5.2 geometry audits, not a
# guessed apparel mask. Each count refers to a physically isolated connected
# mesh island that follows the garment's original armature weights.
TIE_ISLAND_FACE_COUNTS = {
    'female-double-breasted': (436,),
    'female-statement': (616,),
    'male-jacket-tie': (678,382),
    'male-double-breasted': (436,),
    'male-navy-classic': (616,),
    'male-dinner-jacket': (580,580,316),
}

def _colour(code):
    if not re.fullmatch(r"[A-Fa-f0-9]{6}",code):
        raise ValueError("CAST_FORMAL_INVALID_HEX")
    return tuple(int(code[i:i + 2],16)/255 for i in (0,2,4))

def _islands(mesh):
    parent=list(range(len(mesh.vertices)))
    def find(a):
        while a != parent[a]:
            parent[a]=parent[parent[a]]
            a=parent[a]
        return a
    for edge in mesh.edges:
        a,b=edge.vertices
        x,y=find(a),find(b)
        if x!=y: parent[x]=y
    islands={}
    for polygon in mesh.polygons:
        root=find(polygon.vertices[0])
        islands.setdefault(root,[]).append(polygon.index)
    return list(islands.values())

def _island_stats(mesh,indices,world):
    vertices={v for index in indices for v in mesh.polygons[index].vertices}
    pts=[world@mesh.vertices[v].co for v in vertices]
    return {'faces':len(indices),'vertices':len(vertices),
            'bounds':[[min(float(p[i]) for p in pts),max(float(p[i]) for p in pts)] for i in range(3)]}

def _colour_material(source, role, rgb, variant):
    """Use the original packed photographic/illustrated UV atlas as luminance
    and detail authority, recolouring that material rather than drawing an
    unsupported overlay in image space."""
    mat=source.copy()
    mat.name='SCENEBAM_FORMAL_'+role.upper()+'_'+variant.replace('-','_')
    if not mat.use_nodes or not mat.node_tree:
        raise RuntimeError('CAST_FORMAL_MATERIAL_NODES_REQUIRED')
    nodes=mat.node_tree.nodes
    node=next((n for n in nodes if n.type == 'EMISSION' and n.inputs.get('Color')),None)
    if node is None:
        raise RuntimeError('CAST_FORMAL_ATLAS_EMISSION_MISSING')
    sock=node.inputs['Color']
    links=mat.node_tree.links
    existing=list(sock.links)
    if len(existing)!=1 or not any(n.type=='TEX_IMAGE' for n in nodes):
        raise RuntimeError('CAST_FORMAL_ORIGINAL_ATLAS_REQUIRED')
    upstream=existing[0].from_socket
    links.remove(existing[0])
    blend=nodes.new('ShaderNodeMixRGB')
    blend.name='SCENEBAM_FORMAL_'+role.upper()+'_UV_COLOUR'
    blend.blend_type='COLOR'
    blend.inputs[0].default_value=1.0
    blend.inputs[2].default_value=(*rgb,1.0)
    links.new(upstream,blend.inputs[1])
    links.new(blend.outputs[0],sock)
    mat.diffuse_color=(*rgb,1)
    return mat

def apply_formal(scene, variant, suit_hex, tie_hex):
    if variant not in KINDS:
        raise ValueError('CAST_FORMAL_UNKNOWN_STYLE')
    sex = variant.split('-')[0]
    if sex != os.environ.get('CAST_CHARACTER'):
        raise ValueError('CAST_FORMAL_WRONG_BODY')
    root = Path(os.environ.get('CAST_FORMAL_ASSETS_DIR',
        str(Path(__file__).resolve().parents[1] / 'engine_sources/makehuman-lineart/assets/cast-formals'))).resolve()
    file = root / (variant + '.blend')
    if not file.is_file():
        raise FileNotFoundError('CAST_FORMAL_ASSET_MISSING:' + str(file))
    rig = bpy.data.objects.get('Host.rig')
    body = bpy.data.objects.get('Host.body')
    if rig is None or body is None or len(rig.data.bones) != 163:
        raise RuntimeError('CAST_FORMAL_PRODUCTION_RIG_MISSING')
    expected = 'SCENEBAM_FORMAL_' + variant.upper().replace('-','_')
    with bpy.data.libraries.load(str(file),link=False) as (src,dst):
        if expected not in src.objects or 'Host.rig' not in src.objects:
            raise RuntimeError('CAST_FORMAL_ASSET_SIGNATURE_MISSING:' + variant)
        dst.objects = [expected,'Host.rig']
    donor = next((o for o in dst.objects if o and o.name.startswith(expected)),None)
    donor_rig = next((o for o in dst.objects if o and o.type == 'ARMATURE'),None)
    if not donor or not donor_rig or donor.type != 'MESH':
        raise RuntimeError('CAST_FORMAL_DONOR_INCOMPLETE')
    max_error = 0.0
    for bone in rig.data.bones:
        old = donor_rig.data.bones.get(bone.name)
        if old is None:
            raise RuntimeError('CAST_FORMAL_RIG_BONE_MISSING:' + bone.name)
        max_error=max(max_error,max(abs(float(x)-float(y)) for a,b in zip(old.matrix_local,bone.matrix_local) for x,y in zip(a,b)))
    if max_error > 1e-4:
        raise RuntimeError('CAST_FORMAL_RIG_MISMATCH:' + str(max_error))
    # A donor garment's own world matrix belongs to the donor SOURCE rig,
    # which may be staged at a different world origin from SceneBam's host.
    # Preserve donor-rig-relative placement, not absolute scene placement.
    # The old absolute-world copy left tailored coats visibly beside hosts.
    matrix = rig.matrix_world @ donor_rig.matrix_world.inverted_safe() @ donor.matrix_world.copy()
    for modifier in donor.modifiers:
        if modifier.type == 'ARMATURE':
            modifier.object = rig
    donor.parent = rig
    donor.matrix_world = matrix
    scene.collection.objects.link(donor)
    if donor_rig.users == 0:
        bpy.data.objects.remove(donor_rig,do_unlink=True)
    donor.name = expected
    donor['castWardrobeKind']='formal'
    donor['castWardrobeVariant']=variant
    donor['castWardrobeOriginalUV']=True
    # Rig rest-matrix parity does NOT establish garment/body placement.
    # Require upper-torso registration from the actual evaluated geometry.
    bpy.context.view_layer.update()
    def upper_center(obj):
        evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh_eval=evaluated.to_mesh()
        try:
            positions=[evaluated.matrix_world @ v.co for v in mesh_eval.vertices]
            # Cast male's approved Host.body can mask its clothed torso while
            # retaining the bare head/neck mesh. Use its head-axis as a stable
            # lateral registration fallback rather than declaring body absent.
            bands=((1.52,1.84,30),(1.43,1.92,25),(1.05,1.43,25)) if obj is body and sex=='male' else ((1.05,1.43,100),(1.43,1.92,25),(0.80,2.10,25))
            for lo,hi,min_points in bands:
                sample=[p for p in positions if lo <= p.z <= hi]
                if len(sample)>=min_points:
                    return (median(float(p.x) for p in sample),median(float(p.y) for p in sample))
            raise RuntimeError('CAST_FORMAL_BODY_ANCHOR_MISSING:'+obj.name+':'+str(len(positions)))
        finally:
            evaluated.to_mesh_clear()
    garment_center=upper_center(donor)
    body_center=upper_center(body)
    torso_dx=abs(garment_center[0]-body_center[0])
    if torso_dx > 0.12:
        raise RuntimeError('CAST_FORMAL_UNREGISTERED_TORSO:'+variant+':'+str(torso_dx))

    # Same removal rules as the successful production formal proof. Hide all
    # base garment meshes and their derived ink/fit copies, never the face/body.
    prior = ['Host.mindfront_f_dress_11'] if sex == 'female' else [
        'Host.elvs_male_shirt_untucked_bd1','Host.mindfront_male_trousers_2']
    hidden = []
    for obj in bpy.data.objects:
        if obj == donor or obj == rig or obj == body or obj.type != 'MESH':
            continue
        refs = [obj.get(k) for k in ('castFitSource','castGarmentSource','castGarmentProxySource')]
        target = any(obj.name == base or obj.name.startswith(base+'.')
                     or any(str(ref).startswith(base) for ref in refs if ref) for base in prior)
        marks = sex=='female' and (obj.name.startswith('Host.V64_dress_lines') or obj.name.startswith('Host.V26_garment'))
        # Both female suits share an exposed thigh artifact from the OLD
        # character's illustrated lower-leg overlay. A true Cycles object-ID
        # pass (QA run 38667001907) resolved the beige pixels to this mesh,
        # NOT Host.body or the newly rigged suit. Never mutate original art.
        redundant_leg_ink = sex=='female' and (
            obj.name == 'Host.lineart_lower_legs' or
            obj.name.startswith('Host.lineart_lower_legs.'))
        if target or marks or redundant_leg_ink:
            obj.hide_render = True
            hidden.append(obj.name)
    collection = bpy.data.collections.get('V26_GARMENT_MARKS')
    if collection:
        for obj in collection.objects:
            obj.hide_render=True
            hidden.append(obj.name)

    # Donor has one packed UV material. Separate face MATERIAL INDICES by real
    # connected cloth islands. This retains the original vertices, UVs, weights,
    # seam geometry, image detail and physically rigged garment motion.
    mesh=donor.data
    source=mesh.materials[0]
    if len(mesh.materials)!=1 or source is None:
        raise RuntimeError('CAST_FORMAL_UNEXPECTED_DONOR_MATERIAL_LAYOUT')
    islands=_islands(mesh)
    expected=list(TIE_ISLAND_FACE_COUNTS[variant])
    tie=[]
    suits=[]
    other=[]
    for indices in islands:
        # Garment segmentation is expressed relative to the host rig, not the
        # host's absolute world transform (which differs from donor proof scenes).
        stats=_island_stats(mesh,indices,rig.matrix_world.inverted_safe() @ donor.matrix_world)
        count=stats['faces']
        # Tight central upper-chest checks stop similarly-sized sleeves, pants
        # or hardware from being mistaken for the tie.
        xlo,xhi=stats['bounds'][0]
        zlo,zhi=stats['bounds'][2]
        is_tie=(count in expected and xlo > -0.09 and xhi < 0.09
                and zlo >= 0.95 and zhi <= 1.52)
        if is_tie:
            expected.remove(count)
            tie.append((indices,stats))
        elif count >= 900:
            suits.append((indices,stats))
        else:
            other.append((indices,stats))
    if expected or not tie or not suits or len(suits)<2:
        raise RuntimeError('CAST_FORMAL_UV_ISLAND_CONTRACT_FAILED:'+variant+':'+repr(expected))
    # ORIGINAL is an exact native UV-atlas reset, not an approximated palette hex.
    mesh.materials.append(source.copy() if suit_hex=='ORIGINAL' else _colour_material(source,'suit',_colour(suit_hex),variant))
    mesh.materials.append(source.copy() if tie_hex=='ORIGINAL' else _colour_material(source,'tie',_colour(tie_hex),variant))
    for indices,_ in suits:
        for index in indices:mesh.polygons[index].material_index=1
    for indices,_ in tie:
        for index in indices:mesh.polygons[index].material_index=2
    roles={'suit': [stats for _,stats in suits],'tie':[stats for _,stats in tie],
           'preserve':[stats for _,stats in other]}
    # Require exact partition of all polygons and physical separation.
    assert sum(sum(len(ids) for ids,_ in group) for group in (suits,tie,other))==len(mesh.polygons)
    assert all(mesh.polygons[i].material_index==2 for ids,_ in tie for i in ids)
    # Wardrobe-only body occlusion: keep original body topology, shape keys,
    # rig, face, neck, hands and feet. Mask only skin that is INSIDE a fully
    # covered suit/trouser area. This is a per-render reversible modifier on
    # the assembled performer, never an edit to the approved source body.
    # The raw CC0 trousers otherwise expose original leg skin at the thigh.
    visible=body.vertex_groups.get('SCENEBAM_FORMAL_VISIBLE_SKIN')
    if visible is None: visible=body.vertex_groups.new(name='SCENEBAM_FORMAL_VISIBLE_SKIN')
    hand_ids=set()
    for i,v in enumerate(body.data.vertices):
        if any(('hand' in body.vertex_groups[g.group].name.lower()
                or 'finger' in body.vertex_groups[g.group].name.lower()
                or 'wrist' in body.vertex_groups[g.group].name.lower()
                or 'thumb' in body.vertex_groups[g.group].name.lower()
                or 'palm' in body.vertex_groups[g.group].name.lower())
               and g.weight>0.08 for g in v.groups):
            hand_ids.add(i)
    if len(hand_ids)<40:
        raise RuntimeError('CAST_FORMAL_HAND_SKIN_PROTECTION_UNVERIFIED:'+str(len(hand_ids)))
    exposed=[v.index for v in body.data.vertices
             if v.index in hand_ids or (body.matrix_world@v.co).z >= 1.43
             or (body.matrix_world@v.co).z < 0.14]
    if len(exposed)<len(hand_ids)+80:
        raise RuntimeError('CAST_FORMAL_FACE_SKIN_PROTECTION_UNVERIFIED')
    visible.add(exposed,1.0,'REPLACE')
    modifier=body.modifiers.new('SCENEBAM_FORMAL_CLOTHING_UNDERLAY','MASK')
    modifier.vertex_group=visible.name
    modifier.invert_vertex_group=False
    # Exactly the same selected-garment discovery contract used by the
    # original wardrobe in dressswap.py/garm.py. Do not create a second
    # post-render wardrobe path. The single merged formal mesh is tagged so
    # the shared pose fitter does not incorrectly treat it as a shirt without
    # trousers. No changes are applied to the user-facing casual selections.
    os.environ['DOBJ']=donor.name
    os.environ['GARMS']=donor.name+'='+('ORIGINAL' if suit_hex=='ORIGINAL' else suit_hex)
    bpy.context.view_layer.update()
    return {'enabled':True,'variant':variant,'sourceFile':file.name,
            'selectedGarment':donor.name,'nativeWardrobe':True,
            'restError':max_error,'garmentVertices':len(donor.data.vertices),
            'hiddenOriginalGarments':hidden,'materialsByRole':roles,
            'suitHex':suit_hex.upper(),'tieHex':tie_hex.upper(),
            'rigPreserved':True,'collisionCertified':False,
            'bodySkinOcclusion':{'preservedHandVertices':len(hand_ids),'preservedSkinVertices':len(exposed),'originalBodyShapeKeys':len(body.data.shape_keys.key_blocks)},
            'garmentTorsoCenter':garment_center,'bodyTorsoCenter':body_center,'torsoXDeviation':torso_dx}
