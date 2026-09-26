import type { CompositionBundle } from "./types";
import { HeyGenHyperFramesClient } from "./heygen";
import { renderSelfHostedChromium } from "./self-hosted-renderer";

export type RenderProvider = "heygen_hyperframes" | "nexstudios_owned" | "self_hosted_chromium";

export interface RenderOptions {
  aspectRatio?: "16:9" | "9:16" | "1:1";
  resolution?: "1080p" | "720p";
  fps?: number;
  format?: "mp4" | "webm";
  idempotencyKey?: string;
  outputPath?: string;
  inspectionFrameDirectory?: string;
}

export interface UnifiedRenderResult {
  provider: RenderProvider;
  renderId: string;
  assetId?: string;
  status: "completed" | "rendering" | "queued" | "failed";
  videoUrl?: string;
  localOutputPath?: string;
  error?: string;
  actualDurationSeconds?: number;
  actualAspectRatio?: string;
  actualResolution?: string;
  frameRateFps?: number;
  fileSizeBytes?: number;
  cost?: string;
  metrics?: {
    frameCount: number;
    fps: number;
    width: number;
    height: number;
    frameRenderMs: number;
    encodeMs: number;
    totalWallMs: number;
    peakMemoryBytes?: number;
    temporaryDiskBytes: number;
    outputBytes: number;
    audioTrackCount: number;
  };
}

export async function renderCompositionBundle(
  provider: RenderProvider,
  bundle: CompositionBundle,
  options: RenderOptions = {}
): Promise<UnifiedRenderResult> {
  if (provider === "heygen_hyperframes") {
    const client = new HeyGenHyperFramesClient();
    const key = options.idempotencyKey ?? `heygen-${Date.now()}`;
    const uploadRes = await client.upload(bundle, key);
    await client.waitForAsset(uploadRes.assetId, { expectedBytes: uploadRes.archive.byteLength, uploadCompletedAt: uploadRes.uploadedAt });
    const submitRes = await client.submit({
      assetId: uploadRes.assetId,
      composition: bundle.entry,
      aspectRatio: options.aspectRatio ?? "16:9",
      resolution: "1080p",
      fps: options.fps ?? 30,
      format: options.format ?? "mp4",
      idempotencyKey: `submit-${key}`
    });

    const statusRes = await client.get(submitRes.renderId);

    return {
      provider: "heygen_hyperframes",
      renderId: submitRes.renderId,
      assetId: uploadRes.assetId,
      status: statusRes.status as UnifiedRenderResult["status"],
      videoUrl: statusRes.videoUrl,
      error: statusRes.error,
      cost: "$0.00 (Developer Cloud Quota / Included)"
    };
  }

  // Parallel NexStudios-owned backend. The managed provider remains available
  // and historical jobs retain their original provider identifiers.
  return renderSelfHostedChromium(bundle, options);
}
