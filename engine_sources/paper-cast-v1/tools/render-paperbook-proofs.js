#!/usr/bin/env node
/**
 * Renders the three proof spreads for the parametric cast:
 *   1. an adult rowing, with the hands solved onto the oar shaft
 *   2. an adult carrying a child on the back
 *   3. a toddler mid-step, held by an adult hand
 *
 * Usage: node tools/render-paperbook-proofs.js [outDir]
 */
const fs = require('fs');
const path = require('path');
const Rig = require('../runtime/paper-cast-rig.js');
const Body = require('../runtime/cast-body.js');
const Contact = require('../runtime/cast-contact.js');
const Relation = require('../runtime/cast-relation.js');
const Paperbook = require('../runtime/paperbook-figure.js');

const out = path.resolve(process.argv[2] || path.join(__dirname, '..', 'proofs'));
fs.mkdirSync(out, { recursive: true });

const ADULT_LOOK = {
  skin: '#b07a50',
  hair: { color: '#241c17', style: 'bun' },
  top: { color: '#7d9cab', sleeve: 0.35 },
  bottom: { garment: 'wrapper', color: '#c9b08a', pattern: 'diamond', patternColor: '#a2512a', patternScale: 0.045 },
  shoes: { color: '#3d342b' }
};

const CHILD_LOOK = {
  skin: '#b07a50',
  hair: { color: '#241c17', style: 'tuft' },
  top: { color: '#c08a4e', sleeve: 0.25 },
  bottom: { garment: 'shorts', color: '#6b7f6a' },
  shoes: { bare: true }
};

const write = (name, svg) => {
  const file = path.join(out, `${name}.svg`);
  fs.writeFileSync(file, svg);
  return file;
};

/** 1. Rowing: an oar is a prop with contact anchors, and both hands land on it. */
function rowing() {
  const proportion = Body.body({ age: 32, build: 'average' });
  // Oar shaft in body-local units, running from the near hip up and forward.
  const oar = { id: 'oar', anchors: { 'grip-inboard': { x: -0.03, y: 0.13, z: 0.2 }, 'grip-outboard': { x: 0.07, y: 0.09, z: 0.3 } } };
  const relation = Relation.relate('grip-prop', {
    actor: { proportion, yaw: 34 },
    propId: 'oar',
    grips: [
      { effector: 'leftHand', at: Contact.anchor(oar, 'grip-inboard') },
      { effector: 'rightHand', at: Contact.anchor(oar, 'grip-outboard') }
    ],
    height: 900
  });
  const actor = relation.participants[0];
  const figure = Rig.build({ proportion: actor.proportion, height: actor.height, pose: actor.pose, view: actor.yaw });
  const scene = Paperbook.render(figure, { look: ADULT_LOOK, id: 'rower' });
  const joints = figure.joints;
  // Draw the oar through the two solved grips so the contact is visible.
  const a = joints.leftHand;
  const b = joints.rightHand;
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const shaft = `<line x1="${a.x - dx * 1.1}" y1="${a.y - dy * 1.1}" x2="${b.x + dx * 3.8}" y2="${b.y + dy * 3.8}" stroke="#8a6a44" stroke-width="${figure.height * 0.016}" stroke-linecap="round"/>`;
  const svg = scene.svg.replace('</svg>', `${shaft}</svg>`);
  return { name: 'proof-rowing', svg, residual: relation.residual };
}

/** 2. Carrying: two bodies, the grip solved against the other body's knees. */
function carry() {
  const relation = Relation.relate('carry-on-back', {
    carrier: { body: { age: 31, build: 'average' }, yaw: 72 },
    carried: { body: { age: 3 }, yaw: 72 },
    height: 900
  });
  const scene = Paperbook.renderRelation(relation, { looks: { carrier: ADULT_LOOK, carried: CHILD_LOOK } });
  return { name: 'proof-carry-on-back', svg: scene.svg, residual: relation.residual };
}

/** 3. Learning to walk: toddler proportions, mid-step balance, one held hand. */
function supportedWalk() {
  const relation = Relation.relate('support-walk', {
    adult: { body: { age: 29, build: 'slight' }, yaw: 20 },
    toddler: { body: { age: 1.4 }, yaw: 12 },
    side: 'right',
    height: 900
  });
  const scene = Paperbook.renderRelation(relation, { looks: { adult: ADULT_LOOK, toddler: CHILD_LOOK } });
  return { name: 'proof-supported-walk', svg: scene.svg, residual: relation.residual };
}

for (const proof of [rowing(), carry(), supportedWalk()]) {
  const file = write(proof.name, proof.svg);
  console.log(`${proof.name}: contact residual ${(proof.residual * 100).toFixed(1)}% of figure height -> ${path.relative(process.cwd(), file)}`);
}
