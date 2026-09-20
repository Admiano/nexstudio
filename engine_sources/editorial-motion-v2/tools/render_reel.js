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
const { AuthorshipLedger } = require('./authorship_gate');

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
      res.writeHead(200, { 'Content-Type': type, 'Content-Length': stat.size, 'Accept-Ranges': 'bytes', 'Cache-Control': 'no-store' });
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
  const durS = (plan.duration_ms / 1000).toFixed(3);
  let n = 0;
  inputs.push('-f', 'lavfi', '-t', durS, '-i', 'anullsrc=r=48000:cl=stereo');
  n = 1;
  const voice = [];
  for (const seg of plan.voice.segments) {
    if (!seg.audio_path || !fs.existsSync(seg.audio_path)) continue;
    if (seg.start_ms + seg.duration_ms > plan.duration_ms + 1000 / plan.fps) {
      throw new Error(`voice segment ${seg.beat_id} ends at ${seg.start_ms + seg.duration_ms}ms but the film is ${plan.duration_ms}ms; the audio would be cut`);
    }
    inputs.push('-i', seg.audio_path);
    filters.push(`[${n}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay=${seg.start_ms}|${seg.start_ms}[v${n}]`);
    voice.push(`[v${n}]`);
    n += 1;
  }
  filters.push(`[0:a]${voice.join('')}amix=inputs=${voice.length + 1}:normalize=0:duration=first[vox]`);
  const accents = [];
  for (const beat of plan.beats) {
    for (const acc of beat.sound.accents) {
      if (!fs.existsSync(acc.path)) throw new Error(`sound asset missing: ${acc.path}`);
      // Accents obey the same provenance law as the bed: bound license + sha256 or the render throws.
      if (!acc.license) throw new Error(`sound accent ${acc.asset_id || acc.path} has no license evidence`);
      if (acc.sha256 && sha(fs.readFileSync(acc.path)) !== acc.sha256) throw new Error(`sound accent sha256 mismatch: ${acc.path}`);
      inputs.push('-i', acc.path);
      const trim = acc.trim_ms ? `atrim=0:${(acc.trim_ms / 1000).toFixed(3)},afade=t=out:st=${Math.max(0, (acc.trim_ms - 120) / 1000).toFixed(3)}:d=0.12,` : '';
      filters.push(`[${n}:a]aformat=sample_rates=48000:channel_layouts=stereo,${trim}volume=${acc.gain_db}dB,adelay=${acc.film_at_ms}|${acc.film_at_ms}[s${n}]`);
      accents.push(`[s${n}]`);
      n += 1;
    }
  }
  const final = ['[voxm]', ...accents];
  let musicStatus = plan.music ? plan.music.status : 'NONE';
  const wantsMusic = Boolean(plan.music && plan.music.path);
  filters.push(wantsMusic && voice.length ? '[vox]asplit=2[voxm][voxk]' : '[vox]anull[voxm]');
  if (wantsMusic) {
    // Music is bound only with rights evidence: the plan must carry the license + sha256 of the file.
    if (plan.music.status !== 'BOUND_CC0' || !plan.music.license) throw new Error('music slot has a path but no rights evidence');
    if (!fs.existsSync(plan.music.path)) throw new Error(`music asset missing: ${plan.music.path}`);
    if (plan.music.sha256 && sha(fs.readFileSync(plan.music.path)) !== plan.music.sha256) throw new Error(`music sha256 mismatch: ${plan.music.path}`);
    inputs.push('-stream_loop', '-1', '-t', durS, '-i', plan.music.path);
    const mi = n; n += 1;
    const gain = plan.music.gain_db == null ? -19 : plan.music.gain_db;
    const fin = ((plan.music.fade_in_ms || 0) / 1000).toFixed(3);
    const fout = ((plan.music.fade_out_ms || 0) / 1000).toFixed(3);
    const dur = plan.duration_ms / 1000;
    filters.push(`[${mi}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=${gain}dB,afade=t=in:st=0:d=${fin},afade=t=out:st=${(dur - Number(fout)).toFixed(3)}:d=${fout}[mraw]`);
    if (voice.length) {
      // Sidechain-duck the bed under the voice mix; strength comes from the plan's duck_db.
      const ratio = Math.min(20, Math.max(2, Math.abs(plan.music.duck_under_voice_db || -14) / 2.4)).toFixed(1);
      filters.push(`[mraw][voxk]sidechaincompress=threshold=0.02:ratio=${ratio}:attack=30:release=450:makeup=1[mduck]`);
      final.push('[mduck]');
    } else {
      filters.push('[mraw]anull[mduck]');
      final.push('[mduck]');
    }
    musicStatus = `${plan.music.status}:${path.basename(plan.music.path)}`;
  }
  filters.push(`${final.join('')}amix=inputs=${final.length}:normalize=0:duration=first[mix]`);
  ff([...inputs, '-filter_complex', filters.join(';'), '-map', '[mix]', '-t', durS, '-c:a', 'pcm_s16le', out]);
  return { voice_segments: plan.voice.segments.length, accents: accents.length, music: musicStatus };
}

// Karaoke captions: one ASS dialogue per beat with \k word timings so the spoken word highlights.
function writeCaptions(plan, out) {
  const W = plan.output.w, H = plan.output.h;
  const safe = plan.beats[0] && plan.beats[0].composition.safe_area;
  const scale = plan.output.scale || 1;
  const marginV = Math.max(24, Math.round((plan.canvas.h - (safe ? safe.y + safe.h : plan.canvas.h)) * scale * 0.7));
  const accent = (plan.brand.accent || '#e8a317').replace('#', '');
  const accentAss = `&H00${accent.slice(4, 6)}${accent.slice(2, 4)}${accent.slice(0, 2)}`;
  const inkAss = `&H00${(plan.brand.ink || '#141414').replace('#', '').slice(4, 6)}${(plan.brand.ink || '#141414').replace('#', '').slice(2, 4)}${(plan.brand.ink || '#141414').replace('#', '').slice(0, 2)}`;
  const size = Math.round(H * 0.044);
  const header = [
    '[Script Info]', 'ScriptType: v4.00+', `PlayResX: ${W}`, `PlayResY: ${H}`, 'WrapStyle: 0', '',
    '[V4+ Styles]',
    'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
    `Style: K,Inter Display,${size},${accentAss},&H78141414,${inkAss},&H00000000,1,0,0,0,100,100,0,0,1,1.6,1.2,2,60,60,${marginV},1`,
    '',
    '[Events]',
    'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text',
  ];
  const t = (ms) => {
    const h = Math.floor(ms / 3600000), m = Math.floor((ms % 3600000) / 60000), s = (ms % 60000) / 1000;
    return `${h}:${String(m).padStart(2, '0')}:${s.toFixed(2).padStart(5, '0')}`;
  };
  const lines = [];
  for (const b of plan.beats) {
    const words = (b.words || []).filter((w) => w.text && w.text.trim());
    if (!words.length) continue;
    const start = b.start_ms + words[0].start_ms;
    const end = Math.min(plan.duration_ms, b.start_ms + words[words.length - 1].end_ms + 60);
    const body = words.map((w) => `{\\k${Math.max(1, Math.round((w.end_ms - w.start_ms) / 10))}}${w.text.trim().replace(/[{}\\]/g, '')}`).join(' ');
    lines.push(`Dialogue: 0,${t(start)},${t(end)},K,,0,0,0,,${body}`);
  }
  fs.writeFileSync(out, `${header.join('\n')}\n${lines.join('\n')}\n`);
  return lines.length;
}

async function main() {
  const planPath = path.resolve(process.argv[2]);
  const outDir = path.resolve(process.argv[3]);
  const cdp = arg('--cdp', process.env.CDP_URL || 'http://localhost:29229');
  const limit = Number(arg('--limit-ms', 0));
  const plan = JSON.parse(fs.readFileSync(planPath, 'utf8'));
  const fps = Number(arg('--fps', plan.fps));
  const framesDir = path.join(outDir, `frames_${plan.aspect}`);
  const reuseFrames = process.argv.includes('--reuse-frames');
  if (!reuseFrames) {
    fs.rmSync(framesDir, { recursive: true, force: true });
    fs.mkdirSync(framesDir, { recursive: true });
  }

  const srv = await serve();
  const port = srv.address().port;
  const url = `http://127.0.0.1:${port}/compositions/player.html?plan=/fs${planPath}&assets=/fs&v=${fs.statSync(planPath).mtimeMs}`;
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
  // Authorship inspection rides the same seek as the capture: the manifest records exactly the
  // frames that were rendered.
  const ledger = new AuthorshipLedger(fps);
  for (let i = 0; i < total; i += 1) {
    const ms = Math.round((i * 1000) / fps);
    await page.evaluate((t) => window.__em2.seek(t), ms);
    ledger.observe(ms, await page.evaluate(() => window.__em2.inspect()));
    if (reuseFrames) continue;
    await page.screenshot({ path: path.join(framesDir, `f${String(i).padStart(5, '0')}.png`), clip, animations: 'disabled', caret: 'hide' });
    if (i % 150 === 0) process.stdout.write(`${plan.aspect} ${i}/${total} (${((Date.now() - t0) / 1000).toFixed(0)}s)\n`);
  }
  const authorship = ledger.report();

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

  // Karaoke captions (ASS, word-timed) burned into the picture, plus an SRT sidecar.
  const assPath = path.join(outDir, `captions_${plan.aspect}.ass`);
  let captions = 0;
  // Collage films carry the words as on-canvas kinetic type; a caption strip would duplicate them.
  if (!process.argv.includes('--no-captions') && plan.captions_policy !== 'kinetic') {
    captions = writeCaptions(plan, assPath);
    const srt = plan.captions.map((c, i) => `${i + 1}\n${ts(c.start_ms)} --> ${ts(c.end_ms)}\n${c.text}\n`).join('\n');
    fs.writeFileSync(path.join(outDir, `captions_${plan.aspect}.srt`), srt);
  }
  const mp4 = path.join(outDir, `${plan.film_id}_${plan.aspect}.mp4`);
  const fontsDir = path.join(ROOT, 'assets', 'fonts');
  const vf = captions ? `subtitles='${assPath}':fontsdir='${fontsDir}'` : null;
  ff(['-framerate', String(fps), '-i', path.join(framesDir, 'f%05d.png'), '-i', audioPath]
    .concat(vf ? ['-vf', vf] : [])
    .concat(['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '17', '-preset', 'medium', '-c:a', 'aac', '-b:a', '160k', '-t', (plan.duration_ms / 1000).toFixed(3), '-movflags', '+faststart', mp4]));
  const streams = JSON.parse(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'stream=codec_type,duration', '-of', 'json', mp4]).toString()).streams;
  const durations = Object.fromEntries(streams.map((s) => [s.codec_type, Math.round(parseFloat(s.duration) * 1000)]));
  const frameMs = 1000 / fps;
  for (const kind of ['video', 'audio']) {
    if (Math.abs(durations[kind] - plan.duration_ms) > frameMs * 2) throw new Error(`${kind} stream is ${durations[kind]}ms, plan is ${plan.duration_ms}ms`);
  }

  const manifest = {
    schema: 'EditorialRenderManifestV1', runtime: await page.evaluate(() => window.__em2.version), film_id: plan.film_id, aspect: plan.aspect,
    plan_sha256: sha(fs.readFileSync(planPath)), frames: total, fps, output: plan.output, mp4: path.basename(mp4), mp4_sha256: sha(fs.readFileSync(mp4)),
    contact_sheet: `contact_${plan.aspect}.png`, transition_strip: stripFrames.length ? `transitions_${plan.aspect}.png` : null,
    audio, captions_burned: captions, captions_policy: plan.captions_policy || 'burned', page_errors: errors, authorship, native_profile: plan.beats.every((b) => b.composition.native_profile && !b.composition.derived_by_scaling),
  };
  fs.writeFileSync(path.join(outDir, `render_${plan.aspect}.json`), JSON.stringify(manifest, null, 2));
  console.log(JSON.stringify({ mp4, frames: total, errors: errors.length, audio, authorship: authorship.codes }, null, 1));
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
