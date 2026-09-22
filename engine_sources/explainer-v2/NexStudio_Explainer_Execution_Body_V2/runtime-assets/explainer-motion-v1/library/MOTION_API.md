# NexStudio Motion Runtime API

Batch 3 separates reusable animation behaviour from paper artwork. Motion primitives accept any compatible DOM target and return a deterministic, paused, seekable timeline.

## Apply a motion

```js
const card = NexPaperObjects.create('object.rectangular-card.paper-01', {
  title: 'Reusable motion',
  body: 'Artwork and behaviour remain separate.'
});
mount.appendChild(card);

const timeline = NexMotion.apply(card, 'paper-slide', {
  duration: 0.9,
  delay: 0.1,
  intensity: 1,
  energy: 'medium',
  ease: 'expo.out'
});

timeline.restart();
```

The motion may be addressed by its short `key` or its complete ID, such as `motion.entrance.paper-slide`.

## Apply a transition

```js
const transition = NexMotion.transition(
  outgoingScene,
  incomingScene,
  'card-stack-shuffle',
  { duration: 0.95, intensity: 1, energy: 'medium' }
);

transition.restart();
```

Both scenes must share a positioned parent. The outgoing scene remains visible at transition start. The transition is responsible for carrying it away; do not add a separate pre-transition fade-out.

## Timeline contract

All returned timelines support:

- `seek(seconds)`
- `time(seconds)`
- `progress(0..1)`
- `play()`
- `restart()`
- `pause()`
- `kill()`
- `duration()`

Timelines are paused when constructed and contain no infinite repetition.

## Target conventions

- Numeric count: place `data-motion-number="1250"` on the number element.
- Type/write: use `data-motion-type="text"` and optionally `data-motion-text`.
- Connect: mark nodes with `data-connect-from` and `data-connect-to`.
- SVG draw: provide one or more `<path>` elements. A fallback path is generated when none exists.
- Marker highlight: target editable text or a parent containing a heading, paragraph or caption.

## Registry and manifests

- Runtime registry: `runtime/motion-registry.js`
- Individual manifests: `manifests/motions/`
- Compatibility metadata: `manifests/motion-compatibility.json`
- Master registry: `manifests/index.json`
