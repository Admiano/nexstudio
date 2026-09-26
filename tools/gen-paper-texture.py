#!/usr/bin/env python3
"""Generate a warm fibred cream paper texture — deterministic, seeded.

Output: engine_sources/explainer-v2/NexStudio_Explainer_Execution_Body_V2/
        runtime-assets/sketch-ui/textures/paper-warm-1k.png

Layers: cream base -> low-freq mottling -> mid-freq fibre noise -> sparse
ink fibres (short strokes) -> occasional speckle. Written once, vendored.
"""
import math
import random
from PIL import Image, ImageDraw, ImageFilter

W = H = 1024
rng = random.Random(20240917)

BASE = (243, 236, 219)          # warm cream, close to the reference stock
img = Image.new("RGB", (W, H), BASE)
px = img.load()

# --- low-frequency mottling (±7 value) ---
noise = Image.new("L", (W // 8, H // 8))
np = noise.load()
for y in range(H // 8):
    for x in range(W // 8):
        np[x, y] = rng.randrange(256)
noise = noise.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(28))
np = noise.load()
for y in range(H):
    for x in range(W):
        d = (np[x, y] - 128) * 14 // 128          # ±7
        r, g, b = px[x, y]
        px[x, y] = (min(255, max(0, r + d)), min(255, max(0, g + d)), min(255, max(0, b + d)))

# --- mid-frequency fibre noise (±3) ---
noise2 = Image.new("L", (W // 2, H // 2))
np2 = noise2.load()
for y in range(H // 2):
    for x in range(W // 2):
        np2[x, y] = rng.randrange(256)
noise2 = noise2.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.2))
np2 = noise2.load()
for y in range(H):
    for x in range(W):
        d = (np2[x, y] - 128) * 6 // 128           # ±3
        r, g, b = px[x, y]
        px[x, y] = (min(255, max(0, r + d)), min(255, max(0, g + d)), min(255, max(0, b + d)))

# --- fibres: short strokes, slight horizontal bias ---
dr = ImageDraw.Draw(img, "RGBA")
for _ in range(1400):
    x, y = rng.uniform(0, W), rng.uniform(0, H)
    ang = rng.gauss(0, 0.55)                        # near-horizontal
    ln = rng.uniform(1.5, 6.0)
    dx, dy = math.cos(ang) * ln, math.sin(ang) * ln
    dark = rng.random() < 0.55
    col = (90, 80, 60, rng.randint(10, 22)) if dark else (255, 252, 240, rng.randint(12, 26))
    dr.line([(x, y), (x + dx, y + dy)], fill=col, width=1)

# --- speckles ---
for _ in range(900):
    x, y = rng.uniform(0, W), rng.uniform(0, H)
    s = rng.choice([1, 1, 1, 2])
    dr.ellipse([x, y, x + s, y + s], fill=(80, 70, 52, rng.randint(10, 30)))

img.save("engine_sources/explainer-v2/NexStudio_Explainer_Execution_Body_V2/runtime-assets/sketch-ui/textures/paper-warm-1k.png", optimize=True)
print("wrote paper-warm-1k.png")
