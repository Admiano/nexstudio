# Voiceover — audio drives the whiteboard

The audio is the clock: script → VO → word timings → beat windows → scenes.

## Recommended providers (word-level timestamps)

| Provider | Rough cost / 1-min script | Word timings | Notes |
|---|---|---|---|
| ElevenLabs Flash/Turbo | ~$0.05 | `/with-timestamps` (char-level → grouped) | best quality, 3000+ voices, voice cloning |
| OpenAI TTS | ~$0.03 | pair with whisper verbose_json | cheap, fewer voices |
| Azure/Google TTS | ~$0.02 | native word boundaries | solid mid tier |
| **edge-tts** — **default** | $0 | `vo_synth.py --engine edge` | Microsoft neural voices, no key, needs network — closest free thing to paid VO |
| Kokoro (local) | $0 | `vo_synth.py --engine kokoro` | fully offline, 11 voices, MIT |
| Piper / Coqui (local) | $0 | pair with whisper.cpp / aeneas | free, lower fidelity |

A 1-min script is ~900 chars → VO is cents per minute.

## Local synthesis (Kokoro, $0)

```bash
python3 vo_synth.py script.txt my_vo.wav --voice af_sarah --speed 1.0
# writes my_vo.wav + my_vo_words.json ready for --voiceover/--word-timings
```

Requires `kokoro-onnx` + `faster-whisper` (pip) and the model files —
`kokoro-v0_19.onnx` + `voices.npz` under `/home/ubuntu/voices/` (or pass
`--model`/`--voices`). `[stage: x]` authoring hints are stripped before
synthesis. Voices: af_sarah, af_bella, af_nicole, af_sky, am_adam,
am_michael, bf_emma, bf_isabella, bm_george, bm_lewis.

## Usage

```bash
# 1. generate VO anywhere, save word timings
# ElevenLabs: POST /v1/text-to-speech/<voice>/with-timestamps
# whisper:    whisper audio.mp3 --output_format json (word_timestamps=True)

# 2. render — beat windows auto-align to actual speech
python3 pipeline_v3_narration_timed.py plan.json \
    --voiceover vo.mp3 --word-timings vo_words.json --out-dir out
```

`align_beats_to_words` walks the transcript once and re-times each beat to
where its `narration` text is spoken (first narration token → start, last →
end + small tail). Beats whose narration isn't found keep authored timing.

## Lip-sync (visemes)

`tools/vo/visemes.py` turns the VO wav into a mouth-shape timeline via
Rhubarb Lip Sync (MIT). The binary is not committed (90MB); fetch once:

    mkdir -p tools/vo/bin && cd tools/vo/bin
    curl -sL -o r.zip https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.14.0/Rhubarb-Lip-Sync-1.14.0-Linux.zip
    unzip -oq r.zip && mv Rhubarb-Lip-Sync-1.14.0-Linux/rhubarb . && mv Rhubarb-Lip-Sync-1.14.0-Linux/res . && chmod +x rhubarb

Then: `python3 tools/vo/visemes.py vo.wav vo_visemes.json` and pass
`"visemes": "<path>"` in the mocap_rig request JSON for speaking figures.
