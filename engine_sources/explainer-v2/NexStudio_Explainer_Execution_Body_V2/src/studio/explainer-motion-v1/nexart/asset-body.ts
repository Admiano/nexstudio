import type { ProductionRenderBinding, ReferenceLanguageProfile, VisualConstructionPlan, VisualEntity } from "../types";
import { CURATED_ILLUSTRATIONS } from "./curated-illustrations";

export type AssetRecord = { assetId:string; role:"character"|"object"|"environment"; sourcePath:string; tags:string[]; family:"ira-gradient"|"illlustrations-mit"; license:"MIT" };
const IRA_ASSETS: AssetRecord[] = [
  { assetId:"ira-character-boy", role:"character", sourcePath:"nexart-assets/ira/gradient/characters/Boy.svg", tags:["boy", "person", "human", "character"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-character-girl", role:"character", sourcePath:"nexart-assets/ira/gradient/characters/Girl.svg", tags:["girl", "person", "human", "character"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-character-man-simple", role:"character", sourcePath:"nexart-assets/ira/gradient/characters/Man simple.svg", tags:["man", "simple", "person", "human", "character"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-character-behind-woman-", role:"character", sourcePath:"nexart-assets/ira/gradient/characters/behind woman .svg", tags:["behind", "woman", "person", "human", "character"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-character-man-presenting", role:"character", sourcePath:"nexart-assets/ira/gradient/characters/man presenting.svg", tags:["man", "presenting", "person", "human", "character"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-character-man-walking", role:"character", sourcePath:"nexart-assets/ira/gradient/characters/man walking.svg", tags:["man", "walking", "person", "human", "character"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-character-man-with-a-hand-up", role:"character", sourcePath:"nexart-assets/ira/gradient/characters/man with a hand up.svg", tags:["man", "with", "a", "hand", "up", "person", "human", "character"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-character-man-with-documents", role:"character", sourcePath:"nexart-assets/ira/gradient/characters/man with documents.svg", tags:["man", "with", "documents", "person", "human", "character"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-character-man-with-ipad", role:"character", sourcePath:"nexart-assets/ira/gradient/characters/man with ipad.svg", tags:["man", "with", "ipad", "person", "human", "character"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-character-man-with-map", role:"character", sourcePath:"nexart-assets/ira/gradient/characters/man with map.svg", tags:["man", "with", "map", "person", "human", "character"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-character-man-with-paper", role:"character", sourcePath:"nexart-assets/ira/gradient/characters/man with paper.svg", tags:["man", "with", "paper", "person", "human", "character"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-character-man-working", role:"character", sourcePath:"nexart-assets/ira/gradient/characters/man working.svg", tags:["man", "working", "person", "human", "character"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-character-woman-check-phone", role:"character", sourcePath:"nexart-assets/ira/gradient/characters/woman check phone.svg", tags:["woman", "check", "phone", "person", "human", "character"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-character-woman-presenting", role:"character", sourcePath:"nexart-assets/ira/gradient/characters/woman presenting.svg", tags:["woman", "presenting", "person", "human", "character"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-character-woman-sitting", role:"character", sourcePath:"nexart-assets/ira/gradient/characters/woman sitting.svg", tags:["woman", "sitting", "person", "human", "character"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-character-woman-talking", role:"character", sourcePath:"nexart-assets/ira/gradient/characters/woman talking.svg", tags:["woman", "talking", "person", "human", "character"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-character-woman-walking", role:"character", sourcePath:"nexart-assets/ira/gradient/characters/woman walking.svg", tags:["woman", "walking", "person", "human", "character"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-character-women-handup", role:"character", sourcePath:"nexart-assets/ira/gradient/characters/women handup.svg", tags:["women", "handup", "person", "human", "character"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-character-women-sitting", role:"character", sourcePath:"nexart-assets/ira/gradient/characters/women sitting.svg", tags:["women", "sitting", "person", "human", "character"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-armchair", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/Armchair.svg", tags:["armchair"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-bag", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/Bag.svg", tags:["bag"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-books", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/Books.svg", tags:["books"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-calendar", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/Calendar.svg", tags:["calendar"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-computer", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/Computer.svg", tags:["computer"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-cup", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/Cup.svg", tags:["cup"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-flower", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/Flower.svg", tags:["flower"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-laptop", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/Laptop.svg", tags:["laptop"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-leaves", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/Leaves.svg", tags:["leaves"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-pig-with-coins", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/Pig with coins.svg", tags:["pig", "with", "coins"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-table", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/Table.svg", tags:["table"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-bank", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/bank.svg", tags:["bank"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-brush", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/brush.svg", tags:["brush"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-card", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/card.svg", tags:["card"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-chair", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/chair.svg", tags:["chair"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-coins", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/coins.svg", tags:["coins"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-inbox", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/inbox.svg", tags:["inbox"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-lamp", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/lamp.svg", tags:["lamp"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-lamp2", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/lamp2.svg", tags:["lamp2"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-motorcycle", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/motorcycle.svg", tags:["motorcycle"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-phone", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/phone.svg", tags:["phone"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-photos", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/photos.svg", tags:["photos"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-pin", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/pin.svg", tags:["pin"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-rocket", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/rocket.svg", tags:["rocket"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-tag", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/tag.svg", tags:["tag"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-tools", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/tools.svg", tags:["tools"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-object-wallet", role:"object", sourcePath:"nexart-assets/ira/gradient/objects/wallet.svg", tags:["wallet"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-environment-bg1", role:"environment", sourcePath:"nexart-assets/ira/backgrounds/bg1.svg", tags:["bg1", "environment", "scene", "background"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-environment-bg10", role:"environment", sourcePath:"nexart-assets/ira/backgrounds/bg10.svg", tags:["bg10", "environment", "scene", "background"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-environment-bg11", role:"environment", sourcePath:"nexart-assets/ira/backgrounds/bg11.svg", tags:["bg11", "environment", "scene", "background"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-environment-bg12", role:"environment", sourcePath:"nexart-assets/ira/backgrounds/bg12.svg", tags:["bg12", "environment", "scene", "background"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-environment-bg13", role:"environment", sourcePath:"nexart-assets/ira/backgrounds/bg13.svg", tags:["bg13", "environment", "scene", "background"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-environment-bg14", role:"environment", sourcePath:"nexart-assets/ira/backgrounds/bg14.svg", tags:["bg14", "environment", "scene", "background"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-environment-bg15", role:"environment", sourcePath:"nexart-assets/ira/backgrounds/bg15.svg", tags:["bg15", "environment", "scene", "background"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-environment-bg16", role:"environment", sourcePath:"nexart-assets/ira/backgrounds/bg16.svg", tags:["bg16", "environment", "scene", "background"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-environment-bg17", role:"environment", sourcePath:"nexart-assets/ira/backgrounds/bg17.svg", tags:["bg17", "environment", "scene", "background"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-environment-bg18", role:"environment", sourcePath:"nexart-assets/ira/backgrounds/bg18.svg", tags:["bg18", "environment", "scene", "background"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-environment-bg19", role:"environment", sourcePath:"nexart-assets/ira/backgrounds/bg19.svg", tags:["bg19", "environment", "scene", "background"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-environment-bg2", role:"environment", sourcePath:"nexart-assets/ira/backgrounds/bg2.svg", tags:["bg2", "environment", "scene", "background"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-environment-bg20", role:"environment", sourcePath:"nexart-assets/ira/backgrounds/bg20.svg", tags:["bg20", "environment", "scene", "background"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-environment-bg21", role:"environment", sourcePath:"nexart-assets/ira/backgrounds/bg21.svg", tags:["bg21", "environment", "scene", "background"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-environment-bg22", role:"environment", sourcePath:"nexart-assets/ira/backgrounds/bg22.svg", tags:["bg22", "environment", "scene", "background"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-environment-bg3", role:"environment", sourcePath:"nexart-assets/ira/backgrounds/bg3.svg", tags:["bg3", "environment", "scene", "background"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-environment-bg4", role:"environment", sourcePath:"nexart-assets/ira/backgrounds/bg4.svg", tags:["bg4", "environment", "scene", "background"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-environment-bg5", role:"environment", sourcePath:"nexart-assets/ira/backgrounds/bg5.svg", tags:["bg5", "environment", "scene", "background"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-environment-bg6", role:"environment", sourcePath:"nexart-assets/ira/backgrounds/bg6.svg", tags:["bg6", "environment", "scene", "background"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-environment-bg7", role:"environment", sourcePath:"nexart-assets/ira/backgrounds/bg7.svg", tags:["bg7", "environment", "scene", "background"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-environment-bg8", role:"environment", sourcePath:"nexart-assets/ira/backgrounds/bg8.svg", tags:["bg8", "environment", "scene", "background"], family:"ira-gradient", license:"MIT" },
  { assetId:"ira-environment-bg9", role:"environment", sourcePath:"nexart-assets/ira/backgrounds/bg9.svg", tags:["bg9", "environment", "scene", "background"], family:"ira-gradient", license:"MIT" },
];
const ASSETS: AssetRecord[] = [...IRA_ASSETS, ...CURATED_ILLUSTRATIONS];

const HUMAN = /(?:person|people|human|worker|staff|team|volunteer|customer|parent|child|student|teacher|doctor|nurse|manager|operator|creator|driver|courier|presenter|character|woman|man|girl|boy|adult)/i;
const STOP = new Set(["the","a","an","of","and","to","for","with","from","into","scene","object","result","source"]);
const CONCEPT_ALIASES: Record<string,string[]> = {
  smartphone:["phone","device"], mobile:["phone","device"], handset:["phone"],
  computer:["computer","pc","desktop","laptop","workstation","technology"], laptop:["laptop","computer","workstation","technology"],
  workspace:["office","workstation","desk","computer","printer","stationary"], workplace:["office","workstation","desk","computer"],
  office:["office","workstation","desk","computer","printer","stationary","bag"],
  finance:["finance","money","wallet","vault","bank","coins","card"], payment:["payment","wallet","money","card","finance"],
  parcel:["package","box","bag","delivery"], shipment:["package","box","delivery","transport"], delivery:["delivery","transport","courier","package","bag","route"],
  learning:["education","school","blackboard","books","notebook"], education:["education","school","blackboard","books","notebook"],
  healthcare:["health","medical","hospital","lab"], health:["health","medical","hospital","lab"],
  laboratory:["lab","science","experiment"], science:["science","lab","experiment"],
  home:["home","room","interior","living","bedroom"], residential:["home","room","interior","living"],
  hospitality:["hospitality","cafe","food","drink","kitchen"], meal:["food","kitchen","cafe"],
  urban:["city","road","street","transport"], travel:["travel","journey","transport","route"],
  document:["document","paper","notebook","printer","inbox"], paperwork:["document","paper","notebook","printer","inbox"],
  display:["computer","laptop","phone"], screen:["computer","laptop","phone"],
  seat:["chair","armchair","sofa","bench"], furniture:["table","chair","armchair","sofa","bench","lamp"],
  beverage:["drink","coffee","tea","cup"], drink:["drink","coffee","tea","cup"],
};
export function semanticTokens(value:string){
  const base=value.toLowerCase().replace(/[^a-z0-9]+/g," ").split(/\s+/).filter((token)=>token.length>1&&!STOP.has(token));
  const expanded:string[]=[];
  for(const token of base){expanded.push(token,...(CONCEPT_ALIASES[token]??[]));}
  return [...new Set(expanded)];
}
function tokens(value:string){ return semanticTokens(value); }
function hash(value:string){ let h=2166136261; for(const ch of value){h^=ch.charCodeAt(0);h=Math.imul(h,16777619)} return h>>>0; }
export function scoreAuthoredAsset(asset:AssetRecord, semantic:string){
  const direct=[...new Set(semantic.toLowerCase().replace(/[^a-z0-9]+/g," ").split(/\s+/).filter((token)=>token.length>1&&!STOP.has(token)))];
  const requested=tokens(semantic); let score=0;
  const primary=direct[0];
  for(const tag of asset.tags){
    if(primary&&tag===primary)score+=18;
    else if(direct.includes(tag))score+=10;
    else if(direct.some((token)=>tag.includes(token)||token.includes(tag)))score+=5;
    else if(requested.includes(tag))score+=3;
    else if(requested.some((token)=>tag.includes(token)||token.includes(tag)))score+=1;
  }
  return score;
}
export function authoredAssetBinding(asset:AssetRecord, kind:ProductionRenderBinding["kind"], performance=false):ProductionRenderBinding { return { kind, assetId:asset.assetId, sourcePath:asset.sourcePath, license:asset.license, family:asset.family, normalizedStyleFamily:"nexstudio-authored-cartoon-v1", semanticTags:asset.tags, ...(performance?{performanceAuthority:"NEXSTICK_V5_1" as const}:{}) }; }
export function rankAuthoredAssets(role:AssetRecord["role"], semantic:string){
  return ASSETS.filter((asset)=>asset.role===role).map((asset)=>({asset,score:scoreAuthoredAsset(asset,semantic)})).sort((a,b)=>b.score-a.score||a.asset.assetId.localeCompare(b.asset.assetId));
}
export function chooseAuthoredAsset(role:AssetRecord["role"], semantic:string, seed:string, allowZero=false){ const pool=ASSETS.filter((asset)=>asset.role===role); const ranked=rankAuthoredAssets(role,semantic); const best=ranked[0]; if(!best)return undefined; if(best.score<=0&&!allowZero)return undefined; if(best.score<=0)return pool[hash(seed)%pool.length]; return best.asset; }

function characterFamily(semantic:string):NonNullable<ProductionRenderBinding["characterSpec"]>["familyId"] {
  if(/\bgirl\b/i.test(semantic)) return "girl";
  if(/\bboy\b/i.test(semantic)) return "boy";
  if(/\bchild|kid|student\b/i.test(semantic)) return "neutral_child";
  if(/\bwoman|female|mother|girl\b/i.test(semantic)) return "adult_woman_average";
  if(/\bman|male|father|boy\b/i.test(semantic)) return "adult_man_average";
  return "neutral_adult";
}
function characterRoleTags(semantic:string):string[] {
  const map:[RegExp,string][]=[
    [/teacher/i,"teacher"],[/student/i,"student"],[/executive|manager|leader/i,"executive"],[/creator|designer|artist/i,"creator"],
    [/technician|engineer/i,"technician"],[/doctor|nurse|healthcare/i,"healthcare_worker"],[/builder|construction/i,"builder"],[/parent|mother|father/i,"parent"],
    [/child|kid|boy|girl/i,"child"],[/customer|client/i,"customer"],[/helper|volunteer|caregiver/i,"helper"],[/friend/i,"friend"],[/sales/i,"salesperson"],[/presenter|speaker/i,"presenter"],
  ];
  const found=map.filter(([pattern])=>pattern.test(semantic)).map(([,tag])=>tag);
  return found.length?[...new Set(found)]:["helper"];
}
function characterPersonality(semantic:string):NonNullable<ProductionRenderBinding["characterSpec"]>["personality"] {
  for(const value of ["calm","cheerful","confident","shy","energetic","serious","playful","authoritative","warm","reserved"] as const) if(new RegExp(`\\b${value}\\b`,`i`).test(semantic)) return value;
  return "calm";
}
function nexStickCharacterBinding(entity:VisualEntity, semantic:string):ProductionRenderBinding {
  return {
    kind:"CHARACTER_SKIN",
    assetId:`nexstick-v5.1:${entity.id}`,
    sourcePath:"nexstick-v5.1/cast/runtime/nexstick-authored-surface-v1.js",
    license:"INTERNAL",
    family:"nexstick-authored-surface-v1",
    normalizedStyleFamily:"nexstudio-authored-cartoon-v1",
    semanticTags:[...tokens(semantic),"character","authored-surface"],
    performanceAuthority:"NEXSTICK_V5_1",
    characterSpec:{ familyId:characterFamily(semantic), personality:characterPersonality(semantic), roleTags:characterRoleTags(semantic), skin:"NEXSTICK_AUTHORED_SURFACE_V1" },
  };
}

export function bindEntityToAuthoredBody(entity:VisualEntity, input:{ sceneId:string; referenceLanguage?:ReferenceLanguageProfile; authored:boolean }):VisualEntity {
  if(entity.renderBinding)return entity;
  const semantic=`${entity.semanticType} ${entity.label??""}`;
  if(entity.visualClass==="illustration"&&HUMAN.test(semantic)){
    return {...entity,renderBinding:nexStickCharacterBinding(entity,semantic)};
  }
  if(entity.type==="environment"||entity.visualClass==="environment"){
    const asset=chooseAuthoredAsset("environment",semantic,`${input.sceneId}:${entity.id}`,false);
    return asset?{...entity,renderBinding:authoredAssetBinding(asset,"ENVIRONMENT_SVG")}:entity;
  }
  if(input.authored&&(entity.type==="object"||entity.type==="container"||entity.visualClass==="transfer-object"||entity.visualClass==="document"||entity.visualClass==="attached-surface")){
    const asset=chooseAuthoredAsset("object",semantic,`${input.sceneId}:${entity.id}`,false);
    if(asset)return {...entity,renderBinding:authoredAssetBinding(asset,"PROP_SVG")};
    // Do not infer one of a finite set of canned object bodies from prose.
    // Exact authored asset/geometry or production-scoped authored art is required.
    return entity;
  }
  return entity;
}

export function authoredBindingBlockers(construction:VisualConstructionPlan, authored:boolean){
  if(!authored)return [];
  const blockers:string[]=[];
  const entities=[construction.heroEntity,...construction.supportingEntities];
  const state=construction.artDirection?.states?.find((candidate)=>candidate.id===construction.artDirection?.activeStateId);
  for(const entity of entities){
    const semantic=`${entity.semanticType} ${entity.label??""}`;
    const isCharacter=entity.visualClass==="illustration"&&HUMAN.test(semantic);
    const literalObject=entity.importance!=="annotation"&&(entity.type==="object"||entity.type==="container"||entity.visualClass==="transfer-object"||entity.visualClass==="document"||entity.visualClass==="attached-surface");
    const authoredEnvironment=entity.type==="environment"||entity.visualClass==="environment";
    const resolved={...(entity.geometry??{}),...(state?.entities?.[entity.id]??{})};
    const hasConstructedGeometry=Boolean(resolved.paths?.length||resolved.items?.length);
    if((isCharacter||literalObject||authoredEnvironment)&&!entity.renderBinding&&!hasConstructedGeometry) blockers.push(`AUTHORED_BODY_MISSING:${entity.id}:${entity.semanticType}`);
  }
  return blockers;
}

export const authoredAssetRegistry = ASSETS;
