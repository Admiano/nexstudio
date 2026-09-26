'use strict';

/*
 * NexStick Cast V1 — Phase F Role + Casting Resolver
 * Semantic layer only. Does not mutate body geometry, clothing geometry,
 * motion/performance, personality parameters, scene layout, or storyboard.
 */

const VERSION = '1.0.0';
const ROLE_DOC = require('../ROLE_PRESETS_V1.json');

const FAMILY_TRAITS = Object.freeze({
  adult_man_average:   { age_group: 'adult', gender_affinity: 'male',    morphology: 'average' },
  adult_man_broad:     { age_group: 'adult', gender_affinity: 'male',    morphology: 'broad' },
  adult_woman_average: { age_group: 'adult', gender_affinity: 'female',  morphology: 'average' },
  adult_woman_tall:    { age_group: 'adult', gender_affinity: 'female',  morphology: 'tall' },
  boy:                 { age_group: 'child', gender_affinity: 'male',    morphology: 'average' },
  girl:                { age_group: 'child', gender_affinity: 'female',  morphology: 'average' },
  diminutive_man:      { age_group: 'adult', gender_affinity: 'male',    morphology: 'diminutive' },
  diminutive_woman:    { age_group: 'adult', gender_affinity: 'female',  morphology: 'diminutive' },
  diminutive_boy:      { age_group: 'child', gender_affinity: 'male',    morphology: 'diminutive' },
  diminutive_girl:     { age_group: 'child', gender_affinity: 'female',  morphology: 'diminutive' },
  neutral_adult:       { age_group: 'adult', gender_affinity: 'neutral', morphology: 'neutral' },
  neutral_child:       { age_group: 'child', gender_affinity: 'neutral', morphology: 'neutral' }
});

const ROLES = new Map(ROLE_DOC.roles.map(r => [r.role_id, r]));
const ROLE_ALIASES = [
  ['healthcare_worker', /\b(?:healthcare worker|health care worker|medical worker)\b/],
  ['office_worker', /\b(?:office worker|office workers)\b/],
  ['salesperson', /\b(?:salesperson|salespeople|sales person|sales people|seller)\b/],
  ['presenter', /\b(?:presenter|presenters)\b/],
  ['teacher', /\b(?:teacher|teachers)\b/],
  ['student', /\b(?:student|students|learner|learners)\b/],
  ['executive', /\b(?:executive|executives)\b/],
  ['creator', /\b(?:creator|creators)\b/],
  ['technician', /\b(?:technician|technicians)\b/],
  ['builder', /\b(?:builder|builders)\b/],
  ['customer', /\b(?:customer|customers|shopper|shoppers|client|clients)\b/],
  ['helper', /\b(?:helper|helpers|assistant|assistants)\b/],
  ['friend', /\b(?:friend|friends)\b/],
  ['parent', /\b(?:parent|parents|father|fathers|mother|mothers|dad|dads|mom|moms|mum|mums)\b/],
  ['child', /\b(?:child|children|daughter|daughters|son|sons|boy|boys|girl|girls)\b/]
];

const COUNT_WORDS = Object.freeze({
  one:1, two:2, three:3, four:4, five:5, six:6, seven:7, eight:8,
  nine:9, ten:10, eleven:11, twelve:12
});

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function contract() {
  return {
    name: 'NexStickCastResolverV1',
    version: VERSION,
    phase: 'F',
    scope: 'semantic-role-and-casting-presets',
    owns: [
      'role presets',
      'cast request normalization',
      'family candidate compatibility ranking',
      'clothing tag recommendations',
      'accessory tag recommendations',
      'personality preset recommendations',
      'role behavior metadata'
    ],
    doesNotOwn: [
      'body geometry',
      'clothing geometry',
      'motion engine',
      'performance sampling',
      'personality engine parameters',
      'scene layout',
      'storyboard',
      'camera',
      'Director composition'
    ],
    deterministic: true,
    randomCasting: false,
    demographicPolicy: 'explicit constraints filter; underspecified demographics remain ranked candidates'
  };
}

function inferCount(text) {
  const n = text.match(/\b(\d{1,2})\b/);
  if (n) return Math.max(1, Math.min(64, Number(n[1])));
  for (const [word, value] of Object.entries(COUNT_WORDS)) {
    if (new RegExp(`\\b${word}\\b`).test(text)) return value;
  }
  return 1;
}

function inferRole(text) {
  for (const [role, re] of ROLE_ALIASES) if (re.test(text)) return role;
  return null;
}

function inferGender(text) {
  if (/\b(?:female|woman|women|girl|girls|daughter|daughters|mother|mothers|mom|moms|mum|mums)\b/.test(text)) return 'female';
  if (/\b(?:male|man|men|boy|boys|son|sons|father|fathers|dad|dads)\b/.test(text)) return 'male';
  if (/\b(?:neutral|gender neutral|gender-neutral)\b/.test(text)) return 'neutral';
  return null;
}

function inferAge(text) {
  if (/\b(?:child|children|boy|boys|girl|girls|daughter|daughters|son|sons)\b/.test(text)) return 'child';
  if (/\b(?:adult|adults|woman|women|man|men|father|fathers|mother|mothers|parent|parents)\b/.test(text)) return 'adult';
  return null;
}

function inferMorphology(text) {
  if (/\bdiminutive\b/.test(text)) return 'diminutive';
  if (/\bbroad\b/.test(text)) return 'broad';
  if (/\btall\b/.test(text)) return 'tall';
  if (/\baverage\b/.test(text)) return 'average';
  if (/\bneutral\b/.test(text)) return 'neutral';
  return null;
}

function relationLabel(text) {
  if (/\b(?:father|dad)\b/.test(text)) return 'father';
  if (/\b(?:mother|mom|mum)\b/.test(text)) return 'mother';
  if (/\bdaughter\b/.test(text)) return 'daughter';
  if (/\bson\b/.test(text)) return 'son';
  return null;
}

function parseSegment(segment, index) {
  const text = segment.trim().toLowerCase().replace(/[_-]+/g, ' ');
  const role = inferRole(text);
  if (!role) return { error: `No supported role found in segment: ${segment}` };
  const slot = {
    slot_id: `slot_${index + 1}`,
    count: inferCount(text),
    role
  };
  const gender = inferGender(text);
  const age_group = inferAge(text);
  const morphology = inferMorphology(text);
  const label = relationLabel(text);
  if (gender) slot.gender = gender;
  if (age_group) slot.age_group = age_group;
  if (morphology) slot.morphology = morphology;
  if (label) slot.relation_label = label;
  return { slot };
}

function inferRelations(slots) {
  if (slots.length !== 2) return [];
  const [a,b] = slots;
  const pair = new Set([a.role, b.role]);
  if (pair.has('parent') && pair.has('child')) {
    const parent = a.role === 'parent' ? a : b;
    const child = a.role === 'child' ? a : b;
    return [{ type:'parent_child', from_slot:parent.slot_id, to_slot:child.slot_id, metadata:{} }];
  }
  if (pair.has('teacher') && pair.has('student')) {
    const teacher = a.role === 'teacher' ? a : b;
    const student = a.role === 'student' ? a : b;
    return [{ type:'teacher_student', from_slot:teacher.slot_id, to_slot:student.slot_id, metadata:{} }];
  }
  if (pair.has('salesperson') && pair.has('customer')) {
    const seller = a.role === 'salesperson' ? a : b;
    const customer = a.role === 'customer' ? a : b;
    return [{ type:'service', from_slot:seller.slot_id, to_slot:customer.slot_id, metadata:{} }];
  }
  if (a.role === 'friend' && b.role === 'friend') {
    return [{ type:'friendship', from_slot:a.slot_id, to_slot:b.slot_id, metadata:{} }];
  }
  return [];
}

function parseTextRequest(input) {
  if (typeof input !== 'string' || !input.trim()) throw new Error('Cast request text must be a non-empty string');
  const source = input.trim();
  const text = source.toLowerCase();
  if (/\bmixed\s+business\s+team\b/.test(text)) {
    return {
      schema_version: VERSION,
      source_text: source,
      group_template: {
        template_id: 'business_team',
        roles: ['office_worker', 'executive', 'creator', 'salesperson'],
        diversity_intent: 'mixed',
        count_required: true
      }
    };
  }

  let parts;
  if (text.includes('+')) parts = source.split(/\s*\+\s*/);
  else if (/\b(?:father|mother|parent|friend|teacher|customer)\b.*\band\b.*\b(?:daughter(?:s)?|son(?:s)?|child(?:ren)?|friend(?:s)?|student(?:s)?|salesperson|salespeople)\b/i.test(source)) parts = source.split(/\s+and\s+/i);
  else parts = [source];

  const slots = [];
  const errors = [];
  parts.filter(Boolean).forEach((part, i) => {
    const parsed = parseSegment(part, i);
    if (parsed.error) errors.push(parsed.error);
    else slots.push(parsed.slot);
  });
  if (errors.length) return { schema_version: VERSION, source_text: source, parse_errors: errors, slots };
  return {
    schema_version: VERSION,
    source_text: source,
    slots,
    relations: inferRelations(slots)
  };
}

function normalizeRequest(input) {
  if (typeof input === 'string') return parseTextRequest(input);
  if (!input || typeof input !== 'object' || Array.isArray(input)) throw new Error('CastRequest must be a string or object');
  if ((!input.slots || !input.slots.length) && !input.group_template && input.source_text) {
    const parsed = parseTextRequest(input.source_text);
    if (input.request_id) parsed.request_id = input.request_id;
    return parsed;
  }
  const out = clone(input);
  if (!out.schema_version) out.schema_version = VERSION;
  return out;
}

function familyAllowedByExplicitGender(familyId, gender, familyWasExplicit) {
  if (!gender || familyWasExplicit) return true;
  const affinity = FAMILY_TRAITS[familyId].gender_affinity;
  return affinity === gender || affinity === 'neutral';
}

function familyScore(familyId, slot, role) {
  const traits = FAMILY_TRAITS[familyId];
  let score = 80;
  const reasons = [];
  if (role.compatible_families.includes(familyId)) {
    score += 20;
    reasons.push('role_default_compatible_family');
  } else {
    reasons.push('outside_role_default_compatibility');
  }

  if (role.demographic_policy.age.mode === 'preferred') {
    if (role.demographic_policy.age.groups.includes(traits.age_group)) {
      score += 20;
      reasons.push('role_age_preference');
    }
  }
  if (slot.age_group && traits.age_group === slot.age_group) {
    score += 30;
    reasons.push('explicit_age_match');
  }
  if (slot.gender) {
    if (traits.gender_affinity === slot.gender) {
      score += 30;
      reasons.push('explicit_gender_affinity_match');
    } else if (traits.gender_affinity === 'neutral') {
      score += 15;
      reasons.push('neutral_family_compatible_with_explicit_gender');
    } else if (slot.family === familyId) {
      reasons.push('explicit_family_preserved_despite_gender_affinity');
    }
  }
  if (slot.morphology && traits.morphology === slot.morphology) {
    score += 30;
    reasons.push('explicit_morphology_match');
  }
  if (slot.family === familyId) {
    score += 100;
    reasons.push('explicit_family');
  }
  return { score, reasons };
}

function validateRoleAge(role, traits) {
  const age = role.demographic_policy.age;
  if (age.mode !== 'required') return true;
  return age.groups.includes(traits.age_group);
}

function candidateFamilies(slot, role) {
  const familyWasExplicit = Boolean(slot.family);
  let pool = familyWasExplicit ? [slot.family] : Object.keys(FAMILY_TRAITS);
  const warnings = [];

  if (slot.family && !FAMILY_TRAITS[slot.family]) {
    return { candidates: [], warnings: [`Unknown family: ${slot.family}`] };
  }

  if (slot.family && !role.compatible_families.includes(slot.family)) {
    warnings.push('explicit_family_outside_role_default_compatibility_preserved_for_evaluation');
  }

  pool = pool.filter(id => FAMILY_TRAITS[id]);
  pool = pool.filter(id => validateRoleAge(role, FAMILY_TRAITS[id]));
  if (slot.age_group) pool = pool.filter(id => FAMILY_TRAITS[id].age_group === slot.age_group);
  if (slot.morphology) pool = pool.filter(id => FAMILY_TRAITS[id].morphology === slot.morphology);
  if (slot.gender) pool = pool.filter(id => familyAllowedByExplicitGender(id, slot.gender, familyWasExplicit));

  if (!familyWasExplicit && (slot.age_group || slot.gender || slot.morphology) && pool.some(id => !role.compatible_families.includes(id))) {
    warnings.push('explicit_constraints_expand_beyond_role_default_compatibility');
  }

  const candidates = pool.map(id => {
    const traits = FAMILY_TRAITS[id];
    const scored = familyScore(id, slot, role);
    return {
      family_id: id,
      score: scored.score,
      rank_group: scored.score,
      traits: clone(traits),
      reasons: scored.reasons
    };
  }).sort((a,b) => (b.score - a.score) || a.family_id.localeCompare(b.family_id));

  return { candidates, warnings };
}

function recommendations(slot, role) {
  return {
    clothing: slot.clothing_tag ? {
      selection_mode: 'explicit', selected_tag: slot.clothing_tag, ranked_tags: [slot.clothing_tag]
    } : {
      selection_mode: 'recommended', selected_tag: null, ranked_tags: role.clothing_tags.slice()
    },
    accessories: slot.accessory_tags && slot.accessory_tags.length ? {
      selection_mode: 'explicit', selected_tags: slot.accessory_tags.slice(), ranked_tags: slot.accessory_tags.slice()
    } : {
      selection_mode: 'recommended', selected_tags: [], ranked_tags: role.accessory_tags.slice()
    },
    personality: slot.personality ? {
      selection_mode: 'explicit', selected_preset: slot.personality, ranked_presets: [slot.personality]
    } : {
      selection_mode: 'recommended', selected_preset: null, ranked_presets: role.personality_defaults.slice()
    }
  };
}

function makeCastSpec(slot, role, candidate, recs) {
  return {
    schema_version: VERSION,
    role: role.role_id,
    family: candidate.family_id,
    count: slot.count,
    age_group: slot.age_group || candidate.traits.age_group,
    gender: slot.gender || null,
    family_gender_affinity: candidate.traits.gender_affinity,
    morphology: slot.morphology || candidate.traits.morphology,
    clothing: clone(recs.clothing),
    accessories: clone(recs.accessories),
    personality: clone(recs.personality),
    behavior_tags: role.behavior_tags.slice(),
    gesture_tendencies: role.gesture_tendencies.slice(),
    presentation_stance: role.presentation_stance.slice(),
    context_metadata: clone(role.context_metadata),
    relation_label: slot.relation_label || null,
    engine_bindings: {
      body_family_id: candidate.family_id,
      clothing_geometry: 'UNRESOLVED_BY_PHASE_F',
      personality_parameters: 'UNRESOLVED_BY_PHASE_F',
      motion_engine: 'NexPerformanceEngineV4FreeMax'
    }
  };
}

function resolveSlot(slot) {
  const role = ROLES.get(slot.role);
  if (!role) {
    return { slot_id: slot.slot_id, count: slot.count, role: slot.role, status:'INVALID_ROLE', candidates:[], warnings:[`Unsupported role: ${slot.role}`] };
  }
  const recs = recommendations(slot, role);
  const { candidates, warnings } = candidateFamilies(slot, role);
  if (!candidates.length) {
    return {
      slot_id: slot.slot_id,
      count: slot.count,
      role: slot.role,
      status: 'NO_COMPATIBLE_CANDIDATE',
      resolution_mode: 'none',
      candidates: [],
      recommendations: recs,
      warnings: warnings.concat('No family satisfies the explicit request and required role age semantics.')
    };
  }

  const enriched = candidates.map(c => ({ ...c, cast_spec: makeCastSpec(slot, role, c, recs) }));
  const final = enriched.length === 1;
  return {
    slot_id: slot.slot_id,
    count: slot.count,
    role: slot.role,
    status: final ? 'RESOLVED' : 'RANKED_CANDIDATES',
    resolution_mode: final ? 'final_cast_spec' : 'ranked_candidates',
    candidate_order_policy: 'score_desc_then_family_id_lexical; equal-score lexical order is serialization only, not demographic preference',
    final_cast_spec: final ? clone(enriched[0].cast_spec) : null,
    candidates: enriched,
    recommendations: recs,
    member_assignment_policy: slot.count > 1 ? 'resolve_each_member_from_same_ranked_candidate_set_without_inventing_demographics' : 'single_member',
    warnings
  };
}

function resolveGroupTemplate(request) {
  const gt = request.group_template;
  if (!gt || gt.template_id !== 'business_team') {
    return {
      resolver_version: VERSION,
      deterministic: true,
      status: 'INVALID_REQUEST',
      request: clone(request),
      slots: [],
      warnings: ['Unsupported group template.']
    };
  }
  return {
    resolver_version: VERSION,
    deterministic: true,
    status: 'NEEDS_SPECIFICATION',
    request: clone(request),
    group_resolution: {
      template_id: 'business_team',
      count_required: true,
      recognized_roles: gt.roles.slice(),
      diversity_intent: gt.diversity_intent,
      demographic_assignment: 'unresolved',
      policy: 'mixed does not authorize guessing gender, age, or body family; Director may later compose resolved members but Phase F does not choose scene layout'
    },
    slots: [],
    relations: [],
    warnings: ['Business-team intent recognized; member count and demographic constraints remain unspecified.']
  };
}

function resolve(input) {
  const request = normalizeRequest(input);
  if (request.group_template) return resolveGroupTemplate(request);
  if (request.parse_errors && request.parse_errors.length) {
    return {
      resolver_version: VERSION,
      deterministic: true,
      status: 'INVALID_REQUEST',
      request: clone(request),
      slots: [],
      relations: request.relations || [],
      warnings: request.parse_errors.slice()
    };
  }
  if (!Array.isArray(request.slots) || !request.slots.length) {
    return {
      resolver_version: VERSION,
      deterministic: true,
      status: 'INVALID_REQUEST',
      request: clone(request),
      slots: [],
      relations: [],
      warnings: ['CastRequest requires at least one slot or a supported group template.']
    };
  }

  const normalizedSlots = request.slots.map((slot, i) => ({
    slot_id: slot.slot_id || `slot_${i + 1}`,
    count: Number.isInteger(slot.count) ? slot.count : 1,
    ...clone(slot)
  }));
  const slots = normalizedSlots.map(resolveSlot);
  let status = 'RESOLVED';
  if (slots.some(s => s.status === 'INVALID_ROLE' || s.status === 'NO_COMPATIBLE_CANDIDATE')) status = 'INVALID_REQUEST';
  else if (slots.some(s => s.status === 'RANKED_CANDIDATES')) status = 'RANKED_CANDIDATES';

  return {
    resolver_version: VERSION,
    deterministic: true,
    status,
    request: { ...clone(request), slots: normalizedSlots },
    slots,
    relations: clone(request.relations || inferRelations(normalizedSlots)),
    director_handoff: {
      scene_layout: 'NOT_SELECTED_BY_PHASE_F',
      storyboard: 'NOT_SELECTED_BY_PHASE_F',
      cast_resolution_only: true
    },
    warnings: slots.flatMap(s => s.warnings || [])
  };
}

module.exports = {
  version: VERSION,
  contract,
  parseTextRequest,
  normalizeRequest,
  resolve,
  familyTraits: clone(FAMILY_TRAITS),
  rolePresets: clone(ROLE_DOC.roles)
};
