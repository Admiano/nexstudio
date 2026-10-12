"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

/**
 * Shared public-site chrome: the same header, footer and sign-in sheet used by
 * the landing page and every public page (pricing, faq, ...). Keep the menu in
 * one place so it never drifts between pages.
 *
 * linkBase prefixes the section anchors ("#make" on the homepage itself,
 * "/#make" from other public pages).
 */
export function PublicHeader({
  authed,
  googleAuth,
  linkBase = "",
  onEnter,
  onSignIn,
}: {
  authed: boolean;
  googleAuth?: boolean;
  linkBase?: string;
  onEnter?: () => void;
  onSignIn?: () => void;
}) {
  const router = useRouter();
  const [signIn, setSignIn] = useState(false);
  const open = () => {
    if (authed) router.push("/studio");
    else setSignIn(true);
  };
  const enter = onEnter ?? open;
  const signInAction = onSignIn ?? open;
  return (
    <>
      <header className="pw-nav">
        <a aria-label="NexStudio" className="pw-logo" href={`${linkBase}#top`}><span className="brand-mark"><i /></span><span>NexStudio</span></a>
        <nav aria-label="Public navigation" className="pw-links"><a href={`${linkBase}#make`}>Make</a><a href={`${linkBase}#proof`}>What it makes</a><a href={`${linkBase}#nexmind`}>NexMind</a><a href="/pricing">Pricing</a></nav>
        <div className="pw-actions">
          <button className="pw-ghost" onClick={signInAction}>Sign in</button>
          <button className="pw-solid" onClick={enter}>Open Studio</button>
        </div>
      </header>
      {signIn && <SignInSheet googleAuth={googleAuth} onClose={() => setSignIn(false)} />}
    </>
  );
}

export function PublicFooter({ linkBase = "" }: { linkBase?: string }) {
  return (
    <footer className="pw-footer"><span>© 2026 NexStudio · Powered by NexMind</span><div className="pw-footer-links"><a href={`${linkBase}#make`}>Make</a><a href={`${linkBase}#nexmind`}>NexMind</a><a href="/terms">Terms</a><a href="/privacy">Privacy</a><a href="/faq">FAQ</a></div></footer>
  );
}

export function SignInSheet({ onClose, googleAuth }: { onClose: () => void; googleAuth?: boolean }) {
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
      if (!res.ok) throw new Error("The sign-in link couldn't be sent. Try again.");
      setSent(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't send the sign-in link.");
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
            {googleAuth && <>
              <button className="sheet-action sheet-google" onClick={() => { window.location.href = "/api/v1/auth/google/start"; }}>
                <svg aria-hidden="true" viewBox="0 0 18 18" width="16" height="16"><path fill="#4285F4" d="M17.6 9.2c0-.6-.1-1.2-.2-1.8H9v3.4h4.8c-.2 1.1-.8 2-1.8 2.7v2.2h2.9c1.7-1.6 2.7-3.9 2.7-6.5z"/><path fill="#34A853" d="M9 18c2.4 0 4.5-.8 6-2.2l-2.9-2.2c-.8.5-1.9.9-3.1.9-2.4 0-4.4-1.6-5.1-3.8H.9v2.3C2.3 16 5.4 18 9 18z"/><path fill="#FBBC05" d="M3.9 10.7c-.2-.6-.3-1.2-.3-1.7s.1-1.2.3-1.7V5H.9C.3 6.2 0 7.6 0 9s.3 2.8.9 4l3-2.3z"/><path fill="#EA4335" d="M9 3.6c1.3 0 2.5.5 3.4 1.3L15 2.3C13.5.9 11.4 0 9 0 5.4 0 2.3 2 .9 5l3 2.3c.7-2.2 2.7-3.7 5.1-3.7z"/></svg>
                Continue with Google
              </button>
              <div className="sheet-divider"><span>or</span></div>
            </>}
            <div className="field"><label>Email</label><input autoFocus={!googleAuth} type="email" value={email} onChange={(e) => setEmail(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") void submit(); }} placeholder="you@company.com" /></div>
            {error && <p className="field-error">{error}</p>}
            <button className="sheet-action" disabled={busy} onClick={() => void submit()}>{busy ? "Sending…" : "Email me a sign-in link"}</button>
            <p className="sheet-legal">By continuing you agree to the <a href="/terms">Terms</a> and <a href="/privacy">Privacy Policy</a>.</p>
          </>
        )}
      </div>
    </div>
  );
}
