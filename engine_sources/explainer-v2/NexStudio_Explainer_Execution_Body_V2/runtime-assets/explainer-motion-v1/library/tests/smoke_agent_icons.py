from pathlib import Path
from playwright.sync_api import sync_playwright
from batch6_browser_utils import bundled_agent_explorer,bundled_agent_scene
import json
root=Path(__file__).resolve().parents[1];errors=[];results={}
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
    page=b.new_page(viewport={'width':1720,'height':1100})
    page.on('pageerror',lambda e:errors.append('page: '+str(e)))
    page.on('console',lambda m:errors.append('console: '+m.text) if m.type=='error' else None)
    page.set_content(bundled_agent_explorer(root),wait_until='load')
    counts={'all':page.locator('.icon-card').count()}
    for key in ['bespoke','ai-core','resources','automation','trust','output']:
        page.locator(f'[data-filter="{key}"]').click();counts[key]=page.locator('.icon-card').count()
    page.locator('[data-filter="all"]').click()
    structure=page.evaluate('''()=>[...document.querySelectorAll('.icon-card')].map(card=>{const icon=card.querySelector('.nex-icon'),svg=icon.querySelector('svg'),def=NexAgentIcons.getDef(icon.dataset.iconId);return {id:card.dataset.iconId,layers:['icon-shadow-layer','icon-paper-layer','icon-symbol-layer','icon-accent-layer','icon-state-layer'].map(c=>svg.querySelector('.'+c)?.children.length||0),aria:icon.getAttribute('aria-label'),motions:def.compatibleMotions.length,timeline:!!icon.__tl,duration:icon.__tl?.duration()||0,bespoke:def.bespokeInternalMotion}})''')
    motion=page.evaluate('''()=>[...document.querySelectorAll('.nex-icon')].map(icon=>{const tl=icon.__tl;function snap(){return JSON.stringify([icon,...icon.querySelectorAll('*')].slice(0,100).map(n=>{const c=getComputedStyle(n);return [n.tagName,n.className,c.transform,c.opacity,c.strokeDashoffset,n.textContent]}))}const states=[0,.16,.35,.58,.82,1].map(v=>{tl.seek(tl.duration()*v);return snap()});return {id:icon.dataset.iconId,distinct:new Set(states).size,duration:tl.duration()}})''')
    page.select_option('#agentStyle','handmade-scrapbook');style=page.evaluate('document.documentElement.dataset.paperStyle')
    page.select_option('#agentPalette','charcoal');primary=page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--primary').trim()")
    page.fill('#agentPrimary','#2233aa');custom=page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--primary').trim()")
    page.select_option('#agentTreatment','printed-outline');treatment=page.evaluate("()=>[...document.querySelectorAll('.nex-icon')].every(x=>x.dataset.treatment==='printed-outline')")
    page.select_option('#agentSize','42');sizes=page.evaluate("()=>[...document.querySelectorAll('.nex-icon')].map(x=>Math.round(x.getBoundingClientRect().width))")
    page.select_option('#agentState','completed');state=page.evaluate("()=>[...document.querySelectorAll('.nex-icon')].map(x=>({id:x.dataset.iconId,state:x.dataset.state,supported:NexAgentIcons.getDef(x.dataset.iconId).states.includes('completed')}))")
    page.select_option('#agentEnergy','high');energy=page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--motion-scale').trim()")
    page.fill('#agentSearch','handoff');search_count=page.locator('.icon-card').count();page.fill('#agentSearch','')
    api=page.evaluate('''()=>{const mount=document.createElement('div');document.body.appendChild(mount);let icon=NexAgentIcons.create('agent-handoff',{size:80,state:'active'});mount.appendChild(icon);const before=icon.dataset.state;NexAgentIcons.setState(icon,'completed');const fallback=icon.dataset.state;NexAgentIcons.setSize(icon,140);NexAgentIcons.setTreatment(icon,'printed-outline');const after=[Math.round(icon.getBoundingClientRect().width),icon.dataset.treatment];icon=NexAgentIcons.update(icon,{size:64,state:'active'});const tl=NexAgentIcons.animate(icon,{duration:1.2,energy:'medium'});tl.seek(tl.duration()*.5);return {before,fallback,after,updated:Math.round(icon.getBoundingClientRect().width),timeline:tl.duration()>0,apis:['create','animate','setState','setTreatment','setSize','update','getDef'].every(k=>typeof NexAgentIcons[k]==='function')}}''')
    page.screenshot(path=str(root/'reports/agent-icon-explorer.png'),full_page=False)
    results['explorer']={'counts':counts,'structure':structure,'motion':motion,'style':style,'primary':primary,'customPrimary':custom,'treatment':treatment,'sizes':sizes,'state':state,'energyScale':energy,'searchCount':search_count,'api':api}
    page.close()
    scene_results=[]
    for name,viewport in [('multi-agent-orchestration',{'width':1920,'height':1080}),('human-agent-approval',{'width':1080,'height':1080}),('prompt-to-output',{'width':1080,'height':1920})]:
        page=b.new_page(viewport=viewport);page.on('pageerror',lambda e,n=name:errors.append(n+': '+str(e)));page.on('console',lambda m,n=name:errors.append(n+' console: '+m.text) if m.type=='error' else None);page.set_content(bundled_agent_scene(root,name),wait_until='load')
        info=page.evaluate('''name=>{const tl=window.__timelines[name],nodes=[...document.querySelectorAll('.agent-node')];const snaps=[.2,1.4,3.6,6.8,10.2].map(t=>{tl.seek(t);return JSON.stringify(nodes.map(n=>{const i=n.querySelector('.nex-icon'),c=getComputedStyle(i);return [c.transform,c.opacity,n.querySelector('.agent-node-label').textContent]}))});return {registered:!!tl,duration:tl.duration(),nodes:nodes.length,icons:nodes.map(n=>n.querySelector('.nex-icon')?.dataset.iconId),distinct:new Set(snaps).size}}''',name)
        page.evaluate('(name)=>window.__timelines[name].seek(6.7)',name);page.screenshot(path=str(root/f'reports/{name}.png'));scene_results.append({'name':name,**info});page.close()
    results['scenes']=scene_results;b.close()
expected_counts={'all':48,'bespoke':30,'ai-core':11,'resources':11,'automation':14,'trust':6,'output':6}
structure_ok=all(all(v>0 for v in x['layers']) and x['aria'] and x['motions']>=3 and x['timeline'] and x['duration']>0 for x in results['explorer']['structure'])
motion_ok=all(x['distinct']>=3 for x in results['explorer']['motion'])
state_ok=all((x['state']=='completed') if x['supported'] else (x['state']=='active') for x in results['explorer']['state'])
scenes_ok=all(x['registered'] and abs(x['duration']-10.8)<.01 and x['nodes']==8 and len(x['icons'])==8 and x['distinct']>=4 for x in scene_results)
status=not errors and results['explorer']['counts']==expected_counts and structure_ok and motion_ok and results['explorer']['style']=='handmade-scrapbook' and results['explorer']['primary'].lower()=='#c92323' and results['explorer']['customPrimary'].lower()=='#2233aa' and results['explorer']['treatment'] and all(x==42 for x in results['explorer']['sizes']) and state_ok and results['explorer']['energyScale']=='1.25' and results['explorer']['searchCount']>=1 and results['explorer']['api']['apis'] and scenes_ok
report={'status':'PASS' if status else 'FAIL','errors':errors,'expectedCounts':expected_counts,'structureOk':structure_ok,'motionOk':motion_ok,'stateOk':state_ok,'scenesOk':scenes_ok,'results':results}
(root/'reports/batch6-smoke.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2));raise SystemExit(0 if status else 1)
