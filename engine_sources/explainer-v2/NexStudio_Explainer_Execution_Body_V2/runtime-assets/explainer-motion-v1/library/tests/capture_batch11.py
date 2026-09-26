from pathlib import Path
from playwright.sync_api import sync_playwright
from batch11_browser_utils import bundle_explorer,bundle_scene
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parents[1];reports=root/'reports'
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 pg=b.new_page(viewport={'width':1600,'height':1000});pg.set_content(bundle_explorer(root),wait_until='load');pg.wait_for_timeout(750);pg.screenshot(path=str(reports/'creator-module-explorer.png'));pg.close()
 for name,w,h,t in [('creator-growth-recap',1920,1080,10.6),('sponsorship-announcement',1080,1080,10.6),('publishing-workflow',1080,1920,10.6)]:
  pg=b.new_page(viewport={'width':w,'height':h});pg.set_content(bundle_scene(root,name),wait_until='load');pg.evaluate('(t)=>seekComposition(t)',t);pg.screenshot(path=str(reports/f'{name}.png'));pg.close()
 b.close()
paths=[reports/'creator-module-explorer.png',reports/'creator-growth-recap.png',reports/'sponsorship-announcement.png',reports/'publishing-workflow.png']
thumbs=[]
for path in paths:
 im=Image.open(path).convert('RGB');im.thumbnail((760,620));c=Image.new('RGB',(800,660),'white');c.paste(im,((800-im.width)//2,10));ImageDraw.Draw(c).text((16,635),path.stem,fill='black');thumbs.append(c)
canvas=Image.new('RGB',(1600,1320),'white')
for i,im in enumerate(thumbs):canvas.paste(im,((i%2)*800,(i//2)*660))
canvas.save(reports/'batch11-montage.png',quality=92)
print('captured')
