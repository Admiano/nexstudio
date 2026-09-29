window.NexPaperObjects = (()=>{
 const registry=window.NEX_OBJECTS||[];
 const defaults={title:'A PAPER IDEA',body:'Replace this text through the component configuration. Every element remains editable.',price:'$24',meta:'NEXSTUDIO / 2026'};
 const esc=s=>String(s??'').replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
 function text(config,key,fallback){return esc(config[key]??fallback)}
 function media(config){const src=config.media||'';return src?`<img class="replaceable-media" src="${esc(src)}" alt="">`:`<div class="media-placeholder"><span>IMAGE</span><small>replaceable media</small></div>`}
 function lines(body,count=5){const words=String(body||defaults.body).split(/\s+/);let out=[];for(let i=0;i<count;i++)out.push(`<span style="width:${Math.max(38,92-i*8)}%">${esc(words.slice(i*4,i*4+4).join(' ')||'editable paper text')}</span>`);return out.join('')}
 function inner(def,c){const t=text(c,'title',defaults.title),b=text(c,'body',defaults.body),m=text(c,'meta',defaults.meta),p=text(c,'price',defaults.price);switch(def.renderer){
 case 'rectangular-card':return `<div class="object-face card-face"><div class="eyebrow">${m}</div><h3 data-fit>${t}</h3><p data-fit>${b}</p><div class="rule"></div></div>`;
 case 'torn-strip':return `<div class="object-face strip-face"><strong data-fit>${t}</strong><span>${m}</span></div>`;
 case 'sticky-note':return `<div class="object-face sticky-face"><div class="sticky-pin"></div><h3 data-fit>${t}</h3><p data-fit>${b}</p><i class="peel-corner"></i></div>`;
 case 'index-card':return `<div class="object-face index-face"><div class="index-rule red"></div><h3 data-fit>${t}</h3><p data-fit>${b}</p><div class="index-lines"></div></div>`;
 case 'notebook-page':return `<div class="object-face notebook-face"><div class="holes">${'<i></i>'.repeat(5)}</div><h3 data-fit>${t}</h3><div class="written-lines">${lines(b,6)}</div></div>`;
 case 'graph-page':return `<div class="object-face graph-face"><div class="axis axis-x"></div><div class="axis axis-y"></div><div class="plot-line"></div><h3 data-fit>${t}</h3></div>`;
 case 'kraft-card':return `<div class="object-face kraft-face"><div class="kraft-stamp">${m}</div><h3 data-fit>${t}</h3><p data-fit>${b}</p></div>`;
 case 'photo-sheet':return `<div class="object-face photo-face">${media(c)}<div class="photo-caption" data-fit>${t}</div></div>`;
 case 'printed-label':return `<div class="object-face label-face"><span>${m}</span><strong data-fit>${t}</strong></div>`;
 case 'hanging-tag':return `<div class="tag-string"><svg viewBox="0 0 100 80"><path d="M50 2 C12 20 86 48 52 78"/></svg></div><div class="object-face tag-face"><i class="tag-hole"></i><strong data-fit>${t}</strong><small data-fit>${b}</small></div>`;
 case 'paper-tab':return `<div class="object-face tab-face"><strong data-fit>${t}</strong></div>`;
 case 'bookmark':return `<div class="object-face bookmark-face"><span>${m}</span><strong data-fit>${t}</strong><i></i></div>`;
 case 'speech-bubble':return `<div class="object-face speech-face"><p data-fit>${b}</p><div class="speech-dots"><i></i><i></i><i></i></div></div>`;
 case 'thought-bubble':return `<div class="thought-orbs"><i></i><i></i></div><div class="object-face thought-face"><p data-fit>${b}</p></div>`;
 case 'price-sticker':return `<div class="object-face price-face"><small>${t}</small><strong data-fit>${p}</strong><span>${m}</span></div>`;
 case 'announcement-sticker':return `<div class="object-face announcement-face"><span>NEW</span><strong data-fit>${t}</strong><small data-fit>${b}</small></div>`;
 case 'approval-seal':return `<div class="object-face seal-face"><div class="seal-ring"><span>APPROVED</span><strong data-fit>${t}</strong><small>${m}</small></div></div>`;
 case 'event-ticket':return `<div class="object-face ticket-face"><div class="ticket-main"><small>${m}</small><h3 data-fit>${t}</h3><p data-fit>${b}</p></div><div class="ticket-stub"><strong>01</strong><span>ADMIT</span></div></div>`;
 case 'receipt':return `<div class="object-face receipt-face"><h3 data-fit>${t}</h3><div class="receipt-lines">${lines(b,6)}</div><div class="receipt-total"><span>TOTAL</span><strong>${p}</strong></div></div>`;
 case 'newspaper-clipping':return `<div class="object-face news-face"><div class="masthead">THE PAPER DAILY</div><h3 data-fit>${t}</h3><div class="news-columns"><p data-fit>${b}</p><p data-fit>${b}</p></div><small>${m}</small></div>`;
 case 'magazine-clipping':return `<div class="object-face magazine-face">${media(c)}<div class="magazine-copy"><small>${m}</small><h3 data-fit>${t}</h3><p data-fit>${b}</p></div></div>`;
 case 'closed-envelope':return `<div class="object-face envelope-face"><div class="envelope-flap"></div><div class="envelope-label"><small>TO</small><strong data-fit>${t}</strong></div><div class="seal-dot"></div></div>`;
 case 'opening-envelope':return `<div class="letter-insert"><h3 data-fit>${t}</h3><div>${lines(b,4)}</div></div><div class="object-face envelope-face opening"><div class="envelope-flap"></div><div class="envelope-front"></div></div>`;
 case 'letter-sheet':return `<div class="object-face letter-face"><div class="letter-head"><strong>${t}</strong><small>${m}</small></div><div class="letter-lines">${lines(b,8)}</div><div class="signature">NexStudio</div></div>`;
 case 'postcard':return `<div class="object-face postcard-face"><div class="postcard-image">${media(c)}</div><div class="postcard-copy"><div class="stamp-box">STAMP</div><strong data-fit>${t}</strong><p data-fit>${b}</p></div></div>`;
 case 'certificate':return `<div class="object-face certificate-face"><div class="certificate-border"><small>CERTIFICATE OF</small><h3 data-fit>${t}</h3><p data-fit>${b}</p><div class="certificate-seal"></div></div></div>`;
 case 'checklist-sheet':return `<div class="object-face checklist-face"><h3 data-fit>${t}</h3><ul><li><i></i><span>Plan the story</span></li><li><i></i><span>Build the scene</span></li><li><i></i><span>Validate motion</span></li><li><i></i><span>Render output</span></li></ul></div>`;
 case 'folder':return `<div class="folder-sheet"><h3 data-fit>${t}</h3><p data-fit>${b}</p></div><div class="object-face folder-face"><div class="folder-tab">${m}</div><div class="folder-front"><strong data-fit>${t}</strong></div></div>`;
 case 'document-stack':return `<div class="stack-sheet s3"></div><div class="stack-sheet s2"></div><div class="stack-sheet s1"><small>${m}</small><h3 data-fit>${t}</h3><div>${lines(b,4)}</div></div>`;
 case 'paper-stack':return `<div class="stack-sheet p4"></div><div class="stack-sheet p3"></div><div class="stack-sheet p2"></div><div class="stack-sheet p1"><h3 data-fit>${t}</h3></div>`;
 case 'folded-note':return `<div class="object-face folded-face"><div class="fold-panel left"></div><div class="fold-panel right"></div><div class="fold-message"><h3 data-fit>${t}</h3><p data-fit>${b}</p></div></div>`;
 case 'crumpled-ball':return `<div class="object-face crumple-face"><i></i><i></i><i></i><h3 data-fit>${t}</h3></div>`;
 case 'irregular-scrap':return `<div class="object-face scrap-face"><small>${m}</small><h3 data-fit>${t}</h3><p data-fit>${b}</p></div>`;
 case 'ripped-hole':return `<div class="reveal-content"><h3 data-fit>${t}</h3><p data-fit>${b}</p></div><div class="object-face hole-face"><div class="hole-mask"></div></div>`;
 case 'masking-tape':return `<div class="attachment-face masking-tape"><span>${t}</span></div>`;
 case 'clear-tape':return `<div class="attachment-face clear-tape"><i class="tape-sheen"></i></div>`;
 case 'staple-attachment':return `<div class="attachment-face staple-object"><i></i></div>`;
 case 'paperclip-attachment':return `<div class="attachment-face paperclip-object"><i></i></div>`;
 case 'pushpin-attachment':return `<div class="attachment-face pushpin-object"><i></i></div>`;
 case 'string-connector':return `<div class="attachment-face string-object"><svg viewBox="0 0 240 150" preserveAspectRatio="none"><path d="M8 118 C68 8 170 150 232 34"/><circle cx="8" cy="118" r="7"/><circle cx="232" cy="34" r="7"/></svg></div>`;
 default:return `<div class="object-face"><h3>${t}</h3></div>`;}}
 function fitText(root){root.querySelectorAll('[data-fit]').forEach(el=>{el.style.fontSize='';el.style.lineHeight='';let size=parseFloat(getComputedStyle(el).fontSize)||18;const min=6;let guard=0;while((el.scrollHeight>el.clientHeight+2||el.scrollWidth>el.clientWidth+2)&&size>min&&guard<60){size-=.5;el.style.fontSize=size+'px';el.style.lineHeight='1';guard++;}if(el.scrollWidth>el.clientWidth+2){el.style.letterSpacing='-.06em';}})}
 function create(defOrId,config={}){const def=typeof defOrId==='string'?registry.find(x=>x.id===defOrId):defOrId;if(!def)throw new Error('Unknown paper object: '+defOrId);const wrap=document.createElement('div');wrap.className=`paper-object ${def.cssClass} subtype-${def.subtype}`;wrap.dataset.componentId=def.id;wrap.dataset.subtype=def.subtype;wrap.dataset.paperStyle=config.style||document.documentElement.dataset.paperStyle||'clean-editorial';wrap.setAttribute('role','img');wrap.setAttribute('aria-label',def.accessibilityLabel);wrap.style.setProperty('--object-scale',config.scale||1);wrap.innerHTML=`<div class="object-stage">${inner(def,{...defaults,...config})}<div class="object-grain"></div></div>`;requestAnimationFrame(()=>fitText(wrap));return wrap;}
 function getParts(el){return {stage:el.querySelector('.object-stage'),face:el.querySelector('.object-face,.attachment-face,.stack-sheet.s1,.stack-sheet.p1'),detail:el.querySelector('.peel-corner,.tag-string,.speech-dots,.thought-orbs,.seal-ring,.ticket-stub,.receipt-lines,.news-columns,.envelope-flap,.letter-insert,.checklist-face ul,.folder-sheet,.stack-sheet.s2,.fold-panel,.crumple-face i,.hole-mask,.tape-sheen,.staple-object i,.paperclip-object i,.pushpin-object i,.string-object path')};}
 function animate(el,motion,energy='medium'){const def=registry.find(x=>x.id===el.dataset.componentId);motion=motion||def?.defaultMotion||'paper-slide';const mult={low:1.22,medium:1,high:.78}[energy]||1,amp={low:.75,medium:1,high:1.22}[energy]||1;const {stage,face,detail}=getParts(el);const tl=gsap.timeline({paused:true,defaults:{ease:'power3.out'}});const d=.65*mult;
  const entry={
   'paper-slide':()=>tl.fromTo(stage,{opacity:0,x:-70*amp,y:18,rotation:-2},{opacity:1,x:0,y:0,rotation:0,duration:d,ease:'expo.out'},.08),
   'unfold':()=>{tl.fromTo(stage,{opacity:0,scale:.48,rotation:-7},{opacity:1,scale:1,rotation:0,duration:d*1.2,ease:'back.out(1.7)'},.08);if(detail)tl.fromTo(detail,{opacity:0,y:35,scale:.65,rotation:-5},{opacity:1,y:0,scale:1,rotation:0,duration:d,ease:'expo.out'},.30)},
   'peel':()=>{tl.fromTo(stage,{opacity:0,y:42,rotation:-5,scale:.88},{opacity:1,y:0,rotation:0,scale:1,duration:d,ease:'back.out(1.7)'},.08);if(detail)tl.fromTo(detail,{opacity:0,rotation:-28,scale:.4},{opacity:1,rotation:0,scale:1,duration:d*.75,ease:'expo.out'},.32)},
   'drop-settle':()=>tl.fromTo(stage,{opacity:0,y:-95*amp,rotation:5,scale:.92},{opacity:1,y:0,rotation:0,scale:1,duration:d*1.1,ease:'back.out(1.7)'},.08),
   'stamp':()=>{tl.fromTo(stage,{opacity:0,scale:1.75,rotation:-7},{opacity:1,scale:.94,rotation:1,duration:d*.55,ease:'power3.out'},.08);tl.to(stage,{scale:1,rotation:0,duration:d*.35,ease:'back.out(1.7)'},.08+d*.55)},
   'stack-shuffle':()=>{tl.fromTo(stage,{opacity:0,y:50,rotation:-5,scale:.88},{opacity:1,y:0,rotation:0,scale:1,duration:d,ease:'back.out(1.7)'},.08);el.querySelectorAll('.stack-sheet').forEach((x,i)=>tl.fromTo(x,{opacity:0,x:(i-1)*35,y:-22*i,rotation:(i-1)*8},{opacity:1,x:0,y:0,rotation:0,duration:d*.75,ease:'expo.out'},.18+i*.09))},
   'page-flip':()=>{tl.fromTo(stage,{opacity:0,x:-45,scale:.92,rotation:-8},{opacity:1,x:0,scale:1,rotation:0,duration:d,ease:'expo.out'},.08);if(face)tl.fromTo(face,{rotation:-12,scale:.8},{rotation:0,scale:1,duration:d*.8,ease:'back.out(1.7)'},.18)},
   'crumple-flatten':()=>{tl.fromTo(stage,{opacity:0,scale:.25,rotation:-30},{opacity:1,scale:.62,rotation:10,duration:d*.55,ease:'back.out(1.7)'},.08);tl.to(stage,{scale:1,rotation:0,duration:d*.8,ease:'expo.out'},.08+d*.5)},
   'tape-down':()=>{tl.fromTo(stage,{opacity:0,y:-65,rotation:-18,scale:1.1},{opacity:1,y:0,rotation:-3,scale:1,duration:d,ease:'back.out(1.7)'},.08);if(detail)tl.fromTo(detail,{opacity:0,x:-85},{opacity:1,x:85,duration:d*.9,ease:'sine.inOut'},.30)},
   'pin-board':()=>{tl.fromTo(stage,{opacity:0,y:-75,scale:1.28,rotation:9},{opacity:1,y:0,scale:1,rotation:0,duration:d,ease:'back.out(1.7)'},.08);if(detail)tl.fromTo(detail,{opacity:0,y:-32,scale:1.5},{opacity:1,y:0,scale:1,duration:d*.55,ease:'power3.out'},.28)},
   'tear-reveal':()=>{tl.fromTo(stage,{opacity:0,x:-65,rotation:-4,scale:.9},{opacity:1,x:0,rotation:0,scale:1,duration:d,ease:'expo.out'},.08);if(detail)tl.fromTo(detail,{opacity:0,scale:.12,rotation:-18},{opacity:1,scale:1,rotation:0,duration:d*.9,ease:'back.out(1.7)'},.25)},
   'lift-hover':()=>{tl.fromTo(stage,{opacity:0,y:35,scale:.9},{opacity:1,y:-7,scale:1,rotation:1,duration:d,ease:'back.out(1.7)'},.08);tl.to(stage,{y:0,rotation:0,duration:d*.6,ease:'sine.inOut'},.08+d)}
  };(entry[motion]||entry['paper-slide'])();
  bespoke(el,tl,d,def?.renderer);return tl;}
 function bespoke(el,tl,d,type){const q=s=>el.querySelector(s),qa=s=>[...el.querySelectorAll(s)];switch(type){
  case 'sticky-note':if(q('.peel-corner'))tl.fromTo(q('.peel-corner'),{rotation:-35,scale:.4},{rotation:0,scale:1,duration:d*.7,ease:'back.out(1.7)'},.42);break;
  case 'hanging-tag':tl.fromTo(q('.tag-string'),{opacity:0,scale:.45,rotation:-16},{opacity:1,scale:1,rotation:0,duration:d*.8,ease:'expo.out'},.18);tl.fromTo(q('.tag-face'),{rotation:13},{rotation:-2,duration:d*.8,ease:'sine.inOut'},.32);break;
  case 'speech-bubble':qa('.speech-dots i').forEach((x,i)=>tl.fromTo(x,{opacity:0,scale:.1,y:7},{opacity:1,scale:1,y:0,duration:d*.35,ease:'back.out(1.7)'},.42+i*.09));break;
  case 'thought-bubble':qa('.thought-orbs i').forEach((x,i)=>tl.fromTo(x,{opacity:0,scale:.1},{opacity:1,scale:1,duration:d*.45,ease:'back.out(1.7)'},.18+i*.1));break;
  case 'approval-seal':tl.fromTo(q('.seal-ring'),{opacity:0,scale:2.2,rotation:-22},{opacity:1,scale:1,rotation:-7,duration:d*.72,ease:'back.out(1.7)'},.24);break;
  case 'event-ticket':tl.fromTo(q('.ticket-stub'),{opacity:0,x:35,rotation:8},{opacity:1,x:0,rotation:0,duration:d*.65,ease:'expo.out'},.42);break;
  case 'receipt':qa('.receipt-lines span').forEach((x,i)=>tl.fromTo(x,{opacity:0,x:-20},{opacity:1,x:0,duration:d*.28,ease:'power3.out'},.35+i*.07));break;
  case 'newspaper-clipping':tl.fromTo(q('.news-columns'),{opacity:0,y:22},{opacity:1,y:0,duration:d*.65,ease:'expo.out'},.38);break;
  case 'opening-envelope':tl.fromTo(q('.envelope-flap'),{rotation:0,y:0},{rotation:180,y:-7,duration:d*.9,ease:'power2.inOut'},.22);tl.fromTo(q('.letter-insert'),{opacity:0,y:68,scale:.88},{opacity:1,y:-48,scale:1,duration:d*.9,ease:'expo.out'},.46);break;
  case 'checklist-sheet':qa('.checklist-face li i').forEach((x,i)=>tl.fromTo(x,{opacity:0,scale:.1,rotation:-22},{opacity:1,scale:1,rotation:0,duration:d*.32,ease:'back.out(1.7)'},.38+i*.12));break;
  case 'folder':tl.fromTo(q('.folder-sheet'),{opacity:0,y:55,scale:.9},{opacity:1,y:-34,scale:1,duration:d*.8,ease:'expo.out'},.38);break;
  case 'document-stack':qa('.stack-sheet').forEach((x,i)=>tl.fromTo(x,{opacity:0,x:(i-1)*55,y:-40*i,rotation:(i-1)*9},{opacity:1,x:0,y:0,rotation:0,duration:d*.65,ease:'back.out(1.7)'},.18+i*.11));break;
  case 'folded-note':qa('.fold-panel').forEach((x,i)=>tl.fromTo(x,{rotation:(i?1:-1)*65,x:(i?1:-1)*35},{rotation:0,x:0,duration:d*.85,ease:'power2.inOut'},.25));break;
  case 'crumpled-ball':qa('.crumple-face i').forEach((x,i)=>tl.fromTo(x,{opacity:0,scale:.2,rotation:i*35},{opacity:1,scale:1,rotation:0,duration:d*.55,ease:'back.out(1.7)'},.2+i*.08));break;
  case 'ripped-hole':tl.fromTo(q('.hole-mask'),{opacity:1,scale:1.8,rotation:-10},{opacity:1,scale:1,rotation:0,duration:d*.9,ease:'back.out(1.7)'},.26);break;
  case 'clear-tape':tl.fromTo(q('.tape-sheen'),{opacity:0,x:-90},{opacity:.75,x:90,duration:d*.95,ease:'sine.inOut'},.28);break;
  case 'staple-attachment':tl.fromTo(q('.staple-object i'),{y:-35,scale:1.4},{y:0,scale:1,duration:d*.55,ease:'back.out(1.7)'},.22);break;
  case 'paperclip-attachment':tl.fromTo(q('.paperclip-object i'),{x:45,y:-15,rotation:18},{x:0,y:0,rotation:0,duration:d*.72,ease:'expo.out'},.22);break;
  case 'pushpin-attachment':tl.fromTo(q('.pushpin-object i'),{y:-48,scale:1.45},{y:0,scale:1,duration:d*.62,ease:'back.out(1.7)'},.22);break;
  case 'string-connector':tl.fromTo(q('.string-object path'),{opacity:0,scale:.2},{opacity:1,scale:1,duration:d*.85,ease:'expo.out'},.24);break;
 }}
 function attachTo(target,attachmentId,config={}){const targetEl=typeof target==='string'?document.querySelector(target):target;if(!targetEl)throw new Error('Attachment target not found');const att=create(attachmentId,config);att.classList.add('attached-object');att.style.position='absolute';att.style.left=(config.left??50)+'%';att.style.top=(config.top??0)+'%';att.style.zIndex=config.zIndex??20;targetEl.style.position=targetEl.style.position||'relative';targetEl.appendChild(att);return att;}
 function update(el,config={}){const id=el.dataset.componentId,def=registry.find(x=>x.id===id),replacement=create(def,config);el.replaceWith(replacement);return replacement;}
 return {registry,create,animate,attachTo,update,fitText};
})();
