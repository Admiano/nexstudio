"""Render only the Freestyle strokes of an assembled Cast scene: every surface is a holdout, so the PNG alpha is the exact ink the final render draws."""
import bpy,sys
argv=sys.argv[sys.argv.index('--')+1:];out=argv[0];frame=int(argv[1]) if len(argv)>1 else 27
s=bpy.context.scene;s.frame_set(frame)
hold=bpy.data.materials.new('L3D ink holdout');hold.use_nodes=True;nt=hold.node_tree;nt.nodes.clear()
o=nt.nodes.new('ShaderNodeOutputMaterial');h=nt.nodes.new('ShaderNodeHoldout');nt.links.new(h.outputs[0],o.inputs['Surface'])
for vl in s.view_layers:vl.material_override=hold
s.render.engine='CYCLES';s.cycles.samples=1;s.cycles.use_denoising=False;s.cycles.device='CPU'
s.render.film_transparent=True;s.render.use_freestyle=True
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.filepath=out
bpy.ops.render.render(write_still=True)
print('CAST_LIVE3D_INK',out)
