from pathlib import Path
from playwright.sync_api import sync_playwright
from batch10_browser_utils import bundle_editor,bundle_scene
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parents[1];reports=root/'reports'
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 for workflow,name in [(False,'data-editor'),(True,'workflow-editor')]:
  pg=b.new_page(viewport={'width':1600,'height':1000});pg.set_content(bundle_editor(root,workflow),wait_until='load');pg.wait_for_timeout(150);pg.click('#replay');pg.wait_for_timeout(2800);pg.screenshot(path=str(reports/f'{name}.png'),full_page=True);pg.close()
 for name,w,h,t in [('data-story',1920,1080,13.8),('agent-workflow',1080,1080,8.6),('conversion-story',1080,1920,8.6)]:
  pg=b.new_page(viewport={'width':w,'height':h});pg.set_content(bundle_scene(root,name),wait_until='load');pg.evaluate('seekComposition('+str(t)+')');pg.screenshot(path=str(reports/f'{name}.png'),full_page=True);pg.close()
 b.close()
# montage
paths=[reports/'data-editor.png',reports/'workflow-editor.png',reports/'data-story.png',reports/'agent-workflow.png',reports/'conversion-story.png']
thumbs=[]
for p in paths:
 im=Image.open(p).convert('RGB');im.thumbnail((760,620));c=Image.new('RGB',(800,660),'white');c.paste(im,((800-im.width)//2,10));ImageDraw.Draw(c).text((16,635),p.stem,fill='black');thumbs.append(c)
canvas=Image.new('RGB',(1600,1980),'white')
for i,im in enumerate(thumbs):canvas.paste(im,((i%2)*800,(i//2)*660))
canvas.save(reports/'batch10-montage.png',quality=92)
print('captured')
