"""Compose presenter frames into the final MP4.

python3 presenter-compose.py --frames DIR --audio voice.wav --words words.json
    --script script.txt --aspect 16:9|1:1|9:16 --background bg.jpg --out out.mp4
    [--fps 24] [--accent #0052FF] [--kinetic-dir DIR]
    [--promo lower-third|squeeze --promo-name NAME [--promo-image icon.png]
     [--promo-label TEXT] [--promo-at SEC] [--promo-seconds 5]]

Frames are RGBA presenter renders (0001.png ...). Captions reuse the approved
kinetic-type renderer with inline icons: one short line at the bottom. The promo is off unless
--promo is given and appears once, briefly, away from the opening and close.
"""
import argparse, array, json, math, os, random, subprocess, sys, wave
import presenter_visuals as pv
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


def layout(aspect, W, H, lesson=False):
    """Presenter box (x, y, w, h) per format. Lesson mode anchors the teacher
    bottom-right at reduced size so the board scene behind stays readable."""
    if lesson:
        ph = int(H * (0.52 if aspect == '16:9' else 0.46 if aspect == '1:1' else 0.40))
        pw = int(ph * 3 / 4)
        return (W - pw - int(W * 0.04), H - ph, pw, ph)
    if aspect == '16:9':
        ph = H
        pw = int(ph * 3 / 4)
        return (W - pw - int(W * 0.06), 0, pw, ph)
    if aspect == '1:1':
        ph = int(H * 0.96)
        pw = int(ph * 3 / 4)
        return ((W - pw) // 2, H - ph, pw, ph)
    pw = W
    ph = int(pw * 4 / 3)
    return (0, H - ph, pw, ph)


FPS_REVEAL = 15  # caption reveals quantise to 15fps — text steps in like kinetic type, not like a fade


class Cine:
    """Cinematic caption layer — broadcast-controlled, never templated.

    Composition model, differentiated per aspect:
      - ONE anchored caption band per aspect: 16:9 sits in the empty lower
        field beside the right-third presenter; 1:1 is a centered bottom
        band; 9:16 rides the chest zone (the presenter owns the floor)
      - karaoke sweep: the ACTIVE word pops in accent at 1.12x; sung words
        settle to neutral (KTV convention), all on the MFA clock
      - heroes are a once-per-film privilege: the apex word only, behind
        the head, letter-by-letter, held briefly then gone
      - framing is a shot-size CUT grammar, not a zoom: medium holds, then
        the frame hard-cuts to a close crop on the face for the apex (and
        at most one strong pivot), then cuts back. Piecewise constant.
    """

    def __init__(self, ktr, words, script, audio, W, H, aspect, pres, accent):
        import director_plan as dp
        self.dp = dp
        self.W, self.H, self.aspect, self.pres = W, H, aspect, pres
        self.accent = accent
        self.plan = dp.plan(script, words, audio, W, H, pres, aspect)
        # caption band per aspect — anchored differently on purpose:
        # 16:9 lives in the lower field beside the right-third presenter,
        # 1:1 centers at the bottom, 9:16 rides the chest zone above the fold
        if aspect == '9:16':
            self.band = (int(W * 0.07), int(H * 0.56), int(W * 0.93), int(H * 0.72))
        elif aspect == '1:1':
            self.band = (int(W * 0.06), int(H * 0.76), int(W * 0.94), int(H * 0.93))
        else:
            right = max(int(W * 0.52), pres[0] - int(W * 0.02))
            self.band = (int(W * 0.05), int(H * 0.74), right, int(H * 0.93))
        # punch-in focus: the face zone of the presenter box
        self.focus = (pres[0] + pres[2] * 0.5, pres[1] + pres[3] * 0.16)
        self.clauses = []
        self.heroes = []
        bw = max(200, self.band[2] - self.band[0])
        size = int(H * (0.046 if aspect == '9:16' else 0.055))
        for c in self.plan['clauses']:
            for _ in range(4):
                fnt = font(True, size, ktr)
                # wrap the clause into <=2 centered lines at fixed size
                lines, cur, cx = [], [], 0
                for w in c['words']:
                    img = self._word(w['word'], fnt, accent=None)
                    img_a = self._word(w['word'], fnt, accent=accent)
                    if cur and cx + img.width > bw:
                        lines.append(cur)
                        cur, cx = [], 0
                    cur.append({'w': w, 'img': img, 'img_a': img_a, 'x': cx, 'ww': img.width})
                    cx += img.width + int(size * 0.26)
                lines.append(cur)
                if len(lines) <= 2 or size < H * 0.032:
                    break
                size = max(int(H * 0.032), int(size * 0.9))  # fit the band, never clip
            # absolute positions: block centered horizontally, lines stacked
            lh = int(size * 1.3)
            by = self.band[1] + (self.band[3] - self.band[1] - lh * len(lines)) // 2
            placed = []
            for li, line in enumerate(lines):
                lw = line[-1]['x'] + line[-1]['ww'] if line else 0
                lx = self.band[0] + (bw - lw) // 2
                for it in line:
                    placed.append({**it, 'X': lx + it['x'], 'Y': by + li * lh})
            c['placed'] = placed
            self.clauses.append(c)
            if c['hero'] is not None:
                hw = words[c['hero']]['word']
                hf = font(True, int(H * 0.105), ktr)  # restrained: ~10% of frame
                him = self._word(hw, hf, accent=accent)
                tw = min(int(W * 0.44), int(pres[2] * 1.7))
                if him.width > tw:
                    him = him.resize((tw, max(1, int(him.height * tw / him.width))), Image.LANCZOS)
                him = him.filter(ImageFilter.GaussianBlur(1.1))
                letters = self._letters(hw, hf, accent, tw)
                glow = him.copy().filter(ImageFilter.GaussianBlur(12))
                ga = glow.getchannel('A').point(lambda v: int(v * 0.4))
                tinted = Image.new('RGBA', glow.size, (accent[0], accent[1], accent[2], 0))
                tinted.putalpha(ga)
                self.heroes.append({'img': him, 'letters': letters, 'glow': tinted,
                                    't0': words[c['hero']]['start'], 't1': words[c['hero']]['end'] + 0.9,
                                    'entrance': c['entrance'], 'amp': c.get('amp', 1.0),
                                    'minor': False, 'apex': True})

    def _word(self, word, fnt, accent):
        tmp = Image.new('RGBA', (10, 10), (0, 0, 0, 0))
        d = ImageDraw.Draw(tmp)
        sw = max(1, fnt.size // 14)
        bbox = d.textbbox((0, 0), word, font=fnt, stroke_width=sw)
        w, h = bbox[2] - bbox[0] + 16, bbox[3] - bbox[1] + 16
        img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        edge = (accent[0], accent[1], accent[2], 255) if accent else (16, 16, 26, 230)
        fill = (250, 250, 252, 255) if not accent else (255, 255, 255, 255)
        d.text((8 - bbox[0], 8 - bbox[1]), word, font=fnt, fill=fill,
               stroke_width=sw, stroke_fill=edge)
        return img

    def _letters(self, word, fnt, accent, maxw):
        sw = max(1, fnt.size // 14)
        tmp = Image.new('RGBA', (10, 10), (0, 0, 0, 0))
        d = ImageDraw.Draw(tmp)
        letters, x = [], 0
        for ch in word:
            bbox = d.textbbox((0, 0), ch, font=fnt, stroke_width=sw)
            w, h = bbox[2] - bbox[0] + 16, bbox[3] - bbox[1] + 16
            img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            dd = ImageDraw.Draw(img)
            dd.text((8 - bbox[0], 8 - bbox[1]), ch, font=fnt, fill=(250, 250, 252, 255),
                    stroke_width=sw, stroke_fill=(accent[0], accent[1], accent[2], 255))
            letters.append((img, x, ch))
            x += int(d.textlength(ch, font=fnt)) if ch != ' ' else int(fnt.size * 0.3)
        if x > maxw:
            scale = maxw / x
            letters = [(im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS),
                        int(xo * scale), ch) for im, xo, ch in letters]
            x = maxw
        return {'letters': letters, 'w': x, 'h': letters[0][0].height if letters else 0}

    def shot_at(self, t):
        """Framing at t — piecewise constant; returns (scale, focus_x, focus_y).
        The close framing is a crop centred on the face, clamped inside frame."""
        s = self.dp.shot_at(self.plan['shots'], t)
        if s <= 1.001:
            return 1.0, self.W / 2, self.H / 2
        cw, ch = self.W / s, self.H / s
        fx = max(cw / 2, min(self.W - cw / 2, self.focus[0]))
        fy = max(ch / 2, min(self.H - ch / 2, self.focus[1]))
        return s, fx, fy

    def _clause_alpha(self, c, t):
        end = c['t1'] + 0.55
        apex = self.plan.get('apex')
        if apex is not None and c is not apex and c['t1'] <= apex['t0'] and c['t1'] + 0.55 > apex['t0'] - 0.2:
            end = apex['t0'] - 0.2  # dead air: the band clears before the payoff
        if t < c['t0'] - 0.1 or t > end:
            return 0.0
        a = min(1.0, max(0.0, (t - (c['t0'] - 0.1)) / 0.22))
        if t > end - 0.28:
            a *= max(0.0, 1.0 - (t - (end - 0.28)) / 0.28)
        return a

    def behind(self, img, t):
        """World layer: ONLY the apex hero — one per film, behind the head."""
        px, py, pw, ph = self.pres
        for h in self.heroes:
            if h['t0'] - 0.05 <= t <= h['t1']:
                self._draw_hero(img, h, t, px, py, pw, ph)

    def front(self, img, t):
        """Screen layer: the karaoke band, on top of everything, always sharp."""
        for c in self.clauses:
            a = self._clause_alpha(c, t)
            if a <= 0:
                continue
            for it in c['placed']:
                w = it['w']
                if t < w['start'] - 0.02:
                    continue  # unspoken words never pre-show
                active = w['start'] <= t < w['end']
                if active:
                    s = 1.12  # uniform pop for every active word — controlled,
                    it2 = it['img_a']  # the hero carries the apex emphasis
                else:
                    s = 1.0
                    it2 = it['img']  # sung words settle neutral — KTV sweep
                if s > 1.0:
                    sw2, sh2 = int(it2.width * s), int(it2.height * s)
                    it2 = it2.resize((sw2, sh2), Image.LANCZOS)
                    self._blit_a(img, it2, int(it['X'] - (sw2 - it['img'].width) / 2),
                                 int(it['Y'] - (sh2 - it['img'].height) / 2), a)
                else:
                    self._blit_a(img, it2, it['X'], it['Y'], a)

    def _hero_state(self, h, t):
        amp = h['amp']
        ent = h['entrance']
        dur = {'slam': 0.18, 'settle': 0.50, 'rise': 0.60, 'streak': 0.28}.get(ent, 0.55)
        s0 = {'slam': 1 + 0.16 * amp, 'settle': 1 + 0.08 * amp, 'emergence': max(0.8, 1 - 0.14 * amp)}.get(ent, 1.0)
        u = min(1.0, max(0.0, (t - h['t0']) / dur))
        e = 1 - (1 - u) ** 3
        s = s0 + (1 - s0) * e
        dx = int(-60 * amp * (1 - e)) if ent == 'streak' else 0
        dy = int(18 * amp * (1 - e)) if ent == 'rise' else 0
        a = 1.0
        if t < h['t0']:
            a = 0.0
        elif t > h['t1'] - 0.35:
            a = max(0.0, (h['t1'] - t) / 0.35)
        return s, dx, dy, a * 0.92

    def _draw_hero(self, img, h, t, px, py, pw, ph):
        s, dx, dy, a = self._hero_state(h, t)
        if a <= 0:
            return
        base = h['img']
        sw, sh = max(1, int(base.width * s)), max(1, int(base.height * s))
        x = int(px + pw / 2 - sw / 2) + dx
        x = max(int(self.W * 0.02), min(int(self.W * 0.98) - sw, x))
        y = int(py + ph * 0.08) + dy - int((sh - base.height) / 2)
        if h['glow'] is not None:
            ga = min(0.4, h['amp'] * 0.4) * (0.0 if t < h['t0'] else min(1.0, (t - h['t0']) / 0.45))
            if t > h['t1'] - 0.45:
                ga *= max(0.0, (h['t1'] - t) / 0.45)
            if ga > 0.02:
                g = h['glow'] if abs(s - 1.0) < 0.01 else h['glow'].resize((sw, sh), Image.LANCZOS)
                self._blit_a(img, g, x, y, ga)
        if h['letters'] is not None:
            for li, (limg, xo, ch) in enumerate(h['letters']['letters']):
                lat = h['t0'] + li * 0.04
                if t < lat:
                    continue
                age = t - lat
                pop = 1.05 if age < 0.08 else 1.0
                lw = max(1, int(limg.width * s * pop))
                lh = max(1, int(limg.height * s * pop))
                li_img = limg.resize((lw, lh), Image.LANCZOS) if (lw, lh) != limg.size else limg
                self._blit_a(img, li_img, int(x + xo * s), int(y + (0.1 * lh if age < 0.08 else 0)), a)

    def _draw_clause(self, img, c, t, a, dy=0):
        pass  # band model: clauses draw through front(), kept for API compat

    @staticmethod
    def _blit_a(img, strip, x, y, a):
        if a >= 0.999:
            img.alpha_composite(strip, (x, y))
            return
        mask = strip.getchannel('A').point(lambda v: int(v * a))
        tmp = strip.copy()
        tmp.putalpha(mask)
        img.alpha_composite(tmp, (x, y))


class VideoBackground:
    """Decode an mp4 into cover-cropped RGB frames at the output size.

    The board render and the presenter frames are both driven by the same
    voice track, so frame counts line up closely; if the video ends early the
    last frame is held, and extra video beyond the presenter is ignored.
    """

    def __init__(self, video, W, H):
        self.W, self.H = W, H
        self._proc = subprocess.Popen(
            ['ffmpeg', '-loglevel', 'error', '-i', str(video),
             '-vf', f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}',
             '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
            stdout=subprocess.PIPE)
        self._last = None

    def frame(self):
        need = self.W * self.H * 3
        buf = b''
        while len(buf) < need:
            chunk = self._proc.stdout.read(need - len(buf))
            if not chunk:
                break
            buf += chunk
        if len(buf) < need:
            self._proc.wait()
            return self._last
        self._last = Image.frombytes('RGB', (self.W, self.H), buf).convert('RGBA')
        return self._last


class Captions:
    """One short line at the bottom: at most MAX_WORDS words on screen, drawable words still become inline icons."""
    MAX_WORDS = 3

    def __init__(self, ktr, ki, script, words, frame, accent):
        self.ktr, self.accent = ktr, accent
        W, H = frame
        dur = (words[-1]['end'] if words else 1.0)
        plan = {'beats': [{'narration': script, 'start_seconds': 0.0, 'duration_seconds': dur}]}
        self.sents = ktr.sentence_words(plan, words)
        if ki is not None:
            ki.apply(self.sents, ki.select(self.sents))
        self.chunks = [c for s in self.sents for c in self.split(s)]
        size = max(26, int(min(W, H) * 0.052))
        self.w = int(W * 0.9)
        self.specs = [ktr.typeset(c, size, 'grotesk', self.w, margin=int(size * 0.6)) for c in self.chunks]
        self.h = int(max(sp['lh'] for sp in self.specs) * 1.15) if self.specs else size * 2
        self.box = ((W - self.w) // 2, H - self.h - int(H * 0.05), self.w, self.h)
        self.pad = int(size * 0.55)
        self.widths = [max(sum(it['tw'] for it in sp['lines'][0]) + sp['gap'] * (len(sp['lines'][0]) - 1), 1) + 2 * self.pad
                       for sp in self.specs]

    def split(self, sent):
        """Chunks of up to MAX_WORDS, breaking after commas when one falls inside a chunk."""
        ws, icon, out, i = sent['words'], sent.get('icon'), [], 0
        while i < len(ws):
            n = min(self.MAX_WORDS, len(ws) - i)
            comma = next((k + 1 for k in range(n - 1) if ws[i + k]['word'].endswith((',', ';', ':'))), None)
            n = comma or n
            if n == 2 and len(ws) - i - n == 1:
                n = 3
            part = ws[i:i + n]
            c = {'text': ' '.join(w['word'] for w in part), 'words': part, 'start': part[0]['start'], 'end': part[-1]['end']}
            if icon is not None and i <= icon['word'] < i + n:
                c['icon'] = {**icon, 'word': icon['word'] - i}
            out.append(c)
            i += n
        return out

    def current(self, t):
        i = 0
        for k, c in enumerate(self.chunks):
            if c['start'] <= t + 0.04:
                i = k
            else:
                break
        return i

    def frame(self, t):
        """RGBA pill (image, x offset within the caption box)."""
        if not self.chunks:
            return None, 0
        i = self.current(t)
        img = self.ktr.render_kinetic_frame(self.chunks[i:i + 1], self.specs[i:i + 1], t, (self.w, self.h), {}, accent=self.accent, watermark='')
        q = ease((t - self.chunks[i]['start']) / 0.34) if i > 0 else 1.0
        pw = int(self.widths[i - 1] + (self.widths[i] - self.widths[i - 1]) * q) if i > 0 else self.widths[i]
        pw = min(self.w, pw)
        x = (self.w - pw) // 2
        pill = img.crop((x, 0, x + pw, self.h)).convert('RGBA')
        pill.putalpha(card((pw, self.h), self.h // 2).point(lambda v: int(v * 0.94)))
        return pill, x


def sfx_bed(events, dur, path):
    """Quiet cut-sound bed under the voice: a soft whoosh on every framing
    change and a low thump where the apex hero lands. Pure-python synth,
    mono 22050 Hz — kept well under the narration level."""
    sr = 22050
    buf = [0.0] * int(dur * sr)
    n = len(buf)

    def hann(i, L):
        return 0.5 - 0.5 * math.cos(2 * math.pi * i / max(1, L))

    for ev in events:
        start = int(ev['t'] * sr)
        if ev['kind'] == 'thump':
            L = int(0.34 * sr)
            for i in range(L):
                t2 = i / sr
                v = (math.sin(2 * math.pi * 58 * t2) * math.exp(-t2 * 13.0)
                     + 0.4 * math.sin(2 * math.pi * 116 * t2) * math.exp(-t2 * 22.0))
                k = start + i
                if 0 <= k < n:
                    buf[k] += v * 0.30 * hann(i, L)
        else:  # whoosh — brown-ish noise under a hann window
            L = int(0.26 * sr)
            x = 0.0
            for i in range(L):
                x = x * 0.965 + random.gauss(0.0, 0.055)
                k = start + i
                if 0 <= k < n:
                    buf[k] += x * hann(i, L)
    pk = max(1e-6, max(abs(v) for v in buf))
    g = min(1.0, 0.32 / pk)  # stay under the voice
    data = array.array('h', (int(max(-1.0, min(1.0, v * g)) * 32000) for v in buf))
    wv = wave.open(str(path), 'wb')
    wv.setnchannels(1)
    wv.setsampwidth(2)
    wv.setframerate(sr)
    wv.writeframes(data.tobytes())
    wv.close()
    return path


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
    ap.add_argument('--background')
    ap.add_argument('--background-video', help='MP4 to use as the per-frame background instead of a still image')
    ap.add_argument('--lesson', action='store_true', help='Teacher-over-board layout: smaller presenter, no caption pill or icon cards')
    ap.add_argument('--captions', choices=['cinematic', 'pill'], default='cinematic',
                    help='cinematic: director-planned depth captions with camera moves; pill: bottom caption bar')
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
    vbg = None
    if a.background_video:
        vbg = VideoBackground(a.background_video, W, H)
    elif a.background:
        bg = cover(Image.open(a.background).convert('RGB'), (W, H)).convert('RGBA')
    else:
        sys.exit('BACKGROUND_REQUIRED')
    pres = layout(a.aspect, W, H, lesson=a.lesson)
    caps = Captions(ktr, ki, script, words, (W, H), a.accent)
    cap = caps.box
    cine = None
    if not a.lesson and a.captions == 'cinematic':
        cine = Cine(ktr, words, script, a.audio, W, H, a.aspect, pres, accent)
        # P8 evidence: the shot plan this render actually executed
        Path(a.out).with_suffix('.director.json').write_text(json.dumps({
            'authority': 'director_plan_v2', 'aspect': a.aspect,
            'clauses': [{'t0': c['t0'], 't1': c['t1'], 'intent': c['intent'], 'role': c.get('role'),
                         'hero': (words[c['hero']]['word'] if c['hero'] is not None else None),
                         'words': [w['word'] for w in c['words']]} for c in cine.plan['clauses']],
            'shots': cine.plan['shots'], 'sfx': cine.plan['sfx'],
            'heroCount': cine.plan['heroCount']}, indent=1))
    cards = None
    if a.icons == 'auto' and not a.lesson:
        taken = {pv.norm(c['words'][c['icon']['word']]['word']) for c in caps.chunks if c.get('icon')}
        concrete = ki.concrete_noun if ki is not None else None
        plan = pv.plan(words, taken, concrete, len(frames) / a.fps)
        cards = pv.Cards(plan, a.aspect, W, H, pres, ktr, hexrgb(a.accent), Path(a.out).parent / '.visuals')
    icon = Image.open(a.promo_image) if a.promo_image else None
    dur = len(frames) / a.fps
    at = a.promo_at if a.promo_at is not None else max(1.5, min(dur * 0.35, dur - a.promo_seconds - 2.0))
    if a.promo and not a.promo_name.strip():
        sys.exit('PROMO_NAME_REQUIRED')
    bed = None
    if cine and cine.plan.get('sfx'):
        bed = sfx_bed(cine.plan['sfx'], dur + 0.5, str(Path(a.out).with_suffix('.sfx.wav')))
    cmd = ['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
           '-s', f'{W}x{H}', '-r', str(a.fps), '-i', '-', '-i', a.audio]
    if bed:
        cmd += ['-i', bed,
                '-filter_complex', '[1:a][2:a]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[aout]',
                '-map', '0:v', '-map', '[aout]']
    cmd += ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', a.out]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i, fp in enumerate(frames):
        t = i / a.fps
        if vbg is not None:
            fr = vbg.frame()
            if fr is None:
                sys.exit('BACKGROUND_VIDEO_EMPTY')
            fr = fr.copy()
        else:
            fr = bg.copy()
        if cine:
            cine.behind(fr, t)  # apex hero lives in the world, behind the head
        p = Image.open(fp).convert('RGBA').resize((pres[2], pres[3]), Image.LANCZOS)
        fr.alpha_composite(p, (pres[0], pres[1]))
        if cine:
            # shot-size cut: piecewise-constant framing — crop the composite
            # around the face and blow it back up. Instant, no easing.
            s, fx, fy = cine.shot_at(t)
            if s > 1.001:
                cw, ch = round(W / s), round(H / s)
                x0, y0 = round(fx - cw / 2), round(fy - ch / 2)
                fr = fr.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.LANCZOS)
            cine.front(fr, t)  # captions live in UI space — they don't crop
        if cards is not None:
            fr = cards.draw(fr, t)
        c, cx = (None, 0) if (a.lesson or cine) else caps.frame(t)
        if c is not None:
            sh = Image.new('RGBA', (c.width + 40, c.height + 40), (0, 0, 0, 0))
            sh.paste(Image.new('RGBA', c.size, (0, 0, 0, 255)), (20, 20), c.getchannel('A').point(lambda v: int(v * 0.2)))
            sh = sh.filter(ImageFilter.GaussianBlur(9))
            fr.alpha_composite(sh, (cap[0] + cx - 18, cap[1] - 14))
            fr.alpha_composite(c, (cap[0] + cx, cap[1]))
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
                                           'sentences': len(caps.sents), 'captionChunks': len(caps.chunks), 'visuals': [(round(c['at'], 2), c['label']) for c in (cards.cards if cards else [])], 'icons': sum(1 for s in caps.sents if s.get('icon')),
                                           'promo': a.promo, 'promoAt': round(at, 2) if a.promo else None}))


if __name__ == '__main__':
    main()
