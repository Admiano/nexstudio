#!/usr/bin/env node
/**
 * Renders the proof sheet for the world, acting and face layers:
 *   1. anchored relations — sitting, leaning, working, reaching, handing over,
 *      hand in hand, kneeling to pick something up, each staged against a
 *      drawn feature so the contact can be judged by eye
 *   2. one gesture across its four phases, so the acting is visible as acting
 *   3. the face states, including a blink and a spoken line
 *
 * Usage: node tools/render-acting-sheet.js [outDir]
 */
const fs = require('fs');
const path = require('path');
const World = require('../runtime/cast-world.js');
const Relation = require('../runtime/cast-relation.js');
const Acting = require('../runtime/cast-acting.js');
const Face = require('../runtime/cast-face.js');
const Paperbook = require('../runtime/paperbook-figure.js');

const out = path.resolve(process.argv[2] || path.join(__dirname, '..', 'proofs'));
fs.mkdirSync(out, { recursive: true });

// Trousers rather than a wrapper: a floor-length skirt hides exactly the
// legs a seated or kneeling proof exists to show.
const LOOK = {
  skin: '#b07a50',
  hair: { color: '#241c17', style: 'bun' },
  top: { garment: 'tunic', color: '#7d9cab', sleeve: 0.4 },
  bottom: { garment: 'trousers', color: '#7a6a52' },
  shoes: { color: '#3d342b' }
};
const SECOND = { ...LOOK, skin: '#8a5a38', top: { garment: 'shirt', color: '#b4694a', sleeve: 0.9 }, bottom: { garment: 'trousers', color: '#4d5a63' } };

// One feature per proof: a spread staged with every piece of furniture at
// once tells you nothing about which one the character is using.
const stage = (feature) => World.scene({ features: [feature] });

const looksFor = (relation) => {
  const looks = {};
  relation.participants.forEach((p, i) => { looks[p.id] = i === 0 ? LOOK : SECOND; });
  return looks;
};

const staged = [
  ['sits on a chair', 'sit-on', { id: 'chair', kind: 'chair', facing: 20 }, (s) => ({ feature: s.get('chair'), face: { emotion: 'thoughtful' } })],
  ['leans on a counter', 'lean-on', { id: 'counter', kind: 'counter', at: { z: 0.5 }, facing: 180 }, (s) => ({ feature: s.get('counter') })],
  ['works at a table', 'work-at-table', { id: 'table', kind: 'table', at: { z: 0.5 }, facing: 180 }, (s) => ({ feature: s.get('table') })],
  ['reaches a shelf', 'reach-to', { id: 'shelf', kind: 'shelf', at: { x: 0.1, z: -0.4 }, facing: 0 }, (s) => ({ feature: s.get('shelf'), at: 'shelf.reach' })],
  ['kneels to pick up', 'pick-up', null, () => ({ at: { x: 0.06, y: 0.05, z: 0.26 }, kneel: true, yaw: 35 })],
  ['hands something over', 'hand-over', null, () => ({ giver: {}, receiver: { body: { age: 9 } } })],
  ['hand in hand', 'hold-hands', null, () => ({ left: {}, right: { body: { age: 6 } } })],
  ['shakes hands', 'shake-hands', null, () => ({})]
];

const cells = [];
for (const [label, kind, feature, build] of staged) {
  const scene = feature ? stage(feature) : null;
  const spec = { height: 760, scene, ...build(scene || { get: () => null }) };
  const relation = Relation.relate(kind, spec);
  const drawn = Paperbook.renderRelation(relation, { scene: spec.scene, looks: looksFor(relation), faces: spec.face ? { [relation.participants[0].id]: spec.face } : {} });
  cells.push({ label: `${label} — ${(relation.residual * 100).toFixed(1)}%`, svg: drawn.svg });
  fs.writeFileSync(path.join(out, `world-${kind}.svg`), drawn.svg);
}

// One gesture, four phases: the point of the acting layer is that these are
// four different drawings of the same beat.
const act = Acting.perform({ id: 'adanna', beats: [{ at: 0.4, kind: 'point', target: { x: 0.24, y: 0.34, z: 0.3 }, say: 'over there', emotion: 'attentive' }] });
const phases = [];
for (let t = 0; t <= act.duration; t += 0.02) {
  const f = act.at(t);
  if (!phases.some((p) => p.phase === f.phase)) phases.push({ phase: f.phase, t });
}
for (const step of phases) {
  const f = act.at(step.t + 0.08);
  const drawn = Paperbook.renderPose({ height: 700, pose: f.pose, view: 'three-quarter-right', look: LOOK, face: f.face, id: `act-${step.phase}` });
  cells.push({ label: `${step.phase} @ ${step.t.toFixed(2)}s`, svg: drawn.svg });
  fs.writeFileSync(path.join(out, `acting-${step.phase}.svg`), drawn.svg);
}

// Faces, drawn on the same head so only the state differs.
const faceStates = [
  ['neutral', { emotion: 'neutral' }],
  ['attentive', { emotion: 'attentive', gaze: 'left' }],
  ['warm', { emotion: 'warm' }],
  ['joy', { emotion: 'joy' }],
  ['concern', { emotion: 'concern' }],
  ['surprise', { emotion: 'surprise' }],
  ['stern', { emotion: 'stern' }],
  ['tired', { emotion: 'tired' }],
  ['listening', { emotion: 'attentive', listening: true, gaze: 'right' }],
  ['speaking', { emotion: 'warm', speaking: true, viseme: 'ah' }],
  ['blink', { emotion: 'neutral', eyeOpen: 0 }]
];
for (const [label, spec] of faceStates) {
  const drawn = Paperbook.renderPose({ height: 700, view: 'front', look: LOOK, face: Face.state(spec), id: `face-${label}` });
  // Cropped to the head: at spread scale these states are a few pixels
  // across, and the point of the sheet is to be able to judge them.
  const head = drawn.figure.parts.find((p) => p.kind === 'head');
  const r = head.radius * 1.9;
  const box = `${(head.center.x - r).toFixed(1)} ${(head.center.y - r).toFixed(1)} ${(r * 2).toFixed(1)} ${(r * 2).toFixed(1)}`;
  cells.push({ label: `face: ${label}`, svg: drawn.svg.replace(/viewBox="[^"]+"/, `viewBox="${box}"`) });
  fs.writeFileSync(path.join(out, `face-${label}.svg`), drawn.svg);
}

const html = `<!doctype html>
<meta charset="utf-8">
<title>Paper Cast — world, acting and face proofs</title>
<style>
  body { background: #2c2823; color: #efe7d8; font: 14px/1.4 system-ui, sans-serif; margin: 24px; }
  h1 { font-weight: 600; font-size: 18px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 14px; }
  figure { margin: 0; background: #efe7d8; border-radius: 6px; padding: 8px; }
  figure svg { width: 100%; height: 260px; }
  figcaption { color: #3a3028; font-size: 12px; margin-top: 6px; }
</style>
<h1>Paper Cast — anchored relations, gesture phases, face states</h1>
<div class="grid">
${cells.map((c) => `<figure>${c.svg}<figcaption>${c.label}</figcaption></figure>`).join('\n')}
</div>
`;
const sheet = path.join(out, 'acting-sheet.html');
fs.writeFileSync(sheet, html);
console.log(`${cells.length} proofs -> ${path.relative(process.cwd(), sheet)}`);
