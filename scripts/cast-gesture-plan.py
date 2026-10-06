"""Plan a gesture timeline from word timings (and optionally the voiceover audio).

Usage: python3 cast-gesture-plan.py words.json out-timeline.json [--audio voice.wav|mp3]
       [--cues gesture-cues.json] [--rhubarb cues.json | --phonemes phones.json] [--seed N]
       [--size 1.0] [--speed 1.0] [--frequency 1.0]
words.json: [[start_sec, end_sec, "word"], ...] as written by the TTS/aligner
(or cast-phoneme-align.py output, whose "words" list is used).
Content-agnostic: gestures land on stressed words, phrase starts and list
structure; the lexicon (per language, replaceable) only suggests a category.
"""
import argparse,json,math,random,re,subprocess,array
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'engine_sources/makehuman-lineart/character_system'
ap=argparse.ArgumentParser();ap.add_argument('words');ap.add_argument('out')
ap.add_argument('--audio');ap.add_argument('--cues',default=str(ROOT/'gesture-cues.json'));ap.add_argument('--rhubarb');ap.add_argument('--phonemes',help='cast-phoneme-align.py output; preferred over --rhubarb')
ap.add_argument('--seed',type=int,default=1);ap.add_argument('--posture',default='standing',help='standing or seated: which clips the planner may pick');ap.add_argument('--name',default='autoGestures')
ap.add_argument('--mood',default='any',choices=('any','calm','expressive'),help='motion group from cast-motion-groups.py')
ap.add_argument('--presenter',choices=('female','male'),help="excludes the other presenter's signature clips and favours this one's")
for k in ('size','speed','frequency','expressiveness'):ap.add_argument('--'+k,type=float,default=1.0)
a=ap.parse_args()
LIB=json.loads((ROOT/'gesture-clips.json').read_text());CUES=json.loads(Path(a.cues).read_text());R=CUES['rules']
# a mood also scales how often, how large and how fast the presenter gestures
for k,v in LIB.get('groupRules',{}).get('moodStyle',{}).get(a.mood,{}).items():setattr(a,k,getattr(a,k)*v)
fps=LIB['source']['fps'];rng=random.Random(a.seed)
words=json.loads(Path(a.words).read_text());words=words['words'] if isinstance(words,dict) else words
words=[(float(s),float(e),w) for s,e,w in words if w]
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
MEAN=json.loads((ROOT/'gesture-meanings.json').read_text())
# sentences carry the intent (welcome, doubt, reassurance...); pauses only split phrases
sentences=[[0]]
for i in range(1,len(words)):
    if re.search(r'[.!?]$',words[i-1][2]) or words[i][0]-words[i-1][1]>=R.get('sentencePauseSec',0.7):sentences.append([])
    sentences[-1].append(i)
def intent_of(sen):
    text='';pos=[]
    for i in sen:pos.append(len(text));text+=words[i][2].lower()+' '
    for name,pat in MEAN['intents']:
        m=re.search(pat,text)
        if m:return name,max(k for k,p in zip(sen,pos) if p<=m.start())
    best=max(sen,key=lambda i:stress[i] if len(norm(words[i][2]))>=3 else 0)
    return (MEAN['questionIntent'] if words[sen[-1]][2].strip().endswith('?') else MEAN['defaultIntent']),best
intents=[(sen,)+intent_of(sen) for sen in sentences]
# a sentence's gesture should end before the next specific intent's cue, so each one gets its turn
cue_frames=sorted(round(words[c][0]*fps)+1 for _,m,c in intents if m!=MEAN['defaultIntent'])
limit=lambda i:next((f for f in cue_frames if f>round(words[i][0]*fps)+1),10**9)
events=[]
intent_events={(c,m) for _,m,c in intents}
# specific meanings place before plain explaining
for sen,intent,cue in intents:events.append((cue,intent,5+stress[cue]+(0 if intent==MEAN['defaultIntent'] else 2.5)))
# word-level structure: sizes, and pointing on stressed deictic words in plain explaining
plain={i for sen,intent,_ in intents if intent in ('explain','point') for i in sen}
for i,(s0,e0,w) in enumerate(words):
    cat=lex.get(norm(w))
    if cat=='scale':events.append((i,'scale',3+stress[i]))
    if cat=='point' and i in plain and stress[i]>=1:events.append((i,'point',3+stress[i]))
# longer phrases inside a sentence get a light explaining beat on their stressed word
for ph in phrases:
    best=max(ph,key=lambda i:stress[i] if len(norm(words[i][2]))>=3 else 0)
    if len(ph)>=3 and stress[best]>=R['stressBeat']/max(.25,a.frequency):events.append((best,'explain',stress[best]))
# lists: count only where enough enumeration words cluster in a steady rhythm
counts=sorted((i for i,(s0,e0,w) in enumerate(words) if lex.get(norm(w))=='count'),key=lambda i:words[i][0]);keep=[];run=[]
for i in counts+[None]:
    if i is not None and run and words[i][0]-words[run[-1]][0]<=R['countMaxSpacingSec']:run.append(i);continue
    if len(run)>=R['countMinHits']:keep.append(run)
    run=[i] if i is not None else []
events+=[(r[0],'list',20+stress[r[0]]) for r in keep]
list_runs={r[0]:r for r in keep}

def meanings(name,c):
    text=name+' '+c.get('source','').lower()
    if re.search(MEAN['exclude'],text):return set()
    out=set()
    for pat,ms in MEAN['clipRules']:
        if re.search(pat,name) or re.search(pat,c.get('source','').lower()):out|=set(ms)
    if not out and c['category'] in ('open','beat'):out={'explain'}
    return out
clips={}
# very large Mixamo moves (arms overhead, wide T) stay addressable by name but are not auto-picked
MXC=LIB.get('mixamo',{});reach_cap=MXC.get('maxAutoReachCm',1e9);min_frames=MXC.get('minAutoFrames',0)
GR=LIB.get('groupRules',{});calm_reach=GR.get('presenterCalmMaxReachCm',50)
for name,c in LIB['clips'].items():
    if c.get('reachCm',0)>reach_cap or c['frames'][1]-c['frames'][0]+1<min_frames:continue
    if c.get('posture','standing')!=a.posture:continue
    if a.presenter and c.get('presenter','any') not in ('any',a.presenter):continue
    for m in meanings(name,c):clips.setdefault(m,[]).append(name)
# calm keeps calm clips (or small expressive ones); big celebrations fall back to calmer meanings
for m,names in list(clips.items()):
    if a.mood=='calm':
        keep=[n for n in names if LIB['clips'][n].get('mood')=='calm'] or ([] if re.search(MEAN['calmOnly'],m) else [n for n in names if LIB['clips'][n].get('reachCm',0)<=calm_reach])
    elif a.mood=='expressive':keep=[n for n in names if LIB['clips'][n].get('mood')=='expressive'] or names
    else:keep=names
    if keep:clips[m]=keep
    else:del clips[m]
# presenter signature clips count as half-used so they are picked first
bias=lambda n:-.5 if a.presenter and LIB['clips'][n].get('presenter')==a.presenter else 0
fallback=MEAN['fallback']
# per-clip tempo (Mixamo clips slowed to the presenter hand-speed cap) times the style speed
spd=lambda n:a.speed*LIB['clips'][n].get('tempo',1)
pad=lambda n:int(MXC.get('padFrames',0)) if 'mixamo' in LIB['clips'][n] else 0
length=lambda n:round((LIB['clips'][n]['frames'][1]-LIB['clips'][n]['frames'][0]+1)/spd(n))+2*pad(n)
gap=round(R['minGapSec']/max(.25,a.frequency)*fps)
chosen=[];busy=[];used={};DROPS=[]
def chain(cat):
    out=[]
    while cat and cat not in out:out.append(cat);cat=fallback.get(cat)
    return [c for c in out if c in clips]
for i,cat,prio in sorted(events,key=lambda e:-e[2]):
    # try this meaning's clips (least used, then shortest), then its fallbacks, until one fits the free time
    placed=False
    for m in chain(cat):
        for name in sorted(clips[m],key=lambda n:(used.get(n,0)+bias(n),length(n),rng.random())):
            if used.get(name,0)>=R.get('maxRepeats',2):continue
            clip=LIB['clips'][name]
            if m=='list' and i in list_runs:
                hits=[words[k][0] for k in list_runs[i]];at=(hits[0]+hits[-1])/2;anchor=(clip['onset']+clip['release'])/2
            else:at=words[i][0];anchor=clip.get('apex',clip['stroke'])
            start=max(1,round((at-R['strokeLeadSec'])*fps)+1-round(anchor/spd(name))-pad(name));end=start+length(name)-1
            if any(start<=b+gap and end+gap>=s for s,b in busy):continue
            if (i,cat) in intent_events and end+gap>limit(i):continue
            busy.append((start,end));chosen.append((start,end,name,words[i][2],m));used[name]=used.get(name,0)+1;placed=True;break
        if placed:break
    if not placed:DROPS.append((words[i][2],cat))
chosen.sort()
total=max(round(words[-1][1]*fps)+fps//2,(chosen[-1][1]+12) if chosen else 0)
seq=[];cursor=1
for start,end,name,word,cat in chosen:
    seq.append({'idle':max(4,start-cursor)});seq.append({'clip':name,'cue':word,'category':cat});cursor=start+length(name)
seq.append({'idle':max(12,total-cursor+1)})
# expressions: every sentence's intent, at its cue word, plus a soft smile at sentence ends
EX=MEAN.get('expressions',{});expr=[]
def add(cat,t):
    for key,amt,sec in EX.get(cat,[]):expr.append({'at':round(t*fps)+1,'shape':key,'amount':round(amt*a.expressiveness,3),'frames':round(sec*fps)})
for sen,intent,cue in intents:add(intent,words[cue][0])
for sen,intent,cue in intents:
    if intent in ('explain','agree','welcome','thanks','reassure','excited') and re.search(r'[.!]$',words[sen[-1]][2]):add('sentenceEnd',words[sen[-1]][1])
out={'name':a.name,'expressions':expr,'sequence':seq,'style':{'size':a.size,'speed':a.speed,'mood':a.mood,'presenter':a.presenter},'idleLayer':{'seed':a.seed}}
if MXC.get('idleBase',{}).get(a.posture):out['idleBase']=MXC['idleBase'][a.posture]
if a.phonemes:out['lipSync']={'phonemes':a.phonemes,'audio':a.audio,'mouthOpen':1.0}
elif a.rhubarb:out['lipSync']={'rhubarb':a.rhubarb,'mouthOpen':1.2}
Path(a.out).write_text(json.dumps(out,indent=1)+'\n')
print('GESTURE_PLAN',json.dumps({'words':len(words),'phrases':len(phrases),'events':len(events),'intents':[(words[c][2],m) for _,m,c in intents],'gestures':[(round((s-1)/fps,2),n,w,c) for s,_,n,w,c in chosen]}))
