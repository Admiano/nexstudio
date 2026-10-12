import bpy, sys
bpy.ops.render.render = lambda *a, **k: {'FINISHED'}
argv = sys.argv[sys.argv.index('--') + 1:]
src = '/home/ubuntu/work/v1full/scripts/cast-render-assembled.py'
ns = {'__name__': '__main__', '__file__': src}
exec(compile(open(src).read(), src, 'exec'), ns)
bpy.ops.wm.save_as_mainfile(filepath=argv[2])
print('ASSEMBLED_SAVED', flush=True)
