import * as THREE from 'three';
const D=new URLSearchParams(location.search).get('d')||'./cache/',FRAME={x:-0.42,y:1.16,height:1.36},BODY_DEPTH=.003,OUTLINE={width:1.36/1440,colour:.008};
const meta=await (await fetch(D+'meta.json')).json();
const bin=async(u,T)=>new T(await (await fetch(D+u)).arrayBuffer());
const renderer=new THREE.WebGLRenderer({canvas:document.getElementById('c'),antialias:true,alpha:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(1);renderer.setSize(1080,1440,false);renderer.setClearColor(0xffffff,0);
const hh=FRAME.height/2,hw=hh*1080/1440;
const camera=new THREE.OrthographicCamera(-hw,hw,hh,-hh,.01,100);camera.position.set(FRAME.x,FRAME.y,5);camera.lookAt(FRAME.x,FRAME.y,0);
const scene=new THREE.Scene();
const ID=[0,1,2,3].map(i=>new THREE.MeshBasicMaterial({color:new THREE.Color(i===0?0:1,i===2?1:0,i===3?1:0),side:THREE.DoubleSide}));
const meshes=[];
for(let i=0;i<meta.objects.length;i++){
 const o=meta.objects[i],idx=await bin(`obj${i}.idx`,Uint32Array),col=await bin(`obj${i}.col`,Float32Array);
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(new Float32Array(idx.length*3),3));g.setAttribute('color',new THREE.BufferAttribute(col,3));
 const m=new THREE.Mesh(g,new THREE.MeshBasicMaterial({vertexColors:true,side:THREE.DoubleSide}));m.userData.inkId=o.ink;m.position.z=o.body?-BODY_DEPTH:0;m.frustumCulled=false;
 scene.add(m);meshes.push({m,idx,o});
}
const L=await bin('lines.bin',Float32Array),nl=L.length/6,LP=new Float32Array(nl*6),LC=new Float32Array(nl*6);
for(let i=0;i<nl;i++)for(let k=0;k<2;k++)LC.set(L.subarray(i*6+3,i*6+6),i*6+k*3);
const lg=new THREE.BufferGeometry();lg.setAttribute('position',new THREE.BufferAttribute(LP,3));lg.setAttribute('color',new THREE.BufferAttribute(LC,3));
const lineObj=new THREE.LineSegments(lg,new THREE.LineBasicMaterial({vertexColors:true,transparent:true,opacity:.75}));lineObj.frustumCulled=false;scene.add(lineObj);
const hb=await (await fetch(D+'hair.bin')).arrayBuffer();const [np_,no]=new Uint32Array(hb,0,2),hpos=new Float32Array(hb,8,np_*3),hoff=new Int32Array(hb,8+np_*12,no),hc8=new Uint8Array(hb,8+np_*12+no*4,np_*3);
let nm=0;for(let i=0;i<no-1;i++)nm+=Math.max(0,hoff[i+1]-hoff[i]-1);
const HP=new Float32Array(nm*6),HC=new Float32Array(nm*6),hsrc=new Uint32Array(nm*2),tc=new THREE.Color();{let j=0;for(let i=0;i<no-1;i++)for(let k=hoff[i];k<hoff[i+1]-1;k++){for(const [q,p] of [[0,k],[1,k+1]]){hsrc[j*2+q]=p;tc.setRGB(hc8[p*3]/255,hc8[p*3+1]/255,hc8[p*3+2]/255,THREE.SRGBColorSpace);HC.set([tc.r,tc.g,tc.b],j*6+q*3);}j++;}}
const hg=new THREE.BufferGeometry();hg.setAttribute('position',new THREE.BufferAttribute(HP,3));hg.setAttribute('color',new THREE.BufferAttribute(HC,3));
const hairObj=new THREE.LineSegments(hg,new THREE.LineBasicMaterial({vertexColors:true}));hairObj.userData.fibre=true;hairObj.frustumCulled=false;scene.add(hairObj);
const pass={target:new THREE.WebGLRenderTarget(1080,1440,{samples:4}),material:new THREE.ShaderMaterial({vertexShader:'varying vec2 vUv;void main(){vUv=uv;gl_Position=vec4(position.xy,0.,1.);}',fragmentShader:`uniform sampler2D ids;uniform vec2 texel;uniform float strength;uniform vec3 ink;varying vec2 vUv;
void main(){vec3 c=texture2D(ids,vUv).rgb,m=c;for(int x=-1;x<=1;x++)for(int y=-1;y<=1;y++)m=max(m,texture2D(ids,vUv+vec2(x,y)*texel).rgb);
float a=max(m.r-c.r,max((m.g-c.g)*c.r,(m.b-c.b)*c.r));gl_FragColor=vec4(ink,clamp(a,0.,1.)*strength);}`,transparent:true,depthTest:false,depthWrite:false,uniforms:{ids:{value:null},texel:{value:new THREE.Vector2()},strength:{value:1},ink:{value:new THREE.Color()}}})};
const ps=new THREE.Scene();ps.add(new THREE.Mesh(new THREE.PlaneGeometry(2,2),pass.material));const pc=new THREE.OrthographicCamera(-1,1,1,-1,0,1);
function outline(){
 const saved=new Map(),hidden=[];
 scene.traverse(o=>{if(o.isMesh){saved.set(o,o.material);o.material=ID[o.userData.inkId??0]??ID[0];}else if(o.isLineSegments){if(o.userData.fibre){saved.set(o,o.material);o.material=ID[1];}else if(o.visible){o.visible=false;hidden.push(o);}}});
 renderer.setClearColor(0,1);renderer.setRenderTarget(pass.target);renderer.clear();renderer.render(scene,camera);renderer.setRenderTarget(null);renderer.setClearColor(0xffffff,0);
 saved.forEach((m,o)=>o.material=m);hidden.forEach(o=>o.visible=true);
 const upp=FRAME.height/1440,step=Math.max(1,OUTLINE.width/upp),u=pass.material.uniforms;u.ids.value=pass.target.texture;u.texel.value.set(step/1080,step/1440);u.strength.value=Math.min(1,OUTLINE.width/upp);u.ink.value.setRGB(OUTLINE.colour,OUTLINE.colour,OUTLINE.colour,THREE.LinearSRGBColorSpace);
 renderer.autoClear=false;renderer.render(ps,pc);renderer.autoClear=true;
}
window.renderFrame=async f=>{
 const fi=meta.frames.indexOf(f),P=await bin(`frames/${String(f).padStart(4,'0')}.bin`,Float32Array),vis=meta.visible[fi];
 meshes.forEach(({m,idx,o},i)=>{m.visible=vis[i];if(!vis[i])return;const a=m.geometry.attributes.position.array,base=o.offset*3;for(let c=0;c<idx.length;c++){const s=base+idx[c]*3;a[c*3]=P[s];a[c*3+1]=P[s+2];a[c*3+2]=-P[s+1];}m.geometry.attributes.position.needsUpdate=true;});
 for(let i=0;i<nl;i++){const o=meta.objects[L[i*6]],dz=o.body?-BODY_DEPTH:0;for(let k=0;k<2;k++){const s=(o.offset+L[i*6+1+k])*3;LP[i*6+k*3]=P[s];LP[i*6+k*3+1]=P[s+2];LP[i*6+k*3+2]=-P[s+1]+.004+dz;}}
 lg.attributes.position.needsUpdate=true;
 const M=meta.hair[fi];if(M){for(let j=0;j<hsrc.length;j++){const p=hsrc[j]*3,x=hpos[p],y=hpos[p+1],z=hpos[p+2];const X=M[0]*x+M[1]*y+M[2]*z+M[9],Y=M[3]*x+M[4]*y+M[5]*z+M[10],Z=M[6]*x+M[7]*y+M[8]*z+M[11];HP[j*3]=X;HP[j*3+1]=Z;HP[j*3+2]=-Y;}hg.attributes.position.needsUpdate=true;}
 renderer.render(scene,camera);outline();
 return renderer.domElement.toDataURL('image/png');
};
window.ready=true;
