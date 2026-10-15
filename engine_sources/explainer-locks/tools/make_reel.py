#!/usr/bin/env python3
"""make_reel.py — one command: VO in, poster-framed reels out.

Pipeline: script/voice-file -> voice.mp3 + alignment.json -> auto-treatment
(style from styles.json, entities from entity_bank, customer media via
media_library) -> regression_pack render -> web file -> poster-framed file.

  python3 tools/make_reel.py --script "A few years ago, ..." --voice andrew \
      --style photo_story --media desk.png clip.mp4 --out out/my-reel
  python3 tools/make_reel.py --voice-file vo.mp3 --style sketch --aspects 1x1 --out out/r2
  python3 tools/make_reel.py --treatment fixtures/x/treatment.json --fixture-voice fixtures/x --out out/r3

Env: node must be on PATH for the renderer (nvm v24.x):
  export PATH=$HOME/.nvm/versions/node/v24.19.0/bin:$PATH
"""
import argparse, json, os, re, subprocess, sys, uuid, math
from pathlib import Path
from decimal import Decimal
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'services/studio-family-engines'))
from parallel_aspects import render_aspects
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
from generate_voice import synth, align, VOICES  # noqa: E402

STYLES = json.loads((ROOT / "styles.json").read_text())
STYLE_MAP = {s["id"]: s for s in STYLES["styles"]}
VARIANT_MAP = {f'{s["id"]}.{v["id"]}': (s, v) for s in STYLES["styles"] for v in s.get("variants", [])}
BANK = STYLES["entity_bank"]
_PHRASES_RAW = STYLES.get("entity_phrases", {})
VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv"}

CLAUSE_END = re.compile(r"[.!?]$")
CLAUSE_MID = re.compile(r"[,;:]$")
STOPWORDS = set("the a an of to and or in on for with by at is are was were be been it its this that".split())
# function words that must never fuzzy-match into a drawable entity — the
# bank's exact vocabulary is unaffected (these never were keys anyway)
STOPWORDS |= set("""
i me my mine we us our ours you your yours he him his she her hers it its they
them their theirs this these those that there here when where who whom whose
which what how why all any both each few more most other others some such no
nor not only own same so than too very can will would could may might must
shall should ought just don doesnt didnt doesnt has have had do does did done
make made take took say said says go went gone come came see saw seen know
knew think thought want wanted let lets put set use used using find found
gave give gives tell told work worked works call called calls try tried tries
ask asked asks need needed needs feel felt become became leave left seem
seemed keep kept begin began now then also really much many less least every
everyone everything everybody anybody anyone someone somebody something
anything nothing none nobody once twice always never often sometimes usually
again still yet ever almost even about above across after against along among
around before behind below beneath beside between beyond down during except
inside into like off onto out outside over past since through throughout
toward towards under underneath until up upon within without via per near next
""".split())


def log(*a):
    print("[make_reel]", *a, flush=True)


def style_of(arg):
    if arg in VARIANT_MAP:
        s, v = VARIANT_MAP[arg]
        merged = dict(s); merged.update(v); merged.pop("variants", None)
        return merged
    if arg not in STYLE_MAP:
        sys.exit(f"unknown style '{arg}' — choices: {sorted(STYLE_MAP) + sorted(VARIANT_MAP)}")
    return STYLE_MAP[arg]


# ---------- VO ----------
def _espeak_synth(text, out_wav, speed=1.0):
    """Free local fallback when the neural TTS stack isn't installed — espeak-ng
    voice at a brisk news pace. Returns duration in seconds."""
    wpm = max(120, int(175 * float(speed or 1.0)))
    subprocess.run(["espeak-ng", "-v", "en-us", "-s", str(wpm), "-w", str(out_wav), text], check=True)
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=nw=1:nk=1", str(out_wav)],
                           capture_output=True, text=True, check=True)
    return float(probe.stdout.strip() or 1.0)


def _fake_align(wav_dur_s, text, out_json):
    """Deterministic word schedule (~330ms/word, +700ms after sentence end) stretched
    to fit the real wav — clause grouping and beat timing stay sane without whisper."""
    words = []
    t = 0.0
    for tok in text.split():
        w = re.sub(r"[^\w$%&.,!?'\"-]", "", tok)
        if not w:
            continue
        dur = 0.33
        words.append({"text": w, "start_ms": round(t * 1000), "end_ms": round((t + dur) * 1000)})
        t += dur + (0.70 if re.search(r"[.!?]$", tok) else 0.06)
    if words and t > wav_dur_s > 0:
        scale = (wav_dur_s - 0.05) / t
        for w in words:
            w["start_ms"] = round(w["start_ms"] * scale)
            w["end_ms"] = max(w["start_ms"] + 60, round(w["end_ms"] * scale))
    out_json.write_text(json.dumps({"words": words}, indent=1))


def _wav_dur_s(p):
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=nw=1:nk=1", str(p)],
                           capture_output=True, text=True, check=True)
    return float(probe.stdout.strip() or 1.0)


def make_voice(args, fixture_dir):
    out_wav, out_mp3, out_ali = fixture_dir / "voice.wav", fixture_dir / "voice.mp3", fixture_dir / "alignment.json"
    if args.voice_file:
        src = Path(args.voice_file)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), str(out_wav)], check=True)
        norm = fixture_dir / "voice_norm.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(out_wav),
                        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", str(norm)], check=True)
        out_wav = norm
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(out_wav), "-b:a", "160k", str(out_mp3)], check=True)
        log(f"aligning uploaded voice {src.name} ...")
        try:
            align(out_wav, out_ali)
        except Exception as e:
            log(f"whisper alignment unavailable ({e}) — using even word schedule")
            _fake_align(_wav_dur_s(out_wav), "", out_ali)
    else:
        text = args.script or (Path(args.script_file).read_text() if args.script_file else "")
        if not text.strip() and getattr(args, "brief", None):
            # brief -> authored narration via the local/key-gated writer
            from write_script import author_script
            data = author_script(args.brief, seconds=int(args.duration or 35))
            text = data.get("script", "").strip()
            log(f"authored script: {data.get('title', args.brief)} ({len(text.split())} words)")
        if not text.strip():
            sys.exit("need --script/--script-file/--brief or --voice-file")
        from write_script import normalize_tickers
        text = normalize_tickers(text.strip())  # 'SOL' -> 'Solana' for TTS+captions
        try:
            dur = synth(text.strip(), args.voice, out_wav, speed=float(args.speed or 1.0))
        except Exception as exc:
            log(f"voice synth failed ({exc}); falling back to espeak")
            dur = _espeak_synth(text.strip(), out_wav, speed=float(args.speed or 1.0))
        norm = fixture_dir / "voice_norm.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(out_wav),
                        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", str(norm)], check=True)
        out_wav = norm
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(out_wav), "-b:a", "160k", str(out_mp3)], check=True)
        log(f"synthesized {dur:.1f}s of VO ({args.voice}), aligning ...")
        try:
            align(out_wav, out_ali)
        except Exception as e:
            log(f"whisper alignment unavailable ({e}) — using even word schedule")
            _fake_align(dur, text.strip(), out_ali)
    return json.loads(out_ali.read_text())["words"]


# ---------- auto-treatment ----------
MAX_UNITS_PER_BEAT = 5  # compiler contract: TOO_MANY_DISPLAY_UNITS refuses above this


def _unit_count(gwords):
    return len(display_units(gwords))


def chunk_beats(words, max_beats=9):
    pieces, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt_gap = words[i + 1]["start_ms"] - w["end_ms"] if i + 1 < len(words) else 9999
        if CLAUSE_END.search(w["text"]) or nxt_gap >= 650:
            pieces.append(cur); cur = []
    if cur:
        pieces.append(cur)
    # A single clause can outgrow the display cap on its own (a long run-on
    # chunks into >5 units) — cut it at its widest legal mid-clause boundary,
    # falling back to a word cut when there is no comma to break on.
    fine = []
    for p in pieces:
        while _unit_count(p) > MAX_UNITS_PER_BEAT and len(p) > 1:
            commas = [i for i, w in enumerate(p) if CLAUSE_MID.search(w["text"]) and i + 1 < len(p)]
            cut = next((i for i in reversed(commas) if _unit_count(p[:i + 1]) <= MAX_UNITS_PER_BEAT), None)
            if cut is None:
                cut = min(10, len(p) - 1)
            fine.append(p[:cut + 1])
            p = p[cut + 1:]
        fine.append(p)
    # Merge fragments into beats under the cap: the contract is hard, the
    # beat-count target is only pacing.
    beats, cur = [], []
    for p in fine:
        if cur and _unit_count(cur + p) > MAX_UNITS_PER_BEAT:
            beats.append(cur); cur = []
        cur.extend(p)
    if cur:
        beats.append(cur)
    while len(beats) > max_beats:
        i = min(range(len(beats) - 1), key=lambda i: len(beats[i]) + len(beats[i + 1]))
        if _unit_count(beats[i] + beats[i + 1]) > MAX_UNITS_PER_BEAT:
            break
        beats[i:i + 2] = [beats[i] + beats[i + 1]]
    return beats


def clean(t):
    return t.strip()


def chunked_split(clauses):
    # asymmetric split for long clauses: support bboxes are narrow (≤~4 words
    # fit above the type floor), hero bboxes hold ~8. A 14-word clause becomes
    # [setup 3w] + [hero ≤8w] + [qualifier chunks ≤4w] instead of one hero
    # that breaches the legibility floor. Returns (piece, source_clause_index)
    # pairs so units can trace back to their clause's spoken start.
    chunked = []
    for ci, c in enumerate(clauses):
        ws = c.split()
        if len(ws) > 11:
            chunked.append((" ".join(ws[:3]), ci))
            ws = ws[3:]
            chunked.append((" ".join(ws[:8]), ci))
            ws = ws[8:]
            while ws:
                chunked.append((" ".join(ws[:4]), ci))
                ws = ws[4:]
        else:
            chunked.append((c, ci))
    return chunked


def _key_fragment(clause, entity_words):
    """Punchy keyword phrase for kinetic captions: the clause's longest run of
    content words (capped at 4), preferring runs that carry a matched entity —
    'Ethereum added, smart contracts that run themselves' → 'smart contracts'."""
    ws = [w.strip() for w in clause.split() if w.strip()]
    spans, cur = [], []
    for w in ws:
        if word_key(w) in STOPWORDS or len(word_key(w)) < 2:
            if cur:
                spans.append(cur); cur = []
        else:
            cur.append(w)
    if cur:
        spans.append(cur)
    if not spans:
        return " ".join(ws[:4])
    def hit(span):
        return any(word_key(w) in entity_words for w in span)
    spans.sort(key=lambda s: (hit(s), len(s)), reverse=True)
    frag = " ".join(spans[0][:4]).strip(" ,.;:!?")
    return frag or " ".join(ws[:4])


def display_units(gwords, entity_words=None):
    # kinetic keyword captions: every clause shows its key fragment in hero
    # weight — the kinetic type IS the caption, no small verbatim lines
    text = clean(" ".join(w["text"] for w in gwords))
    entity_words = entity_words or set()
    clauses, cstarts, buf = [], [], []
    for wi, w in enumerate(gwords):
        if not buf:
            cstarts.append(wi)
        buf.append(w["text"])
        if CLAUSE_MID.search(w["text"]):
            clauses.append(" ".join(buf)); buf = []
    if buf:
        clauses.append(" ".join(buf))
    pairs = [(c.strip(), s) for c, s in zip(clauses, cstarts) if c.strip()]
    clauses = [c for c, _ in pairs]
    beat_end = gwords[-1]["end_ms"]
    HOLD_MIN_MS = 500  # conservative: compiler floors observed at 100-200ms
    while len(clauses) > 1 and beat_end - gwords[pairs[-1][1]]["start_ms"] < HOLD_MIN_MS:
        clauses[-2] = clauses[-2] + " " + clauses[-1]
        pairs.pop()
    chunked = chunked_split(clauses)
    units, seen = [], set()
    for i, (c, ci) in enumerate(chunked):
        frag = _key_fragment(c, entity_words)
        if not frag:
            continue
        # same key fragment twice reads as a typo, not emphasis — fall back to
        # the full clause tail so the second occurrence still says something
        if word_key(frag) in seen:
            tail = [w for w in c.split() if word_key(w) not in STOPWORDS]
            frag = " ".join(tail[-4:] if tail else c.split()[:4]).strip(" ,.;:!?")
        seen.add(word_key(frag))
        units.append({"text": frag, "role": "hero",
                      "anchor_word": frag.split()[0],
                      "emphasis": 0.9,
                      "semantic_role": "punch" if i == len(chunked) - 1 else "statement",
                      "_clause": ci})
    # A unit anchored on a word inside the beat's readable-close runway lands
    # too late to be read before the beat exits — re-anchor it to the first
    # word of its clause so the keyword arrives as the clause is spoken.
    RUNWAY_MS = 700
    for u in units:
        ci = u.pop("_clause")
        akey = word_key(u["anchor_word"])
        cstart = pairs[ci][1]
        aidx = next((k for k in range(cstart, len(gwords)) if word_key(gwords[k]["text"]) == akey), None)
        if aidx is not None and gwords[aidx]["start_ms"] > beat_end - RUNWAY_MS:
            u["anchor_word"] = gwords[cstart]["text"].strip(" ,.;:!?")
    # The contract caps a beat at three hero units — extra clauses keep their
    # words but step down to support weight.
    for u in units[2:-1]:
        u["role"] = "support"; u["emphasis"] = 0.55
    if not units:
        units.append({"text": text, "role": "hero", "anchor_word": text.split()[0],
                      "emphasis": 0.9, "semantic_role": "statement"})
    return units


def word_key(t):
    t = re.sub(r"[^a-z0-9'-]", "", t.lower())
    return t


def _norm_phrase(s):
    return " ".join(word_key(w) for w in s.split() if word_key(w))


# alias / multi-word surface form -> canonical bank key, normalized like toks
PHRASES = {_norm_phrase(k): v for k, v in _PHRASES_RAW.items()}
MAX_PHRASE_WORDS = max((len(p.split()) for p in PHRASES), default=1)

# a word that is itself a bank key is never a stopword — the function-word
# list must not block real vocabulary
STOPWORDS -= set(BANK)

# semantic fallback: nearest bank concept for words exact matching misses.
# Disabled automatically when transformers/torch or the model is unavailable.
try:
    from semantic_entities import init as _sem_init, lookup as _sem_lookup, embed_texts as _sem_embed
    _SEMANTIC = _sem_init(BANK, PHRASES)
except Exception:
    _sem_lookup, _sem_embed, _SEMANTIC = None, None, False

# neutral markers for beats whose narration names no drawable thing — every
# beat gets an entity (compiler requires >=1), and these read as discourse
# markers rather than a wrong metaphor. Question beats prefer 'question'.
FALLBACK_ENTITIES = [
    {"key": "question", "colour": "icon.icon-park-color.help",
     "mono": "icon.lucide.message-circle-question-mark",
     "emoji": "emoji.noto.red-question-mark", "photo": "question mark"},
    {"key": "point", "colour": "icon.icon-park-color.comment",
     "mono": "icon.mingcute.comment-line",
     "emoji": "emoji.noto.speech-balloon", "photo": "speech bubble"},
    {"key": "idea", "colour": "icon.icon-park-color.lightning",
     "mono": "icon.lucide.lightbulb",
     "emoji": "emoji.noto.light-bulb", "photo": "light bulb"},
    {"key": "highlight", "colour": "icon.icon-park-color.star",
     "mono": "icon.ant-design.star-outlined",
     "emoji": "emoji.noto.star", "photo": "abstract"},
    {"key": "note", "colour": "icon.icon-park-color.bookmark",
     "mono": "icon.mingcute.bookmark-line",
     "emoji": "emoji.noto.sparkles", "photo": "abstract"},
]


def fallback_entity(family, n, question=False):
    spec = (FALLBACK_ENTITIES[0] if question
            else FALLBACK_ENTITIES[(n % (len(FALLBACK_ENTITIES) - 1)) + 1])
    ref = spec.get(family) or spec.get("photo")
    if not ref:
        return None
    ent = {"id": f"e1_{spec['key']}{n}", "kind": "object", "glyph": "TILE",
           "phrase": spec["key"], "bank_key": spec["key"]}
    if family == "photos" or ref == spec.get("photo"):
        ent["concept"] = ref
    else:
        ent["asset_ref"] = ref
    return ent


# exact-key vetoes: a word that is a bank key still loses when a co-occurring
# word proves the everyday sense ("river bank" is not a financial bank)
_POLYSEME_VETO = {
    "bank": {"river", "shore", "canal", "stream", "bankside"},
    "base": {"statue", "bottom", "foundation", "bases"},
}


def pick_entities(gwords, family, already, ctx=None, max_n=4):
    seen = set()
    out = []
    toks = [word_key(w["text"]) for w in gwords]
    tokset = set(toks)
    i = 0
    while i < len(toks):
        tk = toks[i]
        key = None
        span = 1
        # context first: longest multi-word phrase wins over single words
        for n in range(min(MAX_PHRASE_WORDS, len(toks) - i), 1, -1):
            phrase = " ".join(toks[i:i + n])
            if phrase in PHRASES and PHRASES[phrase] in BANK:
                key = PHRASES[phrase]
                span = n
                break
        if not key:
            cands = [tk, tk[:-1] if tk.endswith("s") else tk, tk.rstrip("s'’")]
            key = next((c for c in cands if c in BANK), None)
            if not key:
                # single-word alias (e.g. ticker symbols: btc, eth)
                hit = next((c for c in cands if PHRASES.get(c) in BANK), None)
                if hit:
                    key = PHRASES[hit]
            if not key and _SEMANTIC and tk not in STOPWORDS:
                # nearest concept for vocabulary the bank doesn't spell out
                key = _sem_lookup(tk, BANK, family, already, ctx)
                if not key and i + 1 < len(toks) and toks[i + 1] not in STOPWORDS:
                    two = _sem_lookup(toks[i] + " " + toks[i + 1], BANK, family, already, ctx)
                    if two:
                        key, span = two, 2
        if not key or key in already or (span == 1 and tk in STOPWORDS):
            i += 1
            continue
        if _POLYSEME_VETO.get(key, set()) & tokset:
            i += 1
            continue
        spec = BANK[key]
        ref = spec.get(family) or (spec.get("photo") if family == "photos" else None) or spec.get("colour")
        if not ref or ref in seen:
            i += 1
            continue
        seen.add(ref); already.add(key)
        is_photo = family == "photos" or (family == "colour_icons" and ref == spec.get("photo")) or ref == spec.get("photo")
        ent = {"id": f"e{len(out)+1}_{key}", "kind": "object", "glyph": "TILE",
               "phrase": " ".join(toks[i:i + span]), "bank_key": key}
        if ref == spec.get("photo"):
            ent["concept"] = ref
        else:
            ent["asset_ref"] = ref
        out.append((ent, gwords[i]["text"]))
        i += span
        if len(out) >= max_n:
            break
    return out


def _label_ok(label, units):
    # An inside label must be a bare noun of at most three words and may not
    # restate a display unit already set in type on the same beat.
    ws = label.lower().split()
    if not ws or len(ws) > 3 or ws[0] in ("the", "a", "an"):
        return False
    uws = [u["text"].lower().split() for u in units]
    for u in uws:
        if ws == u or (len(ws) >= 2 and any(u[i:i + len(ws)] == ws for i in range(len(u) - len(ws) + 1))):
            return False
    return True


_NUMWORDS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
             "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
             "twelve": 12, "dozen": 12, "twenty": 20, "hundred": 100, "thousand": 1000,
             "million": 1_000_000, "billion": 1_000_000_000}


_DATA_SMALL = {
    **{k: v for k, v in _NUMWORDS.items() if v < 100 and k not in ("a", "an", "dozen")},
    "zero": 0, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "thirty": 30, "forty": 40,
    "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}
_DATA_SCALES = {"hundred": 100, "thousand": 1000, "million": 1_000_000,
                "billion": 1_000_000_000, "dozen": 12}
_DATA_UNITS = {
    "%": "%", "percent": "%", "percentage": "%", "dollar": "$", "dollars": "$",
    "pound": "£", "pounds": "£", "euro": "€", "euros": "€", "x": "x", "times": "x",
    "second": "seconds", "seconds": "seconds", "minute": "minutes", "minutes": "minutes",
    "hour": "hours", "hours": "hours", "day": "days", "days": "days",
    "week": "weeks", "weeks": "weeks", "month": "months", "months": "months",
    "year": "years", "years": "years", "kilowatt": "kW", "kilowatts": "kW",
    "litre": "litres", "litres": "litres", "liter": "litres", "liters": "litres",
    "kilogram": "kg", "kilograms": "kg", "kg": "kg", "gb": "GB", "mb": "MB",
}
_DATA_PERIODS = (
    "monday tuesday wednesday thursday friday saturday sunday",
    "january february march april may june july august september october november december",
)
_DATA_PERIOD_ABBREVIATIONS = {period: period[:3].title()
                              for cycle in _DATA_PERIODS for period in cycle.split()}
_DATA_LABEL_STOP = STOPWORDS | {
    "from", "to", "versus", "vs", "rose", "grew", "fell", "increased", "decreased",
    "produced", "generated", "cost", "costs", "used", "uses", "reached", "remained",
    "percent", "dollars", "pounds", "euros", "minus", "negative",
} | set(_DATA_SMALL) | set(_DATA_SCALES)


def dataviz_claim(narration, g):
    tokens = list(re.finditer(r"[$£€]|[+\-−]?\d+(?:,\d{3})*(?:\.\d+)?|%|[a-z]+(?:-[a-z]+)*",
                              narration, re.I))
    quantities, i = [], 0
    word_spans = list(re.finditer(r"\S+", narration))
    while i < len(tokens):
        start, j, prefix = i, i, ""
        if tokens[j].group() in ("$", "£", "€"):
            prefix = tokens[j].group()
            j += 1
        sign = 1
        if j < len(tokens) and tokens[j].group().lower() in ("minus", "negative", "plus", "positive"):
            sign, j = -1 if tokens[j].group().lower() in ("minus", "negative") else 1, j + 1
        if j >= len(tokens):
            break
        token = tokens[j].group().lower()
        if re.fullmatch(r"[+\-−]?\d[\d,]*(?:\.\d+)?", token):
            value = Decimal(token.replace(",", "").replace("−", "-")) * sign
            j += 1
            if j < len(tokens) and tokens[j].group().lower() in _DATA_SCALES:
                value *= _DATA_SCALES[tokens[j].group().lower()]
                j += 1
        elif token in _DATA_SMALL or all(p in _DATA_SMALL for p in token.split("-")):
            total, part, consumed = 0, 0, False
            while j < len(tokens):
                w = tokens[j].group().lower()
                if w == "and" and j + 1 < len(tokens) and part and tokens[j + 1].group().lower() in _DATA_SMALL and part % 100 == 0:
                    j += 1
                    continue
                if w in _DATA_SCALES:
                    scale = _DATA_SCALES[w]
                    if scale < 1000:
                        part = (part or 1) * scale
                    else:
                        total += (part or 1) * scale
                        part = 0
                elif all(p in _DATA_SMALL for p in w.split("-")):
                    if consumed and part % 100 and not (part % 100 >= 20 and part % 10 == 0):
                        break
                    part += sum(_DATA_SMALL[p] for p in w.split("-"))
                else:
                    break
                consumed, j = True, j + 1
            value = Decimal(total + part)
            if j < len(tokens) and tokens[j].group().lower() == "point":
                k, digits = j + 1, ""
                while k < len(tokens) and tokens[k].group().lower() in _DATA_SMALL and _DATA_SMALL[tokens[k].group().lower()] < 10:
                    digits += str(_DATA_SMALL[tokens[k].group().lower()])
                    k += 1
                if digits:
                    value, j = value + Decimal("0." + digits), k
            if j < len(tokens) and tokens[j].group().lower() in _DATA_SCALES:
                value *= _DATA_SCALES[tokens[j].group().lower()]
                j += 1
            value *= sign
        else:
            i += 1
            continue
        unit = prefix
        if j < len(tokens) and tokens[j].group().lower() in _DATA_UNITS:
            unit = _DATA_UNITS[tokens[j].group().lower()]
            j += 1
            if unit == "%" and j < len(tokens) and tokens[j].group().lower() == "points":
                unit, j = "percentage points", j + 1
        left, right = tokens[start].start(), tokens[j - 1].end()
        before = narration[:left]
        qualifier = re.search(r"\b(about|roughly|approximately|nearly|up to|at least|at most|more than|less than)\s*$", before, re.I)
        period = ""
        dates = re.findall(r"\b(?:in|during|by|since)\s+(\d{4})\b", before, re.I)
        if dates:
            period = dates[-1]
        for periods in _DATA_PERIODS:
            found = re.findall(r"\b(" + "|".join(periods.split()) + r")\b", before, re.I)
            if found:
                period = found[-1]
        is_date = (not unit and value == int(value) and 1800 <= value <= 2200
                   and bool(re.search(r"\b(?:in|during|by|since|year)\s*$", before, re.I)))
        word_index = next((n for n, w in enumerate(word_spans) if w.end() > tokens[start].start()), 0)
        word_end = next((n for n, w in enumerate(word_spans) if w.start() >= right), len(word_spans))
        after = narration[right:]
        label_match = re.match(r"\s+([a-z]+(?:\s+[a-z]+)?)", after, re.I)
        label, measure = "", ""
        if label_match:
            tail = label_match.group(1).split()
            if tail[0].lower() not in _DATA_LABEL_STOP:
                label = " ".join(w for w in tail if w.lower() not in _DATA_LABEL_STOP)
                measure = tail[0].lower() if not unit else ""
        if not label:
            clause = re.split(r"\b(?:and|while|versus|vs)\b|[,.;:]", before, flags=re.I)[-1]
            label = " ".join(w for w in re.findall(r"[a-z]+", clause, re.I)
                             if w.lower() not in _DATA_LABEL_STOP)[-24:]
        source = narration[left:right]
        quantities.append({"value": str(value), "unit": unit, "label": label, "measure": measure,
                           "signed": bool(re.match(r"[$£€]?[+\-−]|minus|negative|plus|positive", source, re.I)),
                           "qualifier": qualifier.group(1) if qualifier else "",
                           "period": period, "role": "date" if is_date else "measure",
                           "span": [left, right], "source": source, "word_start": word_index, "word_end": word_end,
                           "anchor": g[min(word_index, len(g) - 1)]["text"] if g else tokens[start].group()})
        i = j
    measured = [q for q in quantities if q["role"] == "measure"]
    kind = "NONE"
    if measured:
        kind = "STAT" if len(measured) == 1 else "READOUTS"
        units = {q["unit"] for q in measured if q["unit"]}
        if len(units) == 1:
            for q in measured:
                if not q["unit"] and not q["measure"]:
                    q["unit"] = next(iter(units))
        compatible = len({q["unit"] for q in measured}) == 1
        if len(measured) == 1 and measured[0]["unit"] == "%" and not re.search(
                r"\b(increase[ds]?|decrease[ds]?|rose|fell|growth|grew|change[ds]?|interest|return|inflation|"
                r"discount|cheaper|higher|lower|faster|slower|larger|smaller)\b", narration, re.I):
            kind = "SHARE"
        elif len(measured) == 2 and re.fullmatch(
                r"\s*(?:" + re.escape(measured[0]["measure"]) + r"\s+)?(?:out of|in)\s+(?:every\s+)?",
                narration[measured[0]["span"][1]:measured[1]["span"][0]], re.I):
            if compatible and Decimal(measured[1]["value"]) > 0 and 0 <= Decimal(measured[0]["value"]) <= Decimal(measured[1]["value"]):
                kind = "SHARE"
        elif len(measured) == 2 and compatible and re.search(r"\b(from|versus|vs|compared|than|while|now|before|after)\b", narration, re.I):
            kind = "COMPARISON"
        elif len(measured) >= 3 and compatible and all(q["period"] for q in measured):
            periods = [q["period"].lower() for q in measured]
            indices = ([int(p) for p in periods] if all(p.isdigit() for p in periods) else
                       next(([s.split().index(p) for p in periods] for s in _DATA_PERIODS
                             if all(p in s.split() for p in periods)), []))
            gaps = [b - a for a, b in zip(indices, indices[1:])]
            labels = [set(w for w in re.findall(r"[a-z]+", q["label"].lower())
                          if w not in _DATA_LABEL_STOP and w not in _DATA_PERIOD_ABBREVIATIONS)
                      for q in measured]
            subjects = [label for label in labels if label]
            same_subject = not subjects or bool(set.intersection(*subjects))
            if gaps and len(set(gaps)) == 1 and gaps[0] > 0 and same_subject:
                kind = "TREND"
    return {"kind": kind, "quantities": measured, "source_quantities": quantities}


def dataviz_value(q):
    value = format(Decimal(q["value"]), ",f")
    if re.match(r"[$£€]?\+|plus|positive", q["source"], re.I):
        value = "+" + value
    unit = q["unit"]
    return (unit + value if unit in ("$", "£", "€") else
            value + unit if unit in ("%", "x") else value + (" " + unit if unit else ""))


def dataviz_steps(narration):
    steps = [m.start() for m in re.finditer(r"\b(?:first|second|third|then|next|finally)\b", narration, re.I)]
    if len(steps) < 2 or steps[0] != 0 or len(steps) > 5:
        return []
    return [clean(narration[a:b]).strip(" .,;:") for a, b in zip(steps, steps[1:] + [len(narration)])]


def dataviz_units(g, claim=None):
    if len(g) <= 11:
        return sketch_units(g)
    claim = claim or dataviz_claim(" ".join(w["text"] for w in g), g)
    qs = claim["quantities"]
    spans = []
    if qs and claim["kind"] in ("COMPARISON", "SHARE", "STAT"):
        hi = min(len(g), qs[-1]["word_end"] + bool(qs[-1]["measure"]))
        lo = max(0, qs[0]["word_start"] - 4, hi - 10)
        if lo <= qs[0]["word_start"]:
            spans = [(0, lo), (lo, hi), (hi, len(g))]
    if not spans:
        start = 0
        for i, w in enumerate(g):
            if CLAUSE_END.search(w["text"]) or ";" in w["text"]:
                spans.append((start, i + 1))
                start = i + 1
        if start < len(g):
            spans.append((start, len(g)))
    chunks = []
    dangling = {"a", "an", "the", "of", "to", "from", "and", "or", "in", "over", "with", "by", "for"}
    for a, b in spans:
        while a < b:
            numeric = any(a <= q["word_start"] < b for q in qs)
            stop = min(b, a + (10 if numeric else 5))
            if b - stop == 1 and stop - a < 10:
                stop = b
            while stop < b and stop > a + 2 and word_key(g[stop - 1]["text"]) in dangling:
                stop -= 1
            for q in qs:
                end = min(len(g), q["word_end"] + bool(q["measure"]))
                if q["word_start"] < stop < end:
                    stop = q["word_start"] if q["word_start"] > a else end
            chunks.append((a, stop))
            a = stop
    units, heroes = [], 0
    for i, (a, b) in enumerate(chunks):
        span = g[a:b]
        promoted = heroes < 1 and any(a <= q["word_start"] < b for q in qs)
        heroes += promoted
        units.append({
            "text": " ".join(w["text"] for w in span),
            "role": "hero" if promoted else "support", "anchor_word": span[0]["text"],
            "emphasis": 0.95 if promoted else 0.55,
            "semantic_role": "punch" if promoted else "setup" if i == 0 else "qualifier",
            "can_promote": promoted, "reveal": "WORD_CASCADE",
            "stress": [w["text"] for k, w in enumerate(span, a)
                       if re.search(r"\d", w["text"]) or
                       any(q["word_start"] <= k < q["word_end"] for q in qs)],
        })
    return units


def dataviz_beat(g, bi, n, media):
    narration = clean(" ".join(w["text"] for w in g))
    claim = dataviz_claim(narration, g)
    qs, kind = claim["quantities"], claim["kind"]
    if not qs:
        steps = dataviz_steps(narration)
        if steps:
            return {
                "beat_id": f"b{bi+1:02d}", "beat_type": "SETUP" if bi == 0 else "PAYOFF" if bi == n - 1 else "EXPLANATION",
                "pattern": "PAYOFF_LOCKUP" if bi == n - 1 else "PROGRESSIVE_HERO_BUILD",
                "dominant_layer": "DATA", "narration": narration, "energy": 0.55,
                "display_units": dataviz_units(g), "data": {"kind": "SEQUENCE", "value": " | ".join(steps)},
            }
        beat = sketch_beat(g, bi, n, set(), media)
        beat["illustration"]["confirmation"] = False
        return beat
    beat = {
        "beat_id": f"b{bi+1:02d}", "beat_type": "SETUP" if bi == 0 else "PAYOFF" if bi == n - 1 else "EXPLANATION",
        "pattern": "PAYOFF_LOCKUP" if bi == n - 1 else "PROGRESSIVE_HERO_BUILD",
        "dominant_layer": "HYBRID", "narration": narration, "energy": 0.55, "complexity": 0.5,
        "display_units": dataviz_units(g, claim), "data_claim": claim,
    }
    entities, ops = [], []

    def draw(q, glyph, params, label=""):
        eid = f"datum{len(entities) + 1}"
        entities.append({"id": eid, "kind": "evidence", "glyph": glyph, "size": "support" if glyph == "BAR" else "hero",
                         "params": params, **({"label": label} if label else {})})
        ops.append({"op": "DRAW", "target": eid, "at": {"unit": 0}, "duration_ms": 240})
        return eid

    def land(q, op, eid, value_from=0, value_to=1, params=None):
        start, end = q["word_start"], q["word_end"]
        duration = max(120, min(600, g[end - 1]["end_ms"] - g[start]["start_ms"]))
        ops.append({"op": op, "target": eid, "at": {"word": q["anchor"]},
                    "duration_ms": duration, "from": value_from, "to": value_to,
                    "params": {"end_on_word": True, "word_index": start, "word_span": end - start,
                               **(params or {})}})

    def readouts():
        if len(qs) == 1:
            beat["data"] = {"kind": "STAT", "value": dataviz_value(qs[0]),
                            "label": clean(qs[0]["qualifier"] + " " + qs[0]["label"])}
        elif len(qs) == 2:
            beat["data"] = {"kind": "COMPARISON", "value": dataviz_value(qs[0]), "secondary": dataviz_value(qs[1]),
                            "label": " / ".join(dict.fromkeys(q["label"] for q in qs if q["label"]))}
        else:
            beat["data"] = {"kind": "SEQUENCE", "value": " | ".join(
                clean((q["period"] or q["label"]) + ": " + dataviz_value(q)) for q in qs)}

    values = [Decimal(q["value"]) for q in qs]
    if kind == "COMPARISON" and all(v > 0 for v in values) and not any(q["qualifier"] or q["signed"] for q in qs):
        ceiling = max(values)
        before_after = bool(re.search(r"\bfrom\b.+\bto\b", narration, re.I))
        for i, q in enumerate(qs):
            level = float(values[i] / ceiling)
            # Below the native stroke floor, a bar would exaggerate its datum.
            if level < 0.02:
                entities, ops = [], []
                break
            label = ("Before" if i == 0 else "After") if before_after else q["label"].split()[-1] if q["label"] else ""
            measure = q["label"].split()[-1] if not q["unit"] and q["label"] else ""
            eid = draw(q, "BAR", {"level": level, "value": float(values[i])}, clean(label + " " + dataviz_value(q) + " " + measure)
                       if before_after else clean(label + " " + dataviz_value(q)))
            land(q, "GROW", eid, value_to=level)
            # Source-bound attention: each observed bar changes to the
            # editorial accent only when its value is spoken.
            land(q, "INK", eid)
            if i == 1:
                previous = next((e["id"] for e in entities if e["glyph"] == "BAR"), None)
                if previous and previous != eid:
                    land(q, "DIM", previous, value_to=0.66)
    elif kind == "SHARE" and not any(q["qualifier"] or q["signed"] for q in qs):
        share = values[0] / (100 if len(qs) == 1 else values[1])
        if 0 < share <= 1:
            params = {"level": float(share)}
            whole = values[0] > 0 and values[0] == int(values[0]) and "." not in qs[0]["value"]
            if whole:
                params.update(count=int(values[0]), suffix="%" if len(qs) == 1 else " in " + dataviz_value(qs[1]))
            eid = draw(qs[0], "DONUT", params)
            land(qs[0], "GROW", eid, value_to=float(share))
            if whole:
                land(qs[0], "COUNT", eid)
            else:
                beat["data"] = {"kind": "STAT", "value": dataviz_value(qs[0]), "label": qs[0]["label"]}
    elif kind == "TREND" and len(qs) <= 4 and all(v >= 0 for v in values) and max(values) > 0 and not any(q["qualifier"] or q["signed"] for q in qs):
        eid = "trend"
        entities.append({"id": eid, "kind": "evidence", "glyph": "CHART_LINE", "size": "hero",
                         "params": {"points": [float(v / max(values)) for v in values],
                                    "value_labels": [dataviz_value(q) for q in qs]}})
        # Stage the empty axis while the premise is spoken; actual measured
        # values still draw ONLY when their corresponding quantities are said.
        ops.append({"op": "DRAW", "target": eid,
                    "at": {"word": g[0]["text"]}, "duration_ms": 300})
        land(qs[0], "DIM", eid)
        for i, q in enumerate(qs):
            land(q, "GROW", eid, params={"point_index": i})
            pid = f"point{i + 1}"
            entities.append({"id": pid, "kind": "evidence", "glyph": "PILL", "size": "support",
                             "params": {"value": float(values[i]), "plain_datum": True},
                             "label": clean(_DATA_PERIOD_ABBREVIATIONS.get(q["period"].lower(), q["period"])
                                            + " " + dataviz_value(q))})
            land(q, "DIM", pid)
    elif kind == "STAT" and values[0] > 0 and values[0] == int(values[0]) and "." not in qs[0]["value"] and not (qs[0]["qualifier"] or qs[0]["signed"]):
        q, unit = qs[0], qs[0]["unit"]
        params = {"count": int(values[0]), "caption": q["label"], "tone": "dark"}
        if unit in ("$", "£", "€"):
            params["prefix"] = unit
        elif unit:
            params["suffix"] = unit if unit in ("%", "x") else " " + unit
        eid = draw(q, "COUNTER", params)
        land(q, "COUNT", eid)
    if entities:
        beat["illustration"] = {"form": "DATA_VISUAL" if any(e["glyph"] in ("BAR", "CHART_LINE") for e in entities) else "OBJECT_STAGE",
                                "entities": entities, "relations": [], "program": ops, "confirmation": False,
                                **({"label_space": True} if any(e["glyph"] == "CHART_LINE" for e in entities) else {})}
    elif len(qs) <= 5:
        readouts()
        beat["dominant_layer"] = "DATA"
    else:
        beat = sketch_beat(g, bi, n, set(), media)
        beat["illustration"]["confirmation"] = False
        return beat
    return beat


def dataviz_groups(words):
    groups = sketch_groups(words)
    i = 0
    while i < len(groups):
        candidates = []
        for group in groups[i:i + 5]:
            claim = dataviz_claim(" ".join(w["text"] for w in group), group)
            if not claim["quantities"] or not all(q["period"] for q in claim["quantities"]):
                break
            candidates.append(group)
        for count in range(len(candidates), 1, -1):
            combined = [w for group in candidates[:count] for w in group]
            claim = dataviz_claim(" ".join(w["text"] for w in combined), combined)
            if claim["kind"] == "TREND" and len(combined) <= 28:
                groups[i:i + count] = [combined]
                break
        i += 1
    return groups


def dataviz_continuity(beats):
    source = None
    for beat in beats:
        claim = beat.get("data_claim") or {}
        illustration = beat.get("illustration")
        if source:
            previous = source["data_claim"]
            known = {(q["value"], q["unit"]) for q in previous["quantities"]}
            repeated = all((q["value"], q["unit"]) in known for q in claim.get("quantities", []))
            context = lambda text: {word_key(w) for phrase in sketch_noun_phrases(text)
                                    for w in phrase.split() if word_key(w) not in STOPWORDS}
            related = bool(context(source["narration"]) & context(beat["narration"]))
            reference = bool(re.match(
                r"^(?:(?:that|this) (?:share|figure|number|result|increase|decrease|growth|change|comparison|trend|total|rate)"
                r"|(?:these|those) (?:figures|numbers|results)|the same (?:share|figure|number|result|total|rate))\b",
                beat["narration"], re.I))
            if repeated and (related or reference):
                source["illustration"]["persist_to"] = beat["beat_id"]
                carried = json.loads(json.dumps(source["illustration"]))
                carried.pop("persist_to", None)
                carried["carry"] = {"from_beat": source["beat_id"],
                                    "entities": [e["id"] for e in carried["entities"]]}
                carried["program"] = [{"op": "DIM", "target": e["id"], "at": {"unit": 0},
                                       "duration_ms": 240, "from": 1, "to": .9}
                                      for e in carried["entities"]]
                beat["illustration"] = carried
                beat.pop("data", None)
                beat["dominant_layer"] = "HYBRID"
                beat["data_context_from"] = source["beat_id"]
                continue
        source = beat if illustration and claim.get("quantities") else None


_SKETCH_ACTION = re.compile(
    r"\b(sends?|feeds?|flows?|transfers?|carr(?:y|ies|ied)|"
    r"sticks? to|attaches? to|helps?|makes?|produces?|leads? to|"
    r"connects? to|links? to|improves?|reduces?|increases?|enables?|"
    r"becomes?|changes? into)\b", re.I
)
_SKETCH_INTERFACE = re.compile(
    r"\b(search (?:field|box|results)|type (?:in|into|the word)|"
    r"enter (?:in|into|the word)|filter (?:the )?results|"
    r"select (?:a |the )?(?:category|option|field)|"
    r"choose (?:a |the )?(?:category|option|field))\b", re.I
)
_SKETCH_NEGATION = re.compile(r"\b(not|never|without|no|cannot|can't|doesn't|don't)\b", re.I)


def sketch_units(gwords: list[dict[str, Any]]) -> list[dict[str, Any]]:
    qualifiers = {word_key(w) for w in (
        "but", "not", "never", "without", "no", "cannot", "can't", "doesn't", "don't", "less", "more")}
    text = clean(" ".join(w["text"] for w in gwords))
    action_words = {word_key(m.group().split()[0]) for m in _SKETCH_ACTION.finditer(text)}
    keys = [word_key(w["text"]) for w in gwords]
    cuts = [i for i in range(2, len(gwords) - 1)
            if len(gwords) - i <= 7 and keys[i] not in keys[:i]]
    cut = next((i for i in cuts if keys[i] in qualifiers), None)
    if cut is None:
        cut = next((i for i in cuts if keys[i] in action_words), None)
    spans = [gwords[:cut], gwords[cut:]] if cut is not None else [gwords]
    units = []
    for i, span in enumerate(spans):
        promoted = i == len(spans) - 1
        units.append({
            "text": clean(" ".join(w["text"] for w in span)),
            "role": "hero" if promoted else "support", "anchor_word": span[0]["text"],
            "emphasis": 0.95 if promoted else 0.55,
            "semantic_role": "punch" if promoted else "setup",
            "can_promote": promoted, "reveal": "WORD_CASCADE",
            "stress": [w["text"] for w in span
                       if word_key(w["text"]) in qualifiers | action_words
                       or re.fullmatch(r"can|may|necessarily|usually|about", word_key(w["text"]))],
        })
    return units


def sketch_groups(words):
    compiler_path = str(ROOT / "compiler")
    if compiler_path not in sys.path:
        sys.path.insert(0, compiler_path)
    from editorial_plan_compiler.compiler import _cascade_settle_ms
    from editorial_plan_compiler.master_timeline import OUTGOING_SHARE
    from editorial_plan_compiler.timing import exit_for_pause, readable_close_floor

    groups, group = [], []
    for i, w in enumerate(words):
        group.append(w)
        gap = words[i + 1]["start_ms"] - w["end_ms"] if i + 1 < len(words) else 9999
        if CLAUSE_END.search(w["text"]) or gap >= 650 or (len(group) >= 13 and CLAUSE_MID.search(w["text"])):
            groups.append(group)
            group = []
    if group:
        groups.append(group)
    # Merge adjacent related claims only when the second action depends on
    # context from the first. Retain an initial setup cut for three-claim arcs.
    def nouns(group):
        return {re.sub(r"^(?:another|different) ", "", p.lower())
                for p in sketch_noun_phrases(" ".join(w["text"] for w in group))}
    if len(groups) >= 3:
        i = 1
        while i < len(groups) - 1:
            if len(groups[i] + groups[i + 1]) <= 20 and nouns(groups[i]) & nouns(groups[i + 1]):
                groups[i:i + 2] = [groups[i] + groups[i + 1]]
            else:
                i += 1
    elif len(groups) == 2:
        text_a = " ".join(w["text"] for w in groups[0]).lower()
        text_b = " ".join(w["text"] for w in groups[1]).lower()
        # Short, explicitly source-linked action chains stay in one moving
        # visual argument rather than cutting a few milliseconds after the
        # second action; no artificial duration is added to the voice.
        attachment_then_carry = (
            re.search(r"\b(sticks? to|attaches? to)\b", text_a)
            and re.search(r"\b(carries|carry|transfers|transfer)\b", text_b))
        transfer_then_feed = (
            re.search(r"\b(sends?|transfers?|flows?)\b", text_a)
            and re.search(r"\b(feeds?|delivers?)\b", text_b))
        if (len(groups[0] + groups[1]) <= 20
                and (attachment_then_carry or transfer_then_feed)
                and nouns(groups[0]) & nouns(groups[1])):
            groups = [groups[0] + groups[1]]
    return groups


_SKETCH_NLP: Any = None
_SKETCH_ASSETS: set[str] | None = None
_SKETCH_ICON_FAMILIES = (
    "icon-park-outline", "lucide", "mingcute", "tabler", "carbon",
    "ri", "healthicons", "ant-design", "icon-park-color",
)
_SKETCH_FALSE_FRIEND_ASSETS = {
    "icon.icon-park-color.shade",        # umbrella, not cast shade
    "icon.icon-park-color.label",        # bookmark, not a physical label
    "icon.icon-park-color.instruction",  # code editor, not an instruction sent to a device
}


def sketch_noun_phrases(text):
    """Extract source-mentioned actors/objects without requiring a spaCy model.

    In production the small English model is optional, so a fallback must not
    accidentally turn articles or conjunctions into drawable entities. It
    takes subjects, determiner phrases and objects of source action verbs,
    preserving source order and never inventing unnamed objects.
    """
    global _SKETCH_NLP
    if _SKETCH_NLP is None:
        try:
            import spacy
            _SKETCH_NLP = spacy.load("en_core_web_sm", disable=["ner"])
        except (ImportError, OSError):
            _SKETCH_NLP = False
    if _SKETCH_NLP:
        return [chunk.text for chunk in _SKETCH_NLP(text).noun_chunks]
    articles = {"a", "an", "the", "this", "that", "each", "every", "some"}
    qualifiers = {"another", "different"}
    modifiers = {"better", "lower", "unknown", "paper"}
    verbs = {"sends", "send", "feeds", "feed", "flows", "flow", "transfers",
             "transfer", "carries", "carry", "carried", "sticks", "stick",
             "attaches", "attach", "connects", "connect", "helps", "help",
             "makes", "make", "produces", "produce", "improves", "improve",
             "reduces", "reduce", "increases", "increase", "enables", "enable",
             "becomes", "become", "changes", "change", "prints", "print",
             "visits", "visit", "enters", "enter", "goes", "go", "holds",
             "hold", "stores", "store", "dries", "dry", "means", "mean",
             "solving", "solve", "succeeds", "succeed", "grows", "grow"}
    preps = {"to", "for", "from", "into", "with", "without", "of", "than"}
    stop = articles | {"and", "or", "but", "not", "no", "never", "necessarily",
                       "can", "cannot", "does", "do", "is", "are", "was",
                       "were", "then", "every", "so", "in", "on", "at",
                       "by", "its", "it", "their", "more", "less"}
    matches = []
    for clause in re.split(r"[.!?;]+", text.lower()):
        tokens = re.findall(r"[a-z]+(?:'[a-z]+)?", clause)
        if not tokens:
            continue
        candidates = []
        def emit(start, word, phrase=None):
            if word in stop or word in verbs or word in preps or word in qualifiers:
                return
            candidates.append((start, phrase or word))
        for i, token in enumerate(tokens):
            if token in articles | qualifiers and i + 1 < len(tokens):
                j = i + 1
                if tokens[j] in articles or tokens[j] in preps or tokens[j] in verbs:
                    continue
                # An adjectival modifier is not an independent object.
                if tokens[j] in modifiers and j + 1 < len(tokens) and tokens[j+1] not in verbs | stop:
                    j += 1
                name = tokens[j]
                phrase = ("another " + name) if token in qualifiers else (
                    ("better " + name) if i + 1 < j and tokens[i+1] == "better" else name)
                emit(i, name, phrase)
            if token in verbs:
                j = i+1
                while j < len(tokens) and tokens[j] in articles | preps | stop:
                    j += 1
                if j < len(tokens):
                    if tokens[j] in modifiers and j + 1 < len(tokens) and tokens[j+1] not in verbs | stop:
                        j += 1
                    emit(j, tokens[j], ("better " + tokens[j]) if j>0 and tokens[j-1]=="better" else None)
        first = 0
        while first < len(tokens) and tokens[first] in articles:
            first += 1
        if first < len(tokens):
            subj = first
            if tokens[subj] in modifiers and subj+1<len(tokens) and tokens[subj+1] not in verbs:
                subj += 1
            emit(subj, tokens[subj])
        matches.extend(candidates)
    # Stable order; preserve repeated noun with only one graph identity.
    result, seen = [], set()
    for _, name in sorted(matches, key=lambda p: p[0]):
        if name not in seen:
            result.append(name)
            seen.add(name)
    return result


def sketch_asset(phrase, text):
    global _SKETCH_ASSETS
    if _SKETCH_ASSETS is None:
        from editorial_plan_compiler.illustration import IllustrationRegistry
        registry = IllustrationRegistry()
        _SKETCH_ASSETS = {
            aid for aid, asset in registry.items.items()
            if asset.get("family") in ("icon", "colour-icon")
            and str(asset.get("eligibility", "")).startswith("eligible-")
            and aid not in registry.quarantined
            and (registry._roots[aid] / asset["path"]).is_file()
        }
    key = PHRASES.get(phrase, phrase)
    if _POLYSEME_VETO.get(key, set()) & set(re.findall(r"\w+", text.lower())):
        return None
    slugs = [phrase.replace(" ", "-")]
    if len(phrase.split()) == 1 and phrase.endswith("s") and not phrase.endswith("ss"):
        # Try literal registered singular art, never semantically substitute.
        if phrase.endswith("ies") and len(phrase) > 4:
            slugs.append(phrase[:-3] + "y")
        else:
            slugs.append(phrase[:-1])
    if len(phrase.split()) == 1 and phrase.endswith("s") and _SKETCH_NLP:
        noun = next((w for w in _SKETCH_NLP(text)
                     if w.text.lower() == phrase and w.pos_ == "NOUN"), None)
        if noun and noun.lemma_ != phrase:
            slugs.append(noun.lemma_.replace(" ", "-"))
    for slug in dict.fromkeys(slugs):
        for family in _SKETCH_ICON_FAMILIES:
            ref = f"icon.{family}.{slug}"
            if ref in _SKETCH_ASSETS and ref not in _SKETCH_FALSE_FRIEND_ASSETS:
                return ref
    ref = BANK.get(key, {}).get("mono")
    suffix = (ref or "").rsplit(".", 1)[-1]
    if ref in _SKETCH_ASSETS and (suffix in slugs or (phrase == "bicycle" and suffix == "bike")):
        return ref
    return None


def sketch_entities(gwords, media):
    text = clean(" ".join(w["text"] for w in gwords))
    candidates = sketch_noun_phrases(text)
    # Unrecognised nouns keep their source label rather than a guessed depiction.
    if not candidates:
        candidates = [w["text"] for w in gwords if word_key(w["text"]) in BANK]
    entities: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in candidates:
        if re.match(r"^(?:not|never|no)\b", candidate, re.I):
            continue
        distinct = bool(re.match(r"^(?:another|different)\s", candidate, re.I))
        phrase = re.sub(r"^(?:a|an|the|this|that|some|each|every|another|different) ", "",
                        candidate, flags=re.I)
        if re.search(r"\bof\b", phrase, re.I):
            phrase = re.split(r"\bof\b", phrase, flags=re.I)[-1].strip()
        phrase = phrase.strip(" ,.;:!?\"'").lower()
        if phrase in {"a", "an", "the", "to", "of", "and", "but", "not", "every"}:
            continue
        entity_id = ("sk_another_" if distinct else "sk_") + re.sub(r"\W+", "_", phrase)
        if len(phrase.split()) > 3 or not phrase or entity_id in seen:
            continue
        if not re.search(rf"\b{re.escape(phrase)}\b", text, re.I):
            continue
        seen.add(entity_id)
        ref = sketch_asset(phrase, text)
        # When no licensed catalog symbol matches, use only narrowly defined
        # native procedural objects whose literal meaning equals the source
        # noun. Unrecognized nouns continue to have an honest word carrier.
        primitive = {"pump": "PUMP", "tank": "TANK"}.get(phrase)
        ent = {"id": entity_id, "kind": "object",
               "glyph": "TILE" if ref else (primitive or "PILL"),
               "size": "hero" if not entities else "support",
               "label": phrase, "phrase": phrase}
        if ref:
            ent["asset_ref"] = ref
        entities.append(ent)
        if len(entities) == 4:
            break
    for mi, _mf in media:
        entities.append({"id": f"media{mi+1}", "kind": "evidence",
                         "glyph": "MEDIA", "size": "support", "media_ref": f"media{mi+1}"})
    if not entities:
        # A source sentence with no safely identifiable object still gets a
        # truthful text carrier rather than an unrelated question/idea icon.
        phrase = " ".join(w["text"] for w in gwords[:3]).strip(" ,.;:!?")
        entities.append({"id": "sk_source", "kind": "object", "glyph": "PILL",
                         "size": "hero", "label": phrase, "phrase": phrase})
    return entities[:7]


def sketch_action_stages(narration: str, entities: list[dict[str, Any]]):
    stages: list[tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], str, str]] = []
    for clause_match in re.finditer(r"[^.!?;]+", narration):
        clause = clause_match.group()
        doc = _SKETCH_NLP(clause) if _SKETCH_NLP else None
        actions = list(_SKETCH_ACTION.finditer(clause))
        for i, action in enumerate(actions):
            before = clause[:action.start()]
            after = clause[action.end():actions[i + 1].start() if i + 1 < len(actions) else len(clause)]
            if _SKETCH_NEGATION.search(before):
                continue
            def mentioned(e: dict[str, Any], text: str) -> bool:
                return bool(e.get("phrase") and re.search(rf"\b{re.escape(e['phrase'])}\b", text, re.I))
            subjects = [e for e in entities if mentioned(e, before)]
            objects = [e for e in entities if mentioned(e, after)]
            if doc is not None:
                verb = next((t for t in doc if action.start() <= t.idx < action.end()
                             and t.pos_ == "VERB"), None)
                if verb is not None:
                    heads = [c for c in verb.children if c.dep_ == "nsubj"]
                    if not heads and verb.dep_ == "conj":
                        heads = [c for c in verb.head.children if c.dep_ == "nsubj"]
                    if heads:
                        subjects = [e for e in subjects if any(
                            mentioned(e, " ".join(t.text for t in head.subtree)) for head in heads)]
            if not subjects or not objects:
                continue
            if action.group().lower().startswith(("becom", "chang")):
                # "becomes stiffer" describes a state, not a named object.
                # Transformation drawings need an explicit nominal referent.
                trailing = after.strip().lower()
                if not re.match(r"^(?:a|an|the|another|different|this|that)\b", trailing):
                    continue
            # Conjoined verbs inherit the clause's subject, not the preceding
            # verb's destination. Use the earliest actor before the first verb.
            clause_subject = [e for e in entities if mentioned(e, clause[:actions[0].start()])]
            between = clause[actions[i-1].end():action.start()] if i else ""
            inherited = bool(i and re.search(r"\band\s*$", between, re.I))
            source = clause_subject[-1] if inherited and clause_subject else subjects[-1]
            # Explicit "X sends Y to Z" binds Z as the recipient and Y as the
            # transferred payload. A fallback that chooses the first object can
            # silently lose the Y -> Z leg in a multi-clause process.
            to_dest = re.search(r"\bto\s+(?:(?:a|an|the|another)\s+)?", after, re.I)
            destinations = [e for e in objects if to_dest and mentioned(e, after[to_dest.end():])]
            target = destinations[0] if destinations else (
                objects[-1] if to_dest else objects[0])
            if source is target:
                continue
            destination = re.search(rf"\b{re.escape(target['phrase'])}\b", after, re.I)
            before_destination = (after[:to_dest.start()] if destinations else
                                  after[:destination.start()] if destination else "")
            payload = [e for e in entities if e is not source and e is not target
                       and mentioned(e, before_destination)]
            cue = action.group().lower()
            if cue.startswith(("becom", "chang")):
                relation = "transforms_into"
            elif cue.startswith(("send", "feed", "flow", "transfer", "carr", "make", "produc")):
                relation = "flows_to"
            else:
                relation = "connects"
            if cue.startswith(("stick", "attach")):
                source, target = target, source
            stages.append((source, payload, target, relation, cue.split()[0]))
    return stages


def sketch_beat(gwords, bi, n, previous, media):
    bid = f"b{bi+1:02d}"
    narration = clean(" ".join(w["text"] for w in gwords))
    units = sketch_units(gwords)
    entities = sketch_entities(gwords, media)
    for ent in entities:
        if ent.get("label") and len(ent["label"].split()) > 1:
            ent["label"] = ent["label"].split()[-1]
    is_interface = bool(_SKETCH_INTERFACE.search(narration))
    stages = sketch_action_stages(narration, entities) if not is_interface else []
    if stages:
        # Store every edge by its stable authored entity IDs, not object
        # identity. A physical payload must traverse BOTH source -> payload and
        # payload -> destination; losing its second leg changes the claim.
        links_by_id: dict[tuple[str, str], tuple[dict[str, Any], dict[str, Any], str, str]] = {}
        for source, payload, target, relation, anchor in stages:
            chain = [source, *payload, target]
            added = 0
            for j, (left, right) in enumerate(zip(chain, chain[1:])):
                key = (left["id"], right["id"])
                if key not in links_by_id:
                    # When a previous verb established an attachment, the next
                    # action's FIRST NEW connection starts on its own verb
                    # ("carries"), not on an already-mentioned payload noun.
                    link_anchor = anchor if added == 0 else left["phrase"].split()[0]
                    links_by_id[key] = (left, right, relation, link_anchor)
                    added += 1
        links = list(links_by_id.values())
        for source, payload, target, _, _ in stages:
            if payload:
                chain = [source, *payload, target]
                missing = [(a["id"], b["id"]) for a, b in zip(chain, chain[1:])
                           if (a["id"], b["id"]) not in links_by_id]
                if missing:
                    raise ValueError(f"Sketch payload transport lost authored links: {missing}")
        if links:
            form = ("PROCESS_PIPELINE" if any(r == "flows_to" for _, _, r, _ in links)
                    else "STATE_TRANSFORMATION" if any(r == "transforms_into" for _, _, r, _ in links)
                    else "RELATIONSHIP")
            used = {e["id"] for left, right, _, _ in links for e in (left, right)}
            entities = [e for e in entities if e["id"] in used or e["kind"] == "evidence"]
            order = []
            for left, right, _, _ in links:
                for e in (left, right):
                    if e["id"] not in order:
                        order.append(e["id"])
            entities.sort(key=lambda e: order.index(e["id"]) if e["id"] in order else len(order))
            for e in entities:
                if e["kind"] != "evidence":
                    e["size"] = "support"
            links[0][0]["size"] = "hero"
            if len(entities) == 2 and form != "RELATIONSHIP":
                links[-1][1]["size"] = "hero"
            shared = {e["id"] for e in entities} & previous
            relations = [{"type": r, "source": a["id"], "target": b["id"], "style": "dash"}
                         for a, b, r, _ in links]
            program = [{"op": "DRAW", "target": e["id"], "at": {"word": gwords[0]["text"]},
                        "duration_ms": 500} for e in entities if e["id"] not in shared]
            for left, right, _, anchor in links:
                program.append({"op": "CONNECT", "target": f"{left['id']}->{right['id']}",
                                "at": {"word": anchor}, "duration_ms": 360})
            if len(program) > 10:
                raise ValueError("Sketch scene exceeds the native source-bound action budget")
            for _, _, target, _, anchor in stages:
                if len(program) == 10:
                    break
                program.append({"op": "INK", "target": target["id"],
                                "at": {"word": anchor}, "duration_ms": 300})
            illustration = {"form": form, "entities": entities, "relations": relations,
                            "program": program,
                            **({"carry": {"from_beat": f"b{bi:02d}", "entities": sorted(shared)}}
                               if shared else {})}
            return {
                "beat_id": bid,
                "beat_type": "SETUP" if bi == 0 else ("PAYOFF" if bi == n-1 else "EXPLANATION"),
                "pattern": "PAYOFF_LOCKUP" if bi == n-1 else "PROGRESSIVE_HERO_BUILD",
                "dominant_layer": "HYBRID",
                "narration": narration,
                "energy": 0.55 if bi == 0 else (0.75 if bi == n-1 else 0.65),
                "complexity": 0.5,
                "display_units": units,
                "illustration": illustration,
            }
    current = {e["id"] for e in entities}
    shared = current & previous
    carry = {"from_beat": f"b{bi:02d}", "entities": sorted(shared)} if shared else None
    form, relation = "OBJECT_STAGE", None
    compare = None
    source = target = None
    comparison_negation = None
    if not is_interface:
        compare = re.search(r"\b(versus|vs\.?|compared (?:with|to)|than|whereas|means?)\b", narration, re.I)
        if compare:
            before = [e for e in entities if e.get("phrase") and e["phrase"] in narration[:compare.start()].lower()]
            after = [e for e in entities if e.get("phrase") and e["phrase"] in narration[compare.end():].lower()]
            if before and after:
                source, target = before[-1], after[0]
                form, relation = "COMPARISON", "compares"
                comparison_negation = _SKETCH_NEGATION.search(narration[:compare.start()])
    if source and target:
        order = [source["id"], target["id"]]
        entities.sort(key=lambda e: order.index(e["id"]) if e["id"] in order else len(order))
        source["size"] = "hero"
        target["size"] = "support" if form == "RELATIONSHIP" else "hero"
    chain = [source, target] if source and target else []
    link_word = compare.group().split()[0] if compare else gwords[0]["text"]
    relations = [{"type": relation, "source": a["id"], "target": b["id"], "style": "dash"}
                 for a, b in zip(chain, chain[1:])]
    program = [
        {"op": "DRAW", "target": e["id"], "at": {"word": gwords[0]["text"]},
         "duration_ms": 500}
        for e in entities if e["id"] not in shared
    ]
    if source and target and relation:
        if comparison_negation:
            program.append({"op": "INK", "target": source["id"],
                            "at": {"word": source["phrase"].split()[0]}, "duration_ms": 300})
            program.append({"op": "DIM", "target": f"{source['id']}->{target['id']}",
                            "at": {"word": comparison_negation.group()}, "to": 0.3, "duration_ms": 300})
        for i, r in enumerate(relations):
            anchor = link_word if i == 0 else chain[i]["phrase"].split()[0]
            program.append({"op": "CONNECT", "target": f"{r['source']}->{r['target']}",
                            "at": {"word": anchor}, "duration_ms": 360})
        if not comparison_negation:
            program.append({"op": "INK", "target": target["id"],
                            "at": {"word": target["phrase"].split()[0]}, "duration_ms": 300})
    if not program:
        program.append({"op": "INK", "target": entities[0]["id"],
                        "at": {"word": gwords[0]["text"]}, "duration_ms": 300})
    illustration = {"form": form, "entities": entities, "relations": relations,
                    "program": program[:10], **({"carry": carry} if carry else {})}
    return {
        "beat_id": bid,
        "beat_type": "SETUP" if bi == 0 else ("PAYOFF" if bi == n-1 else "EXPLANATION"),
        "pattern": "PAYOFF_LOCKUP" if bi == n-1 else "PROGRESSIVE_HERO_BUILD",
        "dominant_layer": "HYBRID",
        "narration": narration,
        "energy": 0.55 if bi == 0 else (0.75 if bi == n-1 else 0.65),
        "complexity": 0.5,
        "display_units": units,
        "illustration": illustration,
    }


def build_treatment(args, style, words, media_files, film_id):
    # Style knobs beyond the six visual families: which housing the entity icons
    # wear (TILE/BADGE/CHIP...) and how their connectors draw (solid/dash/arc).
    glyph = style.get("glyph", "TILE")
    link_style = style.get("link_style")
    if style["id"] in ("sketch", "dataviz"):
        words = [{**w, "text": w["text"].strip()} for w in words]
    groups = (sketch_groups(words) if style["id"] == "sketch" else
              dataviz_groups(words) if style["id"] == "dataviz" else chunk_beats(words))
    if style.get("show") == "NEWSREEL":
        media_library = []
        for mi, p in enumerate(media_files):
            p = Path(p)
            kind = "VIDEO" if p.suffix.lower() in VIDEO_EXTS else "IMAGE"
            entry = {"asset_id": f"media{mi+1}", "kind": kind, "path": f"media/{p.name}"}
            wh = probe_dims(p, kind)
            if wh:
                entry["width"], entry["height"] = wh
                if kind == "VIDEO":
                    entry["duration_s"] = probe_dur(p)
            media_library.append(entry)
        return _newscast_treatment(args, style, words, groups, media_library, film_id)
    beats, used_kw, fallback_n, prev_keys = [], set(), 0, set()
    carry_id = carry_key = None
    fam = style["asset_family"]
    fam_key = {"colour_icons": "colour", "mono_icons": "mono", "emoji": "emoji", "photos": "photo"}[fam]
    # film-level topic vector: semantic matches rerank toward keys aligned
    # with what the narration is actually about
    ctx = None
    if _SEMANTIC:
        _ev = _sem_embed(" ".join(w["text"] for w in words))
        if _ev is not None:
            ctx = _ev[0]
    # Pre-pass: the film's ordered topic pool — every bank key any beat will
    # introduce, first-seen order. Float beats draw ambient members from it so
    # sparse narration still fills a cluster.
    film_keys: list = []
    if style.get("finish") == "FLOAT_FIELD":
        seen_k = set()
        for g in groups:
            for ent, _a in pick_entities(g, fam_key, set(), ctx, max_n=6):
                k = ent.get("bank_key")
                if k and k not in seen_k:
                    seen_k.add(k)
                    film_keys.append(k)
    media_iter = iter(enumerate(media_files))
    media_slots = {}
    for mi, mf in media_iter:
        slot = 1 + (mi % max(1, len(groups) - 2)) if len(groups) > 2 else mi % len(groups)
        media_slots.setdefault(slot, []).append((mi, mf))
    n = len(groups)
    sketch_previous = set()
    for bi, g in enumerate(groups):
        bid = f"b{bi+1:02d}"
        narration = clean(" ".join(w["text"] for w in g))
        if style["id"] == "sketch":
            beat = sketch_beat(g, bi, n, sketch_previous, media_slots.get(bi, []))
            if beats:
                beats[-1]["cut"] = "hard"
            beats.append(beat)
            sketch_previous = {e["id"] for e in beat["illustration"]["entities"]}
            continue
        if style["id"] == "dataviz":
            if beats:
                beats[-1]["cut"] = "hard"
            beats.append(dataviz_beat(g, bi, n, media_slots.get(bi, [])))
            continue
        # Float scenes lead with visuals — a beat gets a denser cluster (up to six
        # drawable concepts) so the field never reads as a lone text line. Topic
        # keys may re-enter after one beat off (the film keeps returning to its
        # subject); only the previous beat's set is banned, so clusters evolve
        # instead of repeating identically.
        is_float = style.get("finish") == "FLOAT_FIELD"
        is_journey = bool(style.get("journey"))
        is_collage = bool(style.get("collage"))
        is_dataviz = bool(style.get("dataviz"))
        # Look tuning: journey keeps a leaner field so the carried hero reads as
        # the thing travelling; collage packs the field dense like a media board.
        max_picked = 4 if is_journey else 6
        fill_to = 3 if is_journey else (6 if is_collage else 4)
        picked = pick_entities(g, fam_key, prev_keys if is_float else used_kw, ctx,
                               max_n=max_picked if is_float else 4)
        beat_keys = {ent.get("bank_key") for ent, _a in picked if ent.get("bank_key")}
        if not picked:
            fe = fallback_entity(fam_key, fallback_n, question="?" in narration)
            if fe:
                picked = [(fe, g[0]["text"])]
                fallback_n += 1
        if is_float and len(picked) < fill_to:
            # Sparse narration still leads with visuals: the field fills to the
            # look's target with rotating ambient members of the film's own topic
            # pool — keys the film already introduced, minus the previous beat's,
            # so the cluster keeps evolving instead of going minimal while the
            # voice runs.
            pool = [k for k in film_keys if k not in prev_keys and k not in beat_keys]
            for k in pool[(bi * 2) % len(pool):] + pool[:(bi * 2) % len(pool)] if pool else []:
                if len(picked) >= fill_to:
                    break
                spec = BANK[k]
                ref = spec.get(fam_key) or spec.get("colour")
                if not ref:
                    continue
                ent = {"id": f"e{len(picked)+1}_{k}", "kind": "object", "glyph": "TILE",
                       "phrase": k, "bank_key": k}
                if ref == spec.get("photo"):
                    ent["concept"] = ref
                else:
                    ent["asset_ref"] = ref
                picked.append((ent, g[min(len(g) - 1, 2 + len(picked))]["text"]))
                beat_keys.add(k)
        film_keys = [k for k in film_keys if k not in beat_keys] + [k for k in film_keys if k in beat_keys]
        prev_keys = beat_keys
        # Momentum handoff: the previous beat's hub entity id carries into this
        # beat — if the same concept was picked it keeps its id, otherwise it
        # rides in as an ambient member, so something always travels into the
        # new field instead of the scene dissolving.
        carry = None
        if is_float and carry_id and bi > 0:
            # The carried concept keeps its id across beats — if this beat picked
            # it naturally, rename it onto the carry id; else it rides in as an
            # ambient member, so something always travels into the new field.
            same = next((ent for ent, _a in picked
                         if ent.get("bank_key") == carry_key), None)
            if same is not None:
                same["id"] = carry_id
            else:
                spec = BANK.get(carry_key or "", {})
                ref = spec.get(fam_key) or spec.get("colour")
                if ref:
                    ent = {"id": carry_id, "kind": "object", "glyph": "TILE",
                           "phrase": carry_key, "bank_key": carry_key}
                    if ref == spec.get("photo"):
                        ent["concept"] = ref
                    else:
                        ent["asset_ref"] = ref
                    picked.append((ent, g[0]["text"]))
                else:
                    carry_id = None
            if carry_id:
                carry = {"from_beat": f"b{bi:02d}", "entities": [carry_id]}
        ents = []
        for ent, anchor in picked:
            ents.append([ent, anchor])
        if is_journey and carry_id:
            # Journey staging: the carried object leads the field — it is the
            # thing travelling through the film, so it takes the hero slot.
            ents.sort(key=lambda ea: 0 if ea[0].get("id") == carry_id else 1)
        medias = media_slots.get(bi, [])
        for mi, mf in medias:
            ents.insert(0, ([{"id": f"media{mi+1}", "kind": "evidence", "glyph": "MEDIA",
                              "media_ref": f"media{mi+1}"}, g[0]["text"]]))
        sizes = ["hero", "support", "minor", "support", "minor", "support", "minor"]
        ent_words = set()
        for ent, _a in ents:
            for w in (ent.get("phrase") or "").split():
                k = word_key(w)
                if k:
                    ent_words.add(k)
        units = display_units(g, ent_words)
        entities, program = [], []
        hub_done = False
        for ei, (ent, anchor) in enumerate(ents):
            if is_float and ent["glyph"] == "TILE":
                # Float grammar (reference format): the first icon entity is the
                # hub, brand marks wear the glossy white disc, and every
                # other concept becomes the dark UI bar with its name inside.
                ref = ent.get("asset_ref") or ""
                if not hub_done:
                    # A white disc like the rest — a dark hero disc reads as a
                    # distracting void, not the format's hub.
                    ent["glyph"] = "BADGE"
                    hub_done = True
                elif ref.startswith("brand.") or ei % 2 == 0:
                    # Brand marks always keep the glossy disc; other concepts
                    # alternate — a white icon disc or the dark bar that carries
                    # its name inside, the mix the reference format uses.
                    ent["glyph"] = "BADGE"
                else:
                    ent["glyph"] = "CHIP"
                    lbl = (ent.get("bank_key") or "").replace("-", " ")
                    if lbl and _label_ok(lbl, units):
                        ent["label"] = lbl
            elif ent["glyph"] == "TILE":
                ent["glyph"] = glyph
            ent["size"] = sizes[min(ei, len(sizes) - 1)]
            entities.append(ent)
            if ent["id"] == carry_id and carry:
                # A carried body is already drawn — re-drawing it would flash;
                # it only travels to its new box.
                continue
            program.append({"op": "DRAW", "target": ent["id"], "at": {"word": anchor},
                            "duration_ms": 550})
        hub_id = next((e["id"] for e in entities if e.get("kind") != "evidence"),
                      entities[0]["id"]) if entities else None
        if is_float:
            # The chain continues: this beat's hub id is what the next beat
            # carries forward.
            carry_hub = next((e for e in entities if e.get("kind") != "evidence"), None)
            if carry_hub is not None:
                carry_id = carry_hub["id"]
                carry_key = carry_hub.get("bank_key")
        for ei in range(1, len(entities)):
            tgt = (f"{hub_id}->{entities[ei]['id']}" if is_float
                   else f"{entities[ei-1]['id']}->{entities[ei]['id']}")
            program.append({"op": "CONNECT",
                            "target": tgt,
                            "at": {"word": ents[ei][1]}, "duration_ms": 560})
        if is_float and entities:
            # Controlled masterclass: every float beat keeps animating after the
            # cluster assembles. Two flourishes rotate through the op vocabulary
            # per beat (icon writes itself in accent, accent fill rises, the hub
            # emits a ring, a state flip pops) so consecutive scenes never
            # choreograph the same way. Anchors ride mid/late narration words —
            # motion stays tied to the voice.
            flourishes = ["INK", "FILL", "EMIT", "SWAP"]
            f1 = flourishes[bi % len(flourishes)]
            f2 = flourishes[(bi + 2) % len(flourishes)]
            mid_word = g[len(g) // 2]["text"]
            last_word = g[-1]["text"]
            program.append({"op": f1, "target": hub_id,
                            "at": {"word": mid_word}, "duration_ms": 440})
            sats = [e["id"] for e in entities if e["id"] != hub_id]
            if sats:
                program.append({"op": f2, "target": sats[bi % len(sats)],
                                "at": {"word": last_word}, "duration_ms": 480})
        if is_float:
            relations = [{"type": "connects", "source": hub_id,
                          "target": e["id"], "style": "stem"}
                         for e in entities
                         if e["id"] != hub_id and e.get("kind") != "evidence"]
        else:
            relations = [{"type": "connects",
                          "source": entities[i - 1]["id"],
                          "target": entities[i]["id"],
                          **({"style": link_style} if link_style else {})}
                         for i in range(1, len(entities))]
        if len(program) > 10:
            # The contract caps a beat's program at ten authored ops — keep the
            # cluster's entrances, then its stems, then flourishes if room is left.
            order = {"DRAW": 0, "CONNECT": 1}
            program = sorted(program, key=lambda o: order.get(o["op"], 2))[:10]
        btype = "SETUP" if bi == 0 else ("PAYOFF" if bi == n - 1 else "EXPLANATION")
        illustration = {"form": "OBJECT_STAGE", "entities": entities,
                        "relations": relations,
                        "program": program,
                        **({"carry": carry} if carry else {})}
        beats.append({
            "beat_id": bid,
            "beat_type": btype,
            "pattern": "PAYOFF_LOCKUP" if bi == n - 1 else "PROGRESSIVE_HERO_BUILD",
            "dominant_layer": "TEXT" if style.get("reveal") == "BLOCK" else "HYBRID",
            "narration": narration,
            "energy": 0.55 if bi == 0 else (0.75 if bi == n - 1 else 0.65),
            "complexity": 0.5,
            "display_units": units,
            "illustration": illustration,
        })
    if style["id"] == "dataviz":
        dataviz_continuity(beats)
    media_library = []
    for mi, p in enumerate(media_files):
        p = Path(p)
        kind = "VIDEO" if p.suffix.lower() in VIDEO_EXTS else "IMAGE"
        entry = {"asset_id": f"media{mi+1}", "kind": kind, "path": f"media/{p.name}"}
        wh = probe_dims(p, kind)
        if wh:
            entry["width"], entry["height"] = wh
            if kind == "VIDEO":
                entry["duration_s"] = probe_dur(p)
        media_library.append(entry)
    return {
        "schema": "NexStudioEditorialTreatmentV2",
        "film_id": film_id,
        "note": f"auto-authored by make_reel.py (style={style['id']})",
        "aspects": args.aspects.split(","),
        "fps": 30,
        **({"caption_policy": "kinetic"} if style["id"] == "dataviz" else {}),
        **({"director_style": style["id"]} if style["id"] in ("dataviz", "sketch") else {}),
        "brand": {**style["palette"], "finish": style["finish"]},
        "typography": {"reveal": style["reveal"], "tonal_ink": 0.42, "min_visual_share": 0.6},
        "voice": {"source": "MASTER", "audio_path": "voice.mp3",
                  "alignment_path": "alignment.json", "head_pad_ms": 350},
        "media_library": media_library,
        "beats": beats,
        **({"mood": style["mood"]} if style.get("mood") else {}),
        **({"sfx": style["sfx"]} if style.get("sfx") else {}),
    }


# ---------------- newscast: the numbered-section data-news reel ----------------

_NUM_RE = re.compile(r"(\d[\d,.]*\s*(?:(?:%|percent|x|k|m|b|bn|gb|tb|ms|s)\b)?)|([\$\u20ac\u00a3]\s?\d[\d,.]*)", re.I)
_VS_RE = re.compile(r"\b(vs\.?|versus|head to head|against|compared to|compared with)\b", re.I)
_PRICE_RE = re.compile(r"[\$€£]|\b(dollars?|euros?|pounds?|cents?|price[sd]?|costs?|pricing|fee|fees|usd|msrp)\b", re.I)
_NC_STOP = {"a", "an", "the", "and", "or", "but", "of", "to", "in", "on", "for", "with", "at", "by", "is", "it", "its", "this", "that", "these", "those", "be", "are", "was", "were", "as", "if", "then", "than", "so", "no", "not", "your", "you", "we", "our", "their", "they", "he", "she", "i", "s",
            "against", "versus", "vs", "head", "about", "into", "onto", "upon", "toward", "towards", "via", "per", "between", "during", "through", "throughout", "over", "under", "around", "across", "along", "amid", "among", "within", "without", "beyond", "behind", "beside", "inside", "outside", "off", "out", "away", "back", "ahead", "down", "up", "here", "there", "where", "when", "why", "how", "what", "who", "whom", "whose", "which", "anyone", "everyone", "someone", "anything", "everything", "something", "much", "many", "more", "most", "very", "just", "even", "still", "really", "actually", "basically", "way", "thing", "things", "stuff", "lot", "kind", "sort", "part", "new", "old", "own", "same", "other", "another", "such", "like", "yeah", "uh", "um", "gonna", "well", "now", "then", "also", "too"}
_SEQ_RE = re.compile(r"\b(first|then|next|finally|steps?|stages?|phases?|process|pipeline|setup|install|unbox|assembly|how to)\b", re.I)
_DATE_RE = re.compile(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{0,2}|\b(19|20)\d{2}\b(?!\s*(?:watts?|hours?|percent|%|x|kb?|mb|gb|tb|ms|s|wh|kwh|volts?|hz|fps|bits?|bytes?|px|mm|cm|kg|lbs?)\b)|\bmonday|tuesday|wednesday|thursday|friday|saturday|sunday\b", re.I)
_GENERIC_SECTIONS = ["SETUP", "DETAILS", "NUMBERS", "COMPARE", "ROLE", "PROOF", "VERDICT"]


def _nc_section(g, picked, used_names, bi, last):
    """Name a beat's section from its own content first, the bank key second, and a
    rotating generic last. Names dedupe against sections already used — adjacent
    repeats are fine but a section word should never re-surface non-adjacently."""
    text = " ".join(w["text"] for w in g).upper()
    if bi == 0:
        cand = "THE DROP"
    elif last:
        cand = "VERDICT"
    elif _VS_RE.search(text):
        cand = "HEAD TO HEAD"
    elif _PRICE_RE.search(text):
        cand = "PRICE"
    elif _DATE_RE.search(text):
        cand = "TIMELINE"
    elif _NUM_RE.search(text):
        cand = "THE NUMBERS"
    elif _SEQ_RE.search(text):
        cand = "HOW IT WORKS"
    else:
        cand = None
    cands = [c for c in [cand] if c]
    cands += [((ent.get("bank_key") or "").replace("-", " ").upper())[:14] for ent, _a in picked]
    cands += _GENERIC_SECTIONS[bi % len(_GENERIC_SECTIONS):] + _GENERIC_SECTIONS[:bi % len(_GENERIC_SECTIONS)]
    for c in cands:
        c = re.sub(r"[^A-Z0-9+&%$ ]", "", c).strip()[:14]
        if c and c not in used_names:
            used_names.add(c)
            return c
    return f"PART {bi + 1}"


def _nc_numbers(g):
    """Numbers with a short label carved from the words just before them."""
    out = []
    words = [w["text"] for w in g]
    joined = " ".join(words)
    for m in _NUM_RE.finditer(joined):
        raw = m.group(0).strip()
        if re.search(r"(st|nd|rd|th)\b", raw, re.I) or re.match(r"\s*(st|nd|rd|th)\b", joined[m.end():], re.I):
            continue  # ordinals are dates and ranks, not data
        num_txt = raw.replace(",", "")
        mm = re.match(r"([\$\u20ac\u00a3]?)\s*(\d[\d.]*)\s*(%|percent|x|k|m|b|bn|gb|tb|ms|s)?\b", num_txt, re.I)
        if not mm:
            continue
        pre, digits, suf = mm.group(1) or "", mm.group(2), (mm.group(3) or "").lower()
        try:
            val = float(digits)
        except ValueError:
            continue
        mult = {"k": 1e3, "m": 1e6, "b": 1e9, "bn": 1e9}.get(suf, 1)
        # Label = the thing measured: up to 2 content words after the number
        # ('499 dollars' → 'dollars', '799 category average' → 'category average').
        label_words = []
        for w in joined[m.end():].split()[:4]:
            w2 = w.strip(" ,.;:!?")
            lw = w2.lower()
            if lw in ("a", "an", "the", "of", "at", "in", "on", "for", "to", "by", "and", "or", "is", "was",
                      "than", "under", "over", "out", "up", "full", "enough", "a", "it", "its", "with", "per"):
                if label_words:
                    break
                continue
            if lw.endswith("ing") or lw.endswith("ed") or not w2 or w2[0].isdigit():
                break
            label_words.append(w2)
            if len(label_words) >= 2:
                break
        label = " ".join(label_words) or "figure"
        if len(label) > 18:
            label = label_words[0] if label_words else label[:18]
        out.append({"label": label[:20], "value": val * mult, "pct": suf in ("%", "percent"),
                    "value_text": f"{pre}{digits}{('%' if suf in ('%', 'percent') else suf.upper())}"})
    # One axis one unit family: when plain measures and percents mix, the bars keep the measures.
    plain = [o for o in out if not o["pct"]]
    if len(plain) >= 2:
        out = plain
    for o in out:
        o.pop("pct", None)
    return out[:8]


def _nc_sides(text, subject=None):
    """Two contender names carved from a comparison sentence — the words either
    side of the pivot, or the phrases after each versus/against marker. Bare
    'than' sentences are verdicts, not matchups, so they never reach here."""
    m = re.search(r"\b(vs\.?|versus|against|compared to|compared with|head to head)\b", text, re.I)
    if not m:
        return None
    left = " ".join(text[:m.start()].split()[-3:]).strip(" ,.;:!?")
    left = re.sub(r"\b(head to head|stacked up|going up|face ?off)\b", "", left, flags=re.I).strip(" ,.;:!?")
    left = re.sub(r"^(it|he|she|they|we|this|that|these|those)\s+(is|are|was|were|has|have|gets?|feels?|runs?|comes?)\s+", "", left, flags=re.I).strip()
    left = re.sub(r"^(faster|slower|lighter|heavier|bigger|smaller|better|worse|cheaper|pricier|longer|shorter|stronger|weaker|brighter|darker|newer|older|cleaner|smarter|quicker|easier|harder)\b\s*", "", left, flags=re.I).strip()
    if not left:
        left = (subject or "OURS")
    right_m = re.search(r"\b(?:than|versus|vs\.?|against|over)\b\s+([^,.;:]+?)(?=\s+(?:than|versus|vs\.?|against|and|but|or|wins?|loses?|lost|ties?|leads?|beats?|trails?)\b|[,.;:]|$)", text, re.I)
    right = (right_m.group(1) if right_m else " ".join(text[m.end():].split()[:3])).strip(" ,.;:!?")
    right = re.sub(r"^(to|with)\s+", "", right, flags=re.I).strip()
    if subject:
        for sw_ in subject.split():
            right = re.sub(rf"\b{re.escape(sw_)}\b", "", right, flags=re.I).strip(" ,.;:!?")
    right = right or "THEIRS"
    return " ".join(left.split()[:4]), " ".join(right.split()[:4])


def _nc_segments(text):
    """Step/event labels split on sequence markers and punctuation."""
    parts = re.split(r",|;|\.|\bthen\b|\bnext\b|\bfinally\b|\bfirst\b", text, flags=re.I)
    out = []
    for p in parts:
        if ":" in p:
            p = p.split(":")[-1]
        p = p.strip(" ,.;:!?")
        if len(p) > 1:
            out.append(p)
    return out[:5]


def _nc_widget(bi, g, narration, picked, last, subject=None):
    """One hero widget entity per beat — the content decides which. Returns
    (entity, program_ops) or None for a plain hero-text beat."""
    text = narration
    nums = _nc_numbers(g)
    anchor = g[min(2, len(g) - 1)]["text"].strip(".,;:!?'\"-")
    # Reveal op lands on the first content word after the draw word — the
    # widget fills as soon as its clause opens, never after a dead pause.
    mid = next((w["text"].strip(".,;:!?'\"-") for w in g[3:] if w["text"].strip(".,;:!?-'").lower() not in _NC_STOP), g[min(4, len(g) - 1)]["text"].strip(".,;:!?'\"-"))
    end = g[-1]["text"].strip(".,;:!?'\"-")
    sides = _nc_sides(text, subject) if _VS_RE.search(text) else None
    if sides:
        left, right = sides
        return ({"id": "w1", "kind": "evidence", "glyph": "VS_CARDS", "size": "hero",
                 "params": {"cards": [{"title": left, "mark": left}, {"title": right, "mark": right}]}},
                [{"op": "DRAW", "target": "w1", "at": {"word": anchor}, "duration_ms": 350},
                 {"op": "GROW", "target": "w1", "at": {"word": mid}, "duration_ms": 720}])
    if len(nums) >= 2:
        series = [{"label": n2["label"], "value": n2["value"], "value_text": n2["value_text"]} for n2 in nums]
        if series:
            series[0]["tone"] = "accent"
        return ({"id": "w1", "kind": "evidence", "glyph": "DATA_BARS", "size": "hero",
                 "params": {"series": series}},
                [{"op": "DRAW", "target": "w1", "at": {"word": anchor}, "duration_ms": 350},
                 {"op": "GROW", "target": "w1", "at": {"word": mid}, "duration_ms": 800}])
    if len(_DATE_RE.findall(text)) >= 2:
        evs = ([{"label": (ent.get("phrase") or ent.get("bank_key") or "step"), "sub": ""} for ent, _a in picked[:4]]
               if len(picked) >= 2 else
               [{"label": s2[:16], "sub": ""} for s2 in _nc_segments(text)][:5])
        if len(evs) >= 2:
            return ({"id": "w1", "kind": "evidence", "glyph": "TIMELINE", "size": "hero", "params": {"events": evs}},
                    [{"op": "DRAW", "target": "w1", "at": {"word": anchor}, "duration_ms": 350},
                     {"op": "GROW", "target": "w1", "at": {"word": mid}, "duration_ms": 700}])
    segs = _nc_segments(text)
    if _SEQ_RE.search(text) or len(segs) >= 3:
        drop = {"", "one", "two", "three", "four", "five", "no", "a", "an", "the", "it", "its"}
        def _step(s):
            s = re.sub(r"^.*\b(?:steps?|stages?|phases?|process|how to|setup|install|assembly|stack)\b\s+", "", str(s), flags=re.I).strip()
            s = re.sub(r"\s+(?:that|which|who|it|its|shows?|has|have|had|draw|runs?|uses?|eats?|makes?|keeps?|gives?|takes?|gets?|costs?|sells?|ships?|lasts?)\b.*$", "", s, flags=re.I).strip()
            for _ in range(3):
                s = re.sub(r"^(this|these|those|that|it|is|are|was|were|and|but|or|with|a|an|the)\s+", "", s, flags=re.I).strip()
                s = re.sub(r"\s+(to|of|for|with|and|or|the|a|an|per|on|in|at|by)$", "", s, flags=re.I).strip()
            return " ".join(s.split()[:3])
        seg_steps = [s2 for s2 in (_step(s2) for s2 in segs) if s2.lower() not in drop][:5]
        pick_steps = [s2 for s2 in (_step(ent.get("phrase") or ent.get("bank_key") or "") for ent, _a in picked[:5])
                      if s2.lower() not in drop]
        if _SEQ_RE.search(text):
            steps = seg_steps if len(seg_steps) >= 2 else pick_steps
        else:
            steps = pick_steps if len(pick_steps) >= 2 else seg_steps
        if len(steps) >= 2:
            return ({"id": "w1", "kind": "evidence", "glyph": "FLOW_STEPS", "size": "hero", "params": {"steps": steps}},
                    [{"op": "DRAW", "target": "w1", "at": {"word": anchor}, "duration_ms": 350},
                     {"op": "GROW", "target": "w1", "at": {"word": mid}, "duration_ms": 760}])
    if len(nums) == 1:
        n0 = nums[0]
        mm = re.match(r"([\$\u20ac\u00a3]?)\s*(\d[\d.]*)(.*)", n0["value_text"])
        pre, digits, suf = (mm.group(1) or ""), mm.group(2), (mm.group(3) or "") if mm else ("", n0["value_text"], "")
        return ({"id": "w1", "kind": "evidence", "glyph": "COUNTER", "size": "hero",
                 "params": {"count": round(n0["value"], 2), "prefix": pre, "suffix": suf, "caption": n0["label"],
                            "sep": len(digits) >= 5}},
                [{"op": "DRAW", "target": "w1", "at": {"word": anchor}, "duration_ms": 400},
                 {"op": "COUNT", "target": "w1", "at": {"word": mid}, "duration_ms": 900}])
    if len(picked) >= 3 and bi % 2 == 1:
        cells = [{"name": str(ent.get("phrase") or ent.get("bank_key") or "item"), "sub": "", "concept": ent.get("bank_key") or ""} for ent, _a in picked[:6]]
        return ({"id": "w1", "kind": "evidence", "glyph": "LOGO_GRID", "size": "hero", "params": {"cells": cells, "cols": 3 if len(cells) > 4 else 2}},
                [{"op": "DRAW", "target": "w1", "at": {"word": anchor}, "duration_ms": 350},
                 {"op": "GROW", "target": "w1", "at": {"word": mid}, "duration_ms": 700}])
    if len(picked) >= 2 and bi % 3 == 2:
        rows = [[str(ent.get("phrase") or ent.get("bank_key") or "item"), str(i + 1)] for i, (ent, _a) in enumerate(picked[:4])]
        return ({"id": "w1", "kind": "evidence", "glyph": "DATA_TABLE", "size": "hero",
                 "params": {"header": ["item", "rank"], "rows": rows, "highlight": 0}},
                [{"op": "DRAW", "target": "w1", "at": {"word": anchor}, "duration_ms": 350},
                 {"op": "GROW", "target": "w1", "at": {"word": mid}, "duration_ms": 700}])
    if bi == 0 or len(picked) < 2:
        return ({"id": "w1", "kind": "object", "glyph": "SQUIGGLE", "size": "minor",
                 "params": {"waves": 3}},
                [{"op": "DRAW", "target": "w1", "at": {"word": anchor}, "duration_ms": 620}])
    return None


def _nc_scrub_echo_labels(ent, units):
    """Entity labels must add information, not restate the on-screen type — the compiler
    fails ENTITY_LABEL_ECHO otherwise. A label that collides with a display-unit word
    is dropped; the value/readout still carries the datum."""
    echo = set()
    for u in units:
        for w in re.split(r"\s+", str(u.get("text") or "")):
            echo.add(word_key(w))
    echo.discard("")
    def scrub(s):
        return not s or any(word_key(w) in echo for w in str(s).split())
    p = ent.get("params") or {}
    # Series/row/cell/event/step labels carry the widget's content; contracts require
    # them non-empty and do not echo-check them. Only the entity's own label and a
    # free caption can restate on-screen type, and neither is set on show widgets.
    if ent.get("label") and scrub(ent["label"]):
        ent.pop("label")
    if p.get("caption") and scrub(p["caption"]):
        p.pop("caption")


def _newscast_treatment(args, style, words, groups, media_library, film_id):
    """Keyword-path authorer for the NEWSREEL show grammar: one hero widget per beat,
    a section name per beat, the rotating shade family, and the masthead subject."""
    fam = style["asset_family"]
    fam_key = {"colour_icons": "colour", "mono_icons": "mono", "emoji": "emoji", "photos": "photo"}[fam]
    ctx = None
    if _SEMANTIC:
        _ev = _sem_embed(" ".join(w["text"] for w in words))
        if _ev is not None:
            ctx = _ev[0]
    subject = (getattr(args, "subject", None) or "").strip() or _nc_subject(words)
    beats, used_kw, used_sections, fallback_n = [], set(), set(), 0
    n = len(groups)
    for bi, g in enumerate(groups):
        bid = f"b{bi + 1:02d}"
        narration = clean(" ".join(w["text"] for w in g))
        picked = pick_entities(g, fam_key, used_kw, ctx, max_n=5)
        if not picked:
            fe = fallback_entity(fam_key, fallback_n, question="?" in narration)
            if fe:
                picked = [(fe, g[0]["text"])]
                fallback_n += 1
        for ent, _a in picked:
            if ent.get("bank_key"):
                used_kw.add(ent["bank_key"])
        widget = _nc_widget(bi, g, narration, picked, bi == n - 1, subject)
        entities = []
        program = []
        if widget:
            ent, program = widget
            entities.append(ent)
        # Hero words up top, widget below — the show's reading order.
        units = display_units(g, set())
        for u in units[1:]:
            # The punch is the hero; the rest of the sentence keeps landing as
            # small kinetic words on their anchors — the frame never sits dead
            # while the voice is still going.
            u["role"] = "support"
        if entities:
            _nc_scrub_echo_labels(entities[0], units)
        btype = "HOOK" if bi == 0 else ("PAYOFF" if bi == n - 1 else "PROOF")
        gph = (entities[0]["glyph"] if entities else "") if widget else ""
        pattern = ("PAYOFF_LOCKUP" if bi == n - 1 else
                   {"VS_CARDS": "CONTRAST_RECONFIGURATION",
                    "FLOW_STEPS": "PROCESS_RAIL", "TIMELINE": "SEQUENTIAL_SUPPORT_LIST",
                    "DATA_BARS": "HERO_TO_EVIDENCE_HANDOFF", "DATA_TABLE": "HERO_TO_EVIDENCE_HANDOFF",
                    "COUNTER": "EVIDENCE_PERSISTENCE_CARRIER", "LOGO_GRID": "EVIDENCE_PERSISTENCE_CARRIER",
                    "PROGRESS": "EVIDENCE_PERSISTENCE_CARRIER", "MAGNIFY": "OBJECT_LED_TRANSITION"}.get(gph, "PROGRESSIVE_HERO_BUILD"))
        beats.append({
            "beat_id": bid,
            "beat_type": btype,
            "pattern": pattern,
            "dominant_layer": "HYBRID" if widget else "TEXT",
            "section": _nc_section(g, picked, used_sections, bi, bi == n - 1),
            "narration": narration,
            "energy": 0.6 if bi == 0 else (0.8 if bi == n - 1 else 0.7),
            "complexity": 0.45,
            "display_units": units,
            **({"illustration": {"form": "OBJECT_STAGE", "entities": entities, "program": program}} if widget else {}),
        })
    return {
        "schema": "NexStudioEditorialTreatmentV2",
        "film_id": film_id,
        "note": f"auto-authored by make_reel.py (style={style['id']}, show=NEWSREEL)",
        "aspects": args.aspects.split(","),
        "fps": 30,
        "brand": {**style["palette"], "finish": style["finish"]},
        "typography": {"reveal": style["reveal"], "tonal_ink": 0.42, "min_visual_share": 0.55},
        "voice": {"source": "MASTER", "audio_path": "voice.mp3", "alignment_path": "alignment.json", "head_pad_ms": 350},
        "media_library": media_library,
        "show": {"format": "NEWSREEL", "subject": subject.upper()[:32],
                 "shades": style.get("shades") or style["palette"]},
        "beats": beats,
        "mood": "driving",
        "sfx": "bold",
    }


def _nc_subject(words):
    """Masthead word: the first noun-ish capital content words of the film."""
    txt = " ".join(w["text"] for w in words[:14])
    names = [t for t in re.findall(r"[A-Za-z][A-Za-z0-9.+-]*", txt) if len(t) > 2 and word_key(t) not in STOPWORDS]
    return " ".join(names[:2]).upper() if names else "THE STORY"


def probe_dims(p, kind):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True)
    try:
        w, h = r.stdout.strip().split(",")[:2]
        return int(w), int(h)
    except Exception:
        return None


def probe_dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    try:
        return round(float(r.stdout.strip()), 3)
    except Exception:
        return 0


# ---------- poster ----------
def sketch_posterize(frames_dir, src_mp4, out_mp4, cover_path, plan, fps):
    frames = sorted(Path(frames_dir).glob("f*.jpg"))
    if not frames:
        raise ValueError("Sketch preview requires rendered opening frames")
    first = plan["beats"][0]
    hold = first["ensemble"]["hold_window"]
    start_frame = math.ceil(hold["start_ms"] * fps / 1000)
    last_opening_frame = max(0, math.ceil(first["duration_ms"] * fps / 1000) - 1)
    end_frame = min(math.ceil(hold["end_ms"] * fps / 1000) - 1,
                    last_opening_frame, len(frames) - 1)
    if start_frame > end_frame:
        raise ValueError("Sketch preview requires a completed first-scene frame")
    frame_index = min(max(round((hold["start_ms"] + hold["end_ms"]) * fps / 2000),
                          start_frame), end_frame)
    Path(cover_path).write_bytes(frames[frame_index].read_bytes())
    opening_s = min(frame_index / fps,
                    max(1 / fps, first["words"][0]["start_ms"] / 1000))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src_mp4),
                    "-loop", "1", "-framerate", str(fps), "-i", str(cover_path),
                    "-filter_complex",
                    f"[0:v][1:v]overlay=shortest=1:enable='lt(t,{opening_s:.6f})'[v]",
                    "-map", "[v]", "-map", "0:a", "-c:v", "libx264",
                    "-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p",
                    "-c:a", "copy", "-movflags", "+faststart",
                    str(out_mp4)], check=True)


def posterize(frames_dir, src_mp4, out_mp4, w, h, tmp):
    last = sorted(Path(frames_dir).glob("f*.jpg"))[-1]
    seg, vout = tmp / f"seg_{h}_{uuid.uuid4().hex[:6]}.mp4", tmp / f"v_{h}_{uuid.uuid4().hex[:6]}.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", "30", "-t", "1.6",
                    "-i", str(last), "-vf", f"scale={w}:{h},format=yuv420p",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-an", str(seg)], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(seg), "-i", str(src_mp4),
                    "-filter_complex",
                    "[0:v]fps=30,settb=AVTB,format=yuv420p[p];[1:v]fps=30,settb=AVTB,format=yuv420p[o];"
                    "[p][o]xfade=transition=fade:duration=0.6:offset=1.0[v]",
                    "-map", "[v]", "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                    "-pix_fmt", "yuv420p", "-an", str(vout)], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(vout), "-i", str(src_mp4),
                    "-filter_complex", "[1:a]adelay=1000|1000,apad=whole_dur=99[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(out_mp4)], check=True)
    seg.unlink(missing_ok=True); vout.unlink(missing_ok=True)


def remux_nocaption(frames_dir, audio_wav, out_mp4):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", "15",
                    "-i", str(Path(frames_dir) / "f%05d.jpg"), "-i", str(audio_wav),
                    "-c:v", "libx264", "-crf", "23", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(out_mp4)], check=True)


# ---------- main ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script"); ap.add_argument("--script-file"); ap.add_argument("--voice-file")
    ap.add_argument("--brief", help="topic/brief — authored into a script by tools/write_script.py")
    ap.add_argument("--voice", default="andrew", choices=sorted(VOICES))
    ap.add_argument("--style", default="photo_story")
    ap.add_argument("--media", nargs="*", default=[])
    ap.add_argument("--duration", type=float, default=0,
                    help="target narration seconds (guides --brief script authoring)")
    ap.add_argument("--speed", type=float, default=1.0,
                    help="narration speed multiplier (edge voices)")
    ap.add_argument("--aspects", default="16x9,1x1,9x16")
    ap.add_argument("--out", required=True)
    ap.add_argument("--film-id")
    ap.add_argument("--subject", default=None, help="masthead subject for show styles (e.g. 'ORBIT DESK')")
    ap.add_argument("--treatment", help="use an existing treatment.json instead of auto-authoring")
    ap.add_argument("--fixture-voice", help="fixture dir already containing voice.mp3+alignment.json (with --treatment)")
    ap.add_argument("--no-poster", action="store_true")
    args = ap.parse_args()

    style = style_of(args.style)
    film_id = args.film_id or f"reel-{uuid.uuid4().hex[:8]}"
    out_dir = Path(args.out); out_dir.mkdir(parents=True, exist_ok=True)

    if args.treatment:
        treatment_src = Path(args.treatment)
        voice_dir = Path(args.fixture_voice) if args.fixture_voice else treatment_src.parent
        fixture_dir = voice_dir
        words = json.loads((fixture_dir / "alignment.json").read_text())["words"]
        if fixture_dir.parent.resolve() != (ROOT / "fixtures").resolve():
            dst = ROOT / "fixtures" / fixture_dir.name
            if not dst.exists():
                subprocess.run(["cp", "-r", str(fixture_dir), str(dst)], check=True)
                log(f"copied fixture → {dst}")
            fixture_dir = dst
    else:
        fixture_dir = ROOT / "fixtures" / film_id
        fixture_dir.mkdir(parents=True, exist_ok=True)
        log(f"fixture → {fixture_dir}")
        words = make_voice(args, fixture_dir)
        for mf in args.media:
            dst = fixture_dir / "media" / Path(mf).name
            dst.parent.mkdir(exist_ok=True)
            subprocess.run(["cp", str(mf), str(dst)], check=True)
        media = [fixture_dir / "media" / Path(mf).name for mf in args.media]
        treatment = build_treatment(args, style, words, media, film_id)
        (fixture_dir / "treatment.json").write_text(json.dumps(treatment, indent=1))
        treatment_src = fixture_dir / "treatment.json"

    log(f"rendering {args.aspects} @ {style['id']} ...")
    env = dict(os.environ)
    node_bin = Path.home() / ".nvm/versions/node/v24.19.0/bin"
    if node_bin.is_dir():
        env["PATH"] = str(node_bin) + os.pathsep + env.get("PATH", "")
    r = subprocess.run([sys.executable, str(TOOLS / "regression_pack.py"),
                        "--fixture", fixture_dir.name, "--aspects", args.aspects,
                        "--out", str(out_dir.resolve()),
                        *(["--kinetic-captions"] if style["id"] == "dataviz" else [])],
                       env=env, capture_output=True, text=True)
    print(r.stdout[-2500:] or r.stderr[-2500:])
    if r.returncode != 0:
        sys.exit(f"render failed ({r.returncode})")

    stem = fixture_dir.name
    dims = {"16x9": (1920, 1080), "1x1": (1080, 1080), "9x16": (1080, 1920)}
    manifest = {"film_id": film_id, "style": style["id"], "outputs": {}}
    def package_format(a):
        rd = out_dir / stem
        web = rd / f"{stem}_{a}_web.mp4"
        frames = rd / f"frames_{a}"
        audio = rd / f"audio_{a}.wav"
        if style.get("captions") == "burned" and style["id"] != "dataviz" and frames.exists():
            web_nc = rd / f"{stem}_{a}_nocaption_web.mp4"
            remux_nocaption(frames, audio, web_nc)
            web = web_nc
        if not args.no_poster and style["id"] in ("sketch", "dataviz"):
            poster = rd / f"{stem}_{a}_poster.mp4"
            cover = rd / f"{stem}_{a}_cover.jpg"
            plan = json.loads((rd / f"plan_{a}.json").read_text())
            fps = json.loads((rd / f"render_{a}.json").read_text())["fps"]
            sketch_posterize(frames, web, poster, cover, plan, fps)
            manifest.setdefault("posters", {})[a] = str(cover)
            return str(poster)
        elif not args.no_poster:
            w, h = dims[a]
            poster = rd / f"{stem}_{a}_poster.mp4"
            posterize(frames, web, poster, w, h, out_dir)
            return str(poster)
        else:
            return str(web)
    manifest["outputs"] = render_aspects(
        [a.strip() for a in args.aspects.split(",") if a.strip()], package_format)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=1))
    log("done:")
    for a, p in manifest["outputs"].items():
        log(f"  {a}: {p}")


if __name__ == "__main__":
    main()
