(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.NexStickFamilyVisualizerV1=factory();})(typeof globalThis!=='undefined'?globalThis:this,function(){'use strict';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
const f=n=>Number(n).toFixed(2);const mix=(a,b,t)=>a+(b-a)*t;
function project(p,yaw=-14){const a=yaw*Math.PI/180,c=Math.cos(a),s=Math.sin(a);return {x:p[0]*c+p[2]*s,y:p[1],depth:-p[0]*s+p[2]*c};}
function points(state){const o={};for(const [k,v] of Object.entries(state.pose3d||{}))o[k]=project(v);return o}
function svgCharacter(state,family,opts={}){
 const P=points(state),m=family.morphology,meta=state.morphology?.visual||{},ppm=opts.ppm||220,ox=opts.x||0,ground=opts.groundY||0,baseFloor=Math.min(P.toe_l.y,P.toe_r.y,P.ankle_l.y,P.ankle_r.y),toPx=q=>({x:ox+q.x*ppm,y:ground-(q.y-baseFloor)*ppm});
 const Q={};for(const [k,v] of Object.entries(P))Q[k]=toPx(v);const line=Math.max(opts.minLimbPx||3.2,(meta.limbRadius||.026)*2*ppm),foot=Math.max(line*1.05,(meta.footThickness||.035)*2*ppm),handR=Math.max(2.8,(meta.handRadius||.035)*ppm),headR=Math.max(8,(meta.headRadius||.115)*ppm);
 const centerChest={x:(Q.shoulder_l.x+Q.shoulder_r.x)/2,y:Q.chest.y},centerPelvis={x:(Q.hip_l.x+Q.hip_r.x)/2,y:Q.pelvis.y};
 const shWorld=meta.shoulderWidth||(.42*m.overallScale*m.shoulderWidth),hipWorld=meta.hipWidth||(.36*m.overallScale*m.hipWidth),skelSh=meta.skeletalShoulderWidth||1;
 const shProj=Math.abs(P.shoulder_l.x-P.shoulder_r.x),view=Math.max(.42,Math.min(1,shProj/Math.max(.001,skelSh))),sw=shWorld*ppm*view,hw=hipWorld*ppm*Math.max(.5,view),waist=sw*(.68+.08*(m.waistWidth||1));
 const waistY=mix(centerChest.y,centerPelvis.y,.58),torso=`M ${f(centerChest.x-sw/2)} ${f(centerChest.y)} Q ${f(centerChest.x-waist/2)} ${f(waistY)} ${f(centerPelvis.x-hw/2)} ${f(centerPelvis.y)} L ${f(centerPelvis.x+hw/2)} ${f(centerPelvis.y)} Q ${f(centerChest.x+waist/2)} ${f(waistY)} ${f(centerChest.x+sw/2)} ${f(centerChest.y)} Z`;
 const seg=(a,b,cls='limb',w=line)=>`<line class="${cls}" x1="${f(Q[a].x)}" y1="${f(Q[a].y)}" x2="${f(Q[b].x)}" y2="${f(Q[b].y)}" stroke-width="${f(w)}"/>`;
 let out=`<g class="nex-family-character" data-family="${esc(family.id)}">`;
 out+=seg('hip_l','knee_l')+seg('knee_l','ankle_l')+seg('hip_r','knee_r')+seg('knee_r','ankle_r');
 out+=seg('shoulder_l','elbow_l')+seg('elbow_l','wrist_l')+seg('shoulder_r','elbow_r')+seg('elbow_r','wrist_r');
 out+=`<path class="torso" d="${torso}" stroke-width="${f(Math.max(2.6,line*.42))}"/>`;
 out+=seg('chest','neck','neck',Math.max(2.8,line*.55));
 out+=`<circle class="head" cx="${f(Q.head.x)}" cy="${f(Q.head.y)}" r="${f(headR)}" stroke-width="${f(Math.max(2.8,line*.42))}"/>`;
 const eyeSep=headR*.28,eyeY=Q.head.y-headR*.08;out+=`<circle class="face" cx="${f(Q.head.x-eyeSep)}" cy="${f(eyeY)}" r="${f(Math.max(1.2,headR*.055))}"/><circle class="face" cx="${f(Q.head.x+eyeSep)}" cy="${f(eyeY)}" r="${f(Math.max(1.2,headR*.055))}"/>`;
 for(const s of ['l','r']){out+=`<circle class="hand" cx="${f(Q['wrist_'+s].x)}" cy="${f(Q['wrist_'+s].y)}" r="${f(handR)}" stroke-width="${f(Math.max(2,line*.32))}"/>`;out+=seg('ankle_'+s,'toe_'+s,'foot',foot)}
 if(state.prop&&Array.isArray(state.prop.position)){const pp=toPx(project(state.prop.position));const size=state.prop.size||[.12,.07,.08],pw=Math.max(8,(size[0]||.12)*ppm),ph=Math.max(7,(size[1]||.07)*ppm);out+=`<rect class="prop" x="${f(pp.x-pw/2)}" y="${f(pp.y-ph/2)}" width="${f(pw)}" height="${f(ph)}" rx="${f(Math.min(8,ph*.2))}"/>`}
 out+='</g>';return out;
}
function style(){return `<style>.limb,.neck,.foot{stroke:#1e2329;fill:none;stroke-linecap:round;stroke-linejoin:round}.torso,.head,.hand{fill:#fbfbf8;stroke:#1e2329;stroke-linejoin:round}.face{fill:#1e2329}.prop{fill:#dedede;stroke:#1e2329;stroke-width:2.2}.family-label{font-family:Arial,sans-serif;font-size:20px;font-weight:650;fill:#1e2329}.action-label{font-family:Arial,sans-serif;font-size:15px;font-weight:600;fill:#555}.note{font-family:Arial,sans-serif;font-size:13px;fill:#70757b}.gridline{stroke:#e7e7e3;stroke-width:1}.ground{stroke:#d5d5d0;stroke-width:1.5}</style>`}
function wrap(width,height,body,bg='#f5f5f1'){return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"><rect width="100%" height="100%" fill="${bg}"/>${style()}${body}</svg>`}
return {version:'1.0.0',project,svgCharacter,style,wrap};
});
