"""Render a transparent presenter plate at delivery resolution.

Freestyle thickness and the compositor's contour dilation are both defined in
pixels at the file's native 2880x4320 output, so both must be scaled to the
render height or the ink reads several times too heavy.
"""

import sys
from pathlib import Path

import bpy


NATIVE_HEIGHT = 4320
REFERENCE_HEIGHT = 2160  # the approved 50% preview height

arguments = sys.argv[sys.argv.index("--") + 1 :]
presenter, aspect, directory = arguments
dimensions = {
    "landscape": (1920, 1080),
    "square": (1080, 1080),
    "portrait": (1080, 1920),
}
width, height = dimensions[aspect]

scene = bpy.context.scene
camera = scene.camera
camera.location = (-0.42, -5.0, 1.325)
camera.rotation_euler = (1.5707963, 0, 0)
camera.data.ortho_scale = 1.25 * max(1.0, width / height)
scene.render.resolution_x = width
scene.render.resolution_y = height
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.image_settings.color_depth = "8"
scene.cycles.samples = 12
scene.cycles.use_adaptive_sampling = True
scene.cycles.use_denoising = True

for lineset in scene.view_layers[0].freestyle_settings.linesets:
    lineset.linestyle.thickness *= height / NATIVE_HEIGHT

node_group = scene.compositing_node_group
if node_group is not None:
    for node in node_group.nodes:
        if node.type != "DILATEERODE":
            continue
        native = node.inputs["Size"].default_value
        node.inputs["Size"].default_value = max(
            1, round(native * height / REFERENCE_HEIGHT)
        )

scene.frame_set(27)
output = Path(directory) / f"{presenter}_{aspect}_alpha.png"
scene.render.filepath = str(output)
bpy.ops.render.render(write_still=True)
print("PRESENTER", output, flush=True)
