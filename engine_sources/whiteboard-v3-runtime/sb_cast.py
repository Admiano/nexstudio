"""Storyboard cast: the proto whiteboard character as vector still poses.

Same figure as the RGS proto pack (tools/nexstick/baked/PROTO_*): circle
head, pear torso, stick limbs, oval hands, triangle shoes — drawn front-on
so both arms and a face read. Each still is a pose + a face + optional
expression marks, chosen from the emotion the scene context asks for.

Unit space: figure height H=260, feet at y=0, up is negative y.
Strokes: (points, color, width_scale, fill) — fill False | 'solid'.
"""
from __future__ import annotations

import math
import re

try:
    from nltk.corpus import wordnet as _wn
    _wn.synsets('dog')
except Exception:  # pragma: no cover - WordNet optional
    _wn = None

H = 260.0
HEAD_R = 0.155
HEAD_CY = -0.862
SH_Y = -0.700
HIP_Y = -0.420

# proto pack tones: light body, darker far-side hand/shoe
FILL = '#D9D4C7'
SHADE = '#8B8577'
# shirt tones — paper-pastel washes that give each cast member a color
SHIRTS = ('#8FB3E3', '#95C9A2', '#F2B27A', '#BCA8E0', '#E79A92', '#E9CB7A')


def shirt_for(key) -> str:
    """Stable shirt tone for a cast member (same name, same shirt)."""
    k = str(key or '').lower().strip()
    return SHIRTS[sum(ord(c) * (i + 1) for i, c in enumerate(k)) % len(SHIRTS)]

# occupation -> costume: shirt tone, hat, torso detail, glasses
_OUTFITS = (
    (r'farmer|\bfarm\b|farmhand|rancher|grower|picker|gardener|harvester|'
     r'vintner|vinedresser|shepherd|herder|cowboy',
     {'shirt': '#D98C6A', 'hat': 'straw', 'torso': 'overalls'}),
    (r'beekeeper|apiarist',
     {'shirt': '#F4F1EA', 'hat': 'veil'}),
    (r'fisher|angler|sailor|deckhand|trawler',
     {'shirt': '#E9CB7A', 'hat': 'bucket', 'torso': 'slicker'}),
    (r'pilot|aviator|captain|flight attendant',
     {'shirt': '#F4F1EA', 'hat': 'pilot', 'torso': 'tie'}),
    (r'judge',
     {'shirt': '#3A3D44', 'torso': 'robe', 'glasses': True}),
    (r'lawyer|attorney|solicitor|banker|businessm|businessw|executive|'
     r'\bceo\b|manager|investor|trader|accountant|broker|politician|'
     r'mayor|senator|salesm',
     {'shirt': '#5B6472', 'torso': 'tie'}),
    (r'doctor|surgeon|physician|dentist|vet\b|veterinar|pharmac',
     {'shirt': '#F4F1EA', 'torso': 'coat'}),
    (r'scientist|researcher|chemist|biologist|physicist|lab tech',
     {'shirt': '#F4F1EA', 'torso': 'coat', 'glasses': True}),
    (r'nurse|paramedic|\bmedic\b|caregiver|carer',
     {'shirt': '#9CCFC8', 'hat': 'nursecap', 'torso': 'scrubs'}),
    (r'chef|cook\b|baker|butcher',
     {'shirt': '#F4F1EA', 'hat': 'toque', 'torso': 'apron'}),
    (r'barista|waiter|waitress|server|bartender|cashier|shopkeeper|grocer|'
     r'sommelier|steward',
     {'shirt': '#95C9A2', 'torso': 'apron_brown'}),
    (r'firefighter|fireman|firemen|firefighters',
     {'shirt': '#E0A24A', 'hat': 'firehelmet', 'torso': 'stripes'}),
    (r'craftsman|artisan|artificer|potter|weaver|glassblower|jeweler|smith|'
     r'woodworker|cobbler|shoemaker|tailor|seamstress',
     {'shirt': '#C9B79C', 'torso': 'apron_brown'}),
    (r'builder|construction|carpenter|plumber|electrician|mechanic|'
     r'engineer|miner|welder|roofer|labou?rer|mason|bricklayer|plasterer',
     {'shirt': '#F2B27A', 'hat': 'hardhat', 'torso': 'vest'}),
    (r'police|officer|\bcops?\b|sheriff|detective|security|guard',
     {'shirt': '#6F8FBF', 'hat': 'policecap', 'torso': 'badge'}),
    (r'ranger|forester|park warden|wildlife officer|hiker|explorer|'
     r'zookeeper|gamekeeper|\bkeeper\b',
     {'shirt': '#8E9B6A', 'hat': 'ranger', 'torso': 'badge'}),
    (r'astronaut|cosmonaut|spaceman',
     {'shirt': '#F4F1EA', 'hat': 'spacehelmet', 'torso': 'badge'}),
    (r'diver|scuba|frogman',
     {'shirt': '#46505A', 'glasses': True, 'torso': 'slicker'}),
    (r'coach|trainer|referee|umpire',
     {'shirt': '#D0453E', 'hat': 'cap', 'torso': 'jersey'}),
    (r'athlete|player|contestant|striker|goalkeeper|goalie|footballer|'
     r'runner|swimmer|cyclist|boxer',
     {'shirt': '#3B7BD4', 'torso': 'jersey'}),
    (r'musician|singer|performer|entertainer|drummer|guitarist|'
     r'percussionist|pianist|dancer|actor|actress',
     {'shirt': '#9575CD', 'torso': 'jacket'}),
    (r'thief|burglar|robber|criminal|crook|bandit',
     {'shirt': '#46505A', 'hat': 'beanie', 'torso': 'stripes_dark'}),
    (r'jockey|equestrian|horseman|horsewoman',
     {'shirt': '#D0453E', 'hat': 'cap', 'torso': 'jersey'}),
    (r'journalist|reporter|writer|author|editor|columnist|photographer',
     {'shirt': '#E9CB7A', 'glasses': True, 'torso': 'jacket'}),
    (r'official|inspector|collector|civil servant|bureaucrat|diplomat',
     {'shirt': '#5B6472', 'torso': 'tie'}),
    (r'dispatcher|operator|controller|receptionist|clerk|teller|secretary',
     {'shirt': '#8FB3E3', 'hat': 'headset', 'torso': 'tie'}),
    (r'merchant|seller|vendor|dealer|retailer|shop assistant',
     {'shirt': '#E9CB7A', 'torso': 'apron_brown'}),
    (r'architect|designer|draftsman|draughtsman',
     {'shirt': '#8FB3E3', 'glasses': True, 'torso': 'jacket'}),
    (r'soldier|marine|troop',
     {'shirt': '#8E9B6A', 'hat': 'army'}),
    (r'teacher|professor|lecturer|tutor|librarian|programmer|developer|'
     r'coder|analyst|student|reader',
     {'glasses': True}),
    (r'driver|trucker|courier|delivery|postman|mail carrier',
     {'shirt': '#8FB3E3', 'hat': 'cap'}),
    (r'roaster',
     {'shirt': '#E9CB7A', 'torso': 'apron_brown'}),
)


def _match(text):
    for pat, fit in _OUTFITS:
        if text and re.search(pat, text):
            return dict(fit)
    return None


def _senses(word):
    """Person senses of a role word: its hypernym names (nearest first)
    and its definitions, from WordNet."""
    if _wn is None or not word:
        return [], []
    base = _wn.morphy(word, 'n') or word
    syn = [x for x in _wn.synsets(base.replace(' ', '_'), 'n')[:3]
           if x.lexname() == 'noun.person' and not x.instance_hypernyms()]
    names, seen, frontier = [], set(), syn
    for _depth in range(5):
        nxt = []
        for x in frontier:
            for h in x.hypernyms():
                if h.name() not in seen and h.name() != 'person.n.01':
                    seen.add(h.name())
                    names.append(' '.join(h.lemma_names()).replace('_', ' '))
                    nxt.append(h)
        frontier = nxt
    return names, [x.definition() for x in syn]


_ROOT_ROLE = (('food', 'cook'), ('beverage', 'barista'),
              ('plant', 'farmer'), ('animal', 'farmer'),
              ('vehicle', 'driver'), ('device', 'mechanic'),
              ('structure', 'builder'), ('building material', 'builder'),
              ('substance', 'scientist'), ('book', 'librarian'),
              ('document', 'clerk'), ('money', 'banker'))


def _root_role(word):
    """A job WordNet doesn't list ('chocolatier', 'cheesemaker') dresses
    for what its root word is: chocolate is food, so a cook."""
    if _wn is None:
        return None
    m = re.match(r'([a-z]+?)(?:maker|smith|monger|iers?|ers?|ists?|ors?)$',
                 word)
    if not m or len(m.group(1)) < 3 or _wn.synsets(word, 'n'):
        return None
    root = m.group(1)
    syn = (_wn.synsets(root, 'n') or _wn.synsets(root + 'e', 'n'))[:2]
    anc = {' '.join(h.lemma_names()).replace('_', ' ')
           for x in syn for path in x.hypernym_paths() for h in path}
    for cat, role in _ROOT_ROLE:
        if any(re.search(r'\b' + cat + r'\b', a) for a in anc):
            return _match(role)
    return None


# words that name a person by sex, age or family — not a job to dress for
_KINSHIP = re.compile(
    r"(wo)?m[ae]n|girls?|boys?|lady|ladies|gentleman|mother|mom|mum|"
    r"father|dad|son|daughter|wife|husband|sister|brother|aunt|uncle|"
    r"niece|nephew|grand(mother|father|ma|pa|son|daughter|child)|granny|"
    r"child(ren)?|kids?|baby|toddler|infant|teen(ager)?|youngster|"
    r"person|people|adult|elder|senior|friend|neighbou?r|family|parents?")


def outfit_for(*words) -> dict:
    """Costume for a cast member from its label/concept words — a farmer
    gets a straw hat and overalls, a lawyer a suit and tie. A role the
    table doesn't name dresses as its nearest WordNet ancestor (a vintner
    is a merchant, a sommelier a waiter), then by its definition (a
    farmhand is 'a hired hand on a farm')."""
    text = ' '.join(str(w or '') for w in words).lower().strip()
    fit = _match(text)
    if fit is not None:
        return fit
    for w in words:
        w = str(w or '').lower().strip()
        if _KINSHIP.fullmatch(w.split()[-1] if w else ''):
            continue
        heads = [w, w.split()[-1]] if ' ' in w else [w]
        for head in heads:
            names, glosses = _senses(head)
            for tier in (names, glosses):
                for t in tier:
                    fit = _match(t.lower())
                    if fit is not None:
                        return fit
            fit = _root_role(head)
            if fit is not None:
                return fit
    return {}


_FEMALE = re.compile(
    r"\b(she|her|hers|herself|woman|women|girl|girls|lady|ladies|mother|"
    r"mom|mum|mommy|daughter|wife|sister|aunt|niece|grandmother|grandma|"
    r"granny|queen|princess|bride|actress|waitress|hostess|nun|"
    r"policewoman|businesswoman|chairwoman|horsewoman|fisherwoman|"
    r"spokeswoman|stewardess|heroine|widow|girlfriend|madam|ms|mrs|miss)\b")
_MALE = re.compile(
    r"\b(he|him|his|himself|man|men|boy|boys|gentleman|father|dad|daddy|"
    r"son|husband|brother|uncle|nephew|grandfather|grandpa|king|prince|"
    r"groom|actor|waiter|monk|policeman|businessman|chairman|horseman|"
    r"fisherman|spokesman|steward|hero|widower|boyfriend|sir|mr)\b")
_CHILD = re.compile(
    r"\b(child|children|kid|kids|boy|boys|girl|girls|baby|toddler|son|"
    r"daughter|schoolboy|schoolgirl|pupil|infant|youngster|little|young|"
    r"teenager|teen|niece|nephew|grandchild|grandson|granddaughter)\b")
# rugged outdoor/craft trades wear beards more often than formal ones
_BEARDY = re.compile(
    r"farm|fisher|sailor|captain|lumber|logger|smith|ranger|miner|hunter|"
    r"carpenter|builder|beekeep|trucker|mechanic|shepherd|rancher|"
    r"woodcut|brew|potter|sculpt|artist|musician|guitar|professor|"
    r"explorer|climber|hiker|mountain|chef|baker|butcher|monk|wizard")
_FORMAL = re.compile(
    r"lawyer|attorney|banker|pilot|doctor|nurse|police|officer|soldier|"
    r"judge|manager|ceo|executive|accountant|clerk|agent|guard|"
    r"astronaut|athlete|swimmer|dentist|surgeon|waiter|driver")
HAIR_TONES = ('#2E2420', '#5A3D2B', '#8A5A35', '#C48A4A', '#E0C07A',
              '#1C1C1C', '#9A9A9A')
HAIR_F = ('long', 'ponytail', 'bob', 'bun', 'wavy')
HAIR_M = ('short', 'side', 'curly', 'buzz', 'spiky', 'short', 'bald')
HAIR_CHILD_F = ('pigtails', 'ponytail', 'bob', 'long')
HAIR_CHILD_M = ('short', 'spiky', 'curly', 'side')


def _seed(key, salt):
    h = 2166136261
    for ch in f'{salt}:{key}'.lower():
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return h


def _wn_is(word, roots):
    if _wn is None or not word:
        return False
    for s in _wn.synsets(_wn.morphy(word, 'n') or word, 'n')[:2]:
        if s.lexname() != 'noun.person':
            continue
        if any(h.name() in roots for p in s.hypernym_paths() for h in p):
            return True
    return False


def lexical_sex(label: str) -> str:
    """'f' / 'm' when the word itself says so (its spelling, WordNet
    ancestry, or the head of its WordNet gloss: 'a female grandchild'),
    else ''."""
    label = str(label or '').lower()
    head = label.split()[-1] if label else ''
    if _FEMALE.search(label) or _wn_is(head, {'female.n.02', 'woman.n.01'}):
        return 'f'
    if _MALE.search(label) or _wn_is(head, {'male.n.02', 'man.n.01'}):
        return 'm'
    if _wn is not None and head:
        for s in _wn.synsets(_wn.morphy(head, 'n') or head, 'n')[:1]:
            if s.lexname() != 'noun.person':
                continue
            lead = ' '.join(s.definition().split()[:3])
            if re.search(r'\b(female|woman|girl|daughter|mother)\b', lead):
                return 'f'
            if re.search(r'\b(male|man|boy|son|father)\b', lead):
                return 'm'
    return ''


def look_for(role) -> dict:
    """Body and grooming for a cast member: sex (from the role word, its
    WordNet ancestry, or the pronouns the plan bound to it), child scale,
    and a hairstyle / hair tone / beard picked deterministically from the
    label — beards more likely on rugged trades than formal ones."""
    role = role or {}
    label = str(role.get('label') or '').lower()
    head = label.split()[-1] if label else ''
    sex = lexical_sex(label)
    if not sex:
        sex = 'f' if role.get('gender') == 'f' else 'm'
    if role.get('cast_key'):
        label = f"{label} {role['cast_key']}".lower()
    child = role.get('age') == 'child' or bool(_CHILD.search(label)) \
        or _wn_is(head, {'juvenile.n.01'})
    key = str(role.get('cast_key') or label)
    styles = ((HAIR_CHILD_F if child else HAIR_F) if sex == 'f' else
              (HAIR_CHILD_M if child else HAIR_M))
    hair = styles[_seed(key, 'hair') % len(styles)]
    tones = HAIR_TONES[:5] if child else HAIR_TONES
    tone = tones[_seed(key, 'tone') % len(tones)]
    if re.search(r'\b(grand(father|mother|pa|ma)|granny|old|elderly|'
                 r'elder|senior|retiree|pensioner)\b', label):
        tone = '#9A9A9A'
    if tone == '#9A9A9A' and hair == 'bald':
        hair = 'short'
    beard = role.get('beard') if sex == 'm' and not child else None
    if sex == 'm' and not child and not beard:
        pool = (('full', 'full', 'goatee', 'stubble', 'mustache', None)
                if _BEARDY.search(label) else
                (None, None, None, 'mustache', 'stubble')
                if _FORMAL.search(label) else
                (None, None, 'stubble', 'goatee', 'mustache', 'full'))
        beard = pool[_seed(key, 'beard') % len(pool)]
    skirt = sex == 'f' and _seed(key, 'skirt') % 5 < 3
    return {'sex': sex, 'child': child, 'hair': hair, 'hair_tone': tone,
            'beard': beard, 'skirt': skirt}


CHILD_SCALE = 0.66


# poses where the far hand joins the near one on the object
_TWO_HANDED = {'reach', 'offer', 'hold', 'lift', 'read', 'dig', 'type',
               'climb'}
# verbs that turn a figure side-on toward what it is doing
ENGAGED = {'reach', 'offer', 'hold', 'lift', 'point', 'carry', 'give',
           'show', 'drink', 'read', 'write', 'type', 'dig', 'climb'}

# arm = (elbow, hand) per side, leg = (knee, foot); x > 0 is screen right.
# All in figure heights. Only still poses — no motion is authored here.
_IDLE_ARM = ((0.15, -0.56), (0.19, -0.41))
_IDLE_LEG = ((0.055, -0.20), (0.085, 0.0))
POSES = {
    'idle':      {'r': _IDLE_ARM, 'l': _IDLE_ARM},
    'think':     {'r': ((0.15, -0.50), (0.045, -0.705)),
                  'l': _IDLE_ARM},
    'panic':     {'r': ((0.23, -0.86), (0.095, -0.945)),
                  'l': ((0.23, -0.86), (0.095, -0.945)),
                  'leg': ((0.035, -0.20), (0.11, 0.0))},
    'cheer':     {'r': ((0.19, -0.87), (0.25, -1.01)),
                  'l': ((0.19, -0.87), (0.25, -1.01)),
                  'leg': ((0.07, -0.20), (0.13, 0.0))},
    'crossed':   {'r': ((0.14, -0.55), (-0.075, -0.60)),
                  'l': ((0.14, -0.55), (-0.075, -0.60))},
    'slump':     {'r': ((0.105, -0.50), (0.11, -0.33)),
                  'l': ((0.105, -0.50), (0.11, -0.33)),
                  'head': (0.02, 0.035), 'sh': 0.02},
    'shrug':     {'r': ((0.22, -0.60), (0.29, -0.74)),
                  'l': ((0.22, -0.60), (0.29, -0.74)), 'sh': -0.015},
    'point':     {'r': ((0.21, -0.69), (0.37, -0.72)), 'l': _IDLE_ARM},
    'fist':      {'r': ((0.18, -0.87), (0.19, -1.01)), 'l': _IDLE_ARM},
    'wave':      {'r': ((0.22, -0.74), (0.26, -0.93)), 'l': _IDLE_ARM},
    'hands-hips': {'r': ((0.20, -0.56), (0.10, -0.44)),
                   'l': ((0.20, -0.56), (0.10, -0.44))},
    'hold':      {'r': ((0.20, -0.53), (0.31, -0.60)), 'l': _IDLE_ARM},
    'offer':     {'r': ((0.21, -0.56), (0.34, -0.66)),
                  'l': ((0.21, -0.56), (0.34, -0.66))},
    'reach':     {'r': ((0.25, -0.64), (0.44, -0.63)), 'l': _IDLE_ARM},
    'lift':      {'r': ((0.22, -0.74), (0.33, -0.90)), 'l': _IDLE_ARM},
    # hand at the mouth: a cup or a bite is lifted to the lips
    'drink':     {'r': ((0.19, -0.62), (0.115, -0.785)), 'l': _IDLE_ARM,
                  'head': (-0.012, 0.0)},
    # both hands hold the page up in front, head bowed to it
    'read':      {'r': ((0.17, -0.56), (0.25, -0.70)), 'l': _IDLE_ARM,
                  'head': (0.012, 0.012)},
    'write':     {'r': ((0.20, -0.53), (0.31, -0.49)), 'l': _IDLE_ARM,
                  'head': (0.015, 0.015)},
    'type':      {'r': ((0.21, -0.54), (0.33, -0.52)), 'l': _IDLE_ARM,
                  'head': (0.01, 0.01)},
    # a long tool gripped low with both hands, body leaning in
    'dig':       {'r': ((0.19, -0.50), (0.27, -0.40)), 'l': _IDLE_ARM,
                  'head': (0.03, 0.02)},
    'climb':     {'r': ((0.15, -0.82), (0.22, -0.98)), 'l': _IDLE_ARM},
    # both hands pressed to the sides of the head
    'holdhead':  {'r': ((0.25, -0.76), (0.13, -0.86)),
                  'l': ((0.25, -0.76), (0.13, -0.86)),
                  'head': (0.0, 0.02), 'sh': 0.015},
    # arms open around someone in front
    'hug':       {'r': ((0.20, -0.62), (0.34, -0.64)),
                  'l': ((0.20, -0.62), (0.30, -0.60))},
    # hands clasped at the chest
    'clasp':     {'r': ((0.14, -0.55), (0.04, -0.64)),
                  'l': ((0.14, -0.55), (0.04, -0.64))},
}

# interaction verbs -> still pose (the emotion keeps its face and marks)
ACTIONS = {'hold': 'hold', 'carry': 'hold', 'point': 'point',
           'show': 'point', 'offer': 'offer', 'give': 'offer',
           'reach': 'reach', 'lift': 'lift', 'wave': 'wave',
           'drink': 'drink', 'eat': 'drink', 'read': 'read',
           'write': 'write', 'type': 'type', 'dig': 'dig', 'climb': 'climb'}

# body stance: how far the upper body drops (figure heights) and whether
# the figure must turn side-on for the stance to read
STANCES = {'stand': 0.0, 'walk': 0.0, 'climb': 0.0, 'sit': 0.17,
           'kneel': 0.12}
# held-prop height as a fraction of the figure, by arm pose: a cup at the
# lips is small, a shovel reaches the ground
PROP_SCALE = {'drink': 0.13, 'read': 0.22, 'write': 0.13, 'type': 0.20,
              'dig': 0.62}


def _stance_legs(stance, sgn):
    """[(hip, knee, foot)] in figure heights for a side-on stance, near
    leg last; None for the standing stance."""
    hip_y = HIP_Y + 0.03 + STANCES.get(stance, 0.0)
    if stance == 'sit':
        return [((-sgn * 0.01, hip_y), (sgn * 0.15, hip_y - 0.005),
                 (sgn * 0.165, 0.0)),
                ((sgn * 0.01, hip_y), (sgn * 0.175, hip_y - 0.01),
                 (sgn * 0.20, 0.0))]
    if stance == 'walk':
        return [((-sgn * 0.01, hip_y), (-sgn * 0.035, -0.20),
                 (-sgn * 0.11, -0.012)),
                ((sgn * 0.01, hip_y), (sgn * 0.075, -0.215),
                 (sgn * 0.13, 0.0))]
    if stance == 'climb':
        return [((-sgn * 0.01, hip_y), (sgn * 0.005, -0.20),
                 (-sgn * 0.005, 0.0)),
                ((sgn * 0.01, hip_y), (sgn * 0.13, -0.33),
                 (sgn * 0.14, -0.17))]
    if stance == 'kneel':
        return [((-sgn * 0.01, hip_y), (-sgn * 0.01, -0.025),
                 (-sgn * 0.17, -0.012)),
                ((sgn * 0.01, hip_y), (sgn * 0.13, hip_y + 0.005),
                 (sgn * 0.14, 0.0))]
    return None


def _seat(sgn, hip_y):
    """A plain stool under a seated figure (unit px)."""
    top = hip_y + 0.035
    x0, x1 = -sgn * 0.09, sgn * 0.11
    seat = [_p(x0, top), _p(x1, top), _p(x1, top + 0.03),
            _p(x0, top + 0.03)]
    st = [(seat + [seat[0]], '#A57A55', 0.8, 'solid')]
    for x in (x0 + sgn * 0.02, x1 - sgn * 0.02):
        st.append(([_p(x, top + 0.03), _p(x, 0.0)], 'ink', 0.8, False))
    return st

# emotion -> (pose, face, marks)
EMOTIONS = {
    'neutral':   ('idle', 'neutral', ()),
    'happy':     ('wave', 'smile', ()),
    'think':     ('think', 'think', ('bubble',)),
    'alert':     ('point', 'alert', ('exclaim',)),
    'excited':   ('cheer', 'grin', ('burst',)),
    'greedy':    ('cheer', 'grin', ('burst',)),
    'panic':     ('panic', 'scared', ('sweat', 'shake')),
    'afraid':    ('panic', 'scared', ('sweat',)),
    'calm':      ('crossed', 'serene', ()),
    'confident': ('hands-hips', 'smirk', ()),
    'sad':       ('slump', 'sad', ('drop',)),
    'defeated':  ('slump', 'sad', ('gloom',)),
    'confused':  ('shrug', 'confused', ('question',)),
    'angry':     ('fist', 'angry', ('steam',)),
    'proud':     ('fist', 'smile', ('burst',)),
    'explain':   ('point', 'smile', ()),
    'content':   ('idle', 'smile', ()),
    'laugh':     ('clasp', 'laugh', ('laughlines',)),
    'cry':       ('slump', 'cry', ('tears',)),
    'love':      ('hug', 'serene', ('heart',)),
    'stressed':  ('holdhead', 'sad', ('sweat', 'gloom')),
    'tired':     ('slump', 'tired', ('gloom',)),
    'sleep':     ('idle', 'serene', ('zzz',)),
}
# faces a narrated feeling must show, used by the story QA
FEELING_FACES = {'laugh', 'cry', 'love', 'stressed', 'tired', 'sleep',
                 'happy', 'sad', 'angry', 'afraid', 'panic', 'excited',
                 'proud', 'calm'}

# context words -> emotion, first match wins (annotation, cue, label order)
_LEXICON = [
    ('panic', r'panic|crash|dump|scared|terrif|capitulat|sell[- ]?off|'
              r'liquidat|meltdown|freak'),
    ('afraid', r'fear|worr|anxi|nervous|risk|danger|threat|stress|'
               r'frustrat|stuck|overwhelm'),
    ('excited', r'fomo|hype|\bmoon|pump|euphor|excit|\brush|chase|\bape'),
    ('greedy', r'greed|get rich|all in|lambo'),
    ('calm', r'calm|rational|patien|disciplin|steady|zen|relax|stay'),
    ('think', r'think|\bread\b|\breads\b|analy|research|\bstud|consider|interpret|'
              r'wonder|\bplan|learn|figure out'),
    ('confident', r'confiden|\bsure\b|\bwin|expert|\bpro\b|smart|better'),
    ('alert', r'\bsee|spot|notice|early|earlier|first|discover|\bfind|'
              r'aware|signal'),
    ('defeated', r'defeat|give up|quit|burn ?out|wreck|rekt|exhaust|tired'),
    ('sad', r'\bsad|\blose|\blost|\bloss|\bmiss|regret|broke|bag ?holder'),
    ('confused', r'confus|unsure|\bwhy\b|doubt|\?'),
    ('angry', r'angry|\bmad\b|furious|rage|scam|cheat|unfair'),
    ('proud', r'proud|success|achiev|made it|profit|\bgain'),
    ('happy', r'happy|glad|thank|welcome|hello|love|enjoy'),
    ('explain', r'explain|show|present|teach|guide|point'),
]


def emotion_for(role) -> str:
    """Pick the still's emotion: explicit role['emotion'] wins, then a
    legacy role['expression'] hint, then the role's own words."""
    em = str(role.get('emotion') or '').lower().strip()
    if em in EMOTIONS:
        return em
    for k in ('annotate', 'cue', 'label', 'narration'):
        text = str(role.get(k) or '').lower()
        for emo, pat in _LEXICON:
            if text and re.search(pat, text):
                return emo
    ex = str(role.get('expression') or '').lower()
    dflt = 'content' if role.get('narration') else 'neutral'
    return {'thinking': 'think', 'exclaim': 'alert'}.get(ex, dflt)


def _circle(cx, cy, rx, ry=None, n=26, a0=0.0, a1=2 * math.pi):
    ry = rx if ry is None else ry
    return [(cx + math.cos(a0 + (a1 - a0) * i / n) * rx,
             cy + math.sin(a0 + (a1 - a0) * i / n) * ry) for i in range(n + 1)]


def _p(x, y):
    return (x * H, y * H)


def _face(kind, hx, hy, r, turn=0, glasses=False):
    """Face strokes on the head circle (unit px). `turn` (-1/+1) slides
    the features toward that side for a three-quarter view."""
    st = []
    hx0 = hx
    hx = hx + turn * r * 0.34
    ex, ey = r * (0.25 if turn else 0.36), hy - r * 0.02
    my = hy + r * 0.46

    def dot(x, y, rr=r * 0.10):
        st.append((_circle(x, y, rr, n=10), 'ink', 0.8, 'solid'))

    def line(pts, w=0.75):
        st.append((pts, 'ink', w * 1.35, False))

    def arc(cx, cy, rx, ry, a0, a1, w=0.75):
        line(_circle(cx, cy, rx, ry, 12, a0, a1), w)

    if kind in ('neutral', 'think', 'smile', 'smirk', 'sad', 'angry',
                'confused'):
        dx = r * 0.10 if kind == 'think' else 0.0
        dy = -r * 0.10 if kind == 'think' else (r * 0.05 if kind == 'sad'
                                                 else 0.0)
        dot(hx - ex + dx, ey + dy)
        dot(hx + ex + dx, ey + dy)
    elif kind in ('alert', 'scared', 'grin'):
        for s in (-1, 1):
            line(_circle(hx + s * ex, ey, r * 0.19, r * 0.22, 14), 0.6)
            dot(hx + s * ex + r * (0.04 if kind == 'alert' else 0.0),
                ey + r * 0.03, r * 0.075)
    elif kind in ('serene', 'laugh', 'cry', 'tired'):
        # closed eyes: up-arcs (laugh), down-arcs (serene, cry, tired)
        a0, a1 = ((0.0, math.pi) if kind == 'laugh'
                  else (math.pi, 2 * math.pi))
        for s in (-1, 1):
            arc(hx + s * ex, ey + r * 0.05, r * 0.14, r * 0.10, a0, a1)
    # brows
    by = hy - r * 0.34
    bw = r * 0.18
    if kind in ('scared', 'sad', 'cry', 'tired'):
        for s in (-1, 1):
            line([(hx + s * (ex + bw), by + r * 0.05),
                  (hx + s * (ex - bw), by - r * 0.10)])
    elif kind == 'angry':
        for s in (-1, 1):
            line([(hx + s * (ex + bw), by - r * 0.08),
                  (hx + s * (ex - bw), by + r * 0.09)], 0.9)
    elif kind in ('alert', 'grin'):
        for s in (-1, 1):
            arc(hx + s * ex, by - r * 0.08, bw, r * 0.07, math.pi,
                2 * math.pi)
    elif kind in ('think', 'confused'):
        line([(hx - ex - bw, by + r * 0.02), (hx - ex + bw, by + r * 0.02)])
        arc(hx + ex, by - r * 0.06, bw, r * 0.09, math.pi, 2 * math.pi)
    elif kind == 'smirk':
        for s in (-1, 1):
            line([(hx + s * (ex + bw), by + r * 0.03),
                  (hx + s * (ex - bw), by + r * 0.06)])
    # mouth
    if kind in ('smile', 'serene'):
        arc(hx, my - r * 0.10, r * 0.26, r * 0.16, 0.15 * math.pi,
            0.85 * math.pi)
    elif kind in ('grin', 'laugh'):
        pts = _circle(hx, my - r * 0.10, r * 0.30, r * 0.24, 14, 0.0, math.pi)
        st.append((pts + [pts[0]], 'ink', 0.7, 'solid'))
    elif kind == 'smirk':
        line([(hx - r * 0.18, my), (hx + r * 0.10, my - r * 0.02),
              (hx + r * 0.24, my - r * 0.10)])
    elif kind == 'scared':
        st.append((_circle(hx, my, r * 0.12, r * 0.16, 12), 'ink', 0.7,
                   'solid'))
    elif kind == 'alert':
        line(_circle(hx, my, r * 0.09, r * 0.11, 10), 0.7)
    elif kind == 'tired':
        line([(hx - r * 0.16, my), (hx + r * 0.16, my)])
    elif kind in ('sad', 'angry', 'cry'):
        arc(hx, my + r * 0.10, r * 0.22, r * 0.13, 1.15 * math.pi,
            1.85 * math.pi)
    elif kind == 'confused':
        line([(hx - r * 0.20, my), (hx - r * 0.07, my - r * 0.06),
              (hx + r * 0.06, my + r * 0.03), (hx + r * 0.20, my - r * 0.03)])
    elif kind == 'think':
        line([(hx - r * 0.02, my), (hx + r * 0.20, my - r * 0.02)])
    else:
        line([(hx - r * 0.15, my), (hx + r * 0.15, my)])
    if turn:
        nx = hx0 + turn * r * 0.93
        line([(nx - turn * r * 0.02, ey + r * 0.04),
              (nx + turn * r * 0.16, ey + r * 0.24),
              (nx - turn * r * 0.04, ey + r * 0.30)], 0.6)
    if glasses:
        gr = r * 0.21
        for sx in (-1, 1):
            line(_circle(hx + sx * ex, ey, gr, gr * 0.9, 14), 0.55)
        line([(hx - ex + gr, ey), (hx + ex - gr, ey)], 0.55)
    return st


def _hat(kind, hx, hy, r, d):
    """Headwear strokes over the head (unit px); `d` = facing (+1/-1)."""
    st = []

    def poly(pts, col):
        st.append((pts + [pts[0]], col, 0.8, 'solid'))

    def dome(cy, rx, ry, col):
        pts = _circle(hx, cy, rx, ry, 18, math.pi, 2 * math.pi)
        poly(pts, col)

    top = hy - r
    if kind in ('straw', 'veil'):
        col = '#E3C27A' if kind == 'straw' else '#F4F1EA'
        dome(top + r * 0.38, r * 0.74, r * 0.62, col)
        poly(_circle(hx, top + r * 0.40, r * 1.55, r * 0.24, 22), col)
        st.append(([(hx - r * 0.72, top + r * 0.22),
                    (hx + r * 0.72, top + r * 0.22)], '#B5403A'
                   if kind == 'straw' else '#8B8577', 1.1, False))
        if kind == 'veil':
            for k in range(5):
                x = hx - r * 1.2 + k * r * 0.6
                st.append(([(x, top + r * 0.5), (x * 0 + hx + (x - hx) * 0.9,
                                                  hy + r * 0.9)],
                           'pale', 0.5, False))
    elif kind == 'ranger':
        poly([(hx - r * 0.55, top + r * 0.40), (hx - r * 0.18, top - r * 0.45),
              (hx, top - r * 0.30), (hx + r * 0.18, top - r * 0.45),
              (hx + r * 0.55, top + r * 0.40)], '#B98A5E')
        poly(_circle(hx, top + r * 0.42, r * 1.35, r * 0.20, 22), '#B98A5E')
        st.append(([(hx - r * 0.55, top + r * 0.28),
                    (hx + r * 0.55, top + r * 0.28)], '#6B4A32', 1.0, False))
    elif kind == 'bucket':
        poly([(hx - r * 0.70, top + r * 0.42), (hx - r * 0.55, top - r * 0.22),
              (hx + r * 0.55, top - r * 0.22), (hx + r * 0.70, top + r * 0.42)],
             '#A8B77A')
        poly([(hx - r * 1.18, top + r * 0.68), (hx - r * 0.70, top + r * 0.34),
              (hx + r * 0.70, top + r * 0.34), (hx + r * 1.18, top + r * 0.68)],
             '#A8B77A')
    elif kind in ('pilot', 'policecap', 'cap', 'army'):
        col = {'pilot': '#3A3D44', 'policecap': '#3B5C8C',
               'cap': '#8FB3E3', 'army': '#8E9B6A'}[kind]
        if kind in ('pilot', 'policecap'):
            poly([(hx - r * 0.92, top + r * 0.42), (hx - r * 1.05, top - r * 0.12),
                  (hx + r * 1.05, top - r * 0.12), (hx + r * 0.92, top + r * 0.42)],
                 col)
            st.append((_circle(hx + d * r * 0.1, top + r * 0.1, r * 0.13, n=10),
                       '#E5B83A', 0.6, 'solid'))
        else:
            dome(top + r * 0.45, r * 0.95, r * 0.72, col)
        if kind != 'army':
            poly([(hx + d * r * 0.30, top + r * 0.40),
                  (hx + d * r * 1.35, top + r * 0.58),
                  (hx + d * r * 0.30, top + r * 0.56)], '#3A3D44'
                 if kind != 'cap' else col)
    elif kind in ('firehelmet', 'hardhat'):
        col = '#D0453E' if kind == 'firehelmet' else '#E5B83A'
        dome(top + r * 0.45, r * 1.0, r * 0.82, col)
        if kind == 'firehelmet':
            poly(_circle(hx - d * r * 0.25, top + r * 0.47, r * 1.40, r * 0.18,
                         20), col)
            st.append((_circle(hx + d * r * 0.25, top + r * 0.02, r * 0.18,
                               r * 0.22, 10), '#E5B83A', 0.6, 'solid'))
        else:
            poly(_circle(hx, top + r * 0.47, r * 1.20, r * 0.14, 20), col)
            st.append(([(hx, top - r * 0.36), (hx, top + r * 0.40)], 'ink',
                       0.6, False))
    elif kind == 'spacehelmet':
        st.append((_circle(hx, hy, r * 1.32, n=26), '#A0CAE8', 0.9, False))
        st.append(([(hx + d * r * 0.55, hy - r * 0.95),
                    (hx + d * r * 0.85, hy - r * 0.62)], '#F4F1EA', 1.2,
                   False))
    elif kind == 'beanie':
        dome(top + r * 0.48, r * 0.98, r * 0.78, '#46505A')
        poly(_circle(hx, top + r * 0.48, r * 1.0, r * 0.14, 18), '#3A3D44')
    elif kind == 'headset':
        st.append((_circle(hx, hy, r * 1.08, r * 1.08, 20, math.pi * 1.05,
                           math.pi * 1.95), 'ink', 0.9, False))
        ex = hx - d * r * 1.02
        st.append((_circle(ex, hy, r * 0.20, n=10), '#46505A', 0.6, 'solid'))
        st.append(([(ex, hy + r * 0.15), (hx + d * r * 0.35, hy + r * 0.70)],
                   'ink', 0.7, False))
    elif kind == 'toque':
        poly([(hx - r * 0.62, top + r * 0.30), (hx - r * 0.62, top - r * 0.25),
              (hx + r * 0.62, top - r * 0.25), (hx + r * 0.62, top + r * 0.30)],
             '#F4F1EA')
        for cx, cy, rr in ((-0.45, -0.55, 0.45), (0.45, -0.55, 0.45),
                           (0.0, -0.80, 0.52)):
            poly(_circle(hx + r * cx, top + r * cy, r * rr, n=16), '#F4F1EA')
    elif kind == 'nursecap':
        poly([(hx - r * 0.55, top + r * 0.30), (hx - r * 0.45, top - r * 0.22),
              (hx + r * 0.45, top - r * 0.22), (hx + r * 0.55, top + r * 0.30)],
             '#F4F1EA')
        st.append(([(hx, top - r * 0.12), (hx, top + r * 0.20)], '#D0453E',
                   1.0, False))
        st.append(([(hx - r * 0.16, top + r * 0.04),
                    (hx + r * 0.16, top + r * 0.04)], '#D0453E', 1.0, False))
    return st


def _arcp(hx, hy, R, a0, a1, n=16, bump=0.0, k=0):
    """Points on a circle arc (angles in y-down radians); `bump` scallops
    the radius (curly/spiky edges) with `k` lobes."""
    out = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        rr = R * (1 + (bump * abs(math.sin(k * math.pi * i / n))
                       if bump else 0.0))
        out.append((hx + math.cos(a) * rr, hy + math.sin(a) * rr))
    return out


def _hair(style, tone, hx, hy, r, turn, hatted):
    """Hair strokes (unit px) -> (behind_head, over_head)."""
    back, front = [], []
    if not style:
        return back, front

    def poly(dst, pts):
        dst.append((pts + [pts[0]], tone, 0.8, 'solid'))

    t = turn
    bx = hx - t * r * 0.22
    if style in ('long', 'wavy'):
        n = 12
        bump = 0.06 if style == 'wavy' else 0.0
        side = [(bx - r * 1.08, hy - r * 0.1), (bx - r * 1.12, hy + r * 1.0),
                (bx - r * 0.9, hy + r * 1.5)]
        bot = _arcp(bx, hy + r * 1.35, r * 0.95, math.pi * 0.95,
                    math.pi * 0.05, n, bump, 5)
        poly(back, side + bot + [(bx + r * 1.12, hy + r * 1.0),
                                 (bx + r * 1.08, hy - r * 0.1)]
             + _arcp(bx, hy, r * 1.1, 0.0, -math.pi, 14))
    elif style == 'bob':
        poly(back, [(bx - r * 1.1, hy - r * 0.1), (bx - r * 1.12, hy + r * 0.8),
                    (bx + r * 1.12, hy + r * 0.8), (bx + r * 1.1, hy - r * 0.1)]
             + _arcp(bx, hy, r * 1.1, 0.0, -math.pi, 14))
    elif style == 'ponytail':
        px = hx - (t or 1) * r * 1.05
        poly(back, _arcp(px - (t or 1) * r * 0.12, hy + r * 0.45, r * 0.34,
                         0, 2 * math.pi, 14)
             if t else _arcp(hx, hy - r * 1.05, r * 0.3, 0, 2 * math.pi, 12))
        if t:
            poly(back, _arcp(hx - t * r * 0.9, hy - r * 0.2, r * 0.26, 0,
                             2 * math.pi, 10))
    elif style == 'bun':
        poly(back, _arcp(hx - t * r * 0.55, hy - r * 0.98, r * 0.36, 0,
                         2 * math.pi, 14))
    elif style == 'pigtails':
        for s in ((-1, 1) if not t else (-t,)):
            poly(back, _arcp(hx + s * r * 1.12, hy + r * 0.15, r * 0.3, 0,
                             2 * math.pi, 12))
    if hatted or style == 'bald':
        if style == 'bald' and not hatted:
            for s in ((-1, 1) if not t else (-t,)):
                poly(front, _arcp(hx + s * r * 0.86, hy - r * 0.05, r * 0.2,
                                  0, 2 * math.pi, 10))
        return back, front
    bump, k = {'curly': (0.09, 9), 'spiky': (0.16, 7), 'wavy': (0.04, 6)
               }.get(style, (0.0, 0))
    R = r * (1.04 if style == 'buzz' else 1.08)
    line_y = hy - r * (0.62 if style == 'buzz' else 0.42)
    if t:
        a0, a1 = (math.pi * 0.72, math.pi * 1.9) if t > 0 else (
            math.pi * 0.28, -math.pi * 0.9)
        outer = _arcp(hx, hy, R, a0, a1, 18, bump, k)
        inner = [(hx + t * r * 0.62, hy - r * 0.62),
                 (hx + t * r * 0.15, line_y + r * 0.05),
                 (hx - t * r * 0.30, hy + r * 0.02)]
    else:
        outer = _arcp(hx, hy, R, math.pi * 0.96, math.pi * 2.04, 20, bump, k)
        part = r * (0.25 if style == 'side' else 0.0)
        inner = [(hx + r * 0.92, hy - r * 0.02), (hx + r * 0.55, line_y),
                 (hx + part, line_y - r * (0.12 if part else 0.0)),
                 (hx - r * 0.55, line_y), (hx - r * 0.92, hy - r * 0.02)]
    poly(front, outer + inner)
    return back, front


def _beard(kind, tone, hx, hy, r, turn):
    """Facial hair strokes (unit px) over the lower face."""
    st = []
    if not kind:
        return st
    t = turn
    fx = hx + t * r * 0.34
    my = hy + r * 0.46

    def poly(pts):
        st.append((pts + [pts[0]], tone, 0.75, 'solid'))

    def moustache():
        poly([(fx - r * 0.28, my - r * 0.02), (fx - r * 0.14, my - r * 0.14),
              (fx, my - r * 0.10), (fx + r * 0.14, my - r * 0.14),
              (fx + r * 0.28, my - r * 0.02), (fx, my - r * 0.04)])
    if kind == 'full':
        a0, a1 = ((-math.pi * 0.02, math.pi * 0.72) if t > 0 else
                  (math.pi * 0.28, math.pi * 1.02) if t < 0 else
                  (math.pi * 0.02, math.pi * 0.98))
        outer = _arcp(hx, hy + r * 0.06, r * 1.06, a0, a1, 16, 0.04, 6)
        inner = [(fx + math.cos(a) * r * 0.62, hy + r * 0.22
                  + math.sin(a) * r * 0.42)
                 for a in [a1 + (a0 - a1) * k / 12 for k in range(13)]]
        poly(outer + inner)
        moustache()
    elif kind == 'goatee':
        poly(_arcp(fx, my + r * 0.22, r * 0.12, 0, 2 * math.pi, 12))
        moustache()
    elif kind == 'mustache':
        moustache()
    elif kind == 'stubble':
        for i in range(9):
            a = math.pi * (0.18 + 0.64 * i / 8)
            x, y = hx + math.cos(a) * r * 0.78, hy + math.sin(a) * r * 0.78
            if t and (x - hx) * t < -r * 0.25:
                continue
            st.append((_circle(x, y, r * 0.035, n=6), tone, 0.5, 'solid'))
    return st


def _lashes(hx, hy, r, turn):
    """Eyelash ticks at the outer corner of each eye."""
    hx = hx + turn * r * 0.34
    ex, ey = r * (0.25 if turn else 0.36), hy - r * 0.02
    out = []
    for s in (-1, 1):
        x = hx + s * ex
        out.append(([(x + s * r * 0.08, ey - r * 0.08),
                     (x + s * r * 0.20, ey - r * 0.19)], 'ink', 0.8, False))
    return out


def _skirt(tone, byy, bw, hem):
    """A-line skirt from the waist to `hem` (unit y)."""
    top = byy - 0.02
    pts = [_p(-bw * 1.15, top), _p(-bw * 1.9, hem), _p(bw * 1.9, hem),
           _p(bw * 1.15, top)]
    return [(pts + [pts[0]], tone, 0.8, 'solid')]


def _groom(fit, hx, hy, r, turn):
    """Look strokes for a head -> (behind_head, over_face)."""
    back, front = _hair(fit.get('hair'), fit.get('hair_tone') or '#2E2420',
                        hx, hy, r, turn, bool(fit.get('hat')))
    over = _beard(fit.get('beard'), fit.get('hair_tone') or '#2E2420',
                  hx, hy, r, turn)
    if fit.get('sex') == 'f':
        over += _lashes(hx, hy, r, turn)
    return back, over + front


def _torso_extra(kind, ty, byy, tw, bw, d):
    """Costume detail drawn over the shirt (unit px)."""
    st = []
    h = H

    def poly(pts, col):
        st.append((pts + [pts[0]], col, 0.7, 'solid'))

    def line(pts, col='ink', w=0.6):
        st.append((pts, col, w, False))

    cx = d * 0.018 * h if d else 0.0
    if kind == 'tie':
        poly([(cx - 0.050 * h, ty * h), (cx, (ty + 0.085) * h),
              (cx + 0.050 * h, ty * h)], '#F4F1EA')
        poly([(cx - 0.013 * h, (ty + 0.012) * h), (cx + 0.013 * h, (ty + 0.012) * h),
              (cx + 0.022 * h, (ty + 0.16) * h), (cx, (ty + 0.195) * h),
              (cx - 0.022 * h, (ty + 0.16) * h)], '#B5403A')
    elif kind == 'robe':
        poly([(cx - 0.045 * h, ty * h), (cx, (ty + 0.06) * h),
              (cx + 0.045 * h, ty * h)], '#F4F1EA')
        line([(cx, (ty + 0.06) * h), (cx, (byy + 0.03) * h)], 'pale', 0.7)
    elif kind in ('coat', 'scrubs'):
        line([(cx - 0.075 * h, ty * h), (cx, (ty + 0.12) * h)])
        line([(cx + 0.075 * h, ty * h), (cx, (ty + 0.12) * h)])
        if kind == 'coat':
            line([(cx, (ty + 0.12) * h), (cx, (byy + 0.035) * h)])
            poly([(cx + d * 0.035 * h + 0.012 * h, (ty + 0.15) * h),
                  (cx + d * 0.035 * h + 0.052 * h, (ty + 0.15) * h),
                  (cx + d * 0.035 * h + 0.052 * h, (ty + 0.19) * h),
                  (cx + d * 0.035 * h + 0.012 * h, (ty + 0.19) * h)],
                 '#8FB3E3')
    elif kind in ('apron', 'apron_brown'):
        col = '#F4F1EA' if kind == 'apron' else '#A57A55'
        poly([(cx - 0.055 * h, (ty + 0.08) * h), (cx + 0.055 * h, (ty + 0.08) * h),
              (cx + 0.080 * h, (byy + 0.07) * h), (cx - 0.080 * h, (byy + 0.07) * h)],
             col)
        line([(cx - 0.055 * h, (ty + 0.08) * h), (cx - 0.03 * h, ty * h)])
        line([(cx + 0.055 * h, (ty + 0.08) * h), (cx + 0.03 * h, ty * h)])
    elif kind == 'overalls':
        poly([(cx - 0.060 * h, (ty + 0.10) * h), (cx + 0.060 * h, (ty + 0.10) * h),
              (cx + 0.070 * h, (byy + 0.05) * h), (cx - 0.070 * h, (byy + 0.05) * h)],
             '#6F8FBF')
        for sx in (-1, 1):
            line([(cx + sx * 0.055 * h, (ty + 0.10) * h),
                  (cx + sx * 0.085 * h, (ty + 0.01) * h)], '#3B5C8C', 1.2)
            st.append((_circle(cx + sx * 0.045 * h, (ty + 0.12) * h,
                               0.008 * h, n=8), '#E5B83A', 0.5, 'solid'))
    elif kind in ('stripes', 'vest', 'slicker'):
        col = '#E9E4D6' if kind == 'stripes' else '#E5B83A'
        if kind == 'slicker':
            line([(cx, ty * h), (cx, (byy + 0.035) * h)])
        else:
            for k, fy in enumerate((0.12, 0.20)):
                w_ = tw - (tw - bw) * (fy / (byy - ty)) ** 1.25 - 0.01
                line([(-w_ * h, (ty + fy) * h), (w_ * h, (ty + fy) * h)],
                     col, 2.2)
    elif kind == 'jersey':
        w_ = tw - 0.012
        line([(-w_ * h, (ty + 0.05) * h), (w_ * h, (ty + 0.05) * h)],
             '#F4F1EA', 2.0)
        num = [(cx - 0.015 * h, (ty + 0.10) * h), (cx + 0.02 * h, (ty + 0.10) * h),
               (cx - 0.005 * h, (ty + 0.19) * h)]
        line(num, '#F4F1EA', 1.4)
    elif kind == 'jacket':
        for sx in (-1, 1):
            poly([(cx + sx * 0.012 * h, (ty + 0.01) * h),
                  (cx + sx * 0.070 * h, ty * h),
                  (cx + sx * 0.060 * h, (byy + 0.03) * h),
                  (cx + sx * 0.020 * h, (byy + 0.03) * h)], '#46505A')
    elif kind == 'stripes_dark':
        for fy in (0.07, 0.14, 0.21):
            w_ = tw - (tw - bw) * (fy / (byy - ty)) ** 1.25 - 0.01
            line([(-w_ * h, (ty + fy) * h), (w_ * h, (ty + fy) * h)],
                 '#E9E4D6', 1.8)
    elif kind == 'badge':
        pts = [(cx + d * 0.04 * h + math.cos(a) * 0.018 * h,
                (ty + 0.07) * h + math.sin(a) * 0.018 * h)
               for a in [k * math.pi * 2 / 5 - math.pi / 2 for k in range(5)]]
        poly(pts, '#E5B83A')
    return st


def _marks(kinds, hx, hy, r, top_y):
    """Expression marks around the head, in unit px."""
    st = []
    ink = 'ink'
    for m in kinds:
        if m == 'bubble':
            bx, by = hx + r * 1.55, hy - r * 1.55
            st.append((_circle(bx, by, r * 0.80, r * 0.58, 22), ink, 0.7,
                       False))
            for dx, dy, rr in ((0.62, -0.42, 0.12), (0.88, -0.78, 0.18)):
                st.append((_circle(hx + r * dx, hy + r * dy, r * rr, n=10),
                           ink, 0.6, False))
        elif m == 'exclaim':
            for i, (dx, ang) in enumerate(((1.15, -0.30), (1.55, 0.0))):
                x0, y0 = hx + r * dx, hy - r * 1.25
                ln = r * (0.62 if i == 0 else 0.72)
                x1 = x0 + math.sin(ang) * ln
                y1 = y0 + math.cos(ang) * ln
                st.append(([(x0, y0), (x1, y1)], ink, 1.05, False))
                st.append((_circle(x1 + math.sin(ang) * r * 0.26,
                                   y1 + r * 0.26, r * 0.07, n=8),
                           ink, 0.8, 'solid'))
        elif m == 'burst':
            for a in (-2.6, -2.1, -1.57, -1.05, -0.55):
                c, s = math.cos(a), math.sin(a)
                st.append(([(hx + c * r * 1.35, top_y * 0 + hy + s * r * 1.35),
                            (hx + c * r * 1.75, hy + s * r * 1.75)],
                           ink, 0.8, False))
        elif m in ('sweat', 'drop'):
            sx = hx + r * (1.45 if m == 'sweat' else 0.55)
            sy = hy - r * (0.35 if m == 'sweat' else -0.15)
            drop = [(sx, sy - r * 0.30)]
            drop += _circle(sx, sy, r * 0.14, r * 0.15, 10,
                            -0.1 * math.pi, 1.1 * math.pi)
            drop.append(drop[0])
            st.append((drop, 'a_blue', 0.6, 'solid'))
            st.append((drop, ink, 0.55, False))
            if m == 'sweat':
                sx2 = hx - r * 1.45
                d2 = [(sx2, sy - r * 0.10)] + _circle(
                    sx2, sy + r * 0.18, r * 0.11, r * 0.12, 10,
                    -0.1 * math.pi, 1.1 * math.pi)
                d2.append(d2[0])
                st.append((d2, 'a_blue', 0.6, 'solid'))
                st.append((d2, ink, 0.55, False))
        elif m == 'shake':
            for s in (-1, 1):
                for k in (0, 1):
                    x = hx + s * r * (1.45 + k * 0.28)
                    st.append(([(x, hy - r * 0.35), (x + s * r * 0.06, hy),
                                (x, hy + r * 0.35)], ink, 0.6, False))
        elif m == 'question':
            qx, qy = hx + r * 1.35, hy - r * 1.35
            q = _circle(qx, qy, r * 0.30, r * 0.30, 12, -math.pi, 0.45 * math.pi)
            q += [(qx, qy + r * 0.52)]
            st.append((q, ink, 1.0, False))
            st.append((_circle(qx, qy + r * 0.82, r * 0.07, n=8), ink, 0.8,
                       'solid'))
        elif m == 'gloom':
            for dx in (-0.55, 0.0, 0.55):
                x = hx + r * dx
                st.append(([(x, hy - r * 1.30), (x + r * 0.05, hy - r * 1.62)],
                           'pale', 0.7, False))
        elif m == 'tears':
            for s in (-1, 1):
                x = hx + s * r * 0.30
                st.append(([(x, hy + r * 0.08), (x - s * r * 0.04,
                            hy + r * 0.40), (x, hy + r * 0.62)],
                           'a_blue', 1.1, False))
        elif m == 'laughlines':
            for s in (-1, 1):
                for k in (0, 1):
                    a = -0.6 + k * 0.5
                    c, sn = s * math.cos(a), math.sin(a)
                    st.append(([(hx + c * r * 1.30, hy + sn * r * 1.30),
                                (hx + c * r * 1.62, hy + sn * r * 1.62)],
                               ink, 0.8, False))
        elif m == 'heart':
            cx, cy, k = hx + r * 1.45, hy - r * 1.35, r * 0.30
            pts = [(cx + k * 16 * math.sin(t) ** 3 / 16,
                    cy - k * (13 * math.cos(t) - 5 * math.cos(2 * t)
                              - 2 * math.cos(3 * t) - math.cos(4 * t)) / 16)
                   for t in [2 * math.pi * i / 24 for i in range(25)]]
            st.append((pts, 'a_red', 0.7, 'solid'))
            st.append((pts, ink, 0.6, False))
        elif m == 'zzz':
            for i in range(3):
                zx, zy = hx + r * (1.1 + 0.45 * i), hy - r * (0.9 + 0.5 * i)
                zk = r * (0.16 + 0.05 * i)
                st.append(([(zx - zk, zy - zk), (zx + zk, zy - zk),
                            (zx - zk, zy + zk), (zx + zk, zy + zk)],
                           ink, 0.8, False))
        elif m == 'steam':
            for s in (-1, 1):
                x = hx + s * r * 1.05
                st.append(([(x, hy - r * 0.85), (x + s * r * 0.15, hy - r * 1.1),
                            (x, hy - r * 1.35), (x + s * r * 0.15, hy - r * 1.6)],
                           ink, 0.7, False))
    return st


def _arm_pose(emotion, action, stance):
    pose_n = ACTIONS.get(str(action or '').lower()) or (
        'climb' if stance == 'climb' else
        EMOTIONS.get(emotion, EMOTIONS['neutral'])[0])
    return pose_n


def hand_uv(emotion='neutral', flip=False, action='', outfit=None,
            engaged=None, stance='stand', seat=True):
    """Right (leading) hand position as a fraction (u, v) of the figure's
    ink bounds — where a held prop is anchored."""
    body, _m, _hb = figure(emotion, flip, action, outfit=outfit,
                           engaged=engaged, stance=stance, seat=seat)
    pz = POSES[_arm_pose(emotion, action, stance)]
    sgn = -1 if flip else 1
    hx, hy = _p(sgn * pz['r'][1][0], pz['r'][1][1] + pz.get('sh', 0.0)
                + STANCES.get(stance, 0.0))
    xs = [q[0] for st in body for q in st[0]]
    ys = [q[1] for st in body for q in st[0]]
    return ((hx - min(xs)) / max(1e-6, max(xs) - min(xs)),
            (hy - min(ys)) / max(1e-6, max(ys) - min(ys)))


def figure(emotion='neutral', flip=False, action='', shirt=None,
           outfit=None, engaged=None, stance='stand', seat=True):
    """-> (body_strokes, mark_strokes, head_box) in unit px (feet at 0).
    `action` (hold/point/offer/reach/drink/read...) swaps the arm pose; an
    engaged figure turns three-quarter toward its task (facing -x when
    flipped); `stance` (stand/walk/sit/kneel/climb) sets the legs and how
    low the body sits — a seated figure brings its own stool unless
    `seat` is False (it sits on a drawn seat); `outfit` (see outfit_for)
    dresses it for its role."""
    _p0, face_n, mark_n = EMOTIONS.get(emotion, EMOTIONS['neutral'])
    act_n = str(action or '').lower()
    stance = stance if stance in STANCES else 'stand'
    pose_n = _arm_pose(emotion, act_n, stance)
    fit = dict(outfit or {})
    shirt = fit.get('shirt') or shirt
    if engaged is None:
        engaged = act_n in ENGAGED
    sgn = -1 if flip else 1
    turn = sgn if (engaged or stance != 'stand') else 0
    pz = POSES[pose_n]
    drop = STANCES[stance]
    hdx, hdy = pz.get('head', (0.0, 0.0))
    hdx, hdy = sgn * hdx if turn else hdx, hdy + drop
    if stance == 'walk':
        hdx += sgn * 0.015
    shd = pz.get('sh', 0.0) + drop
    sh_y = SH_Y + shd
    hx, hy = _p(hdx, HEAD_CY + hdy)
    r = HEAD_R * H
    body = []
    fill, ink = FILL, 'ink'
    # head first — the artist inks the face before the body
    head = _circle(hx, hy, r, n=30)
    g_back, g_over = _groom(fit, hx, hy, r, turn)
    body += g_back
    body.append((head, fill, 0.95, 'solid'))
    body += _face(face_n, hx, hy, r, turn, bool(fit.get('glasses')))
    body += g_over
    body += _hat(fit.get('hat'), hx, hy, r, sgn)
    # pear torso (narrower side-on)
    tw, bw = (0.108, 0.058) if turn else (0.125, 0.062)
    far = []
    if turn:
        # far arm sits behind the torso: joins the near hand on the task
        # for two-handed poses, otherwise hangs at the back
        el, hd = pz['r'] if pose_n in _TWO_HANDED else (
            (-0.04, -0.55), (-0.02, -0.42))
        if pose_n in _TWO_HANDED:
            el, hd = (el[0] - 0.09, el[1] + 0.03), (hd[0] - 0.05,
                                                     hd[1] + 0.035)
        shp = _p(-sgn * tw * 0.35, sh_y + 0.01)
        elp = _p(sgn * el[0], el[1] + shd)
        hdp = _p(sgn * hd[0], hd[1] + shd)
        far = [([shp, elp, hdp], ink, 0.85, False),
               (_circle(hdp[0], hdp[1], 0.028 * H, 0.034 * H, 12),
                SHADE, 0.8, 'solid')]
    ty, byy = sh_y + 0.005, HIP_Y + 0.012 + drop
    if stance == 'sit' and seat:
        body += _seat(sgn, HIP_Y + 0.03 + drop)
    # simpler robust outline: left edge down, bottom curve, right edge up,
    # shoulder arc across
    left = [_p(-tw + (tw - bw) * (i / 8) ** 1.25, ty + (byy - ty) * i / 8)
            for i in range(9)]
    bottom = [(math.cos(a) * bw * H, byy * H + math.sin(a) * bw * H * 0.7)
              for a in [math.pi - math.pi * k / 10 for k in range(11)]]
    rgt = [(-x, y) for x, y in reversed(left)]
    shoulder = [(math.cos(a) * tw * H, ty * H - math.sin(a) * tw * H * 0.28)
                for a in [math.pi * k / 10 for k in range(11)]]
    torso_poly = left + bottom[1:] + rgt[1:] + shoulder[1:]
    torso_poly.append(torso_poly[0])
    body += far
    body.append((torso_poly, shirt or fill, 1.0, 'solid'))
    body += _torso_extra(fit.get('torso'), ty, byy, tw, bw, turn)
    if fit.get('skirt') and not fit.get('torso') and stance in (
            'stand', 'walk'):
        body += _skirt(shirt or fill, byy, bw, -0.19)
    # legs (side-on: a short stance, both shoes toward the task)
    legs = pz.get('leg', _IDLE_LEG)
    posed = _stance_legs(stance, sgn)
    for s in (-1, 1):
        if posed:
            hp_, kn_, ft_ = posed[0 if s < 0 else 1]
            hip, kn, ft = _p(*hp_), _p(*kn_), _p(*ft_)
            ds = sgn
        elif turn:
            k = s * sgn
            hip = _p(k * 0.025, HIP_Y + 0.03)
            kn = _p(k * 0.045 + sgn * 0.015, -0.20)
            ft = _p(k * 0.065 + sgn * 0.02, 0.0)
            ds = sgn
        else:
            hip = _p(s * 0.045, HIP_Y + 0.03)
            kn = _p(s * legs[0][0], legs[0][1])
            ft = _p(s * legs[1][0], legs[1][1])
            ds = s
        body.append(([hip, kn, ft], ink, 0.85, False))
        shoe = [(ft[0] - ds * 0.012 * H, ft[1] - 0.048 * H),
                (ft[0] + ds * 0.05 * H, ft[1]),
                (ft[0] - ds * 0.03 * H, ft[1]),
                (ft[0] - ds * 0.012 * H, ft[1] - 0.048 * H)]
        body.append((shoe, SHADE if s < 0 else fill, 0.8, 'solid'))
    # arms
    for side, s in (('l', -1), ('r', 1)):
        if turn and side == 'l':
            continue
        el, hd = pz[side]
        s2 = s * sgn
        shp = _p(s2 * (tw - 0.012), sh_y + 0.006)
        elp = _p(s2 * el[0], el[1] + shd)
        hdp = _p(s2 * hd[0], hd[1] + shd)
        body.append(([shp, elp, hdp], ink, 0.85, False))
        body.append((_circle(hdp[0], hdp[1], 0.028 * H, 0.034 * H, 12),
                     SHADE if s2 < 0 else fill, 0.8, 'solid'))
    inked = []
    for st in body:
        inked.append(st)
        if st[3] == 'solid' and st[1] != 'ink':
            inked.append((st[0], 'ink', 0.62, False))
    body = inked
    top_y = min(q[1] for st in body for q in st[0])
    marks = _marks(mark_n, hx, hy, r, top_y)
    if flip:
        marks = [([(2 * hx - x, y) for x, y in pts], c, w, f)
                 for pts, c, w, f in marks]
    return body, marks, (hx - r, hy - r, hx + r, hy + r)


ARM = (0.145, 0.150)
LEG = (0.215, 0.215)


def _ik(base, tgt, lens, pref):
    """Two-bone IK in unit coords: -> (joint, end). The joint takes the
    side of the base->end line closest to `pref` (a unit direction);
    out-of-reach targets are met at full stretch."""
    a, b = lens
    dx, dy = tgt[0] - base[0], tgt[1] - base[1]
    d = math.hypot(dx, dy)
    d_ = min(max(d, abs(a - b) + 1e-4), a + b - 1e-4)
    ux, uy = (dx / d, dy / d) if d > 1e-9 else (0.0, 1.0)
    end = (base[0] + ux * d_, base[1] + uy * d_)
    along = (a * a - b * b + d_ * d_) / (2 * d_)
    off = math.sqrt(max(0.0, a * a - along * along))
    mx, my = base[0] + ux * along, base[1] + uy * along
    c1 = (mx - uy * off, my + ux * off)
    c2 = (mx + uy * off, my - ux * off)

    def score(c):
        return (c[0] - mx) * pref[0] + (c[1] - my) * pref[1]
    return (c1 if score(c1) >= score(c2) else c2), end


def posed(pose, emotion='neutral', outfit=None, shirt=None):
    """A jointed figure placed by contact targets, facing +x.

    `pose` (unit coords, y down, ground 0): hip (x, y); lean (radians,
    + tips the torso forward); hands {'n','f'} and feet {'n','f'}
    targets for the near/far limbs; optional knee/elbow bend preferences
    (unit directions), 'toe' (shoe direction), 'head' (dx, dy) nod.
    -> (body_strokes, mark_strokes, anchors) in unit px; anchors carry
    hand_n/hand_f/foot_n/foot_f/mouth/eye/head/hip points."""
    _p0, face_n, mark_n = EMOTIONS.get(emotion, EMOTIONS['neutral'])
    fit = dict(outfit or {})
    shirt = fit.get('shirt') or shirt
    hip = pose['hip']
    lean = float(pose.get('lean', 0.0))
    ca, sa = math.cos(lean), math.sin(lean)
    hip0 = HIP_Y + 0.03

    def xf(q):
        # q in unit px of the upright figure -> unit px of the pose
        x, y = q[0] / H, q[1] / H - hip0
        return ((hip[0] + x * ca - y * sa) * H,
                (hip[1] + x * sa + y * ca) * H)

    def up(x, y):
        return xf((x * H, y * H))

    def unit(q):
        return (q[0] / H, q[1] / H)

    hdx, hdy = pose.get('head', (0.0, 0.0))
    hx0, hy0 = _p(0.012 + hdx, HEAD_CY + hdy)
    r = HEAD_R * H
    tw, bw = 0.108, 0.058
    ty, byy = SH_Y + 0.005, HIP_Y + 0.012
    left = [_p(-tw + (tw - bw) * (i / 8) ** 1.25, ty + (byy - ty) * i / 8)
            for i in range(9)]
    bottom = [(math.cos(a) * bw * H, byy * H + math.sin(a) * bw * H * 0.7)
              for a in [math.pi - math.pi * k / 10 for k in range(11)]]
    rgt = [(-x, y) for x, y in reversed(left)]
    shoulder = [(math.cos(a) * tw * H, ty * H - math.sin(a) * tw * H * 0.28)
                for a in [math.pi * k / 10 for k in range(11)]]
    torso = left + bottom[1:] + rgt[1:] + shoulder[1:]
    torso.append(torso[0])
    core = [(torso, shirt or FILL, 1.0, 'solid')]
    core += _torso_extra(fit.get('torso'), ty, byy, tw, bw, 1)
    g_back, g_over = _groom(fit, hx0, hy0, r, 1)
    head = g_back + [(_circle(hx0, hy0, r, n=30), FILL, 0.95, 'solid')]
    head += _face(face_n, hx0, hy0, r, 1, bool(fit.get('glasses')))
    head += g_over
    head += _hat(fit.get('hat'), hx0, hy0, r, 1)
    core = [([xf(q) for q in pts], c, w, f) for pts, c, w, f in core]
    head = [([xf(q) for q in pts], c, w, f) for pts, c, w, f in head]
    sh = {'n': unit(up(0.03, SH_Y + 0.02)), 'f': unit(up(-0.02, SH_Y + 0.02))}
    hp = {'n': unit(up(0.012, hip0)), 'f': unit(up(-0.012, hip0))}
    toe = pose.get('toe', (1.0, 0.0))
    limbs = {}
    for side in ('n', 'f'):
        el, hd = _ik(sh[side], pose['hands'][side], ARM,
                     pose.get('elbow', (-0.35, 0.94)))
        kn, ft = _ik(hp[side], pose['feet'][side], LEG,
                     pose.get('knee', (0.94, -0.2)))
        limbs[side] = (el, hd, kn, ft)

    def limb(side, col):
        el, hd, kn, ft = limbs[side]
        st = [([_p(*hp[side]), _p(*kn), _p(*ft)], 'ink', 0.85, False)]
        fx, fy = _p(*ft)
        tx, ty_ = toe
        nx, ny = -ty_, tx
        shoe = [(fx - tx * 0.012 * H - nx * 0.048 * H,
                 fy - ty_ * 0.012 * H - ny * 0.048 * H),
                (fx + tx * 0.05 * H, fy + ty_ * 0.05 * H),
                (fx - tx * 0.03 * H, fy - ty_ * 0.03 * H)]
        shoe.append(shoe[0])
        st.append((shoe, col, 0.8, 'solid'))
        st.append(([_p(*sh[side]), _p(*el), _p(*hd)], 'ink', 0.85, False))
        hx, hy = _p(*hd)
        st.append((_circle(hx, hy, 0.028 * H, 0.034 * H, 12), col, 0.8,
                   'solid'))
        return st

    body = limb('f', SHADE) + core + head + limb('n', FILL)
    inked = []
    for st in body:
        inked.append(st)
        if st[3] == 'solid' and st[1] != 'ink':
            inked.append((st[0], 'ink', 0.62, False))
    hx, hy = xf((hx0, hy0))
    top_y = min(q[1] for st in inked for q in st[0])
    marks = _marks(mark_n, hx, hy, r, top_y)
    anchors = {'hand_n': _p(*limbs['n'][1]), 'hand_f': _p(*limbs['f'][1]),
               'foot_n': _p(*limbs['n'][3]), 'foot_f': _p(*limbs['f'][3]),
               'mouth': xf((hx0 + r * 0.55, hy0 + r * 0.45)),
               'eye': xf((hx0 + r * 0.6, hy0 - r * 0.05)),
               'head': (hx, hy), 'head_r': r, 'hip': _p(*hip),
               'chest': xf((0.05 * H, (SH_Y + 0.10) * H))}
    return inked, marks, anchors


# every literal tone the cast draws with (the renderer registers these)
with open(__file__, encoding='utf-8') as _f:
    TONES = tuple(sorted(set(re.findall(r"'(#[0-9A-Fa-f]{6})'", _f.read()))))
