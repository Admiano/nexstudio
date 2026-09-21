#!/usr/bin/env node
/*
 * Runtime tests: run the execution-only runtime in headless Chromium against the
 * compiled fixture plans and assert determinism, plan-only behaviour and the
 * visible contracts (collision-free holds, replacement, media, still figure).
 *
 *   node tools/test_runtime.js            (compiles the fixtures first if needed; attaches to CDP_URL, default http://localhost:29229)
 *   CHROME_PATH=/path/to/chrome node tools/test_runtime.js   (launch a headless browser instead)
 */
const fs = require('fs');
const http = require('http');
const path = require('path');
const { spawnSync } = require('child_process');
const { chromium } = require('playwright-core');
const { AuthorshipLedger } = require('./authorship_gate');

const ROOT = path.resolve(__dirname, '..');
const ONLY = process.env.EM2_ONLY ? process.env.EM2_ONLY.split(',') : null;
const FIXTURES = [
  { name: 'reply-speed', treatment: '../fixtures/reply-speed.treatment.json', out: path.join(ROOT, 'out', 'reply-speed') },
  { name: 'water-to-thirsty', treatment: '../fixtures/water-to-thirsty/treatment.json', out: path.join(ROOT, 'out', 'water') },
  { name: 'edge-forms', treatment: '../fixtures/edge-forms/treatment.json', out: path.join(ROOT, 'out', 'edge-forms') },
  { name: 'blind-vinyl', treatment: '../fixtures/blind-vinyl/treatment.json', out: path.join(ROOT, 'out', 'blind-vinyl') },
  { name: 'vo-joe', treatment: '../fixtures/vo-joe/treatment.json', out: path.join(ROOT, 'out', 'vo-joe') },
  { name: 'chassis-demo', treatment: '../fixtures/chassis-demo/treatment.json', out: path.join(ROOT, 'out', 'chassis-demo') },
  { name: 'glyph-shelf', treatment: '../fixtures/glyph-shelf/treatment.json', out: path.join(ROOT, 'out', 'glyph-shelf') },
  { name: 'promo-collage', treatment: '../fixtures/promo-collage/treatment.json', out: path.join(ROOT, 'out', 'promo-collage') },
  { name: 'honey-nut-collage', treatment: '../fixtures/honey-nut-collage/treatment.json', out: path.join(ROOT, 'out', 'honey-nut-collage') },
  { name: 'media-matrix', treatment: '../fixtures/media-matrix/treatment.json', out: path.join(ROOT, 'out', 'media-matrix') },
];
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.webm': 'video/webm', '.woff2': 'font/woff2', '.ttf': 'font/ttf' };

function ensurePlans(fx) {
  if (['9x16', '1x1', '16x9'].every((a) => fs.existsSync(path.join(fx.out, `plan_${a}.json`)))) return;
  const r = spawnSync('python3', ['-m', 'editorial_plan_compiler', fx.treatment, fx.out], { cwd: path.join(ROOT, 'compiler'), stdio: 'inherit' });
  if (r.status !== 0) throw new Error(`fixture compile failed: ${fx.name}`);
}

function serve() {
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => {
      const url = decodeURIComponent(req.url.split('?')[0]);
      const file = url.startsWith('/fs/') ? url.slice(3) : path.join(ROOT, url);
      if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); res.end(); return; }
      const stat = fs.statSync(file);
      const type = MIME[path.extname(file)] || 'application/octet-stream';
      const range = req.headers.range;
      if (range) {
        const [s, e] = range.replace('bytes=', '').split('-');
        const start = Number(s), end = e ? Number(e) : stat.size - 1;
        res.writeHead(206, { 'Content-Type': type, 'Content-Range': `bytes ${start}-${end}/${stat.size}`, 'Accept-Ranges': 'bytes', 'Content-Length': end - start + 1 });
        fs.createReadStream(file, { start, end }).pipe(res);
        return;
      }
      res.writeHead(200, { 'Content-Type': type, 'Content-Length': stat.size, 'Accept-Ranges': 'bytes' });
      fs.createReadStream(file).pipe(res);
    });
    srv.listen(0, '127.0.0.1', () => resolve(srv));
  });
}

const PAGE = `<!doctype html><html><head><link rel="icon" href="data:,"></head><body style="margin:0"><div id="m" style="position:relative;width:100vw;height:100vh"></div>
<script src="/runtime/editorial-runtime.js"></script></body></html>`;

let failures = 0;
function check(name, ok, detail) {
  if (ok) { console.log(`  ok   ${name}`); return; }
  failures += 1;
  console.log(`  FAIL ${name}${detail ? ` — ${detail}` : ''}`);
}

// The frame walker itself: a pose held past the ceiling is named once, with its span; a pose
// that moves (even by ambient drift) or leaves the stage never is.
function ledgerSelfTest() {
  const fps = 30, ms = (i) => Math.round((i * 1000) / fps);
  const run = (sigOf) => {
    const l = new AuthorshipLedger(fps);
    for (let i = 0; i < fps * 6; i += 1) l.observe(ms(i), { entities: { 'b01:x': sigOf(i) }, findings: [] });
    return l.report();
  };
  const frozen = run(() => 'translate(1 1)|1|');
  const drifting = run((i) => `translate(${1 + 0.01 * Math.sin(i)} 1)|1|`);
  const brief = run((i) => (i < fps * 2 ? 'a' : i < fps * 4 ? 'b' : 'c'));
  const gone = run((i) => (i < fps * 2.5 ? 'a' : i < fps * 3.5 ? null : 'a'));
  const f = frozen.findings[0];
  check('authorship ledger: frozen pose named as STATIC_HOLD with its span',
    frozen.codes.join() === 'STATIC_HOLD' && frozen.findings.length === 1 && f.beat_id === 'b01' && f.id === 'x' && f.first_ms === 0 && Math.abs(f.last_ms - 6000) < 40, JSON.stringify(frozen));
  check('authorship ledger: drifting, re-posed and departed elements are not holds',
    drifting.findings.length === 0 && brief.findings.length === 0 && gone.findings.length === 0 && brief.longest_static_hold_ms <= 2000 + 1000 / fps,
    JSON.stringify({ d: drifting.codes, b: brief.longest_static_hold_ms, g: gone.longest_static_hold_ms }));
  const dup = new AuthorshipLedger(fps);
  for (let i = 0; i < 3; i += 1) dup.observe(ms(i), { entities: {}, findings: [{ code: 'EMPTY_CHASSIS', beat_id: 'b02', id: 'y', detail: 'd' }] });
  const d = dup.report().findings;
  check('authorship ledger: a per-frame finding collapses to one span', d.length === 1 && d[0].frames === 3 && d[0].first_ms === 0 && d[0].last_ms === ms(2), JSON.stringify(d));
}

async function main() {
  ledgerSelfTest();
  const srv = await serve();
  const base = `http://127.0.0.1:${srv.address().port}`;
  const chromePath = process.env.CHROME_PATH || '';
  const browser = chromePath
    ? await chromium.launch({ executablePath: chromePath, headless: true, args: ['--no-sandbox', '--disable-gpu'] })
    : await chromium.connectOverCDP(process.env.CDP_URL || 'http://localhost:29229');

  for (const fx of FIXTURES) {
    if (ONLY && !ONLY.includes(fx.name)) continue;
    ensurePlans(fx);
    fs.writeFileSync(path.join(fx.out, '_test_page.html'), PAGE);
    await runFixture(fx, base, browser);
    fs.rmSync(path.join(fx.out, '_test_page.html'), { force: true });
  }
  await browser.close();
  srv.close();
  console.log(failures ? `\n${failures} failure(s)` : '\nall runtime tests passed');
  process.exit(failures ? 1 : 0);
}

async function runFixture(fx, base, browser) {
  const outRel = path.relative(ROOT, fx.out);
  for (const aspect of ['9x16', '1x1', '16x9']) {
    console.log(`[${fx.name} ${aspect}]`);
    const plan = JSON.parse(fs.readFileSync(path.join(fx.out, `plan_${aspect}.json`), 'utf8'));
    const context = browser.contexts()[0] || (await browser.newContext());
    const page = await context.newPage();
    await page.setViewportSize({ width: plan.canvas.w, height: plan.canvas.h });
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e)));
    page.on('console', (m) => m.type() === 'error' && errors.push(m.text()));
    page.on('response', (res) => res.status() >= 400 && errors.push(`${res.status()} ${res.url()}`));
    await page.goto(`${base}/${outRel}/_test_page.html`);

    const r = await page.evaluate(async ({ planUrl, assetPrefix }) => {
      const plan = await (await fetch(planUrl)).json();
      const mount = document.getElementById('m');
      const R = window.EditorialRuntime;
      const out = { rejects: {} };
      try { R.createEditorialFilm({ schema: 'Other' }, mount, {}); out.rejects.schema = false; } catch (e) { out.rejects.schema = /NexStudioEditorialPlanV2/.test(e.message); }
      try { R.createEditorialFilm({ ...plan, gate: { status: 'FAIL', failures: ['x'] } }, mount, {}); out.rejects.gate = false; } catch (e) { out.rejects.gate = /gate is FAIL/.test(e.message); }
      const film = R.createEditorialFilm(plan, mount, { fontBase: '/assets/fonts/', peepsBase: '/assets/peeps/', assetUrl: (p) => (p.startsWith('/') ? assetPrefix + p : p) });
      await film.ready;
      window.__film = film;
      const stage = film.stage;
      out.stage = { w: stage.offsetWidth, h: stage.offsetHeight, aspect: stage.dataset.aspect };
      out.version = film.version;
      out.frames = film.frames;
      out.captions = film.captions.length;
      const ae = film.audioEvents();
      out.audio = { voice: ae.voice.segments.length, accents: ae.accents.length, music: ae.music.status };

      // The visible state is the active beat's subtree; hidden beats are display:none and not part of the frame.
      const snapshot = () => {
        const active = Array.from(stage.children).find((n) => n.style.display !== 'none');
        return active.dataset.beat + '::' + Array.from(active.querySelectorAll('[style]')).map((n) => n.getAttribute('style')).join('|');
      };
      const visibleTextRects = () => {
        const sr = stage.getBoundingClientRect();
        return Array.from(stage.querySelectorAll('.em2-block')).filter((n) => {
          const cs = getComputedStyle(n);
          let vis = cs.visibility !== 'hidden' && Number(cs.opacity) > 0.02;
          for (let p = n.parentElement; vis && p && p !== stage; p = p.parentElement) {
            const pcs = getComputedStyle(p);
            if (pcs.display === 'none' || pcs.visibility === 'hidden' || Number(pcs.opacity) < 0.02) vis = false;
          }
          if (!vis) return false;
          const lines = Array.from(n.querySelectorAll('.em2-line'));
          const unclipped = (v) => v === 'none' || (/^inset\(([\d.% ]+)\)$/.test(v) && v.match(/[\d.]+/g).every((x) => Number(x) < 0.5));
          return lines.some((l) => Number(getComputedStyle(l).opacity) > 0.5 && unclipped(getComputedStyle(l).clipPath)) && unclipped(cs.clipPath);
        }).map((n) => {
          const r = n.getBoundingClientRect();
          return { id: n.dataset.unit, x: r.left - sr.left, y: r.top - sr.top, w: r.width, h: r.height };
        });
      };

      // Determinism: same time reached via different paths gives an identical DOM state.
      out.determinism = [];
      for (const t of [900, 4200, Math.round(plan.duration_ms * 0.5), plan.duration_ms - 300]) {
        await film.seek(t); const a = snapshot();
        await film.seek(0); await film.seek(plan.duration_ms); await film.seek(t + 137); await film.seek(t); const b = snapshot();
        out.determinism.push(a === b);
      }
      await film.frame(120); const f1 = snapshot(); await film.seek(Math.round((120 * 1000) / plan.fps)); out.frameAddress = f1 === snapshot();

      // Holds: every beat's hold window shows all of its authored blocks, none colliding, all inside the canvas.
      out.holds = [];
      for (const b of plan.beats) {
        const t = b.start_ms + b.ensemble.hold_window.start_ms + 10;
        await film.seek(t);
        const rects = visibleTextRects();
        const inside = rects.every((r) => r.x >= -1 && r.y >= -1 && r.x + r.w <= plan.canvas.w + 1 && r.y + r.h <= plan.canvas.h + 1);
        let collide = false;
        for (let i = 0; i < rects.length; i += 1) for (let j = i + 1; j < rects.length; j += 1) {
          const a = rects[i], c = rects[j];
          const ua = b.typography.blocks.find((x) => String(x.unit_index) === a.id), uc = b.typography.blocks.find((x) => String(x.unit_index) === c.id);
          const sameReplace = ua && uc && ua.style.startsWith('replace_stage') && uc.style.startsWith('replace_stage');
          if (sameReplace) continue;
          if (a.x < c.x + c.w - 2 && c.x < a.x + a.w - 2 && a.y < c.y + c.h - 2 && c.y < a.y + a.h - 2) collide = true;
        }
        const expected = b.typography.blocks.filter((x) => !x.style.startsWith('replace_stage_a')).length;
        out.holds.push({ beat: b.beat_id, visible: rects.length, expected, inside, collide });
      }

      // Before the first landing nothing has settled yet.
      const first = plan.beats[0];
      await film.seek(first.start_ms + 20);
      out.preLanding = visibleTextRects().length === 0;

      // Phrase replacement: stage A shows before stage B, then yields to it.
      const rb = plan.beats.find((b) => b.typography.blocks.some((x) => x.style === 'replace_stage_b'));
      if (rb) {
        const a = rb.typography.blocks.find((x) => x.style === 'replace_stage_a'), bb = rb.typography.blocks.find((x) => x.style === 'replace_stage_b');
        const rep = rb.typography.events.find((e) => e.event === 'PHRASE_REPLACE' && e.unit_index === bb.unit_index);
        await film.seek(rb.start_ms + rep.start_ms - 40);
        const before = visibleTextRects().map((r) => r.id);
        await film.seek(rb.start_ms + rep.end_ms + 200);
        const after = visibleTextRects().map((r) => r.id);
        out.replace = { before: before.includes(String(a.unit_index)) && !before.includes(String(bb.unit_index)), after: after.includes(String(bb.unit_index)) && !after.includes(String(a.unit_index)) };
      }

      // Media evidence: the content is hidden before its landing (the frame chrome may
      // legitimately be on stage early — chrome is stage furniture, the evidence is not),
      // present after; video honours trim.
      out.media = [];
      for (const b of plan.beats.filter((x) => x.media)) {
        const beatNode = stage.children[plan.beats.indexOf(b)];
        const frame = beatNode.querySelector('img, video').parentElement;
        const content = frame.querySelector('img, video');
        await film.seek(b.start_ms + Math.max(0, b.media.enter_ms - 30));
        const hiddenBefore = b.media.enter_ms === 0 ? true : (getComputedStyle(content).visibility === 'hidden' || Number(getComputedStyle(content).opacity) < 0.05);
        await film.seek(b.start_ms + b.media.enter_ms + b.media.enter_duration_ms + 50);
        const shown = getComputedStyle(frame).visibility !== 'hidden' && Number(getComputedStyle(frame).opacity) > 0.95;
        const node = frame.querySelector('img, video');
        let videoOk = true;
        if (node.tagName === 'VIDEO') {
          await film.seek(b.start_ms + b.media.enter_ms + 1000);
          const expected = ((b.media.trim && b.media.trim.start) || 0) + 1.0;
          videoOk = Math.abs(node.currentTime - expected) < 0.1;
        }
        out.media.push({ beat: b.beat_id, hiddenBefore, shown, videoOk, loaded: node.tagName === 'VIDEO' ? node.readyState >= 2 : node.complete && node.naturalWidth > 0 });
      }
      // Entity-level media: a MEDIA glyph can carry live video inside any chassis — it must
      // be a real <video>, decode-ready and seeking with the film clock (not a static poster).
      for (const b of plan.beats.filter((x) => x.illustration)) {
        const beatNode = stage.children[plan.beats.indexOf(b)];
        for (const e of b.illustration.entities.filter((en) => en.media && en.media.kind === 'VIDEO')) {
          const frame = beatNode.querySelector(`[data-media-asset="${e.media.asset_id}"]`);
          const node = frame && frame.querySelector('video');
          let videoOk = false, loaded = false;
          if (node) {
            await film.seek(b.start_ms + e.enter_ms + 1200);
            const expected = ((e.media.trim && e.media.trim.start) || 0) + 1.2;
            videoOk = Math.abs(node.currentTime - expected) < 0.1;
            loaded = node.readyState >= 2;
          }
          out.media.push({ beat: b.beat_id, entity: e.id, hiddenBefore: true, shown: Boolean(node), videoOk, loaded });
        }
      }

      // Device chassis: every housed upload (entity- or beat-level) sits in the slab the plan
      // chose, the content never shows before its slab, the slab is never shown empty, and the
      // content stays inside the screen through entrance, hold drift and carry reframes.
      out.chassis = [];
      const housed = [];
      for (const b of plan.beats) {
        if (b.media) housed.push({ b, md: b.media, enter: b.media.enter_ms, dur: b.media.enter_duration_ms, reframe: b.media.reframe, id: b.media.asset_id });
        for (const e of (b.illustration ? b.illustration.entities : []).filter((x) => x.media)) housed.push({ b, md: e.media, enter: e.enter_ms, dur: e.enter_duration_ms, reframe: e.carry_from_bbox ? { start_ms: 0, end_ms: 420 } : null, id: e.media.asset_id, entity: e.id });
      }
      for (const h of housed) {
        const beatNode = stage.children[plan.beats.indexOf(h.b)];
        const frame = beatNode.querySelector(`[data-media-asset="${h.id}"]`);
        const rec = { beat: h.b.beat_id, id: h.id, chassis: frame && frame.dataset.chassis, wanted: h.md.chassis, slab: false, screen: false, contentIn: true, neverEmpty: true, live: h.md.kind !== 'VIDEO', tilt: true, samples: 0 };
        if (!frame) { out.chassis.push(rec); continue; }
        const slab = frame.querySelector('.em2-slab'), screen = frame.querySelector('.em2-screen'), node = frame.querySelector('img, video');
        rec.slab = Boolean(slab) && slab.contains(screen); rec.screen = Boolean(screen) && screen.contains(node);
        rec.tilt = Math.abs((Number(/rotate\((-?[\d.]+)deg\)/.exec(slab.style.transform)[1]) || 0) - (h.md.tilt || 0)) < 0.02;
        const shown = () => getComputedStyle(frame).visibility !== 'hidden' && Number(frame.style.opacity) > 0.05;
        const t0 = h.b.start_ms;
        const times = [];
        for (let t = h.enter - 200; t <= h.enter + (h.dur || 0) + 60; t += 1000 / plan.fps) times.push(t);
        if (h.reframe) for (let t = h.reframe.start_ms; t <= h.reframe.end_ms + 60; t += 1000 / plan.fps) times.push(t);
        const settled = h.enter + (h.dur || 0);
        for (let t = settled; t < h.b.duration_ms - 60; t += 400) times.push(t);
        for (const lt of times) {
          if (lt < 0) continue;
          await film.seek(Math.round(t0 + lt));
          const vis = shown();
          if (lt < h.enter && vis) rec.neverEmpty = false;   // slab may not dress the stage before its content
          if (!vis) continue;
          rec.samples += 1;
          // Content covers its viewport (the screen, or the pane under a browser bar) — no bare
          // screen showing; sub-pixel slack.
          const sr = node.parentElement.getBoundingClientRect(), nr = node.getBoundingClientRect();
          if (nr.left > sr.left + 1.5 || nr.top > sr.top + 1.5 || nr.right < sr.right - 1.5 || nr.bottom < sr.bottom - 1.5) rec.contentIn = false;
          if (Number(node.style.opacity || '1') < 0.05 && lt >= settled) rec.neverEmpty = false;
        }
        if (h.md.kind === 'VIDEO') {
          await film.seek(Math.round(t0 + settled + 900));
          const expected = ((h.md.trim && h.md.trim.start) || 0) + (settled + 900 - h.enter) / 1000;
          rec.live = node.readyState >= 2 && Math.abs(node.currentTime - expected) < 0.1;
        }
        out.chassis.push(rec);
      }

      // Still figure: composed from the compiled parts only, visible in its hold, never animated after entry.
      const fb = plan.beats.find((b) => b.figure);
      if (fb) {
        const beatNode = stage.children[plan.beats.indexOf(fb)];
        const slots = Array.from(beatNode.querySelectorAll('svg g[data-slot]')).map((g) => g.dataset.slot);
        const figSvg = beatNode.querySelector('svg g[data-slot]').closest('svg');
        const paths = figSvg.querySelectorAll('path').length;
        await film.seek(fb.start_ms + fb.figure.enter_ms + fb.figure.enter_duration_ms + 10);
        const host = figSvg.parentElement;
        const s1 = host.getAttribute('style');
        await film.seek(fb.start_ms + fb.ensemble.hold_window.end_ms - 10);
        const s2 = host.getAttribute('style');
        out.figure = { slots, paths, stillDuringHold: s1 === s2, visible: getComputedStyle(host).visibility !== 'hidden' && Number(getComputedStyle(host).opacity) > 0.95 };
      }
      // Illustration programs: entities exist once, hide before entry, run their ops to the authored end values,
      // carry state across beats, and never sit on the copy during the hold.
      out.illustration = [];
      const num = (v) => parseFloat(String(v)) || 0;
      for (const b of plan.beats.filter((x) => x.illustration)) {
        const il = b.illustration;
        const beatNode = stage.children[plan.beats.indexOf(b)];
        const groups = Array.from(beatNode.querySelectorAll('g[data-entity]'));
        const rec = { beat: b.beat_id, form: il.form, entities: groups.length === il.entities.length, hiddenBefore: true, ops: [], carried: true, collide: false };
        const gOf = (id) => groups.find((g) => g.dataset.entity === id);
        for (const e of il.entities) {
          if (e.enter_ms > 30) {
            await film.seek(b.start_ms + e.enter_ms - 20);
            if (getComputedStyle(gOf(e.id)).visibility !== 'hidden') rec.hiddenBefore = false;
          }
        }
        await film.seek(b.start_ms + 5);
        for (const e of il.entities.filter((x) => x.carried)) {
          const g = gOf(e.id);
          if (getComputedStyle(g).visibility === 'hidden' || Number(g.style.opacity) < 0.4) rec.carried = false;
          if (e.state_in.ink === 1 && !Array.from(g.querySelectorAll('[fill-opacity]')).some((n) => Number(n.getAttribute('fill-opacity')) > 0.95)) rec.carried = false;
          if (e.state_in.fill > 0 && !Array.from(g.querySelectorAll('rect')).some((n) => Number(n.getAttribute('height')) > 4)) rec.carried = false;
        }
        for (const op of il.ops) {
          const isRel = op.target.includes('->');
          const node = isRel ? beatNode.querySelector(`g[data-relation="${op.target}"]`) : gOf(op.target);
          if (!node) { rec.ops.push({ op: op.op, target: op.target, ok: false, why: 'no node' }); continue; }
          const transient = op.op === 'SETTLE' || op.op === 'TRACE';
          await film.seek(b.start_ms + op.start_ms - 5);
          const before = node.outerHTML;
          await film.seek(b.start_ms + (transient ? Math.round((op.start_ms + op.end_ms) / 2) : op.end_ms + 5));
          const after = node.outerHTML;
          let ok = before !== after;
          let why = ok ? '' : 'no visible change';
          const drawn = (n, role) => Array.from(n.querySelectorAll(`[data-draw="${role}"]`));
          const outlineDone = (n) => {
            const solid = drawn(n, 'outline'), covers = drawn(n, 'cover'), bodies = drawn(n, 'body');
            return (solid.length + covers.length + bodies.length) > 0 && solid.every((p) => num(p.style.strokeDashoffset) < 0.5)
              && covers.every((p) => -num(p.style.strokeDashoffset) >= num(p.style.strokeDasharray) - 0.5)
              && bodies.every((p) => num(p.style.opacity || '1') > 0.99);
          };
          if (op.op === 'FILL') { const r = node.querySelector('rect[clip-path]'); ok = r && Math.abs(num(r.getAttribute('height')) / (node.getBBox().height || 1) - op.to) < 0.12; why = r && r.getAttribute('height'); }
          if (op.op === 'INK') { ok = Array.from(node.querySelectorAll('[fill-opacity]')).some((n) => Math.abs(Number(n.getAttribute('fill-opacity')) - op.to) < 0.02) || (node.querySelector('g') && node.querySelector('g').style.color !== ''); }
          if (op.op === 'DIM') { ok = Math.abs(Number(node.style.opacity) - op.to) < 0.03; why = node.style.opacity; }
          if (op.op === 'DRAW' || op.op === 'CONNECT') {
            if (op.params && op.params.wipe) {
              // Draw-then-erase: at op end the traveling window has fully exited — stroked parts
              // sit at offset ±len (never drawn / erased), dashed covers reclosed to a full-cover
              // dash, and opacity-driven parts faded out with the sweep pulse.
              const solid = drawn(node, 'outline'), covers = drawn(node, 'cover');
              ok = solid.length + covers.length > 0
                && solid.every((p) => {
                  if (!p.style.strokeDasharray) {
                    const so = p.getAttribute('stroke-opacity');
                    return (so === null || num(so) < 0.05) && num(p.style.opacity || '0') < 0.05;
                  }
                  const L = p.getTotalLength ? p.getTotalLength() : 0;
                  return L === 0 || Math.abs(num(p.style.strokeDashoffset)) >= L - 0.5;
                })
                && covers.every((p) => {
                  const da0 = num(String(p.style.strokeDasharray || '0').split(/[ ,]+/)[0]);
                  return da0 >= (p.getTotalLength ? p.getTotalLength() : 0) - 0.5;
                });
              why = ok ? '' : 'wiped stroke not erased at op end';
            } else {
              ok = outlineDone(node); why = ok ? '' : 'outline not fully drawn';
            }
          }
          if (op.op === 'STRIKE') { const ps = drawn(node, 'strike'); ok = ps.length > 0 && ps.every((p) => num(p.style.strokeDashoffset) < 0.5); why = ok ? '' : 'strike not drawn'; }
          if (op.op === 'TRAVEL') {
            const lens = node.querySelector('g[transform]');
            const target = il.entities.find((x) => x.id === op.params.over[op.params.over.length - 1]).bbox;
            const m = /translate\(([-\d.]+) ([-\d.]+)\)/.exec(lens.getAttribute('transform'));
            ok = m && Math.abs(Number(m[1]) - (target.x + target.w / 2)) < 1 && Math.abs(Number(m[2]) - (target.y + target.h / 2)) < 1;
            why = lens.getAttribute('transform');
          }
          if (op.op === 'GROW') { const r = node.querySelector('rect[data-grow]') || node.querySelector('rect'); if (r) { ok = Math.abs(num(r.getAttribute('height')) / il.entities.find((x) => x.id === op.target).bbox.h - op.to) < 0.05; why = r.getAttribute('height'); } }
          // Persistent EMITs leave visible embers; a fully decaying pulse (to:0) is verified by the
          // before/after pixel diff alone.
          if (op.op === 'EMIT' && op.to !== 0) {
            ok = Array.from(node.querySelectorAll('circle')).some((c) => Number(c.getAttribute('stroke-opacity')) > 0.3)
              || Array.from(node.querySelectorAll('[data-halo]')).some((h) => Number(h.getAttribute('fill-opacity')) > 0.05);
          }
          rec.ops.push({ op: op.op, target: op.target, ok: Boolean(ok), why });
        }
        // Accent discipline: at the settled state only state-change ops may have introduced the accent colour.
        await film.seek(b.start_ms + il.settled_ms + 10);
        const accent = (il.accent || '').toLowerCase();
        const usesAccent = Array.from(beatNode.querySelectorAll('svg [fill], svg [stroke]')).filter((n) => {
          const f = (n.getAttribute('fill') || '').toLowerCase(), s = (n.getAttribute('stroke') || '').toLowerCase();
          const fo = n.hasAttribute('fill-opacity') ? Number(n.getAttribute('fill-opacity')) : 1;
          const so = n.hasAttribute('stroke-opacity') ? Number(n.getAttribute('stroke-opacity')) : 1;
          return (f === accent && fo > 0.05) || (s === accent && so > 0.05);
        }).length;
        const stateChanges = il.ops.filter((o) => o.state_change).length + il.entities.filter((e) => e.state_in && (e.state_in.ink > 0 || e.state_in.fill > 0 || e.state_in.emit > 0)).length;
        rec.accent = { usesAccent, stateChanges, ok: accent === '' || stateChanges > 0 || usesAccent === 0 };
        // Hold: entity boxes clear of every visible text block.
        await film.seek(b.start_ms + b.ensemble.hold_window.start_ms + 10);
        const texts = visibleTextRects();
        const sr = stage.getBoundingClientRect();
        for (const g of groups) {
          if (getComputedStyle(g).visibility === 'hidden' || Number(g.style.opacity) < 0.05) continue;
          const r = g.getBoundingClientRect();
          const gb = { x: r.left - sr.left, y: r.top - sr.top, w: r.width, h: r.height };
          for (const t of texts) if (gb.x < t.x + t.w - 2 && t.x < gb.x + gb.w - 2 && gb.y < t.y + t.h - 2 && t.y < gb.y + gb.h - 2) rec.collide = true;
        }
        out.illustration.push(rec);
      }

      // Word cascade: words land one by one on their voice timings; stressed words settle heavier.
      out.cascade = [];
      for (const b of plan.beats) {
        for (const blk of b.typography.blocks.filter((x) => x.reveal === 'WORD_CASCADE' && x.words && x.words.length > 1)) {
          const beatNode = stage.children[plan.beats.indexOf(b)];
          const wrap = Array.from(beatNode.querySelectorAll('.em2-block')).find((n) => n.dataset.unit === String(blk.unit_index) && n.dataset.style === blk.style);
          const spans = Array.from(wrap.querySelectorAll('.em2-word'));
          const w0 = blk.words[0], w1 = blk.words[1];
          await film.seek(b.start_ms + Math.min(w0.start_ms + 300, w1.start_ms - 1));
          const firstOnly = Number(spans[0].style.opacity) > 0.5 && Number(spans[1].style.opacity) < 0.05;
          await film.seek(b.start_ms + blk.cascade_end_ms + 20);
          const all = spans.every((s) => Number(s.style.opacity) > 0.3 && s.style.filter === 'none');
          const stressed = spans.filter((s) => s.dataset.stress);
          const wghtOf = (s) => Number((s.style.fontVariationSettings.match(/\d+/) || [0])[0]);
          const scaleOf = (s) => Number((/scale\(([\d.]+)\)/.exec(s.style.transform) || [0, 1])[1]);
          const plain = spans.find((x) => !x.dataset.stress);
          // A stressed word must read as a state: heavier than its neighbours, or (already at Black) set larger.
          const sizeOf = (s) => parseFloat(getComputedStyle(s).fontSize);
          const heavier = stressed.every((s) => !plain || wghtOf(s) > wghtOf(plain) || sizeOf(s) > sizeOf(plain) * 1.02 || scaleOf(s) > scaleOf(plain) + 0.02);
          out.cascade.push({ beat: b.beat_id, unit: blk.unit_index, words: spans.length === blk.words.length, firstOnly, all, heavier });
        }
      }

      // Authorship inspection: every rendered frame of the film, as the render tool sees it.
      out.inspections = [];
      for (let t = 0; t < plan.duration_ms; t += 1000 / plan.fps) {
        await film.seek(Math.round(t));
        out.inspections.push({ ms: Math.round(t), snap: film.inspect() });
      }
      // Negative proofs: break the scene graph the way a bad asset or a stray connector would, and the
      // inspector must name it. Each mutation is undone before the next.
      out.authorshipNeg = {};
      const hostShown = (h) => {
        const g = h.closest('[data-entity]');
        return h.firstElementChild && h.querySelector('path,circle,rect,polygon,ellipse') && g.style.visibility !== 'hidden' && Number(g.style.opacity) > 0.5;
      };
      for (const b of plan.beats) {
        if (!b.illustration) continue;
        // A worded chip is content in its own right, so emptying its peg is not an empty housing.
        const hosted = b.illustration.entities.filter((e) => e.asset && (['TILE', 'BADGE'].includes(e.glyph) || (e.glyph === 'CHIP' && !e.label)));
        if (!hosted.length) continue;
        await film.seek(b.start_ms + b.illustration.settled_ms + 40);
        const beatNode = stage.children[plan.beats.indexOf(b)];
        const host = Array.from(beatNode.querySelectorAll('[data-icon-host]')).find((h) => hostShown(h) && hosted.some((e) => e.id === h.dataset.iconHost));
        if (!host) continue;
        const inner = host.firstElementChild;
        const codes = () => film.inspect().findings.filter((f) => f.id === host.dataset.iconHost).map((f) => f.code);
        out.authorshipNeg.clean = codes();
        const tf = inner.getAttribute('transform');
        inner.setAttribute('transform', `${tf} scale(0.05)`);
        out.authorshipNeg.underfill = codes();
        inner.setAttribute('transform', `${tf} scale(4)`);
        out.authorshipNeg.overflow = codes();
        inner.setAttribute('transform', tf);
        const html = inner.innerHTML;
        inner.innerHTML = '';
        out.authorshipNeg.empty = codes();
        inner.innerHTML = html;
        out.authorshipNeg.restored = codes();
        break;
      }
      for (const b of plan.beats) {
        if (!b.illustration || !b.illustration.relations.length) continue;
        const rel = b.illustration.relations[0];
        await film.seek(b.start_ms + b.illustration.settled_ms + 40);
        const beatNode = stage.children[plan.beats.indexOf(b)];
        const rg = beatNode.querySelector(`[data-relation="${rel.id}"]`);
        if (!rg || rg.style.visibility === 'hidden' || Number(rg.style.opacity) < 0.3) continue;
        const end = beatNode.querySelector(`[data-entity="${rel.source}"]`);
        const codes = () => film.inspect().findings.filter((f) => f.id === rel.id).map((f) => f.code);
        out.authorshipNeg.connectorClean = codes();
        const op = end.style.opacity;
        end.style.opacity = '0';
        out.authorshipNeg.orphan = codes();
        end.style.opacity = op;
        break;
      }

      // Motion system: springs, motion blur, secondary motion, camera grammar.
      const scaleOfSvg = (g) => Number((/scale\(([\d.]+)\)/.exec(g.getAttribute('transform') || '') || [0, 1])[1]);
      const blurOn = (elm) => {
        const m = /url\("?#([^)"]+)"?\)/.exec(elm.style.filter || '');
        if (!m) return false;
        const fe = document.getElementById(m[1]).querySelector('feGaussianBlur');
        return fe.getAttribute('stdDeviation').split(' ').some((v) => Number(v) > 0.05);
      };
      out.motion = { springs: [], blur: [], labels: [], connectors: [], camera: [] };
      for (const b of plan.beats) {
        if (!b.illustration) continue;
        const beatNode = stage.children[plan.beats.indexOf(b)];
        for (const e of b.illustration.entities) {
          if (!e.enter_duration_ms || e.enter_duration_ms < 120 || e.carry_from_bbox) continue;
          const g = beatNode.querySelector(`[data-entity="${e.id}"]`);
          const t0 = b.start_ms + e.enter_ms, d = e.enter_duration_ms;
          const samples = [];
          for (const f of [0.05, 0.15, 0.3, 0.5, 0.7, 0.9]) { await film.seek(Math.round(t0 + d * f)); samples.push({ f, scale: scaleOfSvg(g), opacity: Number(g.style.opacity), blur: blurOn(g) }); }
          await film.seek(t0 + d + 600);
          // Rest is judged only when no program op (a GROW, EMIT, SWAP…) is legitimately reshaping the body.
          const restLt = e.enter_ms + d + 600;
          const busy = b.illustration.ops.some((o) => o.target === e.id && o.op !== 'DRAW' && o.start_ms <= restLt && o.end_ms >= restLt);
          const rest = { scale: busy ? 1 : scaleOfSvg(g), blur: blurOn(g) };
          const monotone = samples.every((s, i) => i === 0 || s.opacity >= samples[i - 1].opacity - 1e-4) && samples.every((s) => s.opacity <= 1 + 1e-4);
          const peak = Math.max(...samples.map((s) => s.scale));
          out.motion.springs.push({ beat: b.beat_id, id: e.id, monotone, peak, overshoot: peak > 1.02, rest: Math.abs(rest.scale - 1) < 0.03 });
          // A pop arrival (60%→100%) travels far enough per frame to smear; the editorial 94%→100% landing is below the blur floor by design.
          out.motion.blur.push({ beat: b.beat_id, id: e.id, moving: (plan.motion || {}).entrance !== 'pop' || samples.slice(0, 3).some((s) => s.blur), still: !rest.blur });
          if (out.motion.springs.length >= 6) break;
        }
        // Labels ride their bodies: the label's centre keeps its laid-out offset from the body's
        // centre (scaled with the body) through the whole entrance and carry, whatever the lag.
        for (const e of b.illustration.entities) {
          const g = beatNode.querySelector(`[data-entity="${e.id}"]`);
          const lab = beatNode.querySelector(`.em2-il-label[data-entity="${e.id}"]`);
          if (!lab || !g || !e.label) continue;
          const laidOut = (e.label.bbox.x + e.label.bbox.w / 2 - (e.bbox.x + e.bbox.w / 2)) / e.bbox.w;
          const span = e.carry_from_bbox ? 420 : (e.enter_duration_ms || 0);
          let worst = 0;
          for (let t = b.start_ms + (e.carry_from_bbox ? 0 : e.enter_ms); t <= b.start_ms + (e.carry_from_bbox ? 0 : e.enter_ms) + span + 300; t += 1000 / plan.fps) {
            await film.seek(Math.round(t));
            if (Number(lab.style.opacity) < 0.2 || Number(g.style.opacity) < 0.2) continue;
            const rb = g.getBoundingClientRect(), rl = lab.getBoundingClientRect();
            if (!rb.width || !rl.width) continue;
            worst = Math.max(worst, Math.abs(((rl.left + rl.width / 2) - (rb.left + rb.width / 2)) / rb.width - laidOut));
          }
          out.motion.labels.push({ beat: b.beat_id, id: e.id, worst, ok: worst < 0.12 });
          if (out.motion.labels.length >= 6) break;
        }
        // Connectors ride their endpoints: the drawn start point keeps its offset from the
        // source body while the body drifts through the hold.
        for (const rel of b.illustration.relations) {
          const rg = beatNode.querySelector(`[data-relation="${rel.id}"]`);
          if (!rg || !rel.path) continue;
          const near = { g: beatNode.querySelector(`[data-entity="${rel.source}"]`), ent: b.illustration.entities.find((x) => x.id === rel.source) };
          if (!near.g || !near.ent) continue;
          const path = rg.querySelector('path');
          // Measured in the illustration's own canvas space so the camera's scale during a cut cannot masquerade as drift.
          const svg = rg.closest('svg');
          const apply = (m, p) => { const q = svg.getScreenCTM().inverse().multiply(m); return [q.a * p[0] + q.c * p[1] + q.e, q.b * p[0] + q.d * p[1] + q.f]; };
          const centreOf = (end) => apply(end.g.getScreenCTM(), [end.ent.bbox.x + end.ent.bbox.w / 2, end.ent.bbox.y + end.ent.bbox.h / 2]);
          const hold0 = b.start_ms + b.illustration.settled_ms + 60;
          const at = async (t) => {
            await film.seek(t);
            if (Number(rg.style.opacity) < 0.3) return null;
            const q = apply(path.getScreenCTM(), rel.path[0]), cc = centreOf(near);
            return { x: q[0] - cc[0], y: q[1] - cc[1] };
          };
          const a = await at(hold0), c = await at(Math.min(hold0 + 1900, b.start_ms + b.duration_ms - 60));
          if (!a || !c) continue;
          out.motion.connectors.push({ beat: b.beat_id, id: rel.id, drift: Math.hypot(a.x - c.x, a.y - c.y) });
          break;
        }
      }
      // Camera: every cut is the move the compiler chose, made by the outgoing picture.
      for (let i = 0; i + 1 < plan.beats.length; i += 1) {
        const b = plan.beats[i], tr = b.transition;
        if (!tr || !tr.camera || tr.end_ms <= tr.start_ms) continue;
        const cam = stage.children[i].firstElementChild;
        await film.seek(b.start_ms + tr.start_ms - 40);
        const before = { tx: Number((/translate\((-?[\d.]+)px/.exec(cam.style.transform) || [0, 0])[1]), scale: Number((/scale\(([\d.]+)\)/.exec(cam.style.transform) || [0, 1])[1]) };
        await film.seek(Math.round(b.start_ms + tr.start_ms + (tr.end_ms - tr.start_ms) * 0.4));
        const mid = { tx: Number((/translate\((-?[\d.]+)px/.exec(cam.style.transform) || [0, 0])[1]), scale: Number((/scale\(([\d.]+)\)/.exec(cam.style.transform) || [0, 1])[1]), opacity: Number(cam.style.opacity), blur: blurOn(cam) };
        const incoming = stage.children[i + 1];
        const moved = cam.style.transform !== stage.children[i + 1].firstElementChild.style.transform;
        let ok;
        if (tr.camera.move === 'push_through') ok = mid.scale > before.scale + 0.003 && mid.opacity < 0.9;
        else if (tr.camera.move === 'pull_back') ok = mid.scale < before.scale - 0.003 && mid.opacity < 0.9;
        else if (tr.camera.move === 'drift') ok = Math.abs(mid.tx - before.tx) > 5 && mid.opacity < 0.9 && mid.blur;
        else ok = Math.abs(mid.scale - before.scale) < 0.01 && Math.abs(mid.tx - before.tx) < 2;
        out.motion.camera.push({ beat: b.beat_id, move: tr.camera.move, ok: ok && incoming.style.display === 'block' && moved, before, mid });
      }

      // Per-frame scene-graph cost: seek every frame of the busiest illustration beat.
      const busy = plan.beats.filter((x) => x.illustration).sort((a, c) => c.illustration.ops.length - a.illustration.ops.length)[0] || plan.beats[0];
      const p0 = film.perf.frames;
      for (let t = busy.start_ms; t < busy.start_ms + busy.duration_ms; t += 1000 / plan.fps) await film.seek(Math.round(t));
      out.perf = { frames: film.perf.frames - p0, avg_ms: film.perf.avg_ms, max_ms: film.perf.max_ms };
      return out;
    }, { planUrl: `/${outRel}/plan_${aspect}.json`, assetPrefix: '/fs' });

    check('rejects foreign schema', r.rejects.schema);
    check('refuses failed gate', r.rejects.gate);
    check('runtime version exposed', r.version === 'EDITORIAL_RUNTIME_V3.2', r.version);
    check(`stage is native ${plan.canvas.w}x${plan.canvas.h}`, r.stage.w === plan.canvas.w && r.stage.h === plan.canvas.h && r.stage.aspect === aspect, JSON.stringify(r.stage));
    check('frame count matches plan', r.frames === Math.ceil((plan.duration_ms * plan.fps) / 1000));
    check('captions and audio events exposed', r.captions > 0 && r.audio.voice === plan.voice.segments.length && r.audio.accents > 0 && r.audio.music === plan.music.status, JSON.stringify(r.audio));
    check('seek is deterministic across paths', r.determinism.every(Boolean), JSON.stringify(r.determinism));
    check('frame(n) equals seek(n/fps)', r.frameAddress);
    check('nothing settled before first landing', r.preLanding);
    for (const h of r.holds) check(`hold ${h.beat}: ${h.visible}/${h.expected} blocks, inside, no collision`, h.visible === h.expected && h.inside && !h.collide, JSON.stringify(h));
    if (r.replace) check('phrase replacement A -> B', r.replace.before && r.replace.after, JSON.stringify(r.replace));
    for (const m of r.media) check(`media ${m.beat}: hidden before landing, shown after, loaded, trim`, m.hiddenBefore && m.shown && m.loaded && m.videoOk, JSON.stringify(m));
    for (const c of r.chassis) check(`chassis ${c.beat}/${c.id}: ${c.wanted} slab, content inside screen, never empty, tilt held, live`,
      c.chassis === c.wanted && c.slab && c.screen && c.contentIn && c.neverEmpty && c.live && c.tilt && c.samples > 3, JSON.stringify(c));
    if (r.figure) check('still figure composed from body/head/face parts', r.figure.slots.join(',') === 'body,head,face' && r.figure.paths > 3 && r.figure.stillDuringHold && r.figure.visible, JSON.stringify(r.figure));
    for (const il of r.illustration) {
      const bad = il.ops.filter((o) => !o.ok);
      check(`illustration ${il.beat} ${il.form}: ${il.ops.length} ops, entities built once, hidden before entry, carried state, clear of copy`,
        il.entities && il.hiddenBefore && il.carried && !il.collide && bad.length === 0 && il.accent.ok, JSON.stringify({ ...il, ops: bad }));
    }
    {
      const ledger = new AuthorshipLedger(plan.fps);
      for (const { ms, snap } of r.inspections) ledger.observe(ms, snap);
      const a = ledger.report();
      check(`authorship: ${a.frames_inspected} frames, no generated-look tells (longest hold ${a.longest_static_hold_ms}ms)`, a.findings.length === 0, JSON.stringify(a.findings.slice(0, 6)));
      const n = r.authorshipNeg;
      if (n.clean !== undefined) {
        check('authorship: inspector names a shrunken mark, a leaking mark and an emptied housing, and clears when restored',
          n.clean.length === 0 && n.underfill.includes('ICON_UNDERFILL') && n.overflow.includes('ICON_OVERFLOW') && n.empty.includes('EMPTY_CHASSIS') && n.restored.length === 0, JSON.stringify(n));
      }
      if (n.connectorClean !== undefined) {
        check('authorship: inspector names a connector whose endpoint has gone', n.connectorClean.length === 0 && n.orphan.includes('ORPHAN_CONNECTOR'), JSON.stringify(n));
      }
    }
    {
      const mo = r.motion;
      const badSpring = mo.springs.filter((s) => !s.monotone || !s.rest || (plan.motion && plan.motion.spring === 'snap') !== s.overshoot);
      if (mo.springs.length) check(`motion: ${mo.springs.length} entrances on the '${(plan.motion || {}).spring}' spring — opacity monotone, scale ${(plan.motion || {}).spring === 'snap' ? 'rings' : 'never rings'}, comes to rest`, badSpring.length === 0, JSON.stringify(badSpring));
      const badBlur = mo.blur.filter((s) => !s.moving || !s.still);
      if (mo.blur.length) check(`motion: ${mo.blur.length} bodies blur while travelling and clear at rest`, badBlur.length === 0, JSON.stringify(badBlur));
      const badLabel = mo.labels.filter((l) => !l.ok);
      if (mo.labels.length) check(`motion: ${mo.labels.length} labels ride their bodies through entrance and carry (lag ${(plan.motion || {}).label_lag_ms || 0}ms)`, badLabel.length === 0, JSON.stringify(badLabel));
      const badConn = mo.connectors.filter((c) => c.drift > 1.5);
      if (mo.connectors.length) check(`motion: ${mo.connectors.length} connectors ride their drifting endpoints`, badConn.length === 0, JSON.stringify(badConn));
      const badCam = mo.camera.filter((c) => !c.ok);
      if (mo.camera.length) check(`motion: ${mo.camera.length} cuts made as their compiled camera move (${[...new Set(mo.camera.map((c) => c.move))].join('/')})`, badCam.length === 0, JSON.stringify(badCam));
    }
    for (const c of r.cascade) check(`word cascade ${c.beat}/${c.unit}: words land in order, all settle in focus, stress heavier`, c.words && c.firstOnly && c.all && c.heavier, JSON.stringify(c));
    check(`frame update under 8ms (avg ${r.perf.avg_ms.toFixed(2)}ms, max ${r.perf.max_ms.toFixed(2)}ms over ${r.perf.frames} frames)`, r.perf.avg_ms < 8, JSON.stringify(r.perf));
    check('no page errors', errors.length === 0, errors.join(' | '));
    await page.close();
  }
}

main().catch((e) => { console.error(e); process.exit(1); });
