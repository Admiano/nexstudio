from pathlib import Path
from playwright.sync_api import sync_playwright
from batch12_browser_utils import bundle_explorer,bundle_scene
from PIL import Image,ImageOps,ImageDraw
root=Path(__file__).resolve().parents[1];reports=root/'reports';reports.mkdir(exist_ok=True)
shots=[]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 pg=b.new_page(viewport={'width':1600,'height':1000});pg.set_content(bundle_explorer(root),wait_until='load');pg.wait_for_timeout(650);pg.screenshot(path=str(reports/'documentary-module-explorer.png'),full_page=False);shots.append(reports/'documentary-module-explorer.png');pg.close()
 for name,w,h,t in [('company-history',1920,1080,28.5),('investigative-example',1080,1080,28.5),('personal-memory',1080,1920,28.5)]:
  pg=b.new_page(viewport={'width':w,'height':h});pg.set_content(bundle_scene(root,name),wait_until='load');pg.evaluate('(t)=>seekComposition(t)',t);pg.screenshot(path=str(reports/f'{name}.png'),full_page=False);shots.append(reports/f'{name}.png');pg.close()
 b.close()
thumbs=[]
for p in shots:
 im=Image.open(p).convert('RGB');im.thumbnail((720,450));canvas=Image.new('RGB',(740,490),'white');canvas.paste(im,((740-im.width)//2,15));d=ImageDraw.Draw(canvas);d.text((15,465),p.stem,fill='black');thumbs.append(canvas)
out=Image.new('RGB',(1480,980),'white')
for i,im in enumerate(thumbs):out.paste(im,((i%2)*740,(i//2)*490))
out.save(reports/'batch12-montage.png')
