"""NexStudio V1 illustrated tailored jacket V5 EXTENDED COAT / SKINNED LAPEL / WELT STUDY (ISOLATED UNAPPROVED geometry proof).

Use canonical saved rigged garment topology, material and bone weights.
No new skeleton, source remesh, source action edit, or per-frame construction.
A 3D shell wraps BOTH sides, back and existing sleeve silhouettes rather than
the front-only flat patches from V1 wardrobe trial. Non-final: pose tests
and collar/seam review required before production integration.
"""
import bpy, bmesh, json, math
from mathutils import Vector
from mathutils.kdtree import KDTree

def build_jacket(gender):
    sources = {
        "female": {"name": "Host.mindfront_f_dress_11","low":0.976,
                   "high":1.485,"fabric":(0.34,0.18,0.21,1),
                   "trim":(0.63,0.37,0.37,1)},
        "male": {"name": "Host.elvs_male_shirt_untucked_bd1","low":1.012,
                 "high":1.485,"fabric":(0.12,0.17,0.27,1),
                 "trim":(0.32,0.42,0.56,1)}
    }
    if gender not in sources: raise ValueError(gender)
    conf=sources[gender]
    ob=bpy.data.objects.get(conf["name"])
    body=bpy.data.objects.get("Host.body")
    rig=bpy.data.objects.get("Host.rig")
    assert ob and body and rig, "Canonical source garment missing"
    assert any(x.type=="ARMATURE" for x in ob.modifiers), "Base garment unrigged"
    origin=ob.matrix_world.copy()
    pts=[origin @ x.co for x in ob.data.vertices]
    cx=(max(p.x for p in pts)+min(p.x for p in pts))*.5
    torso=[p for p in pts if 1.10 < p.z < 1.40 and abs(p.x-cx)<.18]
    assert len(torso)>60, "No viable source torso points"
    # The source body has front facing negative Y.
    yfront=min(p.y for p in torso)
    yback=max(p.y for p in torso)
    frontlimit=yfront+.57*(yback-yfront)
    garment=ob.copy()
    garment.data=ob.data.copy()
    garment.name="NEX_V1_TAILORED_JACKET_V5_"+gender.upper()
    garment.data.name=garment.name+"_source-derived-rigged-mesh"
    bpy.context.scene.collection.objects.link(garment)
    # Keep source legibility and deformation weights. Remove lower skirt/trouser
    # geometry while keeping source sleeves, sides and full back.
    bm=bmesh.new(); bm.from_mesh(garment.data)
    bad=[]
    for face in bm.faces:
        p=origin @ face.calc_center_median()
        remove=(p.z<conf["low"] or p.z>conf["high"])
        if not remove and p.y<frontlimit and abs(p.x-cx)<.14:
            t=max(0,min(1,(p.z-conf["low"])/(conf["high"]-conf["low"])))
            # Deep center opening above chest; fitted front closure at waist.
            # The opening stays nonzero for the full height.
            open_width=.022+.105*(t**1.8)
            if abs(p.x-cx)<open_width:remove=True
        if remove: bad.append(face)
    if bad: bmesh.ops.delete(bm,geom=bad,context="FACES")
    lonely=[v for v in bm.verts if not v.link_faces]
    if lonely:bmesh.ops.delete(bm,geom=lonely,context="VERTS")
    retained_faces=len(bm.faces)
    if retained_faces<500:
        bm.free()
        bpy.data.objects.remove(garment,do_unlink=True)
        raise RuntimeError("Bad coat crop: insufficient rigged geometry")
    bm.to_mesh(garment.data);bm.free()
    garment.data.update()
    # Keep the shell outside the approved clothes using restrained separation.
    for v in garment.data.vertices:v.co += v.normal*.0062
    material=bpy.data.materials.new(garment.name+"_matte-woven-ink")
    material.diffuse_color=conf["fabric"]
    material.use_nodes=True
    nd=material.node_tree.nodes;nd.clear()
    out=nd.new("ShaderNodeOutputMaterial")
    sh=nd.new("ShaderNodeEmission")
    sh.inputs["Color"].default_value=conf["fabric"]
    sh.inputs["Strength"].default_value=0.9
    material.node_tree.links.new(sh.outputs[0],out.inputs["Surface"])
    garment.data.materials.clear();garment.data.materials.append(material)
    solid=garment.modifiers.new("NEX V5 jacket front and hem return","SOLIDIFY")
    solid.thickness=.0013
    solid.offset=-1.0
    solid.use_even_offset=False
    solid.use_rim=True
    # V5: a proper bound lapel strip, never polygons across the cutout.
    # The V4 diamonds were chiefly triangulation lines and points anchored
    # inside the deleted V-neck (i.e. onto the coat back or wrong surface).
    # These points lie OUTSIDE the actual width of the existing opening.
    bpy.context.view_layer.update()
    jacketpts=[garment.matrix_world @ v.co for v in garment.data.vertices]
    front_indices=[i for i,p in enumerate(jacketpts)
                   if p.y<frontlimit and 1.06<p.z<1.445 and abs(p.x-cx)<.205]
    if len(front_indices)<70:
        raise RuntimeError("INSUFFICIENT_TRUE_FRONT_JACKET_VERTICES")

    def opening(z):
        t=max(0,min(1,(z-conf["low"])/(conf["high"]-conf["low"])))
        return .022+.105*(t**1.8)

    trim_mat=bpy.data.materials.new(garment.name+"_rolled-lapel-cloth")
    trim_mat.diffuse_color=conf["trim"]
    trim_mat.use_nodes=True
    nodes=trim_mat.node_tree.nodes
    nodes.clear()
    output=nodes.new("ShaderNodeOutputMaterial")
    shader=nodes.new("ShaderNodeEmission")
    shader.inputs["Color"].default_value=conf["trim"]
    shader.inputs["Strength"].default_value=.91
    trim_mat.node_tree.links.new(shader.outputs[0],output.inputs["Surface"])
    ink=bpy.data.materials.get("V59_INK")
    if ink is None: raise RuntimeError("CANONICAL_INK_MISSING")

    def make_skin(boundary,faces,name,mat,wire=False):
        mesh=bpy.data.meshes.new(name+"_mesh")
        mesh.from_pydata([origin.inverted()@p for p,idx in boundary],[],faces)
        mesh.update()
        thing=bpy.data.objects.new(name,mesh)
        bpy.context.scene.collection.objects.link(thing)
        thing.parent=rig
        thing.matrix_world=origin.copy()
        mesh.materials.append(mat)
        for i,(p,src_idx) in enumerate(boundary):
            for g in garment.data.vertices[src_idx].groups:
                key=garment.vertex_groups[g.group].name
                group=thing.vertex_groups.get(key) or thing.vertex_groups.new(name=key)
                group.add([i],g.weight,'REPLACE')
        mod=thing.modifiers.new("Original armature, original weights","ARMATURE")
        mod.object=rig
        if wire:
            rim=thing.modifiers.new("Only the sewn perimeter, no triangulation","WIREFRAME")
            rim.thickness=.00082
            rim.use_replace=True
        else:
            shell=thing.modifiers.new("Bound textile turn","SOLIDIFY")
            shell.thickness=.00095
            shell.offset=-1.0
        thing["sourceRig"]=rig.name
        thing["sourceGarment"]=conf["name"]
        thing["jacketTest"]=True
        return thing

    sewn=[]
    for side in (-1,1):
        # Nearest existing fabric gives Y depth and the underlying skinning
        # weights. X/Z remain on the smooth pattern, instead of snapping to
        # irregular nearest mesh vertices.
        def anchor(dx,z):
            if dx < opening(z)+.008:
                raise RuntimeError("LAPEL_ANCHOR_WITHIN_OPEN_FRONT")
            desired=cx+side*dx
            nearest=min(front_indices,key=lambda i:
                ((jacketpts[i].x-desired)/.7)**2
                +(jacketpts[i].z-z)**2
                +.18*max(0,jacketpts[i].y-yfront))
            p=Vector((desired,jacketpts[nearest].y-.008,z))
            return (p,nearest)
        # Five graduated sections create a readable tapered roll. One polygon
        # per lapel means ink follows the OUTER perimeter only, no internal
        # triangle/diamond markings at the front of the coat.
        levels=[(1.155,.033),(1.221,.042),(1.295,.048),(1.361,.048),(1.415,.027)]
        inside=[]
        outside=[]
        for z,band in levels:
            inside.append(anchor(opening(z)+.015,z))
            outside.append(anchor(opening(z)+.015+band,z))
        boundary=inside+list(reversed(outside))
        face=[tuple(range(len(boundary)))]
        name="NEX_V5_NOTCHED_LAPEL_"+gender+("_L" if side<0 else "_R")
        obj=make_skin(boundary,face,name,trim_mat)
        sewn.append(obj.name)
        edge=make_skin(boundary,face,name+"_perimeter_ink",ink,wire=True)
        sewn.append(edge.name)

        # Two independent welt edges formed on existing jacket surface, with
        # small profile; no invented buttons or new copyright-unclear assets.
        welt=[anchor(.080,1.095),anchor(.145,1.095),
              anchor(.145,1.087),anchor(.080,1.087)]
        obj=make_skin(welt,[(0,1,2,3)],
              "NEX_V5_WELT_"+gender+("_L" if side<0 else "_R"),trim_mat)
        sewn.append(obj.name)
    garment["sourceGarment"]=conf["name"]
    garment["experimentalFamily"]="V1"
    garment["approved"]=False
    record={
        "gender":gender,"source":conf["name"],"coat":garment.name,
        "coat_faces":retained_faces,"source_unchanged":True,
        "source_visible":not ob.hide_render,
        "armature_modifiers":sum(m.type=="ARMATURE" for m in garment.modifiers),
        "new_lapel_objects":sewn,
        "anchoring":"gap-aware continuous XZ contour, local source front Y, original weights",
        "status":"UNAPPROVED_V5_NO_TRIANGLE_FACE_RIM_GESTURE_QA_PENDING",
        "source_license":"MakeHuman garment, retain source credits"
    }
    print("JACKET_V5_LAPEL_BUILT",json.dumps(record),flush=True)
    return record
