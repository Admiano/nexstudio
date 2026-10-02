"""Render the presenter with graded levels of skin shading.

The skin material is a pure Emission shader driven by flat attribute colors, so
the character is unlit: every skin pixel is the same value regardless of form.
This script keeps that base color and multiplies it by a soft key-light ramp
plus a highlight, all at render time. Level 0 renders the shipping look.
"""

import sys
from pathlib import Path

import bpy
from mathutils import Vector


NATIVE_HEIGHT = 4320
REFERENCE_HEIGHT = 2160
SKIN_MATERIALS = ("PEEPS_V2_WARM_SKIN", "V60_EAR_SKIN")
KEY_DIRECTION = Vector((-0.55, -0.72, 0.42)).normalized()
SHADOW_TINT = (0.55, 0.42, 0.40, 1.0)  # multiplied onto the base, so it stays warm
OCCLUSION_TINT = (0.45, 0.32, 0.30, 1.0)
HIGHLIGHT_TINT = (1.0, 0.97, 0.92, 1.0)
LEVELS = {
    0: dict(shade=0.0, occlusion=0.0, highlight=0.0, rim=0.0),
    1: dict(shade=0.45, occlusion=0.45, highlight=0.10, rim=0.0),
    2: dict(shade=0.80, occlusion=0.80, highlight=0.20, rim=0.10),
}


def grade_skin(material, level):
    """Insert a shading chain between the flat color and the emission node."""
    settings = LEVELS[level]
    if not any(settings.values()):
        return
    tree = material.node_tree
    emission = next(n for n in tree.nodes if n.type == "EMISSION")
    color_input = emission.inputs["Color"]
    if not color_input.links:
        return
    flat_color = color_input.links[0].from_socket

    geometry = tree.nodes.new("ShaderNodeNewGeometry")
    key = tree.nodes.new("ShaderNodeVectorMath")
    key.operation = "DOT_PRODUCT"
    key.inputs[1].default_value = KEY_DIRECTION
    tree.links.new(geometry.outputs["Normal"], key.inputs[0])

    ramp = tree.nodes.new("ShaderNodeMapRange")
    ramp.interpolation_type = "SMOOTHSTEP"
    ramp.inputs["From Min"].default_value = -0.10
    ramp.inputs["From Max"].default_value = 0.85
    ramp.inputs["To Min"].default_value = 0.0
    ramp.inputs["To Max"].default_value = 1.0
    tree.links.new(key.outputs["Value"], ramp.inputs["Value"])

    # How much shadow this pixel takes: none on the key side, full facing away.
    away = tree.nodes.new("ShaderNodeMath")
    away.operation = "SUBTRACT"
    away.inputs[0].default_value = 1.0
    tree.links.new(ramp.outputs["Result"], away.inputs[1])

    shadow_factor = tree.nodes.new("ShaderNodeMath")
    shadow_factor.operation = "MULTIPLY"
    shadow_factor.inputs[1].default_value = settings["shade"]
    tree.links.new(away.outputs["Value"], shadow_factor.inputs[0])

    # The shadow is the base colour darkened by a warm tint, so skin keeps its hue.
    shadow_color = tree.nodes.new("ShaderNodeMix")
    shadow_color.data_type = "RGBA"
    shadow_color.blend_type = "MULTIPLY"
    shadow_color.inputs["Factor"].default_value = 1.0
    shadow_color.inputs["B"].default_value = SHADOW_TINT
    tree.links.new(flat_color, shadow_color.inputs["A"])

    shaded = tree.nodes.new("ShaderNodeMix")
    shaded.data_type = "RGBA"
    shaded.blend_type = "MIX"
    tree.links.new(flat_color, shaded.inputs["A"])
    tree.links.new(shadow_color.outputs["Result"], shaded.inputs["B"])
    tree.links.new(shadow_factor.outputs["Value"], shaded.inputs["Factor"])

    current = shaded.outputs["Result"]

    if settings["occlusion"] > 0.0:
        # Contact shading: under the jaw, inside the collar, between the fingers.
        occlusion = tree.nodes.new("ShaderNodeAmbientOcclusion")
        occlusion.samples = 8
        occlusion.only_local = True
        occlusion.inputs["Distance"].default_value = 0.12

        crevice = tree.nodes.new("ShaderNodeMath")
        crevice.operation = "SUBTRACT"
        crevice.inputs[0].default_value = 1.0
        tree.links.new(occlusion.outputs["AO"], crevice.inputs[1])

        crevice_amount = tree.nodes.new("ShaderNodeMath")
        crevice_amount.operation = "MULTIPLY"
        crevice_amount.inputs[1].default_value = settings["occlusion"]
        tree.links.new(crevice.outputs["Value"], crevice_amount.inputs[0])

        occluded_color = tree.nodes.new("ShaderNodeMix")
        occluded_color.data_type = "RGBA"
        occluded_color.blend_type = "MULTIPLY"
        occluded_color.inputs["Factor"].default_value = 1.0
        occluded_color.inputs["B"].default_value = OCCLUSION_TINT
        tree.links.new(current, occluded_color.inputs["A"])

        occluded = tree.nodes.new("ShaderNodeMix")
        occluded.data_type = "RGBA"
        occluded.blend_type = "MIX"
        tree.links.new(current, occluded.inputs["A"])
        tree.links.new(occluded_color.outputs["Result"], occluded.inputs["B"])
        tree.links.new(crevice_amount.outputs["Value"], occluded.inputs["Factor"])
        current = occluded.outputs["Result"]

    if settings["highlight"] > 0.0:
        gloss = tree.nodes.new("ShaderNodeMath")
        gloss.operation = "POWER"
        gloss.inputs[1].default_value = 8.0
        tree.links.new(ramp.outputs["Result"], gloss.inputs[0])

        gloss_amount = tree.nodes.new("ShaderNodeMath")
        gloss_amount.operation = "MULTIPLY"
        gloss_amount.inputs[1].default_value = settings["highlight"]
        tree.links.new(gloss.outputs["Value"], gloss_amount.inputs[0])

        lit = tree.nodes.new("ShaderNodeMix")
        lit.data_type = "RGBA"
        lit.blend_type = "SCREEN"
        lit.inputs["B"].default_value = HIGHLIGHT_TINT
        tree.links.new(current, lit.inputs["A"])
        tree.links.new(gloss_amount.outputs["Value"], lit.inputs["Factor"])
        current = lit.outputs["Result"]

    if settings["rim"] > 0.0:
        facing = tree.nodes.new("ShaderNodeLayerWeight")
        facing.inputs["Blend"].default_value = 0.35
        edge = tree.nodes.new("ShaderNodeMath")
        edge.operation = "MULTIPLY"
        edge.inputs[1].default_value = settings["rim"]
        tree.links.new(facing.outputs["Fresnel"], edge.inputs[0])

        rimmed = tree.nodes.new("ShaderNodeMix")
        rimmed.data_type = "RGBA"
        rimmed.blend_type = "SCREEN"
        rimmed.inputs["B"].default_value = HIGHLIGHT_TINT
        tree.links.new(current, rimmed.inputs["A"])
        tree.links.new(edge.outputs["Value"], rimmed.inputs["Factor"])
        current = rimmed.outputs["Result"]

    tree.links.new(current, color_input)


arguments = sys.argv[sys.argv.index("--") + 1 :]
level = int(arguments[0])
output = Path(arguments[1])

for name in SKIN_MATERIALS:
    material = bpy.data.materials.get(name)
    if material is not None and material.use_nodes:
        grade_skin(material, level)

scene = bpy.context.scene
width, height = 1080, 1920
camera = scene.camera
camera.location = (-0.42, -5.0, 1.325)
camera.rotation_euler = (1.5707963, 0, 0)
camera.data.ortho_scale = 1.25
scene.render.resolution_x = width
scene.render.resolution_y = height
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.cycles.samples = 12
scene.cycles.use_adaptive_sampling = True
scene.cycles.use_denoising = True

for lineset in scene.view_layers[0].freestyle_settings.linesets:
    lineset.linestyle.thickness *= height / NATIVE_HEIGHT

node_group = scene.compositing_node_group
if node_group is not None:
    for node in node_group.nodes:
        if node.type == "DILATEERODE":
            node.inputs["Size"].default_value = max(
                1, round(node.inputs["Size"].default_value * height / REFERENCE_HEIGHT)
            )

scene.frame_set(27)
scene.render.filepath = str(output)
bpy.ops.render.render(write_still=True)
print("SKIN", output, flush=True)