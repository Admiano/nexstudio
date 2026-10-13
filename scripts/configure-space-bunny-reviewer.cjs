// Operator-selected department reviewer. Synthetic probe precedes local activation.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..');
const profile=JSON.parse(fs.readFileSync(path.join(root,'config/nexmind/space-bunny-department-reviewer.json'),'utf8'));
const envPath=path.join(root,'.env');
function updates(){const p=profile.environmentPrefix;return {
 [p+'_PROVIDER']:profile.provider,[p+'_MODEL']:profile.model,[p+'_BASE_URL']:profile.baseUrl,
 [p+'_API_KEY_ENV']:profile.apiKeyEnv,[p+'_API_MODE']:profile.apiMode,[p+'_REASONING']:profile.reasoning,
 [p+'_INPUT_MODALITIES']:profile.inputModalities.join(','),[p+'_AUDIO_INPUT_MODE']:'',
 [p+'_MULTIMODAL_REVIEW_MODE']:'combined',[p+'_AUDIO_SAMPLE_RATE']:'0',
 NEXMIND_RUNTIME_BOOT_ATTESTATION_JSON:'',
};}
function patchEnv(contents,values){const newline=contents.includes('\r\n')?'\r\n':'\n';
 for(const [name,value] of Object.entries(values)){
  const pattern=new RegExp('^'+name+'=[^\\r\\n]*','gm');
  if(pattern.test(contents))contents=contents.replace(pattern,()=>name+'='+value);
  else contents+=(contents.endsWith('\n')?'':newline)+name+'='+value+newline;
 }return contents;
}
async function main(){
 const apply=process.argv.includes('--apply');
 if(process.argv.slice(2).some(x=>!['--apply','--check'].includes(x)))throw Error('Use --check or --apply');
 const original=fs.readFileSync(envPath,'utf8'),env={...process.env,...require('dotenv').parse(original)};
 const out=path.join(root,'reports/openrouter-space-bunny-reviewer');fs.mkdirSync(out,{recursive:true});
 const result={checkedAt:new Date().toISOString(),model:profile.model,provider:profile.provider,
  tasks:profile.tasks,excludedTasks:profile.excludedTasks,credentialPresent:!!env[profile.apiKeyEnv],
  applied:false,status:'PREPARED',plannedEnvironment:updates()};
 function save(){fs.writeFileSync(path.join(out,'activation.json'),JSON.stringify(result,null,2)+'\n');}
 if(!apply){save();console.log(JSON.stringify(result,null,2));return;}
 if(!env[profile.apiKeyEnv]){result.status='BLOCKED_MISSING_CREDENTIAL';save();throw Error('Add '+profile.apiKeyEnv+' to local .env');}
 // Public catalog visibility is recorded, not treated as a replacement for inference.
 const headers={'Authorization':'Bearer '+env[profile.apiKeyEnv],'Content-Type':'application/json'};
 try{
  const catalog=await fetch(profile.baseUrl+'/models',{headers,signal:AbortSignal.timeout(30000)});
  const body=await catalog.json();result.catalog={httpStatus:catalog.status,
   exactModelListed:(body.data||[]).some(x=>x.id===profile.model)};
 }catch(error){result.catalog={error:error.message};}
 const imagePath=path.join(root,'scripts/fixtures/space-bunny-probe.png');
 const content=[{type:'text',text:'Synthetic reviewer conformance test. The only available renderer primitive is TYPE_REVEAL. A proposed plan requires an unbound waterline rule and TRACE_FLOW. Review execution readiness, and inspect the attached image. Return exactly a JSON object with verdict (REVISE or ACCEPT), unsupported (array of strings), and topColor (green or magenta). Do not approve unsupported requirements.'},
  {type:'image_url',image_url:{url:'data:image/png;base64,'+fs.readFileSync(imagePath).toString('base64')}}];
 let response,data;
 try{
  response=await fetch(profile.baseUrl+'/chat/completions',{method:'POST',headers,
   body:JSON.stringify({model:profile.model,messages:[{role:'user',content}],
    ...(String(env.NEXMIND_PROMPT_JSON_SEND_REASONING).toLowerCase()==='true'?{reasoning_effort:profile.reasoning}:{}),
    max_tokens:8192}),signal:AbortSignal.timeout(120000)});
  data=await response.json();
 }catch(error){result.status='BLOCKED_PROBE_TRANSPORT';result.detail=error.message;save();throw Error(result.detail);}
 result.probe={httpStatus:response.status,requestId:data.id||'',resolvedModel:data.model||'',
  errorCode:data.error?.code,errorMessage:data.error?.message,usage:data.usage};
 if(!response.ok){result.status='BLOCKED_MODEL_PROBE';save();throw Error('OpenRouter '+response.status+': '+(data.error?.message||'inference failed'));}
 let answer;try{answer=JSON.parse(data.choices?.[0]?.message?.content||'');}catch{
  result.status='BLOCKED_JSON_CONFORMANCE';save();throw Error('Synthetic reviewer did not return plain valid JSON');
 }
 result.probe.answer=answer;
 const resolved=String(data.model||'');
 if(resolved!==profile.model || answer.verdict!=='REVISE' || answer.topColor!=='green' ||
    !Array.isArray(answer.unsupported) || !answer.unsupported.some(x=>String(x).includes('TRACE_FLOW')) ||
    !answer.unsupported.some(x=>/waterline/i.test(String(x)))){
  result.status='BLOCKED_REVIEWER_CONFORMANCE';save();throw Error('Exact model identity, image perception or unsupported-plan rejection failed');
 }
 // Refuse to overwrite any concurrent user edit, including a credential update.
 if(fs.readFileSync(envPath,'utf8')!==original)throw Error('Local .env changed during probe; retry against the current file');
 const next=patchEnv(original,updates());
 fs.writeFileSync(envPath,next);
 result.applied=true;result.status='APPLIED_BOOT_REFRESH_REQUIRED';
 result.configSha256=crypto.createHash('sha256').update(JSON.stringify(updates())).digest('hex');
 save();console.log(JSON.stringify(result,null,2));
}
module.exports={updates,patchEnv,profile};
if(require.main===module)main().catch(error=>{console.error(error.message);process.exitCode=1;});
