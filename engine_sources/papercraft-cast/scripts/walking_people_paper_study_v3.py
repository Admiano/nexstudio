#!/usr/bin/env python3
"""Private-runner, render-only Walking People paper facet study.
Input original licensed FBX+JPGs. Outputs PNG and JSON only.
Never exports original/derived FBX, glTF, blend, photoscan textures.
"""
import os, bpy, json, math, hashlib, numpy as np
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"assets/walking-people-pack/WalkingPeoplepack2024.fbx"
OUT=Path(os.environ.get("WALKING_PAPER_V3_OUTPUT","walking-paper-v3-proof"))
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SOURCE),use_anim=False)
source={o.name:o for o in bpy.context.scene.objects if o.type=="MESH" and o.name in ("woman1","man1")}
assert set(source)=={"woman1","man1"},list(source)
scene=bpy.context.scene
for ob in bpy.context.scene.objects:
    if ob.type=="MESH":ob.hide_render=True
material_views={}
for ob in source.values():
    material_views[ob.name]=[m.name if m else None for m in ob.data.materials]
    
def bbox(ob):
    w=[ob.matrix_world@Vector(v) for v in ob.bound_box]
    return Vector([min(p[k] for p in w) for k in range(3)]),Vector([max(p[k] for p in w) for k in range(3)])
def get_atlas(name):
    texno={"woman1":1,"man1":2}[name]
    path=SOURCE.parent/("gihapeopletex%d.jpg"%texno)
    if not path.exists():return None,{"found":False}
    im=bpy.data.images.load(str(path),check_existing=False)
    native=list(im.size)
    im.scale(1024,1024)
    buf=np.empty(1024*1024*4,dtype=np.float32)
    im.pixels.foreach_get(buf)
    img=buf.reshape((1024,1024,4))
    return img,{"found":True,"filename":path.name,"native_size":native,"working_size":[1024,1024]}

def faceted_clone(original,ratio,img,tag):
    c=original.copy(); c.data=original.data.copy()
    c.name="PAPER_TEST_"+tag
    scene.collection.objects.link(c)
    w=c.matrix_world.copy()
    if c.parent:c.parent=None;c.matrix_world=w
    for m in list(c.modifiers):c.modifiers.remove(m)
    mesh=c.data
    before=len(mesh.polygons)
    d=c.modifiers.new("Intentional larger facet reduction","DECIMATE")
    d.ratio=ratio
    bpy.context.view_layer.objects.active=c
    for x in bpy.context.selected_objects:x.select_set(False)
    c.select_set(True)
    bpy.ops.object.modifier_apply(modifier=d.name)
    c.select_set(False)
    mesh=c.data
    for f in mesh.polygons:f.use_smooth=False
    colors=mesh.color_attributes.get("PaperFacetColor")
    if not colors:colors=mesh.color_attributes.new(name="PaperFacetColor",type="FLOAT_COLOR",domain="CORNER")
    mesh.color_attributes.active_color=colors
    uv=mesh.uv_layers.active
    vals=np.empty((len(mesh.loops),4),dtype=np.float32)
    vals[:]=(0.74,0.57,0.42,1.)
    used_atlas=bool(uv and img is not None)
    for poly in mesh.polygons:
        lidx=range(poly.loop_start,poly.loop_start+poly.loop_total)
        if used_atlas:
            pts=np.asarray([uv.data[l].uv[:] for l in lidx],dtype=np.float32)
            q=np.median(pts,axis=0)
            xi=max(0,min(1023,int((float(q[0])%1)*1023)))
            yi=max(0,min(1023,int((float(q[1])%1)*1023)))
            source_color=np.clip(img[yi,xi,:3],0,1)
            # Restore paper warmth, discard fine photographic shading;
            # preserve broad source palette classes and dark hair.
            brightness=float(np.dot(source_color,(.25,.62,.13)))
            steps=np.round(brightness*8)/8
            paper_base=np.array([.79,.69,.56],dtype=np.float32)
            if brightness<.21:
                result=np.array([.20,.14,.105],dtype=np.float32)+(source_color*.25)
            else:
                gray=np.ones(3,dtype=np.float32)*steps
                desat=source_color*.48+gray*.52
                result=np.clip(desat*.68+paper_base*.32,0,1)
        else:
            center=poly.center
            relative=(center.z-bbox(original)[0].z)/max(.1,(bbox(original)[1].z-bbox(original)[0].z))
            result=np.array((.30,.22,.17) if relative>.88 else ((.78,.62,.45) if relative>.58 else (.48,.42,.34)),dtype=np.float32)
        # Curated garment/hair/skin region palette: intentional paper hues.
        b0,b1=bbox(original)
        z=(original.matrix_world@poly.center).z
        zz=(z-b0.z)/max(.01,b1.z-b0.z)
        xx=((original.matrix_world@poly.center).x-b0.x)/max(.01,b1.x-b0.x)
        if original.name=="woman1":
            if zz>.90: ink="hair" if xx<.24 or xx>.76 or brightness<.20 else "skin"
            elif zz>.78: ink="hair" if (xx<.32 or xx>.73) and brightness<.34 else "skin"
            elif zz>.60: ink="hair" if (xx<.20 or xx>.82) and brightness<.28 else ("shirt" if .39<xx<.61 else "jacket")
            elif zz>.53: ink="jacket"
            elif zz>.13: ink="pants"
            else: ink="shoes"
            palettes={"skin":(.86,.63,.44),"hair":(.29,.185,.15),"jacket":(.74,.54,.34),"shirt":(.90,.83,.70),"pants":(.56,.52,.43),"shoes":(.38,.32,.28)}
        else:
            if zz>.92:ink="hair" if xx<.32 or xx>.70 or brightness<.25 else "skin"
            elif zz>.79:ink="skin" if brightness>.13 else "hair"
            elif zz>.53:ink="skin" if xx<.25 or xx>.75 else "shirt"
            elif zz>.14:ink="pants"
            else:ink="shoes"
            palettes={"skin":(.85,.59,.40),"hair":(.25,.17,.13),"shirt":(.85,.78,.65),"pants":(.37,.38,.39),"shoes":(.26,.23,.22)}
        result=np.array(palettes[ink],dtype=np.float32)*(0.90+0.14*round(brightness*5)/5)
        # Let the artistically placed geometry, not random face colors,
        # control the appearance; a small plane-angle variation adds texture.
        shade=max(.86,min(1.02,.94+.075*poly.normal.z))
        rgba=np.array([*(result*shade),1.],dtype=np.float32)
        for l in lidx: vals[l]=rgba
    colors.data.foreach_set("color",vals.flatten())
    mesh.update()
    region_count=cut_paper_regions(c,max_faces=54 if ratio>.03 else 28)
    mesh=c.data
    return c,{"paper_regions":region_count,"physical_sheet_thickness":True,"base_polygons":before,"faceted_polygons":len(mesh.polygons),"ratio":ratio,"uv_available":bool(uv),"atlas_sampled":used_atlas,"color_loops":len(mesh.loops)}
    

def cut_paper_regions(candidate,max_faces=42):
    """A real papercraft panel is contiguous faces sharing vertices internally,
    with duplicate vertices only along intentional group cut boundaries.
    Every panel thus receives its own physical side walls under Solidify.
    """
    from collections import defaultdict,deque
    old=candidate.data
    attr=old.color_attributes.get("PaperFacetColor")
    colors=[tuple(attr.data[p.loop_start].color[:3]) for p in old.polygons]
    adj=[set() for _ in old.polygons]
    sides=defaultdict(list)
    for f in old.polygons:
        vs=list(f.vertices)
        for a,b in zip(vs,vs[1:]+vs[:1]):
            sides[(min(a,b),max(a,b))].append(f.index)
    for ids in sides.values():
        if len(ids)!=2:continue
        a,b=ids
        diff=sum((colors[a][k]-colors[b][k])**2 for k in range(3))**.5
        if old.polygons[a].normal.dot(old.polygons[b].normal)>.82 and diff<.12:
            adj[a].add(b);adj[b].add(a)
    taken=[-1]*len(old.polygons);groups=[]
    for seed in sorted(old.polygons,key=lambda f:-f.area):
        if taken[seed.index]>=0:continue
        gid=len(groups);taken[seed.index]=gid
        q=deque([seed.index]);group=[]
        while q and len(group)<max_faces:
            f=q.popleft();group.append(f)
            for near in sorted(adj[f]):
                if taken[near]<0 and len(group)+len(q)<max_faces:
                    taken[near]=gid;q.append(near)
        groups.append(group)
    verts=[];faces=[];rgbs=[]
    for group in groups:
        vmap={}
        mean_color=[sum(colors[fi][k] for fi in group)/len(group) for k in range(3)]
        for fi in group:
            polygon=old.polygons[fi]
            ids=[]
            for v in polygon.vertices:
                if v not in vmap:
                    vmap[v]=len(verts);verts.append(tuple(old.vertices[v].co))
                ids.append(vmap[v])
            faces.append(ids);rgbs.append(mean_color)
    newmesh=bpy.data.meshes.new(candidate.name+"_PAPER_SHEETS")
    newmesh.from_pydata(verts,[],faces);newmesh.update()
    attr_new=newmesh.color_attributes.new(name="PaperFacetColor",type="FLOAT_COLOR",domain="CORNER")
    rgba=np.empty((len(newmesh.loops),4),dtype=np.float32)
    for fi,p in enumerate(newmesh.polygons):
        for loop in range(p.loop_start,p.loop_start+p.loop_total):
            rgba[loop]=[*rgbs[fi],1.]
    attr_new.data.foreach_set("color",rgba.flatten())
    newmesh.color_attributes.active_color=attr_new
    for p in newmesh.polygons:p.use_smooth=False
    candidate.data=newmesh
    solid=candidate.modifiers.new("Physical paper sheet walls","SOLIDIFY")
    low=min(v.co.z for v in newmesh.vertices); high=max(v.co.z for v in newmesh.vertices)
    solid.thickness=max(.00025,(high-low)*.00085)
    solid.offset=-.5
    return len(groups)

def scene_setup():
    scene.render.engine="BLENDER_WORKBENCH"
    scene.display.shading.light="STUDIO"
    scene.display.shading.studiolight_rotate_z=math.radians(15)
    scene.display.shading.color_type="VERTEX"
    scene.display.shading.show_cavity=True
    scene.display.shading.cavity_type="BOTH"
    scene.display.shading.curvature_ridge_factor=1.2
    scene.display.shading.curvature_valley_factor=1.15
    scene.display.shading.show_shadows=True
    scene.render.resolution_x=620
    scene.render.resolution_y=740
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.film_transparent=False
    scene.display.shading.background_type="VIEWPORT"
    scene.display.shading.background_color=(.85,.82,.78)
    camera_data=bpy.data.cameras.new("Camera_ortho")
    camera=bpy.data.objects.new("Camera_ortho",camera_data)
    scene.collection.objects.link(camera)
    camera_data.type="ORTHO"
    scene.camera=camera
    return camera
cam=scene_setup()
report={"source":"WalkingPeoplepack2024.fbx","original_bytes":SOURCE.stat().st_size,
        "original_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "original_source_faces":{n:len(o.data.polygons) for n,o in source.items()},
        "original_mesh_unmodified":True,
        "method":"Decimated real FBX + UV-atlas-sampled face-constant paper colors",
        "quality_gate":"UNAPPROVED: experimental faceting, not authored folded-paper hairstyle",
        "rig_state":"Source static; no armatures or facial animation",
        "license_policy":"No source/derived mesh or full-resolution atlas exported",
        "candidates":[],"renders":[]}
for name,original in source.items():
    image,atlas_meta=get_atlas(name)
    report[name+"_atlas"]=atlas_meta
    # Higher detail preserves the silhouette; second tier tests large facets.
    for tag,ratio in [("FINE",.075),("BOLD",.018)]:
        candidate,data=faceted_clone(original,ratio,image,name+"_"+tag)
        report["candidates"].append({"name":name,"variant":tag,**data})
        for o in source.values():o.hide_render=True
        for ob in bpy.context.scene.objects:
            if ob.name.startswith("PAPER_TEST_"):ob.hide_render=(ob!=candidate)
        mn,mx=bbox(original)
        center=(mn+mx)*.5
        height=max((mx-mn).z,.1)
        cam.data.ortho_scale=height*1.20
        for view,v in [("FRONT",(0,-1,.07)),("THREE_QUARTER",(1,-1,.13)),("PROFILE",(1,0,.10))]:
            cam.location=center+Vector(v).normalized()*height*3
            cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
            out=OUT/("%s_%s_%s.png"%(name,tag,view))
            scene.render.filepath=str(out)
            bpy.ops.render.render(write_still=True)
            report["renders"].append(out.name)
        candidate.hide_render=True
(OUT/"PAPER_V3_AUDIT.json").write_text(json.dumps(report,indent=2))
print("PAPER_V3_PROOF_DONE",json.dumps({"candidates":report["candidates"],"renders":report["renders"]}))
