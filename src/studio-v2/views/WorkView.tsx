"use client";

import { useMemo, useState } from "react";
import { Eyebrow, route, useStudio } from "../App";
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

export function WorkView({ onOpenHistory, onContinue }: { onOpenHistory: (id: string) => void; onContinue: (id: string) => void }) {
  const { projects } = useStudio();
  const [filter, setFilter] = useState<Filter>("all");
  const sorted = useMemo(() => sortDashboardProjects(projects), [projects]);
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
        <span className="work-sort">Most recently updated first</span>
      </div>
      <div className="work-list">
        {list.map((p) => (
          <button key={p.id} className="work-row" onClick={() => onOpenHistory(p.id)}>
            <div className={`work-thumb tone-${p.statusTone ?? "neutral"}`} style={p.coverUrl ? { backgroundImage: `url(${p.coverUrl})`, backgroundSize: "cover" } : undefined} />
            <div className="work-row-main">
              <b>{p.title}</b>
              <span>{p.family}{p.videoType ? ` · ${p.videoType}` : ""}{p.durationSeconds ? ` · ${p.durationSeconds} sec` : ""}</span>
            </div>
            <div className="work-row-side">
              <span className={`work-status tone-${p.statusTone ?? "neutral"}`}>{p.statusLabel}</span>
              {p.seriesId ? <span className="work-series-chip">Series</span> : null}
              <span className="work-open" onClick={(e) => { e.stopPropagation(); onContinue(p.id); }}>Open →</span>
            </div>
          </button>
        ))}
        {list.length === 0 && <p className="empty-note">Nothing in this view yet.</p>}
      </div>
    </div>
  );
}
