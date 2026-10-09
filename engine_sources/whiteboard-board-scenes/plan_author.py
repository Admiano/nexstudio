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
import math
import re
import sys
from pathlib import Path

import sb_activity
import sb_cast
import sb_story
import scene_planner
import scene_map

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
    'idea', 'ideas', 'point', 'points', 'parallel', 'pair', 'pairs',
    'reason', 'reasons', 'result',
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
                'icons': 'auto',
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
              r'empty|lost|fail\w*|extinct|ban\w*|ruin\w*|broke\w*|'
              r'wip\w+ out)\b'),
    ('drips', r'\b(drip\w*|leak\w*|honey|oil|bleed\w*|pour\w*)\b'),
    ('up', r'\b(ris(e|es|ing)|grow\w*|increas\w*|boost\w*|climb\w*|'
           r'improv\w*|recover\w*|jump\w*|soar\w*|surg\w*|spik\w*|'
           r'skyrocket\w*|gain\w*|pump\w*)\b'),
    ('down', r'\b(fall\w*|drop\w*|declin\w*|shrink\w*|lower\w*|'
             r'reduc\w*|worse|crash\w*|plung\w*|plummet\w*|tank\w*|'
             r'sink\w*|dump\w*|wipe\w*)\b'),
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
           'meadow': 'field', 'sea': 'sea', 'ocean': 'sea',
           'coast': 'sea', 'seaside': 'sea', 'harbor': 'sea',
           'harbour': 'sea', 'port': 'sea', 'shore': 'sea', 'beach': 'sea',
           'bay': 'sea'}
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
                'population', 'work', 'today', 'tonight', 'another',
                # manner words masquerading as nouns ('in parallel',
                # 'in general'): no drawing exists for how an act is done
                'parallel', 'general', 'particular', 'common', 'public'}
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


_CLAUSE = {'and', 'but', 'while', 'so', 'as', 'when', 'until', 'then'}
_TOOL_KIND = {'device', 'conveyance', 'implement', 'container'}

# agent nouns that only LOOK -er/-ist tool-derived: 'engineer' is not
# 'engine+er', a 'trainer' holds no train, a 'programmer' no program.
_AGENT_TOOL_FALSE = frozenset({
    'engineer', 'trainer', 'banker', 'printer', 'painter', 'programmer',
    'developer', 'designer', 'presenter', 'retailer', 'auditor', 'operator',
    'instructor', 'interviewer', 'reviewer', 'founder', 'miner', 'broker',
    'dealer', 'lender', 'borrower', 'seller', 'buyer', 'marketer',
    'advertiser', 'analyst', 'therapist', 'custodian', 'validator',
    'researcher', 'teacher', 'preacher', 'speaker', 'writer', 'recorder',
    'reader', 'leader', 'manager', 'officer', 'ranger', 'keeper', 'cooker',
    'cleaner', 'washer', 'waiter', 'porter', 'holder', 'claimer', 'announcer',
    'builder', 'maker', 'creator', 'founder', 'carrier', 'trailer',
    'teacher', 'lecturer', 'mentor', 'senior', 'junior', 'player',
})


def _relational(low: list, i: int) -> bool:
    """'front' in 'in front of', 'top' in 'on top of': a location word
    framed by a preposition and 'of' names a place, not a thing."""
    if _wn is None or i + 1 >= len(low) or low[i + 1] != 'of':
        return False
    k = i - 1 if i and low[i - 1] not in _SB_DET else i - 2
    syn = _wn.synsets(low[i], 'n')[:1]
    return k >= 0 and low[k] in _CAP_PREP and bool(syn) \
        and syn[0].lexname() in ('noun.location', 'noun.relation')


def _clause_end(low: list, k: int) -> int:
    """Index where the clause holding word `k` ends: 'the judge reads the
    verdict | and the family feels relieved'."""
    for j in range(k + 1, len(low) - 1):
        if low[j] in _CLAUSE and (low[j + 1] in _SB_DET
                                  or low[j + 1] in _SB_SUBJ):
            return j
    return len(low)


def _agent_tool(label: str) -> str:
    """The tool an agent noun is named for, when WordNet says it's a
    device or vehicle: trucker -> truck, guitarist -> guitar,
    drummer -> drum. Empty for roles not named for a tool."""
    if _wn is None or not label:
        return ''
    w = label.split()[-1].lower()
    if w in _AGENT_TOOL_FALSE:
        return ''
    m = re.match(r'([a-z]{3,}?)(?:ists?|ers?|ors?)$', w)
    if not m:
        return ''
    r = m.group(1)
    for root in (r, r + 'e', r[:-1] if len(r) > 3 and r[-1] == r[-2] else ''):
        syn = _wn.synsets(root, 'n')[:1] if root else []
        if syn and syn[0].lexname() == 'noun.artifact' and any(
                h.name().split('.')[0] in _TOOL_KIND
                for p in syn[0].hypernym_paths() for h in p):
            return root
    return ''


def _verb_tool(lemma: str) -> str:
    """The tool a verb is named for: hammers -> hammer, saws -> saw,
    shovels -> shovel. Empty when the verb isn't a tool's name."""
    if _wn is None or not lemma:
        return ''
    for syn in _wn.synsets(lemma, 'v')[:1]:
        for lm in syn.lemmas():
            for d in lm.derivationally_related_forms():
                n = d.synset()
                if d.name() == lemma and n.lexname() == 'noun.artifact' \
                        and any(h.name().split('.')[0] in _TOOL_KIND
                                for p in n.hypernym_paths() for h in p):
                    return lemma
    return ''


def _noun_in_context(low: list, i: int, picked: set) -> bool:
    w = low[i]
    prev = low[i - 1] if i else ''
    if w in _SB_ADV or _relational(low, i):
        return False
    if prev in _SB_DET:
        return True
    j = i - 1
    while j > 0 and i - j <= 2 and _wn is not None and low[j] not in (
            _SB_DET | _SB_SUBJ) and (_wn.synsets(low[j], 'a')
                                     or _wn.synsets(low[j], 's')):
        j -= 1
    if j < i - 1:
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
    def is_animal(s_):
        return any(h.name() == 'animal.n.01' for p in s_.hypernym_paths()
                   for h in p)

    def uses(s_):
        return sum(lm.count() for lm in s_.lemmas()
                   if lm.name().lower() == _lemma(w))
    # the commonest sense decides ('painter' is an artist before a
    # cougar); a barely-used first sense yields to an animal next to it
    # ('whale' the giant person vs the sea mammal)
    top = max(syn, key=uses)
    animal = is_animal(top) or (uses(syn[0]) <= 1 and any(
        is_animal(s_) for s_ in syn[:2]))
    # no usage signal at all: the first sense wins only when person senses
    # are at least half the noun's meanings, or a hospital 'monitor'
    # (proctor first, four artifact senses after) draws a person
    n_person = sum(1 for s_ in syn if any(
        h.name() == 'person.n.01'
        for p in s_.hypernym_paths() for h in p))
    person_plurality = uses(top) > 0 or 2 * n_person >= len(syn)
    first = _lemma(w) not in _KIT_ANIMALS and not animal \
        and person_plurality and any(
        h.name() == 'person.n.01' for p in syn[0].hypernym_paths() for h in p)
    adj = bool(_wn.synsets(w, 'a') or _wn.synsets(w, 's'))
    agent = _AGENT.search(w) and not animal and not adj \
        and person_plurality and any(
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


# verb meaning -> (stance, arm pose): the body the action needs. WordNet
# ancestors carry unseen verbs ('strolled' is a walk, 'gulped' a drink).
_BODY_SYN = (('walk.v.01', ('walk', '')), ('run.v.01', ('walk', '')),
             ('climb.v.01', ('climb', 'climb')),
             ('kneel.v.01', ('kneel', '')), ('crouch.v.01', ('kneel', '')),
             ('squat.v.01', ('kneel', '')), ('sit.v.01', ('sit', '')),
             ('sit_down.v.01', ('sit', '')),
             ('drink.v.01', ('', 'drink')), ('eat.v.01', ('', 'drink')),
             ('read.v.01', ('', 'read')), ('write.v.01', ('', 'write')),
             ('dig.v.01', ('', 'dig')),
             ('bring.v.01', ('', 'offer')),
             ('give.v.03', ('', 'offer')))
_BODY_LEMMA = {'type': ('sit', 'type'), 'sign': ('', 'write'),
               'scribble': ('', 'write'), 'sketch': ('', 'write'),
               'draw': ('', 'write'), 'note': ('', 'write'),
               'study': ('', 'read'), 'browse': ('', 'read'),
               'munch': ('', 'drink'), 'chew': ('', 'drink'),
               'bite': ('', 'drink'), 'sip': ('', 'drink'),
               'taste': ('', 'drink'), 'ascend': ('climb', 'climb'),
               'mop': ('', 'dig'), 'sweep': ('', 'dig'), 'rake': ('', 'dig'),
               'scrub': ('', 'dig'), 'shovel': ('', 'dig'),
               'hoe': ('', 'dig'), 'jog': ('walk', ''),
               'wander': ('walk', ''), 'hurry': ('walk', ''),
               'rush': ('walk', ''), 'stroll': ('walk', ''),
               'serve': ('', 'offer'), 'hand': ('', 'offer'),
               'deliver': ('', 'offer')}
# nouns a seated figure sits on, climbed things it clings to
_SEATS = re.compile(r'\b(chair|stool|bench|sofa|couch|seat|armchair|'
                    r'steps?|stairs?|stoop|throne|saddle|log|pew)\b')
_WORN = re.compile(r'\b(wear\w*|wore|worn|put(s|ting)? on|don(s|ned)?)\b')


# what an arm pose holds when the sentence doesn't name it
_ARM_PROP = {'drink': 'cup', 'read': 'book', 'write': 'pen',
             'dig': 'shovel'}


def _is_vessel(label: str) -> bool:
    """True when `label` names something that holds a drink."""
    if _wn is None:
        return False
    for syn in _wn.synsets(str(label).split()[-1], 'n')[:4]:
        anc = {h.name() for pth in syn.hypernym_paths() for h in pth}
        if anc & {'container.n.01', 'vessel.n.03'}:
            return True
    return False


def _body_for(lemma: str) -> tuple:
    """(stance, arm) the verb `lemma` needs, ('', '') if neither."""
    lemma = str(lemma or '').lower()
    if lemma in _BODY_LEMMA:
        return _BODY_LEMMA[lemma]
    if _wn is None:
        return ('', '')
    for syn in _wn.synsets(lemma, 'v')[:2]:
        anc = {h.name() for pth in syn.hypernym_paths() for h in pth}
        for key, body in _BODY_SYN:
            if key in anc:
                return body
    return ('', '')


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
            if paras:
                out.append((head, ' '.join(paras)))
                paras = []
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


_SB_MOMENTS = 6


def _merge_moments(sents: list, cap: int) -> list:
    """At most `cap` drawn moments per scene: the shortest neighbouring
    sentences are drawn together rather than any being dropped."""
    sents = list(sents)
    while len(sents) > cap:
        k = min(range(len(sents) - 1),
                key=lambda i: len(sents[i].split()) + len(sents[i + 1].split()))
        sents[k:k + 2] = [sents[k] + ' ' + sents[k + 1]]
    return sents


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
    note = re.sub(r'\s+(and|or|but|so)$', '',
                  _caption_cut(words[at + 1:], 4))
    if note and ohead in {_lemma(w.lower()) for w in note.split()} | set(
            note.lower().split()) and not obj.get('annotate'):
        obj['annotate'] = note


_SHOCK = re.compile(r'^(panic|gasp|scream|shriek|freak|shock|horrif|'
                    r'terrif|realiz)')


def _mind_bubble(after) -> str:
    """Overlay for a person from the verb that follows them: thinking
    verbs get a thought bubble, shock verbs get exclamation marks."""
    for w in after:
        if _SHOCK.match(w):
            return 'exclaim'
        if _wn is None or w in _SB_DET:
            continue
        vs = _wn.synsets(w, 'v')
        if vs and not _wn.synsets(w, 'n')[:1] or (
                vs and w.endswith('s') and _wn.morphy(w, 'v')):
            return 'thinking' if vs[0].lexname() == 'verb.cognition' else ''
    return ''


_TREND_ART = re.compile(r'chart|graph|trend')
_TREND_COLOR = {'green': 'up', 'red': 'down'}


def _trend_roles(v3, roles, marks, sent):
    """A chart-like role whose sentence says which way it went is drawn as
    that trend: 'the price jumps' -> trend-up, 'the chart crashes' ->
    trend-down, 'a green chart' -> trend-up."""
    cue = {k: bool(re.search(p, sent, re.I)) for k, p in _MARK_CUES
           if k in ('up', 'down')}
    for r in roles:
        if r['icon'] == 'person':
            continue
        art = v3.icon_for(r['icon'])
        if not (isinstance(art, tuple) and _TREND_ART.search(str(art[-1]))):
            continue
        way = next((_TREND_COLOR[w] for w in r['label'].lower().split()
                    if w in _TREND_COLOR), None)
        way = way or next((m['type'] for m in marks
                           if m.get('on') == r['label']
                           and m['type'] in ('up', 'down')), None)
        if way is None and cue.get('up') != cue.get('down'):
            way = 'up' if cue.get('up') else 'down'
        if way:
            r['icon'] = f'trend {way}'
            marks[:] = [m for m in marks if not (
                m.get('on') == r['label'] and m['type'] in ('up', 'down'))]


def _thing_icon(v3, lab: str) -> str:
    """Icon key for a role the script uses as a thing: when the word's art
    resolves to a person ('sap' = fool), draw its nearest non-person
    hypernym instead ('sap' -> liquid)."""
    if _wn is None:
        return lab
    ic0 = v3.icon_for(lab)
    rk0 = v3.sem_rank(lab, ic0) if isinstance(ic0, tuple) else None
    if ic0 != 'person' and (rk0 is None or rk0 <= v3.SEM_BAD_RANK
                            or str(ic0[1]).startswith('kit:')):
        return lab
    head = _lemma(lab.split()[-1])
    if ' ' in lab and ic0 == 'person':
        ich = v3.icon_for(head)
        rkh = v3.sem_rank(head, ich) if isinstance(ich, tuple) else None
        if ich != 'person' and rkh is not None and rkh <= v3.SEM_BAD_RANK:
            return head
    things = [x for x in _wn.synsets(head, 'n')
              if x.lexname() != 'noun.person']
    ctx, _all = v3._context_sense(head)
    # the script's sense, else the first made-thing sense: a plumber's
    # 'valve' is a device, not the heart's
    pick = ([ctx] if ctx in things else []) or [
        x for x in things if x.lexname() == 'noun.artifact'][:1] or things[:1]
    for s_ in pick:
        for path in s_.hypernym_paths():
            for h in reversed(path[:-1]):
                if h.min_depth() < 4:
                    break
                for name in h.lemma_names():
                    cand = name.replace('_', ' ')
                    ic = v3.icon_for(cand)
                    if not isinstance(ic, tuple) or v3._is_emblem(ic):
                        continue
                    rk = v3.sem_rank(cand, ic)
                    better = v3.sem_rank(lab, ic)
                    if (rk is None or rk <= 300) and (
                            ic0 == 'person' or (
                                better is not None and rk0 is not None
                                and better < rk0)):
                        return cand
    return lab


_DEST_PREP = {'to', 'toward', 'towards', 'into', 'onto', 'across', 'through',
              'at', 'over'}
_NOUN_MARKS = ('puffs', 'rain', 'heat', 'drips', 'sparkle')


def _drawable(v3, head: str, used: dict) -> bool:
    ic = v3.icon_for(_lemma(head), used)
    if not isinstance(ic, tuple) or v3._is_emblem(ic):
        return False
    return (str(ic[1]).startswith('kit:') or v3.art_related(_lemma(head), ic)
            or _is_physical(head))


# things a sentence role can be drawn as; people are cast members and
# times, ideas and events have no place in the activity picture
_DRAWN_ROLE_LEX = scene_map._PHYS_NOUN - {'noun.person', 'noun.body'}


def _roles_in_setting(roles, setting):
    """A role filled by the scene's own setting is drawn by the backdrop,
    not as an object inside the activity picture."""
    for r in roles:
        act = r.get('activity') or {}
        rl = act.get('roles') or {}
        for name in [n for n, lab_ in rl.items() if lab_ == setting]:
            act.setdefault('roles_setting', {})[name] = rl.pop(name)
            (act.get('roles_lost') or {}).pop(name, None)
        if 'roles' in act and not rl:
            del act['roles']
        if 'roles_lost' in act and not act['roles_lost']:
            del act['roles_lost']


def _activity(ag, ev, ents, role, roles):
    """Resolve what the actor's body is doing in `ev` (sb_activity) and
    bind the thing it is done with/on/in as the activity partner."""
    def lab(eid):
        return str(ents[eid].get('label') or ents[eid].get('head') or '')
    objs = ([('dobj', lab(ev['patient']))] if ev['patient'] is not None
            else []) + [(p_, lab(e)) for p_, e in ev['preps']]
    spec = sb_activity.resolve(ev['lemma'], objs, '' if 'activity' in ag
                               else ag.get('stance', ''))
    if 'activity' in ag:
        spec = sb_activity.merge(ag['activity'], spec)
        if spec is None:
            return
    if spec is None:
        if sb_activity.is_physical(ev['lemma']):
            ag.setdefault('activity_miss', ev['lemma'])
        return
    act = {k: spec[k] for k in ('schema', 'kind', 'via', 'lemma')}
    if spec.get('posture'):
        act['posture'] = spec['posture']
    eids = ([ev['patient']] if ev['patient'] is not None else []) + [
        e for _p, e in ev['preps']]
    part = next((role(e) for e in eids if role(e) is not None
                 and lab(e) == spec['partner']), None)
    me = roles.index(ag)
    if part is not None and part['icon'] != 'person' \
            and part.get('attach') in (None, 'held', 'under') \
            and part.get('to', me) == me:
        # things in the hands stay 'held'; the rest join the picture
        part.update(attach='held' if spec['schema'] in sb_activity.HAND_SCHEMAS
                    or part.get('attach') == 'held' else 'activity', to=me)
        act['partner'] = part['label']
    for e in eids:
        r_ = role(e)
        if r_ is None or r_ is part or r_['icon'] == 'person' \
                or 'attach' in r_:
            continue
        if lab(e) in spec['absorb']:
            r_.update(attach='activity', to=me)
        elif lab(e) in spec.get('setting', ()):
            r_.update(attach='behind', to=me)
            act.setdefault('setting', []).append(r_['label'])
    # every other narrated thing keeps the role the sentence gives it
    # (source, goal, vantage, instrument ...) and is drawn in that role
    rl = dict((ag.get('activity') or {}).get('roles') or {})
    for rname, rlab in (spec.get('roles') or {}).items():
        if rname in rl:
            continue
        e = next((e for e in eids if lab(e) == rlab), None)
        r_ = role(e) if e is not None else None
        if r_ is None and e is not None \
                and ents[e].get('lex') in _DRAWN_ROLE_LEX \
                and lab(e) not in spec['absorb'] \
                and lab(e) not in spec.get('setting', ()):
            act.setdefault('roles_lost', {})[rname] = rlab
        old_to = r_.get('to') if r_ is not None else None
        owned_by_other = isinstance(old_to, int) and old_to != me \
            and 0 <= old_to < len(roles) \
            and roles[old_to].get('icon') == 'person'
        if r_ is None or r_ is part or r_['icon'] == 'person' \
                or lab(e) in spec['absorb'] \
                or lab(e) in spec.get('setting', ()) \
                or owned_by_other:
            continue
        r_.update(attach='activity', to=me)
        rl[rname] = r_['label']
    if rl:
        act['roles'] = rl
    if 'activity' in ag and ag['activity'].get('partner') \
            and act.get('partner') is None:
        act['partner'] = ag['activity']['partner']
    referenced = {act.get('partner')} | set(rl.values()) \
        | set(spec.get('absorb') or ())
    for r_ in roles:
        if r_.get('attach') == 'activity' and r_.get('to') == me \
                and r_['label'] not in referenced:
            r_['attach'] = 'behind'
            act.setdefault('setting', []).append(r_['label'])
    ag['activity'] = act


def _moment_map(v3, sm: dict, sent: str, cap: int, used: dict,
                compounds: dict, last_person: str):
    """Roles, relation, marks and setting for one sentence from its scene
    map: who acts on what, which way things change, what is ruined, where
    things go, and what each person thinks or fears."""
    ents, events, states = sm['entities'], sm['events'], sm['states']
    # 'a nugget of gold', 'a lump of clay': when the piece has no drawing
    # of its own, the material stands in for it
    alias = {e['id']: e['partitive'] for e in ents if 'partitive' in e}
    for e in ents:
        inner = ents[e['of_part']]['head'] if 'of_part' in e else ''
        if inner and (not _drawable(v3, e['head'], used)
                      or _drawable(v3, inner, used)):
            alias[e['id']] = e['of_part']
            e['partitive'] = e['of_part']
    if alias:
        events = [dict(ev, agent=alias.get(ev['agent'], ev['agent']),
                       patient=alias.get(ev['patient'], ev['patient']),
                       preps=[(p_, alias.get(x, x)) for p_, x in ev['preps']])
                  for ev in events]
    role_of = {}  # entity id -> event role weight
    for ev in events:
        for k, w in (('agent', 3), ('patient', 3)):
            if ev[k] is not None:
                role_of[ev[k]] = max(role_of.get(ev[k], 0), w)
        # the things a physical act is done from/into/with are part of
        # the picture of that act, not scenery
        pw = 3 if sb_activity.is_physical(ev['lemma']) else 2
        for _p, eid in ev['preps']:
            role_of[eid] = max(role_of.get(eid, 0), pw)
    moving = {ev['agent'] for ev in events if ev['dir']} | {
        ev['patient'] for ev in events if ev['dir']}
    wordy = {e['id'] for e in ents if _wn is not None and any(
        x.lexname() == 'noun.communication'
        and e['head'] in x.lemma_names()
        for x in _wn.synsets(e['head'], 'n')[:2])}
    wordy |= {ev['patient'] for ev in events if _wn is not None
              and ev['patient'] is not None
              and ents[ev['patient']]['lex'] in ('noun.act', 'noun.cognition')
              and any(x.lexname() in ('verb.communication', 'verb.cognition')
                      for x in _wn.synsets(ev['lemma'], 'v')[:1])}
    keep, seen, paper = [], set(), set()
    ended = {ev['agent'] for ev in events if ev['agent'] is not None
             and not ev.get('neg') and ev['lemma'] in (
                 'stop', 'cease', 'end', 'finish')
             and ents[ev['agent']].get('lex') == 'noun.phenomenon'}
    toks = [t.lower() for t in re.findall(r"\w+|[^\w\s]", sent)]
    for e in ents:
        if e['id'] in ended:
            continue
        head = e['head']
        if e['at'] < len(toks) and toks[e['at']] == head \
                and _relational(toks, e['at']):
            continue
        person = bool(e.get('person')) or (not e['pron'] and _is_person(head))
        if e['label'] in seen or e.get('time') or head in _SB_NOT_ROLE \
                or 'partitive' in e:
            continue
        # 'at the top', 'on the side': a spot, not something to draw
        if not person and e['lex'] == 'noun.location' \
                and head not in _PLACES and not v3.kit_exact(head) \
                and role_of.get(e['id'], 0) < 3:
            continue
        ic_e = v3.icon_for(_lemma(head), used)
        acted_on = role_of.get(e['id'], 0) >= 3 and ic_e != 'person' and (
            not isinstance(ic_e, tuple) or not v3._is_emblem(ic_e))
        # a verdict, a report, a letter: words someone acts on are drawn
        # as the paper they're written on
        if not person and e['id'] in wordy \
                and role_of.get(e['id'], 0) >= 3 \
                and not _drawable(v3, head, used):
            paper.add(e['id'])
        if not person and not (_drawable(v3, head, used) or acted_on or (
                e['id'] in moving and e['id'] in role_of)
                or e['id'] in paper):
            continue
        agent = any(ev['agent'] == e['id'] for ev in events)
        if not person and not agent and e['lex'] in (
                'noun.feeling', 'noun.cognition', 'noun.time',
                'noun.motive') and not v3.kit_exact(e['label']) \
                and e['id'] not in paper:
            continue
        seen.add(e['label'])
        keep.append((e, person))
    pick = sorted(keep, key=lambda k: k[0]['at'])
    if not pick:
        return None
    idx = {e['id']: n for n, (e, _p) in enumerate(pick)}
    roles = []
    for e, person in pick:
        lab = e['label']
        if not person:
            if ' ' in lab:
                compounds[lab.split()[-1]] = lab
            else:
                lab = compounds.get(lab, lab)
        r: dict = {'label': lab,
                   'icon': 'person' if person else 'document'
                   if e['id'] in paper else _thing_icon(v3, lab)}
        if person:
            r['narration'] = sent
            if e.get('gender'):
                r['gender'] = e['gender']
            if e.get('member_qualifier'):
                r['member_qualifier'] = e['member_qualifier']
        elif int(e.get('count') or 0) > 1:
            r['count'] = int(e['count'])
        roles.append(r)

    by_id = {eid: roles[n] for eid, n in idx.items()}

    def role(eid):
        r_ = by_id.get(eid)
        return r_ if r_ is not None and any(r_ is x for x in roles) else None

    # what each person does, thinks or fears
    for ev in events:
        ag = role(ev['agent']) if ev['agent'] is not None else None
        if ag is None:
            continue
        agent_is_actor = ag['icon'] == 'person' or _is_animal(ag['label'])
        if ag['icon'] == 'person':
            if ev['kind'] == 'fear' and ag.get('bubble') != 'exclaim':
                ag['bubble'] = 'exclaim'
            elif ev['kind'] == 'think' and not ag.get('bubble'):
                ag['bubble'] = 'thinking'
        if not agent_is_actor or 'action' in ag:
            continue
        tgt = role(ev['patient']) if ev['patient'] is not None else None
        tgt = tgt or next((role(e) for _p, e in ev['preps'] if role(e)),
                          None)
        tool = next((role(e) for p_, e in ev['preps'] if p_ == 'with'
                     and role(e) and role(e)['icon'] != 'person'), None)
        held = tool if tool is not None else tgt
        pose = None
        if ag['icon'] == 'person':
            _activity(ag, ev, ents, role, roles)
        stance, arm = _body_for(ev['lemma']) if ag['icon'] == 'person' \
            else ('', '')
        if stance and 'stance' not in ag:
            ag['stance'] = stance
        seat = next((role(e) for p_, e in ev['preps']
                     if p_ in ('on', 'in', 'at', 'onto') and role(e)
                     and _SEATS.search(role(e)['label'])), None)
        if stance and not arm:
            dest = tgt if tgt is not None and tgt['icon'] != 'person' \
                and not (stance == 'sit' and tgt is seat) else None
            if dest is not None and 'target' not in ag:
                ag['target'] = dest['label']
        if stance == 'sit' and seat is not None and 'attach' not in seat:
            seat.update(attach='under', to=roles.index(ag))
        if ag['icon'] == 'person' and _WORN.search(ev['phrase']) \
                and tgt is not None and tgt['icon'] != 'person' \
                and 'attach' not in tgt:
            tgt.update(attach='worn', to=roles.index(ag))
            continue
        if stance and not arm:
            # walking with a bucket: what goes along is carried
            if tool is not None and 'attach' not in tool \
                    and 'action' not in ag:
                tool.update(attach='held', to=roles.index(ag))
                ag['action'] = 'hold'
            continue
        # a long tool (shovel, mop) is held; the ground dug is its target
        held = tool if arm in ('dig', 'climb') else held
        if arm and held is not None and held['icon'] != 'person' \
                and 'attach' not in held and held is not seat:
            held.update(attach='held', to=roles.index(ag))
            if arm == 'drink' and not _is_vessel(held['label']):
                held['icon'] = _thing_icon(v3, 'cup')
            pose = arm
        elif arm and arm != 'climb' and len(roles) <= cap \
                and not any(r_.get('to') == roles.index(ag)
                            and r_.get('attach') == 'held' for r_ in roles):
            prop = _ARM_PROP.get(arm, '')
            if prop and prop not in {r_['label'] for r_ in roles}:
                roles.append({'label': prop, 'icon': _thing_icon(v3, prop),
                              'attach': 'held', 'to': roles.index(ag)})
            pose = arm
        elif arm:
            pose = arm
        if pose:
            pass
        elif _HOLD.search(ev['phrase']) and held is not None \
                and held['icon'] != 'person' and 'attach' not in held:
            held.update(attach='held', to=roles.index(ag))
            pose = 'hold'
            if tool is not None and tgt is not None and tgt is not tool:
                ag['target'] = tgt['label']
        elif ev['kind'] == 'transfer':
            pose = 'offer'
        elif ev['kind'] in ('feel', 'fear', 'think'):
            pose = None
        elif any(re.search(pat, ev['verb'], re.I) for _a, pat in _ACT_CUES):
            pose = next(a for a, pat in _ACT_CUES
                        if re.search(pat, ev['verb'], re.I))
        elif _wn is not None:
            syn = _wn.synsets(ev['lemma'], 'v')[:3]
            pose = next((_VERB_POSE[x.lexname()] for x in syn
                         if x.lexname() in _VERB_POSE), None)
        tool_w = _agent_tool(ag['label']) if ag['icon'] == 'person' else ''
        if pose and tool_w and tgt is not None \
                and not _is_physical(tgt['label']) \
                and tool_w not in {r_['label'] for r_ in roles} \
                and len(roles) <= cap:
            roles.append({'label': tool_w, 'icon': _thing_icon(v3, tool_w),
                          'attach': 'held', 'to': roles.index(ag)})
        vt = _verb_tool(ev['lemma']) if ag['icon'] == 'person' else ''
        if pose and vt and len(roles) <= cap \
                and vt not in {r_['label'] for r_ in roles} \
                and not any(r_.get('attach') == 'held'
                            and r_.get('to') == roles.index(ag)
                            for r_ in roles) \
                and _drawable(v3, vt, used):
            roles.append({'label': vt, 'icon': _thing_icon(v3, vt),
                          'attach': 'held', 'to': roles.index(ag)})
        if pose:
            ag['action'] = pose
            if tgt is None or tgt is ag:
                # the object the verb names isn't drawable: face the
                # nearest thing (else person) in the same sentence
                me = roles.index(ag)
                others = {id(role(e['agent'])) for e in events
                          if e is not ev and e['agent'] is not None
                          and e['agent'] != ev['agent']}
                near = sorted((abs(k - me), r_['icon'] == 'person', k)
                              for k, r_ in enumerate(roles) if r_ is not ag
                              and 'attach' not in r_
                              and id(r_) not in others)
                tgt = roles[near[0][2]] if near else None
                tool = _agent_tool(ag['label']) \
                    if tgt is None and ag['icon'] == 'person' else ''
                if tool and tool not in {r_['label'] for r_ in roles}:
                    roles.append({'label': tool,
                                  'icon': _thing_icon(v3, tool)})
                    tgt = roles[-1]
            if tgt is not None and pose != 'hold':
                ag['target'] = tgt['label']
            elif tgt is not None and 'target' not in ag \
                    and tgt is not held:
                ag['target'] = tgt['label']
    # on / in / beside
    for ev in events:
        mover = ev['patient'] if ev['patient'] is not None else ev['agent']
        mv = role(mover) if mover is not None else None
        for prep, eid in ev['preps']:
            how = _ATTACH_PREP.get(prep)
            host = role(eid)
            if not how or mv is None or host is None or host is mv:
                continue
            if host['label'].split()[-1] in _NOT_HOST:
                continue
            if how == 'in' and (mv['icon'] == 'person'
                                or _is_animal(mv['label'])):
                how = 'beside'
            if 'attach' not in mv and 'attach' not in host:
                mv.update(attach=how, to=roles.index(host))
            break
    setting = ''
    for n in range(len(roles) - 1, -1, -1):
        place = _PLACES.get(roles[n]['label'].split()[-1])
        if place and len(roles) >= 2:
            setting = setting or place
            _drop_role(roles, n)
    for n in range(len(roles) - 1, -1, -1):
        if roles[n]['icon'] == 'person' or len(roles) < 2:
            continue
        art = v3.icon_for(roles[n]['icon'])
        dup = next((b for b, r_ in enumerate(roles) if b < n
                    and r_['icon'] != 'person'
                    and v3.icon_for(r_['icon']) == art), None)
        if dup is not None:
            if any(r_.get('to') == n for r_ in roles):
                # two narrated words, one drawing: keep both words on the
                # surviving element so neither concept silently vanishes
                roles[dup]['label'] += ' & ' + roles[n]['label']
            _drop_role(roles, n)
    if roles and all('attach' in r for r in roles):
        roles[0].pop('attach', None)
        roles[0].pop('to', None)
    labels = {r['label'] for r in roles}
    lab_of = {e['id']: e['label'] for e in ents}
    for e in ents:
        if e['label'] in compounds.values() or e['head'] in compounds:
            lab_of[e['id']] = compounds.get(e['head'], e['label'])
    marks: list = []

    def add(m):
        if m not in marks and len(marks) < 3:
            marks.append(m)

    def thing(eid):
        lab = lab_of.get(eid)
        r = next((x for x in roles if x['label'] == lab), None)
        return r if r is not None and r['icon'] != 'person' else None

    for ev in events:
        if ev.get('neg'):
            continue
        impact = ev['kind'] == 'destroy' and ev['patient'] is None and any(
            p_ in ('on', 'onto', 'into', 'against', 'at')
            for p_, _e in ev['preps'])
        if impact:
            src = thing(ev['agent']) if ev['agent'] is not None else None
            dst = next((thing(e) for p_, e in ev['preps'] if thing(e)), None)
            if src is not None and dst is not None and src is not dst:
                add({'type': 'flow', 'from': src['label'], 'to': dst['label']})
            elif src is not None:
                add({'type': 'motion', 'on': src['label']})
            continue
        subj = [ev['agent'], ev['patient']] if ev['kind'] in (
            'rise', 'fall') else [ev['patient']] + [
            e for p_, e in ev['preps'] if p_ in ('out', 'off', 'away')] + [
            ev['agent']]
        tr = next((thing(e) for e in subj if e is not None and thing(e)),
                  None)
        if ev['kind'] in ('rise', 'fall') and tr is not None:
            add({'type': 'up' if ev['dir'] == 'up' else 'down',
                 'on': tr['label']})
        elif ev['kind'] == 'destroy' and tr is not None:
            art = v3.icon_for(tr['icon'])
            chart = isinstance(art, tuple) and _TREND_ART.search(str(art[-1]))
            add({'type': 'down' if chart else 'cross', 'on': tr['label']})
        elif ev['kind'] in ('move', 'transfer'):
            src = (thing(ev['agent']) if ev['kind'] == 'move'
                   and ev['agent'] is not None
                   and (ev['patient'] is None or sb_story.place_kind(
                       lab_of.get(ev['patient'], ''))) else None)
            src = src or (thing(ev['patient'])
                          if ev['patient'] is not None else None)
            src = src or (thing(ev['agent']) if ev['agent'] is not None
                          else None)
            dst = next((thing(e) for p_, e in ev['preps']
                        if p_ in _DEST_PREP and thing(e)), None)
            if src is not None and dst is not None and src is not dst \
                    and 'attach' not in src:
                add({'type': 'flow', 'from': src['label'],
                     'to': dst['label']})
            elif src is not None and ev['kind'] == 'move':
                add({'type': 'motion', 'on': src['label']})
    for st in states:
        r = thing(st['of'])
        if r is not None and st['kind'] == 'ruin':
            add({'type': 'cross', 'on': r['label']})
    for r in roles:
        if r['icon'] == 'person':
            continue
        words = ' '.join([r['label']] + [st['word'] for st in states
                                         if lab_of.get(st['of']) == r['label']])
        for kind, pat in _MARK_CUES:
            if kind in _NOUN_MARKS and re.search(pat, words, re.I):
                add({'type': kind, 'on': r['label']})
                break
    # the action, as a short verb label pinned to what it happens to
    for ev in events:
        if ev['kind'] in ('feel', 'fear', 'think') or \
                len(ev['phrase'].split()) < 2:
            continue
        on = [ev['patient']] + [e for _p, e in ev['preps']] + [ev['agent']]
        r = next((thing(e) for e in on if e is not None and thing(e)), None)
        if r is None:
            r = next((role(e) for e in on[:-1] if e is not None and role(e)),
                     None)
        if r is None:
            r = role(ev['agent']) if ev['agent'] is not None else None
        if r is not None and not r.get('annotate'):
            words = [w_ for w_ in ev['phrase'].split()
                     if re.fullmatch(r"[\w'-]+", w_)
                     and w_.lower() not in _SB_DET]
            cut_ = next((k for k, w_ in enumerate(words)
                         if k and w_.lower() in _CAP_PREP), len(words))
            words = words[:min(cut_, 3)]
            if len(words) >= 2:
                r['annotate'] = ' '.join(words)
    rel = next((k for k, pat in _REL_CUES if re.search(pat, sent, re.I)), '')
    n_p = sum(1 for r in roles if r['icon'] == 'person')
    if not rel:
        rel = ('reaction' if n_p >= 2 else
               'focus' if len(roles) <= 2 else 'sequence')
    if rel == 'contrast' and len(roles) < 2:
        rel = 'focus'
    if rel == 'before_after':
        cut = re.search(r'\b(but|now|after|no longer|until)\b', sent, re.I)
        at = {e['label']: e['char'] for e in ents}
        for r in roles:
            r['side'] = ('before' if cut and at.get(r['label'], 0)
                         < cut.start() else 'after')
        if len({r['side'] for r in roles}) < 2:
            roles[0]['side'] = 'before'
            for r in roles[1:]:
                r['side'] = 'after'
    _trend_roles(v3, roles, marks, sent)
    marks[:] = [m for m in marks if all(
        m.get(k) in {r['label'] for r in roles}
        for k in ('on', 'from', 'to') if k in m)]
    last_person = next((r['label'] for r in roles if r['icon'] == 'person'
                        and r['label'] not in ('you', 'we', 'i')),
                       last_person)
    del labels
    return roles, rel, marks, setting, last_person


def _drop_role(roles: list, n: int) -> None:
    del roles[n]
    for r_ in roles:
        if r_.get('to') == n:
            r_.pop('attach', None)
            r_.pop('to', None)
        elif isinstance(r_.get('to'), int) and r_['to'] > n:
            r_['to'] -= 1


def build_storyboard(script: str, *, title: str = '', max_roles: int = 3,
                     wpm: float = 150.0) -> dict:
    import pipeline_v3_narration_timed as p3
    p3.load_execution_body(None)
    import v3_board_renderer as v3
    v3.set_ink_only(True)
    v3.set_context(script)
    # the domain kit this script speaks — detected up front so authoring
    # resolves every concept against it, then stamped on the plan so the
    # render resolves the same way
    art_kit = _detect_art_kit(script, v3)
    v3.set_art_kit(art_kit or None)
    beats = []
    used: dict = {}
    prev_rel = ''
    compounds: dict = {}
    last_person = ''
    carry: dict = {}

    def _moment(sent, prev_rel, last_person, cap):
        if last_person and not carry.get('person'):
            carry['person'] = last_person
        sm = scene_map.parse(sent, carry)
        if sm is not None:
            got = _moment_map(v3, sm, sent, cap, used, compounds,
                              last_person)
            if got is not None:
                maps.append(sm)
                return got
        tokens = _WORD_RE.findall(sent)
        low = [t.lower().split("'")[0] for t in tokens]
        cands = []
        seen = set()
        for i, w in enumerate(low):
            if len(w) < 3 or w in _STOP or w in seen:
                continue
            nxt = low[i + 1] if i + 1 < len(low) else ''
            if _wn is not None and i and _wn.synsets(w, 'v') and any(
                    c[0] + len(c[1].split()) == i
                    and (c[2] or w.endswith('s') or low[i - 1].endswith('s'))
                    for c in cands):
                continue
            if nxt in _SB_DET and i and w.endswith('s') and _wn is not None \
                    and _wn.morphy(w, 'v') not in (None, w):
                continue
            if nxt and _wn is not None and _is_person(w) and len(
                    _wn.synsets(w, 'a') + _wn.synsets(w, 's')) > len(
                    _wn.synsets(w, 'n')) and (_is_person(nxt)
                                              or _is_thing(nxt)):
                continue
            if nxt and i and low[i - 1] in _SB_DET and _wn is not None and (
                    _wn.synsets(w, 'a') or _wn.synsets(w, 's')) and not any(
                    h.name() == 'artifact.n.01' for x in _wn.synsets(w, 'n')[:2]
                    for pth in x.hypernym_paths() for h in pth) and not (
                    _wn.synsets(f'{w}_{nxt}') or v3.kit_exact(f'{w} {nxt}')) \
                    and (_is_person(nxt) or _is_thing(nxt)):
                continue
            if nxt and _wn is not None and (_wn.synsets(w, 'a')
                                            or _wn.synsets(w, 's')) \
                    and not _is_physical(w) and (_is_person(nxt)
                                                 or _is_thing(nxt)):
                continue
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
            adj_mod = bool(nxt and _wn is not None and _is_person(nxt)
                           and (_wn.synsets(w, 'a') or _wn.synsets(w, 's')))
            if not verb_use and not adj_use and not adj_mod and _is_person(w) \
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
            drawn = isinstance(ic, tuple) and v3.art_related(_lemma(w), ic)
            if v3._is_emblem(ic) or not (kit or drawn or _is_physical(w)):
                continue
            cands.append((i, _lemma(w), False))
            seen.add(w)
        pro = re.search(r'\b(she|he|they)\b', sent, re.I)
        if pro and last_person and not any(c[2] for c in cands):
            cands.append((len(_WORD_RE.findall(sent[:pro.start()])),
                          last_person, True))
        if not any(c[2] for c in cands):
            m_ = re.search(r'\b(you|we|i)\b', sent, re.I)
            if m_ and (_SB_FEEL.search(sent) or _HOLD.search(sent)):
                at = len(_WORD_RE.findall(sent[:m_.start()]))
                cands.append((at, m_.group(1).lower(), True))
        cands.sort()
        people = [c for c in cands if c[2]]
        things = [c for c in cands if not c[2]]
        pick = sorted(people + things)
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
                bub = _mind_bubble(low[i + len(lab.split()):i + 5])
                if bub:
                    r['bubble'] = bub
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
            hm = _HOLD.search(tail)
            if hm:
                at = i + tail[:hm.start()].count(' ')
                th = next((b for b, (j, _l2, p2) in enumerate(pick)
                           if not p2 and j > at), None)
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
                    end = _clause_end(low, vi)
                    tg = next((b for b, (j, _l2, p2) in enumerate(pick)
                               if not p2 and vi < j < end), None)
                    if tg is None:
                        tg = next((b for b, (j, _l2, p2) in enumerate(pick)
                                   if b != a_ and vi < j < end), None)
                    tool = _agent_tool(_l) if person and tg is None else ''
                    if tool and len(roles) < cap + 1:
                        roles.append({'label': tool,
                                      'icon': _thing_icon(v3, tool)})
                        pick.append((len(low), tool, False))
                        tg = len(roles) - 1
                    if tg is not None:
                        roles[a_]['target'] = roles[tg]['label']
        setting = ''
        for a_ in range(len(roles) - 1, -1, -1):
            place = _PLACES.get(roles[a_]['label'].split()[-1])
            if place and len(roles) >= 2:
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
            nx_ = low[at + 1] if at + 1 < len(low) else ''
            if kind == 'cross' and _wn is not None and _wn.synsets(nx_, 'n') \
                    and not any(pick[n][0] == at + 1 for n in range(len(roles))):
                continue
            if kind == 'cross':
                near = [n for n in range(len(roles))
                        if roles[n]['icon'] != 'person'
                        and -3 <= pick[n][0] - at <= 4]
                if not near:
                    continue
                tgt = min(near, key=lambda n: (pick[n][0] < at,
                                               abs(pick[n][0] - at)))
            if kind == 'cross' and rel == 'before_after':
                tgt = max(range(len(roles)),
                          key=lambda n: (roles[n].get('side') == 'after'
                                         and roles[n]['icon'] != 'person',
                                         n))
            if roles[tgt]['icon'] == 'person' and kind not in ('motion',):
                continue
            marks.append({'type': kind, 'on': roles[tgt]['label']})
        _trend_roles(v3, roles, marks, sent)
        last_person = next((r['label'] for r in roles
                            if r['icon'] == 'person'
                            and r['label'] not in ('you', 'we', 'i')),
                           last_person)
        return roles, rel, marks, setting, last_person

    beat_maps: dict = {}
    for bi, (heading, para) in enumerate(_sb_beats(script)):
        compounds.clear()
        maps: list = []
        sents = [x for x in re.split(r'(?<=[.!?])\s+', para.strip())
                 if len(_WORD_RE.findall(x)) >= 3] or [para]
        if len(sents) == 1:
            roles, rel, marks, setting, last_person = _moment(
                sents[0], prev_rel, last_person, max_roles)
        else:
            roles, marks, setting = [], [], ''
            per = 4
            sents = _merge_moments(sents, _SB_MOMENTS)
            words_n = [len(_WORD_RE.findall(x)) for x in sents]
            moments = [{'at': round(sum(words_n[:k]) / sum(words_n), 3)}
                       for k in range(len(sents))]
            for k, s_ in enumerate(sents):
                n_maps = len(maps)
                r_, _rl, mk_, st_, last_person = _moment(
                    s_, '', last_person, per)
                if len(maps) > n_maps:
                    maps[-1]['_k'] = k
                off = len(roles)
                labs = [r['label'] for r in r_]
                if len(maps) == n_maps and not any(
                        r.get('annotate') for r in r_):
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
        if len(sents) == 1:
            moments = []
        else:
            _one_drawing(roles)
        prev_rel = rel
        sent = sents[-1]
        if setting:
            _roles_in_setting(roles, setting)
        hero, *rest = roles
        dur = max(4.0, len(para.split()) / wpm * 60 + 1.6)
        beats.append({
            'beat_id': f'b{bi + 1:02d}',
            'title': _sb_title(bi + 1, heading, roles, sent),
            # a scene drawn moment by moment labels each step on the board;
            # a single caption line would repeat one sentence of many
            'caption': '' if len(moments) >= 3 else _sb_caption(sent),
            'narration': para,
            'duration_seconds': round(dur, 2),
            'scene': {'sceneId': f'b{bi + 1:02d}', 'relation': rel,
                      'heroRole': hero, 'supportingRoles': rest,
                      'marks': marks,
                      **({'moments': moments} if moments else {}),
                      **({'events': [
                          {k: ev[k] for k in ('verb', 'kind', 'dir',
                                              'phrase')} | {
                              'agent': _ent_label(m_, ev['agent']),
                              'patient': _ent_label(m_, ev['patient'])}
                          for m_ in maps for ev in m_['events']]}
                         if maps else {}),
                      **({'setting': setting} if setting else {})},
        })
        if maps:
            beat_maps[len(beats) - 1] = (maps, sents)
    _cast_looks(beats)
    _noun_labels(beats)
    people = {r['label'] for b in beats for r in
              [b['scene']['heroRole']] + b['scene']['supportingRoles']
              if r.get('icon') == 'person'}
    story = {bi for bi, (maps, _s) in beat_maps.items()
             if sb_story.is_story_scene(maps, people)}
    # a script that is mostly story is told as one throughout
    if beat_maps and len(story) >= 0.6 * len(beat_maps):
        story = set(beat_maps)
    cast = sb_story.Cast()
    told: list = []
    for bi, (maps, sents_) in sorted(beat_maps.items()):
        if bi in story:
            sb_story.stage(beats[bi]['scene'], maps, sents_, cast,
                           lambda w: v3._icon_for(w))
            sp = scene_planner.plan(
                sents_, [p_ for p_ in cast.people if '#' not in p_],
                ' '.join(told[-2:]))
            if sp is not None:
                beats[bi]['scene']['plan_notes'] = scene_planner.apply(
                    beats[bi]['scene'], sp, sents_, cast)
            told.extend(sents_)
        else:
            _graph_scene(beats[bi]['scene'], maps)
            chart = _quantities(sents_)
            if chart is not None:
                sc = beats[bi]['scene']
                rs = [sc['heroRole']] + sc['supportingRoles']
                chart_words = {_lemma(w.lower()) for value in chart['values']
                               for w in re.findall(r'\w+', value['label']
                                                   + ' ' + value['unit'])}
                for r in rs:
                    if isinstance(r.get('to'), int):
                        r['to'] += 1
                    if isinstance(r.get('target'), int):
                        r['target'] += 1
                    if {_lemma(w.lower()) for w in r['label'].split()} \
                            <= chart_words:
                        r['charted'] = True
                sc['heroRole'] = {
                    'label': chart['unit'], 'icon': 'bar chart',
                    'glyph': 'quantity-chart', 'chart': chart,
                    'moment': 0, 'size': 1.0}
                sc['supportingRoles'] = rs
                sc.update(relation='comparison', layout='focus')
                sc.pop('graph', None)
    for bi, b in enumerate(beats):
        # a person persisting across moments is drawn once: the earliest
        # slot survives and inherits the later appearance's activity when
        # it has none of its own ('the agent' receives at 0, reads at 1).
        # A story redraws its cast in every panel.
        if bi in story:
            continue
        sc = b['scene']
        rs = [sc['heroRole']] + sc['supportingRoles']
        for k in range(len(rs) - 1, 0, -1):
            r = rs[k]
            if r.get('icon') != 'person':
                continue
            ident = r.get('cast_key') or r['label']
            j = next((j for j, q in enumerate(rs[:k])
                      if q.get('icon') == 'person'
                      and q.get('moment') != r.get('moment')
                      and (q.get('cast_key') or q['label']) == ident), None)
            if j is None:
                continue
            if not rs[j].get('activity') and r.get('activity'):
                for f_ in ('activity', 'action'):
                    if f_ in r:
                        rs[j][f_] = r[f_]
                pt_ = (r.get('activity') or {}).get('partner')
                if pt_:
                    pi_ = next((i_ for i_, q in enumerate(rs)
                                if i_ not in (j, k)
                                and q['label'] == pt_), None)
                    if pi_ is not None:
                        ti_ = pi_ - (pi_ > k)
                        if ti_ != j:
                            rs[j]['target'] = ti_
            for ge in (sc.get('graph') or {}).get('edges') or []:
                for f_ in ('from', 'to'):
                    if isinstance(ge.get(f_), int):
                        ge[f_] = (j if ge[f_] == k
                                  else ge[f_] - (ge[f_] > k))
            _merge_role(rs, k, j)
            if sc.get('graph'):
                sc['graph']['edges'] = [
                    ge for ge in sc['graph']['edges']
                    if ge.get('from') != ge.get('to')]
        # the same glyph must not draw twice in one scene: roles whose
        # art resolves identically merge onto the earliest one, keeping
        # both words on the surviving element
        for k in range(len(rs) - 1, 0, -1):
            r = rs[k]
            if r.get('icon') == 'person' or r.get('glyph'):
                continue
            art_ = v3.icon_for(r['icon'])
            j = next((j for j, q in enumerate(rs[:k])
                      if q.get('icon') != 'person' and not q.get('glyph')
                      and v3.icon_for(q['icon']) == art_), None)
            if j is None:
                continue
            old_ = str(r['label'])
            if str(rs[j]['label']) != old_:
                rs[j]['label'] = f"{rs[j]['label']} & {old_}"
            for mk in sc.get('marks') or []:
                for f_ in ('on', 'from', 'to'):
                    if str(mk.get(f_) or '') == old_:
                        mk[f_] = rs[j]['label']
            for ge in (sc.get('graph') or {}).get('edges') or []:
                for f_ in ('from', 'to'):
                    if isinstance(ge.get(f_), int):
                        ge[f_] = (j if ge[f_] == k
                                  else ge[f_] - (ge[f_] > k))
            _merge_role(rs, k, j)
            if sc.get('graph'):
                sc['graph']['edges'] = [
                    ge for ge in sc['graph']['edges']
                    if ge.get('from') != ge.get('to')]
        sc['heroRole'], sc['supportingRoles'] = rs[0], rs[1:]
    mode = 'story' if beat_maps and len(story) >= 0.6 * len(beat_maps) \
        else 'explain'
    heading = next((ln.strip()[2:].strip() for ln in script.splitlines()
                    if ln.strip().startswith('# ')), '')
    title = title or heading or _subject(script).title()
    pid = re.sub(r'\W+', '_', title.lower()).strip('_') or 'storyboard'
    return {'production_id': pid, 'title': title,
            'board_layout': 'storyboard',
            'mode': mode,
            'art_kit': art_kit,
            'brandExecution': {'brandAuthority': {
                'background': '#F7F2E7', 'ink': '#1A1A17',
                'accent': '#1A1A17', 'secondary': '#8B8577'}},
            'beats': beats}


def _detect_art_kit(script: str, v3) -> str:
    """The domain kit this script speaks: its keywords score against the
    script text; the leader past the _kit_live threshold wins the plan's
    art_kit so resolution is deterministic instead of context-lucky."""
    txt = ' ' + re.sub(r'[^a-z0-9]+', ' ', script.lower()) + ' '
    best, best_n = None, 0
    for dom, glyphs in v3._kits().items():
        if dom == 'world':
            continue
        hits = [k for meta in glyphs.values()
                for k in meta.get('keywords', ())
                if f' {k} ' in txt]
        if len(hits) > best_n:
            best, best_n = dom, len(hits)
    return best if best_n >= 3 else ''


# verbs that say one thing stands for / is tied to another
_EQUIV = {'back', 'represent', 'stand', 'mirror', 'track', 'follow', 'match',
          'equal', 'peg', 'mean', 'reflect', 'copy', 'link', 'tie', 'mimic',
          'correspond', 'symbolize', 'embody'}
_HOP_PREP = ('to', 'into', 'onto', 'in', 'inside', 'through', 'toward',
             'towards', 'until', 'across', 'via', 'over', 'on', 'at')
_VS_RE = re.compile(r"\b([a-z][\w-]*),?\s+not\s+(?:the\s+|a\s+|an\s+)?"
                    r"([a-z][\w-]*)|\binstead of\s+(?:the\s+|a\s+)?"
                    r"([a-z][\w-]*)", re.I)


# acts a diagram shows as a labelled link rather than a posed picture
_GRAPH_SCHEMAS = frozenset({'look', 'read', 'give', 'point', 'talk', 'hold',
                            'type', 'write'})


def _scene_graph(roles: list, maps: list):
    """The ideas a multi-sentence scene links, as a diagram: who/what acts
    on what (edge = the verb), where it goes next (edge = the preposition),
    what stands for what (backing), and what is contrasted (vs). Returns
    {'edges': [...]} when the scene explains relations between things
    rather than showing bodies doing physical acts; else None. Each thing
    is drawn once and every mention links to it."""
    phys = sum(1 for r in roles if r.get('activity') and (
        r['activity'].get('schema') not in _GRAPH_SCHEMAS))
    if len(roles) < 3:
        return None

    def host(i):
        seen = set()
        while isinstance(roles[i].get('to'), int) and roles[i].get(
                'attach') in ('held', 'on', 'in', 'worn', 'activity',
                              'behind', 'under') and i not in seen:
            seen.add(i)
            i = roles[i]['to']
        return i

    def node(label, k):
        if not label:
            return None
        lab = label.lower()
        head = lab.split()[-1]
        hits = [i for i, r in enumerate(roles)
                if r['label'].lower() == lab
                or str(r.get('cast_key') or '').lower() == lab
                or lab in r.get('aliases', ())
                or r['label'].lower().split()[-1] == head
                or lab.endswith(' ' + r['label'].lower())]
        if not hits:
            return None
        hits.sort(key=lambda i: (bool(roles[i].get('attach')),
                                 roles[i].get('moment') != k,
                                 abs((roles[i].get('moment') or 0) - k)))
        return host(hits[0])

    edges, seen = [], set()

    def add(a, b, text, kind, k):
        if a is None or b is None or a == b:
            return
        key = frozenset((a, b))
        if key in seen:
            return
        seen.add(key)
        edges.append({'from': a, 'to': b, 'text': text, 'kind': kind,
                      'moment': k})

    for sm in maps:
        k = sm.get('_k', 0)
        ents = sm['entities']
        def lab(eid):
            if eid is None:
                return None
            e = ents[eid]
            if e.get('of_part') is not None:
                e = ents[e['of_part']]
            return e['label']
        for ev in sm['events']:
            lem = ev['lemma']
            a = node(lab(ev['agent']), k)
            pt = node(lab(ev['patient']), k)
            preps = [(p_, node(lab(x), k)) for p_, x in ev['preps']]
            by = next((n for p_, n in preps if p_ == 'by'), None)
            if a is None and by is not None:
                a = by
            if a is None and pt is not None and lem != 'be':
                # 'Maria wants to buy a share': the unstated doer is the
                # person the scene is already about
                a = next((host(i) for i in range(len(roles) - 1, -1, -1)
                          if roles[i].get('icon') == 'person'
                          and (roles[i].get('moment') or 0) <= k), None)
            verb = ev['verb'].lower() + (' ' + ev['particle']
                                          if ev['particle'] else '')
            if lem == 'be':
                add(a, pt, 'is a', 'is', k)
                continue
            if lem in _EQUIV:
                tgt = pt if pt is not None and pt != a else next(
                    (n for p_, n in preps if p_ in ('for', 'to', 'with')
                     and n is not None), None)
                if by is not None and pt is not None:
                    add(by, pt, verb, 'backs', k)
                else:
                    add(a, tgt, verb, 'backs', k)
                continue
            kind = 'not' if ev.get('neg') else 'flow'
            hop = next(((p_, n) for p_, n in preps if (
                p_ in _HOP_PREP or p_ == 'for' and pt is not None)
                and n is not None), None)
            if pt is not None:
                add(a, pt, verb, kind, k)
                if hop is not None:
                    add(pt, hop[1], hop[0], kind, k)
            elif hop is not None:
                add(a, hop[1], f'{verb} {hop[0]}', kind, k)
            for p_, n in preps:
                if p_ in ('with', 'from', 'using') and n is not None:
                    add(n, pt if pt is not None else a, p_, 'flow', k)
        for x, p_, y in sm.get('links') or ():
            if p_ == 'of':
                # 'the price of the stock': the stock carries its price
                add(node(lab(y), k), node(lab(x), k), '', 'flow', k)
            else:
                add(node(lab(x), k), node(lab(y), k), p_, 'flow', k)
        for m in _VS_RE.finditer(sm.get('text') or ''):
            if m.group(3):
                continue
            add(node(m.group(1), k), node(m.group(2), k), 'not', 'vs', k)
    linked = {i for e in edges for i in (e['from'], e['to'])}
    if len(edges) < 2 or len(linked) < 3 or phys > 1:
        return None
    return {'edges': edges[:10]}


def _quantities(sents: list) -> dict | None:
    values = []
    for moment, sent in enumerate(sents):
        if re.search(r'\d\s*[-–]\s*\d|(?<!\d)-\s*\d|\b(about|roughly|approximately|'
                     r'nearly|between|less than|more than|up to|minus|hundred|'
                     r'thousand|million|billion|trillion|dozen)\b', sent, re.I):
            return None
        doc = scene_map._parse_doc(sent)
        if doc is None:
            return None
        for token in doc:
            if not re.fullmatch(r'\d+(?:,\d{3})*(?:\.\d+)?', token.text):
                continue
            verb = next((a for a in token.ancestors
                         if a.pos_ in ('VERB', 'AUX')), None)
            if verb is None or any(c.dep_ == 'neg' for c in verb.children):
                continue
            subject = next((c for c in verb.children
                            if c.dep_ in ('nsubj', 'nsubjpass')), None)
            if subject is None:
                continue
            unit = ''
            if token.dep_ in ('nummod', 'compound') and token.head.pos_ == 'NOUN':
                root = token.head
                while root.dep_ == 'compound' and root.head.pos_ == 'NOUN':
                    root = root.head
                parts, pending = [], [root]
                while pending:
                    part = pending.pop()
                    parts.append(part)
                    pending.extend(c for c in part.children if
                                   c.dep_ in ('compound', 'amod') and
                                   not c.like_num)
                unit = ' '.join(p.lemma_.lower() for p in sorted(
                    parts, key=lambda p: p.i))
            currency = doc[token.i - 1].text if token.i else ''
            if currency in ('$', '£', '€'):
                unit = currency
            elif token.i + 1 < len(doc) and doc[token.i + 1].text == '%':
                unit = '%'
            if not unit or unit.isdigit() or unit in ('year', 'month', 'day'):
                continue
            label = next((chunk.text for chunk in doc.noun_chunks
                          if chunk.root == subject), subject.text)
            label = re.sub(r'^(the|a|an)\s+', '', label, flags=re.I)
            # the setting the value belongs to ("In March", "by late
            # summer") is the axis when the subjects don't tell values apart
            setting = next((' '.join(t.text for t in c.subtree
                                     if t.dep_ != 'prep')
                            for c in verb.children
                            if c.dep_ == 'prep' and token not in c.subtree
                            and any(g.dep_ == 'pobj' for g in c.children)),
                           None)
            value = float(token.text.replace(',', ''))
            if not math.isfinite(value):
                return None
            values.append({'label': label, 'value': value, 'word': token.text,
                'unit': unit, 'measure': verb.lemma_, 'moment': moment,
                'source': sent, 'setting': setting,
                'pronoun': subject.pos_ == 'PRON'})
    if not 2 <= len(values) <= 6:
        return None
    settings = [v['setting'] for v in values]
    by_setting = (all(settings) and
                  len({x.lower() for x in settings}) == len(values))
    if by_setting:
        for v in values:
            v['label'] = v['setting']
    elif len({(v['unit'], v['measure']) for v in values}) != 1 or \
            any(v['pronoun'] for v in values):
        return None
    if len({v['unit'] for v in values}) != 1:
        return None
    if len({v['label'].lower() for v in values}) != len(values):
        return None
    for v in values:
        del v['setting'], v['pronoun']
    if max(v['value'] for v in values) <= 0:
        return None
    return {'unit': values[0]['unit'], 'baseline': 0, 'values': values}


def _graph_scene(sc: dict, maps: list) -> None:
    """An explaining scene becomes one diagram: each thing is drawn once
    (later mentions link back to it) and the scene carries its edges."""
    rs = [sc['heroRole']] + sc['supportingRoles']
    loose = ('activity', 'in', 'behind')
    trial = [dict(r) for r in rs]
    for r in trial:
        if r.get('attach') in loose:
            r.pop('attach')
            r.pop('to', None)
    if _scene_graph(trial, maps) is None:
        return
    # a diagram draws each thing as its own node: things an actor works
    # on or sits in become linked nodes, not parts of the actor's picture
    for r in rs:
        r.pop('activity', None)
        if r.get('attach') in loose:
            r.pop('attach')
            r.pop('to', None)
    for k in range(len(rs) - 1, 0, -1):
        r = rs[k]
        if r.get('attach'):
            continue
        ident = (r.get('cast_key') or r['label']).lower()
        j = next((j for j, q in enumerate(rs[:k]) if not q.get('attach')
                  and q.get('icon') == r.get('icon')
                  and (q.get('cast_key') or q['label']).lower() == ident),
                 None)
        if j is None:
            continue
        for q in rs:
            if q.get('to') == k:
                q['to'] = j
        rs[j]['aliases'] = sorted(set(rs[j].get('aliases', []))
                                  | {r['label'].lower()}
                                  | set(r.get('aliases', [])))
        _merge_role(rs, k, j)
    graph = _scene_graph(rs, maps)
    if graph is None:
        return
    edge_verbs = {(str(ge.get('text') or '').split() or [''])[0].lower()
                  for ge in graph['edges']}
    for r_ in rs:
        ann = str(r_.get('annotate') or '').split()
        if len(ann) > 1 and ann[0].lower()[:4] in {v[:4]
                                                 for v in edge_verbs}:
            r_['annotate'] = ' '.join(ann[1:])
    for r in rs:
        if r.get('attach'):
            continue
        name = str(r.get('cast_key') or r['label'])
        ann = str(r.get('annotate') or '').split()
        head = name.split()
        if r.get('icon') == 'person' or len(ann) < len(head) or [
                _lemma(w) for w in ann[-len(head):]] != [
                _lemma(w) for w in head]:
            r['annotate'] = name
        else:
            r['annotate'] = ' '.join(
                [w for w in ann[:-len(head)] if _is_adj(w)] + head)
    sc['heroRole'], sc['supportingRoles'] = rs[0], rs[1:]
    sc.update(relation='explain', layout='graph', graph=graph)


def _one_drawing(roles: list) -> None:
    """A thing an activity picture draws (the truck someone drives) is not
    drawn a second time as a loose icon in another moment of the scene."""
    partners = {}
    for k, r in enumerate(roles):
        p_ = (r.get('activity') or {}).get('partner')
        if p_:
            partners.setdefault(p_, next(
                (j for j, q in enumerate(roles) if q['label'] == p_
                 and q.get('attach') in ('activity', 'held')
                 and q.get('to') == k), None))
    for k in range(len(roles) - 1, -1, -1):
        r = roles[k]
        keep = partners.get(r['label'])
        if r['icon'] == 'person' or 'attach' in r or keep is None \
                or keep == k or r['icon'] != roles[keep]['icon'] \
                or any(q.get('to') == k for q in roles):
            continue
        _merge_role(roles, k, keep)


def _merge_role(roles: list, k: int, keep: int) -> None:
    """Delete roles[k]; references to it move to roles[keep]."""
    del roles[k]
    for q in roles:
        if isinstance(q.get('to'), int):
            q['to'] = keep if q['to'] == k else q['to'] - (q['to'] > k)
        t_ = q.get('target')
        if isinstance(t_, int) and not isinstance(t_, bool):
            q['target'] = (keep - (keep > k) if t_ == k
                           else t_ - (t_ > k))


def _is_adj(w: str) -> bool:
    return bool(_wn is not None and (_wn.synsets(w, 'a') or _wn.synsets(w, 's'))
                and (_wn.morphy(w, 'v') in (None, w)))


def _noun_labels(beats: list) -> None:
    """Board labels name the thing, not the sentence: 'climbed tall
    ladder' on the ladder reads 'tall ladder'; a label that only repeats
    the drawn noun ('read newspaper' on the newspaper) is dropped."""
    for b in beats:
        sc = b['scene']
        for r in [sc['heroRole']] + sc['supportingRoles']:
            ann = str(r.get('annotate') or '').strip()
            if not ann or r.get('icon') == 'person':
                continue
            words = ann.split()
            head = r['label'].split()[-1].lower()
            at = next((k for k, w in enumerate(words)
                       if _lemma(w.lower()) == head or w.lower() == head),
                      None)
            if at is None:
                r.pop('annotate', None)
                continue
            k = at
            while k and _is_adj(words[k - 1].lower()) \
                    and words[k - 1].lower() not in {
                        'outside', 'inside', 'around', 'under', 'over',
                        'behind', 'beside', 'near', 'through', 'along',
                        'across', 'from', 'into', 'onto', 'with', 'at'}:
                k -= 1
            np_ = words[k:at + 1]
            verb = at > 0 and k == at and _wn is not None and bool(
                _wn.morphy(words[0].lower(), 'v'))
            if verb and sc.get('mode') != 'story':
                r['annotate'] = f'{words[0]} {words[at]}'
            else:
                r['annotate'] = ' '.join(np_)


_PRO_F = re.compile(r'\b(she|her|hers|herself)\b', re.I)
_PRO_M = re.compile(r'\b(he|him|his|himself)\b', re.I)
_YOUNG = re.compile(r'\b(little|small|tiny|baby|infant)\s+$', re.I)


def _cast_looks(beats: list) -> None:
    """Bind each cast member's sex (from the pronouns that follow it
    through the narration) and child age ('the little baker') onto every
    role with that label, so the renderer can tell people apart."""
    roles = [r for b in beats for r in
             [b['scene']['heroRole']] + b['scene']['supportingRoles']
             if r.get('icon') == 'person']
    labels = sorted({r['label'] for r in roles
                     if r['label'] not in ('you', 'we', 'i')},
                    key=len, reverse=True)
    # one person under several names: 'the keeper' after 'the lighthouse
    # keeper', or 'her husband, a bearded fisherman'
    qualified = {r['label'] for r in roles if r.get('member_qualifier')}
    root = {lab: next((o for o in labels if o not in qualified
                      and o.endswith(' ' + lab)), lab)
            for lab in labels}
    text = ' '.join(b.get('narration') or '' for b in beats)
    for a_ in labels:
        for b_ in labels:
            if a_ != b_ and re.search(
                    r'\b' + re.escape(a_) + r',\s+(an?|the)\s+(\w+\s+){0,2}?'
                    + re.escape(b_) + r'\b', text, re.I):
                root[b_] = root[a_]
            # 'a young firefighter named Leo': one person, two names
            if a_ != b_ and re.search(
                    r'\b' + re.escape(a_) + r'\s+(named|called)\s+'
                    + re.escape(b_) + r'\b', text, re.I):
                root[b_] = root[a_]
    votes: dict = {lab: [0, 0] for lab in labels}
    young: set = set()
    elderly: set = set()
    bearded: set = set()
    cur = ''
    recent: list = []
    for b in beats:
        for sent in re.split(r'(?<=[.!?])\s+', b.get('narration') or ''):
            prior, prior_recent = cur, list(recent)
            hits = []
            for lab in labels:
                m = re.search(r'\b' + re.escape(lab) + r's?\b', sent, re.I)
                if m and not any(h <= m.start() < h + len(o)
                                 for h, o in hits):
                    hits.append((m.start(), lab))
                    pre = sent[:m.start()]
                    if _YOUNG.search(pre):
                        young.add(root[lab])
                    if re.search(r'\b(old|elderly|elder|senior)\s+$',
                                 pre, re.I):
                        elderly.add(root[lab])
                    if re.search(r'\b(bearded|beard(ed)?)\s+$', pre, re.I):
                        bearded.add(root[lab])
            if hits:
                cur = root[min(hits)[1]]
                for _h, lab in sorted(hits):
                    if root[lab] in recent:
                        recent.remove(root[lab])
                    recent.append(root[lab])
            # a pronoun names the latest referent its gender can fit:
            # 'his granddaughters follow him' -> him is not a granddaughter
            for pro, idx in ((_PRO_F, 0), (_PRO_M, 1)):
                want = 'fm'[idx]
                for mention in pro.finditer(sent):
                    before = [root[lab] for at, lab in sorted(
                        hits, reverse=True) if at < mention.start()]
                    clause = sent[:mention.start()]
                    if re.search(r'\band\s*$', clause, re.I):
                        subjects = [root[lab] for at, lab in hits
                                    if re.search(
                                        r'\b' + re.escape(lab) +
                                        r's?\b[^.!?;]*\b\w+(?:ed|s)\b',
                                        clause, re.I)]
                        if subjects:
                            before = subjects[-1:] + [
                                c for c in before if c != subjects[-1]]
                    candidates = before + ([prior] if prior else []) + \
                        prior_recent[::-1]
                    fit = next((c for c in candidates
                                if sb_cast.lexical_sex(c) in ('', want)), '')
                    if fit:
                        votes[fit][idx] += 1
    for r in roles:
        k = root.get(r['label'], r['label'])
        f, m = votes.get(k, (0, 0))
        if k != r['label']:
            r.setdefault('cast_key', k)
        lex = sb_cast.lexical_sex(r['label'])
        if lex:
            r['gender'] = lex
        elif f != m and 'gender' not in r:
            r['gender'] = 'f' if f > m else 'm'
        if k in young:
            r.setdefault('age', 'child')
        elif k in elderly:
            r.setdefault('age', 'elder')
        if k in bearded:
            r.setdefault('beard', 'full')
    for b in beats:
        # the same person twice in one moment is drawn once
        sc = b['scene']
        rs = [sc['heroRole']] + sc['supportingRoles']
        for k in range(len(rs) - 1, 0, -1):
            r = rs[k]
            ident = r.get('cast_key') or r['label']
            j = next((j for j, q in enumerate(rs[:k])
                      if q.get('icon') == 'person' == r.get('icon')
                      and q.get('moment') == r.get('moment')
                      and (q.get('cast_key') or q['label']) == ident), None)
            if j is not None and not any(q.get('to') == k for q in rs):
                _merge_role(rs, k, j)
        sc['heroRole'], sc['supportingRoles'] = rs[0], rs[1:]


def _ent_label(sm: dict, eid):
    return sm['entities'][eid]['label'] if eid is not None else None


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
