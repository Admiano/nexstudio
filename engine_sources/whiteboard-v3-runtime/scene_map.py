"""Scene map: what a sentence says happens, as data.

A dependency parse (spaCy, MIT, local) turns each narration sentence into
entities (who/what, with their state), events (who does what to whom, toward
where, which way) and states (empty, broken, tired). Event kinds come from the
verb's WordNet hypernyms, so any verb in any niche lands in one of a small set
of depictable kinds without per-word lists:

    rise / fall   change of amount or height   (jumps, soars, crashes, tanks)
    destroy       ruin, loss, death            (wipes out, breaks, dies)
    transfer      giving, buying, sending      (buys, sells, hands)
    move          travel toward/away           (drifts, races, climbs)
    think         cognition                    (thinks, wonders, plans)
    fear          alarm                        (panics, dreads)
    feel          other emotion                (cheers, hopes, worries)
    act           any other doing              (lights, pulls, sips)

`parse()` returns None when no parser is installed; callers fall back.
"""
from __future__ import annotations

import functools

try:
    from nltk.corpus import wordnet as _wn
    _wn.synsets('dog')
except Exception:  # pragma: no cover - WordNet missing
    _wn = None

KINDS = ('rise', 'fall', 'destroy', 'transfer', 'move', 'think', 'fear',
         'feel', 'say', 'perceive', 'act')

_UP = {'increase.v.01', 'increase.v.02', 'rise.v.01', 'rise.v.02',
       'ascend.v.01', 'grow.v.01', 'grow.v.02', 'better.v.02'}
_DOWN = {'decrease.v.01', 'decrease.v.02', 'descend.v.01', 'fall.v.01',
         'fall.v.03', 'sink.v.01', 'worsen.v.01', 'worsen.v.02'}
_RUIN = {'destroy.v.01', 'destroy.v.02', 'damage.v.01', 'kill.v.01',
         'die.v.01', 'lose.v.01', 'lose.v.02', 'ruin.v.02', 'fail.v.04',
         'eliminate.v.03', 'break.v.02', 'break.v.03', 'consume.v.05',
         'wipe_out.v.03', 'collapse.v.01', 'crash.v.01'}
_GIVE = {'transfer.v.05', 'transfer.v.02', 'give.v.03', 'give.v.01',
         'get.v.01', 'sell.v.01', 'buy.v.01', 'pay.v.01', 'lend.v.01',
         'borrow.v.01'}
_THINK = {'imagine.v.01', 'dream.v.01', 'daydream.v.01', 'think.v.01',
          'think.v.03', 'plan.v.01', 'wonder.v.01', 'hope.v.01',
          'wish.v.01', 'believe.v.01', 'remember.v.01', 'decide.v.01',
          'worry.v.01', 'forget.v.01', 'consider.v.01', 'reflect.v.01'}
@functools.lru_cache(maxsize=None)
def people_group(label: str) -> bool:
    """A collective of people ('crew', 'family'), not an arrangement
    ('table', 'array') or a herd."""
    head = (str(label or '').lower().split() or [''])[-1]
    if _wn is None or not head:
        return False
    for s in _wn.synsets(_wn.morphy(head, 'n') or head, 'n')[:1]:
        return any(h.name() == 'social_group.n.01'
                   for path in s.hypernym_paths() for h in path)
    return False


# nouns that go up and down as amounts, not as bodies in space
_AMOUNT_LEX = {'noun.attribute', 'noun.quantity', 'noun.possession',
               'noun.communication', 'noun.act', 'noun.state',
               'noun.relation', 'noun.group'}
_ASPECT_STOP = {'stop', 'cease', 'quit', 'fail', 'refuse'}
_FEAR = {'fear.v.01', 'fear.v.02', 'fear.v.03', 'fear.v.04'}
# adjectives that say a thing is lost or spent (closed class)
_PRIVATIVE = {'empty', 'dead', 'lost', 'gone', 'broken', 'ruined', 'bankrupt',
              'destroyed', 'wrecked', 'bare', 'dry', 'drained', 'shattered',
              'failed', 'burnt', 'burned', 'crushed', 'sunk', 'stranded'}
_COLOUR = {'red', 'green', 'blue', 'yellow', 'black', 'white', 'orange',
           'purple', 'pink', 'brown', 'grey', 'gray', 'golden', 'silver'}
_COPULA = {'be', 'feel', 'look', 'seem', 'become', 'get', 'stay', 'remain',
           'grow', 'turn', 'appear', 'sound', 'go', 'fall'}
_LIGHT = {'be', 'have', 'do', 'get', 'go', 'make', 'let', 'try', 'start',
          'begin', 'keep', 'want', 'need'}
_PEOPLE_PRON = {'he', 'she', 'they', 'i', 'you', 'we', 'him', 'her', 'them',
                'me', 'us'}


_MODELS = ('en_core_web_lg', 'en_core_web_md', 'en_core_web_sm')


@functools.lru_cache(maxsize=1)
def _nlps() -> tuple:
    try:
        import spacy
    except Exception:
        return ()
    out = []
    for name in _MODELS:
        try:
            out.append(spacy.load(name))
        except Exception:
            continue
    return tuple(out)


def available() -> bool:
    return bool(_nlps())


def _clause_score(doc) -> int:
    """Parses disagree on '-s' words ('the price jumps', 'a trader sips
    coffee'); prefer the one whose root is a verb and whose verbs have
    subjects."""
    root = next((t for t in doc if t.dep_ == 'ROOT'), None)
    verbs = [t for t in doc if t.pos_ == 'VERB']
    subj = sum(1 for v in verbs if any(
        c.dep_ in ('nsubj', 'nsubjpass') for c in v.children))
    plural_mod = sum(1 for t in doc if t.dep_ == 'compound'
                     and t.tag_ == 'NNS')
    # 'her reading glasses': a possessive is never a clause subject
    poss_subj = sum(1 for t in doc if t.dep_ == 'nsubj' and t.tag_ == 'PRP$')
    return (3 if root is not None and root.pos_ in ('VERB', 'AUX') else 0) \
        + 2 * subj + len(verbs) - 3 * plural_mod - 4 * poss_subj


@functools.lru_cache(maxsize=2048)
def _parse_doc(sentence: str):
    best = None
    for nlp in _nlps():
        doc = nlp(sentence)
        sc = _clause_score(doc)
        if best is None or sc > best[0]:
            best = (sc, doc)
    return best[1] if best else None


@functools.lru_cache(maxsize=4096)
def _closure(lemma: str) -> frozenset:
    if _wn is None:
        return frozenset()
    out = set()
    for s in _wn.synsets(lemma, 'v')[:4]:
        out.add(s.name())
        out |= {h.name() for h in s.closure(lambda x: x.hypernyms())}
    return frozenset(out)


_PHYS_VERB = ('verb.contact', 'verb.motion', 'verb.possession',
              'verb.consumption', 'verb.creation', 'verb.change')
_PHYS_NOUN = {'noun.artifact', 'noun.food', 'noun.plant', 'noun.animal',
              'noun.object', 'noun.person', 'noun.body', 'noun.substance',
              'noun.communication'}


@functools.lru_cache(maxsize=4096)
def verb_kind(lemma: str, particle: str = '', amount: bool = False,
              physical: bool = False) -> tuple[str, str]:
    """(kind, direction) for a verb lemma (+ particle: 'wipe out').
    `amount`: the subject is an amount (a price, sales, a chart), so any
    sense of the verb that raises or lowers a quantity applies; a body in
    space only takes the verb's first sense. `physical`: the verb acts on a
    physical thing, so its first hands-on sense leads ('picks grapes' is
    plucking, not choosing)."""
    if _wn is None:
        return 'act', ''
    lem = f'{lemma}_{particle}' if particle and _wn.synsets(
        f'{lemma}_{particle}', 'v') else lemma
    syns = _wn.synsets(lem, 'v')
    if physical:
        hands = [x for x in syns[:4] if x.lexname() in _PHYS_VERB]
        syns = hands[:1] + [x for x in syns if x not in hands[:1]]
    lex = syns[0].lexname() if syns else ''
    first = frozenset({syns[0].name()} | {h.name() for h in syns[0].closure(
        lambda x: x.hypernyms())}) if syns else frozenset()
    allc = _closure(lem)
    if particle in ('up', 'down') and lemma in ('go', 'move', 'shoot',
                                                'come', 'head', 'climb'):
        return ('rise', 'up') if particle == 'up' else ('fall', 'down')
    if first & _RUIN or (allc & _RUIN and lex in ('verb.contact',
                                                  'verb.creation')):
        return 'destroy', 'down'
    if first & _FEAR or (lex == 'verb.emotion' and allc & _FEAR):
        return 'fear', ''
    up, down = bool(allc & _UP), bool(allc & _DOWN)
    if first & _UP and not first & _DOWN:
        return 'rise', 'up'
    if first & _DOWN and not first & _UP:
        return 'fall', 'down'
    if amount and up != down:
        return ('rise', 'up') if up else ('fall', 'down')
    if allc & _RUIN and lex in ('verb.change', 'verb.motion'):
        return 'destroy', 'down'
    if lex == 'verb.possession' and (first & _GIVE or allc & _GIVE):
        return 'transfer', ''
    if first & _THINK and lex in ('verb.cognition', 'verb.creation',
                                  'verb.perception', 'verb.emotion'):
        return 'think', ''
    if lex == 'verb.cognition':
        return 'perceive', ''
    if lex == 'verb.emotion':
        return 'feel', ''
    if lex == 'verb.communication':
        return 'say', ''
    if lex == 'verb.perception':
        return 'perceive', ''
    if lex == 'verb.motion' or 'travel.v.01' in first:
        return 'move', ''
    return 'act', ''


def state_kind(adj: str) -> str:
    a = adj.lower()
    if a in _PRIVATIVE:
        return 'ruin'
    if a in _COLOUR:
        return 'colour'
    if _wn is not None:
        v = _wn.morphy(a, 'v')
        if v and v != a and verb_kind(v)[0] == 'destroy':
            return 'ruin'
    return 'quality'


def _noun_lex(lemma: str) -> str:
    if _wn is None:
        return ''
    s = _wn.synsets(lemma, 'n')
    return s[0].lexname() if s else ''


def _is_piece(lemma: str) -> bool:
    """'nugget', 'piece', 'drop': a word naming a bit of some material."""
    if _wn is None:
        return False
    s = _wn.synsets(lemma, 'n')[:1]
    return bool(s) and (s[0].lexname() in ('noun.object', 'noun.shape',
                                            'noun.part')
                        or any(h.name() in ('part.n.02', 'part.n.03')
                               for p in s[0].hypernym_paths() for h in p))


def _lemma_count(word: str) -> int:
    return sum(x.count() for syn in _wn.synsets(word, 'n')
               for x in syn.lemmas() if x.name() == word)


def _noun_head(t) -> str:
    """Noun lemma, keeping plurals that are their own word ('stairs',
    'clothes') but not rare plural senses ('letters' = literature)."""
    head = t.lemma_.lower()
    low = t.lower_
    if _wn is None or t.pos_ != 'NOUN' or low == head:
        return head
    if _wn.morphy(low, 'n') == low and (
            not _wn.synsets(head, 'n')
            or _lemma_count(low) > _lemma_count(head)
            or (_noun_lex(low) == 'noun.artifact'
                and _noun_lex(head) != 'noun.artifact')):
        return low
    return head


def parse(sentence: str, carry: dict | None = None) -> dict | None:
    """Scene map for one sentence. `carry` holds the last person/thing for
    pronouns across sentences and is updated in place."""
    doc = _parse_doc(sentence)
    if doc is None:
        return None
    carry = carry if carry is not None else {}
    ents: list[dict] = []
    by_tok: dict[int, int] = {}

    def misread(t) -> bool:
        # 'buy the same token': a determined verb argument is a noun
        return t.pos_ == 'VERB' and t.dep_ in ('dobj', 'pobj', 'attr') \
            and any(c.dep_ in ('det', 'amod', 'poss') for c in t.children)

    def verbal(t) -> bool:
        if t.pos_ in ('VERB', 'AUX'):
            return not misread(t)
        if t.pos_ != 'NOUN':
            return False
        nxt = t.nbor(1) if t.i + 1 < len(t.doc) else None
        if _bare_verb(t, nxt):
            return True
        clause = t.dep_ in ('conj', 'ROOT') or (
            t.dep_ == 'nsubj' and nxt is not None and nxt.dep_ == 'cc'
            and any(c.dep_ == 'nsubj' and c.i > t.i for c in t.head.children))
        if not clause:
            return False
        if any(c.dep_ == 'nsubj' for c in t.children):
            return True
        # a list item ('buckets, mops, and cardboard boxes') stays a noun
        if t.dep_ == 'conj' and t.head.pos_ in ('NOUN', 'PROPN') \
                and not verbal(t.head):
            return False
        # 'the alarm rings and ...': a 3rd-person verb read as a noun
        return (t.tag_ == 'NNS' and _wn is not None
                and (_wn.morphy(t.lower_, 'v') or t.lower_) != t.lower_
                and any(c.dep_ == 'compound' for c in t.children))

    def _bare_verb(t, nxt) -> bool:
        # 'rocks fly ... and land in', 'lava flows ... and stops before',
        # 'her seismograph jump.': a verb the tagger read as a noun
        if _wn is None or any(c.dep_ in ('det', 'amod', 'nummod')
                              for c in t.children):
            return False
        base = _wn.morphy(t.lower_, 'v')
        if not base:
            return False
        root = t.sent.root
        if t.dep_ == 'conj' and t.i and t.nbor(-1).lower_ == 'and' \
                and nxt is not None and nxt.pos_ in ('ADP', 'DET', 'ADV'):
            return (root.tag_ == 'VBZ' and t.lower_.endswith('s')
                    and base != t.lower_) or (
                root.tag_ in ('VBP', 'VB') and base == t.lower_)
        return (nxt is None or nxt.pos_ == 'PUNCT') and base == t.lower_ \
            and any(c.dep_ == 'poss' for c in t.children) \
            and any(c.dep_ == 'compound' for c in t.children)

    def mod_of_verbal(t) -> bool:
        return t.dep_ == 'compound' and verbal(t.head)

    for t in doc:
        if t.dep_ in ('nmod', 'amod') and t.pos_ == 'NOUN' \
                and t.head.i == t.i + 1 and t.head.pos_ == 'NOUN':
            continue
        if (t.dep_ == 'compound' and not mod_of_verbal(t)) or verbal(t) or (
                t.dep_ == 'poss' and t.pos_ not in ('NOUN', 'PROPN')):
            continue
        low = t.lower_
        if t.pos_ == 'PRON':
            if low in ('it', 'its') and carry.get('thing'):
                ref, person = carry['thing'], False
            elif low in _PEOPLE_PRON and low not in ('her',) or (
                    low == 'her' and t.dep_ != 'poss'):
                g = {'him': 'he', 'her': 'she', 'them': 'they'}.get(low, low)
                ref = (carry.get(g) or (carry.get('person') if g != 'they'
                                        else '')) if g in (
                    'he', 'she', 'they') else low
                if not ref:
                    continue
                if g in ('he', 'she', 'they'):
                    carry[g] = ref
                    for other in {'he', 'she'} - {g}:
                        if carry.get(other) == ref:
                            carry.pop(other)
                person = True
            else:
                continue
            by_tok[t.i] = len(ents)
            ents.append({'id': len(ents), 'label': ref, 'head': ref,
                         'at': t.i, 'char': t.idx, 'pron': True,
                         'person': person,
                         'lex': 'noun.person' if person else ''})
            continue
        if t.pos_ not in ('NOUN', 'PROPN') and not misread(t):
            continue
        comp = [c for c in t.children if c.dep_ in ('compound', 'nmod',
                                                     'amod')
                and c.pos_ == 'NOUN' and c.i == t.i - 1] if not verbal(
            t) else []
        comp = [c for c in t.children if c.dep_ == 'compound'
                and c not in comp] + comp if comp else [
            c for c in t.children if c.dep_ == 'compound'
            and not verbal(t)]
        named = t.pos_ == 'PROPN' and t.ent_type_ == 'PERSON'
        if named:
            # 'Meet Maria': an imperative verb is not part of the name
            comp = [c for c in comp if not (c.i == 0 and _wn is not None
                                             and _wn.synsets(c.lower_, 'v'))]
        colour = [c for c in t.children if c.dep_ == 'amod'
                  and c.lower_ in _COLOUR]
        head = _noun_head(t)
        label = ' '.join([c.lower_ for c in colour]
                         + [c.lower_ for c in comp] + [head])
        by_tok[t.i] = len(ents)
        ents.append({'id': len(ents), 'label': label, 'head': head,
                     'at': min([t.i] + [c.i for c in comp + colour]),
                     'char': min([t.idx] + [c.idx for c in comp + colour]),
                     'pron': False, 'person': named or None,
                     'lex': 'noun.person' if named else _noun_lex(head),
                     'time': t.ent_type_ in ('DATE', 'TIME')
                     or _noun_lex(head) == 'noun.time'})
    for t in doc:
        # 'a line of customers', 'a crowd of fans': draw the members
        if t.dep_ == 'pobj' and t.head.lower_ == 'of' and t.i in by_tok \
                and t.head.head.i in by_tok:
            outer = ents[by_tok[t.head.head.i]]
            if outer['lex'] in ('noun.group', 'noun.quantity') \
                    and not outer['pron']:
                outer['partitive'] = by_tok[t.i]
            elif _is_piece(outer['head']) and not outer['pron']:
                outer['of_part'] = by_tok[t.i]
    links = []
    for t in doc:
        # 'a student in another country', 'a token on a blockchain'
        if t.dep_ == 'prep' and t.head.i in by_tok:
            links += [(by_tok[t.head.i], t.lower_, by_tok[g.i])
                      for g in t.children
                      if g.dep_ == 'pobj' and g.i in by_tok
                      and not (t.lower_ == 'of' and (
                          ents[by_tok[t.head.i]].get('partitive')
                          is not None
                          or ents[by_tok[t.head.i]].get('of_part')
                          is not None))]
    states = []
    for t in doc:
        if t.dep_ == 'amod' and t.head.i in by_tok:
            states.append({'of': by_tok[t.head.i], 'word': t.lower_,
                           'kind': state_kind(t.lower_)})
    events = []
    for t in doc:
        if not verbal(t) or (t.dep_ in ('amod', 'compound')
                             and t.tag_ in ('VBG', 'VBN')):
            continue
        lem = t.lemma_.lower()
        kids = list(t.children)
        prt = next((c.lower_ for c in kids if c.dep_ == 'prt'), '')
        subj = next((c for c in kids if c.dep_ in ('nsubj', 'nsubjpass')
                     and not verbal(c)), None)
        cur = t
        while subj is None and cur.dep_ in ('conj', 'xcomp', 'advcl') \
                and cur.head is not cur:
            cur = cur.head
            subj = next((c for c in cur.children
                         if c.dep_ in ('nsubj', 'nsubjpass')), None)
        if subj is None and t.pos_ == 'NOUN':
            subj = next((c for c in kids if c.dep_ == 'compound'), None)
        # 'a token that stands for a share': the relative pronoun is the
        # noun the clause hangs on
        if t.dep_ == 'relcl' and t.head.i in by_tok and (
                subj is None or subj.tag_ in ('WDT', 'WP')):
            subj = t.head
        obj = next((c for c in kids if c.dep_ in ('dobj', 'attr')), None)
        if subj is not None and subj.dep_ == 'nsubjpass':
            subj, obj = None, subj
        acomp = [c for c in kids if c.dep_ in ('acomp', 'oprd')]
        if lem in _COPULA and acomp and subj is not None \
                and subj.i in by_tok:
            for a in acomp:
                states.append({'of': by_tok[subj.i], 'word': a.lower_,
                               'kind': state_kind(a.lower_)})
            if lem == 'be':
                continue
        if lem in _LIGHT and not prt and obj is None:
            continue
        preps = []
        for c in kids:
            if c.dep_ == 'dative' and c.i in by_tok:
                preps.append(('to', by_tok[c.i]))
            if c.dep_ in ('prep', 'prt', 'advmod', 'agent'):
                for g in c.children:
                    if g.dep_ == 'pobj' and g.i in by_tok:
                        preps.append((c.lower_, by_tok[g.i]))
        sub_e = ents[by_tok[subj.i]] if subj is not None and \
            subj.i in by_tok else (ents[by_tok[obj.i]] if obj is not None
                                   and obj.i in by_tok else None)
        amount = sub_e is not None and sub_e.get('lex') in _AMOUNT_LEX
        pat_e = ents[by_tok[obj.i]] if obj is not None and \
            obj.i in by_tok else None
        physical = pat_e is not None and pat_e.get('lex') in _PHYS_NOUN
        kind, way = verb_kind(lem, prt, amount, physical)
        if lem in _ASPECT_STOP and any(c.dep_ in ('xcomp', 'ccomp')
                                       for c in kids):
            kind, way = 'act', ''
        neg = any(c.dep_ == 'neg' for c in kids) or (
            t.dep_ in ('xcomp', 'ccomp') and t.head.lemma_.lower()
            in _ASPECT_STOP)
        cut = {x.i for c in kids if c.dep_ in (
            'conj', 'cc', 'advcl', 'punct', 'mark', 'ccomp', 'nsubj',
            'nsubjpass', 'aux', 'neg', 'advmod') and c.i < t.i
            or c.dep_ in ('conj', 'cc', 'advcl', 'punct', 'mark', 'ccomp')
            for x in c.subtree}
        span = [x for x in t.subtree if x.i >= t.i and x.i not in cut]
        stop = next((k for k, x in enumerate(span) if x.dep_ == 'cc'
                     or x.pos_ == 'CCONJ'), len(span))
        phrase = ' '.join(x.text for x in span[:stop])
        events.append({
            'verb': t.text, 'lemma': lem, 'particle': prt, 'kind': kind,
            'dir': '' if neg else way, 'neg': neg, 'at': t.i,
            'agent': by_tok.get(subj.i) if subj is not None else None,
            'patient': by_tok.get(obj.i) if obj is not None else None,
            'preps': preps, 'phrase': phrase})
    for e in ents:
        if e.get('person') and e['pron']:
            carry['person'] = e['label']
        elif e['lex'] == 'noun.person' and not e['pron']:
            carry['person'] = e['label']
            if doc[e['at']].tag_ in ('NNS', 'NNPS'):
                carry['they'] = e['label']
        elif e['lex'] == 'noun.group' and not e['pron'] \
                and people_group(e['label']):
            carry['they'] = e['label']
        elif not e['pron'] and not e.get('time'):
            carry['thing'] = e['label']
    return {'text': sentence, 'entities': ents, 'events': events,
            'states': states, 'links': links}
