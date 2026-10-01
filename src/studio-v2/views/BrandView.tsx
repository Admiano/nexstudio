"use client";

import { useEffect, useMemo, useState } from "react";
import { Eyebrow, route, useStudio } from "../App";
import { studioApi } from "../api";
import type { StudioMemoryItemRecord } from "@/studio-v1/dashboard/domain/creative-memory";
import type { SheetId } from "../overlays/Sheets";

export function BrandView({ openSheet, notify, openSeries }: { openSheet: (s: SheetId) => void; notify: (m: string) => void; openSeries: (id: string) => void }) {
  const { brands, projects, series, refresh } = useStudio();
  const [activeId, setActiveId] = useState<string | null>(null);
  const [memory, setMemory] = useState<StudioMemoryItemRecord[]>([]);
  const [editor, setEditor] = useState<null | { mode: "new" | "identity" | "memory" }>(null);

  const brand = brands.find((b) => b.id === activeId) ?? brands[0] ?? null;

  useEffect(() => {
    if (!brand) { setMemory([]); return; }
    const ctl = new AbortController();
    studioApi.memory("BRAND", brand.id, ctl.signal).then((c) => setMemory(c.memories)).catch(() => setMemory([]));
    return () => ctl.abort();
  }, [brand?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const usedIn = useMemo(() => projects.filter((p) => p.brandId === brand?.id).slice(0, 5), [projects, brand?.id]);
  const linkedSeries = useMemo(() => series.filter((s) => s.brandId === brand?.id), [series, brand?.id]);
  const guidance = memory.find((m) => m.category === "GUIDANCE" || m.key === "guidance");
  const voice = memory.find((m) => m.category === "VOICE" || m.key === "voice");
  const keep: string[] = (guidance?.versions?.[0]?.content?.keep as string[] | undefined) ?? [];
  const avoid: string[] = (guidance?.versions?.[0]?.content?.avoid as string[] | undefined) ?? [];

  async function createBrand(name: string, description: string) {
    try {
      await studioApi.createBrand({ name, description });
      await refresh(["brands"]);
      notify("Brand created.");
      setEditor(null);
    } catch (e) {
      notify(e instanceof Error ? e.message : "Could not create brand.");
    }
  }

  async function teachMemory(content: string) {
    if (!brand) return;
    try {
      await studioApi.memoryWrite({ scope: "BRAND", scopeRefId: brand.id, key: "nexmind-notes", category: "VOICE", label: "NexMind notes", content: { text: content } });
      const c = await studioApi.memory("BRAND", brand.id);
      setMemory(c.memories);
      notify("NexMind will carry that forward.");
      setEditor(null);
    } catch (e) {
      notify(e instanceof Error ? e.message : "Memory could not be saved.");
    }
  }

  if (brands.length === 0) {
    return (
      <div className="brand-v2">
        <div className="v2-page-head">
          <div><Eyebrow>Brand memory</Eyebrow><h1>What NexStudio knows.</h1><p>Your brand is not a settings form. It is reusable production context: identity, voice, visual rules and guidance NexMind carries into every video you attach it to.</p></div>
        </div>
        <div className="library-drop"><span><b>No brands yet.</b> Create one and NexMind starts learning what it should sound and look like.</span><button onClick={() => setEditor({ mode: "new" })}>+ New brand</button></div>
        {editor?.mode === "new" && <BrandEditor mode="new" onClose={() => setEditor(null)} onCreate={createBrand} onTeach={teachMemory} />}
      </div>
    );
  }

  return (
    <div className="brand-v2">
      <div className="v2-page-head">
        <div><Eyebrow>Brand memory</Eyebrow><h1>What NexStudio knows.</h1><p>Your brand is not a settings form. It is reusable production context: identity, voice, visual rules and guidance NexMind carries into every video you attach it to.</p></div>
        <div className="v2-page-actions"><button className="v2-secondary" onClick={() => setEditor({ mode: "new" })}>+ New brand</button><button className="v2-primary" onClick={() => openSheet("brand")}>Use in a video</button></div>
      </div>
      <div className="brand-switcher">
        {brands.map((b) => (
          <button key={b.id} className={`brand-chip ${b.id === brand?.id ? "active" : ""}`} onClick={() => setActiveId(b.id)}>{b.name}</button>
        ))}
      </div>
      <section className="brand-stage">
        <div className="brand-stage-main">
          <span className="brand-stage-label">Production identity</span>
          <div className="brand-lockup"><div className="brand-big-mark">{brand?.name?.[0] ?? "•"}</div><div><h2>{brand?.name}</h2><p>{brand?.description || "Describe what this brand should feel like."}</p></div></div>
          <div className="brand-stage-foot"><span className="brand-ready"><i /> Ready for production</span><button className="text-button" onClick={() => setEditor({ mode: "identity" })}>Edit identity</button></div>
        </div>
        <div className="brand-palette"><div className="palette-stack" /><div className="brand-type-sample"><span>Typography</span><strong>Clear by default.</strong><small>System sans</small></div></div>
      </section>
      <div className="brand-memory-grid">
        <section className="memory-card">
          <div className="memory-card-head"><h3>NexMind’s memory</h3><button className="text-button" onClick={() => setEditor({ mode: "memory" })}>Teach NexMind</button></div>
          <p className="memory-summary">{memory.length > 0 ? `${memory.length} remembered item${memory.length > 1 ? "s" : ""}, kept as append-only versions.` : "Nothing remembered yet — teach NexMind what this brand should know."}</p>
          <div className="memory-confidence">{[0, 1, 2, 3, 4].map((i) => <i key={i} className={i < Math.min(5, memory.length) ? "on" : ""} />)}</div>
          <div className="memory-meta"><span>{memory.length > 0 ? "Working context" : "Empty"}</span><span>{brand?.updatedAt ? `Updated ${new Date(brand.updatedAt).toLocaleDateString()}` : ""}</span></div>
        </section>
        <section className="brand-usage">
          <div className="usage-head"><h3>Recently used</h3><button className="text-button" onClick={() => route("work")}>All work →</button></div>
          <div className="usage-list">
            {usedIn.map((p) => <div key={p.id} className="usage-item"><b>{p.title}</b><span>{p.statusLabel}</span></div>)}
            {usedIn.length === 0 && <div className="usage-item"><span>Not attached to any production yet.</span></div>}
          </div>
          <div className="brand-series-strip"><div className="brand-series-strip-head"><span>Linked series</span></div>
            <div className="brand-series-mini">
              {linkedSeries.map((s) => <button key={s.id} className="series-mini" onClick={() => openSeries(s.id)}>{s.name}</button>)}
              {linkedSeries.length === 0 && <span className="series-mini muted">None yet</span>}
            </div>
          </div>
        </section>
      </div>
      <div className="guidance-row">
        <section className="guide-card"><div className="guide-title"><h3>Keep</h3><span className="guide-dot" /></div><div className="guide-chips">{keep.map((k) => <span key={k} className="chip">{k}</span>)}{keep.length === 0 && <span className="chip muted">Add via Teach NexMind</span>}</div></section>
        <section className="guide-card avoid"><div className="guide-title"><h3>Avoid</h3><span className="guide-dot" /></div><div className="guide-chips">{avoid.map((k) => <span key={k} className="chip">{k}</span>)}{avoid.length === 0 && <span className="chip muted">Add via Teach NexMind</span>}</div></section>
      </div>
      <section className="brand-voice"><label>Voice</label><strong>{(voice?.versions?.[0]?.content?.summary as string | undefined) ?? "Not tuned yet"}</strong><span>{voice ? "NexMind will use this in narration and tone." : "Teach NexMind how the brand should sound."}</span><button className="text-button" onClick={() => setEditor({ mode: "memory" })}>Adjust</button></section>
      {editor && <BrandEditor mode={editor.mode} brand={brand} onClose={() => setEditor(null)} onCreate={createBrand} onTeach={teachMemory} />}
    </div>
  );
}

function BrandEditor({ mode, brand, onClose, onCreate, onTeach }: {
  mode: "new" | "identity" | "memory";
  brand?: { id: string; name: string; description: string | null } | null;
  onClose: () => void;
  onCreate: (name: string, desc: string) => Promise<void>;
  onTeach: (content: string) => Promise<void>;
}) {
  const [name, setName] = useState(brand?.name ?? "");
  const [desc, setDesc] = useState(brand?.description ?? "");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const isMemory = mode === "memory";
  const isNew = mode === "new";
  return (
    <div aria-hidden="true" className="brand-edit-overlay open" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <section className="brand-edit-panel">
        <div className="panel-head"><div><p>Brand memory</p><h2>{isNew ? "New brand" : isMemory ? "Teach NexMind" : "Adjust brand"}</h2></div><button aria-label="Close brand editor" className="panel-close" onClick={onClose}>×</button></div>
        <div id="brandEditFields">
          {isMemory ? (
            <div className="field"><label>Tell NexMind something it should always remember for this brand</label><textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="e.g. Always say 'agent payments', never 'crypto payments'. Avoid jargon." /></div>
          ) : (
            <>
              <div className="field"><label>Name</label><input value={name} onChange={(e) => setName(e.target.value)} placeholder="Brand name" /></div>
              <div className="field"><label>Positioning</label><textarea value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="What does this brand do and how should it feel?" /></div>
            </>
          )}
        </div>
        <button className="panel-save" disabled={busy || (isNew && !name.trim())} onClick={async () => { setBusy(true); try { if (isMemory) await onTeach(note); else await onCreate(name.trim(), desc); } finally { setBusy(false); } }}>{busy ? "Saving…" : "Save"}</button>
      </section>
    </div>
  );
}
