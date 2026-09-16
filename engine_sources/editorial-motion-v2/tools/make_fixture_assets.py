#!/usr/bin/env python3
"""Generate the deterministic stand-in "user uploads" used by the fixture film.

Real films use customer media; these exist so the media path (governed
container, focus region, persistence, video trim) is exercised in tests.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / 'fixtures' / 'assets'


def inbox_screenshot(path: Path) -> None:
    W, H = 1440, 900
    im = Image.new('RGB', (W, H), '#ffffff')
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 56], fill='#f2f2f1')
    d.rectangle([0, 56, 260, H], fill='#f7f7f5')
    for i in range(8):
        y = 80 + i * 96
        unread = i not in (1, 4)
        d.rectangle([280, y, W - 40, y + 76], fill='#ffffff', outline='#e2e2e0')
        d.ellipse([300, y + 18, 340, y + 58], fill='#d9d9d7')
        d.rectangle([360, y + 20, 360 + 220 + (i * 37) % 200, y + 34], fill='#0e0e0e' if unread else '#9a9a98')
        d.rectangle([360, y + 44, 360 + 500 + (i * 91) % 400, y + 54], fill='#c9c9c7')
        if unread:
            d.ellipse([W - 80, y + 30, W - 64, y + 46], fill='#0e0e0e')
    for i in range(6):
        d.rectangle([24, 90 + i * 44, 200, 90 + i * 44 + 14], fill='#d4d4d2')
    im.save(path, 'PNG')


def reply_video(path: Path, seconds: int = 4, fps: int = 30) -> None:
    """A chat thread receiving a reply: bubbles land one by one, then a typing indicator resolves."""
    W, H = 1280, 720
    frames = []
    for n in range(seconds * fps):
        t = n / fps
        im = Image.new('RGB', (W, H), '#f7f7f5')
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, W, 72], fill='#ffffff', outline='#e2e2e0')
        d.ellipse([28, 16, 68, 56], fill='#0e0e0e')
        d.rectangle([90, 28, 330, 44], fill='#0e0e0e')
        for i, (side, at, w) in enumerate((('L', 0.2, 520), ('L', 0.9, 380), ('R', 1.7, 460), ('R', 2.6, 300))):
            if t < at:
                continue
            k = min(1.0, (t - at) / 0.25)
            y = 120 + i * 130
            bw = int(w * (0.85 + 0.15 * k))
            x0 = 60 if side == 'L' else W - 60 - bw
            fill = '#ffffff' if side == 'L' else '#0e0e0e'
            d.rounded_rectangle([x0, y, x0 + bw, y + 92], radius=28, fill=fill, outline='#e2e2e0')
            line = '#c9c9c7' if side == 'L' else '#6f6f6d'
            d.rectangle([x0 + 32, y + 30, x0 + bw - 40, y + 42], fill=line)
            d.rectangle([x0 + 32, y + 56, x0 + int(bw * 0.55), y + 66], fill=line)
        if 3.0 <= t:
            y = 120 + 4 * 130
            for j in range(3):
                pulse = 6 + 4 * (1 if int((t - 3.0) * 6) % 3 == j else 0)
                cx = W - 60 - 120 + j * 40
                d.ellipse([cx - pulse, y + 40 - pulse, cx + pulse, y + 40 + pulse], fill='#0e0e0e')
        frames.append(im)
    with tempfile.TemporaryDirectory() as td:
        for n, im in enumerate(frames):
            im.save(Path(td) / f'f{n:04d}.png', 'PNG')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(fps), '-i', f'{td}/f%04d.png',
                        '-c:v', 'libx264', '-preset', 'veryslow', '-crf', '20', '-pix_fmt', 'yuv420p', '-an',
                        '-map_metadata', '-1', '-fflags', '+bitexact', '-flags:v', '+bitexact', str(path)], check=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    inbox_screenshot(OUT / 'inbox-tuesday.png')
    reply_video(OUT / 'reply-landing.mp4')
    print('\n'.join(str(p) for p in sorted(OUT.iterdir())))


if __name__ == '__main__':
    sys.exit(main())
