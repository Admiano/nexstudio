"""Visual-semantic art ranking with a local CLIP model (free, offline after
first weight download). Every drawable glyph is rasterized through the
engine's own stroke path and embedded once (assets/semantic/art_clip.npz);
at plan time a concept's text embedding ranks candidate drawings by what
they actually depict, not by what their file names say."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
BANK = HERE / 'assets' / 'semantic' / 'art_clip.npz'
MODEL = ('ViT-B-32', 'laion2b_s34b_b79k')
PROMPT = 'a simple black line drawing of {}'


def raster(strokes, size=224):
    """Strokes (unit-box or absolute) -> white RGB image, ink black."""
    pts = [q for st in strokes for q in (st[0] or ()) if len(q) >= 2]
    if not pts:
        return None
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    span = max(x1 - x0, y1 - y0, 1e-6)
    pad = size * 0.08
    k = (size - 2 * pad) / span
    ox = pad + ((size - 2 * pad) - (x1 - x0) * k) / 2
    oy = pad + ((size - 2 * pad) - (y1 - y0) * k) / 2
    im = Image.new('RGB', (size, size), 'white')
    dr = ImageDraw.Draw(im)
    for st in strokes:
        p = [(ox + (q[0] - x0) * k, oy + (q[1] - y0) * k) for q in st[0]
             if len(q) >= 2]
        if len(p) < 2:
            continue
        fl = st[3] if len(st) > 3 else False
        if fl and len(p) >= 3:
            dr.polygon(p, fill=(150, 150, 150))
        dr.line(p, fill='black', width=3, joint='curve')
    return im


@lru_cache(maxsize=1)
def _model():
    import open_clip
    import torch
    torch.set_num_threads(max(1, os.cpu_count() or 1))
    m, _, pre = open_clip.create_model_and_transforms(MODEL[0],
                                                      pretrained=MODEL[1])
    m.eval()
    return m, pre, open_clip.get_tokenizer(MODEL[0])


def available() -> bool:
    if os.environ.get('NEX_NO_CLIP'):
        return False
    try:
        import open_clip  # noqa: F401
    except Exception:
        return False
    return BANK.is_file()


@lru_cache(maxsize=1)
def bank():
    z = np.load(BANK, allow_pickle=False)
    keys = [tuple(k.split('|', 1)) for k in z['keys']]
    emb = z['emb'].astype(np.float32)
    return keys, emb, {k: i for i, k in enumerate(keys)}


@lru_cache(maxsize=4096)
def text_emb(phrase: str):
    import torch
    m, _, tok = _model()
    with torch.no_grad():
        t = m.encode_text(tok([PROMPT.format(phrase)])).float()
    t = t / t.norm(dim=-1, keepdim=True)
    return t[0].numpy()


def image_embs(images):
    import torch
    m, pre, _ = _model()
    with torch.no_grad():
        x = torch.stack([pre(im) for im in images])
        e = m.encode_image(x).float()
    e = e / e.norm(dim=-1, keepdim=True)
    return e.numpy()


def score(phrase: str, key) -> float | None:
    """Cosine similarity of the phrase to a banked drawing (dir, slug)."""
    keys, emb, pos = bank()
    i = pos.get(tuple(key))
    return None if i is None else float(emb[i] @ text_emb(phrase))


def top(phrase: str, k: int = 12, dirs=None):
    """Best banked drawings for a phrase: [((dir, slug), sim), ...]."""
    keys, emb, _ = bank()
    s = emb @ text_emb(phrase)
    order = np.argsort(-s)
    out = []
    for i in order:
        if dirs and keys[i][0] not in dirs:
            continue
        out.append((keys[i], float(s[i])))
        if len(out) >= k:
            break
    return out


def rank(phrase: str, key) -> int | None:
    """Position of a banked drawing among all drawings for a phrase
    (0 = the best-matching drawing in the whole library)."""
    keys, emb, pos = bank()
    i = pos.get(tuple(key))
    if i is None:
        return None
    s = emb @ text_emb(phrase)
    return int((s > s[i]).sum())


def image_score(phrase: str, im) -> float:
    return float(image_embs([im])[0] @ text_emb(phrase))
