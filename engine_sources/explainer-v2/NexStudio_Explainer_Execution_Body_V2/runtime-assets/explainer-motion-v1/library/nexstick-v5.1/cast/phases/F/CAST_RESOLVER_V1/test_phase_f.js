'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const R = require('./index.js');
const cases = require('./test_requests_v1.json');
const roleDoc = require('../ROLE_PRESETS_V1.json');

let passed = 0;
const failures = [];

function fail(id, e) { failures.push({id, message:e.message}); }
function candidateIds(slot) { return (slot.candidates || []).map(c => c.family_id); }
function allCandidates(out) { return out.slots.flatMap(s => s.candidates || []); }

for (const tc of cases) {
  try {
    const a = R.resolve(tc.input);
    const b = R.resolve(tc.input);
    assert.deepStrictEqual(a, b, `${tc.id}: resolver is not deterministic`);
    assert.strictEqual(a.deterministic, true, `${tc.id}: deterministic flag`);
    assert.strictEqual(a.status, tc.expect.status, `${tc.id}: status`);

    if (tc.expect.group_template) {
      assert.strictEqual(a.group_resolution.template_id, tc.expect.group_template, `${tc.id}: group template`);
      assert.strictEqual(a.group_resolution.demographic_assignment, 'unresolved', `${tc.id}: group demographics must remain unresolved`);
    }

    if (tc.expect.roles) {
      assert.deepStrictEqual(a.slots.map(s => s.role), tc.expect.roles, `${tc.id}: roles`);
    }
    if (tc.expect.counts) {
      assert.deepStrictEqual(a.slots.map(s => s.count), tc.expect.counts, `${tc.id}: counts`);
    }
    if (tc.expect.relation) {
      assert(a.relations.some(r => r.type === tc.expect.relation), `${tc.id}: missing relation ${tc.expect.relation}`);
    }
    if (tc.expect.must_include) {
      const ids = candidateIds(a.slots[0]);
      for (const id of tc.expect.must_include) assert(ids.includes(id), `${tc.id}: expected candidate ${id}`);
    }
    if (tc.expect.exact_families) {
      const ids = candidateIds(a.slots[0]).slice().sort();
      assert.deepStrictEqual(ids, tc.expect.exact_families.slice().sort(), `${tc.id}: exact families`);
    }
    if (tc.expect.must_exclude_age) {
      assert(!allCandidates(a).some(c => c.traits.age_group === tc.expect.must_exclude_age), `${tc.id}: excluded age leaked`);
    }
    if (tc.expect.final_family) {
      const spec = a.slots[0].final_cast_spec;
      assert(spec, `${tc.id}: missing final cast spec`);
      assert.strictEqual(spec.family, tc.expect.final_family, `${tc.id}: final family`);
    }
    if (tc.expect.clothing) {
      assert.strictEqual(a.slots[0].final_cast_spec.clothing.selected_tag, tc.expect.clothing, `${tc.id}: clothing override`);
    }
    if (tc.expect.personality) {
      assert.strictEqual(a.slots[0].final_cast_spec.personality.selected_preset, tc.expect.personality, `${tc.id}: personality override`);
    }
    if (tc.expect.warning_contains) {
      assert(a.warnings.some(w => w.includes(tc.expect.warning_contains)), `${tc.id}: expected warning`);
    }

    if (a.director_handoff) {
      assert.strictEqual(a.director_handoff.scene_layout, 'NOT_SELECTED_BY_PHASE_F', `${tc.id}: layout boundary`);
      assert.strictEqual(a.director_handoff.storyboard, 'NOT_SELECTED_BY_PHASE_F', `${tc.id}: storyboard boundary`);
    }
    passed++;
  } catch (e) { fail(tc.id, e); }
}

try {
  const roles = roleDoc.roles;
  assert.strictEqual(roles.length, 15, 'exactly 15 first-release role presets');
  assert.strictEqual(new Set(roles.map(r => r.role_id)).size, 15, 'role IDs unique');
  for (const role of roles) {
    assert.strictEqual(role.demographic_policy.gender, 'independent', `${role.role_id}: gender must be independent`);
    assert(!Object.prototype.hasOwnProperty.call(role, 'gender_default'), `${role.role_id}: no gender default`);
    assert(role.compatible_families.length > 0, `${role.role_id}: compatible families`);
    assert(role.clothing_tags.length > 0, `${role.role_id}: clothing tags`);
    assert(role.personality_defaults.length > 0, `${role.role_id}: personality defaults`);
  }
  const exec = roles.find(r=>r.role_id==='executive');
  const health = roles.find(r=>r.role_id==='healthcare_worker');
  const parent = roles.find(r=>r.role_id==='parent');
  const child = roles.find(r=>r.role_id==='child');
  assert.deepStrictEqual(exec.demographic_policy.age, {mode:'required',groups:['adult'],reason:'The first-release semantic model treats executive as an adult organizational role.'});
  assert.strictEqual(health.demographic_policy.age.mode, 'required');
  assert.strictEqual(parent.demographic_policy.age.mode, 'required');
  assert.deepStrictEqual(child.demographic_policy.age.groups, ['child']);
  passed++;
} catch(e) { fail('role-preset-policy',e); }

try {
  const c = R.contract();
  assert.strictEqual(c.randomCasting, false);
  assert(c.doesNotOwn.includes('motion engine'));
  assert(c.doesNotOwn.includes('scene layout'));
  assert(c.doesNotOwn.includes('storyboard'));
  const source = fs.readFileSync(path.join(__dirname,'index.js'),'utf8');
  assert(!/Math\.random|Date\.now|new Date\s*\(/.test(source), 'random/wall-clock source forbidden');
  passed++;
} catch(e) { fail('resolver-contract',e); }

console.log(JSON.stringify({status: failures.length ? 'FAIL' : 'PASS', request_cases_passed: passed - 2, request_cases_total: cases.length, supplemental_checks: 2, failures}, null, 2));
if (failures.length) process.exit(1);
