"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ensureNxPresence } from "./nx-presence";
import { DOCS, type Doc } from "./legal-content";

const SIBLINGS = [
  { slug: "terms", label: "Terms" },
  { slug: "privacy", label: "Privacy" },
  { slug: "faq", label: "FAQ" },
];

export function PublicDoc({ slug }: { slug: keyof typeof DOCS }) {
  const doc: Doc = DOCS[slug];
  const router = useRouter();
  const [authed, setAuthed] = useState(false);
  const [signIn, setSignIn] = useState(false);

  useEffect(() => { ensureNxPresence(); }, []);
  useEffect(() => {
    fetch("/api/v1/account/profile", { credentials: "include" }).then((r) => setAuthed(r.ok)).catch(() => {});
  }, []);

  useEffect(() => {
    const els = Array.from(document.querySelectorAll<HTMLElement>(".pw-reveal:not(.in)"));
    if (!("IntersectionObserver" in window)) { els.forEach((el) => el.classList.add("in")); return; }
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
    }, { threshold: 0.08 });
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);

  return (
    <div id="publicSite">
      <header className="pw-nav">
        <a aria-label="NexStudio" className="pw-logo" href="/"><span className="brand-mark"><i /></span><span>NexStudio</span></a>
        <nav aria-label="Public navigation" className="pw-links">
          <a href="/#make">Make</a><a href="/#proof">What it makes</a><a href="/#nexmind">NexMind</a>
        </nav>
        <div className="pw-actions">
          <button className="pw-ghost" onClick={() => { if (authed) router.push("/studio"); else setSignIn(true); }}>Sign in</button>
          <button className="pw-solid" onClick={() => { if (authed) router.push("/studio"); else setSignIn(true); }}>Open Studio</button>
        </div>
      </header>
      <main>
        <section className="pw-wrap pw-doc-hero pw-reveal in">
          <div className="pw-kicker"><i /> {doc.kicker}</div>
          <h1>{doc.title}</h1>
          <p className="pw-doc-intro">{doc.intro}</p>
          <span className="pw-doc-date">Updated {doc.updated}</span>
        </section>
        <section className="pw-wrap pw-doc">
          <nav className="pw-doc-toc" aria-label="Sections">
            <div className="pw-doc-toc-head">On this page</div>
            {doc.sections.map((s, i) => (
              <a key={s.id} href={`#${s.id}`}><i>{String(i + 1).padStart(2, "0")}</i><span>{s.title}</span></a>
            ))}
          </nav>
          <article className="pw-doc-body">
            {doc.sections.map((s) => (
              <section key={s.id} id={s.id} className="pw-doc-section pw-reveal">
                <h2>{s.title}</h2>
                {s.body.map((p, i) => <p key={i}>{p}</p>)}
              </section>
            ))}
            <div className="pw-doc-siblings">
              {SIBLINGS.filter((x) => x.slug !== doc.slug).map((x) => (
                <a key={x.slug} href={`/${x.slug}`} className="pw-doc-sibling"><span>Also read</span><b>{x.label} →</b></a>
              ))}
            </div>
          </article>
        </section>
        <section className="pw-final"><div className="pw-final-inner"><div className="pw-kicker"><i /> NexStudio</div><h2>Make something worth watching.</h2><p>Start with the brief. NexMind will take it from there, and show you the direction before production begins.</p><button className="pw-solid" onClick={() => { if (authed) router.push("/studio"); else setSignIn(true); }}>Open NexStudio →</button></div></section>
      </main>
      <footer className="pw-footer"><span>© 2026 NexStudio · Powered by NexMind</span><div className="pw-footer-links"><a href="/terms">Terms</a><a href="/privacy">Privacy</a><a href="/faq">FAQ</a></div></footer>
      {signIn && <PublicDocSignIn onClose={() => setSignIn(false)} />}
    </div>
  );
}

function PublicDocSignIn({ onClose }: { onClose: () => void }) {
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
