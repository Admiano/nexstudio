"""Opt-in internal P8 semantic execution adapter; NOT registered public dispatch.

The caller owns authentication of the whole exact request, including committed
score/evidence and sound direction. Hash syntax is never treated as P8 approval.
Legacy explainer_adapter.py and public routes remain unchanged.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[2]
ENGINE = REPO / "engine_sources/explainer-direction"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

from explainer_direction.audio import DeclaredLocalTTS, DeclaredLocalAligner, sha256
from explainer_direction.contracts import CAPABILITIES, ASPECTS, validate_score, validate_evidence


class DirectionAdapterBlocked(RuntimeError):
    pass


def capabilities():
    """No readiness/quality certification inferred from a vocabulary listing."""
    return {"schema": "StudioExplainerDirectionCapabilitiesV1", "capabilities": deepcopy(CAPABILITIES),
            "aspects": list(ASPECTS), "creative_authority": "P8", "public_dispatch_enabled": False,
            "creative_lock": False, "certification": "NOT_CERTIFIED"}


def build_internal_evidence(request, *, authority_verifier, voice_provider=None, aligner=None):
    """Execute exact StudioExplainerDirectionRequestV1 approved semantic request.

    authority_verifier(deepcopy(request))->True is an authenticated *caller*
    boundary and must verify committed decision slots, exact score/evidence and
    P8 state/board plus optional soundDirection. It is not a mock hash checker.
    Required request fields: schema, semanticDirection, evidence, brief,
    outputDirectory. Optional aspects, soundDirection, fps, workers, assetRoot,
    ttsRoute, voiceSource, voiceId, alignerRoute, proof. No fixture injection or
    live authoring is admitted here. Result is render-ready evidence only.
    """
    if not isinstance(request, dict) or request.get("schema") != "StudioExplainerDirectionRequestV1":
        raise DirectionAdapterBlocked("DIRECTION_REQUEST_SCHEMA_REQUIRED")
    required = {"schema", "semanticDirection", "evidence", "brief", "outputDirectory"}
    optional = {"aspects", "soundDirection", "fps", "workers", "assetRoot", "ttsRoute", "voiceSource", "voiceId", "alignerRoute", "proof"}
    if not required <= set(request) or set(request) - required - optional:
        raise DirectionAdapterBlocked("DIRECTION_EXACT_REQUEST_FIELDS_REQUIRED")
    packet = deepcopy(request)
    score = validate_score(packet["semanticDirection"])
    evidence = validate_evidence(packet["evidence"])
    if score["provenance"]["mode"] != "p8_bound" or score["provenance"].get("test_fixture"):
        raise DirectionAdapterBlocked("AUTHENTICATED_P8_SEMANTIC_DIRECTION_REQUIRED")
    if score["evidence"] != evidence or score["brief"] != packet["brief"]:
        raise DirectionAdapterBlocked("P8_DIRECTION_EVIDENCE_AND_BRIEF_MUST_MATCH_EXACTLY")
    if not callable(authority_verifier) or authority_verifier(deepcopy(packet)) is not True:
        raise DirectionAdapterBlocked("P8_CALLER_AUTHENTICATION_FAILED; declared hashes are not authentication")
    if voice_provider is not None and getattr(voice_provider, "is_test_fixture", False):
        raise DirectionAdapterBlocked("FIXTURE_VOICE_FORBIDDEN_IN_P8_ADAPTER")
    if aligner is not None and getattr(aligner, "is_test_fixture", False):
        raise DirectionAdapterBlocked("FIXTURE_ALIGNER_FORBIDDEN_IN_P8_ADAPTER")
    voice_provider = voice_provider if voice_provider is not None else DeclaredLocalTTS(packet.get("ttsRoute"), packet.get("voiceSource"), packet.get("voiceId"))
    aligner = aligner if aligner is not None else DeclaredLocalAligner(packet["alignerRoute"]) if packet.get("alignerRoute") else None
    spec = importlib.util.spec_from_file_location("explainer_direction_local_pipeline", ENGINE / "tools/make_film.py")
    if spec is None or spec.loader is None:
        raise DirectionAdapterBlocked("LOCAL_PIPELINE_MODULE_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest = module.run_pipeline(output=packet["outputDirectory"], score=score, evidence=evidence, brief=packet["brief"],
                 aspects=packet.get("aspects", list(ASPECTS)), voice_provider=voice_provider, aligner=aligner,
                 authority_verifier=lambda candidate: candidate == score,
                 sound_direction=packet.get("soundDirection"),
                 sound_authority_verifier=lambda sound: sound == {"score": score, "sound_direction": packet.get("soundDirection")},
                 fps=packet.get("fps", 30), workers=packet.get("workers", 2),
                 asset_root=packet.get("assetRoot"), proof=packet.get("proof"))
    if manifest["status"] != "RENDER_READY_NOT_CREATIVE_LOCKED":
        raise DirectionAdapterBlocked("DIRECTION_RENDER_NOT_READY")
    manifest_path = Path(packet["outputDirectory"]).resolve() / "manifest.json"
    return {"schema": "StudioExplainerDirectionExecutionEvidenceV1", "status": "RENDER_READY",
            "topLevelCreativeAuthority": "NEXMIND_P8", "executionBody": "EXPLAINER_DIRECTION_V1",
            "creativeLocked": False, "certification": "NOT_CERTIFIED", "publicDispatchEnabled": False,
            "manifestPath": str(manifest_path), "manifestSha256": sha256(manifest_path),
            "semanticAuthority": deepcopy(manifest["authority"]), "directionProvenance": deepcopy(score["provenance"]),
            "renders": deepcopy(manifest["renders"]), "gaps": list(manifest["gaps"])}
