// All operator-selected Inkling review roles. Activate only after native P8 conformance.
const fs=require('node:fs'),path=require('node:path');
const {spawnSync}=require('node:child_process');
const {patchEnv}=require('./configure-space-bunny-reviewer.cjs');
const root=path.resolve(__dirname,'..');
const profile=JSON.parse(fs.readFileSync(path.join(root,'config/nexmind/mimo-reviewers.json'),'utf8'));
function updates(){
 const settings={NEXMIND_RUNTIME_BOOT_ATTESTATION_JSON:''};
 for(const prefix of [profile.departmentPrefix,...profile.finalPrefixes]){
  const final=profile.finalPrefixes.includes(prefix);
  Object.assign(settings,{
   [prefix+'_PROVIDER']:profile.provider,[prefix+'_MODEL']:profile.model,
   [prefix+'_BASE_URL']:profile.baseUrl,[prefix+'_API_KEY_ENV']:profile.apiKeyEnv,
   [prefix+'_API_MODE']:profile.apiMode,[prefix+'_REASONING']:profile.reasoning,
   [prefix+'_INPUT_MODALITIES']:final?'images,audio':'images',
   [prefix+'_AUDIO_INPUT_MODE']:final?profile.audioInputMode:'',
   [prefix+'_MULTIMODAL_REVIEW_MODE']:final?profile.multimodalReviewMode:'combined',
   [prefix+'_AUDIO_SAMPLE_RATE']:String(final?profile.audioSampleRate:0)
  });
 }return settings;
}
async function main(){
 const apply=process.argv.includes('--apply');
 if(process.argv.slice(2).some(x=>!['--apply','--check'].includes(x)))throw Error('Use --check or --apply');
 const envPath=path.join(root,'.env'),original=fs.readFileSync(envPath,'utf8');
 const env={...process.env,...require('dotenv').parse(original)};
 const out=path.join(root,'reports/vercel-mimo-reviewers');fs.mkdirSync(out,{recursive:true});
 const result={checkedAt:new Date().toISOString(),provider:profile.provider,model:profile.model,
  tasks:[...profile.departmentTasks,...profile.finalTasks],credentialPresent:!!env[profile.apiKeyEnv],
  applied:false,status:'PREPARED',plannedEnvironment:updates()};
 const save=()=>fs.writeFileSync(path.join(out,'activation.json'),JSON.stringify(result,null,2)+'\n');
 if(!apply){save();console.log(JSON.stringify(result,null,2));return;}
 if(!env[profile.apiKeyEnv]){result.status='BLOCKED_MISSING_CREDENTIAL';save();throw Error('Missing '+profile.apiKeyEnv);}
 const headers={Authorization:'Bearer '+env[profile.apiKeyEnv]};
 const catalog=await fetch(profile.baseUrl+'/models',{headers,signal:AbortSignal.timeout(30000)});
 const data=await catalog.json();
 result.catalog={httpStatus:catalog.status,exactModelListed:(data.data||[]).some(x=>x.id===profile.model)};
 if(!catalog.ok||!result.catalog.exactModelListed){result.status='BLOCKED_MODEL_CATALOG';save();throw Error('Exact MiMo model unavailable in Gateway catalog');}
 const probeEnv={...env,...updates(),PYTHONUTF8:'1'};
 // Existing local test dependency directory; preserve configured Python search paths.
 const deps=path.join(root,'reports/editorial-motion-enclave-test/python-deps');
 if(fs.existsSync(deps))probeEnv.PYTHONPATH=[deps,probeEnv.PYTHONPATH].filter(Boolean).join(path.delimiter);
 console.log('Probing MiMo with synthetic department, native image/audio and final-review contracts.');
 const probe=spawnSync(env.STUDIO_NEXMIND_P8_PYTHON_BIN||'python',
  ['scripts/probe-mimo-reviewers.py',path.join(out,'conformance.json')],
  {cwd:root,env:probeEnv,encoding:'utf8',timeout:900000,maxBuffer:2*1024*1024});
 if(probe.stdout)process.stdout.write(probe.stdout);
 if(probe.stderr)process.stderr.write(probe.stderr);
 if(probe.error||probe.status!==0){result.status='BLOCKED_CONFORMANCE';save();throw Error(probe.error?.message||'MiMo conformance failed; local routes were not changed');}
 result.conformanceReport='reports/vercel-mimo-reviewers/conformance.json';
 if(fs.readFileSync(envPath,'utf8')!==original)throw Error('Local .env changed during probe; retry against current configuration');
 fs.writeFileSync(envPath,patchEnv(original,updates()));
 result.applied=true;result.status='APPLIED_BOOT_REFRESH_REQUIRED';save();
 console.log(JSON.stringify(result,null,2));
}
module.exports={profile,updates};
if(require.main===module)main().catch(error=>{console.error(error.message);process.exitCode=1;});
