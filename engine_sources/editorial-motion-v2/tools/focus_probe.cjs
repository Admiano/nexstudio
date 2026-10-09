// Focus probe: for every page of a compiled paperbook plan, seek through each focus
// action's window and record the on-screen box the actor sweeps (output px), plus the
// performer's box. stillness_gate.py compares rendered frames against these boxes.
//   node tools/focus_probe.cjs <plan.json> <out.json>
const fs = require('fs');
const path = require('path');
const http = require('http');
const { chromium } = require('playwright-core');

const ROOT = path.resolve(__dirname, '..');
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.woff2': 'font/woff2', '.ttf': 'font/ttf', '.otf': 'font/otf', '.css': 'text/css', '.mp3': 'audio/mpeg', '.wav': 'audio/wav' };
const STEP_MS = 40;

function serve() {
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => {
      const url = decodeURIComponent(req.url.split('?')[0]);
      const file = url.startsWith('/fs/') ? url.slice(3) : path.join(ROOT, url);
      if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); res.end(); return; }
      res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream' });
      fs.createReadStream(file).pipe(res);
    });
    srv.listen(0, '127.0.0.1', () => resolve(srv));
  });
}

function chromePath() {
  if (process.env.CHROME_PATH && fs.existsSync(process.env.CHROME_PATH)) return process.env.CHROME_PATH;
  try { return chromium.executablePath(); } catch (e) { return undefined; }
}

(async () => {
  const [planPath, outPath] = process.argv.slice(2).map((p) => path.resolve(p));
  const plan = JSON.parse(fs.readFileSync(planPath, 'utf8'));
  const srv = await serve();
  const browser = await chromium.launch({ executablePath: chromePath(), headless: false, args: ['--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars', '--mute-audio'] });
  const page = await browser.newPage({ viewport: { width: plan.output.w, height: plan.output.h } });
  await page.goto(`http://127.0.0.1:${srv.address().port}/compositions/player.html?plan=/fs${planPath}&assets=/fs`, { waitUntil: 'networkidle' });
  await page.waitForFunction('window.__em2Ready === true || window.__em2Error', null, { timeout: 60000 });
  const out = { plan: planPath, output: plan.output, beats: [] };
  for (const b of plan.beats) {
    const acts = ((b.illustration || {}).entities || []).filter((e) => e.action && e.action.at != null);
    const rec = { beat_id: b.beat_id, focus: [], figure: null };
    const sample = async (t, ids) => page.evaluate(({ t, bid, ids }) => {
      window.__em2.pause();
      window.__em2.seek(t);
      const cam = document.querySelector(`[data-cam="${bid}"]`);
      const boxOf = (el) => {
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return r.width > 0 && r.height > 0 ? [r.left, r.top, r.right, r.bottom] : null;
      };
      const res = {};
      for (const id of ids) res[id] = cam ? boxOf(cam.querySelector(`[data-entity="${id}"]`)) : null;
      res.__figure = cam ? boxOf(cam.querySelector(`[data-figure="${bid}"]`)) : null;
      res.__edu = cam ? [...cam.querySelectorAll('[data-edu-live]')].map(boxOf).filter(Boolean) : [];
      return res;
    }, { t, bid: b.beat_id, ids });
    const grow = (acc, box) => (!box ? acc : !acc ? box.slice() : [Math.min(acc[0], box[0]), Math.min(acc[1], box[1]), Math.max(acc[2], box[2]), Math.max(acc[3], box[3])]);
    const hold1 = b.start_ms + (b.transition ? b.transition.start_ms : b.duration_ms);
    for (const e of acts) {
      let box = null;
      const t0 = b.start_ms + Number(e.action.at);
      const t1 = Math.min(hold1, t0 + Number(e.action.dur || 600));
      for (let t = t0 - STEP_MS; t <= hold1; t += STEP_MS) {
        const r = await sample(t, [e.id]);
        box = grow(box, r[e.id]);
        if (t > t1 + STEP_MS * 2) break;
      }
      rec.focus.push({ id: e.id, kind: e.action.kind, at: Number(e.action.at), dur: Number(e.action.dur || 0), box });
    }
    let fig = null;
    if (b.figure) {
      for (let t = b.start_ms; t <= hold1; t += STEP_MS * 3) fig = grow(fig, (await sample(t, []))['__figure']);
    }
    rec.figure = fig;
    rec.edu = (await sample(hold1 - 20, []))['__edu'];
    out.beats.push(rec);
  }
  fs.writeFileSync(outPath, JSON.stringify(out, null, 1));
  await browser.close();
  srv.close();
  console.log(`focus boxes -> ${outPath}`);
})().catch((e) => { console.error(e); process.exit(1); });
