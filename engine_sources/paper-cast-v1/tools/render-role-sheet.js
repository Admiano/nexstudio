#!/usr/bin/env node
/**
 * Renders a sheet of figures that differ in wardrobe, headwear and body mass
 * rather than in colour. The check it exists for is blunt: cover the labels
 * and the people should still be telling you what they do.
 *
 * Usage: node tools/render-role-sheet.js [outDir]
 */
const fs = require('fs');
const path = require('path');
const Body = require('../runtime/cast-body.js');
const Paperbook = require('../runtime/paperbook-figure.js');

const SHEET = [
  {
    id: 'fireman',
    label: 'fireman',
    body: { age: 36, build: 'broad' },
    look: {
      skin: '#dda87c',
      hair: { style: 'shaved', color: '#2b221c' },
      head: { kind: 'helmet', color: '#b4462a', trimColor: '#8d3520' },
      top: { garment: 'coverall', color: '#c25a34', trim: ['collar', 'belt', 'band'], trimColor: '#5a3a2a', bandColor: '#f2d64b' },
      shoes: { color: '#241f1c' }
    }
  },
  {
    id: 'police-officer',
    label: 'police officer',
    body: { age: 38 },
    look: {
      skin: '#6d452c',
      hair: { style: 'coils', color: '#1d1713' },
      head: { kind: 'cap', color: '#2b3a52', trimColor: '#1b2430' },
      top: { garment: 'shirt', color: '#38547a', trim: ['collar', 'placket', 'belt', 'badge'], trimColor: '#22334c' },
      bottom: { color: '#2b3340' },
      shoes: { color: '#241f1c' }
    }
  },
  {
    id: 'farmer',
    label: 'farmer',
    body: { age: 54, mass: 0.35 },
    look: {
      skin: '#98603c',
      hair: { style: 'shaved', color: '#6b6258', beard: true },
      head: { kind: 'hat', color: '#c9a86a', trimColor: '#a98a4f' },
      top: { garment: 'shirt', color: '#8a7a4e', sleeve: 0.45, trimColor: '#5f5334' },
      bottom: { color: '#5d5445' },
      shoes: { color: '#4a3b2c' }
    }
  },
  {
    id: 'waiter',
    label: 'waiter',
    body: { age: 27, build: 'slight' },
    look: {
      skin: '#f0cfa8',
      hair: { style: 'bun', color: '#3a2a1c' },
      top: { garment: 'shirt', color: '#f4f1ea', trim: ['collar', 'placket'], trimColor: '#2b2621' },
      over: { kind: 'apron', color: '#33413f' },
      bottom: { color: '#241f1c' },
      shoes: { color: '#1e1a17' }
    }
  },
  {
    id: 'muslim-woman',
    label: 'woman in hijab',
    body: { age: 31 },
    look: {
      skin: '#c1895f',
      head: { kind: 'hijab', color: '#7b5a86' },
      top: { garment: 'robe', color: '#6d4a63' },
      shoes: { color: '#39302a' }
    }
  },
  {
    id: 'indian-man',
    label: 'man in kurta',
    body: { age: 44 },
    look: {
      skin: '#a8713f',
      hair: { style: 'shaved', color: '#241c17', beard: true },
      head: { kind: 'turban', color: '#d8973c' },
      top: { garment: 'kurta', color: '#e6dfd0', trimColor: '#b9ab92' },
      bottom: { color: '#ddd6c6' },
      shoes: { bare: false, color: '#5c4732' }
    }
  },
  {
    id: 'heavy-man',
    label: 'heavy build',
    body: { age: 45, mass: 0.85 },
    look: {
      skin: '#dda87c',
      hair: { style: 'shaved', color: '#3a2f26' },
      top: { garment: 'shirt', color: '#7d9cab', trimColor: '#4e6a78' },
      bottom: { color: '#5d5445' },
      shoes: { color: '#3d342b' }
    }
  },
  {
    id: 'nurse',
    label: 'nurse',
    body: { age: 33, mass: 0.2 },
    look: {
      skin: '#e0b98e',
      hair: { style: 'long', color: '#4a3524' },
      top: { garment: 'coverall', color: '#6fa89b', trim: ['collar', 'placket', 'badge'], trimColor: '#43766c', badgeColor: '#f2f0e6' },
      shoes: { color: '#efe7d8' }
    }
  }
];

function main() {
  const outDir = path.resolve(process.argv[2] || path.join(__dirname, '..', 'proofs'));
  fs.mkdirSync(outDir, { recursive: true });
  const cards = [];

  for (const entry of SHEET) {
    const proportion = Body.body(entry.body);
    const out = Paperbook.renderPose({
      proportion,
      height: Body.heightFor(entry.body, 760),
      view: entry.view || 'three-quarter-right',
      look: entry.look,
      id: entry.id,
      accessibilityLabel: entry.label
    });
    const file = path.join(outDir, `role-${entry.id}.svg`);
    fs.writeFileSync(file, out.svg);
    cards.push(`<figure><figcaption>${entry.label}</figcaption>${out.svg}</figure>`);
    console.log(`role-${entry.id}: ${entry.look.top?.garment || 'tunic'}${entry.look.head ? ` + ${entry.look.head.kind}` : ''} -> ${path.relative(process.cwd(), file)}`);
  }

  const sheet = path.join(outDir, 'role-sheet.html');
  fs.writeFileSync(sheet, `<!doctype html><meta charset="utf-8"><title>Paper Cast role sheet</title>
<body style="background:#c2b09a;font:13px/1.4 system-ui,sans-serif;margin:0">
<div style="display:flex;flex-wrap:wrap;gap:10px;padding:12px;align-items:flex-end">${cards.join('')}</div>
<style>figure{margin:0;background:#efe7d8;padding:8px;border-radius:4px}svg{height:300px;display:block}figcaption{margin-bottom:6px}</style>
</body>`);
  console.log(`sheet -> ${path.relative(process.cwd(), sheet)}`);
}

main();
