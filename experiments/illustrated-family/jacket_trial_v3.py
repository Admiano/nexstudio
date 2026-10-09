"""NexStudio V1 illustrated tailored jacket V3 LAPEL STUDY (ISOLATED UNAPPROVED geometry proof).

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
        "female": {"name": "Host.mindfront_f_dress_11","low":1.048,
                   "high":1.485,"fabric":(0.46,0.25,0.22,1),
                   "trim":(0.59,0.37,0.31,1)},
        "male": {"name": "Host.elvs_male_shirt_untucked_bd1","low":1.047,
                 "high":1.485,"fabric":(0.16,0.21,0.31,1),
                 "trim":(0.27,0.33,0.44,1)}
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
    garment.name="NEX_V1_TAILORED_JACKET_V3_"+gender.upper()
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
            open_width=.018+.105*(t**2.4)
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
    solid=garment.modifiers.new("NEX V3 jacket front and hem return","SOLIDIFY")
    solid.thickness=.0013
    solid.offset=-1.0
    solid.use_even_offset=False
    solid.use_rim=True
    # Minimal lapel prototypes, geometrically over the jacket FRONT; each
    # vertex weights to an actual nearby garment vertex for skeletal reuse.
    bpy.context.view_layer.update()
    jacketpts=[garment.matrix_world @ v.co for v in garment.data.vertices]
    tree=KDTree(len(jacketpts))
    for i,p in enumerate(jacketpts):tree.insert(p,i)
    tree.balance()
    outline={}
    trim_mat=bpy.data.materials.new(garment.name+"_contrasting-tailored-lapel")
    trim_mat.diffuse_color=conf["trim"]
    trim_mat.use_nodes=True
    tr=trim_mat.node_tree.nodes
    tr.clear()
    op=tr.new("ShaderNodeOutputMaterial")
    em=tr.new("ShaderNodeEmission")
    em.inputs["Color"].default_value=conf["trim"]
    em.inputs["Strength"].default_value=.95
    trim_mat.node_tree.links.new(em.outputs[0],op.inputs["Surface"])
    ink=bpy.data.materials.get("V59_INK")
    if ink is None:raise RuntimeError("Source V59_INK line art material unavailable")
    lapels=[]
    for sign in (-1,1):
        # Locate true jacket surface points at desired *relative* torso coords.
        # Search among front torso vertices and choose closest in (X,Z).
        front_indices=[i for i,p in enumerate(jacketpts) if p.y<frontlimit and p.z>1.16 and abs(p.x-cx)<.20]
        if len(front_indices)<30:continue
        def anchor(dx,z):
            x=cx+sign*dx
            idx=min(front_indices,key=lambda i:((jacketpts[i].x-x)/.7)**2+
                                             (jacketpts[i].z-z)**2+
                                             (jacketpts[i].y-yfront)*.12)
            return jacketpts[idx]-Vector((0,.003,0)),idx
        corners=[anchor(.025,1.17),anchor(.058,1.345),anchor(.12,1.420),anchor(.114,1.315)]
        # No destructive work to the source. Lapel is a skinned 3D fabric
        # polygon oriented on the actual source coat instead of a screen decal.
        mesh=bpy.data.meshes.new("NEX_JACKET_LAPEL_"+gender+str(sign))
        mesh.from_pydata([origin.inverted()@p for p,_ in corners],[],[(0,1,2),(0,2,3)])
        mesh.update()
        lp=bpy.data.objects.new(mesh.name,mesh)
        bpy.context.scene.collection.objects.link(lp)
        lp.parent=rig
        lp.matrix_world=origin.copy()
        mesh.materials.append(trim_mat)
        for j,(_,src_idx) in enumerate(corners):
            # Need vertex-group transfer by actual nearest selected source vertex
            orig=garment.data.vertices[src_idx]
            for g in orig.groups:
                key=garment.vertex_groups[g.group].name
                target=lp.vertex_groups.get(key) or lp.vertex_groups.new(name=key)
                target.add([j],g.weight,"REPLACE")
        a=lp.modifiers.new("Same Host rig","ARMATURE");a.object=rig
        edges=lp.modifiers.new("Lapel fabric return","SOLIDIFY");edges.thickness=.0011
        # The original lapel is a skinned geometry surface. Its perimeter ink
        # must be skinned to the same rig (not bone-parented to the head).
        border=lp.copy()
        border.data=lp.data.copy()
        border.name=lp.name+"_authored-ink-edge"
        border.data.name=border.name+"_mesh"
        bpy.context.scene.collection.objects.link(border)
        border.data.materials.clear()
        border.data.materials.append(ink)
        for modifier in list(border.modifiers):
            if modifier.type=="SOLIDIFY":border.modifiers.remove(modifier)
        frame=border.modifiers.new("Ink around tailored lapel","WIREFRAME")
        frame.thickness=.00125
        frame.use_replace=True
        lapels.append(lp.name)
        lapels.append(border.name)
    garment["sourceGarment"]=conf["name"]
    garment["experimentalFamily"]="V1"
    garment["approved"]=False
    record={
        "gender":gender,"source":conf["name"],"coat":garment.name,
        "coat_faces":retained_faces,"source_unchanged":True,
        "source_visible":not ob.hide_render,
        "armature_modifiers":sum(m.type=="ARMATURE" for m in garment.modifiers),
        "new_lapel_objects":lapels,
        "status":"UNAPPROVED_V3_LAPEL_CONTRAST_REQUIRES_RENDER_FIT_DEFORMATION_QA",
        "source_license":"MakeHuman garment, retain source credits"
    }
    print("JACKET_V3_LAPEL_BUILT",json.dumps(record),flush=True)
    return record
