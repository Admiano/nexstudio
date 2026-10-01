"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { formatUSD, MindSpark, useStudio, type ContextChip } from "../App";
import { studioApi } from "../api";

export type FlowStage = "mind" | "direction" | "closed" | "production" | "review" | "publish" | "revision";

export interface FlowState {
  stage: FlowStage;
  productionId?: string;
  prompt?: string;
  contexts?: ContextChip[];
  family?: string | null;
  videoType?: string | null;
  duration?: number;
  aspectRatio?: string;
  thesis?: string;
  beats?: Array<{ start: number; end: number; purposeTitle: string; description: string }>;
  quoteId?: string;
  amountMinor?: number;
  error?: string;
}

export interface FlowApi {
  openFlow: (f: FlowState) => void;
  closeFlow: () => void;
  patchFlow: (p: Partial<FlowState>) => void;
  notify: (m: string) => void;
}

const FAMILY_LABEL: Record<string, string> = {
  explainer: "Explainer", EXPLAINER: "Explainer",
  whiteboard: "Whiteboard", WHITEBOARD: "Whiteboard",
  stickman: "Character", STICKMAN: "Character",
  "editorial-motion": "Illustrated Stories", EDITORIAL_MOTION: "Illustrated Stories",
};

const MIND_STEPS = [
  { key: "understand", title: "Understanding the brief", copy: "Bringing your intent, context and production direction together." },
  { key: "shape", title: "Shaping the production direction", copy: "Choosing the family, format and structure before anything is made." },
  { key: "ready", title: "Direction is ready", copy: "Review every part of it — nothing has been produced yet." },
];

const DEFAULT_VIDEO_TYPE: Record<string, string> = {
  explainer: "product-explainer",
  whiteboard: "concept-breakdown",
  stickman: "short-story",
  "editorial-motion": "kinetic-text-story",
  editorial_motion: "kinetic-text-story",
};

export function FlowOverlay({ flow, api }: { flow: FlowState; api: FlowApi }) {
  const { refresh } = useStudio();
  const [mindStep, setMindStep] = useState(0);
  // Mind → real pipeline: recommend → create draft → plan preview → direction
  useEffect(() => {
    if (flow.stage !== "mind" || !flow.prompt) return;
    const brief = flow.prompt;
    let alive = true;
    (async () => {
      setMindStep(0);
      try {
        let family = flow.family;
        let videoType = flow.videoType;
        if (!family || !videoType) {
          try {
            const rec = await studioApi.recommend(brief);
            if (rec.status === "ready") { family = rec.recommendation?.family; videoType = rec.recommendation?.videoType; }
          } catch { /* fall through to defaults */ }
        }
        family = family ?? "explainer";
        if (!alive) return;
        setMindStep(1);
        const sources = (flow.contexts ?? []).filter((c) => c.kind === "file" || c.kind === "reference").map((c) => ({
          kind: c.kind === "file" ? "UPLOAD" as const : "URL" as const,
          label: c.label,
          reference: c.refId,
        }));
        const brandCtx = flow.contexts?.find((c) => c.kind === "brand");
        const draft = await studioApi.createDraft({
          id: crypto.randomUUID(),
          family: (family ?? "explainer").toUpperCase().replace(/-/g, "_"),
          videoType: videoType ?? DEFAULT_VIDEO_TYPE[(family ?? "explainer").toLowerCase()] ?? "product-explainer",
          prompt: brief,
          sources,
          brandContext: brandCtx ? { brandId: brandCtx.refId, name: brandCtx.label } : undefined,
        });
        const productionId = (draft as { id?: string; productionId?: string }).productionId ?? (draft as { id?: string }).id;
        if (!alive) return;
        if (!productionId) { api.patchFlow({ stage: "closed", error: "The draft could not be created." }); return; }
        api.patchFlow({ productionId, family, videoType });
        // plan preview → direction bridge
        try {
          const preview = await studioApi.planPreview(productionId);
          if (!alive) return;
          const p = preview as { status?: string; thesis?: string; recommendedDuration?: number; beats?: FlowState["beats"]; missingInput?: string[] };
          if (p?.status === "ready" || p?.beats) {
            api.patchFlow({ stage: "direction", thesis: p.thesis, beats: p.beats, duration: p.recommendedDuration ?? flow.duration });
          } else {
            api.patchFlow({ stage: "direction" });
          }
        } catch {
          api.patchFlow({ stage: "direction" });
        }
        setMindStep(2);
      } catch (e) {
        if (!alive) return;
        const msg = e instanceof Error ? e.message : "Production could not start.";
        api.patchFlow({ stage: "closed", error: msg });
      }
    })();
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [flow.stage === "mind"]);

  if (flow.stage === "mind") return <MindStage step={mindStep} />;
  if (flow.stage === "closed") return <ClosedStage flow={flow} onClose={api.closeFlow} />;
  if (flow.stage === "direction") return <DirectionStage flow={flow} api={api} />;
  if (flow.stage === "production") return <ProductionStage flow={flow} api={api} />;
  if (flow.stage === "review") return <ReviewStage flow={flow} api={api} refresh={refresh} />;
  if (flow.stage === "publish") return <PublishStage flow={flow} api={api} />;
  if (flow.stage === "revision") return <RevisionStage flow={flow} api={api} />;
  return null;
}

function MindStage({ step }: { step: number }) {
  const s = MIND_STEPS[Math.min(step, MIND_STEPS.length - 1)];
  return (
    <div className="mind-stage open" data-step={s.key} id="mindStage">
      <div className="mind-fragments" />
      <div aria-hidden="true" className="nx-mind-field">
        <div className="nx-field-rail top" /><div className="nx-field-rail right" /><div className="nx-field-rail bottom" /><div className="nx-field-rail left" />
        <div className="nx-field-axis x" /><div className="nx-field-axis y" />
        <div aria-hidden="true" className="nx-field-core nx-presence nx-presence--core" data-mode="matrix" data-state="listening" />
        <div className="nx-field-word w1">CONTEXT</div><div className="nx-field-word w2">DIRECTION</div>
      </div>
      <div className="mind-wrap"><div className="micro">NexMind</div><h2>{s.title}</h2><p>{s.copy}</p><div className="mind-progress">{MIND_STEPS.map((m, i) => <i key={m.key} className={i <= step ? "active" : ""} />)}</div></div>
    </div>
  );
}

function ClosedStage({ flow, onClose }: { flow: FlowState; onClose: () => void }) {
  return (
    <div className="mind-stage open" data-step="understand">
      <div className="mind-wrap">
        <div className="micro">NexStudio</div>
        <h2>Not open for new productions yet.</h2>
        <p>{flow.error || "This production type is being certified before it opens. Your brief is saved as a draft and nothing was charged."}</p>
        <div className="mind-actions"><button className="v2-primary" onClick={onClose}>Back to Create</button></div>
      </div>
    </div>
  );
}

function DirectionStage({ flow, api }: { flow: FlowState; api: FlowApi }) {
  const { balance, refresh } = useStudio();
  const [adjust, setAdjust] = useState("");
  const [busy, setBusy] = useState(false);
  const beats = flow.beats?.length ? flow.beats : DEFAULT_BEATS;
  const costLabel = flow.amountMinor != null ? formatUSD(flow.amountMinor) : "…";

  async function createVideo() {
    if (!flow.productionId) return;
    setBusy(true);
    try {
      const q = await studioApi.quote(flow.productionId) as { quoteId?: string; amountMinor?: number; finalAmountMinor?: number };
      const amount = q.finalAmountMinor ?? q.amountMinor ?? 0;
      api.patchFlow({ quoteId: q.quoteId, amountMinor: amount });
      const bal = balance?.availableMinor ?? 0;
      if (amount > bal) {
        // top-up via funding intent → Stripe checkout
        const need = amount - bal;
        const intent = await studioApi.fundingIntent(Math.max(need, 100)) as { checkoutUrl?: string };
        if (intent.checkoutUrl) { window.location.href = intent.checkoutUrl; return; }
        api.notify("Add funds from the Credits sheet, then try again.");
        return;
      }
      const res = await studioApi.purchase(flow.productionId, q.quoteId!) as { ok?: boolean; code?: string; amountRequiredMinor?: number };
      if (res.ok === false) {
        if (res.code === "INSUFFICIENT_BALANCE") { api.notify("Balance is short — add credits first."); return; }
        api.notify("Production could not start — try again.");
        return;
      }
      await refresh(["balance", "work", "ledger"]);
      api.patchFlow({ stage: "production" });
    } catch (e) {
      api.notify(e instanceof Error ? e.message : "Production could not start.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div aria-hidden="true" className="direction-stage open" id="directionStage">
      <div className="direction-shell">
        <header className="direction-top">
          <button className="direction-back" onClick={api.closeFlow}>← <span className="direction-back-full">Back to brief</span><span className="direction-back-short">Brief</span></button>
          <div className="direction-id"><span className="direction-id-full">NexMind · Creative direction</span><span className="direction-id-short">NexMind</span></div>
          <div className="direction-status"><i /><span>Ready to adjust</span></div>
        </header>
        <main className="direction-content">
          <section className="direction-hero reveal" style={{ ["--d" as string]: ".04s" }}>
            <div className="direction-kicker"><span>Direction ready</span><span>Nothing has been produced yet</span></div>
            <h1>{flow.thesis || "A clear story with a strong visual pulse."}</h1>
            <p>NexMind has shaped a production direction from your brief. You can change any part naturally before credits are used.</p>
            <div className="direction-context">
              {(flow.contexts ?? []).map((c) => <span key={`${c.kind}:${c.refId}`} className="ctx-pill">{c.label}</span>)}
            </div>
          </section>
          <section className="direction-briefline reveal" style={{ ["--d" as string]: ".1s" }}><div><label>Your brief</label><b>{flow.prompt}</b></div><button onClick={api.closeFlow}>Edit brief</button></section>
          <section className="decision-row reveal" style={{ ["--d" as string]: ".16s" }}>
            <div className="decision"><label>Production</label><strong>{FAMILY_LABEL[flow.family ?? ""] ?? flow.family ?? "Explainer"}</strong><span>{flow.family ? "Your selection" : "NexMind selected"}</span></div>
            <div className="decision"><label>Format</label><strong>{flow.aspectRatio ?? "16:9"}</strong><span>{flow.aspectRatio === "9:16" ? "Vertical" : "Landscape"}</span></div>
            <div className="decision"><label>Length</label><strong>{flow.duration ?? 45} sec</strong><span>Target, not a hard cut</span></div>
            <div className="decision"><label>Voice</label><strong>Warm, assured</strong><span>Natural delivery</span></div>
          </section>
          <section className="direction-grid reveal" style={{ ["--d" as string]: ".23s" }}>
            <div className="story-main">
              <div className="story-label"><h2>How the story moves</h2><span>{beats.length} intentional beats</span></div>
              <div className="story-path">
                {beats.map((b, i) => (
                  <article key={i} className="story-beat"><span className="beat-num">{String(i + 1).padStart(2, "0")}</span><div className="beat-copy"><b>{b.purposeTitle}</b><p>{b.description}</p></div><div className={`beat-visual v${(i % 4) + 1}`} /></article>
                ))}
              </div>
            </div>
            <aside className="creative-side">
              <h2>Creative treatment</h2>
              <div className="creative-sticky">
                <div className="direction-preview"><div className="preview-grid" /><div className="preview-orbit" /><div className="preview-type"><small>NexMind treatment</small><b>Clarity with motion.</b></div></div>
                <div className="creative-list">
                  <div className="creative-item"><label>Look</label><b>Editorial, restrained and spatially clean</b></div>
                  <div className="creative-item"><label>Rhythm</label><b>Confident pacing with room for ideas to land</b></div>
                  <div className="creative-item"><label>Sound</label><b>Purposeful voice, subtle texture, no filler</b></div>
                </div>
              </div>
            </aside>
          </section>
        </main>
      </div>
      <div className="direction-dock">
        <div className="quick-adjusts">
          {["Shorter", "More cinematic", "More energetic", "More restrained"].map((label) => (
            <button key={label} onClick={() => setAdjust(`Make it ${label.toLowerCase()}`)}>{label}</button>
          ))}
        </div>
        <div className="direction-dock-inner">
          <div className="adjuster"><span className="spark">✦</span><input value={adjust} onChange={(e) => setAdjust(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") setAdjust(""); }} placeholder="Tell NexMind what to change…" /><button aria-label="Apply direction change" className="adjust-go" onClick={() => setAdjust("")}>↑</button></div>
          <button aria-label="Create video" className="credit-next" disabled={busy} onClick={() => void createVideo()}><span className="full">{busy ? "Starting…" : <>Create video <span className="cost-label">· <b>{costLabel}</b></span></>}</span><span>→</span></button>
        </div>
      </div>
    </div>
  );
}

const DEFAULT_BEATS = [
  { start: 0, end: 10, purposeTitle: "Earn attention immediately", description: "Open on the clearest tension in the brief, not an introduction." },
  { start: 10, end: 20, purposeTitle: "Frame what matters", description: "Give the viewer the minimum context needed to understand the idea." },
  { start: 20, end: 35, purposeTitle: "Make the idea tangible", description: "Use the strongest visual mechanism of the chosen production family." },
  { start: 35, end: 45, purposeTitle: "Land one memorable takeaway", description: "Finish with clarity rather than another layer of explanation." },
];

const PHASE_ORDER = ["PREPARING", "SHAPING_STORY", "VISUAL_DIRECTION", "DIRECTING_FILM", "INTERNAL_REVIEW", "FINAL_PRODUCTION"];

function ProductionStage({ flow, api }: { flow: FlowState; api: FlowApi }) {
  const [proj, setProj] = useState<{ title?: string; detail?: string; phase?: string; status?: string } | null>(null);
  useEffect(() => {
    if (!flow.productionId) return;
    let alive = true;
    const poll = async () => {
      try {
        const w = await studioApi.workflow(flow.productionId!);
        if (!alive) return;
        if (w) setProj(w as typeof proj);
        const status = String((w as { status?: string } | null)?.status ?? "");
        const phase = String((w as { phase?: string } | null)?.phase ?? "");
        if (status === "COMPLETE" || phase === "FINAL_REVIEW") api.patchFlow({ stage: "review" });
      } catch { /* keep polling */ }
    };
    void poll();
    const t = setInterval(poll, 4000);
    return () => { alive = false; clearInterval(t); };
  }, [flow.productionId]); // eslint-disable-line react-hooks/exhaustive-deps

  const idx = Math.max(0, PHASE_ORDER.indexOf(proj?.phase ?? "PREPARING"));
  return (
    <div aria-hidden="true" className="production-stage open" data-phase="story" id="productionStage">
      <header className="production-top">
        <button aria-label="Leave production and keep working" className="production-leave" onClick={api.closeFlow}>← Keep working</button>
        <div className="production-id"><span className="production-live"><i /> In production</span></div>
      </header>
      <main className="production-main">
        <div className="production-copy">
          <div className="micro">NexStudio Studio</div>
          <h1>{proj?.title ?? "Preparing the production."}</h1>
          <p>{proj?.detail ?? "The Studio is checking the approved brief and what the production system can safely make."}</p>
        </div>
        <div className="production-steps">
          {["Story", "Visuals", "Motion", "Sound", "Review"].map((s, i) => <div key={s} className={`pstep ${i <= idx ? "on" : ""}`}><span>{s}</span></div>)}
        </div>
      </main>
    </div>
  );
}

function ReviewStage({ flow, api, refresh }: { flow: FlowState; api: FlowApi; refresh: () => Promise<void> }) {
  const [busy, setBusy] = useState(false);
  async function act(action: "approve" | "revision", note?: string) {
    if (!flow.productionId) return;
    setBusy(true);
    try {
      await studioApi.review(flow.productionId, action === "approve" ? { action: "approve" } : { action: "revision", note: note || "Please revise" });
      await refresh();
      api.notify(action === "approve" ? "Approved — moved to publish." : "Revision queued with NexMind.");
      api.patchFlow({ stage: action === "approve" ? "publish" : "revision" });
    } catch (e) {
      api.notify(e instanceof Error ? e.message : "That action is not available yet.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div aria-hidden="true" className="finished-stage open" id="finishedStage">
      <header className="review-top">
        <button aria-label="Back to Work" className="review-back" onClick={api.closeFlow}>← <span>Work</span></button>
        <div className="review-brand"><span className="mind-spark">✦</span><span className="review-brand-full">NexStudio · Review</span><span className="review-brand-short">Review</span></div>
        <div className="review-state"><i /><span className="review-state-full">Ready for your call</span><span className="review-state-short">Ready</span></div>
      </header>
      <div className="review-wrap">
        <section className="review-canvas">
          <div className="review-video-shell">
            {flow.productionId ? <video className="review-video" controls playsInline src={`/api/v1/productions/${flow.productionId}/output`} poster={`/api/v1/productions/${flow.productionId}/poster`} /> : <div className="review-video" />}
            <span className="review-version-tag">Ready to review</span>
          </div>
        </section>
        <aside className="review-side">
          <div className="micro">NexStudio</div>
          <h1>Your video is ready.</h1>
          <p className="review-meta">Approve it to publish, or send it back to NexMind with a revision note.</p>
          <div className="review-actions">
            <button className="review-primary" disabled={busy} onClick={() => void act("approve")}>Approve & publish →</button>
            <button className="review-revise" disabled={busy} onClick={() => api.patchFlow({ stage: "revision" })}>Revise with NexMind</button>
            <a className="review-download" href={`/api/v1/productions/${flow.productionId}/output`} download>Download MP4</a>
          </div>
          <p className="review-privacy">Publishing hands the files to you — nothing is posted on your behalf.</p>
        </aside>
      </div>
    </div>
  );
}

const DESTINATIONS = ["YouTube", "TikTok", "Instagram", "X", "Threads", "Facebook"];

function PublishStage({ flow, api }: { flow: FlowState; api: FlowApi }) {
  return (
    <div aria-hidden="true" className="publish-overlay open" id="publishOverlay" onClick={(e) => { if (e.target === e.currentTarget) api.closeFlow(); }}>
      <section className="publish-shell" role="dialog" aria-modal="true">
        <div className="sheet-head"><div><div className="micro">Publish · Privacy first</div><h2>Take it everywhere.</h2><p>NexStudio prepares the file and caption for each destination — you keep your own accounts. Nothing is posted on your behalf.</p></div><button aria-label="Close publish" className="sheet-close" onClick={api.closeFlow}>×</button></div>
        <div className="platform-grid">
          {DESTINATIONS.map((d) => (
            <a key={d} className="platform" href={`/api/v1/productions/${flow.productionId}/output`} download>
              <span className="platform-ico">{d.slice(0, 2).toUpperCase()}</span>
              <span><b>{d}</b><span>{d === "YouTube" ? "MP4 + title + description" : "MP4 + caption"}</span></span>
            </a>
          ))}
        </div>
        <div className="publish-detail">
          <div className="publish-specs">
            <div className="publish-spec"><label>Version</label><b>Prepared</b></div>
            <div className="publish-spec"><label>Format</label><b>{flow.aspectRatio ?? "16:9"}</b></div>
            <div className="publish-spec"><label>Cover</label><b>Ready</b></div>
          </div>
        </div>
      </section>
    </div>
  );
}

function RevisionStage({ flow, api }: { flow: FlowState; api: FlowApi }) {
  const [note, setNote] = useState("");
  const [ts, setTs] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit() {
    if (!flow.productionId || !note.trim()) return;
    setBusy(true);
    try {
      await studioApi.review(flow.productionId, { action: "revision", note: note.trim(), timestampSeconds: ts ? Number(ts) : undefined });
      api.notify("Revision queued — NexMind will take another pass.");
      api.patchFlow({ stage: "production" });
    } catch (e) {
      api.notify(e instanceof Error ? e.message : "Revision could not be queued.");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div aria-hidden="true" className="revision-overlay open" id="revisionOverlay" onClick={(e) => { if (e.target === e.currentTarget) api.closeFlow(); }}>
      <section className="revision-shell" role="dialog" aria-modal="true">
        <div className="sheet-head"><div><div className="revision-nexmind-label"><MindSpark /><div className="micro">NexMind · Revision</div></div><h2>What should change?</h2><p>Describe the result you want. NexMind keeps the approved production context and changes only what is necessary.</p></div><button aria-label="Close revision" className="sheet-close" onClick={api.closeFlow}>×</button></div>
        <div className="revision-composer">
          <textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="Make the opening faster and remove the long middle section." />
          <div className="revision-composer-foot"><span>The current version stays available.</span><input inputMode="numeric" value={ts} onChange={(e) => setTs(e.target.value)} placeholder="Timestamp (sec, optional)" /><button className="revision-review-btn" disabled={busy || !note.trim()} onClick={() => void submit()}>{busy ? "Sending…" : "Review change →"}</button></div>
        </div>
      </section>
    </div>
  );
}
