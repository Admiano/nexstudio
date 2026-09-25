"use client";

import { useEffect, useState } from "react";
import { formatUSD, useStudio } from "../App";
import { studioApi } from "../api";

type Section = "profile" | "credits" | "sessions" | "data" | "privacy";

const NAV: Array<{ key: Section; label: string; hint: string; ico: string }> = [
  { key: "profile", label: "Profile", hint: "Identity", ico: "◈" },
  { key: "credits", label: "Credits & billing", hint: "Ledger", ico: "◉" },
  { key: "sessions", label: "Sign-in sessions", hint: "Security", ico: "▣" },
  { key: "data", label: "Your data", hint: "Export", ico: "⬒" },
  { key: "privacy", label: "Privacy", hint: "Controls", ico: "◐" },
];

interface SessionRow { id: string; current: boolean; userAgent: string | null; lastSeenAt: string; }

function agentLabel(ua: string | null): string {
  if (!ua) return "Another sign-in";
  if (/mobile|iphone|android/i.test(ua)) return "Mobile device";
  if (/macintosh|mac os/i.test(ua)) return "Mac";
  if (/windows/i.test(ua)) return "Windows PC";
  if (/linux/i.test(ua)) return "Linux device";
  return "Another sign-in";
}

function exportStatusLabel(s: string): { text: string; tone: "ready" | "pending" | "failed" } {
  const v = s.toLowerCase();
  if (v === "ready" || v === "complete" || v === "completed") return { text: "Ready", tone: "ready" };
  if (v === "failed" || v === "error") return { text: "Failed", tone: "failed" };
  return { text: "Preparing", tone: "pending" };
}

export function AccountSheet({ onClose, notify }: { onClose: () => void; notify: (m: string) => void }) {
  const [section, setSection] = useState<Section>("profile");
  const { balance, ledger } = useStudio();
  const [sessions, setSessions] = useState<SessionRow[]>([]);
  const [exports, setExports] = useState<Array<{ id: string; type: string; status: string; downloadUrl: string | null }>>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const ctl = new AbortController();
    studioApi.accountSessions(ctl.signal).then((r) => setSessions(r.sessions)).catch(() => {});
    studioApi.accountData(ctl.signal).then((r) => setExports(r.items ?? [])).catch(() => setExports([]));
    return () => ctl.abort();
  }, []);

  async function revokeOthers() {
    setBusy(true);
    try {
      const r = await studioApi.revokeOtherSessions();
      notify(`Signed out of ${r.revoked} other session${r.revoked === 1 ? "" : "s"}.`);
      const s = await studioApi.accountSessions();
      setSessions(s.sessions);
    } catch (e) {
      notify(e instanceof Error ? e.message : "Could not sign out other sessions.");
    } finally { setBusy(false); }
  }

  async function requestExport() {
    setBusy(true);
    try {
      await studioApi.requestAccountExport();
      notify("Export requested — it will appear here when ready.");
      const r = await studioApi.accountData().catch(() => null);
      if (r) setExports(r.items ?? []);
    } catch (e) {
      notify(e instanceof Error ? e.message : "Export could not be requested.");
    } finally { setBusy(false); }
  }

  const otherSessions = sessions.filter((s) => !s.current).length;

  return (
    <div className="account-hub open" id="accountHub" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <section className="account-panel" role="dialog" aria-modal="true">
        <div className="account-head">
          <div className="account-head-title"><span className="account-avatar-big">CM</span><div><h2>Your account.</h2><p>Sessions, credits, data and privacy</p></div></div>
          <button className="account-close" aria-label="Close account" onClick={onClose}>×</button>
        </div>
        <div className="account-body">
          <nav className="account-tabs">
            {NAV.map((n) => (
              <button key={n.key} className={`account-tab ${section === n.key ? "active" : ""}`} onClick={() => setSection(n.key)}>
                <span className="acct-tab-ico">{n.ico}</span><span className="acct-tab-label">{n.label}</span><small>{n.hint}</small>
              </button>
            ))}
            <button className="account-tab account-signout" onClick={async () => { try { await studioApi.signOut(); location.href = "/"; } catch { notify("Could not sign out."); } }}>
              <span className="acct-tab-ico">→</span><span className="acct-tab-label">Sign out</span>
            </button>
          </nav>
          <div className="account-content">
            <div className="account-section active">
              <div className="account-kicker">{NAV.find((n) => n.key === section)?.hint}</div>
              <h1>{NAV.find((n) => n.key === section)?.label}</h1>

              {section === "profile" && (
                <>
                  <p className="account-lead">NexStudio uses email links — no password to leak. Your productions, memory and library are attached to this account.</p>
                  <div className="acct-hero">
                    <span className="acct-hero-avatar">CM</span>
                    <div className="acct-hero-copy">
                      <label>Signed in</label>
                      <b>Magic-link account</b>
                      <span className="acct-hero-sub">Signed in via magic link — no password stored anywhere.</span>
                    </div>
                    <span className="acct-pill">Email verified</span>
                  </div>
                  <div className="acct-facts">
                    <div className="acct-fact"><span className="acct-fact-ico">◈</span><b>No password</b><span>Sign-in links land in your inbox — nothing to forget or leak.</span></div>
                    <div className="acct-fact"><span className="acct-fact-ico">▤</span><b>Work attached</b><span>Every production, brand and asset lives on this account.</span></div>
                    <div className="acct-fact"><span className="acct-fact-ico">◐</span><b>Inspectible memory</b><span>What NexMind remembers is visible to you — and tombstone-able.</span></div>
                  </div>
                </>
              )}

              {section === "credits" && (
                <>
                  <p className="account-lead">Credits fund productions and paid revisions. The ledger is the record of every movement.</p>
                  <div className="acct-balance">
                    <div className="acct-balance-copy">
                      <label>Available balance</label>
                      <b>{balance ? formatUSD(balance.availableMinor) : "—"}</b>
                      {balance && balance.pendingMinor > 0
                        ? <span className="acct-balance-pending">{formatUSD(balance.pendingMinor)} pending — resolves as renders finish</span>
                        : <span className="acct-balance-pending ok">Nothing pending — all credits settled</span>}
                    </div>
                    <span className="acct-balance-mark" aria-hidden="true">◉</span>
                  </div>
                  <div className="acct-list-head"><b>Ledger</b><span>{ledger.length} movement{ledger.length === 1 ? "" : "s"}</span></div>
                  <div className="account-ledger">
                    {ledger.map((e) => (
                      <div key={e.id} className="acct-ledger-row">
                        <span className={`acct-ledger-dot ${e.amountMinor >= 0 ? "in" : "out"}`} aria-hidden="true" />
                        <div className="acct-ledger-copy"><b>{e.description || e.type}</b><span>{e.status} · {new Date(e.createdAt).toLocaleDateString()}</span></div>
                        <strong className={e.amountMinor >= 0 ? "plus" : "minus"}>{e.amountMinor >= 0 ? "+" : ""}{formatUSD(e.amountMinor)}</strong>
                      </div>
                    ))}
                    {ledger.length === 0 && (
                      <div className="acct-empty">
                        <span className="acct-empty-ico">◉</span>
                        <b>No transactions yet.</b>
                        <p>Credits land here the moment you top up or a render settles.</p>
                      </div>
                    )}
                  </div>
                </>
              )}

              {section === "sessions" && (
                <>
                  <p className="account-lead">Every place this account is signed in. Sign out anywhere else instantly.</p>
                  <div className="acct-sessions">
                    {sessions.map((s) => (
                      <div key={s.id} className={`acct-session ${s.current ? "current" : ""}`}>
                        <span className="acct-session-ico">{/mobile|iphone|android/i.test(s.userAgent ?? "") ? "▯" : "▭"}</span>
                        <div className="acct-session-copy">
                          <b>{s.current ? "This device" : agentLabel(s.userAgent)}</b>
                          <span>Last seen {new Date(s.lastSeenAt).toLocaleString()}</span>
                        </div>
                        {s.current ? <span className="acct-pill ok">current</span> : null}
                      </div>
                    ))}
                    {sessions.length === 0 && (
                      <div className="acct-empty"><span className="acct-empty-ico">▣</span><b>No sign-ins found.</b><p>Your sessions will appear here.</p></div>
                    )}
                  </div>
                  <button className="account-secondary" disabled={busy || otherSessions === 0} onClick={() => void revokeOthers()}>
                    {otherSessions > 0 ? `Sign out of ${otherSessions} other session${otherSessions === 1 ? "" : "s"}` : "No other sessions"}
                  </button>
                </>
              )}

              {section === "data" && (
                <>
                  <p className="account-lead">Everything NexStudio holds for you — productions, memory, assets, billing — exportable as a full archive.</p>
                  <div className="acct-export-hero">
                    <span className="acct-export-ico">⬒</span>
                    <div>
                      <b>Full account archive</b>
                      <span>Productions, NexMind memory, library assets and billing history in one download.</span>
                    </div>
                    <button className="account-primary" disabled={busy} onClick={() => void requestExport()}>Request export</button>
                  </div>
                  {exports.length > 0 && (
                    <>
                      <div className="acct-list-head"><b>Requested exports</b><span>{exports.length}</span></div>
                      <div className="acct-exports">
                        {exports.map((x) => {
                          const st = exportStatusLabel(x.status);
                          return (
                            <div key={x.id} className="acct-export">
                              <span className="acct-export-file">⬒</span>
                              <div className="acct-export-copy"><b>{x.type}</b><span>Export archive</span></div>
                              <span className={`acct-pill ${st.tone === "ready" ? "ok" : st.tone === "failed" ? "warn" : ""}`}>{st.text}</span>
                              {x.downloadUrl ? <a className="acct-dl" href={x.downloadUrl}>Download ↓</a> : null}
                            </div>
                          );
                        })}
                      </div>
                    </>
                  )}
                  {exports.length === 0 && (
                    <div className="acct-empty"><span className="acct-empty-ico">⬒</span><b>No exports yet.</b><p>Requested archives appear here with a download link when ready.</p></div>
                  )}
                </>
              )}

              {section === "privacy" && (
                <>
                  <p className="account-lead">NexStudio keeps production memory append-only and inspectable — you can see every remembered fact and tombstone it. Publishing hands files to you; it never posts on your behalf.</p>
                  <div className="acct-facts">
                    <div className="acct-fact"><span className="acct-fact-ico">◐</span><b>Memory you can see</b><span>Everything NexMind remembers is inspectable in Brand and Series.</span></div>
                    <div className="acct-fact"><span className="acct-fact-ico">✕</span><b>Tombstone anything</b><span>Delete a memory and it's gone from every future production.</span></div>
                    <div className="acct-fact"><span className="acct-fact-ico">↗</span><b>You publish, not us</b><span>Files are prepared for you — NexStudio never posts on your behalf.</span></div>
                  </div>
                  <div className="acct-danger">
                    <div className="acct-danger-copy">
                      <b>Deleting the account</b>
                      <span>Removes productions, memory and billing history permanently. Export your data first.</span>
                    </div>
                    <span className="acct-danger-tag">Irreversible</span>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
