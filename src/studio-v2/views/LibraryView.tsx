"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Eyebrow, route, useStudio, type ContextChip } from "../App";
import { studioApi } from "../api";
import type { StudioAsset, StudioAssetKind } from "@/studio-v1/dashboard/domain/assets";
import type { SheetId } from "../overlays/Sheets";

type LibFilter = "all" | "brand" | "image" | "video" | "audio" | "document" | "reference";

const LIB_FILTERS: Array<{ key: LibFilter; label: string }> = [
  { key: "all", label: "All" },
  { key: "brand", label: "Brand assets" },
  { key: "image", label: "Images" },
  { key: "video", label: "Video" },
  { key: "audio", label: "Audio" },
  { key: "document", label: "Documents" },
  { key: "reference", label: "References" },
];

function filterOf(a: StudioAsset): LibFilter {
  if (a.kind === "logo") return "brand";
  if (a.kind === "image" || a.kind === "video" || a.kind === "audio") return a.kind;
  if (a.kind === "document") return "document";
  return "reference";
}

function fmtSize(bytes: number | null): string {
  if (bytes == null) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const RECENT_MS = 7 * 24 * 3600 * 1000;

export function LibraryView({ openSheet, notify, addContext }: { openSheet: (s: SheetId) => void; notify: (m: string) => void; addContext: (chip: ContextChip) => void }) {
  const { assets, refresh, loading } = useStudio();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<LibFilter>("all");
  const [layout, setLayout] = useState<"tiles" | "list">("tiles");
  const [detail, setDetail] = useState<StudioAsset | null>(null);
  const [busy, setBusy] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!detail) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setDetail(null); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [detail]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return assets.filter((a) => {
      if (q && !(a.name || "").toLowerCase().includes(q)) return false;
      if (filter === "all") return true;
      return filterOf(a) === filter;
    });
  }, [assets, search, filter]);

  const brandLinked = useMemo(() => assets.filter((a) => a.kind === "logo").length, [assets]);
  const recentlyUsed = useMemo(() => assets.filter((a) => Date.now() - Date.parse(a.updatedAt) < RECENT_MS).length, [assets]);

  async function ingest(files: FileList | null) {
    if (!files?.length) return;
    setBusy(true);
    try {
      for (const f of Array.from(files)) await studioApi.uploadAsset(f);
      await refresh(["assets"]);
      notify(`${files.length} file${files.length > 1 ? "s" : ""} added to Library — processing now.`);
    } catch (e) {
      notify(e instanceof Error ? e.message : "Upload failed.");
    } finally {
      setBusy(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  function useInVideo(a: StudioAsset) {
    addContext({ kind: "file", refId: a.id, label: a.name || "Asset" });
    setDetail(null);
    route("create");
  }

  async function removeAsset(a: StudioAsset) {
    try {
      await studioApi.deleteAsset(a.id);
      setDetail(null);
      await refresh(["assets"]);
      notify("Removed from reusable Library.");
    } catch (e) {
      notify(e instanceof Error ? e.message : "Could not remove the asset.");
    }
  }

  const toggle = (
    <div className="view-toggle" role="group" aria-label="Layout">
      <button className={layout === "tiles" ? "active" : ""} onClick={() => setLayout("tiles")} aria-pressed={layout === "tiles"}><svg viewBox="0 0 24 24"><rect x="4" y="4" width="7" height="7" rx="1.5" /><rect x="13" y="4" width="7" height="7" rx="1.5" /><rect x="4" y="13" width="7" height="7" rx="1.5" /><rect x="13" y="13" width="7" height="7" rx="1.5" /></svg>Tiles</button>
      <button className={layout === "list" ? "active" : ""} onClick={() => setLayout("list")} aria-pressed={layout === "list"}><svg viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h16" /></svg>List</button>
    </div>
  );

  return (
    <div className="library-v2">
      <div className="v2-page-head">
        <div><Eyebrow>Reusable production context</Eyebrow><h1>Everything NexStudio can use.</h1><p>Files, references and brand material stay reusable without turning creation into file management. Open an asset to see where it belongs, or send it straight into a new production.</p></div>
        <div className="v2-page-actions"><button className="v2-primary" onClick={() => fileRef.current?.click()} disabled={busy}>{busy ? "Uploading…" : "+ Add to Library"}</button></div>
      </div>
      <div className="library-toolbar">
        <label className="library-search"><svg fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24"><circle cx="11" cy="11" r="6" /><path d="m16 16 4 4" /></svg><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search files, brands or references" /></label>
        <input hidden ref={fileRef} multiple type="file" onChange={(e) => void ingest(e.target.files)} />
      </div>
      <div className="library-drop" onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); void ingest(e.dataTransfer.files); }}>
        <span><b>Drop anything here.</b> It becomes reusable context and remains traceable to the productions that use it.</span>
        <button onClick={() => fileRef.current?.click()}>Choose files</button>
      </div>
      <div className="library-summary">
        <div className="lib-summary-main"><span>Ready to use</span><strong>{assets.length ? `${assets.length} reusable item${assets.length === 1 ? "" : "s"} ready for production.` : "Your reusable production material."}</strong></div>
        <div className="lib-summary-cell"><span>Assets</span><strong>{assets.length}</strong></div>
        <div className="lib-summary-cell"><span>Brand-linked</span><strong>{brandLinked}</strong></div>
        <div className="lib-summary-cell"><span>Used recently</span><strong>{recentlyUsed}</strong></div>
      </div>
      <div className="library-controls">
        <div className="library-filters">
          {LIB_FILTERS.map((f) => (
            <button key={f.key} aria-pressed={filter === f.key} className={`lib-filter ${filter === f.key ? "active" : ""}`} onClick={() => setFilter(f.key)}>{f.label}</button>
          ))}
        </div>
        {toggle}
        <span className="library-sort">Most recently used first</span>
      </div>
      {layout === "tiles" ? (
        <div className="library-grid rise">
          {filtered.length === 0 && loading && [0, 1, 2, 3].map((i) => (
            <div key={i} className="asset-card work-sk" aria-hidden="true">
              <div className="asset-preview sk-block" />
              <div className="asset-meta"><div className="sk-line sk-md" /><div className="sk-line sk-sm sk-gap" /></div>
            </div>
          ))}
          {filtered.map((a) => (
            <button key={a.id} className="asset-card" onClick={() => setDetail(a)}>
              <div className={`asset-preview ${a.kind}`} data-mark={(a.name || "A")[0].toUpperCase()}>
                {a.previewUrl ? <img src={a.previewUrl} alt="" loading="lazy" decoding="async" style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} /> : null}
                <span className="asset-badge">{a.kind === "logo" ? "brand" : a.kind}</span>
                {a.rightsAttested ? <i className="asset-ready" /> : null}
              </div>
              <div className="asset-meta">
                <b>{a.name || "Untitled"}</b>
                <p>{a.kind === "logo" ? "Brand asset" : a.mimeType || "Reusable production context"}</p>
                <div className="asset-foot"><span>{fmtSize(a.sizeBytes)}</span><span>{a.sourceProductionId ? "Used in production" : "Not used yet"}</span></div>
              </div>
            </button>
          ))}
          {filtered.length === 0 && !loading && <div className="library-empty">Nothing matches this view. Try another filter or add something new.</div>}
        </div>
      ) : (
        <div className="library-rows work-list rise">
          {filtered.map((a) => (
            <article key={a.id} className="work-row" onClick={() => setDetail(a)} role="button" tabIndex={0} onKeyDown={(e) => { if (e.key === "Enter") setDetail(a); }}>
              <div className="work-thumb-v2 asset" data-mark={(a.name || "A")[0].toUpperCase()} style={a.previewUrl ? { backgroundImage: `url(${a.previewUrl})`, backgroundSize: "cover" } : undefined}>
                <span className="work-thumb-state">{a.status}</span>
              </div>
              <div className="work-info">
                <h3>{a.name || "Untitled"}</h3>
                <p>{a.kind === "logo" ? "Brand asset" : a.mimeType || "file"} · {fmtSize(a.sizeBytes)}</p>
                <div className="work-tags"><span>{a.kind}</span>{a.rightsAttested ? <span>Ready to use</span> : null}</div>
              </div>
              <div className="work-state-v2"><b><span className={`state-dot st-${a.status === "ready" ? "ready" : "production"}`} />{a.status === "ready" ? "Ready" : a.status}</b><span>{a.sourceProductionId ? "Used in production" : "Not used yet"}</span></div>
              <div className="work-row-actions"><button className="work-open" onClick={(e) => { e.stopPropagation(); setDetail(a); }}>Open →</button></div>
            </article>
          ))}
          {filtered.length === 0 && loading && [0, 1, 2].map((i) => (
            <div key={i} className="work-row work-sk" aria-hidden="true">
              <div className="work-thumb-v2 sk-block" />
              <div className="work-info"><div className="sk-line sk-lg" /><div className="sk-line sk-sm sk-gap" /></div>
              <div className="work-state-v2"><div className="sk-line sk-md" /></div>
            </div>
          ))}
          {filtered.length === 0 && !loading && <div className="work-empty"><b>Nothing here.</b><p>Try another filter or add something new.</p></div>}
        </div>
      )}
      {detail && <AssetDetail asset={detail} onClose={() => setDetail(null)} onUse={() => useInVideo(detail)} onRemove={() => void removeAsset(detail)} />}
    </div>
  );
}

function AssetDetail({ asset, onClose, onUse, onRemove }: { asset: StudioAsset; onClose: () => void; onUse: () => void; onRemove: () => void }) {
  const [busy, setBusy] = useState(false);
  return (
    <div aria-hidden="true" className="asset-detail-overlay open" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <section className="asset-detail-panel">
        <div className="panel-head"><div><p>Library asset</p><h2>{asset.name || "Asset"}</h2></div><button aria-label="Close asset details" className="panel-close" onClick={onClose}>×</button></div>
        <div className={`asset-detail-preview asset-preview ${asset.kind}`} data-mark={(asset.name || "A")[0].toUpperCase()}>
          {asset.previewUrl ? <img src={asset.previewUrl} alt="" loading="lazy" decoding="async" style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} /> : null}
        </div>
        <p className="asset-detail-note">{asset.mimeType || "Reusable production context"} · {fmtSize(asset.sizeBytes)}</p>
        <div className="asset-detail-grid">
          <div className="asset-detail-fact"><span>Type</span><b>{asset.kind === "logo" ? "Brand asset" : asset.kind[0].toUpperCase() + asset.kind.slice(1)}</b></div>
          <div className="asset-detail-fact"><span>Brand</span><b>{asset.kind === "logo" ? "Brand-linked" : "Not linked"}</b></div>
          <div className="asset-detail-fact"><span>Rights</span><b>{asset.rightsAttested ? "Ready to use" : "Unverified"}</b></div>
          <div className="asset-detail-fact"><span>Used</span><b>{asset.sourceProductionId ? "In a production" : "Not used yet"}</b></div>
        </div>
        <div className="asset-actions">
          <button className="primary" onClick={onUse}>Use in new video</button>
        </div>
        <button className="panel-danger" disabled={busy} onClick={async () => { setBusy(true); try { await Promise.resolve(onRemove()); } finally { setBusy(false); } }}>{busy ? "Removing…" : "Remove from reusable Library"}</button>
      </section>
    </div>
  );
}
