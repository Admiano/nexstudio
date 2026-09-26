# NexStudio Agent Selection API

Release: **3.0.0-rc1**

The browser and Node-compatible API is implemented in `runtime/agent-selection-api.js` and consumes `manifests/master-agent-registry.json`.

## Initialize

```js
NexAgentSelector.init(NEX_MASTER_REGISTRY, NEX_MASTER_SOUND_TAG_MAP);
```

## Select

```js
const result = NexAgentSelector.select({
  intent: "explain_agent_workflow",
  duration: 8,
  aspectRatio: "16:9",
  paperStyle: "technical-notebook",
  motionEnergy: "medium",
  useCase: "agent",
  brand: {
    primary: "#6D45D8",
    secondary: "#FFB648",
    accent: "#FF5A36"
  },
  content: {
    title: "From prompt to finished video",
    steps: ["Understand", "Plan", "Create", "Validate"]
  },
  requireApprovedAudio: true
});
```

The response contains:

- Primary scene or component recommendation
- Ranked scene-family recommendations
- Ranked lower-level component recommendations
- Required slots and limits
- Compatible motions and transitions
- Brand configuration
- Approved audio recommendations
- Candidate audio suggestions in a separate field
- Warnings and approval blockers

When `requireApprovedAudio` is true, candidate sounds are never returned as approved production audio.

## Search

```js
const results = NexAgentSelector.search({
  query: "documentary evidence",
  categories: ["scene-family", "documentary-module"],
  paperStyle: "handmade-scrapbook",
  aspectRatio: "9:16",
  motionEnergy: "low",
  useCase: "documentary",
  maxDuration: 10
});
```

## Registry files

- `manifests/master-agent-registry.json`
- `manifests/master-filter-facets.json`
- `manifests/master-sound-tag-map.json`
- `manifests/agent-selection-examples.json`
