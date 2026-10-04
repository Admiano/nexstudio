"""Bake a verified continuous-master host into a saved approved native scene.

Blender: -b --python scripts/cast-performance-native.py -- scene.blend request.json output.blend [front|left3q|right3q]
"""
import sys,runpy,json,hashlib,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def run(arguments):
 import bpy
 from mathutils import Vector
 source,request,output=map(Path,arguments[:3]);view=arguments[3] if len(arguments)>3 else 'front'
 if view not in ('front','left3q','right3q'):raise ValueError('FIXED_VIEW_NOT_ADMITTED')
 character=json.loads(request.read_text())['actors'][0]['character']
 hook=runpy.run_path(str(ROOT/'cast-performance-render-hook.py'))
 plan=hook['verified_request'](request,character)
 bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
 if view!='front':
  center=Vector((-.42,0,scene.camera.location.z));angle=math.radians(-35 if view=='left3q' else 35)
  scene.camera.location=center+Vector((5*math.sin(angle),-5*math.cos(angle),0))
  scene.camera.rotation_euler=(center-scene.camera.location).to_track_quat('-Z','Y').to_euler()
 rig=bpy.data.objects.get('Host.rig');body=bpy.data.objects.get('Host.body')
 if rig is None or body is None:raise ValueError('NATIVE_CAST_REQUIRED')
 hook['native_admission'](scene,rig,body,character)
 report=runpy.run_path(str(ROOT/'cast-performance-adapter.py'))['bake_actor'](scene,rig,body,plan['actors'][0],fps=24)
 editor=scene.sequence_editor_create()
 if len(editor.strips):raise ValueError('NATIVE_SOURCE_MUST_NOT_HAVE_EXISTING_AUDIO_STRIPS')
 editor.strips.new_sound('Continuous master audio',plan['masterAudio']['path'],channel=1,frame_start=1)
 for sound in bpy.data.sounds:sound.pack()
 scene.render.use_sequencer=False;scene.frame_set(1)
 metadata={'version':plan['version'],'approvedNativeSourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'masterSha256':plan['masterAudio']['sha256'],'masterDuration':plan['duration'],'fixedView':view,'audioRetimed':False,'nativeReport':report}
 text=bpy.data.texts.new('NATIVE_PERFORMANCE_PROVENANCE.json');text.write(json.dumps(metadata,indent=2))
 output.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True)
 output.with_suffix('.performance.json').write_text(json.dumps(metadata,indent=2))
 print('NATIVE_PERFORMANCE_BAKED',str(output),report['frames'],flush=True)
if __name__=='__main__':run(sys.argv[sys.argv.index('--')+1:])
