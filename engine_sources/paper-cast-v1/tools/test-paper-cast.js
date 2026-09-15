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

test('limb bends are padded so a joint never opens a notch in the silhouette', () => {
  const svg = Renderer.renderPose({ proportion: 'adult-average', height: 400, view: 'profile-right', pose: { armRight: { shoulder: { tilt: 40 }, elbow: { tilt: 100 } } } }).svg;
  assert.ok(/class="pc-joint/.test(svg), 'expected joint pads on the limbs');
  assert.ok(/class="pc-hand-end/.test(svg), 'expected a rounded hand end rather than a square cut strip');
});

test('a timed scene is deterministic and different from its neighbouring second', () => {
  const script = 'The analyst turns to the chart on the screen and points at the spike.';
  const a = Cast.renderScene({ script, time: 2, duration: 5 }).svg;
  const b = Cast.renderScene({ script, time: 2, duration: 5 }).svg;
  const c = Cast.renderScene({ script, time: 3.5, duration: 5 }).svg;
  assert.strictEqual(a, b, 'the same second must render the same frame');
  assert.notStrictEqual(a, c, 'a later second must move the performance on');
});

test('a walking beat travels across the stage instead of standing still', () => {
  const member = Cast.plan({ script: 'The reporter walks across the field toward the crowd, then heads out of frame.' }).cast[0];
  const start = Cast.Performance.frame(member, 0.5, { duration: 5 });
  const end = Cast.Performance.frame(member, 4.5, { duration: 5 });
  assert.ok(Cast.Performance.moving(member), 'a walking beat must be read as locomotion');
  assert.ok(Math.abs(end.offsetX - start.offsetX) > 0.1, 'the walker should cover ground');
});

test('a standing beat breathes without sliding off its mark', () => {
  const member = Cast.plan({ script: 'A presenter welcomes the audience and speaks to camera.' }).cast[0];
  const frames = [0.4, 1.3, 2.6, 4.1].map((t) => Cast.Performance.frame(member, t, { duration: 5 }));
  for (const f of frames) assert.ok(Math.abs(f.offsetX) < 0.02, `a standing figure drifted by ${f.offsetX}`);
  const tilts = frames.map((f) => f.pose.chest.tilt);
  assert.ok(new Set(tilts.map((t) => Math.round(t * 100))).size > 1, 'a standing figure must still breathe');
});

// ---------------------------------------------------------------------------
// Parametric bodies, contact goals, relations and the paperbook skin.
// ---------------------------------------------------------------------------

const Body = require(path.join(ROOT, 'runtime', 'cast-body.js'));
const Contact = require(path.join(ROOT, 'runtime', 'cast-contact.js'));
const Relation = require(path.join(ROOT, 'runtime', 'cast-relation.js'));
const Paperbook = require(path.join(ROOT, 'runtime', 'paperbook-figure.js'));

test('an infant is not a shrunken adult: head, limbs and stature all change shape', () => {
  const infant = Body.body('infant');
  const toddler = Body.body('toddler');
  const adult = Body.body({ age: 30 });
  const headShare = (b) => b.head / b.stature;
  assert.ok(headShare(infant) > headShare(toddler), 'infants are the most top-heavy');
  assert.ok(headShare(toddler) > headShare(adult) * 1.5, 'a toddler head reads much larger than an adult head');
  assert.ok(infant.stature < toddler.stature && toddler.stature < adult.stature);
  // Lengths are fractions of the body's own height, so this is shape, not size.
  assert.ok(infant.thigh < adult.thigh * 0.8, 'an infant has short legs for its own height');
});

test('age is continuous, not a set of presets', () => {
  const heights = [0.5, 2, 5, 9, 14, 30, 74].map((age) => Body.heightFor({ age }, 1000));
  for (let i = 1; i < heights.length - 1; i += 1) assert.ok(heights[i] > heights[i - 1], `age ${i} should be taller`);
  const between = Body.body({ age: 2.5 });
  const two = Body.body({ age: 2 });
  const three = Body.body({ age: 3 });
  assert.ok(between.stature > two.stature && between.stature < three.stature, 'in-between ages interpolate');
  assert.strictEqual(Body.ageBandOf(1.4), 'toddler');
  assert.strictEqual(Body.ageBandOf(0.4), 'infant');
});

test('a build changes mass without changing the age read', () => {
  const slight = Body.body({ age: 30, build: 'slight' });
  const broad = Body.body({ age: 30, build: 'broad' });
  assert.ok(broad.shoulderWidth > slight.shoulderWidth && broad.bodyDepth > slight.bodyDepth);
  assert.strictEqual(Math.round(broad.head * 1000), Math.round(slight.head * 1000));
});

test('a hand goal is reached: the character grips the prop instead of miming it', () => {
  const proportion = Body.body({ age: 32 });
  const oar = { id: 'oar', anchors: { grip: { x: 0.06, y: 0.12, z: 0.26 } } };
  const solved = Contact.solve({
    proportion,
    goals: [{ effector: 'rightHand', at: Contact.anchor(oar, 'grip') }]
  });
  assert.ok(solved.reached, `hand missed the oar by ${solved.residual}`);
  const joints = Contact.joints(proportion, solved.pose);
  const d = Math.hypot(joints.rightHand.x - 0.06, joints.rightHand.y - 0.12, joints.rightHand.z - 0.26);
  assert.ok(d < 0.02, `solved pose does not put the hand on the anchor (${d})`);
});

test('a foot goal plants the foot where the ground is, and unreachable goals say so', () => {
  const proportion = Body.body({ age: 30 });
  // Goals are pelvis-relative fractions of height, and the solver bends joints
  // rather than moving the root, so a step forward stays inside the leg's reach.
  const mark = { x: 0.09, y: -0.44, z: 0.17 };
  const step = Contact.solve({ proportion, goals: [{ effector: 'rightToe', at: mark }] });
  assert.ok(step.reached, `foot missed its mark by ${step.residual}`);
  const toe = Contact.joints(proportion, step.pose).rightToe;
  assert.ok(Math.hypot(toe.x - mark.x, toe.y - mark.y, toe.z - mark.z) < 0.02, 'the foot must land on the mark');
  assert.ok(step.pose.legRight.ankle.tilt !== 0, 'the ankle angles into the ground contact');
  const far = Contact.solve({ proportion, goals: [{ effector: 'rightHand', at: { x: 3, y: 2, z: 3 } }] });
  assert.ok(!far.reached && far.residual > 0.5, 'an out-of-reach goal must report failure, not fake success');
});

test('solving is deterministic and leaves untouched limbs alone', () => {
  const proportion = Body.body({ age: 30 });
  const goals = [{ effector: 'leftHand', at: { x: -0.08, y: 0.2, z: 0.24 } }];
  const a = Contact.solve({ proportion, goals });
  const b = Contact.solve({ proportion, goals });
  assert.deepStrictEqual(a.pose, b.pose);
  assert.deepStrictEqual(a.pose.legRight, Rig.mergePose({}).legRight, 'a hand goal must not rearrange the legs');
});

test('carry-on-back holds the pair together: child above the hips, hands in contact', () => {
  const rel = Relation.relate('carry-on-back', { carrier: { body: { age: 31 } }, carried: { body: { age: 3 } }, height: 900 });
  assert.strictEqual(rel.participants.length, 2);
  const [carrier, child] = rel.participants;
  assert.ok(child.height < carrier.height * 0.6, 'the child must be drawn as a child');
  assert.ok(child.origin.y > 0.3, 'the child rides on the back, it does not stand on the floor');
  assert.ok(child.origin.z < carrier.origin.z, 'the child is behind the carrier');
  assert.ok(rel.residual < 0.05, `contacts drifted by ${rel.residual}`);
  assert.ok(rel.preferredViews.length, 'a stacked pair must tell the compositor which views read');
});

test('support-walk puts both hands on the same point and the toddler mid-step', () => {
  const rel = Relation.relate('support-walk', { adult: { body: { age: 34 } }, toddler: { body: { age: 1.3 } }, height: 900 });
  const [adult, toddler] = rel.participants;
  assert.ok(rel.residual < 0.05, `the hands did not meet (${rel.residual})`);
  const contact = rel.contacts[0];
  assert.ok(contact.between.some((e) => e.startsWith('adult')) && contact.between.some((e) => e.startsWith('toddler')));
  const joints = Contact.joints(toddler.proportion, toddler.pose);
  assert.ok(Math.abs(joints.leftToe.z - joints.rightToe.z) > 0.04, 'one foot must be ahead of the other');
  assert.ok(adult.pose.spine.tilt > 4, 'the adult has to stoop to hold a toddler hand');
});

test('the paperbook renderer draws a valid, deterministic, patterned figure', () => {
  const look = { skin: '#b07f56', top: { color: '#7ba3bd' }, bottom: { garment: 'wrapper', color: '#e2d6bb', pattern: 'diamond', patternColor: '#b6552f' } };
  const svg = Paperbook.renderPose({ proportion: Body.body({ age: 30 }), height: 900, view: 'three-quarter-right', look, id: 'a' }).svg;
  assert.ok(svg.startsWith('<svg') && svg.endsWith('</svg>'));
  assert.ok(!/NaN|undefined/.test(svg), 'the figure contains an unresolved coordinate');
  assert.ok(svg.includes('<pattern'), 'a patterned wrapper must emit its pattern');
  assert.strictEqual(svg, Paperbook.renderPose({ proportion: Body.body({ age: 30 }), height: 900, view: 'three-quarter-right', look, id: 'a' }).svg);
});

test('a relation renders as one interleaved illustration, not two pasted figures', () => {
  const rel = Relation.relate('carry-on-back', { carrier: { body: { age: 31 }, yaw: 72 }, carried: { body: { age: 3 }, yaw: 72 }, height: 900 });
  const scene = Paperbook.renderRelation(rel, {});
  assert.ok(!/NaN|undefined/.test(scene.svg));
  const ids = [...scene.svg.matchAll(/data-id="([^"]+)"/g)].map((m) => m[1]);
  assert.ok(ids.includes('carrier') && ids.includes('carried'), 'both bodies must be drawn');
  const order = ids.join(' ');
  assert.ok(/carried .*carrier|carrier .*carried/.test(order));
  assert.ok(new Set(ids).size === 2 && ids.length > 4, 'bodies must be split into depth-sorted parts');
});

test('the public API exposes the artist, not just the catalogue', () => {
  const scene = Cast.illustrate('support-walk', { adult: { body: { age: 30 } }, toddler: { body: { age: 1.4 } }, height: 800 });
  assert.ok(scene.svg.includes('<svg'));
  assert.ok(Cast.body('toddler').stature < 0.6);
});

const failed = results.filter((r) => !r.ok);
for (const r of results) console.log(`${r.ok ? 'PASS' : 'FAIL'}  ${r.name}${r.ok ? '' : `\n      ${r.error}`}`);
console.log(`\n${results.length - failed.length}/${results.length} passed`);
process.exit(failed.length ? 1 : 0);
