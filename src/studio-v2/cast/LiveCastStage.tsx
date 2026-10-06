"use client";
import {useEffect,useRef,useState} from 'react';
import * as THREE from 'three';
import {GLTFLoader,type GLTF} from 'three/examples/jsm/loaders/GLTFLoader.js';
import AvatarStage,{type AvatarPreviewState} from './AvatarStage';
import {environmentImage,environmentAspect} from './environments';
import {hairShadeRatio,hairTint,liveColours,luminance,selectLiveParts,tintRatio,type LiveManifest,type LivePart,type LiveSelection} from './live3d-parts';
import {normalizeCastSpec,type CastSpec} from './spec';

const BASE='/api/v1/studio/cast/live3d/';
const FRAME={x:-0.42,y:1.16,height:1.36,aspect:3/4};
let manifestRequest:Promise<LiveManifest>|null=null;
const loadManifest=()=>manifestRequest??=fetch(BASE+'manifest.json',{credentials:'include',cache:'no-cache'}).then(r=>{if(!r.ok)throw new Error('CAST_LIVE3D_UNAVAILABLE');return r.json() as Promise<LiveManifest>;}).catch(e=>{manifestRequest=null;throw e;});
const files=new Map<string,Promise<ArrayBuffer>>(),models=new Map<string,Promise<GLTF>>(),lineObjects=new Map<string,THREE.LineSegments>(),hairObjects=new Map<string,{line:THREE.LineSegments;base:Float32Array}>();
const binary=(url:string,version:string)=>{const u=`${BASE}${url}?v=${version}`;let p=files.get(u);if(!p){p=fetch(u,{credentials:'include'}).then(r=>{if(!r.ok)throw new Error('CAST_LIVE3D_PART_MISSING');return r.arrayBuffer();});p.catch(()=>files.delete(u));files.set(u,p);}return p;};
const model=(url:string,version:string)=>{let p=models.get(url);if(!p){p=binary(url,version).then(b=>new GLTFLoader().parseAsync(b,''));p.catch(()=>models.delete(url));models.set(url,p);}return p;};
const toThree=(f:Float32Array,i:number,out:Float32Array,o:number)=>{out[o]=f[i];out[o+1]=f[i+2];out[o+2]=-f[i+1];};

function lines(buf:ArrayBuffer){
 const f=new Float32Array(buf),n=f.length/10,P=new Float32Array(n*6),C=new Float32Array(n*6);
 for(let i=0;i<n;i++){toThree(f,i*10,P,i*6);toThree(f,i*10+3,P,i*6+3);P[i*6+2]+=.004;P[i*6+5]+=.004;for(let k=0;k<2;k++)C.set(f.subarray(i*10+6,i*10+9),i*6+k*3);}
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(P,3));g.setAttribute('color',new THREE.BufferAttribute(C,3));
 return new THREE.LineSegments(g,new THREE.LineBasicMaterial({vertexColors:true,transparent:true,opacity:.75}));
}
function hair(buf:ArrayBuffer){
 const [np,no]=new Uint32Array(buf,0,2),pos=new Float32Array(buf,8,np*3),off=new Int32Array(buf,8+np*12,no),c8=new Uint8Array(buf,8+np*12+no*4,np*3);
 let m=0;for(let i=0;i<no-1;i++)m+=Math.max(0,off[i+1]-off[i]-1);
 const P=new Float32Array(m*6),C=new Float32Array(m*6),t=new THREE.Color();let j=0;
 const put=(p:number,o:number)=>{toThree(pos,p*3,P,o);t.setRGB(c8[p*3]/255,c8[p*3+1]/255,c8[p*3+2]/255,THREE.SRGBColorSpace);C[o]=t.r;C[o+1]=t.g;C[o+2]=t.b;};
 for(let i=0;i<no-1;i++)for(let k=off[i];k<off[i+1]-1;k++){put(k,j*6);put(k+1,j*6+3);j++;}
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(P,3));g.setAttribute('color',new THREE.BufferAttribute(C,3));
 return {line:new THREE.LineSegments(g,new THREE.LineBasicMaterial({vertexColors:true})),base:C.slice()};
}
function mergeCornerColours(mesh:THREE.Mesh){
 if(mesh.userData.merged)return;mesh.userData.merged=true;
 const pos=mesh.geometry.getAttribute('position'),col=mesh.geometry.getAttribute('color');if(!(col instanceof THREE.BufferAttribute)||mesh.userData.base)return;
 const arr=col.array as Float32Array|Uint16Array|Uint8Array,n=col.itemSize,at=new Map<string,number[]>();
 for(let i=0;i<pos.count;i++){const k=`${Math.round(pos.getX(i)*1e5)},${Math.round(pos.getY(i)*1e5)},${Math.round(pos.getZ(i)*1e5)}`;const g=at.get(k);if(g)g.push(i);else at.set(k,[i]);}
 for(const g of at.values()){if(g.length<2)continue;for(let k=0;k<3;k++){const v=g.map(i=>arr[i*n+k]).sort((x,y)=>x-y),m=v.length%2?v[v.length>>1]:(v[v.length/2-1]+v[v.length/2])/2;for(const i of g)arr[i*n+k]=m;}}
 col.needsUpdate=true;
}
function colourAttribute(mesh:THREE.Mesh){const a=mesh.geometry.getAttribute('color');if(!(a instanceof THREE.BufferAttribute))return null;mesh.userData.base??=Float32Array.from(a.array as ArrayLike<number>);return {a,base:mesh.userData.base as Float32Array};}
const lipBoundary=(v:number)=>{const t=Math.min(1,Math.max(0,(v+.04)/.08));return t*t*(3-2*t);};
function multiply(mesh:THREE.Mesh,factor:(i:number,lip:number)=>readonly number[]){
 const c=colourAttribute(mesh);if(!c)return;const lip=mesh.geometry.getAttribute('_lipmask'),n=c.a.itemSize,arr=c.a.array as Float32Array|Uint16Array|Uint8Array,scale=c.a.normalized?(arr instanceof Uint16Array?65535:255):1;
 for(let i=0;i<c.a.count;i++){const f=factor(i,lip?lipBoundary(lip.getX(i)):0);for(let k=0;k<3;k++)arr[i*n+k]=Math.max(0,Math.min(scale,c.base[i*n+k]*f[k]));}c.a.needsUpdate=true;
}
function lipShade(mesh:THREE.Mesh,skin:readonly number[],lip:readonly number[]){
 const c=colourAttribute(mesh);if(!c)return;(c.a.array as Float32Array|Uint16Array|Uint8Array).set(c.base);c.a.needsUpdate=true;
 let mat=mesh.userData.lipMaterial as THREE.MeshBasicMaterial|undefined;
 if(!mat){
  const uniforms={skinRatio:{value:new THREE.Vector3()},lipRatio:{value:new THREE.Vector3()}};
  mat=new THREE.MeshBasicMaterial({vertexColors:true,side:THREE.DoubleSide});mat.userData.uniforms=uniforms;
  mat.onBeforeCompile=sh=>{Object.assign(sh.uniforms,uniforms);
   sh.vertexShader='attribute float _lipmask;\nvarying float vLip;\n'+sh.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nvLip=_lipmask;');
   sh.fragmentShader='uniform vec3 skinRatio;\nuniform vec3 lipRatio;\nvarying float vLip;\n'+sh.fragmentShader.replace('#include <color_fragment>','#include <color_fragment>\ndiffuseColor.rgb=min(diffuseColor.rgb*mix(skinRatio,lipRatio,smoothstep(-.04,.04,vLip)),vec3(1.));');};
  mesh.userData.lipMaterial=mat;
 }
 const u=mat.userData.uniforms as {skinRatio:{value:THREE.Vector3};lipRatio:{value:THREE.Vector3}};u.skinRatio.value.set(skin[0],skin[1],skin[2]);u.lipRatio.value.set(lip[0],lip[1],lip[2]);mesh.material=mat;
}
type HairTint={colour:readonly number[];scale:number;ratio:readonly number[]|null};
function recolourHair(target:Float32Array|Uint16Array|Uint8Array,base:ArrayLike<number>,n:number,count:number,tint:HairTint,scale=1){
 if(tint.ratio){for(let i=0;i<count;i++)for(let k=0;k<3;k++)target[i*n+k]=Math.min(scale,base[i*n+k]*tint.ratio[k]);return;}
 for(let i=0;i<count;i++){const l=luminance(base[i*n]/scale,base[i*n+1]/scale,base[i*n+2]/scale)*tint.scale;for(let k=0;k<3;k++)target[i*n+k]=Math.min(scale,tint.colour[k]*l*scale);}
}
function nameOf(o:THREE.Object3D){let n=o.name;for(let p=o.parent;p&&!n.startsWith('L3D_');p=p.parent)n=p.name;return n.replace(/^L3D_Host\.?/,'').replace(/\./g,'');}

const ID_MATERIALS=[0,1,2,3].map(i=>new THREE.MeshBasicMaterial({color:new THREE.Color(i===0?0:1,i===2?1:0,i===3?1:0),side:THREE.DoubleSide}));
const OUTLINE_VERTEX='varying vec2 vUv;void main(){vUv=uv;gl_Position=vec4(position.xy,0.,1.);}';
const OUTLINE_FRAGMENT=`uniform sampler2D ids;uniform vec2 texel;uniform float strength;uniform vec3 ink;varying vec2 vUv;
void main(){vec3 c=texture2D(ids,vUv).rgb,m=c;for(int x=-1;x<=1;x++)for(int y=-1;y<=1;y++)m=max(m,texture2D(ids,vUv+vec2(x,y)*texel).rgb);
float a=max(m.r-c.r,max((m.g-c.g)*c.r,(m.b-c.b)*c.r));gl_FragColor=vec4(ink,clamp(a,0.,1.)*strength);}`;
type Outline={target:THREE.WebGLRenderTarget;scene:THREE.Scene;camera:THREE.OrthographicCamera;material:THREE.ShaderMaterial};
function outlinePass():Outline{
 const material=new THREE.ShaderMaterial({vertexShader:OUTLINE_VERTEX,fragmentShader:OUTLINE_FRAGMENT,transparent:true,depthTest:false,depthWrite:false,uniforms:{ids:{value:null},texel:{value:new THREE.Vector2()},strength:{value:1},ink:{value:new THREE.Color()}}});
 const scene=new THREE.Scene();scene.add(new THREE.Mesh(new THREE.PlaneGeometry(2,2),material));
 return {target:new THREE.WebGLRenderTarget(1,1,{samples:4}),scene,camera:new THREE.OrthographicCamera(-1,1,1,-1,0,1),material};
}
function drawOutline(renderer:THREE.WebGLRenderer,scene:THREE.Scene,camera:THREE.Camera,pass:Outline,outline:{width:number;colour:number},unitsPerPixel:number){
 const size=renderer.getDrawingBufferSize(new THREE.Vector2());pass.target.setSize(size.x,size.y);
 const saved=new Map<THREE.Object3D,THREE.Material|THREE.Material[]>(),hidden:THREE.Object3D[]=[];
 scene.traverse(o=>{if(o instanceof THREE.Mesh){saved.set(o,o.material);o.material=ID_MATERIALS[o.userData.inkId??0]??ID_MATERIALS[0];}
  else if(o instanceof THREE.LineSegments){if(o.userData.fibre){saved.set(o,o.material);o.material=ID_MATERIALS[1];}else if(o.visible){o.visible=false;hidden.push(o);}}});
 const clear=renderer.getClearColor(new THREE.Color()),alpha=renderer.getClearAlpha();renderer.setClearColor(0x000000,1);
 renderer.setRenderTarget(pass.target);renderer.clear();renderer.render(scene,camera);renderer.setRenderTarget(null);renderer.setClearColor(clear,alpha);
 saved.forEach((m,o)=>{(o as THREE.Mesh).material=m;});hidden.forEach(o=>{o.visible=true;});
 const step=Math.max(1,outline.width/unitsPerPixel),u=pass.material.uniforms;
 u.ids.value=pass.target.texture;u.texel.value.set(step/size.x,step/size.y);u.strength.value=Math.min(1,outline.width/unitsPerPixel);(u.ink.value as THREE.Color).setRGB(outline.colour,outline.colour,outline.colour,THREE.LinearSRGBColorSpace);
 const auto=renderer.autoClear;renderer.autoClear=false;renderer.render(pass.scene,pass.camera);renderer.autoClear=auto;
}

async function assemble(spec:CastSpec,manifest:LiveManifest,selection:LiveSelection){
 const s=normalizeCastSpec(spec),female=s.character==='female',want=liveColours(s),group=new THREE.Group();
 for(const [name,entry] of Object.entries(selection) as [string,{key:string;part:LivePart}][]){
  const part=entry.part,node=(await model(part.glb,manifest.version)).scene;
  node.traverse(o=>{if(o instanceof THREE.Mesh){if(!(o.material instanceof THREE.MeshBasicMaterial))o.material=new THREE.MeshBasicMaterial({vertexColors:true,side:THREE.DoubleSide});o.userData.inkId=part.ink?.[nameOf(o)]??(name==='hair'?1:0);}});
  if(name==='body'&&!globalThis.location?.search.includes('nomerge'))node.traverse(o=>{if(o instanceof THREE.Mesh&&/^(?:body|V60_ear_(?:fill|inner))/.test(nameOf(o)))mergeCornerColours(o);});
  if(name==='body'&&part.skin){const skin=tintRatio(want.skin,part.skin),lip=female&&want.lip&&part.lip?tintRatio(want.lip,part.lip):skin;node.traverse(o=>{if(o instanceof THREE.Mesh&&/^(?:body|V60_ear_(?:fill|inner))/.test(nameOf(o))){if(female&&o.geometry.getAttribute('_lipmask'))lipShade(o,skin,lip);else multiply(o,()=>skin);}});}
  const ht=name==='hair'&&part.hairHex?{...hairTint(want.hair,part.hairHex),ratio:hairShadeRatio(manifest,female?'f':'m',want.hair,part.hairHex)}:null;
  if(ht)node.traverse(o=>{if(o instanceof THREE.Mesh){const c=colourAttribute(o);if(c){const arr=c.a.array as Float32Array|Uint16Array|Uint8Array;recolourHair(arr,c.base,c.a.itemSize,c.a.count,ht,c.a.normalized?(arr instanceof Uint16Array?65535:255):1);c.a.needsUpdate=true;}}});
  if(name==='garment'&&part.tint)for(const [asset,base] of Object.entries(part.tint)){const ratio=tintRatio(want.garments[asset]??base,base),prefix=asset.replace(/\./g,'');node.traverse(o=>{if(o instanceof THREE.Mesh&&nameOf(o).startsWith(prefix))multiply(o,()=>ratio);});}
  group.add(node);
  if(part.lines){let l=lineObjects.get(part.lines);if(!l){l=lines(await binary(part.lines,manifest.version));lineObjects.set(part.lines,l);}group.add(l);}
  if(part.hair){let h=hairObjects.get(part.hair);if(!h){h=hair(await binary(part.hair,manifest.version));h.line.userData.fibre=true;hairObjects.set(part.hair,h);}
   const colour=h.line.geometry.getAttribute('color');if(colour instanceof THREE.BufferAttribute){if(ht)recolourHair(colour.array as Float32Array,h.base,3,colour.count,ht);else (colour.array as Float32Array).set(h.base);colour.needsUpdate=true;}group.add(h.line);}
 }
 return group;
}

export default function LiveCastStage({spec,className,onStatus}:{spec:CastSpec;className?:string;onStatus?:(state:AvatarPreviewState)=>void}){
 const host=useRef<HTMLDivElement>(null),canvas=useRef<HTMLCanvasElement>(null),state=useRef<{renderer:THREE.WebGLRenderer;scene:THREE.Scene;camera:THREE.OrthographicCamera;outline:Outline;style:LiveManifest['outline']}|null>(null);
 const [noWebgl,setNoWebgl]=useState(false),[failedKey,setFailedKey]=useState<string|null>(null),[readyKey,setReadyKey]=useState<string|null>(null);
 const statusRef=useRef(onStatus);statusRef.current=onStatus;
 const key=JSON.stringify(normalizeCastSpec(spec)),fallback=noWebgl||failedKey===key,ready=readyKey===key;
 const draw=()=>{const st=state.current,el=host.current;if(!st||!el)return;const w=Math.max(1,el.clientWidth),h=Math.max(1,el.clientHeight);st.renderer.setSize(w,h,false);
  const half=FRAME.height/2,aspect=w/h,hw=aspect>FRAME.aspect?half*aspect:half*FRAME.aspect,hh=aspect>FRAME.aspect?half:half*FRAME.aspect/aspect;
  Object.assign(st.camera,{left:-hw,right:hw,top:hh,bottom:-hh});st.camera.updateProjectionMatrix();
  st.renderer.render(st.scene,st.camera);if(st.style)drawOutline(st.renderer,st.scene,st.camera,st.outline,st.style,2*hh/st.renderer.getDrawingBufferSize(new THREE.Vector2()).y);};
 useEffect(()=>{
  if(!canvas.current)return;
  try{const renderer=new THREE.WebGLRenderer({canvas:canvas.current,antialias:true,alpha:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(2,window.devicePixelRatio||1));renderer.setClearColor(0xffffff,0);
   const camera=new THREE.OrthographicCamera(-1,1,1,-1,.01,100);camera.position.set(FRAME.x,FRAME.y,5);camera.lookAt(FRAME.x,FRAME.y,0);state.current={renderer,scene:new THREE.Scene(),camera,outline:outlinePass(),style:null};}
  catch{setNoWebgl(true);return;}
  const resize=new ResizeObserver(draw);if(host.current)resize.observe(host.current);
  return()=>{resize.disconnect();state.current?.outline.target.dispose();state.current?.outline.material.dispose();state.current?.renderer.dispose();state.current=null;};
 },[]);
 useEffect(()=>{
  if(fallback)return;let cancelled=false;statusRef.current?.('loading');
  loadManifest().then(async manifest=>{
   const {selection,missing}=selectLiveParts(spec,manifest);if(missing.length)throw new Error('CAST_LIVE3D_PART_MISSING');
   const st=state.current;if(!st)return;const group=await assemble(spec,manifest,selection);if(cancelled)return;
   st.scene.clear();st.scene.add(group);st.style=manifest.outline??null;draw();setReadyKey(key);statusRef.current?.('ready');
  }).catch(()=>{if(!cancelled)setFailedKey(key);});
  return()=>{cancelled=true;};
 // eslint-disable-next-line react-hooks/exhaustive-deps
 },[key,fallback]);
 return <>{fallback&&<AvatarStage spec={spec} className={className} onStatus={onStatus}/>}<div ref={host} className={`cast-render-stage cast-live3d-stage ${className??''}`} hidden={fallback} aria-busy={!ready} data-preview-state={ready?'ready':'loading'} style={spec.environment?{aspectRatio:environmentAspect[spec.environmentFormat??'square'],height:'auto',maxHeight:'100%'}:undefined}>
  {spec.environment&&<img className="cast-environment-plate" src={environmentImage(spec.environment,spec.environmentFormat??'square')} alt=""/>}
  <canvas ref={canvas} role="img" aria-label={`${spec.character==='female'?'Female':'Male'} presenter preview`} style={{position:'absolute',inset:0,width:'100%',height:'100%'}}/>
  {!ready&&<div className="cast-preview-status cast-preview-status-pending" role="status"><span className="cast-preview-spinner"/><span>Loading presenter…</span></div>}
 </div></>;
}
