"""Explicit local commercial audio transport. No voice or timestamp fallback.

Providers implement synthesize(text, output, *, scene_id, film_id) -> dict.
The returned audio_path must be output; source uses the frozen source contract.
Reported words use scene-local milliseconds and bind the exact raw audio hash.
Tests alone may inject is_test_fixture=True providers with test_fixture=True.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import wave
from typing import Any

from .contracts import ALIGNMENT_SCHEMA, validate_alignment, validate_evidence, validate_score

REPO = Path(__file__).resolve().parents[3]
SOUND_ROOT = REPO / "engines/sound/NexStudio_Sound_Library_V2_Production"


class AudioError(RuntimeError):
    pass


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n", encoding="utf-8")


def source_record(source):
    return validate_evidence([{"id": "audio_rights", "claim": "Declared commercial audio provenance.",
                               "status": "supported", "source": source}])[0]["source"]


def run(command, **kwargs):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=kwargs.pop("timeout", 300), **kwargs)
    except (OSError, subprocess.SubprocessError) as exc:
        detail = getattr(exc, "stderr", None) or str(exc)
        raise AudioError(f"AUDIO_COMMAND_FAILED: {command[0]}: {detail[-4000:]}") from exc
    return result


def duration_ms(path):
    result = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)]).stdout)
    duration = float(result["format"]["duration"]) * 1000
    if not math.isfinite(duration) or duration <= 0:
        raise AudioError("AUDIO_DURATION_INVALID")
    return duration


def _registry(name, route_id=None):
    try:
        raw = json.loads(os.environ.get(name, "[]"))
        routes = raw.get("routes") if isinstance(raw, dict) else raw
    except (TypeError, ValueError) as exc:
        raise AudioError(f"INVALID_ROUTE_REGISTRY: {name}") from exc
    if not isinstance(routes, list) or any(not isinstance(r, dict) for r in routes):
        raise AudioError(f"INVALID_ROUTE_REGISTRY: {name}")
    if route_id:
        matches = [r for r in routes if r.get("id") == route_id]
        if len(matches) != 1:
            raise AudioError(f"NO_UNIQUE_DECLARED_LOCAL_ROUTE: {route_id}")
        route = matches[0]
    else:
        eligible = [r for r in routes if r.get("local") is True and r.get("commercialUseAllowed") is True and not r.get("test_fixture")]
        if not eligible:
            raise AudioError(f"NO_DECLARED_LOCAL_ROUTE: {name}; configure an explicit commercial local route; no fallback")
        route = sorted(eligible, key=lambda r: (-int(r.get("priority", 0)), str(r.get("id", ""))))[0]
    if route.get("local") is not True or route.get("commercialUseAllowed") is not True or route.get("test_fixture"):
        raise AudioError("LOCAL_COMMERCIAL_ROUTE_REQUIRED")
    command = route.get("command")
    if not isinstance(command, list) or not command or any(not isinstance(s, str) or not s.strip() for s in command):
        raise AudioError("ROUTE_COMMAND_REQUIRED")
    if any("espeak" in Path(s).name.lower() or s.lower().startswith("fixture:") for s in command):
        raise AudioError("FIXTURE_OR_STOCK_VOICE_FORBIDDEN")
    credential = route.get("credentialEnv")
    if credential and not os.environ.get(credential):
        raise AudioError(f"ROUTE_CREDENTIAL_MISSING: {credential}")
    return deepcopy(route)


def _live_environment():
    if any("fixture" in str(v).lower() for k, v in os.environ.items() if k.endswith("_TRANSPORT")):
        raise AudioError("FIXTURE_TRANSPORT_FORBIDDEN")
    return {**os.environ, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}


def _reported(meta, raw, expected_provider):
    """Only explicit reported provenance is accepted, never EVEN_SCHEDULE sidecars."""
    if not isinstance(meta, dict) or meta.get("method") not in ("provider_word_timestamps", "forced_alignment"):
        raise AudioError("REAL_REPORTED_ALIGNMENT_REQUIRED; scheduled/even/character fixtures are not word timing")
    if meta.get("provider", expected_provider) != expected_provider or meta.get("audio_sha256") != sha256(raw):
        raise AudioError("ALIGNMENT_AUDIO_OR_PROVIDER_MISMATCH")
    if not isinstance(meta.get("words"), list) or not meta["words"]:
        raise AudioError("REPORTED_WORDS_REQUIRED")
    return deepcopy(meta)


class DeclaredLocalTTS:
    """Existing NexStudioAudioProviderRequestV1 command registry, stricter evidence.

    Additional route fields: local:true, provider, source (or explicit source arg).
    Final JSON response: audioPath, providerEvidence.provider and optional alignment
    {provider,method,audio_sha256,words}. An alignmentPath sidecar has this same
    shape. Legacy scheduled Chatterbox timing is refused, not promoted to words.
    A separate declared forced aligner can supply real timing for such voices.
    """
    is_test_fixture = False

    def __init__(self, route_id=None, source=None, voice_id=None):
        self.route = _registry("NEXSTUDIO_TTS_ROUTES_JSON", route_id)
        self.source = source_record(source if source is not None else self.route.get("source"))
        self.provider = self.route.get("provider")
        if not isinstance(self.provider, str) or not self.provider.strip():
            raise AudioError("TTS_PROVIDER_IDENTITY_REQUIRED")
        self.voice_id = voice_id

    def synthesize(self, text, output, *, scene_id, film_id):
        output = Path(output).resolve()
        request = {"schema": "NexStudioAudioProviderRequestV1", "kind": "TTS", "routeId": self.route["id"],
                   "outputPath": str(output), "payload": {"text": text, "sceneId": scene_id, "filmId": film_id,
                       "voiceId": self.voice_id, "alignmentOutputPath": str(output) + ".alignment.json"},
                   "requirements": {"commercialUseAllowed": True, "localOnly": True, "noTrainingRightsAssumption": True,
                                    "audioOnly": True, "reportedWordTimestamps": True, "noSyntheticAlignment": True}}
        env = {**_live_environment(), "NEXSTUDIO_AUDIO_OUTPUT_PATH": str(output), "NEXSTUDIO_AUDIO_KIND": "TTS",
               "NEXSTUDIO_AUDIO_ROUTE_ID": self.route["id"]}
        result = run(self.route["command"], input=json.dumps(request), env=env, cwd=REPO,
                     timeout=int(self.route.get("timeoutSeconds", 300)))
        try:
            meta = json.loads(result.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError) as exc:
            raise AudioError("TTS_RESPONSE_JSON_REQUIRED") from exc
        if not isinstance(meta, dict) or Path(meta.get("audioPath", "")).resolve() != output or not output.is_file():
            raise AudioError("TTS_EXACT_OUTPUT_PATH_REQUIRED")
        evidence = meta.get("providerEvidence", {})
        if evidence.get("provider") != self.provider or "FIXTURE" in str(evidence).upper():
            raise AudioError("TTS_PROVIDER_IDENTITY_OR_FIXTURE_MISMATCH")
        rights = meta.get("rightsEvidence", {})
        if rights.get("commercialUseAllowed") is not True:
            raise AudioError("TTS_COMMERCIAL_RIGHTS_RESPONSE_REQUIRED")
        alignment = meta.get("alignment")
        alignment_path = evidence.get("alignmentPath")
        if alignment is None and alignment_path:
            sidecar = Path(alignment_path).resolve()
            if sidecar != Path(str(output) + ".alignment.json"):
                raise AudioError("TTS_EXACT_ALIGNMENT_PATH_REQUIRED")
            candidate = json.loads(sidecar.read_text(encoding="utf-8"))
            # Refuse a scheduled legacy sidecar; a real forced aligner may follow.
            if candidate.get("method") in ("provider_word_timestamps", "forced_alignment"):
                alignment = candidate
        if alignment is not None:
            alignment = _reported(alignment, output, self.provider)
        return {"audio_path": str(output), "source": self.source, "provider": self.provider, "route": self.route["id"],
                "local": True, "alignment": alignment, "provider_evidence": evidence}


class DeclaredLocalAligner:
    is_test_fixture = False

    def __init__(self, route_id):
        self.route = _registry("EXPLAINER_DIRECTION_ALIGNER_ROUTES_JSON", route_id)
        if not isinstance(self.route.get("provider"), str) or not self.route["provider"].strip():
            raise AudioError("ALIGNER_PROVIDER_REQUIRED")

    def align(self, text, audio, *, scene_id):
        request = {"schema": "explainer-direction.align-request/v1", "text": text, "audio_path": str(audio),
                   "audio_sha256": sha256(audio), "scene_id": scene_id, "requirements": {"local_only": True, "real_alignment": True}}
        result = run(self.route["command"], input=json.dumps(request), env=_live_environment(), cwd=REPO,
                     timeout=int(self.route.get("timeoutSeconds", 300)))
        try:
            meta = json.loads(result.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError) as exc:
            raise AudioError("ALIGNER_JSON_REQUIRED") from exc
        if meta.get("method") != "forced_alignment":
            raise AudioError("FORCED_ALIGNMENT_REQUIRED")
        return _reported(meta, audio, self.route["provider"])


def kokoro_reported_words(tokens):
    """Join tokenizer fragments only at reported whitespace; never space words.

    Punctuation may have no phonetic interval; its text stays attached to the
    actual timed spoken token. Missing timed speech fails complete coverage.
    """
    words, fragments, starts, ends = [], [], [], []
    for token in tokens:
        fragments.append(token.text)
        start, end = getattr(token, "start_ts", None), getattr(token, "end_ts", None)
        if start is not None and end is not None:
            starts.append(float(start) * 1000)
            ends.append(float(end) * 1000)
        if token.whitespace:
            if not starts:
                raise AudioError("KOKORO_TOKEN_TIMING_MISSING")
            words.append({"word": "".join(fragments), "start_ms": min(starts), "end_ms": max(ends)})
            fragments, starts, ends = [], [], []
    if fragments:
        if not starts:
            raise AudioError("KOKORO_TOKEN_TIMING_MISSING")
        words.append({"word": "".join(fragments), "start_ms": min(starts), "end_ms": max(ends)})
    return words


class KokoroLocalTTS:
    """Installed Kokoro KModel/KPipeline using explicit local weights/config/voice.

    No installation or model download. English token start_ts/end_ts originate
    from Kokoro predicted phoneme durations, not independent forced alignment.
    Raw phonemes/pred_dur are preserved as provider evidence, not called measured
    acoustic phonemes. Other languages need a separate reported forced aligner.
    """
    is_test_fixture = False

    def __init__(self, config):
        required = {"id", "model_path", "config_path", "voice_path", "source", "language"}
        if not isinstance(config, dict) or not required <= set(config):
            raise AudioError("KOKORO_EXPLICIT_LOCAL_CONFIG_REQUIRED")
        self.config = deepcopy(config)
        if config["language"] not in ("a", "b"):
            raise AudioError("KOKORO_REPORTED_TOKEN_TIMING_REQUIRES_ENGLISH; use a declared route/forced aligner for other languages")
        self.source = source_record(config["source"])
        self.files = {k: Path(config[k]).resolve() for k in ("model_path", "config_path", "voice_path")}
        if any(not p.is_file() for p in self.files.values()):
            raise AudioError("KOKORO_LOCAL_MODEL_CONFIG_OR_VOICE_MISSING; parent installs, no download fallback")
        speed = config.get("speed", 1)
        if isinstance(speed, bool) or not isinstance(speed, (int, float)) or not 0.5 <= speed <= 2:
            raise AudioError("KOKORO_SPEED_INVALID")
        self.pipe = None

    def synthesize(self, text, output, *, scene_id, film_id):
        _live_environment()
        # Libraries may consult HF; offline is mandatory for the entire load/call.
        keys = ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")
        old = {k: os.environ.get(k) for k in keys}
        try:
            os.environ.update({k: "1" for k in keys})
            try:
                import numpy as np
                import torch
                from kokoro import KModel, KPipeline  # type: ignore[import-untyped]
            except ImportError as exc:
                raise AudioError("KOKORO_PACKAGE_UNAVAILABLE; parent installs; no stock voice fallback") from exc
            if self.pipe is None:
                # Misaki may otherwise invoke spacy.cli.download. Fail before it.
                from spacy.util import is_package
                if not is_package("en_core_web_sm"):
                    raise AudioError("KOKORO_LOCAL_G2P_MODEL_MISSING; parent installs, no implicit spaCy download")
                model = KModel(repo_id="hexgrad/Kokoro-82M", config=str(self.files["config_path"]),
                               model=str(self.files["model_path"])).to(self.config.get("device", "cpu")).eval()
                self.pipe = KPipeline(lang_code=self.config["language"], repo_id="hexgrad/Kokoro-82M", model=model)
                self.voice = torch.load(str(self.files["voice_path"]), map_location="cpu", weights_only=True)
            arrays, words, chunks, offset = [], [], [], 0.0
            for result in self.pipe(text, voice=self.voice, speed=self.config.get("speed", 1), split_pattern=None):
                if result.audio is None:
                    raise AudioError("KOKORO_NO_AUDIO")
                samples = result.audio.detach().cpu().numpy().reshape(-1)
                arrays.append(samples)
                tokens = getattr(result, "tokens", None)
                if tokens:
                    for word in kokoro_reported_words(tokens):
                        words.append({**word, "start_ms": word["start_ms"] + offset, "end_ms": word["end_ms"] + offset})
                chunks.append({"graphemes": result.graphemes, "phonemes": result.phonemes,
                               "predicted_phoneme_duration_frames": result.pred_dur.tolist() if result.pred_dur is not None else None,
                               "offset_ms": offset, "basis": "provider_predicted_durations_not_acoustic_forced_alignment"})
                offset += len(samples) * 1000 / 24000
            if not arrays:
                raise AudioError("KOKORO_NO_AUDIO")
            samples = np.concatenate(arrays)
            if not np.isfinite(samples).all() or np.max(np.abs(samples)) > 1:
                raise AudioError("KOKORO_INVALID_WAVEFORM")
            with wave.open(str(output), "wb") as wav:
                wav.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
                wav.writeframes((samples * 32767).astype("<i2").tobytes())
            alignment = {"provider": "kokoro-local", "method": "provider_word_timestamps", "audio_sha256": sha256(output),
                         "words": words} if words else None
            return {"audio_path": str(output), "source": self.source, "provider": "kokoro-local", "route": self.config["id"],
                    "local": True, "alignment": alignment, "provider_evidence": {"chunks": chunks,
                        "assets": {k: {"path": str(p), "sha256": sha256(p)} for k, p in self.files.items()}}}
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


class CachedLocalVoice:
    """Reuse the exact validated raw TTS bytes while authoring later scenes."""

    def __init__(self, provider):
        self.provider = provider
        self.is_test_fixture = getattr(provider, "is_test_fixture", False)
        self.saved = {}

    def synthesize(self, text, output, *, scene_id, film_id):
        key = (film_id, scene_id)
        output = Path(output).resolve()
        if key in self.saved:
            original_text, raw, raw_hash, metadata = self.saved[key]
            if text != original_text or sha256(raw) != raw_hash or raw == output:
                raise AudioError("STAGED_VOICE_IDENTITY_OR_AUDIO_CHANGED")
            shutil.copyfile(raw, output)
            if sha256(output) != raw_hash:
                raise AudioError("STAGED_VOICE_COPY_CHANGED_AUDIO")
            result = deepcopy(metadata)
            result["audio_path"] = str(output)
            return result
        result = self.provider.synthesize(text, output, scene_id=scene_id, film_id=film_id)
        if isinstance(result, dict) and output.is_file():
            self.saved[key] = (text, output, sha256(output), deepcopy(result))
        return result


def produce_voice(score, output, provider, *, aligner=None, allow_unaligned=False, test_fixture=False):
    """Snapshot raw bytes; normalize without time scaling; pad <1ms to exact PCM.

    All scenes must have real reported words by default. If explicitly allowed,
    unaligned audio is usable only with non-word cues and an authority gap. No
    event duration, cue or narration is silently repaired to fit shorter speech.
    """
    score = validate_score(score)
    if not isinstance(test_fixture, bool) or getattr(provider, "is_test_fixture", False) != test_fixture:
        raise AudioError("TEST_PROVIDER_REQUIRES_EXPLICIT_TEST_FIXTURE; forbidden in live mode")
    if aligner is not None and getattr(aligner, "is_test_fixture", False) != test_fixture:
        raise AudioError("TEST_ALIGNER_REQUIRES_EXPLICIT_TEST_FIXTURE")
    output = Path(output).resolve()
    if output == REPO or REPO in output.parents:
        raise AudioError("AUDIO_OUTPUT_MUST_BE_OUTSIDE_GIT")
    output.mkdir(parents=True, exist_ok=False)
    segments, aligned = [], []
    sources: dict[str, Any] = {}
    for index, scene in enumerate(score["scenes"]):
        raw = output / f"{index:03d}-raw.wav"
        meta = provider.synthesize(scene["narration"], raw, scene_id=scene["id"], film_id=score["film_id"])
        if not isinstance(meta, dict) or meta.get("local") is not True or Path(meta.get("audio_path", "")).resolve() != raw or not raw.is_file():
            raise AudioError("TTS_LOCAL_EXACT_AUDIO_OUTPUT_REQUIRED")
        if not test_fixture and (meta.get("test_fixture") or "fixture" in str(meta.get("provider", "")).lower()):
            raise AudioError("FIXTURE_VOICE_FORBIDDEN")
        source = source_record(meta.get("source"))
        if source["id"] in sources and sources[source["id"]] != source:
            raise AudioError("AUDIO_SOURCE_ID_CONFLICT")
        sources[source["id"]] = source
        if any(not isinstance(meta.get(k), str) or not meta[k].strip() for k in ("provider", "route")):
            raise AudioError("TTS_PROVIDER_AND_ROUTE_REQUIRED")
        raw_hash = sha256(raw)
        reported = meta.get("alignment")
        if reported is None and aligner is not None:
            reported = aligner.align(scene["narration"], raw, scene_id=scene["id"])
        if reported is not None:
            if not isinstance(reported, dict):
                raise AudioError("REPORTED_ALIGNMENT_OBJECT_REQUIRED")
            reported = _reported(reported, raw, reported.get("provider", meta["provider"]))
        if sha256(raw) != raw_hash:
            raise AudioError("ALIGNER_MUTATED_AUDIO")
        if reported is None and (not allow_unaligned or any(e["cue"]["kind"] == "word" for e in scene["events"])):
            raise AudioError(f"REAL_WORD_ALIGNMENT_UNAVAILABLE: {scene['id']}; configure local forced aligner, never fabricate timestamps")
        normalized = output / f"{index:03d}-normalized.wav"
        run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(raw), "-ar", "48000", "-ac", "2", "-c:a", "pcm_s24le", str(normalized)])
        raw_duration = duration_ms(raw)
        if raw_duration > 600000:
            raise AudioError("SCENE_AUDIO_EXCEEDS_CONTRACT_DURATION")
        actual_duration = duration_ms(normalized)
        if abs(actual_duration - raw_duration) > 1:
            raise AudioError("NORMALIZATION_CHANGED_AUDIO_DURATION")
        exact_ms = math.ceil(actual_duration - 1e-7)
        exact = output / f"{index:03d}-scene.wav"
        run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(normalized), "-af", f"apad=whole_len={exact_ms * 48}",
             "-ar", "48000", "-ac", "2", "-c:a", "pcm_s24le", str(exact)])
        if abs(duration_ms(exact) - exact_ms) > 0.01:
            raise AudioError("PCM_DURATION_CONFORMANCE_FAILED")
        if reported:
            # Validate against original waveform duration before adding sub-ms pad.
            single = deepcopy(score)
            single["scenes"] = [scene]
            check = {"schema": ALIGNMENT_SCHEMA, "id": "segment_alignment", "source": {"provider": reported.get("provider", meta["provider"]),
                     "method": reported["method"], "audio_sha256": raw_hash}, "scenes": [{"scene_id": scene["id"],
                     "duration_ms": raw_duration, "words": reported["words"]}]}
            validate_alignment(check, single)
            aligned.append({"scene_id": scene["id"], "duration_ms": exact_ms, "words": reported["words"]})
        record = {"scene_id": scene["id"], "raw_path": str(raw), "raw_sha256": raw_hash, "raw_duration_ms": raw_duration,
                  "path": str(exact), "audio_sha256": sha256(exact), "duration_ms": exact_ms,
                  "pad_ms": exact_ms - actual_duration, "source": source, "provider": meta["provider"], "route": meta["route"],
                  "alignment": reported, "provider_evidence": meta.get("provider_evidence", {})}
        segments.append(record)
    master = output / "voice.wav"
    command = ["ffmpeg", "-nostdin", "-v", "error"]
    for segment in segments:
        command += ["-i", segment["path"]]
    command += ["-filter_complex", "".join(f"[{i}:a]" for i in range(len(segments))) + f"concat=n={len(segments)}:v=0:a=1[voice]",
                "-map", "[voice]", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s24le", str(master)]
    run(command)
    total_ms = sum(s["duration_ms"] for s in segments)
    if abs(duration_ms(master) - total_ms) > 0.01:
        raise AudioError("MASTER_AUDIO_TIMING_MISMATCH")
    master_hash = sha256(master)
    full = None
    if len(aligned) == len(segments):
        methods = {s["alignment"]["method"] for s in segments}
        if len(methods) != 1:
            raise AudioError("MIXED_ALIGNMENT_METHODS_REQUIRE_EXPLICIT_UNIFIED_ALIGNER")
        full = validate_alignment({"schema": ALIGNMENT_SCHEMA, "id": "alignment_" + master_hash[:24],
               "source": {"provider": "+".join(sorted({s['alignment'].get('provider', s['provider']) for s in segments})),
                          "method": next(iter(methods)), "audio_sha256": master_hash}, "scenes": aligned}, score)
    # Multiple sources cannot be laundered as owned mixed media.
    if len(sources) != 1:
        raise AudioError("MULTIPLE_VOICE_SOURCES_REQUIRE_EXPLICIT_AGGREGATE_RIGHTS")
    voice_source = next(iter(sources.values()))
    voice_meta = {"source": voice_source, "provider": "+".join(sorted({s["provider"] for s in segments})),
                  "route": "+".join(sorted({s["route"] for s in segments})), "audio_sha256": master_hash}
    if full:
        voice_meta["alignment_audio_sha256"] = master_hash
        write_json(output / "alignment.json", full)
    write_json(output / "voice-meta.json", voice_meta)
    ledger = {"schema": "explainer-direction.voice-ledger/v1", "test_fixture": test_fixture, "segments": segments,
              "master": {"path": str(master), "sha256": master_hash, "duration_ms": total_ms},
              "alignment_complete": full is not None, "time_stretch": False, "synthetic_word_timing": test_fixture}
    write_json(output / "voice-ledger.json", ledger)
    return {"path": master, "metadata_path": output / "voice-meta.json", "alignment": full, "segments": segments, "ledger": ledger}


def bind_sound_direction(plan, direction, output, *, library_root=SOUND_ROOT):
    """Execute caller-authored semantic sound cues; silence is the default.

    direction={cues:[{event_id,semantic_tag,asset_id,gain,rationale}],
    music:[{path,source,sha256,start_ms,gain,rationale}]}. No auto-scoring, random
    variant cycling, unknown-rights legacy assets, downloads, loops or trimming.
    """
    from .contracts import validate_plan
    plan = validate_plan(plan)
    if not isinstance(direction, dict) or set(direction) - {"cues", "music"}:
        raise AudioError("SOUND_DIRECTION_INVALID")
    output = Path(output).resolve()
    if output == REPO or REPO in output.parents:
        raise AudioError("SOUND_OUTPUT_MUST_BE_OUTSIDE_GIT")
    output.mkdir(parents=True, exist_ok=False)
    root = Path(library_root).resolve()
    tracks: list[dict[str, Any]] = []
    bindings = []
    events = {event["id"]: (event, scene) for scene in plan["scenes"] for event in scene["events"]}
    cues = direction.get("cues", [])
    music = direction.get("music", [])
    if not isinstance(cues, list) or not isinstance(music, list):
        raise AudioError("SOUND_DIRECTION_LISTS_REQUIRED")
    if cues:
        registry = json.loads((root / "manifests/NEXSTUDIO_SOUND_V2_REGISTRY.json").read_text())
        provenance = json.loads((root / "manifests/NEXSTUDIO_SOUND_V2_PROVENANCE.json").read_text())
        assets = {a["assetId"]: a for a in registry["assets"]}
        sources = {s["id"]: s for s in provenance["sources"]}
    for cue in cues:
        if (not isinstance(cue, dict) or set(cue) != {"event_id", "semantic_tag", "asset_id", "gain", "rationale"}
                or any(not isinstance(cue[k], str) or not cue[k].strip() for k in ("event_id", "semantic_tag", "asset_id", "rationale"))):
            raise AudioError("EXACT_SEMANTIC_SOUND_CUE_REQUIRED")
        if cue["event_id"] not in events:
            raise AudioError("SOUND_EVENT_UNKNOWN")
        event, scene = events[cue["event_id"]]
        actors = {a["id"]: a for a in scene["actors"]}
        tracks_for_event = [t for t in scene["tracks"] if t["event_id"] == event["id"] and t["from"] != t["to"]]
        tag = cue["semantic_tag"]
        selections = [t for t in tracks_for_event if t["property"] == "selection" and actors[t["actor_id"]]["kind"] == "selector"]
        scales = [t for t in tracks_for_event if t["property"] == "scale"]
        strokes = [t for t in tracks_for_event if t["property"] == "draw" and t["to"] > t["from"]
                   and actors[t["actor_id"]]["kind"] in ("shape", "axis", "connector")]
        compatible = ((tag in ("ui.select", "ui.switch", "ui.toggle") and selections and event["verb"] in ("select", "update")) or
                      (tag == "motion.ui.expand" and any(t["to"] > t["from"] for t in scales) and event["verb"] in ("grow", "reframe", "morph", "update")) or
                      (tag == "motion.ui.contract" and any(t["to"] < t["from"] for t in scales) and event["verb"] in ("reframe", "morph", "update")) or
                      (tag in ("whiteboard.marker.line", "whiteboard.marker.short", "whiteboard.pencil.short", "whiteboard.pencil.write")
                       and strokes and event["verb"] in ("draw", "connect", "update")))
        if not compatible:
            raise AudioError("SOUND_SEMANTIC_EVENT_MISMATCH; unsupported tags require P8 replan, not random SFX")
        # Discrete selection changes switch at end_ms, unlike continuous motion.
        start_ms = min(t["end_ms"] for t in selections) if tag.startswith("ui.") else event["start_ms"]
        asset = assets.get(cue["asset_id"], {})
        source = sources.get(asset.get("sourceId"), {})
        if asset.get("semanticTag") != tag or asset.get("selectable") is not True or asset.get("status") != "ADMITTED" or asset.get("license") != "CC0-1.0" or source.get("license") != "CC0-1.0":
            raise AudioError("SOUND_ASSET_NOT_DECLARED_CC0_ADMITTED")
        path = (root / asset["path"]).resolve()
        if root not in path.parents or sha256(path) != asset["productionSha256"]:
            raise AudioError("SOUND_LIBRARY_PATH_OR_HASH_MISMATCH")
        license_path = root / "licenses" / ("KENNEY_CC0.txt" if source["id"].startswith("kenney_") else "BIGSOUNDBANK_CC0.txt")
        rights = source_record({"id": "sound_" + source["id"], "uri": source.get("officialPage") or source.get("officialLicensePage"),
                                "locator": str(license_path), "license": "CC0-1.0", "commercial_use": True})
        if not license_path.is_file():
            raise AudioError("SOUND_LICENSE_FILE_MISSING")
        snap = output / f"{len(tracks):03d}{path.suffix}"
        snap.write_bytes(path.read_bytes())
        tracks.append({"path": str(snap), "role": "sound", "source": rights, "start_ms": start_ms, "gain": cue["gain"]})
        bindings.append({**cue, "sha256": sha256(snap), "license_sha256": sha256(license_path), "event_verb": event["verb"],
                         "start_ms": start_ms, "cue_basis": "visible_discrete_state" if tag.startswith("ui.") else "continuous_event_start"})
    for item in music:
        if (not isinstance(item, dict) or set(item) != {"path", "source", "sha256", "start_ms", "gain", "rationale"}
                or any(not isinstance(item[k], str) or not item[k].strip() for k in ("path", "sha256", "rationale"))):
            raise AudioError("EXPLICIT_MUSIC_RIGHTS_HASH_AND_MOTIVE_REQUIRED")
        path = Path(item["path"]).resolve()
        if sha256(path) != item["sha256"]:
            raise AudioError("MUSIC_HASH_MISMATCH")
        snap = output / f"{len(tracks):03d}{path.suffix}"
        snap.write_bytes(path.read_bytes())
        tracks.append({"path": str(snap), "role": "music", "source": source_record(item["source"]), "start_ms": item["start_ms"], "gain": item["gain"]})
        bindings.append({"role": "music", "rationale": item["rationale"], "sha256": sha256(snap)})
    for track in tracks:
        if isinstance(track["gain"], bool) or not isinstance(track["gain"], (int, float)) or not 0 <= track["gain"] <= 2:
            raise AudioError("SOUND_GAIN_INVALID")
        if isinstance(track["start_ms"], bool) or not isinstance(track["start_ms"], (int, float)) or not math.isfinite(track["start_ms"]) or track["start_ms"] < 0 or track["start_ms"] + duration_ms(track["path"]) > plan["duration_ms"] + 0.01:
            raise AudioError("SOUND_MUST_FIT_FILM; no loop/truncation fallback")
    write_json(output / "audio.json", {"tracks": tracks})
    write_json(output / "sound-ledger.json", {"schema": "explainer-direction.sound-ledger/v1", "bindings": bindings, "silence_default": True})
    return output / "audio.json"
