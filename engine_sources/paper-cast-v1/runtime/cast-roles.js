/**
 * NexStudio Paper Cast — role vocabulary
 *
 * Turns the words a story is written in — "a fireman", "a waiter serving
 * food", "an elderly farmer", "a woman in a hijab carrying groceries" — into
 * the things the artist layer understands: a body, a look, a prop and a hold.
 * Without this an author picks hex codes; with it a script line picks an
 * outfit, and the same line always picks the same one.
 *
 * Deliberately not a classifier. It is a vocabulary: word → drawing decision,
 * inspectable and extendable, and it says when it did not recognise anything
 * rather than guessing a fireman.
 */
(function (root, factory) {
  const isNode = typeof module === 'object' && module.exports;
  const deps = isNode
    ? { Props: require('./cast-props.js') }
    : { Props: root.NexCastProps };
  const api = factory(deps);
  if (isNode) module.exports = api;
  root.NexCastRoles = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function ({ Props }) {
  /** Skin is a spectrum; these are named stops on it, not categories of person. */
  const SKIN = {
    porcelain: '#f2d5b4',
    light: '#f0cfa8',
    tan: '#dda87c',
    olive: '#c9975f',
    brown: '#a8713f',
    'deep-brown': '#8a5730',
    deep: '#6d452c'
  };

  const HAIR = { black: '#241c17', brown: '#4a3524', grey: '#8d8578', white: '#d6cdbd', auburn: '#6b3b26' };

  /**
   * Occupations. Each is garment + trim + headwear + prop + how it stands.
   * Colours are defaults an author can override; the silhouette is the part
   * that carries the meaning.
   */
  const ROLES = {
    firefighter: {
      words: ['firefighter', 'fireman', 'firewoman', 'fire fighter', 'fire officer', 'fire crew'],
      look: {
        head: { kind: 'helmet', color: '#b4462a', trimColor: '#8d3520' },
        top: { garment: 'coverall', color: '#c25a34', trim: ['collar', 'belt', 'band'], bandColor: '#f2d64b' },
        shoes: { color: '#241f1c' }
      },
      prop: 'hose',
      stance: 'brace'
    },
    'police-officer': {
      words: ['police officer', 'policeman', 'policewoman', 'police', 'constable', 'officer'],
      look: {
        head: { kind: 'cap', color: '#2b3a52', trimColor: '#1b2430' },
        top: { garment: 'shirt', color: '#38547a', trim: ['collar', 'placket', 'belt', 'badge'], trimColor: '#22334c' },
        bottom: { color: '#2b3340' },
        shoes: { color: '#241f1c' }
      },
      prop: 'notebook'
    },
    farmer: {
      words: ['farmer', 'farmhand', 'peasant', 'grower', 'cultivator'],
      look: {
        head: { kind: 'hat', color: '#c9a86a', trimColor: '#a98a4f' },
        top: { garment: 'shirt', color: '#8a7a4e', sleeve: 0.45, trimColor: '#5f5334' },
        bottom: { color: '#5d5445' },
        shoes: { color: '#4a3b2c' }
      },
      prop: 'hoe',
      stance: 'work'
    },
    waiter: {
      words: ['waiter', 'waitress', 'server', 'serving food', 'serves food', 'restaurant worker', 'steward'],
      look: {
        top: { garment: 'shirt', color: '#f4f1ea', trim: ['collar', 'placket'], trimColor: '#2b2621' },
        over: { kind: 'waist-apron', color: '#33413f' },
        bottom: { color: '#241f1c' },
        shoes: { color: '#1e1a17' }
      },
      prop: 'tray'
    },
    cook: {
      words: ['cook', 'chef', 'kitchen hand', 'baker'],
      look: {
        head: { kind: 'kufi', color: '#f4f1ea' },
        top: { garment: 'jacket', color: '#f4f1ea', trim: ['collar', 'placket'], trimColor: '#c9c2b2' },
        over: { kind: 'apron', color: '#e8e0cd' },
        bottom: { color: '#6b6258' }
      },
      prop: 'plate'
    },
    nurse: {
      words: ['nurse', 'midwife', 'health worker', 'carer'],
      look: {
        top: { garment: 'coverall', color: '#6fa89b', trim: ['collar', 'placket', 'badge'], trimColor: '#43766c', badgeColor: '#f2f0e6' },
        shoes: { color: '#efe7d8' }
      },
      prop: 'notebook'
    },
    doctor: {
      words: ['doctor', 'physician', 'surgeon'],
      look: {
        top: { garment: 'coat', color: '#f4f1ea', trim: ['lapel', 'placket', 'badge'], trimColor: '#cfc7b6' },
        bottom: { color: '#4d5a66' }
      },
      prop: 'notebook'
    },
    teacher: {
      words: ['teacher', 'tutor', 'lecturer', 'headmistress', 'headmaster'],
      look: {
        top: { garment: 'shirt', color: '#8a7ba8', trim: ['collar', 'placket'], trimColor: '#5b4f74' },
        bottom: { color: '#3f4550' }
      },
      prop: 'book'
    },
    'market-trader': {
      words: ['market trader', 'market seller', 'trader', 'vendor', 'hawker', 'stallholder', 'selling'],
      look: {
        head: { kind: 'headtie', color: '#c9542f', trimColor: '#a03f22' },
        top: { garment: 'tunic', color: '#d98a3c' },
        bottom: { garment: 'wrapper', color: '#c9b08a', pattern: 'diamond', patternColor: '#a2512a' }
      },
      prop: 'basket'
    },
    'construction-worker': {
      words: ['construction worker', 'builder', 'labourer', 'laborer', 'mason', 'bricklayer'],
      look: {
        head: { kind: 'helmet', color: '#e0b13c', trimColor: '#b98f28' },
        top: { garment: 'shirt', color: '#5f7b8a', trim: ['collar', 'band'], bandColor: '#f2d64b' },
        bottom: { color: '#6b6258' },
        shoes: { color: '#3b322a' }
      },
      prop: 'crate'
    },
    cleaner: {
      words: ['cleaner', 'janitor', 'sweeper', 'caretaker'],
      look: {
        head: { kind: 'headtie', color: '#7b93a8' },
        top: { garment: 'coverall', color: '#7b93a8', trim: ['collar', 'belt'] }
      },
      prop: 'broom'
    },
    shopper: {
      words: ['carrying groceries', 'with groceries', 'shopping', 'shopper', 'carrying shopping', 'from the market'],
      look: { top: { garment: 'shirt', color: '#a8687a', trimColor: '#7d4655' }, bottom: { color: '#4a4f5c' } },
      prop: 'grocery-bag'
    },
    fisherman: {
      words: ['fisherman', 'fisherwoman', 'rower', 'boatman', 'paddler', 'rowing'],
      look: {
        top: { garment: 'tunic', color: '#7d9cab' },
        bottom: { garment: 'trousers', color: '#8a7f6a' }
      },
      prop: 'oar'
    },
    gardener: {
      words: ['gardener', 'watering', 'planting'],
      look: { head: { kind: 'hat', color: '#b7a377' }, top: { garment: 'shirt', color: '#6f8b6a' }, bottom: { color: '#5d5445' } },
      prop: 'watering-can'
    },
    student: {
      words: ['student', 'pupil', 'schoolgirl', 'schoolboy', 'schoolchild'],
      look: { top: { garment: 'shirt', color: '#8ea7c4', trim: ['collar'] }, bottom: { color: '#3f4550' } },
      prop: 'book',
      body: { age: 11 }
    },
    // The fallback everyone lands on. It has to be the plainest thing in the
    // book: no wrapper, no uniform, nothing a story did not ask for.
    villager: {
      words: ['villager', 'neighbour', 'neighbor', 'passer-by', 'woman', 'man', 'person'],
      look: { top: { garment: 'tunic', color: '#7d9cab' }, bottom: { garment: 'trousers', color: '#5d5445' } },
      prop: null
    }
  };

  /**
   * Everything that is not an occupation: age, body, dress, faith, hair.
   * A modifier only overrides what it names, so "an elderly Muslim farmer"
   * keeps the farmer's hoe and shirt and changes the head and the body.
   */
  const MODIFIERS = {
    infant: { words: ['infant', 'baby'], body: { age: 0.6 } },
    toddler: { words: ['toddler'], body: { age: 1.5 } },
    child: { words: ['child', 'kid', 'young boy', 'young girl', 'little boy', 'little girl'], body: { age: 7 } },
    teenager: { words: ['teenager', 'teenage', 'adolescent'], body: { age: 15 } },
    elderly: { words: ['elderly', 'old ', 'older', 'grandmother', 'grandfather', 'granny', 'grandma', 'grandpa', 'senior'], body: { age: 72 }, look: { hair: { color: HAIR.white } } },
    heavy: { words: ['obese', 'heavy', 'heavyset', 'large man', 'large woman', 'fat', 'big-bodied', 'plus size'], body: { mass: 0.85 } },
    stout: { words: ['stocky', 'stout', 'burly', 'thickset'], body: { mass: 0.45, build: 'broad' } },
    slim: { words: ['slim', 'slender', 'thin', 'skinny', 'wiry'], body: { build: 'slight' } },
    tall: { words: ['tall'], body: { build: 'tall' } },

    // Dress and faith: drawn as the garment people actually wear, not as a
    // skin swatch. A word here changes a silhouette, never a complexion.
    hijab: { words: ['hijab', 'headscarf', 'muslim woman', 'veiled'], look: { head: { kind: 'hijab', color: '#7b5a86' }, top: { garment: 'robe', color: '#6d4a63' }, bottom: { garment: 'trousers', pattern: null } } },
    abaya: { words: ['abaya', 'jilbab'], look: { head: { kind: 'hijab', color: '#3f3a4a' }, top: { garment: 'robe', color: '#2f2b38' }, bottom: { garment: 'trousers', pattern: null } } },
    kufi: { words: ['kufi', 'muslim man', 'imam'], look: { head: { kind: 'kufi', color: '#e8e0cd' }, top: { garment: 'kurta', color: '#f0ece0' }, bottom: { garment: 'trousers', color: '#e6dfd0', pattern: null }, hair: { beard: true } } },
    turban: { words: ['turban', 'sikh'], look: { head: { kind: 'turban', color: '#d8973c' }, hair: { beard: true } } },
    // Garment modifiers restate the lower body too: inheriting a role's
    // wrapper under a kurta or a robe dresses the character twice.
    kurta: { words: ['kurta', 'indian man', 'sherwani'], look: { top: { garment: 'kurta', color: '#e6dfd0', trimColor: '#b9ab92' }, bottom: { garment: 'trousers', color: '#ddd6c6', pattern: null } } },
    sari: { words: ['sari', 'saree', 'indian woman'], look: { top: { garment: 'dress', color: '#b8465e' }, bottom: { garment: 'wrapper', color: '#b8465e', pattern: 'dots', patternColor: '#e8c65a' }, hair: { style: 'bun', color: HAIR.black } } },
    headtie: { words: ['headtie', 'gele', 'head wrap', 'headwrap'], look: { head: { kind: 'headtie', color: '#c9542f' } } },
    robe: { words: ['robe', 'agbada', 'kaftan', 'boubou'], look: { top: { garment: 'robe', color: '#d9c48a' }, bottom: { garment: 'trousers', pattern: null } } },
    dress: { words: ['dress', 'frock'], look: { top: { garment: 'dress', color: '#a8687a' }, bottom: { garment: 'trousers', pattern: null } } },
    wrapper: { words: ['wrapper', 'wrapper skirt', 'in a wrapper'], look: { bottom: { garment: 'wrapper', color: '#c9b08a', pattern: 'diamond', patternColor: '#a2512a' } } },
    apron: { words: ['apron'], look: { over: { kind: 'apron', color: '#33413f' } } },

    // Complexion words only set complexion, and sit at the end of the chain
    // so they never carry a garment or an occupation with them.
    black: { words: ['black', 'african', 'nigerian', 'ghanaian', 'kenyan', 'dark-skinned'], look: { skin: SKIN.deep, hair: { style: 'coils', color: HAIR.black } } },
    brown: { words: ['indian', 'south asian', 'pakistani', 'bangladeshi', 'brown-skinned'], look: { skin: SKIN.brown, hair: { color: HAIR.black } } },
    'middle-eastern': { words: ['arab', 'middle eastern', 'egyptian', 'moroccan'], look: { skin: SKIN.olive, hair: { color: HAIR.black } } },
    white: { words: ['white', 'european', 'caucasian', 'pale'], look: { skin: SKIN.light, hair: { color: HAIR.brown } } },
    'east-asian': { words: ['chinese', 'japanese', 'korean', 'east asian'], look: { skin: SKIN.porcelain, hair: { style: 'long', color: HAIR.black } } },

    bearded: { words: ['bearded', 'with a beard'], look: { hair: { beard: true } } },
    'shaved-head': { words: ['bald', 'shaven', 'shaved head'], look: { hair: { style: 'shaved' } } },
    afro: { words: ['afro'], look: { hair: { style: 'afro' } } },
    'long-hair': { words: ['long hair'], look: { hair: { style: 'long' } } },

    // Actions that change what is in the hands rather than who is holding it.
    carrying: { words: ['carrying groceries', 'with groceries', 'carrying shopping'], prop: 'grocery-bag' },
    'carrying-bags': { words: ['carrying bags', 'laden with bags', 'arms full of bags'], prop: 'shopping-bags' },
    serving: { words: ['serving food', 'serving', 'with a tray'], prop: 'tray' },
    sweeping: { words: ['sweeping', 'with a broom'], prop: 'broom' },
    reading: { words: ['reading', 'with a book'], prop: 'book' },
    'carrying-basket': { words: ['with a basket', 'carrying a basket'], prop: 'basket' },
    'carrying-crate': { words: ['carrying a crate', 'with a crate', 'carrying a box'], prop: 'crate' },
    rowing: { words: ['rowing', 'paddling', 'with an oar'], prop: 'oar' },
    'no-prop': { words: ['empty-handed', 'hands free'], prop: null }
  };

  /** Poses that go with the work, so a farmer is not standing to attention. */
  const STANCES = {
    neutral: {},
    work: { spine: { tilt: 8, swing: 0 }, chest: { tilt: 3, swing: 0 }, neck: { tilt: -5, swing: 0 }, legLeft: { hip: { tilt: 12, swing: 4 }, knee: { tilt: 10, swing: 0 } }, legRight: { hip: { tilt: -10, swing: 4 }, knee: { tilt: 6, swing: 0 } } },
    brace: { spine: { tilt: 6, swing: 0 }, legLeft: { hip: { tilt: 16, swing: 8 }, knee: { tilt: 16, swing: 0 } }, legRight: { hip: { tilt: -12, swing: 8 }, knee: { tilt: 8, swing: 0 } } },
    carry: { spine: { tilt: -3, swing: 0 }, legLeft: { hip: { tilt: 6, swing: 3 } }, legRight: { hip: { tilt: -4, swing: 3 } } }
  };

  const isObject = (v) => v && typeof v === 'object' && !Array.isArray(v);

  function merge(base, extra) {
    const out = { ...base };
    for (const [k, v] of Object.entries(extra || {})) {
      out[k] = isObject(v) && isObject(out[k]) ? merge(out[k], v) : v;
    }
    return out;
  }

  const norm = (text) => ` ${String(text || '').toLowerCase().replace(/[^a-z0-9\s-]/g, ' ').replace(/\s+/g, ' ').trim()} `;

  /** Longest phrase first, so "police officer" never matches as "officer". */
  const entries = (table) => Object.entries(table)
    .flatMap(([id, entry]) => entry.words.map((word) => ({ id, word: ` ${word.trim()} `, entry })))
    .sort((a, b) => b.word.length - a.word.length);

  const ROLE_WORDS = entries(ROLES);
  const MODIFIER_WORDS = entries(MODIFIERS);

  /**
   * Resolve a description into a drawable character.
   *
   *   resolve('an elderly Muslim woman carrying groceries')
   *   // -> { role: 'shopper', modifiers: ['elderly','hijab','carrying'],
   *   //      body: { age: 72, ... }, look: {...}, prop: 'grocery-bag' }
   *
   * @param {string} text
   * @param {{body?:object, look?:object, prop?:string|null, side?:string}} [overrides]
   */
  function resolve(text, overrides) {
    const hay = norm(text);
    const found = ROLE_WORDS.find((r) => hay.includes(r.word));
    const role = found ? found.entry : null;
    const applied = [];

    let body = merge({ age: 32 }, role && role.body);
    let look = merge({}, role && role.look);
    let prop = role ? role.prop : null;
    let stance = (role && role.stance) || 'neutral';

    for (const m of MODIFIER_WORDS) {
      if (!hay.includes(m.word) || applied.includes(m.id)) continue;
      applied.push(m.id);
      if (m.entry.body) body = merge(body, m.entry.body);
      if (m.entry.look) look = merge(look, m.entry.look);
      if ('prop' in m.entry) prop = m.entry.prop;
      if (m.entry.stance) stance = m.entry.stance;
    }

    const over = overrides || {};
    if (over.body) body = merge(body, over.body);
    if (over.look) look = merge(look, over.look);
    // `undefined` is "say nothing"; `null` is "put the prop down".
    if (over.prop !== undefined) prop = over.prop;

    if (prop && !Props.PROPS[prop]) prop = null;
    const hold = prop ? Props.holdOf(prop) : null;
    if (prop && stance === 'neutral' && hold && Object.keys(hold.hands).length > 1) stance = 'carry';

    return {
      text: String(text || ''),
      role: found ? found.id : null,
      recognised: Boolean(found),
      modifiers: applied,
      body,
      look,
      prop,
      side: over.side || 'right',
      stance,
      pose: STANCES[stance] || {},
      label: [found ? found.id.replace(/-/g, ' ') : 'character', prop ? `holding ${Props.PROPS[prop].label}` : null].filter(Boolean).join(', ')
    };
  }

  return { resolve, ROLES, MODIFIERS, STANCES, SKIN, HAIR, merge };
});
