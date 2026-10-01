"use client";

import { useEffect, useState } from "react";
import { formatUSD, useStudio } from "../App";
import { studioApi } from "../api";

type Section = "profile" | "credits" | "sessions" | "data" | "privacy";

const NAV: Array<{ key: Section; label: string; hint: string }> = [
  { key: "profile", label: "Profile", hint: "Identity" },
  { key: "credits", label: "Credits & billing", hint: "Ledger" },
  { key: "sessions", label: "Sign-in sessions", hint: "Security" },
  { key: "data", label: "Your data", hint: "Export" },
  { key: "privacy", label: "Privacy", hint: "Controls" },
];

interface SessionRow { id: string; current: boolean; userAgent: string | null; lastSeenAt: string; }

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
              <button key={n.key} className={`account-tab ${section === n.key ? "active" : ""}`} onClick={() => setSection(n.key)}>{n.label}<small>{n.hint}</small></button>
            ))}
            <button className="account-tab account-signout" onClick={async () => { try { await studioApi.signOut(); location.href = "/"; } catch { notify("Could not sign out."); } }}>Sign out</button>
          </nav>
          <div className="account-content">
            <div className="account-section active">
              <div className="account-kicker">{NAV.find((n) => n.key === section)?.hint}</div>
              <h1>{NAV.find((n) => n.key === section)?.label}</h1>
              {section === "profile" && (
                <>
                  <p className="account-lead">NexStudio uses email links — no password to leak. Your productions, memory and library are attached to this account.</p>
                  <div className="account-card"><div className="account-field"><label>Sign-in email</label><input readOnly value="Signed in via magic link" /></div></div>
                </>
              )}
              {section === "credits" && (
                <>
                  <p className="account-lead">Credits fund productions and paid revisions. The ledger is the record of every movement.</p>
                  <div className="account-card"><b>{balance ? formatUSD(balance.availableMinor) : "—"}</b><span>{balance && balance.pendingMinor > 0 ? `${formatUSD(balance.pendingMinor)} pending` : "Available now"}</span></div>
                  <div className="account-ledger">
                    {ledger.map((e) => (
                      <div key={e.id} className="account-ledger-row"><div><b>{e.description || e.type}</b><span>{e.status} · {new Date(e.createdAt).toLocaleDateString()}</span></div><strong>{formatUSD(e.amountMinor)}</strong></div>
                    ))}
                    {ledger.length === 0 && <p className="account-empty">No transactions yet.</p>}
                  </div>
                </>
              )}
              {section === "sessions" && (
                <>
                  <p className="account-lead">Every place this account is signed in. Sign out anywhere else instantly.</p>
                  <div className="account-card-grid">
                    {sessions.map((s) => (
                      <div key={s.id} className="account-card"><b>{s.current ? "This device" : (s.userAgent || "Another sign-in")}</b><span>Last seen {new Date(s.lastSeenAt).toLocaleString()}</span>{s.current ? <em>current</em> : null}</div>
                    ))}
                    {sessions.length === 0 && <p className="account-empty">No other sessions.</p>}
                  </div>
                  <button className="account-secondary" disabled={busy} onClick={() => void revokeOthers()}>Sign out everywhere else</button>
                </>
              )}
              {section === "data" && (
                <>
                  <p className="account-lead">Everything NexStudio holds for you — productions, memory, assets, billing — exportable as a full archive.</p>
                  <button className="account-primary" disabled={busy} onClick={() => void requestExport()}>Request a full export</button>
                  <div className="account-card-grid">
                    {exports.map((x) => (
                      <div key={x.id} className="account-card"><b>{x.type}</b><span>{x.status}</span>{x.downloadUrl ? <a className="account-secondary" href={x.downloadUrl}>Download</a> : null}</div>
                    ))}
                  </div>
                </>
              )}
              {section === "privacy" && (
                <>
                  <p className="account-lead">NexStudio keeps production memory append-only and inspectable — you can see every remembered fact and tombstone it. Publishing hands files to you; it never posts on your behalf.</p>
                  <div className="account-card"><b>Deleting the account</b><span>Removes productions, memory and billing history permanently.</span></div>
                </>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
