from pathlib import Path
import json, re, os, glob, collections, hashlib, textwrap, shutil
root=Path(__file__).resolve().parents[1]
manifests=root/'manifests'; runtime=root/'runtime'; reports=root/'reports'; tests=root/'tests'; assets=root/'assets'
items=json.loads((manifests/'index.json').read_text())

category_batch={
 'foundation':1,'paper-object':2,'motion':3,'icon':None,'typography':8,'media-container':9,
 'data-visualisation':10,'workflow-diagram':10,'creator-module':11,'documentary-module':12,
 'scene-family':13,'audio':14
}

def batch_for(x):
 c=x.get('category')
 if c!='icon': return category_batch.get(c)
 i=x['id']
 if '.universal.' in i:return 4
 if '.creator.' in i:return 5
 if '.agent.' in i:return 6
 if '.business.' in i:return 7
 return None

source_by_category={
 'foundation':'components/foundation-components.js','paper-object':'components/paper-objects.js','motion':'runtime/motion-engine.js',
 'typography':'components/typography.js','media-container':'components/media-containers.js','data-visualisation':'components/data-visualisations.js',
 'workflow-diagram':'components/data-visualisations.js','creator-module':'components/creator-modules.js',
 'documentary-module':'components/documentary-modules.js','scene-family':'components/scene-rigs.js','audio':None
}
registry_by_category={
 'foundation':'runtime/foundation-registry.js','paper-object':'runtime/object-registry.js','motion':'runtime/motion-registry.js',
 'typography':'runtime/typography-registry.js','media-container':'runtime/media-container-registry.js',
 'data-visualisation':'runtime/data-visualisation-registry.js','workflow-diagram':'runtime/data-visualisation-registry.js',
 'creator-module':'runtime/creator-module-registry.js','documentary-module':'runtime/documentary-module-registry.js',
 'scene-family':'runtime/scene-rig-registry.js','audio':'runtime/audio-registry.js'
}
icon_source={'universal':'components/universal-icons.js','creator':'components/creator-icons.js','agent':'components/agent-icons.js','business':'components/business-icons.js'}
icon_registry={'universal':'runtime/icon-registry.js','creator':'runtime/creator-icon-registry.js','agent':'runtime/agent-icon-registry.js','business':'runtime/business-icon-registry.js'}

def icon_group(x):
 i=x['id']
 for g in icon_source:
  if f'.{g}.' in i:return g
 return 'universal'

# Manifest paths
manifest_paths={}
for p in manifests.rglob('*.json'):
 if p.parent==manifests: continue
 try:d=json.loads(p.read_text())
 except:continue
 if isinstance(d,dict) and d.get('id'):manifest_paths[d['id']]=str(p.relative_to(root))

# Preview paths: scan exact IDs and slugs
preview_paths={}
for p in (root/'previews').rglob('*.html'):
 txt=p.read_text(errors='ignore')
 for x in items:
  if x['id'] in txt: preview_paths.setdefault(x['id'],str(p.relative_to(root)))
# filename/slug fallback
all_previews=list((root/'previews').rglob('*.html'))
for x in items:
 if x['id'] in preview_paths:continue
 slug=x.get('slug') or x['id'].split('.')[-2 if x['id'].endswith('.paper-01') else -1]
 matches=[p for p in all_previews if p.stem==slug or p.stem.endswith('-'+slug)]
 if matches:preview_paths[x['id']]=str(matches[0].relative_to(root))
# shared preview fallback
for x in items:
 if x['id'] in preview_paths:continue
 if x['category']=='foundation':preview_paths[x['id']]='foundation-explorer.html'
 elif x['category']=='motion':preview_paths[x['id']]='motion-explorer.html'
 elif x['category']=='audio' and x.get('slug'):preview_paths[x['id']]=f"previews/audio/{x['slug']}.html"

# Enrich registry
use_case_map={
 'creator':['creator','publish','content','social','audience','channel','campaign','media','video','podcast','newsletter'],
 'agent':['agent','workflow','automation','prompt','tool','model','api','data','approval','handoff','validation'],
 'documentary':['documentary','archive','evidence','history','memory','timeline','map','source','citation','investigation']
}

def infer_use_cases(x):
 text=' '.join([x.get('name',''),x.get('category',''),x.get('subtype','')]+x.get('intents',[])+x.get('keywords',[])).lower()
 out=[k for k,words in use_case_map.items() if any(w in text for w in words)]
 if not out:
  if x['category'] in ['creator-module'] or (x['category']=='icon' and '.creator.' in x['id']):out=['creator']
  elif x['category'] in ['documentary-module']:out=['documentary']
  elif x['category'] in ['workflow-diagram'] or (x['category']=='icon' and '.agent.' in x['id']):out=['agent']
  else:out=['general']
 return out

enriched=[]
for x0 in items:
 x=dict(x0); c=x['category']; batch=batch_for(x)
 if c=='icon':
  g=icon_group(x); source=icon_source[g]; reg=icon_registry[g]
 else:source=source_by_category.get(c);reg=registry_by_category.get(c)
 if c=='audio':source=x.get('productionFile')
 p=preview_paths.get(x['id'])
 record={**x,
  'batch':batch,'useCases':infer_use_cases(x),'manifestPath':manifest_paths.get(x['id']),
  'sourcePath':source,'registryPath':reg,'previewPath':p,
  'availability':{
   'manifest':bool(manifest_paths.get(x['id'])),'source':bool(source and (root/source).exists()),
   'preview':bool(p and (root/p).exists()),'reusable':True,
   'editoriallyApproved': bool(c!='audio' or x.get('editorialApproval')=='approved')
  }
 }
 enriched.append(record)

# Sound tag map to candidate audio
sounds=[x for x in enriched if x['category']=='audio']
all_tags=sorted(set(t for x in enriched for t in x.get('soundTags',[])))
def sound_score(tag,a):
 score=0; tagparts=set(re.split(r'[.\-_ ]+',tag.lower()));
 vals=' '.join(a.get('semanticTags',[])+a.get('recommendedVisualActions',[])+[a.get('name',''),a.get('subtype','')]).lower()
 parts=set(re.split(r'[.\-_ ]+',vals)); score+=len(tagparts&parts)*10
 if tag.startswith('paper') and a.get('subtype')=='paper-foley':score+=10
 if tag.startswith('ui') and a.get('subtype')=='interface':score+=10
 if ('transition' in tag or 'motion' in tag) and a.get('subtype')=='motion-transition':score+=10
 if 'logo' in tag and 'logo' in vals:score+=25
 if 'error' in tag and 'impact' in vals:score+=5
 return score
sound_tag_map={}
for tag in all_tags:
 ranked=sorted(((sound_score(tag,a),a) for a in sounds),key=lambda z:(-z[0],z[1]['id']))
 best=ranked[0][1] if ranked else None
 sound_tag_map[tag]={
  'tag':tag,'candidateAudioId':best['id'] if best else None,'score':ranked[0][0] if ranked else 0,
  'approvedAudioId': next((a['id'] for _,a in ranked if a.get('editorialApproval')=='approved'),None),
  'status':'candidate-mapped' if best else 'unmapped'
 }

facets={
 'categories':collections.Counter(x['category'] for x in enriched),
 'batches':collections.Counter(str(x['batch']) for x in enriched),
 'paperStyles':collections.Counter(s for x in enriched for s in x.get('paperStyles',[])),
 'aspectRatios':collections.Counter(s for x in enriched for s in x.get('aspectRatios',[])),
 'motionEnergy':collections.Counter(s for x in enriched for s in x.get('motionEnergy',[])),
 'useCases':collections.Counter(s for x in enriched for s in x.get('useCases',[])),
 'soundTags':len(all_tags)
}
facets={k:dict(v) if hasattr(v,'items') else v for k,v in facets.items()}
master={
 'release':'3.0.0-rc1','generatedAt':'2026-08-05T17:48:00+01:00','status':'RELEASE_CANDIDATE_AUDIO_APPROVAL_BLOCKED',
 'totalEntries':len(enriched),'entries':enriched,'facets':facets,
 'audioApproval':{'approved':sum(1 for x in sounds if x.get('editorialApproval')=='approved'),'candidate':len(sounds),'requireApprovedDefault':True}
}
(manifests/'master-agent-registry.json').write_text(json.dumps(master,indent=2))
(manifests/'master-filter-facets.json').write_text(json.dumps(facets,indent=2))
(manifests/'master-sound-tag-map.json').write_text(json.dumps(sound_tag_map,indent=2))
(runtime/'master-registry.js').write_text('window.NEX_MASTER_REGISTRY='+json.dumps(master,separators=(',',':'))+';\nwindow.NEX_MASTER_SOUND_TAG_MAP='+json.dumps(sound_tag_map,separators=(',',':'))+';')

# Selection API UMD
api_js=r'''(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;root.NexAgentSelector=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
 const state={registry:null,soundMap:null};
 function init(registry,soundMap){state.registry=registry||globalThis.NEX_MASTER_REGISTRY;state.soundMap=soundMap||globalThis.NEX_MASTER_SOUND_TAG_MAP||{};return api}
 const arr=v=>Array.isArray(v)?v:(v==null?[]:[v]);
 const text=v=>String(v||'').toLowerCase();
 function match(entry,request){let score=0,reasons=[];const q=[request.intent,...arr(request.keywords),request.useCase].filter(Boolean).map(text);const hay=[entry.name,entry.category,entry.subtype,...arr(entry.intents),...arr(entry.keywords),...arr(entry.useCases)].map(text);
  q.forEach(term=>{if(arr(entry.intents).map(text).includes(term)){score+=55;reasons.push('exact intent')}else if(hay.some(h=>h.includes(term)||term.includes(h))){score+=18;reasons.push('semantic keyword')}});
  if(request.componentType&&entry.category===request.componentType){score+=22;reasons.push('component type')}
  if(request.aspectRatio&&arr(entry.aspectRatios).includes(request.aspectRatio)){score+=12;reasons.push('aspect ratio')}
  if(request.paperStyle&&arr(entry.paperStyles).includes(request.paperStyle)){score+=10;reasons.push('paper style')}
  if(request.motionEnergy&&arr(entry.motionEnergy).includes(request.motionEnergy)){score+=8;reasons.push('motion energy')}
  const d=entry.duration||{};if(request.duration!=null&&Number(request.duration)>=Number(d.minimum||0)&&Number(request.duration)<=Number(d.maximum||1e9)){score+=12;reasons.push('duration')}
  if(request.useCase&&arr(entry.useCases).includes(request.useCase)){score+=15;reasons.push('use case')}
  const content=request.content||{},slots=entry.slots||{};if(content.steps&&slots.steps||content.steps&&slots.items){score+=8;reasons.push('step slots')};if(content.media&&JSON.stringify(slots).includes('media')){score+=6;reasons.push('media slot')};if(content.data&&JSON.stringify(slots).includes('data')){score+=6;reasons.push('data slot')};
  return {score,reasons:[...new Set(reasons)]}; }
 function resolveSoundTags(tags,requireApproved){const approved=[],candidates=[],missing=[];arr(tags).forEach(tag=>{const m=state.soundMap[tag];if(!m||!m.candidateAudioId)missing.push(tag);else if(m.approvedAudioId)approved.push(m.approvedAudioId);else candidates.push(m.candidateAudioId)});return{approved:[...new Set(approved)],candidates:[...new Set(candidates)],missing,blocked:!!requireApproved&&approved.length===0&&candidates.length>0}}
 function select(request={}){if(!state.registry)init();const entries=state.registry.entries||state.registry;const requireApproved=request.requireApprovedAudio!==false;let ranked=entries.filter(e=>e.category!=='audio').map(e=>({entry:e,...match(e,request)})).filter(x=>x.score>0).sort((a,b)=>b.score-a.score||a.entry.name.localeCompare(b.entry.name));
  const scenes=ranked.filter(x=>x.entry.category==='scene-family').slice(0,5),components=ranked.filter(x=>x.entry.category!=='scene-family').slice(0,12);const primary=scenes[0]?.entry||components[0]?.entry||null;const sound=resolveSoundTags(primary?.soundTags||[],requireApproved);
  return{request,release:state.registry.release,status:primary?'matched':'no-match',primaryRecommendation:primary,sceneRecommendations:scenes.map(x=>({id:x.entry.id,name:x.entry.name,score:x.score,reasons:x.reasons,requiredSlots:x.entry.slots,compatibleMotions:x.entry.compatibleMotions||[],compatibleTransitions:x.entry.compatibleTransitions||[],soundTags:x.entry.soundTags||[]})),componentRecommendations:components.map(x=>({id:x.entry.id,name:x.entry.name,category:x.entry.category,score:x.score,reasons:x.reasons,requiredSlots:x.entry.slots,compatibleMotions:x.entry.compatibleMotions||[]})),brand:request.brand||{},audio:{requireApproved,approved:sound.approved,candidateSuggestions:sound.candidates,missingTags:sound.missing,status:sound.blocked?'blocked-no-approved-audio':sound.approved.length?'approved':'candidate-only'},warnings:sound.blocked?['Candidate sounds exist, but none are editorially approved. Production audio remains disabled.']:[]}; }
 function search(filters={}){if(!state.registry)init();const query=text(filters.query),cats=arr(filters.categories||filters.category),styles=arr(filters.paperStyles||filters.paperStyle),ratios=arr(filters.aspectRatios||filters.aspectRatio),energies=arr(filters.motionEnergy),uses=arr(filters.useCases||filters.useCase);return state.registry.entries.filter(e=>{const hay=text([e.id,e.name,e.category,e.subtype,...arr(e.intents),...arr(e.keywords)].join(' '));if(query&&!hay.includes(query))return false;if(cats.length&&!cats.includes(e.category))return false;if(styles.length&&!styles.some(x=>arr(e.paperStyles).includes(x)))return false;if(ratios.length&&!ratios.some(x=>arr(e.aspectRatios).includes(x)))return false;if(energies.length&&!energies.some(x=>arr(e.motionEnergy).includes(x)))return false;if(uses.length&&!uses.some(x=>arr(e.useCases).includes(x)))return false;if(filters.maxDuration!=null&&Number(e.duration?.minimum||0)>Number(filters.maxDuration))return false;return true})}
 const api={init,select,search,resolveSoundTags};return api;
});'''
(runtime/'agent-selection-api.js').write_text(api_js)

examples=[
 {'name':'Agent workflow','request':{'intent':'explain_agent_workflow','duration':8,'aspectRatio':'16:9','paperStyle':'technical-notebook','motionEnergy':'medium','useCase':'agent','brand':{'primary':'#6D45D8','secondary':'#FFB648','accent':'#FF5A36'},'content':{'title':'From prompt to finished video','steps':['Understand','Plan','Create','Validate']},'requireApprovedAudio':True}},
 {'name':'Creator launch','request':{'intent':'launch_product','duration':7,'aspectRatio':'1:1','paperStyle':'bold-paper-collage','motionEnergy':'high','useCase':'creator','content':{'title':'Launch the next episode','media':'replaceable'},'requireApprovedAudio':True}},
 {'name':'Documentary evidence','request':{'intent':'show_evidence','duration':9,'aspectRatio':'9:16','paperStyle':'handmade-scrapbook','motionEnergy':'low','useCase':'documentary','content':{'title':'The record remains','media':'archive.jpg'},'requireApprovedAudio':True}}
]
(manifests/'agent-selection-examples.json').write_text(json.dumps(examples,indent=2))

# VO timing placeholders
vo_dir=assets/'voiceover';vo_dir.mkdir(exist_ok=True)
voiceovers={
 'final-creator-system-test':[
  (0,7.1,'Your next idea deserves more than another blank timeline.'),(7.5,14.5,'The bottleneck is rebuilding the production logic every single time.'),(15,22,'NexStudio selects reusable scenes while your media, copy and data stay replaceable.'),(22.5,29.5,'One library can adapt the same story across every important format.'),(30,37,'The creator keeps the direction, the brand and the final approval.'),(37.5,44.5,'The system handles composition, motion and validation.'),(45,52,'Reusable does not have to look repeated.'),(52.5,59.2,'Start with a brief. Finish with a moving paper world.')],
 'final-agent-system-test':[
  (0,7.1,'How does an agent choose a scene without guessing a template?'),(7.5,14.5,'Intent becomes structure through machine-readable slots and limits.'),(15,22,'The agent selects only approved component families and compatible motion.'),(22.5,29.5,'Tools, evidence and data remain modular throughout the workflow.'),(30,37,'Human approval remains a required decision point.'),(37.5,44.5,'One configuration can produce landscape, square and portrait outputs.'),(45,52,'Every scene is inspected before it reaches the renderer.'),(52.5,59.2,'The agent does not guess a template. It selects a storytelling structure.')],
 'final-documentary-system-test':[
  (0,7.1,'The first page was small: a room, a handwritten plan and one deadline.'),(7.5,14.5,'The people arrived before the system, and photographs became memory.'),(15,22,'Every place added another piece to the journey.'),(22.5,29.5,'Documents and citations kept the emotional story anchored to evidence.'),(30,37,'Then the library became a visual language.'),(37.5,44.5,'We stopped rebuilding and started telling.'),(45,52,'What survived was the evidence, the people and the reason the work mattered.'),(52.5,59.2,'Every archive is waiting for motion.')]
}
for name,cues in voiceovers.items():
 data={'id':name,'type':'voiceover-timing-placeholder','durationSeconds':60,'language':'en','audioFile':None,'status':'timing-only','cues':[{'start':a,'end':b,'text':t} for a,b,t in cues]}
 (vo_dir/f'{name}.json').write_text(json.dumps(data,indent=2))
 # vtt
 def ts(s):
  h=int(s//3600);m=int((s%3600)//60);sec=s%60;return f'{h:02d}:{m:02d}:{sec:06.3f}'.replace('.',',')
 (vo_dir/f'{name}.vtt').write_text('WEBVTT\n\n'+'\n\n'.join(f'{i+1}\n{ts(a)} --> {ts(b)}\n{t}' for i,(a,b,t) in enumerate(cues))+'\n')

# Provisional audio schedules for final videos
schedule={
 'final-creator-system-test':[(0.10,'audio.paper-swipe-clean',.33),(7.30,'audio.soft-impact-modern',.22),(15.05,'audio.camera-shutter-clean',.20),(22.35,'audio.marker-swipe-bold',.20),(29.85,'audio.fast-transition-whoosh',.18),(37.35,'audio.text-pop-in',.18),(44.85,'audio.paper-swipe-legacy',.20),(52.3,'audio.final-logo-sting',.30)],
 'final-agent-system-test':[(0.10,'audio.text-pop-in',.22),(7.30,'audio.typewriter-line-return',.18),(15.05,'audio.staple-click-precise',.22),(22.35,'audio.fast-transition-whoosh',.18),(29.85,'audio.rubber-stamp-impact',.24),(37.35,'audio.paper-swipe-clean',.18),(44.85,'audio.soft-impact-modern',.20),(52.3,'audio.final-logo-sting',.28)],
 'final-documentary-system-test':[(0.10,'audio.page-turn-soft',.28),(7.30,'audio.camera-shutter-clean',.18),(15.05,'audio.map-unfold-wide',.18),(22.35,'audio.typewriter-line-return',.16),(29.85,'audio.newspaper-rustle',.18),(37.35,'audio.marker-swipe-bold',.15),(44.85,'audio.archive-drawer-slide',.16),(52.3,'audio.final-logo-sting',.25)]
}
(manifests/'final-system-test-audio-schedules.json').write_text(json.dumps({k:[{'start':a,'audioId':b,'volume':v,'approval':'candidate'} for a,b,v in vals] for k,vals in schedule.items()},indent=2))

print(json.dumps({'entries':len(enriched),'previewMapped':sum(1 for x in enriched if x['availability']['preview']),'sourceMapped':sum(1 for x in enriched if x['availability']['source']),'manifestMapped':sum(1 for x in enriched if x['availability']['manifest']),'soundTags':len(all_tags),'approvedAudio':master['audioApproval']['approved']},indent=2))
