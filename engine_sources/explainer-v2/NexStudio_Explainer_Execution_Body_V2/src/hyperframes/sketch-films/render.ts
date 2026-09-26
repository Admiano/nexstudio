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
import { renderSelfHostedChromium } from "../self-hosted-renderer.js";

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

async function main() {
  const [, , specArg, outArg, ...rest] = process.argv;
  if (!specArg || !outArg) {
    console.error("usage: render.ts <spec.json> <out.mp4> [--inspect <dir>] [--no-poster]");
    process.exit(2);
  }
  const specPath = path.resolve(specArg);
  const outPath = path.resolve(outArg);
  const inspectIdx = rest.indexOf("--inspect");
  const inspectDir = inspectIdx >= 0 ? path.resolve(rest[inspectIdx + 1]) : undefined;
  const noPoster = rest.includes("--no-poster");

  const spec = JSON.parse(await readFile(specPath, "utf8")) as SketchFilmSpec;
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

  const result = await renderSelfHostedChromium(bundle, {
    fps: spec.fps,
    outputPath: outPath,
    inspectionFrameDirectory: inspectDir,
  });
  console.log(JSON.stringify({ bundlePath, result }, null, 2));
  if (result.status !== "completed") process.exit(1);

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
