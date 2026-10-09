# NexStudio Agent Icon API

Batch 6 adds 48 AI-agent, automation and modern software-workflow icons without changing the approved universal or creator icon APIs.

```js
const icon = NexAgentIcons.create("agent-handoff", { size: 144, state: "active", treatment: "paper-cutout" });
mount.appendChild(icon);
const timeline = NexAgentIcons.animate(icon, { motion: "paper-slide", energy: "medium", duration: 1.4 });
timeline.restart();
```

Public methods: `create`, `animate`, `setState`, `setTreatment`, `setSize`, `update`, `getDef`. Each icon is a five-layer editable SVG and reads the existing NexStudio design tokens.
