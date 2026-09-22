/* Domain-neutral deterministic visual grammar executor. Topic semantics arrive
 * entirely through validated entity/relationship plans. */
window.NexVisualConstructions=(()=>{
 const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
 const primitiveVisualInventory=['circle','ellipse','organic-blob','seed','line','curved-line','arrow','dotted-path','branch','stem','leaf','droplet','sun','sun-ray','cloud','soil-layer','ground-line','label','node','container','particle','glow','connector','cutout-mask','document','token','block','tool'];
 const constructionGrammarInventory=['sequential-transformation','sequential-growth','directional-split','branching','converging-inputs','diverging-outputs','linear-flow','network-flow','cycle','layered-cutaway','layer-cutaway','assembly','comparison','cause-and-effect','reveal','transformation','journey-path','orbit','accumulation','hero-transform','freeform'];
 const colors={ink:'#121212',muted:'#665f55',teal:'#315b54',green:'#78ad63',ochre:'#f2b134',coral:'#e86f51',paper:'#fffdf7',blue:'#75a9c8',soil:'#9b6e4c',violet:'#754be8'};
 const line=(x1,y1,x2,y2,stroke=colors.teal,width=8,extra='')=>`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${stroke}" stroke-width="${width}" stroke-linecap="round" ${extra}/>`;
 const path=(d,stroke=colors.teal,width=8,fill='none',extra='')=>`<path d="${d}" stroke="${stroke}" stroke-width="${width}" fill="${fill}" stroke-linecap="round" stroke-linejoin="round" ${extra}/>`;
 const text=(value,x,y,size=22,fill=colors.ink,anchor='middle',weight=800)=>`<text x="${x}" y="${y}" font-family="Arial,Helvetica,sans-serif" font-size="${size}" font-weight="${weight}" fill="${fill}" text-anchor="${anchor}" letter-spacing="1">${esc(value)}</text>`;
  const anchorMarkup=(x,y,scale=1,custom={})=>{const a={center:{x,y},top:{x,y:y-64*scale},bottom:{x,y:y+64*scale},left:{x:x-64*scale,y},right:{x:x+64*scale,y},entry:{x:x-96*scale,y},exit:{x:x+96*scale,y},growthOrigin:{x,y},branchOrigin:{x,y},attachment:{x,y},focus:{x,y},...custom};return Object.entries(a).map(([name,point])=>`data-anchor-${name.replace(/[A-Z]/g,m=>`-${m.toLowerCase()}`)}="${point.x},${point.y}"`).join(' ')};
 const continuityAttrs=entity=>entity.continuity?` data-continuity-entity="true" data-continuity-id="${esc(entity.continuityId||'continuity-hero')}"`:'';
 const heroAttrs=entity=>entity.continuityHero?` data-continuity-hero="${esc(entity.continuityId||'continuity-hero')}"`:'';
 const group=(entity,content,extra='',anchors='')=>`<g class="vc-paper-entity" data-paper-material="cutout" filter="url(#vc-paper-cutout)" data-entity-id="${esc(entity.id)}" data-visual-class="${esc(entity.visualClass||'geometric-object')}" data-representation="${esc(entity.representation||'circle')}" data-motion-capabilities="${esc((entity.capabilities||[]).join(' '))}"${continuityAttrs(entity)}${heroAttrs(entity)} ${anchors} ${extra}>${content}</g>`;
 const arrow=(x1,y1,x2,y2,stroke=colors.coral,width=7)=>line(x1,y1,x2,y2,stroke,width,'marker-end="url(#vc-arrow)" data-motion-piece="flow-path"');
 const leaf=(cx,cy,rx=92,ry=34,rot=0,continuityRole='',pivot)=>{const d=`M${cx-rx} ${cy} C${cx-rx*.52} ${cy-ry*1.08} ${cx+rx*.48} ${cy-ry*.98} ${cx+rx} ${cy} C${cx+rx*.42} ${cy+ry*1.03} ${cx-rx*.46} ${cy+ry*.94} ${cx-rx} ${cy}Z`;const edge=`M${cx-rx+2.8} ${cy+3.5} C${cx-rx*.52+2.8} ${cy-ry*1.08+3.5} ${cx+rx*.48+2.8} ${cy-ry*.98+3.5} ${cx+rx+2.8} ${cy+3.5} C${cx+rx*.42+2.8} ${cy+ry*1.03+3.5} ${cx-rx*.46+2.8} ${cy+ry*.94+3.5} ${cx-rx+2.8} ${cy+3.5}Z`;return `<g data-motion-piece="leaf"${continuityRole?` data-continuity-role="${esc(continuityRole)}"`:''}${pivot?` data-pivot-x="${Number(pivot.x)}" data-pivot-y="${Number(pivot.y)}"`:''} transform="rotate(${rot} ${cx} ${cy})"><path d="${edge}" fill="#152522" opacity=".13" data-paper-underlay="true"/><path d="${d}" fill="${colors.green}" stroke="${colors.teal}" stroke-width="6"/><path d="M${cx-rx*.78} ${cy+ry*.08} Q${cx} ${cy-ry*.08} ${cx+rx*.78} ${cy}" fill="none" stroke="${colors.teal}" stroke-width="3" opacity=".78"/><path d="M${cx-rx*.42} ${cy-ry*.15} Q${cx-rx*.1} ${cy-ry*.34} ${cx+rx*.22} ${cy-ry*.2}" fill="none" stroke="#fffdf7" stroke-width="3" opacity=".24"/></g>`};
 const droplet=(cx,cy,r=17)=>`<path data-motion-piece="droplet" d="M${cx} ${cy-r*1.8} C${cx-r*1.5} ${cy-r*.1} ${cx-r*1.35} ${cy+r} ${cx} ${cy+r} C${cx+r*1.35} ${cy+r} ${cx+r*1.5} ${cy-r*.1} ${cx} ${cy-r*1.8}Z" fill="${colors.blue}" stroke="${colors.teal}" stroke-width="5"/>`;
 const sun=(cx=760,cy=92)=>{let rays='';for(let i=0;i<8;i++){const a=i*Math.PI/4;rays+=line(cx+Math.cos(a)*62,cy+Math.sin(a)*62,cx+Math.cos(a)*86,cy+Math.sin(a)*86,colors.ochre,6)}return `<circle cx="${cx}" cy="${cy}" r="42" fill="${colors.ochre}" stroke="${colors.ink}" stroke-width="6"/>${rays}`};
  const stateFor=plan=>plan.artDirection?.states?.find(state=>state.id===plan.artDirection.activeStateId);
  const geometryFor=(plan,entity)=>({...entity.geometry,...(stateFor(plan)?.entities?.[entity.id]||{})});
  const soil=entity=>{const g=entity.__geometry||{},ground=Number(g.y??382),bottom=Math.min(560,Number(g.height?ground+g.height:560));const top=`M32 ${ground+2} C112 ${ground-7} 186 ${ground+5} 266 ${ground-3} C356 ${ground-12} 438 ${ground+7} 526 ${ground-2} C626 ${ground-11} 724 ${ground+5} 868 ${ground-4}`;return group(entity,`<path d="${top} L868 ${bottom} L32 ${bottom}Z" fill="${g.fill||'#e8ddcc'}" opacity="${g.opacity??.96}"/><path d="M32 ${ground+22} C210 ${ground+12} 350 ${ground+28} 520 ${ground+18} C680 ${ground+7} 780 ${ground+28} 868 ${ground+16} L868 ${bottom} L32 ${bottom}Z" fill="#d8c4aa" opacity=".38"/><path d="${top}" fill="none" stroke="${g.stroke||colors.muted}" stroke-width="${g.strokeWidth||5}" stroke-linecap="round"/>`)};
  const customPaths=(geometry,fallback)=>{const list=Array.isArray(geometry?.paths)&&geometry.paths.length?geometry.paths:fallback;return list.map((spec,index)=>{const normalized=typeof spec==='string'?{d:spec,stroke:colors.coral,strokeWidth:Math.max(4,Number(geometry?.strokeWidth||7)),fill:'none',role:index?'branch':'primary-root',opacity:1}:spec;const stroke=normalized.stroke||geometry?.stroke||colors.teal,width=Number(normalized.strokeWidth||geometry?.strokeWidth||8),fill=normalized.fill||'none',role=normalized.role||(index?'branch':'primary-root'),opacity=normalized.opacity??1;const paperEdge=fill==='none'?`<path d="${normalized.d}" stroke="#171717" stroke-width="${width+4}" fill="none" stroke-linecap="round" stroke-linejoin="round" opacity=".10" transform="translate(2.6 3.3)" data-paper-underlay="true"/>`:'';return `${paperEdge}${path(normalized.d,stroke,width,fill,`data-motion-piece="${role}"${normalized.continuityRole?` data-continuity-role="${esc(normalized.continuityRole)}"`:''} opacity="${opacity}"`)}`}).join('')};
  const root=(x=450,y=380,scale=1,branches=true,geometry={})=>customPaths(geometry,[`M${x} ${y} C${x-8*scale} ${y+58*scale} ${x-65*scale} ${y+94*scale} ${x-94*scale} ${y+155*scale}`,`M${x} ${y+38*scale} C${x+12*scale} ${y+80*scale} ${x+60*scale} ${y+115*scale} ${x+78*scale} ${y+170*scale}`,...(branches?[`M${x-38*scale} ${y+88*scale} C${x-70*scale} ${y+112*scale} ${x-105*scale} ${y+118*scale} ${x-130*scale} ${y+150*scale}`,`M${x+42*scale} ${y+110*scale} C${x+75*scale} ${y+130*scale} ${x+112*scale} ${y+138*scale} ${x+134*scale} ${y+170*scale}`]:[])]);

  function positions(plan){
   const all=[plan.heroEntity,...(plan.supportingEntities||[])],map=new Map(),grammar=plan.spatialGrammar,geometry=entity=>geometryFor(plan,entity);
   if(grammar==='linear-flow'||grammar==='sequential-transformation'||grammar==='cause-and-effect'||grammar==='journey-path') all.forEach((entity,i)=>map.set(entity.id,{x:125+i*(650/Math.max(1,all.length-1)),y:280}));
   else if(grammar==='branching'||grammar==='diverging-outputs'){map.set(plan.heroEntity.id,{x:450,y:280});const supports=all.slice(1);supports.forEach((entity,i)=>{const angle=(-Math.PI*.82)+(i/(Math.max(1,supports.length-1)))*Math.PI*.64;map.set(entity.id,{x:450+Math.cos(angle)*245,y:285+Math.sin(angle)*160})})}
   else if(grammar==='converging-inputs'){map.set(plan.heroEntity.id,{x:500,y:270});const supports=all.slice(1);supports.forEach((entity,i)=>map.set(entity.id,{x:i%2?760:185,y:120+Math.floor(i/2)*165}))}
   else if(grammar==='directional-split'){map.set(plan.heroEntity.id,{x:450,y:350});all.slice(1).forEach((entity)=>{const relation=(plan.relationships||[]).find(item=>item.from===entity.id);map.set(entity.id,{x:450,y:relation?.direction==='down'?415:relation?.direction==='up'?220:300})})}
   else if(grammar==='cycle'){all.forEach((entity,i)=>{const angle=-Math.PI/2+i*Math.PI*2/all.length;map.set(entity.id,{x:450+Math.cos(angle)*210,y:280+Math.sin(angle)*170})})}
   else {map.set(plan.heroEntity.id,{x:450,y:300});all.slice(1).forEach((entity,i)=>map.set(entity.id,{x:180+(i%3)*280,y:i<3?155:430}))}

   const relationList=plan.relationships||[],hero=map.get(plan.heroEntity.id)||{x:450,y:300};
   // Fallback placement is relationship/type based only. Topic-specific geometry
   // is supplied by the resolved ArtDirection state and overrides these values.
   all.forEach((entity,index)=>{
    if(entity.type==='environment')map.set(entity.id,{x:450,y:400});
    else if(entity.visualClass==='field'&&!Number.isFinite(Number(geometry(entity).x)))map.set(entity.id,{x:760-(index%2)*110,y:105+(index%2)*55});
   });
   const offsetFor=(direction)=>direction==='up'?{x:0,y:-155}:direction==='down'?{x:0,y:145}:direction==='left'?{x:-180,y:0}:direction==='right'?{x:180,y:0}:direction==='inward'?{x:-145,y:-80}:direction==='outward'?{x:145,y:-80}:{x:0,y:-105};
   for(const relation of relationList){
    const source=all.find(entity=>entity.id===relation.from),targetPosition=map.get(relation.to)||hero;
    if(!source)continue;
    const explicit=geometry(source),hasExplicit=Number.isFinite(Number(explicit.x))||Number.isFinite(Number(explicit.y));
    if(hasExplicit)continue;
    if(['grows-from','branches-from','attaches-to'].includes(relation.kind)){
     const o=offsetFor(relation.direction);map.set(source.id,{x:targetPosition.x+o.x,y:targetPosition.y+o.y});
    } else if(['flows-to','feeds','passes-to','routes-to','transfers'].includes(relation.kind)){
     const o=offsetFor(relation.direction==='up'?'down':relation.direction==='down'?'up':relation.direction);map.set(source.id,{x:targetPosition.x+o.x,y:targetPosition.y+o.y});
    }
   }
   all.forEach(entity=>{const g=geometry(entity);if(Number.isFinite(Number(g.x))||Number.isFinite(Number(g.y))){const prior=map.get(entity.id)||hero;map.set(entity.id,{...prior,x:Number.isFinite(Number(g.x))?Number(g.x):prior.x,y:Number.isFinite(Number(g.y))?Number(g.y):prior.y})}});
   return map;
  }

  function renderEntity(entity,position,plan){
   const geometry=geometryFor(plan,entity),x=Number(geometry.x??position?.x??450),y=Number(geometry.y??position?.y??280),scale=Number(geometry.scale??1),rep=entity.representation||'circle',label=entity.label||entity.semanticType||entity.id;
   const customAnchors=Object.fromEntries(Object.entries(geometry.anchors||{}).map(([key,point])=>[key,point])), anchors=anchorMarkup(x,y,scale,customAnchors), render=(content,extra='')=>group(entity,content,extra,anchors);
   entity.__geometry=geometry;
   const binding=entity.renderBinding;
   if(binding){
    if(typeof binding.dataUrl!=='string'||!binding.dataUrl.startsWith('data:image/svg+xml;base64,'))throw Error(`AUTHORED_ASSET_BYTES_MISSING:${entity.id}:${binding.assetId||'unknown'}`);
    const kind=binding.kind||'AUTHORED_SVG',family=binding.family||'unknown',assetId=binding.assetId||entity.id,normalizedFamily=binding.normalizedStyleFamily||'missing';
    if(normalizedFamily!=='nexstudio-authored-cartoon-v1')throw Error(`AUTHORED_STYLE_FAMILY_INVALID:${entity.id}:${normalizedFamily}`);
    if(kind==='CHARACTER_SKIN'&&binding.performanceAuthority!=='NEXSTICK_V5_1')throw Error(`CHARACTER_SKIN_MOTION_AUTHORITY_MISSING:${entity.id}`);
    const defaultSize=kind==='ENVIRONMENT_SVG'?{w:900,h:560}:kind==='CHARACTER_SKIN'?{w:250,h:330}:{w:190,h:170};
    const w=Math.max(24,Number(geometry.width??defaultSize.w)*scale),h=Math.max(24,Number(geometry.height??defaultSize.h)*scale);
    const ix=kind==='ENVIRONMENT_SVG'?Number(geometry.x??450)-w/2:x-w/2,iy=kind==='ENVIRONMENT_SVG'?Number(geometry.y??280)-h/2:y-h/2;
    const opacity=Number(geometry.opacity??(kind==='ENVIRONMENT_SVG'?.92:1));
    const preserve=kind==='ENVIRONMENT_SVG'?'xMidYMid slice':'xMidYMid meet';
    if(kind==='CHARACTER_SKIN'&&binding.performanceSequence?.source==='NEXSTICK_V5_1'&&Array.isArray(binding.performanceSequence.frames)&&binding.performanceSequence.frames.length>=3){
     const frames=binding.performanceSequence.frames.map((frame,index)=>{
      if(typeof frame.dataUrl!=='string'||!frame.dataUrl.startsWith('data:image/svg+xml;base64,'))throw Error(`CHARACTER_SKIN_FRAME_INVALID:${entity.id}:${index}`);
      return `<image href="${esc(frame.dataUrl)}" x="${ix}" y="${iy}" width="${w}" height="${h}" preserveAspectRatio="${preserve}" opacity="${index===0?opacity:0}" data-authored-asset="true" data-character-skin="true" data-character-skin-frame="${index}" data-character-skin-time="${Number(frame.t)||0}" data-performance-authority="NEXSTICK_V5_1"/>`;
     }).join('');
     return render(frames,`data-character-skin-sequence="true" data-character-action="${esc(binding.performanceSequence.action||'idle')}" data-authored-asset-id="${esc(assetId)}" data-authored-asset-kind="${esc(kind)}" data-authored-family="${esc(family)}" data-normalized-style-family="${esc(normalizedFamily)}" data-performance-authority="NEXSTICK_V5_1"`);
    }
    return render(`<image href="${esc(binding.dataUrl)}" x="${ix}" y="${iy}" width="${w}" height="${h}" preserveAspectRatio="${preserve}" opacity="${opacity}" data-authored-asset="true" data-authored-asset-id="${esc(assetId)}" data-authored-asset-kind="${esc(kind)}" data-authored-family="${esc(family)}" data-normalized-style-family="${esc(normalizedFamily)}"${kind==='CHARACTER_SKIN'?` data-character-skin="true" data-performance-authority="NEXSTICK_V5_1"`:''}/>`);
   }
   if(rep==='soil-layer'||rep==='ground-line')return soil(entity);
  if(rep==='seed'){
   const opened=(plan.relationships||[]).some(item=>item.from===entity.id&&item.kind==='absorbs');
   const cy=Math.max(y,Number(geometry.y??350)),w=Number(geometry.width??116)*scale,h=Number(geometry.height??76)*scale,rot=Number(geometry.rotation||0),left=x-w*.5,right=x+w*.5,top=cy-h*.5,bottom=cy+h*.5;
   const body=`M${left+w*.08} ${cy-h*.08} C${left+w*.12} ${top+h*.15} ${x-w*.08} ${top-h*.03} ${right-w*.08} ${top+h*.22} C${right+w*.02} ${cy-h*.03} ${right-w*.02} ${bottom-h*.12} ${x+w*.06} ${bottom+h*.02} C${left+w*.18} ${bottom-h*.02} ${left-w*.03} ${cy+h*.13} ${left+w*.08} ${cy-h*.08}Z`;
   const seedBody=`<g transform="rotate(${rot} ${x} ${cy})"><path d="${body}" fill="${geometry.fill||colors.ochre}" stroke="${geometry.stroke||colors.ink}" stroke-width="${geometry.strokeWidth||6}"/><path d="M${left+w*.25} ${cy-h*.08} Q${x} ${top+h*.18} ${right-w*.2} ${cy-h*.16}" fill="none" stroke="#fff6d7" stroke-width="${Math.max(2,3.5*scale)}" opacity=".32"/></g>${opened?path(`M${x-5*scale} ${top+h*.12} Q${x-18*scale} ${cy-h*.08} ${x-1*scale} ${cy+h*.02} Q${x+14*scale} ${cy+h*.14} ${x+7*scale} ${bottom-h*.08}`,colors.coral,Math.max(4,5.5*scale),'none','data-motion-piece="crack"'):''}`;
   return render(seedBody);
  }
   if(rep==='branch')return render(root(x,Math.min(390,y),scale*.78,Boolean(entity.capabilities?.includes('branchable')),{...geometry,stroke:geometry.stroke||'#b86f50'}));
  if(rep==='stem'){
    if(geometry.visible===false)return render('','data-structural-anchor="true"');
    const compositeChildren=(plan.relationships||[]).filter(relation=>relation.to===entity.id&&['grows-from','branches-from','attaches-to'].includes(relation.kind));
    if(entity.visualClass==='group'&&compositeChildren.length)return render('','data-structural-anchor="true" data-composite-group="true"');
    if(entity.visualClass==='group'&&entity!==plan.heroEntity&&geometry.visible!==true&&!((plan.relationships||[]).some(relation=>relation.kind==='grows-from'&&relation.from===entity.id)))return render('','data-structural-anchor="true"');
    const stemFallback=`M${x} ${Number(geometry.y??390)} C${x+3*scale} ${Number(geometry.y??390)-74*scale} ${x-8*scale} ${Number(geometry.y??390)-158*scale} ${x} ${Number(geometry.y??390)-245*scale}`;
    return render(customPaths({...geometry,stroke:geometry.stroke||colors.teal},[stemFallback]).replaceAll('primary-root','primary-stem'));
   }
   if(rep==='leaf'){const count=Math.max(1,Number(geometry.count??(entity.importance==='hero'?3:4)));let leaves='';if(Array.isArray(geometry.items)&&geometry.items.length){for(const item of geometry.items){const rx=Number(item.width??176)/2,ry=Number(item.height??64)/2,ix=Number(item.x),iy=Number(item.y),rot=Number(item.rotation||0),anchorPoint=item.anchor?{x:Number(item.anchor.x),y:Number(item.anchor.y)}:null;leaves+=leaf(ix,iy,rx,ry,rot,item.continuityRole||'',item.pivot||anchorPoint)}}else for(let i=0;i<count;i++){const side=i%2?-1:1,row=Math.floor(i/2);leaves+=leaf(x+side*(72+row*22),y-row*68,88-row*8,32-row*3,side*(22+row*4))}return render(leaves,`data-attachment-quality="${esc((plan.artDirection?.states?.find(state=>state.id===plan.artDirection?.activeStateId)?.quality?.attachmentQuality)||'unspecified')}"`)}
   if(rep==='droplet')return render(droplet(x-42,y-45,16)+droplet(x+12,y-90,13)+droplet(x+55,y-35,15)+(geometry.showLabel?text(label.toUpperCase(),x,y+42,17,colors.blue):''))
  if(rep==='sun'||rep==='sun-ray')return render(sun(x,y));
  if(rep==='cloud')return render(`<path d="M${x-110} ${y+25} C${x-120} ${y-35} ${x-62} ${y-62} ${x-18} ${y-38} C${x+18} ${y-96} ${x+105} ${y-65} ${x+108} ${y} C${x+150} ${y+5} ${x+145} ${y+65} ${x+90} ${y+66} H${x-75} C${x-145} ${y+66} ${x-150} ${y+28} ${x-110} ${y+25}Z" fill="${colors.blue}" opacity=".68" stroke="${colors.teal}" stroke-width="6"/>`);
  if(rep==='document')return render(`<rect x="${x-72}" y="${y-88}" width="144" height="176" rx="12" fill="${colors.paper}" stroke="${colors.ink}" stroke-width="6"/>${line(x-42,y-35,x+42,y-35,colors.muted,5)}${line(x-42,y,x+42,y,colors.muted,5)}${line(x-42,y+35,x+20,y+35,colors.muted,5)}${text(label,x,y+122,18)}`);
  if(rep==='token')return render(`<circle cx="${x}" cy="${y}" r="58" fill="${colors.ochre}" stroke="${colors.ink}" stroke-width="7"/>${text(label.slice(0,3).toUpperCase(),x,y+8,20)}`);
  if(rep==='block')return render(`<rect x="${x-85}" y="${y-70}" width="170" height="140" rx="18" fill="${colors.green}" stroke="${colors.teal}" stroke-width="7"/>${text(label.toUpperCase(),x,y+8,20)}`);
  if(rep==='tool')return render(`<rect x="${x-74}" y="${y-58}" width="148" height="116" rx="58" fill="${colors.violet}" opacity=".82" stroke="${colors.ink}" stroke-width="6"/>${text(label.toUpperCase(),x,y+8,18,colors.paper)}`);
  if(rep==='container'||rep==='node')return render(`<rect x="${x-88}" y="${y-62}" width="176" height="124" rx="${rep==='node'?62:22}" fill="${entity===plan.heroEntity?colors.ochre:colors.paper}" stroke="${colors.ink}" stroke-width="6"/>${text(label.toUpperCase(),x,y+8,18)}`);
   if(rep==='particle'||rep==='glow')return render(`<circle cx="${x}" cy="${y}" r="${Number(geometry.width??52)/2}" fill="${geometry.fill||(rep==='glow'?colors.coral:colors.blue)}" opacity="${geometry.opacity??.88}"/>${text(label.toUpperCase(),x,y+52,17,rep==='glow'?colors.coral:colors.ink)}`);
  return render(`<ellipse cx="${x}" cy="${y}" rx="72" ry="52" fill="${colors.ochre}" stroke="${colors.ink}" stroke-width="6"/>${text(label.toUpperCase(),x,y+8,18)}`);
 }

 function connectorFor(relation,map,entities){const a=map.get(relation.from),b=map.get(relation.to);if(!a||!b)return'';const source=entities.find(entity=>entity.id===relation.from),target=entities.find(entity=>entity.id===relation.to);if(['grows-from','branches-from','attaches-to','absorbs','travels-through','transforms-into'].includes(relation.kind)||(relation.kind==='exits'&&source?.type==='growth-structure'&&target?.type==='environment'))return`<g data-relationship="${esc(relation.kind)}" data-source="${esc(relation.from)}" data-target="${esc(relation.to)}" data-motion-capabilities="path-drawable continuity-capable"></g>`;const flow=['flows-to','produces','feeds','transfers','routes-to','passes-to','connects','orients-toward'].includes(relation.kind);if(flow){const cx=(a.x+b.x)/2,cy=(a.y+b.y)/2-24;const orientation=relation.kind==='orients-toward';const stroke=relation.kind==='flows-to'?colors.blue:colors.teal;return `<g data-relationship="${esc(relation.kind)}" data-source="${esc(relation.from)}" data-target="${esc(relation.to)}" data-motion-connector="true" data-motion-role="${orientation?'orientation-guide':'flow'}" data-motion-capabilities="path-drawable flow-source flow-target"><path d="M${a.x} ${a.y} Q${cx} ${cy} ${b.x} ${b.y}" fill="none" stroke="${stroke}" stroke-width="${orientation?'3':'5'}" stroke-linecap="round" stroke-dasharray="${orientation?'8 16':'9 12'}" opacity="${orientation?'.34':'1'}" data-motion-piece="flow-path"/></g>`}const color=colors.teal;return `<g data-relationship="${esc(relation.kind)}" data-source="${esc(relation.from)}" data-target="${esc(relation.to)}" data-motion-capabilities="path-drawable flow-source flow-target">${arrow(a.x,a.y,b.x,b.y,color,5)}</g>`}

 function entityLayerRank(entity){
  // Paper Motion scenes use semantic layers rather than source-array order.
  // Environment paper establishes the stage; meaningful structure sits above it;
  // transient signals/annotations remain legible in the foreground. This prevents
  // an opaque environment cutout from accidentally hiding roots, paths, or other
  // structural children merely because it was listed later in a plan.
  if(entity?.type==='environment'||entity?.visualClass==='environment')return 0;
  if(entity?.visualClass==='field'||entity?.type==='field')return 1;
  if(entity?.importance==='annotation'||entity?.type==='energy'||['particle','glow'].includes(entity?.visualClass)||['particle','glow'].includes(entity?.representation))return 4;
  if(entity?.visualClass==='attached-surface')return 3;
  return 2;
 }
 function executionLayerEntity(layer){return {id:layer.id,type:layer.role==='background'?'environment':'object',semanticType:layer.semanticPurpose||'production context',importance:'supporting',visualClass:layer.role==='background'?'environment':'illustration',geometry:layer.geometry||{},renderBinding:layer.renderBinding}}
 function renderExecutionLayer(layer,plan){const entity=executionLayerEntity(layer);return renderEntity(entity,{x:Number(layer.geometry?.x??450),y:Number(layer.geometry?.y??280)},plan)}
 function compose(plan){
  if(!constructionGrammarInventory.includes(plan.spatialGrammar))throw Error(`Unsupported construction grammar: ${plan.spatialGrammar}`);
  const all=[plan.heroEntity,...(plan.supportingEntities||[])],map=positions(plan);let body='';
  const executionLayers=plan.productionArt?.executionLayers||[];
  const authoredSceneLayer=executionLayers.find(layer=>layer.source==='PRODUCTION_SCOPED_AUTHORED_ART'&&layer.semanticPurpose==='production-scoped-authored-scene');
  if(authoredSceneLayer)return renderExecutionLayer(authoredSceneLayer,plan);
  const ordered=all.map((entity,index)=>({entity,index,rank:entityLayerRank(entity)})).sort((a,b)=>a.rank-b.rank||a.index-b.index);
  body+=executionLayers.filter(layer=>layer.role==='background').map(layer=>renderExecutionLayer(layer,plan)).join('');
  body+=ordered.filter(item=>item.rank<=1).map(item=>renderEntity(item.entity,map.get(item.entity.id),plan)).join('');
  body+=executionLayers.filter(layer=>layer.role==='midground').map(layer=>renderExecutionLayer(layer,plan)).join('');
  body+=(plan.relationships||[]).map(relation=>connectorFor(relation,map,all)).join('');
  body+=ordered.filter(item=>item.rank>1).map(item=>renderEntity(item.entity,map.get(item.entity.id),plan)).join('');
  body+=executionLayers.filter(layer=>layer.role==='foreground').map(layer=>renderExecutionLayer(layer,plan)).join('');
  if((plan.spatialGrammar==='sequential-growth'||plan.spatialGrammar==='sequential-transformation')&&all.length<4){const hero=map.get(plan.heroEntity.id)||{x:450,y:300};body+=`<g data-relationship="future-state" data-future-state-hint="true" opacity=".22">${path(`M${hero.x} ${hero.y-58} Q${hero.x+110} ${hero.y-135} ${hero.x+220} ${hero.y-185}`,colors.coral,3,'none','stroke-dasharray="8 16"')}</g>`}
  return body;
 }

 function continuityIds(plan){const all=[plan.heroEntity,...(plan.supportingEntities||[])].filter(Boolean),ids=new Set(all.filter(entity=>entity.continuity).map(entity=>entity.id)),relations=plan.relationships||[],structural=new Set(['grows-from','branches-from','attaches-to','travels-through','exits']);if(plan.continuity&&plan.heroEntity)ids.add(plan.heroEntity.id);let changed=true;while(changed){changed=false;for(const relation of relations){if(!structural.has(relation.kind))continue;if(ids.has(relation.from)&&!ids.has(relation.to)){ids.add(relation.to);changed=true}if(ids.has(relation.to)&&!ids.has(relation.from)){ids.add(relation.from);changed=true}}}return ids}
 function assertProductionArtRuntime(plan){
  const art=plan&&plan.productionArt;if(!art)return;
  if(art.status!=='READY_FOR_RENDER')throw Error(`PRODUCTION_ART_BLOCKED:${plan.sceneId||'unknown'}:${(art.blockers||[]).join('|')||'not-ready'}`);
  if(art.releaseGate!=='EXECUTION_FIDELITY_REQUIRED')throw Error(`PRODUCTION_ART_RELEASE_GATE_MISSING:${plan.sceneId||'unknown'}`);
  if(art.rawRigVisibleAllowed!==false)throw Error(`RAW_RIG_EXPOSURE_FORBIDDEN:${plan.sceneId||'unknown'}`);
  const authored=['AUTHORED_SCENE','HYBRID_ILLUSTRATION','WHITEBOARD_SCENE'].includes(art.visualMode);
  if(authored&&art.diagramFallbackAllowed)throw Error(`AUTHORED_SCENE_DIAGRAM_FALLBACK_FORBIDDEN:${plan.sceneId||'unknown'}`);
  if(authored){
   const authoredSceneLayer=(art.executionLayers||[]).find(layer=>layer.source==='PRODUCTION_SCOPED_AUTHORED_ART'&&layer.semanticPurpose==='production-scoped-authored-scene');
   if(authoredSceneLayer){
    if(!art.productionScopedAuthoredPlate||!art.productionScopedAuthoredPlate.lockedSemanticsHash)throw Error(`PRODUCTION_SCOPED_ART_PROVENANCE_MISSING:${plan.sceneId||'unknown'}`);
    if(authoredSceneLayer.renderBinding?.family!=='nexstudio-production-scoped-authored-art-v1')throw Error(`PRODUCTION_SCOPED_ART_FAMILY_INVALID:${plan.sceneId||'unknown'}`);
    return;
   }
   const entities=[plan.heroEntity,...(plan.supportingEntities||[])].filter(Boolean);
   const normalizedFamilies=new Set(entities.filter(entity=>entity.renderBinding).map(entity=>entity.renderBinding.normalizedStyleFamily));
   if(normalizedFamilies.size>1||[...normalizedFamilies].some(family=>family!=='nexstudio-authored-cartoon-v1'))throw Error(`STYLE_GRAMMAR_RUNTIME_MISMATCH:${plan.sceneId||'unknown'}:${[...normalizedFamilies].join(',')}`);
   const hasAuthoredSubstrate=entities.some(entity=>Boolean(entity.renderBinding)||(entity.geometry&&((entity.geometry.paths||[]).length||(entity.geometry.items||[]).length)));
   if(!hasAuthoredSubstrate)throw Error(`AUTHORED_SCENE_SUBSTRATE_MISSING:${plan.sceneId||'unknown'}`);
   const unboundIllustrated=entities.filter(entity=>entity.visualClass==='illustration'&&!entity.renderBinding&&!Boolean(entity.geometry&&((entity.geometry.paths||[]).length||(entity.geometry.items||[]).length)));
   if(unboundIllustrated.length)throw Error(`AUTHORED_ILLUSTRATION_BODY_MISSING:${plan.sceneId||'unknown'}:${unboundIllustrated.map(entity=>entity.id).join(',')}`);
   const presentationReps=new Set(['node','token','block','container','document','tool']);
   const substituted=entities.filter(entity=>!entity.renderBinding&&presentationReps.has(entity.representation||'')&&!Boolean(entity.geometry&&((entity.geometry.paths||[]).length||(entity.geometry.items||[]).length)));
   if(substituted.length)throw Error(`PRESENTATION_PRIMITIVE_IN_AUTHORED_SCENE:${plan.sceneId||'unknown'}:${substituted.map(entity=>entity.id).join(',')}`);
   const authoredElementCount=entities.length+(art.executionLayers||[]).length;
   if(authoredElementCount<3)throw Error(`AUTHORED_SCENE_DENSITY_UNDERSPECIFIED:${plan.sceneId||'unknown'}:${authoredElementCount}<3`);
   if(art.commercialCapability?.replanRequired)throw Error(`PREMIUM_EXECUTION_REPLAN_REQUIRED:${plan.sceneId||'unknown'}:${(art.blockers||[]).filter(reason=>String(reason).startsWith('PREMIUM_')).join('|')}`);
   if(art.sceneComposition?.compositionBlockers?.length)throw Error(`SCENE_COMPOSER_BLOCKED:${plan.sceneId||'unknown'}:${art.sceneComposition.compositionBlockers.join('|')}`);
  }
 }
 function create(plan={}){
  assertProductionArtRuntime(plan);
  const wrap=document.createElement('div');
  wrap.className='nex-visual-construction';
  wrap.dataset.constructionId=plan.constructionId||'production-scoped';
  wrap.dataset.spatialGrammar=plan.spatialGrammar||'freeform';
  wrap.dataset.dominance=plan.dominanceMode||'hybrid';
  wrap.dataset.runtimeStrategy='domain-neutral-grammar';
  if(plan.productionArt){wrap.dataset.productionArtMode=plan.productionArt.visualMode;wrap.dataset.productionArtReleaseGate=plan.productionArt.releaseGate;wrap.dataset.diagramFallbackAllowed=String(Boolean(plan.productionArt.diagramFallbackAllowed));wrap.dataset.rawRigVisibleAllowed=String(Boolean(plan.productionArt.rawRigVisibleAllowed));}
  let renderPlan=plan;
  if(plan.continuity){
   wrap.dataset.continuityObjectId=plan.continuity.objectId;
   wrap.dataset.continuityState=plan.continuity.state;
   // A scene can contain several entities that participate in continuity, but
   // only its current hero represents the single cross-scene visual object.
   // Clone the execution plan so runtime bookkeeping never mutates the
   // persisted NexMind director artifact.
   const persistent=continuityIds(plan);
   renderPlan={
    ...plan,
    heroEntity:{...plan.heroEntity,continuity:true,continuityHero:true,continuityId:plan.continuity.objectId},
    supportingEntities:(plan.supportingEntities||[]).map(entity=>({...entity,continuity:persistent.has(entity.id),continuityHero:false,continuityId:plan.continuity.objectId}))
   };
  }
  wrap.setAttribute('role','img');
  wrap.setAttribute('aria-label',plan.heroEntity?.semanticType||plan.semanticGoal||'visual explanation');
   const surface=plan.artDirection?.surface||{};
   wrap.innerHTML=`<svg viewBox="0 0 900 560" preserveAspectRatio="xMidYMid meet" aria-hidden="true"><defs><marker id="vc-arrow" markerWidth="12" markerHeight="12" refX="10" refY="5" orient="auto"><path d="M0,0 L0,10 L11,5 z" fill="${colors.coral}"/></marker><filter id="vc-paper-shadow" x="-25%" y="-25%" width="150%" height="160%"><feDropShadow dx="3.2" dy="4.4" stdDeviation="2.8" flood-color="#171717" flood-opacity=".18"/></filter><filter id="vc-paper-cutout" x="-28%" y="-28%" width="156%" height="170%"><feTurbulence type="fractalNoise" baseFrequency=".82" numOctaves="2" seed="29" result="noise"/><feColorMatrix in="noise" type="matrix" values=".18 0 0 0 .74  0 .18 0 0 .71  0 0 .18 0 .66  0 0 0 .11 0" result="grain"/><feComposite in="grain" in2="SourceAlpha" operator="in" result="clippedGrain"/><feBlend in="SourceGraphic" in2="clippedGrain" mode="multiply" result="textured"/><feDropShadow in="textured" dx="3.5" dy="4.8" stdDeviation="2.2" flood-color="#171717" flood-opacity=".20"/></filter><filter id="vc-paper-grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".72" numOctaves="3" seed="17"/><feColorMatrix type="saturate" values="0"/><feComponentTransfer><feFuncA type="table" tableValues="0 .075"/></feComponentTransfer></filter></defs><rect x="0" y="0" width="900" height="560" rx="${surface.radius??28}" fill="${surface.fill||colors.paper}" stroke="${surface.stroke||colors.ink}" stroke-width="${surface.strokeWidth??3}" opacity="${surface.opacity??.98}"/><rect x="0" y="0" width="900" height="560" pointer-events="none" filter="url(#vc-paper-grain)" opacity=".82"/>${compose(renderPlan)}</svg>`;
  return wrap;
 }
 return {create,primitiveVisualInventory,constructionGrammarInventory,runtimeStrategy:'domain-neutral-grammar'};
})();
