import { requireSession } from "@/lib/route-auth";
import { json } from "@/lib/http";
import { getPrisma } from "@/lib/db";
import { readEngineJob, type EngineKind } from "@/lib/engine-jobs";
export const runtime = "nodejs";
export async function GET(request: Request) {
  const auth = await requireSession(request); if (auth.response) return auth.response;
  const prisma = getPrisma()!;
  const drafts = await prisma.draft.findMany({ where: { ownerUserId: auth.session!.userId, family: { not: null }, prompt: { not: null } }, orderBy: { updatedAt: "desc" }, take: 100 });
  const ids = drafts.map((draft) => draft.id);
  const productions = ids.length ? await prisma.production.findMany({ where: { id: { in: ids }, ownerUserId: auth.session!.userId }, include: { currentVersion: true, seriesEpisode: true } }) : [];
  const byId = new Map(productions.map((production) => [production.id, production]));

  const items = await Promise.all(drafts.map(async (draft) => {
    const production = byId.get(draft.id); const version = production?.currentVersion;
    const engine = (draft.payload as { engine?: { kind?: string; jobId?: string } } | null)?.engine;
    const engineKind = engine?.kind === "whiteboard" || engine?.kind === "explainer" ? engine.kind as EngineKind : null;
    const jobId = engine?.jobId ?? "";

    let state = production?.studioState ?? draft.studioState;
    let coverUrl = version?.thumbnailObjectKey ? `/api/v1/productions/${draft.id}/poster` : null;
    let previewUrl = version?.previewObjectKey ? `/api/v1/productions/${draft.id}/preview` : null;
    let latestOutputUrl = version?.outputObjectKey ? `/api/v1/productions/${draft.id}/output` : null;
    let enginePhase: string | null = null;
    let failureCode: string | null = null;
    let engineOutputs: Record<string, string> | null = null;

    if (engineKind && jobId) {
      const job = readEngineJob(engineKind, jobId);
      state = job.status === "done" ? "COMPLETE" : job.status === "failed" ? "PRODUCTION_FAILED" : "PRODUCTION";
      enginePhase = job.phase ?? null;
      failureCode = job.failureCode ?? null;
      const outputs = job.outputs ?? {};
      const best = outputs["16x9"] ?? Object.values(outputs)[0] ?? null;
      if (best) { coverUrl = best; previewUrl = best; latestOutputUrl = best; }
      engineOutputs = Object.keys(outputs).length ? outputs : null;
      if (state !== draft.studioState) {
        await prisma.draft.update({ where: { id: draft.id }, data: { studioState: state } }).catch(() => {});
      }
    }

    return {
      id: draft.id, ownerId: draft.ownerUserId, anonymousSessionId: null, family: draft.family, videoType: draft.videoType ?? "", prompt: draft.prompt ?? "", sources: Array.isArray(draft.sources) ? draft.sources : [], duration: draft.duration, aspectRatio: draft.aspectRatio, voicePreference: draft.voicePreference, brandContext: draft.brandContext, createdAt: draft.createdAt.toISOString(), updatedAt: draft.updatedAt.toISOString(), state, title: draft.title,
      coverUrl, previewUrl, latestOutputUrl,
      brandId: production?.brandId ?? null, seriesId: production?.seriesId ?? null, episodeOrdinal: production?.seriesEpisode?.episodeOrdinal ?? null,
      engine: engineKind && jobId ? { kind: engineKind, jobId, phase: enginePhase, failureCode, outputs: engineOutputs } : null,
    };
  }));
  return json({ productions: items, fetchedAt: new Date().toISOString() }, auth.id);
}
