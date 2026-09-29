# NexStudio Paper Motion Library

Version: **3.0.0-rc1**

A reusable paper-texture motion system for creators, agents and NexStudio. The release candidate reconciles **506 unique assets** into one human-browsable and agent-selectable registry.

## Start here

- `index.html` / `master-explorer.html` — master human explorer
- `manifests/master-agent-registry.json` — exact 506-entry registry
- `runtime/agent-selection-api.js` — browser and Node-compatible selection API
- `AGENT_SELECTION_API.md` — API usage
- `FINAL_INVENTORY.md` — exact inventory
- `KNOWN_LIMITATIONS.md` — release blockers and environment limitations

## Exact inventory

- 40 foundation assets
- 40 paper objects
- 32 motion primitives
- 172 icons
- 24 typography systems
- 24 media containers
- 30 data visualisations
- 24 workflow diagrams
- 28 creator modules
- 32 documentary modules
- 36 scene families
- 24 candidate audio assets

Total: **506**

## Final system tests

- Creator explainer: 16:9, bold paper collage
- Agent workflow: 1:1, technical notebook
- Documentary scrapbook: 9:16, handmade scrapbook

Each is 60 seconds at 30 fps and includes timecoded voiceover placeholders.

## Release status

The visual/component system passes final integration QA. Production audio remains blocked because all 24 sounds are technically clean candidates but zero have explicit editorial approval. Candidate audio is disabled whenever `requireApprovedAudio: true`.

The official HyperFrames CLI package was unavailable in this runtime. Exact command attempts are recorded in `reports/batch15-official-cli-attempts.json`; local deterministic validation used Chromium, Playwright and FFmpeg.
