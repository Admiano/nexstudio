"""Model-free lip-sync check measured from rendered pixels (CPU, Workbench).

Usage: blender -b built.blend --python cast-lipsync-pixel-qa.py -- timeline.json report.json [first last]
Renders a flat mask of the mouth interior (oral meshes and teeth, occluded by
the lips and face) per frame, then compares its area with the voiceover:
  - timing offset (frames) between on-screen mouth opening and voiced energy
  - drift: that offset per 15 s window
  - p/b/m: mouth visibly sealed on the frame nearest each bilabial
Nothing is written back to the scene file.
"""
import bpy,json,subprocess,sys,tempfile
from mathutils import Vector
import numpy as np
from pathlib import Path
argv=sys.argv[sys.argv.index('--')+1:];tl=json.loads(Path(argv[0]).read_text());report=Path(argv[1])
cfg=tl['lipSync'];fps=24;start=int(cfg.get('startFrame',1))
s=bpy.context.scene;first=int(argv[2]) if len(argv)>2 else s.frame_start;last=int(argv[3]) if len(argv)>3 else s.frame_end
# the authored oral meshes stand for the mouth interior; the face occludes them when the lips seal
oral=[o for o in s.objects if o.type=='MESH' and o.name.startswith('Cast V12 oral')]
for o in oral:o.hide_render=False
# only the head occludes the mouth from the front: skip evaluating garments, hair and subdivision
keep={'Host.body','Host.V59_face_art','Host.V59_face_frame',*(o.name for o in oral)}
for o in s.objects:
    if o.type=='MESH' and o.name not in keep:o.hide_viewport=o.hide_render=True
    if o.type=='MESH':
        for m in o.modifiers:
            if m.type in('SUBSURF','MASK'):m.show_viewport=m.show_render=False
for o in s.objects:
    if o.type=='MESH':o.color=(1,1,1,1) if o in oral else (0,0,0,1)
s.render.engine='BLENDER_WORKBENCH';sh=s.display.shading;sh.light='FLAT';sh.color_type='OBJECT'
sh.show_object_outline=False;sh.show_cavity=False;sh.show_shadows=False;sh.show_specular_highlight=False
s.render.use_freestyle=False;s.render.film_transparent=False;s.display_settings.display_device='sRGB';s.view_settings.view_transform='Standard'
if s.world:s.world.color=(0,0,0)
if s.compositing_node_group:s.compositing_node_group=None
head=bpy.data.objects['Host.rig'].pose.bones['head']
cam=s.camera;cam.data.type='ORTHO';cam.data.ortho_scale=.10
s.render.resolution_x=s.render.resolution_y=128;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='BW'
rig=bpy.data.objects['Host.rig'];area=[]
# mouth centre in head-bone space, measured on the deformed oral mesh at the first frame
s.frame_set(first);dg=bpy.context.evaluated_depsgraph_get();lower=next(o for o in oral if 'lower' in o.name)
ev=lower.evaluated_get(dg);me=ev.to_mesh();c=sum((lower.matrix_world@v.co for v in me.vertices),Vector())/len(me.vertices);ev.to_mesh_clear()
local=(rig.matrix_world@head.matrix).inverted()@c
with tempfile.TemporaryDirectory() as tmp:
    for f in range(first,last+1):
        s.frame_set(f)
        m=(rig.matrix_world@head.matrix)@local
        cam.location=(m.x,m.y-3,m.z);cam.rotation_euler=(1.5707963,0,0)
        s.render.filepath=f'{tmp}/m.png';bpy.ops.render.render(write_still=True)
        img=bpy.data.images.load(f'{tmp}/m.png');px=np.array(img.pixels[:]).reshape(-1,4)[:,0];bpy.data.images.remove(img)
        area.append(float((px>.5).mean()))
area=np.array(area)
raw=subprocess.run(['ffmpeg','-loglevel','error','-i',str(cfg['audio']),'-af','highpass=f=300,lowpass=f=3000','-f','s16le','-ac','1','-ar','16000','-'],capture_output=True,check=True).stdout
x=np.frombuffer(raw,dtype=np.int16).astype(np.float32)/32768;n=160;rms=np.sqrt((x[:len(x)//n*n].reshape(-1,n)**2).mean(1))
t=(np.arange(first,last+1)-start)/fps;env=np.interp(t,np.arange(len(rms))*.01,rms)
def score(a,b,lags=range(-8,9)):
    a=(a-a.mean())/(a.std()+1e-9);b=(b-b.mean())/(b.std()+1e-9)
    cc=[float(np.mean(a[max(0,-l):len(a)-max(0,l)]*b[max(0,l):len(b)-max(0,-l)])) for l in lags]
    return round(max(cc),3),list(lags)[int(np.argmax(cc))]
ph=json.loads(Path(cfg['phonemes']).read_text())['phones'];spoken=np.zeros(len(t),bool)
for p0,p1,p in ph:
    if p not in('sil','spn',''):spoken|=(t>=p0)&(t<p1)
corr,lag=score(env,area);win=15*fps;wl=[]
for i in range(0,len(t)-win//2,win):
    c,l=score(env[i:i+win],area[i:i+win]);wl.append(l if c>=.35 and spoken[i:i+win].mean()>=.4 else None)
good=[w for w in wl if w is not None];openref=float(np.percentile(area[spoken],90)) if spoken.any() else 1
bil=[(p0+p1)/2 for p0,p1,p in ph if p in('P','B','M')];sealed=0;checked=0
for c in bil:
    f=start+round(c*fps)-first
    if 0<=f<len(area):
        checked+=1;sealed+=min(area[max(0,f-1):f+2])<=.08*openref
out={'frames':len(area),'pixelCorr':corr,'pixelLagFrames':lag,'windowLagFrames':wl,'driftFrames':max(good)-min(good) if good else 0,
     'bilabialsChecked':checked,'bilabialsSealed':int(sealed),'openRef':round(openref,4)}
report.write_text(json.dumps({**out,'area':[round(a,4) for a in area]})+'\n');print('PIXEL_QA',json.dumps(out),flush=True)
