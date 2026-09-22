from pathlib import Path
import json,sys
from playwright.sync_api import sync_playwright
from batch8_browser_utils import bundle
root=Path(__file__).resolve().parents[1];errors=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium');page=browser.new_page(viewport={'width':1440,'height':1000})
    console=[];page.on('console',lambda m: console.append(m.text) if m.type=='error' else None);page.set_content(bundle(root,'typography-explorer.html'),wait_until='load');page.wait_for_timeout(500)
    result=page.evaluate('''()=>{const out={count:NexTypography.registry.length,created:0,layers:0,styles:new Set(),alignments:new Set(),durations:[],special:{}};for(const d of NexTypography.registry){const c=NexTypography.create(d,{title:'Responsive typography',body:'Long-form editable content with punctuation, numbers 123 and safe wrapping.',meta:'NEXSTUDIO',emphasis:'Responsive,typography',items:['One item','Two item','Three item']});document.body.appendChild(c);NexTypography.fitText(c);out.created++;out.layers+=c.querySelectorAll('.type-paper,.type-content').length;for(const s of ['clean-editorial','handmade-scrapbook','technical-notebook']){NexTypography.setStyle(c,s);out.styles.add(c.dataset.style)}for(const a of ['left','center','right']){NexTypography.setAlignment(c,a);out.alignments.add(c.dataset.align)}const tl=NexTypography.animate(c,{duration:1.6,energy:'high'});out.durations.push(tl.duration());tl.seek(tl.duration()*.55);if(d.slug==='typewriter-note')out.special.typewriter=c.querySelector('.typewriter-target').textContent.length;if(d.slug==='statistic-headline')out.special.stat=c.querySelector('[data-number]').textContent;if(d.slug==='numbered-list')out.special.list=c.querySelectorAll('li').length;if(d.slug==='marker-highlight')out.special.marker=getComputedStyle(c.querySelector('.type-highlight-word')).getPropertyValue('--marker-progress');c.remove()}return {...out,styles:[...out.styles],alignments:[...out.alignments],searchButtons:document.querySelectorAll('#type-list button').length,selected:window.__typeExplorer.selected.id}}''')
    if result['count']!=24 or result['created']!=24:errors.append(f"Count mismatch {result}")
    if result['layers']<48:errors.append('Missing paper/content layers')
    if sorted(result['styles'])!=sorted(['clean-editorial','handmade-scrapbook','technical-notebook']):errors.append('Style switching failed')
    if sorted(result['alignments'])!=['center','left','right']:errors.append('Alignment switching failed')
    if min(result['durations'])<=0:errors.append('Invalid animation duration')
    if not result['special'].get('typewriter'):errors.append('Typewriter semantic animation failed')
    if result['special'].get('stat') in (None,'0'):errors.append('Statistic count failed')
    if result['special'].get('list')!=3:errors.append('List rendering failed')
    if result['searchButtons']!=24:errors.append('Explorer navigation incomplete')
    if console:errors.extend(['Browser console: '+x for x in console])
    browser.close()
report={'status':'PASS' if not errors else 'FAIL','details':result,'errors':errors};(root/'reports/batch8-smoke.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
