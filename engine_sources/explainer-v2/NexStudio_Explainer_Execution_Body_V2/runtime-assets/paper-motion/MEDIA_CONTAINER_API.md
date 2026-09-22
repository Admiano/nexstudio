# NexStudio Media Container API

Batch 9 adds 24 replaceable animated media and device containers.

```js
const frame = NexMediaContainers.create("browser-window", {
  media: { type: "website-screenshot", src: "assets/media/site.png" },
  title: "Product workspace",
  body: "Every field remains editable.",
  cropMode: "cover",
  focalX: 50,
  focalY: 35,
  border: "taped",
  style: "clean-editorial"
});
const timeline = NexMediaContainers.animate(frame, { motion: "paper-slide", energy: "medium" });
```

## Public methods

- `create(id, config)`
- `animate(target, options)`
- `replaceMedia(target, media)`
- `update(target, config)`
- `setCrop(target, mode)`
- `setFocalPoint(target, x, y)`
- `setBorder(target, border)`
- `setStyle(target, style)`
- `fitText(target)`
- `getDef(id)`

Media is passed through configuration and is never baked into component source. Surrounding paper/device animation targets `.media-shell`, not the inserted media element.
