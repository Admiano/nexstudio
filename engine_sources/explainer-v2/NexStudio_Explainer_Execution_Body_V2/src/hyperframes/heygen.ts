import { strToU8, zipSync } from "fflate";
import { scanExportPathNames, scanSecretText } from "@/lib/secret-scan";
import type { CloudRenderRequest, CloudRenderResult, CompositionBundle } from "./types";
import {
  appendDiagnosticJson,
  buildRenderPayload,
  documentedHyperFramesSchema,
  sha256,
  validateRenderPayload,
  validateZipArchive,
  writeDiagnosticBinary,
  writeDiagnosticJson
} from "./diagnostics";

function headers(idempotencyKey?: string) {
  const apiKey = process.env.HEYGEN_API_KEY?.trim();
  if (!apiKey) throw new Error("HEYGEN_API_KEY is not configured");
  return {
    "x-api-key": apiKey,
    ...(idempotencyKey ? { "idempotency-key": idempotencyKey } : {})
  };
}

function apiUrl() {
  return process.env.HEYGEN_API_URL?.trim() || "https://api.heygen.com";
}

function dataRecord(payload: unknown) {
  const root = payload as Record<string, unknown>;
  return ((root.data as Record<string, unknown> | undefined) ?? root) as Record<string, unknown>;
}

async function parseResponse(response: Response) {
  const payload = (await response.json().catch(() => ({}))) as Record<string, unknown>;
  if (!response.ok) {
    let message = payload.message as string | undefined;
    if (!message && payload.error) {
      if (typeof payload.error === "object" && payload.error !== null && "message" in payload.error) {
        const nested = payload.error as { message?: unknown };
        message = typeof nested.message === "string" ? nested.message : undefined;
      } else if (typeof payload.error === "string") {
        message = payload.error;
      }
    }
    if (!message) {
      message = `HeyGen request failed with ${response.status}`;
    }
    throw new Error(message);
  }
  return payload;
}

export function zipComposition(bundle: CompositionBundle) {
  const secretFindings = [...scanExportPathNames([...Object.keys(bundle.files), "manifest.json"]), ...Object.entries(bundle.files).flatMap(([file, value]) => typeof value === "string" ? scanSecretText(file, value) : [])];
  if (secretFindings.length) throw new Error(`SOURCE_EXPORT_SECRET_SCAN_FAILED:${secretFindings.map((finding) => `${finding.category}:${finding.name ?? "unknown"}:${finding.file}`).join(",")}`);
  const files = Object.fromEntries(
    Object.entries(bundle.files).map(([path, value]) => [
      path,
      typeof value === "string" ? strToU8(value) : value
    ])
  );
  files["manifest.json"] = strToU8(JSON.stringify(bundle.manifest, null, 2));
  return zipSync(files, { level: 6 });
}

export class HeyGenHyperFramesClient {
  private uploadEvidence = new Map<string, {
    archive: Uint8Array;
    archiveChecksum: string;
    archiveValidation: ReturnType<typeof validateZipArchive>;
    uploadRequest: Record<string, unknown>;
    uploadResponse: Record<string, unknown>;
    uploadedAt: string;
    assetMetadata?: Record<string, unknown>;
    assetReadiness?: unknown;
  }>();

  async upload(bundle: CompositionBundle, idempotencyKey: string) {
    const archive = zipComposition(bundle);
    const archiveChecksum = sha256(archive);
    const archiveValidation = validateZipArchive(archive, bundle.entry);
    if (!archiveValidation.ok) {
      throw new Error(`HyperFrames ZIP validation failed before upload: ${archiveValidation.issues.join(" ")}`);
    }
    const form = new FormData();
    form.set(
      "file",
      new Blob([archive as BlobPart], { type: "application/zip" }),
      `${bundle.manifest.productionId}.zip`
    );
    const response = await fetch(`${apiUrl()}/v3/assets`, {
      method: "POST",
      headers: headers(idempotencyKey),
      body: form
    });
    const payload = await parseResponse(response);
    const data = dataRecord(payload);
    const assetId = (data.asset_id ?? data.id) as string | undefined;
    if (!assetId) throw new Error("HeyGen asset upload did not return an asset_id");
    await writeDiagnosticBinary(assetId, "project.zip", archive);
    await writeDiagnosticJson(assetId, "zip-checksum.json", { sha256: archiveChecksum, byteSize: archive.byteLength, entry: bundle.entry, compositionHash: bundle.manifest.compositionHash });
    await writeDiagnosticJson(assetId, "zip-inventory.json", archiveValidation);
    const uploadRequest = { method: "POST", endpoint: "/v3/assets", headers: { "x-api-key": "[redacted]", "idempotency-key": idempotencyKey }, multipart: { fileName: `${bundle.manifest.productionId}.zip`, contentType: "application/zip", byteSize: archive.byteLength, sha256: archiveChecksum } };
    await writeDiagnosticJson(assetId, "asset-upload-request.json", uploadRequest);
    await writeDiagnosticJson(assetId, "asset-upload-response.json", payload);
    await writeDiagnosticJson(assetId, "asset-id.json", { assetId });
    this.uploadEvidence.set(assetId, { archive, archiveChecksum, archiveValidation, uploadRequest, uploadResponse: payload, uploadedAt: new Date().toISOString() });
    return { assetId, raw: payload, archive, archiveChecksum, archiveValidation, uploadedAt: new Date().toISOString() };
  }

  async getAsset(assetId: string) {
    const response = await fetch(`${apiUrl()}/v3/assets/${encodeURIComponent(assetId)}`, {
      headers: headers()
    });
    return parseResponse(response);
  }

  private assetUsability(assetId: string, metadata: Record<string, unknown>, expectedBytes?: number) {
    const data = dataRecord(metadata);
    const status = String(data.status ?? data.state ?? data.upload_status ?? "").toLowerCase();
    const type = String(data.type ?? data.asset_type ?? data.mime_type ?? data.content_type ?? "").toLowerCase();
    const sizeRaw = data.size ?? data.byte_size ?? data.bytes ?? data.file_size;
    const size = typeof sizeRaw === "number" ? sizeRaw : typeof sizeRaw === "string" ? Number(sizeRaw) : undefined;
    const issues: string[] = [];
    const warnings: string[] = [];
    if (!((data.asset_id ?? data.id) === assetId)) issues.push("Asset metadata does not echo the uploaded asset id.");
    if (status && ["failed", "error", "deleted", "cancelled"].includes(status)) issues.push(`Asset status is terminally unusable: ${status}.`);
    if (status && ["processing", "pending", "uploading", "queued", "created"].includes(status)) issues.push(`Asset is not ready yet: ${status}.`);
    const workspaceId = data.workspace_id ?? data.workspaceId;
    const expectedWorkspaceId = process.env.HEYGEN_WORKSPACE_ID?.trim();
    if (expectedWorkspaceId && workspaceId && workspaceId !== expectedWorkspaceId) issues.push("Asset belongs to a different HeyGen workspace than expected.");
    if (expectedWorkspaceId && !workspaceId) warnings.push("Asset metadata did not include a workspace identifier to verify.");
    if (type && !(type.includes("zip") || type.includes("project") || type.includes("application/zip"))) warnings.push(`Asset type did not explicitly identify a project ZIP: ${type}.`);
    if (expectedBytes !== undefined && size !== undefined && size !== expectedBytes) issues.push(`Uploaded byte size ${size} does not match local ZIP size ${expectedBytes}.`);
    if (expectedBytes !== undefined && size === undefined) warnings.push("Asset metadata did not include an uploaded byte size.");
    return { usable: issues.length === 0, issues, warnings, status: status || undefined, type: type || undefined, byteSize: size };
  }

  async waitForAsset(assetId: string, input: { expectedBytes?: number; uploadCompletedAt?: string; maxAttempts?: number; delayMs?: number } = {}) {
    const history: unknown[] = [];
    const startedAt = Date.now();
    const maxAttempts = input.maxAttempts ?? 8;
    const delayMs = input.delayMs ?? 1500;
    let lastMetadata: Record<string, unknown> | undefined;
    let lastUsability: ReturnType<HeyGenHyperFramesClient["assetUsability"]> | undefined;
    for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
      const checkedAt = new Date().toISOString();
      lastMetadata = await this.getAsset(assetId);
      lastUsability = this.assetUsability(assetId, lastMetadata, input.expectedBytes);
      history.push({ attempt, checkedAt, elapsedMs: Date.now() - startedAt, usability: lastUsability, response: lastMetadata });
      await writeDiagnosticJson(assetId, "asset-metadata-response.json", lastMetadata);
      await writeDiagnosticJson(assetId, "asset-readiness-history.json", history);
      if (lastUsability.usable) {
        const evidence = this.uploadEvidence.get(assetId);
        if (evidence) this.uploadEvidence.set(assetId, { ...evidence, assetMetadata: lastMetadata, assetReadiness: { usability: lastUsability, history, readyAt: checkedAt, delayMs: input.uploadCompletedAt ? Date.parse(checkedAt) - Date.parse(input.uploadCompletedAt) : Date.now() - startedAt } });
        return { assetId, metadata: lastMetadata, usability: lastUsability, history, readyAt: checkedAt, delayMs: input.uploadCompletedAt ? Date.parse(checkedAt) - Date.parse(input.uploadCompletedAt) : Date.now() - startedAt };
      }
      if (attempt < maxAttempts) await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
    throw new Error(`HeyGen asset ${assetId} is not usable for HyperFrames rendering: ${lastUsability?.issues.join(" ") || "metadata unavailable"}`);
  }

  async submit(input: CloudRenderRequest): Promise<CloudRenderResult> {
    const body = buildRenderPayload(input);
    const diff = validateRenderPayload(body, { entryPath: input.composition ?? "index.html", aspectRatio: input.aspectRatio });
    await writeDiagnosticJson(input.assetId, "documented-schema.json", documentedHyperFramesSchema);
    await writeDiagnosticJson(input.assetId, "actual-app-payload.json", body);
    await writeDiagnosticJson(input.assetId, "payload-diff.json", diff);
    if (!diff.ok) throw new Error(`HeyGen HyperFrames payload validation failed: ${diff.issues.join(" ")}`);
    const response = await fetch(`${apiUrl()}/v3/hyperframes/renders`, {
      method: "POST",
      headers: {
        ...headers(input.idempotencyKey),
        "content-type": "application/json"
      },
      body: JSON.stringify(body)
    });
    const payload = await parseResponse(response);
    const normalized = this.normalize(payload, input.assetId);
    await writeDiagnosticJson(input.assetId, "render-request-body.json", body);
    await writeDiagnosticJson(input.assetId, "render-response-body.json", payload);
    await writeDiagnosticJson(input.assetId, "render-id.json", { renderId: normalized.renderId, assetId: input.assetId });
    if (normalized.renderId !== input.assetId) {
      const evidence = this.uploadEvidence.get(input.assetId);
      if (evidence) {
        await writeDiagnosticBinary(normalized.renderId, "project.zip", evidence.archive);
        await writeDiagnosticJson(normalized.renderId, "zip-checksum.json", { sha256: evidence.archiveChecksum, byteSize: evidence.archive.byteLength, entry: input.composition ?? "index.html" });
        await writeDiagnosticJson(normalized.renderId, "zip-inventory.json", evidence.archiveValidation);
        await writeDiagnosticJson(normalized.renderId, "asset-upload-request.json", evidence.uploadRequest);
        await writeDiagnosticJson(normalized.renderId, "asset-upload-response.json", evidence.uploadResponse);
        await writeDiagnosticJson(normalized.renderId, "asset-id.json", { assetId: input.assetId });
        if (evidence.assetMetadata) await writeDiagnosticJson(normalized.renderId, "asset-metadata-response.json", evidence.assetMetadata);
        if (evidence.assetReadiness) await writeDiagnosticJson(normalized.renderId, "asset-readiness-history.json", evidence.assetReadiness);
        await writeDiagnosticJson(normalized.renderId, "render-submission-delay.json", { uploadCompletedAt: evidence.uploadedAt, renderSubmittedAt: new Date().toISOString(), delayMs: Date.now() - Date.parse(evidence.uploadedAt) });
      }
      await writeDiagnosticJson(normalized.renderId, "documented-schema.json", documentedHyperFramesSchema);
      await writeDiagnosticJson(normalized.renderId, "actual-app-payload.json", body);
      await writeDiagnosticJson(normalized.renderId, "payload-diff.json", diff);
      await writeDiagnosticJson(normalized.renderId, "render-request-body.json", body);
      await writeDiagnosticJson(normalized.renderId, "render-response-body.json", payload);
      await writeDiagnosticJson(normalized.renderId, "render-id.json", { renderId: normalized.renderId, assetId: input.assetId });
    }
    return normalized;
  }

  async get(renderId: string): Promise<CloudRenderResult> {
    const response = await fetch(
      `${apiUrl()}/v3/hyperframes/renders/${encodeURIComponent(renderId)}`,
      { headers: headers() }
    );
    const payload = await parseResponse(response);
    const normalized = this.normalize(payload);
    const poll = { checkedAt: new Date().toISOString(), renderId, status: normalized.status, error: normalized.error, response: payload };
    await appendDiagnosticJson(renderId, "polling-history.json", poll);
    if (normalized.status === "failed") await writeDiagnosticJson(renderId, "final-failure-response.json", payload);
    return normalized;
  }

  private normalize(payload: Record<string, unknown>, assetId?: string): CloudRenderResult {
    const data = dataRecord(payload);
    const renderId = (data.render_id ?? data.id) as string | undefined;
    if (!renderId) throw new Error("HeyGen response did not include a render_id");
    const rawStatus = String(data.status ?? (data.video_url ? "completed" : data.failure_message ? "failed" : "queued")).toLowerCase();
    const status = rawStatus === "complete" ? "completed" : rawStatus;
    return {
      renderId,
      status: new Set(["queued", "rendering", "completed", "failed"]).has(status)
        ? (status as CloudRenderResult["status"])
        : "queued",
      assetId: (data.asset_id as string | undefined) ?? assetId,
      videoUrl: data.video_url as string | undefined,
      thumbnailUrl: data.thumbnail_url as string | undefined,
      error: typeof data.error === "string" ? data.error : typeof data.failure_message === "string" ? data.failure_message : typeof data.message === "string" ? data.message : undefined,
      raw: payload
    };
  }
}
