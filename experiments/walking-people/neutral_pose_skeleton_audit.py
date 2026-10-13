"""Non-destructive joint/plant diagnostics for the untouched Walking People source.
Outputs original-source Blender scenes and structured anatomical measurements.
No regenerated eyes, mesh replacements, or changes to source UV/texture/material.
ALL results are development-only until visually approved and licensed.
"""
import bpy, json, sys, math, hashlib, statistics, os
from pathlib import Path
from mathutils import Vector
from collections import defaultdict

root=Path(__file__).resolve().parents[2]
source=root/"engine_sources/papercraft-cast/assets/walking-people-pack/WalkingPeoplepack2024.fbx"
out=Path(os.environ.get("NEX_OUT","working-walking-neutral-review"))
out.mkdir(parents=True,exist_ok=True)
assert source.stat().st_size>60000000
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(source),use_anim=False)
objs={o.name:o for o in bpy.data.objects if o.type=="MESH"}
assert all(n in objs for n in ("man1","woman2"))
tex_paths=list(source.parent.glob("gihapeopletex*.jpg"))
assert len(tex_paths)==5
for img in bpy.data.images:
    basename=Path(img.filepath.replace(chr(92),"/")).name.lower()
    p=next((f for f in tex_paths if f.name.lower()==basename),None)
    if p:
        img.filepath=str(p);img.reload()
src_sha=hashlib.sha256(source.read_bytes()).hexdigest()
report={"source_sha256":src_sha,"source_bytes":source.stat().st_size,
        "method":"untouched source geometry + measured candidate neutral skeleton ONLY",
        "source_meshes":list(objs),"source_armatures":[o.name for o in bpy.data.objects if o.type=="ARMATURE"],
        "source_animations":len(bpy.data.actions),"characters":{}}
for name in ("man1","woman2"):
    o=objs[name]
    base=o.matrix_world.copy()
    # Sample every 2nd vertex for percentile statistics, read-only.
    pts=[base@v.co for v in list(o.data.vertices)[::2]]
    bb=[base@Vector(v) for v in o.bound_box]
    lo=Vector([min(p[i] for p in bb) for i in range(3)])
    hi=Vector([max(p[i] for p in bb) for i in range(3)])
    h=hi.z-lo.z; cx=(hi.x+lo.x)*.5
    stats={}
    for band in ((0,.08),(.08,.15),(.15,.25),(.25,.38),(.38,.48),(.48,.58),(.58,.68),(.68,.76),(.76,.88),(.88,1)):
        rows=[p for p in pts if band[0]<=((p.z-lo.z)/h)<band[1]]
        if not rows:continue
        xs=sorted(p.x for p in rows);ys=sorted(p.y for p in rows)
        def p(a,q):return round(a[min(len(a)-1,max(0,int(q*(len(a)-1))))],5)
        stats[str(band)]={"count":len(rows),"x_p10":p(xs,.1),"x_p25":p(xs,.25),"x_p50":p(xs,.5),"x_p75":p(xs,.75),"x_p90":p(xs,.9),
                           "y_p25":p(ys,.25),"y_p50":p(ys,.5),"y_p75":p(ys,.75)}
    # At the ankle/sole height, split geometry into two foot clusters by median X.
    footpts=[p for p in pts if (p.z-lo.z)/h<.12]
    footcut=statistics.median(p.x for p in footpts)
    feet={}
    for side,subset in (("LEFT",[p for p in footpts if p.x>=footcut]),("RIGHT",[p for p in footpts if p.x<footcut])):
        assert subset
        feet[side]=[round(statistics.median(p[i] for p in subset),5) for i in range(3)]
    footwidth=math.dist(feet["LEFT"],feet["RIGHT"])
    # Simple measured landmarks; not a claim that these equal accurate joint centres.
    torso=[p for p in pts if .50<((p.z-lo.z)/h)<.66 and abs(p.x-cx)<(hi.x-lo.x)*.18]
    ty=statistics.median(p.y for p in torso) if torso else (hi.y+lo.y)*.5
    landmarks={
      "root":[cx,ty,lo.z+.55*h],
      "pelvis":[cx,ty,lo.z+.51*h],
      "spine_mid":[cx,ty,lo.z+.68*h],
      "neck":[cx,ty,lo.z+.86*h],
      "head":[cx,ty,lo.z+.94*h],
      "ankle_L":feet["LEFT"],"ankle_R":feet["RIGHT"],
      "knee_L":[feet["LEFT"][0],ty,lo.z+.285*h],
      "knee_R":[feet["RIGHT"][0],ty,lo.z+.285*h],
      "hip_L":[cx+(hi.x-lo.x)*.08,ty,lo.z+.50*h],
      "hip_R":[cx-(hi.x-lo.x)*.08,ty,lo.z+.50*h],
    }
    # Provisional skeleton as a SEPARATE object, no armature modifier on original scan.
    rigdata=bpy.data.armatures.new(name+"_ANATOMICAL_LANDMARKS_RIG_STUDY")
    rig=bpy.data.objects.new(name+"_ANATOMICAL_LANDMARKS_RIG_STUDY",rigdata)
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active=rig
    bpy.ops.object.mode_set(mode="EDIT")
    for bname,pair in {
       "pelvis":("pelvis","spine_mid"),
       "spine":("spine_mid","neck"),
       "neck":("neck","head"),
       "thigh.L":("hip_L","knee_L"),
       "thigh.R":("hip_R","knee_R"),
       "shin.L":("knee_L","ankle_L"),
       "shin.R":("knee_R","ankle_R"),
    }.items():
        eb=rigdata.edit_bones.new(bname)
        eb.head=landmarks[pair[0]]
        eb.tail=landmarks[pair[1]]
        if (eb.tail-eb.head).length<.001:
            eb.tail.z+=.01
    bpy.ops.object.mode_set(mode="OBJECT")
    rig.hide_render=True
    rig.hide_viewport=True
    rig["DO_NOT_EXPORT_AS_PRODUCTION_RIG"]=True
    rig["not_weighted_to_source"]=True
    def geometry_digest(o):
        sh=hashlib.sha256()
        import struct
        for v in o.data.vertices:
            sh.update(struct.pack("fff",float(v.co.x),float(v.co.y),float(v.co.z)))
        for p in o.data.polygons:
            sh.update(struct.pack("I",int(p.loop_total)))
            for li in p.loop_indices:sh.update(struct.pack("I",o.data.loops[li].vertex_index))
        return sh.hexdigest()
    report["characters"][name]={
      "object":name,"verts":len(o.data.vertices),"polygons":len(o.data.polygons),
      "dims_world":[round(v,4) for v in hi-lo],"bounds":[list(lo),list(hi)],
      "mesh_digest":geometry_digest(o),
      "uv_layers":[uv.name for uv in o.data.uv_layers],
      "original_materials":[m.name for m in o.data.materials if m],
      "foot_split_by_world_x":feet,"foot_separation_m_or_source_units":footwidth,
      "slices":stats,"provisional_landmarks":landmarks,
      "note":"This joint study does NOT retarget animation or alter existing 22-bone Stage 2 checkpoint."
    }

# Render two source characters unmodified from front and 3/4, working-colors show original textures.
scene=bpy.context.scene
camdata=bpy.data.cameras.new("Source assessment camera");camdata.type="ORTHO"
cam=bpy.data.objects.new("Source assessment camera",camdata);scene.collection.objects.link(cam);scene.camera=cam
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.light="STUDIO"
scene.display.shading.color_type="TEXTURE"
scene.display.shading.show_cavity=True
scene.display.shading.background_type="VIEWPORT"
scene.display.shading.background_color=(.90,.90,.90)
scene.render.resolution_x=620;scene.render.resolution_y=780
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
for name in ("man1","woman2"):
    obj=objs[name]
    for ob in objs.values():ob.hide_render=ob!=obj
    bbox=[obj.matrix_world@Vector(v) for v in obj.bound_box]
    lo=Vector([min(p[k] for p in bbox) for k in range(3)])
    hi=Vector([max(p[k] for p in bbox) for k in range(3)])
    mid=(lo+hi)/2
    h=(hi-lo).z
    camdata.ortho_scale=h*1.18
    for angle,vec in (("front",Vector((0,-1,.08))),("threeq",Vector((1,-1,.10)))):
        cam.location=mid+vec.normalized()*h*2.5
        cam.rotation_euler=(mid-cam.location).to_track_quat("-Z","Y").to_euler()
        scene.render.filepath=str(out/(name+"_intact_"+angle+".png"))
        bpy.ops.render.render(write_still=True)
    scene.render.filepath=str(out/(name+"_intact_front.png"))
for ob in objs.values():ob.hide_render=False
scene["ORIGINAL_SKIN_CLOTHES_HAIR"] = "UNCHANGED"
scene["MOTION_VALIDATION"] = "NONE: landmark study, not bound animation"
bpy.ops.wm.save_as_mainfile(filepath=str(out/"ORIGINAL_SCANS_LANDMARKS_ONLY.blend"),compress=True)
(out/"LANDMARK_AUDIT.json").write_text(json.dumps(report,indent=2,default=str))
print("ANATOMICAL_AUDIT_JSON_BEGIN")
print(json.dumps({"source_sha256":report["source_sha256"],"characters":{
  k:{"verts":v["verts"],"dims_world":v["dims_world"],"foot_centers":v["foot_split_by_world_x"],
     "foot_sep":v["foot_separation_m_or_source_units"],"bounds":v["bounds"],
     "materials":v["original_materials"]} for k,v in report["characters"].items()}},default=str))
print("ANATOMICAL_AUDIT_JSON_END")
