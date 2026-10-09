import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { loadExplainerRegistry } from "../src/studio/explainer-motion-v1/registry-loader";
import { analyzeReferenceLanguage } from "../src/studio/explainer-motion-v1/nexart/reference-language";
import { attachProductionArtPlans } from "../src/studio/explainer-motion-v1/nexart/production-art";
import { createScenePlans } from "../src/studio/explainer-motion-v1/scene-plan";
import { renderExplainerStoryboardPreview } from "../src/studio/explainer-motion-v1/preview-renderer";
import { renderCompositionBundle } from "../src/hyperframes/renderer";
import type { BrandTokenSet, DirectorPlan, DirectorScenePlan, StoryPurpose, StorySpec, VisualConstructionPlan, VisualEntity, VisualStyleProfile, VisualVerb } from "../src/studio/explainer-motion-v1/types";

// Execution-only P8 bridge. Creative meaning is authored upstream by NexMind P8.
// This body either executes the exact authored plate/camera/action/Brand commitments
// or fails. It does not own commercial taste, scene-family ideation, or art direction.

type Dict = Record<string, any>;
type Request = {
  schema: "StudioP8ExplainerExecutionRequestV1";
  operation: "BUILD_INTERNAL_REVIEW_EVIDENCE";
  productionId: string;
  durationSeconds: number;
  aspectRatio: "16:9" | "1:1" | "9:16";
  outputDirectory: string;
  finalBoard: Dict;
  creativeCheckpoint: Dict;
  creativeDossier?: Dict | null;
  executionPlan?: Dict | null;
  brandExecution: Dict;
  referenceMedia?: Array<{ assetId: string; path: string; mimeType: string; name?: string }>;
  authoredScenePlates: Array<{ schema:"NexStudioAuthoredScenePlateBindingV1"; beatId:string; lockedSemanticsHash:string; semanticBindings:Array<{semantic_ref:string;role?:string}>; stages:Array<{pngDataUrl:string;sha256:string}>; creativeChoiceIntroduced:false }>;
};

const rec=(v:any):Dict=>v&&typeof v==="object"&&!Array.isArray(v)?v:{};
const arr=(v:any):any[]=>Array.isArray(v)?v:[];
const str=(v:any,f="")=>typeof v==="string"&&v.trim()?v.trim():f;
const sha=(v:any)=>createHash("sha256").update(JSON.stringify(v)).digest("hex");
const slug=(v:string)=>v.toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"").slice(0,64)||"entity";

function decision(checkpoint:Dict, slot:string):Dict {
  const p=rec(rec(rec(checkpoint.state).decisions)[slot]?.payload);
  if(!Object.keys(p).length) throw new Error(`P8_COMMITTED_DECISION_MISSING:${slot}`);
  return p;
}
function p8Story(checkpoint:Dict):Dict {
  const story=rec(decision(checkpoint,"film_thesis").story);
  if(!Object.keys(story).length) throw new Error("P8_COMMITTED_STORY_PAYLOAD_MISSING");
  return story;
}
function authoredPlateFor(req:Request,beatId:string){
  const plate=req.authoredScenePlates.find(item=>item.beatId===beatId);
  if(!plate) throw new Error(`EXPLAINER_AUTHORED_PLATE_REQUIRED:${beatId}`);
  if(plate.schema!=="NexStudioAuthoredScenePlateBindingV1"||plate.creativeChoiceIntroduced!==false) throw new Error(`PRODUCTION_SCOPED_ART_CONTRACT_INVALID:${beatId}`);
  if(!plate.lockedSemanticsHash||!Array.isArray(plate.semanticBindings)||!Array.isArray(plate.stages)||plate.stages.length<1) throw new Error(`PRODUCTION_SCOPED_ART_PAYLOAD_INVALID:${beatId}`);
  const finalStage=plate.stages[plate.stages.length-1]!;
  if(typeof finalStage.pngDataUrl!=="string"||!finalStage.pngDataUrl.startsWith("data:image/png;base64,")) throw new Error(`PRODUCTION_SCOPED_ART_PIXELS_INVALID:${beatId}`);
  return {schema:plate.schema,lockedSemanticsHash:plate.lockedSemanticsHash,semanticBindings:plate.semanticBindings,finalPngDataUrl:finalStage.pngDataUrl,stageCount:plate.stages.length,creativeChoiceIntroduced:false as const};
}
function exactSupportLabels(beat:Dict):string[]{
  return arr(beat.supporting_assets).map((x:any)=>typeof x==="string"?x:str(x?.label||x?.semantic_ref||x?.role||x?.name||x?.id)).filter(Boolean);
}
function entity(label:string,importance:"hero"|"supporting"):VisualEntity {
  return {id:slug(label),type:"object",semanticType:label,importance,visualClass:"illustration",label,capabilities:["continuity-capable","transformable"]};
}
function exactHexes(value:any,out:string[]=[]):string[]{
  if(typeof value==="string") { if(/^#[0-9a-f]{6}$/i.test(value)&&!out.includes(value)) out.push(value); return out; }
  if(Array.isArray(value)) { for(const x of value) exactHexes(x,out); return out; }
  if(value&&typeof value==="object") for(const x of Object.values(value)) exactHexes(x,out);
  return out;
}
function brandTokens(req:Request):BrandTokenSet {
  if(req.brandExecution?.schema!=="StudioBrandExecutionV1"||!str(req.brandExecution?.brandExecutionHash)) throw new Error("EXPLAINER_BRAND_EXECUTION_REQUIRED");
  const colors=exactHexes(req.brandExecution.brandAuthority??req.brandExecution.productionBrandContext??{});
  const neutral=["#ffffff","#f7f7f7","#111111","#555555"];
  const pick=(i:number)=>colors[i%Math.max(1,colors.length)]??neutral[i%neutral.length]!;
  return {paperBg:pick(0),paperSurface:pick(1),ink:pick(2),inkMuted:pick(3),primary:pick(0),secondary:pick(1),accent:pick(2),highlight:pick(3),typographyStyle:str(req.brandExecution?.brandAuthority?.typographyStyle,"brand-bound")};
}
const technicalStyle:VisualStyleProfile={primaryVisualLanguage:"mixed-hybrid",secondaryVisualLanguage:"illustrated",photographyPolicy:"allowed",depth:"light",strokeStyle:"none",shapeStyle:"geometric",motionEnergy:"medium"};

function buildContracts(req:Request, referenceProfile?:any){
  const board=rec(req.finalBoard); if(board.schema!=="NexMindCanonicalSoundStoryboardV4") throw new Error("P8_FINAL_BOARD_SCHEMA_UNSUPPORTED");
  const beats=arr(board.beats); if(!beats.length) throw new Error("P8_FINAL_BOARD_EMPTY");
  const storyP8=p8Story(req.creativeCheckpoint); const storyById=new Map(arr(storyP8.beats).map((b:any)=>[str(b.beat_id),b]));
  const visual=decision(req.creativeCheckpoint,"visual_concept"); const art=decision(req.creativeCheckpoint,"art_direction");
  const constructions:VisualConstructionPlan[]=[]; const directorScenes:DirectorScenePlan[]=[];
  const storyBeats=beats.map((beat:any,index:number)=>{
    const bid=str(beat.beat_id); if(!bid) throw new Error(`P8_BEAT_ID_REQUIRED:${index}`);
    const sb=rec(storyById.get(bid));
    const heroLabel=str(beat.hero_identity); if(!heroLabel) throw new Error(`EXPLAINER_HERO_IDENTITY_REQUIRED:${bid}`);
    const supportLabels=exactSupportLabels(beat); const hero=entity(heroLabel,"hero"); const support=supportLabels.map(label=>entity(label,"supporting"));
    const productionScopedArt=authoredPlateFor(req,bid); const camera=rec(beat.camera); const cameraAtom=rec(camera.camera_atom);
    if(!str(cameraAtom.atom)||!str(cameraAtom.target)) throw new Error(`P8_CAMERA_ATOM_REQUIRED:${bid}`);
    const motions=arr(beat.motion_actions); for(const [ai,a] of motions.entries()) if(!str(rec(a).execution?.resolved_verb)) throw new Error(`P8_MOTION_EXECUTION_BINDING_REQUIRED:${bid}:${ai}`);
    const construction:VisualConstructionPlan={sceneId:`${req.productionId}.${bid}`,semanticGoal:str(beat.scene_thesis,sb.reveal),heroEntity:hero,supportingEntities:support,relationships:[],spatialGrammar:"freeform",labelStrategy:"none",constructionMode:"illustration-composition",requiredCapabilities:["PRODUCTION_SCOPED_AUTHORED_ART"],optionalCapabilities:[],dominanceMode:"illustration-led",styleProfile:technicalStyle,motionIntent:{entryState:str(beat.opening_state,"p8-authored-entry"),mainAction:str(beat.motion_intent,"p8-authored-action"),settledState:str(beat.settled_state,"p8-authored-settle"),exitTransformation:str(beat.continuity_out,"p8-authored-exit"),continuityHandoff:str(beat.continuity_out,"p8-authored-handoff")},visualCoverage:"covered",coverageDecision:"production-scoped-asset",directorContractVersion:"P8_FINAL_BOARD",visualGrammarVersion:"EXECUTION_BODY_V3",productionScopedArt,p8MotionActions:motions,p8CameraAtom:cameraAtom,p8BrandExecutionHash:str(req.brandExecution.brandExecutionHash)};
    constructions.push(construction);
    const directorScene:DirectorScenePlan={sceneId:construction.sceneId,storyFunction:"P8_AUTHORED",visualVerb:"Reveal" as VisualVerb,heroSubject:heroLabel,supportingSubjects:supportLabels,layoutIntent:"P8_AUTHORED_PLATE",informationDensity:"medium",cameraIntent:str(cameraAtom.atom),transitionIntent:str(beat.continuity_out,"P8_AUTHORED"),copyBudget:0,emotionalEnergy:str(rec(beat.editorial).energy,"P8_AUTHORED"),continuityKey:hero.id,visualConcept:str(visual.visual_thesis),visualDirection:{visualVerb:"P8_AUTHORED",heroSubject:heroLabel,startingState:str(beat.opening_state),transformation:str(beat.motion_intent),endingState:str(beat.settled_state),spatialRelationship:str(beat.continuity_out),continuityObject:hero.id,energy:str(rec(beat.editorial).energy,"P8_AUTHORED")},visualConstruction:construction,visualDominance:"illustration-led",styleProfile:technicalStyle,motionIntent:construction.motionIntent};
    directorScenes.push(directorScene);
    const editorial=rec(beat.editorial); const durationValue=Number(rec(editorial.duration).value); const durationRate=Number(rec(editorial.duration).rate); const dur=durationValue>0&&durationRate>0?durationValue/durationRate:req.durationSeconds/beats.length;
    // StoryPurpose/VisualVerb are compatibility fields for the technical shell only.
    // They do not select creative content when a production-scoped plate is present.
    return {id:`${req.productionId}:${bid}`,order:index,purpose:"concept" as StoryPurpose,message:str(sb.reveal,beat.scene_thesis),narration:str(sb.narration_job,sb.reveal||beat.scene_thesis),durationSec:Math.max(.25,dur),semanticMessage:str(beat.scene_thesis),narrativeRole:str(sb.purpose,"P8_AUTHORED"),visualDirection:directorScene.visualDirection,visualVerb:"Reveal" as VisualVerb};
  });
  const withArt=attachProductionArtPlans(constructions,{referenceLanguage:referenceProfile});
  withArt.forEach((c,i)=>{ if(!c.productionArt||c.productionArt.status!=="READY_FOR_RENDER") throw new Error(`PRODUCTION_SCOPED_ART_NOT_READY:${c.sceneId}`); directorScenes[i]!.visualConstruction=c; });
  const thesis=rec(storyP8.film_thesis); const story:StorySpec={id:`${req.productionId}:p8-story`,productionId:req.productionId,title:str(thesis.central_argument,req.productionId),durationSec:storyBeats.reduce((n,b)=>n+b.durationSec,0),sceneCount:storyBeats.length,audience:str(thesis.audience_after,"P8 audience"),goal:str(thesis.central_argument),coreMessage:str(thesis.central_argument),tone:str(thesis.tone,"P8_AUTHORED"),aspectRatio:req.aspectRatio,beats:storyBeats,version:"P8_TO_EXECUTION_BODY_V3",rawRequest:str(rec(rec(req.creativeCheckpoint).state).brief?.prompt)};
  const director:DirectorPlan={storySpecId:story.id,productionId:req.productionId,scenes:directorScenes,version:"P8_TO_EXECUTION_BODY_V3"};
  return {story,director,constructions:withArt,p8:{visual,art,finalBoardHash:sha(board),checkpointStateHash:str(req.creativeCheckpoint.state_hash),brandExecutionHash:str(req.brandExecution.brandExecutionHash)}};
}
function executionFidelity(req:Request,contracts:ReturnType<typeof buildContracts>,scenes:any[]){
  const beats=arr(req.finalBoard.beats); const issues:string[]=[];
  if(contracts.constructions.length!==beats.length||scenes.length!==beats.length) issues.push("BEAT_COUNT_MISMATCH");
  beats.forEach((beat:any,i:number)=>{
    const c=contracts.constructions[i]; const scene=scenes[i]; if(!c||!scene){issues.push(`BEAT_MISSING:${i}`);return;}
    const expectedSupports=exactSupportLabels(beat); const actualSupports=c.supportingEntities.map((x:any)=>x.semanticType);
    if(sha(expectedSupports)!==sha(actualSupports)) issues.push(`SUPPORT_BINDING_MISMATCH:${beat.beat_id}`);
    if(sha(arr(beat.motion_actions))!==sha(c.p8MotionActions??[])) issues.push(`MOTION_BINDING_MISMATCH:${beat.beat_id}`);
    if(sha(rec(rec(beat.camera).camera_atom))!==sha(c.p8CameraAtom??{})) issues.push(`CAMERA_BINDING_MISMATCH:${beat.beat_id}`);
    if(c.p8BrandExecutionHash!==str(req.brandExecution.brandExecutionHash)) issues.push(`BRAND_BINDING_MISMATCH:${beat.beat_id}`);
    if(!c.productionScopedArt||!c.productionArt?.productionScopedAuthoredPlate) issues.push(`AUTHORED_PLATE_BINDING_MISSING:${beat.beat_id}`);
    if(!scene.motionDirection) issues.push(`MOTION_EXECUTION_PLAN_MISSING:${beat.beat_id}`);
  });
  return {schema:"StudioFamilyExecutionFidelityV1",authority:"EXECUTION_FIDELITY_ONLY",status:issues.length?"FAIL":"PASS",issues,commercialScore:null,commercialJudgmentAuthority:false,brandExecutionHash:str(req.brandExecution.brandExecutionHash),finalBoardHash:sha(req.finalBoard)};
}

async function main(){
  const chunks:Buffer[]=[]; for await(const chunk of process.stdin) chunks.push(Buffer.from(chunk)); const req=JSON.parse(Buffer.concat(chunks).toString("utf8")) as Request;
  if(req.schema!=="StudioP8ExplainerExecutionRequestV1") throw new Error("P8_EXPLAINER_REQUEST_SCHEMA_INVALID");
  if(req.operation!=="BUILD_INTERNAL_REVIEW_EVIDENCE") throw new Error(`P8_EXPLAINER_OPERATION_UNSUPPORTED:${String(req.operation)}`);
  if(!Array.isArray(req.authoredScenePlates)||req.authoredScenePlates.length!==arr(req.finalBoard?.beats).length) throw new Error("EXPLAINER_AUTHORED_PLATE_COVERAGE_REQUIRED");
  await mkdir(req.outputDirectory,{recursive:true});
  let reference:any=undefined;
  if(req.referenceMedia?.length){
    const assets=[] as Array<{assetId:string;mimeType:string;bytes:Uint8Array;name?:string}>;
    for(const m of req.referenceMedia){assets.push({assetId:m.assetId,mimeType:m.mimeType,bytes:new Uint8Array(await readFile(m.path)),name:m.name});}
    reference=await analyzeReferenceLanguage(assets);
  }
  const contracts=buildContracts(req,reference?.profile); const registry=loadExplainerRegistry(); const tokens=brandTokens(req);
  const scenes=createScenePlans({story:contracts.story,director:contracts.director,registry,brandTokens:tokens});
  // createScenePlans uses a deterministic technical shell for productionScopedArt;
  // exact motion/camera are generated from p8MotionActions/p8CameraAtom by motion-direction.ts.
  scenes.forEach((scene,i)=>{scene.visualConstruction=contracts.constructions[i];scene.visualDominance=contracts.constructions[i]!.dominanceMode;scene.styleProfile=contracts.constructions[i]!.styleProfile;scene.motionIntent=contracts.constructions[i]!.motionIntent;});
  // Rebuild motion after the exact construction is rebound so there is no selector-authored camera/action plan.
  const { attachMotionDirection } = await import("../src/studio/explainer-motion-v1/motion-direction");
  const exactScenes=attachMotionDirection(scenes.map(s=>({...s,motionDirection:undefined})));
  const composition=renderExplainerStoryboardPreview({story:contracts.story,director:contracts.director,scenes:exactScenes,registry,brandTokens:tokens,frozenAt:"2026-08-16T00:00:00.000Z"});
  const videoPath=path.join(req.outputDirectory,"p8-execution-body-v3-silent.mp4"); const framesDir=path.join(req.outputDirectory,"frames"); await mkdir(framesDir,{recursive:true});
  const rendered=await renderCompositionBundle("nexstudios_owned",composition.bundle,{aspectRatio:req.aspectRatio,resolution:"720p",fps:30,format:"mp4",outputPath:videoPath,inspectionFrameDirectory:framesDir,idempotencyKey:`p8-execution-v3-${req.productionId}`});
  if(rendered.status!=="completed"||!rendered.localOutputPath) throw new Error(`EXPLAINER_EXECUTION_BODY_RENDER_FAILED:${rendered.error||rendered.status}`);
  const fidelity=executionFidelity(req,contracts,exactScenes); if(fidelity.status!=="PASS") throw new Error(`EXPLAINER_EXECUTION_FIDELITY_FAILED:${fidelity.issues.join("|")}`);
  const planPath=path.join(req.outputDirectory,"p8-execution-body-v3-engine-plan.json");
  await writeFile(planPath,JSON.stringify({schema:"StudioP8ExplainerExecutionBodyV3PlanV1",authority:"NEXMIND_P8_ONLY",executionFidelityAuthority:"StudioFamilyExecutionFidelityV1",commercialJudgmentAuthority:false,productionArtAuthority:"PRODUCTION_SCOPED_AUTHORED_ART",duplicateTopLevelDirectors:false,referenceLanguageIndexingAid:reference?.profile??null,executionFidelity:fidelity,...contracts,scenePlans:exactScenes.map(s=>({id:s.id,visualConstruction:s.visualConstruction,motionDirection:s.motionDirection}))},null,2));
  process.stdout.write(JSON.stringify({schema:"StudioP8ExplainerRunnerResultV1",status:"RENDERED",videoPath:rendered.localOutputPath,framesDir,enginePlanPath:planPath,referenceLanguage:reference?.profile??null,metrics:rendered.metrics??null,executionFidelity:fidelity,authority:{topLevel:"NEXMIND_P8",execution:"EXPLAINER_EXECUTION_BODY_V3",commercialJudgment:false,legacyDirectorV3:false,retiredFamilyDirectorsReachable:false}}));
}
main().catch((error)=>{process.stderr.write(error instanceof Error?error.stack||error.message:String(error));process.exit(1);});
