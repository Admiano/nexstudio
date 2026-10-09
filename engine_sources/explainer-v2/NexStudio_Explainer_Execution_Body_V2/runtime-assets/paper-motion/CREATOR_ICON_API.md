# NexStudio Creator Icon API

Batch 5 adds 48 creator, media-production and publishing icons without modifying the Batch 4 universal icon API.

```js
const icon = NexCreatorIcons.create("camera", { size: 144, state: "active", treatment: "paper-cutout" });
mount.appendChild(icon);
const timeline = NexCreatorIcons.animate(icon, { motion: "cut-paper-pop", energy: "medium", duration: 1.4 });
timeline.restart();
```

Public methods: `create`, `animate`, `setState`, `setTreatment`, `setSize`, `update`, `getDef`. Each icon is a five-layer editable SVG and reads the existing NexStudio design tokens.
