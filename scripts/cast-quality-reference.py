#!/usr/bin/env python3
"""Reproduce the opt-in approved-character quality reference without app changes."""
import argparse,json,os,shutil,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--character',choices=('female','male'),required=True)
p.add_argument('--output-dir',type=Path,required=True)
p.add_argument('--blender',default=os.environ.get('BLENDER_BIN') or shutil.which('blender'))
p.add_argument('--upgrade',action=argparse.BooleanOptionalAction,default=True,help='Apply stable hair/fabric and cuff refinements')
p.add_argument('--baseline',action='store_true',help='Use the preceding production appearance')
p.add_argument('--structure',action=argparse.BooleanOptionalAction,default=True,help='Apply bounded inward garment edge thickness')
p.add_argument('--skin',action=argparse.BooleanOptionalAction,default=True,help='Use anatomical skin texture, tailored makeup, and native male ears')
p.add_argument('--hair',action=argparse.BooleanOptionalAction,default=True,help='Build physically shaded, source-weighted hair fibres')
p.add_argument('--frame',type=int,default=27)
p.add_argument('--threads',type=int,default=4)
p.add_argument('--assemble-only',action='store_true')
p.add_argument('--motion',nargs=3,type=int,metavar=('START','END','STEP'))
a=p.parse_args()
if not a.blender or not Path(a.blender).is_file():p.error('Supply an installed Blender 5.2 binary')
if not 1<=a.frame<=998 or not 1<=a.threads<=16:p.error('Frame/threads outside supported range')
a.output_dir=a.output_dir.resolve();a.output_dir.mkdir(parents=True,exist_ok=True)
config=json.loads((root/'docs/cast-quality-reference'/f'{a.character}-reference.request.json').read_text())
config['config']['frame']=a.frame
name=a.character+('-baseline' if a.baseline else '-candidate')
request=a.output_dir/(name+'.request.json');request.write_text(json.dumps(config,indent=2)+'\n')
env=dict(os.environ,**config['config']['env'])
env.update(BLENDER_BIN=str(Path(a.blender).resolve()),CAST_SOURCE_DIR=str(root/'engine_sources/makehuman-lineart/presenters_v1'),CAST_RENDER_ENTRY=str(root/'scripts/cast-render-assembled.py'),MH_ROOT=str(root/'engine_sources/makehuman-lineart/assets'),OPENBLAS_NUM_THREADS='1',CAST_RENDER_THREADS=str(a.threads),CAST_HAIR_GROOM='1' if a.hair and not a.baseline else '0',CAST_SKIN_APPEARANCE='1' if a.skin and not a.baseline else '0',CAST_FINISH_UPGRADE='1' if a.upgrade and not a.baseline else '0',CAST_QUALITY_PILOT='0' if a.baseline else '1',CAST_GARMENT_STRUCTURE_PILOT='1' if a.structure and not a.baseline else '0')
command=['bash',str(root/'scripts/cast-preview-render.sh'),str(request),str(a.output_dir/(name+'.png')),'--scene-output',str(a.output_dir/(name+'.blend'))]
if a.assemble_only:command.append('--assemble-only')
if a.motion:command.extend(['--motion-proof',*[str(v) for v in a.motion]])
with (a.output_dir/(name+'.log')).open('w') as log:result=subprocess.run(command,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
if result.returncode:raise SystemExit('Reference render failed; see '+str(a.output_dir/(name+'.log')))
print('CAST_QUALITY_REFERENCE_COMPLETE',name,str(a.output_dir),flush=True)
