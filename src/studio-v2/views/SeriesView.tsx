"use client";

import { useEffect, useMemo, useState } from "react";
import { Eyebrow, route, useStudio } from "../App";
import { studioApi } from "../api";
import type { StudioMemoryItemRecord } from "@/studio-v1/dashboard/domain/creative-memory";
import type { SheetId } from "../overlays/Sheets";

export function SeriesView({ focusId, openSheet, notify, onOpenHistory }: { focusId: string | null; openSheet: (s: SheetId) => void; notify: (m: string) => void; onOpenHistory: (id: string) => void }) {
  const { series, brands, refresh } = useStudio();
  const [activeId, setActiveId] = useState<string | null>(focusId);
  const [memory, setMemory] = useState<StudioMemoryItemRecord[]>([]);
  const [editor, setEditor] = useState<null | { mode: "new" | "continuity" | "identity" }>(null);
  const [epLayout, setEpLayout] = useState<"list" | "tiles">("list");

  useEffect(() => { if (focusId) setActiveId(focusId); }, [focusId]);

  const current = series.find((s) => s.id === activeId) ?? series[0] ?? null;
  const linkedBrand = current?.brandId ? brands.find((b) => b.id === current.brandId) : null;
  const episodes = useMemo(() => [...(current?.episodes ?? [])].sort((a, b) => b.episodeOrdinal - a.episodeOrdinal), [current]);

  useEffect(() => {
    if (!current) { setMemory([]); return; }
    const ctl = new AbortController();
    studioApi.memory("SERIES", current.id, ctl.signal).then((c) => setMemory(c.memories)).catch(() => setMemory([]));
    return () => ctl.abort();
  }, [current?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const nextOrdinal = (episodes[0]?.episodeOrdinal ?? 0) + 1;
  const continuity = memory.find((m) => m.category === "CONTINUITY" || m.key === "continuity");
  const rules = memory.find((m) => m.key === "rules" || m.category === "GUIDANCE");
  const continuityText = (continuity?.versions?.[0]?.content?.text as string | undefined)
    ?? current?.description ?? "Continuity is attached to every episode.";

  async function createSeries(name: string, description: string) {
    try {
      await studioApi.createSeries({ name, description });
      await refresh(["series"]);
      notify("Series created.");
      setEditor(null);
    } catch (e) {
      notify(e instanceof Error ? e.message : "Could not create series.");
    }
  }

  async function teachContinuity(text: string) {
    if (!current) return;
    try {
      await studioApi.memoryWrite({ scope: "SERIES", scopeRefId: current.id, key: "continuity", category: "CONTINUITY", label: "Series continuity", content: { text } });
      const c = await studioApi.memory("SERIES", current.id);
      setMemory(c.memories);
      notify("Continuity updated for future episodes.");
      setEditor(null);
    } catch (e) {
      notify(e instanceof Error ? e.message : "Memory could not be saved.");
    }
  }

  async function makeNextEpisode() {
    if (!current) return;
    try {
      await studioApi.nextEpisode(current.id, { family: "EXPLAINER", videoType: "explainer-standard", prompt: `Next episode of ${current.name}` });
      notify("Next episode requested.");
    } catch (e) {
      notify(e instanceof Error ? e.message : "Productions are not open yet.");
    }
  }

  if (series.length === 0) {
    return (
      <div className="series-v2">
        <button className="series-back" onClick={() => route("work")}>← Back to Work</button>
        <div className="series-head"><div><Eyebrow>Series continuity</Eyebrow><h1>Series</h1><p>A continuing body of work with memory attached.</p></div><div className="series-head-actions"><button className="primary" onClick={() => setEditor({ mode: "new" })}>+ New series</button></div></div>
        <div className="library-drop"><span><b>No series yet.</b> Create one to give a body of work its own memory and identity.</span><button onClick={() => setEditor({ mode: "new" })}>+ New series</button></div>
        {editor && <SeriesEditor mode={editor.mode} onClose={() => setEditor(null)} onCreate={createSeries} onTeach={teachContinuity} />}
      </div>
    );
  }

  return (
    <div className="series-v2">
      <button className="series-back" onClick={() => route("work")}>← Back to Work</button>
      <div className="series-head">
        <div><Eyebrow>Series continuity</Eyebrow><h1>{current?.name ?? "Series"}</h1><p>{current?.description || "A continuing body of work with memory attached."}</p></div>
        <div className="series-head-actions"><button className="secondary" onClick={() => setEditor({ mode: "new" })}>+ New series</button><button className="primary" onClick={() => void makeNextEpisode()}>Make next episode</button></div>
      </div>
      <div className="series-switcher">
        {series.map((s) => <button key={s.id} aria-pressed={s.id === current?.id} className={`series-switch ${s.id === current?.id ? "active" : ""}`} onClick={() => setActiveId(s.id)}>{s.name}</button>)}
      </div>
      <section className="series-stage">
        <div className="series-stage-main">
          <span className="series-stage-label">Series identity</span>
          <h2>{current?.name}</h2>
          <p className="series-premise">{current?.description || "Define the premise once — every episode inherits it."}</p>
          <div className="series-stage-meta"><span>{episodes.length} episode{episodes.length === 1 ? "" : "s"}</span>{linkedBrand ? <span>Brand · {linkedBrand.name}</span> : null}</div>
        </div>
        <aside className="series-next-card">
          <div><span>Next production</span><strong>Episode {String(nextOrdinal).padStart(2, "0")}</strong><p>NexMind will carry the continuity forward automatically.</p></div>
          <button onClick={() => void makeNextEpisode()}>Make next episode →</button>
        </aside>
      </section>
      <section className="series-production-identity">
        <div className="series-pi-head">
          <div className="series-pi-head-copy"><span>Production identity</span><h3>How this series appears every time.</h3><p>Loaded with continuity in Create, so each episode starts from the established production language.</p></div>
          <button className="series-pi-edit" onClick={() => setEditor({ mode: "identity" })}>Adjust identity →</button>
        </div>
        <div className="series-pi-body"><div className="series-pi-preview" /><div className="series-pi-specs"><div className="pi-spec"><span>System</span><b>Explainer</b></div><div className="pi-spec"><span>Frame</span><b>16:9</b></div></div></div>
      </section>
      <div className="series-memory-grid">
        <section className="series-memory-card">
          <div className="series-card-head"><h3>NexMind continuity memory</h3><button onClick={() => setEditor({ mode: "continuity" })}>Teach NexMind</button></div>
          <p>{continuityText}</p>
          <div className="series-memory-source"><i /><span>Continuity is attached to every episode.</span></div>
        </section>
        <section className="series-brand-card">
          <div className="series-card-head"><h3>Linked Brand</h3><button onClick={() => setEditor({ mode: "identity" })}>Change</button></div>
          <div className="series-brand-lock">{linkedBrand ? <><span className="mark">{linkedBrand.name[0]}</span><span><b>{linkedBrand.name}</b><span>{linkedBrand.description || "Production identity"}</span></span></> : <><span className="mark">—</span><span><b>No linked Brand</b><span>Link one from the brand page</span></span></>}</div>
          <p>When a Brand is linked, it joins Create automatically with the Series. Series memory still owns episode-to-episode continuity.</p>
        </section>
      </div>
      <div className="series-rules-grid">
        <section className="series-rule-card"><span className="series-mini-label">Characters</span><h3>Who stays consistent</h3><div className="series-rule-list"><div className="series-empty-rule">Define via continuity memory.</div></div></section>
        <section className="series-rule-card"><span className="series-mini-label">World</span><h3>What remains true</h3><div className="series-rule-list"><div className="series-rule-item"><b>Premise</b><span>{current?.description || "Define via continuity memory."}</span></div></div></section>
        <section className="series-rule-card"><span className="series-mini-label">Rules</span><h3>Production guardrails</h3><div className="series-rule-list"><div className="series-rule-item"><b>{rules ? "Rules active" : "No rules yet"}</b><span>{rules ? "Guardrails are attached to this series." : "Define via continuity memory."}</span></div></div></section>
      </div>
      <section className="series-episodes">
        <div className="series-episodes-head"><h3>Episode history</h3><span>{episodes.length} episode{episodes.length === 1 ? "" : "s"}</span>
          <div className="view-toggle" role="group" aria-label="Layout">
            <button className={epLayout === "list" ? "active" : ""} onClick={() => setEpLayout("list")} aria-pressed={epLayout === "list"}><svg viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h16" /></svg>List</button>
            <button className={epLayout === "tiles" ? "active" : ""} onClick={() => setEpLayout("tiles")} aria-pressed={epLayout === "tiles"}><svg viewBox="0 0 24 24"><rect x="4" y="4" width="7" height="7" rx="1.5" /><rect x="13" y="4" width="7" height="7" rx="1.5" /><rect x="4" y="13" width="7" height="7" rx="1.5" /><rect x="13" y="13" width="7" height="7" rx="1.5" /></svg>Tiles</button>
          </div>
        </div>
        {epLayout === "tiles" ? (
          <div className="episode-tiles">
            {episodes.map((ep, i) => (
              <button key={ep.id} className="episode-tile" onClick={() => onOpenHistory(ep.productionId)}>
                <span className="ep-num">E{String(ep.episodeOrdinal).padStart(2, "0")}</span>
                <b>{ep.title || `Episode ${ep.episodeOrdinal}`}</b>
                <span className="ep-date">{new Date(ep.createdAt).toLocaleDateString()}</span>
              </button>
            ))}
            {episodes.length === 0 && <div className="episode-row"><span className="episode-num">EP <b>01</b></span><div className="episode-copy"><h4>No episode yet</h4><p>Make the first episode and NexMind will begin building continuity from real work.</p></div><div className="episode-status"><b>Ready</b><span>Continuity prepared</span></div><button onClick={() => void makeNextEpisode()}>Create</button></div>}
          </div>
        ) : (
          <div className="episode-list">
            {episodes.map((ep, i) => (
              <div key={ep.id} className={`episode-row${i === 0 ? " latest" : ""}`}>
                <span className="episode-num">EP <b>{String(ep.episodeOrdinal).padStart(2, "0")}</b></span>
                <div className="episode-copy"><h4>{ep.title || `Episode ${ep.episodeOrdinal}`}</h4><p>Series episode</p></div>
                <div className="episode-status"><b>Saved</b><span>{new Date(ep.createdAt).toLocaleDateString()}</span></div>
                <button onClick={() => onOpenHistory(ep.productionId)}>Open</button>
              </div>
            ))}
            {episodes.length === 0 && <div className="episode-row"><span className="episode-num">EP <b>01</b></span><div className="episode-copy"><h4>No episode yet</h4><p>Make the first episode and NexMind will begin building continuity from real work.</p></div><div className="episode-status"><b>Ready</b><span>Continuity prepared</span></div><button onClick={() => void makeNextEpisode()}>Create</button></div>}
          </div>
        )}
      </section>
      {editor && <SeriesEditor mode={editor.mode} series={current} onClose={() => setEditor(null)} onCreate={createSeries} onTeach={teachContinuity} />}
    </div>
  );
}

function SeriesEditor({ mode, series, onClose, onCreate, onTeach }: {
  mode: "new" | "continuity" | "identity";
  series?: { id: string; name: string; description: string | null } | null;
  onClose: () => void;
  onCreate: (name: string, desc: string) => Promise<void>;
  onTeach: (text: string) => Promise<void>;
}) {
  const [name, setName] = useState(series?.name ?? "");
  const [desc, setDesc] = useState(series?.description ?? "");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const isNew = mode === "new";
  const isTeach = mode === "continuity" || mode === "identity";
  return (
    <div aria-hidden="true" className="series-edit-overlay open" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <section className="series-edit-panel">
        <div className="panel-head"><div><p>Series continuity</p><h2>{isNew ? "New series" : isTeach ? "Teach NexMind continuity" : "Edit series"}</h2></div><button aria-label="Close series editor" className="panel-close" onClick={onClose}>×</button></div>
        <div className="series-edit-body"><div className="series-edit-grid">
          {isTeach ? (
            <div className="focus-field"><label>What should stay true from episode to episode?</label><textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="Characters, world rules, recurring segments, tone…" /></div>
          ) : (
            <>
              <div className="focus-field"><label>Name</label><input value={name} onChange={(e) => setName(e.target.value)} placeholder="Series name" /></div>
              <div className="focus-field"><label>Premise</label><textarea value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="What is this series about?" /></div>
            </>
          )}
        </div>
        <button className="series-edit-save" disabled={busy || (isNew && !name.trim())} onClick={async () => { setBusy(true); try { if (isTeach) await onTeach(note); else await onCreate(name.trim(), desc); } finally { setBusy(false); } }}>{busy ? "Saving…" : "Save series"}</button>
        </div>
      </section>
    </div>
  );
}
