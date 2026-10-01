"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

const FAMILIES = [
  { key: "explainer", name: "Explainer", desc: "Make complex systems instantly understandable without flattening the idea.", art: "explainer" },
  { key: "whiteboard", name: "Whiteboard", desc: "Reason visually in real time so the viewer follows the thinking, not just the answer.", art: "whiteboard" },
  { key: "stickman", name: "Character", desc: "Carry the message through performance, gesture, framing and believable physical intent.", art: "character" },
  { key: "editorial-motion", name: "Illustrated Stories", desc: "Build narrative meaning through typography, illustration, staging and editorial rhythm.", art: "illustrated" },
];

export function PublicSite({ authed }: { authed: boolean }) {
  const router = useRouter();
  const [brief, setBrief] = useState("Make a 30-second launch video for a new agent-payment product. Clear, premium, and built for social.");
  const [demo, setDemo] = useState<"compose" | "thinking" | "direction">("compose");
  const [signIn, setSignIn] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined" && new URLSearchParams(window.location.search).get("signin") === "1") setSignIn(true);
  }, []);

  const enter = () => {
    if (brief.trim()) sessionStorage.setItem("nx.brief", brief);
    if (authed) router.push("/studio"); else setSignIn(true);
  };

  return (
    <div id="publicSite">
      <header className="pw-nav">
        <a aria-label="NexStudio" className="pw-logo" href="#top"><span className="brand-mark"><i /></span><span>NexStudio</span></a>
        <nav aria-label="Public navigation" className="pw-links"><a href="#make">Make</a><a href="#proof">What it makes</a><a href="#nexmind">NexMind</a></nav>
        <div className="pw-actions">
          <button className="pw-ghost" onClick={() => { if (authed) router.push("/studio"); else setSignIn(true); }}>Sign in</button>
          <button className="pw-solid" onClick={enter}>Open Studio</button>
        </div>
      </header>
      <main id="top">
        <section className="pw-wrap pw-hero">
          <div className="pw-hero-main pw-reveal in">
            <div className="pw-kicker"><i /> Creative production, directed by NexMind</div>
            <h1>From brief to <em>finished video.</em></h1>
            <p className="pw-hero-copy">Tell NexMind what you want. Approve the direction. NexStudio makes it, lets you revise it, then download or publish—without turning production into a pile of tools.</p>
            <div className="pw-hero-actions"><button className="pw-solid" onClick={() => document.getElementById("pwBrief")?.focus()}>Make a video →</button><button className="pw-ghost" onClick={() => document.getElementById("make")?.scrollIntoView({ behavior: "smooth" })}>See what it makes</button></div>
            <div className="pw-small-proof"><span>Direction before production</span><span>Card + USDC credits</span><span>Download or publish</span></div>
          </div>
          <div className="pw-live pw-reveal in">
            <div className="pw-demo">
              <div className="pw-demo-top"><div className="pw-demo-brand"><span aria-hidden="true" className="nx-presence nx-presence--mini" data-mode="matrix" data-state="idle" /> NexMind</div><span className="pw-demo-status">{demo === "compose" ? "Waiting for your brief" : demo === "thinking" ? "Shaping the production" : "Direction ready"}</span></div>
              <div className="pw-demo-body">
                {demo === "compose" && (
                  <div className="pw-demo-state">
                    <textarea id="pwBrief" value={brief} onChange={(e) => setBrief(e.target.value)} placeholder="Make a 30-second launch video for a new agent-payment product…" />
                    <div className="pw-demo-chips"><span className="pw-demo-chip">+ Files</span><span className="pw-demo-chip">+ Brand</span><span className="pw-demo-chip">+ Reference</span><span className="pw-demo-chip">+ Series</span></div>
                    <div className="pw-demo-foot"><span>NexMind will show you the direction first.</span><button className="pw-demo-go" onClick={() => { setDemo("thinking"); setTimeout(() => setDemo("direction"), 1400); }}>Ask NexMind <b>→</b></button></div>
                  </div>
                )}
                {demo === "thinking" && (
                  <div className="pw-thinking on"><div><div aria-hidden="true" className="pw-orbit" /><b>Shaping the production</b><small>Brief · format · story · visual language · sound</small></div></div>
                )}
                {demo === "direction" && (
                  <div className="pw-direction on">
                    <div className="pw-dir-label">Here’s what I’d build</div>
                    <h3>A sharp 30-second Illustrated Story with a hard opening and three visual turns.</h3>
                    <div className="pw-dir-meta"><div><span>Treatment</span><b>Illustrated Stories</b></div><div><span>Master</span><b>9:16</b></div><div><span>Length</span><b>30 sec</b></div></div>
                    <div className="pw-dir-beats"><div><i>01</i><span>Open on the friction people already feel.</span></div><div><i>02</i><span>Turn the problem into a visual system.</span></div><div><i>03</i><span>Reveal the product as the clean resolution.</span></div></div>
                    <div className="pw-dir-actions"><button className="accept" onClick={enter}>Use this direction →</button><button className="change" onClick={() => setDemo("compose")}>Change request</button></div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>
        <section className="pw-section" id="make">
          <div className="pw-wrap">
            <div className="pw-section-head pw-reveal"><div><div className="pw-kicker"><i /> Production families</div></div><div><h2>Choose a direction. Or don’t.</h2><p>NexMind can infer the right production treatment from the brief. When you already know what you want, give it a nudge. Either way, you stay in one flow.</p></div></div>
            <div className="pw-families">
              {FAMILIES.map((f, i) => (
                <button key={f.key} aria-label={`Choose ${f.name}`} className="pw-family pw-reveal" data-delay={String(i)} onClick={() => { sessionStorage.setItem("nx.family", f.key); enter(); }}>
                  <div aria-hidden="true" className="pw-family-media"><div className="pw-family-frame"><div className={`family-native family-native-${f.art}`} /></div></div>
                  <div className="pw-family-copy"><b>{f.name}</b><span>{f.desc}</span></div>
                </button>
              ))}
            </div>
          </div>
        </section>
        <section aria-label="Native production intelligence" className="pw-section" id="proof">
          <div className="pw-wrap">
            <div className="pw-proof-grid">
              <article className="pw-proof-card recompose pw-reveal">
                <div className="pw-proof-visual"><div className="recomp-artboard" aria-hidden="true"><div className="recomp-board wide" data-ratio="16:9" /><div className="recomp-board tall" data-ratio="9:16" /><div className="recomp-board square" data-ratio="1:1" /></div></div>
                <div className="pw-proof-copy"><span className="pw-proof-label">Native recomposition</span><h3>Same direction. Different frame.</h3><p>Headline, subject, negative space and supporting copy are deliberately restaged for 16:9, 9:16 and 1:1 instead of cropped from one master.</p></div>
              </article>
              <article className="pw-proof-card production pw-reveal" data-delay="1">
                <div className="pw-proof-visual"><div className="build-artboard" aria-hidden="true"><div className="build-ghost g1" /><div className="build-ghost g2" /><div className="build-ghost g3" /><div className="build-work"><div className="build-preview" /><div className="build-meta"><div className="build-meta-top"><span>Same work</span><b>V3 · Ready</b></div><div className="build-lineage"><span>V1</span><i /><span>V2</span><i /><span>V3</span><i /></div></div></div></div></div>
                <div className="pw-proof-copy"><span className="pw-proof-label">Production, not editing</span><h3>You direct. NexStudio builds.</h3><p>You approve the creative direction, then review the result. Revisions go back through NexMind instead of forcing you into a timeline editor.</p></div>
              </article>
            </div>
          </div>
        </section>
        <section className="pw-section" id="nexmind">
          <div className="pw-wrap">
            <div className="pw-section-head pw-reveal"><div className="pw-kicker"><i /> NexMind intelligence</div><h2>Context becomes creative direction.</h2><p>NexMind reads the brief alongside Brand, Series, references and previous work, then resolves a production direction you can inspect before anything is produced.</p></div>
            <div className="pw-mind-stage pw-reveal">
              <div className="mind-context-stack"><div className="mind-context-label">Context NexMind understands</div>
                <div className="mind-context-card"><div className="mind-context-ico">B</div><div className="mind-context-copy"><b>Brief</b><span>30-second agent-payment launch video</span></div><i className="mind-context-check" /></div>
                <div className="mind-context-card"><div className="mind-context-ico">N</div><div className="mind-context-copy"><b>Brand</b><span>Identity, voice and visual guidance</span></div><i className="mind-context-check" /></div>
                <div className="mind-context-card"><div className="mind-context-ico">S</div><div className="mind-context-copy"><b>Series</b><span>Continuity preserved across episodes</span></div><i className="mind-context-check" /></div>
                <div className="mind-context-card"><div className="mind-context-ico">↗</div><div className="mind-context-copy"><b>Reference</b><span>Links and uploads become production context</span></div><i className="mind-context-check" /></div>
              </div>
              <div className="mind-core-shell"><div className="mind-core-unit"><span aria-hidden="true" className="nx-presence nx-presence--hero" data-mode="fluid" data-state="listening" /><b>NexMind</b><span>resolving the production</span></div><i className="mind-core-arrow" /></div>
              <div className="mind-direction-card"><div className="mind-direction-label">Creative direction</div><h3>Start with the friction. Make the mechanism visible.</h3><div className="mind-direction-meta"><span>Illustrated Stories</span><span>30 sec</span><span>9:16</span></div><div className="mind-decision"><label>Opening</label><b>Lead with the problem people already feel.</b></div><div className="mind-decision"><label>Treatment</label><b>Editorial type + restrained illustration + one dominant visual system.</b></div><div className="mind-decision"><label>Voice</label><b>Confident, direct, no unnecessary performance.</b></div><div className="mind-direction-ready"><i /> Ready for your approval</div></div>
            </div>
          </div>
        </section>
        <section className="pw-final"><div className="pw-final-inner pw-reveal"><div className="pw-kicker"><i /> NexStudio</div><h2>Make something worth watching.</h2><p>Start with the brief. NexMind will take it from there—and show you the direction before production begins.</p><button className="pw-solid" onClick={enter}>Open NexStudio →</button></div></section>
      </main>
      <footer className="pw-footer"><span>© 2026 NexStudio · Powered by NexMind</span><div className="pw-footer-links"><a href="#make">Make</a><a href="#nexmind">NexMind</a></div></footer>
      {signIn && <SignInSheet onClose={() => setSignIn(false)} />}
    </div>
  );
}

function SignInSheet({ onClose }: { onClose: () => void }) {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  async function submit() {
    if (!email.includes("@")) { setError("Enter a valid email."); return; }
    setBusy(true);
    try {
      const res = await fetch("/api/v1/auth/email/request", {
        method: "POST",
        headers: { "content-type": "application/json", "Idempotency-Key": `nx-signin:${crypto.randomUUID()}` },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) throw new Error("Could not send the sign-in link.");
      setSent(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not send the sign-in link.");
    } finally { setBusy(false); }
  }
  return (
    <div className="overlay open" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="sheet" role="dialog" aria-modal="true">
        <div className="sheet-head"><div><p>Sign in</p><h2>Your Studio is one link away.</h2></div><button aria-label="Close" className="close" onClick={onClose}>×</button></div>
        {sent ? (
          <div className="sent-state"><b>Check your inbox.</b><p>We sent a sign-in link to {email}. It opens your Studio directly.</p></div>
        ) : (
          <>
            <div className="field"><label>Email</label><input autoFocus type="email" value={email} onChange={(e) => setEmail(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") void submit(); }} placeholder="you@company.com" /></div>
            {error && <p className="field-error">{error}</p>}
            <button className="sheet-action" disabled={busy} onClick={() => void submit()}>{busy ? "Sending…" : "Email me a sign-in link"}</button>
          </>
        )}
      </div>
    </div>
  );
}
