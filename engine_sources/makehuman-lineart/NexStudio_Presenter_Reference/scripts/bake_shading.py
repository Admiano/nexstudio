"""Save a character file with the approved subtle shading baked into its materials.

Run with: blender -b <source.blend> --python bake_shading.py -- <output.blend>
"""

import sys

import bpy

sys.path.append("/home/ubuntu/work")
import render_shaded as shading

output = sys.argv[sys.argv.index("--") + 1]

for name, preset in shading.GROUPS.items():
    material = bpy.data.materials.get(name)
    if material is not None and material.use_nodes:
        print("BAKED", name, shading.grade(material, preset, 1.0), flush=True)

bpy.ops.wm.save_as_mainfile(filepath=output)
print("SAVED", output, flush=True)
