from pathlib import Path
from playwright.sync_api import sync_playwright
from batch4_browser_utils import bundled_icon_explorer
import json
root=Path(__file__).resolve().parents[1];html=bundled_icon_explorer(root);page_errors=[]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium');page=b.new_page(viewport={'width':1720,'height':1100})
    page.on('pageerror',lambda e:page_errors.append(str(e)));page.on('console',lambda m:page_errors.append('console: '+m.text) if m.type=='error' else None)
    page.set_content(html,wait_until='load')
    counts={'all':page.locator('.icon-card').count()}
    for key in ['bespoke','stateful','navigation']:
        page.locator(f'[data-filter="{key}"]').click();counts[key]=page.locator('.icon-card').count()
    page.locator('[data-filter="all"]').click()
    structure=page.evaluate('''()=>[...document.querySelectorAll('.icon-card')].map(card=>{const icon=card.querySelector('.nex-icon'),svg=icon.querySelector('svg');return {id:card.dataset.iconId,layers:['icon-shadow-layer','icon-paper-layer','icon-symbol-layer','icon-accent-layer','icon-state-layer'].map(c=>svg.querySelector('.'+c)?.children.length||0),aria:icon.getAttribute('aria-label'),motions:NexIcons.getDef(icon.dataset.iconId).compatibleMotions.length,timeline:!!icon.__tl,duration:icon.__tl?.duration()||0}})''')
    animation=page.evaluate('''()=>[...document.querySelectorAll('.nex-icon')].map(icon=>{const tl=icon.__tl;function snap(){return JSON.stringify([icon,...icon.querySelectorAll('*')].slice(0,80).map(n=>{const c=getComputedStyle(n);return [n.tagName,n.className,c.transform,c.opacity,c.strokeDashoffset,c.fill,c.stroke]}))}const states=[0,.2,.45,.7,1].map(p=>{tl.seek(tl.duration()*p);return snap()});return {id:icon.dataset.iconId,states:new Set(states).size,duration:tl.duration()}})''')
    # Theme, treatment, scale and state controls.
    page.select_option('#iconStyle','technical-notebook');style=page.evaluate('document.documentElement.dataset.paperStyle')
    page.select_option('#iconPalette','cobalt');primary=page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--primary').trim()")
    page.select_option('#iconTreatment','printed-outline');treatments=page.evaluate("()=>[...document.querySelectorAll('.nex-icon')].every(x=>x.dataset.treatment==='printed-outline')")
    page.select_option('#iconSize','42');sizes=page.evaluate("()=>[...document.querySelectorAll('.nex-icon')].map(x=>Math.round(x.getBoundingClientRect().width))")
    page.select_option('#iconState','completed');state_result=page.evaluate('''()=>[...document.querySelectorAll('.nex-icon')].map(x=>({id:x.dataset.iconId,state:x.dataset.state,supported:NexIcons.getDef(x.dataset.iconId).states.includes('completed')}))''')
    # Search and manifest interaction.
    page.fill('#iconSearch','bookmark');search_count=page.locator('.icon-card').count();page.fill('#iconSearch','')
    page.locator('.icon-card [data-action="manifest"]').first.click();manifest_open=page.locator('#iconManifest.open').count()==1;manifest_text=page.locator('#iconManifest pre').text_content() or ''
    page.locator('#closeIconManifest').click()
    # Direct API test.
    api=page.evaluate('''()=>{const host=document.createElement('div');document.body.appendChild(host);const icon=NexIcons.create('save',{size:64,treatment:'paper-cutout',state:'inactive'});host.appendChild(icon);NexIcons.setState(icon,'completed');NexIcons.setTreatment(icon,'printed-outline');NexIcons.setSize(icon,180);const tl=NexIcons.animate(icon,{motion:'paper-slide',duration:.8,energy:'high'});tl.seek(tl.duration());return {state:icon.dataset.state,treatment:icon.dataset.treatment,width:Math.round(icon.getBoundingClientRect().width),timeline:tl.duration(),layers:icon.querySelectorAll('svg>g').length}}''')
    page.screenshot(path=str(root/'reports/icon-explorer.png'),full_page=True)
    b.close()
structure_fail=[x for x in structure if any(n<1 for n in x['layers']) or not x['aria'] or x['motions']<3 or not x['timeline'] or x['duration']<=0]
animation_fail=[x for x in animation if x['states']<2]
state_fail=[x for x in state_result if (x['supported'] and x['state']!='completed') or (not x['supported'] and x['state']=='completed')]
status=(not page_errors and counts=={'all':40,'bespoke':15,'stateful':19,'navigation':8} and not structure_fail and not animation_fail and style=='technical-notebook' and primary.lower()=='#1456d8' and treatments and set(sizes)=={42} and not state_fail and search_count==1 and manifest_open and 'icon.universal.' in manifest_text and api['state']=='completed' and api['treatment']=='printed-outline' and api['width']==180 and api['timeline']>0 and api['layers']>=5)
report={'status':'PASS' if status else 'FAIL','pageErrors':page_errors,'filterCounts':counts,'iconsInspected':len(structure),'structureFailures':structure_fail,'animationFailures':animation_fail,'styleSwitch':style,'palettePrimary':primary,'treatmentSwitch':treatments,'sizeValues':sorted(set(sizes)),'stateFailures':state_fail,'searchCount':search_count,'manifestPanel':manifest_open,'directApi':api}
(root/'reports/batch4-smoke.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));raise SystemExit(0 if status else 1)
