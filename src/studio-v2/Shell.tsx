"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { CreateView } from "./views/CreateView";
import { WorkView } from "./views/WorkView";
import { BrandView } from "./views/BrandView";
import { LibraryView } from "./views/LibraryView";
import { SeriesView } from "./views/SeriesView";
import { CreditsSheet } from "./overlays/Credits";
import { AccountSheet } from "./overlays/Account";
import { FlowOverlay, type FlowState } from "./overlays/Flow";
import { PickerSheets, type SheetId } from "./overlays/Sheets";
import { HistoryOverlay } from "./overlays/History";
import { route, useStudio, formatUSD, type ContextChip, type ViewId } from "./App";

export interface ComposerState {
  prompt: string;
  contexts: ContextChip[];
  family: string | null;
  mode?: "brief" | "script";
}

export default function Shell({ view }: { view: ViewId }) {
  const { balance, projects } = useStudio();
  const [sheet, setSheet] = useState<SheetId | null>(null);
  const [creditsOpen, setCreditsOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const [historyId, setHistoryId] = useState<string | null>(null);
  // flow survives refresh: stored per-tab so a reload returns to the same stage
  const [flow, setFlow] = useState<FlowState | null>(null);
  const [flowReady, setFlowReady] = useState(false);
  useEffect(() => {
    try {
      const raw = sessionStorage.getItem("nx.flow");
      if (raw) setFlow(JSON.parse(raw) as FlowState);
    } catch { /* corrupt storage — start clean */ }
    setFlowReady(true);
  }, []);
  useEffect(() => {
    if (!flowReady) return;
    try {
      if (flow) sessionStorage.setItem("nx.flow", JSON.stringify(flow));
      else sessionStorage.removeItem("nx.flow");
    } catch { /* storage full/blocked — non-fatal */ }
  }, [flow, flowReady]);
  const [seriesFocus, setSeriesFocus] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [composer, setComposer] = useState<ComposerState>({ prompt: "", contexts: [], family: null });

  const notify = useCallback((msg: string) => {
    setToast(msg);
  }, []);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3200);
    return () => clearTimeout(t);
  }, [toast]);

  const openSeries = useCallback((id: string | null) => {
    setSeriesFocus(id);
    route("series");
  }, []);

  const addContext = useCallback((chip: ContextChip) => {
    setComposer((c) => ({ ...c, contexts: [...c.contexts.filter((x) => !(x.kind === chip.kind && x.refId === chip.refId)), chip] }));
  }, []);

  const removeContext = useCallback((chip: ContextChip) => {
    setComposer((c) => ({ ...c, contexts: c.contexts.filter((x) => !(x.kind === chip.kind && x.refId === chip.refId)) }));
  }, []);

  const setPrompt = useCallback((prompt: string) => setComposer((c) => ({ ...c, prompt })), []);
  const setFamily = useCallback((family: string | null) => setComposer((c) => ({ ...c, family })), []);
  const setMode = useCallback((mode: "brief" | "script") => setComposer((c) => ({ ...c, mode })), []);

  const flowApi = useMemo(() => ({
    openFlow: (initial: FlowState) => setFlow(initial),
    closeFlow: () => setFlow(null),
    patchFlow: (patch: Partial<FlowState>) => setFlow((f) => (f ? { ...f, ...patch } : f)),
    setSheet, notify, openSeries,
    composer, setComposer,
  }), [composer, notify, openSeries]);

  return (
    <div className="shell">
      <header className="topbar">
        <button aria-label="NexStudio home" className="brand" onClick={() => route("create")} style={{ border: 0, background: "none", padding: 0 }}>
          <span className="brand-mark"><i /></span><span>NexStudio</span>
        </button>
        <nav aria-label="Primary" className="nav">
          {(["create", "work", "brand", "library"] as const).map((v) => (
            <button key={v} data-route={v} className={view === v || (v === "work" && view === "series") ? "active" : ""} aria-current={view === v ? "page" : undefined} onClick={() => route(v)}>
              {v[0].toUpperCase() + v.slice(1)}
            </button>
          ))}
        </nav>
        <div className="account">
          <button aria-label="Open credits" className="credits" onClick={() => setCreditsOpen(true)}>
            <span className="credit-dot" /><span>{balance ? formatUSD(balance.availableMinor) : "—"}</span>
          </button>
          <button aria-label="Open account" className="avatar" onClick={() => setAccountOpen(true)}>CM</button>
        </div>
      </header>
      <main>
        <section className={`view ${view === "create" ? "active" : ""}`} id="view-create">
          <CreateView composer={composer} setPrompt={setPrompt} setFamily={setFamily} setMode={setMode} removeContext={removeContext} openSheet={setSheet} openFlow={flowApi.openFlow} onOpenWork={(id) => {
            const p = projects.find((x) => x.id === id);
            if (p?.engine?.jobId) {
              const done = p.engine.outputs && Object.keys(p.engine.outputs).length > 0;
              flowApi.openFlow(done
                ? { stage: "review", jobKind: p.engine.kind, jobId: p.engine.jobId, jobOutputs: p.engine.outputs ?? {} }
                : { stage: "production", jobKind: p.engine.kind, jobId: p.engine.jobId });
              return;
            }
            setHistoryId(id);
          }} openSeries={openSeries} notify={notify} />
        </section>
        <section className={`view ${view === "work" ? "active" : ""}`} id="view-work">
          <WorkView onOpenHistory={(id) => setHistoryId(id)} onOpenJob={(p) => {
            const done = p.engine.outputs && Object.keys(p.engine.outputs).length > 0;
            flowApi.openFlow(done
              ? { stage: "review", jobKind: p.engine.kind, jobId: p.engine.jobId, jobOutputs: p.engine.outputs ?? {} }
              : { stage: "production", jobKind: p.engine.kind, jobId: p.engine.jobId });
          }} />
        </section>
        <section className={`view ${view === "brand" ? "active" : ""}`} id="view-brand">
          <BrandView openSheet={setSheet} notify={notify} openSeries={openSeries} onOpenWork={(id) => setHistoryId(id)} />
        </section>
        <section className={`view ${view === "library" ? "active" : ""}`} id="view-library">
          <LibraryView openSheet={setSheet} notify={notify} addContext={addContext} />
        </section>
        <section className={`view ${view === "series" ? "active" : ""}`} id="view-series">
          <SeriesView focusId={seriesFocus} openSheet={setSheet} notify={notify} onOpenHistory={(id) => setHistoryId(id)} />
        </section>
      </main>
      <nav aria-label="Mobile primary" className="mobile-nav">
        {(["create", "work", "brand", "library"] as const).map((v) => (
          <button key={v} data-route={v} className={view === v ? "active" : ""} onClick={() => route(v)}>
            <span>{v[0].toUpperCase() + v.slice(1)}</span>
          </button>
        ))}
      </nav>
      <PickerSheets open={sheet} onClose={() => setSheet(null)} composer={composer} addContext={addContext} openSeries={openSeries} notify={notify} />
      {creditsOpen && <CreditsSheet onClose={() => setCreditsOpen(false)} notify={notify} />}
      {accountOpen && <AccountSheet onClose={() => setAccountOpen(false)} notify={notify} />}
      {historyId && <HistoryOverlay productionId={historyId} onClose={() => setHistoryId(null)} openSeries={openSeries} onReview={(id) => { setHistoryId(null); flowApi.openFlow({ stage: "review", productionId: id }); }} notify={notify} />}
      {flow && <FlowOverlay flow={flow} api={flowApi} />}
      {toast ? <div className="toast show">{toast}</div> : null}
    </div>
  );
}
