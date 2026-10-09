"use client";
import {useEffect,useRef,useState} from 'react';
import {environmentImage,environmentAspect} from './environments';
import {castRenderConfig} from './render-config';
import {normalizeCastSpec,type CastSpec} from './spec';
export type AvatarPreviewState='loading'|'ready'|'failed';
type Preview={key:string;status:'queued'|'rendering'|'ready'|'failed';imageUrl?:string;message?:string};
const COMPLETE=new Map<string,string>(),REQUESTS=new Map<string,Promise<string>>();
async function requestPreview(spec:CastSpec):Promise<string>{
 const key=JSON.stringify(castRenderConfig(spec)),cached=COMPLETE.get(key);if(cached)return cached;
 let pending=REQUESTS.get(key);
 if(!pending){
  pending=(async()=>{
   const response=await fetch('/api/v1/studio/cast/previews',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify(spec)});
   if(!response.ok)throw new Error('Preview unavailable. Try again.');
   let preview=(await response.json()).data as Preview;const deadline=Date.now()+20*60_000;
   while(preview.status!=='ready'){
    if(preview.status==='failed')throw new Error(preview.message??'Preview could not be rendered.');
    if(Date.now()>deadline)throw new Error('Preview is taking longer than expected. Try again.');
    await new Promise(resolve=>setTimeout(resolve,1500));
    const poll=await fetch(`/api/v1/studio/cast/previews/${preview.key}`,{credentials:'include',cache:'no-store'});if(!poll.ok)throw new Error('Preview unavailable. Try again.');preview=(await poll.json()).data as Preview;
   }
   if(!preview.imageUrl)throw new Error('Preview image unavailable.');
   await new Promise<void>((resolve,reject)=>{const img=new Image();img.onload=()=>resolve();img.onerror=()=>reject(new Error('Preview image unavailable.'));img.src=preview.imageUrl!;});
   COMPLETE.set(key,preview.imageUrl);return preview.imageUrl;
  })().finally(()=>REQUESTS.delete(key));REQUESTS.set(key,pending);
 }
 return pending;
}
export default function AvatarStage({spec,className,onStatus}:{spec:CastSpec;className?:string;onStatus?:(state:AvatarPreviewState)=>void}){
 const visualKey=JSON.stringify(castRenderConfig(spec));
 const [image,setImage]=useState<{key:string;src:string;character:CastSpec['character']}|null>(null),[error,setError]=useState<string|null>(null),[retry,setRetry]=useState(0);
 const backgroundKey=JSON.stringify([spec.environment,spec.environmentFormat??'square']);
 const [loadedBackground,setLoadedBackground]=useState<string|null>(null);
 const statusRef=useRef(onStatus);statusRef.current=onStatus;const currentSpec=useRef(spec);currentSpec.current=spec;const ready=image?.key===visualKey&&(!spec.environment||loadedBackground===backgroundKey);
 useEffect(()=>{statusRef.current?.(error?'failed':ready?'ready':'loading');},[ready,error,backgroundKey]);
 useEffect(()=>{
  let cancelled=false;setError(null);statusRef.current?.('loading');
  const timer=setTimeout(()=>{const requestedSpec=normalizeCastSpec(currentSpec.current);requestPreview(requestedSpec).then(src=>{if(cancelled)return;setImage({key:visualKey,src,character:requestedSpec.character});}).catch((e:Error)=>{if(cancelled)return;setError(e.message);statusRef.current?.('failed');});},COMPLETE.has(visualKey)?0:300);
  return()=>{cancelled=true;clearTimeout(timer);};
 },[visualKey,retry]);
 return <div className={`cast-render-stage ${className??''}`} aria-busy={!ready&&!error} style={spec.environment?{aspectRatio:environmentAspect[spec.environmentFormat??'square'],height:'auto',maxHeight:'100%'}:undefined} data-preview-state={error?'failed':ready?'ready':'loading'}>
  {spec.environment&&<img key={backgroundKey+retry} className="cast-environment-plate" onLoad={()=>setLoadedBackground(backgroundKey)} onError={()=>setError('Environment image unavailable. Retry preview.')} src={environmentImage(spec.environment,spec.environmentFormat??'square')} alt=""/>}
  <img className="cast-presenter-overlay" style={spec.environment&&spec.environmentFormat==='portrait'?{objectFit:'cover'}:undefined} src={image?.character===spec.character?image.src:`/cast/default-${spec.character}-v20.webp`} alt={`${spec.character==='female'?'Female':'Male'} presenter preview`} fetchPriority={onStatus?'high':'auto'} decoding="sync"/>
  {!ready&&<div className="cast-preview-status cast-preview-status-pending" role="status">{error?<><span>{error}</span><button type="button" onClick={()=>setRetry(n=>n+1)}>Retry preview</button></>:<><span className="cast-preview-spinner"/><span>Rendering your selected look… This can take a few minutes.</span></>}</div>}
 </div>;
}
