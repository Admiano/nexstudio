#!/usr/bin/env node
/*
 * Runtime tests: run the execution-only runtime in headless Chromium against the
 * compiled fixture plans and assert determinism, plan-only behaviour and the
 * visible contracts (collision-free holds, replacement, media, still figure).
 *
 *   node tools/test_runtime.js            (compiles the fixture first if needed)
 *   CHROME_PATH=/path/to/chrome node tools/test_runtime.js
 */
const fs = require('fs');
const http = require('http');
const path = require('path');
const { spawnSync } = require('child_process');
const { chromium } = require('playwright-core');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'out', 'reply-speed');
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.webm': 'video/webm', '.woff2': 'font/woff2', '.ttf': 'font/ttf' };

function ensurePlans() {
  if (['9x16', '1x1', '16x9'].every((a) => fs.existsSync(path.join(OUT, `plan_${a}.json`)))) return;
  const r = spawnSync('python3', ['-m', 'editorial_plan_compiler', '../fixtures/reply-speed.treatment.json', OUT], { cwd: path.join(ROOT, 'compiler'), stdio: 'inherit' });
  if (r.status !== 0) throw new Error('fixture compile failed');
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

const PAGE = `<!doctype html><html><body style="margin:0"><div id="m" style="position:relative;width:100vw;height:100vh"></div>
<script src="/runtime/editorial-runtime.js"></script></body></html>`;

let failures = 0;
function check(name, ok, detail) {
  if (ok) { console.log(`  ok   ${name}`); return; }
  failures += 1;
  console.log(`  FAIL ${name}${detail ? ` — ${detail}` : ''}`);
}

async function main() {
  ensurePlans();
  fs.writeFileSync(path.join(OUT, '_test_page.html'), PAGE);
  const srv = await serve();
  const base = `http://127.0.0.1:${srv.address().port}`;
  const chromePath = process.env.CHROME_PATH || '';
  const browser = await chromium.launch(Object.assign({ headless: true, args: ['--no-sandbox', '--disable-gpu'] }, chromePath ? { executablePath: chromePath } : {}));

  for (const aspect of ['9x16', '1x1', '16x9']) {
    console.log(`[${aspect}]`);
    const plan = JSON.parse(fs.readFileSync(path.join(OUT, `plan_${aspect}.json`), 'utf8'));
    const page = await browser.newPage({ viewport: { width: plan.canvas.w, height: plan.canvas.h } });
    const errors = [];
    page.on('pageerror', (e) => errors.push(String(e)));
    page.on('console', (m) => m.type() === 'error' && errors.push(m.text()));
    await page.goto(`${base}/out/reply-speed/_test_page.html`);

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

      // Media evidence: hidden before its landing, present after; video honours trim.
      out.media = [];
      for (const b of plan.beats.filter((x) => x.media)) {
        const beatNode = stage.children[plan.beats.indexOf(b)];
        const frame = beatNode.querySelector('img, video').parentElement;
        await film.seek(b.start_ms + Math.max(0, b.media.enter_ms - 30));
        const hiddenBefore = b.media.enter_ms === 0 ? true : (getComputedStyle(frame).visibility === 'hidden' || Number(getComputedStyle(frame).opacity) < 0.05);
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

      // Still figure: composed from the compiled parts only, visible in its hold, never animated after entry.
      const fb = plan.beats.find((b) => b.figure);
      if (fb) {
        const beatNode = stage.children[plan.beats.indexOf(fb)];
        const slots = Array.from(beatNode.querySelectorAll('svg g[data-slot]')).map((g) => g.dataset.slot);
        const paths = beatNode.querySelectorAll('svg path').length;
        await film.seek(fb.start_ms + fb.figure.enter_ms + fb.figure.enter_duration_ms + 10);
        const host = beatNode.querySelector('svg').parentElement;
        const s1 = host.getAttribute('style');
        await film.seek(fb.start_ms + fb.ensemble.hold_window.end_ms - 10);
        const s2 = host.getAttribute('style');
        out.figure = { slots, paths, stillDuringHold: s1 === s2, visible: getComputedStyle(host).visibility !== 'hidden' && Number(getComputedStyle(host).opacity) > 0.95 };
      }
      return out;
    }, { planUrl: `/out/reply-speed/plan_${aspect}.json`, assetPrefix: '/fs' });

    check('rejects foreign schema', r.rejects.schema);
    check('refuses failed gate', r.rejects.gate);
    check('runtime version exposed', r.version === 'EDITORIAL_RUNTIME_V2.0', r.version);
    check(`stage is native ${plan.canvas.w}x${plan.canvas.h}`, r.stage.w === plan.canvas.w && r.stage.h === plan.canvas.h && r.stage.aspect === aspect, JSON.stringify(r.stage));
    check('frame count matches plan', r.frames === Math.ceil((plan.duration_ms * plan.fps) / 1000));
    check('captions and audio events exposed', r.captions > 0 && r.audio.voice === plan.beats.length && r.audio.accents > 0 && r.audio.music === plan.music.status, JSON.stringify(r.audio));
    check('seek is deterministic across paths', r.determinism.every(Boolean), JSON.stringify(r.determinism));
    check('frame(n) equals seek(n/fps)', r.frameAddress);
    check('nothing settled before first landing', r.preLanding);
    for (const h of r.holds) check(`hold ${h.beat}: ${h.visible}/${h.expected} blocks, inside, no collision`, h.visible === h.expected && h.inside && !h.collide, JSON.stringify(h));
    if (r.replace) check('phrase replacement A -> B', r.replace.before && r.replace.after, JSON.stringify(r.replace));
    for (const m of r.media) check(`media ${m.beat}: hidden before landing, shown after, loaded, trim`, m.hiddenBefore && m.shown && m.loaded && m.videoOk, JSON.stringify(m));
    if (r.figure) check('still figure composed from body/head/face parts', r.figure.slots.join(',') === 'body,head,face' && r.figure.paths > 3 && r.figure.stillDuringHold && r.figure.visible, JSON.stringify(r.figure));
    check('no page errors', errors.length === 0, errors.join(' | '));
    await page.close();
  }
  await browser.close();
  srv.close();
  fs.rmSync(path.join(OUT, '_test_page.html'), { force: true });
  console.log(failures ? `\n${failures} failure(s)` : '\nall runtime tests passed');
  process.exit(failures ? 1 : 0);
}

main().catch((e) => { console.error(e); process.exit(1); });
