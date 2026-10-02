import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
manifest = json.loads((ROOT / "manifest.json").read_text())
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 19)
title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 23)
CELL_WIDTH = {"landscape": 576, "square": 440, "portrait": 300}
PADDING = 16
LABEL_HEIGHT = 40
presenters = ("male", "female")

for aspect in ("landscape", "square", "portrait"):
    cell_width = CELL_WIDTH[aspect]
    source_width = manifest["formats"][aspect]["width"]
    source_height = manifest["formats"][aspect]["height"]
    cell_height = round(cell_width * source_height / source_width)
    row_height = cell_height + LABEL_HEIGHT + PADDING + 26
    sheet = Image.new(
        "RGB",
        (
            2 * cell_width + 3 * PADDING,
            len(manifest["scene_ids"]) * row_height + 2 * PADDING + 36,
        ),
        "#151c27",
    )
    draw = ImageDraw.Draw(sheet)
    draw.text(
        (PADDING, PADDING),
        f"Illustrated presenter settings  ·  {aspect}  ·  male / female",
        fill="#f5f7fb",
        font=title_font,
    )
    for row, (scene_id, name) in enumerate(manifest["scene_ids"].items()):
        row_y = 2 * PADDING + 36 + row * row_height
        draw.text((PADDING, row_y), name, fill="#e6ecf4", font=font)
        with Image.open(ROOT / manifest["assets"][scene_id][aspect]) as image:
            background = image.convert("RGBA")
            for column, presenter in enumerate(presenters):
                with Image.open(
                    ROOT / "previews" / f"{presenter}_{aspect}_alpha.png"
                ) as foreground:
                    background_sized = background.resize(
                        foreground.size, Image.Resampling.LANCZOS
                    )
                    composed = Image.alpha_composite(
                        background_sized, foreground.convert("RGBA")
                    ).convert("RGB")
                output = ROOT / "previews" / f"{scene_id}_{aspect}_{presenter}.jpg"
                composed.save(output, quality=92, subsampling=0, optimize=True)
                thumb = composed.resize(
                    (cell_width, cell_height), Image.Resampling.LANCZOS
                )
                x = PADDING + column * (cell_width + PADDING)
                y = row_y + LABEL_HEIGHT
                sheet.paste(thumb, (x, y))
                draw.text(
                    (x, y + cell_height + 4),
                    presenter.capitalize(),
                    fill="#b4c6dc",
                    font=font,
                )
    sheet_path = ROOT / "previews" / f"contact_{aspect}.jpg"
    sheet.save(sheet_path, quality=91, subsampling=0, optimize=True)
    print(sheet_path, sheet.size, flush=True)
