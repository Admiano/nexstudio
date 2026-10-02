# makehuman-lineart

MakeHuman-based line-art character engine, imported from the handoff bundle
(`handoff/README_HANDOFF.md` — the original notes, unmodified). Two speaking
characters — **Host** and **Guest** — built on MakeHuman bodies rendered as
flat ink: compositor object-ID masks for silhouette outlines, Freestyle only
on garment border edges, and face marks as bone-parented ink decals.

## Layout

```
scenes/V9/    prior scenes (kept for provenance)
scenes/V10/   handoff release scenes — Host & Guest, 360f @ 24fps
scenes/V11/   current scenes — V10 + articulated mouth + tracked chin mark
scripts/      build_v10.py (V9→V10), build_v11.py (V10→V11), render/verify tools
audio/        host_15s.wav, guest_15s.wav — the baked viseme envelopes' source
qa/           structural + sync QA reports per generation
previews/     rendered stills and review excerpts
handoff/      the original README_HANDOFF.md from the import bundle
```

## Building

```bash
# V10 -> V11 (writes scenes/V11/<P>_FULLBODY_15S_V11.blend)
blender -b scenes/V10/HOST_FULLBODY_15S_V10.blend  --python scripts/build_v11.py
blender -b scenes/V10/GUEST_FULLBODY_15S_V10.blend --python scripts/build_v11.py
```

Needs Blender 5.2.x headless. EEVEE frame ≈ 20s at 720×1080.

## What V11 fixes (see qa/host_V11_QA.json)

- **Mouth articulation.** The V10 mouth was one flat ellipse. Investigation
  showed the lips' fold is a welded crease that can never part, so V11 keeps
  the handoff's decal idiom but articulates it: `V11_mouth_interior`
  (dark opening) + `V11_mouth_teeth` + `V11_mouth_tongue`, vertex-parented to
  the old anchor, with shape keys driven by the already-baked
  `!ex-jawOpen` / `V3_wide/round/closed/FV` envelope. The V9 aperture is
  hidden, not deleted.
- **Chin mark tracking.** The jaw mark was rigid on the `head` bone and
  separated from the skin under jawOpen; it now bakes per-frame location
  keys tracking the chin vert.
- **Phoneme sync — verified.** The baked envelope was checked against the
  WAV energy: all 8 speech segments get mouth activity, 86% of quiet frames
  are closed, and the jaw leads audio by ~1 frame (correct anticipation).

## Known limits (inherited, still open)

Eyes/hair detail, facial acting, garment design/texture, hand ink, posture,
gesture timing, and a finished 30s reel — the handoff's own list; unchanged
by this pass. The mouth decal reads front-on; profile views will be flat.
