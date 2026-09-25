"use client";

import { useEffect, useMemo, useState } from "react";
import { ensureNxPresence } from "../nx-presence";
import type { ComposerState } from "../Shell";
import { route, useStudio, type ContextChip } from "../App";
import { studioApi } from "../api";
import type { FlowState } from "../overlays/Flow";
import type { SheetId } from "../overlays/Sheets";
import { sortDashboardProjects } from "@/studio-v1/dashboard/domain/dashboard";

const FAMILIES = [
  { key: "explainer", label: "Explainer", desc: "Clear ideas, products and systems.", soon: false },
  { key: "whiteboard", label: "Whiteboard", desc: "Drawn reasoning and visual teaching.", soon: false },
  { key: "stickman", label: "Character", desc: "Performance, dialogue and physicality.", soon: true },
  { key: "editorial-motion", label: "Illustrated Stories", desc: "Editorial motion and expressive storytelling.", soon: true },
];

export function CreateView({ composer, setPrompt, setFamily, setMode, removeContext, openSheet, openFlow, onOpenWork, openSeries, notify }: {
  composer: ComposerState;
  setPrompt: (v: string) => void;
  setFamily: (v: string | null) => void;
  setMode: (v: "brief" | "script") => void;
  removeContext: (c: ContextChip) => void;
  openSheet: (s: SheetId) => void;
  openFlow: (f: FlowState) => void;
  onOpenWork: (id: string) => void;
  openSeries: (id: string) => void;
  notify: (m: string) => void;
}) {
  const { projects, series } = useStudio();
  useEffect(() => { ensureNxPresence(); }, []);
  // The public site hands off the tapped family and the typed brief; honor both once.
  useEffect(() => {
    if (!composer.family) {
      const preselect = sessionStorage.getItem("nx.family");
      if (preselect && FAMILIES.some((f) => f.key === preselect && !f.soon)) {
        setFamily(preselect);
        sessionStorage.removeItem("nx.family");
      }
    }
    if (!composer.prompt.trim()) {
      const carried = sessionStorage.getItem("nx.brief");
      if (carried?.trim()) {
        setPrompt(carried.trim());
        setMode("brief");
        sessionStorage.removeItem("nx.brief");
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  // Studio defaults: a saved default family preselects in the composer (once).
  useEffect(() => {
    if (composer.family) return;
    let alive = true;
    studioApi.accountPreferences().then((r) => {
      if (alive && r.preferences.defaultFamily) setFamily(r.preferences.defaultFamily);
    }).catch(() => {});
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const recent = useMemo(() => sortDashboardProjects(projects).slice(0, 3), [projects]);
  const attachedSeries = composer.contexts.find((c) => c.kind === "series");
  const seriesObj = attachedSeries ? series.find((s) => s.id === attachedSeries.refId) : null;

  async function submitBrief() {
    const prompt = composer.prompt.trim();
    if (prompt.length < 8) { notify("Describe the video in a few words first."); return; }
    openFlow({ stage: "mind", prompt, script: composer.mode === "script" ? prompt : undefined, contexts: composer.contexts, family: composer.family });
  }

  function onKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") { e.preventDefault(); void submitBrief(); }
  }

  const canSubmit = composer.prompt.trim().length >= 8;

  const [welcomed, setWelcomed] = useState(true);
  useEffect(() => {
    try { setWelcomed(localStorage.getItem("nx.welcomed") === "1"); } catch { setWelcomed(true); }
  }, []);
  function dismissOnboard() {
    setWelcomed(true);
    try { localStorage.setItem("nx.welcomed", "1"); } catch { /* banner returns next visit — harmless */ }
  }
  const EXAMPLE_BRIEF = "Make a 45-second explainer about how pour-over coffee works — bloom, pour, and drawdown — warm and visual.";
  function tryExample() {
    setMode("brief");
    setPrompt(EXAMPLE_BRIEF);
    dismissOnboard();
  }

  return (
    <div className="create-wrap">
      <div className="hero">
        <div className="eyebrow"><span aria-hidden="true" className="nx-presence nx-presence--mini" data-mode="matrix" data-nx-presence="" data-state="idle"><canvas /></span> NexMind · Creative production</div>
        <h1>What do you want to make?</h1>
        <p className="lead">Describe it naturally. Add anything useful. NexMind will shape the production and show you the direction before anything is made.</p>
      </div>
      {!welcomed && (
        <div className="onboard">
          <div className="onboard-head"><div><span className="onboard-tag">First time here</span><b>Four steps to a finished video</b></div><button aria-label="Dismiss intro" className="onboard-x" onClick={dismissOnboard}>×</button></div>
          <div className="onboard-steps">
            <div className="onboard-step"><i>1</i><span><b>Describe it</b>Your words — or paste a ready script</span></div>
            <div className="onboard-step"><i>2</i><span><b>NexMind writes</b>The story and the direction</span></div>
            <div className="onboard-step"><i>3</i><span><b>You approve</b>Nothing renders without your yes</span></div>
            <div className="onboard-step"><i>4</i><span><b>It renders</b>16:9, 9:16 and 1:1 in one pass</span></div>
          </div>
          <div className="onboard-foot"><button className="onboard-try" onClick={tryExample}>Try this brief →</button><span className="onboard-note">First video takes ~3–6 minutes to render.</span></div>
        </div>
      )}
      <div className="composer-shell">
        <div className="composer" id="composer">
          <div className="composer-head">
            <div className="composer-head-copy">
              <span className="composer-eyebrow">{composer.mode === "script" ? "Your script" : "Your brief"}</span>
              <b>{composer.mode === "script" ? "Finished narration — voiced and illustrated exactly as written" : "Describe the video — NexMind writes the story and direction"}</b>
            </div>
            <div className="composer-mode" role="group" aria-label="Input mode">
              <button type="button" className={composer.mode !== "script" ? "on" : ""} onClick={() => setMode("brief")} title="Describe the idea — NexMind writes it">
                <svg fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M12 20h9" /><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" /></svg>
                Brief
              </button>
              <button type="button" className={composer.mode === "script" ? "on" : ""} onClick={() => setMode("script")} title="Paste finished narration — used verbatim">
                <svg fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" /><path d="M14 2v6h6M9 13h6M9 17h6" /></svg>
                Script
              </button>
            </div>
          </div>
          <div className="context-dock" id="contextDock">
            {composer.contexts.map((c) => (
              <button key={`${c.kind}:${c.refId}`} className={`ctx ctx-${c.kind}`} onClick={() => removeContext(c)} title="Remove context">
                <span className="ctx-ico">{c.kind === "brand" ? "◈" : c.kind === "series" ? "▤" : c.kind === "file" ? "⧉" : "↗"}</span>
                <span><b>{c.label}</b>{c.meta ? <small>{c.meta}</small> : null}</span>
                <span className="ctx-x">×</span>
              </button>
            ))}
          </div>
          <textarea aria-label="Describe your video" className="prompt" value={composer.prompt} onChange={(e) => setPrompt(e.target.value)} onKeyDown={onKey} placeholder={composer.mode === "script" ? "Paste your script — NexStudio voices and illustrates it exactly as written…" : "Make a 45-second launch video explaining why agent payments need a better primitive…"} />
          <div className="composer-foot">
            <div aria-label="Add context" className="tools">
              <button className="tool" onClick={() => openSheet("files")} title="Add files"><svg fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14" /></svg><span>Files</span></button>
              <button className="tool" onClick={() => openSheet("reference")} title="Add reference"><svg fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.1.1l2-2a5 5 0 0 0-7.1-7.1l-1.1 1.1" /><path d="M14 11a5 5 0 0 0-7.1-.1l-2 2A5 5 0 0 0 12 20l1.1-1.1" /></svg><span>Reference</span></button>
              <button className="tool" onClick={() => openSheet("brand")} title="Attach brand"><svg fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8" /><path d="M12 8v8M8 12h8" /></svg><span>Brand</span></button>
              <button className="tool" onClick={() => openSheet("series")} title="Attach series"><svg fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24"><rect height="14" rx="2" width="14" x="5" y="5" /><path d="M9 9h6M9 13h6" /></svg><span>Series</span></button>
            </div>
            <button className="create-btn" disabled={!canSubmit} onClick={() => void submitBrief()}><span>Create</span><svg fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24"><path d="M5 12h14M14 7l5 5-5 5" /></svg></button>
          </div>
          <span className="composer-inkline" aria-hidden="true" />
        </div>
        {seriesObj && (
          <div className="series-carry" style={{ display: "flex" }}>
            <div className="series-carry-visual" aria-hidden="true" />
            <span className="series-carry-copy">
              <span className="series-carry-eyebrow">Series loaded</span>
              <b>{seriesObj.name}</b>
              <small className="series-carry-identity">Production identity loads with continuity.</small>
              <small className="series-carry-previous">Previous episode context will flow into NexMind.</small>
            </span>
            <button onClick={() => openSeries(seriesObj.id)}>View series →</button>
          </div>
        )}
        <span className="kbd">⌘ ↵ to create</span>
      </div>
      <div className="start-block">
        <div className="section-head"><h2>Or give NexMind a direction</h2><p>Optional · it can infer this for you</p></div>
        <div className="directions">
          {FAMILIES.map((f) => (
            <button key={f.key} aria-pressed={composer.family === f.key} aria-disabled={f.soon} className={`direction ${composer.family === f.key ? "active" : ""} ${f.soon ? "soon" : ""}`} data-family={f.key}
              onClick={() => f.soon ? notify(`${f.label} is coming soon — still being shaped.`) : setFamily(composer.family === f.key ? null : f.key)}>
              <span className="check">✓</span>
              {f.soon && <em className="soon-tag">Coming soon</em>}
              <span className="dir-icon"><svg fill="none" stroke="currentColor" strokeWidth="1.6" viewBox="0 0 24 24"><rect height="14" rx="2" width="16" x="4" y="5" /><path d="M8 9h8M8 13h5" /></svg></span>
              <b>{f.label}</b><span>{f.desc}</span>
            </button>
          ))}
        </div>
      </div>
      <div className="recent">
        <div className="section-head"><h2>Continue where you left off</h2><button className="all-work" onClick={() => route("work")}>View all work →</button></div>
        <div className="recent-grid">
          {recent.map((p, i) => (
            <button key={p.id} className="work-card" onClick={() => onOpenWork(p.id)}>
              <div className={`thumb ${["one", "two", "three"][i % 3]}`} style={p.coverUrl ? { backgroundImage: `url(${p.coverUrl})`, backgroundSize: "cover" } : undefined} />
              <div className="work-meta"><span className="status">{p.statusLabel}</span><b>{p.title}</b><span>{p.family} · {p.durationSeconds ? `${p.durationSeconds} sec` : ""}</span></div>
            </button>
          ))}
          {recent.length === 0 && <p className="empty-note">Nothing yet — your productions will appear here.</p>}
        </div>
      </div>
    </div>
  );
}
