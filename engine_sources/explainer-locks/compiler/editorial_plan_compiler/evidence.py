"""Photo evidence: a rights-clean photograph of a concept no vendored mark draws.

An editor with no icon for "coffee bean" drops a photograph of coffee beans into the frame; this
module does the same for the concept ladder. Candidates come from catalogues that expose licence
metadata per work (Openverse, Wikimedia Commons) and only CC0 / public-domain works are taken, so
nothing here needs attribution or a rights review. The chosen file is normalised once with
ffmpeg, cached under assets/evidence with its source, licence and hash recorded in index.json,
and every later compile reads the cache — renders stay deterministic and offline.

Selection is a pure function of the catalogue answer: candidates are scored on how plainly their
title names the concept and ordered by a hash of their catalogue id, never by fetch order.
Set EM2_EVIDENCE=off to forbid the network (the cache still answers).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .lexicon import NounLexicon, _key, _tokens

EVIDENCE_DIR = Path(__file__).resolve().parents[2] / 'assets' / 'evidence'
INDEX_NAME = 'index.json'
USER_AGENT = 'nexstudio-editorial-motion/2.0 (photo evidence; CC0/PD only)'
TIMEOUT_S = 12
MAX_EDGE = 1400
MIN_EDGE = 480
# A strip or panorama cannot fill a housing without cropping most of its subject away.
MAX_ASPECT = 2.2
CANDIDATES_TRIED = 4
PAGE_SIZE = 40
# Catalogue etiquette: one request a second, and a single wait on a 429 before giving up.
REQUEST_GAP_S = 1.0
RETRY_AFTER_MAX_S = 20
OPENVERSE_LICENSES = frozenset(('cc0', 'pdm'))
COMMONS_LICENSES = frozenset(('cc0', 'public domain', 'pd'))
# Titles naming a rendering of the subject rather than the subject itself.
NOT_A_PHOTOGRAPH = frozenset((
    'logo', 'icon', 'clipart', 'clip', 'drawing', 'diagram', 'screenshot', 'map', 'flag', 'vector', 'emoji', 'svg',
    'illustration', 'sketch', 'sign', 'poster', 'chart', 'graph', 'label', 'stamp', 'coin', 'banknote', 'cartoon',
    'painting', 'engraving', 'plate', 'text', 'scan', 'page', 'book', 'cover', 'menu', 'advertisement', 'ad',
    'still', 'catalogue', 'catalog', 'dictionary', 'dictionnaire', 'tome', 'lithograph', 'woodcut', 'print', 'fresco',
    'render', 'rendering', '3d', 'cgi', 'model', 'mockup', 'floorplan', 'blueprint', 'artwork', 'generated', 'ai',
    'advertising', 'intertitle', 'video', 'animation', 'game', 'meme',
))
# Curators' categories or tags that file the picture as art, a graphic or a frame grab.
NOT_A_SUBJECT = frozenset((
    'painting', 'drawing', 'artwork', 'illustration', 'engraving', 'lithograph', 'woodcut', 'fresco', 'cartoon',
    'logo', 'icon', 'clipart', 'diagram', 'map', 'screenshot', 'poster', 'advertising', 'advertisement', 'intertitle',
    'render', 'rendering', '3d', 'cgi', 'generated', 'ai', 'meme', 'animation', 'video',
    'postcard', 'monochrome', 'sepia', 'daguerreotype', 'archaeological', 'archaeology', 'antiquities', 'fossil',
))
# Catalogue categories that describe the record's housekeeping, not its subject.
HOUSEKEEPING_CATEGORY = re.compile(
    r'^(cc[- ]|pd[- ]|self-published|all media|media (needing|missing|with|contributed)|files? |license|uploaded|'
    r'images? (uploaded|from|by|with)|photographs? (by|taken)|taken with|flickr|creative commons|template|'
    r'pages? with|works? (by|of)|.*\bmissing\b|.*\bneeding\b|.*\bwikidata\b|.*\bphotographs taken on\b)', re.I,
)
# A year before photography went colour marks an artwork or a plate reproduction; a photograph
# dated before it is an archive print, not evidence of the thing as a viewer knows it.
ARTWORK_YEAR_BEFORE = 1960
# Below this mean chroma (ffmpeg signalstats SATAVG, 0..~180) a frame is black-and-white.
MONOCHROME_SATURATION = 1.5
# A concept joined to a second named subject shares the frame with it: not a study of the concept.
CO_SUBJECT = frozenset(('and', '&', 'with', 'vs'))
# A title carrying one of these reads as a scene or a person, not a study of the thing.
CROWDED = frozenset(('woman', 'women', 'man', 'men', 'people', 'person', 'girl', 'boy', 'child', 'children', 'family',
                     'festival', 'market', 'street', 'city', 'shop', 'store', 'museum', 'exhibition', 'ceremony',
                     'meeting', 'conference', 'speech', 'crowd', 'audience', 'wedding', 'parade', 'concert', 'party'))
# The thing shown broken, sick or wrecked is not the thing a viewer is being told about.
DAMAGED = frozenset(('diseased', 'damaged', 'broken', 'crash', 'crashed', 'wreck', 'wrecked', 'accident', 'error',
                     'dead', 'rotten', 'burnt', 'burned', 'ruined', 'destroyed', 'abandoned', 'derelict', 'rusty',
                     'mould', 'mold', 'mouldy', 'moldy', 'fault', 'failure', 'messy', 'dirty', 'cluttered', 'stained'))
# Curators filing a picture under people (or warning of a person's rights in it) have said who it is of.
PEOPLE_IN_FRAME = CROWDED | frozenset(('personality', 'portrait', 'portraits', 'selfie', 'selfies', 'faces', 'face'))
# The subject as the object of these is the surface something else sits on, not the picture's subject.
SURFACE_OF = frozenset(('on', 'onto', 'inside', 'atop', 'upon'))
# Words a title may carry without saying anything about the subject.
FUNCTION_WORDS = frozenset(('a', 'an', 'the', 'of', 'in', 'on', 'at', 'to', 'for', 'from', 'by', 'with', 'and', 'or',
                            'its', 'his', 'her', 'their', 'is', 'are', 'was', 'near', 'under', 'over', 'into', 'onto',
                            'inside', 'outside', 'one', 'two', 'three', 'part', 'detail', 'view', 'close', 'up',
                            'closeup', 'macro', 'photo', 'photograph', 'picture', 'unsplash', 'pexels', 'pixabay'))
# Beyond this many title words the file is a described archive record, not a study of one thing.
TITLE_WORDS_MAX = 8
# More words than this that the lexicon does not know as nouns and the title is a name, a Latin
# binomial or another language: 'Kereta Api Bandara' is a train, whatever 'api' matched.
UNKNOWN_WORDS_MAX = 1
SCENE_THINGS = 3


def _title_text(title: str) -> str:
    t = re.sub(r'^file:', '', title.strip(), flags=re.I)
    return re.sub(r'\.(jpe?g|png|tiff?|webp|gif|svg)$', '', t, flags=re.I)


def _names_a_person_or_record(title: str, want: Sequence[str]) -> bool:
    """'Ralph J. Bean' is a man, not a bean; 'OFHSK pantry' is a catalogue number; a title of a
    dozen words is an archive description. None of them is a photograph *of* the concept."""
    t = _title_text(title)
    words = t.split()
    if len(words) > TITLE_WORDS_MAX:
        return True
    if re.search(r'\b[A-Z]\.(\s|$)', t):
        return True
    if any(re.fullmatch(r'[A-Z]{3,}\d*', w) for w in re.split(r'[^A-Za-z0-9]+', t) if w):
        return True
    if re.search(r'\bby\s+[A-Z]', t):
        return True                                    # 'Flower mirror by Gabriel Bracho': a credited work
    return _is_a_proper_name(words, want)


def _object_of_a_surface(title: str, want: Sequence[str]) -> bool:
    """'Cernan on moon', 'a waterdrop on umbrella': the concept is what something else sits on."""
    words = _raw_words(title)
    n = len(want)
    return any(tuple(words[i:i + n]) == tuple(want) and i > 0 and words[i - 1] in SURFACE_OF
               for i in range(len(words) - n + 1))


def _things_before(title: str, want: Sequence[str]) -> int:
    """How many other words the title spends before it reaches the concept: 'Erechtheum Acropolis
    Athens evening moon' is a view of a temple with the moon in it."""
    words = _raw_words(title)
    n = len(want)
    for i in range(len(words) - n + 1):
        if tuple(words[i:i + n]) == tuple(want):
            return sum(1 for w in words[:i] if w not in FUNCTION_WORDS and not w.isdigit() and len(w) > 1)
    return 0


def _is_a_proper_name(words: Sequence[str], want: Sequence[str]) -> bool:
    """'Hamam street Old Salt', 'Turkey Point': the concept written with a capital inside a
    sentence-case title is a place, a brand or a surname, not the thing."""
    later = [w for w in words[1:] if w[:1].isalpha()]
    if not later or all(w[0].isupper() for w in later):
        return False
    want_l = set(want)
    return any(w[0].isupper() and set(_key([re.sub(r'[^A-Za-z]', '', w).lower()])) & want_l for w in later)


def _phrase_in(want: Sequence[str], toks: Sequence[str]) -> bool:
    n = len(want)
    return any(tuple(toks[i:i + n]) == tuple(want) for i in range(len(toks) - n + 1))


def _shares_the_frame(title: str, want: Sequence[str]) -> bool:
    """'Marijuana and pipe', 'dress with leggings': the concept is one of two named subjects, so
    the picture is of the pair, not of it."""
    words = _raw_words(title)
    n = len(want)
    for i in range(len(words) - n + 1):
        if tuple(words[i:i + n]) == tuple(want):
            if (i > 0 and words[i - 1] in CO_SUBJECT) or (i + n < len(words) and words[i + n] in CO_SUBJECT):
                return True
    return False


def _title_words(title: str) -> List[str]:
    """Title words in order, stopwords kept, as written (plural kept: 'scissors' is its own lemma)."""
    t = re.sub(r'\b(img|dsc|dscn|dscf|p|pict|image)[_ -]?\d{2,}\b', ' ', _title_text(title), flags=re.I)
    return [w for w in re.split(r'[^a-z0-9+#&]+', t.lower().replace('_', ' ')) if w]


def _raw_words(title: str) -> List[str]:
    """Title words in order, stopwords kept, singularised: the sequence a compound is read from."""
    return [re.sub(r'(?<=[a-z])\d+$', '', w) for w in _key(_title_words(title))]


def _year(text: str) -> Optional[int]:
    """The year a catalogue date names ('1934', '1895-06-01', 'ca. 2000 BC' → -2000), else None."""
    plain = re.sub(r'<[^>]+>', ' ', text)
    m = re.search(r'\b(\d{1,4})\s*(bc|bce)\b', plain, flags=re.I)
    if m:
        return -int(m.group(1))
    m = re.search(r'\b(1[0-9]{3}|20[0-9]{2})\b', plain)
    return int(m.group(1)) if m else None


@dataclass
class PhotoRecord:
    concept: str
    query: str
    source: str            # openverse | wikimedia_commons
    provider: str          # openverse's upstream (flickr, ...) or 'commons'
    source_id: str
    title: str
    creator: str
    license: str           # CC0 1.0 | Public Domain
    license_url: str
    landing_url: str
    file_url: str
    file: str              # cached file name under EVIDENCE_DIR
    sha256: str
    width: int
    height: int
    fetched: str           # ISO date
    subjects: tuple = ()   # the catalogue's categories / tags, kept so the policy can be re-read offline
    year: Optional[int] = None
    source_size: tuple = ()   # the catalogue's own dimensions before normalisation

    def rights(self) -> str:
        who = f' — {self.creator}' if self.creator else ''
        return f'{self.license} ({self.source}:{self.provider}{who})'


@dataclass
class Candidate:
    source: str
    provider: str
    source_id: str
    title: str
    creator: str
    license: str
    license_url: str
    landing_url: str
    file_url: str
    width: int
    height: int
    subjects: tuple = ()   # what the catalogue's curators say the picture is of (categories / tags)
    year: Optional[int] = None   # when the catalogue dates the photograph


def _slug(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')[:48] or 'concept'


def _title_tokens(title: str) -> List[str]:
    t = re.sub(r'\b(img|dsc|dscn|dscf|p|pict|image)[_ -]?\d{2,}\b', ' ', _title_text(title), flags=re.I)
    toks = [re.sub(r'(?<=[a-z])\d+$', '', tok) for tok in _tokens(t)]
    return [tok for tok in _key(toks) if len(tok) > 1]


class CatalogueDown(Exception):
    """The catalogue did not answer (rate limit, outage, no network): not evidence of a miss."""


_last_request = 0.0


def _pace() -> None:
    global _last_request
    wait = _last_request + REQUEST_GAP_S - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    _last_request = time.monotonic()


def _fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
    for attempt in range(2):
        _pace()
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt == 0:
                try:
                    retry = min(RETRY_AFTER_MAX_S, float(e.headers.get('Retry-After') or 5))
                except ValueError:
                    retry = 5.0
                time.sleep(retry)
                continue
            raise CatalogueDown(f'{e.code} {url}') from e
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as e:
            raise CatalogueDown(str(e)) from e
    raise CatalogueDown(url)


def _fetch_bytes(url: str, limit: int = 40 * 1024 * 1024) -> Optional[bytes]:
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S * 3) as resp:
            data = resp.read(limit + 1)
    except (urllib.error.URLError, TimeoutError, OSError):
        return None
    return data if 0 < len(data) <= limit else None


class PhotoEvidence:
    """Cache-first lookup of a CC0 / public-domain photograph for a concept."""

    def __init__(self, root: Path = EVIDENCE_DIR, lexicon: Optional[NounLexicon] = None, online: Optional[bool] = None):
        self.root = root
        self.lexicon = lexicon
        self.online = (os.environ.get('EM2_EVIDENCE', 'on').lower() not in ('off', '0', 'no')) if online is None else online
        self.index: Dict[str, PhotoRecord] = {}
        self.misses: Dict[str, str] = {}
        self.unavailable: List[str] = []
        idx = root / INDEX_NAME
        if idx.exists():
            doc = json.loads(idx.read_text(encoding='utf-8'))
            for k, v in (doc.get('photos') or {}).items():
                v['subjects'] = tuple(v.get('subjects') or ())
                v['source_size'] = tuple(v.get('source_size') or ())
                self.index[k] = PhotoRecord(**v)
            self.misses = {k: str(v) for k, v in (doc.get('misses') or {}).items()}

    # -- public --------------------------------------------------------------------------------
    @staticmethod
    def key(concept: str) -> str:
        return ' '.join(_key(_tokens(concept)))

    def find(self, concept: str) -> Optional[PhotoRecord]:
        k = self.key(concept)
        if not k:
            return None
        rec = self.index.get(k)
        if rec is not None:
            f = self.root / rec.file
            if f.exists() and hashlib.sha256(f.read_bytes()).hexdigest() == rec.sha256 and self._still_admissible(rec, k):
                return rec
            del self.index[k]
            f.unlink(missing_ok=True)
            self._save()
        if not self.online or k in self.misses or not self._photographable(concept):
            return None
        try:
            rec = self._search(concept, k)
        except CatalogueDown as e:
            # A catalogue that would not answer is not a catalogue with no answer: nothing is
            # written, and the ladder falls through to its lower rungs for this compile only.
            self.unavailable.append(f'{concept}: {e}')
            return None
        if rec is None:
            self.misses[k] = time.strftime('%Y-%m-%d')
        else:
            self.index[k] = rec
        self._save()
        return rec

    def _still_admissible(self, rec: PhotoRecord, k: str) -> bool:
        """A cached record is re-read against today's policy from the catalogue facts it kept, so a
        tightened rule retires old evidence instead of grandfathering it."""
        if not rec.source_size or not self._photographable(rec.concept):
            return False                              # no catalogue facts kept: nothing to re-read it against
        w, h = (rec.source_size or (rec.width, rec.height))[:2]
        cand = Candidate(rec.source, rec.provider, rec.source_id, rec.title, rec.creator, rec.license, rec.license_url,
                         rec.landing_url, rec.file_url, int(w), int(h), tuple(rec.subjects), rec.year)
        return self._score(cand, tuple(k.split())) is not None

    def _photographable(self, concept: str) -> bool:
        """A camera can only be pointed at a thing: a concept the lexicon knows must have a sense
        that names one (a flavour, a collision or a process has no photograph of itself). An
        unknown compound is judged by its head noun."""
        if self.lexicon is None or not self.lexicon.available:
            return True
        lemma = self.lexicon.lemma(concept)
        if lemma is None:
            toks = _tokens(concept)
            lemma = self.lexicon.lemma(toks[-1]) if len(toks) > 1 else None
            if lemma is None:
                return False                          # a word nobody can define has no picture either
        senses = self.lexicon.senses(lemma)
        return any(self.lexicon.depictable(s) for s in senses) and not all(self.lexicon.is_person(s) for s in senses)

    def as_plan(self, rec: PhotoRecord) -> Dict[str, object]:
        return {
            'path': str(self.root / rec.file), 'sha256': rec.sha256, 'source_size': {'w': rec.width, 'h': rec.height},
            'rights': rec.rights(), 'license': rec.license, 'license_url': rec.license_url, 'source': rec.source,
            'source_id': rec.source_id, 'landing_url': rec.landing_url, 'title': rec.title, 'creator': rec.creator,
        }

    # -- search --------------------------------------------------------------------------------
    def _queries(self, concept: str) -> List[str]:
        out = [' '.join(_tokens(concept))]
        if self.lexicon is not None and self.lexicon.available:
            lemma = self.lexicon.lemma(concept)
            if lemma is not None:
                for syn in self.lexicon.synonyms(lemma, limit=1)[:1]:
                    q = syn.replace('_', ' ')
                    if q not in out:
                        out.append(q)
        return out

    def _search(self, concept: str, k: str) -> Optional[PhotoRecord]:
        want = tuple(k.split())
        for query in self._queries(concept):
            cands: List[Candidate] = []
            down: List[str] = []
            for catalogue in (self._openverse, self._commons):
                try:
                    cands += catalogue(query)
                except CatalogueDown as e:
                    down.append(str(e))
            if len(down) == 2:
                raise CatalogueDown('; '.join(down))
            ranked = self._rank(cands, want)
            if not ranked and down:
                # The one catalogue that answered had nothing; the other might have. Not a miss.
                raise CatalogueDown(down[0])
            for cand in ranked[:CANDIDATES_TRIED]:
                rec = self._materialise(cand, concept, query)
                if rec is not None:
                    return rec
        return None

    def _score(self, cand: Candidate, want: Sequence[str]) -> Optional[float]:
        toks = _title_tokens(cand.title)
        if not toks or min(cand.width, cand.height) < MIN_EDGE:
            return None
        if max(cand.width, cand.height) > MAX_ASPECT * min(cand.width, cand.height):
            return None
        if any(t in NOT_A_PHOTOGRAPH for t in toks):
            return None
        if any(t.isdigit() and len(t) == 4 and int(t) < ARTWORK_YEAR_BEFORE for t in toks):
            return None
        if cand.year is not None and cand.year < ARTWORK_YEAR_BEFORE:
            return None
        if not _phrase_in(want, toks) or _names_a_person_or_record(cand.title, want):
            return None
        if self._subject_is_another_thing(cand.title, want) or _shares_the_frame(cand.title, want):
            return None
        if _object_of_a_surface(cand.title, want) or any(t in DAMAGED for t in toks):
            return None
        if self._is_a_different_compound(cand.title, want) or self._foreign_words(cand.title, want) > UNKNOWN_WORDS_MAX:
            return None
        if self._is_a_named_thing(cand.title, want) or _things_before(cand.title, want) >= SCENE_THINGS:
            return None
        subjects = [_title_tokens(s) for s in cand.subjects]
        if any(t in NOT_A_SUBJECT for s in subjects for t in s):
            return None                               # curators filed it as art, a graphic or a frame grab
        if any(t in PEOPLE_IN_FRAME for s in subjects for t in s if t not in want):
            return None                               # filed under the people in it: a person, not the thing
        score = 3.0
        if any(_phrase_in(want, s) for s in subjects):
            score += 1.2                              # filed under the concept itself: a curated study of it
        elif cand.source == 'wikimedia_commons' and not cand.subjects:
            score -= 0.8                              # an uncategorised upload nobody has looked at
        extra = [t for t in toks if t not in want]
        if any(t in CROWDED for t in extra):
            return None                               # a scene with people in it, not a study of the thing
        score -= min(2.0, 0.35 * len(extra))          # a plain study of the subject beats a described scene
        ar = cand.width / cand.height
        if 0.8 <= ar <= 1.6:
            score += 0.4                              # fits the housings' wells without a hard crop
        if max(cand.width, cand.height) >= 1000:
            score += 0.3
        return score

    def _is_a_named_thing(self, title: str, want: Sequence[str]) -> bool:
        """'Ro Server', 'Matatu Speaker', 'Kereta Api': the concept capitalised right beside a
        capitalised word the lexicon knows no thing by is a ship, a brand or a foreign phrase."""
        if self.lexicon is None or not self.lexicon.available:
            return False

        def a_thing(w: str) -> bool:
            lemma = self.lexicon.lemma(w)
            return lemma is not None and any(self.lexicon.depictable(s) for s in self.lexicon.senses(lemma))

        written = [w for w in _title_text(title).split() if w[:1].isalpha()]
        keyed = _key([re.sub(r'[^A-Za-z]', '', w).lower() for w in written])
        n = len(want)
        for i in range(len(keyed) - n + 1):
            if tuple(keyed[i:i + n]) != tuple(want) or not written[i][0].isupper():
                continue
            for j in (i - 1, i + n):
                if 0 <= j < len(written) and written[j][0].isupper() and len(keyed[j]) >= 2 \
                        and keyed[j] not in FUNCTION_WORDS and not a_thing(keyed[j]):
                    return True
        return False

    def _subject_is_another_thing(self, title: str, want: Sequence[str]) -> bool:
        """'Bean salad' is a salad and 'coffee machine' a machine: when every mention of the concept
        is the qualifier of a following thing-noun, the photograph shows that thing. A follower
        that is the concept's own ancestor ('almond nut') or no thing at all is description."""
        if self.lexicon is None or not self.lexicon.available:
            return False
        words = _raw_words(title)
        written = _title_words(title)
        n = len(want)
        heads: List[Optional[str]] = []
        for i in range(len(words) - n + 1):
            if tuple(words[i:i + n]) == tuple(want):
                heads.append(written[i + n] if i + n < len(words) else None)
        if not heads:
            return False
        lemma = self.lexicon.lemma(' '.join(want))
        family = self.lexicon.chain_lemmas(lemma) if lemma else set()
        for h in heads:
            if h is None:
                return False
            hl = self.lexicon.lemma(h)
            if hl is None or hl in family or not any(self.lexicon.depictable(s) for s in self.lexicon.senses(hl)):
                return False
        return True

    def _is_a_different_compound(self, title: str, want: Sequence[str]) -> bool:
        """'Shoe trees' for tree, 'hot dog' for dog: the concept is the head of a compound the
        lexicon knows to be another thing. 'Coffee beans' for bean, 'hard hat' for hat stay."""
        if self.lexicon is None or not self.lexicon.available:
            return False
        words = _raw_words(title)
        n = len(want)
        head = ' '.join(want)
        for i in range(1, len(words) - n + 1):
            if tuple(words[i:i + n]) != tuple(want):
                continue
            compound = ' '.join(words[i - 1:i + n])
            if self.lexicon.lemma(compound) is not None and not self.lexicon.heads_as(compound, head):
                return True
        return False

    def _foreign_words(self, title: str, want: Sequence[str]) -> int:
        if self.lexicon is None or not self.lexicon.available:
            return 0
        raw = _title_words(title)
        keyed = _raw_words(title)
        n = 0
        for w, kw in zip(raw, keyed):
            if w in FUNCTION_WORDS or kw in want or w.isdigit() or len(w) < 3:
                continue
            if self.lexicon.lemma(w) is None and self.lexicon.lemma(kw) is None:
                n += 1
        return n

    def _rank(self, cands: List[Candidate], want: Sequence[str]) -> List[Candidate]:
        scored = []
        for c in cands:
            s = self._score(c, want)
            if s is not None:
                scored.append((-s, hashlib.sha1(f'{c.source}:{c.source_id}'.encode()).hexdigest(), c))
        scored.sort(key=lambda t: (t[0], t[1]))
        return [c for _s, _h, c in scored]

    def _openverse(self, query: str) -> List[Candidate]:
        url = 'https://api.openverse.org/v1/images/?' + urllib.parse.urlencode({
            'q': query, 'license': ','.join(sorted(OPENVERSE_LICENSES)), 'license_type': 'commercial',
            'mature': 'false', 'page_size': PAGE_SIZE,
        })
        doc = _fetch_json(url)
        out: List[Candidate] = []
        for r in doc.get('results') or []:
            lic = str(r.get('license') or '').lower()
            if lic not in OPENVERSE_LICENSES or r.get('mature'):
                continue
            file_url = str(r.get('url') or '')
            if not file_url or not file_url.lower().endswith(('.jpg', '.jpeg')):
                continue
            tags = tuple(str(t.get('name') or '') for t in (r.get('tags') or []) if isinstance(t, dict) and t.get('name'))
            out.append(Candidate(
                'openverse', str(r.get('provider') or r.get('source') or ''), str(r.get('id') or ''), str(r.get('title') or ''),
                str(r.get('creator') or ''), 'CC0 1.0' if lic == 'cc0' else 'Public Domain',
                str(r.get('license_url') or ('https://creativecommons.org/publicdomain/zero/1.0/' if lic == 'cc0' else 'https://creativecommons.org/publicdomain/mark/1.0/')),
                str(r.get('foreign_landing_url') or ''), file_url, int(r.get('width') or 0), int(r.get('height') or 0), tags,
            ))
        return out

    def _commons(self, query: str) -> List[Candidate]:
        url = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode({
            'action': 'query', 'format': 'json', 'generator': 'search', 'gsrsearch': f'{query} haslicense:unrestricted filetype:bitmap',
            'gsrnamespace': 6, 'gsrlimit': PAGE_SIZE, 'prop': 'imageinfo', 'iiprop': 'url|extmetadata|size|mime',
            'iiurlwidth': MAX_EDGE,
        })
        doc = _fetch_json(url)
        out: List[Candidate] = []
        for page in (doc.get('query') or {}).get('pages', {}).values():
            infos = page.get('imageinfo') or []
            if not infos:
                continue
            ii = infos[0]
            meta = ii.get('extmetadata') or {}
            short = str((meta.get('LicenseShortName') or {}).get('value') or '').strip()
            if not (short.lower().startswith('cc0') or short.lower() in COMMONS_LICENSES):
                continue
            if str(ii.get('mime') or '') != 'image/jpeg':   # a PNG on Commons is nearly always a graphic
                continue
            artist = re.sub(r'<[^>]+>', '', str((meta.get('Artist') or {}).get('value') or '')).strip()
            cats = tuple(c.strip() for c in str((meta.get('Categories') or {}).get('value') or '').split('|')
                         if c.strip() and not HOUSEKEEPING_CATEGORY.match(c.strip()))
            out.append(Candidate(
                'wikimedia_commons', 'commons', str(page.get('pageid') or ''), str(page.get('title') or ''), artist,
                'CC0 1.0' if short.lower().startswith('cc0') else 'Public Domain',
                str((meta.get('LicenseUrl') or {}).get('value') or ''), str(ii.get('descriptionurl') or ''),
                str(ii.get('thumburl') or ii.get('url') or ''), int(ii.get('width') or 0), int(ii.get('height') or 0), cats,
                _year(str((meta.get('DateTimeOriginal') or {}).get('value') or '')),
            ))
        return out

    # -- materialise ---------------------------------------------------------------------------
    def _materialise(self, cand: Candidate, concept: str, query: str) -> Optional[PhotoRecord]:
        data = _fetch_bytes(cand.file_url)
        if data is None:
            return None
        self.root.mkdir(parents=True, exist_ok=True)
        raw = self.root / f'.incoming-{hashlib.sha1(cand.file_url.encode()).hexdigest()[:12]}'
        raw.write_bytes(data)
        try:
            name = f'{_slug(concept)}.{hashlib.sha256(data).hexdigest()[:12]}.jpg'
            target = self.root / name
            if not _normalise(raw, target):
                return None
            size = _probe_size(target)
            if size is None or _is_monochrome(target):
                target.unlink(missing_ok=True)
                return None
        finally:
            raw.unlink(missing_ok=True)
        return PhotoRecord(
            concept=concept, query=query, source=cand.source, provider=cand.provider, source_id=cand.source_id,
            title=cand.title, creator=cand.creator, license=cand.license, license_url=cand.license_url,
            landing_url=cand.landing_url, file_url=cand.file_url, file=name,
            sha256=hashlib.sha256(target.read_bytes()).hexdigest(), width=size[0], height=size[1],
            fetched=time.strftime('%Y-%m-%d'), subjects=tuple(cand.subjects), year=cand.year,
            source_size=(cand.width, cand.height),
        )

    def _save(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        doc = {
            'note': 'Photo evidence for the concept ladder: CC0 / public-domain only, normalised by ffmpeg, keyed by concept.',
            'photos': {k: asdict(v) for k, v in sorted(self.index.items())},
            'misses': dict(sorted(self.misses.items())),
        }
        tmp = self.root / (INDEX_NAME + '.tmp')
        tmp.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
        tmp.replace(self.root / INDEX_NAME)


def _normalise(src: Path, target: Path) -> bool:
    """One render-safe JPEG, longest edge ≤ MAX_EDGE, metadata stripped, bit-exact for the same input."""
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        return False
    out = subprocess.run([
        ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(src), '-frames:v', '1', '-an', '-map_metadata', '-1',
        '-fflags', '+bitexact', '-flags:v', '+bitexact', '-idct', 'simple',
        '-vf', f"scale='min({MAX_EDGE},iw)':'min({MAX_EDGE},ih)':force_original_aspect_ratio=decrease:flags=lanczos,format=yuvj420p",
        '-q:v', '3', str(target),
    ], capture_output=True, text=True, check=False)
    return out.returncode == 0 and target.exists() and target.stat().st_size > 0


def _is_monochrome(path: Path) -> bool:
    """A black-and-white frame is an archive print or an art study, whatever its title says."""
    ffprobe = shutil.which('ffprobe')
    if not ffprobe:
        return False
    out = subprocess.run([ffprobe, '-v', 'error', '-f', 'lavfi', '-i', f'movie={path},signalstats',
                          '-show_entries', 'frame_tags=lavfi.signalstats.SATAVG', '-of', 'csv=p=0'],
                         capture_output=True, text=True, check=False)
    try:
        return out.returncode == 0 and float(out.stdout.strip().split('\n')[0]) < MONOCHROME_SATURATION
    except ValueError:
        return False


def _probe_size(path: Path) -> Optional[tuple]:
    ffprobe = shutil.which('ffprobe')
    if not ffprobe:
        return None
    out = subprocess.run([ffprobe, '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                          '-of', 'csv=p=0', str(path)], capture_output=True, text=True, check=False)
    parts = out.stdout.strip().split(',')
    if out.returncode != 0 or len(parts) < 2 or not all(p.strip().isdigit() for p in parts[:2]):
        return None
    w, h = int(parts[0]), int(parts[1])
    return (w, h) if w >= MIN_EDGE // 2 and h >= MIN_EDGE // 2 else None
