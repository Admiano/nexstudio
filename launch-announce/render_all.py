import bpy
s = bpy.context.scene
s.cycles.samples = 32
s.render.resolution_x, s.render.resolution_y = 960, 1280
s.render.resolution_percentage = 100
s.render.image_settings.file_format = 'PNG'
s.render.film_transparent = True
s.render.filepath = '/home/ubuntu/work/launch/frames/f_'
s.frame_start, s.frame_end = 1, 780
bpy.ops.render.render(animation=True)
