"""Fast exact reference still that colours the browser cache.
blender animated.blend --python ref_frame.py -- out.png FRAME"""
import bpy,sys
from pathlib import Path
out,frame=sys.argv[sys.argv.index('--')+1:][:2]
R=Path(__file__).resolve().parents[1];__file__=str(R/'cast-render-assembled.py')
exec(compile((R/'cast-fit-posed-clothing.py').read_text(),str(R/'cast-fit-posed-clothing.py'),'exec'),globals())
s=bpy.context.scene;s.cycles.samples=12;s.cycles.use_denoising=True
s.frame_set(int(frame));fit_posed_clothing(s)
s.render.filepath=out;bpy.ops.render.render(write_still=True)
