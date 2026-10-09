# NexStudio Business Icon API

Batch 7 adds 36 business, commerce, marketing and organizational icons without changing the approved universal, creator or agent icon namespaces.

```js
const icon = NexBusinessIcons.create("campaign", { size: 144, state: "active", treatment: "paper-cutout" });
mount.appendChild(icon);
const timeline = NexBusinessIcons.animate(icon, { motion: "paper-slide", energy: "medium", duration: 1.4 });
timeline.restart();
```

Public methods: `create`, `animate`, `setState`, `setTreatment`, `setSize`, `update`, `getDef`. Every icon is a five-layer editable SVG driven by the existing theme and motion systems. Expense and decline use directional semantics rather than error styling.
