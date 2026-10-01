"use client";

import { useMemo, useRef, useState } from "react";
import { Eyebrow, useStudio } from "../App";
import { studioApi } from "../api";
import type { StudioAsset } from "@/studio-v1/dashboard/domain/assets";
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

function kindOf(a: StudioAsset): LibFilter | "other" {
  const mime = a.mimeType || "";
  if (mime.startsWith("image/")) return "image";
  if (mime.startsWith("video/")) return "video";
  if (mime.startsWith("audio/")) return "audio";
  if (mime.includes("pdf") || mime.includes("document") || mime.includes("text")) return "document";
  return "other";
}

export function LibraryView({ openSheet, notify }: { openSheet: (s: SheetId) => void; notify: (m: string) => void }) {
  const { assets, refresh } = useStudio();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<LibFilter>("all");
  const [detail, setDetail] = useState<StudioAsset | null>(null);
  const [busy, setBusy] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return assets.filter((a) => {
      if (q && !(a.name || "").toLowerCase().includes(q)) return false;
      if (filter === "all") return true;
      if (filter === "brand") return false;
      if (filter === "reference") return false;
      return kindOf(a) === filter;
    });
  }, [assets, search, filter]);

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
        <div className="lib-summary-main"><span>Ready to use</span><strong>Your reusable production material.</strong></div>
        <div className="lib-summary-cell"><span>Assets</span><strong>{assets.length}</strong></div>
        <div className="lib-summary-cell"><span>Brand-linked</span><strong>0</strong></div>
        <div className="lib-summary-cell"><span>Used recently</span><strong>0</strong></div>
      </div>
      <div className="library-controls">
        <div className="library-filters">
          {LIB_FILTERS.map((f) => (
            <button key={f.key} aria-pressed={filter === f.key} className={`lib-filter ${filter === f.key ? "active" : ""}`} onClick={() => setFilter(f.key)}>{f.label}</button>
          ))}
        </div>
        <span className="library-sort">Most recently used first</span>
      </div>
      <div className="library-grid">
        {filtered.map((a) => (
          <button key={a.id} className="lib-card" onClick={() => setDetail(a)}>
            <div className={`lib-thumb kind-${kindOf(a)}`} />
            <div className="lib-meta"><b>{a.name || "Untitled"}</b><span>{a.mimeType || "file"} · {a.status}</span></div>
          </button>
        ))}
        {filtered.length === 0 && <p className="empty-note">No assets match — upload something to get started.</p>}
      </div>
      {detail && <AssetDetail asset={detail} onClose={() => setDetail(null)} />}
    </div>
  );
}

function AssetDetail({ asset, onClose }: { asset: StudioAsset; onClose: () => void }) {
  return (
    <div aria-hidden="true" className="asset-detail-overlay open" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <section className="asset-detail-panel">
        <div className="panel-head"><div><p>Library asset</p><h2>{asset.name || "Asset"}</h2></div><button aria-label="Close asset details" className="panel-close" onClick={onClose}>×</button></div>
        <div className="asset-detail-preview"><div className={`lib-thumb kind-${kindOf(asset)}`} style={{ height: 160 }} /></div>
        <p className="asset-detail-note">Uploaded material is rights-attested and traceable to the productions that use it.</p>
        <div className="asset-detail-grid">
          <div className="asset-detail-fact"><span>Type</span><b>{asset.mimeType || "—"}</b></div>
          <div className="asset-detail-fact"><span>Status</span><b>{asset.status}</b></div>
          <div className="asset-detail-fact"><span>Rights</span><b>Attested</b></div>
          <div className="asset-detail-fact"><span>Added</span><b>{asset.createdAt ? new Date(asset.createdAt).toLocaleDateString() : "—"}</b></div>
        </div>
        <div className="asset-actions"><button className="primary" onClick={onClose}>Use in new video</button></div>
      </section>
    </div>
  );
}
