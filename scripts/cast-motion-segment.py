"""Merge extracted mocap takes into the Mixamo library as gesture-sized parts.

Usage: python3 cast-motion-segment.py sources.json library.json.gz extract.json.gz:FPS [...]
extract files come from cast-mixamo-extract.py run on any Mixamo-skeleton export
(e.g. Rokoko free packs). Each take is resampled to the library fps, keeps its own
source rest pose, and is cut at low arm-motion frames into parts of
segment.minFrames..maxFrames; at most segment.maxParts per take are kept
(every sit/stand transition, then the parts with the most arm motion). A part's posture is read from its hip height:
mostly below -seatedDrop m is "sitting", mostly above is "standing", otherwise a
sit/stand transition, so the planner's posture and category rules apply unchanged.
Re-running replaces the parts previously merged from the same sources.
"""
import gzip,json,math,re,sys
from pathlib import Path

def slerp(a,b,t):
    d=sum(x*y for x,y in zip(a,b))
    if d<0:b=[-x for x in b];d=-d
    if d>.9995:r=[x+(y-x)*t for x,y in zip(a,b)]
    else:
        th=math.acos(d);s=math.sin(th);r=[(math.sin((1-t)*th)*x+math.sin(t*th)*y)/s for x,y in zip(a,b)]
    n=math.sqrt(sum(x*x for x in r));return [round(x/n,4) for x in r]

def resample(clip,src,dst):
    n=clip['frames']
    if src==dst:return clip
    m=int((n-1)*dst/src)+1;q={};hp=[]
    for k,v in clip['q'].items():
        out=[]
        for i in range(m):
            t=i*src/dst;a=min(int(t),n-1);b=min(a+1,n-1);out+=slerp(v[4*a:4*a+4],v[4*b:4*b+4],t-a)
        q[k]=out
    h=clip['hips']
    for i in range(m):
        t=i*src/dst;a=min(int(t),n-1);b=min(a+1,n-1)
        hp+=[round(h[3*a+j]+(h[3*b+j]-h[3*a+j])*(t-a),4) for j in range(3)]
    return dict(clip,frames=m,q=q,hips=hp)

ARMS=[f'{s}{b}' for s in('Left','Right') for b in('Arm','ForeArm','Hand')]
def energy(clip):
    n=clip['frames'];e=[0.0]*n
    for k in ARMS:
        v=clip['q'].get(k)
        if not v:continue
        for f in range(1,n):
            d=abs(sum(x*y for x,y in zip(v[4*f-4:4*f],v[4*f:4*f+4])));e[f]+=2*math.acos(min(1,d))
    r=3;return [sum(e[max(0,f-r):f+r+1])/(min(n,f+r+1)-max(0,f-r)) for f in range(n)]

def cuts(e,lo,hi):
    n=len(e);out=[0];s=0
    while n-s>hi:
        a,b=s+lo,min(s+hi,n-lo);c=min(range(a,b+1),key=lambda f:e[f]);out.append(c);s=c
    out.append(n);return out

def posture(h,a,b,drop):
    z=[h[3*f+2] for f in range(a,b)];sat=sum(x<-drop for x in z)/len(z)
    if sat>.8:return 'sitting'
    if sat<.2:return 'standing'
    return 'transition: sitting to standing' if z[0]<-drop and z[-1]>=-drop else 'transition: standing to sitting'

def main():
    srcp,libp,*extracts=sys.argv[1:];cfg=json.loads(Path(srcp).read_text());seg=cfg['segment']
    with gzip.open(libp,'rt') as fh:lib=json.load(fh)
    tag=Path(srcp).stem.split('-')[0];prefix=re.sub(r'\W','',tag)[:2]+'_'
    lib['clips']={k:v for k,v in lib['clips'].items() if not k.startswith(prefix)}
    added=0
    for spec in extracts:
        path,fps=spec.rsplit(':',1)
        with gzip.open(path,'rt') as fh:ex=json.load(fh)
        for key,clip in ex['clips'].items():
            if key not in cfg['clips']:continue
            name,desc=cfg['clips'][key];clip=resample(clip,int(fps),lib['fps'])
            e=energy(clip);cs=cuts(e,seg['minFrames'],seg['maxFrames'])
            parts=[(i,a,b,posture(clip['hips'],a,b,seg['seatedDrop'])) for i,(a,b) in enumerate(zip(cs,cs[1:]),1)]
            rank=sorted(parts,key=lambda x:(not x[3].startswith('transition'),-sum(e[x[1]:x[2]])/(x[2]-x[1])))
            keep={x[0] for x in rank[:seg.get('maxParts',len(parts))]}
            for i,a,b,p in parts:
                if i not in keep:continue
                k=prefix+re.sub(r'[^a-z0-9]+','_',name.lower()).strip('_')+f'_{i:02d}'
                lib['clips'][k]={'name':f'{name} part {i}','description':f'{desc}, {p}','mixamoId':f'{tag}:{key}:{a}-{b}',
                    'frames':b-a,'q':{bn:v[4*a:4*b] for bn,v in clip['q'].items()},'hips':clip['hips'][3*a:3*b],'rest':ex['rest']}
                added+=1
    with gzip.open(libp,'wt') as fh:json.dump(lib,fh,separators=(',',':'))
    print('MERGED',added,'parts; library',len(lib['clips']))

if __name__=='__main__':main()
