import bpy, json, os
from pathlib import Path

OUT=Path(os.environ.get("PERF_CONTACT_OUT","/tmp/performance-contact"))
OUT.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
fps=scene.render.fps
times=[1.5,3.75,5.75,8.0,10.0,11.7,13.2,16.2,18.5]
scene.render.resolution_x=360
scene.render.resolution_y=540
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
try:
    scene.render.engine="BLENDER_EEVEE_NEXT"
except Exception:
    try: scene.cycles.samples=4
    except Exception: pass
items=[]
for t in times:
    fr=int(round(t*fps))+1
    scene.frame_set(fr)
    p=OUT/f"perf_{fr:04d}.png"
    scene.render.filepath=str(p)
    bpy.ops.render.render(write_still=True)
    items.append({"time":t,"frame":fr,"file":p.name})
json.dump(items,open(OUT/"frames.json","w"),indent=2)
print("PERFORMANCE_CONTACT_RENDERED",len(items),str(OUT))
