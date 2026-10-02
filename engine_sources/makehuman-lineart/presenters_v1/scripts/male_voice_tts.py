import json,subprocess,numpy as np,soundfile as sf
from kokoro import KPipeline
V='am_michael'
w=json.load(open(__import__('os').environ.get('WORDS','words56.json')))
ref,sr=sf.read(__import__('os').environ.get('REFWAV','host56.wav'))
ph=[[w[0]]]
for x in w[1:]:
    (ph[-1].append(x) if x[0]-ph[-1][-1][1]<0.25 else ph.append([x]))
p=KPipeline(lang_code='a')
out=np.zeros(len(ref)); log=[]
for i,g in enumerate(ph):
    t=' '.join(x[2] for x in g)
    a=np.concatenate([np.asarray(r.audio) for r in p(t,voice=V,speed=1.0)])
    nz=np.nonzero(np.abs(a)>0.01)[0]; a=a[nz[0]:nz[-1]+1]
    sf.write('p.wav',a,24000)
    d=g[-1][1]-g[0][0]; r=(len(a)/24000)/d
    f=','.join(['atempo=%.4f'%r] if 0.5<=r<=2 else ['atempo=%.4f'%np.sqrt(r)]*2)
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i','p.wav','-filter:a',f,'-ar',str(sr),'q.wav'],check=True)
    b,_=sf.read('q.wav'); n0=int(g[0][0]*sr); b=b[:len(out)-n0]; out[n0:n0+len(b)]+=b
    log.append((round(g[0][0],2),round(d,2),round(r,3),t))
out*=0.9*np.abs(ref).max()/np.abs(out).max() if np.abs(ref).max()<=1 else 1
sf.write('male56_%s.wav'%V,out,sr)
for l in log: print(l)
