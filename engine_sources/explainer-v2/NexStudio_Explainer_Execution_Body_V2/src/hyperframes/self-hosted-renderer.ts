import { createServer } from "node:http";
import { createHash } from "node:crypto";
import { execFile, spawn } from "node:child_process";
import { promisify } from "node:util";
import {
  copyFile,
  mkdir,
  mkdtemp,
  readFile,
  readdir,
  rm,
  stat,
  writeFile,
} from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { chromium, type Browser } from "playwright-core";
import { findChromiumExecutable, resolveFfmpegExecutable } from "../lib/runtime-executables";
import type { CompositionBundle } from "./types";
import type { RenderOptions, UnifiedRenderResult } from "./renderer";

const execFileAsync = promisify(execFile);

function contentType(file: string) {
  const extension = path.extname(file).toLowerCase();
  return {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
  }[extension] ?? "application/octet-stream";
}

async function directoryBytes(root: string): Promise<number> {
  let bytes = 0;
  for (const entry of await readdir(root, { withFileTypes: true })) {
    const target = path.join(root, entry.name);
    bytes += entry.isDirectory() ? await directoryBytes(target) : (await stat(target)).size;
  }
  return bytes;
}

async function processRssBytes(pid: number | undefined) {
  if (!pid) return 0;
  try {
    if (process.platform === "win32") {
      const { stdout } = await execFileAsync("tasklist", ["/fi", `PID eq ${pid}`, "/fo", "csv", "/nh"], { windowsHide: true });
      const match = stdout.match(/"([\d,]+)\s+K"\s*$/m);
      return match ? Number(match[1].replaceAll(",", "")) * 1024 : 0;
    }
    const status = await readFile(`/proc/${pid}/status`, "utf8");
    const match = status.match(/^VmRSS:\s+(\d+)\s+kB$/m);
    return match ? Number(match[1]) * 1024 : 0;
  } catch {
    return 0;
  }
}

async function runFfmpeg(args: string[], timeoutMs: number, onSample: (pid?: number) => Promise<void>) {
  const started = performance.now();
  const child = spawn(resolveFfmpegExecutable(), args, { windowsHide: true, stdio: ["ignore", "ignore", "pipe"] });
  let stderr = "";
  child.stderr.setEncoding("utf8");
  child.stderr.on("data", (chunk: string) => {
    stderr = `${stderr}${chunk}`.slice(-12_000);
  });
  const sampler = setInterval(() => void onSample(child.pid), 500);
  sampler.unref();
  const timeout = setTimeout(() => child.kill("SIGKILL"), timeoutMs);
  timeout.unref();
  const code = await new Promise<number | null>((resolve, reject) => {
    child.once("error", reject);
    child.once("exit", resolve);
  }).finally(() => {
    clearInterval(sampler);
    clearTimeout(timeout);
  });
  await onSample(child.pid);
  if (code !== 0) throw new Error(`FFmpeg encode failed (${code ?? "terminated"}): ${stderr.slice(-2_000)}`);
  return performance.now() - started;
}

export function audioArguments(bundle: CompositionBundle, root: string) {
  const inputs: string[] = [];
  const filters: string[] = [];
  const mixLabels: string[] = [];
  let inputIndex = 1;
  const narrationLabels: string[] = [];
  let musicLabel: string | undefined;

  for (const track of bundle.manifest.audioTracks) {
    if (track.id === "sound-effect") {
      for (const [cueIndex, cue] of (track.cueTimesSec ?? []).entries()) {
        inputs.push("-i", path.join(root, track.path));
        const label = `sfx${cueIndex}`;
        const delayMs = Math.max(0, Math.round(cue * 1_000));
        // aformat forces a stereo layout before the 2-slot adelay — mono SFX
        // sources otherwise leave the downstream aresample without a channel map.
        filters.push(`[${inputIndex}:a]atrim=0:${track.durationSec},asetpts=PTS-STARTPTS,aformat=channel_layouts=stereo,volume=${track.volume ?? 0.45},adelay=${delayMs}|${delayMs}[${label}]`);
        mixLabels.push(`[${label}]`);
        inputIndex += 1;
      }
      continue;
    }
    if (track.id === "music") inputs.push("-stream_loop", "-1");
    inputs.push("-i", path.join(root, track.path));
    const narrationTrack = track.id === "narration" || track.id.startsWith("narration-");
    const label = narrationTrack ? `narration${inputIndex}` : track.id === "music" ? "musicbase" : `audio${inputIndex}`;
    const duration = track.id === "music" ? bundle.durationSeconds : Math.min(bundle.durationSeconds, track.durationSec);
    const delayMs = narrationTrack ? Math.max(0, Math.round((track.startSec ?? 0) * 1_000)) : 0;
    filters.push(`[${inputIndex}:a]atrim=0:${duration},asetpts=PTS-STARTPTS,aformat=channel_layouts=stereo,volume=${track.volume ?? (track.id === "music" ? 0.18 : 1)}${delayMs ? `,adelay=${delayMs}|${delayMs}` : ""}[${label}]`);
    if (narrationTrack) narrationLabels.push(`[${label}]`);
    else if (track.id === "music") musicLabel = label;
    else mixLabels.push(`[${label}]`);
    inputIndex += 1;
  }

  let narrationBus: string | undefined;
  if (narrationLabels.length === 1) narrationBus = narrationLabels[0];
  else if (narrationLabels.length > 1) {
    // These clips are placed on different scene timestamps. FFmpeg's default
    // amix normalization divides every active clip by the total input count,
    // even while the other delayed inputs are silent. That made a six-scene
    // narration bus roughly 15 dB quieter than its source.
    filters.push(`${narrationLabels.join("")}amix=inputs=${narrationLabels.length}:duration=longest:dropout_transition=0:normalize=0[narrationbus]`);
    narrationBus = "[narrationbus]";
  }
  if (narrationBus && musicLabel) {
    const music = bundle.manifest.audioTracks.find((track) => track.id === "music");
    if (music?.duckUnderNarration !== false) {
      filters.push(`${narrationBus}asplit=2[narrationmix][narrationside]`);
      filters.push(`[${musicLabel}][narrationside]sidechaincompress=threshold=0.025:ratio=8:attack=20:release=350[duckedmusic]`);
      mixLabels.unshift("[narrationmix]", "[duckedmusic]");
    } else {
      mixLabels.unshift(narrationBus, `[${musicLabel}]`);
    }
  } else {
    if (narrationBus) mixLabels.unshift(narrationBus);
    if (musicLabel) mixLabels.unshift(`[${musicLabel}]`);
  }

  if (!mixLabels.length) return { inputs, filters: [], outputLabel: undefined };
  if (mixLabels.length === 1) {
    filters.push(`${mixLabels[0]}aformat=channel_layouts=stereo,apad,atrim=0:${bundle.durationSeconds},loudnorm=I=-16:TP=-1.5:LRA=11,aformat=channel_layouts=stereo,aresample=48000[mixedaudio]`);
  } else {
    // aformat pins stereo on both sides of loudnorm — amix leaves the channel
    // layout unnegotiated, which made aresample fail on mono SFX inputs.
    filters.push(`${mixLabels.join("")}amix=inputs=${mixLabels.length}:duration=longest:dropout_transition=0:normalize=0,aformat=channel_layouts=stereo,apad,atrim=0:${bundle.durationSeconds},loudnorm=I=-16:TP=-1.5:LRA=11,aformat=channel_layouts=stereo,aresample=48000[mixedaudio]`);
  }
  return { inputs, filters, outputLabel: "mixedaudio" };
}

export async function renderSelfHostedChromium(
  bundle: CompositionBundle,
  options: RenderOptions = {},
): Promise<UnifiedRenderResult> {
  const renderId = `nexstudios-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const workDir = await mkdtemp(path.join(os.tmpdir(), `${renderId}-`));
  const framesDir = path.join(workDir, "frames");
  const fps = Math.max(1, Math.min(60, Math.round(options.fps ?? 30)));
  const totalFrames = Math.ceil(bundle.durationSeconds * fps);
  const targetMp4Path = options.outputPath ?? path.resolve("output", "nexstudios-owned", `${renderId}.mp4`);
  const startedAt = performance.now();
  let frameRenderMs = 0;
  let encodeMs = 0;
  let temporaryDiskBytes = 0;
  let peakMemoryBytes = process.memoryUsage().rss;
  let browser: Browser | undefined;
  let server: ReturnType<typeof createServer> | undefined;

  const sampleMemory = async (childPid?: number) => {
    peakMemoryBytes = Math.max(
      peakMemoryBytes,
      process.memoryUsage().rss + await processRssBytes(childPid),
    );
  };

  try {
    await mkdir(framesDir, { recursive: true });
    await mkdir(path.dirname(targetMp4Path), { recursive: true });
    for (const [relative, value] of Object.entries(bundle.files)) {
      const target = path.resolve(workDir, relative);
      if (!target.startsWith(`${path.resolve(workDir)}${path.sep}`)) throw new Error(`Unsafe composition bundle path: ${relative}`);
      await mkdir(path.dirname(target), { recursive: true });
      await writeFile(target, typeof value === "string" ? value : Buffer.from(value));
    }

    server = createServer(async (request, response) => {
      try {
        const pathname = decodeURIComponent(new URL(request.url ?? "/", "http://127.0.0.1").pathname);
        const relative = pathname === "/" ? bundle.entry : pathname.replace(/^\/+/, "");
        const target = path.resolve(workDir, relative);
        if (!target.startsWith(`${path.resolve(workDir)}${path.sep}`)) throw new Error("Path outside bundle.");
        const bytes = await readFile(target);
        response.writeHead(200, { "content-type": contentType(target), "cache-control": "no-store" });
        response.end(bytes);
      } catch {
        response.writeHead(404, { "content-type": "text/plain" });
        response.end("Not found");
      }
    });
    await new Promise<void>((resolve, reject) => {
      server!.once("error", reject);
      server!.listen(0, "127.0.0.1", resolve);
    });
    const address = server.address();
    if (!address || typeof address === "string") throw new Error("NexStudios bundle server did not bind.");

    browser = await chromium.launch({
      executablePath: findChromiumExecutable() ?? (() => { throw new Error("No supported Chromium executable is installed for NexStudios rendering."); })(),
      headless: true,
      args: ["--no-sandbox", "--disable-dev-shm-usage", "--disable-background-timer-throttling", "--disable-renderer-backgrounding"],
    });
    const entryHtml = bundle.files[bundle.entry];
    const canInline = typeof entryHtml === "string" && !/data-composition-src=|<iframe\b/i.test(entryHtml);
    const configuredBatchSize = Number(process.env.NEXSTUDIO_RENDER_FRAME_BATCH_SIZE ?? 240);
    const frameBatchSize = Math.max(fps, Math.min(900, Number.isFinite(configuredBatchSize) ? Math.round(configuredBatchSize) : 240));

    const openCapturePage = async () => {
      if (!browser) throw new Error("NexStudios render browser is unavailable.");
      const context = await browser.newContext({
        viewport: { width: bundle.width, height: bundle.height },
        deviceScaleFactor: 1,
        reducedMotion: "no-preference",
      });
      const page = await context.newPage();
      if (canInline) {
        // Self-contained bundles are safer and more portable when loaded directly:
        // this works in hardened render hosts that block every browser navigation,
        // including loopback and file:// URLs, while preserving the exact authored
        // document and deterministic timeline.
        await page.setContent(entryHtml, { waitUntil: "load", timeout: 30_000 });
      } else {
        await page.goto(`http://127.0.0.1:${address.port}/${bundle.entry}`, { waitUntil: "load", timeout: 30_000 });
      }
      await page.waitForFunction(() => (window as Window & { __renderReady?: boolean }).__renderReady === true, undefined, { timeout: 30_000 });
      const productionBoundary = await page.evaluate(() => {
        const root = document.querySelector<HTMLElement>("[data-nex-production-canvas]");
        const forbidden = root ? [...root.querySelectorAll<HTMLElement>("[data-nex-studio-only],[data-nex-debug],[data-nex-review-control]")].map((node) => ({ tag: node.tagName, className: node.className, marker: node.getAttribute("data-nex-studio-only") || node.getAttribute("data-nex-debug") || node.getAttribute("data-nex-review-control") })) : [];
        return { rootExists: Boolean(root), forbidden };
      });
      if (!productionBoundary.rootExists) throw new Error("PRODUCTION_CAPTURE_ROOT_MISSING: expected [data-nex-production-canvas].");
      if (productionBoundary.forbidden.length) throw new Error(`PRODUCTION_CAPTURE_BOUNDARY_VIOLATION: ${JSON.stringify(productionBoundary.forbidden)}`);
      const productionBox = await page.locator("[data-nex-production-canvas]").boundingBox();
      if (!productionBox || productionBox.width < 2 || productionBox.height < 2) throw new Error("PRODUCTION_CAPTURE_ROOT_EMPTY");
      await page.evaluate(`(async () => {
        const documents = [document, ...[...document.querySelectorAll("iframe")].map((frame) => frame.contentDocument)];
        for (const documentValue of documents) {
          if (!documentValue) throw new Error("Composition iframe is not same-origin or did not load.");
          await documentValue.fonts.ready;
          for (const image of [...documentValue.images]) {
            if (!image.complete) await new Promise((resolve, reject) => {
              image.addEventListener("load", resolve, { once: true });
              image.addEventListener("error", () => reject(new Error("Image failed: " + (image.currentSrc || image.src))), { once: true });
            });
            await image.decode().catch(() => undefined);
            if (!image.naturalWidth || !image.naturalHeight) throw new Error("Image has no decoded geometry: " + (image.currentSrc || image.src));
          }
        }
        for (const frame of [...document.querySelectorAll("iframe")]) {
          if (frame.contentWindow?.__renderReady !== true) throw new Error("Composition iframe is not render-ready: " + frame.src);
        }
      })()`);
      return { context, page, productionBox };
    };

    let capture = await openCapturePage();
    const frameStartedAt = performance.now();
    for (let frameIndex = 0; frameIndex < totalFrames; frameIndex += 1) {
      if (frameIndex > 0 && frameIndex % frameBatchSize === 0) {
        // Long deterministic compositions used to accumulate enough browser/GSAP
        // state that Chromium could stall or be killed before a 30–60 second film
        // completed. Rehydrate a fresh capture document at bounded intervals and
        // seek directly to the next absolute frame. This is topic-agnostic and is
        // safe because the production timeline is required to be deterministic.
        await capture.context.close();
        capture = await openCapturePage();
        await sampleMemory();
      }
      const timeSec = frameIndex / fps;
      await capture.page.evaluate(async (time: number) => {
        const rootTimelines = (window as Window & { __timelines?: Record<string, { time?: (seconds: number, suppressEvents?: boolean) => unknown }> }).__timelines ?? {};
        for (const timeline of Object.values(rootTimelines)) timeline.time?.(time, false);
        for (const frame of [...document.querySelectorAll<HTMLIFrameElement>("iframe[data-start]")]) {
          const start = Number(frame.dataset.start ?? 0);
          const duration = Math.max(0.001, Number(frame.dataset.duration ?? 0.001));
          const localTime = Math.max(0, Math.min(duration, time - start));
          const sceneWindow = frame.contentWindow as (Window & {
            __timelines?: Record<string, { time?: (seconds: number, suppressEvents?: boolean) => unknown }>;
            __seekFrame?: (seconds: number) => Promise<void> | void;
          }) | null;
          const timelines = sceneWindow?.__timelines ?? {};
          for (const timeline of Object.values(timelines)) timeline.time?.(localTime, false);
          // Canonical scenes with local video assets expose this hook so the
          // browser waits for the exact decoded media frame before capture.
          await sceneWindow?.__seekFrame?.(localTime);
        }
        await new Promise<void>((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve())));
      }, timeSec);
      await capture.page.screenshot({
        path: path.join(framesDir, `frame-${String(frameIndex).padStart(7, "0")}.jpg`),
        type: "jpeg",
        quality: 94,
        animations: "disabled",
        clip: capture.productionBox,
      });
      if (frameIndex % fps === 0) await sampleMemory();
    }
    frameRenderMs = performance.now() - frameStartedAt;
    await sampleMemory();
    await capture.context.close();
    await browser.close();
    browser = undefined;

    if (options.inspectionFrameDirectory) {
      await mkdir(options.inspectionFrameDirectory, { recursive: true });
      for (const [label, index] of [
        ["first", 0],
        ["middle", Math.floor((totalFrames - 1) / 2)],
        ["last", totalFrames - 1],
      ] as const) {
        await copyFile(
          path.join(framesDir, `frame-${String(index).padStart(7, "0")}.jpg`),
          path.join(options.inspectionFrameDirectory, `${label}.jpg`),
        );
      }
    }

    temporaryDiskBytes = await directoryBytes(workDir);
    const audio = audioArguments(bundle, workDir);
    const ffmpegArgs = [
      "-y",
      "-framerate", String(fps),
      "-i", path.join(framesDir, "frame-%07d.jpg"),
      ...audio.inputs,
    ];
    if (audio.outputLabel) {
      ffmpegArgs.push("-filter_complex", audio.filters.join(";"), "-map", "0:v:0", "-map", `[${audio.outputLabel}]`);
    } else {
      ffmpegArgs.push("-map", "0:v:0", "-an");
    }
    ffmpegArgs.push(
      "-t", String(bundle.durationSeconds),
      "-r", String(fps),
      "-c:v", "libx264",
      "-preset", "medium",
      "-crf", "18",
      "-pix_fmt", "yuv420p",
      ...(audio.outputLabel ? ["-c:a", "aac", "-b:a", "192k"] : []),
      "-movflags", "+faststart",
      targetMp4Path,
    );
    encodeMs = await runFfmpeg(ffmpegArgs, Math.max(180_000, bundle.durationSeconds * 30_000), sampleMemory);
    const output = await readFile(targetMp4Path);
    const metrics = {
      frameCount: totalFrames,
      fps,
      width: bundle.width,
      height: bundle.height,
      frameRenderMs,
      encodeMs,
      totalWallMs: performance.now() - startedAt,
      peakMemoryBytes,
      temporaryDiskBytes,
      outputBytes: output.byteLength,
      audioTrackCount: bundle.manifest.audioTracks.length,
    };
    return {
      provider: "nexstudios_owned",
      renderId,
      status: "completed",
      localOutputPath: targetMp4Path,
      actualDurationSeconds: bundle.durationSeconds,
      actualAspectRatio: bundle.width === bundle.height ? "1:1" : bundle.width > bundle.height ? "16:9" : "9:16",
      actualResolution: `${bundle.width}x${bundle.height}`,
      frameRateFps: fps,
      fileSizeBytes: output.byteLength,
      cost: "Local Chromium + FFmpeg",
      metrics,
    };
  } catch (error) {
    return {
      provider: "nexstudios_owned",
      renderId,
      status: "failed",
      error: error instanceof Error ? error.message : "NexStudios owned render failed.",
      metrics: {
        frameCount: totalFrames,
        fps,
        width: bundle.width,
        height: bundle.height,
        frameRenderMs,
        encodeMs,
        totalWallMs: performance.now() - startedAt,
        peakMemoryBytes,
        temporaryDiskBytes,
        outputBytes: 0,
        audioTrackCount: bundle.manifest.audioTracks.length,
      },
    };
  } finally {
    await browser?.close().catch(() => undefined);
    if (server) await new Promise<void>((resolve) => server!.close(() => resolve()));
    await rm(workDir, { recursive: true, force: true }).catch(() => undefined);
  }
}

export function ownedRenderFingerprint(bundle: CompositionBundle, fps: number) {
  return createHash("sha256").update(`${bundle.manifest.compositionHash}:${fps}`).digest("hex");
}
