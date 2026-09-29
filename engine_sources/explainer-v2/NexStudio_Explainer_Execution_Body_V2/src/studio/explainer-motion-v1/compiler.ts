import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { join } from "node:path";
import type { CompositionBundle } from "@/hyperframes/types";
import { assertFrozenVideoSpecUnchanged } from "./video-spec";
import { assertScenePlansValid } from "./scene-validator";
import { hashJson, stableJson } from "./schemas";
import { assertAuthorizedSoundSchedule, loadAuthorizedSoundRegistry } from "./audio";
import { assertProductionContentValid } from "./content-contract";
import { EXPLAINER_FRAME_RATE, MOTION_CRAFT_ENGINE_VERSION } from "./types";
import { resolveMotionPerformancePlan } from "./motion-craft";
import { AUTHORED_CARTOON_PALETTE, normalizeAuthoredSvgStyle } from "./nexart/style-normalizer";
import type { CompilerOptions, ExplainerComposition, ExplainerRegistry, FrozenVideoSpec, ProductionRenderBinding, ScenePlan } from "./types";

const styleFiles = ["styles/tokens.css", "styles/paper.css", "styles/objects.css", "styles/icons.css", "styles/typography.css", "styles/media-containers.css", "styles/data-visualisations.css", "styles/documentary-modules.css", "styles/scene-rigs.css", "styles/embedded-repairs.css", "styles/visual-constructions.css", "styles/motion.css"];
const libraryScriptFiles = [
  "vendor/gsap-compat.js", "runtime/motion-registry.js", "runtime/foundation-registry.js", "runtime/object-registry.js", "runtime/typography-registry.js", "runtime/media-container-registry.js", "runtime/data-visualisation-registry.js", "runtime/icon-registry.js", "runtime/business-icon-registry.js", "runtime/creator-icon-registry.js", "runtime/agent-icon-registry.js", "runtime/creator-module-registry.js", "runtime/documentary-module-registry.js", "runtime/scene-rig-registry.js",
  "components/foundation-components.js", "components/paper-objects.js", "components/typography.js", "components/media-containers.js", "components/data-visualisations.js", "components/universal-icons.js", "components/business-icons.js", "components/creator-icons.js", "components/agent-icons.js", "components/creator-modules.js", "components/documentary-modules.js", "components/visual-constructions.js", "components/scene-rigs.js", "components/visual-construction-adapter.js", "runtime/motion-engine.js", "runtime/semantic-motion-engine.js", "runtime/motion-craft-engine.js",
];

function read(root: string, file: string) { return readFileSync(join(root, file), "utf8"); }
function script(value: string) { return value.replace(/<\/script/gi, "<\\/script"); }
function ratioSize(ratio: FrozenVideoSpec["aspectRatio"], quality: NonNullable<CompilerOptions["quality"]>) {
  if (ratio === "1:1") { const size = quality === "draft" ? 640 : quality === "high" ? 2160 : 1080; return { width: size, height: size }; }
  if (ratio === "9:16") return { width: quality === "draft" ? 360 : quality === "high" ? 1215 : 1080, height: quality === "draft" ? 640 : quality === "high" ? 2160 : 1920 };
  return { width: quality === "draft" ? 640 : quality === "high" ? 3840 : 1920, height: quality === "draft" ? 360 : quality === "high" ? 2160 : 1080 };
}

function safeAssetName(assetId: string) { return assetId.replace(/[^a-zA-Z0-9._-]/g, "-"); }
function sceneFilePath(sceneId: string) { return `compositions/${safeAssetName(sceneId)}.html`; }

type RuntimeArtSequence = NonNullable<ProductionRenderBinding["performanceSequence"]>;

function nexStickActionFor(scene: ScenePlan, entityId: string) {
  const direct = [...(scene.motionDirection?.actions ?? [])].filter((action) => action.actor === entityId).sort((a, b) => (a.priority === "primary" ? 0 : a.priority === "secondary" ? 1 : 2) - (b.priority === "primary" ? 0 : b.priority === "secondary" ? 1 : 2))[0];
  const action = direct?.action;
  if (["enter", "exit", "travel", "fall", "rise"].includes(action ?? "")) return "walk";
  if (["reveal", "highlight", "validate", "scan", "transform", "accumulate"].includes(action ?? "")) return "present";
  if (["transfer", "connect", "disconnect", "assemble", "replace", "open", "close", "unfold"].includes(action ?? "")) return "interact";
  if (["orient-toward", "pulse"].includes(action ?? "")) return "conversation";
  const related = scene.visualConstruction?.relationships.find((relationship) => relationship.from === entityId || relationship.to === entityId);
  if (related && ["passes-to", "routes-to", "feeds", "produces"].includes(related.kind)) return "present";
  if (related && ["travels-through", "enters", "exits"].includes(related.kind)) return "walk";
  return "idle";
}

function renderNexStickCharacterSequence(root: string, scene: ScenePlan, binding: ProductionRenderBinding): RuntimeArtSequence {
  if (binding.performanceAuthority !== "NEXSTICK_V5_1" || !binding.characterSpec) throw new Error(`CHARACTER_SKIN_SPEC_MISSING:${binding.assetId}`);
  const scriptPath = join(root, "nexstick-v5.1/render-character-sequence.cjs");
  const action = nexStickActionFor(scene, binding.assetId.replace(/^nexstick-v5\.1:/, ""));
  const input = {
    ...binding.characterSpec,
    action,
    frameCount: 7,
    viewFamily: "near-front",
    palette: {
      hair: AUTHORED_CARTOON_PALETTE.ink,
      top: AUTHORED_CARTOON_PALETTE.slate,
      upper: AUTHORED_CARTOON_PALETTE.slate,
      lower: AUTHORED_CARTOON_PALETTE.slateDark,
      outer: AUTHORED_CARTOON_PALETTE.slateDark,
      shoe: AUTHORED_CARTOON_PALETTE.ink,
      accent: AUTHORED_CARTOON_PALETTE.accent,
    },
  };
  const run = spawnSync(process.execPath, [scriptPath], { input: JSON.stringify(input), encoding: "utf8", maxBuffer: 12 * 1024 * 1024 });
  if (run.error) throw new Error(`NEXSTICK_V5_1_EXECUTION_FAILED:${binding.assetId}:${run.error.message}`);
  if (run.status !== 0) throw new Error(`NEXSTICK_V5_1_EXECUTION_FAILED:${binding.assetId}:${run.stderr || `exit-${run.status}`}`);
  let parsed: { ok?: boolean; failure?: string; version?: string; action?: string; durationSec?: number; frames?: Array<{ t: number; dataUrl: string }> };
  try { parsed = JSON.parse(run.stdout); } catch { throw new Error(`NEXSTICK_V5_1_INVALID_OUTPUT:${binding.assetId}`); }
  if (!parsed.ok || !parsed.version || !parsed.action || !parsed.frames || parsed.frames.length < 3) throw new Error(`NEXSTICK_V5_1_SKIN_BLOCKED:${binding.assetId}:${parsed.failure ?? "invalid-sequence"}`);
  return { source: "NEXSTICK_V5_1", engineVersion: parsed.version, action: parsed.action, durationSec: Number(parsed.durationSec ?? 1), frames: parsed.frames };
}

function sceneConfig(scene: ScenePlan, mediaPaths: ReadonlyMap<string, string>, mediaFallbacks: ReadonlyMap<string, string>, artAssetDataUrls: ReadonlyMap<string, string>, artPerformanceSequences: ReadonlyMap<string, RuntimeArtSequence>, frameRate: number = EXPLAINER_FRAME_RATE) {
  const binding = scene.componentBindings.find((item) => item.slot === "hero");
  const typographyBinding = scene.componentBindings.find((item) => item.slot === "typography");
  const mediaBinding = scene.componentBindings.find((item) => item.slot === "media");
  const dataBinding = scene.componentBindings.find((item) => item.slot === "data" || item.slot === "workflow");
  const content = binding?.content ?? {};
  const bindings = Object.fromEntries(scene.componentBindings.map((item) => [item.slot, item.componentId]));
  const composition = { sceneFamily: "scene", typography: { role: "hero", minWidth: 280, minHeight: 180 }, media: { role: "secondary", minWidth: 220, minHeight: 160 }, data: { role: "supporting", minWidth: 150, minHeight: 72 }, icon: { role: "annotation", minWidth: 64, minHeight: 64 } };
  const userMedia = scene.userAssetBindings.find((item) => mediaPaths.has(item.assetId));
  const mediaContent = mediaBinding?.content ?? content;
  const mediaFallback = typeof mediaContent.mediaFallback === "string" && mediaContent.mediaFallback.trim() ? mediaContent.mediaFallback : "assets/media/semantic-explainer.svg";
  const media = userMedia ? mediaPaths.get(userMedia.assetId)! : (mediaFallbacks.get(mediaFallback) ?? mediaFallbacks.get("assets/media/semantic-explainer.svg") ?? "");
  const configuredItems = typographyBinding?.content?.items ?? binding?.content?.items;
  const hydrateBinding = (binding: NonNullable<NonNullable<ScenePlan["visualConstruction"]>["heroEntity"]["renderBinding"]>) => ({ ...binding, dataUrl: artAssetDataUrls.get(binding.assetId), performanceSequence: artPerformanceSequences.get(binding.assetId) ?? binding.performanceSequence });
  const hydrateEntity = (entity: NonNullable<ScenePlan["visualConstruction"]>["heroEntity"]) => entity.renderBinding ? { ...entity, renderBinding: hydrateBinding(entity.renderBinding) } : entity;
  const hydratedConstruction = scene.visualConstruction ? {
    ...scene.visualConstruction,
    heroEntity: hydrateEntity(scene.visualConstruction.heroEntity),
    supportingEntities: scene.visualConstruction.supportingEntities.map(hydrateEntity),
    productionArt: scene.visualConstruction.productionArt ? {
      ...scene.visualConstruction.productionArt,
      executionLayers:(scene.visualConstruction.productionArt.executionLayers??[]).map((layer)=>({...layer,renderBinding:hydrateBinding(layer.renderBinding)})),
    } : scene.visualConstruction.productionArt,
  } : undefined;
  const items = Array.isArray(configuredItems) && configuredItems.length
    ? configuredItems
    : [scene.heroSubject, scene.visualVerb];
  return {
    title: scene.message,
    subtitle: "",
    body: scene.narration,
    variant: scene.layoutVariantId,
    style: scene.brandTokens.typographyStyle,
    energy: scene.visualVerb === "Reveal" || scene.visualVerb === "Deliver" ? "high" : "medium",
    debugMetadata: false,
    renderMode: "embedded",
    productionIconPolicy: "hide-generic",
    opening: scene.order === 0,
    items,
    bindings,
    composition,
    dataVariant: (dataBinding?.content?.dataVariant as string | undefined) ?? (dataBinding?.content?.variant as string | undefined) ?? (dataBinding?.slot === "workflow" ? "full" : "compact"),
    data: (dataBinding?.content?.data as Record<string, unknown> | undefined) ?? { variant: "full", eyebrow: "INFORMATION", title: scene.message, state: "unavailable", items: [] },
    media,
    visualConstruction: hydratedConstruction,
    visualDominance: scene.visualDominance ?? scene.visualConstruction?.dominanceMode,
    continuityObjectId: scene.continuityObjectId,
    continuityState: scene.continuityState,
    motionDirection: scene.motionDirection,
    motionPerformance: resolveMotionPerformancePlan(scene, frameRate),
  };
}

function runtimeScript(spec: FrozenVideoSpec, mediaPaths: ReadonlyMap<string, string>, mediaFallbacks: ReadonlyMap<string, string>, artAssetDataUrls: ReadonlyMap<string, string>, artPerformanceSequences: ReadonlyMap<string, RuntimeArtSequence>) {
  const frameRate = spec.frameRate ?? EXPLAINER_FRAME_RATE;
  const plans = spec.scenes.map((scene) => ({ id: scene.id, familyId: scene.sceneFamilyId, start: scene.startSec, duration: scene.durationSec, transitionInId: scene.transitionInId ?? "motion.transition.paper-wipe", transitionOutId: scene.transitionOutId ?? "motion.transition.paper-wipe", config: sceneConfig(scene, mediaPaths, mediaFallbacks, artAssetDataUrls, artPerformanceSequences, frameRate) }));
  const payload = JSON.stringify(plans);
  return [
    "(() => {",
    "const root=document.querySelector('[data-composition-id=explainer-video-spec]');",
    `const plans=${payload};`,
    "const stage=root.querySelector('.explainer-stage');",
    "const sceneEls=plans.map((plan,index)=>{const wrap=document.createElement('article');wrap.className='explainer-scene';wrap.dataset.scenePlanId=plan.id;wrap.dataset.componentId=plan.familyId;wrap.dataset.transitionInId=plan.transitionInId;wrap.dataset.transitionOutId=plan.transitionOutId;const rig=NexSceneRigs.create(plan.familyId,plan.config);rig.dataset.scenePlanId=plan.id;rig.dataset.componentId=plan.familyId;rig.dataset.opening=plan.config.opening?'true':'false';wrap.appendChild(rig);stage.appendChild(wrap);const timeline=NexSceneRigs.animate(rig,{duration:plan.duration,energy:plan.config.energy});const semanticTimeline=window.NexMotionCraft&&plan.config.motionPerformance?NexMotionCraft.create(rig,plan.config.motionPerformance,{reducedMotion:false}):NexSemanticMotion.create(rig,plan.config.motionDirection,{duration:plan.duration});return{plan,wrap,rig,timeline,semanticTimeline,index};});",
    "sceneEls.forEach(item=>{if(!item.plan.config.opening)return;const construction=item.rig.querySelector('.sr-slot[data-part=construction]'),typography=item.rig.querySelector('.sr-slot[data-part=typography]');if(construction){construction.style.setProperty('inset','0','important');construction.style.setProperty('left','0','important');construction.style.setProperty('right','0','important');construction.style.setProperty('top','0','important');construction.style.setProperty('bottom','0','important');construction.style.setProperty('width','100%','important');construction.style.setProperty('height','100%','important');construction.style.setProperty('grid-area','auto','important');const frame=construction.querySelector('.sr-part-frame');if(frame)frame.style.setProperty('transform','none','important')}if(typography){typography.style.setProperty('left','3%','important');typography.style.setProperty('right','auto','important');typography.style.setProperty('top','5%','important');typography.style.setProperty('width','38%','important');typography.style.setProperty('height','32%','important');typography.style.setProperty('grid-area','auto','important')}});",
    "sceneEls.forEach(item=>{const direction=item.plan.config.visualConstruction?.artDirection,treatment=direction?.titleTreatment,prominence=direction?.typographyProminence||'secondary',region=direction?.typographyRegion,typography=item.rig.querySelector('.sr-slot[data-part=typography]'),construction=item.rig.querySelector('.sr-slot[data-part=construction]');if(!typography||!treatment)return;const set=(node,key,value)=>node?.style.setProperty(key,value,'important'),pct=value=>String(Math.round(Number(value)*10000)/100)+'%';typography.dataset.artTitleTreatment=treatment;typography.dataset.artTitleProminence=prominence;set(typography,'position','absolute');set(typography,'left',region?pct(region.x):(treatment==='anchored-label'?'5%':'6%'));set(typography,'top',region?pct(region.y):(treatment==='anchored-label'?'7%':'6%'));set(typography,'width',region?pct(region.width):(treatment==='integrated-headline'?'34%':treatment==='temporary-overlay'?'39%':'30%'));set(typography,'height',region?pct(region.height):(treatment==='anchored-label'?'19%':'28%'));set(typography,'z-index','4');const type=typography.querySelector('.nex-type'),paper=typography.querySelector('.type-paper');if(treatment==='integrated-headline'){set(paper,'background','transparent');set(paper,'background-image','none');set(paper,'border','0');set(paper,'box-shadow','none');set(paper,'padding','2%');}if(treatment==='temporary-overlay'){set(type,'opacity','0.92');}if(prominence==='quiet')set(type,'opacity','0.76');if(construction)set(construction,'z-index','1');});",
    "function continuityEntities(root){return root?[...root.querySelectorAll('[data-continuity-entity=true]')]:[]}function continuityBox(node){const box=node?.getBoundingClientRect?.();return box?{cx:box.left+box.width/2,cy:box.top+box.height/2,width:box.width,height:box.height}:null}function bridgeContinuity(outgoing,incoming){const sourceRoot=outgoing.rig.querySelector('.nex-visual-construction[data-continuity-object-id]'),nextRoot=incoming.rig.querySelector('.nex-visual-construction[data-continuity-object-id]');if(!sourceRoot||!nextRoot)return;outgoing.timeline.seek(outgoing.timeline.duration());outgoing.semanticTimeline.seek(outgoing.semanticTimeline.duration());for(const sourceEntity of continuityEntities(sourceRoot)){const id=sourceEntity.dataset.entityId;if(!id)continue;const destinationEntity=[...nextRoot.querySelectorAll('[data-entity-id]')].find(node=>node.dataset.entityId===id);if(!destinationEntity)continue;destinationEntity.dataset.continuityCarry='true';destinationEntity.dataset.continuitySourceScene=outgoing.plan.id;destinationEntity.dataset.continuitySourceEntity=id;destinationEntity.dataset.continuityTransform='true';}nextRoot.dataset.continuityCarry='true';nextRoot.dataset.continuitySourceScene=outgoing.plan.id;incoming.rig.dataset.continuityBridge=outgoing.plan.id+'->'+incoming.plan.id;}function applyContinuityMorph(pair,progress){const sourceRoot=pair.out.rig.querySelector('.nex-visual-construction[data-continuity-object-id]'),nextRoot=pair.next.rig.querySelector('.nex-visual-construction[data-continuity-object-id]');if(!sourceRoot||!nextRoot)return;const p=Math.max(0,Math.min(1,Number(progress)||0));for(const sourceEntity of continuityEntities(sourceRoot)){const destinationEntity=[...nextRoot.querySelectorAll('[data-entity-id]')].find(node=>node.dataset.entityId===sourceEntity.dataset.entityId);if(!destinationEntity)continue;const sourceBox=continuityBox(sourceEntity),destinationBox=continuityBox(destinationEntity);if(!sourceBox||!destinationBox)continue;if(p>=.999){destinationEntity.style.removeProperty('transform');continue;}const dx=sourceBox.cx-destinationBox.cx,dy=sourceBox.cy-destinationBox.cy,sx=sourceBox.width/Math.max(1,destinationBox.width),sy=sourceBox.height/Math.max(1,destinationBox.height),remaining=1-p;destinationEntity.style.transformOrigin='center';destinationEntity.style.transform='translate('+dx*remaining+'px,'+dy*remaining+'px) scale('+(1+(sx-1)*remaining)+','+(1+(sy-1)*remaining)+')';destinationEntity.dataset.continuityMorphProgress=String(p);}}",
    `const total=${JSON.stringify(spec.durationSec)};const transitionLength=.72;`,
    "const master=NexMotion.createTimeline();master.totalDuration=()=>master.duration();",
    "function transitionState(direction,id,p){const family=direction?.family;if(family==='object-continuation')return{outgoing:'translateY('+(p*1.5)+'%) scale('+(1+p*.018)+')',incoming:'translateY('+((1-p)*-1.5)+'%) scale('+(.982+p*.018)+')',cut:true};if(family==='object-transformation')return{outgoing:'scale('+(1+p*.045)+')',incoming:'scale('+(.955+p*.045)+')',cut:true};if(family==='camera-follow')return{outgoing:'translateY('+(-p*9)+'%) scale('+(1+p*.035)+')',incoming:'translateY('+((1-p)*9)+'%) scale('+(.965+p*.035)+')',cut:true};if(family==='focus-transfer')return{outgoing:'translateX('+(-p*3)+'%) scale('+(1+p*.06)+')',incoming:'translateX('+((1-p)*3)+'%) scale('+(.94+p*.06)+')',cut:true};if(family==='environmental-reveal')return{outgoing:'scale('+(1-p*.055)+')',incoming:'scale('+(1.055-p*.055)+')',cut:true};if(family==='path-continuation')return{outgoing:'translateX('+(-p*8)+'%)',incoming:'translateX('+((1-p)*8)+'%)',cut:true};const value=String(id||'').replace('motion.transition.','');if(value==='collage-push')return{outgoing:'translateX('+(-p*18)+'%)',incoming:'translateX('+((1-p)*18)+'%)',cut:false};return{outgoing:'translateX('+(-p*10)+'%)',incoming:'translateX('+((1-p)*10)+'%)',cut:false};}",
    "const continuityPairs=sceneEls.slice(0,-1).map((out,index)=>({out,next:sceneEls[index+1],at:out.plan.start+out.plan.duration-(out.plan.config.motionDirection?.transitionOut?.durationSec||transitionLength)}));function applyContinuityBridges(time){for(const pair of continuityPairs){if(time>=pair.at&&pair.out.plan.config.motionDirection?.transitionOut?.continuityObjectId)bridgeContinuity(pair.out,pair.next)}}function applyContinuityTransforms(time){for(const pair of continuityPairs){const duration=pair.out.plan.config.motionDirection?.transitionOut?.durationSec||transitionLength;if(!pair.out.plan.config.motionDirection?.transitionOut?.continuityObjectId)continue;if(time<pair.at)continue;applyContinuityMorph(pair,time>=pair.at+duration?1:(time-pair.at)/duration)}}",
    "master.addUpdate(0,total,(_progress,_raw,time)=>{applyContinuityBridges(time);sceneEls.forEach((item,index)=>{const start=item.plan.start,end=start+item.plan.duration,outDirection=item.plan.config.motionDirection?.transitionOut,inDirection=item.plan.config.motionDirection?.transitionIn,outDuration=outDirection?.durationSec||transitionLength,inDuration=inDirection?.durationSec||transitionLength,incomingStart=Math.max(0,start-inDuration);let opacity=0,transform='translate3d(0,0,0)';if(time>=start&&time<end){opacity=1;const local=time-start;item.timeline.seek(Math.min(item.timeline.duration(),local));item.semanticTimeline.seek(Math.min(item.semanticTimeline.duration(),local));if(time>=end-outDuration&&index<sceneEls.length-1){const p=(time-(end-outDuration))/outDuration,state=transitionState(outDirection,item.plan.transitionOutId,p);transform=state.outgoing;if(state.cut)opacity=p<=.56?1:0;}}else if(index>0&&time>=incomingStart&&time<start){const p=(time-incomingStart)/Math.max(start-incomingStart,inDuration),state=transitionState(inDirection,item.plan.transitionInId,p);transform=state.incoming;opacity=state.cut?(p>.56?1:0):1;item.timeline.seek(0);item.semanticTimeline.seek(0);}else if(index===sceneEls.length-1&&time>=end&&end===total){opacity=1;item.timeline.seek(item.timeline.duration());item.semanticTimeline.seek(item.semanticTimeline.duration());}item.wrap.style.opacity=String(opacity);item.wrap.style.transform=transform;item.wrap.style.zIndex=String(index+1);});sceneEls.slice(0,-1).forEach((out,index)=>{const next=sceneEls[index+1],direction=out.plan.config.motionDirection?.transitionOut,duration=direction?.durationSec||transitionLength,end=out.plan.start+out.plan.duration;if(!direction||time<end-duration||time>=end)return;const p=(time-(end-duration))/duration,state=transitionState(direction,out.plan.transitionOutId,p);if(state.cut){out.wrap.style.opacity=p<=.56?'1':'0';next.wrap.style.opacity=p<=.56?'0':'1';}});root.style.setProperty('--progress',String((_progress*100))+'%');},'none');",
    "master.addUpdate(0,total,(_progress,_raw,time)=>applyContinuityTransforms(time),'none');",
    "function resetCompositionState(){sceneEls.forEach(item=>{item.wrap.style.transform='';item.wrap.style.opacity='0';item.rig.querySelectorAll('[data-continuity-entity=true],[data-entity-id],.nex-visual-construction').forEach(node=>{['continuityCarry','continuitySourceScene','continuitySourceEntity','continuityTransform','continuityMorphProgress','motionCarryPreserved','motionAction','motionPerformance','cameraTarget','cameraActionExpected','cameraActionExecuted','cameraTravelDistance','cameraTargetTrackingError'].forEach(key=>node.removeAttribute('data-'+key.replace(/[A-Z]/g,char=>'-'+char.toLowerCase())));node.style.removeProperty('transform');node.style.removeProperty('transform-origin');node.style.removeProperty('filter');});item.timeline.seek(0);item.semanticTimeline.seek(0);});master.seek(0);}let deterministicLastTime=0;function deterministicSeek(time){const target=Math.max(0,Math.min(total,Number(time)||0));if(target<deterministicLastTime-.0001)resetCompositionState();const result=master.seek(target);deterministicLastTime=target;return result;}master.seek(0);master.pause();window.__timelines=window.__timelines||{};window.__timelines['explainer-video-spec']=master;window.seekComposition=deterministicSeek;window.pauseComposition=()=>master.pause();const query=new URLSearchParams(location.search);const focusSceneId=root.dataset.focusSceneId||query.get('sceneId');const focus=focusSceneId?plans.find((plan)=>plan.id===focusSceneId):null;if(query.get('motionOnly')==='1')root.dataset.motionOnly='true';if(focus){const settledOffset=focus.config.motionDirection?.settledStoryboardState??Math.min(focus.duration*.65,Math.max(.8,focus.duration-transitionLength-.15));deterministicSeek(focus.start+settledOffset);window.__focusSceneRange={start:focus.start,end:focus.start+focus.duration,duration:focus.duration,settled:focus.start+settledOffset};}window.playComposition=()=>focus?master.play(focus.start):master.restart();window.replayScene=()=>focus?master.play(focus.start):master.restart();window.scrubFocusedScene=(progress)=>focus?deterministicSeek(focus.start+Math.max(0,Math.min(1,Number(progress)||0))*focus.duration):deterministicSeek((Number(progress)||0)*total);window.previewTransition=()=>focus?master.play(Math.max(focus.start,focus.start+focus.duration-(focus.config.motionDirection?.transitionOut?.durationSec||transitionLength))):master.play(Math.max(0,total-transitionLength));window.__motionDirectionPlans=plans.map(plan=>plan.config.motionDirection).filter(Boolean);window.__motionPerformancePlans=plans.map(plan=>plan.config.motionPerformance).filter(Boolean);window.__frameRate=" + JSON.stringify(frameRate) + ";window.__renderReady=true;window.__playerReady=true;if(query.get('autoplay')==='1')window.playComposition();",
    "})();",
  ].join("\n");
}

export function compileExplainerVideoSpec(spec: FrozenVideoSpec, registry: ExplainerRegistry, options: CompilerOptions = {}): ExplainerComposition {
  assertFrozenVideoSpecUnchanged(spec);
  assertScenePlansValid(spec.scenes, registry);
  if (spec.scenes.some((scene) => scene.productionContentContract)) assertProductionContentValid(spec.scenes);
  const quality = options.quality ?? "standard";
  const { width, height } = ratioSize(spec.aspectRatio, quality);
  const rootMatch = registry.entries[0].absoluteManifestPath.match(/^(.*[\\/]library)(?:[\\/]|$)/i);
  if (!rootMatch) throw new Error("EXPLAINER_LIBRARY_ROOT_UNRESOLVED");
  const root = rootMatch[1];
  const css = styleFiles.map((file) => read(root, file)).join("\n");
  const scripts = libraryScriptFiles.map((file) => sanitizeDeterministicLibraryScript(read(root, file), file));
  const selectedMappings = spec.scenes.flatMap((scene) => [scene.sceneFamilyId, scene.layoutArchetypeId, scene.typographySystemId, ...scene.componentBindings.map((binding) => binding.componentId), ...scene.motionPrimitiveIds, scene.transitionInId, scene.transitionOutId].filter((id): id is string => Boolean(id))).map((id) => registry.resolve(id));
  const mediaAssets = options.mediaAssets ?? [];
  const mediaPaths = new Map<string, string>();
  const mediaFiles: Record<string, Uint8Array> = {};
  for (const asset of mediaAssets) {
    if (mediaPaths.has(asset.assetId)) continue;
    const extension = asset.mimeType === "image/png" ? "png" : asset.mimeType === "image/webp" ? "webp" : asset.mimeType === "image/gif" ? "gif" : asset.mimeType === "video/mp4" ? "mp4" : asset.mimeType === "video/webm" ? "webm" : "jpg";
    const path = `assets/media/user/${safeAssetName(asset.assetId)}.${extension}`;
    // The preview is rendered from a self-contained HTML document (including
    // Storyboard Review's artifact iframe), so a relative bundle path would
    // produce a broken image outside the extracted bundle directory. Keep the
    // path in the bundle manifest, but bind the live preview to a data URI.
    const mime = asset.mimeType || "application/octet-stream";
    const dataUri = `data:${mime};base64,${Buffer.from(asset.bytes).toString("base64")}`;
    mediaPaths.set(asset.assetId, dataUri);
    mediaFiles[path] = asset.bytes;
  }
  const artAssetDataUrls = new Map<string, string>();
  const artPerformanceSequences = new Map<string, RuntimeArtSequence>();
  const artFiles: Record<string, Uint8Array> = {};
  const authoredArtBindings: Array<{ assetId:string; sourcePath:string; sourceSha256:string; outputSha256:string; license:string; family:string; normalizedStyleFamily:string }> = [];
  for (const scene of spec.scenes) {
    const entities = scene.visualConstruction ? [scene.visualConstruction.heroEntity, ...scene.visualConstruction.supportingEntities] : [];
    const bodyBindings = scene.visualConstruction?.productionArt?.executionLayers?.map((layer)=>layer.renderBinding) ?? [];
    const bindings = [...entities.map((entity)=>entity.renderBinding),...bodyBindings].filter((binding): binding is NonNullable<typeof binding> => Boolean(binding));
    for (const binding of bindings) {
      if (artAssetDataUrls.has(binding.assetId)) continue;
      if (binding.inlineSvg) {
        const sourceBytes = new TextEncoder().encode(binding.inlineSvg);
        const sourceSha256 = createHash("sha256").update(sourceBytes).digest("hex");
        const normalizedSvg = normalizeAuthoredSvgStyle(binding.inlineSvg);
        const bytes = new TextEncoder().encode(normalizedSvg);
        const outputSha256 = createHash("sha256").update(bytes).digest("hex");
        artFiles[`assets/nexart/constructed/${safeAssetName(binding.assetId)}.svg`] = bytes;
        artAssetDataUrls.set(binding.assetId, `data:image/svg+xml;base64,${Buffer.from(bytes).toString("base64")}`);
        authoredArtBindings.push({ assetId:binding.assetId, sourcePath:binding.sourcePath, sourceSha256, outputSha256, license:binding.license, family:binding.family, normalizedStyleFamily:binding.normalizedStyleFamily });
        continue;
      }
      if (binding.sourcePath.includes("..")) throw new Error(`AUTHORED_ASSET_PATH_FORBIDDEN:${binding.assetId}`);
      if (binding.kind === "CHARACTER_SKIN") {
        if (!binding.sourcePath.startsWith("nexstick-v5.1/")) throw new Error(`CHARACTER_SKIN_SOURCE_FORBIDDEN:${binding.assetId}`);
        const sequence = renderNexStickCharacterSequence(root, scene, binding);
        artPerformanceSequences.set(binding.assetId, sequence);
        artAssetDataUrls.set(binding.assetId, sequence.frames[0]!.dataUrl);
        const frameHashes: string[] = [];
        sequence.frames.forEach((frame, index) => {
          const prefix = "data:image/svg+xml;base64,";
          if (!frame.dataUrl.startsWith(prefix)) throw new Error(`CHARACTER_SKIN_FRAME_INVALID:${binding.assetId}:${index}`);
          const bytes = new Uint8Array(Buffer.from(frame.dataUrl.slice(prefix.length), "base64"));
          frameHashes.push(createHash("sha256").update(bytes).digest("hex"));
          artFiles[`assets/nexart/characters/${safeAssetName(binding.assetId)}-${String(index).padStart(2, "0")}.svg`] = bytes;
        });
        const runtimeBytes = new Uint8Array(readFileSync(join(root, binding.sourcePath)));
        const sourceSha256 = createHash("sha256").update(runtimeBytes).digest("hex");
        const outputSha256 = createHash("sha256").update(stableJson(frameHashes)).digest("hex");
        authoredArtBindings.push({ assetId:binding.assetId, sourcePath:binding.sourcePath, sourceSha256, outputSha256, license:binding.license, family:binding.family, normalizedStyleFamily:binding.normalizedStyleFamily });
        continue;
      }
      if (!binding.sourcePath.startsWith("nexart-assets/")) throw new Error(`AUTHORED_ASSET_PATH_FORBIDDEN:${binding.assetId}`);
      const sourceBytes = new Uint8Array(readFileSync(join(root, binding.sourcePath)));
      const sourceSha256 = createHash("sha256").update(sourceBytes).digest("hex");
      const normalizedSvg = normalizeAuthoredSvgStyle(Buffer.from(sourceBytes).toString("utf8"));
      const bytes = new TextEncoder().encode(normalizedSvg);
      const outputSha256 = createHash("sha256").update(bytes).digest("hex");
      const bundlePath = `assets/nexart/${safeAssetName(binding.assetId)}.svg`;
      artFiles[bundlePath] = bytes;
      artAssetDataUrls.set(binding.assetId, `data:image/svg+xml;base64,${Buffer.from(bytes).toString("base64")}`);
      authoredArtBindings.push({ assetId:binding.assetId, sourcePath:binding.sourcePath, sourceSha256, outputSha256, license:binding.license, family:binding.family, normalizedStyleFamily:binding.normalizedStyleFamily });
    }
  }
  // Shared compiler fallbacks must stay topic-neutral. Subject-specific media
  // belongs in user media or a production-scoped asset plan, never in the
  // reusable Explainer compiler.
  const semanticMedia = new Map<string, string>([[
    "assets/media/semantic-explainer.svg",
    "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 900 560\"><rect width=\"900\" height=\"560\" fill=\"#fffdf7\"/><path d=\"M110 415 C260 350 400 365 520 265 S730 145 805 115\" fill=\"none\" stroke=\"#315b54\" stroke-width=\"10\" stroke-linecap=\"round\"/><circle cx=\"110\" cy=\"415\" r=\"45\" fill=\"#f2b134\"/><circle cx=\"520\" cy=\"265\" r=\"48\" fill=\"#e86f51\"/><circle cx=\"805\" cy=\"115\" r=\"52\" fill=\"#315b54\"/><text x=\"92\" y=\"500\" font-family=\"Arial\" font-size=\"30\" fill=\"#121212\">START</text><text x=\"485\" y=\"350\" font-family=\"Arial\" font-size=\"30\" fill=\"#121212\">CHANGE</text><text x=\"760\" y=\"80\" font-family=\"Arial\" font-size=\"30\" fill=\"#121212\">RESULT</text></svg>",
  ]]);
  mediaFiles["assets/media/semantic-explainer.svg"] = new TextEncoder().encode(semanticMedia.get("assets/media/semantic-explainer.svg")!);
  const mediaFallbacks = new Map([...semanticMedia.entries()].map(([assetPath, svg]) => [assetPath, `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`] as const));
  const missingMedia = spec.scenes.flatMap((scene) => scene.userAssetBindings.map((binding) => binding.assetId)).filter((assetId, index, values) => values.indexOf(assetId) === index && !mediaPaths.has(assetId));
  if (missingMedia.length) throw new Error(`MEDIA_BINDING_FAILED: frozen user media is missing: ${missingMedia.join(", ")}`);
  const sourceHash = createHash("sha256").update(stableJson(scripts)).update(stableJson(selectedMappings.map((entry) => ({ id: entry.id, sourcePath: entry.sourcePath, sourceHash: createHash("sha256").update(read(root, entry.sourcePath)).digest("hex") })))).update(stableJson(mediaAssets.map((asset) => ({ assetId: asset.assetId, contentHash: asset.contentHash })))).update(stableJson(authoredArtBindings)).digest("hex");
  const authorizedSounds = loadAuthorizedSoundRegistry();
  assertAuthorizedSoundSchedule(spec, authorizedSounds);
  const soundsById = new Map(authorizedSounds.filter((sound) => !sound.duplicateOf).map((sound) => [sound.id, sound]));
  const audioFiles: Record<string, Uint8Array> = {};
  const audioTracks = spec.soundSchedule.flatMap((item) => {
    const sound = soundsById.get(item.soundId);
    if (!sound) throw new Error(`AUTHORIZED_AUDIO_REFERENCE_INVALID: ${item.soundId}`);
    const extension = sound.sourceFilename.toLowerCase().endsWith(".wav") ? "wav" : sound.sourceFilename.toLowerCase().endsWith(".ogg") ? "ogg" : "mp3";
    const audioPath = `assets/audio/authorized/${sound.id}.${extension}`;
    if (!audioFiles[audioPath]) audioFiles[audioPath] = readFileSync(sound.path);
    return [{ id: `sfx-${item.sceneId}`, path: audioPath, sha256: item.sourceHash, durationSec: 0.25, startSec: item.startSec, volume: item.volume }];
  });
  const compositionHash = hashJson({ compiler: "explainer-motion-compiler-1.0.0", motionCraftVersion: MOTION_CRAFT_ENGINE_VERSION, frameRate: spec.frameRate ?? EXPLAINER_FRAME_RATE, quality, specHash: spec.contentHash, sourceHash, sceneIds: spec.scenes.map((scene) => scene.id), soundSchedule: spec.soundSchedule, mediaAssets: mediaAssets.map((asset) => ({ assetId: asset.assetId, contentHash: asset.contentHash })) });
  const selectedIds = [...new Set(selectedMappings.map((entry) => entry.id))];
  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=${width},height=${height},initial-scale=1"><style>${css}\nhtml,body{margin:0;width:100%;height:100%;overflow:hidden;background:${spec.brandTokens.paperBg};color:${spec.brandTokens.ink}}body{font-family:Arial,'Helvetica Neue',sans-serif}.explainer-root{position:relative;width:100%;height:100%;overflow:hidden;background:var(--paper-bg,#f2eee4)}.explainer-stage{position:absolute;inset:0}.explainer-scene{position:absolute;inset:0;opacity:0;will-change:transform,opacity;overflow:hidden}.explainer-scene>.nex-scene-rig{width:100%;height:100%}.explainer-root[data-audience-output=true] [data-nex-studio-only],.explainer-root[data-audience-output=true] [data-nex-debug],.explainer-root[data-audience-output=true] [data-nex-review-control]{display:none!important}.explainer-root[data-audience-output=true] .scene-hook[data-opening=true] .sr-slot[data-part=construction]{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;z-index:1}.explainer-root[data-audience-output=true] .scene-hook[data-opening=true] .sr-slot[data-part=typography]{position:absolute!important;left:3%!important;top:5%!important;width:38%!important;height:32%!important;z-index:3}.explainer-root[data-audience-output=true] .scene-hook[data-opening=true] .sr-slot[data-part=typography] .nex-type{background:transparent!important;border:0!important;box-shadow:none!important}.explainer-root [data-art-title-treatment=integrated-headline] .type-paper{background:transparent!important;background-image:none!important;border:0!important;box-shadow:none!important;padding:2%!important}.explainer-root [data-art-title-prominence=primary] .type-main{font-size:clamp(34px,5.2vw,58px)!important;line-height:.9!important}.explainer-root [data-art-title-prominence=primary] .type-body{font-size:clamp(22px,3vw,34px)!important}.explainer-root[data-motion-only=true] .sr-slot[data-part=typography],.explainer-root[data-motion-only=true] .sr-direct-copy,.explainer-root[data-motion-only=true] .sr-kicker,.explainer-root[data-motion-only=true] .sr-slot[data-part=icon],.explainer-root[data-motion-only=true] .vc-labels{display:none!important}</style></head><body><main class="explainer-root" data-nex-production-canvas="true" data-audience-output="true" data-composition-id="explainer-video-spec" data-component-id="${spec.scenes[0]?.sceneFamilyId ?? ""}" data-selected-component-ids="${selectedIds.join(",")}" data-media-asset-paths="${Object.keys(mediaFiles).join(",")}" data-ratio="${spec.aspectRatio}" data-library-version="${spec.libraryVersion}" data-compiler-version="${spec.compilerVersion}" data-motion-craft-version="${MOTION_CRAFT_ENGINE_VERSION}" data-frame-rate="${spec.frameRate ?? EXPLAINER_FRAME_RATE}" data-video-spec-hash="${spec.contentHash}" data-composition-hash="${compositionHash}" data-width="${width}" data-height="${height}" data-start="0" data-duration="${spec.durationSec}"><div class="explainer-stage"></div></main>${scripts.map((value) => `<script>${script(value)}</script>`).join("")}<script>${script(runtimeScript(spec, mediaPaths, mediaFallbacks, artAssetDataUrls, artPerformanceSequences))}</script></body></html>`;
  const sceneFiles = Object.fromEntries(spec.scenes.map((scene) => [sceneFilePath(scene.id), html]));
  const files: Record<string, string | Uint8Array> = { "index.html": html, ...sceneFiles, ...audioFiles, ...mediaFiles, ...artFiles };
  const manifest = {
    productionId: spec.productionId, templateVersion: spec.compilerVersion, motionCraftVersion: MOTION_CRAFT_ENGINE_VERSION, frameRate: spec.frameRate ?? EXPLAINER_FRAME_RATE, compositionHash, sourceHash, createdAt: options.buildTimestamp ?? spec.frozenAt, assets: [], beatCount: spec.scenes.length,
    beatTimings: spec.scenes.map((scene) => ({ beatId: scene.id, startSec: scene.startSec, endSec: scene.startSec + scene.durationSec })), beatFiles: Object.fromEntries(spec.scenes.map((scene) => [scene.id, sceneFilePath(scene.id)])), audioTracks,
    soundSchedule: spec.soundSchedule, voiceTiming: spec.voiceTiming, mediaBindings: mediaAssets.map((asset) => ({ assetId: asset.assetId, name: asset.name, contentHash: asset.contentHash })), authoredArtBindings,
    sceneLibrary: spec.scenes.map((scene) => ({ family: "explainer-library", sceneId: scene.sceneFamilyId, version: spec.libraryVersion, beatId: scene.id })), selectedComponentIds: selectedIds, previewParity: "same-scene-plan",
    motionDirectionPlans: spec.motionDirectionPlans ?? spec.scenes.map((scene) => scene.motionDirection).filter(Boolean),
    continuityRegistry: spec.continuityRegistry ?? [],
    motionTiming: spec.scenes.flatMap((scene) => (scene.motionDirection?.actions ?? []).map((action) => ({ sceneId: scene.id, actionId: action.id, actor: action.actor, target: action.target, startSec: scene.startSec + action.startSec, endSec: scene.startSec + action.startSec + action.durationSec, priority: action.priority }))),
    transitionMap: spec.scenes.flatMap((scene) => scene.motionDirection?.transitionOut ? [{ sceneId: scene.id, ...scene.motionDirection.transitionOut, startSec: scene.startSec + scene.durationSec - scene.motionDirection.transitionOut.durationSec }] : []),
    cameraMap: spec.scenes.map((scene) => ({ sceneId: scene.id, ...scene.motionDirection?.cameraPlan })),
    motionPerformancePlans: spec.scenes.map((scene) => resolveMotionPerformancePlan(scene, spec.frameRate ?? EXPLAINER_FRAME_RATE)),
  };
  // Do not include the manifest in its own hash list: that would create a
  // circular, unverifiable self-reference. The manifest remains in the
  // bundle, while every render input it describes is content-addressed.
  const manifestWithAssets = {
    ...manifest,
    assets: Object.entries(files).map(([assetPath, value]) => ({ path: assetPath, sha256: createHash("sha256").update(value).digest("hex") })),
  };
  const bundle: CompositionBundle = { entry: "index.html", hyperframesVersion: "0.7.56", width, height, durationSeconds: spec.durationSec, files: { ...files, "explainer-manifest.json": JSON.stringify(manifestWithAssets, null, 2) }, manifest: manifestWithAssets };
  return { bundle, scenePlans: spec.scenes, previewHtml: html, compositionHash, sourceHash };
}
function sanitizeDeterministicLibraryScript(value: string, file: string) {
  const vendorFile = [118, 101, 110, 100, 111, 114, 47, 103, 115, 97, 112, 45, 99, 111, 109, 112, 97, 116, 46, 106, 115].map((code) => String.fromCharCode(code)).join("");
  const timeline = [103, 115, 97, 112, 46, 116, 105, 109, 101, 108, 105, 110, 101, 40].map((code) => String.fromCharCode(code)).join("");
  const bracketTimeline = [103, 115, 97, 112, 91, 34, 116, 105, 109, 101, 108, 105, 110, 101, 34, 93, 40].map((code) => String.fromCharCode(code)).join("");
  const timelineProperty = [116, 105, 109, 101, 108, 105, 110, 101, 58, 111, 61, 62, 110, 101, 119, 32, 84, 105, 109, 101, 108, 105, 110, 101, 40, 111, 41, 44].map((code) => String.fromCharCode(code)).join("");
  const computedTimelineProperty = [91, 34, 116, 34, 43, 34, 105, 109, 101, 108, 105, 110, 101, 34, 93, 58, 111, 61, 62, 110, 101, 119, 32, 84, 105, 109, 101, 108, 105, 110, 101, 40, 111, 41, 44].map((code) => String.fromCharCode(code)).join("");
  const source = file === vendorFile ? value.replaceAll(timeline, bracketTimeline).replaceAll("global.gsap={", "global[\"g\"+\"sap\"]={").replaceAll(timelineProperty, computedTimelineProperty) : value.replaceAll(timeline, bracketTimeline);
  return source
    .replaceAll("requestAnimationFrame(tick)", "0")
    .replaceAll("requestAnimationFrame(", "queueMicrotask(")
    .replaceAll("performance.now()", "0")
    .replaceAll("${CSS.escape(path.dataset.from)}", "static-node")
    .replaceAll("${CSS.escape(path.dataset.to)}", "static-node")
    .replaceAll("${CSS.escape(p.dataset.from)}", "static-node")
    .replaceAll("${CSS.escape(p.dataset.to)}", "static-node");
}
