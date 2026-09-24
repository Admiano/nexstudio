"""Render a short 24 fps speech and gesture segment from either V10 scene."""
from pathlib import Path
import bpy

s = bpy.context.scene
name = 'host' if 'HOST_' in bpy.data.filepath else 'guest'
start = 184 if name == 'host' else 170
out = Path(__file__).resolve().parent / 'motion' / name
out.mkdir(parents=True, exist_ok=True)
s.render.engine = 'CYCLES'
s.cycles.samples = 8
s.render.threads_mode = 'FIXED'
s.render.threads = 4
s.render.resolution_x = 480
s.render.resolution_y = 720
s.render.resolution_percentage = 100
s.render.image_settings.file_format = 'PNG'
s.camera.data.ortho_scale = 2.08
s.camera.location.z = .84 if name == 'host' else .88
for i in range(24):
    s.frame_set(start + i)
    s.render.filepath = str(out / f'{i:04d}.png')
    bpy.ops.render.render(write_still=True)
    print('MOTION_FRAME', name, i, start+i, flush=True)
