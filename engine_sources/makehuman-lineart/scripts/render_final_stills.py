"""Final face and full-body stills from corrected V10 scene."""
from pathlib import Path
import bpy

s=bpy.context.scene
p='host' if 'HOST_' in bpy.data.filepath else 'guest'
root=Path(__file__).resolve().parent
s.render.engine='CYCLES';s.cycles.samples=8
s.render.threads_mode='FIXED';s.render.threads=4
s.render.image_settings.file_format='PNG'
s.render.resolution_percentage=100
s.render.resolution_x=720;s.render.resolution_y=720
s.camera.data.ortho_scale=.54
s.camera.location.z=1.53 if p=='host' else 1.60
s.frame_set(194 if p=='host' else 239)
s.render.filepath=str(root/(p+'_face_final.png'))
bpy.ops.render.render(write_still=True)
s.render.resolution_y=1080;s.camera.data.ortho_scale=2.08
s.camera.location.z=.84 if p=='host' else .88
s.frame_set(194 if p=='host' else 180)
s.render.filepath=str(root/(p+'_full_final.png'))
bpy.ops.render.render(write_still=True)
