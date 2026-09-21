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
 * (voice segments, admitted sound accents with their layers, the music bed) and
 * mixed on three buses — voice, sfx, music — into a limited, loudness-measured
 * master, with each bus also written out as a stem.
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

const DEFAULT_MIX = {
  target_lufs: -16.0, true_peak_dbtp: -1.0,
  buses: {
    voice: { highpass_hz: 80, compressor: { threshold_db: -20, ratio: 2.0, attack_ms: 8, release_ms: 120 }, trim_db: 0 },
    sfx: { compressor: { threshold_db: -18, ratio: 3.0, attack_ms: 3, release_ms: 90 }, trim_db: 0 },
    music: { highpass_hz: 40, trim_db: 0, duck: { threshold: 0.1, window_db: 12, attack_ms: 30, release_ms: 450, floor_db: -8 } },
  },
  limiter: { attack_ms: 5, release_ms: 50 },
};
// With a voice on the bus the level is already set by the speaker: a big correction means a broken
// source, so the makeup is bounded and the gate reports the miss. Without one (music + sfx only,
// or a silent placeholder voice) the bed and accents are simply raised to the target.
const MAKEUP_MAX_DB = { voiced: 6, unvoiced: 24 };
const SILENT_LUFS = -50;
const TRUE_PEAK_GUARD_DB = 0.5;

function compressor(c) {
  return `acompressor=threshold=${Math.pow(10, c.threshold_db / 20).toFixed(5)}:ratio=${c.ratio}:attack=${c.attack_ms}:release=${c.release_ms}:makeup=1`;
}

// EBU R128 measurement of a finished file: integrated loudness and true peak.
function measureLoudness(file) {
  const r = spawnSync('ffmpeg', ['-hide_banner', '-nostats', '-i', file, '-af', 'ebur128=peak=true', '-f', 'null', '-'], { encoding: 'utf8' });
  const I = [...r.stderr.matchAll(/I:\s+(-?[\d.]+) LUFS/g)].pop();
  const P = [...r.stderr.matchAll(/Peak:\s+(-?[\d.]+|-inf) dBFS/g)].pop();
  const R = [...r.stderr.matchAll(/LRA:\s+(-?[\d.]+) LU/g)].pop();
  if (!I || !P) throw new Error(`loudness measurement failed for ${file}`);
  // a silent stem measures -inf true peak; the manifest keeps a finite floor
  return { integrated_lufs: Number(I[1]), true_peak_dbtp: P[1] === '-inf' ? -120 : Number(P[1]), range_lu: R ? Number(R[1]) : null };
}

/*
 * Bus mixer. Every source is verified (file present, license, sha256) and routed to one of
 * three buses; each bus gets its own gain staging and dynamics; the master is summed,
 * brought to the target loudness with a measured makeup gain, then limited to the
 * true-peak ceiling. Two passes: mix + measure, then the same graph with the makeup applied.
 */
function buildAudio(plan, out, stemsDir) {
  const mix = { ...DEFAULT_MIX, ...(plan.mix || {}) };
  const buses = { ...DEFAULT_MIX.buses, ...(mix.buses || {}) };
  const durS = (plan.duration_ms / 1000).toFixed(3);
  const dur = plan.duration_ms / 1000;
  const fmt = 'aformat=sample_rates=48000:channel_layouts=stereo';
  const wantsMusic = Boolean(plan.music && plan.music.path);
  let layerCount = 0, accentCount = 0;

  const graph = (makeupDb) => {
    const inputs = [];
    const filters = [];
    inputs.push('-f', 'lavfi', '-t', durS, '-i', 'anullsrc=r=48000:cl=stereo');
    let n = 1;
    // ---- voice bus
    const voice = [];
    for (const seg of plan.voice.segments) {
      if (!seg.audio_path || !fs.existsSync(seg.audio_path)) continue;
      if (seg.start_ms + seg.duration_ms > plan.duration_ms + 1000 / plan.fps) {
        throw new Error(`voice segment ${seg.beat_id} ends at ${seg.start_ms + seg.duration_ms}ms but the film is ${plan.duration_ms}ms; the audio would be cut`);
      }
      inputs.push('-i', seg.audio_path);
      filters.push(`[${n}:a]${fmt},adelay=${seg.start_ms}|${seg.start_ms}[v${n}]`);
      voice.push(`[v${n}]`);
      n += 1;
    }
    const vb = buses.voice;
    filters.push(`[0:a]${voice.join('')}amix=inputs=${voice.length + 1}:normalize=0:duration=first,highpass=f=${vb.highpass_hz},${compressor(vb.compressor)},volume=${vb.trim_db}dB[voxbus]`);
    filters.push('[voxbus]asplit=3[voxm][voxk][voxstem]');
    // ---- sfx bus: every accent layer is its own input
    const layers = [];
    accentCount = 0;
    for (const beat of plan.beats) {
      for (const acc of beat.sound.accents) {
        accentCount += 1;
        const parts = acc.layers && acc.layers.length ? acc.layers : [{ ...acc, role: 'body', offset_ms: 0 }];
        for (const L of parts) {
          if (!fs.existsSync(L.path)) throw new Error(`sound asset missing: ${L.path}`);
          // Layers obey the same provenance law as the bed: bound license + sha256 or the render throws.
          if (!L.license) throw new Error(`sound layer ${L.asset_id || L.path} has no license evidence`);
          if (L.sha256 && sha(fs.readFileSync(L.path)) !== L.sha256) throw new Error(`sound layer sha256 mismatch: ${L.path}`);
          const at = Math.max(0, acc.film_at_ms + (L.offset_ms || 0));
          inputs.push('-i', L.path);
          const trim = L.trim_ms ? `atrim=0:${(L.trim_ms / 1000).toFixed(3)},afade=t=out:st=${Math.max(0, (L.trim_ms - 120) / 1000).toFixed(3)}:d=0.12,` : '';
          filters.push(`[${n}:a]${fmt},${trim}volume=${L.gain_db}dB,adelay=${at}|${at}[s${n}]`);
          layers.push(`[s${n}]`);
          n += 1;
        }
      }
    }
    layerCount = layers.length;
    const sb = buses.sfx;
    inputs.push('-f', 'lavfi', '-t', durS, '-i', 'anullsrc=r=48000:cl=stereo');
    const sfxBase = n; n += 1;
    filters.push(`[${sfxBase}:a]${layers.join('')}amix=inputs=${layers.length + 1}:normalize=0:duration=first,${compressor(sb.compressor)},volume=${sb.trim_db}dB[sfxbus]`);
    filters.push('[sfxbus]asplit=2[sfxm][sfxstem]');
    // ---- music bus
    const mb = buses.music;
    if (wantsMusic) {
      // Music is bound only with rights evidence: the plan must carry the license + sha256 of the file.
      if (plan.music.status !== 'BOUND_CC0' || !plan.music.license) throw new Error('music slot has a path but no rights evidence');
      if (!fs.existsSync(plan.music.path)) throw new Error(`music asset missing: ${plan.music.path}`);
      if (plan.music.sha256 && sha(fs.readFileSync(plan.music.path)) !== plan.music.sha256) throw new Error(`music sha256 mismatch: ${plan.music.path}`);
      // The bed starts `start_offset_ms` into the file so its beat grid meets the film's landings (groove fit).
      const start = (plan.music.start_offset_ms || 0) / 1000;
      inputs.push('-stream_loop', '-1', '-t', (dur + start + 1).toFixed(3), '-i', plan.music.path);
      const mi = n; n += 1;
      const gain = plan.music.gain_db == null ? -19 : plan.music.gain_db;
      const fin = ((plan.music.fade_in_ms || 0) / 1000).toFixed(3);
      const fout = ((plan.music.fade_out_ms || 0) / 1000).toFixed(3);
      filters.push(`[${mi}:a]${fmt},atrim=start=${start.toFixed(3)},asetpts=PTS-STARTPTS,highpass=f=${mb.highpass_hz},volume=${gain + (mb.trim_db || 0)}dB,` +
        `afade=t=in:st=0:d=${fin},afade=t=out:st=${(dur - Number(fout)).toFixed(3)}:d=${fout}[mraw]`);
      if (voice.length) {
        // Sidechain-duck the bed under the voice bus. The compressor ratio is chosen so that a voice
        // sitting `window_db` above the threshold pulls the bed down by exactly the plan's duck floor.
        const depth = Math.abs(plan.music.duck_under_voice_db || mb.duck.floor_db);
        const win = mb.duck.window_db || 12;
        const ratio = Math.min(20, Math.max(1.2, 1 / Math.max(0.05, 1 - depth / win))).toFixed(2);
        filters.push(`[mraw][voxk]sidechaincompress=threshold=${mb.duck.threshold}:ratio=${ratio}:attack=${mb.duck.attack_ms}:release=${mb.duck.release_ms}:makeup=1[musbus]`);
      } else {
        filters.push('[voxk]anullsink;[mraw]anull[musbus]');
      }
    } else {
      inputs.push('-f', 'lavfi', '-t', durS, '-i', 'anullsrc=r=48000:cl=stereo');
      filters.push(`[voxk]anullsink;[${n}:a]anull[musbus]`);
      n += 1;
    }
    filters.push('[musbus]asplit=2[musm][musstem]');
    // ---- master: sum, makeup to target, ceiling
    // alimiter is a sample-peak limiter: run it 4x oversampled so inter-sample (true) peaks are the ones being
    // caught, with a small guard for the residual overshoot the final decimation can reintroduce.
    const limit = Math.pow(10, (mix.true_peak_dbtp - TRUE_PEAK_GUARD_DB) / 20).toFixed(4);
    filters.push(`[voxm][sfxm][musm]amix=inputs=3:normalize=0:duration=first,volume=${makeupDb.toFixed(2)}dB,` +
      `aresample=192000,alimiter=limit=${limit}:attack=${mix.limiter.attack_ms}:release=${mix.limiter.release_ms}:level=false,aresample=48000[mix]`);
    const outs = ['-map', '[mix]', '-t', durS, '-c:a', 'pcm_s16le', out];
    if (stemsDir) {
      fs.mkdirSync(stemsDir, { recursive: true });
      for (const [lbl, name] of [['voxstem', 'voice'], ['sfxstem', 'sfx'], ['musstem', 'music']]) {
        outs.push('-map', `[${lbl}]`, '-t', durS, '-c:a', 'pcm_s16le', path.join(stemsDir, `${name}.wav`));
      }
    } else {
      filters.push('[voxstem]anullsink;[sfxstem]anullsink;[musstem]anullsink');
    }
    ff([...inputs, '-filter_complex', filters.join(';'), ...outs]);
  };

  graph(0);
  const first = measureLoudness(out);
  const voiceLufs = stemsDir ? measureLoudness(path.join(stemsDir, 'voice.wav')).integrated_lufs : null;
  const voiced = voiceLufs != null && voiceLufs > SILENT_LUFS;
  let makeup = 0;
  if (Number.isFinite(first.integrated_lufs)) {
    const cap = voiced ? MAKEUP_MAX_DB.voiced : MAKEUP_MAX_DB.unvoiced;
    makeup = Math.max(-cap, Math.min(cap, mix.target_lufs - first.integrated_lufs));
    if (Math.abs(makeup) >= 0.3) graph(makeup); else makeup = 0;
  }
  const loud = makeup ? measureLoudness(out) : first;
  const musicStatus = wantsMusic ? `${plan.music.status}:${path.basename(plan.music.path)}` : (plan.music ? plan.music.status : 'NONE');
  return {
    voice_segments: plan.voice.segments.length, accents: accentCount, layers: layerCount, music: musicStatus,
    buses: ['voice', 'sfx', 'music'], stems: stemsDir ? ['voice.wav', 'sfx.wav', 'music.wav'] : [],
    groove: wantsMusic ? plan.music.groove : null,
    loudness: { ...loud, target_lufs: mix.target_lufs, ceiling_dbtp: mix.true_peak_dbtp, makeup_db: Number(makeup.toFixed(2)), pre_makeup_lufs: first.integrated_lufs,
      voice_lufs: voiceLufs, voiced },
  };
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
  const audio = buildAudio(plan, audioPath, path.join(outDir, `stems_${plan.aspect}`));

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
