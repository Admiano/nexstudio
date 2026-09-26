# NexStudio Documentary Module API

Batch 12 adds 32 reusable documentary, scrapbook and evidence modules.

```js
const el = NexDocumentaryModules.create("module.documentary.map-journey.paper-01", {
  mood: "investigative",
  style: "technical-notebook",
  media: "assets/media/documentary/city-map.svg",
  routeLabels: ["Archive", "Market", "North Works"],
  title: "The recorded route"
});
mount.append(el);
NexDocumentaryModules.animate(el, {duration: 2.4, energy: "medium"});
```

## Runtime methods

- `create(id, config)` — create an independent module.
- `animate(element, config)` — apply deterministic paper motion.
- `update(element, config)` — replace text, media, sources, routes or mood.
- `setMedia(element, src)` — replace photo/document media.
- `setRedactions(element, boolean)` — reveal or conceal redaction bars.
- `setRoute(element, labels)` — replace route labels.
- `fitText(element)` — rerun responsive text fitting.
- `layoutConnectors(element)` — bind evidence connectors to configured node IDs.

All source and citation fields remain editable. No third-party archive imagery is baked into the runtime. Demo media lives in `assets/media/documentary/` and can be replaced.
