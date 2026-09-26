import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { unzipSync } from "fflate";
import type { AspectRatio, CloudRenderRequest, CompositionBundle } from "./types";

export const hyperframesDiagnosticsRoot = process.env.HYPERFRAMES_DIAGNOSTICS_ROOT?.trim() || ".hyperframes-diagnostics/renders";

type JsonRecord = Record<string, unknown>;

const allowedPayloadFields = new Set([
  "project",
  "composition",
  "format",
  "resolution",
  "aspect_ratio",
  "fps",
  "quality",
  "variables",
  "callback_url",
  "callback_id",
  "title"
]);

export const documentedHyperFramesSchema = {
  source: {
    status: "local-contract",
    note: "Network access to the hosted HeyGen documentation was not available during this repair. This schema is constrained to the user-specified production contract and the repository's local HeyGen managed-cloud implementation notes.",
    localReferences: [
      "docs/NexMarkets_Full_Implementation_And_Robinhood_Deployment_Guide.html#HeyGen managed-cloud render worker",
      "node_modules/@hyperframes/core/docs/core.md",
      "node_modules/@hyperframes/core/docs/quickstart-template.html"
    ]
  },
  endpoint: "/v3/hyperframes/renders",
  method: "POST",
  headers: {
    "x-api-key": "required server-side secret header",
    "content-type": "application/json",
    "idempotency-key": "optional idempotency header"
  },
  body: {
    required: ["project", "composition", "format", "resolution", "aspect_ratio", "fps", "quality"],
    optional: ["variables", "callback_url", "callback_id", "title"],
    properties: {
      project: { type: "object", required: ["type", "asset_id"], properties: { type: ["asset_id"], asset_id: "string" } },
      composition: "ZIP-relative entry HTML path, e.g. index.html",
      format: ["mp4", "webm", "mov"],
      resolution: ["1080p", "4k"],
      aspect_ratio: ["16:9", "9:16", "1:1"],
      fps: "positive integer, normally 30",
      quality: ["draft", "standard", "high"],
      variables: "object, optional",
      callback_url: "public HTTPS URL, optional when polling is used",
      callback_id: "stable caller correlation id, optional",
      title: "string, optional"
    }
  }
} as const;

export type ZipInventoryEntry = {
  path: string;
  caseSensitivePath: string;
  uncompressedSize: number;
  compressedSize: number;
  crc32: string;
  sha256: string;
  mimeExpectation: string;
};

export type ZipValidationReport = {
  ok: boolean;
  entryPath: string;
  issues: string[];
  warnings: string[];
  inventory: ZipInventoryEntry[];
  composition: {
    rootCompositionCount: number;
    rootCompositionId?: string;
    width?: number;
    height?: number;
    timedClipCount: number;
    usesGsap: boolean;
    hasPausedRegisteredTimeline: boolean;
  };
};

export type PayloadDiff = {
  ok: boolean;
  issues: string[];
  warnings: string[];
  undocumentedFields: string[];
  missingRequiredFields: string[];
  invalidEnumFields: Record<string, unknown>;
};

export function sha256(value: Uint8Array | string) {
  return createHash("sha256").update(value).digest("hex");
}

export function bytesOf(value: string | Uint8Array) {
  return typeof value === "string" ? Buffer.from(value) : Buffer.from(value);
}

export function fileMimeExpectation(filePath: string) {
  const extension = filePath.toLowerCase().split(".").pop() || "";
  const map: Record<string, string> = {
    html: "text/html",
    htm: "text/html",
    css: "text/css",
    js: "application/javascript",
    json: "application/json",
    md: "text/markdown",
    png: "image/png",
    jpg: "image/jpeg",
    jpeg: "image/jpeg",
    webp: "image/webp",
    gif: "image/gif",
    svg: "image/svg+xml",
    mp3: "audio/mpeg",
    wav: "audio/wav",
    m4a: "audio/mp4",
    mp4: "video/mp4",
    webm: "video/webm",
    woff: "font/woff",
    woff2: "font/woff2",
    ttf: "font/ttf"
  };
  return map[extension] ?? "application/octet-stream";
}

function readUInt32(buffer: Uint8Array, offset: number) {
  return (buffer[offset] | (buffer[offset + 1] << 8) | (buffer[offset + 2] << 16) | (buffer[offset + 3] << 24)) >>> 0;
}

function readUInt16(buffer: Uint8Array, offset: number) {
  return buffer[offset] | (buffer[offset + 1] << 8);
}

function findEndOfCentralDirectory(buffer: Uint8Array) {
  for (let offset = buffer.length - 22; offset >= 0; offset -= 1) {
    if (readUInt32(buffer, offset) === 0x06054b50) return offset;
  }
  throw new Error("ZIP central directory was not found.");
}

export function zipInventory(archive: Uint8Array): ZipInventoryEntry[] {
  const unzipped = unzipSync(archive);
  const eocd = findEndOfCentralDirectory(archive);
  const centralDirectoryOffset = readUInt32(archive, eocd + 16);
  const entries = readUInt16(archive, eocd + 10);
  const decoder = new TextDecoder();
  const result: ZipInventoryEntry[] = [];
  let offset = centralDirectoryOffset;
  for (let index = 0; index < entries; index += 1) {
    if (readUInt32(archive, offset) !== 0x02014b50) throw new Error("ZIP central directory entry is malformed.");
    const crc = readUInt32(archive, offset + 16).toString(16).padStart(8, "0");
    const compressedSize = readUInt32(archive, offset + 20);
    const uncompressedSize = readUInt32(archive, offset + 24);
    const fileNameLength = readUInt16(archive, offset + 28);
    const extraLength = readUInt16(archive, offset + 30);
    const commentLength = readUInt16(archive, offset + 32);
    const filePath = decoder.decode(archive.slice(offset + 46, offset + 46 + fileNameLength));
    const content = unzipped[filePath];
    result.push({
      path: filePath,
      caseSensitivePath: filePath,
      uncompressedSize,
      compressedSize,
      crc32: crc,
      sha256: content ? sha256(content) : "missing-from-unzip",
      mimeExpectation: fileMimeExpectation(filePath)
    });
    offset += 46 + fileNameLength + extraLength + commentLength;
  }
  return result.sort((a, b) => a.path.localeCompare(b.path));
}

function normalizeZipRelative(reference: string, baseFile: string) {
  const clean = reference.split("#")[0].split("?")[0];
  if (!clean || clean.startsWith("data:") || clean.startsWith("blob:") || clean.startsWith("about:")) return null;
  if (/^[a-z][a-z0-9+.-]*:/i.test(clean)) return clean;
  if (/^[a-zA-Z]:[\\/]/.test(clean) || clean.includes("\\")) return clean;
  const baseDir = baseFile.includes("/") ? baseFile.slice(0, baseFile.lastIndexOf("/")) : "";
  const combined = clean.startsWith("/") ? clean.slice(1) : path.posix.join(baseDir, clean);
  const normalized = path.posix.normalize(combined);
  return normalized === "." ? null : normalized;
}

function extractReferences(content: string) {
  const refs: string[] = [];
  const attribute = /\b(?:src|href|poster|data-composition-src)\s*=\s*(["'])(.*?)\1/gi;
  let match: RegExpExecArray | null;
  while ((match = attribute.exec(content))) refs.push(match[2]);
  const cssUrl = /url\(\s*(["']?)(.*?)\1\s*\)/gi;
  while ((match = cssUrl.exec(content))) refs.push(match[2]);
  return refs;
}

function attr(block: string, name: string) {
  const pattern = new RegExp(`\\b${name}\\s*=\\s*(["'])(.*?)\\1`, "i");
  return block.match(pattern)?.[2];
}

function numericAttribute(block: string, name: string) {
  const value = attr(block, name);
  if (value === undefined) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

export function validateZipArchive(archive: Uint8Array, entryPath: string): ZipValidationReport {
  const issues: string[] = [];
  const warnings: string[] = [];
  let inventory: ZipInventoryEntry[] = [];
  let unzipped: Record<string, Uint8Array> = {};
  try {
    inventory = zipInventory(archive);
    unzipped = unzipSync(archive);
  } catch (error) {
    return {
      ok: false,
      entryPath,
      issues: [error instanceof Error ? error.message : "ZIP could not be inspected."],
      warnings,
      inventory,
      composition: { rootCompositionCount: 0, timedClipCount: 0, usesGsap: false, hasPausedRegisteredTimeline: false }
    };
  }

  const paths = new Set(inventory.map((item) => item.path));
  if (!paths.has(entryPath)) issues.push(`Declared composition entry does not exist exactly in ZIP: ${entryPath}`);
  const topLevelHtml = inventory.filter((item) => item.path.endsWith(".html") && !item.path.includes("/")).length;
  const topLevelDirectories = new Set(inventory.map((item) => item.path.split("/")[0]).filter(Boolean));
  if (!paths.has("index.html") && topLevelHtml === 0 && topLevelDirectories.size === 1) {
    issues.push("ZIP appears to contain a wrapping directory instead of index.html at the archive root.");
  }

  const decoder = new TextDecoder();
  for (const item of inventory) {
    if (!/\.(html|css|js)$/i.test(item.path)) continue;
    const text = decoder.decode(unzipped[item.path]);
    const vendorRuntime = /(^|\/)gsap(\.min)?\.js$/i.test(item.path);
    for (const reference of extractReferences(text)) {
      const resolved = normalizeZipRelative(reference, item.path);
      if (!resolved) continue;
      if (/^https?:\/\//i.test(resolved)) issues.push(`${item.path} references external network URL: ${reference}`);
      if (/localhost|127\.0\.0\.1|0\.0\.0\.0|\.local\b/i.test(resolved)) issues.push(`${item.path} references localhost/private host: ${reference}`);
      if (/^file:\/\//i.test(resolved)) issues.push(`${item.path} references file URL: ${reference}`);
      if (/^[a-zA-Z]:[\\/]/.test(resolved)) issues.push(`${item.path} references Windows local path: ${reference}`);
      if (resolved.startsWith("..")) issues.push(`${item.path} reference escapes project root: ${reference}`);
      if (resolved.startsWith("_next/") || resolved.startsWith("api/") || resolved.startsWith("app/") || resolved.startsWith("src/")) issues.push(`${item.path} depends on application route/source path: ${reference}`);
      if (resolved.includes("node_modules")) issues.push(`${item.path} references node_modules at runtime: ${reference}`);
      if (!/^[a-z][a-z0-9+.-]*:/i.test(resolved) && !paths.has(resolved)) issues.push(`${item.path} references missing ZIP file: ${reference} -> ${resolved}`);
    }
    if (!vendorRuntime && /setTimeout\s*\(/.test(text)) issues.push(`${item.path} uses uncontrolled setTimeout animation.`);
    if (!vendorRuntime && /setInterval\s*\(/.test(text)) issues.push(`${item.path} uses uncontrolled setInterval animation.`);
    if (!vendorRuntime && /\b(Date\.now|performance\.now|new\s+Date\s*\()/.test(text)) issues.push(`${item.path} depends on wall-clock time.`);
    if (!vendorRuntime && /@keyframes|\banimation\s*:/i.test(text) && !/animation\s*:\s*none/i.test(text)) issues.push(`${item.path} uses CSS animation outside a registered timeline.`);
  }

  let composition = { rootCompositionCount: 0, timedClipCount: 0, usesGsap: false, hasPausedRegisteredTimeline: false } as ZipValidationReport["composition"];
  const entryBytes = unzipped[entryPath];
  if (entryBytes) {
    const html = decoder.decode(entryBytes);
    const compositionBlocks = [...html.matchAll(/<([a-z0-9-]+)\b[^>]*\bdata-composition-id\s*=\s*(["']).*?\2[^>]*>/gi)].map((match) => match[0]);
    const rootBlocks = compositionBlocks.filter((block) => attr(block, "data-width") !== undefined || attr(block, "data-height") !== undefined);
    const root = rootBlocks[0] ?? compositionBlocks[0];
    const rootId = root ? attr(root, "data-composition-id") : undefined;
    const timedBlocks = [...html.matchAll(/<([a-z0-9-]+)\b[^>]*\bdata-start\s*=\s*(["']).*?\2[^>]*>/gi)].map((match) => match[0]).filter((block) => block !== root);
    const usesGsap = /\bgsap\b|gsap\.timeline/.test(html) || inventory.some((item) => /gsap/i.test(item.path));
    const allScripts = inventory.filter((item) => item.path.endsWith(".js")).map((item) => decoder.decode(unzipped[item.path])).join("\n") + "\n" + html;
    const hasPausedRegisteredTimeline = /gsap\.timeline\s*\(\s*\{[^}]*paused\s*:\s*true/s.test(allScripts) && /window\.__timelines\s*\[[^\]]+\]\s*=/.test(allScripts);
    composition = {
      rootCompositionCount: rootBlocks.length || compositionBlocks.length,
      rootCompositionId: rootId,
      width: root ? numericAttribute(root, "data-width") : undefined,
      height: root ? numericAttribute(root, "data-height") : undefined,
      timedClipCount: timedBlocks.length,
      usesGsap,
      hasPausedRegisteredTimeline
    };
    if (!root) issues.push("Entry HTML does not declare data-composition-id.");
    if (rootBlocks.length !== 1) issues.push(`Entry HTML must declare exactly one root composition with dimensions; found ${rootBlocks.length}.`);
    if (!attr(root ?? "", "data-start")) issues.push("Root composition is missing data-start.");
    if (!composition.width || !composition.height) issues.push("Root composition is missing numeric data-width/data-height.");
    if (!timedBlocks.length) issues.push("Entry HTML must contain at least one timed clip.");
    for (const block of timedBlocks) {
      if (!attr(block, "data-duration")) issues.push(`Timed clip is missing data-duration: ${block.slice(0, 160)}`);
      if (!attr(block, "data-track-index")) issues.push(`Timed clip is missing data-track-index: ${block.slice(0, 160)}`);
      const tag = block.match(/^<([a-z0-9-]+)/i)?.[1]?.toLowerCase();
      if (tag !== "audio" && !/\bclass\s*=\s*(["'])[^"']*\bclip\b/i.test(block)) issues.push(`Timed visual clip is missing class="clip": ${block.slice(0, 160)}`);
    }
    if (usesGsap && !hasPausedRegisteredTimeline) issues.push("GSAP is used without a paused registered window.__timelines timeline.");
  }

  return { ok: issues.length === 0, entryPath, issues, warnings, inventory, composition };
}

export function buildRenderPayload(input: CloudRenderRequest) {
  const payload: JsonRecord = {
    project: {
      type: "asset_id",
      asset_id: input.assetId
    },
    composition: input.composition ?? "index.html",
    fps: input.fps ?? 30,
    quality: input.quality ?? "standard",
    format: input.format ?? "mp4",
    resolution: input.resolution ?? "1080p"
  };
  if (input.aspectRatio) payload.aspect_ratio = input.aspectRatio;
  if (input.variables) payload.variables = input.variables;
  if (input.callbackUrl) payload.callback_url = input.callbackUrl;
  if (input.callbackId) payload.callback_id = input.callbackId;
  if (input.title) payload.title = input.title;
  return payload;
}

function isPublicHttpsUrl(value: string) {
  try {
    const url = new URL(value);
    if (url.protocol !== "https:") return false;
    return !/^(localhost|127\.0\.0\.1|0\.0\.0\.0)$/i.test(url.hostname) && !/\.local$/i.test(url.hostname);
  } catch {
    return false;
  }
}

export function validateRenderPayload(payload: JsonRecord, options: { entryPath: string; aspectRatio?: AspectRatio }): PayloadDiff {
  const issues: string[] = [];
  const warnings: string[] = [];
  const undocumentedFields = Object.keys(payload).filter((key) => !allowedPayloadFields.has(key));
  const required = documentedHyperFramesSchema.body.required;
  const missingRequiredFields = required.filter((key) => payload[key] === undefined || payload[key] === null || payload[key] === "");
  const invalidEnumFields: Record<string, unknown> = {};
  const project = payload.project as JsonRecord | undefined;
  if (!project || typeof project !== "object") issues.push("project object is required.");
  if (project?.type !== "asset_id") invalidEnumFields["project.type"] = project?.type;
  if (!project?.asset_id || typeof project.asset_id !== "string") issues.push("project.asset_id is required.");
  if (payload.composition !== options.entryPath) issues.push(`composition path ${String(payload.composition)} does not match uploaded entry ${options.entryPath}.`);
  if (!["mp4", "webm", "mov"].includes(String(payload.format))) invalidEnumFields.format = payload.format;
  if (!["1080p", "4k"].includes(String(payload.resolution))) invalidEnumFields.resolution = payload.resolution;
  if (!["16:9", "9:16", "1:1"].includes(String(payload.aspect_ratio))) invalidEnumFields.aspect_ratio = payload.aspect_ratio;
  if (!["draft", "standard", "high"].includes(String(payload.quality))) invalidEnumFields.quality = payload.quality;
  if (!Number.isInteger(payload.fps) || Number(payload.fps) <= 0) issues.push("fps must be a positive integer.");
  if (payload.callback_url !== undefined && (typeof payload.callback_url !== "string" || !isPublicHttpsUrl(payload.callback_url))) issues.push("callback_url must be a publicly reachable HTTPS URL when supplied.");
  if (options.aspectRatio && payload.aspect_ratio !== options.aspectRatio) issues.push(`aspect_ratio ${String(payload.aspect_ratio)} conflicts with expected ${options.aspectRatio}.`);
  if (payload.variables !== undefined && (typeof payload.variables !== "object" || Array.isArray(payload.variables) || payload.variables === null)) issues.push("variables must be an object when supplied.");
  if (undocumentedFields.length) issues.push(`Payload contains undocumented fields: ${undocumentedFields.join(", ")}.`);
  if (missingRequiredFields.length) issues.push(`Payload is missing required fields: ${missingRequiredFields.join(", ")}.`);
  for (const [key, value] of Object.entries(invalidEnumFields)) issues.push(`Payload field ${key} has invalid value ${JSON.stringify(value)}.`);
  if (!payload.callback_url) warnings.push("callback_url omitted; completion must rely on polling or another configured background reconciliation path.");
  return { ok: issues.length === 0, issues, warnings, undocumentedFields, missingRequiredFields, invalidEnumFields };
}

export function redact(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(redact);
  if (!value || typeof value !== "object") return value;
  const result: JsonRecord = {};
  for (const [key, raw] of Object.entries(value as JsonRecord)) {
    const lower = key.toLowerCase();
    if (lower.includes("api_key") || lower === "x-api-key" || lower === "authorization" || lower.includes("credential") || lower.includes("secret")) {
      result[key] = "[redacted]";
    } else if ((lower.endsWith("url") || lower.includes("_url")) && lower !== "callback_url" && typeof raw === "string") {
      result[key] = raw ? "[redacted-url]" : raw;
    } else if (lower.includes("signature") || lower.includes("token")) {
      result[key] = "[redacted]";
    } else {
      result[key] = redact(raw);
    }
  }
  return result;
}

export async function writeDiagnosticJson(renderId: string, name: string, payload: unknown) {
  const dir = path.resolve(process.cwd(), hyperframesDiagnosticsRoot, renderId);
  await mkdir(dir, { recursive: true });
  await writeFile(path.join(dir, name), JSON.stringify(redact(payload), null, 2) + "\n");
}

export async function appendDiagnosticJson(renderId: string, name: string, payload: unknown) {
  const dir = path.resolve(process.cwd(), hyperframesDiagnosticsRoot, renderId);
  await mkdir(dir, { recursive: true });
  const file = path.join(dir, name);
  const existing = await readFile(file, "utf8").then((value) => JSON.parse(value) as unknown[]).catch(() => [] as unknown[]);
  existing.push(redact(payload));
  await writeFile(file, JSON.stringify(existing, null, 2) + "\n");
}

export async function writeDiagnosticBinary(renderId: string, name: string, payload: Uint8Array) {
  const dir = path.resolve(process.cwd(), hyperframesDiagnosticsRoot, renderId);
  await mkdir(dir, { recursive: true });
  await writeFile(path.join(dir, name), payload);
}

export async function writeCallbackDiagnostic(renderId: string, payload: { receivedAt: string; headers: JsonRecord; body: unknown }) {
  const stamp = payload.receivedAt.replace(/[:.]/g, "-");
  await writeDiagnosticJson(renderId, `callback-${stamp}.json`, payload);
}

export function minimalHyperFramesApiTestBundle(): CompositionBundle {
  const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=1920,height=1080">
  <title>NexStudio HyperFrames API Test</title>
  <style>
    *{box-sizing:border-box}html,body{margin:0;width:1920px;height:1080px;overflow:hidden;background:#101216;color:#f7f7f2;font-family:Arial,Helvetica,sans-serif}
    [data-composition-id]{position:relative;width:1920px;height:1080px;overflow:hidden;display:grid;place-items:center}
    .clip{position:absolute;inset:0;display:grid;place-items:center;visibility:hidden}
    .clip span{font-size:72px;font-weight:700;line-height:1.1}
  </style>
</head>
<body>
  <main data-composition-id="nexstudio-api-minimal" data-start="0" data-duration="5" data-width="1920" data-height="1080">
    <div id="text-001" class="clip" data-start="0" data-duration="5" data-track-index="1"><span>NexStudio API render test</span></div>
  </main>
</body>
</html>`;
  const hash = sha256(html);
  return {
    entry: "index.html",
    hyperframesVersion: process.env.HYPERFRAMES_VERSION ?? "0.7.56",
    width: 1920,
    height: 1080,
    durationSeconds: 5,
    files: { "index.html": html },
    manifest: {
      productionId: "hyperframes-api-minimal",
      templateVersion: "api-minimal-1.0.0",
      compositionHash: hash,
      sourceHash: hash,
      createdAt: new Date().toISOString(),
      assets: [{ path: "index.html", sha256: hash }],
      beatCount: 1,
      beatTimings: [{ beatId: "text-001", startSec: 0, endSec: 5 }],
      audioTracks: []
    }
  };
}
