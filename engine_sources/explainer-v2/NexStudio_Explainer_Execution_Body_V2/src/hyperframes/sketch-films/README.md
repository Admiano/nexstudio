# sketch-films — spec-driven paper-sketch films

Authors whole films as a declarative spec (`SketchFilmSpec`) and renders them
through the self-hosted HyperFrames Chromium renderer. The visual language is
the `sketch-ui` scene library: thin ink line-art (seeded rough.js) on warm
paper, one mint accent, DM Serif Display kinetic type.

## Render a spec

```bash
tsx src/hyperframes/sketch-films/render.ts \
  src/hyperframes/sketch-films/specs/launch-promo/spec.json \
  out/launch-promo.mp4
```

Requires `google-chrome`/`chromium` on PATH (`CHROMIUM_EXECUTABLE_PATH` also
works) and `ffmpeg`/`ffprobe`.

## Direct a film from a prompt

`direct.ts` is the director layer: a free-text brief → beat plan → scene
selection → validated `SketchFilmSpec`. It is what keeps the system from
being a fixed template — the brief decides which scene types appear (and in
which order), the copy, the transitions, and the camera moves.

```bash
tsx src/hyperframes/sketch-films/direct-cli.ts \
  "make a launch film for an agent that turns a text brief into a finished sketch-style video" \
  src/hyperframes/sketch-films/specs/directed-demo \
  [--duration 38] [--product "NEX STUDIO"] [--cta "..."] [--tagline "..."] [--seed 97]

tsx src/hyperframes/sketch-films/render.ts \
  src/hyperframes/sketch-films/specs/directed-demo/spec.json \
  out/directed-demo.mp4
```

Two input modes, one compiler:

- `prompt` (free text): the prompt is split into clauses and each clause is
  classified by content shape — claims → headline scenes, enumerations →
  `word-list`/`feature-grid`/`process-rail`, figures → `stat`, quotations →
  `quote`, contrasts → `split`, product-interface asks → `chat-prompt` /
  `phone-app` / `agent-window`. Verb sequences become `process-rail` steps.
- `script` (`FilmBeat[]`): the caller supplies structured beats
  (`head`/`sub`/`items`/`stat`/`quote`/`media`/`a`+`b`/`word`/`keyword`,
  optional `role`, `sceneType` pin, per-beat `duration`); the compiler maps
  each beat to the scene type that best carries its content.

```bash
tsx src/hyperframes/sketch-films/direct-cli.ts \
  --script beats.json out/spec-dir
```

Either way the compiler dedupes scene types (a type repeats only when the
narrative carries it twice — pinned beats are never overridden; an inferred
beat colliding with a pinned neighbour is re-typed), times the film from role
weights, assigns transitions + camera moves, derives SFX cues, and runs
`validateSpec` (scenes tile the timeline, required params present, no adjacent
duplicate types).

Copy is deterministic by default; inject an LLM (or any source) per beat via
`directToSpec(brief, { copywriter })`.

## API

`POST /api/v1/sketch-films` accepts JSON `{prompt}` or `{script}` or `{spec}`
(plus `duration`/`product`/`tagline`/`cta`/`seed`), compiles via the director,
and renders async. Poll `GET /api/v1/sketch-films/{jobId}`; the film lands at
`outputs.film`. `GET /api/v1/sketch-films` returns the accepted body shape
and scene types.

## Spec shape

```jsonc
{
  "productionId": "launch-promo",
  "width": 720, "height": 720, "fps": 30,
  "durationSeconds": 38.6,
  "music": "audio/music.mp3",          // loops; loudnorm'd with SFX
  "sfx": ["audio/pop.mp3"],            // per-cue at scene transitions
  "scenes": [
    {
      "id": "beat-01", "type": "chat-prompt",
      "start": 0, "duration": 3.9,
      "transition": "wipe",            // see transitions below
      "camera": { "push": 0.05 },      // optional push/pan
      "kicker": "BRIEF → FILM",        // furniture (top-left mono)
      "kickerR": "...", "foot": "...", // more furniture
      "prompt": "turn this brief into a launch video."
    }
  ]
}
```

Transitions: `cut`/`fade`/`rise`/`wipe` are inline; `torn`, `push`, `page`,
`shuffle`, `tape`, `crumple`, `paper` map to the paper-motion transition
library (torn-paper reveal, collage push, page turn, card-stack shuffle,
tape peel, crumple, paper wipe).

Asset paths are relative to the spec file. Music gets `id:"music"` (loop);
SFX get `id:"sound-effect"` with `cueTimesSec` auto-derived from each scene's
`start` unless `cueTimesSec` is given explicitly on the scene.

## Scene types (runtime-assets/sketch-ui)

`type-card` (kinetic serif word risers), `chat-prompt` (sketched prompt box,
typewriter, cursor), `agent-window` (browser chrome + sidebar + checklist),
`step` (outlined display word + variant illustration: `build` / `test` /
`render`), `phone-app`, `storyboard` (cell draw-on + FRAMES counter),
`compose-graph` (node + wire draw-on + mint travel dots), `render-bar`,
`player` (player chrome + mini product), `logo-mark` (two-wedge draw-on mark),
`end-card` (brand lockup + pill), `hero-build` (progressive phrase-chunk
reveals + keyword promote), `phrase-swap` (word replaced in place via mask),
`process-rail` (travelling focal dot + sequential label resolve),
`payoff-lockup` (convergent settle + longest hold), `word-object-bridge`
(keyword recedes as the named object draws itself).

Content-typed primitives (domain-agnostic — the general-purpose vocabulary):
`chapter` (section marker + rule), `word-list` (phrases land with mint
underlines), `feature-grid` (icon cards pop+settle), `stat` (counting figure +
suffix), `quote` (drawn quote marks + attribution), `media-frame` (framed
image or drawn placeholder), `split` (A/B contrast), `marquee-word` (huge
outlined word + mint wash).

Layout discipline: every scene body lives inside `.sk-safe` (inset inside the
furniture margins), and furniture (kickers/foot/index) owns the margins — so
content can never collide with chrome. Camera moves run on a `.sk-cam`
wrapper so transition transforms never fight them. Elements that appear get
a defined exit (cursor drifts off, caret settles) — nothing floats.

Motion comes from two stacked layers: each scene's local timeline plus any
`NexMotion` paper effects attached to elements (`cut-paper-pop`,
`drop-and-settle`, `stamp-impact`, `ink-reveal`, …), both sought
deterministically per frame by the master timeline.

## How it works

- `assemble.ts` turns a spec into a `CompositionBundle`: copies
  `runtime-assets/sketch-ui` + `paper-motion` runtime files, fonts, textures,
  media assets and audio into the bundle layout, and emits an `index.html`
  that boots `NexSketch.start(spec)`, registers `__timelines`, and sets
  `__renderReady` after fonts load.
- `index.html` carries `data-composition-src` so the renderer serves the
  bundle over HTTP (required — `page.setContent` would break relative URLs).
- Determinism: all motion is seekable (gsap-compat timelines +
  `MotionTimeline.addUpdate`); rough.js shapes are seeded, so frame N looks
  identical on every seek.

## Renderer audio fix

`self-hosted-renderer.ts` adds `aformat=channel_layouts=stereo` around the
mix chain — mono/layout-ambiguous sources previously broke `aresample`
negotiation in ffmpeg.
