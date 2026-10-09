"""Fit original CC0 Toigo ballet flats onto the V1 female Host rig in a disposable scene."""
import bpy, sys, json
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index("--")+1:]
gender,render_path,suit_src,shoe_src=args[:4]
if gender!="female":
    # Reuse the original rigged V1 male footwear asset instead of leaving the
    # suit donor's leg hems with no finished footwear. Read-only canonical;
    # these visibility changes apply exclusively to the disposable proof.
    obj=bpy.data.objects.get("Host.mindfront_shoes_monk_strap_male")
    rig=bpy.data.objects.get("Host.rig")
    if obj is None or rig is None:
        raise RuntimeError("CANONICAL_MALE_MONK_STRAP_SHOES_MISSING")
    if not any(m.type=="ARMATURE" and m.object==rig for m in obj.modifiers):
        raise RuntimeError("CANONICAL_MALE_SHOES_NOT_BOUND_TO_ORIGINAL_RIG")
    obj.hide_render=False
    obj.hide_viewport=False
    for name in ("Host.lineart_shoe.L","Host.lineart_shoe.R"):
        proxy=bpy.data.objects.get(name)
        if proxy:proxy.hide_render=True
    out=Path(render_path).resolve()
    bpy.ops.wm.save_as_mainfile(filepath=str(out.with_suffix(".blend")),copy=True,compress=True)
    report={"asset":"Host.mindfront_shoes_monk_strap_male","gender":gender,
            "source":"pre-existing approved V1 male footwear",
            "sourceRigUnchanged":True,
            "status":"UNAPPROVED_MALE_ORIGINAL_SHOE_REUSE_TRIAL"}
    out.with_name(out.stem+"-shoes.json").write_text(json.dumps(report,indent=2))
    print("V1_MALE_EXISTING_MONK_SHOES_RESTORED",json.dumps(report),flush=True)
else:
    src=Path(shoe_src).resolve()
    assert src.is_file(), "CC0 shoes MHClO missing"
    header="\n".join(src.read_text(errors="replace").splitlines()[:24]).lower()
    assert "license cc0" in header, "Unverified shoe license"
    repo=Path(__file__).resolve().parents[2]
    sys.path.insert(0,str(repo/"engine_sources/makehuman-lineart/scripts"))
    import mhclo_fit as F
    scene=bpy.context.scene
    rig=bpy.data.objects["Host.rig"]
    body=bpy.data.objects["Host.body"]
    rig.data.pose_position="REST"
    scene.frame_set(27)
    bpy.context.view_layer.update()
    coords,refs=F.fit(str(src),F.shaped_coords(body))
    _,_,objp=F.load_mhclo(str(src))
    obj_vertices,faces=F.load_obj(objp)
    assert len(coords)==len(obj_vertices) and len(coords)>100
    basis=body.matrix_world.copy()
    mesh=bpy.data.meshes.new("NEX_V1_CC0_BALLET_FLATS_FEMALE_MESH")
    inv=basis.inverted()
    mesh.from_pydata([inv@p for p in coords],[],faces)
    # Preserve source OBJ texture coordinates for the shoe illustration.
    raw_uv=[]
    face_uv=[]
    for line in open(objp,encoding="utf8",errors="replace"):
        if line.startswith("vt "):
            p=line.split();raw_uv.append((float(p[1]),float(p[2])))
        elif line.startswith("f "):
            row=[]
            for item in line.split()[1:]:
                bits=item.split("/")
                row.append(int(bits[1])-1 if len(bits)>1 and bits[1] else None)
            face_uv.append(row)
    if len(face_uv)==len(mesh.polygons) and raw_uv and all(
        k is not None and 0<=k<len(raw_uv) for row in face_uv for k in row):
        uv=mesh.uv_layers.new(name="Original flat footwear UV")
        for face,row in zip(mesh.polygons,face_uv):
            for loop,k in zip(face.loop_indices,row):uv.data[loop].uv=raw_uv[k]
    mesh.update()
    for p in mesh.polygons:p.use_smooth=True
    shoe=bpy.data.objects.new("NEX_CC0_FEMALE_BALLET_FLATS",mesh)
    scene.collection.objects.link(shoe)
    shoe.parent=rig
    shoe.matrix_world=basis.copy()
    deform={b.name for b in rig.data.bones if b.use_deform}
    gname={g.index:g.name for g in body.vertex_groups if g.name in deform}
    used={i for ids,ws,ofs in refs for i in ids}
    bw={i:[(gname[w.group],w.weight) for w in body.data.vertices[i].groups if w.group in gname] for i in used}
    weights={}
    for vi,(ids,ws,offset) in enumerate(refs):
        total={}
        for i,w in zip(ids,ws):
            for name,weight in bw[i]:total[name]=total.get(name,0.0)+weight*w
        norm=sum(total.values()) or 1
        for k,v in total.items():
            if v>1e-5:weights.setdefault(k,[]).append((vi,v/norm))
    for name,rows in weights.items():
        vg=shoe.vertex_groups.new(name=name)
        for vi,w in rows:vg.add([vi],w,"REPLACE")
    arm=shoe.modifiers.new("Original V1 Host Rig","ARMATURE")
    arm.object=rig
    mhmat=next(src.parent.glob("*.mhmat"),None)
    image=None
    if mhmat:
        for row in mhmat.read_text(errors="replace").splitlines():
            x=row.split()
            if len(x)>1 and x[0]=="diffuseTexture":
                p=src.parent/x[1]
                if p.is_file():
                    image=bpy.data.images.load(str(p),check_existing=True)
                    image.pack()
                break
    mat=bpy.data.materials.new("NEX_CC0_FEMALE_BALLET_FLATS_ORIGINAL")
    mat.use_nodes=True
    nodes=mat.node_tree.nodes
    nodes.clear()
    end=nodes.new("ShaderNodeOutputMaterial")
    em=nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value=.75
    if image and mesh.uv_layers:
        uv=nodes.new("ShaderNodeUVMap")
        uv.uv_map=mesh.uv_layers.active.name
        tex=nodes.new("ShaderNodeTexImage")
        tex.image=image
        mat.node_tree.links.new(uv.outputs["UV"],tex.inputs["Vector"])
        mat.node_tree.links.new(tex.outputs["Color"],em.inputs["Color"])
    else:em.inputs["Color"].default_value=(.035,.024,.02,1)
    mat.node_tree.links.new(em.outputs[0],end.inputs["Surface"])
    mesh.materials.append(mat)
    hidden=[]
    for name in ("Host.lineart_shoe.L","Host.lineart_shoe.R"):
        o=bpy.data.objects.get(name)
        if o:o.hide_render=True;hidden.append(name)
    rig.data.pose_position="POSE"
    scene.frame_set(27)
    bpy.context.view_layer.update()
    shoe["approved"]=False
    shoe["sourceAsset"]="toigo_ballet_flats"
    shoe["sourceLicense"]="CC0"
    report={"asset":"toigo_ballet_flats","license":"CC0",
            "fittedVertices":len(mesh.vertices),"faces":len(mesh.polygons),
            "deformGroups":len(weights),"visibleOriginalShoesHiddenOnlyInTestScene":hidden,
            "sourceRigUnchanged":True,"status":"UNAPPROVED_SHOE_FIT_TRIAL"}
    out=Path(render_path).resolve()
    # Update ONLY the disposable proof scene; never the canonical source .blend.
    bpy.ops.wm.save_as_mainfile(filepath=str(out.with_suffix(".blend")),copy=True,compress=True)
    out.with_name(out.stem+"-shoes.json").write_text(json.dumps(report,indent=2))
    print("REAL_CC0_FEMALE_SHOE_FIT_OK",json.dumps(report),flush=True)
