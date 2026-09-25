#!/usr/bin/env node
/**
 * Draws characters straight from script lines — no hex codes, no pose names:
 *
 *   node tools/render-story-sheet.js [outDir] ["a line of script" ...]
 *
 * The check it exists for: read the caption, cover it, and the drawing should
 * still be telling you who this is and what they are doing.
 */
const fs = require('fs');
const path = require('path');
const Cast = require('../runtime/paper-cast.js');

const DEFAULT_LINES = [
  'a fireman',
  'a police officer',
  'an elderly farmer',
  'a waiter serving food',
  'a woman in a hijab carrying groceries',
  'an Indian man in a turban',
  'an obese man carrying a crate',
  'a black market trader with a basket',
  'a white nurse',
  'a cleaner sweeping',
  'a fisherman rowing',
  'a child reading'
];

function main() {
  const args = process.argv.slice(2);
  const outDir = path.resolve(args[0] || path.join(__dirname, '..', 'proofs'));
  const lines = args.length > 1 ? args.slice(1) : DEFAULT_LINES;
  fs.mkdirSync(outDir, { recursive: true });

  const drawings = [];
  for (const line of lines) {
    const drawn = Cast.illustrateRole(line, { height: 760, view: 'three-quarter-right' });
    const slug = line.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 48);
    const file = path.join(outDir, `story-${slug}.svg`);
    fs.writeFileSync(file, drawn.svg);
    drawings.push({ line, drawn });
    const c = drawn.character;
    console.log(`${line}\n  role=${c.role || 'UNRECOGNISED'} prop=${c.prop || '-'} modifiers=[${c.modifiers.join(', ')}] grip residual=${(drawn.residual * 100).toFixed(1)}%`);
  }

  // One scale for the whole sheet, so a child stands next to an adult at the
  // size the story gave them instead of being blown up to fill its card.
  const tallest = Math.max(...drawings.map((d) => d.drawn.height));
  const cards = drawings.map(({ line, drawn }) => {
    const px = Math.round((drawn.height / tallest) * 330);
    return `<figure><figcaption>${line}</figcaption><div class="fig" style="height:${px}px">${drawn.svg}</div></figure>`;
  });

  const sheet = path.join(outDir, 'story-sheet.html');
  fs.writeFileSync(sheet, `<!doctype html><meta charset="utf-8"><title>Paper Cast story sheet</title>
<body style="background:#c2b09a;font:13px/1.4 system-ui,sans-serif;margin:0">
<div style="display:flex;flex-wrap:wrap;gap:10px;padding:12px;align-items:flex-end">${cards.join('')}</div>
<style>figure{margin:0;background:#efe7d8;padding:8px;border-radius:4px;display:flex;flex-direction:column;justify-content:flex-end}.fig{display:flex;align-items:flex-end}svg{height:100%;display:block}figcaption{margin-bottom:6px}</style>
</body>`);
  console.log(`\nsheet -> ${path.relative(process.cwd(), sheet)}`);
}

main();
