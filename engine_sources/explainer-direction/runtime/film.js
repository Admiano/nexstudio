/* Native SVG execution; no legacy scene layouts, animation timers, network artwork or creative authority. */
(function (root) {
  'use strict';
  const boundary=root.ExplainerDirectionPlan;
  if(!boundary)throw new Error('Load runtime/plan.js before runtime/film.js');
  const NS='http://www.w3.org/2000/svg';
  let serial=0;
  const clamp=(v,min=0,max=1)=>Math.min(max,Math.max(min,v));
  const el=(tag,attrs={},parent)=>{const node=document.createElementNS(NS,tag);for(const [k,v] of Object.entries(attrs))node.setAttribute(k,String(v));if(parent)parent.appendChild(node);return node;};
  const ease=(name,t)=>name==='step'?(t>=1?1:0):name==='ease_in'?t*t:name==='ease_out'?1-(1-t)**2:name==='ease_in_out'?(t<.5?2*t*t:1-(-2*t+2)**2/2):t;
  const blend=(a,b,t)=>'#'+[1,3,5].map(i=>Math.round(parseInt(a.slice(i,i+2),16)*(1-t)+parseInt(b.slice(i,i+2),16)*t).toString(16).padStart(2,'0')).join('');
  const numText=(a,value)=>`${value.toFixed(a.payload.decimals??0)}${a.payload.unit==='1'?'':a.payload.unit==='%'?'%':' '+a.payload.unit}`;
  function createFilm(input,mount,options={}) {
    if(!(mount instanceof Element))throw new boundary.PlanError('mount must be an Element');
    if(Object.keys(options).some(k=>!['onError'].includes(k)))throw new boundary.PlanError('unsupported runtime option');
    const plan=boundary.validatePlan(input),prefix=`ed-${++serial}`,w=plan.canvas.width,h=plan.canvas.height;
    let destroyed=false,readyDone=false,at=0,error=null,active=[],fits=[];
    const imageURLs=[];
    const svg=el('svg',{xmlns:NS,viewBox:`0 0 ${w} ${h}`,width:w,height:h,role:'img','aria-label':plan.title,'data-runtime':'explainer-direction/v1'},mount);
    svg.style.cssText='display:block;width:100%;height:100%;overflow:hidden;';
    const defs=el('defs',{},svg);el('rect',{x:0,y:0,width:w,height:h,fill:plan.output.background},svg);
    const ctx=document.createElement('canvas').getContext('2d');
    const family=`EDLocal${serial}`;
    const style=plan.style,palette=style.palette,stroke=style.strokes.width;
    const font=new FontFace(family,`url(${JSON.stringify(style.typography.font_url)})`,{weight:'100 900'});
    const primitives=[];
    const scenes=plan.scenes.map((scene,si)=>{
      const group=el('g',{'data-scene':scene.id,display:'none'},svg);
      const sceneClip=el('clipPath',{id:`${prefix}-scene-${si}`,clipPathUnits:'userSpaceOnUse'},defs);
      const sceneRect=el('rect',{x:0,y:0,width:w,height:h},sceneClip);
      group.setAttribute('clip-path',`url(#${sceneClip.id})`);
      el('rect',{x:0,y:0,width:w,height:h,fill:palette.background},group);
      const nodes=Object.create(null),parents=Object.create(null);for(const a of scene.actors)if(a.kind==='group')for(const c of a.payload.children)parents[c]=a.id;
      for(const [ai,a] of scene.actors.entries()){
        const g=a.geometry,aid=`${prefix}-${si}-${ai}`;
        const outer=el('g',{'data-actor':a.id,'data-kind':a.kind,'aria-label':a.label});
        const clip=el('clipPath',{id:aid+'-reveal',clipPathUnits:'userSpaceOnUse'},defs);
        const revealRect=el('rect',{x:g.x,y:g.y,width:g.width,height:g.height},clip);
        const masked=el('g',{'clip-path':`url(#${clip.id})`},outer);
        const content=el('g',a.kind==='group'?{}:{transform:`translate(${g.x} ${g.y})`},masked);
        const fillClip=el('clipPath',{id:aid+'-fill',clipPathUnits:'userSpaceOnUse'},defs);
        const fillRect=el('rect',{x:0,y:0,width:g.width,height:g.height},fillClip);
        const view={a,outer,content,revealRect,fillRect,fillClip,state:{},metrics:{},si};nodes[a.id]=view;primitives.push(view);
        if(a.kind==='group')continue;
        if(['text','number'].includes(a.kind)){
          view.text=el('text',{'font-family':family,'font-weight':a.kind==='number'||a.payload.purpose==='headline'?'650':'450'},content);
          if(a.kind==='number')view.label=el('text',{'font-family':family,'font-weight':'450'},content);
        }else if(a.kind==='shape'){
          view.area=el('path',{'clip-path':`url(#${fillClip.id})`},content);
          view.outline=el('path',{fill:'none',pathLength:1,'stroke-linejoin':'round'},content);
        }else if(a.kind==='panel'){
          view.area=el('rect',{x:0,y:0,width:g.width,height:g.height,rx:style.strokes.corner_radius,'clip-path':`url(#${fillClip.id})`},content);
          view.outline=el('rect',{x:stroke/2,y:stroke/2,width:Math.max(0,g.width-stroke),height:Math.max(0,g.height-stroke),rx:style.strokes.corner_radius,fill:'none'},content);
        }else if(a.kind==='bar'){
          view.bed=el('rect',{},content);view.area=el('rect',{'clip-path':`url(#${fillClip.id})`},content);view.marker=el('path',{fill:'none'},content);
          view.label=el('text',{'font-family':family},content);
        }else if(a.kind==='axis'){
          view.outline=el('path',{fill:'none',pathLength:1},content);view.ticks=el('g',{},content);
        }else if(a.kind==='connector'){
          view.outline=el('path',{fill:'none',pathLength:1,'stroke-linejoin':'round'},content);view.arrow=el('path',{fill:'none','stroke-linejoin':'round'},content);
        }else if(a.kind==='selector'){
          view.items=a.payload.options.map((s,i)=>{const item=el('g',{'data-option':i},content);return {item,mark:el('path',{fill:'none'},item),text:el('text',{'font-family':family},item),label:s};});
        }else if(a.kind==='particles'){
          view.dots=Array.from({length:a.payload.count},(_,i)=>el('circle',{'data-particle':i},content));
        }else if(a.kind==='image'){
          view.image=el('image',{x:0,y:0,width:g.width,height:g.height,preserveAspectRatio:a.payload.fit==='cover'?'xMidYMid slice':'xMidYMid meet'},content);
          view.outline=el('rect',{x:stroke/2,y:stroke/2,width:Math.max(0,g.width-stroke),height:Math.max(0,g.height-stroke),fill:'none'},content);
        }
      }
      for(const a of scene.actors)(parents[a.id]?nodes[parents[a.id]].content:group).appendChild(nodes[a.id].outer);
      const tracks=[...scene.tracks].sort((a,b)=>a.start_ms-b.start_ms||a.end_ms-b.end_ms);
      return {scene,group,sceneRect,nodes,parents,tracks};
    });
    function checkAlive(){if(destroyed)throw new Error('Film destroyed');}
    function textFit(texts,g,maxLines,size,p,weight='450'){
      let result=null;
      const wrap=(text,s)=>{ctx.font=`${weight} ${s}px ${family}`;const words=text.split(/\s+/u),lines=[];let line='';for(const word of words){if(ctx.measureText(word).width>g.width+.01)return null;const next=line?line+' '+word:word;if(line&&ctx.measureText(next).width>g.width){lines.push(line);line=word;}else line=next;}if(line)lines.push(line);return lines;};
      for(let s=size;s>=Math.min(16,size);s-=.5){const all=texts.map(t=>wrap(t,s));const lineHeight=Math.max(s*1.18,g.line_height?g.line_height*s/size:0);if(all.every(ls=>ls&&ls.length<=maxLines&&ls.length*lineHeight<=g.height+.01)){result={size:s,lineHeight,all};break;}}
      if(!result)throw new boundary.PlanError('Text does not fit readable compiled bounds',p);
      fits.push({actor:p,font_size:result.size,requested_size:size,max_lines:maxLines});return result;
    }
    function setLines(node,lines,size,lineHeight,x=0,y=0){node.replaceChildren();node.setAttribute('font-size',size);lines.forEach((s,i)=>{const t=el('tspan',{x,y:y+size+i*lineHeight},node);t.textContent=s;});}
    function fitAll(){
      for(const v of primitives){const {a}=v,g=a.geometry;const ts=plan.scenes[v.si].tracks.filter(t=>t.actor_id===a.id);
        if(a.kind==='text'){const texts=[a.initial.text,...ts.filter(t=>t.property==='text').map(t=>t.to)];v.metrics=textFit(texts,g,a.payload.max_lines??8,g.font_size,a.id,a.payload.purpose==='headline'?'650':'450');v.texts=new Map(texts.map((t,i)=>[t,v.metrics.all[i]]));}
        if(a.kind==='number'){const values=[a.initial.value,...ts.filter(t=>t.property==='value').flatMap(t=>[t.from,t.to])],texts=values.map(x=>numText(a,x));const labelSize=Math.min(style.typography.label_size,g.font_size*.48),reserve=labelSize*1.4;v.metrics=textFit(texts,{...g,height:g.height-reserve},1,g.font_size,a.id,'650');v.labelFit=textFit([a.label],{width:g.width,height:reserve},1,labelSize,a.id+'.label');}
        if(a.kind==='selector'){const opts=a.payload.options;let fitted=null;for(let columns=1;columns<=Math.min(8,opts.length);columns++){const rows=Math.ceil(opts.length/columns),cw=g.width/columns,ch=g.height/rows;try{const count=fits.length;const m=textFit(opts,{width:cw-24,height:ch-12},2,style.typography.label_size,a.id);fits.length=count;if(!fitted||m.size>fitted.metrics.size)fitted={columns,rows,cw,ch,metrics:m};}catch(e){if(!(e instanceof boundary.PlanError))throw e;}}if(!fitted)throw new boundary.PlanError('Selector options do not fit',a.id);v.metrics=fitted;fits.push({actor:a.id,font_size:fitted.metrics.size,columns:fitted.columns});}
        if(a.kind==='bar')v.labelFit=textFit([a.label],{width:g.width,height:Math.min(g.height*.25,style.typography.label_size*1.4)},1,Math.min(style.typography.label_size,g.height*.18),a.id+'.label');
      }
    }
    function stateAt(view,ms){const states={};for(const a of view.scene.actors)states[a.id]={...a.initial};for(const t of view.tracks){if(ms<t.start_ms)continue;const fraction=t.end_ms===t.start_ms?1:clamp((ms-t.start_ms)/(t.end_ms-t.start_ms));const progress=ease(t.easing,fraction);states[t.actor_id][t.property]=typeof t.from==='number'&&typeof t.to==='number'?t.from+(t.to-t.from)*progress:progress===1?t.to:t.from;}return states;}
    function shapePath(variant,width,height){const x=stroke/2,y=stroke/2,W=Math.max(0,width-stroke),H=Math.max(0,height-stroke),cx=width/2,cy=height/2;
      if(variant==='circle')return `M ${cx-W/2} ${cy} a ${W/2} ${H/2} 0 1 0 ${W} 0 a ${W/2} ${H/2} 0 1 0 ${-W} 0`;
      if(variant==='diamond')return `M ${cx} ${y} L ${x+W} ${cy} L ${cx} ${y+H} L ${x} ${cy} Z`;
      if(variant==='hexagon')return `M ${x+W*.25} ${y} L ${x+W*.75} ${y} L ${x+W} ${cy} L ${x+W*.75} ${y+H} L ${x+W*.25} ${y+H} L ${x} ${cy} Z`;
      const r=Math.min(style.strokes.corner_radius,W/2,H/2);return `M ${x+r} ${y} H ${x+W-r} Q ${x+W} ${y} ${x+W} ${y+r} V ${y+H-r} Q ${x+W} ${y+H} ${x+W-r} ${y+H} H ${x+r} Q ${x} ${y+H} ${x} ${y+H-r} V ${y+r} Q ${x} ${y} ${x+r} ${y} Z`;
    }
    function renderActors(view,ms){const states=stateAt(view,ms);view.states=states;
      function multiply(a,b){return [a[0]*b[0]+a[2]*b[1],a[1]*b[0]+a[3]*b[1],a[0]*b[2]+a[2]*b[3],a[1]*b[2]+a[3]*b[3],a[0]*b[4]+a[2]*b[5]+a[4],a[1]*b[4]+a[3]*b[5]+a[5]];}
      function project(m,p){return {x:m[0]*p.x+m[2]*p.y+m[4],y:m[1]*p.x+m[3]*p.y+m[5]};}
      function inverse(m){const d=m[0]*m[3]-m[1]*m[2];if(!Number.isFinite(d)||d===0)throw new boundary.PlanError('Actor transform is not invertible');return [m[3]/d,-m[1]/d,-m[2]/d,m[0]/d,(m[2]*m[5]-m[3]*m[4])/d,(m[1]*m[4]-m[0]*m[5])/d];}
      function transform(id,stateMap){
        const a=view.nodes[id].a,g=a.geometry,s=stateMap[id],scale=s.scale??1;
        const angle=(s.rotation??0)*Math.PI/180,c=Math.cos(angle)*scale,b=Math.sin(angle)*scale,cx=g.x+g.width/2,cy=g.y+g.height/2;
        let result=[c,b,-b,c,s.x-g.x+cx-c*cx+b*cy,s.y-g.y+cy-b*cx-c*cy];
        if(view.parents[id])result=multiply(transform(view.parents[id],stateMap),result);
        return result;
      }
      function routePoints(id){
        const a=view.nodes[id].a,g=a.geometry,pts=g.points.map(p=>({...p})),current=inverse(transform(id,states));
        for(const [index,target] of [[0,a.payload.from],[pts.length-1,a.payload.to]]){
          const p=pts[index],point=project(current,project(transform(target,states),{x:g.x+p.x,y:g.y+p.y}));
          p.x=point.x-g.x;p.y=point.y-g.y;
        }
        if(a.payload.routing==='elbow'&&pts.length===4){
          if(Math.abs(g.points[1].x-g.points[0].x)<1e-6){const mid=(pts[0].y+pts[3].y)/2;pts[1]={x:pts[0].x,y:mid};pts[2]={x:pts[3].x,y:mid};}
          else{const mid=(pts[0].x+pts[3].x)/2;pts[1]={x:mid,y:pts[0].y};pts[2]={x:mid,y:pts[3].y};}
        }
        return pts;
      }
      function pointAlong(pts,fraction){
        const lengths=pts.slice(1).map((p,i)=>Math.hypot(p.x-pts[i].x,p.y-pts[i].y)),total=lengths.reduce((sum,n)=>sum+n,0);
        if(total<=1e-8)throw new boundary.PlanError('Material route has no traversable length');
        let distance=total*clamp(fraction);
        for(let i=0;i<lengths.length;i++){if(lengths[i]&&distance<=lengths[i]){const t=distance/lengths[i];return {x:pts[i].x+(pts[i+1].x-pts[i].x)*t,y:pts[i].y+(pts[i+1].y-pts[i].y)*t};}distance-=lengths[i];}
        return pts.at(-1);
      }
      function effectiveHighlight(id){let value=states[id].highlight??0;for(let p=view.parents[id];p;p=view.parents[p])value=1-(1-value)*(1-(states[p].highlight??0));return value;}
      for(const a of view.scene.actors){const v=view.nodes[a.id],g=a.geometry,s=states[a.id],highlight=effectiveHighlight(a.id),color=blend(palette[a.role],palette.accent,highlight),sw=stroke*(1+highlight),scale=s.scale??1;
        v.state=s;v.outer.setAttribute('opacity',s.opacity);v.outer.setAttribute('transform',`translate(${s.x-g.x} ${s.y-g.y}) translate(${g.x+g.width/2} ${g.y+g.height/2}) rotate(${s.rotation??0}) scale(${scale}) translate(${-g.x-g.width/2} ${-g.y-g.height/2})`);v.revealRect.setAttribute('width',g.width*(s.reveal??1));v.fillRect.setAttribute('y',g.height*(1-(s.fill??1)));v.fillRect.setAttribute('height',g.height*(s.fill??1));
        if(v.outline){v.outline.setAttribute('stroke',color);v.outline.setAttribute('stroke-width',sw);v.outline.setAttribute('stroke-dasharray',`${s.draw??1} 1`);v.outline.setAttribute('stroke-dashoffset',0);}
        if(v.area)v.area.setAttribute('fill',color);
        if(a.kind==='text'){setLines(v.text,v.texts.get(s.text),v.metrics.size,v.metrics.lineHeight);v.text.setAttribute('fill',color);}
        if(a.kind==='number'){const text=numText(a,s.value);ctx.font=`650 ${v.metrics.size}px ${family}`;if(ctx.measureText(text).width>g.width+.01)throw new boundary.PlanError('Intermediate numeric readout exceeds fitted bounds',a.id);setLines(v.text,[text],v.metrics.size,v.metrics.lineHeight);v.text.setAttribute('fill',color);setLines(v.label,v.labelFit.all[0],v.labelFit.size,v.labelFit.lineHeight,0,v.metrics.size*1.3);v.label.setAttribute('fill',palette.muted);}
        if(a.kind==='shape'){const d=shapePath(s.variant,g.width,g.height);v.area.setAttribute('d',d);v.outline.setAttribute('d',d);v.area.setAttribute('fill-opacity',style.materials.surface==='outlined'?.18:1);}
        if(a.kind==='panel'){v.area.setAttribute('fill-opacity',style.materials.surface==='outlined'?.18:1);v.outline.setAttribute('stroke-dasharray','none');}
        if(a.kind==='bar'){const vertical=a.payload.orientation==='vertical',ratio=(s.value-a.payload.domain[0])/(a.payload.domain[1]-a.payload.domain[0]),top=v.labelFit.size*1.5,innerH=Math.max(0,g.height-top),barW=vertical?g.width*.45:g.width,barH=vertical?innerH:innerH*.45,bx=vertical?(g.width-barW)/2:0,by=top+(vertical?0:(innerH-barH)/2);
          const setRect=(node,x,y,width,height)=>{for(const [k,val] of Object.entries({x,y,width,height}))node.setAttribute(k,val);};
          setRect(v.bed,bx,by,barW,barH);v.bed.setAttribute('fill',palette.surface);v.bed.setAttribute('stroke',color);v.bed.setAttribute('stroke-width',stroke);
          setRect(v.area,bx,by+(vertical?barH*(1-ratio):0),vertical?barW:barW*ratio,vertical?barH*ratio:barH);
          // fill is independent of truthful magnitude, not a substitute for value.
          setRect(v.fillRect,bx,by+barH*(1-(s.fill??1)),barW,barH*(s.fill??1));
          const mx=bx+barW*ratio,my=by+barH*(1-ratio);v.marker.setAttribute('d',vertical?`M ${bx-8} ${my} H ${bx+barW+8}`:`M ${mx} ${by-8} V ${by+barH+8}`);v.marker.setAttribute('stroke',palette.accent);v.marker.setAttribute('stroke-width',sw);setLines(v.label,v.labelFit.all[0],v.labelFit.size,v.labelFit.lineHeight);v.label.setAttribute('fill',palette.text);
        }
        if(a.kind==='axis'){const pts=g.points,d=pts.map((p,i)=>`${i?'L':'M'} ${p.x} ${p.y}`).join(' ');v.outline.setAttribute('d',d);v.ticks.replaceChildren();const first=pts[0],last=pts.at(-1),ticks=a.payload.ticks??5,vertical=a.payload.orientation==='vertical';
          for(let i=0;i<ticks;i++){const f=i/(ticks-1),x=first.x+(last.x-first.x)*f,y=first.y+(last.y-first.y)*f,val=a.payload.domain[0]+(a.payload.domain[1]-a.payload.domain[0])*f;const tick=el('g',{opacity:f<=(s.draw??1)?1:0},v.ticks);el('path',{d:vertical?`M ${x-6} ${y} H ${x+6}`:`M ${x} ${y-6} V ${y+6}`,stroke:color,'stroke-width':sw},tick);const text=el('text',{x:vertical?x+12:x,y:vertical?y+5:y+Math.min(28,g.height*.18),'font-family':family,'font-size':Math.min(style.typography.label_size,Math.max(16,(vertical?g.height:g.width)/ticks*.18)),'text-anchor':vertical?'start':'middle',fill:palette.muted},tick);text.textContent=Number(val.toPrecision(6)).toString();}
        }
        if(a.kind==='connector'){const pts=routePoints(a.id);
          const d=pts.map((p,i)=>`${i?'L':'M'} ${p.x} ${p.y}`).join(' ');v.outline.setAttribute('d',d);
          const total=pts.slice(1).reduce((sum,p,i)=>sum+Math.hypot(p.x-pts[i].x,p.y-pts[i].y),0),extent=total*(s.draw??1);let travelled=0,tip=pts[0],angle=0;for(let i=1;i<pts.length;i++){const a=pts[i-1],b=pts[i],len=Math.hypot(b.x-a.x,b.y-a.y);if(travelled+len>=extent){const t=len?(extent-travelled)/len:0;tip={x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t};angle=Math.atan2(b.y-a.y,b.x-a.x);break;}travelled+=len;}
          const head=Math.max(10,sw*4);v.arrow.setAttribute('d',`M ${tip.x-head*Math.cos(angle-.5)} ${tip.y-head*Math.sin(angle-.5)} L ${tip.x} ${tip.y} L ${tip.x-head*Math.cos(angle+.5)} ${tip.y-head*Math.sin(angle+.5)}`);v.arrow.setAttribute('stroke',color);v.arrow.setAttribute('stroke-width',sw);v.arrow.setAttribute('opacity',a.payload.arrow&&(s.draw??1)>0?1:0);
        }
        if(a.kind==='selector'){const m=v.metrics;v.items.forEach((item,i)=>{const x=(i%m.columns)*m.cw,y=Math.floor(i/m.columns)*m.ch,selected=i===s.selection;item.item.setAttribute('transform',`translate(${x} ${y})`);item.mark.setAttribute('d',`M 4 6 V ${m.ch-6} M 4 ${m.ch-6} H ${m.cw-10}`);item.mark.setAttribute('stroke',selected?color:palette.muted);item.mark.setAttribute('stroke-width',selected?sw:stroke*.5);item.mark.setAttribute('opacity',selected?1:.35);setLines(item.text,m.metrics.all[i],m.metrics.size,m.metrics.lineHeight,16,Math.max(0,(m.ch-m.metrics.all[i].length*m.metrics.lineHeight)/2));item.text.setAttribute('fill',selected?color:palette.muted);item.text.setAttribute('font-weight',selected?'650':'450');});}
        if(a.kind==='particles'){
          const count=a.payload.count,flow=s.flow??0,binding=a.payload.path;
          let pts,r=Math.max(2,Math.min(g.width,g.height)/Math.max(12,Math.sqrt(count)*5));
          if(binding){
            const route=view.nodes[binding.connector].a.geometry,mapping=multiply(inverse(transform(a.id,states)),transform(binding.connector,states));
            pts=routePoints(binding.connector).map(p=>{const point=project(mapping,{x:route.x+p.x,y:route.y+p.y});return {x:point.x-g.x,y:point.y-g.y};});
            r=Math.max(3,Math.min(8,stroke*1.8));
            const x=Math.min(...pts.map(p=>p.x))-r,y=Math.min(...pts.map(p=>p.y))-r;
            rect(v.revealRect,g.x+x,g.y+y,(Math.max(...pts.map(p=>p.x))-x+r)*(s.reveal??1),Math.max(...pts.map(p=>p.y))-y+r);
          }
          v.dots.forEach((dot,i)=>{
            let x,y;const f=(i+.5)/count,phase=(f+flow)%1;
            if(binding){({x,y}=pointAlong(pts,binding.direction==='reverse'?1-phase:phase));}
            else if(a.payload.arrangement==='stream'){x=r+phase*(g.width-2*r);y=g.height/2+Math.sin(i*2.399+flow*Math.PI*2)*g.height*.23;}
            else if(a.payload.arrangement==='radial'){const angle=i*2.399+flow*Math.PI*2,rad=Math.sqrt(f)*.42;x=g.width/2+Math.cos(angle)*rad*g.width;y=g.height/2+Math.sin(angle)*rad*g.height;}
            else{const cols=Math.ceil(Math.sqrt(count*g.width/Math.max(1,g.height))),rows=Math.ceil(count/cols);x=((i%cols+.5+flow)%cols)/cols*g.width;y=(Math.floor(i/cols)+.5)/rows*g.height;}
            dot.setAttribute('cx',x);dot.setAttribute('cy',y);dot.setAttribute('r',r);dot.setAttribute('fill',color);dot.setAttribute('opacity',clamp((s.fill??1)*count-i));
          });
        }
        if(a.kind==='image'){v.outline.setAttribute('stroke',palette.accent);v.outline.setAttribute('stroke-opacity',highlight);v.outline.setAttribute('stroke-dasharray','none');}
      }
    }
    function rect(node,x,y,width,height){for(const [k,v]of Object.entries({x,y,width,height}))node.setAttribute(k,v);}
    function seek(ms){checkAlive();if(!readyDone)throw new Error('Await film.ready before seek');if(!Number.isFinite(ms))throw new Error('seek requires finite milliseconds');at=clamp(ms,0,plan.duration_ms);const index=at===plan.duration_ms?scenes.length-1:scenes.findIndex(v=>at>=v.scene.start_ms&&at<v.scene.end_ms);active=[];
      for(const view of scenes){view.group.setAttribute('display','none');view.group.setAttribute('opacity',1);rect(view.sceneRect,0,0,w,h);}
      const outgoing=scenes[index];renderActors(outgoing,at);outgoing.group.removeAttribute('display');active.push(outgoing.scene.id);
      const tr=outgoing.scene.transition;if((tr.kind==='fade'||tr.kind==='wipe')&&at>=tr.start_ms){const t=clamp((at-tr.start_ms)/(tr.end_ms-tr.start_ms)),incoming=scenes[index+1];if(incoming){renderActors(incoming,incoming.scene.start_ms);incoming.group.removeAttribute('display');active.push(incoming.scene.id);}if(tr.kind==='fade'){outgoing.group.setAttribute('opacity',1-t);if(incoming)incoming.group.setAttribute('opacity',t);}else{const dir=tr.direction;const a=dir==='right'?[w*t,0,w*(1-t),h]:dir==='left'?[0,0,w*(1-t),h]:dir==='down'?[0,h*t,w,h*(1-t)]:[0,0,w,h*(1-t)];const b=dir==='right'?[0,0,w*t,h]:dir==='left'?[w*(1-t),0,w*t,h]:dir==='down'?[0,0,w,h*t]:[0,h*(1-t),w,h*t];rect(outgoing.sceneRect,...a);if(incoming)rect(incoming.sceneRect,...b);}}
      svg.setAttribute('data-time-ms',at);return inspect();
    }
    function inspect(){checkAlive();return JSON.parse(JSON.stringify({schema:'explainer-direction.runtime-inspection/v1',film_id:plan.film_id,time_ms:at,duration_ms:plan.duration_ms,ready:readyDone,error:error?.message??null,active_scenes:active,direction:plan.direction,provenance:plan.provenance,typography:fits,scenes:scenes.filter(v=>active.includes(v.scene.id)).map(v=>({id:v.scene.id,states:v.states,events:v.scene.events.filter(e=>at>=e.start_ms&&at<=e.end_ms).map(e=>e.id)}))}));}
    const imageLoads=primitives.filter(v=>v.a.kind==='image').map(async v=>{
      const {src,mime}=v.a.payload;
      const response=await fetch(src,{credentials:'same-origin'});
      if(!response.ok)throw new boundary.PlanError('Declared raster image could not be decoded',src);
      const bytes=new Uint8Array(await response.arrayBuffer());
      const prefix=(values,offset=0)=>values.every((n,i)=>bytes[offset+i]===n);
      const raster=mime==='image/png'?prefix([137,80,78,71,13,10,26,10]):mime==='image/jpeg'?prefix([255,216,255]):prefix([82,73,70,70])&&prefix([87,69,66,80],8);
      if(!raster)throw new boundary.PlanError('Declared image is not the admitted raster MIME; no SVG fallback',src);
      const url=URL.createObjectURL(new Blob([bytes],{type:mime}));imageURLs.push(url);
      const image=new Image();image.src=url;
      try{await image.decode();}catch(e){throw new boundary.PlanError('Declared raster image could not be decoded',src);}
      if(destroyed){URL.revokeObjectURL(url);return;}
      v.image.setAttribute('href',url);
    });
    const ready=Promise.all([font.load().then(f=>{if(destroyed)return;document.fonts.add(f);}),...imageLoads]).then(()=>{checkAlive();fitAll();readyDone=true;seek(0);return inspect();}).catch(e=>{error=e;svg.remove();document.fonts.delete(font);imageURLs.forEach(url=>URL.revokeObjectURL(url));if(typeof options.onError==='function')options.onError(e);throw e;});
    function destroy(){if(destroyed)return;destroyed=true;svg.remove();document.fonts.delete(font);imageURLs.forEach(url=>URL.revokeObjectURL(url));}
    return Object.freeze({ready,seek,inspect,destroy});
  }
  root.ExplainerDirection=Object.freeze({createFilm,version:'explainer-direction.runtime/v1'});
})(window);
