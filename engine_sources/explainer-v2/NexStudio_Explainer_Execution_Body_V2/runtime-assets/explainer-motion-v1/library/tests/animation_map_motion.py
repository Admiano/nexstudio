from pathlib import Path
from playwright.sync_api import sync_playwright
from batch3_browser_utils import bundled_motion_explorer,bundled_transition_demo
import json
root=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium');page=b.new_page(viewport={'width':1920,'height':1080});page.set_content(bundled_motion_explorer(root),wait_until='load')
 data=page.evaluate('''()=>[...document.querySelectorAll('.motion-card')].map(card=>{const el=[...card.querySelector('.motion-target-cell').children].find(x=>x.__tl),tl=el.__tl;const base=(tl.base?.tweens||[]).map(t=>({start:t.start,end:t.start+t.duration*(1+(t.repeat||0)),duration:t.duration,target:t.el.className||t.el.tagName,ease:t.ease}));const custom=(tl.custom||[]).map(t=>({start:t.start,end:t.start+t.duration,duration:t.duration,ease:t.easing,custom:true}));const intervals=[...base,...custom].sort((a,b)=>a.start-b.start);let cursor=0,dead=[];for(const x of intervals){if(x.start-cursor>.35)dead.push({from:cursor,to:x.start,duration:x.start-cursor});cursor=Math.max(cursor,x.end)}if(tl.duration()-cursor>.35)dead.push({from:cursor,to:tl.duration(),duration:tl.duration()-cursor});return {id:card.dataset.motionId,duration:tl.duration(),baseTweenCount:base.length,customUpdaterCount:custom.length,deadZones:dead,intervals}})''')
 page.set_content(bundled_transition_demo(root),wait_until='load')
 transition=page.evaluate('''()=>{const starts=[2.15,5.2,8.25,11.3,14.35,17.4,20.45],out=[];for(let i=0;i<starts.length;i++){window.seekComposition(starts[i]+.001);const scenes=[...document.querySelectorAll('.transition-scene')];out.push({index:i,time:starts[i],outgoingOpacity:Number(getComputedStyle(scenes[i]).opacity),incomingOpacity:Number(getComputedStyle(scenes[i+1]).opacity)})}let blank=[];for(let t=0;t<=23.6;t+=.2){window.seekComposition(t);const v=[...document.querySelectorAll('.transition-scene')].filter(x=>Number(getComputedStyle(x).opacity)>.02).length;if(!v)blank.push(t)}return {starts:out,blankFrames:blank}}''')
 b.close()
fail=[x for x in data if x['deadZones'] or (x['baseTweenCount']+x['customUpdaterCount']==0)]
preserve=[x for x in transition['starts'] if x['outgoingOpacity']<.95]
status=len(data)==32 and not fail and not transition['blankFrames'] and not preserve
report={'status':'PASS' if status else 'FAIL','motionCount':len(data),'totalBaseTweens':sum(x['baseTweenCount'] for x in data),'totalCustomUpdaters':sum(x['customUpdaterCount'] for x in data),'motionsWithDeadZones':[x['id'] for x in fail],'transitionPreservationFailures':preserve,'blankFrameCount':len(transition['blankFrames']),'motions':data,'transitionChoreography':transition}
(root/'reports/batch3-animation-map.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['motions','transitionChoreography']},indent=2));raise SystemExit(0 if status else 1)
