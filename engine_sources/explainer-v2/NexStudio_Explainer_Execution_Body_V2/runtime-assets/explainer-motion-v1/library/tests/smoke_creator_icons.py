from pathlib import Path
from playwright.sync_api import sync_playwright
from batch5_browser_utils import bundled_creator_explorer,bundled_creator_scene
import json
root=Path(__file__).resolve().parents[1];errors=[];results={}
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
    page=b.new_page(viewport={'width':1720,'height':1100})
    page.on('pageerror',lambda e:errors.append('page: '+str(e)))
    page.on('console',lambda m:errors.append('console: '+m.text) if m.type=='error' else None)
    page.set_content(bundled_creator_explorer(root),wait_until='load')
    counts={'all':page.locator('.icon-card').count()}
    for key in ['bespoke','media','production','publishing','analytics']:
        page.locator(f'[data-filter="{key}"]').click();counts[key]=page.locator('.icon-card').count()
    page.locator('[data-filter="all"]').click()
    structure=page.evaluate('''()=>[...document.querySelectorAll('.icon-card')].map(card=>{const icon=card.querySelector('.nex-icon'),svg=icon.querySelector('svg'),def=NexCreatorIcons.getDef(icon.dataset.iconId);return {id:card.dataset.iconId,layers:['icon-shadow-layer','icon-paper-layer','icon-symbol-layer','icon-accent-layer','icon-state-layer'].map(c=>svg.querySelector('.'+c)?.children.length||0),aria:icon.getAttribute('aria-label'),motions:def.compatibleMotions.length,timeline:!!icon.__tl,duration:icon.__tl?.duration()||0,bespoke:def.bespokeInternalMotion}})''')
    motion=page.evaluate('''()=>[...document.querySelectorAll('.nex-icon')].map(icon=>{const tl=icon.__tl;function snap(){return JSON.stringify([icon,...icon.querySelectorAll('*')].slice(0,90).map(n=>{const c=getComputedStyle(n);return [n.tagName,n.className,c.transform,c.opacity,c.strokeDashoffset,n.textContent]}))}const states=[0,.18,.4,.68,1].map(v=>{tl.seek(tl.duration()*v);return snap()});return {id:icon.dataset.iconId,distinct:new Set(states).size,duration:tl.duration()}})''')
    page.select_option('#creatorStyle','technical-notebook');style=page.evaluate('document.documentElement.dataset.paperStyle')
    page.select_option('#creatorPalette','cobalt');primary=page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--primary').trim()")
    page.fill('#creatorPrimary','#2233aa');custom=page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--primary').trim()")
    page.select_option('#creatorTreatment','printed-outline');treatment=page.evaluate("()=>[...document.querySelectorAll('.nex-icon')].every(x=>x.dataset.treatment==='printed-outline')")
    page.select_option('#creatorSize','42');sizes=page.evaluate("()=>[...document.querySelectorAll('.nex-icon')].map(x=>Math.round(x.getBoundingClientRect().width))")
    page.select_option('#creatorState','completed');state=page.evaluate("()=>[...document.querySelectorAll('.nex-icon')].map(x=>({id:x.dataset.iconId,state:x.dataset.state,supported:NexCreatorIcons.getDef(x.dataset.iconId).states.includes('completed')}))")
    page.select_option('#creatorEnergy','high');energy=page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--motion-scale').trim()")
    page.fill('#creatorSearch','publish');search_count=page.locator('.icon-card').count();page.fill('#creatorSearch','')
    api=page.evaluate('''()=>{const mount=document.createElement('div');document.body.appendChild(mount);let icon=NexCreatorIcons.create('camera',{size:80,state:'active'});mount.appendChild(icon);const before=icon.dataset.state;NexCreatorIcons.setState(icon,'completed');const fallback=icon.dataset.state;NexCreatorIcons.setSize(icon,140);NexCreatorIcons.setTreatment(icon,'printed-outline');const after=[Math.round(icon.getBoundingClientRect().width),icon.dataset.treatment];icon=NexCreatorIcons.update(icon,{size:64,state:'active'});const tl=NexCreatorIcons.animate(icon,{duration:1.2,energy:'medium'});tl.seek(tl.duration()*.5);return {before,fallback,after,updated:Math.round(icon.getBoundingClientRect().width),timeline:tl.duration()>0,apis:['create','animate','setState','setTreatment','setSize','update','getDef'].every(k=>typeof NexCreatorIcons[k]==='function')}}''')
    page.screenshot(path=str(root/'reports/creator-icon-explorer.png'),full_page=False)
    results['explorer']={'counts':counts,'structure':structure,'motion':motion,'style':style,'primary':primary,'customPrimary':custom,'treatment':treatment,'sizes':sizes,'state':state,'energyScale':energy,'searchCount':search_count,'api':api}
    page.close()
    scene_results=[]
    for name,viewport in [('creator-workflow',{'width':1920,'height':1080}),('media-production',{'width':1080,'height':1080}),('publishing',{'width':1080,'height':1920})]:
        page=b.new_page(viewport=viewport);page.on('pageerror',lambda e,n=name:errors.append(n+': '+str(e)));page.on('console',lambda m,n=name:errors.append(n+' console: '+m.text) if m.type=='error' else None);page.set_content(bundled_creator_scene(root,name),wait_until='load')
        info=page.evaluate('''name=>{const tl=window.__timelines[name],nodes=[...document.querySelectorAll('.creator-node')];const snaps=[.2,1.4,3.5,6.7,9.7].map(t=>{tl.seek(t);return JSON.stringify(nodes.map(n=>{const i=n.querySelector('.nex-icon'),c=getComputedStyle(i);return [c.transform,c.opacity,n.querySelector('.creator-node-label').textContent]}))});return {registered:!!tl,duration:tl.duration(),nodes:nodes.length,icons:nodes.map(n=>n.querySelector('.nex-icon')?.dataset.iconId),distinct:new Set(snaps).size}}''',name)
        page.evaluate('(name)=>window.__timelines[name].seek(6.5)',name);page.screenshot(path=str(root/f'reports/{name}.png'));scene_results.append({'name':name,**info});page.close()
    results['scenes']=scene_results;b.close()
expected_counts={'all':48,'bespoke':18,'media':5,'production':4,'publishing':11,'analytics':3}
structure_ok=all(all(v>0 for v in x['layers']) and x['aria'] and x['motions']>=3 and x['timeline'] and x['duration']>0 for x in results['explorer']['structure'])
motion_ok=all(x['distinct']>=3 for x in results['explorer']['motion'])
state_ok=all((x['state']=='completed') if x['supported'] else (x['state']=='active') for x in results['explorer']['state'])
scenes_ok=all(x['registered'] and abs(x['duration']-10.2)<.01 and x['nodes']==7 and len(x['icons'])==7 and x['distinct']>=4 for x in scene_results)
status=not errors and results['explorer']['counts']==expected_counts and structure_ok and motion_ok and results['explorer']['style']=='technical-notebook' and results['explorer']['primary'].lower()=='#1456d8' and results['explorer']['customPrimary'].lower()=='#2233aa' and results['explorer']['treatment'] and all(x==42 for x in results['explorer']['sizes']) and state_ok and results['explorer']['energyScale']=='1.25' and results['explorer']['searchCount']>=1 and results['explorer']['api']['apis'] and scenes_ok
report={'status':'PASS' if status else 'FAIL','errors':errors,'expectedCounts':expected_counts,'structureOk':structure_ok,'motionOk':motion_ok,'stateOk':state_ok,'scenesOk':scenes_ok,'results':results}
(root/'reports/batch5-smoke.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2));raise SystemExit(0 if status else 1)
