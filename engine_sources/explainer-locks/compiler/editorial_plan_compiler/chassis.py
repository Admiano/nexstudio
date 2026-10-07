"""Device chassis for customer media.

Every uploaded image or video is presented inside a housing — a phone slab for portrait
media, a screenshot slab for landscape and square media, a paper card for documents — so a
frame never shows a bare, unframed asset. The choice is a pure function of the asset's kind
and aspect; an authored ``chassis`` param always wins. The tilt is profile-driven and
deterministic per asset so the same upload lands the same way on every render.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, Optional

CHASSIS = ('phone', 'browser', 'card', 'shot')

# Aspect (w/h) below which media reads as a handset screen rather than a desktop shot.
PORTRAIT_AR = 0.85
TILT_MIN_DEG = 2.4
TILT_MAX_DEG = 4.6
# Below this on-stage share the housing is a supporting still and sits square; heroes float.
TILT_FLOAT_SIZES = ('hero',)
# A handset is a fixed object: its slab keeps the device ratio and the screen cover-fits the
# upload. Other housings wrap the media's own ratio.
PHONE_AR = 0.478


def resolve_chassis(kind: str, width: int, height: int, authored: Optional[str] = None) -> str:
    if authored:
        if authored not in CHASSIS:
            raise ValueError(f'unknown chassis {authored!r}')
        return authored
    if kind == 'DOCUMENT':
        return 'card'
    ar = (width / height) if height else 1.0
    return 'phone' if ar < PORTRAIT_AR else 'shot'


def chassis_aspect(chassis: str, media_ar: float) -> float:
    return PHONE_AR if chassis == 'phone' else media_ar


def resolve_tilt(asset_id: str, motion: Dict[str, Any], size: str = 'hero', authored: Optional[float] = None) -> float:
    """Stable per-asset float tilt in degrees; sign alternates on the asset's hash so a stage
    with two shots never leans the same way. Editorial profiles keep media square."""
    if authored is not None:
        return max(-14.0, min(14.0, float(authored)))
    gain = float(motion.get('media_tilt', 0.0) or 0.0)
    if gain <= 0 or size not in TILT_FLOAT_SIZES:
        return 0.0
    h = hashlib.sha256(asset_id.encode('utf-8')).digest()
    mag = TILT_MIN_DEG + (TILT_MAX_DEG - TILT_MIN_DEG) * (h[0] / 255.0)
    sign = -1.0 if h[1] & 1 else 1.0
    return round(sign * mag * gain, 2)


def housing(kind: str, width: int, height: int, asset_id: str, motion: Dict[str, Any], size: str = 'hero',
            authored_chassis: Optional[str] = None, authored_tilt: Optional[float] = None) -> Dict[str, Any]:
    chassis = resolve_chassis(kind, width, height, authored_chassis)
    return {'chassis': chassis, 'tilt': resolve_tilt(asset_id, motion, size, authored_tilt)}
