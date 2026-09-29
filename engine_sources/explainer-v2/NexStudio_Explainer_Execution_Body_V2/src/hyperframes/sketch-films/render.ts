/**
 * Render a sketch-film spec to MP4 via the self-hosted Chromium renderer.
 *
 *   tsx src/hyperframes/sketch-films/render.ts <spec.json> <out.mp4> [--inspect <dir>]
 *
 * Post-render delivery pass (the brag-style finish):
 *   - verify: ffprobe the file — duration/fps/codec/pix_fmt/audio presence
 *   - poster: pick spec.posterSec (or the settled last beat), extract the
 *     frame, bake it as frame 0 so embeds/thumbnails show the brand moment
 *   - share: write <out>-share.txt from spec.shareCopy
 *   - report: <out>.report.json with the probed facts + poster choice
 *
 * Run from the engine root so `@/` path aliases resolve (see engine tsconfig).
 */
import path from "node:path";
import { readFile, writeFile, mkdir, rename } from "node:fs/promises";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";
import { assembleSketchFilmBundle } from "./assemble.js";
import type { SketchFilmSpec } from "./spec.js";
import { renderSelfHostedChromium, audioArguments } from "../self-hosted-renderer.js";
import { mkdtemp } from "node:fs/promises";
import * as os from "node:os";

const execFileAsync = promisify(execFile);
const here = path.dirname(fileURLToPath(import.meta.url));
const engineRoot = path.resolve(here, "../../..");

type Probe = {
  duration: number; fps: number; width: number; height: number;
  vcodec: string; pixFmt: string; colorRange: string; acodec: string | null;
  warnings: string[];
};

async function probeFile(file: string, spec: SketchFilmSpec): Promise<Probe> {
  const { stdout } = await execFileAsync("ffprobe", [
    "-v", "error", "-show_entries",
    "format=duration:stream=codec_name,codec_type,width,height,r_frame_rate,pix_fmt,color_range",
    "-of", "json", file,
  ]);
  const j = JSON.parse(stdout);
  const vs = (j.streams || []).find((s: Record<string, string>) => s.codec_type === "video") || {};
  const as = (j.streams || []).find((s: Record<string, string>) => s.codec_type === "audio");
  const fps = eval(String(vs.r_frame_rate || "0/1").replace(/[^0-9/]/g, "")) || 0;
  const p: Probe = {
    duration: Number(j.format?.duration || 0), fps: Math.round(fps * 100) / 100,
    width: Number(vs.width || 0), height: Number(vs.height || 0),
    vcodec: vs.codec_name || "", pixFmt: vs.pix_fmt || "", colorRange: vs.color_range || "unspecified",
    acodec: as ? as.codec_name : null,
    warnings: [],
  };
  if (Math.abs(p.duration - spec.durationSeconds) > 0.35) p.warnings.push(`duration drift: ${p.duration}s vs ${spec.durationSeconds}s`);
  if (Math.abs(p.fps - spec.fps) > 0.6) p.warnings.push(`fps drift: ${p.fps} vs ${spec.fps}`);
  if (p.vcodec !== "h264" && p.vcodec !== "hevc") p.warnings.push(`unexpected vcodec ${p.vcodec}`);
  if (p.pixFmt !== "yuv420p") p.warnings.push(`pix_fmt ${p.pixFmt} — players expect yuv420p`);
  if (!p.acodec) p.warnings.push("no audio stream — music/SFX missing");
  return p;
}

async function bakePoster(videoPath: string, spec: SketchFilmSpec): Promise<{ posterPath: string; posterSec: number } | null> {
  const sec = spec.posterSec ?? spec.durationSeconds - 0.5;
  const posterPath = videoPath.replace(/\.mp4$/i, "") + "-poster.png";
  try {
    await execFileAsync("ffmpeg", [
      "-y", "-v", "error", "-ss", String(sec), "-i", videoPath,
      "-frames:v", "1", posterPath,
    ]);
    /* bake the poster as literal frame 0 — thumbnails and embeds show the
       brand moment, not the opening motion; one frame, 33ms, invisible */
    const tmpPath = videoPath.replace(/\.mp4$/i, "") + ".poster-baked.mp4";
    await execFileAsync("ffmpeg", [
      "-y", "-v", "error", "-i", videoPath, "-loop", "1", "-t", "0.04", "-i", posterPath,
      "-filter_complex", `[1:v]scale=${spec.width}:${spec.height}[p];[0:v][p]overlay=0:0:enable='eq(n,0)'`,
      "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
      "-c:a", "copy", tmpPath,
    ]);
    await rename(tmpPath, videoPath);
    return { posterPath, posterSec: sec };
  } catch (e) {
    console.error("poster bake skipped:", (e as Error).message);
    return null;
  }
}

/* --- composite render: AE-grade pixel transitions --------------------------
   Each scene renders in isolation (spec.segment), then ffmpeg xfade rebuilds
   the transitions in frame space — real deformation, not clip-path approxi-
   mations. A light post pass (temporal blur = motion blur + grain) lands
   on top. `cut` boundaries get a 0.1s micro-fade so the chain stays xfade. */
const XFADE: Record<string, string> = {
  fade: "fade", fadefilter: "fadegrays", wipe: "wipeleft", push: "slideleft",
  collage: "diagbr", doors: "vertopen", squeeze: "squeezev", crosswarp: "distance",
  iris: "circleopen", diamond: "rectcrop", clockwipe: "radial", blinds: "hrslice",
  crosshatch: "hlslice", dreamy: "fadegrays", swirl: "distance", linearblur: "hblur",
  dissolve: "dissolve", pixelize: "pixelize", starwipe: "circlecrop",
  torn: "hlslice", page: "wiperight", crumple: "pixelize", tape: "wipebl",
  shuffle: "vdslice", zoom: "distance", rise: "slideup", morph: "distance",
};

async function compositeRender(spec: SketchFilmSpec, specDir: string, outPath: string): Promise<number> {
  const workDir = await mkdtemp(path.join(os.tmpdir(), "nexfilm-composite-"));
  const filesDir = path.join(workDir, "files");
  const segPaths: string[] = [];
  const scenes = spec.scenes;
  for (let i = 0; i < scenes.length; i++) {
    const segSpec: SketchFilmSpec = {
      ...spec, scenes, segment: i,
      durationSeconds: scenes[i].duration,
      music: undefined, sfx: [], shareCopy: undefined, posterSec: undefined,
    };
    const segBundle = await assembleSketchFilmBundle(segSpec, { engineRoot, specDir });
    const segPath = path.join(workDir, `seg-${String(i).padStart(2, "0")}.mp4`);
    const r = await renderSelfHostedChromium(segBundle, { fps: spec.fps, outputPath: segPath });
    if (r.status !== "completed") throw new Error(`segment ${i} render failed: ${r.status}`);
    segPaths.push(segPath);
    console.error(`  segment ${i + 1}/${scenes.length} rendered (${scenes[i].type}, ${scenes[i].duration}s)`);
  }

  /* xfade chain — offset accumulates: out_len += dur_i - T_i.
     boundaryT[i] = the overlap consumed when scene i enters. */
  const n = segPaths.length;
  const vdurs = scenes.map(s => s.duration);
  const vfilters: string[] = [];
  const boundaryT: number[] = [0];
  let outLen = vdurs[0];
  let prev = "[0:v]";
  for (let i = 1; i < n; i++) {
    const tr = scenes[i].transition || "fade";
    const name = tr === "cut" ? "fade" : (XFADE[tr] ?? "fade");
    const T = tr === "cut" ? 0.1 : Math.min(0.7, Math.max(0.4, Math.min(vdurs[i - 1], vdurs[i]) * 0.15));
    const offset = Math.max(0, outLen - T);
    const label = i === n - 1 ? "vchain" : `vx${i}`;
    vfilters.push(`${prev}[${i}:v]xfade=transition=${name}:duration=${T.toFixed(3)}:offset=${offset.toFixed(3)}[${label}]`);
    prev = `[${label}]`;
    outLen += vdurs[i] - T;
    boundaryT[i] = T;
  }
  /* post pass — temporal blur + grain, off via spec.postFx === false */
  const post = spec.postFx === false ? "" : spec.postFx && spec.postFx.motionBlur === false ? "" : "tmix=frames=3:weights='1 2 1',";
  const grain = spec.postFx === false ? 0 : (spec.postFx?.grain ?? 4);
  const postChain = `${post}${grain ? `noise=alls=${grain}:allf=t,` : ""}format=yuv420p`;
  vfilters.push(`[vchain]${postChain}[vout]`);

  /* audio: film-level tracks muxed over the composite — reuse the shared
     audio graph builder, shifting its input indices past the n seg inputs */
  /* cue remap: a film-time cue inside scene j shifts by every overlap that
     boundary ≤ scene j consumed, so SFX still land on their moments */
  const sceneStarts = scenes.map(s => s.start ?? 0);
  const shiftCue = (c: number) => {
    let shift = 0;
    for (let i = 1; i < n; i++) if (sceneStarts[i] <= c + 1e-6) shift += boundaryT[i];
    return Math.max(0, c - shift);
  };
  const specAdj: SketchFilmSpec = {
    ...spec,
    durationSeconds: outLen,
    sfx: (spec.sfx ?? []).map(x => ({ ...x, atSec: x.atSec.map(shiftCue) })),
  };
  const bundle = await assembleSketchFilmBundle(specAdj, { engineRoot, specDir });
  await mkdir(filesDir, { recursive: true });
  for (const [rel, value] of Object.entries(bundle.files)) {
    const target = path.resolve(filesDir, rel);
    if (!target.startsWith(path.resolve(filesDir) + path.sep)) throw new Error(`unsafe path ${rel}`);
    await mkdir(path.dirname(target), { recursive: true });
    await writeFile(target, typeof value === "string" ? value : Buffer.from(value));
  }
  const audio = audioArguments(bundle, filesDir);
  const audioFilters = audio.filters.map(f => f.replace(/\[(\d+):a\]/g, (_m, k) => `[${Number(k) + n - 1}:a]`));
  const args = [
    "-y", "-v", "warning",
    ...segPaths.flatMap(p => ["-i", p]),
    ...audio.inputs,
    "-filter_complex", [...vfilters, ...audioFilters].join(";"),
    "-map", "[vout]",
    ...(audio.outputLabel ? ["-map", `[${audio.outputLabel}]`] : ["-an"]),
    "-t", String(outLen), "-r", String(spec.fps),
    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
    ...(audio.outputLabel ? ["-c:a", "aac", "-b:a", "160k"] : []),
    outPath,
  ];
  await execFileAsync("ffmpeg", args, { timeout: 300_000, maxBuffer: 8 << 20 });
  console.error(`  composite: ${n} segments → ${outLen.toFixed(1)}s via xfade`);
  return outLen;
}

async function main() {
  const [, , specArg, outArg, ...rest] = process.argv;
  if (!specArg || !outArg) {
    console.error("usage: render.ts <spec.json> <out.mp4> [--inspect <dir>] [--no-poster] [--compose]");
    process.exit(2);
  }
  const specPath = path.resolve(specArg);
  const outPath = path.resolve(outArg);
  const inspectIdx = rest.indexOf("--inspect");
  const inspectDir = inspectIdx >= 0 ? path.resolve(rest[inspectIdx + 1]) : undefined;
  const noPoster = rest.includes("--no-poster");
  const compose = rest.includes("--compose");

  let spec = JSON.parse(await readFile(specPath, "utf8")) as SketchFilmSpec;
  const bundle = await assembleSketchFilmBundle(spec, {
    engineRoot,
    specDir: path.dirname(specPath),
  });
  const bundlePath = outPath.replace(/\.mp4$/i, "") + ".bundle.json";
  await mkdir(path.dirname(outPath), { recursive: true });
  await writeFile(
    bundlePath,
    JSON.stringify(
      {
        ...bundle,
        files: Object.fromEntries(
          Object.entries(bundle.files).map(([k, v]) => [k, typeof v === "string" ? v : `<${v.byteLength} bytes>`]),
        ),
      },
      null,
      2,
    ),
  );

  if (compose) {
    const outLen = await compositeRender(spec, path.dirname(specPath), outPath);
    spec = { ...spec, durationSeconds: outLen, posterSec: Math.min(spec.posterSec ?? outLen - 0.5, outLen - 0.3) };
    console.log(JSON.stringify({ bundlePath, result: { status: "completed", localOutputPath: outPath, mode: "composite" } }, null, 2));
  } else {
    const result = await renderSelfHostedChromium(bundle, {
      fps: spec.fps,
      outputPath: outPath,
      inspectionFrameDirectory: inspectDir,
    });
    console.log(JSON.stringify({ bundlePath, result }, null, 2));
    if (result.status !== "completed") process.exit(1);
  }

  /* delivery pass: verify → poster → share copy → report */
  const probe = await probeFile(outPath, spec);
  const poster = noPoster ? null : await bakePoster(outPath, spec);
  let sharePath: string | undefined;
  if (spec.shareCopy) {
    sharePath = outPath.replace(/\.mp4$/i, "") + "-share.txt";
    await writeFile(sharePath, spec.shareCopy + "\n");
  }
  const report = {
    surface: spec.surface || "sketch",
    probe, poster, sharePath,
    beats: spec.scenes.length,
  };
  const reportPath = outPath.replace(/\.mp4$/i, "") + ".report.json";
  await writeFile(reportPath, JSON.stringify(report, null, 2));
  console.log(`verified ${outPath}: ${probe.duration}s ${probe.fps}fps ${probe.width}x${probe.height} ${probe.vcodec}/${probe.pixFmt} audio=${probe.acodec || "NONE"}` +
    (probe.warnings.length ? ` WARNINGS: ${probe.warnings.join("; ")}` : "") +
    (poster ? ` poster@${poster.posterSec}s` : "") + (sharePath ? ` shareCopy` : ""));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
