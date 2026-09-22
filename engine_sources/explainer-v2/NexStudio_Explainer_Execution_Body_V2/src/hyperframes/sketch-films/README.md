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
      "transition": "wipe",            // or "fade" (default), "cut"
      "kicker": "BRIEF → FILM",        // furniture (top-left mono)
      "kickerR": "...", "foot": "...", // more furniture
      "prompt": "turn this brief into a launch video."
    }
  ]
}
```

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
`end-card` (brand lockup + pill).

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
