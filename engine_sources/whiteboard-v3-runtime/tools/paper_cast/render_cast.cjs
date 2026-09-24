// Renders the paper-cast cast as LINE-ART SVGs for the whiteboard renderer.
// Each cast member is posed in a fitting situation; output is stroke-only
// (pb-rim highlights and pb-shadow ellipses stripped) so the art inks like
// every other whiteboard element.
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

// joint-angle pose presets (degrees; tilt = down→forward→up)
const POSES = {
  rest: {},
  point: { armRight: { shoulder: { tilt: 62, swing: -14 }, elbow: { tilt: 6, swing: 2 } } },
  explain: { armLeft: { shoulder: { tilt: 38, swing: -22 }, elbow: { tilt: 24, swing: 4 } },
             armRight: { shoulder: { tilt: 38, swing: 22 }, elbow: { tilt: 24, swing: -4 } } },
  wave: { armRight: { shoulder: { tilt: 150, swing: 14 }, elbow: { tilt: 18, swing: 8 } } },
  lift: { armLeft: { shoulder: { tilt: 55, swing: -10 }, elbow: { tilt: 30, swing: 4 } },
          armRight: { shoulder: { tilt: 55, swing: 10 }, elbow: { tilt: 30, swing: -4 } },
          spine: { tilt: -8, swing: 0 }, crouch: 0.35 },
  carry: { armLeft: { shoulder: { tilt: 48, swing: -8 }, elbow: { tilt: 62, swing: 6 } },
           armRight: { shoulder: { tilt: 48, swing: 8 }, elbow: { tilt: 62, swing: -6 } } },
  seated: { legLeft: { hip: { tilt: 82, swing: 6 }, knee: { tilt: 86, swing: 0 }, ankle: { tilt: -80 } },
            legRight: { hip: { tilt: 82, swing: -6 }, knee: { tilt: 86, swing: 0 }, ankle: { tilt: -80 } },
            spine: { tilt: -4, swing: 0 } },
  think: { armRight: { shoulder: { tilt: 42, swing: -18 }, elbow: { tilt: 105, swing: 8 } },
           head: { yaw: 0, pitch: -8 } },
  beckon: { armRight: { shoulder: { tilt: 66, swing: -6 }, elbow: { tilt: 40, swing: 12 } } },
};

// cast member -> situation spec
const CAST = {
  'presenter':         { proportion: 'adult-average', pose: 'point',    look: { top: { garment: 'shirt' } },  face: 'warm',       view: 'three-quarter-right' },
  'teacher':           { proportion: 'adult-average', pose: 'explain',  look: { top: { garment: 'kurta' } },  face: 'attentive',  view: 'three-quarter-right' },
  'student':           { proportion: 'teen',          pose: 'rest',   look: { top: { garment: 'shirt' } },  face: 'attentive',  view: 'front' },
  'child':             { proportion: 'child',         pose: 'wave',     look: { top: { garment: 'tunic' } },  face: 'joy',        view: 'front' },
  'executive':         { proportion: 'adult-tall',    pose: 'rest',     look: { top: { garment: 'jacket' } }, face: 'stern',      view: 'front' },
  'office-worker':     { proportion: 'adult-average', pose: 'think',   look: { top: { garment: 'shirt' } },  face: 'neutral',    view: 'three-quarter-right' },
  'creator':           { proportion: 'adult-slight',  pose: 'think',    look: { top: { garment: 'tunic' } },  face: 'thoughtful', view: 'three-quarter-right' },
  'technician':        { proportion: 'adult-broad',   pose: 'lift',     look: { top: { garment: 'coverall' } },face: 'effort',     view: 'front' },
  'healthcare-worker': { proportion: 'adult-average', pose: 'explain',  look: { top: { garment: 'coverall' } },face: 'warm',       view: 'front' },
  'builder':           { proportion: 'adult-broad',   pose: 'lift',     look: { top: { garment: 'coverall' }, head: { kind: 'helmet' } }, face: 'effort', view: 'front' },
  'parent':            { proportion: 'adult-average', pose: 'carry',    look: { top: { garment: 'shirt' } },  face: 'warm',       view: 'three-quarter-right' },
  'customer':          { proportion: 'adult-average', pose: 'rest',     look: { top: { garment: 'tunic' } },  face: 'attentive',  view: 'front' },
  'support-helper':    { proportion: 'adult-slight',  pose: 'beckon',   look: { top: { garment: 'vest' } },   face: 'warm',       view: 'three-quarter-right' },
  'salesperson':       { proportion: 'adult-tall',    pose: 'beckon',   look: { top: { garment: 'jacket' } }, face: 'warm',       view: 'front' },
  'peer-friend':       { proportion: 'adult-slight',  pose: 'wave',     look: { top: { garment: 'shirt' } },  face: 'joy',        view: 'front' },
  'mentor':            { proportion: 'senior',        pose: 'explain',  look: { top: { garment: 'coat' }, hair: { color: '#b9b2a8' } }, face: 'thoughtful', view: 'three-quarter-right' },
  'analyst':           { proportion: 'adult-average', pose: 'point',    look: { top: { garment: 'jacket' } }, face: 'attentive',  view: 'three-quarter-right' },
  'field-reporter':    { proportion: 'adult-average', pose: 'explain',  look: { top: { garment: 'jacket' } }, face: 'attentive',  view: 'front' },
  // extra bodies for generic roles
  'toddler':           { proportion: 'toddler',       pose: 'rest',     look: { top: { garment: 'tunic' } },  face: 'joy',        view: 'front' },
  'heavyset':          { proportion: 'adult-heavy',   pose: 'rest',     look: { top: { garment: 'shirt' } },  face: 'neutral',    view: 'front' },
};

const OUT = require('path').resolve(__dirname, '../../assets/paper_cast');
fs.mkdirSync(OUT, { recursive: true });
const manifest = {};
for (const [id, s] of Object.entries(CAST)) {
  const r = Fig.renderPose({
    proportion: s.proportion, height: s.proportion === 'child' ? 620
      : s.proportion === 'teen' ? 800 : s.proportion === 'toddler' ? 480
      : s.proportion === 'senior' ? 940 : 1000,
    pose: POSES[s.pose] || {},
    view: { viewAxis: s.view || 'three-quarter-right' },
    look: s.look, face: s.face,
    background: false, grain: false,
  });
  let svg = r.svg
    .replace(/<g class="pb-shadow">.*?<\/g>/g, '')
    .replace(/<g class="pb-rim"[^>]*>.*?<\/g>/g, '')
    .replace(/<defs>.*?<\/defs>/s, '');
  fs.writeFileSync(`${OUT}/${id}.svg`, svg);
  manifest[id] = { viewBox: r.viewBox, proportion: s.proportion,
                   pose: s.pose, face: s.face };
  console.log(id, r.viewBox);
}
fs.writeFileSync(`${OUT}/manifest.json`, JSON.stringify(manifest, null, 1));
console.log('done', Object.keys(CAST).length);
