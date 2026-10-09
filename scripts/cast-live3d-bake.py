"""Freeze an assembled Cast scene at the preview frame and export its browser parts.

Each visible mesh keeps its final Blender colour as per-corner colours. Native
fibre hair, Freestyle-marked edges and the lip mask travel as side files."""
import bpy,sys,os,json
argv=sys.argv[sys.argv.index('--')+1:];outdir=argv[0];frame=int(argv[1]) if len(argv)>1 else 27
KEYS=json.loads(os.environ['PART_KEYS']);LINES_ONLY=os.environ.get('LINES_ONLY')=='1';HAIR_ONLY=os.environ.get('HAIR_ONLY')=='1';ONLY=set(os.environ.get('BAKE_GROUPS','').split(','))-{''}
GARMENTS={x.split('=')[0] for x in os.environ.get('CAST_GARMENTS','').split(',') if x}|({os.environ['CAST_DRESS']} if os.environ.get('CAST_DRESS') else set())
def group(n):
    n=n.removeprefix('L3D_')
    if n.startswith('Host.watch_') or n.startswith('V17_W_'):return 'watch'
    if n.startswith('Host.V62_') or 'neck_chain' in n or n.startswith('Host.V17_NECK'):return 'neck'
    if n.startswith('Host.V17_ear'):return 'earring'
    if n.startswith('Host.hair_'):return 'hair'
    base=n.removeprefix('Host.').split('.preview-fit')[0].rsplit('.',1)[0] if n.removeprefix('Host.').count('.')  else n.removeprefix('Host.')
    if 'dress_lines' in n or n.startswith('Host.V63_') or n.startswith('Host.V70_G_') or any(n.removeprefix('Host.').startswith(g) for g in GARMENTS):return 'garment'
    return 'body'
out=os.path.join(outdir,'_all.glb')
s=bpy.context.scene;s.frame_set(frame)
s.render.engine='CYCLES';s.cycles.samples=int(os.environ.get('BAKE_SAMPLES','16'));s.cycles.device='CPU'
for o in s.objects:
    for m in o.modifiers:
        if m.type=='SUBSURF':m.levels=m.render_levels
dg=bpy.context.evaluated_depsgraph_get()
src=[o for o in s.objects if o.type=='MESH' and not o.hide_render and o.visible_get()]
coll=bpy.data.collections.new('LIVE3D');s.collection.children.link(coll)
copies=[]
for o in src:
    me=bpy.data.meshes.new_from_object(o.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg)
    c=bpy.data.objects.new('L3D_'+o.name,me);c.matrix_world=o.matrix_world.copy();coll.objects.link(c)
    for i,sl in enumerate(o.material_slots):
        if i<len(me.materials):me.materials[i]=sl.material
    copies.append((o,c))
for o in s.objects:
    if o.type in('MESH','CURVES') and not o.name.startswith('L3D_'):o.hide_render=True
report=[]
for o,c in copies:
    if ONLY and group(c.name) not in ONLY:continue
    me=c.data
    # drop faces whose material is fully transparent
    import bmesh
    bm=bmesh.new();bm.from_mesh(me)
    bad={i for i,m in enumerate(me.materials) if m and m.node_tree and any(n.type=='BSDF_TRANSPARENT' for n in m.node_tree.nodes) and not any(n.type in('EMISSION','BSDF_PRINCIPLED') for n in m.node_tree.nodes)}
    if bad:
        bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index in bad],context='FACES')
    bm.to_mesh(me);bm.free()
    if not me.polygons:continue
    ca=me.color_attributes.new('Col','BYTE_COLOR','CORNER');me.color_attributes.active_color=ca
    bpy.ops.object.select_all(action='DESELECT');c.select_set(True);bpy.context.view_layer.objects.active=c
    lit=any(m and m.node_tree and any(n.type in('BSDF_PRINCIPLED','BSDF_HAIR_PRINCIPLED','BSDF_DIFFUSE') for n in m.node_tree.nodes) for m in me.materials)
    s.cycles.samples=int(os.environ.get('BAKE_SAMPLES','16'))*(8 if lit else 1)
    if not LINES_ONLY:bpy.ops.object.bake(type='COMBINED' if lit else 'EMIT',target='VERTEX_COLORS')
    report.append((c.name,len(me.vertices),len(me.polygons)))
print('BAKED',json.dumps(report))
import numpy as np,struct,bmesh
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
refpath=os.environ.get('REF_PNG')
fib=[] if (LINES_ONLY and not HAIR_ONLY) or (ONLY and 'hair' not in ONLY) else [o for o in s.objects if o.type=='CURVES' and o.visible_get()]
if fib and refpath:
    im=bpy.data.images.load(refpath);iw,ih=im.size;px=np.array(im.pixels[:],dtype=np.float32).reshape(ih,iw,4)
    e=fib[0].evaluated_get(dg).data;mw=fib[0].matrix_world
    pos=np.empty(len(e.points)*3,dtype=np.float32);e.attributes['position'].data.foreach_get('vector',pos);pos=pos.reshape(-1,3)
    pos=(np.c_[pos,np.ones(len(pos))]@np.array(mw).T)[:,:3].astype(np.float32)
    off=np.empty(len(e.curves)+1,dtype=np.int32);e.curve_offset_data.foreach_get('value',off)
    cam=s.camera;cx,cz=cam.location.x,cam.location.z;sc=cam.data.ortho_scale;ar=s.render.resolution_x/s.render.resolution_y
    u=(pos[:,0]-cx)/(sc*ar)+.5;v=(pos[:,2]-cz)/sc+.5
    xi=np.clip((u*iw).astype(int),0,iw-1);yi=np.clip((v*ih).astype(int),0,ih-1)
    col=px[yi,xi,:3]  # linear
    from mathutils.bvhtree import BVHTree
    vs,fs_=[],[]
    for o_,c_ in copies:
        if group(c_.name)=='hair' or o_.pass_index==11:continue
        k=len(vs);mw_=c_.matrix_world;vs+= [mw_@v.co for v in c_.data.vertices];fs_+=[[k+i for i in f.vertices] for f in c_.data.polygons]
    tree=BVHTree.FromPolygons(vs,fs_);back=-(s.camera.matrix_world.to_3x3()@Vector((0,0,-1))).normalized()
    seen=px[yi,xi,3]>.5
    for i in np.flatnonzero(seen):
        if tree.ray_cast(Vector(pos[i])+back*2e-4,back)[0] is not None:seen[i]=False
    if seen.any():
        fallback=np.median(col[seen],axis=0)
        for a_,b_ in zip(off[:-1],off[1:]):
            ok=np.flatnonzero(seen[a_:b_])
            if len(ok)==b_-a_:continue
            if not len(ok):col[a_:b_]=fallback;continue
            idx=np.arange(b_-a_);near=ok[np.clip(np.searchsorted(ok,idx),0,len(ok)-1)]
            prev=ok[np.clip(np.searchsorted(ok,idx)-1,0,len(ok)-1)];near=np.where(np.abs(prev-idx)<np.abs(near-idx),prev,near)
            col[a_:b_]=col[a_+near]
    print('HAIR_SEEN',int(seen.sum()),len(seen))
    keep=np.ones(len(e.curves),bool)
    os.makedirs(f"{outdir}/hair",exist_ok=True)
    with open(f"{outdir}/hair/{KEYS['hair']}.hair.bin",'wb') as f:
        f.write(struct.pack('<II',len(pos),len(off)));f.write(pos.tobytes());f.write(off.tobytes());f.write((np.clip(col,0,1)*255).astype(np.uint8).tobytes())
    print('HAIR',len(pos),len(off)-1)
if HAIR_ONLY:sys.exit(0)
segs={}
fs=s.view_layers[0].freestyle_settings
from mathutils import Matrix,Vector
VIEW=(s.camera.matrix_world.to_3x3()@Vector((0,0,-1))).normalized()
def in_ls(ls,orig):
    if not ls.show_render:return False
    if ls.select_by_collection and ls.collection:
        inside=orig.name in ls.collection.all_objects
        if inside==(ls.collection_negation=='EXCLUSIVE'):return False
    return True
for o,c in copies:
    me=c.data;mw=c.matrix_world
    if not me.polygons:continue
    want_border=[ls for ls in fs.linesets if ls.select_border and in_ls(ls,o)]
    want_mark=[ls for ls in fs.linesets if ls.select_edge_mark and in_ls(ls,o)]
    want_contour=[ls for ls in fs.linesets if (ls.select_silhouette or ls.select_contour) and in_ls(ls,o)]
    if not(want_border or want_mark or want_contour):continue
    bm=bmesh.new();bm.from_mesh(me);bm.edges.ensure_lookup_table();bm.transform(mw);bm.normal_update();mw=Matrix()
    fe=me.attributes.get('freestyle_edge')
    for e in bm.edges:
        ls=None
        if want_border and e.is_boundary:ls=want_border[0]
        elif want_mark and fe and fe.data[e.index].value:ls=want_mark[0]
        elif want_contour and len(e.link_faces)==2 and (e.link_faces[0].normal.dot(VIEW)>0)!=(e.link_faces[1].normal.dot(VIEW)>0):ls=want_contour[0]
        if ls is None:continue
        a=mw@e.verts[0].co;b=mw@e.verts[1].co;col=ls.linestyle.color
        segs.setdefault(group(c.name),[]).append((a.x,a.y,a.z,b.x,b.y,b.z,col[0],col[1],col[2],ls.linestyle.thickness))
    bm.free()
for g,v in segs.items():
    if KEYS.get(g):os.makedirs(f'{outdir}/{g}',exist_ok=True);np.array(v,dtype=np.float32).tofile(f'{outdir}/{g}/{KEYS[g]}.lines.raw.bin')
    if KEYS.get(g):open(f'{outdir}/{g}/{KEYS[g]}.lines.job','w').write(os.environ.get('JOB_ID','x'))
print('LINES',{g:len(v) for g,v in segs.items()},{ls.name:(ls.collection_negation if ls.collection else None) for ls in fs.linesets})
ink={}
for o,c in copies:
    if o.pass_index in (1,2,3):ink.setdefault(group(c.name),{})[c.name]=o.pass_index
for g,v in ink.items():
    if KEYS.get(g):os.makedirs(f'{outdir}/{g}',exist_ok=True);json.dump(v,open(f'{outdir}/{g}/{KEYS[g]}.ink.json','w'))
if LINES_ONLY:sys.exit(0)
# swap to plain vertex-colour materials for export
flat=bpy.data.materials.new('L3D_vcol');flat.use_nodes=True
nt=flat.node_tree;b=nt.nodes['Principled BSDF'];a=nt.nodes.new('ShaderNodeVertexColor');a.layer_name='Col';nt.links.new(a.outputs['Color'],b.inputs['Base Color'])
for o,c in copies:
    c.data.materials.clear();c.data.materials.append(flat)
    if 'lipmask' in c.data.attributes and c.data.attributes['lipmask'].domain=='POINT' and c.data.attributes['lipmask'].data_type=='FLOAT':
        lm=c.data.attributes.new('_LIPMASK','FLOAT','POINT');v=np.empty(len(c.data.vertices),np.float32);c.data.attributes['lipmask'].data.foreach_get('value',v);lm.data.foreach_set('value',v)
    for k in [k for k in c.data.attributes.keys() if k not in('position','Col','sharp_face','_LIPMASK') and not k.startswith('.')]:
        try:c.data.attributes.remove(c.data.attributes[k])
        except Exception:pass
cam=s.camera
print('CAMERA',json.dumps({'loc':list(cam.matrix_world.translation),'rot':list(cam.rotation_euler),'ortho':cam.data.ortho_scale,'res':[s.render.resolution_x,s.render.resolution_y]}))
groups={}
for o,c in copies:
    if c.data.polygons:groups.setdefault(group(c.name),[]).append(c)
meta={}
for g,objs in groups.items():
    if not KEYS.get(g):print('SKIP_GROUP',g,[c.name for c in objs]);continue
    os.makedirs(f'{outdir}/{g}',exist_ok=True);path=f'{outdir}/{g}/{KEYS[g]}.glb'
    bpy.ops.object.select_all(action='DESELECT')
    for c in objs:c.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path,export_format='GLB',use_selection=True,export_apply=True,export_vertex_color='ACTIVE',export_normals=True,export_materials='EXPORT',export_attributes=True)
    meta[g]={'key':KEYS[g],'objects':[c.name for c in objs],'bytes':os.path.getsize(path)}
    print('EXPORTED',path,os.path.getsize(path))
json.dump({'keys':KEYS,'groups':meta,'env':{k:os.environ.get(k,'') for k in ('CAST_SKIN_HEX','CAST_HAIR_HEX','CAST_LIP_HEX','CAST_DRESS','CAST_DRESS_HEX','CAST_GARMENTS')}},open(f"{outdir}/meta-{os.environ.get('JOB_ID','x')}.json",'w'),indent=1)
