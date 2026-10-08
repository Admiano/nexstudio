"""Seat a baked timeline under a chair and render seated waist-up frames.

Two steps in one Blender session:
  --chair <chair.blend> --seat <seat.json>   append a measured chair (from
      cast_chair.py) under the frame-1 pelvis, lowest foot on the floor.
  --render <out-dir> [--from N --to M]       per frame: refit garments
      (cast-fit-posed-clothing.py), then render a seated waist-up ortho view
      to <out-dir>/fNNNN.png (RGBA, Cycles).

The seated camera frames pelvis.x at ~0.98m with ortho 1.15 — a waist-up
presenter in a chair. Rendered figures composite over any backdrop for
podcast-style multi-presenter shots.

blender -b seated_timeline.blend --python scripts/cast-seat-scene.py -- \
    --chair /path/armchair.blend --seat /path/seat.json \
    --render /path/frames --from 1 --to 375 --character male
"""
import bpy,sys,os,runpy,json
from pathlib import Path
from mathutils import Vector

args=sys.argv[sys.argv.index('--')+1:]
def opt(name,default=None):
    return args[args.index(name)+1] if name in args else default

s=bpy.context.scene
rig=bpy.data.objects['Host.rig']
character=opt('--character','male')
os.environ['CAST_CHARACTER']=character

s.frame_set(1);bpy.context.view_layer.update()
pelv=(rig.matrix_world@rig.pose.bones['spine05'].head).copy()
floor=min(v.z for v in [(rig.matrix_world@rig.pose.bones['foot.L'].head),
                        (rig.matrix_world@rig.pose.bones['foot.R'].head)])

if opt('--chair') and opt('--seat'):
    desc=json.load(open(opt('--seat')))['seats'][0]
    with bpy.data.libraries.load(opt('--chair')) as (src,dst):dst.objects=src.objects
    for o in dst.objects:s.collection.objects.link(o)
    root=dst.objects[0]
    k=desc['scale'];root.scale=(k,k,k)
    sc=Vector(desc['seatCentre']);fl=Vector(desc['floor']);facing=Vector(desc['facing'])
    xy=Vector((pelv.x,pelv.y,0))+facing*0.05
    root.location=Vector((xy.x-sc.x*k,xy.y-sc.y*k,floor-fl.z*k))
    bpy.context.view_layer.update()
    print('SEAT_CHAIR',root.name,'loc',tuple(round(v,3) for v in root.location),'scale',round(k,3))

if opt('--save'):
    bpy.ops.wm.save_as_mainfile(filepath=opt('--save'))

if opt('--render'):
    os.environ['GARMS']=';'.join(o.name for o in s.objects if o.type=='MESH'
        and not o.get('castGarmentSource') and not o.get('castFitSource')
        and (not o.hide_render or o.get('castFitOriginalHideRender') is False)
        and any(m and m.get('castFabric') for m in o.data.materials))
    cam=s.camera
    cam.location=(pelv.x,-5.0,0.98);cam.rotation_euler=(1.5707963,0,0)
    cam.data.type='ORTHO';cam.data.ortho_scale=float(opt('--ortho','1.15'))
    s.render.engine='CYCLES';s.cycles.samples=int(os.environ.get('SAMPLES','12'))
    s.cycles.use_denoising=True
    s.render.resolution_x=int(opt('--width','540'));s.render.resolution_y=int(opt('--height','720'))
    s.render.resolution_percentage=100
    s.render.film_transparent=True
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
    out=opt('--render');os.makedirs(out,exist_ok=True)
    fit=str(Path(__file__).with_name('cast-fit-posed-clothing.py'))
    for f in range(int(opt('--from','1')),int(opt('--to',str(s.frame_end)))+1):
        s.frame_set(min(f,s.frame_end));bpy.context.view_layer.update()
        runpy.run_path(fit)
        s.render.filepath=f'{out}/f{f:04d}.png'
        bpy.ops.render.render(write_still=True)
        print('SEAT_FRAME',f,flush=True)
