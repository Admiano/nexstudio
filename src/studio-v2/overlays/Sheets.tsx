"use client";

import { useRef, useState } from "react";
import { Overlay, SheetHead, route, useStudio, type ContextChip } from "../App";
import { studioApi } from "../api";
import type { ComposerState } from "../Shell";

export type SheetId = "files" | "reference" | "brand" | "series";

export function PickerSheets({ open, onClose, composer, addContext, openSeries, notify }: {
  open: SheetId | null;
  onClose: () => void;
  composer: ComposerState;
  addContext: (c: ContextChip) => void;
  openSeries: (id: string | null) => void;
  notify: (m: string) => void;
}) {
  if (!open) return null;
  if (open === "files") return <FilesSheet onClose={onClose} addContext={addContext} notify={notify} />;
  if (open === "reference") return <ReferenceSheet onClose={onClose} addContext={addContext} />;
  if (open === "brand") return <BrandSheet onClose={onClose} addContext={addContext} notify={notify} />;
  if (open === "series") return <SeriesSheet onClose={onClose} addContext={addContext} openSeries={openSeries} notify={notify} />;
  return null;
}

function FilesSheet({ onClose, addContext, notify }: { onClose: () => void; addContext: (c: ContextChip) => void; notify: (m: string) => void }) {
  const ref = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const { refresh } = useStudio();
  async function addFiles(files: FileList | null) {
    if (!files?.length) return;
    setBusy(true);
    try {
      for (const f of Array.from(files)) {
        const a = await studioApi.uploadAsset(f);
        addContext({ kind: "file", refId: a.id, label: f.name, meta: f.type || "file" });
      }
      await refresh(["assets"]);
      onClose();
    } catch (e) {
      notify(e instanceof Error ? e.message : "Upload failed.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <Overlay onClose={onClose}>
      <SheetHead eyebrow="Add context" title="Bring your files in." onClose={onClose} />
      <div className="file-zone" onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); void addFiles(e.dataTransfer.files); }}>
        <input ref={ref} multiple type="file" onChange={(e) => void addFiles(e.target.files)} />
        <b>Drop files here</b>
        <p>Scripts, decks, images, logos, video, audio or documents.</p>
        <button onClick={() => ref.current?.click()} disabled={busy}>{busy ? "Uploading…" : "Choose files"}</button>
      </div>
    </Overlay>
  );
}

function ReferenceSheet({ onClose, addContext }: { onClose: () => void; addContext: (c: ContextChip) => void }) {
  const [url, setUrl] = useState("");
  return (
    <Overlay onClose={onClose}>
      <SheetHead eyebrow="Reference" title="Add something NexMind should understand." onClose={onClose} />
      <div className="field"><label>URL</label><input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://example.com/video-or-page" type="url" /></div>
      <button className="sheet-action" disabled={!url.trim()} onClick={() => { addContext({ kind: "reference", refId: url.trim(), label: url.trim() }); onClose(); }}>Add reference</button>
    </Overlay>
  );
}

function BrandSheet({ onClose, addContext, notify }: { onClose: () => void; addContext: (c: ContextChip) => void; notify: (m: string) => void }) {
  const { brands, refresh } = useStudio();
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  async function create() {
    if (!name.trim()) return;
    setBusy(true);
    try {
      const r = await studioApi.createBrand({ name: name.trim(), description: description.trim() || undefined });
      await refresh(["brands"]);
      const id = (r as { brandId?: string }).brandId;
      if (id) addContext({ kind: "brand", refId: id, label: name.trim() });
      onClose();
    } catch (e) {
      notify(e instanceof Error ? e.message : "Could not create brand.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <Overlay onClose={onClose}>
      <SheetHead eyebrow="Brand" title="Which brand should guide this?" onClose={onClose} />
      <div className="choice-list">
        {brands.map((b) => (
          <button key={b.id} className="choice" onClick={() => { addContext({ kind: "brand", refId: b.id, label: b.name }); onClose(); route("create"); }}>
            <span className="ico">{b.name[0]}</span>
            <span><b>{b.name}</b><span>{b.description || "Identity, voice and visual guidance"}</span></span>
            <span className="arrow">→</span>
          </button>
        ))}
        {brands.length === 0 && <p className="empty-note">No brands yet.</p>}
      </div>
      {creating ? (
        <div className="field">
          <label>Brand name</label>
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Acme Studio" />
          <label style={{ marginTop: 10 }}>Description <span style={{ textTransform: "none", letterSpacing: 0 }}>(optional)</span></label>
          <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="What this brand sounds and looks like" />
          <button className="sheet-action" disabled={busy || !name.trim()} onClick={() => void create()}>{busy ? "Creating…" : "Create brand"}</button>
        </div>
      ) : (
        <div className="series-sheet-foot"><button className="manage" onClick={() => { onClose(); route("brand"); }}>Manage brands</button><button className="new" onClick={() => setCreating(true)}>+ New brand</button></div>
      )}
    </Overlay>
  );
}

function SeriesSheet({ onClose, addContext, openSeries, notify }: { onClose: () => void; addContext: (c: ContextChip) => void; openSeries: (id: string | null) => void; notify: (m: string) => void }) {
  const { series, refresh } = useStudio();
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  async function create() {
    if (!name.trim()) return;
    try {
      await studioApi.createSeries({ name: name.trim() });
      await refresh(["series"]);
      notify("Series created.");
      setCreating(false);
      setName("");
    } catch (e) {
      notify(e instanceof Error ? e.message : "Could not create series.");
    }
  }
  return (
    <Overlay onClose={onClose}>
      <SheetHead eyebrow="Series" title="Continue a series." sub="Choose one. NexMind loads both episode continuity and the production identity that defines how the series looks and sounds." onClose={onClose} />
      <div className="series-choice-list">
        {series.map((s) => (
          <button key={s.id} className="choice" onClick={() => { addContext({ kind: "series", refId: s.id, label: s.name, meta: `${s.episodes?.length ?? 0} episodes` }); onClose(); }}>
            <span className="ico">{s.name[0]}</span>
            <span><b>{s.name}</b><span>{s.description || `${s.episodes?.length ?? 0} episodes`}</span></span>
            <span className="arrow">→</span>
          </button>
        ))}
        {series.length === 0 && <p className="empty-note">No series yet.</p>}
      </div>
      {creating ? (
        <div className="field"><label>Series name</label><input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Weekly explainer" /><button className="sheet-action" onClick={() => void create()}>Create series</button></div>
      ) : (
        <div className="series-sheet-foot"><button className="manage" onClick={() => { onClose(); openSeries(null); }}>Manage series</button><button className="new" onClick={() => setCreating(true)}>+ New series</button></div>
      )}
    </Overlay>
  );
}
