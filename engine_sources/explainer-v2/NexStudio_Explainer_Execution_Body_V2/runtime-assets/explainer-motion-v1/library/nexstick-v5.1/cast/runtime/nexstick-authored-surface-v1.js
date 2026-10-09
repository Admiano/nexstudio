'use strict';
const Mesh=require('./nexstick-mesh-deformer-v1.js');
const NS=global.NexStickman;
const VERSION='1.0.0-authored-master-surface';
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const f=n=>(+n).toFixed(2);
const mix=(a,b,t)=>({x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t,depth:(a.depth||0)+((b.depth||0)-(a.depth||0))*t});
const mid=(a,b)=>mix(a,b,.5);
const sub=(a,b)=>({x:a.x-b.x,y:a.y-b.y});
const len=v=>Math.hypot(v.x,v.y);
const norm=v=>{const d=Math.max(1e-6,len(v));return{x:v.x/d,y:v.y/d};};
const add=(a,b,s=1)=>({x:a.x+b.x*s,y:a.y+b.y*s});
const unit=(a,b)=>norm(sub(b,a));
const perp=v=>({x:-v.y,y:v.x});
const dot=(a,b)=>a.x*b.x+a.y*b.y;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
const rgba=(hex,op)=>hex; // SVG output stays flat/authored; no CSS effects.

const MASTER_KIND={
 adult_man_average:'adult_male',adult_man_broad:'adult_male',diminutive_man:'adult_male',
 adult_woman_average:'adult_female',adult_woman_tall:'adult_female',diminutive_woman:'adult_female',
 boy:'child',girl:'child',diminutive_boy:'child',diminutive_girl:'child',neutral_child:'child',neutral_adult:'neutral_adult'
};
const STYLE={
 adult_man_average:{identity:'AM-01',skin:'#A96F50',hair:'#24201E',top:'#E6DED2',lower:'#3A4149',shoe:'#2A2D31',accent:'#A37850'},
 adult_man_broad:{identity:'AM-02',skin:'#704633',hair:'#191717',top:'#718598',lower:'#343B43',shoe:'#25282C',accent:'#B2804D'},
 adult_woman_average:{identity:'AF-01',skin:'#8B5943',hair:'#211B19',top:'#CAB9A6',lower:'#3B3E48',shoe:'#25282D',accent:'#AE7D56'},
 adult_woman_tall:{identity:'AF-02',skin:'#D2A07B',hair:'#36251F',top:'#74887D',lower:'#40454B',shoe:'#272A2E',accent:'#B68555'},
 boy:{identity:'BY-01',skin:'#8C5C43',hair:'#1E1B1A',top:'#907259',lower:'#44515D',shoe:'#2A2E33',accent:'#D29B59'},
 girl:{identity:'GR-01',skin:'#C98A67',hair:'#29211F',top:'#887AA0',lower:'#454852',shoe:'#292D32',accent:'#D29B6B'},
 diminutive_man:{identity:'AM-03',skin:'#52362B',hair:'#171515',top:'#687D6D',lower:'#363E43',shoe:'#262B2E',accent:'#B28A55'},
 diminutive_woman:{identity:'AF-03',skin:'#A46B50',hair:'#2E201C',top:'#8F706B',lower:'#41444B',shoe:'#292C30',accent:'#B98964'},
 diminutive_boy:{identity:'BY-02',skin:'#76503C',hair:'#1D1918',top:'#75899C',lower:'#404B56',shoe:'#2B2F34',accent:'#C48F58'},
 diminutive_girl:{identity:'GR-02',skin:'#B97C5B',hair:'#30231F',top:'#947FA8',lower:'#464A54',shoe:'#2A2E33',accent:'#CF9767'},
 neutral_adult:{identity:'NA-01',skin:'#A67559',hair:'#2D2825',top:'#777D83',lower:'#3E454C',shoe:'#292D31',accent:'#AD825C'},
 neutral_child:{identity:'NC-01',skin:'#B97D5E',hair:'#2B2321',top:'#808B94',lower:'#48535E',shoe:'#2B3035',accent:'#C29465'}
};

// 16 distinct identity grammars. Hair/wardrobe can vary independently.
const IDENTITIES={
 'AM-01':{master:'adult_male',head:'oval',jaw:.74,eyes:.31,brows:'straight',nose:'bridge',mouth:'soft',hair:'sidepart',facial:'stubble'},
 'AM-02':{master:'adult_male',head:'square',jaw:.91,eyes:.29,brows:'heavy',nose:'broad',mouth:'flat',hair:'crop',facial:'shortbeard'},
 'AM-03':{master:'adult_male',head:'compact',jaw:.83,eyes:.34,brows:'angled',nose:'dot',mouth:'soft',hair:'curltop',facial:'none'},
 'AM-04':{master:'adult_male',head:'long',jaw:.70,eyes:.32,brows:'soft',nose:'long',mouth:'smile',hair:'bald',facial:'goatee'},
 'AF-01':{master:'adult_female',head:'soft',jaw:.76,eyes:.34,brows:'arched',nose:'bridge',mouth:'soft',hair:'bob',facial:'none'},
 'AF-02':{master:'adult_female',head:'long',jaw:.70,eyes:.31,brows:'soft',nose:'long',mouth:'smile',hair:'bun',facial:'none'},
 'AF-03':{master:'adult_female',head:'round',jaw:.86,eyes:.36,brows:'arched',nose:'dot',mouth:'soft',hair:'curly',facial:'none'},
 'AF-04':{master:'adult_female',head:'heart',jaw:.62,eyes:.33,brows:'straight',nose:'bridge',mouth:'flat',hair:'braid',facial:'none'},
 'BY-01':{master:'child',head:'childRound',jaw:.86,eyes:.35,brows:'soft',nose:'dot',mouth:'soft',hair:'messy',facial:'none'},
 'BY-02':{master:'child',head:'childOval',jaw:.78,eyes:.34,brows:'straight',nose:'dot',mouth:'smile',hair:'roundcrop',facial:'none'},
 'GR-01':{master:'child',head:'childOval',jaw:.79,eyes:.36,brows:'soft',nose:'dot',mouth:'smile',hair:'ponytail',facial:'none'},
 'GR-02':{master:'child',head:'childRound',jaw:.87,eyes:.37,brows:'arched',nose:'dot',mouth:'soft',hair:'bob',facial:'none'},
 'NA-01':{master:'neutral_adult',head:'oval',jaw:.77,eyes:.33,brows:'soft',nose:'dot',mouth:'flat',hair:'short',facial:'none'},
 'NA-02':{master:'neutral_adult',head:'squareSoft',jaw:.84,eyes:.32,brows:'straight',nose:'bridge',mouth:'soft',hair:'curlyShort',facial:'none'},
 'NC-01':{master:'child',head:'childRound',jaw:.86,eyes:.35,brows:'soft',nose:'dot',mouth:'soft',hair:'roundcrop',facial:'none'},
 'NC-02':{master:'child',head:'childOval',jaw:.78,eyes:.36,brows:'arched',nose:'dot',mouth:'smile',hair:'curlyShort',facial:'none'}
};
const EXPRESSIONS={
 neutral:{brow:0,lid:1,mouth:'soft',open:0},attentive:{brow:-.03,lid:.92,mouth:'soft',open:0},happy:{brow:-.05,lid:.86,mouth:'smile',open:0},serious:{brow:.05,lid:.86,mouth:'flat',open:0},curious:{brow:-.10,lid:.96,mouth:'soft',open:0},concerned:{brow:.12,lid:.88,mouth:'down',open:0},surprised:{brow:-.18,lid:1.22,mouth:'o',open:.75},thinking:{brow:.02,lid:.72,mouth:'side',open:0},speaking:{brow:-.02,lid:.94,mouth:'open',open:.52}
};
const VISEMES={rest:{open:0,width:1},A:{open:.62,width:1.02},E:{open:.34,width:1.18},I:{open:.24,width:.92},O:{open:.56,width:.64},U:{open:.38,width:.56},M:{open:.02,width:.84},F:{open:.12,width:1.0},L:{open:.28,width:.88}};
const VIEWS={front:{yaw:0,face:0},'near-front':{yaw:-12,face:-.10},'3q-left':{yaw:-35,face:-.34},'3q-right':{yaw:35,face:.34},'profile-left':{yaw:-78,face:-.82},'profile-right':{yaw:78,face:.82}};
const HAND_POSES=['relaxed','open','point','tap','pinch','precision_grip','power_grip','receive','offer','present','support_large','type','phone_hold','count','stop'];
const HAND_ORIENTATIONS=['palm-front','palm-back','edge-left','edge-right','foreshortened/contact'];
const FOOT_STATES=['plant','heel-lift','toe-off','swing','seated','crouched/bent'];

function presentation(id){if(id.includes('woman'))return'woman';if(id.includes('man'))return'man';if(id.includes('girl'))return'girl';if(id.includes('boy'))return'boy';if(id.includes('child'))return'child';return'neutral';}
function masterKind(id){return MASTER_KIND[id]||'neutral_adult';}
function project(result,opts={}){
 const w=opts.width||360,h=opts.height||440,view=VIEWS[opts.viewFamily]||null,yaw=opts.yawDeg??view?.yaw??-10,scale=opts.scale||220;
 const camera={origin:opts.origin||[w*.5,h-30],scale,yaw_deg:yaw,pitch_deg:opts.pitchDeg||0,root_center:opts.rootCenter!==false};
 return{P:NS.project(result.state.pose3d,camera),camera,w,h,scale,viewFamily:opts.viewFamily||'near-front',faceTurn:view?.face??clamp(yaw/95,-.9,.9)};
}
function dims(result,scale){
 const b=result.bodyProfile||{},p=presentation(result.familyId),child=['boy','girl','child'].includes(p),kind=masterKind(result.familyId);
 const structural=kind==='adult_male'?1.04:kind==='adult_female'?.96:child?.84:1;
 return{
  ua:Math.max(5.5,(b.limbRadiusM?.upperArm||.044)*scale*.63*structural),fa:Math.max(5,(b.limbRadiusM?.forearm||.039)*scale*.59*structural),
  thigh:Math.max(7,(b.limbRadiusM?.thigh||.062)*scale*.62*(child?.85:1)),calf:Math.max(5.5,(b.limbRadiusM?.calf||.050)*scale*.57*(child?.84:1)),
  neck:Math.max(4,(b.limbRadiusM?.neck||.042)*scale*.50),headRx:Math.max(15,(b.head?.radiusXM||.10)*scale*(child?1.12:1)*.89),headRy:Math.max(19,(b.head?.radiusYM||.125)*scale*(child?1.10:1)*.88),
  hand:Math.max(8.2,(b.hand?.fingerWidthM||.016)*scale*(child?3.0:3.5)),foot:Math.max(9,(b.foot?.widthM||.075)*scale*.74),
  shoulderHalf:Math.max(18,(b.torso?.minShoulderHalfM||.155)*scale*(kind==='adult_male'?1.04:kind==='adult_female'?.94:child?.82:1)),
  hipHalf:Math.max(17,(b.torso?.minHipHalfM||.15)*scale*(kind==='adult_female'?1.08:kind==='adult_male'?.94:child?.86:1)),
  waistTaper:clamp(b.torso?.waistTaper||.84,kind==='adult_female'?.73:.77,.95)
 };
}
function bodyGeometry(P,d){
 const neck=P.neck||mid(P.clavicle_l,P.clavicle_r),chest=P.chest||mid(P.clavicle_l,P.clavicle_r),pelvis=P.pelvis||mid(P.hip_l,P.hip_r),axis=unit(neck,pelvis);let side=perp(axis);
 const cm=mid(P.clavicle_l,P.clavicle_r);if(dot(sub(P.clavicle_l,cm),side)<0)side={x:-side.x,y:-side.y};
 const shC=mix(neck,chest,.60),waC=mix(chest,pelvis,.62),hipC=pelvis,sh=d.shoulderHalf,hp=d.hipHalf,wa=(sh+(hp-sh)*.55)*d.waistTaper;
 const nL=add(neck,side,d.neck*.48),nR=add(neck,side,-d.neck*.48),sL=add(add(shC,axis,-3),side,sh),sR=add(add(shC,axis,-3),side,-sh),aL=add(add(shC,axis,8),side,sh*.88),aR=add(add(shC,axis,8),side,-sh*.88),wL=add(waC,side,wa),wR=add(waC,side,-wa),hL=add(hipC,side,hp),hR=add(hipC,side,-hp);
 const path=`M ${f(nL.x)} ${f(nL.y)} C ${f(add(sL,axis,-8).x)} ${f(add(sL,axis,-8).y)} ${f(sL.x)} ${f(sL.y)} ${f(aL.x)} ${f(aL.y)} C ${f(add(wL,side,3).x)} ${f(add(wL,side,3).y)} ${f(wL.x)} ${f(wL.y)} ${f(hL.x)} ${f(hL.y)} Q ${f(hipC.x)} ${f(hipC.y+7)} ${f(hR.x)} ${f(hR.y)} C ${f(wR.x)} ${f(wR.y)} ${f(add(wR,side,-3).x)} ${f(add(wR,side,-3).y)} ${f(aR.x)} ${f(aR.y)} C ${f(sR.x)} ${f(sR.y)} ${f(add(sR,axis,-8).x)} ${f(add(sR,axis,-8).y)} ${f(nR.x)} ${f(nR.y)} Q ${f(neck.x)} ${f(neck.y+3)} ${f(nL.x)} ${f(nL.y)} Z`;
 const socketL=sL,socketR=sR,hipRootL=hL,hipRootR=hR;
 return{neck,chest,pelvis,axis,side,shC,waC,hipC,sh,hp,wa,path,socketL,socketR,hipRootL,hipRootR,nL,nR,sL,sR,wL,wR,hL,hR};
}
function styleFor(result,opts={}){const base=STYLE[result.familyId]||STYLE.neutral_adult;return{...base,...(opts.palette||{})};}
function clothingPreset(result){const id=result.clothingPreset?.presetId||'';return global.NexClothingLibraryV1?.presets?.find(p=>p.id===id)||{id,items:{}};}
function svgPath(d,fill,stroke='#2A2725',sw=1.35,attrs=''){return `<path ${attrs} d="${d}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" stroke-linejoin="round"/>`;}
function circle(p,r,fill,stroke='none',sw=0,attrs=''){return `<circle ${attrs} cx="${f(p.x)}" cy="${f(p.y)}" r="${f(r)}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}"/>`;}

function headShape(c,rx,ry,type){let jaw=.76,chin=.83,top=.98;if(type==='square'){jaw=.92;chin=.71;}else if(type==='squareSoft'){jaw=.85;chin=.77;}else if(type==='round'||type==='childRound'){jaw=.88;chin=.88;}else if(type==='soft'){jaw=.78;chin=.87;}else if(type==='long'){ry*=1.07;jaw=.70;chin=.76;}else if(type==='compact'){ry*=.95;jaw=.84;chin=.82;}else if(type==='heart'){jaw=.62;chin=.79;}else if(type==='childOval'){jaw=.79;chin=.89;}
 return{ry,d:`M ${f(c.x)} ${f(c.y-ry*top)} C ${f(c.x+rx*.76)} ${f(c.y-ry*.98)} ${f(c.x+rx)} ${f(c.y-ry*.43)} ${f(c.x+rx*.93)} ${f(c.y+ry*.16)} C ${f(c.x+rx*jaw)} ${f(c.y+ry*.67)} ${f(c.x+rx*.34)} ${f(c.y+ry*chin)} ${f(c.x)} ${f(c.y+ry*.89)} C ${f(c.x-rx*.34)} ${f(c.y+ry*chin)} ${f(c.x-rx*jaw)} ${f(c.y+ry*.67)} ${f(c.x-rx*.93)} ${f(c.y+ry*.16)} C ${f(c.x-rx)} ${f(c.y-ry*.43)} ${f(c.x-rx*.76)} ${f(c.y-ry*.98)} ${f(c.x)} ${f(c.y-ry*top)} Z`};
}
function hairBack(c,rx,ry,kind,color,turn){
 if(kind==='bob')return `<path d="M ${f(c.x-rx*1.03)} ${f(c.y-ry*.20)} Q ${f(c.x)} ${f(c.y-ry*1.15)} ${f(c.x+rx*1.04)} ${f(c.y-ry*.17)} L ${f(c.x+rx*.86)} ${f(c.y+ry*.72)} Q ${f(c.x)} ${f(c.y+ry*.99)} ${f(c.x-rx*.88)} ${f(c.y+ry*.70)} Z" fill="${color}"/>`;
 if(kind==='curly'||kind==='curlyShort'){const n=kind==='curly'?12:9,r=rx*(kind==='curly'?.26:.22);return Array.from({length:n},(_,i)=>{const a=Math.PI*2*i/n,x=c.x+Math.cos(a)*rx*.87,y=c.y-ry*.12+Math.sin(a)*ry*.72;return `<circle cx="${f(x)}" cy="${f(y)}" r="${f(r)}" fill="${color}"/>`;}).join('');}
 if(kind==='ponytail')return `<path d="M ${f(c.x+rx*(turn<0?-.86:.86))} ${f(c.y-ry*.23)} Q ${f(c.x+rx*(turn<0?-1.45:1.45))} ${f(c.y+ry*.05)} ${f(c.x+rx*(turn<0?-1.10:1.10))} ${f(c.y+ry*.62)} Q ${f(c.x+rx*(turn<0?-.82:.82))} ${f(c.y+ry*.22)} ${f(c.x+rx*(turn<0?-.86:.86))} ${f(c.y-ry*.23)} Z" fill="${color}"/>`;
 if(kind==='bun')return `<circle cx="${f(c.x+rx*.32*(turn||1))}" cy="${f(c.y-ry*.93)}" r="${f(rx*.33)}" fill="${color}"/>`;
 if(kind==='braid')return `<g>${[0,1,2,3].map(i=>`<ellipse cx="${f(c.x+rx*(turn<0?-.95:.95))}" cy="${f(c.y+ry*(.10+i*.28))}" rx="${f(rx*.18)}" ry="${f(ry*.16)}" fill="${color}"/>`).join('')}</g>`;
 return '';
}
function hairFront(c,rx,ry,kind,color){
 if(kind==='bald')return '';
 if(['crop','short','roundcrop'].includes(kind))return `<path d="M ${f(c.x-rx*.85)} ${f(c.y-ry*.32)} Q ${f(c.x)} ${f(c.y-ry*1.11)} ${f(c.x+rx*.85)} ${f(c.y-ry*.31)} Q ${f(c.x+rx*.42)} ${f(c.y-ry*.61)} ${f(c.x-rx*.85)} ${f(c.y-ry*.32)} Z" fill="${color}"/>`;
 if(kind==='sidepart')return `<path d="M ${f(c.x-rx*.86)} ${f(c.y-ry*.31)} Q ${f(c.x-rx*.12)} ${f(c.y-ry*1.17)} ${f(c.x+rx*.87)} ${f(c.y-ry*.29)} Q ${f(c.x+rx*.23)} ${f(c.y-ry*.63)} ${f(c.x-rx*.86)} ${f(c.y-ry*.31)} Z" fill="${color}"/>`;
 if(['curltop','messy'].includes(kind))return Array.from({length:7},(_,i)=>{const a=Math.PI*(.08+.14*i),x=c.x+Math.cos(a)*rx*.64,y=c.y-ry*.74-Math.sin(a)*ry*.22;return `<circle cx="${f(x)}" cy="${f(y)}" r="${f(rx*.25)}" fill="${color}"/>`;}).join('');
 if(kind==='bob'||kind==='bun'||kind==='ponytail'||kind==='braid')return `<path d="M ${f(c.x-rx*.87)} ${f(c.y-ry*.30)} Q ${f(c.x)} ${f(c.y-ry*1.10)} ${f(c.x+rx*.87)} ${f(c.y-ry*.30)} Q ${f(c.x+rx*.25)} ${f(c.y-ry*.60)} ${f(c.x-rx*.87)} ${f(c.y-ry*.30)} Z" fill="${color}"/>`;
 if(kind==='curly'||kind==='curlyShort')return Array.from({length:7},(_,i)=>{const x=c.x-rx*.72+i*(rx*1.44/6),y=c.y-ry*.75-Math.sin(i*.9)*ry*.10;return `<circle cx="${f(x)}" cy="${f(y)}" r="${f(rx*.25)}" fill="${color}"/>`;}).join('');
 return `<path d="M ${f(c.x-rx*.82)} ${f(c.y-ry*.31)} Q ${f(c.x)} ${f(c.y-ry*1.05)} ${f(c.x+rx*.82)} ${f(c.y-ry*.31)} Z" fill="${color}"/>`;
}
function faceSvg(c,rx,ry,identityId,style,{expression='neutral',blink=0,gazeX=0,gazeY=0,viseme='rest',turn=0,hideHair=false,hairSway=0}={}){
 const id=IDENTITIES[identityId]||IDENTITIES['NA-01'],ex=EXPRESSIONS[expression]||EXPRESSIONS.neutral,vi=VISEMES[viseme]||VISEMES.rest,hs=headShape(c,rx,ry,id.head),ink='#2A2725';ry=hs.ry;
 const hb=hideHair?'':hairBack(c,rx,ry,id.hair,style.hair,turn),hf=hideHair?'':hairFront(c,rx,ry,id.hair,style.hair),hairOpen=hideHair?'':`<g data-secondary-motion="hair" transform="rotate(${f(clamp(hairSway,-2.2,2.2))} ${f(c.x)} ${f(c.y-ry*.45)})">`,hairClose=hideHair?'':'</g>';let out=hairOpen+hb+hairClose+svgPath(hs.d,style.skin,ink,1.35,'data-face-head="true"')+hairOpen+hf+hairClose;
 const profile=Math.abs(turn)>.68,eyeScale=profile?.88:1,sep=rx*id.eyes*(1-Math.abs(turn)*.42),eyeY=c.y-ry*.08,shift=turn*rx*.15;
 const eyeXs=profile?[c.x+shift+Math.sign(turn||1)*sep*.10]:[c.x+shift-sep,c.x+shift+sep];
 const lid=clamp(ex.lid*(1-blink),.04,1.25),er=Math.max(1.7,rx*.075)*eyeScale;
 for(const x of eyeXs){out+=`<ellipse cx="${f(x)}" cy="${f(eyeY)}" rx="${f(er)}" ry="${f(Math.max(.55,er*.78*lid))}" fill="${ink}"/>`;if(lid>.35)out+=`<circle cx="${f(x+gazeX*er*.5)}" cy="${f(eyeY+gazeY*er*.38)}" r="${f(er*.20)}" fill="#F8F5EF"/>`;}
 const browY=eyeY-ry*.16+ex.brow*ry,bw=rx*.23;for(const x of eyeXs)out+=`<path d="M ${f(x-bw)} ${f(browY+ex.brow*ry*.08)} Q ${f(x)} ${f(browY-ry*.025)} ${f(x+bw)} ${f(browY-ex.brow*ry*.08)}" fill="none" stroke="${ink}" stroke-width="1.35" stroke-linecap="round"/>`;
 const nx=c.x+turn*rx*.18,ny=c.y+ry*.10;if(id.nose==='bridge'||id.nose==='long')out+=`<path d="M ${f(nx)} ${f(c.y-ry*.03)} Q ${f(nx+turn*rx*.07+rx*.03)} ${f(ny)} ${f(nx+rx*.01)} ${f(ny+ry*(id.nose==='long'?.10:.05))}" fill="none" stroke="${ink}" stroke-width="1.05" stroke-linecap="round"/>`;else out+=circle({x:nx,y:ny},1.1,ink);
 let mouth=ex.mouth==='soft'?id.mouth:ex.mouth,open=Math.max(ex.open,vi.open),mw=rx*.28*vi.width,mouthY=c.y+ry*.36;
 if(open>.08||mouth==='o'||mouth==='open'){const mh=Math.max(2.2,ry*(.045+.10*open));out+=`<ellipse cx="${f(c.x+turn*rx*.08)}" cy="${f(mouthY)}" rx="${f(mw*.62)}" ry="${f(mh)}" fill="#6F3F3A" stroke="${ink}" stroke-width="1.0"/>`;if(open>.35)out+=`<path d="M ${f(c.x-mw*.30)} ${f(mouthY+mh*.10)} Q ${f(c.x)} ${f(mouthY+mh*.55)} ${f(c.x+mw*.30)} ${f(mouthY+mh*.10)}" stroke="#D88983" stroke-width="1.1" fill="none"/>`;}
 else {let md;if(mouth==='smile')md=`M ${f(c.x-mw)} ${f(mouthY-1)} Q ${f(c.x)} ${f(mouthY+ry*.10)} ${f(c.x+mw)} ${f(mouthY-1)}`;else if(mouth==='down')md=`M ${f(c.x-mw)} ${f(mouthY+ry*.05)} Q ${f(c.x)} ${f(mouthY-ry*.05)} ${f(c.x+mw)} ${f(mouthY+ry*.05)}`;else if(mouth==='side')md=`M ${f(c.x-mw*.75)} ${f(mouthY)} Q ${f(c.x+mw*.15)} ${f(mouthY+ry*.04)} ${f(c.x+mw*.65)} ${f(mouthY-ry*.01)}`;else if(mouth==='flat')md=`M ${f(c.x-mw*.75)} ${f(mouthY)} L ${f(c.x+mw*.75)} ${f(mouthY)}`;else md=`M ${f(c.x-mw)} ${f(mouthY)} Q ${f(c.x)} ${f(mouthY+ry*.04)} ${f(c.x+mw)} ${f(mouthY)}`;out+=`<path d="${md}" stroke="${ink}" stroke-width="1.25" fill="none" stroke-linecap="round"/>`;}
 if(id.facial!=='none'){const opacity=id.facial==='shortbeard'?.42:.28,sw=id.facial==='shortbeard'?4.8:id.facial==='goatee'?3.4:2.4;out+=`<path d="M ${f(c.x-rx*.55)} ${f(c.y+ry*.39)} Q ${f(c.x)} ${f(c.y+ry*.84)} ${f(c.x+rx*.55)} ${f(c.y+ry*.39)}" stroke="${style.hair}" stroke-width="${sw}" opacity="${opacity}" fill="none" stroke-linecap="round"/>`;}
 return out;
}

function mappedHandPose(raw){const p=raw||'relaxed';return({pregrasp:'receive',grip:'power_grip',open:'open',offer:'offer',handoff:'offer',precision:'precision_grip',support:'support_large',phone:'phone_hold'}[p]||HAND_POSES.includes(p)?({pregrasp:'receive',grip:'power_grip',open:'open',offer:'offer',handoff:'offer',precision:'precision_grip',support:'support_large',phone:'phone_hold'}[p]||p):'relaxed');}
function handSvg(P,side,d,style,rawPose,opts={}){
 const s=side==='left'?'l':'r',w=P['wrist_'+s],el=P['elbow_'+s],v=unit(el,w),n=perp(v),pose=mappedHandPose(opts.poseOverride||rawPose?.pose),orientation=opts.orientationOverride||rawPose?.orientation||'palm-front',oriScale=orientation.startsWith('edge')?.62:orientation==='foreshortened/contact'?.78:1,L=d.hand*1.58,W=d.hand*.75*oriScale,center=add(w,v,L*.38),ink='#2A2725',flip=(side==='left'?1:-1)*(orientation==='palm-back'?-1:1);
 const palmBase=add(center,v,-L*.34),palmTip=add(center,v,L*.23),palmD=`M ${f(add(palmBase,n,W*.45).x)} ${f(add(palmBase,n,W*.45).y)} Q ${f(add(palmTip,n,W*.50).x)} ${f(add(palmTip,n,W*.50).y)} ${f(add(palmTip,n,W*.18).x)} ${f(add(palmTip,n,W*.18).y)} Q ${f(add(palmTip,n,-W*.48).x)} ${f(add(palmTip,n,-W*.48).y)} ${f(add(palmBase,n,-W*.42).x)} ${f(add(palmBase,n,-W*.42).y)} Z`;
 let out=svgPath(palmD,style.skin,ink,1.05,`data-hand="${side}" data-hand-pose="${pose}" data-hand-orientation="${orientation}"`);
 const finger=(offset,lenMul,rad=.13,bend=0)=>{const base=add(palmTip,n,offset*W),dir=norm({x:v.x+n.x*bend,y:v.y+n.y*bend}),tip=add(base,dir,L*lenMul);return Mesh.ribbonSvg(base,mix(base,tip,.53),tip,{r0:W*rad,rj:W*rad*.92,r1:W*rad*.70,fill:style.skin,stroke:ink,strokeWidth:.85,steps:7,attrs:'data-finger="true"'});};
 if(['open','receive','offer','present','stop','support_large'].includes(pose)){out+=finger(-.43,.47,.12,-.06)+finger(-.14,.57,.12,-.02)+finger(.14,.59,.12,.02)+finger(.42,.52,.115,.07);}
 else if(['point','tap','count'].includes(pose)){out+=finger(.04,.66,.125,0)+finger(-.27,.32,.13,-.12)+finger(.30,.30,.13,.14);if(pose==='count')out+=finger(-.14,.58,.12,-.02);}
 else if(['pinch','precision_grip','type'].includes(pose)){out+=finger(.12,.46,.12,-.04)+finger(-.16,.31,.13,-.16)+finger(.35,.30,.12,.12);}
 else if(['power_grip','phone_hold'].includes(pose)){out+=`<path d="M ${f(add(palmTip,n,-W*.43).x)} ${f(add(palmTip,n,-W*.43).y)} Q ${f(add(palmTip,v,L*.29).x)} ${f(add(palmTip,v,L*.29).y)} ${f(add(palmTip,n,W*.43).x)} ${f(add(palmTip,n,W*.43).y)}" stroke="${ink}" stroke-width="${f(W*.67)}" fill="none" stroke-linecap="round"/>`;}
 else out+=finger(-.18,.34,.13,-.08)+finger(.16,.36,.13,.08);
 const thumbBase=add(center,n,flip*W*.40),thumbTip=add(add(thumbBase,v,L*.20),n,flip*W*.34);out+=Mesh.ribbonSvg(thumbBase,mix(thumbBase,thumbTip,.55),thumbTip,{r0:W*.15,rj:W*.14,r1:W*.10,fill:style.skin,stroke:ink,strokeWidth:.8,steps:6});
 return out;
}
function footStateFor(result,side){const a=result.state?.action||result.state?.originalAction||'';if(a==='sit')return'seated';if(['low_pickup','table_pickup','pickup'].includes(a))return'crouched/bent';if(['walk','run','dance','sprint'].includes(a)){const s=side==='left'?'l':'r',ank=result.state.pose3d?.['ankle_'+s],toe=result.state.pose3d?.['toe_'+s];if(ank&&ank[1]>.13)return'swing';if(ank&&toe&&ank[1]-toe[1]>.035)return'heel-lift';if(ank&&toe&&toe[1]-ank[1]>.035)return'toe-off';}return'plant';}
function footSvg(P,side,d,style,result){const s=side==='left'?'l':'r',a=P['ankle_'+s],t=P['toe_'+s]||{x:a.x+(side==='left'?-18:18),y:a.y},v=unit(a,t),n=perp(v),L=Math.max(14,len(sub(t,a)))+d.foot*.75,W=d.foot,heel=add(a,v,-W*.32),ball=add(a,v,L*.54),tip=add(a,v,L),h1=add(heel,n,W*.38),h2=add(heel,n,-W*.38),b1=add(ball,n,W*.43),b2=add(ball,n,-W*.50),tt=add(tip,n,-W*.13),state=footStateFor(result,side);const dd=`M ${f(h1.x)} ${f(h1.y)} Q ${f(b1.x)} ${f(b1.y)} ${f(tip.x)} ${f(tip.y)} Q ${f(tt.x)} ${f(tt.y)} ${f(b2.x)} ${f(b2.y)} Q ${f(h2.x)} ${f(h2.y)} ${f(heel.x)} ${f(heel.y)} Z`;return svgPath(dd,style.shoe,'#292725',1.2,`data-foot="${side}" data-foot-state="${state}"`);}


function limbSkin(result,P,G,d,style){let back=[],front=[];const torsoDepth=((P.chest?.depth||0)+(P.pelvis?.depth||0))/2;
 for(const [side,s,root] of [['left','l',G.socketL],['right','r',G.socketR]]){const e=P['elbow_'+s],w=P['wrist_'+s],depth=((root.depth||0)+(e.depth||0)+(w.depth||0))/3,svg=Mesh.ribbonSvg(root,e,w,{r0:d.ua*1.04,rj:Math.max(d.fa*1.02,d.ua*.82),r1:d.fa*.58,fill:style.skin,stroke:'#292725',strokeWidth:1.15,steps:16,volumePreserve:.16,attrs:`data-skin-arm="${side}"`});(depth<torsoDepth?back:front).push(svg);}
 for(const [side,s,root] of [['left','l',G.hipRootL],['right','r',G.hipRootR]]){const k=P['knee_'+s],a=P['ankle_'+s],depth=((root.depth||0)+(k.depth||0)+(a.depth||0))/3,svg=Mesh.ribbonSvg(root,k,a,{r0:d.thigh*1.03,rj:Math.max(d.calf*1.08,d.thigh*.78),r1:d.calf*.56,fill:style.skin,stroke:'#292725',strokeWidth:1.15,steps:16,volumePreserve:.14,attrs:`data-skin-leg="${side}"`});(depth<torsoDepth?back:front).push(svg);}
 return{back:back.join(''),front:front.join('')};
}
function garmentKinds(preset){const i=preset.items||{};return{upper:i.upper||'',lower:i.lower||'',full:i.full_body||'',outer:i.outerwear||'',footwear:i.footwear||''};}
function secondaryMotion(result){const a=result.state?.action||'',active=['walk','run','dance','sprint','jump'].includes(a),amp=active?(a==='dance'?1:0.55):0.18,t=+result.time||+result.state?.time||0;return clamp(Math.sin(t*7.1+result.familyId.length*.37)*amp,-1,1);}
function clothing(result,P,G,d,style){const preset=clothingPreset(result),g=garmentKinds(preset),ink='#292725',rootInset=Math.max(3,d.ua*.70),legInset=Math.max(2,d.thigh*.38),secondary=secondaryMotion(result);let back='',core='',front='';
 const longSleeve=!!g.outer||g.upper.includes('shirt')||g.upper.includes('sweater')||g.upper.includes('hood')||g.upper.includes('work');
 const sleeveColor=g.outer?mixColor(style.top,'#252525',.12):style.top;
 for(const [side,s,socket] of [['left','l',G.socketL],['right','r',G.socketR]]){const e=P['elbow_'+s],w=P['wrist_'+s],toward=unit(socket,G.chest),root=add(socket,toward,rootInset),end=longSleeve?mix(e,w,.78):mix(root,e,.58),midJ=longSleeve?e:mix(root,end,.56),depth=((socket.depth||0)+(e.depth||0)+(w.depth||0))/3,svg=Mesh.ribbonSvg(root,midJ,end,{r0:d.ua*1.18,rj:Math.max(d.ua*.85,d.fa*1.02),r1:(longSleeve?d.fa:d.ua)*.80,fill:sleeveColor,stroke:ink,strokeWidth:1.1,steps:14,volumePreserve:.13,attrs:`data-garment-sleeve="${side}"`});if(depth<((P.chest?.depth||0)+(P.pelvis?.depth||0))/2)back+=svg;else front+=svg;}
 // lower garments: trousers/jeans/shorts or skirt/dress, always rooted inside pelvis.
 const isDress=!!g.full&&g.full.includes('dress'),isSkirt=g.lower.includes('skirt')||isDress,isShorts=g.lower.includes('short');
 if(isSkirt){const knee=mid(P.knee_l,P.knee_r),axis=unit(G.hipC,knee),ratio=isDress?.78:.66,hem=add(add(G.hipC,axis,Math.max(27,len(sub(knee,G.hipC))*ratio)),G.side,secondary*1.6),spread=G.hp*(isDress?1.20:1.16),lT=add(G.hipC,G.side,G.hp*.97),rT=add(G.hipC,G.side,-G.hp*.97),lH=add(hem,G.side,spread),rH=add(hem,G.side,-spread);core+=svgPath(`M ${f(lT.x)} ${f(lT.y)} C ${f(add(lT,axis,15).x)} ${f(add(lT,axis,15).y)} ${f(lH.x)} ${f(lH.y)} ${f(lH.x)} ${f(lH.y)} Q ${f(hem.x)} ${f(hem.y+3)} ${f(rH.x)} ${f(rH.y)} C ${f(rH.x)} ${f(rH.y)} ${f(add(rT,axis,15).x)} ${f(add(rT,axis,15).y)} ${f(rT.x)} ${f(rT.y)} Z`,style.lower,ink,1.15,'data-garment="skirt"');}
 else for(const [side,s,root0] of [['left','l',G.hipRootL],['right','r',G.hipRootR]]){const k=P['knee_'+s],a=P['ankle_'+s],root=add(root0,unit(root0,G.hipC),legInset),end=isShorts?mix(root,k,.58):a,joint=isShorts?mix(root,end,.54):k;core+=Mesh.ribbonSvg(root,joint,end,{r0:d.thigh*1.12,rj:isShorts?d.thigh*.94:Math.max(d.thigh*.80,d.calf*.98),r1:isShorts?d.thigh*.78:d.calf*.55,fill:style.lower,stroke:ink,strokeWidth:1.1,steps:14,volumePreserve:.10,attrs:`data-garment-leg="${side}"`});}
 // torso garment owns the shoulder/sleeve seam and hides all roots.
 const shoulder=g.outer?G.sh+3:G.sh+1.5,hip=G.hp+1.8,wa=G.wa+1,nL=add(G.neck,G.side,d.neck*.49),nR=add(G.neck,G.side,-d.neck*.49),sL=add(add(G.shC,G.axis,-3),G.side,shoulder),sR=add(add(G.shC,G.axis,-3),G.side,-shoulder),aL=add(add(G.shC,G.axis,8),G.side,shoulder*.86),aR=add(add(G.shC,G.axis,8),G.side,-shoulder*.86),wL=add(G.waC,G.side,wa),wR=add(G.waC,G.side,-wa),hL=add(G.hipC,G.side,hip),hR=add(G.hipC,G.side,-hip);
 const torsoD=`M ${f(nL.x)} ${f(nL.y)} C ${f(add(sL,G.axis,-7).x)} ${f(add(sL,G.axis,-7).y)} ${f(sL.x)} ${f(sL.y)} ${f(aL.x)} ${f(aL.y)} C ${f(wL.x)} ${f(wL.y)} ${f(wL.x)} ${f(wL.y)} ${f(hL.x)} ${f(hL.y)} Q ${f(G.hipC.x)} ${f(G.hipC.y+5)} ${f(hR.x)} ${f(hR.y)} C ${f(wR.x)} ${f(wR.y)} ${f(wR.x)} ${f(wR.y)} ${f(aR.x)} ${f(aR.y)} C ${f(sR.x)} ${f(sR.y)} ${f(add(sR,G.axis,-7).x)} ${f(add(sR,G.axis,-7).y)} ${f(nR.x)} ${f(nR.y)} Q ${f(G.neck.x)} ${f(G.neck.y+4)} ${f(nL.x)} ${f(nL.y)} Z`;
 core+=svgPath(torsoD,g.outer?mixColor(style.top,'#202020',.10):style.top,ink,1.2,'data-garment="torso"');
 // authored detailing makes garments readable without replacing the coherent body master.
 const cx=G.chest.x,cy=G.chest.y,collarY=G.neck.y+8,detail=style.accent;
 if(g.upper.includes('shirt')||g.outer.includes('blazer')||g.outer.includes('jacket')){core+=`<path d="M ${f(G.neck.x-d.neck*.40)} ${f(collarY)} L ${f(cx-4)} ${f(collarY+10)} L ${f(cx)} ${f(collarY+4)} L ${f(cx+4)} ${f(collarY+10)} L ${f(G.neck.x+d.neck*.40)} ${f(collarY)}" fill="none" stroke="${ink}" stroke-width="1.05" stroke-linejoin="round"/>`;for(let i=0;i<3;i++)core+=circle({x:cx,y:cy+8+i*10},1.05,detail);}
 if(g.outer.includes('blazer')){core+=`<path d="M ${f(G.neck.x-3)} ${f(collarY+2)} L ${f(cx-10)} ${f(cy+20)} L ${f(cx-2)} ${f(cy+11)} L ${f(cx)} ${f(G.waC.y-2)} M ${f(G.neck.x+3)} ${f(collarY+2)} L ${f(cx+10)} ${f(cy+20)} L ${f(cx+2)} ${f(cy+11)}" fill="none" stroke="${ink}" stroke-width="1.15"/>`;}
 if(g.outer.includes('hood')){core+=`<path d="M ${f(G.neck.x-d.neck*.85)} ${f(G.neck.y+4)} Q ${f(G.neck.x)} ${f(G.neck.y-8)} ${f(G.neck.x+d.neck*.85)} ${f(G.neck.y+4)}" fill="none" stroke="${detail}" stroke-width="4.2" stroke-linecap="round"/><path d="M ${f(cx-13)} ${f(G.waC.y-9)} Q ${f(cx)} ${f(G.waC.y+1)} ${f(cx+13)} ${f(G.waC.y-9)}" fill="none" stroke="${ink}" stroke-width="1"/>`;}
 if(g.upper.includes('tshirt'))core+=`<path d="M ${f(G.neck.x-d.neck*.50)} ${f(G.neck.y+3)} Q ${f(G.neck.x)} ${f(G.neck.y+10)} ${f(G.neck.x+d.neck*.50)} ${f(G.neck.y+3)}" fill="none" stroke="${ink}" stroke-width="1"/>`;
 if(g.upper.includes('work')||g.outer.includes('work'))core+=`<rect x="${f(cx+5)}" y="${f(cy+3)}" width="12" height="9" rx="1.5" fill="none" stroke="${ink}" stroke-width="1"/><circle cx="${f(cx-10)}" cy="${f(cy+7)}" r="2.6" fill="${detail}"/>`;
 if(!isSkirt&&!isShorts)core+=`<path d="M ${f(G.hipC.x-G.hp*.75)} ${f(G.hipC.y+4)} Q ${f(G.hipC.x)} ${f(G.hipC.y+8)} ${f(G.hipC.x+G.hp*.75)} ${f(G.hipC.y+4)}" fill="none" stroke="${ink}" stroke-width="1" opacity=".8"/>`;
 return{back,core,front,presetId:preset.id};
}
function mixColor(a,b,t){const pa=parseInt(a.slice(1),16),pb=parseInt(b.slice(1),16),ar=pa>>16,ag=(pa>>8)&255,ab=pa&255,br=pb>>16,bg=(pb>>8)&255,bb=pb&255;return'#'+[ar+(br-ar)*t,ag+(bg-ag)*t,ab+(bb-ab)*t].map(x=>Math.round(x).toString(16).padStart(2,'0')).join('');}
function contextMarkup(result,pr,style){let out='';const projectWorld=p=>NS.project({root:result.state.pose3d.root,x:p},{...pr.camera,root_center:true}).x;if(result.state.prop?.position){const q=projectWorld(result.state.prop.position),sx=Math.max(15,(result.state.prop.size?.[0]||.12)*pr.scale),sy=Math.max(10,(result.state.prop.size?.[1]||result.state.prop.size?.[2]||.08)*pr.scale*.7);out+=`<rect data-context="prop" x="${f(q.x-sx/2)}" y="${f(q.y-sy/2)}" width="${f(sx)}" height="${f(sy)}" rx="6" fill="${style.accent}" stroke="#292725" stroke-width="1.2"/>`;}return out;}
function expressionState(result,opts={}){let expression=opts.expression||'neutral';const a=result.state?.action||result.state?.originalAction||'';if(!opts.expression){if(['talk','conversation'].includes(a))expression='speaking';else if(['dance','jump','sprint'].includes(a))expression='happy';else if(['interact','captured_reach','pickup','low_pickup'].includes(a))expression='attentive';}return{expression,blink:clamp(opts.blink??0,0,1),gazeX:clamp(opts.gazeX??0,-1,1),gazeY:clamp(opts.gazeY??0,-1,1),viseme:opts.viseme||((expression==='speaking')?'A':'rest')};}
function render(result,opts={}){
 const w=opts.width||360,h=opts.height||440;if(!result||result.blocked||!result.state?.pose3d)return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><rect width="100%" height="100%" fill="#F8F6F1"/><text x="18" y="36" font-family="sans-serif">BLOCKED</text></svg>`;
 const pr=project(result,{...opts,width:w,height:h}),P=pr.P,d=dims(result,pr.scale),style=styleFor(result,opts),G=bodyGeometry(P,d),skin=limbSkin(result,P,G,d,style),garments=clothing(result,P,G,d,style),identityId=opts.identityId||style.identity,id=IDENTITIES[identityId]||IDENTITIES['NA-01'],ex=expressionState(result,opts),ink='#292725';
 const bg=opts.background===null?'':`<rect width="100%" height="100%" fill="${opts.background||'#F8F6F1'}"/>`;
 let body='';body+=contextMarkup(result,pr,style);body+=`<g data-layer="back-skin">${skin.back}</g>`;
 // Torso-owned skin mass and front limbs are completed before garments; clothing then
 // covers the same anatomy without allowing skin to punch through trousers/sleeves.
 body+=`<g data-layer="core-skin">${svgPath(G.path,style.skin,ink,1.2,'data-skin-torso="true"')}</g><g data-layer="front-skin">${skin.front}</g>`;
 body+=`<g data-layer="back-clothing">${garments.back}</g><g data-layer="core-clothing">${garments.core}</g><g data-layer="front-clothing">${garments.front}</g>`;
 body+=`<g data-layer="hands-feet">${handSvg(P,'left',d,style,result.state.hands?.left,{poseOverride:opts.leftHandPose,orientationOverride:opts.leftHandOrientation})}${handSvg(P,'right',d,style,result.state.hands?.right,{poseOverride:opts.rightHandPose,orientationOverride:opts.rightHandOrientation})}${footSvg(P,'left',d,style,result)}${footSvg(P,'right',d,style,result)}</g>`;
 // neck is soft and hidden partially by the neckline, no exposed hinge.
 const neckEnd=mix(G.neck,P.head,.52);body+=`<g data-layer="head"><path d="${Mesh.ribbon(G.neck,mix(G.neck,neckEnd,.55),neckEnd,{r0:d.neck*.48,rj:d.neck*.47,r1:d.neck*.43,steps:8}).d}" fill="${style.skin}" stroke="${ink}" stroke-width="1"/>${faceSvg(P.head,d.headRx,d.headRy,identityId,style,{...ex,turn:pr.faceTurn,hairSway:secondaryMotion(result)*1.8})}</g>`;
 return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" data-surface="${VERSION}" data-master-kind="${masterKind(result.familyId)}" data-family="${esc(result.familyId)}" data-identity="${esc(identityId)}" data-view="${esc(pr.viewFamily)}" data-clothing="${esc(garments.presetId)}">${bg}<g>${body}</g></svg>`;
}
function faceCloseup(familyId,{width=220,height=220,identityId,expression='neutral',blink=0,gazeX=0,gazeY=0,viseme='rest',viewFamily='front',hideHair=false}={}){const style=STYLE[familyId]||STYLE.neutral_adult,id=identityId||style.identity,c={x:width/2,y:height/2+8},child=masterKind(familyId)==='child',rx=child?54:49,ry=child?61:64,turn=(VIEWS[viewFamily]||VIEWS.front).face;return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}"><rect width="100%" height="100%" fill="#F8F6F1"/>${faceSvg(c,rx,ry,id,style,{expression,blink,gazeX,gazeY,viseme,turn,hideHair})}</svg>`;}
function geometryContract(result,opts={}){if(!result||result.blocked)return{blocked:true};const pr=project(result,opts),d=dims(result,pr.scale),G=bodyGeometry(pr.P,d);return{blocked:false,version:VERSION,familyId:result.familyId,masterKind:masterKind(result.familyId),viewFamily:pr.viewFamily,anchors:{shoulderL:G.socketL,shoulderR:G.socketR,hipL:G.hipRootL,hipR:G.hipRootR,neck:G.neck,chest:G.chest,pelvis:G.pelvis},dimensions:d};}
function contract(){return{name:'NexStickAuthoredSurfaceV1',version:VERSION,scope:'render-surface-and-authored-appearance',mutatesMotion:false,motionAuthority:'NexPerformance/NexStick',deformation:Mesh.version,primaryMasters:['adult_male','adult_female','child'],derivedMasters:['neutral_adult','neutral_child','diminutive adult/child','broad/tall variants'],identityCount:Object.keys(IDENTITIES).length,viewFamilies:Object.keys(VIEWS),expressions:Object.keys(EXPRESSIONS),visemes:Object.keys(VISEMES),handPoses:HAND_POSES,handOrientations:HAND_ORIENTATIONS,footStates:FOOT_STATES,guarantees:['torso-owned shoulder mass','pelvis-owned hip mass','continuous elbow/knee deformation','no hinge discs','clothing roots share body geometry','independent face/gaze/hand state','bounded deterministic hair/skirt secondary motion','deterministic SVG output'],doesNotOwn:['motion generation','world contact','role casting','storyboard direction']};}
module.exports={version:VERSION,render,faceCloseup,geometryContract,contract,IDENTITIES,EXPRESSIONS,VISEMES,VIEWS,HAND_POSES,HAND_ORIENTATIONS,FOOT_STATES,MASTER_KIND,STYLE,masterKind,footStateFor};
