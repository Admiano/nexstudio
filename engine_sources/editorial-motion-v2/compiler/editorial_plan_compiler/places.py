"""The environment artist's atlas: every place a story can happen in, what names it, what
hints at it, and the set pieces that make it read as itself on a still page.

A place is chosen from the words of the page (and carried from the page before when the
page names none); its painter draws the ground and sky, its dressing stands in the world.
Nouns a place prints (a barn on a farm, a window in a room) are answered by the scene,
never repeated as stickers."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

# (concept, x, baseline, width, height, plane) — x/width as fractions of the canvas width,
# baseline/height as fractions of its height. Width 0 keeps the art's own proportions.
Dress = Tuple[str, float, float, float, float, float]


@dataclass(frozen=True)
class Place:
    name: str
    painter: str
    names: FrozenSet[str]
    cues: FrozenSet[str]
    dressing: Tuple[Dress, ...]
    interior: bool = False

    @property
    def covers(self) -> FrozenSet[str]:
        return self.names | frozenset(c for c, *_ in self.dressing)


def _p(name: str, painter: str, names: str, cues: str, dressing: Sequence[Dress], interior: bool = False) -> Place:
    return Place(name, painter, frozenset(names.split()), frozenset(cues.split()), tuple(dressing), interior)


# Order breaks ties: the more specific place wins over the broader one.
PLACES: Tuple[Place, ...] = (
    _p('classroom', 'classroom', 'classroom class lesson', 'teacher desk chalkboard blackboard pupil student homework',
       [('chalkboard', 0.22, 0.50, 0.46, 0.27, 0.2), ('bookshelf', 0.80, 0.70, 0.13, 0.36, 0.3),
        ('globe-showing-americas', 0.82, 0.335, 0.0, 0.09, 0.32), ('window', 0.07, 0.50, 0.11, 0.26, 0.2),
        ('desk', 0.12, 0.92, 0.20, 0.16, 0.62), ('desk', 0.40, 0.92, 0.20, 0.16, 0.62), ('desk', 0.68, 0.92, 0.20, 0.16, 0.62)],
       interior=True),
    _p('kitchen', 'kitchen', 'kitchen', 'stove oven cook cooking bake baking kettle pan fridge sink cupboard',
       [('cupboard', 0.06, 0.34, 0.32, 0.16, 0.2), ('window', 0.46, 0.46, 0.18, 0.26, 0.2),
        ('cupboard', 0.72, 0.34, 0.22, 0.16, 0.2), ('counter', 0.03, 0.74, 0.94, 0.22, 0.32),
        ('stove', 0.66, 0.74, 0.18, 0.26, 0.34), ('teapot', 0.30, 0.52, 0.0, 0.08, 0.36),
        ('potted-plant', 0.52, 0.52, 0.0, 0.08, 0.34)], interior=True),
    _p('bedroom', 'bedroom', 'bedroom nursery', 'bed pillow blanket pyjamas pajamas bedtime asleep sleep',
       [('window', 0.10, 0.52, 0.16, 0.30, 0.2), ('curtain', 0.05, 0.56, 0.07, 0.36, 0.22), ('curtain', 0.24, 0.56, 0.07, 0.36, 0.22),
        ('frame', 0.70, 0.34, 0.10, 0.15, 0.2), ('bed', 0.52, 0.86, 0.40, 0.24, 0.45), ('teddy-bear', 0.56, 0.70, 0.0, 0.09, 0.47), ('lamp', 0.88, 0.72, 0.07, 0.24, 0.4),
        ('rug', 0.24, 0.97, 0.36, 0.10, 0.5)], interior=True),
    _p('home', 'room', 'room lounge indoors inside living-room', 'sofa couch fireplace rug curtain lamp window table chair shelf',
       [('window', 0.08, 0.52, 0.16, 0.30, 0.2), ('curtain', 0.03, 0.56, 0.07, 0.36, 0.22), ('curtain', 0.20, 0.56, 0.07, 0.36, 0.22),
        ('fireplace', 0.40, 0.72, 0.24, 0.32, 0.24), ('frame', 0.46, 0.30, 0.12, 0.14, 0.2), ('bookshelf', 0.78, 0.72, 0.15, 0.40, 0.28),
        ('rug', 0.26, 0.97, 0.46, 0.12, 0.5)], interior=True),
    _p('farm', 'fields', 'farm farmyard barn pasture ranch crops countryside',
       'tractor cow pig hen chicken rooster sheep goat horse farmer hay haystack corn wheat scarecrow lamb calf piglet',
       [('barn', 0.56, 0.66, 0.22, 0.30, 0.34), ('silo', 0.79, 0.66, 0.07, 0.34, 0.33),
        ('haystack', 0.14, 0.74, 0.14, 0.11, 0.45), ('tractor', 0.36, 0.73, 0.0, 0.09, 0.46),
        ('fence', 0.02, 0.84, 0.46, 0.09, 0.6), ('fence', 0.52, 0.84, 0.46, 0.09, 0.6)]),
    _p('airport', 'runway', 'airport runway airfield terminal hangar',
       'airplane plane jet pilot luggage suitcase passenger flight helicopter',
       [('terminal', 0.06, 0.60, 0.44, 0.14, 0.26), ('controltower', 0.72, 0.60, 0.10, 0.36, 0.26),
        ('small-airplane', 0.22, 0.20, 0.0, 0.07, 0.18), ('airplane', 0.56, 0.72, 0.0, 0.11, 0.4)]),
    _p('stadium', 'pitch', 'stadium pitch football soccer arena match',
       'goal goalkeeper keeper referee striker team whistle score scored kick kicked',
       [('stands', -0.08, 0.54, 1.16, 0.22, 0.24), ('floodlight', 0.04, 0.40, 0.08, 0.32, 0.22),
        ('floodlight', 0.88, 0.40, 0.08, 0.32, 0.22), ('goal', 0.80, 0.78, 0.16, 0.16, 0.5)]),
    _p('school', 'yard', 'school schoolyard playground recess',
       'teacher pupil student bell satchel backpack',
       [('schoolhouse', 0.30, 0.64, 0.42, 0.34, 0.3), ('flagpole', 0.80, 0.66, 0.08, 0.36, 0.3),
        ('school-bus', 0.08, 0.80, 0.0, 0.10, 0.5), ('fence', 0.52, 0.84, 0.46, 0.08, 0.6)]),
    _p('cottage', 'land', 'house cottage cabin hut home doorstep porch', 'roof chimney porch doorstep gate',
       [('house', 0.44, 0.72, 0.30, 0.36, 0.34), ('evergreen-tree', 0.12, 0.72, 0.0, 0.30, 0.36),
        ('deciduous-tree', 0.80, 0.72, 0.0, 0.28, 0.36), ('fence', 0.60, 0.86, 0.38, 0.08, 0.6)]),
    _p('harbour', 'sea', 'harbor harbour port dock quay pier wharf marina',
       'boat ship sailor fisherman anchor lighthouse seagull gull',
       [('lighthouse', 0.84, 0.54, 0.0, 0.30, 0.24), ('sailboat', 0.22, 0.58, 0.0, 0.10, 0.28),
        ('pier', -0.04, 0.80, 0.46, 0.14, 0.55)]),
    _p('beach', 'sand', 'beach shore seaside coast sand', 'sandcastle shell bucket spade surf wave crab',
       [('palm-tree', 0.04, 0.74, 0.0, 0.36, 0.36), ('umbrella-on-ground', 0.74, 0.82, 0.0, 0.16, 0.45),
        ('sandcastle', 0.30, 0.88, 0.12, 0.10, 0.55), ('spiral-shell', 0.56, 0.92, 0.0, 0.05, 0.6)]),
    _p('forest', 'woods', 'forest woods wood grove jungle', 'owl fox deer squirrel mushroom log badger hedgehog',
       [('evergreen-tree', 0.00, 0.62, 0.0, 0.26, 0.26), ('evergreen-tree', 0.22, 0.60, 0.0, 0.22, 0.24),
        ('deciduous-tree', 0.64, 0.62, 0.0, 0.26, 0.26), ('evergreen-tree', 0.84, 0.61, 0.0, 0.24, 0.24),
        ('deciduous-tree', -0.06, 0.82, 0.0, 0.46, 0.5), ('evergreen-tree', 0.82, 0.84, 0.0, 0.50, 0.52),
        ('mushroom', 0.30, 0.86, 0.0, 0.06, 0.6), ('log', 0.56, 0.88, 0.16, 0.06, 0.6)]),
    _p('pond', 'pond', 'pond lake river stream', 'duck duckling frog lily reed swan',
       [('reed', 0.10, 0.74, 0.08, 0.14, 0.5), ('reed', 0.82, 0.76, 0.08, 0.16, 0.5),
        ('deciduous-tree', 0.70, 0.60, 0.0, 0.26, 0.3)]),
    _p('mountains', 'peaks', 'mountain mountains peak valley alps cliff', 'climber goat eagle',
       [('evergreen-tree', 0.10, 0.80, 0.0, 0.20, 0.5), ('evergreen-tree', 0.80, 0.82, 0.0, 0.24, 0.52)]),
    _p('desert', 'desert', 'desert dunes', 'cactus camel lizard scorpion',
       [('cactus', 0.12, 0.80, 0.0, 0.22, 0.45), ('cactus', 0.78, 0.76, 0.0, 0.14, 0.4)]),
    _p('space', 'space', 'space universe cosmos galaxy orbit', 'rocket astronaut planet comet satellite alien spaceship',
       [('ringed-planet', 0.70, 0.34, 0.0, 0.18, 0.2), ('globe-showing-americas', 0.06, 1.02, 0.0, 0.30, 0.3),
        ('satellite', 0.36, 0.22, 0.0, 0.08, 0.24)]),
    _p('underwater', 'underwater', 'underwater seabed reef', 'coral octopus whale shark jellyfish submarine seaweed',
       []),
    _p('city', 'street', 'city town street road downtown village shop store', 'car bus taxi traffic shop store building crossing',
       [('building', 0.02, 0.70, 0.16, 0.40, 0.3), ('convenience-store', 0.30, 0.70, 0.0, 0.22, 0.36),
        ('building', 0.56, 0.70, 0.14, 0.46, 0.3), ('office-building', 0.84, 0.70, 0.0, 0.34, 0.32),
        ('traffic-light', 0.20, 0.80, 0.0, 0.16, 0.5), ('taxi', 0.70, 0.86, 0.0, 0.09, 0.62)]),
    _p('garden', 'garden', 'garden yard backyard park', 'flower bee butterfly seed watering tulip sunflower',
       [('fence', -0.02, 0.70, 0.52, 0.10, 0.4), ('fence', 0.50, 0.70, 0.52, 0.10, 0.4),
        ('deciduous-tree', 0.78, 0.68, 0.0, 0.30, 0.34), ('tulip', 0.08, 0.86, 0.0, 0.08, 0.6),
        ('tulip', 0.16, 0.88, 0.0, 0.07, 0.62), ('sunflower', 0.88, 0.90, 0.0, 0.12, 0.62)]),
    _p('meadow', 'land', 'meadow field fields grass hill hills', '',
       [('deciduous-tree', 0.80, 0.70, 0.0, 0.28, 0.36)]),
)
BY_NAME: Dict[str, Place] = {p.name: p for p in PLACES}
INTERIOR_OF = {'cottage': 'home', 'school': 'classroom', 'farm': 'home'}
INSIDE = frozenset(('inside', 'indoors', 'room', 'window', 'fireplace', 'sofa', 'couch', 'rug', 'curtain', 'bed', 'table',
                    'kitchen', 'stove', 'oven', 'chalkboard', 'blackboard', 'desk', 'bedroom', 'classroom'))
OUTSIDE = frozenset(('outside', 'outdoors', 'yard', 'sky', 'sun'))
WINTER = frozenset(('snow', 'snowy', 'snowman', 'snowflake', 'winter', 'icicle', 'icicles', 'frost', 'frosty', 'sled', 'blizzard'))
THAW = frozenset(('summer', 'spring', 'blossom'))
# Wall fixtures frame a room; they never stand forward as a page's subject.
FIXTURES = frozenset(('window', 'curtain', 'frame', 'rug', 'fence', 'cupboard', 'counter'))
# Landscape features that may stand behind any outdoor place (a cabin on the mountain).
FAR_FEATURES = {'mountains': frozenset(('mountain', 'mountains', 'peak', 'alps'))}


def _words(text: str) -> List[str]:
    out = []
    for w in re.findall(r"[a-z]+", text.lower()):
        out.append(w[:-1] if len(w) > 3 and w.endswith('s') and not w.endswith('ss') else w)
        out.append(w)
    return out


def _score(ws: Sequence[str], p: Place) -> int:
    return sum(3 for w in set(ws) if w in p.names) + sum(1 for w in set(ws) if w in p.cues)


def place_of(text: str, prev: Optional[str]) -> Optional[str]:
    """The place a page's words name, or `prev` when they name none. Interior words move a
    house, school or farm story inside; "outside" steps back out of a room."""
    ws = _words(text)
    wset = set(ws)
    best, top = None, 0
    for p in PLACES:
        s = _score(ws, p)
        if s > top:
            best, top = p, s
    outside = bool(wset & OUTSIDE)
    inside = bool(wset & INSIDE) and not outside
    prev_p = BY_NAME.get(prev or '')
    if best is None or top < 2:
        # Only cue-level evidence: stay where the story is unless the page steps in or out.
        if prev_p is not None and (best is None or top < 1 or best.interior == prev_p.interior):
            if outside and prev_p.interior:
                return 'cottage' if prev_p.name in ('home', 'kitchen', 'bedroom') else 'school'
            if inside and not prev_p.interior:
                rooms = [(s, p.name) for p in PLACES if p.interior and (s := _score(ws, p)) > 0]
                return max(rooms, key=lambda sp: sp[0])[1] if rooms else INTERIOR_OF.get(prev_p.name, 'home')
            return prev_p.name
        if best is None:
            return 'home' if inside else prev
    assert best is not None
    if inside and not best.interior:
        rooms = [(s, p.name) for p in PLACES if p.interior and (s := _score(ws, p)) > 0]
        if rooms:
            return max(rooms, key=lambda sp: sp[0])[1]
        return INTERIOR_OF.get(best.name, 'home') if best.name in INTERIOR_OF or best.name == 'meadow' else best.name
    if outside and best.interior:
        return 'cottage'
    return best.name


@dataclass(frozen=True)
class Where:
    place: str
    winter: bool
    far: Tuple[str, ...]


def story_places(texts: Sequence[str]) -> List[Where]:
    """One place per page: the first place the story names stands behind every page before it."""
    first = None
    for t in texts:
        first = place_of(t, None)
        if first:
            break
    prev = first or 'meadow'
    winter = any(set(_words(t)) & WINTER for t in texts[:1])
    out: List[Where] = []
    for t in texts:
        ws = set(_words(t))
        name = place_of(t, prev) or prev
        if ws & WINTER:
            winter = True
        elif ws & THAW:
            winter = False
        far = [f for f, words in FAR_FEATURES.items() if ws & words and f != name]
        out.append(Where(name, winter, tuple(far)))
        prev = name
    return out


def covered(place: str, far: Sequence[str] = ()) -> FrozenSet[str]:
    """Every noun the painted place answers: its names, its set pieces, and far features."""
    p = BY_NAME.get(place)
    out = set(p.covers) if p else set()
    if p and p.interior:
        out |= {'house', 'home', 'cabin', 'cottage', 'room', 'wall', 'floor'}
    for f in far:
        out |= FAR_FEATURES.get(f, frozenset())
    return frozenset(out)
