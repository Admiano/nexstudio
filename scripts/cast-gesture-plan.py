"""Plan a gesture timeline from word timings (and optionally the voiceover audio).

Usage: python3 cast-gesture-plan.py words.json out-timeline.json [--audio voice.wav|mp3]
       [--cues gesture-cues.json] [--rhubarb cues.json] [--seed N]
       [--size 1.0] [--speed 1.0] [--frequency 1.0]
words.json: [[start_sec, end_sec, "word"], ...] as written by the TTS/aligner.
Content-agnostic: gestures land on stressed words, phrase starts and list
structure; the lexicon (per language, replaceable) only suggests a category.
"""
import argparse,json,math,random,re,subprocess,array
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'engine_sources/makehuman-lineart/character_system'
ap=argparse.ArgumentParser();ap.add_argument('words');ap.add_argument('out')
ap.add_argument('--audio');ap.add_argument('--cues',default=str(ROOT/'gesture-cues.json'));ap.add_argument('--rhubarb')
ap.add_argument('--seed',type=int,default=1);ap.add_argument('--name',default='autoGestures')
for k in ('size','speed','frequency','expressiveness'):ap.add_argument('--'+k,type=float,default=1.0)
a=ap.parse_args()
LIB=json.loads((ROOT/'gesture-clips.json').read_text());CUES=json.loads(Path(a.cues).read_text());R=CUES['rules']
fps=LIB['source']['fps'];rng=random.Random(a.seed)
words=[(float(s),float(e),w) for s,e,w in json.loads(Path(a.words).read_text())]
norm=lambda w:re.sub(r"[^\w']+",'',w.lower())
lex={norm(w):cat for cat,ws in CUES['lexicon'].items() for w in ws}

def energies():
    if not a.audio:return None
    raw=subprocess.run(['ffmpeg','-loglevel','error','-i',a.audio,'-f','s16le','-ac','1','-ar','16000','-'],capture_output=True,check=True).stdout
    x=array.array('h',raw);out=[]
    for s,e,_ in words:
        seg=x[int(s*16000):max(int(s*16000)+1,int(e*16000))]
        out.append(math.sqrt(sum(v*v for v in seg)/len(seg)) if seg else 0.0)
    return out
E=energies()
# stress: loudness and duration relative to the speaker's own average, per letter
# short function words are never stress peaks, whatever their duration
dur=[(e-s)/max(3,len(norm(w))) for s,e,w in words];md=sum(dur)/len(dur)
me=(sum(E)/len(E)) if E else 1
stress=[(d/md)*(E[i]/me if E else 1) for i,d in enumerate(dur)]
med=sorted(stress)[len(stress)//2]
stress=[s/med for s in stress]

# phrases split on pauses and sentence ends
phrases=[[0]]
for i in range(1,len(words)):
    if words[i][0]-words[i-1][1]>=R['pauseSec'] or re.search(r'[.!?]$',words[i-1][2]):phrases.append([])
    phrases[-1].append(i)
events=[]
for ph in phrases:
    question=words[ph[-1]][2].strip().endswith('?')
    best=max(ph,key=lambda i:stress[i] if len(norm(words[i][2]))>=3 else 0)
    for i in ph:
        cat=lex.get(norm(words[i][2]));cat=CUES.get('categoryFor',{}).get(cat,cat)
        if cat=='greeting' and i!=ph[0]:cat=None
        if cat=='point' and R['pointNeedsStress'] and stress[i]<1:cat=None
        if cat:events.append((i,cat,2+stress[i]))
    if question:events.append((best,'question',1.5+stress[best]))
    if stress[best]>=R['stressEmphasis']/max(.25,a.frequency):events.append((best,'emphasis',1+stress[best]))
    elif stress[best]>=R['stressBeat']/max(.25,a.frequency):
        events.append((best,'open' if len(ph)>=R['longPhraseWords'] else 'beat',stress[best]))
# lists: count only where enough enumeration words cluster
counts=sorted((e for e in events if e[1]=='count'),key=lambda e:words[e[0]][0]);keep=[];run=[]
# a list is a run of enumeration words in a steady rhythm, not any lone "next" or "one"
for e in counts+[None]:
    if e and run and words[e[0]][0]-words[run[-1][0]][0]<=R['countMaxSpacingSec']:run.append(e);continue
    if len(run)>=R['countMinHits']:keep.append(run[0])
    run=[e] if e else []
events_all=list(events)
# list structure outranks single-word stress
events=[e for e in events if e[1]!='count']+[(i,c,10+p) for i,c,p in keep]

clips={}
# very large Mixamo moves (arms overhead, wide T) stay addressable by name but are not auto-picked
reach_cap=LIB.get('mixamo',{}).get('maxAutoReachCm',1e9)
for name,c in LIB['clips'].items():
    if c.get('reachCm',0)<=reach_cap:clips.setdefault(c['category'],[]).append(name)
fallback={'question':'open','emphasis':'open','scale':'open','greeting':'open','point':'beat','count':'open','open':'beat','negation':'beat','think':'question'}
# per-clip tempo (Mixamo clips slowed to the presenter hand-speed cap) times the style speed
spd=lambda n:a.speed*LIB['clips'][n].get('tempo',1)
length=lambda n:round((LIB['clips'][n]['frames'][1]-LIB['clips'][n]['frames'][0]+1)/spd(n))
stroke=lambda n:round(LIB['clips'][n]['stroke']/spd(n))
gap=round(R['minGapSec']/max(.25,a.frequency)*fps)
chosen=[];busy=[];used={}
for i,cat,prio in sorted(events,key=lambda e:-e[2]):
    while cat and cat not in clips:cat=fallback.get(cat)
    if not cat:continue
    # spread usage: least-used clip first, spill into the fallback category once a category is worn
    if min(used.get(n,0) for n in clips[cat])>=R.get('maxRepeats',2) and fallback.get(cat) in clips:cat=fallback[cat]
    low=min(used.get(n,0) for n in clips[cat]);name=rng.choice([n for n in clips[cat] if used.get(n,0)==low])
    clip=LIB['clips'][name]
    if cat=='count':
        hits=[words[i][0]]
        for k,c,_ in sorted((e for e in events_all if e[1]=='count'),key=lambda e:words[e[0]][0]):
            if 0<words[k][0]-hits[-1]<=R['countMaxSpacingSec']:hits.append(words[k][0])
        at=(hits[0]+hits[-1])/2;anchor=(clip['onset']+clip['release'])/2
    else:at=words[i][0];anchor=clip.get('apex',clip['stroke'])
    start=round((at-R['strokeLeadSec'])*fps)+1-round(anchor/spd(name))
    start=max(1,start);end=start+length(name)-1
    if any(start<=b+gap and end+gap>=s for s,b in busy):continue
    busy.append((start,end));chosen.append((start,end,name,words[i][2],cat));used[name]=used.get(name,0)+1
chosen.sort()
total=max(round(words[-1][1]*fps)+fps//2,(chosen[-1][1]+12) if chosen else 0)
seq=[];cursor=1
for start,end,name,word,cat in chosen:
    seq.append({'idle':max(4,start-cursor)});seq.append({'clip':name,'cue':word,'category':cat});cursor=start+length(name)
seq.append({'idle':max(12,total-cursor+1)})
# expressions: from the placed gestures plus every sentence end
EX=CUES.get('expressions',{});expr=[]
def add(cat,t):
    for key,amt,sec in EX.get(cat,[]):expr.append({'at':round(t*fps)+1,'shape':key,'amount':round(amt*a.expressiveness,3),'frames':round(sec*fps)})
for start,end,name,word,cat in chosen:add(cat,(start-1+LIB['clips'][name].get('apex',LIB['clips'][name]['stroke'])/spd(name))/fps)
for ph in phrases:
    if re.search(r'[.!]$',words[ph[-1]][2]):add('sentenceEnd',words[ph[-1]][1])
out={'name':a.name,'expressions':expr,'sequence':seq,'style':{'size':a.size,'speed':a.speed},'idleLayer':{'seed':a.seed}}
if a.rhubarb:out['lipSync']={'rhubarb':a.rhubarb,'mouthOpen':1.2}
Path(a.out).write_text(json.dumps(out,indent=1)+'\n')
print('GESTURE_PLAN',json.dumps({'words':len(words),'phrases':len(phrases),'events':len(events),'gestures':[(round((s-1)/fps,2),n,w) for s,_,n,w,_ in chosen]}))
