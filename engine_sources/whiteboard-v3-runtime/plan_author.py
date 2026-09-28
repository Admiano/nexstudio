#!/usr/bin/env python3
"""plan_author — decision layer: script text -> production plan JSON.

The authoring side of the specialist pipeline: a deterministic rule
chain (no LLM at runtime) that turns a plain script into the plan
contract the renderers consume. Splits the script into beats, extracts
drawable concepts, picks a grammar, and emits plan JSON.

CLI:
    python3 plan_author.py script.txt --type diagram \
        --title "How does Devin work?" --domain tech --out plan.json
    python3 plan_author.py script.txt --emit-vo   # lines for the TTS pass

Script format: one sentence per beat (blank lines also split). Optional
'# Title' first line becomes the headline; a line like '[stage: COLLECT]'
sets that beat's stage label.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

_STOP = {
    'the', 'a', 'an', 'and', 'or', 'but', 'of', 'to', 'in', 'on', 'at',
    'for', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be',
    'been', 'being', 'it', 'its', "it's", 'this', 'that', 'these', 'those',
    'you', 'your', 'we', 'our', 'they', 'their', 'he', 'she', 'his', 'her',
    'i', 'me', 'my', 'us', 'them', 'what', 'which', 'who', 'when', 'where',
    'why', 'how', 'all', 'any', 'both', 'each', 'more', 'most', 'other',
    'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
    'than', 'too', 'very', 'can', 'will', 'just', 'into', 'over', 'after',
    'then', 'once', 'here', 'there', 'up', 'down', 'out', 'off', 'again',
    'about', 'between', 'through', 'during', 'before', 'while', 'because',
    'until', 'if', 'do', 'does', 'did', 'doing', 'done', 'has', 'have',
    'had', 'having', 'get', 'gets', 'got', 'getting', 'make', 'makes',
    'made', 'making', 'take', 'takes', 'took', 'go', 'goes', 'went',
    'come', 'comes', 'came', 'see', 'sees', 'saw', 'know', 'knows',
    'thing', 'things', 'way', 'ways', 'lot', 'lots', 'kind', 'every',
    'much', 'many', 'first', 'second', 'third', 'also', 'well', 'even',
    'still', 'new', 'now', 'one', 'two', 'three', 'like', 'really',
    # contraction stems (apostrophe tail already dropped) + discourse
    # fillers — none of these can stand on a board as a label or icon
    'don', 'doesn', 'didn', 'isn', 'aren', 'wasn', 'weren', 'won',
    'wouldn', 'couldn', 'shouldn', 'can', 'cannot', 'mustn', 'mightn',
    'needn', 'shan', 'ain', 'll', 've', 're', 'd',
    'whatever', 'whenever', 'wherever', 'whoever', 'whichever',
    'however', 'although', 'though', 'anyway', 'anyways', 'anymore',
    'besides', 'otherwise', 'meanwhile', 'somewhere', 'anywhere',
    'everywhere', 'nowhere', 'somehow', 'something', 'anything',
    'everything', 'nothing', 'somebody', 'anybody', 'everybody',
    'nobody', 'someone', 'anyone', 'everyone', 'maybe', 'perhaps',
    'probably', 'certainly', 'surely', 'basically', 'actually',
    'literally', 'generally', 'usually', 'sometimes', 'often',
    'always', 'never', 'yes', 'yeah', 'okay', 'right',
    # prepositions/conjunctions that draw nothing sensible
    'whether', 'around', 'within', 'without', 'upon', 'onto', 'toward',
    'towards', 'beyond', 'among', 'across', 'along', 'against', 'except',
    'plus', 'per', 'via', 'amid', 'inside', 'outside', 'beside',
    'under', 'above', 'below', 'behind', 'despite', 'unless',
    'since', 'ago', 'yet', 'either', 'neither', 'rather',
    'instead', 'aside', 'apart', 'according', 'regarding', 'including',
    'given', 'considering', 'depending', 'owing', 'due', 'worth',
    # abstract verbs/quantities/adjectives — they survive stoplists meant
    # for fillers but still draw nothing sensible ('starts', 'millions',
    # 'efficient', 'mattering' all ended up as board labels once)
    'start', 'starts', 'started', 'starting', 'begin', 'begins', 'began',
    'beginning', 'end', 'ends', 'ended', 'ending', 'moment', 'instant',
    'trick', 'million', 'millions', 'billion', 'billions', 'trillion',
    'amount', 'number', 'numbers', 'level', 'levels', 'rate', 'degree',
    'matter', 'matters', 'mattering', 'efficient', 'efficiency',
    'effective', 'exactly', 'exact', 'precise', 'regional', 'global',
    'way', 'ways', 'thing', 'things', 'stuff', 'kind', 'kinds', 'sort',
    'sorts', 'type', 'types', 'part', 'parts', 'piece', 'pieces', 'bit',
    'bits', 'lot', 'lots', 'bunch', 'case', 'cases', 'fact', 'facts',
    'idea', 'ideas', 'point', 'points', 'reason', 'reasons', 'result',
    'results', 'side', 'sides', 'place', 'places', 'name', 'names',
    'change', 'changes', 'effect', 'effects', 'issue', 'issues',
    'get', 'gets', 'got', 'getting', 'make', 'makes', 'made', 'making',
    'take', 'takes', 'took', 'give', 'gives', 'gave', 'go', 'goes',
    'went', 'gone', 'come', 'comes', 'came', 'keep', 'keeps', 'kept',
    'let', 'lets', 'put', 'puts', 'see', 'sees', 'seen', 'know',
    'knows', 'knew', 'feel', 'feels', 'felt', 'seem', 'seems',
    'seemed', 'try', 'tries', 'tried', 'use', 'uses', 'using',
    'want', 'wants', 'wanted', 'need', 'needs', 'needed', 'look',
    'looks', 'looking', 'find', 'finds', 'found', 'become', 'becomes',
    'became', 'happen', 'happens', 'happened', 'mean', 'means',
    'meant', 'move', 'moves', 'moving', 'tell', 'tells', 'told',
    'say', 'says', 'said', 'call', 'called', 'calls', 'help', 'helps',
    'stop', 'stops', 'turn', 'turns', 'set', 'sets', 'run', 'runs',
    'just', 'only', 'even', 'still', 'really', 'very', 'quite',
    'pretty', 'much', 'many', 'several', 'own', 'same', 'different',
    'similar', 'important', 'entire', 'whole', 'certain', 'sure',
    'clear', 'real', 'true', 'perfect', 'correct', 'wrong', 'good',
    'better', 'best', 'bad', 'worse', 'worst', 'new', 'old', 'big',
    'small', 'large', 'huge', 'little', 'long', 'short', 'high',
    'low', 'early', 'late', 'fast', 'slow', 'hard', 'easy', 'simple',
    'single', 'multiple', 'full', 'empty', 'open', 'closed', 'main',
    'major', 'minor', 'general', 'specific', 'particular', 'special',
    'normal', 'common', 'various', 'possible', 'likely', 'able',
    'unable', 'free', 'busy', 'ready', 'next', 'previous', 'following',
    'dozen', 'dozens', 'distant',
    'expect', 'expects', 'expected', 'expecting', 'yours', 'mine',
    'ours', 'theirs', 'hers', 'deliver', 'delivers', 'delivered',
    'delivering', 'belong', 'belongs', 'remember', 'remembers',
}

# process cue words -> flow layout (stage chain) rather than the
# hero-satellite anatomy grammar
_PROCESS_CUES = re.compile(
    r'\b(step|stage|phase|then|next|finally|first|process|workflow|'
    r'pipeline|cycle|after that|at the end)\b', re.I)

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z\-']+")


def _sentences(script: str) -> list[tuple[str, str]]:
    """-> [(sentence_text, stage_hint)] — '[stage: X]' markers captured."""
    out = []
    for para in re.split(r'\n+', script):
        para = para.strip()
        if not para or para.startswith('#'):
            continue
        stage = ''
        m = re.search(r'\[\s*stage\s*:\s*([^\]]+)\]', para, re.I)
        if m:
            stage = m.group(1).strip()
            para = para[:m.start()] + para[m.end():]
        for s in re.split(r'(?<=[.!?])\s+|;\s+', para):
            s = s.strip()
            if s:
                out.append((s, stage))
                stage = ''
    # merge fragments shorter than 4 words into the previous beat
    merged: list[tuple[str, str]] = []
    for s, st in out:
        if merged and len(s.split()) < 4 and not st:
            prev, pstage = merged[-1]
            merged[-1] = (prev + ' ' + s, pstage)
        else:
            merged.append((s, st))
    return merged


def _content_words(sentence: str) -> list[str]:
    # drop apostrophe tails first ("that's" -> "that", "don't" -> "don")
    # so the stoplist sees the stem — fillers can't leak into labels
    out = []
    for w in _WORD_RE.findall(sentence):
        stem = w.lower().split("'")[0]
        if len(stem) >= 3 and stem not in _STOP:
            out.append(stem)
    return out


def _bigrams(words: list[str]) -> list[str]:
    return [f'{words[i]} {words[i + 1]}' for i in range(len(words) - 1)]


# Ambiguous vocabulary: the same word means different drawable things in
# different domains ('ram' is an animal in nature content, a memory chip
# in tech). Domain remaps the concept BEFORE scoring so the right art is
# requested. Extend as vocabulary collisions surface — never per-plan.
_DISAMBIG: dict[str, dict[str, str]] = {
    'tech': {'ram': 'chip', 'python': 'python logo', 'java': 'java logo',
             'shell': 'terminal', 'mouse': 'computer mouse',
             'apple': 'apple logo', 'chrome': 'browser',
             'windows': 'computer window'},
    'nature': {'python': 'snake', 'java': 'island', 'apple': 'apple fruit',
               'mouse': 'mouse animal', 'crane': 'bird'},
    'health': {'python': 'snake'},
    'finance': {'apple': 'apple logo', 'python': 'python logo'},
}


def _disambiguate(word: str, domain: str) -> str:
    return _DISAMBIG.get(domain.lower(), {}).get(word, word) \
        if domain else word


def _concepts(sentence: str, icon_for, used: dict, limit: int = 3,
              domain: str = '') -> list[str]:
    """Rank drawable concepts: score every bigram/single by resolution —
    a bigram earns its place only when its parts don't resolve as well
    alone ('pull request', 'garbage truck'); otherwise clean nouns win."""
    words = [_disambiguate(w, domain) for w in _content_words(sentence)]
    # a remapped multi-word entry stands alone — don't let it absorb a
    # neighbour into a bigram ('computer mouse moves')
    candidates = [f'{words[i]} {words[i + 1]}' for i in range(len(words) - 1)
                  if ' ' not in words[i] and ' ' not in words[i + 1]]
    scored: list[tuple[float, int, str]] = []
    card_candidates: list[tuple[int, str]] = []
    for pos, c in enumerate(candidates + words):
        ic = icon_for(c, used)
        if not ic:
            continue
        if ic == 'card':
            # nothing drawables covers this concept — remember it as a
            # labelled-tile fallback rather than dropping the beat empty
            card_candidates.append((pos, c))
            continue
        score = 5.0
        if ' ' in c:
            parts = c.split()
            w0, w1 = parts[0], parts[-1]
            s0 = icon_for(w0, used)
            s1 = icon_for(w1, used)
            if not ((s0 and s0 != 'card') or (s1 and s1 != 'card')):
                score += 2.0
            score -= 0.6  # tidy single nouns are the default
        else:
            score += min(len(c), 10) * 0.05
        scored.append((score, pos, c))
    scored.sort(key=lambda t: -t[0])
    picked: list[str] = []
    seen_words: set[str] = set()
    seen_tails: set[str] = set()
    for _s, _p, c in scored:
        if len(picked) >= limit:
            break
        cw = set(c.split())
        # captions derive from the tail word — 'story fact' and 'fact'
        # would both draw a tile labelled FACT
        if cw & seen_words or c.split()[-1] in seen_tails:
            continue
        picked.append(c)
        seen_words |= cw
        seen_tails.add(c.split()[-1])
    if not picked:
        # nothing resolved above emblem level: keep the last content
        # words so the beat still draws labelled emblems, not an empty
        # cell
        for w in reversed(words):
            if w not in seen_tails:
                picked.append(w)
                seen_tails.add(w)
                if len(picked) >= limit:
                    break
        picked.reverse()
    return picked


def _stage_label(sentence: str, hint: str) -> str:
    if hint:
        return hint[:14]
    words = _content_words(sentence)
    # cells are narrow — fit the label to ~10 chars so adjacent stage
    # labels never run into each other
    out = ''
    for w in words:
        cand = f'{out} {w}'.strip()
        if len(cand) > 10 and out:
            break
        out = cand
    return (out or sentence)[:14]


def _subject(script: str) -> str:
    """Most frequent content word — the thing the video is about."""
    from collections import Counter
    words = [w for s, _ in _sentences(script) for w in _content_words(s)]
    c = Counter(w for w in words if len(w) >= 4)
    return c.most_common(1)[0][0] if c else ''


def build_plan(script: str, *, vtype: str = 'diagram',
               title: str = '', domain: str = '',
               summary: str = '', transition: str = '',
               page_size: int = 4) -> dict:
    import pipeline_v3_narration_timed as p3
    p3.load_execution_body(None)
    import v3_board_renderer as v3

    beats_in = _sentences(script)
    flow = bool(_PROCESS_CUES.search(script)) or len(beats_in) >= 4
    used: dict = {}
    pid = re.sub(r'\W+', '_', (title or 'UNTITLED').upper())
    if vtype == 'kinetic':
        beats = [{'beat_id': f'k{i + 1:02d}', 'narration': s,
                  'duration_seconds': max(3.2, len(s.split()) * 0.42 + 1.2)}
                 for i, (s, _h) in enumerate(beats_in)]
        return {'schema': 'NexMindKineticPlanV1',
                'production_id': pid,
                'type': 'kinetic',
                'beats': beats}
    if vtype == 'whiteboard':
        wb_beats = []
        t = 0.0
        for i, (sentence, hint) in enumerate(beats_in):
            dur = max(3.2, len(sentence.split()) * 0.42 + 1.2)
            concepts = _concepts(sentence, v3.icon_for, used,
                                 domain=domain)
            hero = next(
                (c for c in concepts
                 if v3.icon_for(c, used) in ('person', 'agent')),
                concepts[0] if concepts else _subject(sentence))
            rest = [c for c in concepts if c != hero]
            wb_beats.append({
                'beat_id': f'{i + 1:02d}_{hero.split()[-1]}',
                'start_seconds': round(t, 3),
                'duration_seconds': round(dur, 3),
                'narration': sentence,
                'scene': {
                    'sceneId': f'{i + 1:02d}_{hero.split()[-1]}',
                    'heroRole': hero,
                    'supportingRoles': rest[:3],
                    'screenCopy': {
                        'primary': _stage_label(sentence, hint).upper()},
                    'semanticRelationships': ([{
                        'source': hero, 'target': rest[0], 'kind': 'acts'
                    }] if rest else []),
                }})
            t += dur
        return {'schema': 'NexMindWhiteboardV3NarrationTimedPlanV1',
                'production_id': pid,
                'camera_variant': 'board_sections',
                'output_ratios': ['16:9'],
                'pacing': {'transition_seconds': 1.5,
                           'board_reveal_seconds': 1.5},
                'beats': wb_beats}

    beats = []
    t = 0.0
    for i, (sentence, hint) in enumerate(beats_in):
        dur = max(3.2, len(sentence.split()) * 0.42 + 1.2)
        b: dict = {
            'narration': sentence,
            'start_seconds': round(t, 3),
            'duration_seconds': round(dur, 3),
        }
        stage = _stage_label(sentence, hint)
        concepts = _concepts(sentence, v3.icon_for, used, domain=domain)

        def _el(c: str, at: str, label: str) -> dict:
            if v3.icon_for(c, used) == 'person':
                return {'person': c, 'label': label, 'at': at}
            return {'icon': c, 'label': label, 'at': at}

        spec: dict = {'stage': stage}
        if flow:
            spec['region'] = 'cell'
            spec['elements'] = [
                _el(c, 'cell', c.split()[-1].upper())
                for c in concepts]
        else:
            region = ('left' if i == 0 else
                      'right' if i == len(beats_in) - 1 else 'hero')
            spec['region'] = region
            if region == 'hero':
                spec['elements'] = [
                    {'part': c, 'label': c.upper(), 'at': a}
                    for c, a in zip(
                        concepts, ('hero-tl', 'hero-tr', 'hero-c'))]
            else:
                spec['elements'] = [
                    _el(c, region, c.upper()) for c in concepts]
                spec['elements'].append(
                    {'arrow': {'from': region, 'to': 'hero'}}
                    if i == 0 else
                    {'arrow': {'from': 'hero', 'to': region}})
        if transition in ('erase', 'zoom') and i > 0:
            spec['transition'] = transition
        elif flow and page_size and i > 0 and i % page_size == 0:
            # a long script pages: the outgoing cells wipe and the next
            # chapter refills the same grid slots
            spec['transition'] = 'erase'
        b['diagram'] = spec
        beats.append(b)
        t += dur

    dg: dict = {
        'title': title or _subject(script).title(),
        'summary': summary,
        'layout': 'flow' if flow else 'satellite',
    }
    if not flow:
        dg['hero'] = _subject(script) or 'object'
    return {'production_id': pid, 'beats': beats, 'diagram': dg}


# ---------------------------------------------------------------------------
# storyboard authoring: script -> relation/role/emotion/vignette plan.
# Deterministic rules over WordNet (free, local); the output is ordinary
# plan JSON the author can edit before rendering.
try:
    from nltk.corpus import wordnet as _wn
    _wn.synsets('dog')
except Exception:  # pragma: no cover - WordNet optional
    _wn = None

_REL_CUES = [
    ('before_after', r'\b(before|used to|no longer|anymore|collapse\w*|'
                     r'turns? into)\b'),
    ('contrast', r'\b(but|however|instead|versus|vs\.?|unlike|while others|'
                 r'whereas)\b'),
    ('cycle', r'\b(cycle|again and again|repeats?|loop|every year|'
              r'each season)\b'),
    ('sequence', r'\b(then|next|first|finally|steps?|from .+ to)\b'),
]
_MARK_CUES = [
    ('flow', r'\b(carr(y|ies|ying)|mov(e|es|ing)|fl(y|ies|ying)|spread|'
             r'travel|send|deliver|transport|flows?|pass(es)?|shipp?)\w*'),
    ('puffs', r'\b(smoke|smok\w+|burn\w*|fire|steam|fumes|exhaust|'
              r'pollut\w+|emission\w*)\b'),
    ('cross', r'\b(die|dies|dying|dead|collapse\w*|kill\w*|destroy\w*|'
              r'empty|lost|fail\w*|extinct|ban\w*)\b'),
    ('drips', r'\b(drip\w*|leak\w*|honey|oil|bleed\w*|pour\w*)\b'),
    ('up', r'\b(ris(e|es|ing)|grow\w*|increas\w*|boost\w*|climb\w*|'
           r'improv\w*|recover\w*)\b'),
    ('down', r'\b(fall\w*|drop\w*|declin\w*|shrink\w*|lower\w*|'
             r'reduc\w*|worse)\b'),
    ('rain', r'\b(rain\w*|storm\w*|flood\w*|monsoon)\b'),
    ('heat', r'\b(heat\w*|hot|drought|warming|scorch\w*|fever)\b'),
    ('motion', r'\b(rush\w*|speed\w*|fast|race\w*|hurr\w*|run(s|ning)?)\b'),
    ('sparkle', r'\b(thriv\w*|healthy|clean|shin\w*|success\w*|bright|'
                r'fresh|heal\w*)\b'),
]
_HOLD = re.compile(r'\b(us(e|es|ing)|hold\w*|carr(y|ies)|grab\w*|'
                   r'lift\w*|wield\w*|with (a|an|the|his|her|their))\b')
_ACT_CUES = (
    ('reach', r'\b(pick\w*|reach\w*|grab\w*|touch\w*|press\w*|grind\w*|'
              r'heat(s|ed|ing)?|wash\w*|fix\w*|build\w*|plant(s|ed|ing)?|'
              r'open(s|ed|ing)?|feed\w*|cook\w*|rid(e|es|ing)|rode|'
              r'catch\w*|fly(ing)?|steer\w*|repair\w*)\b'),
    ('offer', r'\b(pour\w*|offer\w*|giv(e|es|ing)|serv\w*|hand(s|ed)?)\b'),
    ('point', r'\b(point\w*|show\w*|explain\w*|teach\w*|train\w*|'
              r'warn\w*|brought|bring\w*|lead\w*|guid\w*|releas\w*|argu\w*|'
              r'defend\w*)\b'),
    ('wave', r'\b(wav\w*|greet\w*|call\w*)\b'),
)
# place nouns the backdrop draws better than an icon can
_PLACES = {'river': 'river', 'riverbank': 'river', 'stream': 'river',
           'road': 'road', 'street': 'road', 'highway': 'road',
           'city': 'city', 'forest': 'forest', 'woods': 'forest',
           'field': 'field', 'hillside': 'field', 'farm': 'field',
           'meadow': 'field'}
_NOT_HOST = {'sunlight', 'light', 'air', 'rain', 'time', 'season', 'sun',
             'wind', 'shade', 'dark', 'water'}
_ATTACH_PREP = {'on': 'on', 'onto': 'on', 'atop': 'on', 'in': 'in',
                'inside': 'in', 'into': 'in', 'within': 'in',
                'beside': 'beside', 'near': 'beside', 'next': 'beside'}


def _lemma(w: str) -> str:
    if _wn is None:
        return w
    return _wn.morphy(w, 'n') or w


_SB_DET = {'a', 'an', 'the', 'this', 'that', 'these', 'those', 'his', 'her',
           'their', 'its', 'our', 'your', 'my', 'every', 'each', 'one',
           'some', 'many', 'few', 'fewer', 'more', 'new', 'no', 'of', 'on',
           'in', 'into', 'onto', 'from', 'with', 'over', 'through', 'by',
           'at', 'under', 'single', 'long', 'green', 'hot', 'warm', 'ripe',
           'dry', 'fallen', 'young', 'old'}
_SB_NOT_ROLE = {'morning', 'mornings', 'hour', 'hours', 'day', 'days', 'time',
                'week', 'weeks', 'year', 'years', 'minute', 'minutes',
                'night', 'evening', 'change', 'hands', 'hand', 'seconds',
                'population', 'work'}
_SB_SUBJ = {'i', 'you', 'we', 'they', 'he', 'she', 'it', 'who', 'to'}
_SB_ADV = {'back', 'away', 'past', 'again', 'around', 'over', 'through',
           'down', 'off', 'out', 'ahead', 'apart', 'together', 'time'}
_SB_FEEL = re.compile(r'\b(happy|sad|afraid|scared|worr\w*|stress\w*|calm|'
                      r'angry|proud|excited|tired|confused|relieved|love)\b',
                      re.I)


def _is_physical(w: str) -> bool:
    if _wn is None:
        return True
    forms = {_lemma(w), w[:-1] if w.endswith('s') else w}
    syn = [x for f in forms for x in _wn.synsets(f, 'n')[:2]]
    return any(any(h.name() in ('artifact.n.01', 'physical_entity.n.01')
                   for p in s_.hypernym_paths() for h in p)
               and s_.lexname() != 'noun.body' for s_ in syn)


def _noun_in_context(low: list, i: int, picked: set) -> bool:
    w = low[i]
    prev = low[i - 1] if i else ''
    if w in _SB_ADV:
        return False
    if prev in _SB_DET:
        return True
    if prev in _SB_SUBJ:
        return False
    if prev in picked and _wn is not None and _wn.synsets(w, 'v') \
            and (w.endswith(('s', 'ed')) or not _wn.synsets(w, 'n')):
        return False
    return _is_thing(w)


_AGENT = re.compile(r'(er|or|ist|ian|ista|ant|ent)s?$')


_KIT_ANIMALS = frozenset(json.loads(
    (Path(__file__).resolve().parent / 'assets' / 'kits' / 'animals'
     / 'index.json').read_text(encoding='utf-8'))['glyphs'])


def _is_animal(w: str) -> bool:
    if _lemma(w) in _KIT_ANIMALS:
        return True
    if _wn is None:
        return False
    syn = _wn.synsets(_lemma(w), 'n')[:2]
    return any(h.name() == 'animal.n.01' for s_ in syn
               for p in s_.hypernym_paths() for h in p)


_CREW = {'staff', 'crew', 'team', 'workers', 'people', 'residents',
         'commuters', 'commuter', 'staffers', 'volunteers'}


def _is_person(w: str) -> bool:
    if w in _CREW:
        return True
    if _wn is None:
        return False
    syn = _wn.synsets(_lemma(w), 'n')
    if not syn:
        return bool(_AGENT.search(w)) and len(w) > 5
    hit = {'person.n.01', 'causal_agent.n.01'}
    animal = any(h.name() == 'animal.n.01' for s_ in syn
                 for p in s_.hypernym_paths() for h in p)
    first = _lemma(w) not in _KIT_ANIMALS and any(
        h.name() == 'person.n.01' for p in syn[0].hypernym_paths() for h in p)
    adj = bool(_wn.synsets(w, 'a') or _wn.synsets(w, 's'))
    agent = _AGENT.search(w) and not animal and not adj and any(
        any(h.name() in hit for p in s_.hypernym_paths() for h in p)
        for s_ in syn[:2])
    return bool(first or agent)


def _is_thing(w: str) -> bool:
    """Concrete, drawable noun reading (not a verb/adjective use)."""
    if _wn is None:
        return True
    n = _wn.synsets(_lemma(w), 'n')
    if not n:
        return False
    v = _wn.synsets(w, 'v')
    a = _wn.synsets(w, 'a') + _wn.synsets(w, 's')
    if w.endswith(('ing', 'ly')) and (v or a):
        return False
    if len(v) > len(n) * 1.5 or len(a) > len(n) * 1.5:
        return False
    return True


_VERB_POSE = {'verb.contact': 'reach', 'verb.creation': 'reach',
              'verb.consumption': 'reach', 'verb.competition': 'reach',
              'verb.change': 'reach', 'verb.possession': 'offer',
              'verb.communication': 'point', 'verb.perception': 'point',
              'verb.cognition': 'point', 'verb.motion': 'reach'}
_NOT_ACT = {'is', 'are', 'was', 'were', 'be', 'has', 'have', 'had', 'feels',
            'feel', 'seems', 'looks', 'gets', 'becomes', 'stays', 'stayed',
            'smiles', 'cheers', 'claps', 'and', 'who', 'that', 'also',
            'then', 'still', 'never', 'always'}


def prev_det(low: list, i: int) -> bool:
    return not i or low[i - 1] in _SB_DET


def _verb_pose(low: list, i: int):
    """(pose, verb index) for the verb a subject at `low[i]` performs,
    from the word's WordNet verb class (contact/creation -> reach,
    possession -> offer, communication/perception -> point)."""
    if _wn is None:
        return None
    for k in range(i + 1, min(i + 3, len(low))):
        w = low[k]
        if w in _NOT_ACT or w in _SB_ADV:
            return None
        base = _wn.morphy(w, 'v')
        obj_next = k + 1 < len(low) and low[k + 1] in _SB_DET
        if not base or (w == base and _wn.synsets(w, 'n')
                        and not w.endswith('s') and not obj_next):
            continue
        for syn in _wn.synsets(base, 'v')[:3]:
            pose = _VERB_POSE.get(syn.lexname())
            if pose:
                return pose, k
        return None
    return None


def _sb_beats(script: str) -> list[tuple[str, str]]:
    """-> [(heading, narration)]; paragraphs are beats, '## Heading' sets
    a heading, otherwise every sentence is its own beat."""
    out, head, paras = [], '', []
    for line in script.splitlines() + ['']:
        t = line.strip()
        if t.startswith('## '):
            head = t[3:].strip()
            continue
        if t.startswith('#'):
            continue
        if t:
            paras.append(t)
            continue
        if paras:
            out.append((head, ' '.join(paras)))
            head, paras = '', []
    if len(out) == 1 and not out[0][0]:
        return [('', s) for s, _h in _sentences(out[0][1])]
    return out


def _sb_title(i: int, heading: str, roles: list, sentence: str) -> str:
    if heading:
        return f'{i}. {heading}'
    for r in roles:
        if r.get('icon') != 'person':
            return f'{i}. {r["label"].title()}'
    words = _content_words(sentence)
    return f'{i}. {" ".join(words[:2]).title()}'


def _sb_caption(sentence: str) -> str:
    clauses = [c.strip(' ,.;:!?') for c in re.split(
        r'[,;:]|\band\b|\bbut\b|\bwhile\b|\bso\b', sentence)]
    clauses = [c for c in clauses if 2 <= len(c.split()) <= 7]
    pick = clauses[-1] if clauses else sentence
    pick = _caption_cut(pick.strip(' ,.;:!?').split())
    return f'"{pick[:1].upper()}{pick[1:]}."'


_CAP_PREP = {'in', 'on', 'to', 'into', 'onto', 'from', 'with', 'at', 'for',
             'by', 'through', 'across', 'under', 'over', 'near', 'inside'}


def _caption_cut(words: list, limit: int = 7) -> str:
    """Shorten at a phrase boundary: drop trailing prepositional phrases
    ('spread the beans | in the sun to dry'), never end on a determiner,
    preposition or dangling modifier ('cuts the ripe')."""
    if len(words) > limit:
        cut = [k for k in range(2, len(words)) if words[k].lower() in _CAP_PREP]
        fit = [k for k in cut if k <= limit]
        words = words[:fit[-1]] if fit else words[:limit + 2]
    while len(words) > 2 and (words[-1].lower() in _SB_DET | _CAP_PREP
                              or (_wn is not None and words[-2].lower()
                                  in _SB_DET and not _wn.synsets(
                                  _lemma(words[-1].lower()), 'n')
                                  and _wn.synsets(words[-1].lower(), 'a'))):
        words = words[:-1]
    return ' '.join(words)


def _sb_annot(tokens: list[str], idx: int, nouns: set) -> str:
    """Verb phrase right after a role noun ('queen lays eggs' -> 'lays
    eggs'), capped at 3 words and stopping at the next role noun."""
    out = []
    toks = [w.lower() for w in tokens[idx + 1: idx + 6]]
    for k, lw in enumerate(toks):
        if lw in nouns or lw in ('and', 'but', 'while', 'because', 'which',
                                 'so', 'until'):
            break
        nxt = toks[k + 1] if k + 1 < len(toks) else ''
        if lw in ('a', 'an', 'the', 'his', 'her', 'their', 'its'):
            continue
        if lw in _STOP and not out and lw not in ('is', 'are', 'stays'):
            continue
        if (nxt in nouns and _wn is not None and out
                and (_wn.synsets(lw, 'a') or _wn.synsets(lw, 's'))):
            break
        out.append(lw)
        if sum(1 for o in out if o not in _STOP) >= 2 or len(out) >= 3:
            break
    while out and out[-1] in _STOP:
        out.pop()
    if not out or _wn is None:
        return ' '.join(out)
    adj = bool(_wn.synsets(out[-1], 'a') or _wn.synsets(out[-1], 's'))
    verb = bool(_wn.synsets(out[0], 'v'))
    if len(out) == 1:
        return ''
    if not (verb or adj):
        return ''
    return ' '.join(out)


def _step_note(sent: str, roles: list) -> None:
    """Pin a moment's verb phrase ('drills a small hole') to the object it
    acts on, so each step of a multi-moment scene reads on the board."""
    if len(roles) < 2:
        return
    words = [w.strip(' ,.;:!?"') for w in sent.split()]
    low = [w.lower() for w in words]
    head = roles[0]['label'].split()[-1]
    at = next((k for k, w in enumerate(low) if _lemma(w) == head
               or w == head), None)
    if at is None and low and low[0] in ('he', 'she', 'they'):
        at = 0
    if at is None:
        return
    tg = roles[0].get('target')
    obj = next((r for r in roles if r['label'] == tg), None) or next(
        (r for r in roles[1:] if not r.get('attach')), roles[1])
    ohead = obj['label'].split()[-1]
    note = _caption_cut(words[at + 1:], 4)
    if note and ohead in {_lemma(w.lower()) for w in note.split()} | set(
            note.lower().split()) and not obj.get('annotate'):
        obj['annotate'] = note


def _thing_icon(v3, lab: str) -> str:
    """Icon key for a role the script uses as a thing: when the word's art
    resolves to a person ('sap' = fool), draw its nearest non-person
    hypernym instead ('sap' -> liquid)."""
    if _wn is None or v3.icon_for(lab) != 'person':
        return lab
    head = _lemma(lab.split()[-1])
    for s_ in [x for x in _wn.synsets(head, 'n')
               if x.lexname() != 'noun.person'][:1]:
        for path in s_.hypernym_paths():
            for h in reversed(path[:-1]):
                if h.min_depth() < 4:
                    break
                for name in h.lemma_names():
                    cand = name.replace('_', ' ')
                    ic = v3.icon_for(cand)
                    rk = v3.sem_rank(cand, ic) if isinstance(
                        ic, tuple) else None
                    if (isinstance(ic, tuple) and not v3._is_emblem(ic)
                            and (rk is None or rk <= 300)):
                        return cand
    return lab


def build_storyboard(script: str, *, title: str = '', max_roles: int = 3,
                     wpm: float = 150.0) -> dict:
    import pipeline_v3_narration_timed as p3
    p3.load_execution_body(None)
    import v3_board_renderer as v3
    v3.set_ink_only(True)
    v3.set_context(script)
    beats = []
    used: dict = {}
    prev_rel = ''
    compounds: dict = {}
    last_person = ''
    def _moment(sent, prev_rel, last_person, cap):
        tokens = _WORD_RE.findall(sent)
        low = [t.lower().split("'")[0] for t in tokens]
        cands = []
        seen = set()
        for i, w in enumerate(low):
            if len(w) < 3 or w in _STOP or w in seen:
                continue
            nxt = low[i + 1] if i + 1 < len(low) else ''
            big = (f'{w} {_lemma(nxt)}' if nxt and nxt not in _STOP
                   else '')
            if big and ((_wn is not None and _wn.synsets(big.replace(' ', '_')))
                        or v3.kit_exact(big)
                        or (_is_person(nxt) and not _is_person(w)
                            and _is_thing(w) and prev_det(low, i))
                        or (i and _is_thing(w) and not _is_person(w)
                            and not _is_person(nxt) and _is_thing(nxt)
                            and _is_physical(nxt)
                            and not (_wn is not None and _wn.synsets(w, 'v')
                                     and not _wn.synsets(w, 'n'))
                            and not (nxt.endswith('s') and _wn is not None
                                     and _wn.synsets(nxt, 'v')))):
                cands.append((i, big, _is_person(nxt)))
                seen |= {w, nxt}
                continue
            picked_w = {low[c[0]] for c in cands}
            prev_ = low[i - 1] if i else ''
            verb_use = bool(i and low[i - 1] in picked_w and _wn is not None
                            and w.endswith('s') and _wn.synsets(w, 'v'))
            adj_use = bool(nxt and _wn is not None
                           and prev_ in _SB_DET | _CAP_PREP
                           and (_wn.synsets(w, 'a') or _wn.synsets(w, 's'))
                           and _is_thing(nxt) and not _is_person(nxt))
            mod_det = bool(i >= 1 and prev_det(low, i - 1) and _wn is not None
                           and (_wn.synsets(prev_, 'a')
                                or _wn.synsets(prev_, 's')))
            if not verb_use and not adj_use and _is_person(w) \
                    and prev_ not in _SB_SUBJ and (
                    prev_ in _SB_DET or mod_det or not i or _is_thing(w)
                    or not (_wn and _wn.synsets(w, 'v'))):
                cands.append((i, _lemma(w), True))
                seen.add(w)
                continue
            if not _noun_in_context(low, i, picked_w) or w in _SB_NOT_ROLE:
                continue
            ic = v3.icon_for(_lemma(w), used)
            kit = isinstance(ic, tuple) and str(ic[1]).startswith('kit:')
            if v3._is_emblem(ic) or not (kit or _is_physical(w)):
                continue
            cands.append((i, _lemma(w), False))
            seen.add(w)
        pro = re.match(r'\s*(she|he|they)\b', sent, re.I)
        if pro and last_person and not any(c[2] for c in cands):
            cands.append((0, last_person, True))
        if not any(c[2] for c in cands):
            m_ = re.search(r'\b(you|we|i)\b', sent, re.I)
            if m_ and (_SB_FEEL.search(sent) or _HOLD.search(sent)):
                at = len(_WORD_RE.findall(sent[:m_.start()]))
                cands.append((at, m_.group(1).lower(), True))
        cands.sort()
        people = [c for c in cands if c[2]][:2]
        things = [c for c in cands if not c[2]]
        pick = sorted(people + things[:max(1, cap - len(people))])
        pick = pick[:cap]
        if not pick:
            pick = [(0, _subject(sent) or 'idea', False)]
        nouns = {c[1].split()[-1] for c in pick} | {
            tokens[c[0]].lower() for c in pick}
        roles = []
        for i, lab, person in pick:
            if ' ' in lab and not person:
                compounds[lab.split()[-1]] = lab
            elif not person:
                lab = compounds.get(lab, lab)
            r: dict = {'label': lab, 'icon': 'person' if person
                       else _thing_icon(v3, lab)}
            ann = _sb_annot(tokens, i, nouns)
            if ann and not re.search(r'\b' + r'\s+'.join(map(re.escape,
                                     ann.split())) + r'\b', sent, re.I):
                ann = ''
            if ann:
                r['annotate'] = ann
            if person:
                r['narration'] = sent
            roles.append(r)
        # relation
        rel = next((k for k, pat in _REL_CUES if re.search(pat, sent, re.I)),
                   '')
        n_p = sum(1 for r in roles if r['icon'] == 'person')
        if not rel:
            rel = ('reaction' if n_p >= 2 else
                   'focus' if len(roles) <= 2 else 'sequence')
        if rel == 'contrast' and len(roles) < 2:
            rel = 'focus'
        if rel == 'before_after':
            cut = re.search(r'\b(but|now|after|no longer|until)\b', sent, re.I)
            ci = len(_WORD_RE.findall(sent[:cut.start()])) if cut else None
            for (i, _l, _p), r in zip(pick, roles):
                r['side'] = ('before' if ci is not None and i < ci
                             else 'after')
            if len({r['side'] for r in roles}) < 2:
                roles[0]['side'] = 'before'
                for r in roles[1:]:
                    r['side'] = 'after'
        if rel == prev_rel and rel in ('focus', 'sequence') and len(roles) >= 3:
            rel = 'sequence' if rel == 'focus' else 'focus'
        # composition: a person using/holding a thing holds it; an object
        # named with on/in another role sits on/in it
        for a_, (i, _l, person) in enumerate(pick):
            if not person:
                continue
            tail = ' '.join(low[i:i + 6])
            if _HOLD.search(tail):
                th = next((b for b, (j, _l2, p2) in enumerate(pick)
                           if not p2 and j > i), None)
                if th is not None and 'attach' not in roles[th]:
                    roles[th].update(attach='held', to=a_)
                    roles[a_]['action'] = 'hold'
        for b_, (i, _l, _p) in enumerate(pick):
            for k_ in range(i + 1, min(i + 3, len(low))):
                prep = _ATTACH_PREP.get(low[k_])
                if not prep:
                    continue
                if prep == 'in' and (_p or _is_animal(low[i])):
                    prep = 'beside'
                host = next((h for h, (j, _l2, _p2) in enumerate(pick)
                             if j > k_ and j <= k_ + 3), None)
                if host is not None and roles[host]['label'].split()[-1] \
                        in _NOT_HOST:
                    host = None
                if host is not None and host != b_ \
                        and 'attach' not in roles[b_] \
                        and 'attach' not in roles[host]:
                    roles[b_].update(attach=prep, to=host)
                break
        for a_, (i, _l, person) in enumerate(pick):
            if (person or _is_animal(_l)) and 'action' not in roles[a_]:
                tail = ' '.join(low[i:i + 7])
                hit = min(((m_.start(), a) for a, pat in _ACT_CUES
                           for m_ in [re.search(pat, tail)] if m_),
                          default=None)
                vp = None if hit else _verb_pose(low, i + _l.count(' '))
                if hit or vp:
                    roles[a_]['action'] = hit[1] if hit else vp[0]
                    vi = (i + tail[:hit[0]].count(' ')) if hit else vp[1]
                    tg = next((b for b, (j, _l2, p2) in enumerate(pick)
                               if not p2 and j > vi), None)
                    if tg is None:
                        tg = next((b for b, (j, _l2, p2) in enumerate(pick)
                                   if b != a_ and j > vi), None)
                    if tg is not None:
                        roles[a_]['target'] = roles[tg]['label']
        setting = ''
        for a_ in range(len(roles) - 1, -1, -1):
            place = _PLACES.get(roles[a_]['label'].split()[-1])
            if place and len(roles) >= 3:
                setting = setting or place
                del roles[a_], pick[a_]
                for r_ in roles:
                    if r_.get('to') == a_:
                        r_.pop('attach', None)
                        r_.pop('to', None)
                    if isinstance(r_.get('to'), int) and r_['to'] > a_:
                        r_['to'] -= 1
        for a_ in range(len(roles) - 1, -1, -1):
            if roles[a_]['icon'] == 'person' or len(roles) < 3:
                continue
            art = v3.icon_for(roles[a_]['icon'])
            dup = next((b for b, r_ in enumerate(roles) if b != a_
                        and r_['icon'] != 'person'
                        and v3.icon_for(r_['icon']) == art), None)
            if dup is not None and dup < a_ and not any(
                    r_.get('to') == a_ for r_ in roles):
                del roles[a_], pick[a_]
                for r_ in roles:
                    if isinstance(r_.get('to'), int) and r_['to'] > a_:
                        r_['to'] -= 1
        if all('attach' in r for r in roles):
            roles[0].pop('attach', None)
            roles[0].pop('to', None)
        # story marks from the verbs
        marks = []
        free = [n for n, r in enumerate(roles) if 'attach' not in r]
        for kind, pat in _MARK_CUES:
            m = re.search(pat, sent, re.I)
            if not m or len(marks) >= 2:
                continue
            if kind == 'flow':
                if not re.search(pat + r'(\s+\w+){0,3}?\s+(to|into|onto|'
                                 r'between|across|through)\b', sent, re.I):
                    continue
                objs = [n for n in free if roles[n]['icon'] != 'person']
                if len(objs) >= 2:
                    marks.append({'type': 'flow', 'from': roles[objs[0]]['label'],
                                  'to': roles[objs[-1]]['label']})
                continue
            # nearest role noun to the cue word
            at = len(_WORD_RE.findall(sent[:m.start()]))
            tgt = min(range(len(roles)),
                      key=lambda n: abs(pick[n][0] - at))
            if kind == 'cross' and rel == 'before_after':
                tgt = max(range(len(roles)),
                          key=lambda n: (roles[n].get('side') == 'after'
                                         and roles[n]['icon'] != 'person',
                                         n))
            if roles[tgt]['icon'] == 'person' and kind not in ('motion',):
                continue
            marks.append({'type': kind, 'on': roles[tgt]['label']})
        last_person = next((r['label'] for r in roles
                            if r['icon'] == 'person'
                            and r['label'] not in ('you', 'we', 'i')),
                           last_person)
        return roles, rel, marks, setting, last_person

    for bi, (heading, para) in enumerate(_sb_beats(script)):
        sents = [x for x in re.split(r'(?<=[.!?])\s+', para.strip())
                 if len(_WORD_RE.findall(x)) >= 3] or [para]
        if len(sents) == 1:
            roles, rel, marks, setting, last_person = _moment(
                sents[0], prev_rel, last_person, max_roles)
        else:
            roles, marks, setting = [], [], ''
            per = 3 if len(sents) == 2 else 2
            for k, s_ in enumerate(sents[:3]):
                r_, _rl, mk_, st_, last_person = _moment(
                    s_, '', last_person, per)
                off = len(roles)
                labs = [r['label'] for r in r_]
                _step_note(s_, r_)
                for r in r_:
                    r['moment'] = k
                    if isinstance(r.get('to'), int):
                        r['to'] += off
                    if r.get('target') in labs:
                        r['target'] = off + labs.index(r['target'])
                roles += r_
                marks += [m for m in mk_ if m.get('type') != 'flow']
                setting = setting or st_
            rel = 'story'
        prev_rel = rel
        sent = sents[-1]
        hero, *rest = roles
        dur = max(4.0, len(para.split()) / wpm * 60 + 1.6)
        beats.append({
            'beat_id': f'b{bi + 1:02d}',
            'title': _sb_title(bi + 1, heading, roles, sent),
            'caption': _sb_caption(sent),
            'narration': para,
            'duration_seconds': round(dur, 2),
            'scene': {'sceneId': f'b{bi + 1:02d}', 'relation': rel,
                      'heroRole': hero, 'supportingRoles': rest,
                      'marks': marks,
                      **({'setting': setting} if setting else {})},
        })
    title = title or _subject(script).title()
    pid = re.sub(r'\W+', '_', title.lower()).strip('_') or 'storyboard'
    return {'production_id': pid, 'title': title,
            'board_layout': 'storyboard',
            'brandExecution': {'brandAuthority': {
                'background': '#F7F2E7', 'ink': '#1A1A17',
                'accent': '#1A1A17', 'secondary': '#8B8577'}},
            'beats': beats}


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('script', help='script text file (one beat per line)')
    ap.add_argument('--type', default='diagram',
                    choices=('diagram', 'kinetic', 'whiteboard',
                             'storyboard'))
    ap.add_argument('--title', default='')
    ap.add_argument('--domain', default='')
    ap.add_argument('--summary', default='')
    ap.add_argument('--transition', default='',
                    choices=('', 'erase', 'zoom'),
                    help='per-beat canvas transition (diagram only)')
    ap.add_argument('--page-size', type=int, default=4,
                    help='flow cells per board page before an erase turn')
    ap.add_argument('--out', default='')
    ap.add_argument('--emit-vo', action='store_true',
                    help='print narration lines (for the TTS pass)')
    args = ap.parse_args(argv)

    script = Path(args.script).read_text()
    if args.emit_vo:
        print('\n'.join(s for s, _ in _sentences(script)))
        return 0

    if args.type == 'storyboard':
        plan = build_storyboard(script, title=args.title)
    else:
        plan = build_plan(script, vtype=args.type, title=args.title,
                          domain=args.domain, summary=args.summary,
                          transition=args.transition,
                          page_size=args.page_size)
    out = args.out or (Path(args.script).stem + '_plan.json')
    Path(out).write_text(json.dumps(plan, indent=1))
    print(out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
