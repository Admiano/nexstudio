"use client";

import type { StudioAsset, StudioAssetPage } from "@/studio-v1/dashboard/domain/assets";
import type { StudioBalance, StudioBillingHistory } from "@/studio-v1/dashboard/domain/billing";
import type { DashboardProject } from "@/studio-v1/dashboard/domain/dashboard";
import type { StudioBrandRoot, StudioMemoryCollection, StudioMemoryScope, StudioSeriesRoot } from "@/studio-v1/dashboard/domain/creative-memory";

export interface ProductionDetail {
  id: string;
  title: string | null;
  prompt: string;
  family: string | null;
  videoType: string;
  state: string;
  duration: number | null;
  aspectRatio: string | null;
  coverUrl: string | null;
  previewUrl: string | null;
  latestOutputUrl: string | null;
  brandId: string | null;
  seriesId: string | null;
  episodeOrdinal: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface WorkflowProjection {
  state?: string;
  stages?: Array<{ key: string; label: string; status: string; detail?: string }>;
  [key: string]: unknown;
}

export interface VersionRecord {
  id: string;
  versionNumber: number;
  approvedAt: string | null;
  createdAt: string;
  isCurrent: boolean;
}

export interface ProblemDetail {
  code?: string;
  title?: string;
  detail?: string;
}

async function readJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, {
    credentials: "include",
    headers: { Accept: "application/json" },
    cache: "no-store",
    signal,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as (ProblemDetail & { problem?: ProblemDetail }) | null;
    const err = new Error(body?.title || body?.problem?.title || `Request failed (${response.status})`) as Error & { code?: string; status?: number };
    err.code = body?.code ?? body?.problem?.code;
    err.status = response.status;
    throw err;
  }
  const payload = await response.json() as { data?: T } | T;
  if (payload && typeof payload === "object" && "data" in payload) return (payload as { data: T }).data;
  return payload as T;
}

async function postJson<T>(url: string, body: unknown, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    credentials: "include",
    headers: { "content-type": "application/json", Accept: "application/json", "Idempotency-Key": crypto.randomUUID() },
    body: JSON.stringify(body),
    signal,
  });
  if (!response.ok) {
    const parsed = await response.json().catch(() => null) as (ProblemDetail & { problem?: ProblemDetail }) | null;
    const err = new Error(parsed?.title || parsed?.problem?.title || `Request failed (${response.status})`) as Error & { code?: string; status?: number };
    err.code = parsed?.code ?? parsed?.problem?.code;
    err.status = response.status;
    throw err;
  }
  const payload = await response.json() as { data?: T } | T;
  if (payload && typeof payload === "object" && "data" in payload) return (payload as { data: T }).data;
  return payload as T;
}

export interface EngineJobStatus {
  jobId: string;
  status: "running" | "done" | "failed";
  outputs?: Record<string, string>;
  exitCode?: number;
  error?: string;
  progress?: { phase?: string; aspect?: string; aspectsDone?: number; aspectsTotal?: number } | null;
}

export type EngineKind = "explainer" | "whiteboard";

async function postForm<T>(url: string, form: FormData): Promise<T> {
  const response = await fetch(url, { method: "POST", credentials: "include", body: form });
  if (!response.ok) {
    const parsed = await response.json().catch(() => null) as (ProblemDetail & { problem?: ProblemDetail }) | null;
    const err = new Error(parsed?.title || parsed?.problem?.title || `Request failed (${response.status})`) as Error & { code?: string; status?: number };
    err.code = parsed?.code ?? parsed?.problem?.code;
    err.status = response.status;
    throw err;
  }
  const payload = await response.json() as { data?: T } | T;
  if (payload && typeof payload === "object" && "data" in payload) return (payload as { data: T }).data;
  return payload as T;
}

export const studioApi = {
  work: (signal?: AbortSignal) =>
    readJson<{ productions: Array<DashboardProject & { prompt?: string | null }>; fetchedAt?: string }>("/api/v1/studio/productions", signal)
      .then((p) => ({ projects: p.productions, fetchedAt: p.fetchedAt ?? new Date().toISOString() })),
  brands: (signal?: AbortSignal) => readJson<{ brands: StudioBrandRoot[] }>("/api/v1/studio/brands", signal),
  series: (signal?: AbortSignal) => readJson<{ series: StudioSeriesRoot[] }>("/api/v1/studio/series", signal),
  memory: (scope: StudioMemoryScope, scopeRefId: string, signal?: AbortSignal) =>
    readJson<StudioMemoryCollection>(`/api/v1/studio/memory?scope=${scope}&scopeRefId=${encodeURIComponent(scopeRefId)}`, signal),
  memoryWrite: (input: {
    scope: StudioMemoryScope;
    scopeRefId: string;
    key: string;
    category: string;
    label?: string;
    content: Record<string, unknown>;
    reason?: string;
  }, signal?: AbortSignal) =>
    postJson<{ memoryItemId: string; versionId: string; versionNumber: number }>("/api/v1/studio/memory", input, signal),
  assets: (signal?: AbortSignal) => readJson<StudioAssetPage>("/api/v1/studio/assets", signal),
  balance: (signal?: AbortSignal) => readJson<StudioBalance>("/api/v1/studio/balance", signal),
  billingHistory: (signal?: AbortSignal) => readJson<StudioBillingHistory>("/api/v1/studio/billing/history", signal),
  versions: (productionId: string, signal?: AbortSignal) =>
    readJson<{ currentVersionNumber: number | null; versions: VersionRecord[] }>(`/api/v1/studio/productions/${productionId}/versions`, signal),
  workflow: (productionId: string, signal?: AbortSignal) =>
    readJson<WorkflowProjection>(`/api/v1/studio/productions/${productionId}/workflow`, signal),
  draft: (productionId: string, signal?: AbortSignal) =>
    readJson<ProductionDetail>(`/api/v1/studio/production-drafts/${productionId}`, signal),
  recommend: (prompt: string, signal?: AbortSignal) =>
    postJson<{ status: string; recommendation?: { family: string; videoType: string; reason: string } }>("/api/v1/studio/recommendation", { prompt }, signal),
  script: (input: { brief: string; family: string; videoType: string; duration: number; beats?: Array<{ purposeTitle: string; description: string }> }, signal?: AbortSignal) =>
    postJson<{ status: string; script?: string; lines?: string[]; title?: string | null }>("/api/v1/studio/script", input, signal),
  createDraft: (input: {
    id: string; family: string; videoType: string; prompt: string;
    duration?: number | null; aspectRatio?: string | null; voicePreference?: string | null;
    sources?: Array<{ kind: string; label?: string | null; reference?: string | null; id?: string }>;
    brandContext?: Record<string, unknown> | null;
  }, signal?: AbortSignal) => postJson<ProductionDetail>("/api/v1/studio/production-drafts", input, signal),
  planPreview: (productionId: string, signal?: AbortSignal) =>
    postJson<unknown>("/api/v1/studio/plan-preview", { productionId }, signal),
  quote: (productionId: string, signal?: AbortSignal) =>
    postJson<unknown>(`/api/v1/studio/productions/${productionId}/quote`, {}, signal),
  purchase: (productionId: string, quoteId: string, signal?: AbortSignal) =>
    postJson<unknown>(`/api/v1/studio/productions/${productionId}/purchase`, { quoteId }, signal),
  review: (productionId: string, input: { action: "approve" } | { action: "revision"; note?: string; timestampSeconds?: number }, signal?: AbortSignal) =>
    postJson<unknown>(`/api/v1/productions/${productionId}/review`, input, signal),
  createBrand: (input: { name: string; slug?: string; description?: string; authority?: Record<string, unknown> }, signal?: AbortSignal) =>
    postJson<{ brandId: string }>("/api/v1/studio/brands", input, signal),
  createSeries: (input: { name: string; description?: string; brandId?: string; bible?: Record<string, unknown> }, signal?: AbortSignal) =>
    postJson<{ seriesId: string }>("/api/v1/studio/series", input, signal),
  nextEpisode: (seriesId: string, input: { family: string; videoType: string; prompt: string; duration?: number | null; aspectRatio?: string | null }, signal?: AbortSignal) =>
    postJson<unknown>(`/api/v1/studio/series/${seriesId}/next-episode`, input, signal),
  fundingIntent: (requestedTopupMinor: number, signal?: AbortSignal) =>
    postJson<unknown>("/api/v1/studio/funding-intents", { purpose: "BALANCE_TOPUP", requestedTopupMinor }, signal),
  accountSessions: (signal?: AbortSignal) => readJson<{ sessions: Array<{ id: string; current: boolean; userAgent: string | null; lastSeenAt: string }> }>("/api/v1/account/sessions", signal),
  revokeOtherSessions: async (signal?: AbortSignal) => {
    const response = await fetch("/api/v1/account/sessions", { method: "DELETE", credentials: "include", signal });
    if (!response.ok) throw new Error(`Could not revoke sessions (${response.status})`);
    return response.json() as Promise<{ revoked: number }>;
  },
  requestAccountExport: (signal?: AbortSignal) => postJson<unknown>("/api/v1/account/data", { type: "EXPORT" }, signal),
  accountData: (signal?: AbortSignal) => readJson<{ items: Array<{ id: string; type: string; status: string; downloadUrl: string | null }> }>("/api/v1/account/data", signal),
  explainerCatalog: (signal?: AbortSignal) =>
    readJson<{ styles: Array<{ id: string; name: string; tagline?: string; variants?: Array<{ id: string; name: string }> }>; voices: string[]; aspects: string[] }>("/api/v1/explainers", signal),
  whiteboardCatalog: (signal?: AbortSignal) =>
    readJson<{ types: Array<{ id: string; name: string }>; themes: string[]; voices: string[]; aspects: string[] }>("/api/v1/whiteboards", signal),
  createEngineJob: (kind: EngineKind, form: FormData) =>
    postForm<{ jobId: string; status: string; statusUrl: string }>(`/api/v1/${kind}s`, form),
  engineJobStatus: (kind: EngineKind, jobId: string, signal?: AbortSignal) =>
    readJson<EngineJobStatus>(`/api/v1/${kind}s/${jobId}`, signal),
  signIn: (email: string) => postJson<unknown>("/api/v1/auth/email/request", { email }),
  signOut: () => postJson<unknown>("/api/v1/auth/logout", {}),
  uploadAsset: async (file: File, signal?: AbortSignal): Promise<StudioAsset> => {
    const form = new FormData();
    form.set("file", file);
    form.set("rightsAttested", "true");
    const response = await fetch("/api/v1/studio/assets", {
      method: "POST",
      credentials: "include",
      body: form,
      signal,
    });
    if (!response.ok) {
      const parsed = await response.json().catch(() => null) as { problem?: ProblemDetail } | null;
      throw new Error(parsed?.problem?.title || `Upload failed (${response.status})`);
    }
    return response.json() as Promise<StudioAsset>;
  },
};
