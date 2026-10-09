import { createHash } from "node:crypto";
import { execFile } from "node:child_process";
import { mkdtemp, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import sharp from "sharp";
import type { ReferenceLanguageProfile } from "../types";
import type { ReferenceFrameEvidence, ReferenceLanguageEvidence, ReferenceSourceAsset } from "./contracts";

const exec = promisify(execFile);
const clamp = (n: number, min = 0, max = 1) => Math.max(min, Math.min(max, n));

async function probe(path: string) {
  const { stdout } = await exec("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "json", path], { maxBuffer: 1024 * 1024 });
  const parsed = JSON.parse(stdout) as { format?: { duration?: string } };
  const duration = Number(parsed.format?.duration ?? 0);
  if (!Number.isFinite(duration) || duration <= 0) throw new Error("REFERENCE_LANGUAGE_ANALYSIS_FAILED: invalid reference-video duration.");
  return duration;
}

async function frameMetrics(bytes: Uint8Array) {
  const image = sharp(bytes).resize({ width: 320, withoutEnlargement: true }).removeAlpha().greyscale();
  const { data, info } = await image.raw().toBuffer({ resolveWithObject: true });
  const count = info.width * info.height;
  let nonWhite = 0, sum = 0, sumSq = 0, edge = 0;
  const threshold = 242;
  for (let i = 0; i < count; i += 1) {
    const v = data[i]!;
    if (v < threshold) nonWhite += 1;
    sum += v;
    sumSq += v * v;
    const x = i % info.width;
    const y = Math.floor(i / info.width);
    if (x > 0 && Math.abs(v - data[i - 1]!) > 26) edge += 1;
    if (y > 0 && Math.abs(v - data[i - info.width]!) > 26) edge += 1;
  }
  const mean = sum / count;
  const variance = Math.max(0, sumSq / count - mean * mean);
  return { raw: data, width: info.width, height: info.height, nonWhiteOccupancy: nonWhite / count, edgeDensity: edge / Math.max(1, count * 2), lumaStd: Math.sqrt(variance) };
}

function delta(a: Buffer, b: Buffer) {
  const length = Math.min(a.length, b.length);
  if (!length) return 0;
  let total = 0;
  for (let i = 0; i < length; i += 1) total += Math.abs(a[i]! - b[i]!);
  return total / (length * 255);
}

async function analyzeVideo(source: ReferenceSourceAsset): Promise<ReferenceLanguageEvidence> {
  const dir = await mkdtemp(join(tmpdir(), "nexstudio-reference-"));
  try {
    const ext = source.mimeType.includes("quicktime") ? ".mov" : ".mp4";
    const input = join(dir, `reference${ext}`);
    await writeFile(input, source.bytes);
    const durationSec = await probe(input);
    const samples = Math.max(4, Math.min(8, Math.ceil(durationSec * 1.5)));
    const fps = samples / durationSec;
    await exec("ffmpeg", ["-hide_banner", "-loglevel", "error", "-i", input, "-vf", `fps=${fps},scale=640:-2`, "-frames:v", String(samples), "-q:v", "3", join(dir, "frame-%02d.jpg")], { maxBuffer: 1024 * 1024 * 4 });
    const names = (await readdir(dir)).filter((name) => /^frame-\d+\.jpg$/.test(name)).sort();
    if (names.length < 2) throw new Error("REFERENCE_LANGUAGE_ANALYSIS_FAILED: reference yielded too few frames.");
    const frames: ReferenceFrameEvidence[] = [];
    const metrics: Awaited<ReturnType<typeof frameMetrics>>[] = [];
    for (let i = 0; i < names.length; i += 1) {
      const bytes = new Uint8Array(await readFile(join(dir, names[i]!)));
      metrics.push(await frameMetrics(bytes));
      frames.push({
        sourceId: source.assetId,
        mimeType: "image/jpeg",
        dataUrl: `data:image/jpeg;base64,${Buffer.from(bytes).toString("base64")}`,
        sampleTimeSec: Math.round(((i + .5) / names.length) * durationSec * 1000) / 1000,
        sha256: createHash("sha256").update(bytes).digest("hex"),
      });
    }
    const mean = (key: "nonWhiteOccupancy" | "edgeDensity" | "lumaStd") => metrics.reduce((sum, item) => sum + item[key], 0) / metrics.length;
    const meanFrameDelta = metrics.slice(1).reduce((sum, item, index) => sum + delta(metrics[index]!.raw, item.raw), 0) / Math.max(1, metrics.length - 1);
    const occupancy = mean("nonWhiteOccupancy");
    const edges = mean("edgeDensity");
    const lumaStd = mean("lumaStd");
    const whiteField = occupancy < .44;
    const authoredSceneBias = clamp((occupancy * 1.35) + (edges * 4.2) + (meanFrameDelta * .8));
    const densityTarget: ReferenceLanguageProfile["densityTarget"] = occupancy >= .24 || edges >= .055 ? "rich" : occupancy >= .13 ? "balanced" : "sparse";
    const profile: ReferenceLanguageProfile = {
      version: "reference-language.v1",
      sourceIds: [source.assetId],
      sourceKinds: [source.mimeType],
      frameCount: frames.length,
      durationSec,
      meanNonWhiteOccupancy: Number(occupancy.toFixed(4)),
      meanEdgeDensity: Number(edges.toFixed(4)),
      meanLumaStd: Number(lumaStd.toFixed(2)),
      meanFrameDelta: Number(meanFrameDelta.toFixed(4)),
      whiteField,
      authoredSceneBias: Number(authoredSceneBias.toFixed(3)),
      densityTarget,
      textDominanceMax: densityTarget === "rich" ? .18 : .25,
      minimumForegroundOccupancy: Number(Math.max(.12, occupancy * .72).toFixed(3)),
      maximumDeadWhiteRatio: Number(Math.min(.7, Math.max(.28, 1 - occupancy * .82)).toFixed(3)),
      notes: [
        "Reference constraints describe visual language only; shots, story content and compositions must remain original.",
        whiteField ? "Treat white/near-white as an actively composed field, not unused canvas." : "Reference is not primarily white-field composition.",
        densityTarget === "rich" ? "Prefer authored scene density and environmental storytelling over presentation layouts." : "Preserve the measured reference density rather than adding arbitrary clutter.",
      ],
    };
    return { profile, frames };
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
}

async function analyzeImage(source: ReferenceSourceAsset): Promise<ReferenceLanguageEvidence> {
  const normalized = await sharp(source.bytes).resize({ width: 960, withoutEnlargement: true }).jpeg({ quality: 88 }).toBuffer();
  const m = await frameMetrics(normalized);
  const occupancy = m.nonWhiteOccupancy;
  const authoredSceneBias = clamp(occupancy * 1.45 + m.edgeDensity * 4.4);
  const densityTarget: ReferenceLanguageProfile["densityTarget"] = occupancy >= .24 || m.edgeDensity >= .055 ? "rich" : occupancy >= .13 ? "balanced" : "sparse";
  const profile: ReferenceLanguageProfile = {
    version: "reference-language.v1", sourceIds: [source.assetId], sourceKinds: [source.mimeType], frameCount: 1,
    meanNonWhiteOccupancy: Number(occupancy.toFixed(4)), meanEdgeDensity: Number(m.edgeDensity.toFixed(4)), meanLumaStd: Number(m.lumaStd.toFixed(2)), meanFrameDelta: 0,
    whiteField: occupancy < .44, authoredSceneBias: Number(authoredSceneBias.toFixed(3)), densityTarget,
    textDominanceMax: densityTarget === "rich" ? .18 : .25, minimumForegroundOccupancy: Number(Math.max(.12, occupancy * .72).toFixed(3)), maximumDeadWhiteRatio: Number(Math.min(.7, Math.max(.28, 1 - occupancy * .82)).toFixed(3)),
    notes: ["Reference constraints describe visual language only; composition/content must remain original."],
  };
  return { profile, frames: [{ sourceId: source.assetId, mimeType: "image/jpeg", dataUrl: `data:image/jpeg;base64,${normalized.toString("base64")}`, sampleTimeSec: 0, sha256: createHash("sha256").update(normalized).digest("hex") }] };
}

export async function analyzeReferenceLanguage(sources: readonly ReferenceSourceAsset[]): Promise<ReferenceLanguageEvidence | undefined> {
  if (!sources.length) return undefined;
  const source = sources[0]!;
  if (source.mimeType.startsWith("video/")) return analyzeVideo(source);
  if (source.mimeType.startsWith("image/")) return analyzeImage(source);
  throw new Error(`REFERENCE_LANGUAGE_ANALYSIS_FAILED: unsupported reference MIME type ${source.mimeType}.`);
}
