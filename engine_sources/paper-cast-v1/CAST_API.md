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
