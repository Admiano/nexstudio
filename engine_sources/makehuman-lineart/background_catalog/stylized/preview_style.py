from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
STYLIZED = ROOT / "stylized"
sources = {
    "Photographic original": ROOT / "masters" / "living_room.png",
    "Painterly": STYLIZED / "masters" / "living_room.png",
    "Illustrated": STYLIZED / "masters" / "living_room_alt.png",
}
size = (960, 540)
scale = 0.6
cell = (round(size[0] * scale), round(size[1] * scale))
sheet = Image.new("RGB", (2 * cell[0] + 36, 3 * (cell[1] + 42) + 18), "#19222d")
draw = ImageDraw.Draw(sheet)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
for row, (label, source) in enumerate(sources.items()):
    with Image.open(source) as background:
        plate = ImageOps.fit(background.convert("RGBA"), size, method=Image.Resampling.LANCZOS)
    for column, presenter in enumerate(("male", "female")):
        with Image.open(ROOT / "previews" / f"{presenter}_landscape_alpha.png") as layer:
            composite = Image.alpha_composite(plate, layer.convert("RGBA"))
        x, y = 12 + column * (cell[0] + 12), 12 + row * (cell[1] + 42)
        sheet.paste(composite.convert("RGB").resize(cell, Image.Resampling.LANCZOS), (x, y))
        draw.text((x, y + cell[1] + 7), f"{label} · {presenter}", font=font, fill="#ebf1f8")
output = STYLIZED / "previews" / "style_calibration.jpg"
sheet.save(output, quality=94)
print(output)
