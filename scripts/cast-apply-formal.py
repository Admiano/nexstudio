"""SceneBam V21 production Cast formalwear adapter.

Called only AFTER the existing character, polish, garments and cloth pass finish.
Imports geometry proven on the production-assembled female V3/male V6 cast rig,
preserving Host.rig, shape keys and all original performance actions.

Requires the independently packaged, SHA256-pinned assets. We deliberately fail
closed if a suit/tie separation is missing; never paint a costume-shaped patch.
"""
import bpy
import os
import re
from pathlib import Path

KINDS = {
    "female-double-breasted", "female-statement",
    "male-jacket-tie", "male-double-breasted",
    "male-navy-classic", "male-dinner-jacket",
}
SUIT_EXCLUDE = ("tie", "bow", "neck", "button", "metal", "shoe", "sole", "skin", "shirt", "watch", "hair", "eye", "teeth")
TIE_NAMES = ("necktie", "bowtie", "bow_tie", "tie", "cravat")

def _colour(code):
    if not re.fullmatch(r"[A-Fa-f0-9]{6}",code):
        raise ValueError("CAST_FORMAL_INVALID_HEX")
    return tuple(int(code[i:i + 2],16)/255 for i in (0,2,4))

def _shade(material, rgb):
    material.diffuse_color = (*rgb, 1)
    material.use_nodes = True
    count = 0
    for node in material.node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            socket = node.inputs.get('Base Color')
            if socket is not None:
                socket.default_value = (*rgb,1)
                count += 1
        elif node.type == 'BSDF_DIFFUSE':
            socket = node.inputs.get('Color')
            if socket is not None:
                socket.default_value = (*rgb,1)
                count += 1
    if count == 0:
        raise RuntimeError('CAST_FORMAL_UNCOLOURABLE_MATERIAL:' + material.name)

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
    matrix = donor.matrix_world.copy()
    for modifier in donor.modifiers:
        if modifier.type == 'ARMATURE':
            modifier.object = rig
    donor.parent = rig
    donor.matrix_world = matrix
    scene.collection.objects.link(donor)
    if donor_rig.users == 0:
        bpy.data.objects.remove(donor_rig,do_unlink=True)
    donor.name = expected

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
        if target or marks:
            obj.hide_render = True
            hidden.append(obj.name)
    collection = bpy.data.collections.get('V26_GARMENT_MARKS')
    if collection:
        for obj in collection.objects:
            obj.hide_render=True
            hidden.append(obj.name)

    # A real rigged mesh has per-face material slots: tint the tailored fabric
    # and the tie material separately, without altering the body or white shirt.
    roles = {'suit': [], 'tie': [], 'preserve': []}
    rgb={'suit':_colour(suit_hex),'tie':_colour(tie_hex)}
    materials = [m for m in donor.data.materials if m]
    for slot,material in enumerate(donor.data.materials):
        if material is None:
            continue
        name = material.name.lower().replace(' ','_')
        role = 'tie' if any(t in name for t in TIE_NAMES) else ('preserve' if any(t in name for t in SUIT_EXCLUDE) else 'suit')
        roles[role].append({'slot':slot,'original':material.name})
        if role in rgb:
            copy=material.copy()
            copy.name='SCENEBAM_' + role.upper() + '_' + variant.replace('-','_') + '_' + str(slot)
            _shade(copy,rgb[role])
            donor.data.materials[slot]=copy
    if not roles['suit'] or not roles['tie']:
        raise RuntimeError('CAST_FORMAL_SEPARATE_SUIT_TIE_MATERIALS_REQUIRED:' + repr(roles))
    scene.view_layers.update() if hasattr(scene.view_layers,'update') else bpy.context.view_layer.update()
    return {'enabled':True,'variant':variant,'sourceFile':file.name,
            'restError':max_error,'garmentVertices':len(donor.data.vertices),
            'hiddenOriginalGarments':hidden,'materialsByRole':roles,
            'suitHex':suit_hex.upper(),'tieHex':tie_hex.upper(),
            'rigPreserved':True,'collisionCertified':False}
