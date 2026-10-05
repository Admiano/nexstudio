"""Seat descriptors for a chair/sofa asset (.blend or .fbx), measured from the mesh.

blender -b --python scripts/cast_chair.py -- chairs.fbx out.json [--seat-height 0.45]

Each chair is found as an empty named like '*chair*'/'*sofa*'/'*seat*' that owns meshes
(or the whole file is one seat). Rays find the cushion top at the seat centre, the
backrest side (where the surface rises), the front edge and the inner width between
the arms. `scale` brings the cushion top to --seat-height (a standard seat is
0.43-0.48 m); placement code applies it uniformly about the floor point.
"""
import bpy,sys,json,re
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def _load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if path.lower().endswith('.fbx'):bpy.ops.import_scene.fbx(filepath=path)
    else:
        with bpy.data.libraries.load(path) as (src,dst):dst.objects=src.objects
        for o in dst.objects:
            if o:bpy.context.scene.collection.objects.link(o)

def _meshes(root):
    out=[];stack=[root]
    while stack:
        o=stack.pop();stack+=list(o.children)
        if o.type=='MESH':out.append(o)
    return out

def _tree(objs):
    d=bpy.context.evaluated_depsgraph_get();P=[];F=[]
    for o in objs:
        e=o.evaluated_get(d);me=e.to_mesh();b=len(P)
        P+=[o.matrix_world@v.co for v in me.vertices];F+=[[b+i for i in p.vertices] for p in me.polygons];e.to_mesh_clear()
    return BVHTree.FromPolygons(P,F),P

def describe(objs,name,seat_height):
    t,P=_tree(objs);lo=Vector([min(p[i] for p in P) for i in range(3)]);hi=Vector([max(p[i] for p in P) for i in range(3)]);c=(lo+hi)/2
    def top(x,y):
        h=t.ray_cast(Vector((x,y,hi.z+1)),Vector((0,0,-1)),hi.z-lo.z+2);return h[0].z if h[0] else None
    seat=top(c.x,c.y)
    if seat is None:return None
    # backrest: the horizontal direction in which the top surface rises furthest
    best=None
    for d in (Vector((0,1,0)),Vector((0,-1,0)),Vector((1,0,0)),Vector((-1,0,0))):
        span=abs((hi-lo).dot(d))/2;rise=max((top(*(c+d*span*f/10).xy) or seat)-seat for f in range(1,10))
        if best is None or rise>best[0]:best=(rise,d)
    back=best[1];front=-back;span=abs((hi-lo).dot(front))/2
    edge=max(f for f in range(0,11) if top(*(c+front*span*f/10).xy) is not None)*span/10
    side=Vector((-front.y,front.x,0));z=seat+0.05;width=0
    for s in (side,-side):
        h=t.ray_cast(Vector((c.x,c.y,z)),s,abs((hi-lo).dot(s)));width+=h[3] if h[0] else abs((hi-lo).dot(s))/2
    floor=lo.z;k=(seat_height/(seat-floor)) if seat_height else 1
    return {'name':name,'objects':[o.name for o in objs],'floor':[c.x,c.y,floor],'seatTop':seat-floor,'seatCentre':[c.x,c.y,seat],
            'facing':list(front),'frontEdge':edge,'innerWidth':width,'backRise':best[0],'scale':k,'scaledSeatTop':(seat-floor)*k,'scaledInnerWidth':width*k}

def _image_ok(im):
    import os
    return bool(im and (im.packed_file or os.path.exists(bpy.path.abspath(im.filepath))))

def place(src,desc,at,facing=(0,-1,0),seat_height=None,collide=False,name='castChair.seat'):
    """Bring one described seat into the open scene: cushion centre under `at` (x,y),
    turned to `facing`, uniformly scaled so the cushion top is `seat_height` above z=0."""
    import math
    before=set(bpy.data.objects)
    if src.lower().endswith('.fbx'):bpy.ops.import_scene.fbx(filepath=src)
    else:
        with bpy.data.libraries.load(src) as (a,b):b.objects=a.objects
        for o in b.objects:
            if o:bpy.context.scene.collection.objects.link(o)
    new=[o for o in bpy.data.objects if o not in before];keep=set()
    for n in desc['objects']:
        o=next((x for x in new if x.name==n or x.name.split('.')[0]==n),None)
        while o:keep.add(o);o=o.parent
    for o in new:
        if o not in keep:bpy.data.objects.remove(o)
    k=(seat_height/desc['seatTop']) if seat_height else desc.get('scale',1)
    root=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(root)
    root.location=Vector(desc['floor'])
    bpy.context.view_layer.update()
    for o in keep:
        if o.parent is None:mw=o.matrix_world.copy();o.parent=root;o.matrix_parent_inverse=root.matrix_world.inverted();o.matrix_world=mw
    f=Vector(desc['facing']);g=Vector(facing)
    root.rotation_euler=(0,0,math.atan2(g.y,g.x)-math.atan2(f.y,f.x));root.scale=(k,k,k);root.location=(at[0],at[1],0)
    mat=bpy.data.materials.get('chair') or bpy.data.materials.new('chair');mat.use_nodes=True
    mat.node_tree.nodes['Principled BSDF'].inputs[0].default_value=(.2,.2,.22,1)
    for o in keep:
        if o.type!='MESH':continue
        broken=[m for m in o.data.materials if m and m.use_nodes and any(n.type=='TEX_IMAGE' and not _image_ok(n.image) for n in m.node_tree.nodes)]
        if broken or not o.data.materials:o.data.materials.clear();o.data.materials.append(mat)
        if collide:o.modifiers.new('Collision','COLLISION');o.collision.thickness_outer=.01
    bpy.context.view_layer.update();return root,[o for o in keep if o.type=='MESH']

if __name__=='__main__':
    a=sys.argv[sys.argv.index('--')+1:];h=float(a[a.index('--seat-height')+1]) if '--seat-height' in a else 0.45
    _load(a[0])
    roots=[o for o in bpy.data.objects if re.search(r'chair|sofa|seat|bench|stool',o.name,re.I) and not (o.parent and re.search(r'chair|sofa|seat|bench|stool',o.parent.name,re.I))]
    groups=[(r.name,_meshes(r)) for r in roots] or [('seat',[o for o in bpy.data.objects if o.type=='MESH'])]
    out=[x for x in (describe(m,n,h) for n,m in groups if m) if x]
    json.dump({'source':a[0],'seats':out},open(a[1],'w'),indent=2);print('CHAIRS',json.dumps(out),flush=True)
