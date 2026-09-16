#!/usr/bin/env node
/*
 * Render a compiled EditorialPlan into MP4 (video + semantic sound mix), a
 * frozen-progress contact sheet, transition strips and a render manifest.
 *
 *   node tools/render_reel.js <plan.json> <out_dir> [--cdp http://localhost:29229] [--fps 30] [--limit-ms N]
 *
 * Frame-addressable capture: the page is seeked to every frame time and the
 * stage is screenshotted, so the result is deterministic and identical to the
 * player's seek() state. Audio is assembled only from the plan's bindings
 * (voice segments, admitted sound accents, silent music slot).
 */
const fs = require('fs');
const http = require('http');
const path = require('path');
const { execFileSync, spawnSync } = require('child_process');
const { chromium } = require('playwright-core');

const ROOT = path.resolve(__dirname, '..');
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png', '.mp4': 'video/mp4', '.woff2': 'font/woff2', '.ttf': 'font/ttf', '.wav': 'audio/wav' };

function arg(name, dflt) {
  const i = process.argv.indexOf(name);
  return i > 0 ? process.argv[i + 1] : dflt;
}

function serve() {
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => {
      const url = decodeURIComponent(req.url.split('?')[0]);
      // /fs/<absolute path> exposes compiled-plan asset paths; everything else is the package tree.
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

function ff(args) {
  const r = spawnSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', ...args], { stdio: 'inherit' });
  if (r.status !== 0) throw new Error(`ffmpeg failed: ${args.join(' ')}`);
}

function buildAudio(plan, out) {
  const inputs = [];
  const filters = [];
  const labels = [];
  let n = 0;
  const durS = (plan.duration_ms / 1000).toFixed(3);
  inputs.push('-f', 'lavfi', '-t', durS, '-i', 'anullsrc=r=48000:cl=stereo');
  labels.push('[0:a]');
  n = 1;
  for (const seg of plan.voice.segments) {
    if (!seg.audio_path || !fs.existsSync(seg.audio_path)) continue;
    if (seg.start_ms + seg.duration_ms > plan.duration_ms + 1000 / plan.fps) {
      throw new Error(`voice segment ${seg.beat_id} ends at ${seg.start_ms + seg.duration_ms}ms but the film is ${plan.duration_ms}ms; the audio would be cut`);
    }
    inputs.push('-i', seg.audio_path);
    filters.push(`[${n}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay=${seg.start_ms}|${seg.start_ms}[v${n}]`);
    labels.push(`[v${n}]`);
    n += 1;
  }
  for (const beat of plan.beats) {
    for (const acc of beat.sound.accents) {
      if (!fs.existsSync(acc.path)) throw new Error(`sound asset missing: ${acc.path}`);
      inputs.push('-i', acc.path);
      filters.push(`[${n}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=${acc.gain_db}dB,adelay=${acc.film_at_ms}|${acc.film_at_ms}[s${n}]`);
      labels.push(`[s${n}]`);
      n += 1;
    }
  }
  if (plan.music && plan.music.path) throw new Error('music slot has a path but the runtime has no rights evidence for it');
  filters.push(`${labels.join('')}amix=inputs=${labels.length}:normalize=0:duration=first[mix]`);
  ff([...inputs, '-filter_complex', filters.join(';'), '-map', '[mix]', '-t', durS, '-c:a', 'pcm_s16le', out]);
  return { voice_segments: plan.voice.segments.length, accents: labels.length - 1 - plan.voice.segments.length, music: plan.music.status };
}

async function main() {
  const planPath = path.resolve(process.argv[2]);
  const outDir = path.resolve(process.argv[3]);
  const cdp = arg('--cdp', process.env.CDP_URL || 'http://localhost:29229');
  const limit = Number(arg('--limit-ms', 0));
  const plan = JSON.parse(fs.readFileSync(planPath, 'utf8'));
  const fps = Number(arg('--fps', plan.fps));
  const framesDir = path.join(outDir, `frames_${plan.aspect}`);
  fs.rmSync(framesDir, { recursive: true, force: true });
  fs.mkdirSync(framesDir, { recursive: true });

  const srv = await serve();
  const port = srv.address().port;
  const url = `http://127.0.0.1:${port}/compositions/player.html?plan=/fs${planPath}&assets=/fs`;
  const chromePath = arg('--chrome', process.env.CHROME_PATH || '');
  const browser = chromePath
    ? await chromium.launch({ executablePath: chromePath, headless: true, args: ['--no-sandbox', '--disable-gpu', '--font-render-hinting=none'] })
    : await chromium.connectOverCDP(cdp);
  const context = browser.contexts()[0] || (await browser.newContext());
  const page = await context.newPage();
  await page.bringToFront(); // a background tab is throttled by the browser; capture must own the foreground
  await page.setViewportSize({ width: plan.output.w, height: plan.output.h });
  const errors = [];
  page.on('console', (m) => m.type() === 'error' && errors.push(m.text()));
  page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForFunction('window.__em2Ready === true || window.__em2Error', null, { timeout: 60000 }).catch(() => {});
  const err = await page.evaluate(() => window.__em2Error || (window.__em2Ready ? null : 'runtime never became ready'));
  if (err) throw new Error(`${err}\n${errors.join('\n')}`);
  const stage = await page.$('.em2-stage');
  const box = await stage.boundingBox();
  const clip = { x: Math.round(box.x), y: Math.round(box.y), width: plan.output.w, height: plan.output.h };

  const total = Math.ceil(((limit || plan.duration_ms) * fps) / 1000);
  const t0 = Date.now();
  for (let i = 0; i < total; i += 1) {
    const ms = Math.round((i * 1000) / fps);
    await page.evaluate((t) => window.__em2.seek(t), ms);
    await page.screenshot({ path: path.join(framesDir, `f${String(i).padStart(5, '0')}.png`), clip, animations: 'disabled', caret: 'hide' });
    if (i % 150 === 0) process.stdout.write(`${plan.aspect} ${i}/${total} (${((Date.now() - t0) / 1000).toFixed(0)}s)\n`);
  }

  // Frozen-progress contact sheet: one frame per beat at the start of its hold window, plus transition strips.
  const holdFrames = plan.beats.map((b) => Math.min(total - 1, Math.round(((b.start_ms + (b.ensemble.hold_window ? b.ensemble.hold_window.start_ms : b.duration_ms * 0.7)) * fps) / 1000)));
  const stripFrames = [];
  plan.beats.forEach((b, bi) => {
    if (bi === plan.beats.length - 1 || !b.transition) return;
    const s = b.start_ms + b.transition.start_ms, e = b.start_ms + b.transition.end_ms + 240;
    for (let k = 0; k < 6; k += 1) stripFrames.push(Math.min(total - 1, Math.round(((s + ((e - s) * k) / 5) * fps) / 1000)));
  });
  const sheetDir = path.join(outDir, `sheet_${plan.aspect}`);
  fs.rmSync(sheetDir, { recursive: true, force: true });
  fs.mkdirSync(sheetDir);
  holdFrames.forEach((f, i) => fs.copyFileSync(path.join(framesDir, `f${String(f).padStart(5, '0')}.png`), path.join(sheetDir, `h${String(i).padStart(3, '0')}.png`)));
  stripFrames.forEach((f, i) => fs.copyFileSync(path.join(framesDir, `f${String(f).padStart(5, '0')}.png`), path.join(sheetDir, `t${String(i).padStart(3, '0')}.png`)));
  const cols = plan.aspect === '9x16' ? 6 : plan.aspect === '1x1' ? 4 : 3;
  const tileW = plan.aspect === '9x16' ? 270 : plan.aspect === '1x1' ? 360 : 480;
  const tileH = Math.round((tileW * plan.output.h) / plan.output.w);
  ff(['-framerate', '1', '-i', path.join(sheetDir, 'h%03d.png'), '-vf', `scale=${tileW}:${tileH},tile=${cols}x${Math.ceil(holdFrames.length / cols)}:padding=6:margin=6:color=0x222222`, '-frames:v', '1', path.join(outDir, `contact_${plan.aspect}.png`)]);
  if (stripFrames.length) {
    ff(['-framerate', '1', '-i', path.join(sheetDir, 't%03d.png'), '-vf', `scale=${Math.round(tileW * 0.6)}:${Math.round(tileH * 0.6)},tile=6x${stripFrames.length / 6}:padding=4:margin=6:color=0x222222`, '-frames:v', '1', path.join(outDir, `transitions_${plan.aspect}.png`)]);
  }

  const audioPath = path.join(outDir, `audio_${plan.aspect}.wav`);
  const audio = buildAudio(plan, audioPath);
  const mp4 = path.join(outDir, `${plan.film_id}_${plan.aspect}.mp4`);
  ff(['-framerate', String(fps), '-i', path.join(framesDir, 'f%05d.png'), '-i', audioPath, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '17', '-preset', 'medium', '-c:a', 'aac', '-b:a', '160k', '-t', (plan.duration_ms / 1000).toFixed(3), '-movflags', '+faststart', mp4]);
  const streams = JSON.parse(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'stream=codec_type,duration', '-of', 'json', mp4]).toString()).streams;
  const durations = Object.fromEntries(streams.map((s) => [s.codec_type, Math.round(parseFloat(s.duration) * 1000)]));
  const frameMs = 1000 / fps;
  for (const kind of ['video', 'audio']) {
    if (Math.abs(durations[kind] - plan.duration_ms) > frameMs * 2) throw new Error(`${kind} stream is ${durations[kind]}ms, plan is ${plan.duration_ms}ms`);
  }

  // Captions (SRT) straight from the plan's word timings.
  const srt = plan.captions.map((c, i) => `${i + 1}\n${ts(c.start_ms)} --> ${ts(c.end_ms)}\n${c.text}\n`).join('\n');
  fs.writeFileSync(path.join(outDir, `captions_${plan.aspect}.srt`), srt);

  const manifest = {
    schema: 'EditorialRenderManifestV1', runtime: await page.evaluate(() => window.__em2.version), film_id: plan.film_id, aspect: plan.aspect,
    plan_sha256: sha(fs.readFileSync(planPath)), frames: total, fps, output: plan.output, mp4: path.basename(mp4), mp4_sha256: sha(fs.readFileSync(mp4)),
    contact_sheet: `contact_${plan.aspect}.png`, transition_strip: stripFrames.length ? `transitions_${plan.aspect}.png` : null,
    audio, page_errors: errors, native_profile: plan.beats.every((b) => b.composition.native_profile && !b.composition.derived_by_scaling),
  };
  fs.writeFileSync(path.join(outDir, `render_${plan.aspect}.json`), JSON.stringify(manifest, null, 2));
  console.log(JSON.stringify({ mp4, frames: total, errors: errors.length, audio }, null, 1));
  await page.close();
  if (chromePath) await browser.close();
  srv.close();
  process.exit(errors.length ? 2 : 0);
}

function ts(ms) {
  const h = Math.floor(ms / 3600000), m = Math.floor((ms % 3600000) / 60000), s = Math.floor((ms % 60000) / 1000), f = ms % 1000;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')},${String(f).padStart(3, '0')}`;
}
function sha(buf) { return require('crypto').createHash('sha256').update(buf).digest('hex'); }

main().catch((e) => { console.error(e); process.exit(1); });
