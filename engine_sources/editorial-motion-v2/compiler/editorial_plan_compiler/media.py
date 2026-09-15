"""Customer media ingest.

Uploaded images and videos arrive in whatever codec the customer had. The
renderer captures frames in a Chromium build with only royalty-free codecs, so
every asset is normalised to a render-safe intermediate before it enters a plan:
video -> VP9/WebM (muted; the plan owns audio), images -> left alone when they
are PNG/JPEG/WebP, otherwise re-encoded to PNG. Both the customer original and
the intermediate are hashed so provenance can prove what was shown came from
what was uploaded. Nothing is cropped or retimed here; focus and trim stay in
the plan for the runtime to apply.
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from .contracts import MediaAsset, TreatmentError

RENDER_SAFE_IMAGE_SUFFIXES = {'.png', '.jpg', '.jpeg', '.webp'}
VIDEO_CODEC = 'vp9'


@dataclass
class NormalisedMedia:
    asset_id: str
    kind: str
    original_path: str
    original_sha256: str
    render_path: str
    render_sha256: str
    render_codec: str
    width: int
    height: int
    duration_s: float
    normalised: bool


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _probe(path: Path) -> dict:
    ffprobe = shutil.which('ffprobe')
    if not ffprobe:
        raise TreatmentError('FFPROBE_UNAVAILABLE', 'ffprobe is required to ingest customer media')
    out = subprocess.run(
        [ffprobe, '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=codec_name,width,height:format=duration',
         '-of', 'default=noprint_wrappers=1', str(path)],
        capture_output=True, text=True, check=False,
    )
    if out.returncode != 0:
        raise TreatmentError('MEDIA_UNREADABLE', f'{path}: {out.stderr.strip()[:200]}')
    info: dict = {}
    for line in out.stdout.splitlines():
        if '=' in line:
            k, v = line.split('=', 1)
            info[k.strip()] = v.strip()
    return info


def normalise_media(asset: MediaAsset, work_dir: Path) -> NormalisedMedia:
    src = Path(asset.path)
    if not src.exists():
        raise TreatmentError('MEDIA_ASSET_FILE_MISSING', asset.path)
    info = _probe(src)
    width = int(info.get('width') or asset.width)
    height = int(info.get('height') or asset.height)
    if (width, height) != (asset.width, asset.height):
        raise TreatmentError('MEDIA_DIMENSIONS_MISMATCH', f'{asset.asset_id}: declared {asset.width}x{asset.height}, file is {width}x{height}')
    raw_duration = info.get('duration') or ''
    duration = float(raw_duration) if raw_duration.replace('.', '', 1).isdigit() else float(asset.duration_s or 0.0)
    original_sha = _sha(src)
    media_dir = work_dir / 'media'
    media_dir.mkdir(parents=True, exist_ok=True)

    if asset.kind == 'VIDEO':
        codec = str(info.get('codec_name') or '')
        target = media_dir / f'{asset.asset_id}.{original_sha[:12]}.webm'
        if codec == VIDEO_CODEC and src.suffix.lower() == '.webm':
            return NormalisedMedia(asset.asset_id, asset.kind, str(src), original_sha, str(src), original_sha, codec, width, height, duration, False)
        if not target.exists():
            _transcode_video(src, target)
        return NormalisedMedia(asset.asset_id, asset.kind, str(src), original_sha, str(target), _sha(target), VIDEO_CODEC, width, height, duration, True)

    if src.suffix.lower() in RENDER_SAFE_IMAGE_SUFFIXES:
        return NormalisedMedia(asset.asset_id, asset.kind, str(src), original_sha, str(src), original_sha, src.suffix.lower().lstrip('.'), width, height, 0.0, False)
    target = media_dir / f'{asset.asset_id}.{original_sha[:12]}.png'
    if not target.exists():
        _run_ffmpeg(['-i', str(src), '-frames:v', '1', '-pix_fmt', 'rgba', str(target)])
    return NormalisedMedia(asset.asset_id, asset.kind, str(src), original_sha, str(target), _sha(target), 'png', width, height, 0.0, True)


def _transcode_video(src: Path, target: Path) -> None:
    # Deterministic, muted, constant-quality VP9 with even dimensions and no metadata drift.
    _run_ffmpeg([
        '-i', str(src), '-an', '-map_metadata', '-1', '-fflags', '+bitexact', '-flags:v', '+bitexact',
        '-c:v', 'libvpx-vp9', '-crf', '28', '-b:v', '0', '-row-mt', '1', '-deadline', 'good', '-cpu-used', '1',
        '-pix_fmt', 'yuv420p', '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2', str(target),
    ])


def _run_ffmpeg(args: list) -> None:
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        raise TreatmentError('FFMPEG_UNAVAILABLE', 'ffmpeg is required to normalise customer media')
    out = subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', *args], capture_output=True, text=True, check=False)
    if out.returncode != 0:
        raise TreatmentError('MEDIA_NORMALISE_FAILED', out.stderr.strip()[:300])

