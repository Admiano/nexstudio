"""Noun coverage: every concrete thing the narration names on a picture-book page is drawn there.

A page that says "the fox jumped over the log" and prints only a fox has quietly lost the log.
The gate reads each beat's narration for determiner-headed noun phrases, keeps the ones the
lexicon knows as concrete (animal, artifact, body, food, object, person, plant, substance...),
and requires each to be answered by something printed on that page: an illustration entity,
a scene element, a backdrop plate, the figure's prop, the teaching block's objects, or — for
people — the performer. What is left is reported as NOUN_NOT_DRAWN and fails the build.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Set, Tuple

from .directing import IRREGULAR, VERB_KIND
from .lexicon import NounLexicon, singular

DETERMINERS = frozenset((
    'the', 'a', 'an', 'his', 'her', 'their', 'my', 'our', 'your', 'its', 'this', 'that', 'these', 'those',
    'some', 'every', 'each', 'another', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine',
    'ten', 'eleven', 'twelve', 'many', 'several', 'no', 'both', 'all',
))
# Words that sit between a determiner and its noun.
MODIFIERS = frozenset((
    'tiny', 'little', 'big', 'small', 'tall', 'short', 'old', 'new', 'young', 'bright', 'dark', 'red', 'blue',
    'green', 'yellow', 'orange', 'purple', 'pink', 'white', 'black', 'brown', 'golden', 'silver', 'round', 'long',
    'huge', 'giant', 'soft', 'warm', 'cold', 'hot', 'full', 'empty', 'whole', 'last', 'first', 'next', 'other',
    'same', 'final', 'great', 'good', 'happy', 'sad', 'quiet', 'loud', 'wide', 'deep', 'high', 'low', 'pale',
    'shiny', 'sleepy', 'hungry', 'thirsty', 'brave', 'clever', 'kind', 'wild', 'wooden', 'heavy', 'light',
    'more', 'most', 'very', 'magic', 'secret', 'lovely', 'beautiful', 'silly', 'fluffy', 'furry', 'ripe',
))
# The printed environment: every picture-book page stands on ground under a sky.
ENVIRONMENT = frozenset(('sky', 'ground', 'air', 'land', 'earth', 'world', 'soil', 'dirt', 'floor', 'page', 'book',
                         'place', 'way', 'side', 'top', 'bottom', 'end', 'middle', 'edge', 'front', 'back', 'inside',
                         'outside', 'home', 'room', 'distance', 'shade', 'shadow', 'light', 'darkness'))
# One object seen in its states: any stage prints the thing.
STATE_FAMILIES = (
    frozenset(('seed', 'sprout', 'seedling', 'shoot', 'plant', 'sapling', 'stem', 'bud', 'flower', 'bloom', 'blossom')),
    frozenset(('moon', 'crescent', 'half-moon', 'full-moon', 'new-moon')),
    frozenset(('egg', 'chick', 'hatchling', 'shell', 'eggshell')),
    frozenset(('caterpillar', 'chrysalis', 'cocoon', 'butterfly', 'pupa', 'larva')),
    frozenset(('tadpole', 'frog', 'frogspawn')),
    frozenset(('acorn', 'oak', 'tree')),
    frozenset(('ice', 'water', 'puddle', 'snow', 'snowman')),
    frozenset(('candle', 'flame', 'fire', 'wick')),
)
# The scene setting prints its own place: an urban page is the town, an underwater page the sea.
SETTING_NOUNS = {
    'urban': frozenset(('town', 'city', 'street', 'road', 'village')),
    'outdoor': frozenset(('field', 'garden', 'meadow', 'park', 'grass', 'countryside', 'yard')),
    'ground': frozenset(('soil', 'earth', 'underground', 'mud')),
    'underwater': frozenset(('sea', 'ocean', 'water', 'seabed')),
    'space': frozenset(('space', 'universe', 'cosmos')),
    'indoor': frozenset(('room', 'house', 'home')),
}
# Relational roles name how printed things stand to each other, not a new thing.
ROLES = frozenset(('partner', 'friend', 'team', 'family', 'neighbour', 'neighbor', 'helper', 'twin', 'pair'))
# Words whose everyday sense on a page is another printed concept.
ALIASES = {'cup': ('trophy',), 'ocean': ('wave',), 'sea': ('wave',), 'pond': ('wave',), 'lake': ('wave',),
           'floodlight': ('streetlamp', 'lamp'), 'town': ('skyline', 'building', 'house'), 'city': ('skyline', 'building')}
SIMILE = frozenset(('like', 'as'))
RUNTIME = Path(__file__).resolve().parents[2] / 'runtime' / 'editorial-runtime.js'
# Resolutions that put a picture of the concept itself on the page (not its ancestor, not its word).
DRAWN_VIA = frozenset(('exact', 'synonym', 'bank', 'photo'))


@lru_cache(maxsize=1)
def paper_art() -> Tuple[FrozenSet[str], Dict[str, str]]:
    """The runtime's authored PAPER_ART keys and PAPER_ALIAS table, read from the runtime source."""
    src = RUNTIME.read_text(encoding='utf-8')
    a0 = src.index('const PAPER_ART = {')
    art = frozenset(m.group(1) or m.group(2) for m in re.finditer(r"^    (?:'([a-z0-9_-]+)'|([a-z0-9_]+)): \[", src[a0:src.index('\n  };', a0)], re.M))
    b0 = src.index('const PAPER_ALIAS = {')
    body = src[b0:src.index('\n  };', b0)]
    alias = {(m.group(1) or m.group(2)): m.group(3) for m in re.finditer(r"(?:'([a-z0-9_-]+)'|\b([a-z0-9_]+)): '([a-z0-9_-]+)'", body)}
    return art, alias


def paper_key(concept: str) -> Optional[str]:
    """The authored art the runtime prints for a concept (mirrors runtime paperArtKey)."""
    art, alias = paper_art()
    words = re.sub(r'[^a-z0-9]+', ' ', str(concept).lower()).split()
    if not words:
        return None
    for n in range(len(words), 0, -1):
        for c in ('-'.join(words[len(words) - n:]), '-'.join(words[:n])):
            k = alias.get(c, c)
            if k in art:
                return k
    return None
WORD_RE = re.compile(r"[a-z][a-z'-]*")


BREAKS = frozenset((
    'and', 'or', 'but', 'of', 'to', 'in', 'on', 'at', 'by', 'with', 'for', 'from', 'into', 'onto', 'over', 'under',
    'up', 'down', 'out', 'off', 'near', 'behind', 'beside', 'through', 'across', 'around', 'past', 'is', 'was',
    'are', 'were', 'be', 'been', 'has', 'had', 'have', 'will', 'would', 'can', 'could', 'did', 'does', 'then',
    'so', 'as', 'than', 'that', 'which', 'who', 'while', 'when', 'where', 'all', 'too', 'again', 'away', 'now',
))


COPULA = frozenset(('is', 'was', 'were', 'are', 'am', 'be', 'became', 'become', 'becomes', 'seemed', 'stayed'))
# Parts and positions of a thing already on the page, not things of their own.
PARTS = frozenset(('center', 'centre', 'face', 'sliver', 'piece', 'part', 'bit', 'half', 'horizon', 'rest', 'lot',
                   'kind', 'sort', 'type', 'row', 'group', 'pair', 'set', 'number', 'shape', 'size', 'colour', 'color'))
COMMON_VERBS = frozenset(('come', 'go', 'drink', 'open', 'step', 'sit', 'look', 'see', 'run', 'make', 'take', 'get',
                          'give', 'grow', 'sleep', 'wake', 'stand', 'fall', 'rise', 'shine', 'turn', 'reach', 'push',
                          'pull', 'sing', 'play', 'eat', 'hide', 'wait', 'rest', 'swim', 'fly', 'jump', 'land', 'stay'))


def _verbish(t: str) -> bool:
    if t.endswith('ed') or t in IRREGULAR or (VERB_KIND.get(t) is not None and t not in ('ball', 'light')):
        return True
    stem = t[:-2] if t.endswith('es') and t[:-2] in COMMON_VERBS else t[:-1] if t.endswith('s') else ''
    return bool(stem) and (stem in COMMON_VERBS or VERB_KIND.get(stem) is not None)


def noun_phrases(narration: str) -> List[Tuple[str, List[str]]]:
    """(determiner, run) for every determiner-headed noun phrase: the words after the
    determiner up to punctuation, a function word or a verb (at most three)."""
    out: List[Tuple[str, List[str]]] = []
    for clause in re.split(r"[,.;:!?\u2014\u2013()\"]+", narration.lower()):
        toks = [t.strip("'") for t in WORD_RE.findall(clause)]
        for i, t in enumerate(toks):
            if t not in DETERMINERS or (i > 0 and (toks[i - 1] in COPULA or toks[i - 1] in SIMILE)):
                continue
            run: List[str] = []
            for u in toks[i + 1:i + 5]:
                if u in DETERMINERS or u in BREAKS or (run and _verbish(u)):
                    break
                run.append(u)
            if run:
                out.append((t, run))
    return out


class NounGate:
    def __init__(self, lexicon: Optional[NounLexicon] = None, scene_shapes: Iterable[str] = ()):
        self.lex = lexicon or NounLexicon()
        self.shapes = frozenset(scene_shapes)

    @staticmethod
    def entity_drawn(e: Any) -> bool:
        """The entity prints its own concept: authored paper art, or a mark/plate of the thing itself."""
        if paper_key(e.concept):
            return True
        via = ((e.params or {}).get('resolution') or {}).get('via')
        return via in DRAWN_VIA

    def _concrete(self, word: str) -> Optional[Tuple[str, bool]]:
        """(lemma, is_person) when the word's everyday sense is a drawable thing."""
        lemma = self.lex.lemma(word)
        if lemma is None:
            return None
        senses = self.lex.senses(lemma, 1)
        if not senses or not self.lex.depictable(senses[0]):
            return None
        return lemma, self.lex.is_person(senses[0])

    def things(self, narration: str) -> List[Tuple[str, str, bool]]:
        """(word as spoken, lemma, is_person) for each concrete noun the sentence names."""
        seen: Set[str] = set()
        out: List[Tuple[str, str, bool]] = []
        for _det, run in noun_phrases(narration):
            word, hit, head = '', None, ''
            for k in range(len(run) - 1, -1, -1):
                if run[k] in MODIFIERS:
                    continue
                if k > 0 and run[k - 1] not in MODIFIERS:
                    two = self._concrete(f'{run[k - 1]} {run[k]}')
                    if two is not None and '_' in two[0]:
                        word, hit, head = f'{run[k - 1]} {run[k]}', two, run[k]
                        break
                one = self._concrete(run[k])
                if one is not None:
                    word, hit, head = run[k], one, run[k]
                    break
            if hit is None or singular(head) in ENVIRONMENT or singular(head) in PARTS or hit[0] in seen:
                continue
            seen.add(hit[0])
            out.append((word, hit[0], hit[1]))
        return out

    def _answers(self, lemma: str, word: str, printed: Iterable[str]) -> bool:
        w = {singular(x) for x in re.split(r'[\s_-]+', word)} | {lemma.replace('_', '-'), lemma.replace('_', ' ')}
        for c in printed:
            cn = c.lower().strip()
            parts = {singular(x) for x in re.split(r'[\s_-]+', cn) if x}
            if w & parts or cn in w:
                return True
            if any((w | {singular(lemma)}) & fam and (parts | {cn}) & fam for fam in STATE_FAMILIES):
                return True
            if self.lex.available and self.lex.related(lemma.replace('_', ' '), cn.replace('-', ' ')):
                return True
        return False

    def beat_misses(self, beat: Any) -> List[str]:
        printed: List[str] = []
        il = beat.illustration
        if il is not None:
            printed += [e.concept for e in il.entities if e.concept and self.entity_drawn(e)]
        edu = (beat.page or {}).get('edu') or {}
        if edu.get('object'):
            printed.append(str(edu['object']))
        scene = beat.scene or {}
        resolved = scene.get('resolved') or {}
        printed += [str(x) for x in scene.get('elements') or [] if str(x).lower() in self.shapes or x in resolved]
        printed += [str(p.get('concept')) for p in beat.backdrop or [] if p.get('concept') and (p.get('asset') or paper_key(str(p['concept'])))]
        fig = beat.figure
        if fig is not None and fig.prop and fig.prop.get('concept'):
            printed.append(str(fig.prop['concept']))
        misses = []
        for word, lemma, person in self.things(beat.narration or ''):
            if person and fig is not None:
                continue
            head = singular(word.split()[-1])
            if head in ROLES or head in SETTING_NOUNS.get(str(scene.get('setting') or ''), ()):
                continue
            if any(a in printed for a in ALIASES.get(head, ())) or self._answers(lemma, word, printed):
                continue
            misses.append(word)
        return misses

    def film_failures(self, film: Any) -> List[str]:
        out = []
        for b in film.beats:
            for e in (b.illustration.entities if b.illustration else []):
                if e.concept and not self.entity_drawn(e) and self._concrete(e.concept):
                    via = ((e.params or {}).get('resolution') or {}).get('via')
                    out.append(f'CONCEPT_NOT_DRAWN:{b.beat_id}:{e.id}: {e.concept!r} prints only as {via} — no art draws the thing itself')
            for w in self.beat_misses(b):
                out.append(f'NOUN_NOT_DRAWN:{b.beat_id}:{w!r} is named in the narration but nothing on the page draws it')
        return out
