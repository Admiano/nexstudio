"""Isolated illustrated-strand linework trial on the REAL fitted CC0 bob.

Strokes are projected against the actual deforming hair mesh (not painted image).
Attach to original head bone only; canonical rig, source mesh and action unchanged.
"""
import bpy,math,sys,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

args=sys.argv[sys.argv.index("--")+1:]
gender,output=args[:2]
if gender!="female":raise RuntimeError("STRAND_TRIAL_ONLY_FEMALE_BOB")
out=Path(output).resolve();out.parent.mkdir(parents=True,exist_ok=True)
bpy.context.scene.frame_set(27)
bpy.context.view_layer.update()
rig=bpy.data.objects["Host.rig"]
hair=bpy.data.objects["NEX_V1_CC0_HAIR_toigo_blunt_bob_with_bangs"]
assert hair["approved"]==False and len(rig.data.bones)==163
deps=bpy.context.evaluated_depsgraph_get()
evaluated=hair.evaluated_get(deps)
mesh=evaluated.to_mesh()
points=[evaluated.matrix_world@v.co for v in mesh.vertices]
lo=Vector([min(p[i] for p in points) for i in range(3)])
hi=Vector([max(p[i] for p in points) for i in range(3)])
cx=(lo.x+hi.x)*.5
front=lo.y-.35
zmax=hi.z
zmin=lo.z
evaluated.to_mesh_clear()
tree=BVHTree.FromObject(hair,deps)
M=hair.matrix_world.copy()
inv=M.inverted()
origin=Vector((cx,front,zmax))
direction=inv.to_3x3()@Vector((0,1,0))
direction.normalize()
hitcount=0
misscount=0

def locate(x,z):
    global hitcount,misscount
    local=inv@Vector((x,front,z))
    pos,norm,face,dist=tree.ray_cast(local,direction,3)
    if pos is None:
        misscount+=1
        return None
    hitcount+=1
    wp=M@pos
    n=(M.to_3x3().inverted().transposed()@norm).normalized()
    return wp+n*.0014

mat=bpy.data.materials.new("NEX_CC0_BOB_AUTHORED_BROWN_STRANDS")
mat.diffuse_color=(.215,.112,.085,1)
mat.use_nodes=True
nodes=mat.node_tree.nodes
nodes.clear()
outnode=nodes.new("ShaderNodeOutputMaterial")
em=nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value=(.215,.112,.085,1)
em.inputs["Strength"].default_value=.8
mat.node_tree.links.new(em.outputs[0],outnode.inputs["Surface"])

created=[]
# Natural tapered flow-lines projected onto measured hair surface.
# Stagger line height and direction, avoiding the "evenly spaced ruler" look.
patterns=[
    (-.112,.075,.195,-.026),
    (-.086,.061,.167,-.013),
    (-.063,.067,.191,-.016),
    (-.037,.047,.174,-.008),
    (-.008,.058,.183,-.006),
    (.021,.069,.187,.008),
    (.050,.055,.170,.016),
    (.077,.073,.188,.014),
    (.100,.079,.205,.027),
]
for i,(dx,start_drop,end_drop,drift) in enumerate(patterns):
    path=[]
    for t in range(13):
        u=t/12
        z=zmax-start_drop-(end_drop-start_drop)*u+.002*math.sin(2.2*u+i*.5)
        side=-1 if dx<0 else 1
        x=cx+dx+drift*(u*u)+side*.009*math.sin(math.pi*u)+.0015*math.sin(4.5*u+i*.7)
        p=locate(x,z)
        if p is not None:path.append(p)
    if len(path)<8:continue
    cu=bpy.data.curves.new("V1_BOB_REAL_SURFACE_STRAND_%02d"%i,"CURVE")
    cu.dimensions="3D"
    cu.resolution_u=2
    cu.bevel_depth=.00034 if i%3 else .00042
    cu.bevel_resolution=1
    cu.materials.append(mat)
    spline=cu.splines.new("POLY")
    spline.points.add(len(path)-1)
    for point,v in zip(spline.points,path):point.co=(v.x,v.y,v.z,1)
    ob=bpy.data.objects.new(cu.name,cu)
    bpy.context.scene.collection.objects.link(ob)
    world=ob.matrix_world.copy()
    ob.parent=rig
    ob.parent_type="BONE"
    ob.parent_bone="head"
    ob.matrix_world=world
    ob["experimentalOnly"]=True
    ob["measuredOnActualHair"]=True
    created.append(ob.name)
if len(created)<6:raise RuntimeError("ILLUSTRATED_STRANDS_NOT_REPROJECTED_ON_TO_HAIR_MESH")
report={"gender":gender,"sourceFittedHair":hair.name,
        "newRealGeometryStrokes":created,"raysHit":hitcount,"raysMissed":misscount,
        "originalRig":rig.name,
        "sourceCanonicalSceneUntouched":True,
        "status":"UNAPPROVED_SECOND_PASS_CURVED_SURFACE_STRAND_QA"}
bpy.ops.wm.save_as_mainfile(filepath=str(out.with_suffix(".blend")),compress=True,copy=True)
out.with_name(out.stem+"-strand-qa.json").write_text(json.dumps(report,indent=2))
print("BOB_AUTHORED_ILLUSTRATION_STROKES",json.dumps(report),flush=True)
