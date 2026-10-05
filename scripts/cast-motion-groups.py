"""Tag every gesture clip with a mood (calm/expressive) and presenter affinity.

Usage: python3 cast-motion-groups.py [--check]
Mood comes from measured motion (peak hand speed, reach) and the clip category;
presenter affinity from the performance named in the clip's source. Rules live
in gesture-clips.json under "groupRules" so they can be edited without code.
"""
import json,re,sys,collections
from pathlib import Path
P=Path(__file__).resolve().parents[1]/'engine_sources/makehuman-lineart/character_system/gesture-clips.json'
LIB=json.loads(P.read_text());R=LIB['groupRules']
hit=lambda text,words:any(re.search(r'\b'+re.escape(w),text) for w in words)
def mood(name,c,text):
    if hit(text,R['expressiveWords']):return 'expressive'
    if c['category'] in R['calmCategories'] or hit(text,R['calmWords']):return 'calm'
    if c['category'] in R['expressiveCategories']:return 'expressive'
    if c.get('peakSpeed') is None:return 'calm'
    return 'calm' if c['peakSpeed']<=R['calmMaxPeakSpeed'] and c.get('reachCm',0)<=R['calmMaxReachCm'] else 'expressive'
def presenter(text):
    f,m=hit(text,R['femaleWords']),hit(text,R['maleWords'])
    return 'female' if f and not m else 'male' if m and not f else 'any'
groups=collections.defaultdict(lambda:collections.defaultdict(list))
for name,c in LIB['clips'].items():
    text=(name+' '+str(c.get('source',''))).lower().replace('_',' ')
    c['mood'],c['presenter']=mood(name,c,text),presenter(text)
    posture=c.get('posture','standing')
    groups[f"{posture}.{c['mood']}"][c['category']].append(name)
    if c['presenter']!='any':groups[f"{posture}.{c['presenter']}"][c['category']].append(name)
LIB['groups']={k:dict(sorted(v.items())) for k,v in sorted(groups.items())}
text=json.dumps(LIB,indent=2)+'\n'
if '--check' in sys.argv:sys.exit(0 if P.read_text()==text else 'CAST_MOTION_GROUPS_STALE')
P.write_text(text)
print('MOTION_GROUPS',json.dumps({k:sum(map(len,v.values())) for k,v in LIB['groups'].items()}))
