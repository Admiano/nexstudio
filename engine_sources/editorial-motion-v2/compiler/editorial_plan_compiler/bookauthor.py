"""Offline picture-book author: any plain story script -> a paperbook treatment.

Deterministic and free: pages follow the voice's own sentence groups; each page draws
only the concrete things its sentence names that the book can print (authored paper
art first, then the open flat libraries); number sentences become teaching layouts;
setting and light carry from page to page until the words change them. Nothing is
invented to fill a page — the director and the gates decide what moves.
"""
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .coverage import STAND_INS, NounGate, paper_key, young_of
from .illustration import IllustrationRegistry
from .lexicon import AssetFinder, NounLexicon, singular

PACKS = ('emoji.fluent-flat', 'emoji.noto')
MAX_THINGS = 3
# The scene engine paints the land and sky itself; a separate mark of them is a sticker.
LANDFORMS = frozenset(('hill', 'hills', 'mountain', 'mountains', 'field', 'grass', 'sky', 'ground', 'land', 'meadow', 'farm', 'sea', 'ocean'))
SAME_PLURAL = frozenset(('sheep', 'fish', 'ice', 'snow', 'deer', 'moose', 'bison', 'salmon'))
NUMBERS = {w: i for i, w in enumerate(
    'zero one two three four five six seven eight nine ten eleven twelve'.split())}
SETTING_WORDS: Sequence[Tuple[str, Tuple[str, ...]]] = (
    ('space', ('space', 'planet', 'planets', 'rocket', 'astronaut', 'orbit', 'galaxy', 'comet')),
    ('underwater', ('underwater', 'ocean', 'sea', 'reef', 'seabed', 'coral')),
    ('indoor', ('kitchen', 'room', 'bedroom', 'house', 'home', 'inside', 'indoors', 'table', 'bed', 'classroom')),
    ('urban', ('city', 'street', 'town', 'road', 'traffic')),
    ('outdoor', ('outside', 'garden', 'field', 'park', 'forest', 'meadow', 'farm', 'yard', 'hill', 'grass', 'mountain', 'woods')),
)
MOOD_WORDS: Sequence[Tuple[str, Tuple[str, ...]]] = (
    ('night', ('night', 'bedtime', 'moon', 'stars', 'midnight', 'dark', 'asleep')),
    ('dawn', ('morning', 'sunrise', 'dawn', 'woke')),
    ('dusk', ('evening', 'sunset', 'dusk')),
    ('storm', ('storm', 'thunder', 'lightning', 'rain', 'raining', 'rainy')),
    ('day', ('day', 'sun', 'sunny', 'noon', 'afternoon')),
)


def _words(text: str) -> List[str]:
    return re.findall(r"[a-z']+|\d+", text.lower())


def _num(w: str) -> Optional[int]:
    return int(w) if w.isdigit() else NUMBERS.get(w)


def _pick(words: List[str], table: Sequence[Tuple[str, Tuple[str, ...]]]) -> Optional[str]:
    for name, keys in table:
        if any(w in keys for w in words):
            return name
    return None


def edu_of(text: str, things: List[str]) -> Optional[Dict[str, Any]]:
    """A number sentence -> the teaching layout it states, else None."""
    ws = _words(text)
    nums = [n for n in (_num(w) for w in ws) if n is not None]
    if not things or not nums:
        return None
    obj, t = things[0], ' '.join(ws)
    two = len(nums) >= 2
    for op, kind in (('plus', 'add'), ('minus', 'subtract'), ('take away', 'subtract'),
                     ('times', 'multiply'), ('divided by', 'share')):
        m = re.search(r'(\w+) ' + op + r' (\w+)', t)
        if m and _num(m.group(1)) is not None and _num(m.group(2)) is not None:
            return {'kind': kind, 'object': obj, 'a': _num(m.group(1)), 'b': _num(m.group(2))}
    if two and ('times' in ws or 'rows' in ws or 'groups' in ws):
        return {'kind': 'multiply', 'object': obj, 'a': nums[0], 'b': nums[1]}
    if two and ('share' in ws or 'shared' in ws or 'divided' in ws or 'between' in ws):
        return {'kind': 'share', 'object': obj, 'a': nums[0], 'b': nums[1]}
    if two and ('plus' in ws or 'more' in ws or 'add' in ws):
        return {'kind': 'add', 'object': obj, 'a': nums[0], 'b': nums[1]}
    if two and ('minus' in ws or 'take away' in t or 'away' in ws or 'left' in ws):
        return {'kind': 'subtract', 'object': obj, 'a': nums[0], 'b': nums[1]}
    if 'count' in ws or len(nums) >= 3:
        return {'kind': 'count', 'object': obj, 'a': max(nums)}
    for k, w in enumerate(ws[:-1]):
        n = _num(w)
        if n is not None and n >= 2 and singular(ws[k + 1]) in things:
            # "Seven fish swam": a number naming a printed set is a count the page must show.
            return {'kind': 'count', 'object': singular(ws[k + 1]), 'a': n}
    return None


class BookAuthor:
    def __init__(self) -> None:
        reg = IllustrationRegistry()
        self.lex = NounLexicon()
        self.finder = AssetFinder(reg.items, self.lex, reg.quarantined)
        self.gate = NounGate(self.lex)

    def printable(self, concept: str) -> bool:
        if concept in LANDFORMS:
            return False
        if paper_key(concept):
            return True
        return any(self.finder.resolve(concept, p, True, True).via in ('exact', 'synonym') for p in PACKS)

    def stand_in(self, head: str, lemma: str, word: str) -> Optional[str]:
        """The next-best printable thing for a noun the book cannot draw: its nearest
        drawable ancestor (icicle -> ice, lantern -> lamp), accepted only when the
        coverage gate reads it as answering the noun."""
        for p in PACKS:
            r = self.finder.resolve(head, p, True, True)
            if r.via == 'composite' and r.path:
                cand = singular(str(r.path[-1]))
                if cand != head and self.printable(cand) and self.gate.answered_by(lemma, word, [cand]):
                    return cand
        return None

    def things(self, text: str) -> List[str]:
        out: List[str] = []
        ws = _words(text)
        # Number-headed nouns ("five sheep", "two more birds") name the things a count shows.
        for k, w in enumerate(ws[:-1]):
            if _num(w) is not None:
                nxt = ws[k + 2] if ws[k + 1] == 'more' and k + 2 < len(ws) else ws[k + 1]
                c = singular(nxt)
                c = c if self.printable(c) else young_of(c)
                if _num(nxt) is None and c not in out and self.gate.things(f'the {nxt}') and self.printable(c):
                    out.append(c)
        for m in re.finditer(r'\b(?:rows|groups|piles|baskets|bags|lots) of (\w+)', ' '.join(ws)):
            c = singular(m.group(1))
            if c not in out and self.printable(c):
                out.append(c)
        for word, lemma, person in self.gate.things(text):
            head = singular(word.split()[-1])
            sub = STAND_INS.get(head)
            if sub and self.printable(sub):
                if sub not in out:
                    out.append(sub)
                continue
            if person:
                if self.printable(head) and head not in out:
                    out.append(head)
                continue
            for c in (lemma.replace('_', ' '), head, young_of(head)):
                if self.printable(c) and c not in out:
                    out.append(c)
                    break
            else:
                stand = None if head in LANDFORMS else self.stand_in(head, lemma, word)
                if stand and stand not in out:
                    out.append(stand)
        return out[:MAX_THINGS]

    def author(self, groups: List[List[Dict[str, Any]]], film_id: str) -> Dict[str, Any]:
        beats: List[Dict[str, Any]] = []
        setting, mood = 'outdoor', 'day'
        motif: Optional[str] = None
        prev_things: List[str] = []
        for i, g in enumerate(groups):
            text = re.sub(r'\s+([,.;:!?])', r'\1', ' '.join(' '.join(w['text'] for w in g).split()))
            ws = _words(text)
            setting = _pick(ws, SETTING_WORDS) or setting
            mood = _pick(ws, MOOD_WORDS) or mood
            things = self.things(text)
            if not things and prev_things:
                # A sentence that names nothing drawable continues the page before it:
                # "Six take away two" still counts the icicles just named.
                things = list(prev_things)
            edu = edu_of(text, things)
            prev_things = things or prev_things
            page: Dict[str, Any] = {'title': self.title(things, edu), 'layout': 'half'}
            beat: Dict[str, Any] = {
                'beat_id': f'b{i + 1:02d}',
                'beat_type': 'HOOK' if i == 0 else ('PAYOFF' if i == len(groups) - 1 else 'SETUP'),
                'pattern': 'HERO_SCALE_PROMOTION', 'narration': text,
                'energy': 0.5, 'complexity': 0.4, 'page': page,
                'scene': {'setting': setting, 'mood': mood},
            }
            if not edu and not things:
                named = [w for w, _, person in self.gate.things(text) if not person]
                raise ValueError(f'UNPRINTABLE_BEAT: beat {i + 1} names nothing the book can draw '
                                 f'({", ".join(named) or "no concrete noun"}): "{text}"')
            if edu:
                page['edu'] = edu
            elif things:
                motif = motif or things[0]
                ents = [{'id': re.sub(r'[^a-z0-9]+', '_', c), 'kind': 'object', 'glyph': 'TILE',
                         'size': 'hero' if k == 0 else 'support', 'concept': c} for k, c in enumerate(things)]
                beat['illustration'] = {
                    'form': 'OBJECT_STAGE', 'entities': ents, 'relations': [],
                    'program': [{'op': 'DRAW', 'target': e['id'], 'at': {'offset_ms': 250 + 150 * k},
                                 'duration_ms': 600, 'from': 0.0, 'to': 1.0} for k, e in enumerate(ents)]}
            beats.append(beat)
        return {
            'schema': 'NexStudioEditorialTreatmentV2', 'film_id': film_id,
            'note': 'authored offline by bookauthor from the plain script',
            'aspects': ['16x9'], 'fps': 30,
            'brand': {'ink': '#3a2a1e', 'paper': '#f4ead6', 'accent': '#c8553d', 'finish': 'PAPER'},
            'typography': {'reveal': 'WORD_CASCADE', 'tonal_ink': 0.42, 'min_visual_share': 0.6},
            'voice': {'source': 'MASTER', 'audio_path': 'voice.mp3', 'alignment_path': 'alignment.json', 'head_pad_ms': 350},
            'media_library': [],
            'world': {'grain': 'grain-fine', 'motif': {'concept': motif or 'star', 'corner': 'bottom-right'}, 'book': 'paperbook'},
            'beats': beats,
        }

    @staticmethod
    def title(things: List[str], edu: Optional[Dict[str, Any]]) -> str:
        if edu:
            form = {'count': 'Count the {}s', 'add': 'More {}s', 'subtract': 'Fewer {}s',
                    'multiply': 'Rows of {}s', 'share': 'Sharing {}s'}[edu['kind']]
            obj = str(edu['object'])
            return form.replace('{}s', obj if obj in SAME_PLURAL else obj + 's').title()
        return f'The {things[0].title()}' if things else 'And Then'
