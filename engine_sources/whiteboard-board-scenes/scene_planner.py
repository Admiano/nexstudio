"""Scene understanding for story scenes: a local language model reads a
whole scene and writes what an illustrator would plan before drawing.

For each scene the plan names the place and the fixtures that stay in it
(a piano in a music room stays in every picture there), and for every
sentence what each person's body is doing (one of the motor schemas of
`sb_activity`), with what, on what, their expression, and the things the
picture needs even when unsaid (rain -> an umbrella in the hand).

The model is free and local (Qwen2.5-7B-Instruct, Apache-2.0, through
llama.cpp). Output is constrained to a JSON schema, decoding is greedy
and every plan is cached by its prompt, so a script always gets the same
plan. Without the model (or with NEXSTUDIO_SCENE_LLM=off) `plan` returns
None and the rule-based staging stands alone.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

import sb_activity
import sb_cast
import sb_story
import scene_map

_CACHE = os.path.expanduser(os.environ.get(
    'NEXSTUDIO_SCENE_PLAN_CACHE', '~/.cache/nexstudio/scene_plans'))
_MODEL_GLOB = ('~/models/qwen2.5-7b-instruct-q4_k_m-00001-of-*.gguf',
               '~/models/*instruct*.gguf')
_VERSION = 'scene-plan-v3'

# what each body pattern looks like, so the model picks by meaning
ACTIONS = {
    'stand': 'standing still, no particular action',
    'walk': 'walking somewhere', 'run': 'running', 'jump': 'jumping',
    'dance': 'dancing', 'hike': 'hiking up a hill or trail',
    'climb': 'climbing a ladder, tree, wall or rock face',
    'crawl': 'crawling', 'swim': 'swimming', 'glide': 'skiing, skating, surfing',
    'drive': 'driving or steering a vehicle (seated, hands on the wheel)',
    'ride': 'riding on a bike, horse or animal', 'row': 'rowing a boat',
    'board': 'getting on or into a vehicle',
    'sit': 'sitting on a seat, bench, sofa or floor',
    'lie': 'lying down, sleeping in bed', 'kneel': 'kneeling or crouching',
    'sit_read': 'sitting and reading', 'sit_drink': 'sitting and drinking',
    'desk': 'sitting at a desk or table working',
    'read': 'reading something held in the hands',
    'drink': 'drinking from a cup or bottle', 'eat': 'eating food',
    'cook': 'cooking or stirring at a stove', 'cut': 'cutting with a knife or tool',
    'craft': 'working with the hands on something on a table (knead, sew, build)',
    'pour': 'pouring a liquid from one container into another',
    'wipe': 'wiping, cleaning, washing', 'dig': 'digging, sweeping',
    'plant': 'planting', 'fix': 'repairing or building with tools',
    'strike': 'hammering or hitting', 'paint': 'painting',
    'write': 'writing', 'type': 'typing on a computer',
    'carry': 'carrying something', 'hold': 'holding something in the hands',
    'give': 'handing something to another person',
    'pick': 'picking up or picking fruit', 'lift': 'lifting something heavy',
    'push': 'pushing (a cart, a door)', 'pull': 'pulling or dragging',
    'throw': 'throwing', 'kick': 'kicking',
    'open': 'opening a door, box or gate',
    'look': 'watching or looking at something',
    'point': 'pointing at something', 'photo': 'taking a photo',
    'phone': 'talking on a phone', 'talk': 'talking, telling, singing',
    'play': 'playing a musical instrument', 'fish': 'fishing with a rod',
    'hug': 'hugging another person', 'clap': 'clapping hands',
    'wave': 'waving a hand', 'bow': 'bowing',
    'nod': 'nodding the head', 'tap': 'tapping fingers or a foot',
    'cover_face': 'covering the face with the hands',
    'wipe_tears': 'wiping tears from the eyes',
}
EXPRESSIONS = ('neutral', 'happy', 'laugh', 'sad', 'cry', 'angry',
               'afraid', 'stressed', 'tired', 'sleep', 'love', 'proud',
               'calm', 'excited', 'think', 'confused')


def _schema() -> dict:
    s = {'type': 'string'}
    person = {'type': 'object', 'properties': {
        'name': s,
        'action': {'type': 'string', 'enum': list(ACTIONS)},
        'object': s, 'on': s, 'with_person': s,
        'expression': {'type': 'string', 'enum': list(EXPRESSIONS)},
        'holding': s, 'wearing': s},
        'required': ['name', 'action', 'object', 'on', 'with_person',
                     'expression', 'holding', 'wearing']}
    moment = {'type': 'object', 'properties': {
        'sentence': {'type': 'integer'},
        'place': s,
        'people': {'type': 'array', 'items': person},
        'things': {'type': 'array', 'items': s}},
        'required': ['sentence', 'place', 'people', 'things']}
    return {'type': 'object', 'properties': {
        'place': s, 'fixtures': {'type': 'array', 'items': s},
        'moments': {'type': 'array', 'items': moment}},
        'required': ['place', 'fixtures', 'moments']}


_SYSTEM = (
    "You are the storyboard artist of a hand-drawn whiteboard video. "
    "Before anything is drawn you read a whole scene and plan, for every "
    "sentence, the one picture shown while it is spoken. Reply in JSON.")


def _prompt(sents: list, people: list, before: str) -> str:
    acts = '\n'.join(f'  {k}: {v}' for k, v in ACTIONS.items())
    lines = '\n'.join(f'{i}. {s}' for i, s in enumerate(sents))
    known = ', '.join(people) if people else '(none named yet)'
    ctx = f'Story so far: {before}\n' if before else ''
    return (
        f"{ctx}Scene sentences:\n{lines}\n\n"
        f"People already in the story: {known}\n\n"
        "Plan the scene:\n"
        "- place: where the whole scene happens, a short noun (kitchen, "
        "music room, street, park, town hall, bedroom ...).\n"
        "- fixtures: up to 4 large things that stay in that place and "
        "should be in every picture of it (piano, window, bed, counter, "
        "trees ...), only ones the scene mentions or clearly implies.\n"
        "- moments: one per sentence, with `sentence` = its number and "
        "`place` = where that sentence happens (repeat the scene place "
        "if unchanged).\n"
        "  - people: every person or animal visible in that picture, by "
        "the name used in the story (use 'mia', 'teacher', 'boy 1', "
        "'boy 2'; an animal such as 'puppy' counts). For each:\n"
        "    action: what the body is doing, chosen from:\n"
        f"{acts}\n"
        "    Use the meaning in context: 'plays a song' at a piano is "
        "play; 'taps the rhythm on his knee' is tap; 'tells a story' is "
        "talk. A person who only listens is stand or sit.\n"
        "    object: the thing the action is done with or on, '' if none; "
        "a part of the person's own body (knee, hands, face) is not an "
        "object.\n"
        "    on: the seat, bed, ladder or surface the body is on, '' if "
        "standing on the floor or ground.\n"
        "    with_person: the other person the action is done to or "
        "with, '' if none.\n"
        "    expression: the face, from "
        f"{', '.join(EXPRESSIONS)}.\n"
        "    holding: the thing in the hands, '' if none.\n"
        "    wearing: clothing the sentence mentions, '' if none.\n"
        "  - things: every concrete object the picture must show, said "
        "or clearly implied (rain implies an umbrella only if someone "
        "has one; a concert implies a stage). Short nouns, no people, "
        "no abstract words (mistake, rhythm, song, joy, afternoon).\n")


_LLM = None


def _model_path() -> str:
    env = os.environ.get('NEXSTUDIO_SCENE_LLM', '')
    if env.lower() in ('off', '0', 'none', 'false'):
        return ''
    if env and os.path.exists(os.path.expanduser(env)):
        return os.path.expanduser(env)
    for g in _MODEL_GLOB:
        hits = sorted(glob.glob(os.path.expanduser(g)))
        if hits:
            return hits[0]
    return ''


def available() -> bool:
    if not _model_path():
        return False
    return Llama is not None


def _complete(prompt: str) -> str:
    global _LLM
    if _LLM is None:
        _LLM = Llama(model_path=_model_path(), n_ctx=8192,
                     n_threads=max(1, int(os.environ.get(
                         'OMP_NUM_THREADS', min(8, os.cpu_count() or 1)))),
                     seed=0, verbose=False)
    r = _LLM.create_chat_completion(
        messages=[{'role': 'system', 'content': _SYSTEM},
                  {'role': 'user', 'content': prompt}],
        response_format={'type': 'json_object', 'schema': _schema()},
        temperature=0.0, max_tokens=2200)
    return r['choices'][0]['message']['content']


def plan(sents: list, people: list = (), before: str = '') -> dict | None:
    """The illustrator's plan of one story scene, or None (no model)."""
    if os.environ.get('NEXSTUDIO_SCENE_LLM', '').lower() in (
            'off', '0', 'none', 'false'):
        return None
    prompt = _prompt(list(sents), sorted(people), before)
    key = hashlib.sha256((_VERSION + prompt).encode()).hexdigest()[:24]
    path = os.path.join(_CACHE, key + '.json')
    if os.path.exists(path):
        try:
            with open(path) as f:
                got = _clean(json.load(f), len(sents))
            if len(got['moments']) == len(sents):
                return got
        except (OSError, ValueError, TypeError):
            pass
    if not available():
        return None
    try:
        got = _clean(json.loads(_complete(prompt)), len(sents))
    except (ValueError, KeyError, TypeError):
        return None
    if len(got['moments']) != len(sents):
        return None
    os.makedirs(_CACHE, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(got, f, indent=1)
    return got


def _word(s) -> str:
    return re.sub(r'\s+', ' ', re.sub(r"[^a-z0-9 '#-]", ' ',
                                      str(s or '').lower())).strip()


def _clean(p: dict, n: int) -> dict:
    if not isinstance(p, dict):
        raise ValueError('scene plan must be an object')
    out = {'place': _word(p.get('place')),
           'fixtures': [_word(x) for x in p.get('fixtures') or []
                        if _word(x)][:4],
           'moments': []}
    seen = set()
    for m in p.get('moments') or []:
        if not isinstance(m, dict):
            continue
        k = m.get('sentence')
        if type(k) is not int or not 0 <= k < n or k in seen:
            continue
        seen.add(k)
        ppl = []
        for q in m.get('people') or []:
            if not isinstance(q, dict):
                continue
            nm = _word(q.get('name'))
            if not nm:
                continue
            ppl.append({f: _word(q.get(f)) for f in (
                'object', 'on', 'with_person', 'holding', 'wearing')} | {
                'name': nm,
                'action': q.get('action') if q.get('action') in ACTIONS
                else 'stand',
                'expression': q.get('expression')
                if q.get('expression') in EXPRESSIONS else 'neutral'})
        out['moments'].append({
            'sentence': k, 'place': _word(m.get('place')) or out['place'],
            'people': ppl,
            'things': [_word(x) for x in m.get('things') or []
                       if _word(x)]})
    out['moments'].sort(key=lambda m: m['sentence'])
    return out


# planner action -> motor schema ('' = no activity of its own)
_ALIAS = {'stand': '', 'write': 'desk', 'type': 'desk'}
_PHYS = {'noun.artifact', 'noun.food', 'noun.plant', 'noun.animal',
         'noun.object', 'noun.substance'}
_EXPR_EMO = {'wipe_tears': 'cry', 'cover_face': 'sad'}
_MAX_IMPLIED = 2
_SEATS = {'seat.n.03', 'chair.n.01', 'bench.n.01', 'sofa.n.01',
          'stool.n.01'}


def schema_of(action: str) -> str:
    a = _ALIAS.get(action, action)
    return a if a in sb_activity.SCHEMAS else ''


def _head(label: str) -> str:
    h = (re.findall(r"[a-z]+", str(label or '').lower()) or [''])[-1]
    if sb_story._wn is not None and h:
        return sb_story._wn.morphy(h, 'n') or h
    return h


# senses of words that name no thing to draw
_ABSTRACT = {'noun.communication', 'noun.act', 'noun.attribute',
             'noun.feeling', 'noun.cognition', 'noun.event', 'noun.time',
             'noun.state', 'noun.process', 'noun.relation',
             'noun.quantity', 'noun.motive', 'noun.possession'}


def concrete(label: str) -> bool:
    """A thing that can be drawn: its head noun names a physical object,
    not a person, a body part, a place, a time or an idea."""
    h = _head(label)
    if not h or sb_story.is_body_part(h) or sb_story.place_kind(h):
        return False
    return sb_story._lex(h) in _PHYS


def _who(name: str, people: list, alias: dict = None):
    """The person role a planner name refers to ('teacher' -> the role
    'mister okafor' cast as 'piano teacher'), or None."""
    nm = _word(name)
    toks = set(nm.split())
    key = (alias or {}).get(nm)
    if key:
        hit = next((r for r in people if key in (r.get('label'),
                                                 r.get('cast_key'))), None)
        if hit is not None:
            return hit
    best, score = None, 0
    for r in people:
        keys = {str(r.get(k) or '').lower() for k in
                ('label', 'cast_key', 'group')} - {''}
        keys |= {k.split('#')[0] for k in keys}
        keys |= set(r.get('aliases') or ())
        sc = 3 if nm in keys else 2 if any(
            toks & set(k.split()) for k in keys) else 0
        if sc > score:
            best, score = r, sc
    return best


def _mentioned(label: str, text: str) -> bool:
    h = _head(label)
    return bool(h) and any(_head(w) == h for w in
                          re.findall(r"[a-z]+", text.lower()))


def apply(sc: dict, plan: dict, sents: list, cast=None) -> list:
    """Merge the planner's reading into a staged story scene. The
    narration's own people and objects always stay; the plan only (a)
    replaces a body pattern the words alone got wrong or could not
    find, (b) adds faces and gestures, (c) keeps fixtures the scene
    names in every picture of its place and (d) adds the few concrete
    things a picture needs. It never adds a person. Returns notes of
    every change and every rejected suggestion."""
    rs = [sc['heroRole']] + sc['supportingRoles']
    notes = []
    alias = {lab: str(v.get('cast_key') or lab) for lab, v in
             (cast.people.items() if cast is not None else ())}
    named = {_head(r['label']) for r in rs if r.get('icon') != 'person'}
    fixtures = [f for f in plan.get('fixtures') or ()
                if concrete(f) and sb_story._lex(_head(f)) != 'noun.animal'
                and _head(f) in named]
    for f in set(plan.get('fixtures') or ()) - set(fixtures):
        notes.append({'reject': 'fixture', 'label': f})
    sc['scene_plan'] = plan
    sc['places'] = list(sc.get('places') or [])
    sc['places'].extend([''] * max(0, len(sents) - len(sc['places'])))
    fixture_place = {}
    carry: dict = {}
    for f in fixtures:
        first = next((m for m in plan['moments'] if
                      _mentioned(f, sents[m['sentence']])), None)
        if first is not None:
            fixture_place[f] = first['place']
    for m in plan.get('moments') or ():
        k = m['sentence']
        if k >= len(sents):
            continue
        sent = sents[k].lower()
        spoken = scene_map.parse(sents[k], carry)
        here = [r for r in rs if int(r.get('moment') or 0) == k]
        people = [r for r in here if r.get('icon') == 'person']
        place = m.get('place') or plan.get('place')
        if place and (not sc['places'][k] or _mentioned(place, sent)):
            sc['places'][k] = sb_story.place_kind(place) or place
        heads = {_head(r['label']) for r in here}

        def add(label, extra):
            h = _head(label)
            if h in heads:
                return None
            heads.add(h)
            r_ = {'label': label, 'icon': label, 'moment': k,
                  'size': sb_story.size_of(label), 'planned': True, **extra}
            rs.append(r_)
            return r_
        implied = 0
        for q in m.get('people') or ():
            r = _who(q['name'], people, alias)
            if r is None and _head(q['name']) in heads:
                continue
            if r is None:
                prior = _who(q['name'], [o for o in rs
                             if o.get('icon') == 'person' and
                             int(o.get('moment') or 0) < k], alias)
                if prior is None:
                    notes.append({'reject': 'person', 'moment': k,
                                  'name': q['name']})
                    continue
                r = {key: value for key, value in prior.items()
                     if key not in ('activity', 'action', 'attach', 'to',
                                    'touch', 'lap_of', 'held', 'lean_on')}
                r.update(moment=k, narration=sents[k], planned=True)
                rs.append(r)
                here.append(r)
                people.append(r)
            me = rs.index(r)
            act = q.get('action') or 'stand'
            sch = schema_of(act)
            cur = r.get('activity') or {}
            if cur.get('posture'):
                sch = cur['schema']
            part = cur.get('partner')
            own = str(r.get('narration') or '').lower() == sent
            names = {r['label'], r.get('cast_key') or '', q['name']} \
                | set(r.get('aliases') or ())
            stated = sch == cur.get('schema')
            if spoken is not None:
                stated = stated or any(
                    (sb_activity.resolve(ev['lemma'], ()) or {}).get(
                        'schema') == sch
                    and (ev['agent'] is not None
                         and spoken['entities'][ev['agent']]['label'] in names
                         or sch in ('walk', 'run', 'hike', 'crawl', 'swim')
                         and any(prep == 'with'
                                 and spoken['entities'][eid]['label'] in names
                                 for prep, eid in ev['preps']))
                    for ev in spoken['events'])
            if not stated and sch not in ('stand', 'sit', 'lie'):
                notes.append({'reject': 'unstated-action', 'moment': k,
                              'name': q['name'], 'action': act})
                continue
            if sch and (own or not cur) and (
                    sch != cur.get('schema') or
                    _head(q.get('object')) != _head(part)):
                obj = q.get('object') or ''
                if obj and not (concrete(obj) or (
                        sb_activity.noun_cat(obj)
                        and not sb_story.is_body_part(obj) or
                        sb_activity.noun_cat(obj) == 'instrument')):
                    obj = ''
                posture = r.get('stance', '')
                if (q.get('on') and sb_story._closure(
                        _head(q['on']), k=1) & _SEATS):
                    posture = 'sit'
                objects = [('dobj', obj)] if obj else []
                if q.get('on') and concrete(q['on']):
                    objects.append(('on', q['on']))
                if sch == cur.get('schema'):
                    preps = {'source': 'from', 'goal': 'into',
                             'instrument': 'with', 'vantage': 'from'}
                    objects.extend((preps[role], label)
                                   for role, label in
                                   (cur.get('roles') or {}).items()
                                   if role in preps and label)
                spec = sb_activity.resolve(
                    cur.get('lemma') or act, objects, posture, schema=sch)
                if spec is not None:
                    original = sb_activity.resolve(
                        cur.get('lemma') or '',
                        [('dobj', cur['partner'])] if cur.get('partner') else (),
                        cur.get('posture') or '')
                    generic = sb_activity.resolve(cur.get('lemma') or '', ())
                    if spec['schema'] == cur.get('schema') or (
                            original is not None
                            and original['schema'] == cur.get('schema')
                            and (sch in ('stand', 'sit', 'lie')
                                 or generic is not None
                                 and generic['schema'] == sch)):
                        spec.update(cur)
                    old = cur.get('partner')
                    for o in here:
                        if o.get('to') == me and o['label'] == old and \
                                o.get('attach') in ('activity', 'held'):
                            if concrete(o['label']):
                                o.pop('attach')
                                o.pop('to')
                            else:
                                o['absorbed'] = True
                    new = dict(spec, via='scene-plan')
                    if cur.get('posture'):
                        new['posture'] = cur['posture']
                    new.pop('partner', None)
                    for o in here:
                        if o.get('to') == me and o.get('icon') != 'person' \
                                and not concrete(o['label']):
                            o['absorbed'] = True
                    if spec.get('partner'):
                        pr = next((o for o in here if o['label']
                                   == spec['partner']), None)
                        if pr is not None and pr.get('to') not in (None, me):
                            pr = None
                        said = _mentioned(spec['partner'], sent)
                        if pr is None and (said or spec['partner'] in fixtures
                                           or implied < _MAX_IMPLIED):
                            implied += not said
                            pr = add(spec['partner'], {})
                        if pr is not None:
                            pr.update(attach='held' if spec['schema'] in
                                      sb_activity.HAND_SCHEMAS
                                      and spec.get('kind') != 'keyboard'
                                      else 'activity', to=me)
                            new['partner'] = pr['label']
                    r['activity'] = new
                    r.pop('activity_miss', None)
                    notes.append({'moment': k, 'person': r['label'],
                                  'schema': [cur.get('schema'), sch]})
            emo = _EXPR_EMO.get(act) or q.get('expression') or 'neutral'
            if emo != 'neutral' and emo in sb_cast.EMOTIONS \
                    and not r.get('emotion'):
                r['emotion'] = emo
            peer = _who(q.get('with_person') or '', people, alias)
            if peer is not None and peer is not r:
                r['face_to'] = peer.get('cast_key') or peer['label']
                if act == 'hug':
                    r['touch'] = [peer.get('cast_key') or peer['label']]
            for w_ in (q.get('wearing'), q.get('holding')):
                o = next((o for o in here if w_ and o.get('icon') != 'person'
                          and _head(o['label']) == _head(w_)
                          and sb_story.is_worn(o['label'])), None)
                if o is not None and not o.get('to'):
                    o.update(worn=True, to=me)
                    o.pop('attach', None)
                    notes.append({'moment': k, 'worn': o['label']})
            hold = q.get('holding') or ''
            if sb_story.is_worn(hold):
                hold = ''
            if hold and concrete(hold) and not any(
                    o.get('to') == me for o in here) and (
                    _mentioned(hold, sent) or implied < _MAX_IMPLIED):
                implied += not _mentioned(hold, sent)
                if add(hold, {'attach': 'held', 'to': me}) is not None:
                    notes.append({'moment': k, 'held': hold})
        for t in m.get('things') or ():
            if not concrete(t) or _head(t) in heads:
                continue
            said = _mentioned(t, sent)
            if not said and (implied >= _MAX_IMPLIED or sb_story._lex(
                    _head(t)) == 'noun.animal'):
                notes.append({'reject': 'thing', 'moment': k, 'label': t})
                continue
            implied += not said
            add(t, {})
            notes.append({'moment': k, 'thing': t, 'said': said})
        # narrated words the illustrator drew no thing for (a song, a
        # mistake, a part of the body, a verb read as a noun) stay unsaid
        wanted = {_head(x) for q in m.get('people') or () for x in (
            q.get('object'), q.get('holding')) if x} | {
            _head(t) for t in m.get('things') or ()}
        acts = {q.get('action') for q in m.get('people') or ()}
        for o in here:
            if o.get('icon') == 'person' or o.get('absorbed') or \
                    o.get('group') or _head(o['label']) in wanted:
                continue
            h = _head(o['label'])
            if sb_story.place_kind(h):
                continue
            if sb_story.is_body_part(h) or h in acts or (
                    sb_story._lex(h) in _ABSTRACT):
                o['absorbed'] = True
                notes.append({'moment': k, 'unsaid': o['label']})
        if people:
            seated = any((r.get('activity') or {}).get('schema') in
                         sb_activity._SEATED_SCHEMAS | {'play'}
                         or r.get('stance') == 'sit' for r in people)
            for f in fixtures:
                if fixture_place.get(f) != place:
                    continue
                if seated and sb_story._closure(_head(f), k=1) & _SEATS:
                    continue
                if add(f, {'fixture': True}) is not None:
                    notes.append({'moment': k, 'fixture': f})
    sc['heroRole'], sc['supportingRoles'] = rs[0], rs[1:]
    return notes
