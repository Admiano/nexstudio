# Install and run

## Standalone

```bash
cd editorial-motion-v1
npm run build
npm test
python3 -m http.server 8901
# http://127.0.0.1:8901/compositions/editorial-explorer.html
```

The explorer takes a script, a ratio, a paper style and an uploaded-media list
(`type|src`, one per line), directs the film and plays the master timeline.

## Inside this repo

`python3 scripts/install-engines.py` copies the package to
`engines/editorial-motion` (`STUDIO_EDITORIAL_MOTION_ROOT`), beside the other
engine roots.

## Inside another paper-motion tree

The package vendors the paper-motion runtime it needs under `vendor/paper-motion`.
To run against a host tree instead, point the script tags at the host's
`runtime/`, `components/` and `styles/` and keep this package's
`manifests/editorial-data.js`, `runtime/` and `styles/editorial.css`.

Load order:

```html
<link rel="stylesheet" href="vendor/paper-motion/styles/tokens.css">
<link rel="stylesheet" href="vendor/paper-motion/styles/paper.css">
<link rel="stylesheet" href="vendor/paper-motion/styles/motion.css">
<link rel="stylesheet" href="vendor/paper-motion/styles/typography.css">
<link rel="stylesheet" href="vendor/paper-motion/styles/icons.css">
<link rel="stylesheet" href="vendor/paper-motion/styles/media-containers.css">
<link rel="stylesheet" href="styles/editorial.css">

<script src="vendor/paper-motion/vendor/gsap-compat.js"></script>
<script src="vendor/paper-motion/runtime/motion-registry.js"></script>
<script src="vendor/paper-motion/runtime/motion-engine.js"></script>
<script src="vendor/paper-motion/runtime/typography-registry.js"></script>
<script src="vendor/paper-motion/runtime/icon-registry.js"></script>
<script src="vendor/paper-motion/runtime/media-container-registry.js"></script>
<script src="vendor/paper-motion/components/typography.js"></script>
<script src="vendor/paper-motion/components/universal-icons.js"></script>
<script src="vendor/paper-motion/components/media-containers.js"></script>

<script src="manifests/editorial-data.js"></script>
<script src="runtime/script-context.js"></script>
<script src="runtime/layout-engine.js"></script>
<script src="runtime/peeps-library.js"></script>
<script src="runtime/editorial-director.js"></script>
<script src="runtime/editorial.js"></script>
```

## API

```js
const { plan, timeline } = await NexEditorial.render(frameEl, script, {
  ratio: '9:16',                 // '16:9' | '1:1' | '9:16'
  style: 'clean-editorial',      // any paper-motion paper style
  duration: 30,                  // seconds
  media: [{ type: 'image', name: 'dashboard-report.svg', src: '…' }],
  assetBase: 'assets/peeps/'
});

timeline.pause().seek(12.5);     // paused and seekable: time -> frame is pure
```

Lower level:

```js
const plan = NexEditorialDirector.direct(script, { ratio, duration, media, registries });
await NexEditorial.create(frameEl, plan, { style, assetBase });
const timeline = NexEditorial.animate(frameEl);
```

`plan.shots[i]` carries `role`, `emphasis`, `typography` (slug + content),
`icons`, `media`, `character` (parts, emotion, framing, score) and `layout`
(regions, dropped elements, plan key) — the whole decision trail, deterministic
for a given script and seed.

## Capture a reel

With the explorer served on 8901 and Chrome exposing CDP:

```bash
PLAYWRIGHT_MODULE=playwright CDP_URL=http://localhost:29229 \
RATIO=9:16 FPS=12 OUT=frames/9x16 node tools/capture-reel.js

ffmpeg -y -framerate 12 -i frames/9x16/f%05d.png \
  -c:v libx264 -pix_fmt yuv420p -crf 20 reel-9x16.mp4
```

## Authoring data, not code

| What to change | Where |
| --- | --- |
| Roles, emotion, person/media cues, pacing | `manifests/editorial-lexicon.json` |
| Typography intents, content requirements, icon budgets, media and character gates, ratio frames | `manifests/editorial-rules.json` |
| Face/pose/body semantics for Open Peeps | `manifests/peeps-semantics.json` |
| Part inventory | `assets/peeps/parts-index.json` |

Run `npm run build` after editing any of them: it regenerates
`manifests/editorial-data.js` (the browser bundle) and `editorial-manifest.json`.
