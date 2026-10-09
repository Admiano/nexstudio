import {chromium} from '../../node_modules/playwright-core/index.mjs';
import {writeFileSync,mkdirSync} from 'fs';
const [,,url,first,last,out,workers='4']=process.argv;mkdirSync(out,{recursive:true});
const frames=[];for(let f=+first;f<=+last;f++)frames.push(f);
const chrome=process.env.CHROME_BIN||process.env.CHROME_PATH||`${process.env.HOME}/.local/bin/google-chrome`;
const t0=Date.now();
await Promise.all([...Array(Math.max(1,+workers))].map(async(_,w)=>{
 const b=await chromium.launch({executablePath:chrome,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
  const p=await b.newPage({viewport:{width:1080,height:1440}});
  let failed=null;p.on('pageerror',e=>{failed=e.message;});
  await p.goto(url);await p.waitForFunction(()=>window.ready,null,{timeout:600000});
  for(let i=w;i<frames.length;i+=+workers){
   if(failed)throw new Error(failed);
   const f=frames[i],d=await p.evaluate(f=>window.renderFrame(f),f);
   writeFileSync(`${out}/${String(f).padStart(4,'0')}.png`,Buffer.from(d.split(',')[1],'base64'));
  }
 }finally{await b.close();}
}));
console.log('PRESENTER_CAPTURE',JSON.stringify({frames:frames.length,ms:Date.now()-t0,workers:+workers}));
