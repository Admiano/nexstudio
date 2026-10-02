import {mkdirSync,writeFileSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {DEFAULT_SPEC} from '../src/studio-v2/cast/spec';
import {castRenderConfig} from '../src/studio-v2/cast/render-config';
const root=process.env.CAST_PREVIEW_CACHE_DIR??path.join(process.cwd(),'engine_sources/makehuman-lineart/out/cast-previews');
for(const spec of Object.values(DEFAULT_SPEC)){
 const config=castRenderConfig(spec),key=createHash('sha256').update(JSON.stringify(config)).digest('hex'),dir=path.join(root,key);
 if(process.argv.includes('--check')){if(!existsSync(path.join(dir,'preview.png')))throw new Error('Approved default preview missing: '+spec.character);}
 else {mkdirSync(dir,{recursive:true});writeFileSync(path.join(dir,'request.json'),JSON.stringify({key,config}));console.log(spec.character,key);}
}
