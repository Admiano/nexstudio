#!/usr/bin/env node
/*
 * Asset pre-flight: render every registry SVG the way the runtime does (inline, in Chrome) and
 * quarantine the ones that would betray the film — geometry that leaks past the viewBox, art
 * that paints almost nothing once inlined (filter/gradient-dependent bodies), files that reach
 * outside themselves (scripts, foreignObject, external hrefs) or fail to parse at all.
 *
 *   node tools/preflight_assets.js                 (attaches to CDP_URL, default http://localhost:29229)
 *   node tools/preflight_assets.js --only emoji.fluent   (one pack, for iteration)
 *
 * Writes assets/community/preflight.json: { version, checked, quarantined: { id: reason }, ... }.
 * The compiler refuses a quarantined asset_ref and the concept finder never offers one.
 */
const fs = require('fs');
const http = require('http');
const path = require('path');
const { chromium } = require('playwright-core');

const ROOT = path.resolve(__dirname, '..');
const REGISTRIES = ['assets/illustration/registry.json', 'assets/community/icons-registry.json', 'assets/community/colour-registry.json'];
const OUT = path.join(ROOT, 'assets', 'community', 'preflight.json');
const VERSION = 'ASSET_PREFLIGHT_V1';
// A mark that paints under COVERAGE_MIN of its viewBox area is not the mark its label promises;
// a mark with more than OVERFLOW_MAX of its paint outside the viewBox ghosts the frame. A one-
// pixel band around the box is ignored so anti-aliased edges are never mistaken for a leak.
const COVERAGE_MIN = 0.03;
const OVERFLOW_MAX = 0.01;
const EDGE_BAND = 1.5;
const RASTER = 96;
const MARGIN = 48;

const only = (() => { const i = process.argv.indexOf('--only'); return i > 0 ? process.argv[i + 1] : null; })();

function loadItems() {
  const items = [];
  for (const rel of REGISTRIES) {
    const p = path.join(ROOT, rel);
    if (!fs.existsSync(p)) continue;
    const doc = JSON.parse(fs.readFileSync(p, 'utf8'));
    for (const a of doc.assets) items.push({ id: a.id, path: path.join(path.dirname(p), a.path) });
  }
  return only ? items.filter((a) => a.id.startsWith(only)) : items;
}

function staticCheck(svg) {
  if (!/<svg[\s>]/i.test(svg)) return 'PARSE: no <svg> root';
  if (/<script[\s>]/i.test(svg)) return 'SCRIPT: executable content';
  if (/<foreignObject[\s>]/i.test(svg)) return 'FOREIGN_OBJECT: html embedded in the mark';
  if (/(xlink:href|href|src)\s*=\s*"(https?:|\/\/|file:)/i.test(svg)) return 'EXTERNAL_REF: reaches outside the file';
  if (/<image[\s>]/i.test(svg) && !/<image[^>]*href\s*=\s*"data:/i.test(svg)) return 'EXTERNAL_IMAGE: bitmap not embedded';
  return null;
}

function serve() {
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => {
      const url = decodeURIComponent(req.url.split('?')[0]);
      const file = url.startsWith('/fs/') ? url.slice(3) : path.join(ROOT, url);
      if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); res.end(); return; }
      res.writeHead(200, { 'Content-Type': file.endsWith('.svg') ? 'image/svg+xml' : 'text/html' });
      fs.createReadStream(file).pipe(res);
    });
    srv.listen(0, '127.0.0.1', () => resolve(srv));
  });
}

const PAGE = `<!doctype html><html><body style="margin:0;background:#fff"><div id="m"></div><script>
// Rasterise the SVG inlined into a host box sized RASTER, on a canvas RASTER + 2*MARGIN wide, and
// measure the paint inside the box versus outside it.
window.__preflight = async function (svgText, raster, margin, band) {
  const doc = new DOMParser().parseFromString(svgText, 'image/svg+xml');
  const src = doc.documentElement;
  if (src.nodeName === 'parsererror' || !src.getAttribute) return { error: 'PARSE: not well-formed svg' };
  const vbRaw = src.getAttribute('viewBox');
  const vb = (vbRaw || ('0 0 ' + (src.getAttribute('width') || 100) + ' ' + (src.getAttribute('height') || 100))).split(/[\\s,]+/).map(Number);
  if (vb.length !== 4 || !(vb[2] > 0) || !(vb[3] > 0)) return { error: 'VIEWBOX: unusable viewBox ' + JSON.stringify(vbRaw) };
  const size = raster + margin * 2;
  const s = Math.min(raster / vb[2], raster / vb[3]);
  const bw = vb[2] * s, bh = vb[3] * s, bx = (size - bw) / 2, by = (size - bh) / 2;
  const ns = 'http://www.w3.org/2000/svg';
  const host = document.createElementNS(ns, 'svg');
  host.setAttribute('xmlns', ns);
  host.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink');
  host.setAttribute('width', size); host.setAttribute('height', size);
  host.setAttribute('viewBox', '0 0 ' + size + ' ' + size);
  host.style.color = '#000';
  for (const a of src.attributes) if (!/^(width|height|viewBox|xmlns.*|id|class|style)$/.test(a.name)) host.setAttribute(a.name, a.value);
  const g = document.createElementNS(ns, 'g');
  g.setAttribute('transform', 'translate(' + bx + ' ' + by + ') scale(' + s + ') translate(' + (-vb[0]) + ' ' + (-vb[1]) + ')');
  g.innerHTML = src.innerHTML;
  host.appendChild(g);
  const xml = new XMLSerializer().serializeToString(host);
  const url = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(xml);
  const img = new Image();
  const loaded = await new Promise((res) => { img.onload = () => res(true); img.onerror = () => res(false); img.src = url; });
  if (!loaded) return { error: 'RENDER_FAIL: chrome could not decode the svg' };
  const c = document.createElement('canvas'); c.width = size; c.height = size;
  const ctx = c.getContext('2d');
  ctx.drawImage(img, 0, 0, size, size);
  const px = ctx.getImageData(0, 0, size, size).data;
  let inside = 0, outside = 0;
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    if (px[(y * size + x) * 4 + 3] < 24) continue;
    const cx = x + 0.5, cy = y + 0.5;
    if (cx >= bx && cx < bx + bw && cy >= by && cy < by + bh) inside++;
    else if (cx < bx - band || cx > bx + bw + band || cy < by - band || cy > by + bh + band) outside++;
  }
  return { coverage: inside / (bw * bh), overflow: outside / Math.max(1, inside + outside) };
};
</script></body></html>`;

async function main() {
  const items = loadItems();
  const srv = await serve();
  const base = `http://127.0.0.1:${srv.address().port}`;
  const pagePath = path.join(ROOT, 'out', '_preflight.html');
  fs.mkdirSync(path.dirname(pagePath), { recursive: true });
  fs.writeFileSync(pagePath, PAGE);
  const browser = process.env.CHROME_PATH
    ? await chromium.launch({ executablePath: process.env.CHROME_PATH, headless: true, args: ['--no-sandbox', '--disable-gpu'] })
    : await chromium.connectOverCDP(process.env.CDP_URL || 'http://localhost:29229');
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  await page.goto(`${base}/out/_preflight.html`);

  const quarantined = {};
  const reasons = {};
  let checked = 0;
  const t0 = Date.now();
  for (const it of items) {
    checked += 1;
    let svg;
    try { svg = fs.readFileSync(it.path, 'utf8'); } catch (e) { quarantined[it.id] = 'FILE_MISSING'; continue; }
    const st = staticCheck(svg);
    if (st) { quarantined[it.id] = st; continue; }
    const r = await page.evaluate(([t, ra, m, b]) => window.__preflight(t, ra, m, b), [svg, RASTER, MARGIN, EDGE_BAND]);
    if (r.error) quarantined[it.id] = r.error;
    else if (r.coverage < COVERAGE_MIN) quarantined[it.id] = `UNDERPAINT: paints ${(r.coverage * 100).toFixed(1)}% of its box inline`;
    else if (r.overflow > OVERFLOW_MAX) quarantined[it.id] = `OVERFLOW: ${(r.overflow * 100).toFixed(1)}% of its paint lands outside the viewBox`;
    if (checked % 1000 === 0) console.log(`  ${checked}/${items.length} checked, ${Object.keys(quarantined).length} quarantined, ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  for (const reason of Object.values(quarantined)) { const code = reason.split(':')[0]; reasons[code] = (reasons[code] || 0) + 1; }
  await ctx.close();
  await browser.close();
  srv.close();
  fs.rmSync(pagePath, { force: true });

  let prev = { quarantined: {} };
  if (only && fs.existsSync(OUT)) prev = JSON.parse(fs.readFileSync(OUT, 'utf8'));
  const merged = only ? { ...Object.fromEntries(Object.entries(prev.quarantined).filter(([k]) => !k.startsWith(only))), ...quarantined } : quarantined;
  const sorted = Object.fromEntries(Object.keys(merged).sort().map((k) => [k, merged[k]]));
  const out = {
    version: VERSION, thresholds: { coverage_min: COVERAGE_MIN, overflow_max: OVERFLOW_MAX, raster_px: RASTER, edge_band_px: EDGE_BAND },
    checked: only ? (prev.checked || 0) : checked, quarantined_count: Object.keys(sorted).length, reasons, quarantined: sorted,
  };
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1) + '\n');
  console.log(`${checked} checked, ${Object.keys(quarantined).length} quarantined → ${path.relative(ROOT, OUT)}`);
  console.log(JSON.stringify(reasons));
}

main().catch((e) => { console.error(e); process.exit(1); });
