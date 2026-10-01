#!/usr/bin/env node
/**
 * Editorial motion validation: layout integrity per ratio, script reading,
 * contextual cast selection, icon and media restraint, determinism.
 */
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const Script = require(path.join(root, 'runtime/script-context.js'));
const Layout = require(path.join(root, 'runtime/layout-engine.js'));
const Peeps = require(path.join(root, 'runtime/peeps-library.js'));
const Director = require(path.join(root, 'runtime/editorial-director.js'));
const { registries } = require(path.join(root, 'tools/load-registries.js'));

const RULES = require(path.join(root, 'manifests/editorial-rules.json'));
const reg = registries();
const RATIOS = ['16:9', '1:1', '9:16'];

let passed = 0;
const failures = [];
function test(name, fn) {
  try {
    fn();
    passed += 1;
    console.log('  ok   ' + name);
  } catch (error) {
    failures.push({ name, error });
    console.log('  FAIL ' + name + '\n       ' + error.message);
  }
}
function assert(cond, message) {
  if (!cond) throw new Error(message || 'assertion failed');
}

const SCRIPT = `Your team still copies numbers between five tools every morning.
It is slow, manual and exhausting, and mistakes slip through.
What if the report wrote itself?
NexStudio reads your sources and drafts the update in seconds.
Teams cut reporting time by 78 percent in the first month.
A nurse on call reviews the patient summary before her shift ends.
Download the app and start free today.`;

const MEDIA = [
  { type: 'image', name: 'dashboard-report.png' },
  { type: 'video', name: 'team-standup.mp4' }
];

const plan = (over = {}) => Director.direct(over.script || SCRIPT, {
  ratio: '16:9', duration: 30, registries: reg, ...over
});

console.log('\nscript reading');
test('splits a script into weighted beats with roles', () => {
  const doc = Script.read(SCRIPT, { duration: 30 });
  assert(doc.beats.length >= 5, 'too few beats');
  assert(doc.beats.every((b) => b.text.trim().length), 'empty beat');
  assert(new Set(doc.beats.map((b) => b.role)).size >= 3, 'roles are not varied');
  assert(Math.abs(doc.beats.reduce((n, b) => n + b.duration, 0) - 30) < 0.01, 'durations do not fill the runtime');
});
test('detects numbers, people and show cues from the text alone', () => {
  const doc = Script.read(SCRIPT, { duration: 30 });
  const stat = doc.beats.find((b) => b.text.includes('78 percent'));
  const person = doc.beats.find((b) => b.text.includes('nurse'));
  assert(stat.entities.numbers.length, 'statistic not detected');
  assert(person.person > 0.3, 'person not detected: ' + person.person);
});
test('blends role disposition into flat beats', () => {
  const doc = Script.read('The pipeline breaks every Monday.', { duration: 5 });
  const brief = Script.brief(doc.beats[0]);
  assert(brief.emotion.valence < 0, 'a problem beat should not read positive');
});

console.log('\nratio-native layout');
test('every authored plan is collision free in every ratio', () => {
  const report = Layout.audit();
  assert(report.length >= RATIOS.length * 5, 'too few authored plans: ' + report.length);
  for (const entry of report) {
    assert(!entry.problems || !entry.problems.length, JSON.stringify(entry));
    assert(entry.regions >= 1, 'empty plan ' + entry.key);
  }
});
test('regions stay inside the frame safe area', () => {
  for (const ratio of RATIOS) {
    for (const kinds of [['text'], ['text', 'icons'], ['text', 'character'], ['text', 'media']]) {
      const solved = Layout.solve(ratio, kinds);
      for (const r of solved.regions) {
        assert(r.x >= -0.001 && r.y >= -0.001 && r.x + r.w <= 1.001 && r.y + r.h <= 1.001,
          `${ratio}/${solved.key}/${r.id} leaves the frame`);
      }
    }
  }
});
test('drops the least important element rather than overlapping', () => {
  const solved = Layout.solve('9:16', ['text', 'icons', 'media', 'character']);
  assert(solved.dropped.length >= 1, 'nothing dropped from an over-full frame');
  assert(solved.byId.text, 'text must never be dropped');
});
test('each ratio is authored, not scaled', () => {
  const keys = RATIOS.map((r) => JSON.stringify(Layout.solve(r, ['text', 'character']).regions));
  assert(new Set(keys).size === RATIOS.length, 'ratios share one layout');
});

console.log('\nopen peeps still cast');
test('every part referenced by the index exists on disk', () => {
  const index = require(path.join(root, 'assets/peeps/parts-index.json'));
  for (const group of Object.values(index.parts)) {
    for (const part of group) {
      assert(fs.existsSync(path.join(root, 'assets/peeps', part.file)), 'missing ' + part.file);
    }
  }
});
test('resolves a different face for opposite emotions', () => {
  const happy = Peeps.resolve({ emotion: { valence: 0.9, arousal: 0.8, tags: ['win'] }, seed: 'a' });
  const sad = Peeps.resolve({ emotion: { valence: -0.9, arousal: 0.2, tags: ['problem'] }, seed: 'a' });
  assert(happy.parts.face.id !== sad.parts.face.id, 'emotion does not change the face');
  assert(Peeps.meta('face', happy.parts.face.id).valence > Peeps.meta('face', sad.parts.face.id).valence,
    'face valence does not follow the beat');
});
test('resolves pose from beat vocabulary', () => {
  const medical = Peeps.resolve({ keywords: ['nurse', 'patient'], emotion: { valence: 0.1, arousal: 0.4 }, seed: 'b' });
  const tags = Peeps.meta('pose', medical.parts.body.id).tags || [];
  assert(tags.some((t) => ['nurse', 'doctor', 'clinic', 'patient'].includes(t)),
    'medical beat resolved to ' + medical.parts.body.id);
});
test('composes one still SVG with no animation in it', () => {
  const selection = Peeps.resolve({ emotion: { valence: 0.4, arousal: 0.5 }, seed: 'c' });
  const read = (file) => fs.readFileSync(path.join(root, 'assets/peeps', file), 'utf8');
  const figure = Peeps.compose(selection, read);
  assert(figure.svg.startsWith('<svg'), 'not an svg');
  assert(!/animate|@keyframes|<script/i.test(figure.svg), 'the still figure contains motion');
  assert(figure.width > 0 && figure.height > 0, 'empty figure box');
});
test('the same context always resolves the same figure', () => {
  const ctx = { emotion: { valence: 0.2, arousal: 0.5 }, keywords: ['team'], seed: 'd' };
  assert(JSON.stringify(Peeps.resolve(ctx)) === JSON.stringify(Peeps.resolve(ctx)), 'cast selection is not deterministic');
});

console.log('\ndirection: text leads, nothing strays');
test('every beat carries exactly one typographic component', () => {
  for (const ratio of RATIOS) {
    const p = plan({ ratio });
    for (const shot of p.shots) {
      assert(shot.typography && shot.typography.slug, 'beat without type');
      assert(shot.layout.byId.text, 'text has no region');
      const said = shot.text.toLowerCase();
      const strings = Object.values(shot.typography.content)
        .flatMap((v) => (Array.isArray(v) ? v : [v]))
        .filter((v) => typeof v === 'string' && v.trim())
        .flatMap((v) => v.split(','));
      for (const value of strings) {
        const probe = value.trim().toLowerCase();
        assert(said.includes(probe.slice(0, Math.min(14, probe.length))), 'typography invented copy: ' + value);
      }
    }
  }
});
test('icons only appear for words the script actually says', () => {
  const p = plan();
  for (const shot of p.shots) {
    const said = new Set(shot.text.toLowerCase().split(/[^a-z0-9]+/));
    for (const icon of shot.icons) {
      assert(icon.matched.length && icon.matched.every((m) => said.has(m.toLowerCase())),
        `stray icon ${icon.slug} on "${shot.text}"`);
    }
  }
});
test('a script that names nothing drawable gets no icons', () => {
  const p = plan({ script: 'Somehow the feeling lingered longer than anyone expected.' });
  assert(p.shots.every((s) => !s.icons.length), 'icons on a beat that names nothing');
});
test('icon budget and cooldown are respected', () => {
  for (const ratio of RATIOS) {
    const p = plan({ ratio });
    const budget = RULES.icons.maxPerShot[ratio];
    p.shots.forEach((shot, i) => {
      assert(shot.icons.length <= budget, 'icon budget exceeded');
      if (i > 0) {
        const prev = new Set(p.shots[i - 1].icons.map((x) => x.slug));
        assert(shot.icons.every((x) => !prev.has(x.slug)), 'icon repeated back to back');
      }
    });
  }
});

console.log('\ndirection: character earns its place');
test('no character when no beat earns emphasis', () => {
  const p = plan({ script: 'A quiet note. Another quiet note. One more quiet note.' });
  assert(p.stats.withCharacter === 0, 'character appeared without emphasis');
});
test('characters never run back to back and stay under the share cap', () => {
  for (const ratio of RATIOS) {
    const p = plan({ ratio });
    p.shots.forEach((shot, i) => {
      if (i > 0) assert(!(shot.character && p.shots[i - 1].character), 'characters back to back');
    });
    assert(p.stats.withCharacter / p.shots.length <= RULES.character.maxShare + 1e-6, 'share cap exceeded');
  }
});
test('character and media never share a frame', () => {
  const p = plan({ media: MEDIA });
  assert(p.shots.every((s) => !(s.character && s.media)), 'character competes with media');
});
test('a person-heavy script does bring a character in', () => {
  const p = plan({ script: 'Meet Ada, the nurse who runs the ward alone.\nShe is exhausted and the shift has barely started.\nOne tool gives her the evening back.' });
  assert(p.stats.withCharacter >= 1, 'no character on a person-led script');
});

console.log('\ndirection: uploaded media, only where it fits');
test('media is placed when the script matches an upload', () => {
  const p = plan({ media: MEDIA });
  assert(p.stats.withMedia >= 1, 'matching upload never used');
  const shot = p.shots.find((s) => s.media);
  assert(reg.media.some((m) => m.slug === shot.media.slug), 'unknown media container');
});
test('unrelated uploads are left out entirely', () => {
  const p = plan({
    script: 'A quiet idea grows slowly. It takes patience. It rewards patience.',
    media: [{ type: 'image', name: 'unrelated-kitchen-tiles.jpg' }]
  });
  assert(p.stats.withMedia === 0, 'irrelevant media forced into the frame');
});
test('no media library means no media', () => {
  assert(plan().stats.withMedia === 0, 'media without an upload');
});
test('an upload is not reused beyond its cap', () => {
  const p = plan({ media: [MEDIA[0]] });
  const uses = p.shots.filter((s) => s.media).length;
  assert(uses <= RULES.media.maxReuse, 'upload reused too often');
});

console.log('\nframe integrity');
test('no shot exceeds the element budget of its ratio', () => {
  for (const ratio of RATIOS) {
    const p = plan({ ratio, media: MEDIA });
    const max = RULES.frames[ratio].maxElements;
    for (const shot of p.shots) assert(shot.layout.regions.length <= max, `${ratio} overfilled`);
  }
});
test('regions within a shot never overlap', () => {
  for (const ratio of RATIOS) {
    for (const shot of plan({ ratio, media: MEDIA }).shots) {
      const r = shot.layout.regions;
      for (let i = 0; i < r.length; i += 1) {
        for (let j = i + 1; j < r.length; j += 1) {
          const a = r[i]; const b = r[j];
          const hit = a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
          assert(!hit, `${ratio} ${a.id} overlaps ${b.id}`);
        }
      }
    }
  }
});
test('shots tile the runtime without gaps', () => {
  const p = plan({ duration: 24 });
  let cursor = 0;
  for (const shot of p.shots) {
    assert(Math.abs(shot.start - cursor) < 0.01, 'gap before shot ' + shot.index);
    cursor += shot.duration;
  }
  assert(Math.abs(cursor - 24) < 0.01, 'runtime not filled');
});
test('the same script and seed always direct the same film', () => {
  assert(JSON.stringify(plan()) === JSON.stringify(plan()), 'direction is not deterministic');
});
test('all three ratios direct successfully from one script', () => {
  for (const ratio of RATIOS) {
    const p = plan({ ratio, media: MEDIA });
    assert(p.shots.length >= 5 && p.ratio === ratio, 'ratio failed: ' + ratio);
  }
});

console.log('\npackaging');
test('the generated data bundle matches the manifests on disk', () => {
  const bundlePath = path.join(root, 'manifests/editorial-data.js');
  assert(fs.existsSync(bundlePath), 'run tools/build-manifests.js');
  const window = {};
  new Function('window', fs.readFileSync(bundlePath, 'utf8'))(window);
  assert(JSON.stringify(window.NEX_EDITORIAL_RULES) === JSON.stringify(RULES), 'bundle is stale');
});
test('the package manifest counts what actually ships', () => {
  const manifest = require(path.join(root, 'manifests/editorial-manifest.json'));
  assert(manifest.counts.typography === reg.typography.length, 'typography count drifted');
  assert(manifest.counts.icons === reg.icons.length, 'icon count drifted');
  assert(manifest.counts.mediaContainers === reg.media.length, 'media count drifted');
  assert(manifest.counts.motion === reg.motion.length, 'motion count drifted');
});

console.log(`\n${passed}/${passed + failures.length} passed`);
process.exit(failures.length ? 1 : 0);
