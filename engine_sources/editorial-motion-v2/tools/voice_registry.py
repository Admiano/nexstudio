"""NexStudio voice registry — the studio's approved narration voices.

Ten voices across three free engines:
- kokoro:     local Kokoro-82M (Apache 2.0), CPU-friendly
- edge:       Microsoft Edge neural voices via edge-tts (free endpoint, needs network)
- chatterbox: Chatterbox-Turbo clone (MIT) from a stored reference clip

Each entry carries display metadata so API surfaces can show real names,
accents and a playable preview without knowing engine internals.
"""
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parents[1]

VOICES = {
    # -- Kokoro (local, Apache 2.0) --
    "heart": {
        "engine": "kokoro", "kokoro": "af_heart", "lang": "a",
        "label": "Heart", "gender": "female", "accent": "American",
        "engineLabel": "Kokoro",
    },
    "sky": {
        "engine": "kokoro", "kokoro": "af_sky", "lang": "a",
        "label": "Sky", "gender": "female", "accent": "American",
        "engineLabel": "Kokoro",
    },
    "sarah": {
        "engine": "kokoro", "kokoro": "af_sarah", "lang": "a",
        "label": "Sarah", "gender": "female", "accent": "American",
        "engineLabel": "Kokoro",
    },
    "liam": {
        "engine": "kokoro", "kokoro": "am_liam", "lang": "a",
        "label": "Liam", "gender": "male", "accent": "American",
        "engineLabel": "Kokoro",
    },
    "adam": {
        "engine": "kokoro", "kokoro": "am_adam", "lang": "a",
        "label": "Adam", "gender": "male", "accent": "American",
        "engineLabel": "Kokoro",
    },
    # -- Microsoft Edge neural voices (free cloud endpoint) --
    "emma": {
        "engine": "edge", "edge": "en-US-EmmaMultilingualNeural",
        "label": "Emma", "gender": "female", "accent": "American",
        "engineLabel": "Microsoft neural",
    },
    "emily": {
        "engine": "edge", "edge": "en-IE-EmilyNeural",
        "label": "Emily", "gender": "female", "accent": "Irish",
        "engineLabel": "Microsoft neural",
    },
    "andrew": {
        "engine": "edge", "edge": "en-US-AndrewMultilingualNeural",
        "label": "Andrew", "gender": "male", "accent": "American",
        "engineLabel": "Microsoft neural",
    },
    "steffan": {
        "engine": "edge", "edge": "en-US-SteffanNeural",
        "label": "Steffan", "gender": "male", "accent": "American",
        "engineLabel": "Microsoft neural",
    },
    # -- Chatterbox-Turbo clone (MIT) of public-domain narrator David Clarke --
    "david": {
        "engine": "chatterbox", "ref": "assets/voices/david_ref.wav",
        "label": "David", "gender": "male", "accent": "British",
        "engineLabel": "Chatterbox clone",
    },
}

DEFAULT_VOICE = "andrew"


def voice_meta(voice_id: str) -> dict:
    """Public metadata for one voice (no engine internals)."""
    v = VOICES[voice_id]
    return {
        "id": voice_id,
        "name": v["label"],
        "gender": v["gender"],
        "accent": v["accent"],
        "engine": v["engineLabel"],
        "preview": f"/voice-previews/{voice_id}.mp3",
    }
