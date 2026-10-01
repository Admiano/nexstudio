/**
 * Builds the cast manifests, the facet index and the browser registry from the
 * archetype source table below. Re-runnable and deterministic:
 *   node tools/build-cast-manifests.js
 */
'use strict';
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const MANIFESTS = path.join(ROOT, 'manifests');
const CAST_DIR = path.join(MANIFESTS, 'cast');
const RELEASE = '1.0.0';

const VIEW_AXES = ['front', 'three-quarter-left', 'three-quarter-right', 'profile-left', 'profile-right', 'back-left', 'back-right', 'back'];
const PAPER_STYLES = ['clean-editorial', 'handmade-scrapbook', 'technical-notebook', 'bold-paper-collage'];
const ASPECT_RATIOS = ['16:9', '1:1', '9:16'];

const ARCHETYPES = [
  {
    slug: 'presenter', name: 'Presenter', role: 'presenter', ageBand: 'adult', proportion: 'adult-average', formality: 'smart-casual',
    intents: ['capture_attention', 'introduce_topic', 'narrate', 'reveal_content'],
    keywords: ['presenter', 'host', 'narrator', 'speaker', 'introduction'],
    useCases: ['explainer', 'agent', 'creator', 'documentary'],
    personalities: ['confident', 'warm', 'cheerful'],
    poses: ['address-audience', 'explain-open-hands', 'present-to-content', 'point-at-detail', 'idle-stance', 'celebrate-lift'],
    look: { skin: '#dda87c', hair: { color: '#2f2a26', length: 0.28 }, top: { color: '#3f6b7d', sleeve: 0.62 }, bottom: { color: '#2d3742' }, shoes: { color: '#23231f' }, accent: '#d98032' }
  },
  {
    slug: 'teacher', name: 'Teacher', role: 'teacher', ageBand: 'adult', proportion: 'adult-average', formality: 'smart-casual',
    intents: ['explain_concept', 'teach_step', 'guide_attention', 'compare_options'],
    keywords: ['teacher', 'tutor', 'lesson', 'classroom', 'instructor', 'explain'],
    useCases: ['explainer', 'education', 'documentary'],
    personalities: ['calm', 'warm', 'authoritative'],
    poses: ['explain-open-hands', 'present-to-content', 'point-at-detail', 'address-audience', 'listen-attentive'],
    look: { skin: '#c1895f', hair: { color: '#5a3a22', length: 0.42 }, top: { color: '#7a5c8f', sleeve: 0.7 }, bottom: { color: '#3b3a44' }, shoes: { color: '#332b26' }, accent: '#e2b23c' }
  },
  {
    slug: 'student', name: 'Student', role: 'student', ageBand: 'teen', proportion: 'teen', formality: 'casual',
    intents: ['receive_information', 'ask_question', 'show_progress', 'react'],
    keywords: ['student', 'learner', 'class', 'study', 'question', 'homework'],
    useCases: ['explainer', 'education'],
    personalities: ['curious', 'shy', 'energetic'],
    poses: ['listen-attentive', 'think-considering', 'work-at-surface', 'walk-stride', 'celebrate-lift'],
    look: { skin: '#f0c9a4', hair: { color: '#8c6239', length: 0.5 }, top: { color: '#c65f4a', sleeve: 0.4 }, bottom: { color: '#41506b' }, shoes: { color: '#ddd8d0' }, accent: '#5aa9a3' }
  },
  {
    slug: 'child', name: 'Child', role: 'child', ageBand: 'child', proportion: 'child', formality: 'casual',
    intents: ['react', 'play', 'receive_information', 'show_wonder'],
    keywords: ['child', 'kid', 'young', 'pupil', 'playful'],
    useCases: ['explainer', 'education', 'family'],
    personalities: ['playful', 'cheerful', 'curious'],
    poses: ['idle-stance', 'celebrate-lift', 'listen-attentive', 'walk-stride', 'think-considering'],
    look: { skin: '#9a6440', hair: { color: '#2f2a26', length: 0.2 }, top: { color: '#e0a33c', sleeve: 0.35 }, bottom: { color: '#4a6b53' }, shoes: { color: '#c7443a' }, accent: '#4a6b53' }
  },
  {
    slug: 'executive', name: 'Executive', role: 'executive', ageBand: 'adult', proportion: 'adult-tall', formality: 'formal',
    intents: ['state_decision', 'set_direction', 'approve_outcome', 'address_stakeholders'],
    keywords: ['executive', 'leader', 'director', 'boardroom', 'decision', 'strategy'],
    useCases: ['business', 'agent', 'commerce'],
    personalities: ['authoritative', 'serious', 'confident'],
    poses: ['address-audience', 'present-to-content', 'idle-stance', 'listen-attentive', 'hand-over'],
    look: { skin: '#6f4630', hair: { color: '#2f2a26', length: 0.18 }, top: { color: '#2b3550', sleeve: 0.92 }, bottom: { color: '#222a3c' }, shoes: { color: '#1b1b1b' }, accent: '#b8903f' }
  },
  {
    slug: 'office-worker', name: 'Office worker', role: 'office_worker', ageBand: 'adult', proportion: 'adult-average', formality: 'business-casual',
    intents: ['show_work', 'process_task', 'collaborate', 'report_status'],
    keywords: ['office', 'worker', 'desk', 'admin', 'workflow', 'colleague'],
    useCases: ['business', 'agent', 'explainer'],
    personalities: ['calm', 'reserved', 'cheerful'],
    poses: ['work-at-surface', 'sit-and-talk', 'listen-attentive', 'hand-over', 'idle-stance'],
    look: { skin: '#dda87c', hair: { color: '#5a3a22', length: 0.24 }, top: { color: '#5f7f8c', sleeve: 0.85 }, bottom: { color: '#39414d' }, shoes: { color: '#2a2622' }, accent: '#8fa8b5' }
  },
  {
    slug: 'creator', name: 'Creator', role: 'creator', ageBand: 'adult', proportion: 'adult-slight', formality: 'casual',
    intents: ['make_content', 'show_craft', 'demonstrate', 'publish_result'],
    keywords: ['creator', 'maker', 'designer', 'studio', 'camera', 'editing'],
    useCases: ['creator', 'explainer', 'agent'],
    personalities: ['energetic', 'playful', 'confident'],
    poses: ['work-at-surface', 'present-to-content', 'explain-open-hands', 'celebrate-lift', 'walk-stride'],
    look: { skin: '#c1895f', hair: { color: '#b0462f', length: 0.55 }, top: { color: '#2f6f5e', sleeve: 0.45 }, bottom: { color: '#2f3440' }, shoes: { color: '#e4ded4' }, accent: '#e8734a' }
  },
  {
    slug: 'technician', name: 'Technician', role: 'technician', ageBand: 'adult', proportion: 'adult-broad', formality: 'workwear',
    intents: ['diagnose', 'repair', 'operate_device', 'investigate'],
    keywords: ['technician', 'engineer', 'repair', 'machine', 'maintenance', 'diagnostic'],
    useCases: ['industrial', 'explainer', 'documentary'],
    personalities: ['serious', 'calm', 'reserved'],
    poses: ['inspect-crouch', 'work-at-surface', 'point-at-detail', 'carry-load', 'idle-stance'],
    look: { skin: '#9a6440', hair: { color: '#2f2a26', length: 0.16 }, top: { color: '#3e6b8a', sleeve: 0.9 }, bottom: { color: '#3a4149' }, shoes: { color: '#25201c' }, accent: '#f0a92b' }
  },
  {
    slug: 'healthcare-worker', name: 'Healthcare worker', role: 'healthcare_worker', ageBand: 'adult', proportion: 'adult-average', formality: 'uniform',
    intents: ['care_for_person', 'explain_procedure', 'reassure', 'record_observation'],
    keywords: ['healthcare', 'nurse', 'clinician', 'doctor', 'patient', 'clinic'],
    useCases: ['healthcare', 'explainer', 'documentary'],
    personalities: ['warm', 'calm', 'authoritative'],
    poses: ['listen-attentive', 'explain-open-hands', 'work-at-surface', 'hand-over', 'idle-stance'],
    look: { skin: '#f0c9a4', hair: { color: '#d8d3cc', length: 0.26 }, top: { color: '#e8ece9', sleeve: 0.6 }, bottom: { color: '#4f7f76' }, shoes: { color: '#f2f0ea' }, accent: '#3f8f7f' }
  },
  {
    slug: 'builder', name: 'Builder', role: 'builder', ageBand: 'adult', proportion: 'adult-broad', formality: 'workwear',
    intents: ['construct', 'move_material', 'show_effort', 'deliver'],
    keywords: ['builder', 'construction', 'site', 'lifting', 'trade', 'assembly'],
    useCases: ['industrial', 'explainer'],
    personalities: ['energetic', 'confident', 'serious'],
    poses: ['carry-load', 'inspect-crouch', 'walk-stride', 'point-at-detail', 'idle-stance'],
    look: { skin: '#6f4630', hair: { color: '#2f2a26', length: 0.14 }, top: { color: '#d8862c', sleeve: 0.5 }, bottom: { color: '#4a4f57' }, shoes: { color: '#2d2419' }, accent: '#f2c744' }
  },
  {
    slug: 'parent', name: 'Parent', role: 'parent', ageBand: 'adult', proportion: 'adult-average', formality: 'casual',
    intents: ['support_other_character', 'decide_for_family', 'reassure', 'compare_options'],
    keywords: ['parent', 'family', 'home', 'guardian', 'household'],
    useCases: ['family', 'commerce', 'explainer'],
    personalities: ['warm', 'calm', 'cheerful'],
    poses: ['listen-attentive', 'explain-open-hands', 'hand-over', 'walk-stride', 'idle-stance'],
    look: { skin: '#dda87c', hair: { color: '#8c6239', length: 0.46 }, top: { color: '#a8574f', sleeve: 0.52 }, bottom: { color: '#39445a' }, shoes: { color: '#6b5a4a' }, accent: '#e2a04a' }
  },
  {
    slug: 'customer', name: 'Customer', role: 'customer', ageBand: 'adult', proportion: 'adult-average', formality: 'casual',
    intents: ['evaluate_option', 'buy', 'ask_question', 'react'],
    keywords: ['customer', 'shopper', 'buyer', 'client', 'checkout', 'store'],
    useCases: ['commerce', 'explainer', 'business'],
    personalities: ['curious', 'cheerful', 'reserved'],
    poses: ['think-considering', 'listen-attentive', 'walk-stride', 'celebrate-lift', 'idle-stance'],
    look: { skin: '#c1895f', hair: { color: '#2f2a26', length: 0.36 }, top: { color: '#5c6f3f', sleeve: 0.42 }, bottom: { color: '#454a55' }, shoes: { color: '#d8d2c8' }, accent: '#c96f4a' }
  },
  {
    slug: 'support-helper', name: 'Support helper', role: 'helper', ageBand: 'adult', proportion: 'adult-slight', formality: 'business-casual',
    intents: ['resolve_issue', 'guide_user', 'reassure', 'handoff'],
    keywords: ['support', 'helper', 'service', 'assist', 'agent', 'guide'],
    useCases: ['agent', 'business', 'explainer'],
    personalities: ['warm', 'calm', 'cheerful'],
    poses: ['explain-open-hands', 'hand-over', 'work-at-surface', 'listen-attentive', 'idle-stance'],
    look: { skin: '#9a6440', hair: { color: '#2f2a26', length: 0.3 }, top: { color: '#4b6fae', sleeve: 0.68 }, bottom: { color: '#333b47' }, shoes: { color: '#2b2b2b' }, accent: '#6fb3c9' }
  },
  {
    slug: 'salesperson', name: 'Salesperson', role: 'salesperson', ageBand: 'adult', proportion: 'adult-tall', formality: 'business-casual',
    intents: ['pitch_offer', 'demonstrate', 'compare_options', 'close_deal'],
    keywords: ['sales', 'pitch', 'offer', 'demo', 'deal', 'retail'],
    useCases: ['commerce', 'business', 'agent'],
    personalities: ['confident', 'cheerful', 'energetic'],
    poses: ['present-to-content', 'address-audience', 'hand-over', 'point-at-detail', 'celebrate-lift'],
    look: { skin: '#f0c9a4', hair: { color: '#5a3a22', length: 0.22 }, top: { color: '#7e4b6d', sleeve: 0.88 }, bottom: { color: '#2e3340' }, shoes: { color: '#1f1c1a' }, accent: '#e6b352' }
  },
  {
    slug: 'peer-friend', name: 'Peer', role: 'friend', ageBand: 'adult', proportion: 'adult-slight', formality: 'casual',
    intents: ['converse', 'react', 'support_other_character', 'collaborate'],
    keywords: ['friend', 'peer', 'colleague', 'conversation', 'partner'],
    useCases: ['explainer', 'creator', 'family'],
    personalities: ['cheerful', 'playful', 'warm'],
    poses: ['sit-and-talk', 'listen-attentive', 'explain-open-hands', 'walk-stride', 'idle-stance'],
    look: { skin: '#dda87c', hair: { color: '#c9a227', length: 0.4 }, top: { color: '#3d7f6f', sleeve: 0.38 }, bottom: { color: '#3f4553' }, shoes: { color: '#e6e0d6' }, accent: '#d97b5e' }
  },
  {
    slug: 'mentor', name: 'Mentor', role: 'mentor', ageBand: 'senior', proportion: 'senior', formality: 'smart-casual',
    intents: ['advise', 'reflect', 'teach_step', 'set_direction'],
    keywords: ['mentor', 'senior', 'advisor', 'experience', 'coach', 'veteran'],
    useCases: ['documentary', 'business', 'education'],
    personalities: ['calm', 'authoritative', 'warm'],
    poses: ['think-considering', 'explain-open-hands', 'sit-and-talk', 'listen-attentive', 'idle-stance'],
    look: { skin: '#c1895f', hair: { color: '#d8d3cc', length: 0.2 }, top: { color: '#6a6f5c', sleeve: 0.9 }, bottom: { color: '#454038' }, shoes: { color: '#3a2f27' }, accent: '#a8763f' }
  },
  {
    slug: 'analyst', name: 'Analyst', role: 'analyst', ageBand: 'adult', proportion: 'adult-average', formality: 'business-casual',
    intents: ['show_data', 'compare_options', 'report_status', 'investigate'],
    keywords: ['analyst', 'data', 'report', 'chart', 'metrics', 'research'],
    useCases: ['business', 'agent', 'documentary'],
    personalities: ['serious', 'calm', 'curious'],
    poses: ['point-at-detail', 'present-to-content', 'work-at-surface', 'think-considering', 'idle-stance'],
    look: { skin: '#6f4630', hair: { color: '#2f2a26', length: 0.34 }, top: { color: '#46536b', sleeve: 0.82 }, bottom: { color: '#2f3540' }, shoes: { color: '#262320' }, accent: '#5fa8d3' }
  },
  {
    slug: 'field-reporter', name: 'Field reporter', role: 'reporter', ageBand: 'adult', proportion: 'adult-average', formality: 'smart-casual',
    intents: ['narrate', 'investigate', 'interview', 'move_through_story'],
    keywords: ['reporter', 'journalist', 'documentary', 'interview', 'field', 'story'],
    useCases: ['documentary', 'explainer', 'creator'],
    personalities: ['curious', 'confident', 'serious'],
    poses: ['walk-stride', 'address-audience', 'sit-and-talk', 'turn-away', 'listen-attentive'],
    look: { skin: '#dda87c', hair: { color: '#5a3a22', length: 0.32 }, top: { color: '#8a6a45', sleeve: 0.72 }, bottom: { color: '#3c4148' }, shoes: { color: '#42352a' }, accent: '#c9542f' }
  }
];

const poseLibrary = JSON.parse(fs.readFileSync(path.join(MANIFESTS, 'pose-library.json'), 'utf8'));
const poseIds = new Set(poseLibrary.poses.map((p) => p.id));

function manifestFor(archetype) {
  const unknown = archetype.poses.filter((p) => !poseIds.has(p));
  if (unknown.length) throw new Error(`${archetype.slug} references unknown poses: ${unknown.join(', ')}`);
  return {
    id: `cast.${archetype.slug}.paper-01`,
    name: archetype.name,
    version: RELEASE,
    category: 'cast-character',
    subtype: archetype.role,
    slug: archetype.slug,
    renderer: 'paper-cast-figure',
    role: archetype.role,
    ageBand: archetype.ageBand,
    proportion: archetype.proportion,
    formality: archetype.formality,
    intents: archetype.intents,
    keywords: [...new Set(['character', 'cast', 'paper', archetype.role, ...archetype.keywords])],
    useCases: archetype.useCases,
    personalities: archetype.personalities,
    paperStyles: PAPER_STYLES,
    aspectRatios: ASPECT_RATIOS,
    viewAxes: VIEW_AXES,
    defaultViewAxis: 'three-quarter-right',
    motionEnergy: [...new Set(archetype.poses.flatMap((id) => poseLibrary.poses.find((p) => p.id === id).energy))],
    poses: archetype.poses,
    defaultPose: archetype.poses[0],
    duration: { minimum: 2, recommended: 6, maximum: 14 },
    look: archetype.look,
    slots: {
      name: { type: 'string', maxCharacters: 32 },
      line: { type: 'string', maxCharacters: 120 },
      prop: { type: 'string', maximumItems: 1, replaceable: true }
    },
    compatibleMotions: ['cast-settle', 'cast-gesture', 'cast-turn', 'cast-walk'],
    compatibleTransitions: ['page-turn', 'paper-wipe', 'torn-paper-reveal', 'collage-push'],
    soundTags: [`cast.${archetype.role}`, 'paper.character.settle', 'paper.cutout.move'],
    themeTokens: ['--paper-bg', '--paper-surface', '--ink', '--ink-muted', '--primary', '--secondary', '--accent', '--shadow-color', '--shadow-opacity', '--grain-opacity', '--outline-width'],
    accessibilityLabel: `${archetype.name} paper cut-out character, orientation and pose resolved from script context`,
    agentSelection: {
      useWhen: archetype.intents,
      storyRole: archetype.role,
      avoidWhen: ['no_character_in_script', 'view_axis_unsupported']
    }
  };
}

function build() {
  fs.mkdirSync(CAST_DIR, { recursive: true });
  for (const file of fs.readdirSync(CAST_DIR)) if (file.endsWith('.json')) fs.unlinkSync(path.join(CAST_DIR, file));

  const manifests = ARCHETYPES.map(manifestFor);
  for (const manifest of manifests) fs.writeFileSync(path.join(CAST_DIR, `${manifest.id}.json`), `${JSON.stringify(manifest, null, 2)}\n`);

  const index = {
    schemaVersion: '1.0.0',
    release: RELEASE,
    generatedBy: 'tools/build-cast-manifests.js',
    count: manifests.length,
    entries: manifests
  };
  fs.writeFileSync(path.join(MANIFESTS, 'cast-index.json'), `${JSON.stringify(index, null, 2)}\n`);

  const facets = {
    schemaVersion: '1.0.0',
    release: RELEASE,
    roles: [...new Set(manifests.map((m) => m.role))].sort(),
    ageBands: [...new Set(manifests.map((m) => m.ageBand))].sort(),
    proportions: [...new Set(manifests.map((m) => m.proportion))].sort(),
    formality: [...new Set(manifests.map((m) => m.formality))].sort(),
    personalities: [...new Set(manifests.flatMap((m) => m.personalities))].sort(),
    useCases: [...new Set(manifests.flatMap((m) => m.useCases))].sort(),
    intents: [...new Set(manifests.flatMap((m) => m.intents))].sort(),
    viewAxes: VIEW_AXES,
    paperStyles: PAPER_STYLES,
    aspectRatios: ASPECT_RATIOS,
    poses: poseLibrary.poses.map((p) => ({ id: p.id, intents: p.intents, gestureTags: p.gestureTags, energy: p.energy, viewAxes: p.viewAxes, requiresFacingTarget: !!p.requiresFacingTarget }))
  };
  fs.writeFileSync(path.join(MANIFESTS, 'cast-facets.json'), `${JSON.stringify(facets, null, 2)}\n`);

  const registry = `/* Generated by tools/build-cast-manifests.js — do not edit by hand. */\n(function (root) {\n  const registry = ${JSON.stringify({ release: RELEASE, entries: manifests }, null, 2)};\n  const facets = ${JSON.stringify(facets, null, 2)};\n  const poses = ${JSON.stringify(poseLibrary, null, 2)};\n  const api = { registry, facets, poses };\n  if (typeof module === 'object' && module.exports) module.exports = api;\n  root.NEX_CAST = registry;\n  root.NEX_CAST_FACETS = facets;\n  root.NEX_CAST_POSES = poses;\n})(typeof globalThis !== 'undefined' ? globalThis : this);\n`;
  fs.writeFileSync(path.join(ROOT, 'runtime', 'cast-registry.js'), registry);

  console.log(JSON.stringify({ characters: manifests.length, poses: poseLibrary.poses.length, viewAxes: VIEW_AXES.length }));
}

build();
