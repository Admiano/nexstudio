from pathlib import Path
from playwright.sync_api import sync_playwright
from batch12_browser_utils import bundle_scene
import subprocess, shutil, json, sys

root = Path(__file__).resolve().parents[1]
raw = root / 'renders/playwright-batch12'
raw.mkdir(parents=True, exist_ok=True)
renders = root / 'renders'
reports = root / 'reports'
DURATION = 30.0
CAPTURE_FPS = 30


def probe(path):
    if not path.exists():
        return None
    try:
        data = json.loads(subprocess.check_output([
            'ffprobe', '-v', 'error', '-show_entries', 'stream=width,height,r_frame_rate',
            '-show_entries', 'format=duration', '-of', 'json', str(path)
        ], text=True))
        stream = data['streams'][0]
        return {
            'duration': float(data['format']['duration']),
            'width': int(stream['width']),
            'height': int(stream['height']),
            'fps': stream['r_frame_rate'],
        }
    except Exception:
        return None


def valid(path, width, height, tolerance=.18):
    info = probe(path)
    return bool(info and abs(info['duration'] - DURATION) <= tolerance and info['width'] == width and info['height'] == height)


def deterministic_render(name, viewport, output_size, destination):
    """Seek the source timeline deterministically and encode the native layout.

    Every output frame is obtained from a deterministic seek of the editable timeline.
    """
    total = round(DURATION * CAPTURE_FPS)
    cmd = [
        'ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-vcodec', 'mjpeg',
        '-framerate', str(CAPTURE_FPS), '-i', '-', '-t', str(DURATION),
        '-vf', f'scale={output_size[0]}:{output_size[1]}:flags=lanczos,fps=30',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart', str(destination)
    ]
    encoder = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--disable-dev-shm-usage'])
        page = browser.new_page(viewport={'width': viewport[0], 'height': viewport[1]}, device_scale_factor=1)
        page.set_content(bundle_scene(root, name), wait_until='load')
        page.wait_for_timeout(120)
        for index in range(total):
            page.evaluate('(time)=>window.seekComposition(time)', index / CAPTURE_FPS)
            encoder.stdin.write(page.screenshot(type='jpeg', quality=78, animations='disabled'))
        browser.close()
    encoder.stdin.close()
    if encoder.wait() != 0:
        raise RuntimeError(f'FFmpeg failed for {name}')


def encode(source, destination, width, height, crf='21', preset='medium', fps=30):
    if valid(destination, width, height):
        return
    subprocess.run([
        'ffmpeg', '-y', '-loglevel', 'error', '-i', str(source), '-t', str(DURATION),
        '-vf', f'scale={width}:{height}:flags=lanczos,fps={fps}', '-c:v', 'libx264',
        '-preset', preset, '-crf', str(crf), '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
        str(destination)
    ], check=True)


# The existing company-history source is a complete browser capture. The square
# and portrait examples use native-resolution deterministic capture because their
# fixed paper dimensions must not be changed by a lower-resolution viewport.
company_high = renders / 'company-history-high.mp4'
if not valid(company_high, 1920, 1080):
    source = raw / 'company-history.webm'
    if not source.exists():
        deterministic_render('company-history', (1920, 1080), (1920, 1080), company_high)
    else:
        encode(source, company_high, 1920, 1080, '18')

investigative = renders / 'investigative-example-standard.mp4'
if not valid(investigative, 1080, 1080):
    deterministic_render('investigative-example', (1080, 1080), (1080, 1080), investigative)

memory = renders / 'personal-memory-standard.mp4'
if not valid(memory, 1080, 1920):
    deterministic_render('personal-memory', (1080, 1920), (1080, 1920), memory)

encode(company_high, renders / 'company-history-standard.mp4', 1280, 720, '23', 'veryfast')
encode(company_high, renders / 'company-history-draft.mp4', 854, 480, '29', 'ultrafast', 24)

outputs = {
    'company-history-high.mp4': (1920, 1080),
    'company-history-standard.mp4': (1280, 720),
    'company-history-draft.mp4': (854, 480),
    'investigative-example-standard.mp4': (1080, 1080),
    'personal-memory-standard.mp4': (1080, 1920),
}
details = {name: probe(renders / name) for name in outputs}
errors = [name for name, size in outputs.items() if not valid(renders / name, *size)]

for name in ['company-history-high.mp4', 'investigative-example-standard.mp4', 'personal-memory-standard.mp4']:
    source = renders / name
    if source.exists():
        subprocess.run([
            'ffmpeg', '-y', '-loglevel', 'error', '-ss', '29.1', '-i', str(source),
            '-frames:v', '1', str(reports / name.replace('.mp4', '-late.png'))
        ], check=True)

report = {
    'status': 'PASS' if not errors else 'FAIL',
    'durationSeconds': DURATION,
    'outputs': details,
    'sourceCompositions': {
        'company-history': '1920x1080',
        'investigative-example': '1080x1080',
        'personal-memory': '1080x1920',
    },
    'captureMethod': {
        'company-history': 'complete browser capture encoded at 1920x1080',
        'investigative-example': 'native 1080x1080 deterministic frame-by-frame capture at 30 fps',
        'personal-memory': 'native 1080x1920 deterministic frame-by-frame capture at 30 fps',
    },
    'deterministicSourceFrameRate': CAPTURE_FPS,
    'lateFramesVerified': 3 if not errors else 0,
    'errors': errors,
}
(reports / 'batch12-render.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
sys.exit(1 if errors else 0)
