# NexStudio Audio System API

Batch 14 keeps sound separate from visual components.

```js
NexAudio.search({ tags: ["paper.soft"] })
NexAudio.recommend({ tags: ["transition.page"], requireApproved: true })
NexAudio.audition("audio.page-turn-soft", { volume: 0.7, timingOffset: -0.08 })
NexAudio.schedule(container, [{ audioId: "audio.page-turn-soft", start: 2.4 }], { voiceoverDuckingDb: 6 })
```

## Approval policy

The 24 discovered sources pass technical QA but are marked `candidate`. They are disabled by default in production selection. An editor must update `approvalStatus` to `approved` after listening.

## Non-destructive model

- Original masters remain in `assets/audio/masters/candidate-v1/`.
- Production copies live in `assets/audio/production/candidate-v1/`.
- Visual components contain semantic tags only.
- Volume, offset, alternate selection and ducking are mix-time controls.
