# Paper Cast API

Characters resolve from script context the same way scenes do through
`NexAgentSelector`: text in, ranked and staged cast out. Orientation is part of
the resolution, not a render flag — a beat decides whether a character faces the
viewer, the content, or another character.

## Quick start

```js
const cast = NexPaperCast.init();                  // browser: needs runtime/cast-registry.js loaded first
const scene = cast.renderScene({
  script: 'The analyst turns to the chart on the screen and points at the spike.',
  paperStyle: 'clean-editorial',
  aspectRatio: '16:9',
  seed: 'beat-04'
});
container.innerHTML = scene.svg;
```

`scene.cast[i]` reports what was decided and why:

```json
{
  "id": "cast.analyst.paper-01",
  "role": "analyst",
  "pose": "point-at-detail",
  "stage": { "x": -0.3, "depth": 0 },
  "view": { "viewAxis": "three-quarter-right", "yaw": 38, "headYaw": 12.4, "addressing": "content" },
  "score": 76,
  "reasons": ["role:analyst", "intent:guide_attention", "keyword:chart+data", "action:point-at-detail"]
}
```

## Request

| Field | Meaning |
| --- | --- |
| `script` | The beat. Everything below is inferred from it unless overridden. |
| `role`, `intent(s)`, `action`, `ageBand`, `useCase`, `motionEnergy` | Explicit overrides; always beat inference. |
| `castSize` | 1–4. Inferred from the script when omitted. |
| `cast[]` | Explicit slots: `{ id, pose, x, depth, addressing, gazeAt, name, line }`. |
| `paperStyle` | `clean-editorial`, `handmade-scrapbook`, `technical-notebook`, `bold-paper-collage`. |
| `aspectRatio` | `16:9`, `1:1`, `9:16`. |
| `seed` | Fixes the paper cut noise, so the same beat always cuts the same character. |
| `staging.contentAnchor` | `{ x, depth }` of the thing being presented; defaults to the side the script implies, level with the cast. |

## Orientation model

The rig poses the body in body-local 3D and projects it through a view yaw, so
all eight axes are the same character rather than eight drawings:

`front · three-quarter-left/right · profile-left/right · back-left/right · back`

- `addressing` picks the target (`camera`, `content`, `travel`, `exit`, a cast index, an id or a role).
  Beats that move ("walks across", "heads out of frame") resolve to the direction
  of travel rather than to a bystander or the viewer.
- The yaw that faces that target is computed from stage geometry, then snapped
  to an axis the chosen pose supports. A pose that cannot turn far enough is
  replaced by one that can, so a character never explains to the wall.
- Leftover turn goes to the head (±62°), which is how a character works at a
  surface upstage while glancing back at the viewer.
- Parts are sorted by projected depth, so the far arm and far leg are occluded
  by the torso and the far eye drops out of a turned face.

## Cut-out rendering

Body pieces are never outlined individually. Every solid is stroked once as a
thick ink pass, then the same shapes are re-filled on top, so only the outer
contour survives and the figure reads as one cut sheet rather than assembled
components. Internal separation comes from tone: depth shading plus a step
between a limb and the garment behind it. Faces, folds and other ink details
are drawn after both passes.

## In the paperbook (paper-motion)

`install-engines.py` grafts the runtime into the installed paper-motion tree, so
the cast is used there the way any other paper-motion component is used:

```js
const stage = NexCastStage.create({
  script: 'The teacher explains the diagram while the student takes notes.',
  paperStyle: 'clean-editorial',
  aspectRatio: '16:9',
  duration: 5,
  seed: 'beat-2'
});
host.append(stage);
const tl = NexCastStage.animate(stage, { duration: 5 }); // paused, seekable
tl.seek(2.4);
```

| Path | Role |
| --- | --- |
| `components/paper-cast-stage.js` | `component.cast-stage.paper-01`: create / animate / update / plan. |
| `runtime/paper-cast/*` | Selector, context, rig, performance and renderer. |
| `styles/paper-cast.css` | Stage and reel layout tokens. |
| `compositions/cast-reel.html` | 30-second, six-beat contextual cast reel. |

`NexCastStage.animate()` returns a paused `NexMotion` timeline. Every frame is a
pure function of `(member, time, duration)` via `NexCastPerformance.frame()`, so
seeking to the same time always renders the same SVG — the reel can be scrubbed
or captured frame by frame without drift. Standing figures breathe and sway in
place; walking or exiting figures gain a gait cycle and travel across the stage
in the direction they are already facing.

## Paperbook figures: bodies, contacts, props, roles

The catalogue path above picks a drawing. The paperbook path draws one: a body
is a set of parameters, a pose is the result of reaching for something, and an
outfit is a silhouette rather than a colour.

```js
const { svg, character, residual } = NexPaperCast.illustrateRole(
  'an elderly farmer with a hoe',
  { view: 'three-quarter-right', height: 900 }
);
```

`character` is what the words were taken to mean, and is worth reading before
trusting the drawing:

```json
{
  "role": "farmer", "recognised": true, "modifiers": ["elderly"],
  "body": { "age": 72 },
  "look": { "head": { "kind": "hat" }, "top": { "garment": "shirt" } },
  "prop": "hoe", "side": "right", "stance": "work",
  "label": "farmer, holding a hoe"
}
```

`residual` is how far the hands finished from the prop, as a fraction of figure
height — a drawing whose hand missed the handle says so instead of hiding it.

| Call | Use |
| --- | --- |
| `illustrateRole(text, opts)` | A line of script → a drawn character. |
| `describeRole(text, overrides)` | The same resolution, without drawing. |
| `illustrateFigure({ proportion, pose, goals, look, props, view })` | One body, posed from goals. |
| `illustrate(kind, spec, opts)` | A relation; `relations()` lists them. |
| `stage({ features })` | An environment as named contact points: `scene.anchor('table.edge')`. |
| `perform({ id, beats })` | A beat over time: `act.at(t)` gives pose, face and weight. |
| `dialogue({ lines })` | Turn-taking: the listener looks at the speaker. |
| `face(spec, t)` | Brows, eye aperture, blink, mouth, gaze, speaking or listening. |
| `relations()` | The relations this cast can draw. |
| `body(spec)` | Proportions for `{ age, build, stature, mass }`. |
| `props()` / `roles()` / `wardrobe()` | What the artist can draw and answer to. |

Boundaries worth stating plainly: the vocabulary answers to listed words, not to
arbitrary prose, and an unmatched line comes back `recognised: false` rather
than as a confident wrong character. Complexion words set complexion only —
dress and headwear come from dress words, so no garment is inferred from a skin
tone and no skin tone is inferred from a garment.

## Staging against the world

A relation takes its contact points from the environment rather than from
coordinates chosen by hand, so a chair of a different height moves the body
that sits on it:

```js
const scene = Cast.stage({ features: [{ id: 'table', kind: 'table', at: { z: 0.5 }, facing: 180 }] });
const work = Cast.illustrate('work-at-table', { feature: scene.get('table') }, { scene });
```

World coordinates are fractions of the primary figure's height with the ground
at `y = 0`. A seat too tall for the body leaves the feet off the floor and
reports it in `residual` rather than stretching the legs to reach.

## Acting and faces

```js
const act = Cast.perform({ id: 'adanna', beats: [{ at: 0.4, kind: 'point', target: { x: 0.3, y: 0.4, z: 0.4 }, say: 'over there' }] });
const frame = act.at(1.2);   // { phase, pose, face, weight, offsetX, offsetY }
```

A gesture is prepared, struck, held and released; between beats the body
breathes, shifts weight and settles. Sampling is a pure function of the actor
and the time, so a spread asked for the same moment twice draws the same
picture — which is what a still book needs.

## Other entry points

| Call | Use |
| --- | --- |
| `NexPaperCast.plan(request)` | Selection and staging without SVG. |
| `NexPaperCast.renderFigure({ id, pose, viewAxis, paperStyle, look, seed })` | One character, no stage. |
| `NexPaperCast.analyze(script, hints)` | Just the extracted context. |
| `NexPaperCast.search(query, limit)` | Rank the roster against free text. |

## Extending

- **New character**: add a row to `ARCHETYPES` in `tools/build-cast-manifests.js`
  and re-run it; manifests, facets and the browser registry regenerate together.
- **New pose**: add it to `manifests/pose-library.json` with its intents, gesture
  tags and the view axes it reads well in, then list it on the archetypes that
  can use it.
- **New art backend**: implement `render(figure, options)` against the rig output
  and swap it in. Script-to-character semantics stay identical, because the
  selector emits a plan rather than artwork.
