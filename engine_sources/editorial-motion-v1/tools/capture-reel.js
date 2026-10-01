/**
 * Frame-accurate capture of an editorial film, one ratio at a time.
 *
 * The master timeline is paused and seekable and every frame is a pure
 * function of time, so frames are stepped rather than recorded in real time:
 * no dropped frames, no drift, the same bytes on every run.
 *
 *   node tools/capture-reel.js                        # 16:9, 12fps, 30s
 *   RATIO=9:16 FPS=24 OUT=/tmp/frames node tools/capture-reel.js
 *
 * Requires playwright (`npx playwright install chromium`) or a running Chrome
 * exposing a CDP endpoint via CDP_URL.
 */
const fs = require('fs');
const path = require('path');

const URL = process.env.REEL_URL || 'http://127.0.0.1:8901/compositions/editorial-explorer.html';
const CDP = process.env.CDP_URL || '';
const RATIO = process.env.RATIO || '16:9';
const FPS = Number(process.env.FPS || 12);
const DURATION = Number(process.env.DURATION || 30);
const OUT = process.env.OUT || path.resolve(process.cwd(), 'frames', RATIO.replace(':', 'x'));

(async () => {
  const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
  fs.rmSync(OUT, { recursive: true, force: true });
  fs.mkdirSync(OUT, { recursive: true });

  const browser = CDP ? await chromium.connectOverCDP(CDP) : await chromium.launch();
  const context = browser.contexts()[0] || (await browser.newContext());
  const page = await context.newPage();
  await page.setViewportSize({ width: 1600, height: 1000 });

  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  page.on('console', (m) => m.type() === 'error' && errors.push(m.text()));

  await page.goto(URL, { waitUntil: 'networkidle' });
  await page.click(`#ratios button:text-is("${RATIO}")`);
  await page.waitForFunction(() => !!document.getElementById('frame').__editorialTimeline);
  await page.waitForTimeout(800);

  const total = Math.round(FPS * DURATION);
  for (let i = 0; i < total; i += 1) {
    await page.evaluate((time) => document.getElementById('frame').__editorialTimeline.pause().seek(time), i / FPS);
    await page.locator('#frame').screenshot({ path: path.join(OUT, `f${String(i).padStart(5, '0')}.png`) });
    if (i % 60 === 0) process.stdout.write(`${RATIO} ${i}/${total}\n`);
  }

  console.log('errors:', errors.length ? errors.slice(0, 6) : 'none');
  console.log(`frames: ${OUT}`);
  console.log(`encode: ffmpeg -y -framerate ${FPS} -i ${OUT}/f%05d.png -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" -c:v libx264 -pix_fmt yuv420p -crf 20 reel-${RATIO.replace(':', 'x')}.mp4`);
  await page.close();
  await browser.close();
})();
