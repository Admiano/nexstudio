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
outlined word + mint wash), `orbit` (brand hub + named items circling on a
drawn ellipse — for "X now supports A, B, C" beats), `kinetic-headline`
(words slam in individually, landing kick + mint underline on the accent).

Brand marks are never baked in: `end-card`/`logo-mark` take `mark` —
`false` for none, `'icon:<name>'` for a sketch icon, a media asset
name/path/URL for supplied art (inkified), or omit for the default: the
brand's first letter in a hand-drawn mint ring.

Layout discipline: every scene body lives inside `.sk-safe` (inset inside the
furniture margins), and furniture (kickers/foot/index/`note`) owns the
margins — so content can never collide with chrome. Camera moves run on a
`.sk-cam` wrapper so transition transforms never fight them. Elements that
appear get a defined exit (cursor drifts off, caret settles) — nothing
floats. Composition contract per scene: subject + furniture + a detail layer
(ghost numeral, hairline rules, rings, caption stubs, FIG labels) so no frame
reads as a card in a void. During transition windows the incoming scene's
clock is pre-rolled — the wipe crosses onto content already mid-entrance, so
no frame is ever blank.

Surface: warm fibred paper (`paper-warm-1k.png`, procedurally generated via
`tools/gen-paper-texture.py`) under a fine speckle tile (`grain-fine-256.png`
— reused from editorial-motion-v2's community surfaces) — override both per
spec via `paperTexture` / `grainTexture`, or pick a named `paperStock`
(`warm` | `ivory` | `kraft` | `newsprint`; explicit `theme` tokens win over
the stock's tints).

Theme + layout: `spec.theme` (`{paper, paper2, ink, ink2, accent,
accentDeep, texture, stock}`) sets brand tokens on documentElement and the
stage so rough.js strokes resolve them too; CLI accepts `--theme file.json`
or `--accent/--accent-deep/--paper/--ink`. `spec.layout` sets the film's
presentation weight — `editorial` (default), `poster` (type-forward,
display scale ×1.22, centered lane, wide-tracked kickers), `deck`
(tighter lane, scale ×0.92); a scene-level `layout` overrides per beat.

Media + inkify: `spec.assets` (`{name: path-relative-to-spec}`) stages files
into `media/`; scene params (`media`, `poster`, `thumbs`, phone card `img`)
accept the bare asset name or an inline path/URL. Every `<img>` runs through
the `#sk-inkify` SVG filter — saturate→blur→edge-convolve→invert → dark
lines on white, multiply-blended into the paper — so supplied art reads as
part of the ink world. `inkify: false` on a scene falls back to plain
grayscale.

Structured product content: the UI-mockup scenes take real content, not
chrome placeholders — `agent-window` accepts `tasks` ({title, sub, on}) for
the sidebar and `messages` ({from, text}) for a chat transcript;
`phone-app` cards take {title, sub, meta, img, icon}; `storyboard` takes
`cells` as a label array and `thumbs` (inkified) per cell; `chat-prompt`
takes `tags` chips; `step` takes a `caption`. `FilmBeat` carries the same
fields (`tasks`/`messages`/`cards`/`cells`/`thumbs`/`poster`/`tags`) and
`FilmBrief.media` flows to `spec.assets`. When a scripted film doesn't say,
the director's enrichment pass fills the mockups from the film itself —
sidebar tasks and board cells name the actual beats, phone cards carry the
brief's items. `POST /api/v1/sketch-films` also accepts `media`:
`{name: url | data-uri | repo-relative path}`, staged into the job's spec
dir before compile.

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
