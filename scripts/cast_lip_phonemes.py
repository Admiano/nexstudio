"""Phoneme-level lip sync on the existing mouth shape keys (pure Python + numpy).

Targets per ARPAbet phoneme blend the face's existing keys; dominance-weighted
co-articulation (Cohen-Massaro) lets rounding start early and keeps closures
sharp. The jaw scales with each vowel's loudness relative to the speaker and
with lexical stress. p/b/m always close the lips on the frame nearest the sound.
"""
import json,subprocess
import numpy as np
from pathlib import Path
ROUND=('V3_round','A_pucker','A_funnel')
def _rms(audio,hop=.01):
    raw=subprocess.run(['ffmpeg','-loglevel','error','-i',str(audio),'-f','s16le','-ac','1','-ar','16000','-'],capture_output=True,check=True).stdout
    x=np.frombuffer(raw,dtype=np.int16).astype(np.float32)/32768;n=int(16000*hop)
    frames=x[:len(x)//n*n].reshape(-1,n);return np.sqrt((frames**2).mean(1)+1e-12),hop
def build(cfg,total,fps,table):
    T=table['phonemes'];split=table.get('diphthongs',{})
    phones=json.loads(Path(cfg['phonemes']).read_text())['phones']
    seq=[]
    for s,e,p in phones:
        base=p.rstrip('012');stress=int(p[-1]) if p[-1].isdigit() else None
        if base in split:
            m=(s+e)/2;seq+=[(s,m,split[base][0],stress),(m,e,split[base][1],stress)]
        else:seq.append((s,e,base if base in T else 'sil',stress))
    keys=sorted({k for v in T.values() for k in v['target']})
    rms,hop=_rms(cfg['audio']) if cfg.get('audio') else (None,None)
    gains=[]
    vowel=lambda b:T[b].get('vowel',False)
    if rms is not None:
        lv=[float(rms[int(s/hop):max(int(s/hop)+1,int(e/hop))].mean()) for s,e,b,_ in seq]
        med=float(np.median([v for v,(s,e,b,_) in zip(lv,seq) if vowel(b)]) or 1)
    L=table['loudness'];SM=table['stressGain']
    for i,(s,e,b,st) in enumerate(seq):
        g=1.0
        if vowel(b):
            if rms is not None:g*=min(L['max'],max(L['min'],(lv[i]/med)**L['exponent']))
            g*=SM.get(str(st),1.0)
        gains.append(g)
    lead=float(cfg.get('leadSec',table.get('leadSec',.04)));start=int(cfg.get('startFrame',1));jaw_gain=float(cfg.get('mouthOpen',1))
    t=(np.arange(total+2)-start)/fps+lead
    out={}
    for k in keys:
        spread=table['spreadSec']['round' if k in ROUND else 'default']
        num=np.zeros_like(t);den=np.full_like(t,1e-6)
        for (s,e,b,st),g in zip(seq,gains):
            spec=T[b];tgt=spec['target'].get(k,0.0)
            if k in table['openKeys']:tgt*=g*(jaw_gain if k=='!ex-jawOpen' else 1)
            x=np.maximum(0,np.abs(t-(s+e)/2)-(e-s)/2)/spread
            d=spec.get('dominance',1.0)*np.exp(-x**2)
            num+=d*min(1.0,tgt);den+=d
        out[k]=np.clip(num/den,0,1)
    # hard closure on bilabials: the frame nearest each p/b/m centre seals the lips
    hits=0;bil=[(s,e) for s,e,b,_ in seq if T[b].get('closure')]
    for s,e in bil:
        f=start+round(((s+e)/2-lead)*fps)
        for g in (f-1,f,f+1):
            if 1<=g<=total:
                w=1.0 if g==f else .5
                out['V3_closed'][g]=max(out['V3_closed'][g],table['closure']['closed']*w)
                for k in table['openKeys']:out[k][g]*=1-w*.9
        hits+=out['V3_closed'][f]>=.6 if 1<=f<=total else 0
    qa={'phones':len(seq),'bilabials':len(bil),'bilabialClosed':int(hits)}
    qa['maxValue']={k:round(float(max(v)),3) for k,v in out.items()};qa['inBounds']=all(0<=float(min(v)) and float(max(v))<=1 for v in out.values())
    if rms is not None:
        env=np.interp(t-lead,np.arange(len(rms))*hop,rms);jaw=out['!ex-jawOpen'];m=(t>=0)&(t<=len(rms)*hop)
        a=(env[m]-env[m].mean())/(env[m].std()+1e-9);b=(jaw[m]-jaw[m].mean())/(jaw[m].std()+1e-9)
        lags=range(-6,7);cc=[float(np.mean(a[max(0,-l):len(a)-max(0,l)]*b[max(0,l):len(b)-max(0,-l)])) for l in lags]
        qa.update(jawLoudnessCorr=round(max(cc),3),jawLagFrames=list(lags)[int(np.argmax(cc))])
        # drift: best lag per 15 s window must stay within a frame of the overall lag
        win=int(15*fps);wl=[]
        for i in range(0,len(a)-win//2,win):
            x,y=a[i:i+win],b[i:i+win]
            c2=[float(np.mean(x[max(0,-l):len(x)-max(0,l)]*y[max(0,l):len(y)-max(0,-l)])) for l in lags]
            wl.append(list(lags)[int(np.argmax(c2))])
        qa.update(windowLagFrames=wl,driftFrames=max(wl)-min(wl) if wl else 0)
        sv=[(st,gains[i]) for i,(s,e,b,st) in enumerate(seq) if vowel(b)]
        qa['meanGainStressed']=round(float(np.mean([g for st,g in sv if st==1] or [0])),3);qa['meanGainUnstressed']=round(float(np.mean([g for st,g in sv if st==0] or [0])),3)
    return {k:[float(v) for v in row] for k,row in out.items()},qa
