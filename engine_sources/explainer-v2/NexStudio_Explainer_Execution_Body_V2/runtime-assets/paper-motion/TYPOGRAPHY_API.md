# NexStudio Animated Typography API

```js
const card = NexTypography.create("statistic-headline", {
  value: "308", title: "Reusable components", body: "Configured from data.",
  style: "clean-editorial", alignment: "left", emphasis: "Reusable"
});
container.appendChild(card);
NexTypography.fitText(card);
NexTypography.animate(card, { duration: 1.8, energy: "high" }).restart();
```

## Public methods

- `NexTypography.create(idOrSlug, config)`
- `NexTypography.fitText(element)`
- `NexTypography.animate(element, options)`
- `NexTypography.update(element, config)`
- `NexTypography.setStyle(element, style)`
- `NexTypography.setAlignment(element, alignment)`

Each manifest defines explicit copy limits in `characterGuidance` and `slots`. No ordinary wrapping depends on fixed `<br>` tags.
