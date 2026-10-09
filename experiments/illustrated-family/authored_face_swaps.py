"""UNAPPROVED proof: author genuinely different *drawing geometry* for the V1 face.

Not another proportion-only morph. Distinct two-layer eye outlines, eyebrow
silhouettes and nose marks are constructed from new control points. The original
mouth and rig remain intact. Source scenes are opened read-only; all destructive
edits apply only to the in-memory experiment and separate saved proof scene.
Expression / blink interaction needs follow-up validation before integration.
"""
import bpy, bmesh, math, json
from mathutils import Vector, Matrix

STYLES = {
 "expressive": {"label":"Open-eyed expressive", "w":.024,"h":.0125,
     "brow":"high_round","nose":"petite"},
 "resolute": {"label":"Resolute angular", "w":.0235,"h":.0084,
     "brow":"bold_flat","nose":"wide"},
 "thoughtful": {"label":"Thoughtful narrow", "w":.0250,"h":.0066,
     "brow":"angled","nose":"long"},
}

def connected(mesh):
    links=[[] for _ in mesh.vertices]
    for edge in mesh.edges:
        a,b=edge.vertices;links[a].append(b);links[b].append(a)
    unvisited=set(range(len(mesh.vertices)))
    groups=[]
    while unvisited:
        stack=[unvisited.pop()];comp=[]
        while stack:
            i=stack.pop();comp.append(i)
            for j in links[i]:
                if j in unvisited:unvisited.remove(j);stack.append(j)
        groups.append(comp)
    return groups

def remove_original_eyes_and_lashes():
    removed={}
    for name in ["Host.V59_face_art","Host.V59_face_frame"]:
        ob=bpy.data.objects.get(name)
        assert ob and ob.type=="MESH",name
        mesh=ob.data
        islands=connected(mesh)
        eyes=[c for c in islands if len(c) in (96,56)]
        if len(eyes)!=4:
            raise RuntimeError("Cannot isolate the four authored eye stroke islands in "+name+
                               ": found "+str([len(c) for c in islands]))
        index={i for comp in eyes for i in comp}
        before=len(mesh.vertices)
        bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table()
        bmesh.ops.delete(bm,geom=[bm.verts[i] for i in index],context="VERTS")
        bm.to_mesh(mesh);bm.free();mesh.update()
        if len(mesh.vertices)!=before-len(index):raise RuntimeError("Unexpected eye-mesh topology")
        if mesh.shape_keys:
            for sk in mesh.shape_keys.key_blocks:
                if len(sk.data)!=len(mesh.vertices):raise RuntimeError("Eye edit broke facial shape key "+sk.name)
        removed[name]={"beforeVertices":before,"afterVertices":len(mesh.vertices),
                      "eyeStrokeVerticesRemoved":len(index),"shapeKeysPreserved":len(mesh.shape_keys.key_blocks) if mesh.shape_keys else 0}
    for name in ("Host.eyebrow001","Host.eyelashes01","Host.V10_nose_L","Host.V10_nose_R"):
        ob=bpy.data.objects.get(name)
        if ob:ob.hide_render=True
    return removed

def make_stroke(name,world_points,thickness=.0011,material=None):
    path=bpy.data.curves.new(name,"CURVE")
    path.dimensions="3D";path.resolution_u=16
    path.bevel_depth=thickness;path.bevel_resolution=2
    spline=path.splines.new("POLY")
    spline.points.add(len(world_points)-1)
    for p,point in zip(spline.points,world_points):
        p.co=(*point,1)
    if material:path.materials.append(material)
    ob=bpy.data.objects.new(name,path)
    bpy.context.scene.collection.objects.link(ob)
    # Bone-parent for shared head motion, while keeping authored points at
    # their originally measured world-space positions in the baseline pose.
    world=ob.matrix_world.copy()
    rig=bpy.data.objects["Host.rig"]
    ob.parent=rig;ob.parent_type="BONE";ob.parent_bone="head"
    ob.matrix_world=world
    ob["identityFeaturePrototype"]=True
    ob["blinkGeometryValidation"]="UNVERIFIED"
    return ob

def authored_eye_outline(cx,cz,front,side,style):
    P=STYLES[style]
    W,H=P["w"],P["h"]
    tilt={"expressive":-.002,"resolute":.003,"thoughtful":-.004}[style]
    if side=="L":tilt=-tilt
    up,down=[],[]
    for i in range(25):
        t=-1+2*i/24
        q=max(0,1-t*t)
        if style=="expressive":
            top=H*(q**.56)
            bottom=-.78*H*(q**.64)
        elif style=="resolute":
            top=H*(q**.83)+.0007
            bottom=-.40*H*(q**.93)
        else:
            top=H*(q**1.08)-.0010
            bottom=-.28*H*q
        dz=tilt*t
        up.append(Vector((cx+W*t,front,cz+top+dz)))
        down.append(Vector((cx+W*t,front,cz+bottom+dz)))
    return up,down

def brow_points(cx,cz,front,side,style):
    out=[]
    for i in range(23):
        t=-1+2*i/22
        if style=="expressive":
            z=cz+.016 + .008*(1-t*t)
            w=.024
        elif style=="resolute":
            z=cz+.016 + (.004*t if side=="L" else -.004*t)
            w=.026
        else:
            z=cz+.018 + .004*(1-t*t) + (-.006*t if side=="L" else .006*t)
            w=.027
        out.append(Vector((cx+w*t,front,z)))
    return out

def nose_points(facecenter,pupil_mid_z,front,style):
    cx=facecenter
    z=pupil_mid_z-.045
    if style=="expressive":
        return [
            [Vector((cx-.004,front,z+.018)),Vector((cx-.002,front,z+.005)),Vector((cx+.002,front,z)),
             Vector((cx+.009,front,z-.002))],
            [Vector((cx-.011,front,z-.003)),Vector((cx-.005,front,z-.006))]
        ]
    if style=="resolute":
        return [
            [Vector((cx+.001,front,z+.023)),Vector((cx+.005,front,z+.009)),Vector((cx+.013,front,z-.003))],
            [Vector((cx-.014,front,z-.002)),Vector((cx-.005,front,z-.005))],
            [Vector((cx+.006,front,z-.005)),Vector((cx+.017,front,z-.002))]
        ]
    return [
        [Vector((cx+.004,front,z+.026)),Vector((cx+.002,front,z+.012)),Vector((cx-.004,front,z-.006)),
         Vector((cx+.002,front,z-.008))],
        [Vector((cx-.009,front,z-.007)),Vector((cx-.003,front,z-.009))]
    ]

def build_identity(style,gender):
    if style not in STYLES:raise ValueError(style)
    rig=bpy.data.objects.get("Host.rig")
    body=bpy.data.objects.get("Host.body")
    if not rig or not body:raise RuntimeError("Canonical rig/body missing")
    original_shape_keys=[k.name for k in body.data.shape_keys.key_blocks]
    scene=bpy.context.scene
    scene.frame_set(27)
    bpy.context.view_layer.update()
    eye_objs=[bpy.data.objects.get("Host.lineart_pupil."+i) for i in ("L","R")]
    if any(o is None for o in eye_objs):raise RuntimeError("Canonical pupil missing")
    pupils={}
    for side,obj in zip(("L","R"),eye_objs):
        coord=sum((obj.matrix_world@v.co for v in obj.data.vertices),Vector())/len(obj.data.vertices)
        pupils[side]=coord
    removed=remove_original_eyes_and_lashes()
    # Native drawing material, no visual redesign of the base family.
    material=bpy.data.materials.get("V59_INK")
    if material is None:raise RuntimeError("Canonical ink material missing")
    created=[]
    for side in ("L","R"):
        center=pupils[side]
        # Curves in front of original line layer / pupil, ensuring visibility.
        front=center.y-.005
        up,down=authored_eye_outline(center.x,center.z,front,side,style)
        created.append(make_stroke("NEX_ID_"+style+"_eyeTop_"+side,up,
                                   .0013 if style=="resolute" else .00105,material).name)
        created.append(make_stroke("NEX_ID_"+style+"_eyeLower_"+side,down,.00085,material).name)
        brow=brow_points(center.x,center.z,front-.001,side,style)
        created.append(make_stroke("NEX_ID_"+style+"_brow_"+side,brow,
                                   .0020 if style=="expressive" else (.0028 if style=="resolute" else .0019),
                                   material).name)
    nose_front=min(p.y for p in pupils.values())-.005
    facecenter=(pupils["L"].x+pupils["R"].x)*.5
    for i,line in enumerate(nose_points(facecenter,(pupils["L"].z+pupils["R"].z)*.5,nose_front,style)):
        created.append(make_stroke("NEX_ID_"+style+"_nose_"+str(i),line,.0009,material).name)
    if [k.name for k in body.data.shape_keys.key_blocks]!=original_shape_keys:
        raise RuntimeError("Existing body facial performance key inventory changed")
    report={"style":style,"identityLabel":STYLES[style]["label"],"gender":gender,
       "source":bpy.data.filepath,"blender":bpy.app.version_string,
       "removedOriginalEyeArt":removed,"authoredFeatures":created,
       "mouthOriginal":"PRESERVED","bodyRigOriginal":"PRESERVED",
       "bodyShapeKeyCount":len(original_shape_keys),
       "status":"UNAPPROVED_NEUTRAL_STILLS_ONLY",
       "performance":"New authored strokes bone-parented; facial eyelid/blink and extreme viseme tests pending"}
    print("AUTHORED_IDENTITY_BUILD_OK",json.dumps(report),flush=True)
    return report
