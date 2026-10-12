#!/usr/bin/env python3
"""Local semantic author/TTS/compiler/audit/renderer integration; never shipping."""
from __future__ import annotations

import argparse
from copy import deepcopy
from fractions import Fraction
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

ENGINE = Path(__file__).resolve().parents[1]
REPO = ENGINE.parents[1]
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from explainer_direction import authoring  # noqa: E402
from explainer_direction.audio import (AudioError, CachedLocalVoice, DeclaredLocalTTS, DeclaredLocalAligner, KokoroLocalTTS,  # noqa: E402
                                      bind_sound_direction, produce_voice, sha256, write_json)
from explainer_direction.compiler import compile_score  # noqa: E402
from explainer_direction.contracts import ASPECTS, ScoreError, validate_evidence, validate_plan, validate_score  # noqa: E402
from explainer_direction.quality import audit_score, audit_plan, audit_aspects, validate_observable_actions  # noqa: E402

NODE = os.environ.get("EXPLAINER_DIRECTION_NODE") or "node"
GAPS = ["No Creative Lock or public-production eligibility is granted.",
        "Exact encoded native audio/video needs independent Final Producer and perceptual review.",
        "Build/judge-bound blind human calibration and commercial certification remain external gates.",
        "Evidence truth, source/asset rights and declared provider authenticity require independent verification."]


class PipelineError(RuntimeError):
    pass


def json_file(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _aspects(values):
    if isinstance(values, str):
        values = values.split(",")
    if not isinstance(values, (list, tuple)) or not values or len(set(values)) != len(values) or any(a not in ASPECTS for a in values):
        raise PipelineError("ASPECTS_REQUIRE_UNIQUE_NATIVE_16:9_9:16_1:1")
    return list(values)


def _audit(report, stage):
    if report.get("technical_pass") is not True:
        raise PipelineError(f"STRUCTURAL_AUDIT_FAILED: {stage}; inspect saved findings; no invented quality score or fallback")


def render_plan(plan_path, output, *, voice, metadata, audio=None, workers=2, asset_root=None):
    command = [NODE, str(ENGINE / "tools/render.cjs"), "--plan", str(plan_path), "--out", str(output),
               "--voice", str(voice), "--voice-meta", str(metadata), "--workers", str(workers)]
    if audio:
        command += ["--audio", str(audio)]
    if asset_root:
        command += ["--asset-root", str(asset_root)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=7200, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    if result.returncode:
        raise PipelineError(f"RENDER_FAILED: {(result.stderr or result.stdout)[-5000:]}")
    return json_file(Path(output) / "render-manifest.json")


def _verify_render(plan, plan_path, directory, manifest, voice_hash):
    if manifest.get("status") != "RENDERED_DEVELOPMENT_PREFLIGHT" or manifest.get("silent") is not False:
        raise PipelineError("RENDERED_AUDIO_VIDEO_EVIDENCE_REQUIRED")
    if manifest.get("plan", {}).get("input_sha256") != sha256(plan_path) or manifest.get("duration_ms") != plan["duration_ms"] or manifest.get("canvas") != plan["canvas"] or manifest.get("aspect") != plan["aspect"]:
        raise PipelineError("RENDER_PLAN_IDENTITY_MISMATCH")
    movie = manifest.get("movie", {})
    if movie.get("file") != "film.mp4" or sha256(directory / "film.mp4") != movie.get("sha256"):
        raise PipelineError("RENDER_MOVIE_HASH_MISMATCH")
    frames = manifest.get("frames", [])
    expected_frames = (plan["duration_ms"] * plan["output"]["fps"] + 999) // 1000
    if len(frames) != expected_frames or len(frames) != manifest.get("frame_count"):
        raise PipelineError("RENDER_FRAMES_INCOMPLETE")
    for index, frame in enumerate(frames):
        if frame.get("index") != index or frame.get("file") != f"frames/{index:06d}.png" or frame.get("time_ms") != index * 1000 / plan["output"]["fps"] or sha256(directory / frame["file"]) != frame.get("sha256"):
            raise PipelineError("RENDER_FRAME_IDENTITY_MISMATCH")
    voices = [a for a in manifest.get("audio", []) if a.get("role") == "voice"]
    if len(voices) != 1 or voices[0].get("sha256") != voice_hash:
        raise PipelineError("RENDER_VOICE_IDENTITY_MISMATCH")
    probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(directory / "film.mp4")],
                                     check=True, capture_output=True, text=True).stdout)
    video: dict[str, Any] = next((s for s in probe["streams"] if s["codec_type"] == "video"), {})
    sound: dict[str, Any] = next((s for s in probe["streams"] if s["codec_type"] == "audio"), {})
    if ((video.get("width"), video.get("height")) != (plan["canvas"]["width"], plan["canvas"]["height"])
            or video.get("codec_name") != "h264" or int(video.get("nb_frames", -1)) != expected_frames
            or Fraction(video.get("r_frame_rate", "0/1")) != plan["output"]["fps"]
            or sound.get("codec_name") != "aac" or sound.get("sample_rate") != "48000" or sound.get("channels") != 2):
        raise PipelineError("ENCODED_NATIVE_VIDEO_OR_AUDIO_MISMATCH")
    if abs(float(probe["format"]["duration"]) * 1000 - plan["duration_ms"]) > 1000 / plan["output"]["fps"] + 60:
        raise PipelineError("ENCODED_DURATION_NONCONFORMANCE")
    return {"aspect": plan["aspect"], "movie": str(directory / "film.mp4"), "movie_sha256": movie["sha256"],
            "render_manifest": str(directory / "render-manifest.json"), "render_manifest_sha256": sha256(directory / "render-manifest.json"),
            "frames": len(frames), "probe": probe}


def _inventory(output):
    records = []
    for path in sorted(output.rglob("*")):
        if path.is_file() and path != output / "manifest.json":
            if path.is_symlink() or output not in path.resolve().parents:
                raise PipelineError("OUTPUT_SNAPSHOT_ESCAPE")
            records.append({"path": path.relative_to(output).as_posix(), "sha256": sha256(path), "bytes": path.stat().st_size})
    return records


def run_pipeline(*, output, brief=None, evidence=None, family=None, context=None, score=None, film_id=None,
                 aspects=("16:9", "9:16", "1:1"), provider=None, voice_provider=None, aligner=None,
                 authority_verifier=None, sound_direction=None, sound_authority_verifier=None, history=None, allow_unaligned=False,
                 fps=30, workers=2, asset_root=None, proof=None, staged=False, concept_first=False, compact=False,
                 test_fixture=False, renderer=None, max_repairs=2, source_judge=None,
                 source_quote_narration=False):
    """Author live or execute an authenticated score; return hash-bound manifest.

    Approved score creative fields are immutable. TTS changes only duration,
    timing and resolved cue bindings through authoring.bind_alignment. Shorter
    speech that cannot fit authored actions fails and requires upstream repair.
    Test-only injection requires test_fixture=True, labels every output, and
    cannot execute P8 provenance. A fake renderer is test-only, never live proof.
    """
    aspects = _aspects(aspects)
    if isinstance(fps, bool) or not isinstance(fps, int) or not 1 <= fps <= 60 or workers not in (2, 3, 4):
        raise PipelineError("FPS_1_TO_60_AND_WORKERS_2_TO_4_REQUIRED")
    if proof not in (None, "short", "full"):
        raise PipelineError("UNKNOWN_PROOF_MODE")
    if not isinstance(source_quote_narration, bool) or source_quote_narration and (not compact or score is not None):
        raise PipelineError("SOURCE_QUOTATION_REQUIRES_LIVE_COMPACT_AUTHORING")
    if not isinstance(test_fixture, bool) or renderer is not None and not test_fixture:
        raise PipelineError("RENDERER_INJECTION_TEST_ONLY")
    if voice_provider is None:
        raise PipelineError("EXPLICIT_LOCAL_TTS_PROVIDER_REQUIRED")
    output = Path(output).expanduser().resolve()
    if output == REPO or REPO in output.parents or not output.parent.is_dir():
        raise PipelineError("OUTPUT_REQUIRES_EXISTING_PARENT_OUTSIDE_GIT")
    output.mkdir(exist_ok=False)
    manifest: dict[str, Any] = {"schema": "explainer-direction.production/v1", "status": "RUNNING", "test_fixture": test_fixture,
                "output_directory": str(output), "authority": {"creative_authority": "P8", "creative_lock": False,
                    "public_dispatch_enabled": False, "certification": "NOT_CERTIFIED", "caller_authenticated": False},
                "gaps": list(GAPS), "errors": [], "artifacts": [], "renders": []}
    try:
        if score is not None:
            validated = validate_score(score)
            if bool(validated["provenance"].get("test_fixture", False)) != test_fixture:
                raise PipelineError("SCORE_FIXTURE_AND_EXECUTION_MODE_MISMATCH")
            if film_id is not None and film_id != validated["film_id"] or brief is not None and brief != validated["brief"]:
                raise PipelineError("APPROVED_SCORE_ID_OR_BRIEF_MUST_NOT_CHANGE")
            if evidence is not None and validate_evidence(evidence) != validated["evidence"]:
                raise PipelineError("APPROVED_SCORE_EVIDENCE_MUST_MATCH_EXACTLY")
            if family is not None and family != validated["style"]["family"]:
                raise PipelineError("APPROVED_SCORE_CANNOT_BE_RESTYLED")
            if validated["provenance"]["mode"] == "p8_bound":
                if test_fixture or not callable(authority_verifier) or authority_verifier(deepcopy(validated)) is not True:
                    raise PipelineError("P8_CALLER_AUTHENTICATION_REQUIRED; hashes alone are not authority")
                if sound_direction:
                    packet = {"score": deepcopy(validated), "sound_direction": deepcopy(sound_direction)}
                    if not callable(sound_authority_verifier) or sound_authority_verifier(packet) is not True:
                        raise PipelineError("P8_SOUND_DIRECTION_CALLER_AUTHENTICATION_REQUIRED")
                manifest["authority"]["caller_authenticated"] = True
            elif authority_verifier is not None:
                raise PipelineError("DEVELOPMENT_SCORE_CANNOT_BE_PROMOTED_BY_VERIFIER")
        else:
            if brief is None or evidence is None:
                raise PipelineError("LIVE_AUTHORING_REQUIRES_BRIEF_AND_EVIDENCE")
            options = {"test_fixture": test_fixture, "staged": staged, "concept_first": concept_first, "compact": compact,
                       "source_quote_narration": source_quote_narration,
                       "max_repairs": max_repairs, "source_judge": source_judge}
            if film_id is not None:
                options["film_id"] = film_id
            if staged or compact:
                cached_voice = CachedLocalVoice(voice_provider)
                preparation_count = 0

                def prepare_narration(partial_score):
                    nonlocal preparation_count
                    preparation_count += 1
                    preview = produce_voice(partial_score, output / f"prepared-voice-{preparation_count:03d}",
                                            cached_voice, aligner=aligner,
                                            allow_unaligned=allow_unaligned, test_fixture=test_fixture)
                    return {"duration_ms": preview["segments"][-1]["duration_ms"],
                            "alignment": preview["alignment"]}

                options["prepare_narration"] = prepare_narration
                voice_provider = cached_voice
            validated = authoring.author_score(brief, evidence, family=family or "ocean", context=context,
                                               provider=provider, history=history, **options)
        write_json(output / "request.json", {"brief": validated["brief"], "evidence": validated["evidence"],
                   "context": context, "family": validated["style"]["family"], "aspects": aspects, "proof": proof,
                   "score_input": score is not None, "staged": staged, "concept_first": concept_first, "compact": compact,
                   "max_repairs": max_repairs, "fps": fps, "sound_direction": sound_direction,
                   "source_quote_narration": source_quote_narration,
                   "source_grounder": getattr(source_judge, "identity", None)})
        write_json(output / "authored-score.json", validated)
        manifest.update({"film_id": validated["film_id"], "direction_provenance": validated["provenance"], "aspects": aspects})
        manifest["authority"]["semantic_status"] = validated["provenance"]["status"]
        if validated["provenance"]["mode"] == "development":
            manifest["gaps"].insert(0, "Missing authenticated P8 direction; standalone DEVELOPMENT_PREFLIGHT only.")
            if source_quote_narration:
                manifest["gaps"].append(
                    "Narration repeats the supplied evidence sentences; this development sample does not prove original narration authoring.")
            if source_judge is None:
                manifest["gaps"].append("No independent local source-entailment preflight supplied.")
            else:
                manifest["gaps"].append("Local entailment preflight is a veto signal, not independent P8 factual certification.")
        if test_fixture:
            manifest["gaps"].insert(0, "TEST_FIXTURE_EXECUTION_ONLY; not local inference, production voice or creative proof.")
        before = audit_score(validated, history=history)
        write_json(output / "authored-audit.json", before)
        _audit(before, "authored score")
        voice = produce_voice(validated, output / "voice", voice_provider, aligner=aligner,
                              allow_unaligned=allow_unaligned, test_fixture=test_fixture)
        if voice["alignment"] is not None:
            conformed = authoring.bind_alignment(validated, voice["alignment"])
        else:
            if "alignment" in validated or any(e["cue"]["kind"] == "word" for s in validated["scenes"] for e in s["events"]):
                raise PipelineError("COMPLETE_REAL_ALIGNMENT_REQUIRED_FOR_ALIGNED_OR_WORD_CUE_SCORE")
            conformed = deepcopy(validated)
            for scene, segment in zip(conformed["scenes"], voice["segments"]):
                scene["duration_ms"] = segment["duration_ms"]
                scene["timing"] = "provisional"
            conformed = validate_score(conformed)
            manifest["gaps"].append("Voice has no complete reported word alignment; explicit unaligned preflight, never word-timing proof.")
        if any(e["cue"]["kind"] == "fraction" for s in conformed["scenes"] for e in s["events"]):
            manifest["gaps"].append("Fraction anchors remain explicitly provisional; real speech does not turn fractions into word cues.")
        duration = sum(s["duration_ms"] for s in conformed["scenes"])
        if proof == "short" and not 15000 <= duration <= 25000:
            raise PipelineError(f"SHORT_PROOF_REQUIRES_ACTUAL_15_TO_25_SECONDS: {duration}ms; re-author, no padding/stretching workaround")
        if proof == "full" and duration <= 25000:
            raise PipelineError("FULL_PROOF_REQUIRES_MORE_THAN_25_SECONDS_OF_ACTUAL_SCENES")
        manifest["duration_ms"] = duration
        manifest["voice"] = {"audio_sha256": sha256(voice["path"]), "alignment_complete": voice["alignment"] is not None,
                             "time_stretch": False, "ledger": "voice/voice-ledger.json"}
        write_json(output / "score.json", conformed)
        for index in range(len(conformed["scenes"])):
            validate_observable_actions(conformed, index)
        report = audit_score(conformed, history=history)
        write_json(output / "score-audit.json", report)
        _audit(report, "conformed score")
        plans = []
        for aspect in aspects:
            plan = compile_score(conformed, aspect)
            plan["output"]["fps"] = fps
            plan = validate_plan(plan)
            plans.append(plan)
            slug = aspect.replace(":", "x")
            plan_path = output / f"plan-{slug}.json"
            write_json(plan_path, plan)
            check = audit_plan(plan)
            write_json(output / f"audit-{slug}.json", check)
            _audit(check, aspect)
        if set(aspects) == set(ASPECTS):
            native = audit_aspects(plans)
            write_json(output / "aspect-audit.json", native)
            _audit(native, "native aspects")
        else:
            manifest["gaps"].append("Native-aspect proof incomplete; not all three aspects were requested.")
        audio = bind_sound_direction(plans[0], sound_direction or {}, output / "sound")
        selected_renderer = renderer or render_plan
        for plan in plans:
            slug = plan["aspect"].replace(":", "x")
            directory = output / f"render-{slug}"
            plan_path = output / f"plan-{slug}.json"
            rendered = selected_renderer(plan_path, directory, voice=voice["path"], metadata=voice["metadata_path"],
                                          audio=audio, workers=workers, asset_root=asset_root)
            if renderer is None:
                result = _verify_render(plan, plan_path, directory, rendered, sha256(voice["path"]))
            else:
                result = {"aspect": plan["aspect"], "test_only_renderer": True, "result": rendered}
            manifest["renders"].append(result)
        manifest["status"] = "TEST_FIXTURE_RENDER_READY" if test_fixture else "RENDER_READY_NOT_CREATIVE_LOCKED"
    except Exception as exc:
        manifest["status"] = "FAILED"
        manifest["errors"].append({"type": type(exc).__name__, "message": str(exc)})
        raise
    finally:
        try:
            manifest["artifacts"] = _inventory(output)
        except Exception as inventory_error:
            manifest["status"] = "FAILED"
            manifest["errors"].append({"type": type(inventory_error).__name__, "message": str(inventory_error)})
            write_json(output / "manifest.json", manifest)
            raise
        write_json(output / "manifest.json", manifest)
    return manifest


def load_verifier(spec):
    """Explicit trusted caller code, not an approval JSON/hash-only bypass."""
    filename, sep, function = spec.rpartition(":")
    path = Path(filename).expanduser().resolve()
    if not sep or path.suffix != ".py" or not path.is_file() or not function.isidentifier():
        raise PipelineError("AUTHORITY_VERIFIER_REQUIRES_EXISTING_PYTHON_FILE:FUNCTION")
    module_spec = importlib.util.spec_from_file_location("explainer_direction_caller_authority", path)
    if module_spec is None or module_spec.loader is None:
        raise PipelineError("CALLER_AUTHORITY_MODULE_UNAVAILABLE")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    verifier = getattr(module, function, None)
    if not callable(verifier):
        raise PipelineError("AUTHORITY_VERIFIER_CALLABLE_REQUIRED")
    return verifier


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--brief", help="Exact brief text (use --brief-file for a UTF-8 file).")
    source.add_argument("--brief-file", type=Path)
    source.add_argument("--score", type=Path, help="Validated semantic score; P8 scores additionally require caller authentication.")
    p.add_argument("--evidence", type=Path, help="JSON array of factual records, never implicitly fetched.")
    p.add_argument("--family", choices=("neon", "candy", "forest", "ocean", "ember"))
    p.add_argument("--context", type=Path, help="JSON audience/brand/intent context.")
    p.add_argument("--aspects", default="16:9,9:16,1:1")
    p.add_argument("--out", required=True, type=Path, help="New directory under an existing parent outside git.")
    p.add_argument("--film-id")
    p.add_argument("--tts-route", help="Exact local commercial NEXSTUDIO_TTS_ROUTES_JSON route; no fallback.")
    p.add_argument("--voice-source", type=Path, help="Explicit frozen commercial provenance if absent from route.")
    p.add_argument("--voice-id")
    p.add_argument("--kokoro-config", type=Path, help="Explicit installed offline model/config/voice paths and provenance.")
    p.add_argument("--aligner-route", help="Declared real local forced aligner when TTS has no reported words.")
    p.add_argument("--authority-verifier", help="Trusted caller Python FILE:FUNCTION authenticates full approved score/P8 hashes.")
    p.add_argument("--sound-direction", type=Path)
    p.add_argument("--sound-authority-verifier", help="Trusted FILE:FUNCTION authenticates {score,sound_direction} for P8 audio cues.")
    p.add_argument("--history", type=Path)
    p.add_argument("--allow-unaligned", action="store_true", help="Explicit non-word-cue preflight only; leaves timing authority gap.")
    p.add_argument("--staged", action="store_true")
    p.add_argument("--concept-first", action="store_true", help="Compare genuine concepts, then author the selected film; reduces local CPU work.")
    p.add_argument("--compact", action="store_true", help="Use compact evidence-bound two-pass authoring.")
    p.add_argument("--source-quote-narration", action="store_true", help="Explicit compact preflight: speak supplied evidence sentences.")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--workers", type=int, choices=(2, 3, 4), default=2)
    p.add_argument("--asset-root", type=Path)
    p.add_argument("--proof", choices=("short", "full"))
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    if args.kokoro_config and (args.tts_route or args.voice_source or args.voice_id):
        parser().error("--kokoro-config is mutually exclusive with route voice arguments")
    if not args.score and not args.evidence:
        parser().error("live authoring requires --evidence")
    try:
        tts = KokoroLocalTTS(json_file(args.kokoro_config)) if args.kokoro_config else DeclaredLocalTTS(
            args.tts_route, json_file(args.voice_source) if args.voice_source else None, args.voice_id)
        manifest = run_pipeline(output=args.out, brief=args.brief if args.brief is not None else
                     args.brief_file.read_text(encoding="utf-8") if args.brief_file else None,
                     evidence=json_file(args.evidence) if args.evidence else None,
                     score=json_file(args.score) if args.score else None, family=args.family,
                     context=json_file(args.context) if args.context else None, film_id=args.film_id,
                     aspects=args.aspects, voice_provider=tts,
                     aligner=DeclaredLocalAligner(args.aligner_route) if args.aligner_route else None,
                     authority_verifier=load_verifier(args.authority_verifier) if args.authority_verifier else None,
                     sound_direction=json_file(args.sound_direction) if args.sound_direction else None,
                     sound_authority_verifier=load_verifier(args.sound_authority_verifier) if args.sound_authority_verifier else None,
                     history=json_file(args.history) if args.history else None, allow_unaligned=args.allow_unaligned,
                     fps=args.fps, workers=args.workers, asset_root=args.asset_root, proof=args.proof, staged=args.staged,
                     concept_first=args.concept_first, compact=args.compact,
                     source_quote_narration=args.source_quote_narration)
        print(json.dumps({"status": manifest["status"], "manifest": str(args.out.resolve() / "manifest.json"),
                          "authority": manifest["authority"], "gaps": manifest["gaps"]}))
        return 0
    except (AudioError, PipelineError, ScoreError, authoring.ProviderError, ValueError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "FAILED", "error": type(exc).__name__, "message": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
