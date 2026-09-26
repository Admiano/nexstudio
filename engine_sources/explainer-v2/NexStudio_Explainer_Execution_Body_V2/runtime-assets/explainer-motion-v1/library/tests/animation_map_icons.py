from pathlib import Path
from playwright.sync_api import sync_playwright
from batch4_browser_utils import bundled_icon_explorer,bundled_icon_dock
import json
root=Path(__file__).resolve().parents[1]

def intervals_from_timeline_data(data):
    intervals=[]
    for entry in data:
        off=entry.get('offset',0)
        for t in entry.get('base',[]): intervals.append({'start':off+t['start'],'end':off+t['end'],'kind':'tween','target':t.get('target'),'ease':t.get('ease')})
        for t in entry.get('custom',[]): intervals.append({'start':off+t['start'],'end':off+t['end'],'kind':'updater','ease':t.get('ease')})
    return sorted(intervals,key=lambda x:x['start'])

def dead_zones(intervals,duration,threshold=.36):
    cursor=0;dead=[]
    for x in intervals:
        if x['start']-cursor>threshold:dead.append({'from':cursor,'to':x['start'],'duration':x['start']-cursor})
        cursor=max(cursor,x['end'])
    if duration-cursor>threshold:dead.append({'from':cursor,'to':duration,'duration':duration-cursor})
    return dead

with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium');page=b.new_page(viewport={'width':1720,'height':1100});page.set_content(bundled_icon_explorer(root),wait_until='load')
    raw=page.evaluate('''()=>[...document.querySelectorAll('.nex-icon')].map(icon=>{const tl=icon.__tl;return {id:icon.dataset.iconId,slug:icon.dataset.slug,duration:tl.duration(),bespoke:NexIcons.getDef(icon.dataset.iconId).bespokeInternalMotion,entries:tl.entries.map(e=>({offset:e.offset||0,base:(e.timeline.base?.tweens||[]).map(t=>({start:t.start,end:t.start+t.duration*(1+(t.repeat||0)),duration:t.duration,target:t.el.className||t.el.tagName,ease:t.ease})),custom:(e.timeline.custom||[]).map(t=>({start:t.start,end:t.start+t.duration,duration:t.duration,ease:t.easing}))}))}})''')
    # Semantic part snapshots for bespoke motions.
    semantic=page.evaluate('''()=>[...document.querySelectorAll('.nex-icon')].filter(x=>NexIcons.getDef(x.dataset.iconId).bespokeInternalMotion).map(icon=>{const tl=icon.__tl,parts=[...icon.querySelectorAll('[class*="part-"]')];const perPart=parts.map(part=>{const snaps=[.08,.42,.78,1].map(p=>{tl.seek(tl.duration()*p);const c=getComputedStyle(part);return JSON.stringify([c.transform,c.opacity,c.strokeDashoffset,c.fill,c.stroke,part.getAttribute('d')])});return {part:part.getAttribute('class'),states:new Set(snaps).size}});const changed=perPart.filter(x=>x.states>=2);return {id:icon.dataset.iconId,parts:perPart.length,changedParts:changed.length,examples:changed.slice(0,3)}})''')
    page.close()
    page=b.new_page(viewport={'width':1920,'height':1080});page.set_content(bundled_icon_dock(root),wait_until='load')
    dock=page.evaluate('''()=>{const tl=window.__timelines['icon-dock-demo'];let blank=[],selection=[];for(let t=0;t<=19.4;t+=.2){tl.seek(t);const visible=[...document.querySelectorAll('.dock-large-item')].filter(x=>Number(getComputedStyle(x).opacity)>.5);if(!document.querySelector('.dock-workspace')||Number(getComputedStyle(document.querySelector('.icon-dock-canvas')).opacity)<.02)blank.push(t);selection.push({time:t,visible:visible.length,active:[...document.querySelectorAll('.dock-slot.active')].map(x=>x.dataset.slug)})}const base=(tl.base?.tweens||[]).map(t=>({start:t.start,end:t.start+t.duration*(1+(t.repeat||0)),duration:t.duration,target:t.el.className||t.el.tagName,ease:t.ease}));const custom=(tl.custom||[]).map(t=>({start:t.start,end:t.start+t.duration,duration:t.duration,ease:t.easing}));return {duration:tl.duration(),base,custom,blank,selectionFailures:selection.filter(x=>x.visible!==1||x.active.length!==1)}}''')
    b.close()
icons=[]
for item in raw:
    intervals=intervals_from_timeline_data(item['entries']);dead=dead_zones(intervals,item['duration']);icons.append({**{k:item[k] for k in ['id','slug','duration','bespoke']},'baseTweenCount':sum(len(e['base']) for e in item['entries']),'customUpdaterCount':sum(len(e['custom']) for e in item['entries']),'deadZones':dead,'intervals':intervals})
dock_intervals=sorted([{'start':x['start'],'end':x['end'],'kind':'tween'} for x in dock['base']]+[{'start':x['start'],'end':x['end'],'kind':'updater'} for x in dock['custom']],key=lambda x:x['start'])
dock_dead=dead_zones(dock_intervals,dock['duration'])
fail=[x for x in icons if x['deadZones'] or x['baseTweenCount']+x['customUpdaterCount']==0]
semantic_fail=[x for x in semantic if x['changedParts']<1]
status=len(icons)==40 and not fail and len(semantic)==15 and not semantic_fail and not dock['blank'] and not dock['selectionFailures'] and not dock_dead
report={'status':'PASS' if status else 'FAIL','iconCount':len(icons),'bespokeSemanticTests':len(semantic),'totalBaseTweens':sum(x['baseTweenCount'] for x in icons),'totalCustomUpdaters':sum(x['customUpdaterCount'] for x in icons),'iconsWithDeadZones':[x['id'] for x in fail],'semanticFailures':semantic_fail,'dockDuration':dock['duration'],'dockBaseTweens':len(dock['base']),'dockCustomUpdaters':len(dock['custom']),'dockDeadZones':dock_dead,'dockBlankFrames':dock['blank'],'dockSelectionFailures':dock['selectionFailures'],'icons':icons,'semanticTests':semantic,'dock':dock}
(root/'reports/batch4-animation-map.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['icons','semanticTests','dock']},indent=2));raise SystemExit(0 if status else 1)
