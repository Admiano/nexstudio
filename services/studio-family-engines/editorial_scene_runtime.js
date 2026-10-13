/* Execute typed P8 states. Internal role/semantic labels are never display copy. */
(() => {
  'use strict';
  const plan=JSON.parse(document.getElementById('nex-plan').textContent);
  const spec=plan.authoredScenes,stage=document.getElementById('nex-stage');
  const clamp=x=>Math.max(0,Math.min(1,x)),lerp=(a,b,q)=>a+(b-a)*q;
  const ease=q=>q*q*(3-2*q);
  const graphemes=new Intl.Segmenter(undefined,{granularity:'grapheme'});
  const pieces=s=>[...graphemes.segment(s)].map(x=>x.segment);
  function color(a,b,q){
    return '#'+[1,3,5].map(i=>Math.round(lerp(parseInt(a.slice(i,i+2),16),parseInt(b.slice(i,i+2),16),q)).toString(16).padStart(2,'0')).join('');
  }
  function transition(a,b,q){
    const n={...b};
    for(const key of ['opacity','fontSize','weight'])if(typeof a[key]==='number'&&typeof b[key]==='number')n[key]=lerp(a[key],b[key],q);
    n.rect=b.rect.map((v,i)=>lerp(a.rect[i],v,q));
    if(a.color&&b.color)n.color=color(a.color,b.color,q);
    if(q<1&&a.text!==b.text)n.text=a.text;
    if(q<1&&a.renderSrc!==b.renderSrc)n.renderSrc=a.renderSrc;
    if(q<1)for(const key of ['font','align'])if(key in a)n[key]=a[key];
    return n;
  }
  function seek(t){
    t=Math.max(0,Math.min(spec.duration-1e-7,Number(t)||0));
    const s=spec.scenes.find(s=>t>=s.start&&t<s.end)||spec.scenes.at(-1);
    const states=new Map(s.nodes.map(n=>[n.id,{...n,rect:[...n.rect]}]));
    for(const action of s.actions){
      if(action.verb==='SETTLE')continue;
      const n=states.get(action.nodeId),q=ease(clamp((t-action.start)/(action.end-action.start)));
      if(action.verb==='TYPE_REVEAL'){
        const from=action.before?.text||'',full=pieces(action.after.text),count=pieces(from).length;
        n.text=full.slice(0,count+Math.floor((full.length-count)*q)).join('');
      }else if(action.verb==='REVEAL')n.opacity=action.after.opacity*q;
      else states.set(action.nodeId,transition(action.before,action.after,q));
    }
    stage.replaceChildren();const world=document.createElement('div');world.className='p8-world';stage.appendChild(world);
    const width=innerWidth,height=innerHeight;
    for(const n of states.values()){
      const el=document.createElement('div');el.className='p8-node '+n.kind;el.dataset.semanticId=n.id;
      const [x,y,w,h]=n.rect;
      Object.assign(el.style,{left:x*width+'px',top:y*height+'px',width:w*width+'px',height:h*height+'px',opacity:String(n.opacity)});
      if(n.kind==='TEXT'){
        el.textContent=n.text;
        Object.assign(el.style,{fontFamily:{didone:'NativeDidone',sans:'Arial',mono:'monospace'}[n.font],
          fontSize:n.fontSize*Math.min(width,height)+'px',fontWeight:String(n.weight),color:n.color,textAlign:n.align});
      }else if(n.kind==='BACKGROUND'){el.style.backgroundColor=n.color;stage.insertBefore(el,world);continue;}
      else if(n.kind==='ASSET'){const img=document.createElement('img');img.alt='';img.src=n.renderSrc;el.appendChild(img);}
      world.appendChild(el);
    }
    const camera=s.camera,q=ease(clamp((t-s.start)/(s.end-s.start)));
    let dx=0,dy=0,scale=1;
    if(camera.motivated){
      scale=lerp(camera.scaleStart,camera.scaleEnd,q);
      const target=states.get(camera.targetContinuityId),[x,y,w,h]=target.rect;
      const amount={STRONG:.34,MODERATE:.26,SUBTLE:.18,NONE:0}[camera.intensity];
      if(['PAN','REFRAME','TRACK','FOLLOW'].includes(camera.atom))dx=(.5-x-w/2)*100*amount*q;
      if(['TILT','REFRAME','TRACK','FOLLOW'].includes(camera.atom))dy=(.5-y-h/2)*100*amount*q;
    }
    world.style.transform=`translate(${dx}%,${dy}%) scale(${scale})`;
    const lineRects=[];let visible=0,copyClipped=false;const nodes=[];
    for(const n of states.values()){
      const el=stage.querySelector(`[data-semantic-id="${CSS.escape(n.id)}"]`);
      if(n.opacity>.01&&n.kind!=='VACANCY'&&(n.kind!=='TEXT'||n.text))visible++;
      if(n.kind==='TEXT'&&n.opacity>.01&&n.text){
        const range=document.createRange();range.selectNodeContents(el);const r=range.getBoundingClientRect(),box=el.getBoundingClientRect();
        lineRects.push([r.x,r.y,r.width,r.height]);
        if(r.x<-.1||r.y<-.1||r.right>width+.1||r.bottom>height+.1||r.x<box.x-.1||r.right>box.right+.1||r.bottom>box.bottom+.1)copyClipped=true;
      }
      nodes.push({id:n.id,kind:n.kind,text:n.text,opacity:n.opacity,rect:n.rect});
    }
    const fontLoaded=[...states.values()].filter(n=>n.kind==='TEXT'&&n.text&&n.opacity>.01)
      .every(n=>document.fonts.check('48px '+{didone:'NativeDidone',sans:'Arial',mono:'monospace'}[n.font]));
    return {time:t,beatId:s.beatId,nodes,lineRects,copyClipped,visibleSemanticCount:visible,
      visibleAnonymousHelperCount:0,fontLoaded,cameraTransform:world.style.transform};
  }
  window.NexFacelessRenderer={seek};seek(0);
})();
