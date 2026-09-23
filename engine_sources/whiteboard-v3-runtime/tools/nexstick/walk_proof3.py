"""Walk proof v3 — real nexstick mocap -> paperbook rig -> line-art strokes.

(1) hand inks the figure (frame-0 pose) + ground line
(2) figure physically walks the board; x travel = real mocap root world-x.
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
RUNTIME = HERE.parent.parent
sys.path.insert(0, str(RUNTIME / 'tools' / 'paper_cast'))
import line_cast  # noqa: E402

W, H, FPS = 1280, 720, 24
DRAW_S, WALK_S = 2.4, 2.6
GROUND_Y = int(H * 0.78)
MARGIN_X = 140
FIG_PX = int(H * 0.58)          # rendered figure height
SPEED_MPS = 1.15
HAND_PNG = RUNTIME / 'assets' / 'hand' / 'drawing-hand.png'
SVG_DIR = Path('/tmp/mocap_rig_frames')
OUT = Path('/tmp/mocap_walk3')
NODE = '/home/ubuntu/.nvm/versions/node/v24.19.0/bin/node'


def paste_hand(img, tip):
    hand = getattr(paste_hand, '_img', None)
    if hand is None:
        h = Image.open(HAND_PNG).convert('RGBA')
        scale = (H * 0.24) / h.height
        hand = h.resize((max(1, int(h.width * scale)), int(H * 0.24)), Image.LANCZOS)
        paste_hand._img = hand
    img.paste(hand, (int(tip[0] - 5), int(tip[1] - 8)), hand)


def load_frames():
    n = int((WALK_S + 0.5) * FPS)
    subprocess.run([NODE, str(HERE / 'mocap_rig.cjs'),
                    json.dumps({'action': 'walk', 'speedMps': SPEED_MPS}),
                    str(SVG_DIR), str(n), str(FPS)], check=True)
    meta = json.loads((SVG_DIR / 'poses.json').read_text())
    frames = []
    for i, m in enumerate(meta):
        svg = SVG_DIR / f'g{i:03d}.svg'
        strokes = line_cast.figure_strokes(str(svg), 1000)   # native svg units
        ys = [y for poly, _ in strokes for _, y in poly]
        xmin = min(x for poly, _ in strokes for x, _ in poly)
        xmax = max(x for poly, _ in strokes for x, _ in poly)
        frames.append({'strokes': strokes, 'ymin': min(ys), 'ymax': max(ys),
                       'cx': (xmin + xmax) / 2, 'root_m': m['root'][2]})
    return frames


def draw_figure(img, fr, cx_px, ground_y, scale, n_show=None):
    d = ImageDraw.Draw(img)
    strokes = fr['strokes']
    n = len(strokes) if n_show is None else n_show
    last_tip = None
    for poly, detail in strokes[:n]:
        pts = [(cx_px - (x - fr['cx']) * scale,   # mirror x: face leads +x travel
                ground_y - (0 - y) * scale) for x, y in poly]
        if len(pts) < 2:
            continue
        if detail == 'fill':
            d.polygon(pts, fill=0)
        else:
            d.line(pts, fill=0, width=max(2, int(scale * (6 if not detail else 3))), joint='curve')
        last_tip = pts[-1]
    return last_tip


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob('f*.png'):
        old.unlink()
    frames = load_frames()
    # scale: figure pixel height -> FIG_PX
    hgt = max(f['ymax'] - f['ymin'] for f in frames)
    scale = FIG_PX / hgt
    root0 = frames[0]['root_m']

    total = int((DRAW_S + WALK_S) * FPS)
    n_draw = int(DRAW_S * FPS)
    rest = frames[0]
    written = 0
    for fi in range(total):
        img = Image.new('RGB', (W, H), (253, 252, 248))
        d = ImageDraw.Draw(img)
        d.line([(MARGIN_X - 70, GROUND_Y), (W - MARGIN_X + 70, GROUND_Y)], fill=0, width=3)
        if fi < n_draw:
            n_show = max(1, int(len(rest['strokes']) * (fi + 1) / n_draw))
            tip = draw_figure(img, rest, MARGIN_X + 90, GROUND_Y, scale, n_show)
            if tip and fi % 2 == 0:
                paste_hand(img, tip)
        else:
            i = min(fi - n_draw, len(frames) - 1)
            fr = frames[i]
            # real mocap root travel (metres) -> px at figure scale
            x_m = (fr['root_m'] - root0)
            px_m = scale * 1000 / 1.68   # svg height 1000 == 1.68 m figure
            cx = min(MARGIN_X + 90 + x_m * px_m, W - MARGIN_X - 40)
            if cx > W + 260:
                break
            draw_figure(img, fr, cx, GROUND_Y, scale)
        img.convert('RGB').save(OUT / f'f{fi:04d}.png')
        written += 1

    subprocess.run(['ffmpeg', '-y', '-framerate', str(FPS), '-i', str(OUT / 'f%04d.png'),
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '/home/ubuntu/MOCAP_WALK3.mp4'],
                   check=True, capture_output=True)
    print('frames:', written, '| scale:', round(scale, 3))


if __name__ == '__main__':
    main()
