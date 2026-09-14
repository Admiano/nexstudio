# NexStudio Paper Cast v1

Paper-native contextual cast for the paper-motion (paperbook) dialect: the
characters that the explainer library was missing, resolved from the user script
instead of picked from stock drawings.

Before this, scenes were resolved from context (manifests + facets +
`NexAgentSelector`) while characters were 36 fixed SVGs with no manifests — one
pose, one age, one outfit, permanently facing the camera. This package gives
characters the same contract, plus orientation.

## What is here

```
manifests/cast/*.json      18 archetypes (role, age band, proportion, poses, look, facets)
manifests/pose-library.json 16 poses in body-local angles, with the view axes each reads in
manifests/cast-facets.json  facet index for the selector and explorers
runtime/paper-cast-rig.js   2.5D rig: pose in 3D, project through a view yaw, sort by depth
runtime/paper-cast-renderer.js  paper cut-out SVG with deterministic torn edges and grain
runtime/cast-context.js     script → role / intent / action / who is being addressed
runtime/cast-selector.js    ranking + staging: positions, body yaw, head yaw
runtime/paper-cast.js       public API (plan, renderScene, renderFigure, analyze, search)
runtime/cast-registry.js    generated browser registry
cast-explorer.html          type a beat, see it staged; roster, poses and orientation sweep
tools/                      manifest build, validation suite, review contact sheet
```

## Use

```bash
node tools/build-cast-manifests.js   # regenerate manifests, facets and registry
node tools/test-paper-cast.js        # 16 checks: rig, depth order, staging, render sweep
node tools/render-contact-sheet.js   # .review/contact-sheet.html for visual review
```

```js
const scene = require('./runtime/paper-cast.js').init().renderScene({
  script: 'The customer asks the support agent a question and they talk to each other.'
});
```

See [CAST_API.md](CAST_API.md) for the request shape and the orientation model.

## Why not NexStick V5.1

The stickman package is a 3D 22-joint performance engine in metres with compiled
motion vaults, and its own completion report calls its visual layer a
debug/regression surface with no production skin delivered. Binding it in would
have meant a 3D→2D projection layer plus a new skin for a look it was never
certified for. Its cast semantics (roles, clothing, family morphologies) are
style-agnostic JSON and informed the archetypes here; the engine is not used.
