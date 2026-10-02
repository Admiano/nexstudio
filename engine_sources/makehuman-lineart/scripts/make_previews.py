"""Lay out actual Blender-rendered V9/V10 stills for review."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parent
v9 = root.parent / 'restored' / 'v9_package' / 'previews'
if not v9.exists():
    v9 = root.parent / 'baseline_V9' / 'previews'
frames = root if (root / 'host_face_final.png').exists() else root.parent / 'previews'
destination = root if frames == root else root.parent / 'previews'
font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font = ImageFont.truetype(font_path, 22)

before = Image.open(v9 / 'V9_FACE_PREVIEW.png').convert('RGB')
face = Image.new('RGB', (1440, 1520), 'white')
tiles = [
    ('Host V9', before.crop((0, 78, 720, 798)), 0, 40),
    ('Host V10', Image.open(frames / 'host_face_final.png').convert('RGB'), 720, 40),
    ('Guest V9', before.crop((760, 78, 1480, 798)), 0, 800),
    ('Guest V10', Image.open(frames / 'guest_face_final.png').convert('RGB'), 720, 800),
]
d = ImageDraw.Draw(face)
for title, image, x, y in tiles:
    d.text((x + 22, y - 30), title, font=font, fill='black')
    face.paste(image, (x, y))
face.save(destination / 'V10_FACE_COMPARISON.png')

full = Image.new('RGB', (1440, 1130), 'white')
d = ImageDraw.Draw(full)
for title, file, x in [('Host V10', 'host_full_final.png', 0),
                       ('Guest V10', 'guest_full_final.png', 720)]:
    d.text((x + 24, 14), title, font=font, fill='black')
    full.paste(Image.open(frames / file).convert('RGB'), (x, 50))
full.save(destination / 'V10_FULLBODY_PREVIEW.png')
