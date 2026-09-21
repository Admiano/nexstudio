"""Concept → asset resolution: the fallback ladder behind an entity's `concept`.

P8 names what an entity *is* ("almond", "invoice", "12%"); this module finds how to draw it,
walking one rung at a time and recording which rung answered so the plan can be audited:

    exact       an asset whose label/tags are the concept itself
    synonym     an asset for a lemma sharing the concept's WordNet synset
    hypernym    an asset for an ancestor (almond → edible nut → nut), ≤ HYPERNYM_DEPTH up
    composite   a hypernym mark two or more rungs up, so the concept word is typeset beside it
    typographic the concept typeset inside the housing — never a random or blank mark
    numeric     a figure ("12%", "1,000+") typeset in the data face

Nothing here is keyed to a fixture: the vocabulary is the vendored registries plus the
WordNet noun lexicon materialised by tools/build_lexicon.py.
"""
from __future__ import annotations

import gzip
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

LEXICON_PATH = Path(__file__).resolve().parents[2] / 'assets' / 'community' / 'lexicon' / 'noun-lexicon.json.gz'

HYPERNYM_DEPTH = 3
SENSE_LIMIT = 2
# Ancestors too abstract to draw: a walk that reaches one stops without an answer.
ABSTRACT = frozenset((
    'entity', 'physical_entity', 'abstraction', 'abstract_entity', 'object', 'physical_object', 'whole', 'unit',
    'artifact', 'artefact', 'thing', 'matter', 'substance', 'causal_agent', 'cause', 'causal_agency',
    'psychological_feature', 'attribute', 'relation', 'measure', 'quantity', 'amount', 'group', 'grouping',
    'event', 'act', 'human_action', 'human_activity', 'state', 'communication', 'part', 'portion', 'piece',
    'instrumentality', 'instrumentation', 'organism', 'being', 'living_thing', 'animate_thing', 'person',
    'individual', 'someone', 'somebody', 'mortal', 'soul', 'location', 'region', 'area', 'content', 'cognition',
    'knowledge', 'noesis', 'process', 'physical_process', 'phenomenon', 'natural_object', 'material', 'stuff',
    'commodity', 'trade_good', 'good', 'goods', 'consumer_goods', 'possession', 'property', 'belongings', 'holding',
    'concept', 'conception', 'construct', 'idea', 'thought', 'system', 'structure', 'construction', 'body', 'collection',
    'aggregation', 'accumulation', 'assemblage', 'social_group', 'organization', 'organisation', 'activity',
    'happening', 'occurrence', 'occurrent', 'natural_event', 'condition', 'status', 'situation', 'feeling',
    'medium', 'covering', 'container', 'conveyance', 'transport', 'equipment', 'implement', 'creation',
    'product', 'production', 'work', 'form', 'shape', 'kind', 'sort', 'variety', 'type', 'category', 'class',
    'set', 'point', 'component', 'constituent', 'element', 'factor', 'ingredient', 'ware', 'merchandise',
    'plant_part', 'plant_organ', 'reproductive_structure', 'plant', 'flora', 'plant_life', 'animal', 'animate_being',
    'beast', 'brute', 'creature', 'fauna', 'chordate', 'vertebrate', 'craniate', 'mammal', 'mammalian', 'placental',
    'eutherian', 'placental_mammal', 'eutherian_mammal', 'worker', 'adult', 'grownup', 'expert', 'professional',
    'professional_person', 'skilled_worker', 'trained_worker', 'skilled_workman', 'leader', 'writing',
    'written_communication', 'written_language', 'black_and_white', 'document', 'papers', 'written_document',
    'signal', 'signaling', 'sign', 'indication', 'evidence', 'information', 'info', 'message', 'subject_matter',
    'consumer_good', 'solid', 'fluid', 'liquid', 'food', 'nutrient', 'foodstuff', 'food_product', 'produce',
    'green_goods', 'green_groceries', 'garden_truck', 'device', 'mechanism', 'machine', 'tool', 'organ',
    'body_part', 'external_body_part', 'extremity', 'appendage', 'member', 'symbol', 'representation',
    'change', 'alteration', 'modification', 'interest', 'stake', 'share', 'security', 'certificate', 'commencement',
    'start', 'beginning', 'nutriment', 'nutrition', 'nourishment', 'sustenance', 'aliment', 'alimentation', 'victuals',
    'dish', 'course', 'code', 'computer_code', 'program', 'programme', 'computer_program', 'computer_programme',
    'software', 'software_program', 'computer_software', 'software_system', 'software_package', 'package',
    'deposit', 'depository', 'repository', 'depositary', 'storage_space', 'facility', 'installation',
))
# Registry tags that name the pack or drawing style, not the subject.
NOISE_TAGS = frozenset(('emoji', 'emoji3d', 'brand', 'colour-icon', 'icon', 'line', 'fill', 'placeable', 'pointable', 'objects', 'tech',
                        'finance', 'health', 'comms', 'nature', 'people', 'food', 'time', 'transport', 'emotion', 'one', 'two', 'three', 'four'))
# Skin-tone / gender / style variants read as the base mark; they answer only when asked for.
VARIANT_TOKENS = frozenset(('light', 'medium', 'dark', 'skin', 'tone', 'medium-light', 'medium-dark', 'flat', 'high', 'contrast'))
NUMERIC_RE = re.compile(r'^[+\-~≈]?\s*[$€£¥]?\d[\d,.\s]*[%xX×+kKmMbB]?(\s*[a-zA-Z%]{,4})?$')
# WordNet lexicographer files whose synsets name things a mark can draw: animal, artifact, body,
# food, location, object, person, plant, shape, substance.
DEPICTABLE_FILES = frozenset((5, 6, 8, 13, 15, 17, 18, 20, 25, 27))
STOP = frozenset(('the', 'a', 'an', 'of', 'and', 'or', 'with', 'for', 'to', 'in', 'on', 'at', 'by'))


def _tokens(text: str) -> List[str]:
    return [t for t in re.split(r'[^a-z0-9+#]+', text.lower().replace('_', ' ')) if t and t not in STOP]


def singular(tok: str) -> str:
    if len(tok) <= 3 or tok.endswith('ss') or tok.endswith('us') or tok.endswith('is'):
        return tok
    if tok.endswith('ies') and len(tok) > 4:
        return tok[:-3] + 'y'
    if tok.endswith(('ches', 'shes', 'xes', 'ses', 'zes')):
        return tok[:-2]
    if tok.endswith('s'):
        return tok[:-1]
    return tok


def _key(tokens: Iterable[str]) -> Tuple[str, ...]:
    return tuple(singular(t) for t in tokens)


class NounLexicon:
    """Sense-ordered synonyms and hypernym chains for English nouns (WordNet 3.1, nouns only)."""

    def __init__(self, path: Path = LEXICON_PATH):
        self.path = path
        self.synsets: Dict[str, Dict[str, object]] = {}
        self.index: Dict[str, List[str]] = {}
        self.tagged: Dict[str, List[int]] = {}
        self.version: Optional[str] = None
        if path.exists():
            with gzip.open(path, 'rt', encoding='utf-8') as fh:
                doc = json.load(fh)
            self.synsets = doc['synsets']
            self.index = doc['index']
            self.tagged = {k: v for k, v in doc.get('tagged', {}).items() if isinstance(v, list)}
            self.version = doc.get('source')

    @property
    def available(self) -> bool:
        return bool(self.index)

    def lemma(self, concept: str) -> Optional[str]:
        """The lexicon lemma for a concept, trying spaced, joined and singular spellings."""
        toks = _tokens(concept)
        if not toks:
            return None
        for cand in ('_'.join(toks), ''.join(toks), '_'.join(_key(toks)), ''.join(_key(toks)), '-'.join(toks)):
            if cand in self.index:
                return cand
        return None

    def senses(self, lemma: str, limit: int = SENSE_LIMIT) -> List[str]:
        """The senses the ladder may walk, most frequent first. Where the corpus tagged the lemma,
        an untagged sense is dropped: those are where 'sugar' becomes money, 'loan' a borrowed word
        and 'tomato' a herb. Untagged lemmas ('almond': tree, nut) keep their leading senses."""
        all_senses = self.index.get(lemma, [])
        counts = self.tagged.get(lemma)
        if counts and any(counts):
            all_senses = [s for s, c in zip(all_senses, counts) if c > 0]
        else:
            # No corpus evidence which sense is everyday: a mark draws things, so only the senses
            # that name things are walked ('wrench' the tool, never the injury).
            things = [s for s in all_senses if self.depictable(s)]
            all_senses = things or all_senses
        return all_senses[:limit]

    def depictable(self, sid: str) -> bool:
        return self.synsets[sid].get('f') in DEPICTABLE_FILES

    def _lemmas(self, sid: str) -> List[str]:
        lems = self.synsets[sid]['l']
        return list(lems) if isinstance(lems, list) else []

    def _hypernyms(self, sid: str) -> List[str]:
        hyp = self.synsets[sid]['h']
        return list(hyp) if isinstance(hyp, list) else []

    def synonyms(self, lemma: str, limit: int = SENSE_LIMIT) -> List[str]:
        out: List[str] = []
        for sid in self.senses(lemma, limit):
            for lem in self._lemmas(sid):
                if lem != lemma and lem not in out and self.reads_as(lem, sid):
                    out.append(lem)
        return out

    def reads_as(self, lemma: str, sid: str) -> bool:
        """Does `lemma`, met on its own, mean synset `sid`? A substitute word only works when a
        viewer reads it that way: 'bike' is a bicycle and 'bill' an invoice often enough, but
        'word' is never a password and a 'chest' is a torso before it is a box."""
        senses = self.index.get(lemma, [])
        if sid not in senses[:5]:
            return False
        counts = self.tagged.get(lemma)
        if not counts or not any(counts):
            return sid in self.senses(lemma)
        c = counts[senses.index(sid)]
        return c > 0 and c * 4 >= max(counts)

    def hypernym_levels(self, lemma: str, depth: int = HYPERNYM_DEPTH, limit: int = SENSE_LIMIT, all_senses: bool = False) -> List[List[str]]:
        """Lemmas at each ancestor level (1 = parent), pruned once a level is all-abstract. Past
        the parent only a synset's canonical lemma counts: the minor names of a grandparent
        ('nutrition' for nutriment, 'code' for computer program) are where meaning drifts."""
        frontier = list(self.index.get(lemma, [])[:5] if all_senses else self.senses(lemma, limit))
        levels: List[List[str]] = []
        seen: Set[str] = set(frontier)
        for _ in range(depth):
            nxt: List[str] = []
            for sid in frontier:
                for h in self._hypernyms(sid):
                    if h not in seen:
                        seen.add(h)
                        nxt.append(h)
            if not nxt:
                break
            lemmas: List[str] = []
            for sid in nxt:
                for lem in (self._lemmas(sid) if not levels else self._lemmas(sid)[:1]):
                    if lem not in ABSTRACT and lem not in lemmas and (all_senses or self.reads_as(lem, sid)):
                        lemmas.append(lem)
            if not lemmas:
                break
            levels.append(lemmas)
            frontier = nxt
        return levels

    def chain_lemmas(self, lemma: str, depth: int = HYPERNYM_DEPTH + 2) -> Set[str]:
        out: Set[str] = {lemma}
        for lv in self.hypernym_levels(lemma, depth, all_senses=True):
            out.update(lv)
        return out

    def related(self, a: str, b: str) -> bool:
        """True when two lemmas share an ancestor (or one is the other's ancestor) in any sense —
        the guard that keeps 'nut and bolt' from answering 'almond' while 'macadamia nut' does."""
        la, lb = self.lemma(a), self.lemma(b)
        if not la or not lb:
            return False
        ca = self.chain_lemmas(la)
        cb = self.chain_lemmas(lb)
        return bool((ca & cb) - {la, lb}) or la in cb or lb in ca


@dataclass
class Resolution:
    concept: str
    via: str                          # exact | synonym | hypernym | composite | typographic | numeric
    asset_ref: Optional[str] = None
    word: Optional[str] = None        # typeset inside the housing (composite / typographic / numeric)
    path: List[str] = field(default_factory=list)   # lexicon walk that led to the asset

    def as_dict(self) -> Dict[str, object]:
        return {'concept': self.concept, 'via': self.via, 'asset_ref': self.asset_ref, 'word': self.word, 'path': list(self.path)}


class AssetFinder:
    """Searches the registries by subject; the ladder above decides what a concept becomes."""

    def __init__(self, items: Dict[str, Dict[str, object]], lexicon: NounLexicon, quarantined: Optional[Dict[str, str]] = None):
        self.items = items
        self.lexicon = lexicon
        self.quarantined = dict(quarantined or {})
        self._by_label: Dict[Tuple[str, ...], List[str]] = {}
        self._by_term: Dict[str, Set[str]] = {}
        for aid, item in items.items():
            if aid in self.quarantined:
                continue
            label = str(item.get('label') or aid.split('.')[-1].replace('-', ' '))
            toks = _tokens(label)
            if not toks:
                continue
            self._by_label.setdefault(_key(toks), []).append(aid)
            terms = set(_key(toks)) | {singular(t) for t in (item.get('tags') or []) if isinstance(t, str) and t.lower() not in NOISE_TAGS and not t.isdigit()}
            for t in terms:
                self._by_term.setdefault(t, set()).add(aid)

    # -- candidate scoring ---------------------------------------------------------------------
    @staticmethod
    def pack_of(aid: str) -> str:
        return '.'.join(aid.split('.')[:2])

    def _native(self, aid: str) -> bool:
        return self.items[aid].get('colour') == 'native'

    def _is_brand(self, aid: str) -> bool:
        return self.items[aid].get('family') == 'brand'

    def _label_key(self, aid: str) -> Tuple[str, ...]:
        item = self.items[aid]
        return _key(_tokens(str(item.get('label') or aid.split('.')[-1].replace('-', ' '))))

    def _names_other_thing(self, head: str, want: Tuple[str, ...]) -> bool:
        """A trailing head noun that is itself a thing unrelated to the subject names something
        else: 'coffee machine', 'document folder'. A related head ('factory building') or a word
        the lexicon does not know as a noun ('dress longuette') is only description."""
        if not self.lexicon.available or self.lexicon.lemma(head) is None:
            return False
        return not self.lexicon.related(head, ' '.join(want))

    def _weak(self, aid: str, want: Tuple[str, ...]) -> bool:
        """The subject is only the qualifier of the label's head: a 'coffee machine' is a machine, a
        'honey pot' a pot. Such a mark never answers on its own; typeset beside its word it may."""
        lk = self._label_key(aid)
        extra = [t for t in lk if t not in want]
        return set(want) <= set(lk) and len(extra) == 1 and lk[-1] == extra[0] and self._names_other_thing(extra[0], want)

    def _rank(self, aid: str, want: Tuple[str, ...], pack: Optional[str]) -> Tuple[float, str]:
        lk = self._label_key(aid)
        extra = [t for t in lk if t not in want]
        if lk == want:
            score = 3.0
        elif set(want) <= set(lk) and len(extra) <= 1:
            score = 2.0           # one qualifier ('red apple', 'file spreadsheet') still names the subject
        elif set(want) <= set(lk):
            score = -1.0          # 'chart cluster bar' is a chart, whatever its tags say
        else:
            score = 1.0
        if any(t in VARIANT_TOKENS for t in extra):
            score -= 1.2
        if score < 0:
            return (score, aid)   # a label that names another thing is not rescued by being in the right pack
        if pack and self.pack_of(aid) == pack:
            score += 1.5
        elif pack and self._native(aid) and not self._is_brand(aid):
            score -= 3.0          # a native mark from another pack breaks the one-pack law; logos are exempt
        if self._native(aid) and not pack:
            score += 0.3          # collage finish: colour art first when the film has no pack yet
        return (score, aid)

    def _candidates(self, phrase: str, pack: Optional[str], allow_brand: bool, exact_only: bool, head_only: bool = False, weak: bool = False) -> List[str]:
        want = _key(_tokens(phrase))
        if not want:
            return []
        ids: Set[str] = set(self._by_label.get(want, []))
        if head_only:
            # The phrase as the head noun of a label with one describing qualifier: 'hot beverage'
            # is a beverage. A qualifier that is itself a thing names another thing ('kiwi fruit',
            # 'flash payment'), and 'beverage box' is a box: neither answers.
            for key, aids in self._by_label.items():
                if len(key) == len(want) + 1 and key[1:] == want and self.lexicon.lemma(key[0]) is None:
                    ids.update(aids)
        elif not exact_only:
            pools = [self._by_term.get(t, set()) for t in want]
            if pools and all(pools):
                ids |= set.intersection(*pools)
        out = [a for a in ids if (allow_brand or not self._is_brand(a)) and self._weak(a, want) == weak]
        ranked = sorted(out, key=lambda a: self._rank(a, want, pack), reverse=True)
        return [a for a in ranked if self._rank(a, want, pack)[0] > 0]

    # -- ladder --------------------------------------------------------------------------------
    def resolve(self, concept: str, pack: Optional[str] = None, can_type: bool = True, native_only: bool = False, named: bool = False) -> Resolution:
        """Walk the ladder for a concept. `pack` pins native marks to the film's colour pack;
        `can_type` says the housing can typeset a word (TILE / BADGE / CHIP); ICON cannot.
        `named` says the housing already shows the concept's name (a labelled CHIP), so an
        ancestor's mark may stand alone; elsewhere an ancestor is only drawn beside the word."""
        text = ' '.join(str(concept).split())
        if NUMERIC_RE.match(text):
            return Resolution(text, 'numeric', word=text)

        def pick(phrase: str, allow_brand: bool = False, exact_only: bool = False, head_only: bool = False, weak: bool = False) -> Optional[str]:
            cands = self._candidates(phrase, pack, allow_brand, exact_only, head_only, weak)
            if allow_brand and phrase[:1].isupper():
                # Written as a name, the name's own logo outranks a same-spelt common noun's icon.
                cands = [a for a in cands if self._is_brand(a)] + [a for a in cands if not self._is_brand(a)]
            return self._first(cands, native_only)

        lemma = self.lexicon.lemma(text) if self.lexicon.available else None
        # exact — a brand mark answers only to its own name, written as a name ("Slack") or
        # unknown to the lexicon; a common noun ("apple") never lands on a logo.
        hit = None
        if text[:1].isupper() or lemma is None:
            hit = pick(text, allow_brand=True, exact_only=True)
        if hit is None:
            hit = pick(text)
        if hit is not None:
            return Resolution(text, 'exact', asset_ref=hit, path=[text])

        toks = _tokens(text)
        if lemma is None and len(toks) > 1 and self.lexicon.available:
            # An unknown compound falls to its head noun and keeps its own name beside the mark.
            head = self.lexicon.lemma(toks[-1])
            if head is not None:
                inner = self.resolve(toks[-1], pack, can_type, native_only, named)
                if inner.asset_ref and can_type and (self._label_key(inner.asset_ref) == _key([toks[-1]]) or self.lexicon.related(toks[-1], self._label_text(inner.asset_ref))):
                    return Resolution(text, 'composite', asset_ref=inner.asset_ref, word=text, path=[text, toks[-1]] + inner.path[1:])
        if lemma is not None:
            # A stand-in word is taken at its own name only: 'tube' is not a 'test tube'.
            for syn in self.lexicon.synonyms(lemma):
                hit = pick(syn.replace('_', ' '), exact_only=True)
                if hit is not None:
                    return Resolution(text, 'synonym', asset_ref=hit, path=[text, syn])
            # An ancestor drawn beside the typeset word may be a qualified mark ('hot beverage' for
            # coffee → beverage): the word says which one. Standing alone it must be the plain name.
            composite = can_type and not named
            for depth, level in enumerate(self.lexicon.hypernym_levels(lemma), start=1):
                for hyper in level:
                    hit = pick(hyper.replace('_', ' '), exact_only=True, head_only=composite and depth == 1)
                    if hit is None:
                        continue
                    if not can_type and depth > 1:
                        continue      # a bare mark two rungs up is somebody else's picture
                    if named or not can_type:
                        return Resolution(text, 'hypernym', asset_ref=hit, word=None, path=[text, hyper])
                    return Resolution(text, 'composite', asset_ref=hit, word=text, path=[text, hyper])
        if can_type:
            # Last mark before type: a label the subject only qualifies ('honey pot', 'cheese wedge')
            # drawn beside the word, which says what the picture is of.
            hit = pick(text, weak=True)
            if hit is not None:
                return Resolution(text, 'composite', asset_ref=hit, word=None if named else text, path=[text, self._label_text(hit)])
        if can_type:
            return Resolution(text, 'typographic', word=text)
        return Resolution(text, 'unresolved')

    def _first(self, ids: Sequence[str], native_only: bool) -> Optional[str]:
        for a in ids:
            if native_only and not self._native(a):
                continue
            return a
        return None

    def _label_text(self, aid: str) -> str:
        return str(self.items[aid].get('label') or aid.split('.')[-1].replace('-', ' '))
