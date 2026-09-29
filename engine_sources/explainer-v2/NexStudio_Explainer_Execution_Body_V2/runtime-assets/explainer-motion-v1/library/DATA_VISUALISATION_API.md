# NexStudio Data Visualisation and Workflow API

`window.NexDataVisualisations` creates JSON-driven charts and workflow diagrams.

## Core methods

- `create(id, config)`
- `animate(target, options)`
- `update(target, config)`
- `setData(target, data)`
- `fitText(target)`
- `format(value, config)`
- `getDef(idOrSlug)`

All components support `ready`, `empty`, `loading`, and `unavailable` states. Data charts accept positive, neutral, and negative values and the formats `number`, `compact`, `currency`, and `percent`. Workflow diagrams accept `nodes` and `edges` arrays.
