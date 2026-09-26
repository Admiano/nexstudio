from pathlib import Path
from playwright.sync_api import sync_playwright
from batch8_browser_utils import bundle
root=Path(__file__).resolve().parents[1];reports=root/'reports';reports.mkdir(exist_ok=True)
shots=[('typography-explorer.html',1440,1000,None,'typography-explorer.png'),('compositions/typography-landscape.html',1920,1080,5.5,'typography-landscape.png'),('compositions/typography-square.html',1080,1080,5.5,'typography-square.png'),('compositions/typography-portrait.html',1080,1920,5.5,'typography-portrait.png'),('compositions/kinetic-typography-demo.html',1920,1080,1.8,'kinetic-type-01.png'),('compositions/kinetic-typography-demo.html',1920,1080,7.8,'kinetic-type-02.png'),('compositions/kinetic-typography-demo.html',1920,1080,11.2,'kinetic-type-03.png'),('compositions/kinetic-typography-demo.html',1920,1080,18.0,'kinetic-type-04.png')]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 for rel,w,h,t,out in shots:
  page=b.new_page(viewport={'width':w,'height':h});page.set_content(bundle(root,rel),wait_until='load');page.wait_for_timeout(200)
  if t is not None:
   name=Path(rel).stem;page.evaluate('''([n,t])=>window.__timelines[n].seek(t)''',[name,t])
  page.screenshot(path=str(reports/out),full_page=False)
  page.close()
 b.close()
