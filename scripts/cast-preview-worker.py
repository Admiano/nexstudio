#!/usr/bin/env python3
"""Durable bounded Blender queue. One original scene/process per selection."""
import argparse,fcntl,json,os,re,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE_VERSION='bf88447b8f898bea078c44b9202cfe2b7ff13be5';RENDER_VERSION='approved-v3-v6-finish-v7-upper-thigh'
CACHE=Path(os.environ.get('CAST_PREVIEW_CACHE_DIR',ROOT/'engine_sources/makehuman-lineart/out/cast-previews'))
SOURCE=Path(os.environ.get('CAST_SOURCE_DIR',ROOT/'engine_sources/makehuman-lineart/presenters_v1'))
ENV_KEYS={'CAST_CHARACTER','CAST_FACE','CAST_HAIR_STYLE','CAST_HAIR_HEX','CAST_SKIN_HEX','CAST_LIP_HEX','CAST_NECK','CAST_WATCH','CAST_DRESS','CAST_DRESS_HEX','CAST_MALE_LOOK','CAST_MALE_HAIR','CAST_HAIR_DYE','CAST_GARMENTS'}
BLENDER=os.environ.get('BLENDER_BIN') or shutil.which('blender')
def atomic_json(path,value):
    tmp=path.with_name(path.name+f'.{os.getpid()}.tmp');tmp.write_text(json.dumps(value));tmp.replace(path)
def status(job,value,**extra):atomic_json(job/'status.json',{'status':value,'updatedAt':time.time(),**extra})
def validate(config):
    if config['sourceVersion']!=SOURCE_VERSION or config['renderVersion']!=RENDER_VERSION:raise ValueError('CAST_SOURCE_VERSION_MISMATCH')
    if type(config['frame']) is not int or not 1<=config['frame']<=998 or config['resolutionPercentage']!=50 or config.get('framing')!='upper-thigh':raise ValueError('CAST_RENDER_PROFILE_INVALID')
    env=config['env']
    if set(env)!=ENV_KEYS or any(not isinstance(v,str) or len(v)>400 or not re.fullmatch(r'[A-Za-z0-9_=,.-]*',v) for v in env.values()):raise ValueError('CAST_RENDER_ENV_INVALID')
    if env['CAST_CHARACTER'] not in ('female','male') or env['CAST_FACE'] not in ('0','1','2'):raise ValueError('CAST_CHARACTER_INVALID')
def render(job):
    config=json.loads((job/'request.json').read_text())['config'];validate(config)
    if not BLENDER or not Path(BLENDER).is_file():raise RuntimeError('BLENDER_RUNTIME_MISSING')
    if not (SOURCE/'scenes/BASE_V58.blend').is_file():raise RuntimeError('CAST_SOURCE_SCENE_MISSING')
    env=dict(os.environ);env.update(config['env']);env.update({'CAST_SOURCE_DIR':str(SOURCE),'BLENDER_BIN':BLENDER,'CAST_RENDER_ENTRY':str(ROOT/'scripts/cast-render-assembled.py'),'MH_ROOT':os.environ.get('MH_ROOT',str(SOURCE.parent/'assets')),'PYTHONUNBUFFERED':'1','OPENBLAS_NUM_THREADS':'1'})
    # The cache version names a fixed profile, independent of worker startup
    # environment or experimental settings used by reference tooling.
    env.update(CAST_QUALITY_PILOT='1',CAST_FINISH_UPGRADE='1',CAST_GARMENT_STRUCTURE_PILOT='1')
    started=time.monotonic();status(job,'rendering')
    with (job/'render.log').open('w') as log:result=subprocess.run(['bash',str(ROOT/'scripts/cast-preview-render.sh'),str(job/'request.json'),str(job/'render.png')],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900)
    if result.returncode!=0 or not (job/'render.png').is_file():raise RuntimeError(f'CAST_RENDER_FAILED:{result.returncode}')
    (job/'render.png').replace(job/'preview.png');status(job,'ready',seconds=round(time.monotonic()-started,2));print('CAST_PREVIEW_READY',job.name,round(time.monotonic()-started,2),flush=True)
def take_lock():
    lock=(CACHE/'.worker.lock').open('a+')
    try:fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:lock.close();return None
    return lock
def drain():
    CACHE.mkdir(parents=True,exist_ok=True);lock=take_lock()
    if lock is None:return
    try:
        while True:
            jobs=sorted((p.parent for p in CACHE.glob('*/request.json') if re.fullmatch(r'[a-f0-9]{64}',p.parent.name)),key=lambda p:(p/'request.json').stat().st_mtime)
            pending=[]
            for job in jobs:
                if (job/'preview.png').is_file():continue
                try:s=json.loads((job/'status.json').read_text())['status']
                except (OSError,ValueError,KeyError):s='queued'
                if s!='failed':pending.append(job)
            if not pending:return
            job=pending[0]
            try:render(job)
            except Exception as e:status(job,'failed',error=str(e));print('CAST_PREVIEW_FAILED',job.name,str(e),flush=True)
    finally:lock.close()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--drain',action='store_true');p.add_argument('--watch',action='store_true');args=p.parse_args()
    while True:
        drain()
        if not args.watch:break
        time.sleep(1)
