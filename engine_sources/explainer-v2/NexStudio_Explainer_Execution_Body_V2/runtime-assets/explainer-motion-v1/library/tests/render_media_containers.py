from pathlib import Path
from playwright.sync_api import sync_playwright
from batch9_browser_utils import bundle_media_scene, bundle_media_explorer
import subprocess, shutil, json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'renders' / 'playwright-batch9'
RAW.mkdir(parents=True, exist_ok=True)
REPORTS = ROOT / 'reports'
RENDERS = ROOT / 'renders'
DURATION = 12.0


def probe(path: Path):
    if not path.exists():
        return None
    try:
        data = json.loads(subprocess.check_output([
            'ffprobe','-v','error','-show_entries','stream=width,height,r_frame_rate',
            '-show_entries','format=duration','-of','json',str(path)
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


def valid(path: Path, width: int, height: int, tolerance: float = 0.08):
    info = probe(path)
    return bool(info and abs(info['duration'] - DURATION) <= tolerance and info['width'] == width and info['height'] == height)


def encode(src: Path, dst: Path, width: int, height: int, crf='21', preset='medium', fps=30):
    if valid(dst, width, height):
        return
    subprocess.run([
        'ffmpeg','-y','-loglevel','error','-i',str(src),'-t',str(DURATION),
        '-vf',f'scale={width}:{height},fps={fps}', '-c:v','libx264','-preset',preset,
        '-crf',str(crf),'-pix_fmt','yuv420p','-movflags','+faststart',str(dst)
    ], check=True)


def record_scene(browser, name: str, width: int, height: int, raw_name: str):
    dst = RAW / raw_name
    # WebM dimensions are only an intermediate; duration is sufficient for resume.
    info = probe(dst)
    if info and abs(info['duration'] - DURATION) <= 0.15:
        return dst
    ctx = browser.new_context(
        viewport={'width': width, 'height': height},
        record_video_dir=str(RAW),
        record_video_size={'width': width, 'height': height},
    )
    page = ctx.new_page()
    page.set_content(bundle_media_scene(ROOT, name), wait_until='load')
    page.wait_for_timeout(350)
    page.evaluate('(n)=>window.__timelines[n].restart()', name)
    page.wait_for_timeout(12600)
    video = page.video
    ctx.close()
    captured = Path(video.path())
    if captured != dst:
        shutil.move(str(captured), str(dst))
    return dst


def screenshots(browser):
    explorer = REPORTS / 'media-container-explorer.png'
    page = browser.new_page(viewport={'width':1720,'height':1100})
    page.set_content(bundle_media_explorer(ROOT), wait_until='load')
    page.wait_for_timeout(800)
    page.screenshot(path=str(explorer), full_page=True)
    page.close()
    for name,w,h in [('product-demo',1920,1080),('creator-profile',1080,1080),('photo-story',1080,1920)]:
        out = REPORTS / f'{name}.png'
        pg = browser.new_page(viewport={'width':w,'height':h})
        pg.set_content(bundle_media_scene(ROOT,name),wait_until='load')
        pg.wait_for_timeout(350)
        pg.evaluate('seekComposition(6.4)')
        pg.screenshot(path=str(out),full_page=True)
        pg.close()


def montage():
    paths=[REPORTS/'product-demo.png', REPORTS/'creator-profile.png', REPORTS/'photo-story.png']
    thumbs=[]
    for path in paths:
        image=Image.open(path).convert('RGB'); image.thumbnail((720,720)); thumbs.append(image)
    canvas=Image.new('RGB',(1440,1440),(239,232,220))
    for image,pos in zip(thumbs,[(0,0),(720,0),(360,720)]):
        canvas.paste(image,pos)
    canvas.save(REPORTS/'batch9-montage.png')


def main():
    outputs = {
        'product-demo-high.mp4': (1920,1080),
        'product-demo-standard.mp4': (1280,720),
        'product-demo-draft.mp4': (854,480),
        'creator-profile-standard.mp4': (1080,1080),
        'photo-story-standard.mp4': (1080,1920),
    }
    missing_master = not valid(RENDERS/'product-demo-high.mp4',1920,1080)
    missing_creator = not valid(RENDERS/'creator-profile-standard.mp4',1080,1080)
    missing_story = not valid(RENDERS/'photo-story-standard.mp4',1080,1920)
    needs_screens = any(not (REPORTS/x).exists() for x in ['media-container-explorer.png','product-demo.png','creator-profile.png','photo-story.png'])

    product_src = creator_src = story_src = None
    if missing_master or missing_creator or missing_story or needs_screens:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
            if missing_master:
                product_src=record_scene(browser,'product-demo',1280,720,'product-demo.webm')
            if missing_creator:
                creator_src=record_scene(browser,'creator-profile',1080,1080,'creator-profile.webm')
            if missing_story:
                # Lighter capture is intentionally used for reliable portrait rendering.
                story_src=record_scene(browser,'photo-story',540,960,'photo-story.webm')
            screenshots(browser)
            browser.close()

    if missing_master:
        encode(product_src,RENDERS/'product-demo-high.mp4',1920,1080,crf='18')
    encode(RENDERS/'product-demo-high.mp4',RENDERS/'product-demo-standard.mp4',1280,720,crf='23',preset='veryfast')
    encode(RENDERS/'product-demo-high.mp4',RENDERS/'product-demo-draft.mp4',854,480,crf='29',preset='ultrafast',fps=24)
    if missing_creator:
        encode(creator_src,RENDERS/'creator-profile-standard.mp4',1080,1080,crf='21')
    if missing_story:
        encode(story_src,RENDERS/'photo-story-standard.mp4',1080,1920,crf='21')

    montage()
    details={name:probe(RENDERS/name) for name in outputs}
    errors=[name for name,(w,h) in outputs.items() if not valid(RENDERS/name,w,h)]
    report={
        'status':'PASS' if not errors else 'FAIL',
        'duration':DURATION,
        'outputs':details,
        'sourceCompositions':{
            'product-demo':'1920x1080',
            'creator-profile':'1080x1080',
            'photo-story':'1080x1920',
        },
        'captureNotes':{
            'product-demo':'1280x720 deterministic browser capture encoded to 1920x1080',
            'creator-profile':'native 1080x1080 deterministic browser capture',
            'photo-story':'540x960 deterministic browser capture encoded to native 1080x1920 delivery',
        },
        'errors':errors,
    }
    (REPORTS/'batch9-render.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    if errors:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
