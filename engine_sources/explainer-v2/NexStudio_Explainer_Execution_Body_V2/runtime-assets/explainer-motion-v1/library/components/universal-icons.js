window.NexIcons = (() => {
  const registry = window.NEX_ICONS || [];
  const NS = 'http://www.w3.org/2000/svg';
  const q = value => typeof value === 'string' ? document.querySelector(value) : value;
  const getDef = value => typeof value === 'object' ? value : registry.find(x => x.id === value || x.slug === value);
  const clamp = (v,a=0,b=1) => Math.min(b,Math.max(a,v));

  const symbols = {
    add: `<path class="icon-symbol-stroke part-plus-h" d="M34 60H86"/><path class="icon-symbol-stroke part-plus-v" d="M60 34V86"/>`,
    remove: `<path class="icon-symbol-stroke part-minus" d="M32 60H88"/>`,
    search: `<circle class="icon-symbol-stroke part-search-ring" cx="52" cy="51" r="23"/><path class="icon-symbol-stroke part-search-handle" d="M69 68L88 87"/><circle class="icon-accent-fill part-search-dot" cx="44" cy="43" r="5"/>`,
    edit: `<path class="icon-symbol-fill part-pencil" d="M32 80L38 61L74 25L94 45L58 81L38 87Z"/><path class="icon-symbol-stroke part-pencil-line" d="M68 31L88 51M38 61L58 81"/>`,
    delete: `<path class="icon-symbol-stroke part-bin-lid" d="M34 40H86M48 31H72"/><path class="icon-symbol-fill part-bin-body" d="M39 42L44 89H76L81 42Z"/><path class="icon-symbol-stroke" d="M54 54V76M66 54V76"/>`,
    save: `<path class="icon-symbol-fill part-save-body" d="M31 26H80L91 37V92H31Z"/><path class="icon-highlight-fill part-save-slot" d="M42 28H72V49H42Z"/><rect class="icon-accent-fill part-save-label" x="43" y="64" width="36" height="22" rx="5"/><path class="icon-symbol-stroke part-save-mark" d="M56 70V80M50 75H62"/>`,
    copy: `<rect class="icon-accent-fill part-copy-back" x="29" y="27" width="48" height="55" rx="8"/><rect class="icon-symbol-fill part-copy-front" x="43" y="39" width="48" height="55" rx="8"/>`,
    share: `<path class="icon-symbol-stroke part-share-link" d="M43 51L73 35M43 68L74 84"/><circle class="icon-accent-fill part-share-node node-a" cx="34" cy="59" r="12"/><circle class="icon-symbol-fill part-share-node node-b" cx="82" cy="30" r="12"/><circle class="icon-symbol-fill part-share-node node-c" cx="83" cy="89" r="12"/>`,
    send: `<path class="icon-symbol-fill part-send-plane" d="M23 55L96 26L69 96L55 68Z"/><path class="icon-symbol-stroke" d="M55 68L96 26M55 68L35 79"/>`,
    download: `<path class="icon-symbol-stroke part-download-arrow" d="M60 25V70M43 54L60 72L77 54"/><path class="icon-symbol-fill part-tray" d="M31 75V91H89V75"/>`,
    upload: `<path class="icon-symbol-stroke part-upload-arrow" d="M60 74V29M43 45L60 27L77 45"/><path class="icon-symbol-fill part-tray" d="M31 75V91H89V75"/>`,
    refresh: `<path class="icon-symbol-stroke part-refresh" d="M88 53A30 30 0 0 0 37 37L28 47M32 67A30 30 0 0 0 83 83L92 73"/><path class="icon-accent-fill" d="M27 30L28 48L46 47ZM93 90L92 72L74 73Z"/>`,
    undo: `<path class="icon-symbol-stroke part-undo" d="M34 48H72C87 48 94 59 90 73C87 84 77 89 66 89H51"/><path class="icon-symbol-fill" d="M38 31L20 48L38 65Z"/>`,
    redo: `<path class="icon-symbol-stroke part-redo" d="M86 48H48C33 48 26 59 30 73C33 84 43 89 54 89H69"/><path class="icon-symbol-fill" d="M82 31L100 48L82 65Z"/>`,
    settings: `<g class="part-gear"><circle class="icon-symbol-fill" cx="60" cy="60" r="28"/><circle class="icon-highlight-fill" cx="60" cy="60" r="11"/><path class="icon-symbol-stroke" d="M60 18V28M60 92V102M18 60H28M92 60H102M30 30L37 37M83 83L90 90M90 30L83 37M37 83L30 90"/></g>`,
    lock: `<rect class="icon-symbol-fill part-lock-body" x="31" y="52" width="58" height="44" rx="8"/><path class="icon-symbol-stroke part-lock-shackle" d="M43 53V41C43 18 77 18 77 41V53"/><circle class="icon-highlight-fill" cx="60" cy="73" r="6"/><path class="icon-symbol-stroke" d="M60 79V87"/>`,
    unlock: `<rect class="icon-symbol-fill part-lock-body" x="31" y="52" width="58" height="44" rx="8"/><path class="icon-symbol-stroke part-lock-shackle" d="M43 53V41C43 21 71 19 77 35"/><circle class="icon-highlight-fill" cx="60" cy="73" r="6"/><path class="icon-symbol-stroke" d="M60 79V87"/>`,
    check: `<circle class="icon-accent-fill part-check-circle" cx="60" cy="60" r="36"/><path class="icon-symbol-stroke part-check" d="M39 61L53 75L82 45"/>`,
    close: `<path class="icon-symbol-stroke part-close-a" d="M35 35L85 85"/><path class="icon-symbol-stroke part-close-b" d="M85 35L35 85"/>`,
    warning: `<path class="icon-symbol-fill part-warning-triangle" d="M60 22L101 94H19Z"/><path class="icon-symbol-stroke part-warning-mark" d="M60 45V68"/><circle class="icon-accent-fill part-warning-dot" cx="60" cy="82" r="5"/>`,
    information: `<circle class="icon-symbol-fill" cx="60" cy="60" r="37"/><circle class="icon-highlight-fill" cx="60" cy="39" r="5"/><path class="icon-symbol-stroke" d="M60 55V82"/>`,
    help: `<circle class="icon-symbol-fill" cx="60" cy="60" r="37"/><path class="icon-symbol-stroke" d="M45 47C47 32 72 30 78 44C84 57 69 63 61 69V74"/><circle class="icon-highlight-fill" cx="60" cy="84" r="5"/>`,
    home: `<path class="icon-symbol-fill part-home" d="M22 58L60 25L98 58V96H72V70H48V96H22Z"/><path class="icon-accent-stroke" d="M17 61L60 22L103 61"/>`,
    menu: `<path class="icon-symbol-stroke part-menu-a" d="M28 38H92"/><path class="icon-symbol-stroke part-menu-b" d="M28 60H92"/><path class="icon-symbol-stroke part-menu-c" d="M28 82H92"/>`,
    calendar: `<rect class="icon-symbol-fill part-calendar-page" x="25" y="29" width="70" height="67" rx="10"/><path class="icon-symbol-stroke" d="M25 50H95M43 22V38M77 22V38"/><g class="part-calendar-dates"><rect class="icon-highlight-fill" x="38" y="61" width="13" height="12" rx="2"/><rect class="icon-accent-fill" x="55" y="61" width="13" height="12" rx="2"/><rect class="icon-highlight-fill" x="72" y="61" width="13" height="12" rx="2"/><rect class="icon-accent-fill" x="38" y="77" width="13" height="12" rx="2"/><rect class="icon-highlight-fill" x="55" y="77" width="13" height="12" rx="2"/></g>`,
    clock: `<circle class="icon-symbol-fill part-clock-ring" cx="60" cy="60" r="38"/><path class="icon-symbol-stroke part-hour" d="M60 60V40"/><path class="icon-accent-stroke part-minute" d="M60 60L80 68"/><circle class="icon-highlight-fill" cx="60" cy="60" r="5"/>`,
    location: `<path class="icon-symbol-fill part-location" d="M60 101C60 101 30 73 30 49C30 31 43 20 60 20C77 20 90 31 90 49C90 73 60 101 60 101Z"/><circle class="icon-highlight-fill" cx="60" cy="49" r="12"/>`,
    link: `<path class="icon-symbol-stroke part-link-a" d="M50 73L42 81C31 92 14 75 25 64L41 48C49 40 59 42 66 49"/><path class="icon-accent-stroke part-link-b" d="M70 47L78 39C89 28 106 45 95 56L79 72C71 80 61 78 54 71"/><path class="icon-symbol-stroke" d="M44 76L76 44"/>`,
    attachment: `<path class="icon-symbol-stroke part-attachment" d="M48 57L70 35C84 21 104 42 90 56L56 90C35 111 5 80 26 59L59 26"/>`,
    filter: `<path class="icon-symbol-fill part-filter" d="M23 30H97L70 60V91L50 99V60Z"/><path class="icon-accent-stroke" d="M34 43H86"/>`,
    sort: `<path class="icon-symbol-stroke part-sort-up" d="M41 88V31M27 46L41 31L55 46"/><path class="icon-accent-stroke part-sort-down" d="M79 32V89M65 74L79 89L93 74"/>`,
    expand: `<path class="icon-symbol-stroke" d="M50 31H30V51M70 31H90V51M50 89H30V69M70 89H90V69"/><path class="icon-accent-stroke" d="M31 50L49 32M89 50L71 32M31 70L49 88M89 70L71 88"/>`,
    collapse: `<path class="icon-symbol-stroke" d="M30 49H50V29M90 49H70V29M30 71H50V91M90 71H70V91"/><path class="icon-accent-stroke" d="M31 48L49 30M89 48L71 30M31 72L49 90M89 72L71 90"/>`,
    forward: `<path class="icon-symbol-stroke" d="M29 60H85"/><path class="icon-symbol-fill part-forward" d="M68 38L92 60L68 82Z"/>`,
    back: `<path class="icon-symbol-stroke" d="M91 60H35"/><path class="icon-symbol-fill part-back" d="M52 38L28 60L52 82Z"/>`,
    play: `<circle class="icon-symbol-fill part-play-ring" cx="60" cy="60" r="38"/><path class="icon-highlight-fill part-play" d="M50 40L82 60L50 80Z"/>`,
    pause: `<circle class="icon-symbol-fill" cx="60" cy="60" r="38"/><rect class="icon-highlight-fill part-pause-a" x="44" y="39" width="11" height="42" rx="3"/><rect class="icon-highlight-fill part-pause-b" x="65" y="39" width="11" height="42" rx="3"/>`,
    stop: `<circle class="icon-symbol-fill" cx="60" cy="60" r="38"/><rect class="icon-highlight-fill part-stop" x="43" y="43" width="34" height="34" rx="5"/>`,
    favourite: `<path class="icon-symbol-stroke part-heart-outline" d="M60 91C60 91 24 70 24 46C24 25 48 20 60 38C72 20 96 25 96 46C96 70 60 91 60 91Z"/><path class="icon-accent-fill part-heart-fill" d="M60 88C60 88 29 68 29 47C29 32 47 29 60 45C73 29 91 32 91 47C91 68 60 88 60 88Z"/>`,
    bookmark: `<path class="icon-symbol-stroke part-bookmark-outline" d="M37 25H83V96L60 80L37 96Z"/><path class="icon-accent-fill part-bookmark-fill" d="M42 30H78V86L60 73L42 86Z"/>`
  };

  function paperLayers(){
    return `<g class="icon-shadow-layer"><path class="icon-paper-shadow" d="M16 27Q20 14 37 15L82 12Q100 17 103 34L106 79Q101 99 82 104L37 106Q18 101 14 83L12 43Q12 32 16 27Z"/></g>
      <g class="icon-paper-layer"><path class="icon-paper-shape" d="M13 23Q20 12 36 14L84 11Q100 16 105 33L107 78Q103 98 83 103L36 106Q17 100 13 82L10 42Q10 30 13 23Z"/><path class="icon-paper-edge" d="M18 25Q24 18 38 19L82 16Q94 19 99 35L101 76Q97 91 80 97L38 99Q23 94 19 80L16 43Q16 31 18 25Z"/><circle class="icon-active-ring" cx="60" cy="60" r="49"/></g>`;
  }
  function stateLayer(){return `<g class="icon-state-layer"><g class="icon-complete-badge"><circle cx="91" cy="29" r="15"/><path d="M84 29L89 34L99 23"/></g></g>`}
  function sizeBand(size){return size<=56?'small':size>=144?'large':'medium'}

  function create(value,config={}){
    const def=getDef(value);if(!def)throw new Error(`Unknown icon: ${value}`);
    const size=Number(config.size||96),treatment=config.treatment||'paper-cutout';
    const allowed=def.states||['inactive','active'];
    const state=allowed.includes(config.state)?config.state:(config.state==='default'?'active':allowed[0]);
    const el=document.createElement('div');
    el.className='nex-icon';el.dataset.iconId=def.id;el.dataset.componentId=def.id;el.dataset.slug=def.slug;el.dataset.treatment=treatment;el.dataset.state=state;el.dataset.sizeBand=sizeBand(size);el.style.setProperty('--icon-size',`${size}px`);
    el.setAttribute('role','img');el.setAttribute('aria-label',config.accessibilityLabel||def.accessibilityLabel);el.setAttribute('aria-live','off');
    const svg=document.createElementNS(NS,'svg');svg.setAttribute('viewBox','0 0 120 120');svg.setAttribute('class','nex-icon-svg');svg.setAttribute('aria-hidden','true');
    svg.innerHTML=`${paperLayers()}<g class="icon-symbol-layer">${symbols[def.slug]||symbols.help}</g><g class="icon-accent-layer"><path class="icon-accent-stroke icon-accent-mark" d="M88 92L97 83"/></g>${stateLayer()}`;
    el.appendChild(svg);const grain=document.createElement('span');grain.className='icon-paper-grain';grain.setAttribute('aria-hidden','true');el.appendChild(grain);
    if(config.showLabel){const label=document.createElement('span');label.className='icon-label';label.textContent=config.label||def.name;el.appendChild(label)}
    el.__iconConfig={size,treatment,state,label:config.label||def.name};return el;
  }

  class CombinedTimeline{
    constructor(entries=[]){this.entries=entries;this.now=0;this.paused=true;this.timer=null;this._duration=Math.max(0,...entries.map(x=>(x.offset||0)+x.timeline.duration()));}
    duration(){return this._duration}
    seek(t){this.now=clamp(Number(t)||0,0,this._duration);for(const entry of this.entries){const local=this.now-(entry.offset||0);entry.timeline.seek(local<=0?0:local>=entry.timeline.duration()?entry.timeline.duration():local)}return this}
    time(v){return v==null?this.now:this.seek(v)}
    progress(v){return v==null?(this._duration?this.now/this._duration:0):this.seek(v*this._duration)}
    pause(){if(this.timer)cancelAnimationFrame(this.timer);this.timer=null;this.paused=true;return this}
    play(from){if(from!=null)this.seek(from);this.pause();this.paused=false;const initial=this.now,start=performance.now();const tick=now=>{if(this.paused)return;const t=initial+(now-start)/1000;if(t>=this._duration){this.seek(this._duration);this.pause();return}this.seek(t);this.timer=requestAnimationFrame(tick)};this.timer=requestAnimationFrame(tick);return this}
    restart(){this.seek(0);return this.play()}
    kill(){this.entries.forEach(x=>x.timeline.kill?.());return this.pause()}
  }

  function pathDraw(tl,path,start,duration,ease='power2.out'){
    if(!path)return;let len=180;try{len=path.getTotalLength()||180}catch(_){}
    path.style.strokeDasharray=String(len);
    tl.addUpdate(start,duration,p=>{path.style.strokeDashoffset=String(len*(1-p));path.style.opacity=String(p)},ease);
  }
  function staggerScale(tl,nodes,start,duration){const list=[...nodes],seg=duration/Math.max(1,list.length+1);list.forEach((n,i)=>tl.fromTo(n,{opacity:0,scale:.2},{opacity:1,scale:1,duration:seg*2,ease:'back.out(1.7)'},start+i*seg))}
  function genericInternal(el,o){const tl=NexMotion.createTimeline(),symbol=el.querySelector('.icon-symbol-layer'),accent=el.querySelector('.icon-accent-layer');tl.fromTo(symbol,{y:7,scale:.9,opacity:.55},{y:0,scale:1,opacity:1,duration:o.duration*.68,ease:'power2.out'},0);tl.fromTo(accent,{opacity:0,scale:.6},{opacity:1,scale:1,duration:o.duration*.5,ease:'back.out(1.7)'},o.duration*.28);return tl}
  function bespokeInternal(el,slug,o){
    const tl=NexMotion.createTimeline(),S=s=>el.querySelector(s),SA=s=>el.querySelectorAll(s),d=o.duration;
    switch(slug){
      case 'search': pathDraw(tl,S('.part-search-ring'),0,d*.56);tl.fromTo(S('.part-search-handle'),{opacity:0,scaleX:.1,rotation:-35},{opacity:1,scaleX:1,rotation:0,duration:d*.42,ease:'back.out(1.7)'},d*.32);tl.fromTo(S('.part-search-dot'),{opacity:0,scale:.2},{opacity:1,scale:1,duration:d*.32,ease:'back.out(1.7)'},d*.58);break;
      case 'save': tl.fromTo(S('.part-save-slot'),{y:-18,opacity:0},{y:0,opacity:1,duration:d*.42,ease:'back.out(1.7)'},0);tl.fromTo(S('.part-save-label'),{scaleY:.05,opacity:0},{scaleY:1,opacity:1,duration:d*.45,ease:'power2.out'},d*.2);tl.fromTo(S('.part-save-mark'),{opacity:0,rotation:-45,scale:.2},{opacity:1,rotation:0,scale:1,duration:d*.4,ease:'back.out(1.7)'},d*.52);break;
      case 'share': pathDraw(tl,S('.part-share-link'),0,d*.62);staggerScale(tl,SA('.part-share-node'),d*.1,d*.65);break;
      case 'download': tl.fromTo(S('.part-download-arrow'),{y:-24,opacity:0},{y:12,opacity:1,duration:d*.58,ease:'power3.out'},0);tl.to(S('.part-download-arrow'),{y:0,duration:d*.25,ease:'back.out(1.7)'},d*.58);tl.fromTo(S('.part-tray'),{scaleX:.75,y:5},{scaleX:1,y:0,duration:d*.38,ease:'back.out(1.7)'},d*.4);break;
      case 'upload': tl.fromTo(S('.part-upload-arrow'),{y:24,opacity:0},{y:-12,opacity:1,duration:d*.58,ease:'power3.out'},0);tl.to(S('.part-upload-arrow'),{y:0,duration:d*.25,ease:'back.out(1.7)'},d*.58);tl.fromTo(S('.part-tray'),{scaleX:.75,y:5},{scaleX:1,y:0,duration:d*.38,ease:'back.out(1.7)'},0);break;
      case 'refresh': tl.fromTo(S('.part-refresh'),{rotation:-210,opacity:.3,scale:.82},{rotation:0,opacity:1,scale:1,duration:d,ease:'back.out(1.7)'},0);break;
      case 'lock': tl.fromTo(S('.part-lock-shackle'),{y:-16,scaleY:1.15,opacity:.25},{y:0,scaleY:1,opacity:1,duration:d*.62,ease:'back.out(1.7)'},0);tl.fromTo(S('.part-lock-body'),{scale:.88,y:5},{scale:1,y:0,duration:d*.48,ease:'back.out(1.7)'},d*.24);break;
      case 'unlock': tl.fromTo(S('.part-lock-shackle'),{rotation:-38,x:-7,y:-7,opacity:.35},{rotation:0,x:0,y:0,opacity:1,duration:d*.7,ease:'back.out(1.7)'},0);tl.fromTo(S('.part-lock-body'),{scale:.88},{scale:1,duration:d*.42,ease:'back.out(1.7)'},d*.24);break;
      case 'check': tl.fromTo(S('.part-check-circle'),{opacity:0,scale:.3},{opacity:1,scale:1,duration:d*.55,ease:'back.out(1.7)'},0);pathDraw(tl,S('.part-check'),d*.28,d*.58);break;
      case 'warning': tl.fromTo(S('.part-warning-triangle'),{opacity:0,scale:1.65,rotation:-5},{opacity:1,scale:1,rotation:0,duration:d*.62,ease:'back.out(1.7)'},0);tl.fromTo(S('.part-warning-mark'),{y:-15,opacity:0},{y:0,opacity:1,duration:d*.38,ease:'power3.out'},d*.32);tl.fromTo(S('.part-warning-dot'),{scale:.2,opacity:0},{scale:1,opacity:1,duration:d*.32,ease:'back.out(1.7)'},d*.57);break;
      case 'calendar': tl.fromTo(S('.part-calendar-page'),{rotationX:-65,scaleY:.72,opacity:.25},{rotationX:0,scaleY:1,opacity:1,duration:d*.6,ease:'power2.inOut'},0);staggerScale(tl,SA('.part-calendar-dates > *'),d*.35,d*.58);break;
      case 'clock': tl.fromTo(S('.part-hour'),{rotation:-115},{rotation:0,duration:d*.74,ease:'power2.out'},0);tl.fromTo(S('.part-minute'),{rotation:-310},{rotation:0,duration:d,ease:'power2.out'},0);tl.fromTo(S('.part-clock-ring'),{scale:.85,opacity:.5},{scale:1,opacity:1,duration:d*.45,ease:'back.out(1.7)'},0);break;
      case 'play': tl.fromTo(S('.part-play'),{x:-14,opacity:0,scale:.55},{x:0,opacity:1,scale:1.12,duration:d*.58,ease:'back.out(1.7)'},0);tl.to(S('.part-play'),{scale:1,duration:d*.25,ease:'power2.out'},d*.58);tl.fromTo(S('.part-play-ring'),{scale:.88},{scale:1,duration:d*.5,ease:'back.out(1.7)'},0);break;
      case 'favourite': tl.fromTo(S('.part-heart-outline'),{scale:.65,opacity:.35},{scale:1.12,opacity:1,duration:d*.48,ease:'back.out(1.7)'},0);tl.to(S('.part-heart-outline'),{scale:1,duration:d*.23,ease:'power2.out'},d*.48);tl.fromTo(S('.part-heart-fill'),{opacity:0,scale:.65},{opacity:1,scale:1,duration:d*.45,ease:'back.out(1.7)'},d*.34);break;
      case 'bookmark': tl.fromTo(S('.part-bookmark-outline'),{y:-28,scaleY:.55,opacity:.2},{y:0,scaleY:1,opacity:1,duration:d*.64,ease:'back.out(1.7)'},0);tl.fromTo(S('.part-bookmark-fill'),{opacity:0,scaleY:.15},{opacity:1,scaleY:1,duration:d*.42,ease:'power2.out'},d*.36);break;
      default:return genericInternal(el,o);
    }
    return tl;
  }

  function animate(target,config={}){
    const el=q(target),def=getDef(el?.dataset.iconId);if(!el||!def)throw new Error('Icon target or definition missing');
    const motion=config.motion||def.defaultMotion,duration=Number(config.duration||def.duration.recommended),energy=config.energy||config.motionEnergy||'medium';
    [...el.querySelectorAll('[data-motion-layer]')].forEach(x=>x.remove());
    const entrance=NexMotion.apply(el,motion,{duration:Math.max(.35,duration*.72),energy,intensity:config.intensity??1,ease:config.ease});
    const internal=def.bespokeInternalMotion?bespokeInternal(el,def.slug,{duration:Math.max(.4,duration*.82),energy}):genericInternal(el,{duration:Math.max(.4,duration*.72),energy});
    const combined=new CombinedTimeline([{timeline:entrance,offset:0},{timeline:internal,offset:Math.max(.08,duration*.24)}]);combined.seek(0);el.__tl=combined;el.__iconTimeline=combined;return combined;
  }
  function setState(target,state){const el=q(target),def=getDef(el?.dataset.iconId);if(!el||!def)return el;if(!(def.states||[]).includes(state))state=(def.states||['inactive'])[0];el.dataset.state=state;el.__iconConfig.state=state;return el}
  function setTreatment(target,treatment){const el=q(target);if(el){el.dataset.treatment=treatment;el.__iconConfig.treatment=treatment}return el}
  function setSize(target,size){const el=q(target);if(el){size=Number(size)||96;el.style.setProperty('--icon-size',`${size}px`);el.dataset.sizeBand=sizeBand(size);el.__iconConfig.size=size}return el}
  function update(target,config={}){const el=q(target),def=getDef(el?.dataset.iconId);if(!el||!def)throw new Error('Icon target missing');const next=create(def,{...el.__iconConfig,...config});el.replaceWith(next);return next}
  return {registry,getDef,create,animate,setState,setTreatment,setSize,update,CombinedTimeline};
})();
