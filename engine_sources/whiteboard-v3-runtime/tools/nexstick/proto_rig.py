#!/usr/bin/env python3
"""proto_rig — render vault motion clips in the RGS proto-stick style.

Draws exercise_vault_v5.json joint frames as the same character the
proto pack ships: filled circle head + tapered grey torso with ink
outline, thin stick limbs, dot hands, shoe tips — pure ink on alpha.
Output lands in tools/nexstick/baked/PROTO_<CLIP>/ exactly like
mh_bake/proto_pack output, so fig_motion.get_strip serves it.

This is the sanctioned way to extend the proto cast: only motion from
the vaults may be drawn through it (exercise set today); nothing else
is added to the character.

Usage: python3 tools/proto_rig.py [CLIP ...]   # default: all EX_*
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
VAULT = HERE / 'compiled' / 'exercise_vault_v5.json'
OUT = HERE / 'baked'

# proto palette measured from the pack (idle frame): ink outline ~#0A0A0A,
# body fill ~#E2E2E2, hands/feet fill darker
INK = (12, 12, 12, 255)
FILL = (226, 226, 226, 255)
DOT = (26, 26, 30, 255)

S = 260.0            # px per meter — strips get union-cropped anyway
CANVAS = (512, 512)
GROUND_Y = CANVAS[1] - 30      # feet rest here; union crop trims margins
HEAD_R = 0.19        # proto head radius (m) — the pack's big-head ratio
TORSO_W_TOP = 0.135  # shoulder halfwidth (m) — slim like the pack
TORSO_W_BOT = 0.095  # hip halfwidth (m)
LIMB_W = 6           # px stroke width for arms/legs
OUTLINE_W = 4        # px outline on filled shapes
HAND_R = 0.055       # hand dot radius (m)
FOOT_W = 9           # shoe stroke width (px)


def _j(frame, joints, name):
    return frame[joints.index(name)]


OBLIQUE = 0.35       # lateral x blends into screen-x — near/far limbs
                     # separate like the pack's stance instead of
                     # collapsing onto one stroke in pure profile


def _px(x, y, z):
    """world (z fwd, y up, x lateral) -> canvas px (oblique side view)."""
    return (CANVAS[0] / 2 + (z + OBLIQUE * x) * S, GROUND_Y - y * S)


def _perp(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1.0
    return -dy / n * S, dx / n * S  # unit px perpendicular * S scale


def _cap_arc(dr, c, r_px, a_deg, a_mid_deg):
    """Ink the semicircle of the disc at (c, r_px) starting at angle
    a_deg, choosing the sweep that passes through a_mid_deg (PIL arcs
    sweep clockwise from the start angle in image coords)."""
    box = [c[0] - r_px, c[1] - r_px, c[0] + r_px, c[1] + r_px]
    if (a_mid_deg - a_deg) % 360 < 180:
        dr.arc(box, a_deg, a_deg + 180, fill=INK, width=OUTLINE_W)
    else:
        dr.arc(box, a_deg + 180, a_deg + 360, fill=INK, width=OUTLINE_W)


def draw_frame(frame, joints, canvas_w=CANVAS[0], canvas_h=CANVAS[1]):
    """One vault frame -> RGBA PIL image in proto style."""
    img = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    P = {j: _px(*_j(frame, joints, j)) for j in joints}

    def limb(a, b, c=None, w=LIMB_W):
        pts = [P[a], P[b]] + ([P[c]] if c else [])
        dr.line(pts, fill=INK, width=w, joint='curve')

    # far-side limbs first (right side reads as far in the pack's pose)
    for s in ('r', 'l'):
        limb(f'shoulder_{s}', f'elbow_{s}', f'wrist_{s}')
        limb(f'hip_{s}', f'knee_{s}', f'ankle_{s}')
        # shoe: ankle->toe thick stroke + toe cap
        a, t = P[f'ankle_{s}'], P[f'toe_{s}']
        dr.line([a, t], fill=DOT, width=FOOT_W)
        dr.ellipse([t[0] - FOOT_W / 2, t[1] - FOOT_W / 2,
                    t[0] + FOOT_W / 2, t[1] + FOOT_W / 2], fill=DOT)
        # hand dot at wrist
        wx, wy = P[f'wrist_{s}']
        r = HAND_R * S
        dr.ellipse([wx - r, wy - r, wx + r, wy + r], fill=DOT)

    # torso: tapered capsule pelvis->neck — filled quad + cap discs,
    # then ink: two side edges and the exterior arc of each cap
    pel, nek = P['pelvis'], P['neck']
    ux, uy = _perp(pel, nek)          # unit perpendicular * S (px/m)
    wt, wb = TORSO_W_TOP, TORSO_W_BOT  # halfwidths in metres
    np_, nm_ = (nek[0] + ux * wt, nek[1] + uy * wt), \
        (nek[0] - ux * wt, nek[1] - uy * wt)
    pp_, pm_ = (pel[0] + ux * wb, pel[1] + uy * wb), \
        (pel[0] - ux * wb, pel[1] - uy * wb)
    dr.polygon([np_, nm_, pm_, pp_], fill=FILL)
    dr.ellipse([nek[0] - wt * S, nek[1] - wt * S,
                nek[0] + wt * S, nek[1] + wt * S], fill=FILL)
    dr.ellipse([pel[0] - wb * S, pel[1] - wb * S,
                pel[0] + wb * S, pel[1] + wb * S], fill=FILL)
    dr.line([np_, pp_], fill=INK, width=OUTLINE_W)
    dr.line([nm_, pm_], fill=INK, width=OUTLINE_W)
    a_perp = math.degrees(math.atan2(uy, ux))
    _cap_arc(dr, nek, wt * S, a_perp,
             math.degrees(math.atan2(nek[1] - pel[1], nek[0] - pel[0])))
    _cap_arc(dr, pel, wb * S, a_perp + 180,
             math.degrees(math.atan2(pel[1] - nek[1], pel[0] - nek[0])))

    # head: filled circle centered on the head joint
    hx, hy = P['head']
    hr = HEAD_R * S
    dr.ellipse([hx - hr, hy - hr, hx + hr, hy + hr],
               fill=FILL, outline=INK, width=OUTLINE_W)
    return img


def render_clip(name, clip, joints, out_root=OUT):
    imgs = [draw_frame(fr, joints) for fr in clip['frames']]
    box = None
    for im in imgs:
        b = im.getchannel('A').getbbox()
        box = (b if box is None else
               (min(box[0], b[0]), min(box[1], b[1]),
                max(box[2], b[2]), max(box[3], b[3])))
    if not box:
        return None
    pad = 4
    box = (max(0, box[0] - pad), max(0, box[1] - pad),
           min(imgs[0].width, box[2] + pad),
           min(imgs[0].height, box[3] + pad))
    d = out_root / f'PROTO_{name}'
    d.mkdir(parents=True, exist_ok=True)
    for i, im in enumerate(imgs):
        im.crop(box).save(d / f'f{i:04d}.png')
    meta = {'clip': f'PROTO_{name}', 'frames': len(imgs),
            'fps': float(clip.get('fps') or 30),
            'res': [box[2] - box[0], box[3] - box[1]],
            'cam': 'side', 'proto': True,
            'source': 'proto_rig', 'license': clip.get('license')}
    (d / 'meta.json').write_text(json.dumps(meta, indent=1))
    return d


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    v = json.loads(VAULT.read_text())
    joints, clips = v['joints'], v['clips']
    todo = argv or sorted(clips)
    done = []
    for name in todo:
        if name not in clips:
            print(f'skip unknown clip {name}')
            continue
        d = render_clip(name, clips[name], joints)
        done.append(str(d.name) if d else f'{name}:EMPTY')
    print(f'{len(done)} clips -> {OUT}')
    print('\n'.join(done))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
