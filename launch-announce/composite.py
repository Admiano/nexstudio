#!/usr/bin/env python3
"""Composite launch frames: char render (RGBA) over keynote stage w/ real page states in screen."""
import sys, os
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

LAUNCH = '/home/ubuntu/work/launch'
STAGE = f'{LAUNCH}/keynote-stage.png'
OUT = sys.argv[1] if len(sys.argv) > 1 else f'{LAUNCH}/composite'

# --- stage to 1920x1080 (fit width, center-crop) ---
stage = Image.open(STAGE).convert('RGB')
sw = 1920 / stage.width
stage = stage.resize((1920, int(stage.height * sw)), Image.LANCZOS)
top = (stage.height - 1080) // 2
stage = stage.crop((0, top, 1920, top + 1080))

# screen rect in final coords
SX0, SY0, SX1, SY1 = [int(v * 1.25) for v in (445, 122, 1439, 646)]
SY0 -= top; SY1 -= top

def screen_with(state_png):
    fr = stage.copy()
    st = Image.open(f'{LAUNCH}/state_{state_png}.png').convert('RGB')
    f = st.width / 1680.0  # device pixel ratio (capture is 2x CSS coords)
    inner = 26
    w, h = SX1 - SX0 - inner * 2, SY1 - SY0 - inner * 2
    card = Image.new('RGB', (w, h), (247, 246, 242))
    # the real modal is two columns — show each in its screen half, full-bleed:
    # left 44%: preview column incl 'Your avatar' panel at its bottom
    lw = int(w * 0.44)
    pane = st.crop((int(545 * f), int(55 * f), int(985 * f), int(845 * f))).convert('L')
    a = np.asarray(pane)
    mask = a < 200
    rows, cols = mask.sum(axis=1), mask.sum(axis=0)
    ys = np.where(rows > 0.10 * mask.shape[1])[0]
    xs = np.where(cols > 0.10 * mask.shape[0])[0]
    pad = 14
    y0, y1 = max(10, ys.min() - pad), min(mask.shape[0] - 10, ys.max() + pad)
    x0, x1 = max(60, xs.min() - pad), min(mask.shape[1] - 60, xs.max() + pad)
    fig = st.crop((int(545 * f) + x0, int(55 * f) + y0, int(545 * f) + x1, int(55 * f) + y1))
    # tone the pane's near-white bg to the card cream so no white box edge shows
    fa = np.asarray(fig).astype(np.int16)
    nw = (fa[..., 0] > 228) & (fa[..., 1] > 226) & (fa[..., 2] > 220)
    fa[nw] = (247, 246, 242)
    fig = Image.fromarray(np.clip(fa, 0, 255).astype(np.uint8), fig.mode).convert('RGB')
    # 'Your avatar' panel pinned to the column bottom, as in the real modal
    box = st.crop((int(630 * f), int(1090 * f), int(1000 * f), int(1195 * f)))
    box = box.resize((lw - 20, int(box.height * (lw - 20) / box.width)), Image.LANCZOS)
    card.paste(box, (10, h - 10 - box.height))
    # figure fills the space above the box with even margins — never clipped
    fh = h - box.height - 20 - 18
    fig = fig.resize((int(fig.width * fh / fig.height), fh), Image.LANCZOS)
    if fig.width > lw - 20:
        fig = fig.resize((lw - 20, int(fig.height * (lw - 20) / fig.width)), Image.LANCZOS)
    card.paste(fig, ((lw - fig.width) // 2, 18))
    # right 56%: options column (name field + sections + Add to cast), right inset
    rm = 18
    rw = w - lw - rm - 14
    rc = st.crop((int(990 * f), 0, int(1660 * f), int(760 * f)))
    rc = rc.resize((rw, int(rc.height * rw / rc.width)), Image.LANCZOS)
    rc = rc.crop((0, 0, rw, min(h, rc.height)))
    card.paste(rc, (lw + 14, 0))
    mask = Image.new('L', card.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, *card.size], radius=22, fill=255)
    fr.paste(card, (SX0 + inner, SY0 + inner), mask)
    return fr

def alpha_box(im):
    a = np.array(im.split()[-1])
    ys, xs = np.where(a > 12)
    if len(ys) == 0: return None
    return xs.min(), xs.max(), ys.min(), ys.max()

REF_CENTER_X = 903.0  # alpha bbox center-x at the mark (still_0230)

def paste_char(base, char_png, floor_y=995, target_x=1150):
    ch = Image.open(char_png).convert('RGBA')
    b = alpha_box(ch)
    if not b: return base
    fig_h = b[3] - b[2]
    s = 465 / fig_h
    center_x = (b[0] + b[1]) / 2
    ch = ch.resize((int(ch.width * s), int(ch.height * s)), Image.LANCZOS)
    b = alpha_box(ch)
    feet_y, feet_x = b[3], (b[0] + b[1]) // 2
    # lateral stage position follows his world x (stage-left entrance)
    dx = int(target_x + (center_x - REF_CENTER_X) * s - feet_x)
    dy = int(floor_y - feet_y)
    # contact shadow
    sh = Image.new('RGBA', base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(sh)
    cw = max(30, (b[1] - b[0]) // 3)
    d.ellipse([dx + b[0] + cw, floor_y - 8, dx + b[1] - cw, floor_y + 12], fill=(20, 16, 14, 90))
    sh = sh.filter(ImageFilter.GaussianBlur(7))
    out = Image.alpha_composite(base.convert('RGBA'), sh)
    out.alpha_composite(ch, (dx, dy))
    return out.convert('RGB')

# frame -> state mapping (zero-lag swaps at gesture apexes)
def state_for(f):
    if f >= 539: return '5_save'
    if f >= 436: return '4_jeans'
    if f >= 339: return '2_braids'
    if f >= 205: return '1_man'
    return '0_default'

def render_one(char_path, f, out_path):
    base = screen_with(state_for(f))
    out = paste_char(base, char_path)
    out.save(out_path)
    return out_path

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    if len(sys.argv) > 1 and sys.argv[1] == 'film':
        film_dir = f'{LAUNCH}/film'
        os.makedirs(film_dir, exist_ok=True)
        import glob
        done = {os.path.basename(p) for p in glob.glob(f'{film_dir}/*.png')}
        for i in range(1, 781):
            p = f'{LAUNCH}/frames/f_{i:04d}.png'
            if not os.path.exists(p):
                break
            if f'film_{i:04d}.png' in done:
                continue
            render_one(p, i, f'{film_dir}/film_{i:04d}.png')
            if i % 60 == 0:
                print('composited', i, flush=True)
    else:
        for f in [30, 100, 230, 320, 415, 520, 640, 738]:
            p = f'{LAUNCH}/stills/still_{f:04d}.png'
            if os.path.exists(p):
                print(render_one(p, f, f'{OUT}/board_{f:04d}.png'))
