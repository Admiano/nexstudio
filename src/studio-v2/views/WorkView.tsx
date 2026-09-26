"use client";

import { useMemo, useState } from "react";
import { Eyebrow, route, useStudio } from "../App";
import { loadViewed, markViewed } from "../viewed";
import { sortDashboardProjects, type DashboardProject } from "@/studio-v1/dashboard/domain/dashboard";

type Filter = "all" | "needs" | "production" | "ready" | "published";

const FILTERS: Array<{ key: Filter; label: string }> = [
  { key: "all", label: "All work" },
  { key: "needs", label: "Needs you" },
  { key: "production", label: "In production" },
  { key: "ready", label: "Ready" },
  { key: "published", label: "Published / handed off" },
];

function bucket(p: DashboardProject): Filter | "other" {
  if (p.needsAction) return "needs";
  const s = (p.state || "").toUpperCase();
  if (s.includes("REVIEW") || s === "READY" || p.statusTone === "ready") return "ready";
  if (s.includes("PROGRESS") || s.includes("RENDER") || s.includes("PRODUC")) return "production";
  if (s.includes("PUBLISH") || s.includes("COMPLETE") || s.includes("DELIVER")) return "published";
  return "other";
}

export function WorkView({ onOpenHistory, onOpenJob }: {
  onOpenHistory: (id: string) => void;
  onOpenJob: (p: { engine: { kind: "whiteboard" | "explainer"; jobId: string; outputs?: Record<string, string> | null }; id: string }) => void;
}) {
  const { projects, loading } = useStudio();
  const [filter, setFilter] = useState<Filter>("all");
  const [layout, setLayout] = useState<"list" | "tiles">("list");
  const [viewed] = useState<Set<string>>(() => loadViewed());
  const sorted = useMemo(() => sortDashboardProjects(projects) as typeof projects, [projects]);
  const needs = sorted.filter((p) => p.needsAction).length;
  const making = sorted.filter((p) => bucket(p) === "production").length;
  const ready = sorted.filter((p) => bucket(p) === "ready").length;
  const list = filter === "all" ? sorted : sorted.filter((p) => bucket(p) === filter);

  return (
    <div className="work-v2">
      <div className="work-v2-head">
        <div>
          <Eyebrow>Your production home</Eyebrow>
          <h1>Everything you’re making.</h1>
          <p>Open a production and continue from the exact place that matters. Versions, revisions and publishing stay attached without turning your work into project-management clutter.</p>
        </div>
        <button className="work-create-new" onClick={() => route("create")}>+ New video</button>
      </div>
      <div className="work-summary">
        <div className="work-summary-main"><span>Right now</span><strong>{needs > 0 ? `${needs} item${needs > 1 ? "s" : ""} need${needs > 1 ? "" : "s"} you.` : "Your work is up to date."}</strong></div>
        <div className="work-summary-cell"><span>Needs you</span><strong>{needs}</strong></div>
        <div className="work-summary-cell"><span>Being made</span><strong>{making}</strong></div>
        <div className="work-summary-cell"><span>Ready</span><strong>{ready}</strong></div>
      </div>
      <div className="work-controls">
        <div className="work-filters">
          {FILTERS.map((f) => (
            <button key={f.key} aria-pressed={filter === f.key} className={`work-filter ${filter === f.key ? "active" : ""}`} onClick={() => setFilter(f.key)}>{f.label}</button>
          ))}
        </div>
        <div className="view-toggle" role="group" aria-label="Layout">
          <button className={layout === "list" ? "active" : ""} onClick={() => setLayout("list")} aria-pressed={layout === "list"}><svg viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h16" /></svg>List</button>
          <button className={layout === "tiles" ? "active" : ""} onClick={() => setLayout("tiles")} aria-pressed={layout === "tiles"}><svg viewBox="0 0 24 24"><rect x="4" y="4" width="7" height="7" rx="1.5" /><rect x="13" y="4" width="7" height="7" rx="1.5" /><rect x="4" y="13" width="7" height="7" rx="1.5" /><rect x="13" y="13" width="7" height="7" rx="1.5" /></svg>Tiles</button>
        </div>
        <span className="work-sort">Most recently updated first</span>
      </div>
      <div className={layout === "tiles" ? "work-tiles rise" : "work-list rise"}>
        {list.map((p) => {
          const s = (p.state || "").toUpperCase();
          const dot = p.statusTone === "recovering" || s.includes("REVISION") ? "revision"
            : p.statusTone === "ready" || s === "COMPLETE" || s.includes("REVIEW") || s.includes("READY") ? "ready"
            : s.includes("PRODUCTION") || s.includes("PLANNING") || s.includes("PENDING") || s.includes("RETRY") ? "production"
            : s.includes("PUBLISH") || s.includes("DELIVER") ? "published"
            : "direction";
          const detail = p.needsAction ? "Waiting on you"
            : dot === "production" ? "Rendering now"
            : dot === "ready" ? "Ready to open"
            : "In direction";
          const family = (p.family || "").toLowerCase();
          const job = p.engine?.jobId ? { engine: { kind: p.engine.kind, jobId: p.engine.jobId, outputs: p.engine.outputs }, id: p.id } : null;
          const isNew = dot === "ready" && !viewed.has(p.id);
          const open = () => { markViewed(p.id); (job ? onOpenJob(job) : onOpenHistory(p.id)); };
          const thumb = <div className={`work-thumb-v2 ${family}`} style={p.coverUrl ? { backgroundImage: `url(${p.coverUrl})`, backgroundSize: "cover" } : undefined}><span className="work-thumb-state">{p.statusLabel}</span>{isNew && <span className="work-new">New</span>}</div>;
          const info = <div className="work-info"><h3>{p.title}</h3><p>{p.family}{p.videoType ? ` · ${p.videoType}` : ""}{p.durationSeconds ? ` · ${p.durationSeconds} sec` : ""}</p><div className="work-tags"><span>{p.family}</span>{p.videoType ? <span>{p.videoType}</span> : null}{p.durationSeconds ? <span>{p.durationSeconds}s</span> : null}{p.seriesId ? <span>Series</span> : null}</div></div>;
          const state = <div className="work-state-v2"><b><span className={`state-dot st-${dot}`} />{p.statusLabel}</b><span>{detail}</span></div>;
          if (layout === "tiles") {
            return (
              <article key={p.id} className="work-tile" onClick={open} role="button" tabIndex={0} onKeyDown={(e) => { if (e.key === "Enter") open(); }}>
                {thumb}
                {info}
                <div className="work-tile-foot">{state}<button className="work-open" onClick={(e) => { e.stopPropagation(); open(); }}>Open →</button></div>
              </article>
            );
          }
          return (
            <article key={p.id} className="work-row" onClick={open} role="button" tabIndex={0} onKeyDown={(e) => { if (e.key === "Enter") open(); }}>
              {thumb}
              {info}
              {state}
              <div className="work-row-actions">
                <button className="work-open" onClick={(e) => { e.stopPropagation(); open(); }}>Open →</button>
                {!job && <button className="work-history-btn" onClick={(e) => { e.stopPropagation(); onOpenHistory(p.id); }}>History</button>}
              </div>
            </article>
          );
        })}
        {list.length === 0 && loading && [0, 1, 2].map((i) => (
          <div key={i} className="work-row work-sk" aria-hidden="true">
            <div className="work-thumb-v2 sk-block" />
            <div className="work-info"><div className="sk-line sk-lg" /><div className="sk-line sk-sm sk-gap" /><div className="work-tags"><span className="sk-chip" /><span className="sk-chip" /></div></div>
            <div className="work-state-v2"><div className="sk-line sk-md" /><div className="sk-line sk-sm" /></div>
          </div>
        ))}
        {list.length === 0 && !loading && (
          <div className="work-empty"><b>Nothing here yet.</b><p>Start a new video and it lands in this list.</p></div>
        )}
      </div>
    </div>
  );
}
