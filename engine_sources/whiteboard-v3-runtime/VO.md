# Voiceover — audio drives the whiteboard

The audio is the clock: script → VO → word timings → beat windows → scenes.

## Recommended providers (word-level timestamps)

| Provider | Rough cost / 1-min script | Word timings | Notes |
|---|---|---|---|
| ElevenLabs Flash/Turbo | ~$0.05 | `/with-timestamps` (char-level → grouped) | best quality, 3000+ voices, voice cloning |
| OpenAI TTS | ~$0.03 | pair with whisper verbose_json | cheap, fewer voices |
| Azure/Google TTS | ~$0.02 | native word boundaries | solid mid tier |
| Piper / Coqui (local) | $0 | pair with whisper.cpp / aeneas | free, lower fidelity |

A 1-min script is ~900 chars → VO is cents per minute.

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
