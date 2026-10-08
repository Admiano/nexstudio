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
    """-> {'clauses': [...], 'camera': [(t0,t1,s0,s1,mode)], 'apex': clause, 'heroCount': n}

    Film-level grammar, not per-sentence: the whole-script energy envelope picks
    clause ROLES (opener/dev/pivot/apex/close); the apex clause gets the full
    three-act hero treatment while everything co-visible yields to it."""
    if not words:
        return {'clauses': [], 'camera': [], 'apex': None, 'heroCount': 0}
    mean = json.loads(MEAN_PATH.read_text()) if MEAN_PATH.exists() else {
        'intents': [], 'defaultIntent': 'explain', 'questionIntent': 'question'}
    stress = _stress(words, audio_path)
    E = _energies(words, audio_path) or [0.0] * len(words)
    sentences = _sentences(words, script)
    intents = [(sen,) + _intent(words, sen, mean, stress, raw) for sen, raw in sentences]

    dur_total = max(1.0, words[-1]['end'] - words[0]['start'])
    # intent weight: how much a sentence DESERVES the camera's attention
    IW = {'contrast': 1.45, 'question': 1.35, 'negate': 1.3, 'disbelief': 1.3, 'excited': 1.3,
          'reassure': 1.2, 'scale': 1.2, 'concern': 1.15, 'welcome': 1.0, 'you': 1.05,
          'explain': 1.0, 'think': 0.95, 'point': 0.95, 'agree': 0.9, 'funny': 0.9,
          'thanks': 0.9, 'list': 0.9, 'uncertain': 0.75, 'narrate': 0.7, 'still': 0.6}

    # clause list first (flat), then role assignment over the whole arc
    clauses = []
    for si, (sen, intent, cue) in enumerate(intents):
        for ci, clause in enumerate(_clauses(words, sen)):
            w0, w1 = clause[0], clause[-1]
            clauses.append({
                'sent': si, 'clause': ci, 'intent': intent, 'cue': cue,
                't0': words[w0]['start'], 't1': words[w1]['end'],
                'words': [{'i': i, 'word': words[i]['word'], 'start': words[i]['start'],
                           'end': words[i]['end'], 'stress': round(stress[i], 3),
                           'energy': round(E[i], 1)} for i in clause],
            })
    n = len(clauses)
    last_sent = intents[-1][0] if intents else []
    for c in clauses:
        s_mean = sum(w['stress'] for w in c['words']) / max(1, len(c['words']))
        e_mean = sum(w['energy'] for w in c['words']) / max(1, len(c['words']))
        c['w'] = IW.get(c['intent'], 1.0) * s_mean * (1.0 + 0.4 * (c['t0'] / dur_total))
        c['e'] = e_mean
    # apex = the clause the whole film builds toward — highest weighted energy,
    # excluding the opener (it opens the film, it isn't the payoff)
    apex_i = max(range(1 if n > 2 else 0, n), key=lambda i: clauses[i]['w'], default=None)
    for i, c in enumerate(clauses):
        if i == apex_i:
            c['role'] = 'apex'
        elif c['sent'] == 0 and c['clause'] == 0:
            c['role'] = 'opener'
        elif c['sent'] == (len(intents) - 1) and c['clause'] == len(_clauses(words, last_sent)) - 1:
            c['role'] = 'close'
        elif c['intent'] in ('contrast', 'negate', 'question', 'disbelief'):
            c['role'] = 'pivot'
        else:
            c['role'] = 'dev'

    ENTRANCE = {'contrast': 'slam', 'negate': 'slam', 'disbelief': 'slam',
                'question': 'emergence', 'excited': 'rise', 'scale': 'emergence',
                'reassure': 'settle', 'concern': 'rise'}
    last_hero_t = -9.9
    for i, c in enumerate(clauses):
        shot = INTENT_SHOTS.get(c['intent'], INTENT_SHOTS['explain'])
        c['depth'] = 'front' if (c['role'] == 'opener' and shot['depth'] == 'front') else \
            ('far' if shot['depth'] == 'far' else 'mid')
        c['side'] = 'left' if (c['sent'] + c['clause']) % 2 == 0 else 'right'
        c['hero'] = None
        c['minor'] = True
        c['entrance'] = ENTRANCE.get(c['intent'], 'emergence')
        # amp ∝ the hero word's measured loudness vs the speaker's average
        hero_i = _hero_pick(words, [w['i'] for w in c['words']], stress, c['cue'])
        if c['role'] == 'apex':
            if hero_i is None:
                cand = [w['i'] for w in c['words'] if len(norm(w['word'])) >= 4 and norm(w['word']) not in STOP]
                hero_i = max(cand, key=lambda j: stress[j]) if cand else c['words'][-1]['i']
            c['hero'], c['minor'] = hero_i, False
            last_hero_t = c['t0']
        elif shot.get('hero') and hero_i is not None and c['t0'] - last_hero_t >= 2.2:
            c['hero'] = hero_i
            last_hero_t = c['t0']
        if c['hero'] is not None:
            c['amp'] = max(0.7, min(1.6, E[c['hero']] / (sum(E) / max(1, len(E)) + 1e-6)))

    # camera: clause-role driven — apex pushes hardest, the clause before it
    # holds still (dead air makes the payoff land), openers whip or settle,
    # closes settle and the frame never lands anywhere
    cam = []
    for i, c in enumerate(clauses):
        shot = INTENT_SHOTS.get(c['intent'], INTENT_SHOTS['explain'])
        if c['role'] == 'apex':
            cam.append((c['t0'] - 0.3, c['t1'], 1.0, 1.13, 'push'))
        elif apex_i is not None and i == apex_i - 1:
            cam.append((c['t0'] - 0.15, c['t1'] + 0.25, 1.03, 1.0, 'hold'))  # let it breathe
        elif c['role'] == 'opener' and shot['camera'] == 'whip':
            cam.append((c['t0'] - 0.05, c['t0'] + 1.1, 1.18, 1.0, 'whip'))
        elif shot['camera'] == 'push':
            cam.append((c['t0'] - 0.25, c['t1'], 1.0, 1.08, 'push'))
        else:
            cam.append((c['t0'] - 0.15, c['t1'], 1.05, 1.0, 'settle'))
    cam.sort(key=lambda x: x[0])
    apex = clauses[apex_i] if apex_i is not None else None
    return {'clauses': clauses, 'camera': cam, 'apex': apex,
            'heroCount': sum(1 for c in clauses if c['hero'] is not None)}

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
