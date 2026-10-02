from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_current_capability_packet() -> Dict[str, Any]:
    """Performer-capability packet for P8.

    The stickman performer registry was retired with the character offerings;
    P8 now plans only against the family execution authorities bound into the
    capability graph below. The packet shape is retained so callers keep working.
    """
    return {
        "schema": "StudioNexMindCapabilityPacketV1",
        "authorities": {},
        "performerOverrides": {},
    }


def _art_generation_available() -> bool:
    raw = os.environ.get("NEXSTUDIO_ART_EXECUTION_REGISTRY_JSON", "").strip()
    if not raw:
        return False
    try:
        registry = json.loads(raw)
    except Exception:
        return False
    caps = registry.get("capabilities") if isinstance(registry, dict) else None
    gen = caps.get("authored_scene_illustration") if isinstance(caps, dict) else None
    review = caps.get("authored_scene_pixel_fidelity_review") if isinstance(caps, dict) else None
    return all(isinstance(rec, dict) and rec.get("transport") == "command" and bool(rec.get("command")) for rec in (gen,review))


def _fallback_family_execution_authority(family: str) -> Dict[str, Any]:
    """Bind direct/preflight P8 calls to the checked-in family execution authority.

    The production workflow normally supplies the runtime authority explicitly.
    Direct Python preflights do not pass through that TypeScript workflow, so without
    this fallback they previously reported familyExecutionAuthority={} and deprived
    the creative brain of the execution-body identity it is meant to target. The
    explicit request authority always wins; this fallback never grants public-ship
    eligibility or invents capabilities absent from the checked-in registry.
    """
    registry_path=ROOT / "src" / "studio-v1" / "public" / "certification" / "four-family-capability-registry.json"
    try:
        registry=json.loads(registry_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    rec=((registry.get("families") or {}).get(str(family or "").lower()) or {}) if isinstance(registry,dict) else {}
    authority=rec.get("authority") if isinstance(rec,dict) else None
    if not isinstance(authority,dict) or not str(authority.get("authorityId") or "").strip():
        return {}
    return {
        "authorityId":str(authority.get("authorityId") or ""),
        "sourceLabel":str(authority.get("sourceLabel") or ""),
        "sourceArchiveSha256":str(authority.get("sha256") or ""),
        "technicalStatus":str(authority.get("technical") or ""),
        "executionBody":str(authority.get("execution") or ""),
        "sourceRegistry":"src/studio-v1/public/certification/four-family-capability-registry.json",
        "sourceRegistrySha256":canonical_hash(registry),
        "authorityMode":"DIRECT_PREFLIGHT_FALLBACK__EXPLICIT_WORKFLOW_AUTHORITY_OVERRIDES",
    }

def build_capability_graph(request: Dict[str, Any], packet: Dict[str, Any]) -> Dict[str, Any]:
    family = str(request.get("family") or "").upper()
    base = deepcopy(request.get("capabilityGraph") or {})
    supplied_authority=deepcopy(base.get("familyExecutionAuthority") or {})
    authorities={"family_execution_body": supplied_authority if supplied_authority else _fallback_family_execution_authority(family)}
    base.update({
        "schema": "StudioNexMindCapabilityGraphV2",
        "production_family": family,
        "video_type": request.get("videoType"),
        "duration_seconds": request.get("durationSeconds"),
        "aspect_ratio": request.get("aspectRatio"),
        "current_authorities": authorities,
        "public_family_constraints": list(((base.get("familyExecutionCapabilities") or {}).get("performerClasses") or [])),
        "family_execution_capabilities": deepcopy(base.get("familyExecutionCapabilities") or {}),
        # This bridge must not invent an asset-generation body merely to make an
        # Art Director proposal pass. A later current NexArt capability packet may
        # explicitly enable this.
        "production_scoped_asset_generation": bool(base.get("production_scoped_asset_generation", False) or _art_generation_available()),
    })
    return base
