"""Prototype 01: detachable, rigged illustrated waistcoat over the V1 garment.

Operates ONLY on a Blender scene already loaded from a disposable canonical copy.
The source garment remains visible, with original datablocks and action untouched.
This deliberately makes a small geometry-led outfit alternative, not a production
blazer. Do not ship without front, 3/4, pose, clipping and seam QA.
"""
import bpy
import bmesh
import json
import math
from mathutils import Vector

SOURCES = {
    "female": ("Host.mindfront_f_dress_11", "FEMALE", (0.82, 0.74, 0.59, 1)),
    "male": ("Host.elvs_male_shirt_untucked_bd1", "MALE", (0.22, 0.30, 0.42, 1)),
}

def build_waistcoat(gender):
    if gender not in SOURCES:
        raise ValueError("gender must be female or male")
    source_name, label, rgba = SOURCES[gender]
    source = bpy.data.objects.get(source_name)
    rig = bpy.data.objects.get("Host.rig")
    body = bpy.data.objects.get("Host.body")
    if not source or not rig or not body:
        raise RuntimeError("Source garment/rig/body not present: " + source_name)
    if source.type != 'MESH' or not any(m.type == 'ARMATURE' for m in source.modifiers):
        raise RuntimeError("Expected a rigged source garment: " + source_name)

    # No object from the immutable source scene is edited; source remains enabled.
    obj = source.copy()
    obj.data = source.data.copy()
    obj.name = "V1_WARDROBE_TRIAL_" + label + "_WAISTCOAT"
    obj.data.name = obj.name + "_MESH"
    bpy.context.scene.collection.objects.link(obj)

    # Derive the cut region from measured garment height and actor centre.
    # Uses real world positions of source vertices, not invented human geometry.
    garment_points = [source.matrix_world @ v.co for v in source.data.vertices]
    left = min(p.x for p in garment_points)
    right = max(p.x for p in garment_points)
    middle_x = (left+right)*0.5
    torso_points = [p for p in garment_points if 1.10 < p.z < 1.40 and abs(p.x-middle_x)<0.22]
    if len(torso_points) < 64:
        raise RuntimeError("Cannot safely identify torso geometry in source garment")
    front_y = min(p.y for p in torso_points)
    back_y = max(p.y for p in torso_points)
    torso_width = max(0.14, min(0.22, (right-left)*0.38))
    # Keep below the neckline and above the waist. Remove a shallow V-shaped
    # front opening so the approved shirt or dress is visible beneath.
    low, high = (1.10,1.385) if gender=="female" else (1.09,1.385)
    threshold = front_y+(back_y-front_y)*0.55
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    delete=[]
    for face in bm.faces:
        p=source.matrix_world @ face.calc_center_median()
        dx=abs(p.x-middle_x)
        in_torso = low <= p.z <= high and dx < torso_width
        opening = False
        if in_torso and p.y < threshold:
            t=max(0,min(1,(p.z-low)/(high-low)))
            opening_width=0.014 + 0.065*t*t
            opening=(dx<opening_width)
        if not in_torso or opening:delete.append(face)
    if delete:bmesh.ops.delete(bm,geom=delete,context="FACES")
    isolated=[v for v in bm.verts if not v.link_faces]
    if isolated:bmesh.ops.delete(bm,geom=isolated,context="VERTS")
    if len(bm.faces)<50:
        bm.free()
        bpy.data.objects.remove(obj,do_unlink=True)
        raise RuntimeError("Waistcoat clipping removed too much source garment")
    remaining_faces=len(bm.faces)
    bm.to_mesh(obj.data);bm.free();obj.data.update()
    # Offset over the source shirt/dress. Geometry normals are inherited from
    # a garment built and rigged by the original MakeHuman pipeline.
    for v in obj.data.vertices:
        v.co += v.normal * 0.0042

    # Own single illustrated colour; an original-derived garment retains
    # bone weights, rig modifiers and correct silhouette registration.
    mat=bpy.data.materials.new(obj.name+"_FABRIC")
    mat.diffuse_color=rgba
    mat.use_nodes=True
    nt=mat.node_tree
    nt.nodes.clear()
    out=nt.nodes.new("ShaderNodeOutputMaterial")
    emission=nt.nodes.new("ShaderNodeEmission")
    emission.inputs['Color'].default_value=rgba
    emission.inputs['Strength'].default_value=0.88
    nt.links.new(emission.outputs[0],out.inputs['Surface'])
    obj.data.materials.clear()
    obj.data.materials.append(mat)

    # New modifier is non-destructive and supports real open neckline and hem.
    shell=obj.modifiers.new("Wardrobe trial bounded hem","SOLIDIFY")
    shell.thickness=0.00125
    shell.offset=-1.0
    shell.use_even_offset=False
    shell.use_rim=True
    obj["v1WardrobeProof"]="01"
    obj["sourceGarment"]=source_name
    obj["sourcePreserved"]=True
    obj["performanceValidated"]=False
    report = {
        "gender":gender,"object":obj.name,"source":source_name,
        "new_faces":remaining_faces,"rig":rig.name,
        "armature_modifiers":sum(m.type=="ARMATURE" for m in obj.modifiers),
        "source_visible":not source.hide_render,
        "base_garment_preserved":True,
        "qa_status":"VISUAL_AND_PERFORMANCE_REVIEW_REQUIRED",
        "license_note":"Source-derived MakeHuman garment. Retain asset CC-BY attribution.",
    }
    print("WARDROBE_TRIAL_CREATED",json.dumps(report),flush=True)
    return report
