# Known Limitations — 3.0.0-rc1

## Production blocker: sound approval

The library contains 24 technically validated candidate sounds, but none has received explicit editorial approval. Production selection therefore defaults to `requireApprovedAudio: true` and returns no approved sound.

The three final audiovisual system tests use candidate sounds solely to prove timing, mixing, metadata and playback. Their filenames and MP4 metadata identify them as provisional.

Before production release:

1. Audition and approve or reject each candidate.
2. Replace the eight missing sound masters documented in `AUDIO_GAP_REPORT.md`.
3. Re-run Batch 14 audio QA and Batch 15 final video mixing.
4. Change the release from RC to production only after approved-audio count is greater than zero and required coverage is complete.

## Official HyperFrames CLI unavailable

The official `hyperframes` package was not cached in this runtime. The five requested CLI commands were attempted in offline mode and failed before execution. Exact command results are in `reports/batch15-official-cli-attempts.json`.

All local validation used the deterministic, seekable compatibility runtime with Chromium, Playwright and FFmpeg. An official CLI pass remains required in the NexStudio production environment.

## Design-system colour literals

The hardcoded-colour audit found literals used for palette definitions, paper simulation, ink/status semantics and test themes. No external client brand is permanently embedded. Normal brand colours remain controlled through theme tokens.

## Replaceable raster references

One reusable source path references replaceable demonstration media. No component artwork is flattened into a mandatory raster asset.

## Voiceover

The final test videos contain timecoded voiceover placeholders in JSON and WebVTT. They do not contain final narration.
