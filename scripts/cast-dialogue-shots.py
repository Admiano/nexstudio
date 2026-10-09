"""Compose multi-speaker seated/podcast timelines from per-speaker plans.

Each speaker runs `cast-gesture-plan.py` on their own words/audio first. This
script places those plans on a shared clock — speakers listed in `dialogue.json`
with a `start` (seconds). For every speaker it emits a timeline.json where:

- rhubarb mouthCue times and expression `at` frames shift by the speaker's start
- listening windows fill with idle plus one `listen` clip near the middle —
  listen clips must be quiet seated idles (still/breathing); the silent partner
  never plays gesture clips while the other speaker is talking
- the tail pads with idle so every timeline reaches `total` seconds

dialogue.json:
{
  "total": 15.9,           # shared take length, seconds
  "fps": 24,
  "seat": {"height": 0.45, "kneeGap": 0.35, "footGap": 0.55},
  "idleBase": "mx_sitting_idle_sitting_in_chair_hands_resting_on_thighs",
  "listenClips": ["mx_ro_judge_03", "mx_ro_judge_05"],
  "speakers": [
    {"name": "male",   "start": 0.0,  "plan": "male/timeline.json",
     "rhubarb": "male/cues.json"},
    {"name": "female", "start": 7.65, "plan": "female/timeline.json",
     "rhubarb": "female/cues.json"}
  ]
}

python3 scripts/cast-dialogue-shots.py dialogue.json out_dir/
"""
import json,sys,copy
from pathlib import Path

def shift_rhubarb(src, dst, offset):
    cues=json.loads(Path(src).read_text())
    for q in cues['mouthCues']:
        q['start']+=offset; q['end']+=offset
    Path(dst).write_text(json.dumps(cues))
    return dst

def main():
    cfg=json.loads(Path(sys.argv[1]).read_text());out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
    fps=cfg.get('fps',24);total_f=int(round(cfg['total']*fps))
    listens=cfg.get('listenClips') or ['mx_sitting_idle_sitting_with_breathing_idle','mx_sitting_idle_sitting_still_in_a_chair']
    for i,sp in enumerate(cfg['speakers']):
        plan=json.loads(Path(sp['plan']).read_text());off_s=sp['start'];off_f=int(round(off_s*fps))
        for e in plan.get('expressions',[]):e['at']+=off_f
        # listening stretch before the speaker's first planned step
        pre=[]
        if off_f>fps:  # more than a second of listening: idle + a nod + idle
            clip=listens[i%len(listens)]
            clip_f=80  # ro_judge/listen clips run ~50-95f; fills aim at the offset
            a=max(8,off_f//3);b=max(8,off_f-a-clip_f)
            pre=[{"idle":a},{"clip":clip,"cue":" listen","category":"listen"},{"idle":b}]
        elif off_f>0:
            pre=[{"idle":off_f}]
        seq=pre+plan['sequence']
        # tail: estimate content length and pad the rest with idle — split around
        # a listen clip so an early speaker still nods during later turns
        def est(step):
            return step.get('idle',0)+48 if 'idle' in step else 100
        est_len=sum(est(s) for s in seq)-30*max(0,len(seq)-1)
        gap=max(0,total_f-est_len)
        if gap>fps*2:
            a=gap//2-48;b=gap-a-148
            tail=[{"idle":max(8,a)},{"clip":listens[(i+1)%len(listens)],"cue":" listen","category":"listen"},{"idle":max(8,b)}]
        elif gap>0:
            tail=[{"idle":gap}]
        else:
            tail=[]
        seq=seq+tail
        plan['sequence']=seq
        if 'rhubarb' in sp:
            dst=str(out/f"{sp['name']}_cues.json")
            plan['lipSync']={"rhubarb":shift_rhubarb(sp['rhubarb'],dst,off_s),"mouthOpen":plan.get('lipSync',{}).get('mouthOpen',1.2)}
        if cfg.get('seat'):plan['seat']=cfg['seat']
        if cfg.get('idleBase'):plan['idleBase']=cfg['idleBase']
        dst=out/f"{sp['name']}_dialogue.json";dst.write_text(json.dumps(plan,indent=1))
        print('DIALOGUE',sp['name'],'start',off_s,'->',dst)

if __name__=='__main__':
    main()
