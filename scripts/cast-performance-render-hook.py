"""Server-owned opt-in native performance hook for the existing cast renderer."""
import hashlib,json,runpy,sys,wave,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def native_admission(scene,rig,body,character):
    import bpy
    admission=json.loads((ROOT/'native-performance-admission.json').read_text())[character]
    digest=hashlib.sha256(b''.join(struct.pack('fff',*v.co) for v in body.data.vertices)).hexdigest()
    if digest!=admission['bodyMeshSha256']:raise ValueError('NATIVE_APPEARANCE_REQUIRES_ADMISSION')
    for key in ('visibleHair','visibleGarment'):
        obj=scene.objects.get(admission[key])
        if obj is None or obj.hide_render:raise ValueError('NATIVE_LOOK_REQUIRES_RENDER_ADMISSION')
    return admission

def verified_request(path,character):
    request=json.loads(Path(path).read_text());audio=request.get('masterAudio') or {}
    source=Path(audio.get('path',''))
    if not source.is_file():raise ValueError('MASTER_AUDIO_NOT_AVAILABLE')
    if hashlib.sha256(source.read_bytes()).hexdigest()!=audio.get('sha256'):raise ValueError('MASTER_AUDIO_HASH_MISMATCH')
    # Production requests must describe the whole decoded PCM master. This
    # pathway accepts WAV masters, never compressed-container duration guesses.
    with wave.open(str(source)) as wav:
        actual=wav.getnframes()/wav.getframerate()
        tolerance=1/wav.getframerate()
    if abs(actual-float(audio.get('duration',0)))>tolerance:raise ValueError('MASTER_AUDIO_DURATION_MISMATCH')
    actors=request.get('actors') or []
    if len(actors)!=1 or actors[0].get('character')!=character:raise ValueError('RENDER_CHARACTER_MISMATCH')
    if actors[0].get('posture','standing')!='standing':raise ValueError('SEATED_REQUIRES_CERTIFIED_NATIVE_SCENE')
    return runpy.run_path(str(ROOT/'cast-performance-director.py'))['compile_scene'](request)

def apply_performance(scene,path,character,frame):
    import bpy
    plan=verified_request(path,character)
    last=__import__('math').ceil(plan['duration']*scene.render.fps)
    if isinstance(frame,bool) or not isinstance(frame,int) or not 1<=frame<=last:raise ValueError('FRAME_OUTSIDE_CONTINUOUS_MASTER')
    rig=bpy.data.objects.get('Host.rig');body=bpy.data.objects.get('Host.body')
    if rig is None or body is None:raise ValueError('NATIVE_CAST_REQUIRED')
    native_admission(scene,rig,body,character)
    report=runpy.run_path(str(ROOT/'cast-performance-adapter.py'))['bake_actor'](scene,rig,body,plan['actors'][0],fps=scene.render.fps)
    scene.frame_set(frame);bpy.context.view_layer.update()
    return {'version':plan['version'],'actor':plan['actors'][0]['actor_id'],'masterSha256':plan['masterAudio']['sha256'],'masterDuration':plan['duration'],'frames':report['frames'],'audioRetimed':False,'handAdmission':plan['actors'][0]['handAdmission']}
