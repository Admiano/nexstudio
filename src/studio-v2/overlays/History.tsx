"use client";

import { useEffect, useState } from "react";
import { useStudio } from "../App";
import { studioApi, type VersionRecord } from "../api";

export function HistoryOverlay({ productionId, onClose, openSeries, onReview, notify }: {
  productionId: string;
  onClose: () => void;
  openSeries: (id: string | null) => void;
  onReview: (id: string) => void;
  notify: (m: string) => void;
}) {
  const { projects, series } = useStudio();
  const item = projects.find((p) => p.id === productionId) ?? null;
  const [versions, setVersions] = useState<VersionRecord[]>([]);
  const linkedSeries = item?.seriesId ? series.find((s) => s.id === item.seriesId) : null;

  useEffect(() => {
    const ctl = new AbortController();
    studioApi.versions(productionId, ctl.signal).then((v) => setVersions(v.versions)).catch(() => setVersions([]));
    return () => ctl.abort();
  }, [productionId]);

  return (
    <div aria-hidden="true" className="work-history-overlay open" id="workHistoryOverlay" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <aside className="work-history-panel" role="dialog" aria-modal="true">
        <div className="work-history-top">
          <div><span className="mini-label">Production history</span><h2>{item?.title ?? "Production"}</h2><p>Versions and publishing stay attached.</p></div>
          <button aria-label="Close" className="work-history-close" onClick={onClose}>×</button>
        </div>
        <div className="work-history-body">
          <div className="work-history-hero">
            <div className={`work-thumb-v2 ${(item?.family ?? "").toLowerCase()}`} style={item?.coverUrl ? { backgroundImage: `url(${item.coverUrl})`, backgroundSize: "cover" } : undefined} />
            <div className="history-current">
              <span className="mini-label">{item?.statusLabel ?? "In progress"}</span>
              <h3>Current version</h3>
              <p>{item?.prompt ? `“${item.prompt}”` : "Open this production to continue."}</p>
            </div>
          </div>
          <section className="history-section">
            <div className="history-section-head"><h3>Series lineage</h3><span>{linkedSeries ? linkedSeries.name : "Not attached"}</span></div>
            {linkedSeries ? (
              <div className="work-series-actions"><button onClick={() => openSeries(linkedSeries.id)}>Open series</button></div>
            ) : <p className="account-empty">This production is not part of a series.</p>}
          </section>
          <section className="history-section">
            <div className="history-section-head"><h3>Versions</h3><span>{versions.length} version{versions.length === 1 ? "" : "s"}</span></div>
            <div className="version-stack">
              {versions.map((v) => (
                <div key={v.id} className="version-card">
                  <span className="version-num">v{v.versionNumber}</span>
                  <div><b>{v.isCurrent ? "Current version" : "Version"}</b><p>{v.approvedAt ? "Approved" : "Created"}</p></div>
                  <time>{new Date(v.approvedAt ?? v.createdAt).toLocaleDateString()}</time>
                </div>
              ))}
              {versions.length === 0 && <p className="account-empty">No completed versions yet.</p>}
            </div>
          </section>
          <button className="history-action" onClick={() => onReview(productionId)}>Open review →</button>
          {item?.latestOutputUrl ? <a className="history-action secondary" href={item.latestOutputUrl}>Open latest output</a> : null}
        </div>
      </aside>
    </div>
  );
}
