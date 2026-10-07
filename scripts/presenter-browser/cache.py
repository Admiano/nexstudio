"""Bake an animated Cast presenter into a browser point cache.
blender animated.blend --python cache.py -- OUT F0 FIRST LAST REF.png
Colours and line selection are baked once at F0; per-frame world positions of every mesh vertex
(after posed-clothing fit, shape keys and armature) are written per frame; hair is fitted rigidly per frame.
Meshes with a driven render visibility (teeth, blink lashes) are kept even if hidden at F0 and toggle per frame."""
import bpy,bmesh,sys,os,json,time,struct,numpy as np
from pathlib import Path
from mathutils import Vector
argv=sys.argv[sys.argv.index('--')+1:];OUT=Path(argv[0]);F0=int(argv[1]);FRAMES=list(range(int(argv[2]),int(argv[3])+1))
REF=argv[4] if len(argv)>4 else None
R=Path(__file__).resolve().parents[1];__file__=str(R/'cast-render-assembled.py')
exec(compile((R/'cast-fit-posed-clothing.py').read_text(),str(R/'cast-fit-posed-clothing.py'),'exec'),globals())
OUT.mkdir(parents=True,exist_ok=True);(OUT/'frames').mkdir(exist_ok=True)
s=bpy.context.scene
for o in s.objects:
    for m in o.modifiers:
        if m.type=='SUBSURF':m.levels=m.render_levels
s.frame_set(F0);fit_posed_clothing(s);dg=bpy.context.evaluated_depsgraph_get()
driven={o.name for o in s.objects if o.animation_data and any(d.data_path=='hide_render' for d in o.animation_data.drivers)}
src=[o for o in s.objects if o.type=='MESH' and o.visible_get() and (not o.hide_render or o.name in driven)]
s.render.engine='CYCLES';s.cycles.device='CPU'
coll=bpy.data.collections.new('PCACHE');s.collection.children.link(coll);copies=[]
for o in src:
    me=bpy.data.meshes.new_from_object(o.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg)
    a=me.attributes.new('oidx','INT','POINT');a.data.foreach_set('value',np.arange(len(me.vertices),dtype=np.int32))
    c=bpy.data.objects.new('PC_'+o.name,me);c.matrix_world=o.matrix_world.copy();coll.objects.link(c)
    for i,sl in enumerate(o.material_slots):
        if i<len(me.materials):me.materials[i]=sl.material
    copies.append((o,c))
for o in s.objects:
    if o.type in('MESH','CURVES') and not o.name.startswith('PC_'):o.hide_render=True
t0=time.monotonic();objs=[]
for o,c in copies:
    me=c.data;bm=bmesh.new();bm.from_mesh(me)
    bad={i for i,m in enumerate(me.materials) if m and m.node_tree and any(n.type=='BSDF_TRANSPARENT' for n in m.node_tree.nodes) and not any(n.type in('EMISSION','BSDF_PRINCIPLED') for n in m.node_tree.nodes)}
    if bad:bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index in bad],context='FACES')
    bm.to_mesh(me);bm.free()
    if not me.polygons:continue
    ca=me.color_attributes.new('Col','BYTE_COLOR','CORNER');me.color_attributes.active_color=ca
    bpy.ops.object.select_all(action='DESELECT');c.select_set(True);bpy.context.view_layer.objects.active=c
    lit=any(m and m.node_tree and any(n.type in('BSDF_PRINCIPLED','BSDF_HAIR_PRINCIPLED','BSDF_DIFFUSE') for n in m.node_tree.nodes) for m in me.materials)
    s.cycles.samples=16*(8 if lit else 1)
    bpy.ops.object.bake(type='COMBINED' if lit else 'EMIT',target='VERTEX_COLORS')
    objs.append((o,c))
print('BAKE_S',round(time.monotonic()-t0,1),flush=True)
# lines at F0, as in cast-live3d-bake.py
fs=s.view_layers[0].freestyle_settings;VIEW=(s.camera.matrix_world.to_3x3()@Vector((0,0,-1))).normalized()
def in_ls(ls,orig):
    if not ls.show_render:return False
    if ls.select_by_collection and ls.collection:
        inside=orig.name in ls.collection.all_objects
        if inside==(ls.collection_negation=='EXCLUSIVE'):return False
    return True
order=[o for o,_ in objs];index={o.name:i for i,o in enumerate(order)}
segs=[]
cam=s.camera
meta={'objects':[],'frames':FRAMES,'f0':F0,'camera':{'x':cam.location.x,'z':cam.location.z,'scale':cam.data.ortho_scale,'aspect':s.render.resolution_x/s.render.resolution_y}}
for oi,(o,c) in enumerate(objs):
    me=c.data;mw=c.matrix_world;ox=np.empty(len(me.vertices),np.int32);me.attributes['oidx'].data.foreach_get('value',ox)
    me.calc_loop_triangles()
    lv=np.empty(len(me.loops),np.int32);me.loops.foreach_get('vertex_index',lv)
    tl=np.empty(len(me.loop_triangles)*3,np.int32);me.loop_triangles.foreach_get('loops',tl)
    col=np.empty(len(me.loops)*4,np.float32);me.color_attributes['Col'].data.foreach_get('color',col);col=col.reshape(-1,4)[:,:3]
    corner=ox[lv[tl]].astype(np.uint32);ccol=col[tl]
    name=o.name;base=f'obj{oi}'
    corner.tofile(OUT/f'{base}.idx');ccol.astype(np.float32).tofile(OUT/f'{base}.col')
    meta['objects'].append({'name':name,'verts':len(o.evaluated_get(dg).data.vertices) if False else None,'corners':len(corner),'ink':o.pass_index if o.pass_index in(1,2,3) else (1 if name.startswith('Host.hair_') else 0),'body':name.startswith(('Host.body','Host.V60_ear','Host.lineart_lower_legs','Host.high-poly','Host.eyebrow','Host.V59','Cast V12'))})
    want_border=[ls for ls in fs.linesets if ls.select_border and in_ls(ls,o)]
    want_mark=[ls for ls in fs.linesets if ls.select_edge_mark and in_ls(ls,o)]
    want_contour=[ls for ls in fs.linesets if (ls.select_silhouette or ls.select_contour) and in_ls(ls,o)]
    if not(want_border or want_mark or want_contour):continue
    bm=bmesh.new();bm.from_mesh(me);bm.edges.ensure_lookup_table();bm.transform(mw);bm.normal_update()
    fe=me.attributes.get('freestyle_edge');ol=bm.verts.layers.int.get('oidx')
    for e in bm.edges:
        ls=None
        if want_border and e.is_boundary:ls=want_border[0]
        elif want_mark and fe and fe.data[e.index].value:ls=want_mark[0]
        elif want_contour and len(e.link_faces)==2 and (e.link_faces[0].normal.dot(VIEW)>0)!=(e.link_faces[1].normal.dot(VIEW)>0):ls=want_contour[0]
        if ls is None:continue
        a,b=e.verts;cl=ls.linestyle.color
        segs.append((oi,a[ol],b[ol],a.co.x,a.co.y,a.co.z,b.co.x,b.co.y,b.co.z,cl[0],cl[1],cl[2]))
    bm.free()
np.array(segs,dtype=np.float64).tofile(OUT/'lines.raw.f64')
# per-frame positions
hair=[o for o in s.objects if o.type=='CURVES' and o.name.startswith('Cast V11')]
def world(o,co):m=np.array(o.matrix_world);return co@m[:3,:3].T+m[:3,3]
hb=None
if REF and hair:
    s.frame_set(F0);fit_posed_clothing(s);dg=bpy.context.evaluated_depsgraph_get()
    e=hair[0].evaluated_get(dg).data;hb=np.empty(len(e.points)*3,np.float32);e.attributes['position'].data.foreach_get('vector',hb);hb=world(hair[0],hb.reshape(-1,3)).astype(np.float32)
    off=np.empty(len(e.curves)+1,np.int32);e.curve_offset_data.foreach_get('value',off)
    im=bpy.data.images.load(REF);iw,ih=im.size;px=np.array(im.pixels[:],dtype=np.float32).reshape(ih,iw,4)
    cam=s.camera;sc=cam.data.ortho_scale;ar=s.render.resolution_x/s.render.resolution_y
    u=(hb[:,0]-cam.location.x)/(sc*ar)+.5;v=(hb[:,2]-cam.location.z)/sc+.5
    col=px[np.clip((v*ih).astype(int),0,ih-1),np.clip((u*iw).astype(int),0,iw-1),:3]
    with open(OUT/'hair.bin','wb') as fh:
        fh.write(struct.pack('<II',len(hb),len(off)));fh.write(hb.tobytes());fh.write(off.tobytes());fh.write((np.clip(col,0,1)*255).astype(np.uint8).tobytes())
pick=np.linspace(0,len(hb)-1,8000).astype(int) if hb is not None else None
offs=[];acc=0
for o in order:
    n=len(o.evaluated_get(dg).to_mesh().vertices);o.evaluated_get(dg).to_mesh_clear();offs.append((acc,n));acc+=n
for i,(a,n) in enumerate(offs):meta['objects'][i].update(offset=a,verts=n)
meta['totalVerts']=acc;meta['hair']=[]
t0=time.monotonic()
for f in FRAMES:
    s.frame_set(f);fit_posed_clothing(s);dg=bpy.context.evaluated_depsgraph_get();buf=np.zeros((acc,3),np.float32);vis=[]
    for i,o in enumerate(order):
        a,n=offs[i];ok=o.visible_get() and not(o.name in driven and o.hide_render);vis.append(ok)
        if not ok:continue
        me=o.evaluated_get(dg).to_mesh();p=np.empty(len(me.vertices)*3,np.float32);me.vertices.foreach_get('co',p);o.evaluated_get(dg).to_mesh_clear()
        if len(p)!=n*3:raise RuntimeError(f'TOPOLOGY {o.name} {f}')
        buf[a:a+n]=world(o,p.reshape(-1,3))
    buf.tofile(OUT/'frames'/f'{f:04}.bin')
    M=None
    if hb is not None and hair:
        e=hair[0].evaluated_get(dg).data;p=np.empty(len(e.points)*3,np.float32);e.attributes['position'].data.foreach_get('vector',p);p=world(hair[0],p.reshape(-1,3))
        X=hb[pick].astype(np.float64);Y=p[pick].astype(np.float64);mx,my=X.mean(0),Y.mean(0);U,S,Vt=np.linalg.svd((X-mx).T@(Y-my));D=np.diag([1,1,np.sign(np.linalg.det(Vt.T@U.T))]);Rm=Vt.T@D@U.T;T=my-Rm@mx
        M=[*Rm.ravel(),*T];meta.setdefault('hairErr',[]).append(float(np.abs((X-mx)@Rm.T+my-Y).max()))
    meta['hair'].append(M);meta.setdefault('visible',[]).append(vis)
print('FRAMES_S',round(time.monotonic()-t0,1),len(FRAMES),flush=True)
json.dump(meta,open(OUT/'meta.json','w'))
print('CACHE_DONE',acc,len(segs),flush=True)
