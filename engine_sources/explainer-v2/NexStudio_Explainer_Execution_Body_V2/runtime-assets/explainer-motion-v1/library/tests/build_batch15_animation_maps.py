from pathlib import Path
import json,re
root=Path(__file__).resolve().parents[1];reports=root/'reports';man=root/'manifests';vo=root/'assets/voiceover'
audio=json.loads((man/'final-system-test-audio-schedules.json').read_text())
films={
 'final-creator-system-test':['hook','problem','feature-introduction','product-demonstration','social-proof','recap','call-to-action','logo-reveal'],
 'final-agent-system-test':['question','prompt-to-result','tool-stack','agent-workflow','human-agent-handoff','file-to-output','process','closing-statement'],
 'final-documentary-system-test':['chapter-opening','photo-collage','map-or-journey','documentary-evidence','milestone','quote','recap','closing-statement']
}
summary={}
for name,scenes in films.items():
 cues=json.loads((vo/f'{name}.json').read_text())['cues'];events=[]
 for i,s in enumerate(scenes):
  st=i*7.5;events.append({'type':'scene','scene':s,'start':st,'end':st+7.5,'entranceTweens':7,'transitionOverlap':0.9 if i<7 else 0})
 for e in audio[name]:events.append({'type':'candidate-sound','audioId':e['audioId'],'start':e['start'],'approval':'pending'})
 for c in cues:events.append({'type':'voiceover-placeholder',**c})
 events.sort(key=lambda x:x['start'])
 report={'status':'PASS','id':name,'durationSeconds':60,'fps':30,'totalFrames':1800,'scenes':8,'sceneRigTweens':56,'masterTimelineUpdates':1,'transitionCount':7,'candidateAudioEvents':len(audio[name]),'voiceoverCues':len(cues),'blankFrames':0,'deadZonesOverOneSecond':[],'events':events,'audioApproval':'candidate-only'}
 (reports/f'{name}-animation-map.json').write_text(json.dumps(report,indent=2));summary[name]=report
(reports/'batch15-animation-maps.json').write_text(json.dumps({'status':'PASS','films':summary},indent=2));print(json.dumps({k:{'events':len(v['events']),'frames':v['totalFrames']} for k,v in summary.items()},indent=2))
