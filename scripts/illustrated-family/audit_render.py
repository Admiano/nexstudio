#!/usr/bin/env python3
"""Read-only illustrated-family audit, real Blender stills and isolated FACE proofs.

Always load a canonical V1 scene as the Blender startup file. All saves and
renders are written under --out. No production data or animation actions edited.
"""
import argparse
import json
import os
import runpy
import sys
from collections import Counter
from pathlib import Path

import bpy
from mathutils import Vector

def args_after_dash():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--gender", choices=("female", "male"))
    p.add_argument("--face", type=int, choices=(0, 1, 2, 3), default=0)
    p.add_argument("--facevar-script")
    p.add_argument("--smoke", action="store_true")
    return p.parse_args(args)

def render_settings(width, height, samples=12):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    return scene

def smoke(out):
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=False)
    s = render_settings(256, 256, 8)
    s.render.filepath = str(out / "blender-smoke.png")
    bpy.ops.render.render(write_still=True)
    assert Path(s.render.filepath).is_file()
    (out / "runtime.json").write_text(json.dumps({
        "blender": bpy.app.version_string,
        "engine": s.render.engine,
        "image": Path(s.render.filepath).name
    }, indent=2))
    print("SMOKE_RENDER_OK", s.render.filepath, flush=True)

def world_coords(mesh_obj, group_name=None):
    verts = mesh_obj.data.vertices
    if group_name and group_name in mesh_obj.vertex_groups:
        gidx = mesh_obj.vertex_groups[group_name].index
        indices = [v.index for v in verts if any(
            g.group == gidx and g.weight > 0.15 for g in v.groups)]
        if indices:
            return [mesh_obj.matrix_world @ verts[i].co for i in indices]
    return [mesh_obj.matrix_world @ v.co for v in verts]

def bbox(points):
    return Vector(tuple(min(p[d] for p in points) for d in range(3))), \
           Vector(tuple(max(p[d] for p in points) for d in range(3)))

def audit():
    objects = []
    for ob in sorted(bpy.data.objects, key=lambda o: o.name):
        record = {
            "name": ob.name, "type": ob.type,
            "visible_render": not ob.hide_render,
            "parent": ob.parent.name if ob.parent else None,
            "parent_type": ob.parent_type,
            "modifiers": [{"name": m.name, "type": m.type} for m in ob.modifiers],
        }
        if ob.type == "ARMATURE":
            record["bone_count"] = len(ob.data.bones)
            record["bones"] = [b.name for b in ob.data.bones]
        if ob.type == "MESH":
            record["vertices"] = len(ob.data.vertices)
            record["faces"] = len(ob.data.polygons)
            record["vertex_groups"] = [g.name for g in ob.vertex_groups]
            record["materials"] = [m.name if m else None for m in ob.data.materials]
            if ob.data.shape_keys:
                record["shape_keys"] = [k.name for k in ob.data.shape_keys.key_blocks]
                record["active_keys"] = {
                    k.name: round(k.value, 6) for k in ob.data.shape_keys.key_blocks
                    if abs(k.value) > 1e-6
                }
        objects.append(record)
    dependencies = []
    for im in bpy.data.images:
        p = bpy.path.abspath(im.filepath) if im.filepath else ""
        dependencies.append({
            "name": im.name, "source": im.source,
            "path": im.filepath, "resolved": p,
            "packed": bool(im.packed_file),
            "exists": bool(im.packed_file) or im.source in {"GENERATED", "VIEWER"}
                      or bool(p and os.path.isfile(p))
        })
    libraries = [{
        "name": lib.name, "path": lib.filepath,
        "resolved": bpy.path.abspath(lib.filepath),
        "exists": os.path.exists(bpy.path.abspath(lib.filepath))
    } for lib in bpy.data.libraries]
    return {
        "blender": bpy.app.version_string,
        "scene": bpy.data.filepath,
        "frame": bpy.context.scene.frame_current,
        "render_engine_original": bpy.context.scene.render.engine,
        "counts": dict(Counter(x["type"] for x in objects)),
        "objects": objects,
        "images": dependencies,
        "libraries": libraries,
        "missing_image_dependencies": [x for x in dependencies if not x["exists"]],
        "missing_libraries": [x for x in libraries if not x["exists"]],
    }

def camera_setup(target, scale, view):
    s = bpy.context.scene
    camera = bpy.data.objects.get("ILLUSTRATED_FAMILY_AUDIT_CAMERA")
    if camera is None:
        data = bpy.data.cameras.new("ILLUSTRATED_FAMILY_AUDIT_CAMERA")
        camera = bpy.data.objects.new(data.name, data)
        s.collection.objects.link(camera)
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = scale
    # Faces point toward negative Y in the canonical V1 rigs.
    camera.location = target + Vector((0.0 if view == "front" else 1.7, -5.0, 0.12))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    s.camera = camera

def render_view(out, name, target, scale, size, view):
    s = render_settings(size[0], size[1])
    camera_setup(target, scale, view)
    s.render.filepath = str(out / name)
    bpy.ops.render.render(write_still=True)
    if not Path(s.render.filepath).is_file():
        raise RuntimeError("No render was produced: " + s.render.filepath)
    print("RENDER_OK", s.render.filepath, flush=True)

def main():
    args = args_after_dash()
    out = Path(args.out).resolve()
    if args.smoke:
        smoke(out)
        return
    out.mkdir(parents=True, exist_ok=True)
    if not args.gender:
        raise RuntimeError("--gender is required for canonical scene validation")
    if not bpy.data.filepath:
        raise RuntimeError("Load an existing canonical .blend scene first")
    if not bpy.data.objects.get("Host.body") or not bpy.data.objects.get("Host.rig"):
        raise RuntimeError("Canonical Host.body / Host.rig are missing")
    metadata = audit()
    metadata["requested_gender"] = args.gender
    metadata["face_identity"] = args.face
    (out / "inventory.json").write_text(json.dumps(metadata, indent=2))

    scene = bpy.context.scene
    scene.frame_set(27)
    if args.face:
        if not args.facevar_script or not Path(args.facevar_script).is_file():
            raise RuntimeError("Native V1 facevar.py not accessible")
        # Existing implementation applies the authored rest-pose deltas across
        # shape-key blocks. This is a disposable variant scene, never canonical.
        os.environ["FACE"] = str(args.face)
        runpy.run_path(args.facevar_script, run_name="__main__")

    bpy.context.view_layer.update()
    body = bpy.data.objects["Host.body"]
    entire_min, entire_max = bbox(world_coords(body))
    head_min, head_max = bbox(world_coords(body, "head"))
    center = (entire_min + entire_max) / 2
    head = (head_min + head_max) / 2
    overall_height = max(1.6, entire_max.z - entire_min.z)
    head_height = max(0.19, head_max.z - head_min.z)
    # Omit the Guest and reference mannequins in comparison renders only.
    for obj in bpy.data.objects:
        if obj.name.startswith(("Guest.", "Ref.")):
            obj.hide_render = True

    # Save separate, editable .blend proving the variant uses real geometry.
    proof = out / (args.gender + "_face" + str(args.face) + ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=str(proof), compress=True, copy=True)
    print("EDITABLE_PROOF_OK", proof, flush=True)
    render_view(out, "body_front.png", center, overall_height * 1.38,
                (480, 720), "front")
    render_view(out, "face_front.png", head, max(0.35, head_height * 1.7),
                (500, 500), "front")
    render_view(out, "face_threeq.png", head, max(0.35, head_height * 1.7),
                (500, 500), "threeq")
    print("FOUNDATION_OK", args.gender, args.face, flush=True)

if __name__ == "__main__":
    main()
