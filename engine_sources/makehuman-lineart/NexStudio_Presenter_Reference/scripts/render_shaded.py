"""Render a presenter with the approved subtle shading on skin, garments and hair.

Every material in the character files is a flat Emission shader, so the
presenters are unlit: a surface reads the same value no matter which way it
faces. This adds, per material group, a soft key-light gradient, contact
shading in the crevices, and a restrained highlight. Ink and line-art
materials are deliberately left flat so the drawn line work stays crisp.

Usage: blender -b <file> --python render_shaded.py -- <aspect> <output.png> [level]
"""

import sys
from pathlib import Path

import bpy
from mathutils import Vector


NATIVE_HEIGHT = 4320
REFERENCE_HEIGHT = 2160
KEY_DIRECTION = Vector((-0.55, -0.72, 0.42)).normalized()
HIGHLIGHT_TINT = (1.0, 0.97, 0.92, 1.0)

# Shadow tints multiply the material's own colour, so each surface keeps its hue.
SKIN = dict(
    shade=0.45,
    shadow=(0.55, 0.42, 0.40, 1.0),
    occlusion=0.45,
    occlusion_tint=(0.45, 0.32, 0.30, 1.0),
    distance=0.12,
    highlight=0.10,
    sharpness=8.0,
)
CLOTH = dict(
    shade=0.42,
    shadow=(0.60, 0.62, 0.68, 1.0),
    occlusion=0.40,
    occlusion_tint=(0.52, 0.54, 0.60, 1.0),
    distance=0.16,
    highlight=0.07,
    sharpness=10.0,
)
HAIR = dict(
    shade=0.50,
    shadow=(0.52, 0.42, 0.36, 1.0),
    occlusion=0.30,
    occlusion_tint=(0.45, 0.36, 0.30, 1.0),
    distance=0.08,
    # A narrow warm band across the mass reads as the sheen along the strands;
    # a wide or white one desaturates the hair into a grey cap.
    highlight=0.07,
    highlight_tint=(1.0, 0.84, 0.62, 1.0),
    sharpness=26.0,
)

GROUPS = {
    "PEEPS_V2_WARM_SKIN": SKIN,
    "V60_EAR_SKIN": SKIN,
    "V70_G_elvs_male_shirt_untucked_bd1": CLOTH,
    "V70_G_mindfront_male_trousers_2": CLOTH,
    "V70_G_mindfront_shoes_monk_strap_male": CLOTH,
    "V63_DRESS_mindfront_f_dress_11": CLOTH,
    "LINEART_HAIR_PAPER": HAIR,
}


def grade(material, preset, level):
    """Insert a shading chain between the flat colour and the emission node."""
    tree = material.node_tree
    emission = next((n for n in tree.nodes if n.type == "EMISSION"), None)
    if emission is None:
        return False
    if emission.inputs["Color"].links:
        flat_color = emission.inputs["Color"].links[0].from_socket
    else:
        # Constant-colour material: promote the value to a node we can shade.
        constant = tree.nodes.new("ShaderNodeRGB")
        constant.outputs["Color"].default_value = emission.inputs["Color"].default_value
        flat_color = constant.outputs["Color"]

    geometry = tree.nodes.new("ShaderNodeNewGeometry")
    key = tree.nodes.new("ShaderNodeVectorMath")
    key.operation = "DOT_PRODUCT"
    key.inputs[1].default_value = KEY_DIRECTION
    tree.links.new(geometry.outputs["Normal"], key.inputs[0])

    ramp = tree.nodes.new("ShaderNodeMapRange")
    ramp.interpolation_type = "SMOOTHSTEP"
    ramp.inputs["From Min"].default_value = -0.10
    ramp.inputs["From Max"].default_value = 0.85
    tree.links.new(key.outputs["Value"], ramp.inputs["Value"])

    away = tree.nodes.new("ShaderNodeMath")
    away.operation = "SUBTRACT"
    away.inputs[0].default_value = 1.0
    tree.links.new(ramp.outputs["Result"], away.inputs[1])

    shadow_factor = tree.nodes.new("ShaderNodeMath")
    shadow_factor.operation = "MULTIPLY"
    shadow_factor.inputs[1].default_value = preset["shade"] * level
    tree.links.new(away.outputs["Value"], shadow_factor.inputs[0])

    shadow_color = tree.nodes.new("ShaderNodeMix")
    shadow_color.data_type = "RGBA"
    shadow_color.blend_type = "MULTIPLY"
    shadow_color.inputs["Factor"].default_value = 1.0
    shadow_color.inputs["B"].default_value = preset["shadow"]
    tree.links.new(flat_color, shadow_color.inputs["A"])

    shaded = tree.nodes.new("ShaderNodeMix")
    shaded.data_type = "RGBA"
    shaded.blend_type = "MIX"
    tree.links.new(flat_color, shaded.inputs["A"])
    tree.links.new(shadow_color.outputs["Result"], shaded.inputs["B"])
    tree.links.new(shadow_factor.outputs["Value"], shaded.inputs["Factor"])
    current = shaded.outputs["Result"]

    occlusion = tree.nodes.new("ShaderNodeAmbientOcclusion")
    occlusion.samples = 8
    occlusion.only_local = True
    occlusion.inputs["Distance"].default_value = preset["distance"]

    crevice = tree.nodes.new("ShaderNodeMath")
    crevice.operation = "SUBTRACT"
    crevice.inputs[0].default_value = 1.0
    tree.links.new(occlusion.outputs["AO"], crevice.inputs[1])

    crevice_amount = tree.nodes.new("ShaderNodeMath")
    crevice_amount.operation = "MULTIPLY"
    crevice_amount.inputs[1].default_value = preset["occlusion"] * level
    tree.links.new(crevice.outputs["Value"], crevice_amount.inputs[0])

    occluded_color = tree.nodes.new("ShaderNodeMix")
    occluded_color.data_type = "RGBA"
    occluded_color.blend_type = "MULTIPLY"
    occluded_color.inputs["Factor"].default_value = 1.0
    occluded_color.inputs["B"].default_value = preset["occlusion_tint"]
    tree.links.new(current, occluded_color.inputs["A"])

    occluded = tree.nodes.new("ShaderNodeMix")
    occluded.data_type = "RGBA"
    occluded.blend_type = "MIX"
    tree.links.new(current, occluded.inputs["A"])
    tree.links.new(occluded_color.outputs["Result"], occluded.inputs["B"])
    tree.links.new(crevice_amount.outputs["Value"], occluded.inputs["Factor"])
    current = occluded.outputs["Result"]

    gloss = tree.nodes.new("ShaderNodeMath")
    gloss.operation = "POWER"
    gloss.inputs[1].default_value = preset["sharpness"]
    tree.links.new(ramp.outputs["Result"], gloss.inputs[0])

    gloss_amount = tree.nodes.new("ShaderNodeMath")
    gloss_amount.operation = "MULTIPLY"
    gloss_amount.inputs[1].default_value = preset["highlight"] * level
    tree.links.new(gloss.outputs["Value"], gloss_amount.inputs[0])

    lit = tree.nodes.new("ShaderNodeMix")
    lit.data_type = "RGBA"
    lit.blend_type = "SCREEN"
    lit.inputs["B"].default_value = preset.get("highlight_tint", HIGHLIGHT_TINT)
    tree.links.new(current, lit.inputs["A"])
    tree.links.new(gloss_amount.outputs["Value"], lit.inputs["Factor"])

    tree.links.new(lit.outputs["Result"], emission.inputs["Color"])
    return True


def main():
    arguments = sys.argv[sys.argv.index("--") + 1 :]
    aspect, output = arguments[0], Path(arguments[1])
    level = float(arguments[2]) if len(arguments) > 2 else 1.0

    if level > 0.0:
        for name, preset in GROUPS.items():
            material = bpy.data.materials.get(name)
            if material is not None and material.use_nodes:
                print("SHADED", name, grade(material, preset, level), flush=True)

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
    print("PRESENTER", output, flush=True)


if __name__ == "__main__":
    main()
