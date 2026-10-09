"""Rebuild a customized character from a versioned Cast request."""
import argparse,importlib.util,json,os,shutil,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--request',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--scene-output',type=Path,required=True)
p.add_argument('--assemble-only',action='store_true')
p.add_argument('--blender',default=os.environ.get('BLENDER_BIN') or shutil.which('blender'))
a=p.parse_args()
if not a.blender:p.error('set BLENDER_BIN or pass --blender')
config=json.loads(a.request.read_text())['config']
spec=importlib.util.spec_from_file_location('cast_worker',root/'scripts/cast-preview-worker.py')
worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker);worker.validate(config)
env=dict(os.environ);env.update(config['env'])
env.update(CAST_SOURCE_DIR=str(root/'engine_sources/makehuman-lineart/presenters_v1'),MH_ROOT=str(root/'engine_sources/makehuman-lineart/assets'),BLENDER_BIN=a.blender,CAST_RENDER_ENTRY=str(root/'scripts/cast-render-assembled.py'),OPENBLAS_NUM_THREADS='1')
for flag in ['CAST_QUALITY_PILOT','CAST_FINISH_UPGRADE','CAST_GARMENT_STRUCTURE_PILOT','CAST_SKIN_APPEARANCE','CAST_HAIR_GROOM','CAST_FACIAL_REFINEMENT','CAST_CLOTH_APPEARANCE']:env[flag]='1'
for path in [a.output,a.scene_output]:path.resolve().parent.mkdir(parents=True,exist_ok=True)
command=['bash',str(root/'scripts/cast-preview-render.sh'),str(a.request.resolve()),str(a.output.resolve()),'--scene-output',str(a.scene_output.resolve())]
if a.assemble_only:command.append('--assemble-only')
subprocess.run(command,cwd=root,env=env,check=True)
