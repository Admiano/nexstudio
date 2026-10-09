/**
 * Renders a review sheet of the cast: every view axis for one archetype, one
 * pose per archetype, and a few staged script beats.
 *   node tools/render-contact-sheet.js [outputDir]
 */
'use strict';
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const Cast = require(path.join(ROOT, 'runtime', 'paper-cast.js'));
const Rig = require(path.join(ROOT, 'runtime', 'paper-cast-rig.js'));

Cast.init();
const out = path.resolve(process.argv[2] || path.join(ROOT, '.review'));
fs.mkdirSync(out, { recursive: true });

const axes = Object.keys(Rig.VIEW_AXES);
const cell = (label, svg) => `<figure><div class="art">${svg}</div><figcaption>${label}</figcaption></figure>`;

const orientation = axes
  .map((axis) => cell(axis, Cast.renderFigure({ id: 'cast.presenter.paper-01', pose: 'present-to-content', viewAxis: axis }).svg))
  .join('');

const poses = Cast.poses.poses
  .map((pose) => {
    const entry = Cast.registry.entries.find((e) => e.poses.includes(pose.id)) || Cast.registry.entries[0];
    return cell(`${pose.id} · ${entry.slug}`, Cast.renderFigure({ id: entry.id, pose: pose.id, viewAxis: pose.viewAxes[Math.min(1, pose.viewAxes.length - 1)] }).svg);
  })
  .join('');

const roster = Cast.registry.entries
  .map((entry) => cell(`${entry.slug} · ${entry.ageBand}`, Cast.renderFigure({ id: entry.id, viewAxis: 'three-quarter-right', paperStyle: 'handmade-scrapbook' }).svg))
  .join('');

const BEATS = [
  'The presenter welcomes the audience and speaks to camera.',
  'The analyst turns to the chart on the screen and points at the spike.',
  'The technician crouches and inspects the machine.',
  'The customer asks the support agent a question and they talk to each other.',
  'The reporter walks across the field toward the crowd.',
  'The teacher explains the diagram while the student listens.'
];

const beats = BEATS.map((script) => {
  const scene = Cast.renderScene({ script, paperStyle: 'clean-editorial' });
  const detail = scene.cast.map((c) => `${c.slug}/${c.pose}/${c.view.viewAxis}→${c.view.addressing}`).join(' · ');
  return `<section class="beat"><p class="script">${script}</p><div class="stage">${scene.svg}</div><p class="detail">${detail}</p></section>`;
}).join('');

const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Paper cast review sheet</title>
<style>
 body{margin:0;padding:32px;background:#e9e3d6;font:14px/1.4 ui-sans-serif,system-ui;color:#241f1c}
 h2{margin:32px 0 12px;font-size:16px;letter-spacing:.08em;text-transform:uppercase}
 .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}
 figure{margin:0;background:#fbf7ee;border:1px solid #cfc6b4;padding:8px;text-align:center}
 .art svg{width:100%;height:190px}
 figcaption{font-size:11px;color:#6c6259;margin-top:6px}
 .beat{margin-bottom:24px;background:#fbf7ee;border:1px solid #cfc6b4;padding:12px}
 .stage svg{width:100%;height:auto}
 .script{margin:0 0 8px;font-weight:600}
 .detail{margin:8px 0 0;font-size:12px;color:#6c6259}
</style></head><body>
<h1>Paper cast review sheet</h1>
<h2>Orientation sweep — one character, eight view axes</h2><div class="grid">${orientation}</div>
<h2>Pose library</h2><div class="grid">${poses}</div>
<h2>Cast roster</h2><div class="grid">${roster}</div>
<h2>Staged script beats</h2>${beats}
</body></html>`;

fs.writeFileSync(path.join(out, 'contact-sheet.html'), html);
console.log(path.join(out, 'contact-sheet.html'));
