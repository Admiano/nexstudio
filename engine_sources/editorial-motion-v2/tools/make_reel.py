#!/usr/bin/env python3
"""make_reel.py — one command: VO in, poster-framed reels out.

Pipeline: script/voice-file -> voice.mp3 + alignment.json -> treatment
(style from styles.json; the story analyst authors arc/scenes/entities/motif
when configured — see story_analyst.py — else the entity_bank keyword path;
customer media via media_library) -> regression_pack render -> web file ->
poster-framed file.

  python3 tools/make_reel.py --script "A few years ago, ..." --voice andrew \
      --style tiles --media desk.png clip.mp4 --out out/my-reel
  python3 tools/make_reel.py --voice-file vo.mp3 --style sketch --aspects 1x1 --out out/r2
  python3 tools/make_reel.py --treatment fixtures/x/treatment.json --fixture-voice fixtures/x --out out/r3

Env: node must be on PATH for the renderer (nvm v24.x):
  export PATH=$HOME/.nvm/versions/node/v24.19.0/bin:$PATH
"""
import argparse, json, os, re, subprocess, sys, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
from generate_voice import synth, align, VOICES  # noqa: E402
import story_analyst  # noqa: E402
sys.path.insert(0, str(TOOLS.parent / "compiler"))
from editorial_plan_compiler.bookauthor import BookAuthor  # noqa: E402

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
def make_voice(args, fixture_dir):
    out_wav, out_mp3, out_ali = fixture_dir / "voice.wav", fixture_dir / "voice.mp3", fixture_dir / "alignment.json"
    if args.voice_file:
        src = Path(args.voice_file)
        # Same normalization the synthesized voice gets: an uploaded track at a
        # different level would otherwise leave the master outside the mix's
        # bounded makeup range and fail loudness_on_target.
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), str(out_wav)], check=True)
        norm = fixture_dir / "voice_norm.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(out_wav),
                        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", str(norm)], check=True)
        out_wav = norm
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(out_wav), "-b:a", "160k", str(out_mp3)], check=True)
        log(f"aligning uploaded voice {src.name} ...")
        align(out_wav, out_ali)
    else:
        text = args.script or (Path(args.script_file).read_text() if args.script_file else "")
        if not text.strip() and getattr(args, "brief", None):
            # brief -> authored narration via the local/key-gated writer
            from write_script import author_script
            data = author_script(args.brief, seconds=35)
            text = data.get("script", "").strip()
            log(f"authored script: {data.get('title', args.brief)} ({len(text.split())} words)")
        if not text.strip():
            sys.exit("need --script/--script-file/--brief or --voice-file")
        from write_script import normalize_tickers
        text = normalize_tickers(text.strip())  # 'SOL' -> 'Solana' for TTS+captions
        dur = synth(text.strip(), args.voice, out_wav)
        norm = fixture_dir / "voice_norm.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(out_wav),
                        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", str(norm)], check=True)
        out_wav = norm
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(out_wav), "-b:a", "160k", str(out_mp3)], check=True)
        log(f"synthesized {dur:.1f}s of VO ({args.voice}), aligning ...")
        align(out_wav, out_ali)
    return json.loads(out_ali.read_text())["words"]


# ---------- auto-treatment ----------
def chunk_beats(words, max_beats=9):
    groups, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt_gap = words[i + 1]["start_ms"] - w["end_ms"] if i + 1 < len(words) else 9999
        if CLAUSE_END.search(w["text"]) or nxt_gap >= 650:
            groups.append(cur); cur = []
    if cur:
        groups.append(cur)
    merged = []
    for g in groups:
        if merged and len(g) < 3:
            merged[-1].extend(g)
        else:
            merged.append(list(g))
    while len(merged) > max_beats:
        # merge the shortest adjacent pair
        i = min(range(len(merged) - 1), key=lambda i: len(merged[i]) + len(merged[i + 1]))
        merged[i:i + 2] = [merged[i] + merged[i + 1]]
    return merged


def clean(t):
    return t.strip()


def chunked_split(clauses):
    # asymmetric split for long clauses: support bboxes are narrow (≤~4 words
    # fit above the type floor), hero bboxes hold ~8. A 14-word clause becomes
    # [setup 3w] + [hero ≤8w] + [qualifier chunks ≤4w] instead of one hero
    # that breaches the legibility floor.
    chunked = []
    for c in clauses:
        ws = c.split()
        if len(ws) > 11:
            chunked.append(" ".join(ws[:3]))
            ws = ws[3:]
            chunked.append(" ".join(ws[:8]))
            ws = ws[8:]
            while ws:
                chunked.append(" ".join(ws[:4]))
                ws = ws[4:]
        else:
            chunked.append(c)
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
    clauses = chunked_split(clauses)
    units, seen = [], set()
    for i, c in enumerate(clauses):
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
                      "semantic_role": "punch" if i == len(clauses) - 1 else "statement"})
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


def _media_library(media_files):
    library = []
    for mi, p in enumerate(media_files):
        p = Path(p)
        kind = "VIDEO" if p.suffix.lower() in VIDEO_EXTS else "IMAGE"
        entry = {"asset_id": f"media{mi+1}", "kind": kind, "path": f"media/{p.name}"}
        wh = probe_dims(p, kind)
        if wh:
            entry["width"], entry["height"] = wh
            if kind == "VIDEO":
                entry["duration_s"] = probe_dur(p)
        library.append(entry)
    return library


def _script_text(args, words):
    text = args.script or (Path(args.script_file).read_text() if args.script_file else "")
    return text.strip() or " ".join(w["text"] for w in words).strip()




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


def build_treatment(args, style, words, media_files, film_id):
    """-> (treatment, storyboard_or_None, source) — story analyst first per --analyst
    mode, legacy keyword bank otherwise."""
    groups = chunk_beats(words)
    aspects = [a.strip() for a in args.aspects.split(",")]
    if args.book == "paperbook":
        return BookAuthor().author(groups, film_id), None, "bookauthor"
    media_library = _media_library(media_files)
    mode = story_analyst.analyst_mode(args)
    if mode != "keywords":
        try:
            treatment, storyboard = story_analyst.build_llm_treatment(
                _script_text(args, words), words, groups, style,
                media_library, film_id, aspects)
            treatment["note"] = (treatment.get("note") or "") + f" [story-analyst model={story_analyst.analyst_config()['model'] or 'replay'}, style={style['id']}]"
            return treatment, storyboard, "story_analyst"
        except story_analyst.AnalystUnavailable as e:
            if mode == "llm":
                sys.exit(f"story analyst unavailable: {e}")
            log(f"story analyst unavailable ({e}) — keyword fallback")
        except story_analyst.AnalystInvalid as e:
            if mode == "llm":
                sys.exit(f"story analyst output invalid: {e}")
            log(f"story analyst invalid ({e}) — keyword fallback")
    return _keyword_treatment(args, style, words, groups, media_files, media_library, film_id), None, "keywords"


def _keyword_treatment(args, style, words, groups, media_files, media_library, film_id):
    # Style knobs beyond the six visual families: which housing the entity icons
    # wear (TILE/BADGE/CHIP...) and how their connectors draw (solid/dash/arc).
    glyph = style.get("glyph", "TILE")
    link_style = style.get("link_style")
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
    for bi, g in enumerate(groups):
        bid = f"b{bi+1:02d}"
        narration = clean(" ".join(w["text"] for w in g))
        # Float scenes lead with visuals — a beat gets a denser cluster (up to six
        # drawable concepts) so the field never reads as a lone text line. Topic
        # keys may re-enter after one beat off (the film keeps returning to its
        # subject); only the previous beat's set is banned, so clusters evolve
        # instead of repeating identically.
        is_float = style.get("finish") == "FLOAT_FIELD"
        picked = pick_entities(g, fam_key, prev_keys if is_float else used_kw, ctx,
                               max_n=6 if is_float else 4)
        beat_keys = {ent.get("bank_key") for ent, _a in picked if ent.get("bank_key")}
        if not picked:
            fe = fallback_entity(fam_key, fallback_n, question="?" in narration)
            if fe:
                picked = [(fe, g[0]["text"])]
                fallback_n += 1
        if is_float and len(picked) < 4:
            # Sparse narration still leads with visuals: the field fills to four
            # with rotating ambient members of the film's own topic pool — keys
            # the film already introduced, minus the previous beat's, so the
            # cluster keeps evolving instead of going minimal while the voice runs.
            pool = [k for k in film_keys if k not in prev_keys and k not in beat_keys]
            for k in pool[(bi * 2) % len(pool):] + pool[:(bi * 2) % len(pool)] if pool else []:
                if len(picked) >= 4:
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
        medias = media_slots.get(bi, [])
        for mi, mf in medias:
            ents.insert(0, [{"id": f"media{mi+1}", "kind": "evidence", "glyph": "MEDIA",
                             "media_ref": f"media{mi+1}"}, g[0]["text"]])
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
        beats.append({
            "beat_id": bid,
            "beat_type": btype,
            "pattern": "PAYOFF_LOCKUP" if bi == n - 1 else "PROGRESSIVE_HERO_BUILD",
            "dominant_layer": "TEXT" if style.get("reveal") == "BLOCK" else "HYBRID",
            "narration": narration,
            "energy": 0.55 if bi == 0 else (0.75 if bi == n - 1 else 0.65),
            "complexity": 0.5,
            "display_units": units,
            "illustration": {"form": "OBJECT_STAGE", "entities": entities,
                             "relations": relations,
                             "program": program,
                             **({"carry": carry} if carry else {})},
        })
    return {
        "schema": "NexStudioEditorialTreatmentV2",
        "film_id": film_id,
        "note": f"auto-authored by make_reel.py (style={style['id']})",
        "aspects": args.aspects.split(","),
        "fps": 30,
        "brand": {**style["palette"], "finish": style["finish"]},
        "typography": {"reveal": style["reveal"], "tonal_ink": 0.42, "min_visual_share": 0.6},
        "voice": {"source": "MASTER", "audio_path": "voice.mp3",
                  "alignment_path": "alignment.json", "head_pad_ms": 350},
        "media_library": media_library,
        "beats": beats,
        **({"mood": style["mood"]} if style.get("mood") else {}),
        **({"sfx": style["sfx"]} if style.get("sfx") else {}),
    }


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
def posterize(frames_dir, src_mp4, out_mp4, w, h, tmp, first_frame=False):
    # The poster intro is a held still fading into frame 0. Editorial styles hold the
    # end card; a paperbook holds its opening spread — a book does not open on its last page.
    fs = sorted(Path(frames_dir).glob("f*.jpg"))
    still = fs[0] if first_frame else fs[-1]
    seg, vout = tmp / f"seg_{h}_{uuid.uuid4().hex[:6]}.mp4", tmp / f"v_{h}_{uuid.uuid4().hex[:6]}.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", "30", "-t", "1.6",
                    "-i", str(still), "-vf", f"scale={w}:{h},format=yuv420p",
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
    ap.add_argument("--style", default="tiles")
    ap.add_argument("--media", nargs="*", default=[])
    ap.add_argument("--aspects", default="16x9,1x1,9x16")
    ap.add_argument("--out", required=True)
    ap.add_argument("--film-id")
    ap.add_argument("--treatment", help="use an existing treatment.json instead of auto-authoring")
    ap.add_argument("--fixture-voice", help="fixture dir already containing voice.mp3+alignment.json (with --treatment)")
    ap.add_argument("--analyst", choices=["auto", "llm", "keywords"], default=None,
                    help="treatment source: auto uses the LLM story analyst when configured "
                         "(STUDIO_ANALYST or --analyst; NEXMIND_STORY_ANALYST_* for provider), "
                         "keywords forces the legacy entity-bank path")
    ap.add_argument("--book", choices=["paperbook"], default=None,
                    help="author the script offline as a still-page picture book (landscape)")
    ap.add_argument("--no-poster", action="store_true")
    ap.add_argument("--no-review", action="store_true",
                    help="skip the film-level certification pass (certification.json)")
    ap.add_argument("--strict-review", action="store_true",
                    help="exit non-zero when the film certification verdict is FAIL")
    args = ap.parse_args()

    if args.book and args.aspects == ap.get_default("aspects"):
        args.aspects = "16x9"
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
        treatment, storyboard, tsource = build_treatment(args, style, words, media, film_id)
        (fixture_dir / "treatment.json").write_text(json.dumps(treatment, indent=1))
        if storyboard:
            (fixture_dir / "storyboard.json").write_text(json.dumps(storyboard, indent=1))
        treatment_src = fixture_dir / "treatment.json"
        log(f"treatment source: {tsource}")

    log(f"rendering {args.aspects} @ {style['id']} ...")
    env = dict(os.environ)
    env["PATH"] = os.path.expanduser("~/.nvm/versions/node/v24.19.0/bin") + ":" + env["PATH"]
    r = subprocess.run([sys.executable, str(TOOLS / "regression_pack.py"),
                        "--fixture", fixture_dir.name, "--aspects", args.aspects,
                        "--out", str(out_dir.resolve())],
                       env=env, capture_output=True, text=True)
    print(r.stdout[-2500:] or r.stderr[-2500:])
    if r.returncode != 0:
        sys.exit(f"render failed ({r.returncode})")

    stem = fixture_dir.name
    try:
        book = (json.loads(Path(treatment_src).read_text()).get("world") or {}).get("book")
    except Exception:
        book = None
    dims = {"16x9": (1920, 1080), "1x1": (1080, 1080), "9x16": (1080, 1920)}
    manifest = {"film_id": film_id, "style": style["id"], "outputs": {}}
    if not args.treatment:
        manifest["treatment_source"] = tsource
        if storyboard:
            manifest["storyboard"] = str(fixture_dir / "storyboard.json")
    for aspect in args.aspects.split(","):
        a = aspect.strip()
        rd = out_dir / stem
        web = rd / f"{stem}_{a}_web.mp4"
        frames = rd / f"frames_{a}"
        audio = rd / f"audio_{a}.wav"
        if style.get("captions") == "burned" and frames.exists():
            web_nc = rd / f"{stem}_{a}_nocaption_web.mp4"
            remux_nocaption(frames, audio, web_nc)
            web = web_nc
        if not args.no_poster:
            w, h = dims[a]
            poster = rd / f"{stem}_{a}_poster.mp4"
            posterize(frames, web, poster, w, h, out_dir, first_frame=(book == "paperbook"))
            manifest["outputs"][a] = str(poster)
        else:
            manifest["outputs"][a] = str(web)
    if not args.no_review:
        sys.path.insert(0, str(TOOLS))
        import film_review
        cert = film_review.certify(out_dir / stem, [], out_dir / stem / "gate_report.json")
        (out_dir / stem / "certification.json").write_text(json.dumps(cert, indent=1) + "\n")
        bad = [c for c in cert["checks"] if c["status"] == "FAIL"]
        log(f"certification: {cert['verdict']} "
            f"({cert['counts']['PASS']} pass, {cert['counts']['WARN']} warn, "
            f"{cert['counts']['FAIL']} fail, {cert['counts']['SKIP']} skip)")
        for c in bad:
            log(f"  FAIL [{c['scope']}] {c['id']}: {c['detail']}")
        if cert["verdict"] == "FAIL" and args.strict_review:
            sys.exit("certification failed")
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=1))
    log("done:")
    for a, p in manifest["outputs"].items():
        log(f"  {a}: {p}")


if __name__ == "__main__":
    main()
