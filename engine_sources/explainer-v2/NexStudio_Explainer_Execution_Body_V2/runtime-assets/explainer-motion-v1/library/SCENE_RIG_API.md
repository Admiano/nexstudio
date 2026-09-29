# NexStudio Scene Rig API

Batch 13 introduces 36 configurable scene families assembled exclusively from approved lower-level components.

```js
const scene = NexSceneRigs.create("product-demonstration", {
  title: "Show the product in motion",
  body: "Replaceable copy and media",
  variant: "B",
  style: "technical-notebook",
  energy: "medium",
  duration: 7.5
});
const timeline = NexSceneRigs.animate(scene, {duration: 3});
```

Each manifest documents two layouts, 3–12 second timing, slot limits, compatible icon categories, transitions and sound tags.
