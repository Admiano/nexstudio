"use client";

import { useEffect, useMemo, useState } from "react";
import { Eyebrow, route, useStudio } from "../App";
import { studioApi } from "../api";
import type { StudioMemoryItemRecord } from "@/studio-v1/dashboard/domain/creative-memory";
import type { SheetId } from "../overlays/Sheets";

type Authority = {
  palette?: string[];
  typography?: string;
  typeSample?: string;
  positioning?: string;
  voice?: string;
  voiceDetail?: string;
  keep?: string[];
  avoid?: string[];
  memory?: string;
};

const DEFAULT_PALETTE = ["#111612", "#ffb000", "#f4f3ef", "#ffffff"];

function readableOn(hex: string): string {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex.trim());
  if (!m) return "#111612";
  const n = parseInt(m[1], 16);
  const lum = (0.2126 * (n >> 16) + 0.7152 * ((n >> 8) & 255) + 0.0722 * (n & 255)) / 255;
  return lum > 0.55 ? "#1d1400" : "#ffffff";
}

function authorityOf(memory: StudioMemoryItemRecord[]): Authority {
  const item = memory.find((m) => m.key === "brand.authority" || m.category === "BRAND_AUTHORITY");
  const c = (item?.versions?.[0]?.content ?? {}) as Record<string, unknown>;
  const palette = Array.isArray(c.palette)
    ? (c.palette as string[])
    : Object.values((c.palette ?? {}) as Record<string, string>).filter((v) => typeof v === "string");
  const typography = typeof c.typography === "string" ? c.typography : ((c.typography as Record<string, string>)?.family ?? "");
  const typeSample = typeof c.typography === "object" && c.typography ? ((c.typography as Record<string, string>).sample ?? "") : (c.typeSample as string | undefined);
  const voice = typeof c.voice === "string" ? c.voice : ((c.voice as Record<string, string>)?.shorthand ?? "");
  const voiceDetail = typeof c.voice === "object" && c.voice ? ((c.voice as Record<string, string>).detail ?? "") : (c.voiceDetail as string | undefined);
  return {
    palette,
    typography,
    typeSample,
    positioning: c.positioning as string | undefined,
    voice,
    voiceDetail,
    keep: (c.keep as string[] | undefined) ?? (c.must as string[] | undefined),
    avoid: (c.avoid as string[] | undefined) ?? (c.mustNot as string[] | undefined),
    memory: (c.memory as string | undefined) ?? (c.creativeInstructions as string | undefined),
  };
}

const PALETTE_SLOTS = ["ink", "accent", "base", "light"];

function encodeAuthority(a: Authority): Record<string, unknown> {
  const palette: Record<string, string> = {};
  (a.palette ?? DEFAULT_PALETTE).slice(0, 4).forEach((c, i) => { palette[PALETTE_SLOTS[i]] = c; });
  return {
    logos: [],
    palette,
    typography: { family: a.typography ?? "Inter / system sans", sample: a.typeSample ?? "" },
    voice: { shorthand: a.voice ?? "", detail: a.voiceDetail ?? "" },
    must: a.keep ?? [],
    mustNot: a.avoid ?? [],
    assetRefs: [],
    creativeInstructions: a.memory ?? "",
    positioning: a.positioning ?? "",
  };
}

export function BrandView({ openSheet, notify, openSeries, onOpenWork }: {
  openSheet: (s: SheetId) => void;
  notify: (m: string) => void;
  openSeries: (id: string) => void;
  onOpenWork: (id: string) => void;
}) {
  const { brands, projects, series, refresh } = useStudio();
  const [activeId, setActiveId] = useState<string | null>(null);
  const [memory, setMemory] = useState<StudioMemoryItemRecord[]>([]);
  const [editor, setEditor] = useState<null | { mode: "new" | "identity" | "voice" | "memory" }>(null);

  const brand = brands.find((b) => b.id === activeId) ?? brands[0] ?? null;
  const auth = useMemo(() => authorityOf(memory), [memory]);
  const palette = (auth.palette?.length ? auth.palette : DEFAULT_PALETTE).slice(0, 4);
  const accent = palette[1] ?? DEFAULT_PALETTE[1];

  useEffect(() => {
    if (!brand) { setMemory([]); return; }
    const ctl = new AbortController();
    studioApi.memory("BRAND", brand.id, ctl.signal).then((c) => setMemory(c.memories)).catch(() => setMemory([]));
    return () => ctl.abort();
  }, [brand?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const usedIn = useMemo(() => projects.filter((p) => p.brandId === brand?.id).slice(0, 4), [projects, brand?.id]);
  const linkedSeries = useMemo(() => series.filter((s) => s.brandId === brand?.id), [series, brand?.id]);
  const keep = auth.keep ?? [];
  const avoid = auth.avoid ?? [];

  async function writeAuthority(patch: Authority) {
    if (!brand) return;
    const next = encodeAuthority({ ...auth, ...patch });
    await studioApi.memoryWrite({ scope: "BRAND", scopeRefId: brand.id, key: "brand.authority", category: "BRAND_AUTHORITY", label: "Production authority", content: next });
    const c = await studioApi.memory("BRAND", brand.id);
    setMemory(c.memories);
  }

  async function createBrand(input: { name: string; positioning: string; color: string }) {
    try {
      await studioApi.createBrand({
        name: input.name,
        description: input.positioning,
        authority: encodeAuthority({
          palette: ["#111612", input.color, "#f4f3ef", "#ffffff"],
          positioning: input.positioning,
          typography: "Inter / system sans",
          typeSample: "Clear by default.",
          voice: "Natural, confident",
          voiceDetail: "Use clear, human language.",
          keep: ["Clear language"],
          avoid: ["Generic treatment"],
          memory: "NexMind is still learning this brand. Add a few rules and references as you use it.",
        }),
      });
      await refresh(["brands"]);
      notify("Brand created.");
      setEditor(null);
    } catch (e) {
      notify(e instanceof Error ? e.message : "Could not create brand.");
    }
  }

  async function saveIdentity(input: { name: string; positioning: string; typography: string }) {
    if (!brand) return;
    try {
      await studioApi.updateBrand(brand.id, { name: input.name, description: input.positioning });
      await writeAuthority({ positioning: input.positioning, typography: input.typography });
      await refresh(["brands"]);
      notify("Identity updated.");
      setEditor(null);
    } catch (e) {
      notify(e instanceof Error ? e.message : "Could not update the brand.");
    }
  }

  async function saveVoice(input: { voice: string; voiceDetail: string }) {
    try {
      await writeAuthority({ voice: input.voice, voiceDetail: input.voiceDetail });
      notify("Voice saved — NexMind will use it in narration.");
      setEditor(null);
    } catch (e) {
      notify(e instanceof Error ? e.message : "Could not save voice.");
    }
  }

  async function saveMemory(input: { memory: string; keep: string[]; avoid: string[] }) {
    try {
      await writeAuthority({ memory: input.memory, keep: input.keep, avoid: input.avoid });
      notify("NexMind will carry that forward.");
      setEditor(null);
    } catch (e) {
      notify(e instanceof Error ? e.message : "Memory could not be saved.");
    }
  }

  function useInVideo() {
    openSheet("brand");
    route("create");
  }

  if (brands.length === 0) {
    return (
      <div className="brand-v2">
        <div className="v2-page-head">
          <div><Eyebrow>Brand memory</Eyebrow><h1>What NexStudio knows.</h1><p>Your brand is not a settings form. It is reusable production context: identity, voice, visual rules and guidance NexMind carries into every video you attach it to.</p></div>
        </div>
        <div className="library-drop"><span><b>No brands yet.</b> Create one and NexMind starts learning what it should sound and look like.</span><button onClick={() => setEditor({ mode: "new" })}>+ New brand</button></div>
        {editor?.mode === "new" && <BrandEditor mode="new" onClose={() => setEditor(null)} onNew={createBrand} />}
      </div>
    );
  }

  return (
    <div className="brand-v2">
      <div className="v2-page-head">
        <div><Eyebrow>Brand memory</Eyebrow><h1>What NexStudio knows.</h1><p>Your brand is not a settings form. It is reusable production context: identity, voice, visual rules and guidance NexMind carries into every video you attach it to.</p></div>
        <div className="v2-page-actions"><button className="v2-secondary" onClick={() => setEditor({ mode: "new" })}>+ New brand</button><button className="v2-primary" onClick={useInVideo}>Use in a video</button></div>
      </div>
      <div className="brand-switcher">
        {brands.map((b) => {
          const bg = b.id === brand?.id ? accent : "#ffffff";
          return (
            <button key={b.id} aria-pressed={b.id === brand?.id} className={`brand-switch ${b.id === brand?.id ? "active" : ""}`}
              style={{ ["--brand-bg" as string]: accent, ["--brand-fg" as string]: readableOn(accent) }}
              onClick={() => setActiveId(b.id)}>
              <span className="mini-mark" style={{ background: bg === "#ffffff" ? "#111612" : accent, color: bg === "#ffffff" ? "#ffffff" : readableOn(accent) }}>{b.name[0]}</span>
              {b.name}
            </button>
          );
        })}
      </div>
      <section className="brand-stage">
        <div className="brand-stage-main">
          <span className="brand-stage-label">Production identity</span>
          <div className="brand-lockup">
            <div className="brand-big-mark" style={{ background: accent, color: readableOn(accent) }}>{brand?.name?.[0] ?? "•"}</div>
            <div><h2>{brand?.name}</h2><p>{auth.positioning || brand?.description || "Describe what this brand should feel like."}</p></div>
          </div>
          <div className="brand-stage-foot"><span className="brand-ready"><i /> Ready for production</span><button className="text-button" onClick={() => setEditor({ mode: "identity" })}>Edit identity</button></div>
        </div>
        <div className="brand-palette">
          <div className="palette-stack">
            {palette.map((c) => <div key={c} className="palette-swatch" style={{ background: c }}><span>{c.toUpperCase()}</span></div>)}
          </div>
          <div className="brand-type-sample"><span>Typography</span><strong>{auth.typeSample || "Clear by default."}</strong><small>{auth.typography || "Inter / system sans"}</small></div>
        </div>
      </section>
      <div className="brand-memory-grid">
        <section className="memory-card">
          <div className="memory-card-head"><h3>NexMind’s memory</h3><button className="text-button" onClick={() => setEditor({ mode: "memory" })}>Teach NexMind</button></div>
          <p className="memory-summary">{auth.memory || (memory.length > 0 ? `${memory.length} remembered item${memory.length > 1 ? "s" : ""}, kept as append-only versions.` : "Nothing remembered yet — teach NexMind what this brand should know.")}</p>
          <div className="memory-confidence">{[0, 1, 2, 3, 4].map((i) => <i key={i} className={i < Math.min(5, memory.length) ? "on" : ""} />)}</div>
          <div className="memory-meta"><span>{memory.length > 0 ? "Working context" : "Strong working context"}</span><span>{brand?.updatedAt ? `Updated ${new Date(brand.updatedAt).toLocaleDateString()}` : "Updated recently"}</span></div>
        </section>
        <section className="brand-usage">
          <div className="usage-head"><h3>Recently used</h3><button className="text-button" onClick={() => route("work")}>All work →</button></div>
          <div className="usage-list">
            {usedIn.map((p) => (
              <div key={p.id} className="usage-item">
                <span className="usage-thumb" style={{ ["--brand-accent" as string]: accent }} />
                <span><b>{p.title}</b><span>{p.family} · {p.statusLabel}</span></span>
                <button onClick={() => onOpenWork(p.id)}>Open →</button>
              </div>
            ))}
            {usedIn.length === 0 && <div className="usage-empty">Attach this brand in Create and the productions that use it will appear here.</div>}
          </div>
          <div className="brand-series-strip"><div className="brand-series-strip-head"><span>Linked series</span></div>
            <div className="brand-series-mini">
              {linkedSeries.map((s) => <button key={s.id} className="series-mini" onClick={() => openSeries(s.id)}>{s.name}</button>)}
              {linkedSeries.length === 0 && <span className="series-mini" style={{ border: 0, cursor: "default", color: "var(--muted)" }}>None yet</span>}
            </div>
          </div>
        </section>
      </div>
      <div className="guidance-row">
        <section className="guide-card"><div className="guide-title"><h3>Keep</h3><span className="guide-dot" /></div><div className="guide-chips">{keep.map((k) => <span key={k} className="guide-chip">{k}</span>)}{keep.length === 0 && <span className="guide-chip">Add via Teach NexMind</span>}</div></section>
        <section className="guide-card avoid"><div className="guide-title"><h3>Avoid</h3><span className="guide-dot" /></div><div className="guide-chips">{avoid.map((k) => <span key={k} className="guide-chip">{k}</span>)}{avoid.length === 0 && <span className="guide-chip">Add via Teach NexMind</span>}</div></section>
      </div>
      <section className="brand-voice">
        <label>Voice</label>
        <strong>{auth.voice || "Not tuned yet"}</strong>
        <span>{auth.voiceDetail || "Teach NexMind how the brand should sound."}</span>
        <button className="text-button" onClick={() => setEditor({ mode: "voice" })}>Adjust</button>
      </section>
      {editor && (
        <BrandEditor
          mode={editor.mode}
          brand={brand}
          authority={auth}
          onClose={() => setEditor(null)}
          onNew={createBrand}
          onIdentity={saveIdentity}
          onVoice={saveVoice}
          onMemory={saveMemory}
        />
      )}
    </div>
  );
}

function BrandEditor({ mode, brand, authority, onClose, onNew, onIdentity, onVoice, onMemory }: {
  mode: "new" | "identity" | "voice" | "memory";
  brand?: { id: string; name: string; description: string | null } | null;
  authority?: Authority;
  onClose: () => void;
  onNew?: (input: { name: string; positioning: string; color: string }) => Promise<void>;
  onIdentity?: (input: { name: string; positioning: string; typography: string }) => Promise<void>;
  onVoice?: (input: { voice: string; voiceDetail: string }) => Promise<void>;
  onMemory?: (input: { memory: string; keep: string[]; avoid: string[] }) => Promise<void>;
}) {
  const [name, setName] = useState(mode === "new" ? "" : (brand?.name ?? ""));
  const [positioning, setPositioning] = useState(mode === "new" ? "" : (authority?.positioning ?? brand?.description ?? ""));
  const [color, setColor] = useState(authority?.palette?.[1] ?? "#ffb000");
  const [typography, setTypography] = useState(authority?.typography ?? "Inter / system sans");
  const [voice, setVoice] = useState(authority?.voice ?? "");
  const [voiceDetail, setVoiceDetail] = useState(authority?.voiceDetail ?? "");
  const [mem, setMem] = useState(authority?.memory ?? "");
  const [keepText, setKeepText] = useState((authority?.keep ?? []).join("\n"));
  const [avoidText, setAvoidText] = useState((authority?.avoid ?? []).join("\n"));
  const [busy, setBusy] = useState(false);

  const title = mode === "new" ? "Add a brand" : mode === "identity" ? "Edit identity" : mode === "voice" ? "Adjust how it sounds" : "Teach NexMind";
  const eyebrow = mode === "new" ? "New production identity" : mode === "identity" ? "Production identity" : mode === "voice" ? "Voice" : "NexMind memory";

  async function save() {
    setBusy(true);
    try {
      if (mode === "new") await onNew?.({ name: name.trim(), positioning: positioning.trim(), color });
      else if (mode === "identity") await onIdentity?.({ name: name.trim(), positioning: positioning.trim(), typography: typography.trim() });
      else if (mode === "voice") await onVoice?.({ voice: voice.trim(), voiceDetail: voiceDetail.trim() });
      else await onMemory?.({ memory: mem.trim(), keep: keepText.split("\n").map((x) => x.trim()).filter(Boolean), avoid: avoidText.split("\n").map((x) => x.trim()).filter(Boolean) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div aria-hidden="true" className="brand-edit-overlay open" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <section className="brand-edit-panel">
        <div className="panel-head"><div><p>{eyebrow}</p><h2>{title}</h2></div><button aria-label="Close brand editor" className="panel-close" onClick={onClose}>×</button></div>
        <div id="brandEditFields">
          {mode === "new" && (
            <>
              <div className="focus-field"><label>Brand name</label><input value={name} onChange={(e) => setName(e.target.value)} placeholder="Brand name" /></div>
              <div className="focus-field"><label>Positioning</label><input value={positioning} onChange={(e) => setPositioning(e.target.value)} placeholder="One clear sentence" /></div>
              <div className="focus-field"><label>Primary colour</label><input type="color" value={color} onChange={(e) => setColor(e.target.value)} /></div>
            </>
          )}
          {mode === "identity" && (
            <>
              <div className="focus-field"><label>Brand name</label><input value={name} onChange={(e) => setName(e.target.value)} /></div>
              <div className="focus-field"><label>Positioning</label><textarea value={positioning} onChange={(e) => setPositioning(e.target.value)} /></div>
              <div className="focus-field"><label>Typography</label><input value={typography} onChange={(e) => setTypography(e.target.value)} /></div>
            </>
          )}
          {mode === "voice" && (
            <>
              <div className="focus-field"><label>Voice shorthand</label><input value={voice} onChange={(e) => setVoice(e.target.value)} placeholder="e.g. Warm, precise, never salesy" /></div>
              <div className="focus-field"><label>How NexMind should interpret it</label><textarea value={voiceDetail} onChange={(e) => setVoiceDetail(e.target.value)} placeholder="e.g. Short sentences. Confident but never loud. Explain, don't sell." /></div>
            </>
          )}
          {mode === "memory" && (
            <>
              <div className="focus-field"><label>What should NexMind remember?</label><textarea value={mem} onChange={(e) => setMem(e.target.value)} placeholder="e.g. Always say 'agent payments', never 'crypto payments'. Avoid jargon." /></div>
              <div className="focus-field"><label>Keep — one per line</label><textarea value={keepText} onChange={(e) => setKeepText(e.target.value)} /></div>
              <div className="focus-field"><label>Avoid — one per line</label><textarea value={avoidText} onChange={(e) => setAvoidText(e.target.value)} /></div>
            </>
          )}
        </div>
        <button className="panel-save" disabled={busy || (mode !== "memory" && mode !== "voice" && !name.trim())} onClick={() => void save()}>{busy ? "Saving…" : "Save"}</button>
      </section>
    </div>
  );
}
