"""Render a packaged character at an original frame and fixed camera view."""
import argparse,os,shutil,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--character',choices=['female','male'],required=True)
p.add_argument('--style',default='native')
p.add_argument('--view',choices=['front','left-3q'],default='front')
p.add_argument('--frame',type=int,default=27)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--blender',default=os.environ.get('BLENDER_BIN') or shutil.which('blender'))
a=p.parse_args()
if not 1<=a.frame<=998:p.error('frame must be between 1 and 998')
style='fixed-left-3q' if a.view=='left-3q' and a.style=='native' else a.style
scene=root/'engine_sources/makehuman-lineart/character_system/scenes'/a.character/style/'character.blend'
if not scene.is_file():p.error('packaged character/style not found')
if not a.blender:p.error('set BLENDER_BIN or pass --blender')
a.output.resolve().parent.mkdir(parents=True,exist_ok=True)
subprocess.run([a.blender,'-b',str(scene),'--threads','4','--python-exit-code','1','--python',str(root/'scripts/cast-render-saved.py'),'--',a.character,a.view,str(a.frame),str(a.output.resolve())],check=True)
