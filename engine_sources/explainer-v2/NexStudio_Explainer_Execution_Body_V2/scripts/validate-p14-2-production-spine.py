#!/usr/bin/env python3
from __future__ import annotations
import argparse,base64,json,re,subprocess,sys
from pathlib import Path

def read(root,rel): return (root/rel).read_text('utf-8',errors='replace')
def add(c,n,ok,d=None): c.append({'name':n,'pass':bool(ok),'detail':d})
def run(cmd,**kw): return subprocess.run(cmd,capture_output=True,text=True,timeout=kw.pop('timeout',30),**kw)

def character_smoke(root:Path):
 p=root/'runtime-assets/explainer-motion-v1/library/nexstick-v5.1/render-character-sequence.cjs'
 payload={'familyId':'adult_woman_average','personality':'warm','roleTags':['helper'],'action':'present','frameCount':4,'palette':{'ink':'#20282B','paper':'#FFFDF8','accent':'#E58A4A','green':'#748A76'}}
 r=run(['node',str(p)],input=json.dumps(payload),timeout=30)
 try:o=json.loads(r.stdout)
 except Exception:return False,(r.stdout+r.stderr)[-600:]
 frames=o.get('frames') or []
 try: svg=base64.b64decode(frames[0]['dataUrl'].split(',',1)[1]).decode('utf-8','replace') if frames else ''
 except Exception: svg=''
 return o.get('ok') is True and len(frames)>=3 and '<svg' in svg, {'ok':o.get('ok'),'frames':len(frames),'version':o.get('version')}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('root',nargs='?',default=str(Path(__file__).resolve().parents[1]));args=ap.parse_args();root=Path(args.root).resolve();c=[]
 runner=read(root,'scripts/studio-p8-explainer-runner.ts'); prod=read(root,'src/studio/explainer-motion-v1/nexart/production-art.ts'); env=read(root,'src/studio/explainer-motion-v1/nexart/environment-constructor.ts'); obj=read(root,'src/studio/explainer-motion-v1/nexart/constructed-object.ts'); asset=read(root,'src/studio/explainer-motion-v1/nexart/asset-body.ts'); spec=read(root,'src/studio/explainer-motion-v1/nexart/specialist-artists.ts'); comp=read(root,'src/studio/explainer-motion-v1/compiler.ts'); typ=read(root,'src/studio/explainer-motion-v1/types.ts'); motion=read(root,'src/studio/explainer-motion-v1/motion-direction.ts'); grammar=read(root,'src/studio/explainer-motion-v1/execution-grammar.ts'); scene=read(root,'src/studio/explainer-motion-v1/nexart/scene-composer.ts'); style=read(root,'src/studio/explainer-motion-v1/nexart/style-grammar.ts'); vc=read(root,'runtime-assets/explainer-motion-v1/library/components/visual-constructions.js')
 add(c,'P8 execution runner present','StudioP8ExplainerExecutionRequestV1' in runner)
 add(c,'P8 is sole creative authority','runNexMindExplainerDirectors' not in runner and 'production-director' not in runner)
 add(c,'rejected P14.2 Director folder absent',not (root/'src/studio/explainer-motion-v1/nexmind').exists())
 add(c,'no old Director invocation scripts',not any(root.glob('scripts/run-nexmind*')))
 add(c,'execution grammar is neutral','executionMotionVersions' in grammar and 'Director' not in grammar)
 add(c,'motion execution uses neutral grammar','./execution-grammar' in motion and './nexmind/' not in motion)
 add(c,'specialist body is deterministic execution planning','dispatchSpecialistArtists' in spec)
 add(c,'specialist body contains no embedded model council','callNexMind' not in spec and 'runNexArtSpecialistCouncil' not in spec)
 add(c,'production-art systems include execution-fidelity check','EXECUTION_FIDELITY_CHECK' in typ and 'EXECUTION_FIDELITY_REQUIRED' in prod and 'VISUAL_CRITIC_REQUIRED' not in prod)
 add(c,'premium character missing is explicit blocker','PREMIUM_CHARACTER_MASTER_UNAVAILABLE' in prod)
 add(c,'weak character body cannot masquerade as premium','nexstudio-rive-premium-v1' in prod and 'UNAVAILABLE' in prod)
 add(c,'environment never infers a semantic world archetype','SEMANTIC_SCENE_GRAPH_WORLD' not in env and 'office' not in env.lower() and 'home' not in env.lower())
 add(c,'environment accepts only explicit authored world or white field','EXPLICIT_AUTHORED_WORLD' in env and 'INTENTIONAL_WHITE_FIELD' in env and 'UNAVAILABLE' in env)
 add(c,'missing environment fails/replans instead of generic fallback','PRODUCTION_SCOPED_AUTHORED_ENVIRONMENT_REQUIRED' in env)
 add(c,'environment binding is P8/asset execution-only','no-house-archetype' in env and 'APPROVED_ASSET' in env)
 add(c,'environment has no premium-context invention heuristic','PREMIUM_ENVIRONMENT_CONTEXT_INSUFFICIENT' not in env)
 add(c,'constructed-object compatibility symbol is fail-closed','constructedObjectBinding' in obj and 'return undefined' in obj)
 add(c,'constructed object has no canned common-prop catalogue',not any(x in obj.lower() for x in ['phone','package','payment','cup','bottle','computer']))
 add(c,'unknown object is not generic-symbol substituted','return undefined' in obj)
 add(c,'asset body uses authored assets and never constructed fallback','scoreAuthoredAsset' in asset and 'constructedObjectBinding' not in asset)
 add(c,'inline SVG body supported by type contract','inlineSvg' in typ)
 add(c,'compiler consumes inline SVG bodies','inlineSvg' in comp and 'sourceSha256' in comp and 'outputSha256' in comp)
 add(c,'style grammar has single normalized art family','nexstudio-authored-cartoon-v1' in style)
 add(c,'scene composer enforces occupancy','SCENE_COMPOSER_LOW_FOREGROUND_OCCUPANCY' in scene)
 add(c,'scene composer enforces rich density','SCENE_COMPOSER_RICH_DENSITY_REQUIRES_5_ELEMENTS' in scene)
 add(c,'scene composer enforces environment depth','SCENE_COMPOSER_ENVIRONMENT_REQUIRES_3_DEPTH_LAYERS' in scene)
 add(c,'runtime rejects presentation substitution','PRESENTATION_PRIMITIVE_IN_AUTHORED_SCENE' in vc)
 add(c,'runtime forbids raw rig exposure','RAW_RIG_EXPOSURE_FORBIDDEN' in vc)
 add(c,'runtime enforces style family','STYLE_GRAMMAR_RUNTIME_MISMATCH' in vc)
 add(c,'family body has execution-fidelity-only gate','StudioFamilyExecutionFidelityV1' in runner and 'commercialScore:null' in runner and 'reviewExplainerCompositionFrames' not in runner)
 add(c,'private critic source absent',not (root/'src/lib/studio-critic.ts').exists() and not (root/'src/studio/explainer-motion-v1/nexart/visual-critic.ts').exists())
 add(c,'private critic capability router absent',not (root/'src/lib/execution-capability-model.ts').exists())
 add(c,'execution body contains no private model router',not (root/'src/lib/execution-capability-model.ts').exists())
 add(c,'model routing belongs outside family body','NEXMIND_MODEL_REGISTRY_JSON' not in runner)
 add(c,'no family-private critic role override','NEXMIND_EXPLAINER_VISUAL_CRITIC' not in runner and not (root/'src/lib/execution-capability-model.ts').exists())
 add(c,'P8 motion requires explicit executable binding','P8_MOTION_EXECUTION_BINDING_REQUIRED' in runner)
 add(c,'no generic visual verb fallback','return "Reveal"' not in runner)
 add(c,'reference-language analysis retained','analyzeReferenceLanguage' in runner)
 add(c,'production art requires execution fidelity','EXECUTION_FIDELITY_REQUIRED' in prod and 'VISUAL_CRITIC_REQUIRED' not in prod)
 add(c,'production art never allows raw rig','rawRigVisibleAllowed:false' in prod.replace(' ',''))
 ok,d=character_smoke(root);add(c,'embedded performer body executes mechanically',ok,d)
 # syntax checks for all TS execution source
 ts=list((root/'src').rglob('*.ts'))+[root/'scripts/studio-p8-explainer-runner.ts']
 js="const ts=require('typescript'),fs=require('fs');let bad=[];for(const p of process.argv.slice(1)){const r=ts.transpileModule(fs.readFileSync(p,'utf8'),{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext},reportDiagnostics:true,fileName:p});for(const d of r.diagnostics||[])if(d.category===ts.DiagnosticCategory.Error)bad.push(p+':'+ts.flattenDiagnosticMessageText(d.messageText,' '));}if(bad.length){console.error(bad.join('\\n'));process.exit(1)}"
 tr=run(['node','-e',js,*map(str,ts)],timeout=40);add(c,'all execution TypeScript parses',tr.returncode==0,tr.stderr[-700:] if tr.stderr else {'files':len(ts)})
 # reachable source is free of named model identities and rejected director refs
 text='\n'.join(p.read_text(errors='ignore') for p in ts)
 add(c,'execution source has no named model identities',not re.search(r'(?i)gpt-\d|deepseek|claude|gemini|luna|\bsol\b',text))
 add(c,'execution source has no rejected Director imports','explainer-motion-v1/nexmind' not in text and 'runNexMindStoryDirector' not in text and 'runNexMindVisualDirector' not in text)
 # nontrivial runtime corpus
 svg=list((root/'runtime-assets/explainer-motion-v1/library/nexart-assets').rglob('*.svg'));add(c,'authored vector corpus retained',len(svg)>=80,len(svg))
 add(c,'NexStick execution support retained',(root/'runtime-assets/explainer-motion-v1/library/nexstick-v5.1/render-character-sequence.cjs').exists())
 passed=sum(x['pass'] for x in c);report={'schemaVersion':'explainer-execution-body-v2-qa','status':'PASS' if passed==len(c) else 'FAIL','passed':passed,'total':len(c),'checks':c,'truthBoundary':{'executionBodyIntegrated':passed==len(c),'commercial95Proven':False,'liveBlindFilmProven':False}}
 out=root/'EXECUTION_BODY_QA.json';out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'passed':passed,'total':len(c),'out':str(out)},indent=2))
 if passed!=len(c):
  [print('FAIL',x['name'],x['detail'],file=sys.stderr) for x in c if not x['pass']];sys.exit(1)
if __name__=='__main__':main()
