"""Stable surface detail, restrained hair-end cleanup and cuff clearance.

Opt-in refinement of existing assets. No new characters, rig or clothing.
"""
import bpy,os,bmesh
finish_report={'enabled':os.environ.get('CAST_FINISH_UPGRADE')=='1','hair':[],'fabrics':[],'cuffs':[]}

def rest_attribute(ob,name):
    attr=ob.data.attributes.get(name) or ob.data.attributes.new(name,'FLOAT_VECTOR','POINT')
    for vertex,item in zip(ob.data.vertices,attr.data):item.vector=ob.matrix_world@vertex.co

if finish_report['enabled']:
    # The source hair gradient uses world height. A rest-space attribute keeps
    # roots/dye bands attached to the hair when the head moves.
    hairs=[ob for ob in bpy.data.objects if ob.type=='MESH' and not ob.hide_render and any(m and m.name=='LINEART_HAIR_PAPER' for m in ob.data.materials)]
    for ob in hairs:
        points=[ob.matrix_world@v.co for v in ob.data.vertices]
        low=min(p.z for p in points);high=max(p.z for p in points);moved=0;maximum=0
        if high-low>0.13 and os.environ.get('CAST_HAIR_STYLE') in ('long','bob','bangs','braid'):
            mesh=bmesh.new();mesh.from_mesh(ob.data);mesh.verts.ensure_lookup_table()
            boundary={v.index for e in mesh.edges if e.is_boundary for v in e.verts}
            changes={};inverse=ob.matrix_world.inverted().to_3x3()
            for index in boundary:
                point=points[index]
                if point.z>low+0.16:continue
                vertex=mesh.verts[index]
                neighbours=[edge.other_vert(vertex).index for edge in vertex.link_edges if edge.is_boundary]
                if len(neighbours)!=2:continue
                average=(points[neighbours[0]]+points[neighbours[1]])*0.5
                delta=(average-point)*0.5
                if delta.length>0.004:delta*=0.004/delta.length
                if delta.length>1e-7:changes[index]=inverse@delta;maximum=max(maximum,delta.length)
            mesh.free()
            for index,delta in changes.items():
                ob.data.vertices[index].co+=delta
                if ob.data.shape_keys:
                    for key in ob.data.shape_keys.key_blocks:key.data[index].co+=delta
            moved=len(changes);ob.data.update()
        rest_attribute(ob,'cast_hair_rest')
        finish_report['hair'].append({'object':ob.name,'endVerticesRefined':moved,'maximumWorldDisplacement':maximum,'restGradient':True})
    material=bpy.data.materials.get('LINEART_HAIR_PAPER')
    if material and material.use_nodes:
        tree=material.node_tree;attribute=tree.nodes.get('Cast hair rest coordinates') or tree.nodes.new('ShaderNodeAttribute')
        attribute.name='Cast hair rest coordinates';attribute.attribute_name='cast_hair_rest'
        replaced=0
        for link in list(tree.links):
            if link.from_node.type=='NEW_GEOMETRY' and link.from_socket.name=='Position':
                tree.links.new(attribute.outputs['Vector'],link.to_socket);replaced+=1
        finish_report['hairGradientLinksReplaced']=replaced

    names=[x.split('=')[0] for x in os.environ.get('GARMS','').split(';') if x]
    if os.environ['CAST_CHARACTER']=='female':names=[os.environ['DOBJ']]
    garments=[bpy.data.objects[name] for name in names if name in bpy.data.objects and not any(k in name.lower() for k in ('shoe','sneaker'))]
    for ob in garments:
        rest_attribute(ob,'cast_cloth_rest')
        name=ob.name.lower()
        fabric='knit' if any(k in name for k in ('knit','fisherman')) else ('denim' if 'jeans' in name else ('wool' if 'wool' in name else ('satin' if any(k in name for k in ('qipao','cocktail')) else 'woven')))
        amplitude={'knit':0.035,'denim':0.025,'wool':0.025,'satin':0.008,'woven':0.012}[fabric]
        for material in ob.data.materials:
            if not material or not material.use_nodes:continue
            tree=material.node_tree
            if tree.nodes.get('Cast stable fabric grain'):continue
            emission=next((n for n in tree.nodes if n.type=='EMISSION'),None)
            if not emission or not emission.inputs['Color'].links:continue
            original=emission.inputs['Color'].links[0].from_socket
            attr=tree.nodes.new('ShaderNodeAttribute');attr.attribute_name='cast_cloth_rest'
            noise=tree.nodes.new('ShaderNodeTexNoise');noise.name='Cast stable fabric grain';noise.noise_dimensions='3D'
            noise.inputs['Scale'].default_value=180 if fabric=='knit' else 260
            noise.inputs['Detail'].default_value=1.0;noise.inputs['Roughness'].default_value=0.45
            tree.links.new(attr.outputs['Vector'],noise.inputs['Vector'])
            remap=tree.nodes.new('ShaderNodeMapRange');remap.inputs['To Min'].default_value=1-amplitude;remap.inputs['To Max'].default_value=1+amplitude
            tree.links.new(noise.outputs['Fac'],remap.inputs['Value'])
            multiply=tree.nodes.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1
            tree.links.new(original,multiply.inputs[1]);tree.links.new(remap.outputs['Result'],multiply.inputs[2]);tree.links.new(multiply.outputs[0],emission.inputs['Color'])
        finish_report['fabrics'].append({'object':ob.name,'fabric':fabric,'amplitude':amplitude,'coordinates':'rest-mesh'})

    # A complete, rigged skin target retains the wrist surface hidden by the
    # garment coverage masks. Only sleeve-end vertices receive clearance.
    body=bpy.data.objects['Host.body'];target=None
    for ob in garments:
        if any(k in ob.name.lower() for k in ('pants','trouser','jeans')):continue
        wrist_groups={group.index for group in ob.vertex_groups if group.name.startswith(('wrist.','hand.'))}
        members=[v.index for v in ob.data.vertices if sum(g.weight for g in v.groups if g.group in wrist_groups)>0.12]
        if not members:continue
        if target is None:
            target=body.copy();target.name='Cast internal full-skin clearance';target.data=body.data
            for modifier in list(target.modifiers):
                if modifier.type=='MASK':target.modifiers.remove(modifier)
            bpy.context.scene.collection.objects.link(target);target.hide_render=True;target['castInternalTarget']=True
        group=ob.vertex_groups.get('Cast sleeve clearance') or ob.vertex_groups.new(name='Cast sleeve clearance');group.add(members,1.0,'REPLACE')
        modifier=ob.modifiers.get('Cast sleeve clearance') or ob.modifiers.new('Cast sleeve clearance','SHRINKWRAP')
        modifier.target=target;modifier.vertex_group=group.name;modifier.wrap_method='NEAREST_SURFACEPOINT';modifier.wrap_mode='OUTSIDE';modifier.offset=0.0018
        proxies=[proxy for proxy in bpy.data.objects if proxy.get('castGarmentProxySource')==ob.name]
        for proxy in proxies:
            proxy_group=proxy.vertex_groups.get(group.name) or proxy.vertex_groups.new(name=group.name)
            proxy_group.add(members,1.0,'REPLACE')
            proxy_modifier=proxy.modifiers.get('Cast sleeve clearance') or proxy.modifiers.new('Cast sleeve clearance','SHRINKWRAP')
            proxy_modifier.target=target;proxy_modifier.vertex_group=proxy_group.name
            proxy_modifier.wrap_method='NEAREST_SURFACEPOINT';proxy_modifier.wrap_mode='OUTSIDE';proxy_modifier.offset=0.0018
        finish_report['cuffs'].append({'object':ob.name,'vertices':len(members),'clearance':0.0018,'preservesRig':True,'seamProxiesCorrected':len(proxies)})
    bpy.context.view_layer.update()
print('CAST_FINISH_UPGRADE',finish_report,flush=True)
