"use client";

import dynamic from "next/dynamic";
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { StudioAsset } from "@/studio-v1/dashboard/domain/assets";
import type { StudioBalance, StudioBillingEntry } from "@/studio-v1/dashboard/domain/billing";
import type { StudioBrandRoot, StudioSeriesRoot } from "@/studio-v1/dashboard/domain/creative-memory";
import type { DashboardProject } from "@/studio-v1/dashboard/domain/dashboard";
import { studioApi } from "./api";

export type ViewId = "create" | "work" | "brand" | "library" | "series";

export interface ContextChip {
  kind: "brand" | "series" | "file" | "reference";
  refId: string;
  label: string;
  meta?: string;
}

export type Scope = "work" | "brands" | "series" | "assets" | "balance" | "ledger";

export interface StudioData {
  projects: Array<DashboardProject & { prompt?: string | null; engine?: { kind: "whiteboard" | "explainer"; jobId: string; phase: string | null; failureCode: string | null; outputs?: Record<string, string> | null } | null }>;
  brands: StudioBrandRoot[];
  series: StudioSeriesRoot[];
  assets: StudioAsset[];
  balance: StudioBalance | null;
  ledger: StudioBillingEntry[];
  loading: boolean;
  refresh: (scopes?: Scope[]) => Promise<void>;
}

const StudioContext = createContext<StudioData | null>(null);

export function useStudio(): StudioData {
  const ctx = useContext(StudioContext);
  if (!ctx) throw new Error("useStudio outside StudioContext");
  return ctx;
}

const VIEWS: ViewId[] = ["create", "work", "brand", "library", "series"];

function hashToView(hash: string): ViewId | null {
  const v = hash.replace(/^#\/?/, "");
  return (VIEWS as string[]).includes(v) ? (v as ViewId) : null;
}

export function route(view: ViewId) {
  if (location.hash !== `#${view}`) location.hash = view;
}

export function formatUSD(minor: number): string {
  return new Intl.NumberFormat(undefined, { style: "currency", currency: "USD" }).format(minor / 100);
}

export function MindSpark() {
  return <span className="mind-spark">✦</span>;
}

export function Eyebrow({ children }: { children: React.ReactNode }) {
  return <div className="eyebrow"><MindSpark /> {children}</div>;
}

export function Overlay({ onClose, children }: { onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="overlay open" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="sheet" role="dialog" aria-modal="true">{children}</div>
    </div>
  );
}

export function SheetHead({ eyebrow, title, sub, onClose }: { eyebrow: string; title: string; sub?: string; onClose: () => void }) {
  return (
    <div className="sheet-head">
      <div><p>{eyebrow}</p><h2>{title}</h2>{sub ? <div className="series-picker-intro">{sub}</div> : null}</div>
      <button aria-label="Close" className="close" onClick={onClose}>×</button>
    </div>
  );
}

const Shell = dynamic(() => import("./Shell"), { ssr: false });

export function StudioApp({ initialAuthed }: { initialAuthed: boolean }) {
  const [view, setView] = useState<ViewId>("create");
  const [projects, setProjects] = useState<StudioData["projects"]>([]);
  const [brands, setBrands] = useState<StudioBrandRoot[]>([]);
  const [seriesList, setSeriesList] = useState<StudioSeriesRoot[]>([]);
  const [assets, setAssets] = useState<StudioAsset[]>([]);
  const [balance, setBalance] = useState<StudioBalance | null>(null);
  const [ledger, setLedger] = useState<StudioBillingEntry[]>([]);
  const [loading, setLoading] = useState(initialAuthed);
  const abortRef = useRef<AbortController | null>(null);

  const refresh = useCallback(async (scopes?: Scope[]) => {
    if (!initialAuthed) { setLoading(false); return; }
    abortRef.current?.abort();
    const ctl = new AbortController();
    abortRef.current = ctl;
    const want = new Set(scopes ?? (["work", "brands", "series", "assets", "balance", "ledger"] as Scope[]));
    const jobs: Array<Promise<void>> = [];
    try {
      if (want.has("work")) jobs.push(studioApi.work(ctl.signal).then((w) => setProjects(w.projects)).catch(() => {}));
      if (want.has("brands")) jobs.push(studioApi.brands(ctl.signal).then((b) => setBrands(b.brands)).catch(() => {}));
      if (want.has("series")) jobs.push(studioApi.series(ctl.signal).then((s) => setSeriesList(s.series)).catch(() => {}));
      if (want.has("assets")) jobs.push(studioApi.assets(ctl.signal).then((a) => setAssets(a.items)).catch(() => {}));
      if (want.has("balance")) jobs.push(studioApi.balance(ctl.signal).then(setBalance).catch(() => {}));
      if (want.has("ledger")) jobs.push(studioApi.billingHistory(ctl.signal).then((h) => setLedger(h.entries)).catch(() => {}));
      await Promise.allSettled(jobs);
    } finally {
      setLoading(false);
    }
  }, [initialAuthed]);

  useEffect(() => { refresh(); }, [refresh]);

  useEffect(() => {
    const onHash = () => setView(hashToView(location.hash) ?? "create");
    onHash();
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const data = useMemo<StudioData>(() => ({
    projects, brands, series: seriesList, assets, balance, ledger, loading, refresh,
  }), [projects, brands, seriesList, assets, balance, ledger, loading, refresh]);

  return (
    <StudioContext.Provider value={data}>
      <Shell view={view} />
    </StudioContext.Provider>
  );
}
