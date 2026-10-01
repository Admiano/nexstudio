(function(global){
  const state = new WeakMap();
  const eases={
    none:t=>t, linear:t=>t,
    'power1.in':t=>t*t,'power1.out':t=>1-(1-t)*(1-t),'power1.inOut':t=>t<.5?2*t*t:1-Math.pow(-2*t+2,2)/2,
    'power2.in':t=>t*t*t,'power2.out':t=>1-Math.pow(1-t,3),'power2.inOut':t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2,
    'power3.in':t=>t*t*t*t,'power3.out':t=>1-Math.pow(1-t,4),'power3.inOut':t=>t<.5?8*Math.pow(t,4):1-Math.pow(-2*t+2,4)/2,
    'power4.out':t=>1-Math.pow(1-t,5),
    'expo.out':t=>t===1?1:1-Math.pow(2,-10*t),'expo.inOut':t=>t===0||t===1?t:t<.5?Math.pow(2,20*t-10)/2:(2-Math.pow(2,-20*t+10))/2,
    'back.out(1.7)':t=>{const c1=1.7,c3=c1+1;return 1+c3*Math.pow(t-1,3)+c1*Math.pow(t-1,2)},
    'sine.inOut':t=>-(Math.cos(Math.PI*t)-1)/2,
    'circ.out':t=>Math.sqrt(1-Math.pow(t-1,2))
  };
  const transformKeys=['x','y','z','scale','scaleX','scaleY','rotation','rotationX','rotationY','skewX','skewY','opacity'];
  function targetsOf(target){ if(typeof target==='string') return [...document.querySelectorAll(target)]; if(target instanceof Element) return [target]; return Array.from(target||[]); }
  function parseNum(v){ if(typeof v==='number')return {n:v,u:''}; const m=String(v??'').trim().match(/^(-?[0-9.]+)(.*)$/); return m?{n:Number(m[1]),u:m[2]||''}:{n:0,u:''}; }
  function base(el){ if(!state.has(el)){ const cs=getComputedStyle(el); state.set(el,{x:0,y:0,z:0,scale:1,scaleX:1,scaleY:1,rotation:0,rotationX:0,rotationY:0,skewX:0,skewY:0,opacity:Number(cs.opacity)||1,vars:{},css:{}}); } return state.get(el); }
  function clone(v){return {...v,vars:{...(v.vars||{})},css:{...(v.css||{})}}}
  function apply(el,vals){ const b=base(el); Object.assign(b,vals); if(vals.vars)Object.assign(b.vars,vals.vars);if(vals.css)Object.assign(b.css,vals.css);
    const sx=(b.scale==null?1:b.scale)*(b.scaleX==null?1:b.scaleX), sy=(b.scale==null?1:b.scale)*(b.scaleY==null?1:b.scaleY);
    el.style.transform=`translate3d(${b.x||0}px,${b.y||0}px,${b.z||0}px) rotateX(${b.rotationX||0}deg) rotateY(${b.rotationY||0}deg) rotate(${b.rotation||0}deg) skew(${b.skewX||0}deg,${b.skewY||0}deg) scale(${sx},${sy})`;
    if(b.opacity!=null)el.style.opacity=b.opacity;
    Object.entries(b.vars||{}).forEach(([k,v])=>el.style.setProperty(k,v));
    Object.entries(b.css||{}).forEach(([k,v])=>{try{el.style[k]=v}catch(_){}});
  }
  function parsePosition(tl,pos){ if(pos==null) return tl.cursor; if(typeof pos==='number') return pos; if(typeof pos==='string'){ if(pos==='<') return tl.lastStart; if(pos==='>') return tl.cursor; if(pos.startsWith('<')) return tl.lastStart+Number(pos.slice(1)||0); if(pos.startsWith('>')) return tl.cursor+Number(pos.slice(1)||0); if(pos.startsWith('+=')) return tl.cursor+Number(pos.slice(2)); if(pos.startsWith('-=')) return tl.cursor-Number(pos.slice(2)); if(tl.labels[pos]!=null) return tl.labels[pos]; const label=pos.match(/^([\w-]+)([+-]=)([0-9.]+)$/); if(label&&tl.labels[label[1]]!=null) return tl.labels[label[1]]+(label[2]=='+='?1:-1)*Number(label[3]); } return tl.cursor; }
  function interpolate(a,b,p){const pa=parseNum(a),pb=parseNum(b);return `${pa.n+(pb.n-pa.n)*p}${pb.u||pa.u}`}
  class Timeline{
    constructor(opts={}){this.paused=opts.paused!==false;this.defaults=opts.defaults||{};this.tweens=[];this.labels={};this.cursor=0;this.lastStart=0;this.timer=null;this.now=0;this._reversed=false;}
    addLabel(name,pos){this.labels[name]=parsePosition(this,pos);return this;}
    _add(kind,target,a,b,pos){ const from=kind==='fromTo'?a:(kind==='from'?a:{}); const to=kind==='fromTo'?b:(kind==='to'?a:{}); const vars=Object.assign({},this.defaults,to); const dur=Math.max(0,Number(vars.duration??.5)); const start=parsePosition(this,pos)+Number(vars.delay||0); const els=targetsOf(target); let stagger=vars.stagger||0; if(typeof stagger==='object')stagger=Number(stagger.each??(stagger.amount&&els.length>1?stagger.amount/(els.length-1):0));stagger=Number(stagger)||0;
      els.forEach((el,i)=>{this.tweens.push({el,start:start+i*stagger,duration:dur,from:{...from},to:{...to},ease:vars.ease||this.defaults.ease||'power1.out',repeat:Math.max(0,Number(vars.repeat||0)),yoyo:!!vars.yoyo});});
      this.lastStart=start; this.cursor=Math.max(this.cursor,start+dur*(1+Math.max(0,Number(vars.repeat||0)))+(els.length?stagger*(els.length-1):0)); return this; }
    from(target,vars,pos){return this._add('from',target,vars,null,pos)}
    to(target,vars,pos){return this._add('to',target,vars,null,pos)}
    fromTo(target,from,to,pos){return this._add('fromTo',target,from,to,pos)}
    set(target,vars,pos){const v={...vars,duration:0};return this._add('fromTo',target,vars,v,pos)}
    duration(v){if(v==null)return this.cursor;this.cursor=Number(v)||this.cursor;return this}
    _props(obj){ const out={vars:{},css:{}}; for(const [k,v] of Object.entries(obj||{})){ if(['duration','ease','stagger','delay','repeat','yoyo','onUpdate','onStart','onComplete','overwrite','immediateRender'].includes(k))continue; if(k==='autoAlpha')out.opacity=Number(v); else if(k.startsWith('--'))out.vars[k]=v; else if(transformKeys.includes(k))out[k]=Number(v); else out.css[k]=v; } return out; }
    seek(time){ this.now=Math.max(0,Number(time)||0); const byEl=new Map(); this.tweens.forEach(t=>{if(!byEl.has(t.el))byEl.set(t.el,[]);byEl.get(t.el).push(t)}); byEl.forEach((tw,el)=>{ let current={x:0,y:0,z:0,scale:1,scaleX:1,scaleY:1,rotation:0,rotationX:0,rotationY:0,skewX:0,skewY:0,opacity:1,vars:{},css:{}};
        tw.sort((a,b)=>a.start-b.start).forEach((t,idx)=>{ const fromRaw=this._props(t.from),toRaw=this._props(t.to); const from=clone(current);Object.assign(from,fromRaw);Object.assign(from.vars,fromRaw.vars);Object.assign(from.css,fromRaw.css); const to=clone(from);Object.assign(to,toRaw);Object.assign(to.vars,toRaw.vars);Object.assign(to.css,toRaw.css);
          if(this.now<t.start){if(idx===0&&Object.keys(fromRaw).length)current=from;return;}
          const total=t.duration*(1+t.repeat);let local=t.duration===0?t.duration:Math.min(total,Math.max(0,this.now-t.start));let cycle=t.duration===0?0:Math.min(t.repeat,Math.floor(local/t.duration));let cp=t.duration===0?1:(local-cycle*t.duration)/t.duration;if(local>=total)cp=1;if(t.yoyo&&cycle%2===1)cp=1-cp; const ep=(eases[t.ease]||eases['power1.out'])(Math.max(0,Math.min(1,cp))); const vals={vars:{},css:{}};
          transformKeys.forEach(k=>{const av=from[k]??(k.startsWith('scale')?1:(k==='opacity'?1:0)),bv=to[k]??av;vals[k]=Number(av)+(Number(bv)-Number(av))*ep;});
          for(const k of new Set([...Object.keys(from.vars||{}),...Object.keys(to.vars||{})]))vals.vars[k]=interpolate(from.vars[k]??to.vars[k],to.vars[k]??from.vars[k],ep);
          for(const k of new Set([...Object.keys(from.css||{}),...Object.keys(to.css||{})])){const av=from.css[k]??to.css[k],bv=to.css[k]??av;const na=parseNum(av),nb=parseNum(bv);vals.css[k]=(String(av).match(/^(-?[0-9.]+)/)&&String(bv).match(/^(-?[0-9.]+)/))?`${na.n+(nb.n-na.n)*ep}${nb.u||na.u}`:(ep<1?av:bv);}
          current=vals;
        }); apply(el,current); }); return this; }
    time(v){return v==null?this.now:this.seek(v)}
    progress(v){return v==null?(this.cursor?this.now/this.cursor:0):this.seek(v*this.cursor)}
    pause(){if(this.timer)cancelAnimationFrame(this.timer);this.timer=null;this.paused=true;return this}
    play(from){if(from!=null)this.seek(from);this.pause();this.paused=false;const initial=this.now,start=performance.now();const tick=now=>{if(this.paused)return;let t=initial+(now-start)/1000;if(t>=this.cursor){this.seek(this.cursor);this.pause();return;}this.seek(t);this.timer=requestAnimationFrame(tick)};this.timer=requestAnimationFrame(tick);return this}
    restart(){this.seek(0);return this.play()}
    reverse(from){if(from!=null)this.seek(from);this.pause();this.paused=false;const initial=this.now||this.cursor,start=performance.now();const tick=now=>{if(this.paused)return;let t=initial-(now-start)/1000;if(t<=0){this.seek(0);this.pause();return;}this.seek(t);this.timer=requestAnimationFrame(tick)};this.timer=requestAnimationFrame(tick);return this}
    kill(){return this.pause()}
  }
  function one(method,target,a,b){const tl=new Timeline({paused:false});if(method==='fromTo')tl.fromTo(target,a,b,0);else tl[method](target,a,0);tl.play();return tl;}
  global.gsap={timeline:o=>new Timeline(o),set:(target,vars)=>{targetsOf(target).forEach(el=>apply(el,vars));},to:(target,vars)=>one('to',target,vars),from:(target,vars)=>one('from',target,vars),fromTo:(target,a,b)=>one('fromTo',target,a,b)};
})(window);
