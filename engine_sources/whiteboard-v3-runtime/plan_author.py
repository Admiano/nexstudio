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
            if not hero:
                hero = 'idea'
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


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('script', help='script text file (one beat per line)')
    ap.add_argument('--type', default='diagram',
                    choices=('diagram', 'kinetic', 'whiteboard'))
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
