"""Story mode for the storyboard planner.

A narrative scene (people doing, feeling and touching things in places)
is staged as pictures, never as a relation diagram:

  * `is_story_scene` tells a narrative scene from an explaining one by
    what its sentences do: bodies acting, feeling and touching versus
    things standing for, flowing to or being traded for other things.
  * `stage` completes each moment of a story scene: every person the
    sentence names (or its pronouns point to) is present, groups are
    drawn member by member ('two boys' -> two boys, 'the older boy' ->
    that same boy each time), emotions come from the verbs and states
    ('cries', 'is tired', 'with a smile'), body parts become poses or
    contacts ('holds her head', 'on her lap', 'kisses their foreheads'),
    people put to bed lie in it, places become the panel's backdrop,
    floors and grounds are the panel floor, substances with no drawing
    of their own are drawn in their container, and everything carries a
    real-world size so a cup is smaller than a sofa."""
from __future__ import annotations

import copy
import re

try:
    from nltk.corpus import wordnet as _wn
    _wn.synsets('dog')
except Exception:  # pragma: no cover
    _wn = None

import sb_activity
import scene_map
import sb_cast

_STORY_LEX = {'verb.motion', 'verb.contact', 'verb.body',
              'verb.consumption', 'verb.emotion'}

# verb lemma -> emotion shown on the doer
_EMO_VERB = {
    'laugh': 'laugh', 'giggle': 'laugh', 'chuckle': 'laugh',
    'smile': 'happy', 'grin': 'happy', 'beam': 'happy',
    'cry': 'cry', 'sob': 'cry', 'weep': 'cry', 'wail': 'cry',
    'whimper': 'cry', 'sigh': 'tired', 'yawn': 'tired',
    'frown': 'sad', 'sulk': 'sad', 'pout': 'sad', 'mourn': 'sad',
    'hug': 'love', 'kiss': 'love', 'cuddle': 'love', 'embrace': 'love',
    'snuggle': 'love', 'scream': 'panic', 'shriek': 'panic',
    'shout': 'angry', 'yell': 'angry', 'worry': 'afraid',
    'fret': 'afraid', 'tremble': 'afraid', 'cheer': 'excited',
    'celebrate': 'excited', 'sleep': 'sleep', 'nap': 'sleep',
    'doze': 'sleep', 'relax': 'calm', 'rest': 'calm'}
_EMO_ADJ = {
    'happy': 'happy', 'glad': 'happy', 'joyful': 'happy',
    'cheerful': 'happy', 'delighted': 'happy', 'relieved': 'happy',
    'grateful': 'happy', 'proud': 'proud', 'tired': 'tired',
    'exhausted': 'tired', 'sleepy': 'tired', 'weary': 'tired',
    'sad': 'sad', 'upset': 'sad', 'unhappy': 'sad', 'lonely': 'sad',
    'angry': 'angry', 'mad': 'angry', 'furious': 'angry',
    'scared': 'afraid', 'afraid': 'afraid', 'frightened': 'afraid',
    'worried': 'stressed', 'nervous': 'stressed', 'anxious': 'stressed',
    'stressed': 'stressed', 'overwhelmed': 'stressed',
    'frustrated': 'stressed', 'calm': 'calm', 'relaxed': 'calm',
    'peaceful': 'calm', 'excited': 'excited', 'asleep': 'sleep'}
# strongest feeling wins when a sentence carries several
_EMO_RANK = ('sleep', 'cry', 'laugh', 'stressed', 'angry', 'panic',
             'afraid', 'sad', 'love', 'tired', 'excited', 'proud',
             'happy', 'calm')
_WITH_FEEL = re.compile(r'\bwith (a|an)\s+(big\s+|wide\s+|warm\s+)?'
                        r'(smile|grin|laugh|sigh|frown|tears?)\b', re.I)
_WITH_EMO = {'smile': 'happy', 'grin': 'happy', 'laugh': 'laugh',
             'sigh': 'tired', 'frown': 'sad', 'tear': 'cry', 'tears': 'cry'}

_NUM = {'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'both': 2,
        'twin': 2, 'twins': 2, 'couple': 2, 'pair': 2, 'few': 3,
        'several': 3, '2': 2, '3': 3, '4': 4, '5': 5}
_IRREG = {'child': 'children', 'man': 'men', 'woman': 'women',
          'person': 'people', 'mouse': 'mice', 'goose': 'geese',
          'foot': 'feet', 'wife': 'wives', 'thief': 'thieves'}
# words that pick one member out of a group
_MEMBER = ('older', 'elder', 'eldest', 'oldest', 'bigger', 'younger',
           'youngest', 'little', 'littlest', 'smaller', 'baby', 'first',
           'second', 'third', 'middle', 'other', 'tall', 'taller',
           'short', 'shorter')
_MEMBER_RE = re.compile(r'\b(' + '|'.join(_MEMBER) + r')\s+(\w+)\b', re.I)
_OLDER = {'older', 'elder', 'eldest', 'oldest', 'bigger', 'first', 'tall',
          'taller'}
_YOUNGER = {'younger', 'youngest', 'little', 'littlest', 'smaller',
            'baby', 'second', 'third', 'short', 'shorter'}
_HOLD_VERBS = {'hug', 'embrace', 'cuddle', 'hold', 'comfort', 'squeeze',
               'pet', 'stroke', 'cradle', 'carry'}
_OUTSIDE = re.compile(r'\b(outside|outdoors?|streets?|roads?|corner|'
                      r'sidewalk|yard|garden|park|field|forest|beach|'
                      r'sunrise|sunset)\b')
_INSIDE = re.compile(r'\b(inside|indoors|within)\b')
_STREETY = re.compile(r'\b(streets?|roads?|corner|sidewalk)\b')
_PLURAL_PRO = re.compile(r'\b(them|they|both|their|all)\b', re.I)
_POSS = re.compile(r"\b(on|in|into|onto|across)\s+(her|his|their|"
                   r"[A-Z]\w+'s)\s+(\w+(?:'s)?\s+)?(lap|laps|arms|shoulders?|"
                   r"back|knees?)\b")

# (kind, WordNet anchors) most specific first: a panel's backdrop
_PLACES = (
    ('kitchen', {'kitchen.n.01', 'galley.n.01', 'bakery.n.01'}),
    ('bedroom', {'bedroom.n.01', 'nursery.n.01', 'dormitory.n.01'}),
    ('bathroom', {'bathroom.n.01', 'toilet.n.01'}),
    ('living', {'living_room.n.01', 'family_room.n.01', 'den.n.04'}),
    ('classroom', {'classroom.n.01', 'school.n.02', 'school.n.01'}),
    ('office', {'office.n.01', 'workplace.n.01', 'study.n.05'}),
    ('cafe', {'restaurant.n.01', 'coffee_shop.n.01', 'bar.n.02'}),
    ('hospital', {'hospital.n.01', 'clinic.n.03', 'infirmary.n.01'}),
    ('store', {'shop.n.01', 'mercantile_establishment.n.01',
               'marketplace.n.01', 'supermarket.n.01', 'checkout.n.01'}),
    ('outdoor', {'park.n.02', 'garden.n.01', 'yard.n.02', 'street.n.01',
                 'road.n.01', 'field.n.01', 'forest.n.01', 'beach.n.01',
                 'playground.n.01', 'geographical_area.n.01',
                 'body_of_water.n.01', 'land.n.04', 'mountain.n.01',
                 'farm.n.01', 'backyard.n.01'}),
    ('home', {'home.n.01', 'home.n.03', 'dwelling.n.01', 'house.n.01',
              'apartment.n.01', 'room.n.01'}),
)
_SURFACE = {'floor.n.01', 'floor.n.02', 'ground.n.01', 'earth.n.02',
            'wall.n.01', 'ceiling.n.01', 'pavement.n.01', 'sidewalk.n.01',
            'surface.n.01'}
_BED = {'bed.n.01', 'bunk.n.03', 'crib.n.01', 'hammock.n.02', 'cot.n.03',
        'bedroll.n.01'}
_LIQUID = {'liquid.n.01', 'beverage.n.01', 'liquid_body_substance.n.01',
           'oil.n.01', 'water.n.01', 'water.n.06', 'milk.n.01'}
# real-world height as a fraction of a standing adult
_WORN = {'clothing.n.01', 'footwear.n.01', 'footwear.n.02', 'glove.n.02',
         'headdress.n.01', 'garment.n.01', 'hat.n.01', 'shoe.n.01',
         'boot.n.01', 'glove.n.01', 'mitten.n.01'}
_SIZES = (
    ({'door.n.01', 'doorway.n.01', 'entrance.n.01'}, 1.20),
    ({'tree.n.01', 'building.n.01'}, 1.05),
    ({'car.n.01', 'truck.n.01', 'bus.n.01', 'boat.n.01'}, 0.72),
    ({'bicycle.n.01', 'handcart.n.01', 'shopping_cart.n.01',
      'wagon.n.01', 'baby_buggy.n.01'}, 0.52),
    ({'bed.n.01', 'sofa.n.01', 'table.n.02', 'desk.n.01'}, 0.44),
    ({'chair.n.01', 'seat.n.03', 'home_appliance.n.01', 'stove.n.02',
      'oven.n.01', 'refrigerator.n.01', 'cabinet.n.01',
      'furniture.n.01', 'appliance.n.02'}, 0.50),
    ({'dog.n.01', 'sheep.n.01', 'pig.n.01', 'goat.n.01'}, 0.36),
    ({'horse.n.01', 'cow.n.01', 'cattle.n.01'}, 0.85),
    ({'toy.n.01', 'doll.n.01', 'ball.n.01', 'bag.n.01', 'bag.n.04',
      'basket.n.01', 'box.n.01', 'bucket.n.01', 'pot.n.01',
      'pan.n.01', 'bowl.n.01', 'bowl.n.03', 'lamp.n.01'}, 0.24),
    ({'food.n.01', 'food.n.02', 'fruit.n.01', 'vegetable.n.01',
      'container.n.01', 'utensil.n.01', 'tableware.n.01',
      'publication.n.01', 'book.n.01', 'device.n.01', 'tool.n.01',
      'implement.n.01', 'bird.n.01', 'cat.n.01', 'young_mammal.n.01',
      'kitten.n.01', 'puppy.n.01', 'rodent.n.01'}, 0.20),
)


def _closure(word: str, pos: str = 'n', k: int = 2) -> set:
    if _wn is None or not word:
        return set()
    base = _wn.morphy(word, pos) or word
    out = set()
    for s in _wn.synsets(base, pos)[:k]:
        out.add(s.name())
        for path in s.hypernym_paths():
            out.update(h.name() for h in path)
    return out


def _lex(word: str, pos: str = 'n') -> str:
    if _wn is None or not word:
        return ''
    base = _wn.morphy(word, pos) or word
    ss = _wn.synsets(base, pos)
    return ss[0].lexname() if ss else ''


def place_kind(word: str) -> str:
    """The backdrop a place noun calls for ('' when it is not a place)."""
    phrase = str(word or '').lower().strip()
    head = phrase.split()[-1:] or ['']
    head = head[0]
    noun = phrase.replace(' ', '_')
    noun = noun if _lex(noun) else head
    lex = _lex(noun)
    if not head or lex == 'noun.person':
        return ''
    if lex not in ('noun.artifact', 'noun.location', 'noun.object',
                   'noun.group', 'noun.plant'):
        return ''
    cl = _closure(noun, k=1)
    if lex == 'noun.artifact' and cl & (
            _BED | {'furniture.n.01', 'container.n.01'}):
        return ''
    for kind, anchors in _PLACES:
        if cl & anchors:
            return kind
    if cl & {'building.n.01', 'room.n.01', 'facility.n.01'}:
        return phrase
    return ''


def is_surface(word: str) -> bool:
    head = (str(word or '').lower().split() or [''])[-1]
    return bool(_closure(head, k=1) & _SURFACE) and not place_kind(head)


def is_body_part(word: str) -> bool:
    head = (str(word or '').lower().split() or [''])[-1]
    return _lex(head) == 'noun.body' or (
        head.endswith('s') and _lex(head[:-1]) == 'noun.body')


def is_worn(word: str) -> bool:
    head = (str(word or '').lower().split() or [''])[-1]
    return bool(_closure(head, k=1) & _WORN)


def size_of(word: str) -> float:
    head = (str(word or '').lower().split() or [''])[-1]
    cl = _closure(head, k=1)
    for anchors, s in _SIZES:
        if cl & anchors:
            return s
    return 0.34


def _person_ent(e: dict, people: set) -> bool:
    return (e.get('lex') == 'noun.person' or bool(e.get('person'))
            or str(e.get('label') or '').lower() in people)


def is_story_scene(maps: list, people: set = frozenset()) -> bool:
    """Narrative when most of the scene's acts are people's bodies
    moving, touching, eating or feeling — not things standing for,
    flowing to or being exchanged for other things."""
    story = total = explain = 0
    for sm in maps:
        ents = sm['entities']
        for ev in sm['events']:
            if ev['lemma'] == 'be':
                explain += 1
                continue
            total += 1
            ag = ev.get('agent')
            if ag is None or not _person_ent(ents[ag], people):
                explain += 1
                continue
            lem = ev['lemma']
            if (lem in _EMO_VERB or sb_activity.is_physical(lem)
                    or (_wn is not None and _wn.synsets(lem, 'v')
                        and _wn.synsets(lem, 'v')[0].lexname()
                        in _STORY_LEX)):
                story += 1
        for st in sm.get('states') or ():
            if str(st.get('word') or '').lower() in _EMO_ADJ:
                story += 1
                total += 1
    return story >= 1 and story >= explain and story >= 0.45 * max(1, total)


# ---- role list helpers -----------------------------------------------
def _insert(roles: list, at: int, role: dict) -> None:
    for q in roles:
        if isinstance(q.get('to'), int) and q['to'] >= at:
            q['to'] += 1
        t_ = q.get('target')
        if isinstance(t_, int) and not isinstance(t_, bool) and t_ >= at:
            q['target'] = t_ + 1
    roles.insert(at, role)


def _drop(roles: list, k: int) -> None:
    del roles[k]
    for q in roles:
        if isinstance(q.get('to'), int):
            if q['to'] == k:
                q.pop('to')
                q.pop('attach', None)
            elif q['to'] > k:
                q['to'] -= 1
        t_ = q.get('target')
        if isinstance(t_, int) and not isinstance(t_, bool):
            if t_ == k:
                q.pop('target')
            elif t_ > k:
                q['target'] = t_ - 1


def _plural(label: str) -> str:
    head = label.split()[-1]
    pl = _IRREG.get(head) or (head + 'es' if re.search(r'(s|x|ch|sh)$',
                                                       head) else
                              head[:-1] + 'ies' if re.search(
                                  r'[^aeiou]y$', head) else head + 's')
    return ' '.join(label.split()[:-1] + [pl])


class Cast:
    """Script-wide memory of who is who: named people, groups and the
    members a group is made of, and each person's sex for pronouns."""

    def __init__(self):
        self.groups: list = []
        self.place = ''
        self.building = ''    # {'label','n','members','sex','child'}
        self.people: dict = {}    # label -> template role
        self.order: list = []     # labels by last mention
        self.introduced: set = set()

    def note(self, r: dict) -> None:
        lab = r['label']
        if lab not in self.people:
            self.people[lab] = {k: r[k] for k in ('gender', 'age', 'beard',
                                                  'cast_key') if k in r}
        if lab in self.order:
            self.order.remove(lab)
        self.order.append(lab)

    def group_for(self, label: str, n: int, child: bool, sex: str):
        g = next((g for g in self.groups if g['label'] == label), None)
        if g is None:
            g = next((g for g in reversed(self.groups)
                      if g['n'] == n and g['child'] == child
                      and (g['sex'] == sex or not sex or not g['sex'])),
                     None)
            if g is not None:
                g.setdefault('aliases', set()).add(label)
        if g is None:
            members = [lab for lab in self.order if lab != label
                       and lab in self.introduced
                       and '#' not in lab
                       and self.people[lab].get('cast_key', lab) == lab
                       and sb_cast.look_for(dict(
                           self.people[lab], label=lab))['child']
                       and (not sex or self.people[lab].get('gender') == sex)]
            g = {'label': label, 'n': n, 'sex': sex, 'child': child,
                 'members': (members if child and len(members) == n else
                             [f'{label}#{i + 1}' for i in range(n)]),
                 'mods': {}}
            self.groups.append(g)
        return g

    def group_of(self, label: str):
        return next((g for g in self.groups if g['label'] == label
                     or label in g.get('aliases', ())), None)

    def last_group(self):
        return self.groups[-1] if self.groups else None

    def last(self, sex: str = '', but: str = ''):
        for lab in reversed(self.order):
            if lab == but or '#' in lab:
                continue
            if not sex or self.people.get(lab, {}).get('gender') == sex:
                return lab
        for lab in reversed(self.order):
            if lab != but and '#' not in lab and sb_cast.lexical_sex(
                    lab) == '' and not self.people.get(lab, {}).get('gender'):
                return lab
        return ''


def _emotion(sm: dict, eid_ok, sent: str) -> str:
    found = []
    for ev in sm['events']:
        if ev.get('agent') is not None and eid_ok(ev['agent']):
            e_ = _EMO_VERB.get(ev['lemma'])
            if e_ == 'sleep' or ev['lemma'] == 'fall' and re.search(
                    r'\bfalls?\s+asleep\b|\bfell\s+asleep\b', sent, re.I):
                e_ = 'sleep'
            if e_:
                found.append(e_)
    for st in sm.get('states') or ():
        if eid_ok(st.get('of')):
            e_ = _EMO_ADJ.get(str(st.get('word') or '').lower())
            if e_:
                found.append(e_)
    for m in _WITH_FEEL.finditer(sent):
        found.append(_WITH_EMO[m.group(3).lower()])
    found = [f for f in found if f in _EMO_RANK]
    if not found:
        return ''
    if 'sleep' in found:
        return 'sleep'
    return min(found, key=_EMO_RANK.index)


def stage(sc: dict, maps: list, sents: list, cast: Cast,
          icon_for=None) -> None:
    """Complete every moment of a story scene in place (see module doc)."""
    rs = [sc['heroRole']] + sc['supportingRoles']
    for r in rs:
        if r.get('icon') == 'person':
            cast.note(r)
            r.pop('annotate', None)
            target = r.get('to')
            if r.get('attach') in ('beside', 'near', 'with') \
                    and isinstance(target, int) \
                    and rs[target].get('icon') == 'person':
                r.pop('attach')
                r.pop('to')
    by_k = {int(sm.get('_k', 0)): sm for sm in maps}
    places: list = []
    posture: dict = {}
    for k in range(len(sents)):
        sent = sents[k]
        sm = by_k.get(k)
        low = sent.lower()

        def mom():
            return [i for i, r in enumerate(rs)
                    if int(r.get('moment') or 0) == k]

        def people_here():
            return [i for i in mom() if rs[i].get('icon') == 'person']

        def ensure(label, template=None):
            alias = cast.people.get(label, {}).get('cast_key')
            for i in people_here():
                if label in (rs[i]['label'], rs[i].get('cast_key')) or (
                        alias and alias in (rs[i]['label'],
                                            rs[i].get('cast_key'))):
                    return i
            base = dict(cast.people.get(label, {}))
            base.update(template or {})
            nr = {'label': label, 'icon': 'person', 'narration': sent,
                  'moment': k, **base}
            at = max(mom() + [len(rs) - 1]) + 1 if mom() else len(rs)
            _insert(rs, at, nr)
            cast.note(nr)
            return at

        # 1. everyone the sentence's acts involve is in the picture
        if sm is not None:
            ents = sm['entities']
            known = set(cast.people)
            for ev in sm['events']:
                for eid in [ev.get('agent'), ev.get('patient')] + [
                        e for _p, e in ev['preps']]:
                    if eid is None:
                        continue
                    lab = str(ents[eid].get('label') or '')
                    if lab in known and '#' not in lab:
                        had = any(rs[i]['label'] == lab
                                  for i in people_here())
                        i = ensure(lab)
                        if not had and eid == ev.get('agent'):
                            _own_act(rs[i], ev, ents, [rs[j] for j in mom()])
            # '... in the kitchen with his captain': present, if not acting
            for e_ in ents:
                lab = str(e_.get('label') or '')
                if lab in known and '#' not in lab and not e_.get('pron') \
                        and e_.get('lex') == 'noun.person':
                    ensure(lab)
        cast.introduced.update(rs[i]['label'] for i in people_here())
        # 2. groups: 'two boys', 'the boys', 'them both'
        for i in list(people_here()):
            r = rs[i]
            lab = r['label']
            pl = _plural(lab)
            m = re.search(r'\b(?:(\w+)\s+)?(?:(\w+)\s+)?' + re.escape(pl)
                          + r'\b', low)
            if not m:
                continue
            n = next((_NUM[w] for w in (m.group(1), m.group(2))
                      if w and w in _NUM), None)
            g = cast.group_of(lab)
            if n is None:
                n = g['n'] if g else 2
            lk = sb_cast.look_for(r)
            sex = r.get('gender') or sb_cast.lexical_sex(lab)
            g = cast.group_for(lab, n, lk['child'], sex)
            r['group'] = g['label']
        # a collective ('the crew', 'the family') is several people
        for i in list(people_here()):
            r = rs[i]
            if r.get('group') or not scene_map.people_group(r['label']):
                continue
            g = cast.group_for(r['label'], 3, False, '')
            r['group'] = g['label']
        # 'them' / 'both' / 'their' with no plural noun: the last group
        g_last = cast.last_group()
        if g_last and _PLURAL_PRO.search(low) and not any(
                rs[i].get('group') for i in people_here()):
            tmpl = next((dict(cast.people[mb]) for mb in g_last['members']
                         if mb in cast.people), {})
            i = ensure(g_last['label'], dict(tmpl, group=g_last['label']))
            rs[i]['group'] = g_last['label']
            rs[i].pop('activity', None)
            rs[i].pop('annotate', None)
        # one member: 'the older boy'
        for mm in _MEMBER_RE.finditer(sent):
            mod, noun = mm.group(1).lower(), mm.group(2).lower()
            lab = (_wn.morphy(noun, 'n') if _wn else None) or noun
            g = cast.group_of(lab)
            if g is None and _lex(lab) == 'noun.person':
                # 'the younger girl' of 'his two granddaughters'
                sx = sb_cast.lexical_sex(lab)
                g = next((g_ for g_ in reversed(cast.groups)
                          if not sx or not g_['sex'] or g_['sex'] == sx),
                         None)
                if g is not None:
                    g.setdefault('aliases', set()).add(lab)
            if g is None or noun != lab:
                continue
            mod = ('older' if mod in _OLDER else
                   'younger' if mod in _YOUNGER else mod)
            idx = g['mods'].get(mod)
            if idx is None:
                used = set(g['mods'].values())
                pref = (0 if mod in _OLDER else len(g['members']) - 1
                        if mod in _YOUNGER else None)
                free = [j for j in range(len(g['members'])) if j not in used]
                if not free:
                    continue
                idx = pref if pref in free else free[0]
                g['mods'][mod] = idx
            for i in people_here():
                r = rs[i]
                words = r['label'].split()
                qualified = len(words) > 1 and words[-1] == lab \
                    and words[0] == mm.group(1).lower()
                unbound = r.get('cast_key') not in g['members']
                if (qualified or r['label'] == lab and unbound) \
                        and not r.get('group'):
                    if qualified:
                        r['aliases'] = sorted(set(
                            r.get('aliases', ())) | {r['label']})
                        r['label'] = lab
                    r['cast_key'] = g['members'][idx]
                    r['member_rank'] = ('older' if mod in _OLDER else
                                        'younger' if mod in _YOUNGER else '')
                    cast.people.setdefault(r['cast_key'], {
                        kk: r[kk] for kk in ('gender', 'age') if kk in r})
        # 3. body parts, surfaces, places, beds, substances
        for i in sorted(mom(), reverse=True):
            r = rs[i]
            if r.get('icon') == 'person':
                continue
            lab = r['label']
            act = next((a.get('activity') or {} for a in rs
                        if a.get('moment') == r.get('moment')
                        and (a.get('activity') or {}).get('partner') == lab),
                       {})
            head = lab.split()[-1]
            artifact_sense = _wn is not None and any(
                s.lexname() == 'noun.artifact'
                for s in _wn.synsets(head, 'n')[:3])
            carried_artifact = (artifact_sense
                                and act.get('schema') in ('carry', 'hold')
                                and not re.search(
                                    r'\b(her|his|their|own)\s+'
                                    + re.escape(lab) + r'\b',
                                    r.get('narration', ''), re.I))
            if is_body_part(lab) and not carried_artifact:
                r['body_part'] = True
            elif is_worn(lab) and people_here():
                # 'pulls on his boots': on the body, not beside it
                r['worn'] = True
            elif is_surface(lab):
                r['surface'] = True
            else:
                pk = place_kind(lab)
                if pk:
                    r['place'] = pk
            if not (r.get('body_part') or r.get('surface') or r.get('place')):
                r.setdefault('size', size_of(lab))
            head = lab.split()[-1]
            acts = sm is not None and any(
                ev.get('agent') is not None and str(
                    sm['entities'][ev['agent']].get('label') or '') == lab
                for ev in sm['events'])
            if acts:
                # 'the alarm rings': a thing that acts is drawn
                pass
            elif head in _WITH_EMO or _lex(head) in ('noun.feeling',
                                                   'noun.time') or re.search(
                    r'\b(after|before|during|since|until|by)\s+(the\s+)?'
                    + re.escape(lab) + r'\b', low):
                _drop(rs, i)
        # where this moment happens: its own place word, else the last one
        pk = ''
        # 'bread from her bakery' names where it came from, not where we are
        here_ = re.sub(r"\bfrom\s+(?:the\s+|an?\s+|her\s+|his\s+|their\s+"
                       r"|my\s+|our\s+)?(?:\w+\s+)?\w+", ' ', low)
        ambient_outside = sm is not None and any(
            ev['agent'] is not None
            and sm['entities'][ev['agent']].get('lex') == 'noun.phenomenon'
            and any(p == 'outside' for p, _e in ev.get('preps') or ())
            for ev in sm['events'])
        if ambient_outside:
            here_ = _OUTSIDE.sub(' ', here_)
            for ev in sm['events']:
                if ev['agent'] is None or ents[ev['agent']].get(
                        'lex') != 'noun.phenomenon':
                    continue
                weather = next((i for i in mom() if rs[i]['label']
                                == ents[ev['agent']]['label']), None)
                window_label = next((ents[eid]['label']
                                     for prep, eid in ev.get('preps') or ()
                                     if prep == 'outside'
                                     and ents[eid].get('head') == 'window'), '')
                window = next((i for i in mom()
                               if rs[i]['label'] == window_label), None)
                if weather is not None and window is not None:
                    rs[weather]['attach'] = 'in'
                    rs[weather]['to'] = window
                    rs[weather]['setting_detail'] = True
        person_labels = {r['label'] for r in rs
                         if r.get('icon') == 'person'}
        person_words = {word for label in person_labels for word in
                        re.findall(r"[a-z]+", label)}
        nouns = [e['label'] for e in sm['entities']
                 if e['label'] in here_ and e['label'] not in person_labels
                 and e.get('lex') != 'noun.person'] if sm is not None else []
        nouns += [word for word in re.findall(r"[a-z]+", here_)
                  if word not in person_words]
        for w in nouns:
            k_ = place_kind(w) if len(w) > 3 else ''
            if k_ and (not pk or pk == 'home'):
                pk = k_
        if not pk:
            for i in mom():
                pk = pk or _room_of(rs[i]['label'])
        prev = places[-1] if places else cast.place
        if pk and pk not in ('outdoor', 'street'):
            cast.building = pk
        if _OUTSIDE.search(low) and not ambient_outside:
            pk = 'street' if _STREETY.search(low) else 'outdoor'
        elif _INSIDE.search(low) and pk in ('', 'outdoor', 'street'):
            pk = cast.building or prev
        if pk in ('', 'home') and prev and prev not in ('outdoor', 'store',
                                                        'street'):
            pk = prev if not pk or prev != 'home' else pk
        places.append(pk or prev)
        cast.place = places[-1]
        # 4. people's acts on each other and on their own bodies
        if sm is not None:
            ents = sm['entities']

            def lab_of(eid):
                return str(ents[eid].get('label') or '') if eid is not None \
                    else ''

            def role_of(label):
                return next((i for i in people_here()
                             if rs[i]['label'] == label
                             or rs[i].get('cast_key') == label
                             or label in rs[i].get('aliases', ())), None)

            for ev in sm['events']:
                ai = role_of(lab_of(ev.get('agent')))
                if ai is None:
                    continue
                pat = ev.get('patient')
                plab = lab_of(pat)
                pi = role_of(plab) if plab != rs[ai]['label'] else None
                phr = str(ev.get('phrase') or '').lower()
                if pi is None and (_PLURAL_PRO.search(phr) or (
                        pat is not None and ents[pat].get('pron')
                        and plab == rs[ai]['label'])):
                    pi = next((i for i in people_here()
                               if rs[i].get('group')), None)
                if pi is None:
                    # 'reads them a story': the listeners
                    to_ = next((e for p_, e in ev['preps'] if p_ == 'to'),
                               None)
                    if to_ is not None and lab_of(to_) != rs[ai]['label']:
                        pi = role_of(lab_of(to_))
                    elif to_ is not None and ents[to_].get('pron'):
                        pi = next((i for i in people_here()
                                   if rs[i].get('group')), None)
                if pi is None and ev['lemma'] in _HOLD_VERBS \
                        and plab and _lex(plab.split()[-1]) == 'noun.animal':
                    pi = next((i for i in mom() if rs[i]['label'] == plab),
                              None)
                if pat is not None and is_body_part(plab):
                    if re.search(r'\b(her|his|their)\s+(own\s+)?'
                                 + re.escape(plab), phr) and re.search(
                                     r'\btheir\b', phr) and pi is None:
                        pi = next((i for i in people_here()
                                   if rs[i].get('group')), None)
                    if pi is None and ev['lemma'] in (
                            'hold', 'clutch', 'grab', 'rub', 'hide',
                            'bury', 'shake', 'scratch'):
                        rs[ai]['emotion'] = 'stressed'
                        rs[ai].pop('action', None)
                if pi is not None and pi != ai:
                    rs[ai]['touch'] = sorted(set(rs[ai].get('touch', []))
                                             | {rs[pi].get('group')
                                                or rs[pi].get('cast_key')
                                                or rs[pi]['label']})
                    rs[ai]['target'] = pi
                    if ev['lemma'] in _HOLD_VERBS:
                        rs[ai]['action'] = 'offer'
                    elif not rs[ai].get('activity'):
                        rs[ai].setdefault('action', 'reach')
                    bed = next((e for p_, e in ev['preps']
                                if p_ in ('into', 'in', 'onto', 'on')
                                and _closure(lab_of(e), k=1) & _BED), None)
                    if bed is not None:
                        rs[pi]['activity'] = {'schema': 'lie', 'kind': '',
                                              'via': 'story:put-in-bed',
                                              'lemma': 'lie'}
                        rs[pi]['emotion'] = rs[pi].get('emotion') or 'calm'
                        rs[ai].pop('activity', None)
                        rs[ai]['action'] = 'reach'
            # 'sits on her lap' / 'sleeps in his arms'
            for mm in _POSS.finditer(sent):
                who, part = mm.group(2), mm.group(4).lower()
                near = sorted(((low.rfind(rs[i]['label'], 0, mm.start()), i)
                               for i in people_here()), reverse=True)
                sitter = near[0][1] if near and near[0][0] >= 0 else None
                if sitter is None:
                    continue
                mid = (mm.group(3) or '').strip().lower()
                if mid.endswith("'s"):
                    # 'on his captain's shoulder': the captain's
                    owner = mid[:-2]
                elif who.lower() in ('her', 'his', 'their'):
                    sex = {'her': 'f', 'his': 'm'}.get(who.lower(), '')
                    owner = cast.last(sex, but=rs[sitter]['label'])
                else:
                    owner = who[:-2].lower()
                if not owner:
                    continue
                oi = ensure(owner)
                if oi == sitter:
                    # 'taps the rhythm on his knee': their own body
                    continue
                if part.startswith(('shoulder', 'back')):
                    # 'asleep on his captain's shoulder': leaning on them
                    rs[sitter]['touch'] = sorted(set(
                        rs[sitter].get('touch', [])) | {owner})
                    rs[sitter]['lean_on'] = owner
                    rs[sitter].pop('action', None)
                    continue
                if part == 'arms':
                    # 'her daughter in her arms': carried, not sat on
                    rs[oi].pop('activity', None)
                    rs[oi]['stance'] = 'stand'
                    rs[oi]['action'] = 'offer'
                    sr = rs[sitter]
                    sr.pop('activity', None)
                    sr.pop('stance', None)
                    sr.pop('action', None)
                    sr['lap_of'] = owner
                    sr['held'] = True
                    sr.pop('annotate', None)
                    continue
                rs[oi]['activity'] = {'schema': 'sit', 'kind': '',
                                      'via': 'story:lap', 'lemma': 'sit'}
                rs[oi]['stance'] = 'sit'
                rs[oi].setdefault('emotion', 'love')
                sr = rs[sitter]
                act = sr.pop('activity', None) or {}
                sr['stance'] = 'sit'
                if act.get('schema') in ('sit_drink', 'drink', 'eat'):
                    sr['action'] = 'drink'
                elif act.get('schema') in ('sit_read', 'read'):
                    sr['action'] = 'read'
                else:
                    sr.pop('action', None)
                sr['lap_of'] = owner
                sr.pop('annotate', None)
        # 5. feelings of each person in the moment
        if sm is not None:
            ents = sm['entities']
            for i in people_here():
                r = rs[i]
                names = {r['label'], r.get('cast_key') or ''} \
                    | set(r.get('aliases') or ())

                def ok(eid, names=names):
                    return eid is not None and str(
                        ents[eid].get('label') or '') in names
                emo = _emotion(sm, ok, sent)
                if emo and not (r.get('emotion') == 'stressed'
                                and emo in ('tired', 'sad')):
                    r['emotion'] = emo
                if emo == 'sleep' and r.get('lean_on'):
                    # dozing against someone: still sitting beside them
                    r['activity'] = {'schema': 'sit', 'kind': '',
                                     'via': 'story:asleep', 'lemma': 'sit'}
                elif emo == 'sleep':
                    r['activity'] = {'schema': 'lie', 'kind': '',
                                     'via': 'story:asleep', 'lemma': 'lie'}
        # 6. a posture holds until the story changes it
        for i in people_here():
            r = rs[i]
            ident = r.get('group') or r.get('cast_key') or r['label']
            sch = (r.get('activity') or {}).get('schema')
            if sch in ('lie', 'sit') and r.get('activity', {}).get(
                    'via', '').startswith('story:'):
                posture[ident] = r['activity']
            elif sch is None and ident in posture and not r.get('lap_of') \
                    and r.get('stance') not in ('walk',):
                r['activity'] = dict(posture[ident])
            elif sch is not None:
                posture.pop(ident, None)
    # substances with no drawing of their own are drawn in their container
    if icon_for is not None:
        for r in rs:
            if r.get('icon') == 'person' or r.get('place') \
                    or r.get('attach') == 'held':
                continue
            head = r['label'].split()[-1]
            if _lex(head) not in ('noun.food', 'noun.substance'):
                continue
            ic = icon_for(r['label'])
            name = str(ic[2] if isinstance(ic, tuple) and len(ic) > 2
                       else ic).lower()
            liquid = bool(_closure(head, k=1) & _LIQUID)
            if head[:4] in name.replace('-', ' ') and not (
                    liquid and not _CONTAINER.search(name)):
                continue
            r['icon'] = 'jug' if liquid else 'bag'
            r['container_for'] = r['label']
    # a bed or seat a posture already draws is not drawn twice
    for r in rs:
        if r.get('icon') == 'person':
            continue
        k_ = r.get('moment')
        sch = {(q.get('activity') or {}).get('schema') for q in rs
               if q.get('icon') == 'person' and q.get('moment') == k_}
        cl = _closure(r['label'].split()[-1], k=1)
        if r.get('attach') != 'activity' and (('lie' in sch and cl & _BED)
                or ('sit' in sch and cl & {
                'seat.n.03', 'chair.n.01', 'sofa.n.01', 'bench.n.01'})):
            r['absorbed'] = True
    # a group is drawn member by member
    for i in range(len(rs) - 1, -1, -1):
        r = rs[i]
        g = cast.group_of(r.get('group') or '') if r.get('group') else None
        if g is None:
            continue
        r['cast_key'] = g['members'][0]
        rank = {v: k_ for k_, v in g['mods'].items()}
        r['member_rank'] = _rank(rank.get(0))
        for j, mb in enumerate(g['members'][1:], 1):
            cp = copy.deepcopy(r)
            cp['cast_key'] = mb
            cp['member_rank'] = _rank(rank.get(j))
            cp.pop('annotate', None)
            _insert(rs, i + j, cp)
    shared = {}
    for r in rs:
        act = r.get('activity') or {}
        if r.get('icon') == 'person' and act.get('schema') in (
                'carry', 'hold', 'desk') and act.get('partner'):
            shared.setdefault((r.get('moment'), act['partner']), []).append(r)
    for (moment, partner), actors in shared.items():
        prop = next((r for r in rs if r.get('moment') == moment
                     and r['label'] == partner and int(r.get('count') or 1) == 1
                     and isinstance(r.get('to'), int)), None)
        if len(actors) != 2 or prop is None:
            continue
        primary = rs[prop['to']]
        if not any(primary is r for r in actors):
            continue
        helper = next(r for r in actors if r is not primary)
        primary['shared_with'] = helper.get('cast_key') or helper['label']
        helper['shared_with'] = primary.get('cast_key') or primary['label']
        primary['touch'] = sorted(set(primary.get('touch') or ())
                                  | {primary['shared_with']})
        helper['touch'] = sorted(set(helper.get('touch') or ())
                                 | {helper['shared_with']})
        helper['activity']['shared_partner'] = partner
        if helper['activity'].get('roles'):
            helper['activity']['shared_roles'] = helper['activity'].pop('roles')
    # a member keeps its own look ('boy#2') and its sex from the word
    for r in rs:
        if r.get('icon') == 'person':
            identity = cast.people.get(r.get('cast_key'), {})
            for key in ('gender', 'age', 'beard'):
                if key in identity:
                    r.setdefault(key, identity[key])
            lk = sb_cast.look_for({'label': r['label']})
            word_sex = sb_cast._FEMALE.search(r['label']) or \
                sb_cast._MALE.search(r['label'])
            if word_sex:
                r['gender'] = lk['sex']
    # the picture shows what people do; a sentence-fragment caption on a
    # person only restates (or misnames) it
    for r in rs:
        if r.get('icon') == 'person':
            r.pop('annotate', None)
    sc['heroRole'], sc['supportingRoles'] = rs[0], rs[1:]
    sc['places'] = places
    sc['mode'] = 'story'
    sc['relation'] = 'story'
    sc['composition'] = 'stage'
    sc.pop('layout', None)
    sc.pop('graph', None)


_CONTAINER = re.compile(r'(jug|bottle|glass|carton|cup|mug|jar|can|pitcher|'
                        r'kettle|pot|bucket|flask)')
# furniture that names the room it stands in
_ROOMS = (('bedroom', _BED), ('kitchen', {'stove.n.02', 'oven.n.01',
          'refrigerator.n.01', 'sink.n.01', 'dishwasher.n.01'}),
          ('living', {'sofa.n.01', 'television_receiver.n.01',
                      'fireplace.n.01', 'armchair.n.01'}),
          ('store', {'shopping_cart.n.01', 'cash_register.n.01',
                     'cashier.n.01'}),
          ('office', {'desk.n.01', 'computer.n.01'}),
          ('classroom', {'blackboard.n.01'}))


def _room_of(label: str) -> str:
    cl = _closure(str(label).split()[-1], k=1)
    return next((k for k, a in _ROOMS if cl & a), '')


def _own_act(r: dict, ev: dict, ents: list, here: list) -> None:
    """The body act of a person the planner left out of a moment."""
    def lab(eid):
        return str(ents[eid].get('label') or '')
    objs = ([('dobj', lab(ev['patient']))] if ev.get('patient') is not None
            else []) + [(p_, lab(e)) for p_, e in ev['preps']]
    spec = sb_activity.resolve(ev['lemma'], objs, '')
    if spec is None:
        return
    r['activity'] = {k: spec[k] for k in ('schema', 'kind', 'via', 'lemma')}
    part = next((q for q in here if q.get('icon') != 'person'
                 and q['label'] == spec.get('partner')), None)
    if part is not None and 'attach' not in part:
        r['activity']['partner'] = part['label']
        part['absorbed'] = True


def _rank(mod):
    return ('older' if mod in _OLDER else 'younger' if mod in _YOUNGER
            else '')
