"""Transition grammar: every cut is a camera move the compiler picks from the beats on either side.

One grammar for the whole film — matched moves rather than a per-profile effect:
  push_through  the picture pushes into the next beat (energy rises)
  pull_back     the picture settles back out of the beat (energy falls)
  drift         a lateral matched move, direction alternating per beat (kinetic profiles, level energy)
  dissolve      soft focus dissolve (editorial profiles, level energy; carries, whose move is the element)
  cut           the authored hard cut — only when the treatment asks (beat.cut = 'hard')
The window is energy-scaled: hotter beats cut faster, never longer than the speaker's own exit.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .contracts import BeatTreatment

ENERGY_STEP = 0.12          # energy delta that reads as a rise or a fall
WINDOW_SLOW_MS = 440        # cut window at zero energy
WINDOW_FAST_MS = 260        # cut window at full energy
CUT_WINDOW_MS = 0           # a hard cut has no overlap


def transition_window_ms(cur: BeatTreatment, nxt: Optional[BeatTreatment], exit_ms: int) -> int:
    if nxt is None:
        return min(200, exit_ms)
    if cur.cut == 'hard':
        return CUT_WINDOW_MS
    hot = max(cur.energy, nxt.energy)
    return int(min(exit_ms, round(WINDOW_SLOW_MS + (WINDOW_FAST_MS - WINDOW_SLOW_MS) * hot)))


def camera_move(cur: BeatTreatment, nxt: Optional[BeatTreatment], mode: str, beat_index: int, kinetic: bool) -> Optional[Dict[str, Any]]:
    """The camera treatment of the cut out of `cur`; None on the last beat (nothing to cut to)."""
    if nxt is None:
        return None
    direction = 1 if beat_index % 2 == 0 else -1
    if cur.cut == 'hard':
        return {'move': 'cut', 'dir': 0, 'blur': 0.0}
    carried = mode in ('EVIDENCE_PERSISTENCE', 'ILLUSTRATION_PERSISTENCE') or bool(
        nxt.illustration and nxt.illustration.carry_from == cur.beat_id and nxt.illustration.carry_entities)
    if carried:
        # The matched move is the carried element itself; the camera only lets the rest go.
        return {'move': 'dissolve', 'dir': direction, 'blur': 0.0}
    delta = nxt.energy - cur.energy
    if delta >= ENERGY_STEP:
        move = 'push_through'
    elif delta <= -ENERGY_STEP:
        move = 'pull_back'
    else:
        move = 'drift' if kinetic else 'dissolve'
    return {'move': move, 'dir': direction, 'blur': 1.0}
