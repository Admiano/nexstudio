#!/usr/bin/env python3
"""make_reel.py — one command: VO in, poster-framed reels out.

Pipeline: script/voice-file -> voice.mp3 + alignment.json -> auto-treatment
(style from styles.json, entities from entity_bank, customer media via
media_library) -> regression_pack render -> web file -> poster-framed file.

  python3 tools/make_reel.py --script "A few years ago, ..." --voice bm_george \
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

STYLES = json.loads((ROOT / "styles.json").read_text())
STYLE_MAP = {s["id"]: s for s in STYLES["styles"]}
VARIANT_MAP = {f'{s["id"]}.{v["id"]}': (s, v) for s in STYLES["styles"] for v in s.get("variants", [])}
BANK = STYLES["entity_bank"]
VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv"}

CLAUSE_END = re.compile(r"[.!?]$")
CLAUSE_MID = re.compile(r"[,;:]$")
STOPWORDS = set("the a an of to and or in on for with by at is are was were be been it its this that".split())


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
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), str(out_wav)], check=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-b:a", "160k", str(out_mp3)], check=True)
        log(f"aligning uploaded voice {src.name} ...")
        align(out_wav, out_ali)
    else:
        text = args.script or (Path(args.script_file).read_text() if args.script_file else "")
        if not text.strip():
            sys.exit("need --script/--script-file or --voice-file")
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


def display_units(gwords):
    text = clean(" ".join(w["text"] for w in gwords))
    # clauses split on , ; :
    clauses, buf = [], []
    for w in gwords:
        buf.append(w["text"])
        if CLAUSE_MID.search(w["text"]):
            clauses.append(" ".join(buf)); buf = []
    if buf:
        clauses.append(" ".join(buf))
    clauses = [c.strip() for c in clauses if c.strip()]
    units = []
    if len(clauses) >= 3:
        roles = ["support"] + ["support"] * (len(clauses) - 2) + ["support"]
        hero_i = max(range(1, len(clauses)), key=lambda i: len(clauses[i].split()))
        for i, c in enumerate(clauses):
            role = "hero" if i == hero_i else ("support" if i == 0 else "support")
            sem = "setup" if i == 0 else ("statement" if i == hero_i else "qualifier")
            units.append({"text": c, "role": role, "anchor_word": c.split()[0],
                          "emphasis": 0.9 if role == "hero" else 0.5, "semantic_role": sem})
    elif len(clauses) == 2:
        hero_i = 0 if len(clauses[0].split()) >= len(clauses[1].split()) else 1
        for i, c in enumerate(clauses):
            units.append({"text": c, "role": "hero" if i == hero_i else "support",
                          "anchor_word": c.split()[0],
                          "emphasis": 0.9 if i == hero_i else 0.5,
                          "semantic_role": "statement" if i == hero_i else ("setup" if i == 0 else "qualifier")})
    else:
        words_ = text.split()
        if len(words_) > 6:
            units.append({"text": " ".join(words_[:3]) + ",", "role": "support",
                          "anchor_word": words_[0], "emphasis": 0.45, "semantic_role": "setup"})
            units.append({"text": " ".join(words_[3:]), "role": "hero",
                          "anchor_word": words_[3], "emphasis": 0.9, "semantic_role": "statement"})
        else:
            units.append({"text": text, "role": "hero", "anchor_word": words_[0],
                          "emphasis": 0.9, "semantic_role": "statement"})
    return units


def word_key(t):
    t = re.sub(r"[^a-z0-9'-]", "", t.lower())
    return t


def pick_entities(gwords, family, already):
    seen = set()
    out = []
    toks = [word_key(w["text"]) for w in gwords]
    for i, tk in enumerate(toks):
        cands = [tk, tk[:-1] if tk.endswith("s") else tk, tk.rstrip("s'’")]
        key = next((c for c in cands if c in BANK), None)
        if not key or key in already or tk in STOPWORDS:
            continue
        spec = BANK[key]
        ref = spec.get(family) or (spec.get("photo") if family == "photos" else None) or spec.get("colour")
        if not ref:
            continue
        if ref in seen:
            continue
        seen.add(ref); already.add(key)
        is_photo = family == "photos" or (family == "colour_icons" and ref == spec.get("photo")) or ref == spec.get("photo")
        ent = {"id": f"e{len(out)+1}_{key}", "kind": "object", "glyph": "TILE"}
        if ref == spec.get("photo"):
            ent["concept"] = ref
        else:
            ent["asset_ref"] = ref
        out.append((ent, gwords[i]["text"]))
        if len(out) >= 4:
            break
    return out


def build_treatment(args, style, words, media_files, film_id):
    groups = chunk_beats(words)
    beats, used_kw = [], set()
    fam = style["asset_family"]
    fam_key = {"colour_icons": "colour", "mono_icons": "mono", "emoji": "emoji", "photos": "photo"}[fam]
    media_iter = iter(enumerate(media_files))
    media_slots = {}
    for mi, mf in media_iter:
        slot = 1 + (mi % max(1, len(groups) - 2)) if len(groups) > 2 else mi % len(groups)
        media_slots.setdefault(slot, []).append((mi, mf))
    n = len(groups)
    for bi, g in enumerate(groups):
        bid = f"b{bi+1:02d}"
        narration = clean(" ".join(w["text"] for w in g))
        picked = pick_entities(g, fam_key, used_kw)
        ents = []
        for ent, anchor in picked:
            ents.append([ent, anchor])
        medias = media_slots.get(bi, [])
        for mi, mf in medias:
            ents.insert(0, ([{"id": f"media{mi+1}", "kind": "evidence", "glyph": "MEDIA",
                              "media_ref": f"media{mi+1}"}, g[0]["text"]]))
        sizes = ["hero", "support", "minor", "support", "minor", "support", "minor"]
        entities, program = [], []
        for ei, (ent, anchor) in enumerate(ents):
            ent["size"] = sizes[min(ei, len(sizes) - 1)]
            entities.append(ent)
            program.append({"op": "DRAW", "target": ent["id"], "at": {"word": anchor},
                            "duration_ms": 550})
        for ei in range(1, len(entities)):
            program.append({"op": "CONNECT",
                            "target": f"{entities[ei-1]['id']}->{entities[ei]['id']}",
                            "at": {"word": ents[ei][1]}, "duration_ms": 350})
        btype = "SETUP" if bi == 0 else ("PAYOFF" if bi == n - 1 else "EXPLANATION")
        beats.append({
            "beat_id": bid,
            "beat_type": btype,
            "pattern": "PAYOFF_LOCKUP" if bi == n - 1 else "PROGRESSIVE_HERO_BUILD",
            "dominant_layer": "TEXT" if style.get("reveal") == "BLOCK" else "HYBRID",
            "narration": narration,
            "energy": 0.55 if bi == 0 else (0.75 if bi == n - 1 else 0.65),
            "complexity": 0.5,
            "display_units": display_units(g),
            "illustration": {"form": "OBJECT_STAGE", "entities": entities,
                             "relations": [{"type": "connects",
                                            "source": entities[i - 1]["id"],
                                            "target": entities[i]["id"]}
                                           for i in range(1, len(entities))],
                             "program": program},
        })
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
        "brand": {**style["palette"], "finish": style["finish"]},
        "typography": {"reveal": style["reveal"], "tonal_ink": 0.42, "min_visual_share": 0.6},
        "voice": {"source": "MASTER", "audio_path": "voice.mp3",
                  "alignment_path": "alignment.json", "head_pad_ms": 350},
        "media_library": media_library,
        "beats": beats,
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
    ap.add_argument("--voice", default="bm_george", choices=sorted(VOICES))
    ap.add_argument("--style", default="tiles")
    ap.add_argument("--media", nargs="*", default=[])
    ap.add_argument("--aspects", default="16x9,1x1,9x16")
    ap.add_argument("--out", required=True)
    ap.add_argument("--film-id")
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
    env["PATH"] = os.path.expanduser("~/.nvm/versions/node/v24.19.0/bin") + ":" + env["PATH"]
    r = subprocess.run([sys.executable, str(TOOLS / "regression_pack.py"),
                        "--fixture", fixture_dir.name, "--aspects", args.aspects,
                        "--out", str(out_dir.resolve())],
                       env=env, capture_output=True, text=True)
    print(r.stdout[-2500:] or r.stderr[-2500:])
    if r.returncode != 0:
        sys.exit(f"render failed ({r.returncode})")

    stem = fixture_dir.name
    dims = {"16x9": (1920, 1080), "1x1": (1080, 1080), "9x16": (1080, 1920)}
    manifest = {"film_id": film_id, "style": style["id"], "outputs": {}}
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
            posterize(frames, web, poster, w, h, out_dir)
            manifest["outputs"][a] = str(poster)
        else:
            manifest["outputs"][a] = str(web)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=1))
    log("done:")
    for a, p in manifest["outputs"].items():
        log(f"  {a}: {p}")


if __name__ == "__main__":
    main()
