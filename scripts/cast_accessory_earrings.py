"""Finish the five existing earring silhouettes at their saved lobe mounts."""
import math
import bpy,bmesh
from mathutils import Vector,Matrix
from cast_accessory_finish import finish_material,make_tube

def apply_earrings(style):
    rig=bpy.data.objects['Host.rig'];body=bpy.data.objects['Host.body'];collection=body.users_collection[0]
    gold=finish_material('V17_EARRING_GOLD','CBA654','metal');pearl=finish_material('V17_EARRING_PEARL','EFE7D6','pearl')
    old=[o for o in bpy.data.objects if o.name.startswith(('Host.V60_earring','Host.V61_ear_'))]
    mounts={}
    for side in ['L','R']:
        ob=bpy.data.objects.get('Host.V60_earring_'+side)
        if ob is None:
            ob=next((o for o in old if o.name.endswith('_'+side) and o.name.startswith('Host.V61_ear_post')),None)
        if ob is None:
            ob=next((o for o in old if o.name.endswith('_'+side) and o.name.startswith('Host.V61_ear_pearl') and not any(k in o.name for k in ('rim','hi'))),None)
        if ob is None:raise RuntimeError('ACCESSORY_EARRING_MOUNT_MISSING: '+side)
        coords=[ob.matrix_world@v.co for v in ob.data.vertices]
        top=max(v.z for v in coords);near=[v for v in coords if v.z>top-.0013]
        mounts[side]=sum(near,Vector())/len(near)
    for ob in old:ob.hide_render=True
    created=[]
    def parent(ob):
        mw=ob.matrix_world.copy();ob.parent=rig;ob.parent_type='BONE';ob.parent_bone='head';bpy.context.view_layer.update();ob.matrix_world=mw;created.append(ob);return ob
    def tube(name,P,r,material=gold,closed=False):return parent(make_tube(name,P,r,material,closed,collection,sides=16))
    def sphere(name,center,size,material=gold):
        bm=bmesh.new();bmesh.ops.create_uvsphere(bm,u_segments=48,v_segments=24,radius=1)
        for v in bm.verts:v.co=Vector(center)+Vector((v.co.x*size[0],v.co.y*size[1],v.co.z*size[2]))
        mesh=bpy.data.meshes.new(name);bm.to_mesh(mesh);bm.free();mesh.materials.append(material)
        for p in mesh.polygons:p.use_smooth=True
        ob=bpy.data.objects.new(name,mesh);collection.objects.link(ob);return parent(ob)
    for side,mount in mounts.items():
        suffix='_'+side;mount.y-=.0006
        sphere('Host.V17_ear_post'+suffix,mount,(.0013,.0010,.0013))
        if style in ('hoop','statement'):
            radius=.0105 if style=='hoop' else .0135;thickness=.00065 if style=='hoop' else .0009
            center=mount+Vector((0,0,-radius))
            outward=1 if mount.x>-.42 else -1
            P=[center+Vector((math.sin(q)*radius+outward*.003*(1-math.cos(q)),0,math.cos(q)*radius)) for q in [i*2*math.pi/128 for i in range(128)]]
            tube('Host.V17_ear_hoop'+suffix,P,thickness,closed=True)
            # A discrete clasp gives the closed hoop a believable lobe attachment.
            sphere('Host.V17_ear_clasp'+suffix,mount+Vector((.0008,0,-.0013)),(.0008,.0010,.0015))
        elif style=='bar':
            end=mount+Vector((0,0,-.024))
            tube('Host.V17_ear_bar'+suffix,[mount,end],.00125)
            sphere('Host.V17_ear_bar_tip'+suffix,end,(.00125,.00125,.00125))
        elif style=='stud':
            sphere('Host.V17_ear_setting'+suffix,mount,(.0037,.0021,.0037))
            sphere('Host.V17_ear_pearl'+suffix,mount+Vector((0,-.0017,0)),(.0035,.0034,.0035),pearl)
        elif style=='drop':
            end=mount+Vector((0,0,-.010))
            tube('Host.V17_ear_drop_link'+suffix,[mount,end],.00048)
            # A true tapered drop replaces the former stretched sphere.
            center=end+Vector((0,0,-.0065));verts=[];faces=[];segments=48;rows=32
            for j in range(rows+1):
                t=math.pi*j/rows;z=math.cos(t)*.0068;r=math.sin(t)*.0043*(.52+.48*j/rows)
                for i in range(segments):
                    q=2*math.pi*i/segments;verts.append(center+Vector((math.cos(q)*r,math.sin(q)*r*.45,z)))
            for j in range(rows):
                for i in range(segments):faces.append((j*segments+i,j*segments+(i+1)%segments,(j+1)*segments+(i+1)%segments,(j+1)*segments+i))
            mesh=bpy.data.meshes.new('V17 true teardrop');mesh.from_pydata(verts,[],faces);mesh.materials.append(gold)
            for p in mesh.polygons:p.use_smooth=True
            ob=bpy.data.objects.new('Host.V17_ear_drop'+suffix,mesh);collection.objects.link(ob);parent(ob)
    return {'style':style,'mounts':{s:list(v) for s,v in mounts.items()},'objects':[o.name for o in created]}
