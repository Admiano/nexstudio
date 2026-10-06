"""Activity depiction: a narrated verb becomes a whole picture.

A verb resolves (through WordNet ancestry, refined by what it acts on)
to a motor schema. Each schema places a jointed figure (sb_cast.posed)
by contact targets — hands on the wheel, feet on the slope, hips on the
saddle — inside apparatus drawn around it (car body, mountain, table,
water ...), with the narrated object fitted into the schema's slot.

Unit space: figure height 1 (sb_cast.H px), ground y=0, the actor faces
+x; `compose` mirrors for flip. Strokes: (points, color, width, fill).
"""
from __future__ import annotations

import math
import re

import sb_cast

try:
    from nltk.corpus import wordnet as _wn
    _wn.synsets('dog')
except Exception:  # pragma: no cover - WordNet optional
    _wn = None

H = sb_cast.H

# verb synset (anywhere on a hypernym path) -> schema; most specific wins
_VERB_ANCHORS = (
    ('drive.v.01', 'drive'), ('steer.v.01', 'drive'), ('fly.v.03', 'drive'),
    ('operate.v.03', 'drive'),
    ('bicycle.v.01', 'ride'), ('ride.v.01', 'ride'), ('ride.v.02', 'ride'),
    ('boat.v.01', 'row'), ('sail.v.01', 'drive'),
    ('climb.v.01', 'climb'), ('ascend.v.01', 'climb'),
    ('swim.v.01', 'swim'), ('dive.v.01', 'swim'),
    ('glide.v.01', 'glide'), ('ski.v.01', 'glide'),
    ('crawl.v.01', 'crawl'),
    ('run.v.01', 'run'), ('travel_rapidly.v.01', 'run'),
    ('trek.v.01', 'hike'), ('walk.v.01', 'walk'),
    ('jump.v.01', 'jump'), ('dance.v.01', 'dance'),
    ('push.v.01', 'push'), ('pull.v.01', 'pull'), ('drag.v.01', 'pull'),
    ('raise.v.02', 'lift'), ('load.v.01', 'lift'),
    ('kick.v.01', 'kick'), ('propel.v.01', 'throw'),
    ('drink.v.01', 'drink'), ('eat.v.01', 'eat'), ('consume.v.02', 'eat'),
    ('stir.v.01', 'cook'), ('cook.v.01', 'cook'), ('cook.v.02', 'cook'),
    ('heat.v.01', 'cook'),
    ('cut.v.01', 'cut'), ('strike.v.01', 'strike'), ('nail.v.01', 'strike'),
    ('repair.v.01', 'fix'), ('construct.v.01', 'fix'),
    ('assemble.v.01', 'fix'),
    ('paint.v.01', 'paint'), ('paint.v.02', 'paint'),
    ('type.v.01', 'type'), ('write.v.01', 'write'), ('write.v.02', 'write'),
    ('read.v.01', 'read'),
    ('sleep.v.01', 'lie'), ('lie.v.01', 'lie'), ('lie_down.v.01', 'lie'),
    ('recumb.v.01', 'lie'),
    ('sit.v.01', 'sit'), ('sit_down.v.01', 'sit'), ('kneel.v.01', 'kneel'),
    ('crouch.v.01', 'kneel'), ('squat.v.01', 'kneel'),
    ('dig.v.01', 'dig'), ('brush.v.04', 'dig'), ('wipe_up.v.01', 'dig'),
    ('plant.v.01', 'plant'), ('sow.v.01', 'plant'),
    ('water.v.01', 'pour'), ('pour.v.01', 'pour'), ('spray.v.01', 'pour'),
    ('rub.v.01', 'wipe'), ('clean.v.01', 'wipe'), ('wash.v.02', 'wipe'),
    ('embrace.v.02', 'give'), ('give.v.01', 'give'), ('pass.v.05', 'give'),
    ('feed.v.01', 'give'), ('feed.v.02', 'give'), ('transfer.v.02', 'give'),
    ('bring.v.01', 'carry'), ('transport.v.02', 'carry'),
    ('carry.v.01', 'carry'),
    ('fish.v.01', 'fish'), ('photograph.v.01', 'photo'),
    ('sing.v.01', 'talk'), ('talk.v.01', 'talk'), ('talk.v.02', 'talk'),
    ('communicate.v.02', 'talk'), ('telephone.v.01', 'phone'),
    ('teach.v.01', 'point'), ('indicate.v.02', 'point'),
    ('show.v.01', 'point'), ('point.v.01', 'point'),
    ('look.v.01', 'look'), ('watch.v.01', 'look'), ('perceive.v.01', 'look'),
    ('examine.v.02', 'look'), ('analyze.v.01', 'look'),
    ('check.v.01', 'look'), ('inspect.v.01', 'look'),
    ('open.v.01', 'open'), ('close.v.01', 'open'),
    ('sew.v.01', 'craft'), ('knit.v.01', 'craft'), ('weave.v.01', 'craft'),
    ('fasten.v.01', 'craft'),
    ('reap.v.01', 'pick'), ('gather.v.01', 'pick'), ('pluck.v.01', 'pick'),
    ('hold.v.02', 'hold'), ('keep.v.01', 'hold'), ('grasp.v.01', 'hold'),
    ('seize.v.01', 'hold'), ('catch.v.04', 'hold'), ('take.v.04', 'hold'),
)
_VERB_MAP = dict(_VERB_ANCHORS)

# lemma senses WordNet ranks badly for narration
_LEMMA = {'jog': 'run', 'sprint': 'run', 'dash': 'run', 'race': 'run',
          'hike': 'hike', 'stroll': 'walk', 'march': 'walk', 'wander': 'walk',
          'scale': 'climb', 'study': 'read', 'browse': 'read',
          'serve': 'give', 'deliver': 'give', 'hand': 'give', 'offer': 'give',
          'call': 'phone', 'text': 'phone', 'dial': 'phone',
          'pick': 'pick', 'harvest': 'pick', 'hold': 'hold', 'grab': 'hold',
          'catch': 'hold', 'carry': 'carry', 'haul': 'pull', 'tow': 'pull',
          'lug': 'carry', 'bring': 'carry', 'fetch': 'carry',
          'play': 'play', 'strum': 'play', 'sing': 'talk', 'shout': 'talk',
          'yell': 'talk', 'lecture': 'point', 'present': 'point',
          'explain': 'point', 'mop': 'dig', 'sweep': 'dig', 'rake': 'dig',
          'hoe': 'dig', 'shovel': 'dig', 'vacuum': 'dig', 'scrub': 'wipe',
          'wash': 'wipe', 'wipe': 'wipe', 'polish': 'wipe', 'milk': 'kneel',
          'weed': 'plant', 'garden': 'plant', 'pack': 'lift', 'stack': 'lift',
          'unload': 'lift', 'wrap': 'craft', 'tie': 'craft', 'knead': 'cook',
          'bake': 'cook', 'fry': 'cook', 'boil': 'cook', 'grill': 'cook',
          'chop': 'cut', 'slice': 'cut', 'carve': 'cut', 'saw': 'cut',
          'hammer': 'strike', 'knock': 'strike', 'forge': 'strike',
          'pound': 'strike', 'fix': 'fix', 'mend': 'fix', 'build': 'fix',
          'photograph': 'photo', 'film': 'photo', 'draw': 'write',
          'sketch': 'write', 'sign': 'write', 'jot': 'write',
          'skate': 'glide', 'surf': 'glide', 'ski': 'glide',
          'snowboard': 'glide', 'sail': 'drive', 'pilot': 'drive',
          'steer': 'drive', 'drive': 'drive', 'commute': 'drive',
          'paddle': 'row', 'row': 'row', 'kayak': 'row', 'canoe': 'row',
          'cycle': 'ride', 'bike': 'ride', 'pedal': 'ride', 'nap': 'lie',
          'rest': 'sit', 'relax': 'sit', 'type': 'type', 'eat': 'eat',
          'munch': 'eat', 'chew': 'eat', 'bite': 'eat', 'taste': 'eat',
          'sip': 'drink', 'gulp': 'drink', 'drink': 'drink',
          'observe': 'look', 'watch': 'look', 'inspect': 'look',
          'examine': 'look', 'check': 'look', 'measure': 'look',
          'water': 'pour', 'spray': 'pour', 'pour': 'pour', 'fill': 'pour',
          # --- domain vocab: tech/finance/health/education narration ---
          'tokenize': 'craft', 'mint': 'craft', 'generate': 'craft',
          'choose': 'pick', 'select': 'pick', 'adopt': 'pick',
          'encrypt': 'craft', 'compile': 'fix', 'automate': 'fix',
          'integrate': 'fix', 'assemble': 'fix', 'configure': 'fix',
          'maintain': 'fix', 'train': 'point', 'tutor': 'point',
          'lecture': 'point', 'mentor': 'point', 'present': 'point',
          'demonstrate': 'point', 'illustrate': 'point',
          'pitch': 'point', 'prompt': 'type', 'query': 'type',
          'search': 'look', 'scan': 'look', 'audit': 'look',
          'verify': 'look', 'monitor': 'look', 'screen': 'look',
          'diagnose': 'look', 'analyze': 'look', 'forecast': 'look',
          'review': 'read', 'study': 'read', 'research': 'look',
          'browse': 'read', 'survey': 'look', 'read': 'read',
          'prescribe': 'write', 'record': 'write', 'register': 'write',
          'enroll': 'write', 'sign': 'write', 'grade': 'write',
          'assess': 'write', 'code': 'type', 'debug': 'type',
          'deploy': 'carry', 'ship': 'carry', 'deliver': 'carry',
          'transport': 'carry', 'migrate': 'walk', 'scale': 'climb',
          'tokenize': 'craft', 'exchange': 'give', 'swap': 'give',
          'trade': 'give', 'transfer': 'give', 'send': 'give',
          'distribute': 'give', 'reward': 'give', 'pay': 'give',
          'refund': 'give', 'lend': 'give', 'borrow': 'give',
          'fund': 'give', 'invest': 'give', 'donate': 'give',
          'administer': 'give', 'inject': 'give', 'vaccinate': 'give',
          'immunize': 'give', 'dose': 'give', 'dispense': 'give',
          'sell': 'give', 'buy': 'give', 'purchase': 'give',
          'store': 'hold', 'stake': 'hold', 'secure': 'hold',
          'vault': 'hold', 'hodl': 'hold', 'custody': 'hold',
          'backup': 'hold', 'retain': 'hold', 'protect': 'hold',
          'guard': 'hold', 'safeguard': 'hold',
          'mine': 'dig', 'excavate': 'dig', 'drill': 'dig',
          'unlock': 'open', 'lock': 'hold',
          'release': 'give', 'launch': 'throw', 'publish': 'give',
          'submit': 'give', 'upload': 'lift', 'download': 'lift',
          'load': 'lift', 'approve': 'write', 'authorize': 'write',
          'test': 'look', 'validate': 'look', 'inspect': 'look',
          'negotiate': 'talk', 'pitch': 'point', 'advertise': 'talk',
          'promote': 'talk', 'market': 'talk', 'announce': 'talk',
          'present': 'point', 'consult': 'talk', 'meet': 'talk',
          'collaborate': 'talk', 'interview': 'talk', 'question': 'talk',
          'prescribe': 'write', 'operate': 'fix', 'suture': 'fix',
          'repair': 'fix', 'patch': 'fix', 'heal': 'fix', 'treat': 'fix',
          'feed': 'give', 'serve': 'give', 'issue': 'give',
          'target': 'point', 'aim': 'point', 'attack': 'strike',
          'breach': 'strike', 'exploit': 'strike', 'hack': 'strike',
          'phish': 'strike', 'steal': 'strike', 'rob': 'strike',
          'split': 'cut', 'divide': 'cut', 'fractionalize': 'cut'}

# lemmas that never depict a body activity by themselves
_ABSTRACT = {'be', 'have', 'seem', 'feel', 'become', 'know', 'think',
             'want', 'need', 'like', 'love', 'hope', 'believe', 'get',
             'make', 'do', 'let', 'begin', 'start', 'stop', 'continue',
             'grow', 'turn', 'keep', 'remain', 'stay', 'happen', 'cover',
             'crackle', 'fall', 'rise', 'shine', 'blow', 'thank', 'smile',
             'laugh', 'cry', 'decide', 'agree', 'learn', 'remember',
             'forget', 'wait', 'arrive', 'leave', 'go', 'come', 'return'}
_PHYSICAL_LEX = {'verb.motion', 'verb.contact', 'verb.consumption',
                 'verb.body', 'verb.creation'}

# lexicographer file -> closest body pattern when no anchor matched
_LEX_CLOSEST = {'verb.motion': 'walk', 'verb.contact': 'hold',
                'verb.consumption': 'eat', 'verb.creation': 'fix',
                'verb.body': 'stand'}

# noun ancestors -> the category a schema is refined by
_NOUN_CATS = (
    ('bicycle.n.01', 'bike'), ('motorcycle.n.01', 'bike'),
    ('wheeled_vehicle.n.01', None),
    ('bus.n.01', 'bus'), ('truck.n.01', 'truck'), ('tractor.n.01', 'truck'),
    ('van.n.05', 'truck'), ('locomotive.n.01', 'truck'),
    ('train.n.01', 'truck'), ('car.n.01', 'car'),
    ('motor_vehicle.n.01', 'car'), ('aircraft.n.01', 'plane'),
    ('boat.n.01', 'boat'), ('ship.n.01', 'boat'), ('vessel.n.02', 'boat'),
    ('skateboard.n.01', 'board'), ('ski.n.01', 'board'),
    ('surfboard.n.01', 'board'), ('ice_skate.n.01', 'board'),
    ('ladder.n.01', 'ladder'), ('stairs.n.01', 'stairs'),
    ('stairway.n.01', 'stairs'), ('mountain.n.01', 'mountain'),
    ('hill.n.01', 'hill'), ('natural_elevation.n.01', 'mountain'),
    ('slope.n.01', 'hill'), ('trail.n.02', 'hill'), ('trail.n.01', 'hill'),
    ('cliff.n.01', 'wall'), ('rock.n.01', 'wall'), ('wall.n.01', 'wall'),
    ('tree.n.01', 'tree'),
    ('musical_instrument.n.01', 'instrument'),
    ('board.n.03', 'board_w'), ('blackboard.n.01', 'board_w'),
    ('whiteboard.n.01', 'board_w'), ('canvas.n.02', 'board_w'),
    ('easel.n.01', 'board_w'), ('chart.n.01', 'board_w'),
    ('map.n.01', 'doc'), ('document.n.01', 'doc'), ('book.n.01', 'doc'),
    ('publication.n.01', 'doc'), ('bed.n.01', 'bed'),
    ('table.n.02', 'table'), ('desk.n.01', 'table'),
    ('counter.n.01', 'table'), ('workbench.n.01', 'table'),
    ('stove.n.01', 'stove'), ('seat.n.03', 'seat'), ('bench.n.01', 'seat'),
    ('door.n.01', 'door'), ('gate.n.01', 'door'), ('window.n.01', 'door'),
    ('computer.n.01', 'device'), ('telephone.n.01', 'phone'),
    ('camera.n.01', 'camera'), ('body_of_water.n.01', 'water'),
    ('plant.n.02', 'plant'), ('fruit.n.01', 'plant'),
    ('flower.n.01', 'plant'), ('animal.n.01', 'animal'),
    ('container.n.01', 'vessel'), ('food.n.01', 'food'),
    ('food.n.02', 'food'), ('beverage.n.01', 'drink'),
)
_NOUN_MAP = dict(_NOUN_CATS)
_NOUN_WORDS = {'road': 'road', 'street': 'road', 'highway': 'road',
               'mountain': 'mountain', 'peak': 'mountain', 'summit':
               'mountain', 'trail': 'hill', 'path': 'hill', 'hill': 'hill',
               'car': 'car', 'taxi': 'car', 'cab': 'car', 'jeep': 'car',
               'truck': 'truck', 'lorry': 'truck', 'tractor': 'truck',
               'bus': 'bus', 'bike': 'bike', 'bicycle': 'bike',
               'motorbike': 'bike', 'scooter': 'bike', 'horse': 'animal',
               'camel': 'animal', 'pony': 'animal', 'donkey': 'animal',
               'elephant': 'animal', 'plane': 'plane', 'jet': 'plane',
               'helicopter': 'plane', 'boat': 'boat', 'ship': 'boat',
               'canoe': 'boat', 'kayak': 'boat', 'ferry': 'boat',
               'river': 'water', 'lake': 'water', 'sea': 'water',
               'ocean': 'water', 'pool': 'water', 'pond': 'water',
               'laptop': 'device', 'computer': 'device',
               'keyboard': 'device', 'phone': 'phone', 'wall': 'wall',
               'cliff': 'wall', 'rock': 'wall', 'ladder': 'ladder',
               'stairs': 'stairs', 'steps': 'stairs', 'table': 'table',
               'desk': 'table', 'counter': 'table', 'bench': 'seat',
               'chair': 'seat', 'sofa': 'seat', 'couch': 'seat',
               'stool': 'seat', 'bed': 'bed', 'door': 'door',
               'gate': 'door', 'map': 'doc', 'logbook': 'doc',
               'book': 'doc', 'newspaper': 'doc', 'letter': 'doc',
               'guitar': 'instrument', 'piano': 'instrument',
               'violin': 'instrument', 'drum': 'instrument',
               'board': 'board_w', 'whiteboard': 'board_w',
               'blackboard': 'board_w', 'canvas': 'board_w',
               'stove': 'stove', 'pot': 'stove', 'pan': 'stove',
               'kettle': 'vessel', 'cup': 'vessel', 'mug': 'vessel',
               'camera': 'camera', 'snow': 'ground', 'soil': 'ground',
               'floor': 'ground', 'garden': 'ground', 'hole': 'ground'}
VEHICLES = ('car', 'truck', 'bus', 'plane', 'boat')

_POSTURE = {'lie', 'sit', 'kneel'}


def noun_cat(label):
    """Coarse depiction category of a noun phrase, or ''."""
    words = re.findall(r'[a-z]+', str(label or '').lower())
    if not words:
        return ''
    head = words[-1]
    if head in _NOUN_WORDS:
        return _NOUN_WORDS[head]
    if _wn is None:
        return ''
    for syn in _wn.synsets(head, 'n')[:3]:
        best, depth = '', -1
        for pth in syn.hypernym_paths():
            for d, h in enumerate(pth):
                c = _NOUN_MAP.get(h.name())
                if c and d > depth:
                    best, depth = c, d
        if best:
            return best
    return ''


def _verb_schema(lemma):
    """-> (schema, via) from the lemma table, WordNet anchors, or the
    closest pattern of the verb's lexical field; ('', '') if abstract."""
    lem = str(lemma or '').lower()
    if not lem or lem in _ABSTRACT:
        return '', ''
    if lem in _LEMMA:
        return _LEMMA[lem], 'lemma'
    if _wn is None:
        return '', ''
    syns = _wn.synsets(lem, 'v')
    if not syns:
        return '', ''
    ranked = sorted(syns[:4], key=lambda s: -sum(
        lm.count() for lm in s.lemmas() if lm.name() == lem))
    for syn in ranked[:2]:
        best, depth = '', -1
        for pth in syn.hypernym_paths():
            for d, h in enumerate(pth):
                sc = _VERB_MAP.get(h.name())
                if sc and d > depth:
                    best, depth = sc, d
        if best:
            return best, 'wordnet:' + syn.name()
    lex = ranked[0].lexname()
    if lex in _LEX_CLOSEST:
        return _LEX_CLOSEST[lex], 'closest:' + lex
    return '', ''


def is_physical(lemma):
    """True when a verb names something a body does."""
    lem = str(lemma or '').lower()
    if not lem or lem in _ABSTRACT:
        return False
    if lem in _LEMMA:
        return True
    if _wn is None:
        return False
    syns = _wn.synsets(lem, 'v')
    return bool(syns) and syns[0].lexname() in _PHYSICAL_LEX


def resolve(lemma, objects=(), posture=''):
    """Verb + the things it acts on -> activity spec or None.

    `objects`: [(relation, label)] — relation 'dobj' or a preposition.
    `posture`: a stance already established for the actor ('sit' ...).
    Returns {'schema', 'via', 'partner' (label or None), 'kind' (the
    partner's category), 'lemma'}."""
    sc, via = _verb_schema(lemma)
    if not sc:
        return None
    cats = [(rel, lab, noun_cat(lab)) for rel, lab in objects if lab]

    def first(*want, rels=None):
        return next(((lab, c) for rel, lab, c in cats if c in want
                     and (rels is None or rel in rels)), (None, ''))

    partner, kind = (cats[0][1], cats[0][2]) if cats else (None, '')
    # a vehicle one moves toward or loads into is a destination, not a ride
    veh, vk = first(*VEHICLES, 'bike', 'animal',
                    rels=('dobj', 'in', 'on', 'aboard', 'by', 'across',
                          'along', 'inside', 'up', 'down'))
    if sc in ('drive', 'ride', 'walk', 'run', 'carry') and veh is not None \
            and (sc != 'carry' or vk in VEHICLES):
        if vk in ('bike', 'animal'):
            sc = 'ride'
        elif vk in VEHICLES:
            sc = 'drive'
        partner, kind = veh, vk
    if sc == 'ride' and veh is None:
        sc = 'walk' if not partner else 'ride'
    if sc == 'drive':
        kind = vk if vk in VEHICLES else (
            'plane' if str(lemma) in ('fly', 'pilot') else
            'boat' if str(lemma) == 'sail' else 'car')
        partner = veh
    if sc == 'row':
        partner, kind = veh, 'boat'
    if sc in ('climb', 'walk', 'hike', 'run'):
        s_, k_ = first('mountain', 'hill', 'wall', 'tree', 'ladder',
                       'stairs')
        if s_ is not None:
            partner, kind = s_, k_
            if sc == 'climb' or k_ in ('mountain', 'hill', 'stairs'):
                sc = 'climb' if k_ in ('wall', 'tree', 'ladder') or \
                    sc == 'climb' else 'hike'
        elif sc == 'climb':
            kind = 'mountain'
    if sc == 'swim':
        partner, kind = first('water')
        kind = 'water'
    if sc == 'glide':
        partner, kind = first('board')
    if sc == 'play':
        p_, k_ = first('instrument')
        sc = 'play' if p_ is not None else 'jump'
        partner, kind = (p_, k_) if p_ is not None else (partner, kind)
    if sc in ('write', 'paint', 'point'):
        b_, _k = first('board_w')
        if b_ is not None:
            partner, kind = b_, 'board_w'
            sc = 'paint' if sc == 'paint' else (
                'point' if sc == 'point' else 'board')
        elif sc == 'write':
            sc = 'desk'
    if sc in ('read', 'type', 'craft', 'eat', 'drink', 'look') and (
            posture == 'sit' or first('table')[0] is not None):
        t_, _k = first('table')
        sc = {'read': 'desk', 'type': 'desk', 'craft': 'desk',
              'eat': 'desk', 'drink': 'sit_drink', 'look': 'desk'}[sc]
        if partner is None or noun_cat(partner) in ('table', 'seat'):
            partner = next((lab for rel, lab, c in cats
                            if c not in ('table', 'seat')), None)
            kind = noun_cat(partner) if partner else ''
    if sc == 'type':
        sc = 'desk'
    if sc == 'sit':
        s_, _k = first('seat')
        t_, _k2 = first('table')
        if t_ is not None:
            sc, partner, kind = 'desk', None, ''
        else:
            partner, kind = s_, ('seat' if s_ is not None else '')
    if sc == 'lie':
        partner, kind = first('bed')
    if sc == 'cook' and not first('stove')[0]:
        kind = kind or 'food'
    if sc == 'phone':
        partner, kind = first('phone')
    if sc == 'give' and partner is not None and kind == 'animal':
        sc = 'kneel'
    if sc in ('carry', 'hold') and kind == 'doc':
        sc = 'read' if sc == 'hold' else sc
    if sc == 'look' and kind == 'doc':
        sc = 'read'
    if sc == 'strike' and kind == 'door':
        sc = 'open'
    if sc == 'wipe' and kind == 'ground':
        sc = 'dig'
    if sc == 'stand':
        return None
    if sc == 'sit_drink' and first('table')[0] is not None:
        kind = 'table'
    own = _BUILTIN.get(sc, ())
    one = sc in _ONE_SURFACE and kind in own
    absorb = [lab for _r, lab, c in cats if c in own and lab != partner
              and (not one or c == kind)]
    # a second surface the apparatus doesn't draw (the tree a ladder
    # leans into) is drawn as the backdrop of the picture
    setting = [lab for _r, lab, c in cats if one and c in own
               and c != kind and lab != partner]
    roles = _roles(sc, cats)
    if sc in _FLOW:
        # the vessel poured from is held; the liquid is the stream; a
        # thing watered or filled that is no liquid is where it lands
        ins = roles.get('instrument')
        if ins and noun_cat(ins) in ('drink', 'water'):
            if 'theme' in roles and 'goal' not in roles:
                roles['goal'] = roles.pop('theme')
            roles['theme'] = roles.pop('instrument')
        th = roles.get('theme')
        if th and noun_cat(th) not in ('drink', 'water', 'vessel', 'stove') \
                and 'goal' not in roles:
            roles['goal'] = roles.pop('theme')
        vs = [roles.get(r) for r in ('source', 'theme', 'instrument')]
        partner = next((lab for lab in vs if lab and noun_cat(lab) in
                        ('vessel', 'stove')), roles.get('instrument'))
        kind = noun_cat(partner) if partner else ''
    if sc in _PERCEIVE and roles.get('vantage') == partner:
        partner = roles.get('theme')
        kind = noun_cat(partner) if partner else ''
    return {'schema': sc, 'via': via, 'partner': partner, 'kind': kind,
            'lemma': str(lemma or '').lower(), 'absorb': absorb,
            'setting': setting, 'roles': roles}


# what the body does with each narrated thing, read from its relation to
# the verb: the thing acted on (dobj), where it comes from and goes to,
# what it is done with, and where a watcher watches from
_PERCEIVE = {'look', 'photo', 'point', 'read', 'talk', 'phone'}
_FLOW = {'pour'}
_SRC_PREP = {'from', 'off', 'out', 'out_of'}
_GOAL_PREP = {'into', 'onto', 'to', 'toward', 'towards', 'in', 'on', 'over',
              'at', 'across', 'through', 'under', 'inside'}
_VANTAGE_PREP = {'from', 'through', 'out', 'out_of', 'behind', 'inside'}
_SEEN_PREP = {'at', 'toward', 'towards', 'over', 'on', 'across'}


_OPENING = {'window.n.01', 'door.n.01', 'doorway.n.01', 'opening.n.01',
            'entrance.n.01', 'hatchway.n.01', 'aperture.n.01'}
_OPTIC = {'magnifier.n.01', 'optical_instrument.n.01', 'camera.n.01',
          'optical_device.n.01'}


def vantage_kind(label):
    """How a place one watches from is drawn: 'opening' (a frame the
    watcher looks out of), 'optic' (held to the eye) or 'place' (the
    ground the watcher stands in)."""
    words = re.findall(r'[a-z]+', str(label or '').lower())
    if not words:
        return 'place'
    if noun_cat(label) == 'door':
        return 'opening'
    if _wn is None:
        return 'place'
    for syn in _wn.synsets(words[-1], 'n')[:2]:
        up = {h.name() for pth in syn.hypernym_paths() for h in pth}
        if up & _OPTIC:
            return 'optic'
        if up & _OPENING:
            return 'opening'
    return 'place'


def _roles(sc, cats):
    roles = {}
    for rel, lab, _c in cats:
        if rel == 'dobj':
            r = 'theme'
        elif rel == 'with':
            r = 'instrument'
        elif sc in _PERCEIVE:
            r = ('vantage' if rel in _VANTAGE_PREP else
                 'theme' if rel in _SEEN_PREP else '')
        elif rel in _SRC_PREP:
            r = 'source'
        elif rel in _GOAL_PREP:
            r = 'goal'
        else:
            r = ''
        if r and r not in roles:
            roles[r] = lab
    return roles


# schemas whose apparatus draws exactly one surface of the kinds they own
_ONE_SURFACE = ('climb', 'hike')

# apparatus a schema draws itself: narrated props of that kind are absorbed
_BUILTIN = {'drive': VEHICLES + ('road',), 'ride': ('road', 'hill'),
            'row': ('water', 'boat'), 'swim': ('water',),
            'climb': ('mountain', 'hill', 'wall', 'tree', 'ladder',
                      'stairs'),
            'hike': ('mountain', 'hill', 'stairs', 'road'),
            'walk': ('road',), 'run': ('road',),
            'desk': ('table', 'seat'), 'sit_drink': ('table', 'seat'),
            'sit_read': ('seat',), 'craft': ('table', 'seat'),
            'sit': ('seat',), 'lie': ('bed',), 'fish': ('water',),
            'cook': ('table', 'stove'), 'cut': ('table',),
            'wipe': ('table',), 'fix': ('table',), 'strike': ('table',),
            'board': ('board_w',), 'paint': ('board_w',),
            'plant': ('ground',), 'dig': ('ground',)}

# a seated actor who then does something with their hands stays seated
_SEATED_HANDS = {'read': 'sit_read', 'drink': 'sit_drink',
                 'eat': 'sit_drink', 'write': 'desk', 'type': 'desk',
                 'craft': 'desk', 'hold': 'sit_read', 'phone': 'sit_read',
                 'look': 'sit_read'}


def merge(prev, spec):
    """Combine a posture activity with a later hands activity of the
    same actor ('sat on a bench and read a logbook') -> spec or None."""
    if not prev or not spec:
        return None
    if prev.get('schema') == 'sit' and spec['schema'] in (
            'desk', 'sit_drink', 'sit_read'):
        return spec
    if prev.get('schema') == 'sit' and spec['schema'] in _SEATED_HANDS:
        return dict(spec, schema=_SEATED_HANDS[spec['schema']],
                    via=str(spec.get('via')) + '+sit')
    return None


# ---------------------------------------------------------------- drawing
INK = 'ink'
PALE = 'pale'
C = {'car': '#C8553D', 'truck': '#3F7CAC', 'bus': '#E3B23C',
     'plane': '#DDE3E8', 'boat': '#A0522D', 'bike': '#3F7CAC',
     'tire': '#3A3A3A', 'seat': '#6B5B4B', 'wood': '#A57A55',
     'rock': '#B9AFA0', 'snow': '#F4F1EA', 'grass': '#8DB36B',
     'water': '#8EC5E8', 'bed': '#9FB7D9', 'sheet': '#F4F1EA',
     'soil': '#8B6B4A', 'metal': '#9AA3AB', 'board': '#F4F1EA',
     'steam': '#C9CED3', 'glass': '#CFE8F3', 'leaf': '#6FA35A'}
TONES = tuple(sorted(set(C.values()) | {'#E8E2D6', '#F2D16B', '#C8553D',
                                          '#E3C27A', '#8EC5E8', '#3F7CAC'}))


def _u(pts):
    return [(x * H, y * H) for x, y in pts]


def _poly(pts, col, w=0.8):
    q = _u(pts)
    return [(q + [q[0]], col, w, 'solid'), (q + [q[0]], INK, 0.62, False)]


def _line(pts, col=INK, w=0.85):
    return [(_u(pts), col, w, False)]


def _circ(cx, cy, r, col=None, ry=None, n=22, a0=0.0, a1=2 * math.pi,
          w=0.8):
    ry = r if ry is None else ry
    pts = [(cx + math.cos(a0 + (a1 - a0) * i / n) * r,
            cy + math.sin(a0 + (a1 - a0) * i / n) * ry) for i in range(n + 1)]
    if col is None:
        return _line(pts, INK, w)
    return _poly(pts[:-1], col, w)


def _wheel(cx, cy, r):
    return _circ(cx, cy, r, C['tire']) + _circ(cx, cy, r * 0.45, '#E8E2D6')


def _body_pt(pose, dx, dy):
    """A point on the torso frame (dx forward, dy up from hip, negative
    = up) of a pose, in unit coords."""
    a = float(pose.get('lean', 0.0))
    hx, hy = pose['hip']
    return (hx + dx * math.cos(a) - dy * math.sin(a),
            hy + dx * math.sin(a) + dy * math.cos(a))


def _mouth(pose):
    return _body_pt(pose, 0.095, -0.45)


def _std(hip=(0.0, -0.39), lean=0.04, hn=(0.10, -0.40), hf=(-0.08, -0.42),
         fn=(0.07, 0.0), ff=(-0.05, 0.0), **kw):
    d = {'hip': hip, 'lean': lean, 'hands': {'n': hn, 'f': hf},
         'feet': {'n': fn, 'f': ff}}
    d.update(kw)
    return d


def _vehicle(kind, col):
    """-> (pose, back, front, marks) for a seated operator facing +x."""
    back, front, marks = [], [], []
    lift = {'truck': 0.14, 'bus': 0.14}.get(kind, 0.0)
    hy = -0.46 - lift
    pose = _std(hip=(0.0, hy), lean=-0.10,
                hn=(0.27, hy - 0.28), hf=(0.29, hy - 0.20),
                fn=(0.36, hy + 0.22), ff=(0.33, hy + 0.24),
                knee=(0.3, -0.95), elbow=(0.0, 1.0))
    back += _poly([(-0.17, hy), (-0.07, hy), (-0.13, hy - 0.48),
                   (-0.25, hy - 0.48)], C['seat'])
    if kind == 'boat':
        pose['hip'] = (0.0, -0.52)
        pose['hands'] = {'n': (0.27, -0.80), 'f': (0.29, -0.72)}
        pose['feet'] = {'n': (0.30, -0.30), 'f': (0.27, -0.28)}
        back = _poly([(-0.17, -0.52), (-0.07, -0.52), (-0.13, -0.98),
                      (-0.25, -0.98)], C['seat'])
        back += _circ(0.30, -0.76, 0.10, None) + _line(
            [(0.30, -0.76), (0.40, -0.52)])
        for a in range(0, 360, 60):
            r_ = math.radians(a)
            back += _line([(0.30, -0.76), (0.30 + 0.14 * math.cos(r_),
                                           -0.76 + 0.14 * math.sin(r_))])
        front += _poly([(-0.85, -0.50), (1.05, -0.50), (0.80, -0.08),
                        (-0.70, -0.08)], col or C['boat'])
        for k in range(4):
            x0 = -1.0 + k * 0.62
            front += _line([(x0, -0.06), (x0 + 0.15, -0.12), (x0 + 0.30,
                            -0.06), (x0 + 0.45, -0.12)], C['water'], 1.2)
        return pose, back, front, marks
    if kind == 'plane':
        pose['hip'] = (0.0, -0.50)
        pose['hands'] = {'n': (0.26, -0.72), 'f': (0.28, -0.66)}
        pose['feet'] = {'n': (0.34, -0.28), 'f': (0.31, -0.26)}
        back = _poly([(-0.17, -0.50), (-0.07, -0.50), (-0.13, -0.98),
                      (-0.25, -0.98)], C['seat'])
        back += _line([(0.26, -0.72), (0.36, -0.46)], INK, 1.1)
        front += _poly([(-1.3, -0.30), (0.95, -0.30), (1.25, -0.46),
                        (0.95, -0.62), (0.45, -0.60), (-1.2, -0.62),
                        (-1.45, -0.98), (-1.6, -0.98), (-1.45, -0.30)],
                       col or C['plane'])
        front += _poly([(-0.55, -0.40), (0.20, -0.40), (-0.35, -0.02),
                        (-0.65, -0.02)], col or C['plane'])
        back += _line([(0.45, -0.60), (0.22, -1.12), (-0.45, -1.14),
                       (-0.55, -0.62)], INK, 1.0)
        for y in (-0.9, -0.7):
            marks += _line([(-1.9, y), (-1.65, y)], PALE, 0.8)
        return pose, back, front, marks
    x0, x1 = (-0.72, 0.86) if kind == 'car' else (-1.05, 0.86)
    top = -0.56 - lift
    roof = -1.14 - lift
    body = col or C.get(kind, C['car'])
    back += _line([(0.43, top), (0.22, roof), (-0.46 if kind == 'car'
                                               else x0 + 0.06, roof),
                   (-0.62 if kind == 'car' else x0 + 0.02, top)], INK, 1.0)
    back += _poly([(0.22, roof - 0.01), (0.25, roof + 0.03),
                   (-0.46 if kind == 'car' else x0 + 0.05, roof + 0.03),
                   (-0.46 if kind == 'car' else x0 + 0.05, roof - 0.01)],
                  body)
    if kind != 'car':
        back += _line([(x0 + 0.02, top), (x0 + 0.02, roof)], INK, 1.0)
        for wx in (x0 + 0.30, x0 + 0.62):
            back += _line([(wx, top), (wx, roof)], INK, 0.8)
    # steering wheel on its column, in front of the chest
    wx, wy = 0.29, hy - 0.24
    back += _circ(wx, wy, 0.035, None, ry=0.11, w=1.1)
    back += _line([(wx + 0.02, wy + 0.04), (0.44, top + 0.04)], INK, 1.0)
    front += _poly([(x0, -0.16), (x1, -0.16), (x1 + 0.04, top + 0.16),
                    (0.70, top + 0.06), (0.43, top), (x0 + 0.08, top),
                    (x0 - 0.02, top + 0.12)], body)
    front += _line([(0.10, top + 0.05), (0.10, -0.2)], INK, 0.6)
    front += _line([(0.18, top + 0.14), (0.26, top + 0.14)], INK, 0.8)
    for cx in ((x0 + 0.30, x1 - 0.32) if kind == 'car' else
               (x0 + 0.32, x0 + 0.62, x1 - 0.32)):
        front += _wheel(cx, -0.14, 0.14)
    front += _poly([(x1 - 0.02, top + 0.24), (x1 + 0.05, top + 0.24),
                    (x1 + 0.05, top + 0.31), (x1 - 0.02, top + 0.31)],
                   '#F2D16B')
    marks += _line([(x1 + 0.10, 0.02), (x1 + 0.95, 0.02)], PALE, 1.0)
    for k in range(3):
        xa = x1 + 0.20 + k * 0.28
        marks += _line([(xa, -0.02), (xa + 0.14, -0.02)], INK, 0.7)
    for y in (-0.38, -0.52 - lift, -0.66 - lift):
        marks += _line([(x0 - 0.40, y), (x0 - 0.12, y)], PALE, 0.8)
    return pose, back, front, marks


def _bike(col):
    back, front = [], []
    rw = 0.22
    rx, fx, cy = -0.40, 0.44, -0.22
    back += _circ(rx, cy, rw, None, w=1.1) + _circ(fx, cy, rw, None, w=1.1)
    seat, head, crank = (-0.12, -0.56), (0.30, -0.64), (0.02, -0.22)
    front += _line([(rx, cy), seat, crank, (rx, cy)], col or C['bike'], 1.3)
    front += _line([seat, head, crank], col or C['bike'], 1.3)
    front += _line([head, (fx, cy)], col or C['bike'], 1.3)
    front += _line([head, (0.27, -0.80), (0.36, -0.82)], INK, 1.1)
    back += _poly([(-0.20, -0.60), (-0.04, -0.60), (-0.06, -0.56),
                   (-0.18, -0.56)], C['seat'])
    pose = _std(hip=(-0.11, -0.62), lean=0.55, hn=(0.28, -0.81),
                hf=(0.27, -0.80), fn=(0.10, -0.26), ff=(-0.05, -0.22),
                knee=(0.9, -0.4), elbow=(0.0, 1.0))
    marks = []
    for y in (-0.30, -0.50):
        marks += _line([(-0.95, y), (-0.70, y)], PALE, 0.8)
    return pose, back, front, marks


def _slope(kind):
    """Mountain/hill face rising to +x -> (surface fn, back strokes)."""
    peak = (1.05, -1.45) if kind == 'mountain' else (1.10, -0.95)
    base = (-0.95, 0.0)
    far = (1.9, 0.0)
    col = C['rock'] if kind == 'mountain' else C['grass']
    back = _poly([base, peak, far], col)
    if kind == 'mountain':
        t0 = 0.72
        a = (base[0] + (peak[0] - base[0]) * t0,
             base[1] + (peak[1] - base[1]) * t0)
        b = (far[0] + (peak[0] - far[0]) * t0, far[1] + (peak[1] - far[1])
             * t0)
        back += _poly([a, peak, b, (b[0] - 0.12, b[1] + 0.06),
                       (peak[0], a[1] + 0.02), (a[0] + 0.10, a[1] + 0.07)],
                      C['snow'])
        back += _line([(peak[0], peak[1]), (peak[0], peak[1] - 0.22)])
        back += _poly([(peak[0], peak[1] - 0.22), (peak[0] + 0.16,
                       peak[1] - 0.18), (peak[0], peak[1] - 0.14)],
                      '#C8553D')
    for k in range(5):
        x = 0.1 + k * 0.33
        back += _line([(x, -0.02 - 0.05 * (k % 2)), (x + 0.12, -0.10)],
                      PALE, 0.7)
    sl = (peak[1] - base[1]) / (peak[0] - base[0])

    def surf(x):
        return base[1] + (x - base[0]) * sl
    return surf, sl, back


def _climb(kind):
    back, front, marks = [], [], []
    if kind in ('mountain', 'hill'):
        surf, sl, back = _slope(kind)
        ang = math.atan(sl)
        xf_, xn = -0.05, 0.20
        yf, yn = surf(xf_), surf(xn)
        hip = (0.04, (yf + yn) / 2 - 0.30)
        pose = _std(hip=hip, lean=0.70, fn=(xn, yn), ff=(xf_, yf),
                    hn=(0.40, surf(0.40) - 0.02), hf=(0.34, surf(0.34)
                                                      - 0.01),
                    toe=(math.cos(ang), math.sin(ang)),
                    knee=(0.8, -0.6), elbow=(0.2, 0.98))
        return pose, back, front, marks
    if kind == 'ladder':
        for x in (0.26, 0.50):
            back += _line([(x, 0.0), (x, -1.75)], C['wood'], 1.6)
        for k in range(1, 9):
            back += _line([(0.26, -k * 0.2), (0.50, -k * 0.2)], C['wood'],
                          1.2)
        pose = _std(hip=(0.14, -0.86), lean=-0.12, hn=(0.30, -1.40),
                    hf=(0.32, -1.20), fn=(0.30, -0.60), ff=(0.29, -0.40),
                    knee=(1.0, -0.2), toe=(1.0, 0.0), elbow=(-0.4, 0.9))
        return pose, back, front, marks
    if kind == 'stairs':
        pts = [(-0.6, 0.0)]
        for k in range(6):
            pts += [(-0.3 + k * 0.28, -k * 0.16),
                    (-0.3 + k * 0.28, -(k + 1) * 0.16)]
        pts += [(1.4, -0.96), (1.4, 0.0)]
        back += _poly(pts, C['wood'])
        pose = _std(hip=(0.08, -0.72), lean=0.18, fn=(0.26, -0.48),
                    ff=(-0.03, -0.32), hn=(0.22, -0.66), hf=(-0.06, -0.70))
        return pose, back, front, marks
    # a vertical face: wall, cliff, rock, tree trunk
    col = C['wood'] if kind == 'tree' else C['rock']
    back += _poly([(0.36, 0.0), (0.33, -1.0), (0.40, -1.8), (1.20, -1.8),
                   (1.25, 0.0)], col)
    if kind == 'tree':
        back += _circ(0.80, -2.05, 0.60, C['leaf'], ry=0.40)
    for (x, y) in ((0.36, -1.42), (0.35, -1.18), (0.36, -0.62),
                   (0.34, -0.40)):
        back += _circ(x + 0.02, y, 0.03, C['seat'])
    pose = _std(hip=(0.12, -0.84), lean=-0.10, hn=(0.34, -1.42),
                hf=(0.33, -1.18), fn=(0.34, -0.62), ff=(0.32, -0.40),
                knee=(1.0, -0.4), toe=(1.0, -0.2), elbow=(-0.5, 0.8))
    return pose, back, front, marks


def _table(x0=0.26, x1=0.98, top=-0.52):
    st = _poly([(x0, top), (x1, top), (x1, top + 0.035), (x0, top + 0.035)],
               C['wood'])
    for x in (x0 + 0.05, x1 - 0.05):
        st += _line([(x, top + 0.035), (x, 0.0)], INK, 0.9)
    return st


def _chair(seat_=True):
    st = _poly([(-0.16, -0.235), (0.14, -0.235), (0.14, -0.205),
                (-0.16, -0.205)], C['wood'])
    st += _line([(-0.15, -0.235), (-0.19, -0.80)], C['wood'], 1.4)
    for x in (-0.14, 0.12):
        st += _line([(x, -0.205), (x, 0.0)], INK, 0.9)
    return st if seat_ else []


SEATED = _std(hip=(-0.02, -0.24), lean=0.06, hn=(0.15, -0.33),
              hf=(0.12, -0.35), fn=(0.20, -0.015), ff=(0.17, 0.0),
              knee=(0.65, -0.75), toe=(1.0, 0.1))


_SEATED_SCHEMAS = {'drive', 'ride', 'row', 'desk', 'sit', 'sit_drink',
                   'sit_read',
                   'craft', 'fish', 'lie'}


def _reach_err(pose):
    """Worst distance (figure heights) by which a limb target lies
    beyond the limb's reach for this hip and lean."""
    hip0 = sb_cast.HIP_Y + 0.03
    worst = 0.0
    for side, dx in (('n', 0.03), ('f', -0.02)):
        sh = _body_pt(pose, dx, sb_cast.SH_Y + 0.02 - hip0)
        for tgt, base, (a, b) in ((pose['hands'][side], sh, sb_cast.ARM),
                                  (pose['feet'][side],
                                   _body_pt(pose, 0.012 if side == 'n'
                                            else -0.012, 0.0),
                                   sb_cast.LEG)):
            d = math.hypot(tgt[0] - base[0], tgt[1] - base[1])
            worst = max(worst, d - (a + b) + 0.004, abs(a - b) - d)
    return worst


def _settle(pose, fixed_hip):
    """Shift hip/lean (the least) until every limb reaches its contact;
    seated schemas keep their hips on the support and only lean."""
    if _reach_err(pose) <= 0.0:
        return pose
    hx, hy = pose['hip']
    ln = float(pose.get('lean', 0.0))
    best, key = pose, (_reach_err(pose), 0.0)
    steps = [k * 0.03 for k in range(-6, 7)]
    for dl in [k * 0.08 for k in range(-6, 7)]:
        for dx in ([0.0] if fixed_hip else steps):
            for dy in ([0.0] if fixed_hip else steps):
                cand = dict(pose, hip=(hx + dx, hy + dy), lean=ln + dl)
                err = max(0.0, _reach_err(cand))
                k_ = (round(err, 3), abs(dx) + abs(dy) + abs(dl) * 0.3)
                if k_ < key:
                    best, key = cand, k_
    return best


def _schema(sc, kind, col, tool):
    """-> (pose, back, front, marks, slot, extra) for one schema; `slot`
    is (cx, bottom, size) in unit coords for the narrated object or
    None; `extra` holds strokes drawn over the hands (tools)."""
    back, front, marks, extra = [], [], [], []
    slot = None
    if sc == 'drive':
        pose, back, front, marks = _vehicle(kind or 'car', col)
        return pose, back, front, marks, None, extra
    if sc == 'ride':
        if kind == 'animal':
            pose = _std(hip=(0.0, -0.88), lean=0.12, hn=(0.30, -0.96),
                        hf=(0.28, -0.94), fn=(0.10, -0.52),
                        ff=(0.06, -0.54), knee=(0.8, -0.3),
                        elbow=(0.0, 1.0))
            return pose, back, front, marks, ('mount', 0.0, 1.30), extra
        pose, back, front, marks = _bike(col)
        return pose, back, front, marks, None, extra
    if sc == 'row':
        pose = dict(SEATED, hip=(0.0, -0.52), hands={'n': (0.30, -0.66),
                    'f': (0.26, -0.64)}, feet={'n': (0.30, -0.30),
                                               'f': (0.26, -0.28)})
        front += _poly([(-0.85, -0.50), (1.0, -0.50), (0.80, -0.10),
                        (-0.70, -0.10)], col or C['boat'])
        extra += _line([(0.05, -0.95), (0.30, -0.66), (0.70, 0.10)],
                       C['wood'], 1.4)
        extra += _poly([(0.64, 0.02), (0.78, 0.0), (0.80, 0.22),
                        (0.68, 0.24)], C['wood'])
        for k in range(4):
            x0 = -1.0 + k * 0.62
            front += _line([(x0, -0.06), (x0 + 0.15, -0.12), (x0 + 0.30,
                            -0.06), (x0 + 0.45, -0.12)], C['water'], 1.2)
        return pose, back, front, marks, None, extra
    if sc == 'climb':
        pose, back, front, marks = _climb(kind or 'mountain')
        return pose, back, front, marks, None, extra
    if sc == 'hike':
        if kind in ('mountain', 'hill', 'stairs'):
            pose, back, front, marks = _climb(kind)
            hx_, hy_ = pose['hip']
            pose = dict(pose, lean=0.22, hands={
                'n': (hx_ + 0.24, hy_ - 0.14), 'f': (hx_ - 0.06, hy_ - 0.02)},
                elbow=(0.0, 1.0))
            if kind != 'stairs':
                h_ = pose['hands']['n']
                extra += _line([(h_[0] - 0.02, h_[1] - 0.10),
                                (h_[0] + 0.10, h_[1] + 0.34)], C['wood'],
                               1.3)
            return pose, back, front, marks, None, extra
        sc = 'walk'
    if sc in ('walk', 'run', 'carry'):
        if sc == 'run':
            pose = _std(hip=(0.0, -0.36), lean=0.32, fn=(0.22, -0.05),
                        ff=(-0.22, -0.12), hn=(0.24, -0.62),
                        hf=(-0.14, -0.46), elbow=(-0.3, 0.95),
                        knee=(1.0, -0.1))
            for y in (-0.35, -0.55, -0.75):
                marks += _line([(-0.62, y), (-0.36, y)], PALE, 0.8)
        else:
            pose = _std(hip=(0.0, -0.385), lean=0.06, fn=(0.13, 0.0),
                        ff=(-0.12, -0.01), hn=(0.11, -0.40),
                        hf=(-0.12, -0.44))
        marks += _line([(-0.5, 0.02), (0.9, 0.02)], PALE, 1.0)
        if sc == 'carry':
            pose['hands'] = {'n': (0.20, -0.58), 'f': (0.17, -0.55)}
            pose['elbow'] = (0.0, 1.0)
            slot = ('hands', 0.26, 0.30)
        return pose, back, front, marks, slot, extra
    if sc == 'glide':
        pose = _std(hip=(0.0, -0.32), lean=0.22, fn=(0.14, 0.0),
                    ff=(-0.14, 0.0), hn=(0.30, -0.66), hf=(-0.30, -0.62),
                    knee=(1.0, -0.3), elbow=(0.0, 1.0))
        front += _poly([(-0.34, 0.02), (0.36, 0.02), (0.42, -0.02),
                        (0.36, 0.05), (-0.34, 0.05)], col or C['bike'])
        for y in (-0.2, -0.4):
            marks += _line([(-0.85, y), (-0.55, y)], PALE, 0.8)
        return pose, back, front, marks, None, extra
    if sc == 'crawl':
        pose = _std(hip=(-0.10, -0.28), lean=1.10, hn=(0.28, 0.0),
                    hf=(0.24, 0.0), fn=(-0.34, -0.02), ff=(-0.38, -0.02),
                    knee=(0.0, 1.0), toe=(-1.0, 0.0), elbow=(0.3, 0.9),
                    head=(0.0, 0.02))
        return pose, back, front, marks, None, extra
    if sc == 'swim':
        pose = _std(hip=(0.0, -0.16), lean=1.45, hn=(0.60, -0.18),
                    hf=(-0.12, -0.10), fn=(-0.56, -0.14),
                    ff=(-0.52, -0.22), toe=(-1.0, 0.0), knee=(0.0, -1.0),
                    elbow=(0.0, -1.0), head=(-0.02, -0.02))
        for k in range(5):
            x0 = -1.0 + k * 0.45
            front += _line([(x0, -0.10), (x0 + 0.11, -0.16), (x0 + 0.22,
                            -0.10), (x0 + 0.33, -0.16)], C['water'], 1.4)
        back += _poly([(-1.05, -0.12), (1.2, -0.12), (1.2, 0.10),
                       (-1.05, 0.10)], C['water'])
        marks += _circ(0.86, -0.26, 0.03) + _circ(0.92, -0.34, 0.02)
        return pose, back, front, marks, None, extra
    if sc in ('jump', 'dance'):
        pose = _std(hip=(0.0, -0.56), lean=-0.05, fn=(0.12, -0.14),
                    ff=(-0.10, -0.18), hn=(0.20, -1.08),
                    hf=(-0.16 if sc == 'jump' else -0.24,
                        -1.04 if sc == 'jump' else -0.60),
                    elbow=(0.0, 1.0), knee=(1.0, 0.1))
        marks += _line([(-0.22, 0.02), (0.24, 0.02)], PALE, 1.0)
        return pose, back, front, marks, None, extra
    if sc in ('push', 'pull'):
        if sc == 'push':
            pose = _std(hip=(0.0, -0.35), lean=0.48, fn=(0.08, 0.0),
                        ff=(-0.26, -0.01), hn=(0.44, -0.54),
                        hf=(0.42, -0.50), elbow=(0.0, 1.0))
            slot = ('ahead', 0.44, 0.62)
        else:
            pose = _std(hip=(0.02, -0.37), lean=-0.30, fn=(0.20, 0.0),
                        ff=(-0.06, 0.0), hn=(0.24, -0.56),
                        hf=(0.22, -0.54), elbow=(0.0, 1.0))
            extra += _line([(0.24, -0.56), (0.62, -0.30)], C['wood'], 1.0)
            slot = ('ahead', 0.62, 0.55)
        marks += _line([(-0.45, 0.02), (1.3, 0.02)], PALE, 1.0)
        marks += _circ(-0.10, -0.98, 0.02) + _circ(-0.16, -0.90, 0.015)
        return pose, back, front, marks, slot, extra
    if sc == 'lift':
        pose = _std(hip=(-0.04, -0.30), lean=0.30, fn=(0.12, 0.0),
                    ff=(-0.10, 0.0), hn=(0.26, -0.48), hf=(0.23, -0.46),
                    elbow=(0.0, 1.0), knee=(1.0, -0.3))
        slot = ('hands', 0.30, 0.34)
        return pose, back, front, marks, slot, extra
    if sc == 'throw':
        pose = _std(hip=(0.0, -0.39), lean=-0.10, fn=(0.18, 0.0),
                    ff=(-0.14, 0.0), hn=(-0.10, -1.00), hf=(0.22, -0.66),
                    elbow=(-0.6, 0.2))
        slot = ('hand', 0.0, 0.14)
        marks += _line([(0.05, -1.05), (0.45, -1.15), (0.80, -1.00)],
                       PALE, 0.9)
        return pose, back, front, marks, slot, extra
    if sc == 'kick':
        pose = _std(hip=(0.0, -0.41), lean=-0.10, fn=(0.33, -0.16),
                    ff=(-0.04, 0.0), hn=(0.16, -0.62), hf=(-0.20, -0.58),
                    knee=(0.6, -0.8))
        slot = ('at', (0.48, -0.02), 0.16)
        marks += _line([(0.60, -0.14), (0.78, -0.18)], PALE, 0.8)
        return pose, back, front, marks, slot, extra
    if sc in ('desk', 'sit_drink', 'craft', 'type'):
        pose = dict(SEATED, lean=0.16, hands={'n': (0.40, -0.56),
                                              'f': (0.36, -0.55)},
                    elbow=(0.0, 1.0))
        back += _chair()
        front += _table()
        slot = ('surface', (0.56, -0.52), 0.28)
        if sc == 'sit_drink' and kind != 'table':
            front = []
        if sc == 'sit_drink':
            m = _mouth(pose)
            pose['hands'] = {'n': (m[0] + 0.04, m[1] + 0.05),
                             'f': (0.36, -0.55)}
            pose['elbow'] = (0.3, 0.95)
            slot = ('hand', 0.0, 0.13)
        return pose, back, front, marks, slot, extra
    if sc == 'sit_read':
        pose = dict(SEATED, hands={'n': (0.24, -0.62), 'f': (0.20, -0.60)},
                    elbow=(0.0, 1.0), head=(0.01, 0.02))
        back += _chair()
        return pose, back, front, marks, ('hands', 0.24, 0.22), extra
    if sc == 'sit':
        pose = dict(SEATED)
        if kind != 'seat':
            back += _chair()
            return pose, back, front, marks, None, extra
        return pose, back, front, marks, ('seat', 0.0, 0.52), extra
    if sc in ('drink', 'eat'):
        pose = _std(hn=(0.0, 0.0))
        m = _mouth(pose)
        pose['hands'] = {'n': (m[0] + 0.04, m[1] + 0.05),
                         'f': (-0.06, -0.42)}
        pose['elbow'] = (0.3, 0.95)
        slot = ('hand', 0.0, 0.13)
        return pose, back, front, marks, slot, extra
    if sc == 'lie':
        pose = _std(hip=(0.22, -0.40), lean=-1.52, fn=(0.66, -0.40),
                    ff=(0.64, -0.37), hn=(0.08, -0.44), hf=(0.10, -0.42),
                    toe=(0.0, -1.0), knee=(0.0, -1.0), elbow=(0.0, -1.0))
        back += _poly([(-0.70, -0.34), (0.80, -0.34), (0.80, -0.20),
                       (-0.70, -0.20)], C['bed'])
        back += _line([(-0.66, -0.20), (-0.66, 0.0)], INK, 1.0)
        back += _line([(0.76, -0.20), (0.76, 0.0)], INK, 1.0)
        back += _line([(-0.70, -0.62), (-0.70, 0.0)], C['wood'], 1.6)
        back += _circ(-0.50, -0.40, 0.14, C['sheet'], ry=0.06)
        front += _poly([(0.02, -0.52), (0.78, -0.48), (0.80, -0.34),
                        (0.0, -0.34)], C['sheet'])
        for k, (dx, dy) in enumerate(((0.0, 0.0), (0.10, -0.10),
                                      (0.22, -0.22))):
            s_ = 0.04 + 0.015 * k
            x_, y_ = -0.40 + dx, -0.78 + dy
            marks += _line([(x_, y_), (x_ + s_, y_), (x_, y_ + s_),
                            (x_ + s_, y_ + s_)], INK, 0.8)
        return pose, back, front, marks, None, extra
    if sc in ('kneel', 'plant'):
        pose = _std(hip=(0.0, -0.26), lean=0.80, fn=(0.18, 0.0),
                    ff=(-0.20, -0.01), hn=(0.34, -0.12), hf=(0.31, -0.10),
                    knee=(0.9, -0.4), elbow=(0.0, 1.0))
        pose['knee_f'] = (0.0, 1.0)
        if sc == 'plant':
            front += _circ(0.45, 0.0, 0.16, C['soil'], ry=0.05)
        slot = ('ahead', 0.34, 0.42 if kind == 'animal' else 0.26)
        return pose, back, front, marks, slot, extra
    if sc == 'dig':
        pose = _std(hip=(0.0, -0.37), lean=0.28, fn=(0.10, 0.0),
                    ff=(-0.14, 0.0), hn=(0.24, -0.44), hf=(0.10, -0.60),
                    elbow=(0.0, 1.0))
        end = (0.50, -0.02)
        extra += _line([(0.04, -0.70), end], C['wood'], 1.4)
        t = tool or 'shovel'
        if t in ('broom', 'sweep', 'rake', 'hoe'):
            extra += _poly([(end[0] - 0.08, end[1] - 0.06),
                            (end[0] + 0.10, end[1] - 0.06),
                            (end[0] + 0.14, end[1] + 0.02),
                            (end[0] - 0.12, end[1] + 0.02)], '#E3C27A')
        elif t in ('mop', 'vacuum'):
            for k in range(5):
                extra += _line([end, (end[0] - 0.08 + k * 0.04,
                                      end[1] + 0.03)], C['sheet'], 1.2)
        else:
            extra += _poly([(end[0] - 0.05, end[1] - 0.10),
                            (end[0] + 0.07, end[1] - 0.08),
                            (end[0] + 0.06, end[1] + 0.03),
                            (end[0] - 0.04, end[1] + 0.02)], C['metal'])
        front += _circ(0.72, 0.0, 0.14, C['soil'] if t == 'shovel'
                       else C['snow'], ry=0.05)
        slot = ('ahead', 0.62, 0.24)
        return pose, back, front, marks, slot, extra
    if sc in ('cook', 'cut', 'wipe', 'fix', 'strike'):
        pose = _std(hip=(0.0, -0.39), lean=0.16, hn=(0.38, -0.56),
                    hf=(0.34, -0.54), elbow=(0.0, 1.0))
        top = -0.52
        front += _table(0.26, 1.0, top)
        slot = ('surface', (0.66, top), 0.30)
        if sc == 'cook':
            front += _poly([(0.46, top - 0.02), (0.86, top - 0.02),
                            (0.82, top - 0.22), (0.50, top - 0.22)],
                           C['metal'])
            extra += _line([(0.36, -0.62), (0.62, top - 0.10)], C['wood'],
                           1.2)
            for k in range(3):
                x_ = 0.56 + k * 0.10
                marks += _line([(x_, top - 0.28), (x_ + 0.03, top - 0.36),
                                (x_, top - 0.44)], C['steam'], 0.9)
            slot = ('surface', (0.66, top - 0.18), 0.18)
        elif sc == 'cut':
            front += _poly([(0.40, top - 0.03), (0.92, top - 0.03),
                            (0.92, top), (0.40, top)], C['wood'])
            extra += _poly([(0.38, -0.58), (0.56, top - 0.05),
                            (0.58, top - 0.08), (0.40, -0.61)], C['metal'])
        elif sc == 'strike':
            pose['hands'] = {'n': (0.20, -0.92), 'f': (0.36, -0.56)}
            pose['elbow'] = (-0.5, 0.6)
            extra += _line([(0.20, -0.92), (0.30, -1.06)], C['wood'], 1.4)
            extra += _poly([(0.24, -1.12), (0.40, -1.04), (0.37, -0.98),
                            (0.21, -1.06)], C['metal'])
            for a in (-0.5, 0.0, 0.5):
                marks += _line([(0.66 + 0.10 * math.sin(a), top - 0.34),
                                (0.66 + 0.18 * math.sin(a), top - 0.44)],
                               INK, 0.7)
        elif sc == 'wipe':
            extra += _circ(0.40, -0.55, 0.05, '#8EC5E8', ry=0.03)
        elif sc == 'fix':
            extra += _line([(0.38, -0.56), (0.52, top - 0.08)], C['metal'],
                           1.4)
        return pose, back, front, marks, slot, extra
    if sc in ('board', 'paint', 'point'):
        pose = _std(hip=(0.0, -0.39), lean=0.02, hn=(0.30, -0.78),
                    hf=(-0.04, -0.44), elbow=(0.0, 1.0))
        if kind == 'board_w' or sc in ('board', 'paint'):
            back += _poly([(0.30, -1.20), (1.10, -1.20), (1.10, -0.46),
                           (0.30, -0.46)], C['board'])
            back += _line([(0.55, -0.46), (0.48, 0.0)], C['wood'], 1.2)
            back += _line([(1.05, -0.46), (1.12, 0.0)], C['wood'], 1.2)
            pose['hands']['n'] = (0.31, -0.80)
            if sc == 'paint':
                extra += _line([(0.31, -0.80), (0.39, -0.86)], C['wood'],
                               1.2)
                back += _line([(0.55, -1.0), (0.75, -0.95), (0.95, -1.05)],
                              '#3F7CAC', 1.4)
            else:
                extra += _line([(0.30, -0.79), (0.35, -0.84)], INK, 1.3)
                back += _line([(0.55, -1.05), (0.85, -1.05)], INK, 0.8)
                back += _line([(0.55, -0.92), (1.0, -0.92)], INK, 0.8)
            slot = ('board', (0.80, -0.62), 0.30) if kind != 'board_w' \
                else None
        else:
            pose['hands']['n'] = (0.30, -0.78)
            slot = ('ahead', 0.70, 0.55)
        return pose, back, front, marks, slot, extra
    if sc == 'read':
        pose = _std(hn=(0.22, -0.64), hf=(0.18, -0.62), elbow=(0.0, 1.0),
                    head=(0.01, 0.02))
        slot = ('hands', 0.24, 0.22)
        return pose, back, front, marks, slot, extra
    if sc == 'phone':
        pose = _std(hn=(0.0, 0.0))
        e_ = _body_pt(pose, 0.02, -0.46)
        pose['hands'] = {'n': (e_[0] + 0.02, e_[1] + 0.02),
                         'f': (-0.06, -0.42)}
        pose['elbow'] = (0.4, 0.9)
        slot = ('hand', 0.0, 0.10)
        marks += _circ(0.20, -0.88, 0.06, None, a0=-1.0, a1=1.0, n=8)
        return pose, back, front, marks, slot, extra
    if sc == 'photo':
        pose = _std(hn=(0.0, 0.0))
        e_ = _body_pt(pose, 0.14, -0.47)
        pose['hands'] = {'n': (e_[0] + 0.03, e_[1] + 0.02),
                         'f': (e_[0] + 0.02, e_[1] + 0.06)}
        pose['elbow'] = (0.0, 1.0)
        slot = ('hand', 0.0, 0.14)
        return pose, back, front, marks, slot, extra
    if sc == 'look':
        pose = _std(lean=0.20, hn=(0.20, -0.66), hf=(-0.06, -0.44),
                    elbow=(0.0, 1.0))
        slot = ('ahead', 0.62, 0.50)
        e_ = _body_pt(pose, 0.14, -0.47)
        marks += _line([(e_[0] + 0.06, e_[1]), (e_[0] + 0.24, e_[1] + 0.06)],
                       PALE, 0.7)
        return pose, back, front, marks, slot, extra
    if sc in ('give', 'hold'):
        if sc == 'give':
            pose = _std(lean=0.08, hn=(0.36, -0.60), hf=(0.30, -0.58),
                        elbow=(0.0, 1.0))
            slot = ('hands', 0.40, 0.20)
        else:
            pose = _std(hn=(0.20, -0.56), hf=(0.16, -0.54),
                        elbow=(0.0, 1.0))
            slot = ('hands', 0.24, 0.22)
        return pose, back, front, marks, slot, extra
    if sc == 'pick':
        pose = _std(lean=0.04, hn=(0.20, -0.92), hf=(0.10, -0.58),
                    elbow=(-0.3, 0.9))
        slot = ('ahead', 0.14, 1.20)
        return pose, back, front, marks, slot, extra
    if sc == 'pour':
        pose = _std(lean=0.10, hn=(0.36, -0.64), hf=(0.14, -0.56),
                    elbow=(0.0, 1.0))
        slot = ('hand', 0.0, 0.24)
        return pose, back, front, marks, slot, extra
    if sc == 'fish':
        pose = dict(SEATED, hands={'n': (0.22, -0.56), 'f': (0.18, -0.54)},
                    elbow=(0.0, 1.0))
        back += _poly([(-0.30, -0.235), (0.40, -0.235), (0.40, -0.175),
                       (-0.30, -0.175)], C['wood'])
        back += _line([(0.30, -0.175), (0.30, 0.10)], C['wood'], 1.2)
        extra += _line([(0.12, -0.50), (1.10, -1.30)], C['wood'], 1.1)
        extra += _line([(1.10, -1.30), (1.24, 0.02)], PALE, 0.6)
        back += _poly([(0.40, -0.02), (1.8, -0.02), (1.8, 0.14),
                       (0.40, 0.14)], C['water'])
        return pose, back, front, marks, None, extra
    if sc == 'play':
        pose = _std(hn=(0.14, -0.52), hf=(0.14, -0.66), elbow=(0.0, 1.0))
        slot = ('hands', 0.14, 0.34)
        for k in range(2):
            marks += _circ(0.40 + k * 0.12, -0.96 - k * 0.08, 0.02, INK)
            marks += _line([(0.42 + k * 0.12, -0.96 - k * 0.08),
                            (0.42 + k * 0.12, -1.08 - k * 0.08)])
        return pose, back, front, marks, slot, extra
    if sc == 'open':
        pose = _std(lean=0.06, hn=(0.34, -0.50), hf=(-0.06, -0.42),
                    elbow=(0.0, 1.0))
        slot = ('ahead', 0.36, 1.10 if kind == 'door' else 0.40)
        return pose, back, front, marks, slot, extra
    if sc == 'talk':
        pose = _std(hn=(0.26, -0.62), hf=(-0.06, -0.44), elbow=(0.0, 1.0))
        for k in range(3):
            a = -0.5 + k * 0.5
            marks += _line([(0.22 + 0.04 * math.cos(a), -0.86 + 0.06 * a),
                            (0.30 + 0.06 * math.cos(a), -0.88 + 0.10 * a)],
                           INK, 0.7)
        return pose, back, front, marks, None, extra
    return None


def _xf_art(art, box):
    """Fit strokes (world coords) uniformly into a unit box: centred,
    bottom on the box bottom -> unit px strokes."""
    xs = [q[0] for a in art for q in a[0]]
    ys = [q[1] for a in art for q in a[0]]
    if not xs:
        return []
    aw, ah = max(1e-6, max(xs) - min(xs)), max(1e-6, max(ys) - min(ys))
    bw, bh = (box[2] - box[0]) * H, (box[3] - box[1]) * H
    k = min(bw / aw, bh / ah)
    ox = (box[0] + box[2]) / 2 * H - (min(xs) + max(xs)) / 2 * k
    oy = box[3] * H - max(ys) * k
    out = []
    for st in art:
        fl = st[3] if len(st) > 3 else False
        if isinstance(fl, tuple):
            fl = (fl[0], fl[1] * k)
        out.append(([(ox + q[0] * k, oy + q[1] * k) for q in st[0]],
                    st[1], st[2], fl))
    return out


def _slot_box(slot, anchors, aspect):
    kind, where, size = slot
    w = size * max(0.3, min(2.6, aspect))
    h = size
    if w > size * 1.4:
        h = size * 1.4 / max(0.3, aspect)
        w = size * 1.4
    if kind in ('hand', 'hands'):
        hx = anchors['hand_n'][0] / H
        hy = anchors['hand_n'][1] / H
        if kind == 'hands':
            hx = (anchors['hand_n'][0] + anchors['hand_f'][0]) / 2 / H
            hy = (anchors['hand_n'][1] + anchors['hand_f'][1]) / 2 / H
        return (hx - w / 2, hy - h * 0.55, hx + w / 2, hy + h * 0.45)
    if kind == 'ahead':
        x0 = where
        return (x0, -h, x0 + w, 0.0)
    if kind in ('surface', 'board', 'at'):
        cx, bot = where
        return (cx - w / 2, bot - h, cx + w / 2, bot)
    if kind == 'mount':
        w = size * max(0.8, min(1.8, aspect))
        h = w / max(0.8, min(1.8, aspect))
        return (-w / 2, -0.94 + 0.10, w / 2, 0.0) if h < 0.94 else \
            (-w / 2, -0.84, w / 2, 0.0)
    if kind == 'seat':
        return (-0.30, -0.24, 0.26, 0.0)
    return None


def _tint(art):
    """The dominant solid fill of a drawing, or None."""
    cnt = {}
    for st in art or ():
        if len(st) > 3 and st[3] == 'solid' and str(st[1]).startswith('#'):
            n = len(st[0])
            cnt[st[1]] = cnt.get(st[1], 0) + n
    return max(cnt, key=cnt.get) if cnt else None


def _backdrop(arts, strokes):
    """Setting art behind the picture: as tall as the apparatus + actor,
    standing on the ground past the far (facing) edge, overlapping it."""
    xs = [q[0] for s_ in strokes for q in s_[0]]
    ys = [q[1] for s_ in strokes for q in s_[0]]
    if not xs:
        return []
    out = []
    x_at = max(xs)
    for art in arts:
        pts = [q for a in art for q in a[0]]
        if not pts:
            continue
        ax = [q[0] for q in pts]
        ay = [q[1] for q in pts]
        asp = (max(ax) - min(ax)) / max(1e-6, max(ay) - min(ay))
        h = (max(0.0, max(ys)) - min(ys)) * 1.08
        w = h * asp
        box = (x_at - w * 0.45, max(0.0, max(ys)) - h, x_at + w * 0.55,
               max(0.0, max(ys)))
        out += _xf_art(art, box)
        x_at = box[2]
    return out


def _pts(strokes):
    return [q for st in strokes for q in st[0]]


def _bbox(strokes):
    q = _pts(strokes)
    if not q:
        return None
    return (min(p[0] for p in q), min(p[1] for p in q),
            max(p[0] for p in q), max(p[1] for p in q))


def _rot(strokes, c, a):
    ca, sa = math.cos(a), math.sin(a)
    return [([(c[0] + (x - c[0]) * ca - (y - c[1]) * sa,
               c[1] + (x - c[0]) * sa + (y - c[1]) * ca) for x, y in st[0]],)
            + tuple(st[1:]) for st in strokes]


def _shift(strokes, dx, dy=0.0):
    return [([(x + dx, y + dy) for x, y in st[0]],) + tuple(st[1:])
            for st in strokes]


def _at(art, cx, bot, h):
    """Art fitted to height h (unit px), bottom-centre at (cx, bot)."""
    bb = _bbox(art)
    if bb is None:
        return []
    asp = (bb[2] - bb[0]) / max(1e-6, bb[3] - bb[1])
    w = h * max(0.3, min(2.4, asp))
    return _xf_art(art, ((cx - w / 2) / H, (bot - h) / H,
                         (cx + w / 2) / H, bot / H))


def _outline(art):
    return [(st[0], st[1], st[2], False) for st in art
            if not (len(st) > 3 and st[3])]


def _frame_stroke(st, fb):
    bb = _bbox([st])
    return (bb[2] - bb[0] >= 0.9 * (fb[2] - fb[0])
            and bb[3] - bb[1] >= 0.9 * (fb[3] - fb[1]))


def _seg_dist(pts, c):
    best = float('inf')
    for a, b in zip(pts, pts[1:] or pts):
        vx, vy = b[0] - a[0], b[1] - a[1]
        t = 0.0 if not (vx or vy) else max(0.0, min(1.0, (
            (c[0] - a[0]) * vx + (c[1] - a[1]) * vy) / (vx * vx + vy * vy)))
        best = min(best, math.hypot(a[0] + t * vx - c[0],
                                    a[1] + t * vy - c[1]))
    return best


def _kettle():
    return (_poly([(0.0, 0.0), (0.30, 0.0), (0.34, -0.22), (0.26, -0.30),
                   (0.04, -0.30), (-0.04, -0.22)], C['metal'])
            + _line([(0.30, -0.14), (0.50, -0.30)], C['metal'], 1.4)
            + _line([(0.02, -0.26), (-0.10, -0.40), (0.14, -0.44)], INK, 0.9))


def _liquid(label):
    c = noun_cat(label) if label else ''
    return C['wood'] if c == 'drink' else C['water']


def _place_roles(sc, spec, pose, anch, body, obj, arts):
    """Draw the narrated things in the roles the sentence gives them.

    -> (behind, over, obj, contacts, placed) — strokes behind / over
    the figure, the (possibly re-posed) held object, role contacts
    (name, point, target) and {role: placed}."""
    behind, over, contacts, placed = [], [], [], {}
    roles = {r: lab for r, lab in (spec.get('roles') or {}).items()
             if lab and lab != spec.get('partner')
             and lab not in (spec.get('absorb') or ())
             and lab not in (spec.get('setting') or ())}
    if sc in _FLOW:
        if not obj:
            hx, hy = anch['hand_n']
            obj = _xf_art(_kettle(), ((hx - 0.2 * H) / H, (hy - 0.1 * H) / H,
                                      (hx + 0.2 * H) / H, (hy + 0.1 * H) / H))
        obj = _rot(obj, anch['hand_n'], 0.62)
        sp = max(_pts(obj), key=lambda q: q[0] - 0.2 * q[1])
        rim = (sp[0] + 0.03 * H, sp[1] + 0.16 * H)
        goal = arts.get('goal') if 'goal' in roles else None
        if goal:
            small = noun_cat(roles['goal']) in ('vessel', 'drink', 'food', '')
            gh = 0.17 * H if small else 0.42 * H
            bot = rim[1] + gh if small else 0.0
            if not small:
                rim = (rim[0], -gh)
            g = _at(goal, rim[0], bot, gh)
            gb = _bbox(g)
            if gb is not None:
                if small and bot < -0.2 * H:
                    behind += _table((gb[0] / H) - 0.12, (gb[2] / H) + 0.12,
                                     bot / H)
                behind += g
                rim = ((gb[0] + gb[2]) / 2, gb[1] + 0.02 * H)
                contacts.append(('stream', rim, (
                    min(max(rim[0], gb[0]), gb[2]), gb[1] + 0.02 * H)))
            placed['goal'] = bool(g)
        mid = ((sp[0] + rim[0]) / 2 + 0.02 * H, (sp[1] + rim[1]) / 2)
        over += [([sp, mid, rim], _liquid(roles.get('theme')), 1.3, False)]
        if 'theme' in roles:
            placed['theme'] = True
    vant = arts.get('vantage') if 'vantage' in roles else None
    vk = vantage_kind(roles.get('vantage')) if vant else ''
    if vant and vk == 'optic':
        ey = anch['eye']
        it = _at(vant, ey[0] + 0.10 * H, ey[1] + 0.07 * H, 0.16 * H)
        over += it
        placed['vantage'] = bool(it)
        vant = None
    elif vant and vk == 'place':
        bb = _bbox(body)
        it = _at(vant, (bb[0] + bb[2]) / 2 - 0.10 * H, 0.0, 1.05 * H)
        behind += it
        placed['vantage'] = bool(it)
        vant = None
    if vant:
        bb = _bbox(body)
        cx = (bb[0] + bb[2]) / 2
        top = bb[1] - 0.08 * H
        sill = anch['hip'][1] - 0.02 * H
        w = max(0.62 * H, (bb[2] - bb[0]) + 0.24 * H)
        fr = _outline(_xf_art(vant, ((cx - w / 2) / H, top / H,
                                     (cx + w / 2) / H, sill / H)))
        fb = _bbox(fr) or (cx - w / 2, top, cx + w / 2, sill)
        fr = [st for st in fr if _frame_stroke(st, fb) or
              _seg_dist(st[0], anch['head']) > anch['head_r'] * 1.15]
        x0, x1 = fb[0] - 0.10 * H, fb[2] + 0.10 * H
        wall = [([(x0, fb[3]), (x1, fb[3]), (x1, 0.0), (x0, 0.0),
                  (x0, fb[3])], '#E8E2D6', 0.8, 'solid'),
                ([(x0, fb[3]), (x1, fb[3]), (x1, 0.0), (x0, 0.0),
                  (x0, fb[3])], INK, 0.62, False)]
        over += wall + fr
        hd = anch['head']
        contacts.append(('view', hd, (min(max(hd[0], fb[0]), fb[2]),
                                      min(max(hd[1], fb[1]), fb[3]))))
        ob = _bbox(obj)
        if ob is not None and ob[0] < x1 + 0.10 * H:
            obj = _shift(obj, x1 + 0.10 * H - ob[0])
        placed['vantage'] = bool(fr)
    ins = arts.get('instrument') if 'instrument' in roles else None
    if ins:
        hx, hy = anch['hand_f']
        it = _at(ins, hx, hy + 0.10 * H, 0.22 * H)
        over += it
        placed['instrument'] = bool(it)
    allb = _bbox(behind + obj + body + over)
    for r in ('theme', 'goal', 'source'):
        if r not in roles or r in placed or not arts.get(r):
            continue
        h = 0.70 * H if sc in ('walk', 'run', 'hike', 'drive', 'ride',
                                'swim', 'crawl') else 0.45 * H
        g = _at(arts[r], 0.0, 0.0, h)
        gb = _bbox(g)
        if gb is None:
            placed[r] = False
            continue
        dx = (allb[0] - 0.06 * H - gb[2]) if r == 'source' else (
            allb[2] + 0.06 * H - gb[0])
        g = _shift(g, dx)
        behind += g
        allb = _bbox(behind + obj + body + over)
        placed[r] = True
    for r in roles:
        placed.setdefault(r, False)
    return behind, over, obj, contacts, placed


def compose(spec, partner_art=None, emotion='neutral', outfit=None,
            shirt=None, flip=False, backdrop=(), role_arts=None):
    """Draw an activity: apparatus + posed figure + narrated object.

    -> (strokes, marks, anchors, meta) in unit px, or None when the spec
    has no drawing. `meta` records the schema, contacts (name, point,
    target) and whether the partner art was placed."""
    sc = spec.get('schema')
    kind = spec.get('kind') or ''
    tool = spec.get('tool') or spec.get('lemma') or ''
    col = _tint(partner_art) if sc in ('drive', 'ride', 'row', 'glide') \
        else None
    got = _schema(sc, kind, col, tool)
    if got is None:
        return None
    pose, back, front, marks, slot, extra = got
    pose = dict(pose, hands=dict(pose['hands']), feet=dict(pose['feet']))
    pose = _settle(pose, sc in _SEATED_SCHEMAS)
    body, fmarks, anch = sb_cast.posed(pose, emotion, outfit, shirt)
    if sb_cast.EMOTIONS.get(emotion, ('',))[0] == 'holdhead' \
            and sc not in HAND_SCHEMAS:
        # a feeling that takes both hands to the head overrides free hands
        hx, hy = anch['head'][0] / sb_cast.H, anch['head'][1] / sb_cast.H
        hr = anch['head_r'] / sb_cast.H
        pose['hands'] = {'n': (hx + hr * 0.85, hy + hr * 0.15),
                         'f': (hx - hr * 0.75, hy + hr * 0.20)}
        body, fmarks, anch = sb_cast.posed(pose, emotion, outfit, shirt)
    if pose.get('knee_f'):
        # a far knee that rests on the ground (kneeling)
        body2, _m2, _a2 = sb_cast.posed(dict(pose, knee=pose['knee_f']),
                                        emotion, outfit, shirt)
        nf = sum(1 for st in body2 if st[1] == sb_cast.SHADE) + 2
        body = body2[:nf] + body[nf:]
    obj, placed = [], False
    if slot is not None and partner_art:
        xs = [q[0] for a in partner_art for q in a[0]]
        ys = [q[1] for a in partner_art for q in a[0]]
        asp = (max(xs) - min(xs)) / max(1e-6, max(ys) - min(ys)) if xs \
            else 1.0
        box = _slot_box(slot, anch, asp)
        if box is not None:
            obj = _xf_art(partner_art, box)
            placed = bool(obj)
    if slot is not None and slot[0] == 'seat' and not placed:
        back = back + _chair()
    r_back, r_over, obj, r_con, r_placed = _place_roles(
        sc, spec, pose, anch, body, obj, role_arts or {})
    if sc in _FLOW:
        placed = True
    back = back + r_back
    extra = extra + r_over
    if slot is not None and slot[0] in ('mount', 'seat'):
        strokes = back + obj + body + front + extra
    elif slot is not None and slot[0] in ('hand', 'hands'):
        strokes = back + body + front + obj + extra
    else:
        strokes = back + obj + body + front + extra
    if backdrop:
        strokes = _backdrop(backdrop, strokes) + strokes
    contacts = [('hand_n', anch['hand_n'], _u([pose['hands']['n']])[0]),
                ('hand_f', anch['hand_f'], _u([pose['hands']['f']])[0]),
                ('foot_n', anch['foot_n'], _u([pose['feet']['n']])[0]),
                ('foot_f', anch['foot_f'], _u([pose['feet']['f']])[0])]
    contacts += r_con
    if flip:
        def mx(pts):
            return [(-x, y) for x, y in pts]
        strokes = [(mx(s[0]),) + tuple(s[1:]) for s in strokes]
        marks = [(mx(s[0]),) + tuple(s[1:]) for s in marks + fmarks]
        anch = {k: ((-v[0], v[1]) if isinstance(v, tuple) else v)
                for k, v in anch.items()}
        contacts = [(n, (-a[0], a[1]), (-t[0], t[1])) for n, a, t in contacts]
    else:
        marks = marks + fmarks
    meta = {'schema': sc, 'kind': kind, 'contacts': contacts,
            'placed': placed, 'slot': slot[0] if slot else None,
            'backdrop': len(backdrop), 'roles': r_placed,
            'partner': spec.get('partner'), 'via': spec.get('via')}
    return strokes, marks, anch, meta


def contact_error(meta):
    """Worst hand/foot miss against its target, in figure heights."""
    worst = 0.0
    for _n, a, t in meta.get('contacts', ()):
        worst = max(worst, math.hypot(a[0] - t[0], a[1] - t[1]) / H)
    return worst


SCHEMAS = ('drive', 'ride', 'row', 'climb', 'hike', 'walk', 'run', 'carry',
           'glide', 'crawl', 'swim', 'jump', 'dance', 'push', 'pull', 'lift',
           'throw', 'kick', 'desk', 'sit_drink', 'sit_read', 'craft', 'sit', 'drink',
           'eat', 'lie', 'kneel', 'plant', 'dig', 'cook', 'cut', 'wipe',
           'fix', 'strike', 'board', 'paint', 'point', 'read', 'phone',
           'photo', 'look', 'give', 'hold', 'pick', 'pour', 'fish', 'play',
           'open', 'talk')


def _hand_slot(sc):
    got = _schema(sc, '', None, '')
    return bool(got and got[4] and got[4][0] in ('hand', 'hands'))


# schemas whose narrated object is carried in the hands
HAND_SCHEMAS = frozenset(sc for sc in SCHEMAS if _hand_slot(sc))
