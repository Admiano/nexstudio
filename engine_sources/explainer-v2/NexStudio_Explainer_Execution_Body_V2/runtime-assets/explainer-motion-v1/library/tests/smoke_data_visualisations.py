from pathlib import Path
from playwright.sync_api import sync_playwright
from batch10_browser_utils import component_harness,bundle_editor,bundle_scene
import json
root=Path(__file__).resolve().parents[1];errors=[];details=[]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium')
 page=browser.new_page(viewport={'width':1300,'height':850});logs=[];page.on('console',lambda m: logs.append(m.text) if m.type=='error' else None);page.on('pageerror',lambda e: logs.append(str(e)))
 page.set_content(component_harness(root),wait_until='load')
 result=page.evaluate('''async()=>{const out=[];for(const d of NEX_DATA_VISUALISATIONS){stage.innerHTML='';const el=NexDataVisualisations.create(d.id,d.sampleConfig);stage.append(el);const tl=NexDataVisualisations.animate(el,{duration:2});tl.seek(0);const at0={numbers:[...el.querySelectorAll('.dv-number')].map(x=>x.textContent),nodes:[...el.querySelectorAll('.wf-node')].map(x=>getComputedStyle(x).opacity),shell:getComputedStyle(el.querySelector('.dv-shell')).opacity};tl.seek(tl.duration());const atEnd={numbers:[...el.querySelectorAll('.dv-number')].map(x=>x.textContent),nodes:[...el.querySelectorAll('.wf-node')].map(x=>getComputedStyle(x).opacity),shell:getComputedStyle(el.querySelector('.dv-shell')).opacity};out.push({id:d.id,category:d.category,layers:!!el.querySelector('.dv-shell')&&!!el.querySelector('.dv-content'),at0,atEnd,aria:el.getAttribute('aria-label')});}return out}''')
 for r in result:
  if not r['layers']:errors.append(r['id']+': shell missing')
  if not r['aria']:errors.append(r['id']+': aria missing')
  if r['atEnd']['shell']=='0':errors.append(r['id']+': shell not animated in')
  if r['category']=='workflow-diagram' and r['atEnd']['nodes'] and any(float(x)<.9 for x in r['atEnd']['nodes']):errors.append(r['id']+': workflow nodes not visible at end')
  if r['category']=='data-visualisation' and r['atEnd']['numbers'] and r['at0']['numbers']==r['atEnd']['numbers']:errors.append(r['id']+': values did not animate from zero')
 details=result
 # state variants, signs, formats, variable counts and update
 state=page.evaluate('''()=>{const d=NEX_DATA_VISUALISATIONS.find(x=>x.category==='data-visualisation');let a={};for(const s of ['empty','loading','unavailable']){stage.innerHTML='';let el=NexDataVisualisations.create(d.id,{...d.sampleConfig,state:s});stage.append(el);a[s]=!!el.querySelector('.dv-state')}let f={};for(const format of ['number','compact','currency','percent'])f[format]=NexDataVisualisations.format(-12500,{format,currency:'USD'});let el=NexDataVisualisations.create('data.bar-chart.paper-01',{title:'Variable',items:[{label:'A',value:-4},{label:'B',value:0},{label:'C',value:7}]});stage.innerHTML='';stage.append(el);let before=el.querySelectorAll('.dv-bar').length;el=NexDataVisualisations.setData(el,{title:'Updated',items:[{label:'One',value:2},{label:'Two',value:5},{label:'Three',value:9},{label:'Four',value:4}]});stage.innerHTML='';stage.append(el);return {states:a,formats:f,before,after:el.querySelectorAll('.dv-bar').length}}''')
 if not all(state['states'].values()):errors.append('State variants failed')
 if state['before']!=3 or state['after']!=4:errors.append('Variable item/update failed')
 # editors
 for workflow in [False,True]:
  ep=browser.new_page(viewport={'width':1450,'height':900});elog=[];ep.on('pageerror',lambda e:elog.append(str(e)));ep.set_content(bundle_editor(root,workflow),wait_until='load');ep.wait_for_timeout(500)
  count=ep.locator('#component option').count();expected=24 if workflow else 30
  if count!=expected:errors.append(f'Editor {workflow}: expected {expected}, got {count}')
  if ep.locator('.nex-dv').count()!=1:errors.append(f'Editor {workflow}: preview missing')
  ep.fill('#json','{"title":"Live edit","items":[{"label":"A","value":12},{"label":"B","value":-4}]}') if not workflow else ep.fill('#json','{"title":"Live workflow","nodes":[{"id":"a","label":"Input"},{"id":"b","label":"Output"}],"edges":[{"from":"a","to":"b"}]}')
  ep.click('#apply');ep.wait_for_timeout(100)
  if ep.locator('#error').inner_text().strip():errors.append(f'Editor {workflow}: JSON apply error')
  errors.extend('editor console '+x for x in elog);ep.close()
 # scenes
 for name in ['data-story','agent-workflow','conversion-story']:
  sp=browser.new_page(viewport={'width':1000,'height':1000});ser=[];sp.on('pageerror',lambda e:ser.append(str(e)));sp.set_content(bundle_scene(root,name),wait_until='load');sp.wait_for_timeout(150);count=sp.locator('.scene-card').count();sp.evaluate('seekComposition(13.8)')
  if count<3:errors.append(name+': insufficient scene cards')
  if sp.locator('.nex-dv').count()!=count:errors.append(name+': components missing')
  errors.extend(name+' console '+x for x in ser);sp.close()
 errors.extend('console '+x for x in logs);browser.close()
report={'status':'PASS' if not errors else 'FAIL','componentChecks':len(details),'dataComponents':sum(x['category']=='data-visualisation' for x in details),'workflowComponents':sum(x['category']=='workflow-diagram' for x in details),'stateVariants':['empty','loading','unavailable'],'formats':['number','compact','currency','percent'],'editors':2,'scenes':3,'errors':errors}
(root/'reports/batch10-smoke.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));raise SystemExit(1 if errors else 0)
