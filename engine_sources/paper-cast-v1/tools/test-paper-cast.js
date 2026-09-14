/**
 * Validation suite for the paper cast system:
 *   node tools/test-paper-cast.js
 */
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const Rig = require(path.join(ROOT, 'runtime', 'paper-cast-rig.js'));
const Renderer = require(path.join(ROOT, 'runtime', 'paper-cast-renderer.js'));
const Context = require(path.join(ROOT, 'runtime', 'cast-context.js'));
const Cast = require(path.join(ROOT, 'runtime', 'paper-cast.js'));

const results = [];
function test(name, fn) {
  try {
    fn();
    results.push({ name, ok: true });
  } catch (error) {
    results.push({ name, ok: false, error: error.message });
  }
}

const VIEW_AXES = Object.keys(Rig.VIEW_AXES);
Cast.init();

test('manifest inventory matches the generated registry and the files on disk', () => {
  const index = JSON.parse(fs.readFileSync(path.join(ROOT, 'manifests', 'cast-index.json'), 'utf8'));
  const files = fs.readdirSync(path.join(ROOT, 'manifests', 'cast')).filter((f) => f.endsWith('.json'));
  assert.strictEqual(index.count, index.entries.length);
  assert.strictEqual(files.length, index.count);
  assert.strictEqual(Cast.registry.entries.length, index.count);
  const ids = new Set(index.entries.map((e) => e.id));
  assert.strictEqual(ids.size, index.count, 'cast ids must be unique');
});

test('every manifest pose exists in the pose library', () => {
  const poseIds = new Set(Cast.poses.poses.map((p) => p.id));
  for (const entry of Cast.registry.entries) {
    for (const id of entry.poses) assert.ok(poseIds.has(id), `${entry.id} → unknown pose ${id}`);
    assert.ok(entry.poses.includes(entry.defaultPose), `${entry.id} default pose not in pose list`);
  }
});

test('rig builds a figure on all eight view axes', () => {
  for (const axis of VIEW_AXES) {
    const figure = Rig.build({ view: axis, height: 900 });
    assert.strictEqual(figure.view.axis, axis);
    assert.ok(figure.parts.length >= 13, `${axis}: expected limb + torso + head parts`);
    assert.ok(figure.bounds.maxX > figure.bounds.minX && figure.bounds.maxY > figure.bounds.minY, `${axis}: empty bounds`);
    for (const part of figure.parts) assert.ok(Number.isFinite(part.depth), `${axis}: non-finite depth`);
  }
});

test('profile views compress the silhouette and back views hide the face', () => {
  const width = (axis) => {
    const f = Rig.build({ view: axis, height: 900 });
    return f.bounds.maxX - f.bounds.minX;
  };
  assert.ok(width('profile-right') < width('front') * 0.8, 'profile should be narrower than front');
  const back = Rig.build({ view: 'back', height: 900 });
  assert.ok(back.head.facing < -0.9, 'back view head should face away from camera');
  assert.ok(!Renderer.render(back, {}).svg.includes('pc-head-face'), 'back view must not draw facial features');
});

test('parts are emitted far-to-near so the far arm sits behind the torso', () => {
  const figure = Rig.build({ view: 'three-quarter-right', height: 900 });
  const depths = figure.parts.map((p) => p.depth);
  assert.deepStrictEqual(depths, [...depths].sort((a, b) => a - b), 'parts must be depth sorted');
  const torso = figure.parts.findIndex((p) => p.kind === 'torso');
  // Turned to stage right, so the character's right side is the one facing away.
  const farArm = figure.parts.findIndex((p) => p.id === 'right-upper-arm');
  const nearArm = figure.parts.findIndex((p) => p.id === 'left-upper-arm');
  assert.ok(farArm < torso, 'far arm must draw before the torso');
  assert.ok(nearArm > torso, 'near arm must draw after the torso');
});

test('head yaw is independent of body yaw', () => {
  const figure = Rig.build({ view: 'profile-right', pose: { head: { yaw: -90 } }, height: 900 });
  assert.strictEqual(figure.view.axis, 'profile-right');
  assert.strictEqual(figure.head.viewAxis, 'front');
  assert.ok(figure.head.facing > 0.99, 'head should address the camera while the body stays in profile');
});

test('rendering is deterministic for a seed and varies with it', () => {
  const opts = { view: 'three-quarter-left', height: 900, paperStyle: 'handmade-scrapbook', seed: 'abc' };
  assert.strictEqual(Renderer.renderPose(opts).svg, Renderer.renderPose(opts).svg);
  assert.notStrictEqual(Renderer.renderPose(opts).svg, Renderer.renderPose({ ...opts, seed: 'xyz' }).svg);
});

test('every archetype renders in every pose and view axis without NaN geometry', () => {
  let rendered = 0;
  for (const entry of Cast.registry.entries) {
    for (const pose of entry.poses) {
      for (const axis of entry.viewAxes) {
        const out = Cast.renderFigure({ id: entry.id, pose, viewAxis: axis });
        assert.ok(!/NaN|Infinity|undefined/.test(out.svg), `${entry.id}/${pose}/${axis} produced invalid geometry`);
        assert.ok(out.svg.startsWith('<svg') && out.svg.endsWith('</svg>'));
        rendered += 1;
      }
    }
  }
  assert.ok(rendered >= 600, `expected a broad render sweep, got ${rendered}`);
});

test('script context extracts role, action and target', () => {
  const ctx = Context.analyze('The technician crouches and inspects the machine, then points at the fault on the screen.');
  assert.strictEqual(ctx.role, 'technician');
  assert.ok(['inspect-crouch', 'point-at-detail'].includes(ctx.action));
  assert.strictEqual(ctx.addressing, 'content');
});

test('addressing the content turns the body away from the camera', () => {
  const scene = Cast.renderScene({ script: 'The analyst turns to the chart on the screen and points at the spike.' });
  const member = scene.cast[0];
  assert.strictEqual(member.role, 'analyst');
  assert.notStrictEqual(member.view.viewAxis, 'front');
  assert.strictEqual(member.view.addressing, 'content');
  assert.ok(scene.svg.includes('data-view-axis="' + member.view.viewAxis + '"'));
});

test('addressing the viewer produces a camera-facing body', () => {
  const scene = Cast.renderScene({ script: 'The presenter welcomes the audience and speaks to camera.' });
  assert.strictEqual(scene.cast[0].view.addressing, 'camera');
  assert.strictEqual(scene.cast[0].view.viewAxis, 'front');
});

test('two characters in conversation face each other, not the camera', () => {
  const scene = Cast.renderScene({ script: 'The customer asks the support agent a question and they talk to each other.', castSize: 2 });
  assert.strictEqual(scene.cast.length, 2);
  const [left, right] = scene.cast;
  assert.ok(left.stage.x < right.stage.x);
  assert.ok(left.view.yaw > 0, 'the left character should turn toward stage right');
  assert.ok(right.view.yaw < 0, 'the right character should turn toward stage left');
  assert.notStrictEqual(left.id, right.id);
});

test('selection is contextual: different scripts cast different characters', () => {
  const picks = [
    'The nurse explains the procedure to the patient.',
    'The builder carries boxes across the site.',
    'The child listens to the story and celebrates.',
    'The executive sets the strategy for the board.'
  ].map((script) => Cast.plan({ script }).cast[0].role);
  assert.deepStrictEqual(picks, ['healthcare_worker', 'builder', 'child', 'executive']);
});

test('walking uses a locomotion pose and never a front view', () => {
  const plan = Cast.plan({ script: 'The reporter walks across the field toward the crowd.' });
  assert.strictEqual(plan.cast[0].pose, 'walk-stride');
  assert.notStrictEqual(plan.cast[0].view.viewAxis, 'front');
});

test('paper styles change the cut without breaking the SVG', () => {
  for (const style of Object.keys(Renderer.PAPER_STYLES)) {
    const out = Cast.renderFigure({ id: 'cast.presenter.paper-01', paperStyle: style });
    assert.ok(out.svg.includes('<path'), `${style} produced no paper shapes`);
  }
});

test('scene svg is valid for each aspect ratio', () => {
  for (const ratio of ['16:9', '1:1', '9:16']) {
    const scene = Cast.renderScene({ script: 'The teacher explains the diagram to the class.', aspectRatio: ratio });
    const frame = Cast.FRAMES[ratio];
    assert.ok(scene.svg.includes(`viewBox="0 0 ${frame.width} ${frame.height}"`));
    assert.strictEqual((scene.svg.match(/<svg/g) || []).length, 1);
  }
});

test('a profile torso keeps its body depth instead of collapsing to a line', () => {
  const width = (axis) => {
    const t = Rig.build({ proportion: 'adult-average', height: 600, view: axis, pose: {} }).torso;
    return t.shoulderRight.x - t.shoulderLeft.x;
  };
  const front = width('front');
  for (const axis of ['profile-left', 'profile-right']) {
    assert.ok(width(axis) > front * 0.45, `${axis} torso collapsed to ${width(axis).toFixed(1)}`);
  }
});

test('feet stand on the stage ground line at every view axis', () => {
  for (const axis of VIEW_AXES) {
    const figure = Rig.build({ proportion: 'adult-average', height: 600, view: axis, pose: {} });
    const feet = figure.parts.filter((p) => p.kind === 'foot');
    assert.ok(feet.every((f) => f.b.y > f.a.y), `${axis}: a foot has no visible height`);
    assert.ok(Math.abs(figure.ground - Math.max(...feet.map((f) => f.b.y + f.widthTo * 0.5))) < 1e-6);
  }
  // On stage a member is lifted by its ground line, not by its padded bounds,
  // so the shoes touch the dashed floor instead of hovering above it.
  const frame = Cast.FRAMES['16:9'];
  const scene = Cast.renderScene({ script: 'The presenter welcomes the audience.', aspectRatio: '16:9' });
  const figure = Rig.build({ proportion: scene.cast[0].proportion, height: frame.height * frame.figureHeight, view: scene.cast[0].view.viewAxis, pose: { ...scene.cast[0].poseAngles, head: { ...(scene.cast[0].poseAngles.head || {}), yaw: scene.cast[0].view.headYaw } } });
  const lift = Number(/translate\(0 (-?[\d.]+)\)/.exec(scene.svg)[1]);
  assert.ok(Math.abs(lift + figure.ground) < 0.02, `member sits ${(lift + figure.ground).toFixed(1)} off the ground line`);
  assert.ok(scene.svg.includes(`y1="${frame.height * frame.ground}"`));
});

test('a four-hander is laid out without overlapping silhouettes', () => {
  for (const ratio of ['16:9', '1:1', '9:16']) {
    const scene = Cast.renderScene({ script: 'The teacher, student, doctor and builder discuss plans together.', aspectRatio: ratio });
    assert.strictEqual(scene.cast.length, 4);
    const xs = [...scene.svg.matchAll(/class="pc-stage-member"[^>]*transform="translate\((-?[\d.]+) /g)].map((m) => Number(m[1]));
    assert.strictEqual(xs.length, 4);
    const sorted = [...xs].sort((a, b) => a - b);
    for (let i = 1; i < sorted.length; i += 1) {
      assert.ok(sorted[i] - sorted[i - 1] > Cast.FRAMES[ratio].width * 0.1, `${ratio}: members ${i - 1}/${i} are stacked`);
    }
  }
});

test('every named role in a beat is cast, not silently dropped', () => {
  const plan = Cast.plan({ script: 'The teacher, student, doctor and builder discuss plans together.' });
  assert.deepStrictEqual(plan.cast.map((m) => m.role), ['teacher', 'student', 'healthcare_worker', 'builder']);
});

test('travel and exit beats orient along the direction of movement', () => {
  const travel = Cast.plan({ script: 'The reporter walks across the field toward the crowd.' }).cast[0];
  assert.strictEqual(travel.view.addressing, 'travel');
  assert.ok(travel.view.viewAxis.startsWith('profile'), `expected a profile, got ${travel.view.viewAxis}`);
  const exit = Cast.plan({ script: 'The builder carries boxes across the site and heads out of frame.' }).cast[0];
  assert.strictEqual(exit.view.addressing, 'exit');
  assert.notStrictEqual(exit.view.viewAxis, 'front');
});

test('poses are chosen so the body can actually face what it addresses', () => {
  const beats = [
    'The teacher explains the diagram while the student listens.',
    'The customer asks the support agent a question and they talk to each other.',
    'The analyst turns to the chart on the screen and points at the spike.',
    'The reporter walks across the field toward the crowd.'
  ];
  for (const script of beats) {
    const plan = Cast.plan({ script });
    assert.deepStrictEqual(plan.warnings.filter((w) => w.includes('cannot face')), [], `${script} -> ${plan.warnings.join('; ')}`);
  }
});

test('the figure carries one merged contour instead of per-part outlines', () => {
  const svg = Renderer.renderPose({ proportion: 'adult-average', height: 400, view: 'three-quarter-right', pose: {} }).svg;
  const cuts = [...svg.matchAll(/class="pc-cut"/g)].length;
  assert.ok(cuts > 8, `expected a silhouette pass, found ${cuts} cut shapes`);
  const ink = Renderer.resolveLook({}).ink;
  for (const el of svg.match(/<(?:path|ellipse)[^>]*class="pc-(?:torso|head|neck|hair|limb|foot|hand|sleeve)[^"]*"[^>]*>/g) || []) {
    assert.ok(!el.includes(`stroke="${ink}"`), `body fill still draws its own ink seam: ${el.slice(0, 80)}`);
  }
});

const failed = results.filter((r) => !r.ok);
for (const r of results) console.log(`${r.ok ? 'PASS' : 'FAIL'}  ${r.name}${r.ok ? '' : `\n      ${r.error}`}`);
console.log(`\n${results.length - failed.length}/${results.length} passed`);
process.exit(failed.length ? 1 : 0);
