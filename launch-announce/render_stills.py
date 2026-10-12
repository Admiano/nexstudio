import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
s = bpy.context.scene
s.cycles.samples = 32
s.render.resolution_x = 1440; s.render.resolution_y = 1920; s.render.resolution_percentage = 100
s.render.film_transparent = True
frames = [30, 100, 230, 320, 415, 520, 640, 738]
for f in frames:
    s.frame_set(f)
    s.render.filepath = f'{argv[0]}/still_{f:04d}.png'
    bpy.ops.render.render(write_still=True)
    print('STILL_DONE', f, flush=True)
