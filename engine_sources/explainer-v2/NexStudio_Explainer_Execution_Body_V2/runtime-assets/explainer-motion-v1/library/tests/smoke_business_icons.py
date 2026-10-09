from pathlib import Path
from playwright.sync_api import sync_playwright
from batch7_browser_utils import bundled_business_explorer,bundled_business_scene
import json,sys
root=Path(__file__).resolve().parents[1];errors=[];results={}
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
    page=b.new_page(viewport={'width':1720,'height':1100})
    page.on('pageerror',lambda e:errors.append('page: '+str(e)))
    page.on('console',lambda m:errors.append('console: '+m.text) if m.type=='error' else None)
    page.set_content(bundled_business_explorer(root),wait_until='load')
    counts={'all':page.locator('.icon-card').count()}
    for key in ['bespoke','metrics','commerce','marketing','organization']:
        page.locator(f'[data-filter="{key}"]').click();counts[key]=page.locator('.icon-card').count()
    page.locator('[data-filter="all"]').click()
    structure=page.evaluate('''()=>[...document.querySelectorAll('.icon-card')].map(card=>{const icon=card.querySelector('.nex-icon'),svg=icon.querySelector('svg'),def=NexBusinessIcons.getDef(icon.dataset.iconId);return {id:card.dataset.iconId,layers:['icon-shadow-layer','icon-paper-layer','icon-symbol-layer','icon-accent-layer','icon-state-layer'].map(c=>svg.querySelector('.'+c)?.children.length||0),aria:icon.getAttribute('aria-label'),motions:def.compatibleMotions.length,timeline:!!icon.__tl,duration:icon.__tl?.duration()||0,bespoke:def.bespokeInternalMotion}})''')
    motion=page.evaluate('''()=>[...document.querySelectorAll('.nex-icon')].map(icon=>{const tl=icon.__tl;function snap(){return JSON.stringify([icon,...icon.querySelectorAll('*')].slice(0,120).map(n=>{const c=getComputedStyle(n);return [n.tagName,n.className,c.transform,c.opacity,c.strokeDashoffset,n.textContent]}))}const states=[0,.14,.31,.52,.76,1].map(v=>{tl.seek(tl.duration()*v);return snap()});return {id:icon.dataset.iconId,distinct:new Set(states).size,duration:tl.duration(),bespoke:NexBusinessIcons.getDef(icon.dataset.iconId).bespokeInternalMotion}})''')
    page.select_option('#businessStyle','handmade-scrapbook');style=page.evaluate('document.documentElement.dataset.paperStyle')
    page.select_option('#businessPalette','charcoal');primary=page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--primary').trim()")
    page.fill('#businessPrimary','#2233aa');custom=page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--primary').trim()")
    page.select_option('#businessTreatment','printed-outline');treatment=page.evaluate("()=>[...document.querySelectorAll('.nex-icon')].every(x=>x.dataset.treatment==='printed-outline')")
    page.select_option('#businessSize','42');sizes=page.evaluate("()=>[...document.querySelectorAll('.nex-icon')].map(x=>Math.round(x.getBoundingClientRect().width))")
    page.select_option('#businessState','completed');state=page.evaluate("()=>[...document.querySelectorAll('.nex-icon')].map(x=>({id:x.dataset.iconId,state:x.dataset.state,supported:NexBusinessIcons.getDef(x.dataset.iconId).states.includes('completed')}))")
    page.select_option('#businessEnergy','high');energy=page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--motion-scale').trim()")
    page.fill('#businessSearch','campaign');search_count=page.locator('.icon-card').count();page.fill('#businessSearch','')
    api=page.evaluate('''()=>{const mount=document.createElement('div');document.body.appendChild(mount);let icon=NexBusinessIcons.create('campaign',{size:80,state:'active'});mount.appendChild(icon);const before=icon.dataset.state;NexBusinessIcons.setState(icon,'completed');const completed=icon.dataset.state;NexBusinessIcons.setSize(icon,140);NexBusinessIcons.setTreatment(icon,'printed-outline');const after=[Math.round(icon.getBoundingClientRect().width),icon.dataset.treatment];icon=NexBusinessIcons.update(icon,{size:64,state:'active'});const tl=NexBusinessIcons.animate(icon,{duration:1.2,energy:'medium'});tl.seek(tl.duration()*.5);return {before,completed,after,updated:Math.round(icon.getBoundingClientRect().width),timeline:tl.duration()>0,apis:['create','animate','setState','setTreatment','setSize','update','getDef'].every(k=>typeof NexBusinessIcons[k]==='function')}}''')
    results['explorer']={'counts':counts,'structureCount':len(structure),'badLayers':[x['id'] for x in structure if min(x['layers'])<1],'missingAria':[x['id'] for x in structure if not x['aria']],'shortMotion':[x['id'] for x in structure if x['motions']<3 or not x['timeline'] or x['duration']<=0],'motionDistinctMinimum':min(x['distinct'] for x in motion),'bespokeLowDistinct':[x['id'] for x in motion if x['bespoke'] and x['distinct']<3],'style':style,'primaryAfterPalette':primary,'customPrimary':custom,'treatment':treatment,'sizeRange':[min(sizes),max(sizes)],'completedFallbackValid':all((x['state']=='completed') if x['supported'] else (x['state']=='active') for x in state),'energy':energy,'searchCount':search_count,'api':api}
    expected={'all':36,'bespoke':24,'metrics':10,'commerce':11,'marketing':8,'organization':7}
    if counts!=expected:errors.append(f'Filter counts wrong: {counts}')
    if results['explorer']['badLayers']:errors.append('Missing populated layers')
    if results['explorer']['missingAria']:errors.append('Missing aria labels')
    if results['explorer']['shortMotion']:errors.append('Motion metadata/runtime failures')
    if results['explorer']['bespokeLowDistinct']:errors.append('Bespoke motion lacks distinct states')
    if not treatment or min(sizes)!=42 or max(sizes)!=42:errors.append('Explorer treatment/size controls failed')
    if search_count<1 or not api['apis'] or not api['timeline']:errors.append('Search/API failure')
    for name in ['commerce-workflow','campaign-result','milestone-scene']:
        pg=b.new_page(viewport={'width':1920 if name=='commerce-workflow' else 1080,'height':1080 if name!='milestone-scene' else 1920})
        local=[];pg.on('pageerror',lambda e,local=local:local.append(str(e)));pg.on('console',lambda m,local=local:local.append(m.text) if m.type=='error' else None)
        pg.set_content(bundled_business_scene(root,name),wait_until='load')
        data=pg.evaluate('''()=>{const id=document.querySelector('.business-scene').id,tl=window.__timelines[id];const snaps=[0,.6,2.3,5.7,8.9,10.75].map(t=>{seekComposition(t);return {t,visible:[...document.querySelectorAll('.business-node')].filter(n=>{const r=n.getBoundingClientRect(),s=getComputedStyle(n);return r.width>0&&r.height>0&&s.opacity!=='0'}).length,active:[...document.querySelectorAll('.nex-icon')].filter(n=>getComputedStyle(n).opacity!=='0'&&getComputedStyle(n).transform!=='none').length}});return {id,duration:tl.duration(),nodeCount:document.querySelectorAll('.business-node').length,iconCount:document.querySelectorAll('.nex-business-icon').length,snaps}}''')
        results[name]={'errors':local,**data}
        if local or data['duration']!=10.8 or data['nodeCount']!=8 or data['iconCount']!=8:errors.append(f'{name} scene failure')
        pg.close()
    b.close()
report={'status':'PASS' if not errors else 'FAIL','results':results,'errors':errors}
(root/'reports/batch7-smoke.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
