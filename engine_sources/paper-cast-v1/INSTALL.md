# Paper Cast — install and run

Everything in this package is plain HTML/CSS/SVG/JS. There is no build step and
no runtime dependency; Node is only used for the tools, and Playwright only for
frame capture.

```
runtime/      the cast engine (browser + Node, no dependencies)
manifests/    archetypes, pose library, facets, generated registry
paperbook/    the paper-motion component, styles and the 30-second reel
tools/        manifest build, test suite, contact sheet, reel capture
cast-explorer.html   standalone explorer — open it and type a script
```

## 1. Run it standalone (no paper-motion needed)

```bash
cd paper-cast-v1
python3 -m http.server 8898
# open http://127.0.0.1:8898/cast-explorer.html
```

Type any beat ("the teacher explains the diagram while the student takes
notes") and the roster, poses, orientation sweep and staged scene update.

In Node:

```bash
node -e "const s=require('./runtime/paper-cast.js').renderScene({script:'The reporter walks out of frame.'});require('fs').writeFileSync('scene.svg',s.svg)"
```

Checks and regeneration:

```bash
node tools/build-cast-manifests.js   # rebuild manifests, facets, browser registry
node tools/test-paper-cast.js        # 27 checks: rig, depth, staging, timing, render
node tools/render-contact-sheet.js   # .review/contact-sheet.html
```

## 2. Install into paper-motion (the paperbook)

Copy into the installed paper-motion tree — this is exactly what
`scripts/install-engines.py` in the NexStudio repo automates:

| From | To (inside `runtime-assets/paper-motion/`) |
| --- | --- |
| `runtime/` | `runtime/paper-cast/` |
| `manifests/` | `manifests/paper-cast/` |
| `paperbook/paper-cast-stage.js` | `components/paper-cast-stage.js` |
| `paperbook/paper-cast.css` | `styles/paper-cast.css` |
| `paperbook/cast-reel.js` | `runtime/cast-reel.js` |
| `paperbook/cast-reel.html` | `compositions/cast-reel.html` |

```bash
PM=/path/to/runtime-assets/paper-motion
rm -rf "$PM/runtime/paper-cast" && cp -r runtime "$PM/runtime/paper-cast"
mkdir -p "$PM/manifests/paper-cast" && cp -r manifests/. "$PM/manifests/paper-cast/"
cp paperbook/paper-cast-stage.js "$PM/components/paper-cast-stage.js"
cp paperbook/paper-cast.css      "$PM/styles/paper-cast.css"
cp paperbook/cast-reel.js        "$PM/runtime/cast-reel.js"
cp paperbook/cast-reel.html      "$PM/compositions/cast-reel.html"
```

Load order in any composition (scripts, in this order):

```html
<link rel="stylesheet" href="../styles/paper-cast.css">
<script src="../runtime/paper-cast/paper-cast-rig.js"></script>
<script src="../runtime/paper-cast/paper-cast-renderer.js"></script>
<script src="../runtime/paper-cast/cast-context.js"></script>
<script src="../runtime/paper-cast/cast-selector.js"></script>
<script src="../runtime/paper-cast/cast-performance.js"></script>
<script src="../runtime/paper-cast/cast-registry.js"></script>
<script src="../runtime/paper-cast/paper-cast.js"></script>
<script src="../components/paper-cast-stage.js"></script>
```

Then use it like any other paper-motion component:

```js
const stage = NexCastStage.create({
  script: 'The analyst turns to the chart and points at the spike.',
  paperStyle: 'clean-editorial',   // handmade-scrapbook | technical-notebook | bold-paper-collage
  aspectRatio: '16:9',             // 1:1 | 9:16
  duration: 5,
  seed: 'beat-3'
});
host.append(stage);
const tl = NexCastStage.animate(stage, { duration: 5 }); // paused NexMotion timeline
tl.seek(2.4);                                            // same time -> same frame
```

## 3. Run the 30-second reel

```bash
cd /path/to/runtime-assets/paper-motion
python3 -m http.server 8899
# open http://127.0.0.1:8899/compositions/cast-reel.html
```

Drive it from the console:

```js
window.__timelines['cast-reel'].play();
window.seekComposition(12.5);   // jump to any second
```

Capture and encode it (720 stepped frames, no real-time recording):

```bash
npm i -D playwright && npx playwright install chromium
node tools/capture-reel.js                 # REEL_URL / FPS / DURATION / OUT env vars
ffmpeg -y -framerate 24 -i frames/f%05d.png -c:v libx264 -pix_fmt yuv420p -crf 20 reel.mp4
```

The reel's six beats live at the top of `paperbook/cast-reel.js` — each is a
`{ rig, kicker, title, script }` row, and the cast for a beat comes entirely
from its `script`, so editing the sentence recasts the shot.

## What drives a character

The only required input is a sentence. From it the selector resolves role, age
band, body proportion, personality, clothing, action, gesture and pose, then
stages the cast: ground position, depth order, body yaw on one of eight view
axes, and an independent head yaw. A figure faces what it addresses — content,
a peer, the camera, its direction of travel, or the exit — instead of defaulting
to the viewer. `NexPaperCast.plan(request)` returns that decision as JSON
without rendering, so it can be overridden or driven from your own pipeline.
