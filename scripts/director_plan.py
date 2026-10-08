"""Director plan for the cinematic caption layer — context-derived, never templated.

Reads the MFA word clock, the speaker's own loudness/duration statistics and the
intent lexicon shared with the gesture planner (gesture-meanings.json), and emits
a shot plan: which clause goes to which depth tier, which word earns a hero
behind-the-head card, and how the virtual camera pushes, whips or settles through
each beat. Same inputs, different questions — every timing and every pick comes
from the actual narration, so two different scripts never produce the same edit.
"""
import json, math, re, subprocess, array
from pathlib import Path

MEAN_PATH = Path(__file__).resolve().parents[1] / 'engine_sources/makehuman-lineart/character_system/gesture-meanings.json'
STOP = set('a an the and or but of to in on for with at by is are was were be been it its this that these those i we you he she they as not no do does did can could will would should may might'.split())

def norm(w):
    return re.sub(r'[^a-z0-9]', '', w.lower())

def _energies(words, audio):
    if not audio:
        return None
    try:
        raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', audio, '-f', 's16le', '-ac', '1', '-ar', '16000', '-'],
                             capture_output=True, check=True).stdout
    except Exception:
        return None
    x = array.array('h', raw)
    out = []
    for w in words:
        seg = x[int(w['start'] * 16000):max(int(w['start'] * 16000) + 1, int(w['end'] * 16000))]
        out.append(math.sqrt(sum(v * v for v in seg) / len(seg)) if seg else 0.0)
    return out

def _stress(words, audio):
    """Word stress = loudness and duration-per-letter vs the speaker's own
    average, normalised to the median (same scoring as cast-gesture-plan.py)."""
    E = _energies(words, audio)
    dur = [(w['end'] - w['start']) / max(3, len(norm(w['word']))) for w in words]
    md = sum(dur) / max(1, len(dur))
    me = (sum(E) / len(E)) if E else 1.0
    st = [(d / md) * (E[i] / me if E else 1.0) for i, d in enumerate(dur)]
    med = sorted(st)[len(st) // 2] if st else 1.0
    return [s / (med or 1.0) for s in st]

def _sentences(words, script=None, pause_sec=0.7):
    """Sentence grouping -> [(indices, raw_text)]. MFA word streams carry no
    punctuation (phones.json), so boundaries come from the script text first —
    each script sentence's word count maps onto the timed word list in order —
    with delivery pauses as backstop."""
    if script:
        parts = re.split(r'([.!?]+)', script)
        texts = [(parts[i] + (parts[i + 1] if i + 1 < len(parts) else '')).strip()
                 for i in range(0, len(parts), 2)]
        texts = [t for t in texts if t.strip()]
        sents, k = [], 0
        for t in texts:
            n = max(1, len([w for w in t.split() if norm(w)]))
            if k < len(words):
                sents.append((list(range(k, min(len(words), k + n))), t))
                k += n
        while k < len(words):
            if sents:
                sents[-1][0].append(k)
            else:
                sents.append(([k], ''))
            k += 1
        if sents:
            return sents
    sents = [([0], '')]
    for i in range(1, len(words)):
        if re.search(r'[.!?]$', words[i - 1]['word']) or words[i]['start'] - words[i - 1]['end'] >= pause_sec:
            sents.append(([], ''))
        sents[-1][0].append(i)
    return sents

def _intent(words, sen, mean, stress, script_sen=None):
    text = (script_sen if script_sen is not None else
            ' '.join(words[i]['word'] for i in sen)).lower()
    pos, t2 = [], ''
    for i in sen:
        pos.append(len(t2))
        t2 += words[i]['word'].lower() + ' '
    for name, pat in mean['intents']:
        m = re.search(pat, text)
        if m:
            # the cue is the timed word whose position covers the pattern hit
            hit = m.start() if script_sen is None else min(m.start(), len(t2) - 1)
            return name, max(k for k, p in zip(sen, pos) if p <= hit)
    best = max(sen, key=lambda i: stress[i] if len(norm(words[i]['word'])) >= 3 else 0)
    q = (script_sen if script_sen is not None else words[sen[-1]]['word']).strip().endswith('?')
    return (mean['questionIntent'] if q else mean['defaultIntent']), best

def _clauses(words, sen):
    """Sub-sentence beats split on delivery pauses (>=0.42s)."""
    out, cur = [], [sen[0]]
    for i in sen[1:]:
        if words[i]['start'] - words[cur[-1]]['end'] >= 0.42:
            out.append(cur)
            cur = [i]
        else:
            cur.append(i)
    out.append(cur)
    return out

def _hero_pick(words, clause, stress, cue_idx):
    """The clause's emphasis carrier: the intent's cue word when it's a real
    content word, else the most stressed content word in the clause."""
    def ok(i):
        n = norm(words[i]['word'])
        return len(n) >= 4 and n not in STOP
    if cue_idx is not None and cue_idx in clause and ok(cue_idx) and stress[cue_idx] >= 1.0:
        return cue_idx
    cand = [i for i in clause if ok(i)]
    if not cand:
        return None
    best = max(cand, key=lambda i: stress[i])
    return best if stress[best] >= 1.15 else None

# intent -> shot grammar. 'push' grows the frame through the beat; 'whip' opens
# the film; 'settle' breathes out; hero intents get a behind-the-head word.
# Names are the gesture lexicon's (gesture-meanings.json) — same source, so a
# word that earns a gesture earns the matching camera treatment.
INTENT_SHOTS = {
    'welcome': {'camera': 'whip', 'depth': 'front'},
    'thanks': {'camera': 'settle', 'depth': 'mid'},
    'question': {'camera': 'push', 'hero': True, 'depth': 'mid'},
    'reassure': {'camera': 'push', 'hero': True, 'depth': 'mid'},
    'contrast': {'camera': 'push', 'hero': True, 'depth': 'mid'},
    'concern': {'camera': 'push', 'hero': True, 'depth': 'mid'},
    'negate': {'camera': 'push', 'hero': True, 'depth': 'mid'},
    'excited': {'camera': 'push', 'hero': True, 'depth': 'mid'},
    'disbelief': {'camera': 'push', 'hero': True, 'depth': 'mid'},
    'uncertain': {'camera': 'settle', 'depth': 'far'},
    'point': {'camera': 'settle', 'depth': 'mid'},
    'agree': {'camera': 'settle', 'depth': 'mid'},
    'funny': {'camera': 'settle', 'depth': 'mid'},
    'scale': {'camera': 'push', 'hero': True, 'depth': 'mid'},
    'you': {'camera': 'push', 'depth': 'mid'},
    'think': {'camera': 'settle', 'depth': 'mid'},
    'explain': {'camera': 'settle', 'depth': 'mid'},
    'list': {'camera': 'settle', 'depth': 'mid'},
    'narrate': {'camera': 'settle', 'depth': 'far'},
    'still': {'camera': 'settle', 'depth': 'far'},
}

def plan(script, words, audio_path, W, H, pres_box):
    """-> {'clauses': [...], 'camera': [(t0,t1,s0,s1,mode)], 'heroCount': n}"""
    if not words:
        return {'clauses': [], 'camera': [], 'heroCount': 0}
    mean = json.loads(MEAN_PATH.read_text()) if MEAN_PATH.exists() else {
        'intents': [], 'defaultIntent': 'explain', 'questionIntent': 'question'}
    stress = _stress(words, audio_path)
    sentences = _sentences(words, script)
    intents = [(sen,) + _intent(words, sen, mean, stress, raw) for sen, raw in sentences]

    px, py, pw, ph = pres_box
    clauses, cam, last_hero_t = [], [], -9.9
    # film opens on a whip-in only when the first sentence actually greets;
    # otherwise it opens settled. Every later clause picks its shot by intent.
    for si, (sen, intent, cue) in enumerate(intents):
        shot = dict(INTENT_SHOTS.get(intent, INTENT_SHOTS['explain']))
        if si == 0 and intent != 'welcome':
            shot['camera'] = 'settle'
        for ci, clause in enumerate(_clauses(words, sen)):
            w0, w1 = clause[0], clause[-1]
            t0, t1 = words[w0]['start'], words[w1]['end']
            word_list = [{'i': i, 'word': words[i]['word'], 'start': words[i]['start'], 'end': words[i]['end'],
                          'stress': round(stress[i], 3)} for i in clause]
            hero_i = None
            if shot.get('hero') and t0 - last_hero_t >= 2.2:
                hero_i = _hero_pick(words, clause, stress, cue)
                if hero_i is not None:
                    last_hero_t = t0
            clauses.append({
                'sent': si, 'clause': ci, 'intent': intent, 't0': t0, 't1': t1,
                'words': word_list,
                'depth': 'front' if (shot['depth'] == 'front' and ci == 0) else ('far' if shot['depth'] == 'far' else 'mid'),
                'hero': hero_i,
                'side': 'left' if (si + ci) % 2 == 0 else 'right',
            })
            # camera segment: push grows, settle relaxes, whip opens the film
            if shot['camera'] == 'push':
                cam.append((t0 - 0.25, t1, 1.0, 1.10, 'push'))
            elif shot['camera'] == 'whip' and si == 0 and ci == 0:
                cam.append((t0 - 0.05, t0 + 1.1, 1.18, 1.0, 'whip'))
            elif shot['camera'] == 'settle':
                cam.append((t0 - 0.15, t1, 1.05, 1.0, 'settle'))
    cam.sort(key=lambda c: c[0])
    return {'clauses': clauses, 'camera': cam, 'heroCount': sum(1 for c in clauses if c['hero'] is not None)}

def camera_at(camera, t):
    """Frame scale at time t: eases between segment endpoints; between segments
    the frame keeps a slow creep so it never lands (1.0 -> 1.03 drift)."""
    s = 1.0
    for (t0, t1, s0, s1, mode) in camera:
        if t < t0:
            break
        if t <= t1:
            u = (t - t0) / max(0.01, t1 - t0)
            e = 1 - (1 - u) ** 3 if mode == 'whip' else u * u * (3 - 2 * u)
            s = s0 + (s1 - s0) * e
        else:
            # after the segment ends it keeps breathing at ~3% per clause length
            s = s1 + min(0.03, (t - t1) * 0.012)
    return s
