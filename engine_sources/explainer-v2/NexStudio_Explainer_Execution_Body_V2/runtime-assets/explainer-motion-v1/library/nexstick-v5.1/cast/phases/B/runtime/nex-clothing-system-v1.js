(function(root){'use strict';
const VERSION='1.0.0-phase-b';
const CATEGORIES=['upper','lower','full_body','outerwear','footwear','optional_headwear','optional_accessory'];
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const dist=(a,b)=>Math.hypot((a[0]-b[0]),(a[1]-b[1]),(a[2]-b[2]));
const mix=(a,b,t)=>a.map((v,i)=>v+(b[i]-v)*t);
const avg=(a,b)=>mix(a,b,.5);
const clone=x=>JSON.parse(JSON.stringify(x));
const stable=x=>JSON.stringify(x,Object.keys(x).sort());
const FAMILIES=['adult_man','adult_woman','boy','girl','diminutive_adult','diminutive_child','elder_adult','plus_size_adult'];

// These are LAB-ONLY metric proxies. Phase A replaces them with measured BodyPreset metrics.
// Diminutive families deliberately change ratios/widths independently instead of uniform adult scaling.
const LAB_BODY_METRICS={
 adult_man:{family:'adult_man',shoulderHalfWidth:.205,chestHalfWidth:.17,waistHalfWidth:.145,hipHalfWidth:.14,upperArmRadius:.038,forearmRadius:.032,thighRadius:.058,calfRadius:.046,footRadius:.042,torsoLengthScale:1,limbWidthScale:1},
 adult_woman:{family:'adult_woman',shoulderHalfWidth:.185,chestHalfWidth:.16,waistHalfWidth:.132,hipHalfWidth:.165,upperArmRadius:.035,forearmRadius:.03,thighRadius:.061,calfRadius:.044,footRadius:.039,torsoLengthScale:.98,limbWidthScale:.96},
 boy:{family:'boy',shoulderHalfWidth:.16,chestHalfWidth:.135,waistHalfWidth:.12,hipHalfWidth:.125,upperArmRadius:.031,forearmRadius:.026,thighRadius:.048,calfRadius:.038,footRadius:.036,torsoLengthScale:.9,limbWidthScale:.86},
 girl:{family:'girl',shoulderHalfWidth:.155,chestHalfWidth:.132,waistHalfWidth:.116,hipHalfWidth:.13,upperArmRadius:.03,forearmRadius:.025,thighRadius:.048,calfRadius:.037,footRadius:.035,torsoLengthScale:.9,limbWidthScale:.85},
 diminutive_adult:{family:'diminutive_adult',shoulderHalfWidth:.175,chestHalfWidth:.154,waistHalfWidth:.14,hipHalfWidth:.15,upperArmRadius:.036,forearmRadius:.031,thighRadius:.056,calfRadius:.044,footRadius:.038,torsoLengthScale:1.10,limbWidthScale:1.02,nonUniformFit:true},
 diminutive_child:{family:'diminutive_child',shoulderHalfWidth:.145,chestHalfWidth:.128,waistHalfWidth:.116,hipHalfWidth:.122,upperArmRadius:.029,forearmRadius:.025,thighRadius:.045,calfRadius:.036,footRadius:.034,torsoLengthScale:1.13,limbWidthScale:.9,nonUniformFit:true},
 elder_adult:{family:'elder_adult',shoulderHalfWidth:.19,chestHalfWidth:.168,waistHalfWidth:.15,hipHalfWidth:.155,upperArmRadius:.037,forearmRadius:.032,thighRadius:.059,calfRadius:.046,footRadius:.041,torsoLengthScale:.98,limbWidthScale:1.0},
 plus_size_adult:{family:'plus_size_adult',shoulderHalfWidth:.225,chestHalfWidth:.215,waistHalfWidth:.205,hipHalfWidth:.225,upperArmRadius:.052,forearmRadius:.043,thighRadius:.078,calfRadius:.059,footRadius:.046,torsoLengthScale:1,limbWidthScale:1.28}
};

function validateBody(body){
 if(!body||!body.family||!body.metrics)throw new Error('BodyPreset metrics required from Phase A');
 const needed=['shoulderHalfWidth','chestHalfWidth','waistHalfWidth','hipHalfWidth','upperArmRadius','forearmRadius','thighRadius','calfRadius','footRadius'];
 for(const k of needed)if(!(body.metrics[k]>0))throw new Error('BodyPreset metric missing: '+k);
 return body;
}
function validateItem(item){
 const req=['id','category','compatibleBodyFamilies','anchorBindRegions','silhouetteRules','layerPriority','occlusionRules','motionSafeExpansion','minimumClearances','styleTags','roleTags','ageCompatibility','genderNeutralCompatible'];
 for(const k of req)if(item[k]===undefined)throw new Error('clothing item '+(item.id||'?')+' missing '+k);
 if(!CATEGORIES.includes(item.category))throw new Error('bad clothing category '+item.category);
 return true;
}
function validateLibrary(lib){
 const ids=new Set(); for(const it of lib.items){validateItem(it);if(ids.has(it.id))throw new Error('duplicate item '+it.id);ids.add(it.id)}
 for(const p of lib.presets){if(!p.id||!p.items)throw new Error('bad preset'); for(const id of Object.values(p.items).filter(Boolean))if(!ids.has(id))throw new Error('preset '+p.id+' missing item '+id)}
 return true;
}
function bodyPreset(family){const metrics=clone(LAB_BODY_METRICS[family]);if(!metrics)throw new Error('unknown lab family '+family);return {id:'lab_'+family,family,metrics,source:'phase-b-lab-proxy-only'}}
function itemMap(lib){return Object.fromEntries(lib.items.map(x=>[x.id,x]))}
function compatible(item,body){return item.compatibleBodyFamilies.includes('*')||item.compatibleBodyFamilies.includes(body.family)||item.compatibleBodyFamilies.includes('future_adult')&&['elder_adult','plus_size_adult'].includes(body.family)}
function bendAngle(a,b,c){const ab=a.map((v,i)=>v-b[i]),cb=c.map((v,i)=>v-b[i]);const da=Math.hypot(...ab),dc=Math.hypot(...cb);if(!da||!dc)return 0;const d=clamp(ab.reduce((s,v,i)=>s+v*cb[i],0)/(da*dc),-1,1);return Math.acos(d)}
function posture(p){
 const knee=Math.max(bendAngle(p.hip_l,p.knee_l,p.ankle_l),bendAngle(p.hip_r,p.knee_r,p.ankle_r));
 const elbow=Math.max(bendAngle(p.shoulder_l,p.elbow_l,p.wrist_l),bendAngle(p.shoulder_r,p.elbow_r,p.wrist_r));
 const hipToKneeY=Math.min(p.hip_l[1]-p.knee_l[1],p.hip_r[1]-p.knee_r[1]);
 const seated=(knee<2.25 && hipToKneeY<.16) || (p.pelvis[1]<.70 && hipToKneeY<.22);
 const low=p.pelvis[1]<.72 || Math.min(p.wrist_l[1],p.wrist_r[1])<.45;
 const highMotion=elbow<1.35 || knee<1.45;
 return {kneeAngle:knee,elbowAngle:elbow,seated,low,highMotion};
}
function envelopeSegment(id,a,b,r,bodyR,clearance,layer,kind,meta={}){return {id,type:'segment_envelope',kind,a:a.slice(),b:b.slice(),radius:r,bodyRadius:bodyR,clearance,layer,...meta}}
function fitUpper(item,p,b,m,post,outer=false){
 const c=item.minimumClearances.torso||.012, exp=item.motionSafeExpansion.torso||.018, bend=post.highMotion?(item.motionSafeExpansion.highMotion||.012):0;
 const top=Math.max(m.shoulderHalfWidth,m.chestHalfWidth)+c+exp+bend+(outer?.010:0), waist=m.waistHalfWidth+c+exp*.55, hem=Math.max(m.hipHalfWidth,m.waistHalfWidth)+c+exp;
 const chest=p.chest, pelvis=p.pelvis;
 const sleeveClear=item.minimumClearances.arm||.008, sleeveExp=item.motionSafeExpansion.arm||.012;
 const sleeveRadiusUpper=m.upperArmRadius+sleeveClear+sleeveExp+(post.highMotion?.006:0)+(outer?.008:0);
 const sleeveRadiusFore=m.forearmRadius+sleeveClear+sleeveExp+(post.highMotion?.005:0)+(outer?.007:0);
 const sleeve=item.silhouetteRules.sleeve||'short';
 const regions=[{id:item.id+':torso',type:'torso_envelope',kind:outer?'outerwear':'upper',chest:chest.slice(),pelvis:pelvis.slice(),topHalfWidth:top,waistHalfWidth:waist,hemHalfWidth:hem,bodyTopHalfWidth:m.shoulderHalfWidth,bodyWaistHalfWidth:m.waistHalfWidth,bodyHemHalfWidth:m.hipHalfWidth,clearance:c,layer:item.layerPriority}];
 for(const s of ['l','r']){
   const sh=p['shoulder_'+s],el=p['elbow_'+s],wr=p['wrist_'+s];
   const shortEnd=mix(sh,el,.48);
   if(sleeve==='none')continue;
   if(sleeve==='short')regions.push(envelopeSegment(item.id+':upperarm_'+s,sh,shortEnd,sleeveRadiusUpper,m.upperArmRadius,sleeveClear,item.layerPriority,'sleeve',{side:s}));
   else {regions.push(envelopeSegment(item.id+':upperarm_'+s,sh,el,sleeveRadiusUpper,m.upperArmRadius,sleeveClear,item.layerPriority,'sleeve',{side:s})); regions.push(envelopeSegment(item.id+':forearm_'+s,el,wr,sleeveRadiusFore,m.forearmRadius,sleeveClear,item.layerPriority,'sleeve',{side:s}));}
 }
 return regions;
}
function fitTrousers(item,p,b,m,post){
 const c=item.minimumClearances.leg||.009,exp=item.motionSafeExpansion.leg||.012; const hi=post.highMotion?(item.motionSafeExpansion.highMotion||.010):0;
 const thigh=m.thighRadius+c+exp+hi, calf=m.calfRadius+c+exp*.7+hi*.5, regions=[];
 for(const s of ['l','r']){regions.push(envelopeSegment(item.id+':thigh_'+s,p['hip_'+s],p['knee_'+s],thigh,m.thighRadius,c,item.layerPriority,'trouser',{side:s}));regions.push(envelopeSegment(item.id+':calf_'+s,p['knee_'+s],p['ankle_'+s],calf,m.calfRadius,c,item.layerPriority,'trouser',{side:s}));}
 regions.push({id:item.id+':waist',type:'waist_band',center:p.pelvis.slice(),halfWidth:m.hipHalfWidth+c+exp,height:.055,layer:item.layerPriority,clearance:c}); return regions;
}
function fitSkirt(item,p,b,m,post,fullBody=false){
 const c=item.minimumClearances.leg||.012,exp=item.motionSafeExpansion.leg||.028;
 const hipHalf=m.hipHalfWidth+c+(item.motionSafeExpansion.torso||.015);
 const kneeSpread=Math.max(Math.abs(p.knee_l[0]-p.pelvis[0]),Math.abs(p.knee_r[0]-p.pelvis[0]))+m.thighRadius+c;
 const motionNeed=Math.max(hipHalf,kneeSpread+exp+(post.seated?.055:0)+(post.highMotion?.035:0));
 const targetLen=item.silhouetteRules.length==='long'?.62:item.silhouetteRules.length==='midi'?.46:.34;
 let hemY=p.pelvis[1]-targetLen; if(post.seated)hemY=Math.min(p.knee_l[1],p.knee_r[1])-.04;
 return [{id:item.id+':skirt',type:'skirt_envelope',kind:fullBody?'dress_skirt':'skirt',centerTop:p.pelvis.slice(),hipHalfWidth:hipHalf,hemHalfWidth:motionNeed,hemY,clearance:c,legSpreadNeed:kneeSpread,layer:item.layerPriority,seatedExpansion:post.seated,highMotionExpansion:post.highMotion,split:item.silhouetteRules.split||'adaptive'}];
}
function fitFootwear(item,p,b,m,post){const c=item.minimumClearances.foot||.006,exp=item.motionSafeExpansion.foot||.008,r=m.footRadius+c+exp,regions=[];for(const s of ['l','r'])regions.push(envelopeSegment(item.id+':shoe_'+s,p['ankle_'+s],p['toe_'+s],r,m.footRadius,c,item.layerPriority,'footwear',{side:s,sole:item.silhouetteRules.sole||'flat'}));return regions}
function fitHeadwear(item,p,b,m){const c=item.minimumClearances.head||.01,exp=item.motionSafeExpansion.head||.01;return [{id:item.id+':headwear',type:'headwear',center:p.head.slice(),radius:.105+c+exp,layer:item.layerPriority,style:item.silhouetteRules.style||'cap'}]}
function fitAccessory(item,p,b,m){return [{id:item.id+':accessory',type:'accessory',center:p.chest.slice(),anchor:'chest',layer:item.layerPriority,style:item.silhouetteRules.style||'badge'}]}
function fitItem(item,p,b,post){const m=b.metrics;if(item.category==='upper')return fitUpper(item,p,b,m,post,false);if(item.category==='outerwear')return fitUpper(item,p,b,m,post,true);if(item.category==='lower')return item.silhouetteRules.form==='skirt'?fitSkirt(item,p,b,m,post,false):fitTrousers(item,p,b,m,post);if(item.category==='full_body'){const top=fitUpper(item,p,b,m,post,false);return top.concat(fitSkirt(item,p,b,m,post,true))}if(item.category==='footwear')return fitFootwear(item,p,b,m,post);if(item.category==='optional_headwear')return fitHeadwear(item,p,b,m);if(item.category==='optional_accessory')return fitAccessory(item,p,b,m);return []}
function fit({pose3d,body,preset,library,palette={}}){
 if(!pose3d)throw new Error('canonical V4 pose3d required');validateBody(body);validateLibrary(library);const map=itemMap(library),post=posture(pose3d),regions=[],used=[];
 for(const cat of CATEGORIES){const id=preset.items[cat];if(!id)continue;const item=map[id];if(!item)throw new Error('unknown item '+id);if(!compatible(item,body))throw new Error(item.id+' incompatible with '+body.family);regions.push(...fitItem(item,pose3d,body,post));used.push(item)}
 regions.sort((a,b)=>(a.layer||0)-(b.layer||0)||a.id.localeCompare(b.id));
 return {version:VERSION,bodyId:body.id,bodyFamily:body.family,presetId:preset.id,posture:post,regions,items:used.map(x=>x.id),palette:clone(palette),sourcePose:'NexPerformance V4 pose3d',drivesMotion:false,createsSkeleton:false};
}
function qaFit(fitResult){
 const issues=[];let minClear=Infinity,maxBind=0;
 for(const r of fitResult.regions){
  if(r.type==='segment_envelope'){const clear=r.radius-r.bodyRadius;minClear=Math.min(minClear,clear);if(clear+1e-9<r.clearance)issues.push({code:'BODY_CLOTHING_PENETRATION_PROXY',region:r.id,clear});if(!r.a||!r.b)issues.push({code:'DETACHED_BIND',region:r.id});}
  if(r.type==='torso_envelope'){for(const [cloth,body] of [['topHalfWidth','bodyTopHalfWidth'],['waistHalfWidth','bodyWaistHalfWidth'],['hemHalfWidth','bodyHemHalfWidth']]){const clear=r[cloth]-r[body];minClear=Math.min(minClear,clear);if(clear+1e-9<r.clearance)issues.push({code:'TORSO_PENETRATION_PROXY',region:r.id,at:cloth,clear});}}
  if(r.type==='skirt_envelope'){const clear=r.hemHalfWidth-r.legSpreadNeed;minClear=Math.min(minClear,clear);if(clear+1e-9<r.clearance)issues.push({code:'SKIRT_LEG_CATASTROPHIC_INTERSECTION_RISK',region:r.id,clear});if(fitResult.posture.seated&&!r.seatedExpansion)issues.push({code:'SKIRT_MISSING_SEATED_EXPANSION',region:r.id});}
 }
 return {pass:issues.length===0,issues,minClearance:isFinite(minClear)?minClear:null,maxBindError:maxBind};
}
function deterministicCompare(a,b){return JSON.stringify(a)===JSON.stringify(b)}

function project(pt,view){const s=view.scale||270, ox=view.ox||160, oy=view.oy||500; return {x:ox+pt[0]*s,y:oy-pt[1]*s,z:pt[2]}}
function pathStroke(a,b,r,view,cls,extra=''){const A=project(a,view),B=project(b,view);return `<path class="${cls}" d="M ${A.x.toFixed(2)} ${A.y.toFixed(2)} L ${B.x.toFixed(2)} ${B.y.toFixed(2)}" stroke-width="${(2*r*view.scale).toFixed(2)}" ${extra}/>`}
function renderSVG(pose,fitResult,opts={}){
 const w=opts.width||320,h=opts.height||540,view={scale:opts.scale||270,ox:opts.ox||w/2,oy:opts.oy||h-22};const pal={ink:'#17191d',skin:'#f3d5bd',upper:'#5b7cfa',lower:'#28344f',outer:'#20242c',shoe:'#16181c',accent:'#f0aa3c',...fitResult.palette,...opts.palette};
 let body='';const segs=[['shoulder_l','elbow_l'],['elbow_l','wrist_l'],['shoulder_r','elbow_r'],['elbow_r','wrist_r'],['hip_l','knee_l'],['knee_l','ankle_l'],['hip_r','knee_r'],['knee_r','ankle_r'],['chest','pelvis'],['neck','head'],['shoulder_l','shoulder_r'],['hip_l','hip_r']];for(const [a,b] of segs)body+=pathStroke(pose[a],pose[b],.018,view,'bodyline');const hp=project(pose.head,view);body+=`<circle class="head" cx="${hp.x}" cy="${hp.y}" r="${(.105*view.scale).toFixed(1)}"/>`;
 let cloth='';for(const r of fitResult.regions){
  if(r.type==='segment_envelope'){let key=r.kind==='trouser'?'lower':r.kind==='footwear'?'shoe':r.kind==='sleeve'?'upper':'upper';if(r.id.includes('blazer')||r.id.includes('hoodie')||r.kind==='outerwear')key='outer';cloth+=pathStroke(r.a,r.b,r.radius,view,'cloth '+key);}
  else if(r.type==='torso_envelope'){const c=project(r.chest,view),pel=project(r.pelvis,view),th=r.topHalfWidth*view.scale,wh=r.waistHalfWidth*view.scale,hh=r.hemHalfWidth*view.scale;const midY=(c.y+pel.y)/2;const key=r.kind==='outerwear'?'outer':'upper';cloth+=`<path class="cloth ${key}" d="M ${(c.x-th).toFixed(1)} ${c.y.toFixed(1)} Q ${(c.x-wh).toFixed(1)} ${midY.toFixed(1)} ${(pel.x-hh).toFixed(1)} ${pel.y.toFixed(1)} L ${(pel.x+hh).toFixed(1)} ${pel.y.toFixed(1)} Q ${(c.x+wh).toFixed(1)} ${midY.toFixed(1)} ${(c.x+th).toFixed(1)} ${c.y.toFixed(1)} Z"/>`;}
  else if(r.type==='skirt_envelope'){const t=project(r.centerTop,view),hw=r.hipHalfWidth*view.scale,bw=r.hemHalfWidth*view.scale,hy=view.oy-r.hemY*view.scale;cloth+=`<path class="cloth lower" d="M ${(t.x-hw).toFixed(1)} ${t.y.toFixed(1)} L ${(t.x-bw).toFixed(1)} ${hy.toFixed(1)} L ${(t.x+bw).toFixed(1)} ${hy.toFixed(1)} L ${(t.x+hw).toFixed(1)} ${t.y.toFixed(1)} Z"/>`; if(r.split!=='none')cloth+=`<path class="seam" d="M ${t.x.toFixed(1)} ${(hy-20).toFixed(1)} L ${t.x.toFixed(1)} ${hy.toFixed(1)}"/>`;}
  else if(r.type==='waist_band'){const c=project(r.center,view);cloth+=`<path class="seam" d="M ${(c.x-r.halfWidth*view.scale).toFixed(1)} ${c.y.toFixed(1)} L ${(c.x+r.halfWidth*view.scale).toFixed(1)} ${c.y.toFixed(1)}"/>`;}
  else if(r.type==='headwear'){const c=project(r.center,view),rr=r.radius*view.scale;cloth+=`<path class="cloth outer" d="M ${(c.x-rr).toFixed(1)} ${(c.y-rr*.45).toFixed(1)} Q ${c.x.toFixed(1)} ${(c.y-rr*1.05).toFixed(1)} ${(c.x+rr).toFixed(1)} ${(c.y-rr*.45).toFixed(1)} L ${(c.x+rr*1.2).toFixed(1)} ${(c.y-rr*.38).toFixed(1)}"/>`;}
  else if(r.type==='accessory'){const c=project(r.center,view);cloth+=`<circle class="accent" cx="${(c.x+28).toFixed(1)}" cy="${(c.y+14).toFixed(1)}" r="7"/>`;}
 }
 // Body goes first; clothing is an overlay. Head is redrawn last so collars never swallow it.
 return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" data-nex-clothing="${VERSION}"><style>.bodyline{fill:none;stroke:${pal.skin};stroke-linecap:round;stroke-linejoin:round}.head{fill:${pal.skin};stroke:${pal.ink};stroke-width:3}.cloth{fill:none;stroke-linecap:round;stroke-linejoin:round}.cloth.upper{fill:${pal.upper};stroke:${pal.upper}}.cloth.lower{fill:${pal.lower};stroke:${pal.lower}}.cloth.outer{fill:${pal.outer};stroke:${pal.outer}}.cloth.shoe{fill:${pal.shoe};stroke:${pal.shoe}}path.cloth.upper,path.cloth.lower,path.cloth.outer,path.cloth.shoe{stroke-linejoin:round}.seam{fill:none;stroke:${pal.ink};stroke-width:2;opacity:.28}.accent{fill:${pal.accent};stroke:${pal.ink};stroke-width:2}</style><g>${body}${cloth}<circle class="head" cx="${hp.x}" cy="${hp.y}" r="${(.105*view.scale).toFixed(1)}"/></g></svg>`;
}
root.NexClothingSystemV1={version:VERSION,categories:CATEGORIES,families:FAMILIES,labBodyMetrics:LAB_BODY_METRICS,bodyPreset,validateItem,validateLibrary,fit,qaFit,deterministicCompare,renderSVG,posture};
})(typeof window!=='undefined'?window:globalThis);
