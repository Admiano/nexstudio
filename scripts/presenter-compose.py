"""Compose presenter frames into the final MP4.

python3 presenter-compose.py --frames DIR --audio voice.wav --words words.json
    --script script.txt --aspect 16:9|1:1|9:16 --background bg.jpg --out out.mp4
    [--fps 24] [--accent #0052FF] [--kinetic-dir DIR]
    [--promo lower-third|squeeze --promo-name NAME [--promo-image icon.png]
     [--promo-label TEXT] [--promo-at SEC] [--promo-seconds 5]]

Frames are RGBA presenter renders (0001.png ...). Captions reuse the approved
kinetic-type renderer with inline icons on a soft card. The promo is off unless
--promo is given and appears once, briefly, away from the opening and close.
"""
import argparse, json, math, os, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZES = {'16:9': (1920, 1080), '1:1': (1080, 1080), '9:16': (1080, 1920)}
FONT_DIRS = ['/usr/share/fonts/truetype/dejavu']


def ease(p):
    p = max(0.0, min(1.0, p))
    return p * p * (3 - 2 * p)


def hexrgb(v):
    v = v.lstrip('#')
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def font(bold, size, ktr):
    return ktr._font('grotesk', bold, size)


def cover(img, size):
    W, H = size
    s = max(W / img.width, H / img.height)
    im = img.resize((math.ceil(img.width * s), math.ceil(img.height * s)), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((x, y, x + W, y + H))


def layout(aspect, W, H):
    """Presenter box (x, y, w, h) and caption card box per format."""
    if aspect == '16:9':
        ph = H
        pw = int(ph * 3 / 4)
        pres = (W - pw - int(W * 0.06), 0, pw, ph)
        cap = (int(W * 0.05), int(H * 0.58), int(W * 0.50), int(H * 0.34))
    elif aspect == '1:1':
        ph = int(H * 0.96)
        pw = int(ph * 3 / 4)
        pres = ((W - pw) // 2, H - ph, pw, ph)
        cap = (int(W * 0.06), int(H * 0.70), int(W * 0.88), int(H * 0.25))
    else:
        pw = W
        ph = int(pw * 4 / 3)
        pres = (0, H - ph, pw, ph)
        cap = (int(W * 0.06), int(H * 0.07), int(W * 0.88), int(H * 0.22))
    return pres, cap


class Captions:
    def __init__(self, ktr, ki, script, words, size, accent):
        self.ktr, self.size, self.accent = ktr, size, accent
        dur = (words[-1]['end'] if words else 1.0)
        plan = {'beats': [{'narration': script, 'start_seconds': 0.0, 'duration_seconds': dur}]}
        self.sents = ktr.sentence_words(plan, words)
        if ki is not None:
            ki.apply(self.sents, ki.select(self.sents))
        w, h = size
        base = max(34, int(h * 0.20))
        self.specs = [ktr.typeset(s, base, 'grotesk', w, margin=int(w * 0.05), frame_h=h) for s in self.sents]
        for spec in self.specs:
            s = base
            while spec['block_h'] > h * 0.86 and s > 22:
                s = int(s * 0.9)
                i = self.specs.index(spec)
                spec = ktr.typeset(self.sents[i], s, 'grotesk', w, margin=int(w * 0.05), frame_h=h)
                self.specs[i] = spec

    def frame(self, t):
        img = self.ktr.render_kinetic_frame(self.sents, self.specs, t, self.size, {}, accent=self.accent, watermark='')
        return img


def card(size, radius):
    m = Image.new('L', size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius, fill=255)
    return m


def fit_text(d, text, f_bold, maxw, ktr, start):
    s = start
    while s > 14:
        f = font(f_bold, s, ktr)
        if d.textlength(text, font=f) <= maxw:
            return f
        s -= 2
    return font(f_bold, 14, ktr)


def icon_tile(icon, side):
    if icon is None:
        return None
    im = icon.convert('RGBA')
    im.thumbnail((side, side), Image.LANCZOS)
    tile = Image.new('RGBA', (side, side), (255, 255, 255, 255))
    tile.alpha_composite(im, ((side - im.width) // 2, (side - im.height) // 2))
    m = card((side, side), side // 5)
    out = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    out.paste(tile, (0, 0), m)
    return out


def lower_third(frame, p, W, H, name, label, icon, accent, ktr, cap):
    """Broadcast-style strap: accent bar wipes in, then the plate, then text."""
    if p <= 0:
        return frame
    a_in, a_out = ease(p / 0.12), ease((1 - p) / 0.10)
    vis = min(a_in, a_out)
    side = int(min(W, H) * 0.085)
    pad = int(side * 0.28)
    d0 = ImageDraw.Draw(frame)
    f_name = fit_text(d0, name, True, int(W * 0.42), ktr, int(side * 0.46))
    f_lab = font(False, int(side * 0.26), ktr)
    tw = max(d0.textlength(name, font=f_name), d0.textlength(label, font=f_lab))
    plate_w = int((side + pad * 3 + tw) )
    plate_h = side + pad * 2
    x0 = int(W * 0.05)
    gap = int(min(W, H) * 0.025)
    y0 = cap[1] - plate_h - gap if cap[1] > H / 2 else int(H * 0.80)
    bar = max(6, side // 9)
    reveal = int((plate_w + bar) * vis)
    layer = Image.new('RGBA', (plate_w + bar, plate_h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rectangle((0, 0, bar - 1, plate_h), fill=accent + (255,))
    ld.rectangle((bar, 0, plate_w + bar, plate_h), fill=(250, 250, 248, 238))
    tile = icon_tile(icon, side)
    tx = bar + pad
    if tile is not None:
        layer.alpha_composite(tile, (tx, pad))
        tx += side + pad
    ld.text((tx, pad + int(side * 0.02)), label.upper(), font=f_lab, fill=(110, 108, 100, 255))
    ld.text((tx, pad + int(side * 0.36)), name, font=f_name, fill=(20, 20, 18, 255))
    clip = Image.new('L', layer.size, 0)
    ImageDraw.Draw(clip).rectangle((0, 0, reveal, plate_h), fill=255)
    layer.putalpha(Image.composite(layer.getchannel('A'), Image.new('L', layer.size, 0), clip))
    shadow = Image.new('RGBA', layer.size, (0, 0, 0, 0))
    shadow.putalpha(layer.getchannel('A').point(lambda v: int(v * 0.25)).filter(ImageFilter.GaussianBlur(8)))
    frame.alpha_composite(shadow, (x0 + 4, y0 + 6))
    frame.alpha_composite(layer, (x0, y0))
    return frame


def squeeze(frame, p, W, H, name, label, icon, accent, ktr):
    """Squeeze-back: the programme shrinks to a corner and an L-band carries the promo."""
    if p <= 0:
        return frame
    q = min(ease(p / 0.10), ease((1 - p) / 0.10))
    k = 1 - 0.24 * q
    sw, sh = int(W * k), int(H * k)
    band = Image.new('RGBA', (W, H), (14, 16, 22, 255))
    bd = ImageDraw.Draw(band)
    g = max(4, int(min(W, H) * 0.006))
    bd.line((sw + g, 0, sw + g, sh + g), fill=accent + (255,), width=g)
    bd.line((0, sh + g, sw + g, sh + g), fill=accent + (255,), width=g)
    bw, bh = W - sw, H - sh
    side = int(min(bh, bw if W < H else bh) * 0.62)
    if q > 0.6 and side > 20:
        a = int(255 * ease((q - 0.6) / 0.4))
        tile = icon_tile(icon, side)
        f_lab = font(False, max(14, int(side * 0.24)), ktr)
        f_name = fit_text(bd, name, True, int(W * 0.5), ktr, max(18, int(side * 0.48)))
        x = int(W * 0.04)
        y = sh + (bh - side) // 2
        txt = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        td = ImageDraw.Draw(txt)
        if tile is not None:
            txt.alpha_composite(tile, (x, y))
            x += side + int(side * 0.3)
        td.text((x, y + int(side * 0.04)), label.upper(), font=f_lab, fill=(170, 172, 180, 255))
        td.text((x, y + int(side * 0.38)), name, font=f_name, fill=(255, 255, 255, 255))
        txt.putalpha(txt.getchannel('A').point(lambda v: v * a // 255))
        band.alpha_composite(txt)
    band.alpha_composite(frame.resize((sw, sh), Image.LANCZOS), (0, 0))
    return band


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--frames', required=True)
    ap.add_argument('--audio', required=True)
    ap.add_argument('--words', required=True)
    ap.add_argument('--script', required=True)
    ap.add_argument('--aspect', choices=SIZES, default='16:9')
    ap.add_argument('--background', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--fps', type=int, default=24)
    ap.add_argument('--accent', default='#0052FF')
    ap.add_argument('--kinetic-dir', default=str(Path(__file__).resolve().parents[1] / 'engine_sources/whiteboard-v3-runtime'))
    ap.add_argument('--icons', choices=['auto', 'off'], default='auto')
    ap.add_argument('--promo', choices=['lower-third', 'squeeze'])
    ap.add_argument('--promo-name', default='')
    ap.add_argument('--promo-image')
    ap.add_argument('--promo-label', default='Brought to you by')
    ap.add_argument('--promo-at', type=float)
    ap.add_argument('--promo-seconds', type=float, default=5.0)
    a = ap.parse_args()

    os.environ.setdefault('WHITEBOARD_V3_SYSTEM_PACKAGE', str(Path(__file__).resolve().parents[1] / 'engines/whiteboard-v3-system/NEXMIND_WHITEBOARD_V3_SYSTEM_PACKAGE'))
    sys.path.insert(0, a.kinetic_dir)
    import pipeline_v3_narration_timed as core
    core.load_execution_body(None)
    import kinetic_type_renderer as ktr
    ki = None
    if a.icons == 'auto':
        try:
            import kinetic_icons as ki
        except ImportError:
            ki = None
    W, H = SIZES[a.aspect]
    words = json.loads(Path(a.words).read_text())
    words = words['words'] if isinstance(words, dict) else words
    words = [w if isinstance(w, dict) else {'start': w[0], 'end': w[1], 'word': w[2]} for w in words]
    script = Path(a.script).read_text().strip()
    frames = sorted(Path(a.frames).glob('*.png'))
    accent = hexrgb(a.accent)
    bg = cover(Image.open(a.background).convert('RGB'), (W, H)).convert('RGBA')
    pres, cap = layout(a.aspect, W, H)
    caps = Captions(ktr, ki, script, words, (cap[2], cap[3]), a.accent)
    mask = card((cap[2], cap[3]), int(min(cap[2], cap[3]) * 0.08))
    icon = Image.open(a.promo_image) if a.promo_image else None
    dur = len(frames) / a.fps
    at = a.promo_at if a.promo_at is not None else max(1.5, min(dur * 0.35, dur - a.promo_seconds - 2.0))
    if a.promo and not a.promo_name.strip():
        sys.exit('PROMO_NAME_REQUIRED')
    enc = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                            '-s', f'{W}x{H}', '-r', str(a.fps), '-i', '-', '-i', a.audio,
                            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
                            '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', a.out],
                           stdin=subprocess.PIPE)
    for i, fp in enumerate(frames):
        t = i / a.fps
        fr = bg.copy()
        p = Image.open(fp).convert('RGBA').resize((pres[2], pres[3]), Image.LANCZOS)
        fr.alpha_composite(p, (pres[0], pres[1]))
        c = caps.frame(t).convert('RGBA')
        c.putalpha(mask.point(lambda v: int(v * 0.94)))
        sh = Image.new('RGBA', c.size, (0, 0, 0, 0))
        sh.putalpha(mask.point(lambda v: int(v * 0.22)).filter(ImageFilter.GaussianBlur(10)))
        fr.alpha_composite(sh, (cap[0] + 3, cap[1] + 6))
        fr.alpha_composite(c, (cap[0], cap[1]))
        if a.promo:
            pp = (t - at) / a.promo_seconds
            if 0 < pp < 1:
                if a.promo == 'lower-third':
                    fr = lower_third(fr, pp, W, H, a.promo_name.strip(), a.promo_label, icon, accent, ktr, cap)
                else:
                    fr = squeeze(fr, pp, W, H, a.promo_name.strip(), a.promo_label, icon, accent, ktr)
        enc.stdin.write(fr.convert('RGB').tobytes())
    enc.stdin.close()
    if enc.wait() != 0:
        sys.exit('ENCODE_FAILED')
    print('PRESENTER_COMPOSE', json.dumps({'frames': len(frames), 'seconds': round(dur, 2), 'aspect': a.aspect,
                                           'sentences': len(caps.sents), 'icons': sum(1 for s in caps.sents if s.get('icon')),
                                           'promo': a.promo, 'promoAt': round(at, 2) if a.promo else None}))


if __name__ == '__main__':
    main()
