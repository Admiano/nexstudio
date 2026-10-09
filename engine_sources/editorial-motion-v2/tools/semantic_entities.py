"""Semantic entity resolver: nearest-bank-concept matching for narration words
that exact keys/phrases miss ("vehicles" -> car, "decentralized finance" ->
decentralized, "eigenlayer" -> layer2).

BGE-small-en-v1.5 (MIT licence) embeddings on CPU via transformers+torch. The
index is cached under ~/.cache/nexstudio keyed by a hash of bank+phrases so it
rebuilds automatically when the bank changes. Everything degrades gracefully:
missing torch/transformers/model/index => semantic matching simply disabled and
exact matching keeps working.

Safety: only non-brand refs are eligible — brand marks must still come through
exact keys/aliases so a lookalike word can't fuzzy-match into a logo.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

MODEL = "BAAI/bge-small-en-v1.5"
THRESHOLD = 0.75
_CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "nexstudio"

_state = {"ready": False, "docs": None, "targets": None, "vec": None, "model": None, "tok": None, "failed": False}


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def init(bank, phrases):
    """Build or load the embedding index for the given bank+phrases content."""
    if _state["ready"] or _state["failed"]:
        return _state["ready"]
    try:
        import numpy as np
        import torch
        from transformers import AutoModel, AutoTokenizer
    except Exception:
        _state["failed"] = True
        return False

    # docs: canonical keys plus phrase surface forms -> canonical key
    docs, targets = [], []
    seen = set()
    for key in bank:
        docs.append(key.replace("_", " "))
        targets.append(key)
        seen.add(key)
    for ph, key in phrases.items():
        if key in bank and ph not in seen:
            docs.append(ph)
            targets.append(key)
            seen.add(ph)

    sig = _sha("|".join(docs))
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    npz = _CACHE_DIR / f"entity_index_{sig}.npz"
    if npz.exists():
        try:
            z = np.load(npz, allow_pickle=False)
            _state.update(ready=True, docs=docs, targets=targets, vec=z["vec"])
            return True
        except Exception:
            npz.unlink(missing_ok=True)

    try:
        tok = AutoTokenizer.from_pretrained(MODEL)
        mdl = AutoModel.from_pretrained(MODEL).eval()
        with torch.no_grad():
            vec = _embed(mdl, tok, docs)
        np.savez_compressed(npz, vec=vec)
        _state.update(ready=True, docs=docs, targets=targets, vec=vec,
                      model=mdl, tok=tok)
        return True
    except Exception:
        _state["failed"] = True
        return False


def _embed(mdl, tok, texts):
    import numpy as np
    import torch
    out = []
    with torch.no_grad():
        for i in range(0, len(texts), 64):
            batch = texts[i:i + 64]
            b = tok(batch, padding=True, truncation=True, max_length=32, return_tensors="pt")
            h = mdl(**b).last_hidden_state
            m = b["attention_mask"].unsqueeze(-1).float()
            v = (h * m).sum(1) / m.sum(1).clamp(min=1e-9)
            out.append(torch.nn.functional.normalize(v, dim=1).numpy())
    return np.concatenate(out)


def embed_texts(texts):
    """Embed arbitrary strings; used to build the film-context vector."""
    if _state["model"] is None:
        try:
            from transformers import AutoModel, AutoTokenizer
            _state["tok"] = AutoTokenizer.from_pretrained(MODEL)
            _state["model"] = AutoModel.from_pretrained(MODEL).eval()
        except Exception:
            return None
    return _embed(_state["model"], _state["tok"], texts)


def lookup(text, bank, family, exclude=frozenset(), ctx=None):
    """Return a canonical bank key semantically nearest to `text`, or None.

    Score = 0.65*cos(word,key) + 0.35*cos(film_context,key) when `ctx` (an
    embedding of the film's narration) is given — an everyday polyseme like
    "base" resolves to basechain only when the film is actually about crypto.
    Only keys whose ref for `family` is a non-brand drawable are eligible —
    fuzzy-matching into a logo is a hijack risk we don't take.
    """
    if not _state["ready"] or _state["vec"] is None:
        return None
    q = embed_texts([text])
    if q is None:
        return None
    q = q[0]
    word_scores = _state["vec"] @ q
    if ctx is not None:
        ctx_scores = _state["vec"] @ ctx
        scores = 0.65 * word_scores + 0.35 * ctx_scores
    else:
        scores = word_scores
    order = scores.argsort()[::-1][:8]
    for j in order:
        if scores[j] < THRESHOLD:
            return None
        key = _state["targets"][j]
        if key in exclude:
            continue
        spec = bank.get(key)
        if not spec:
            continue
        ref = spec.get(family) or (spec.get("photo") if family == "photos" else None) or spec.get("colour")
        if ref and not str(ref).startswith("brand."):
            return key
    return None


def enabled():
    return _state["ready"]
