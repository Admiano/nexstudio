"""Preserve approved hand/cloth/oral appearance without editing actions."""
import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector
PROFILE='illustrated-actor-refinement-v18'
def shaped(ob):
    points=[v.co.copy() for v in ob.data.vertices]
    if ob.data.shape_keys:
        basis=ob.data.shape_keys.key_blocks[0]
        for k in list(ob.data.shape_keys.key_blocks)[1:]:
            if k.value and not k.mute:
                for i,p in enumerate(k.data):points[i]+=(p.co-basis.data[i].co)*k.value
    return points

def hand_anatomy(body):
    name='Cast V18 wrist and digit contour'
    if body.data.shape_keys.key_blocks.get(name):return {'reused':True}
    co=shaped(body);adj=[set() for _ in co]
    for edge in body.data.edges:a,b=edge.vertices;adj[a].add(b);adj[b].add(a)
    groups={g.index:g.name for g in body.vertex_groups};key=body.shape_key_add(name=name,from_mix=False);key.value=1;deltas=[]
    for v in body.data.vertices:
        weights={groups[g.group]:g.weight for g in v.groups}
        if weights.get('body',0)<.5:continue
        wrist=sum(w for n,w in weights.items() if n.startswith(('wrist.','metacarpal')))
        digit=sum(w for n,w in weights.items() if n.startswith('finger'))
        if wrist+digit<.12 or not adj[v.index]:continue
        delta=(sum((co[j] for j in adj[v.index]),Vector())/len(adj[v.index])-co[v.index])
        # Tangential smoothing keeps the hand volume. The normal component
        # only softens lumpy transitions, bounded below one millimetre.
        normal=v.normal.normalized();delta=(delta-normal*delta.dot(normal)*.75)*(.13*wrist+.07*digit)
        if delta.length>.00065:delta*=.00065/delta.length
        key.data[v.index].co+=delta;deltas.append(delta.length)
    return {'shapeKey':name,'vertices':len(deltas),'maximumMetres':max(deltas,default=0),'sourceBasisPreserved':True}

def driver_for_bend(key,rig,bone,expression):
    d=key.driver_add('value').driver;d.expression=expression
    v=d.variables.new();v.name='bend';v.type='TRANSFORMS';t=v.targets[0];t.id=rig;t.bone_target=bone;t.transform_type='ROT_X';t.transform_space='LOCAL_SPACE'

def cloth_refinement(scene):
    rig=bpy.data.objects['Host.rig'];rows=[]
    # Remove only hidden helper geometry from the old garment collision target.
    # Clothing deletion masks are still removed to expose real covered skin.
    for target in scene.objects:
        if target.get('castInternalTarget') and not target.modifiers.get('Hide helpers'):
            m=target.modifiers.new('Hide helpers','MASK');m.vertex_group='body'
            with bpy.context.temp_override(object=target,active_object=target):bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0)
    garments=[o for o in scene.objects if o.type=='MESH' and not o.get('castGarmentSource') and not o.get('castFitSource') and (not o.hide_render or o.get('castFitOriginalHideRender') is False) and any(m and m.get('castFabric') for m in o.data.materials) and not any(x in o.name.lower() for x in ('trouser','pants','jeans','shoe','sneaker'))]
    for ob in garments:
        if ob.get('castEliteCloth')==PROFILE:continue
        if not ob.data.shape_keys:ob.shape_key_add(name='Basis')
        fabric=next(m.get('castFabric') for m in ob.data.materials if m and m.get('castFabric'))
        co=shaped(ob);groups={g.index:g.name for g in ob.vertex_groups};edgecount={}
        for poly in ob.data.polygons:
            for e in poly.edge_keys:edgecount[e]=edgecount.get(e,0)+1
        protected={i for e,n in edgecount.items() if n==1 for i in e}
        adj=[set() for _ in co]
        for e in ob.data.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
        for _ in range(2):protected|={j for i in list(protected) for j in adj[i]}
        pitch,amp={'knit':(.043,.0020),'pique':(.031,.00125),'jersey':(.036,.00165),'fine satin':(.055,.00135),'woven cotton':(.030,.00135)}.get(fabric,(.048,.0016))
        details=[]
        for side in ('L','R'):
            bone=rig.data.bones['lowerarm01.'+side];axis=(bone.tail_local-bone.head_local).normalized();elbow=bone.head_local
            key=ob.shape_key_add(name='Cast V18 elbow compression '+side,from_mix=False);changed=0;maxdelta=0
            for v in ob.data.vertices:
                if v.index in protected:continue
                weights={groups[g.group]:g.weight for g in v.groups};w=sum(x for n,x in weights.items() if n in ['upperarm02.'+side,'lowerarm01.'+side])
                if w<.05:continue
                p=co[v.index];along=(p-elbow).dot(axis);near=math.exp(-(along/.050)**2);amount=amp*math.sin(along*math.tau/pitch+.7)*near*w
                key.data[v.index].co+=v.normal*amount;changed+=1;maxdelta=max(maxdelta,abs(amount))
            driver_for_bend(key,rig,'lowerarm01.'+side,'min(1,max(0,abs(bend)*1.1))')
            details.append({'area':'elbow '+side,'vertices':changed,'maximumMetres':maxdelta,'driver':bone.name})
        # Fine tension fans at the underarm and waist, broadening for satin and
        # heavier crepe. No ridges across the centre of the chest or neck rim.
        key=ob.shape_key_add(name='Cast V18 fabric tension',from_mix=False);changed=0;maxdelta=0
        for v in ob.data.vertices:
            if v.index in protected:continue
            p=co[v.index];ax=abs(p.x);front=max(0,min(1,-p.y/.07))
            under=math.exp(-((ax-.13)/.055)**2-((p.z-1.29)/.085)**2)
            waist=math.exp(-((ax-.11)/.065)**2-((p.z-1.05)/.055)**2)
            region=max(under,waist)*front
            if region<.01:continue
            phase=(p.z+.38*ax)*math.tau/(pitch*1.55)
            amount=amp*.8*math.sin(phase)*region
            key.data[v.index].co+=v.normal*amount;changed+=1;maxdelta=max(maxdelta,abs(amount))
        key.value=.6;driver_for_bend(key,rig,'spine01','min(1,.55+abs(bend)*2.5)')
        details.append({'area':'underarm/chest-side/waist','vertices':changed,'maximumMetres':maxdelta})
        # Existing stroke meshes are already deform-bound to their garment;
        # material/ink changes are unnecessary and would change the art style.
        ob['castEliteCloth']=PROFILE;rows.append({'object':ob.name,'fabric':fabric,'protectedRimVertices':len(protected),'foldPitchMetres':pitch,'relief':details})
    return rows

def oral_refinement(scene):
    rows=[]
    # Existing anatomical arches and tongue already articulate from the jaw.
    # Make closed-mouth visibility ease via recession rather than changing
    # the binary guard or exposing dental anatomy through a sealed lip.
    for ob in scene.objects:
        if not ob.name.startswith('Cast V12 oral') or not ob.data.shape_keys:continue
        k=ob.data.shape_keys.key_blocks.get('Closed lip seal')
        if k and k.id_data.animation_data:
            for fc in k.id_data.animation_data.drivers:
                if fc.data_path=='key_blocks["Closed lip seal"].value':
                    fc.driver.expression='pow(max(0,min(1,(.085-jaw)/.07)),2)'
                    rows.append({'object':ob.name,'recession':'quadratic lip-seal easing','anatomicalSourcePreserved':True})
    return rows
def apply_visual_refinement(scene,character):
    body=bpy.data.objects['Host.body']
    report={'profile':PROFILE,'handAnatomy':hand_anatomy(body),'cloth':cloth_refinement(scene),'oral':oral_refinement(scene),'animationChanged':False,'skinShaderChanged':False,'sourceTopologyChanged':False}
    scene['castVisualReport']=json.dumps(report)
    bpy.context.view_layer.update()
    return report
