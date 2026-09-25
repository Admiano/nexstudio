const fs = require('fs');
const nodeReq = require;
const cache = {};
function load(f) {
  const abs = './' + f;
  if (cache[abs]) return cache[abs];
  const src = fs.readFileSync(f, 'utf8');
  const m = { exports: {} };
  const req = (p) => p.startsWith('./') ? load(p.slice(2)) : nodeReq(p);
  new Function('module', 'exports', 'require', src)(m, m.exports, req);
  cache[abs] = m.exports;
  return m.exports;
}
const Fig = load('paperbook-figure.js');
console.log('api:', Object.keys(Fig));
const r = Fig.renderPose({
  proportion: 'child', height: 620, pose: {},
  view: { viewAxis: 'three-quarter-right' },
  look: 'hoodie', face: 'smile',
  background: false, grain: false, page: false,
});
console.log('viewBox', r.viewBox);
fs.writeFileSync('/tmp/pc_child.svg', r.svg);
const r2 = Fig.renderPose({
  proportion: 'adult-broad', height: 1000,
  pose: { arms: { right: { shoulder: { tilt: 62, swing: -12 }, elbow: { tilt: 8, swing: 2 } } } },
  view: { viewAxis: 'front' }, look: 'button-shirt', face: 'smile',
  background: false, grain: false, page: false,
});
fs.writeFileSync('/tmp/pc_adult.svg', r2.svg);
console.log('viewBox2', r2.viewBox, 'written');
