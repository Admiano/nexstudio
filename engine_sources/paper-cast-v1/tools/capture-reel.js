/**
 * Frame-accurate capture of a paper-cast composition.
 *
 * The reel is a paused, seekable timeline and every frame is a pure function of
 * time, so frames are stepped rather than recorded in real time: no dropped
 * frames, no drift, identical output on every run.
 *
 *   node tools/capture-reel.js                       # 24fps x 30s -> ./frames
 *   REEL_URL=... FPS=12 DURATION=30 OUT=/tmp/f node tools/capture-reel.js
 *
 * Requires playwright (`npx playwright install chromium`) or an already running
 * Chrome exposing a CDP endpoint via CDP_URL.
 */
const fs = require('fs');
const path = require('path');

const URL = process.env.REEL_URL || 'http://127.0.0.1:8899/compositions/cast-reel.html';
const CDP = process.env.CDP_URL || '';
const FPS = Number(process.env.FPS || 24);
const DURATION = Number(process.env.DURATION || 30);
const OUT = process.env.OUT || path.resolve(process.cwd(), 'frames');

(async () => {
  const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
  fs.rmSync(OUT, { recursive: true, force: true });
  fs.mkdirSync(OUT, { recursive: true });

  const browser = CDP ? await chromium.connectOverCDP(CDP) : await chromium.launch();
  const context = browser.contexts()[0] || (await browser.newContext());
  const page = await context.newPage();
  await page.setViewportSize({ width: 1920, height: 1080 });

  const errors = [];
  page.on('console', (m) => m.type() === 'error' && errors.push(m.text()));
  page.on('pageerror', (e) => errors.push(String(e)));

  await page.goto(URL, { waitUntil: 'networkidle' });
  await page.waitForFunction('!!window.__timelines && !!window.__timelines["cast-reel"]');

  const total = Math.round(FPS * DURATION);
  for (let i = 0; i < total; i += 1) {
    await page.evaluate((time) => window.seekComposition(time), i / FPS);
    await page.screenshot({ path: path.join(OUT, `f${String(i).padStart(5, '0')}.png`) });
    if (i % 60 === 0) process.stdout.write(`${i}/${total}\n`);
  }

  console.log('errors:', errors.length ? errors.slice(0, 10) : 'none');
  console.log(`frames: ${OUT}`);
  console.log(`encode: ffmpeg -y -framerate ${FPS} -i ${OUT}/f%05d.png -c:v libx264 -pix_fmt yuv420p -crf 20 reel.mp4`);
  await page.close();
  await browser.close();
})();
