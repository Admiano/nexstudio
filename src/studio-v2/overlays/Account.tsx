"use client";

import { useEffect, useState } from "react";
import { formatUSD, useStudio } from "../App";
import { studioApi } from "../api";

type Section = "profile" | "credits" | "sessions" | "preferences" | "data" | "privacy";

const NAV: Array<{ key: Section; label: string; hint: string; ico: string }> = [
  { key: "profile", label: "Profile", hint: "Identity", ico: "◈" },
  { key: "credits", label: "Credits & billing", hint: "Ledger", ico: "◉" },
  { key: "preferences", label: "Preferences", hint: "Studio", ico: "◧" },
  { key: "sessions", label: "Sign-in sessions", hint: "Security", ico: "▣" },
  { key: "data", label: "Your data", hint: "Export", ico: "⬒" },
  { key: "privacy", label: "Privacy", hint: "Controls", ico: "◐" },
];

const VOICES = [
  { id: "emma", label: "Emma", tag: "US" }, { id: "ava", label: "Ava", tag: "US" },
  { id: "andrew", label: "Andrew", tag: "US" }, { id: "brian", label: "Brian", tag: "US" },
  { id: "sonia", label: "Sonia", tag: "UK" }, { id: "natasha", label: "Natasha", tag: "AU" },
];
const DURATIONS = [30, 45, 60, 90];

interface SessionRow { id: string; current: boolean; userAgent: string | null; lastSeenAt: string; createdAt?: string; }
interface Prefs { notifyRendersEmail: boolean; notifyUpdatesEmail: boolean; defaultVoice: string | null; defaultDuration: number | null; defaultFamily: string | null; paymentMethod: "card" | "usdc"; }

export function initialsOf(name: string | null | undefined, email: string | null | undefined): string {
  const src = (name ?? "").trim() || (email ?? "").split("@")[0];
  const parts = src.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return src.slice(0, 2).toUpperCase() || "NX";
}

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

function Toggle({ on, onChange, disabled }: { on: boolean; onChange: () => void; disabled?: boolean }) {
  return <button type="button" aria-pressed={on} disabled={disabled} className={`account-toggle ${on ? "on" : ""}`} onClick={onChange}><i /></button>;
}

export function AccountSheet({ onClose, notify, profile, onProfile, openCredits }: {
  onClose: () => void;
  notify: (m: string) => void;
  profile: { displayName: string | null; email: string | null } | null;
  onProfile: (p: { displayName: string | null; email: string | null }) => void;
  openCredits: () => void;
}) {
  const [section, setSection] = useState<Section>("profile");
  const { balance, ledger } = useStudio();
  const [sessions, setSessions] = useState<SessionRow[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [exports, setExports] = useState<Array<{ id: string; type: string; status: string; downloadUrl: string | null }>>([]);
  const [busy, setBusy] = useState(false);
  const [name, setName] = useState(profile?.displayName ?? "");
  const [nameDirty, setNameDirty] = useState(false);
  const [prefs, setPrefs] = useState<Prefs | null>(null);
  const [deletion, setDeletion] = useState<"none" | "pending">("none");
  const [devConfirmUrl, setDevConfirmUrl] = useState<string | null>(null);

  useEffect(() => {
    const ctl = new AbortController();
    studioApi.accountSessions(ctl.signal).then((r) => setSessions(r.sessions)).catch(() => {}).finally(() => setSessionsLoading(false));
    studioApi.accountData(ctl.signal).then((r) => setExports(r.items ?? [])).catch(() => setExports([]));
    studioApi.accountPreferences(ctl.signal).then((r) => setPrefs(r.preferences as Prefs)).catch(() => {});
    return () => ctl.abort();
  }, []);

  useEffect(() => { if (!nameDirty) setName(profile?.displayName ?? ""); }, [profile, nameDirty]);

  async function saveName() {
    const v = name.trim();
    if (!v) { notify("Give the account a name first."); return; }
    setBusy(true);
    try {
      const r = await studioApi.updateProfile(v);
      onProfile(r.profile);
      setNameDirty(false);
      notify("Name saved — it signs your work from here.");
    } catch (e) { notify(e instanceof Error ? e.message : "Could not save the name."); }
    finally { setBusy(false); }
  }

  async function patchPrefs(patch: Partial<Prefs>) {
    const next = { ...prefs, ...patch } as Prefs;
    setPrefs(next);
    try { const r = await studioApi.updatePreferences(patch); setPrefs(r.preferences as Prefs); }
    catch (e) { notify(e instanceof Error ? e.message : "Preference could not be saved."); }
  }

  async function revokeSession(id: string) {
    setBusy(true);
    try {
      const r = await studioApi.revokeSession(id);
      if (r.current) { location.href = "/"; return; }
      setSessions((s) => s.filter((x) => x.id !== id));
      notify("That session is signed out.");
    } catch (e) { notify(e instanceof Error ? e.message : "Could not sign out that session."); }
    finally { setBusy(false); }
  }

  async function revokeOthers() {
    setBusy(true);
    try {
      const r = await studioApi.revokeOtherSessions();
      notify(`Signed out of ${r.revoked} other session${r.revoked === 1 ? "" : "s"}.`);
      const s = await studioApi.accountSessions();
      setSessions(s.sessions);
    } catch (e) { notify(e instanceof Error ? e.message : "Could not sign out other sessions."); }
    finally { setBusy(false); }
  }

  async function requestExport() {
    setBusy(true);
    try {
      await studioApi.requestAccountExport();
      notify("Export requested — it will appear here when ready.");
      const r = await studioApi.accountData().catch(() => null);
      if (r) setExports(r.items ?? []);
    } catch (e) { notify(e instanceof Error ? e.message : "Export could not be requested."); }
    finally { setBusy(false); }
  }

  async function requestDeletion() {
    setBusy(true);
    try {
      const r = await studioApi.requestDeletion();
      setDeletion("pending");
      if (r.devConfirmUrl) setDevConfirmUrl(r.devConfirmUrl);
      notify("Confirmation sent — deletion only happens after you confirm from the email.");
    } catch (e) { notify(e instanceof Error ? e.message : "Deletion could not be requested."); }
    finally { setBusy(false); }
  }

  async function cancelDeletion() {
    setBusy(true);
    try {
      await studioApi.cancelDeletion();
      setDeletion("none");
      setDevConfirmUrl(null);
      notify("Deletion request cancelled — your account is safe.");
    } catch (e) { notify(e instanceof Error ? e.message : "Could not cancel the request."); }
    finally { setBusy(false); }
  }

  const otherSessions = sessions.filter((s) => !s.current).length;
  const initials = initialsOf(profile?.displayName, profile?.email);

  return (
    <div className="account-hub open" id="accountHub" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <section className="account-panel" role="dialog" aria-modal="true">
        <div className="account-head">
          <div className="account-head-title"><span className="account-avatar-big">{initials}</span><div><h2>Your account.</h2><p>Sessions, credits, data and privacy</p></div></div>
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
                    <span className="acct-hero-avatar">{initials}</span>
                    <div className="acct-hero-copy">
                      <label>Signed in</label>
                      <b>{profile?.displayName || "Magic-link account"}</b>
                      <span className="acct-hero-sub">{profile?.email ?? "Signed in via magic link — no password stored anywhere."}</span>
                    </div>
                    <span className="acct-pill">Email verified</span>
                  </div>
                  <div className="acct-field-row">
                    <div className="account-field acct-field-grow">
                      <label>Display name</label>
                      <input value={name} placeholder="What should NexStudio call you?" onChange={(e) => { setName(e.target.value); setNameDirty(true); }} onKeyDown={(e) => { if (e.key === "Enter") void saveName(); }} />
                    </div>
                    <button className="account-secondary acct-field-btn" disabled={busy || !nameDirty || !name.trim()} onClick={() => void saveName()}>Save</button>
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
                  <button className="account-primary acct-topup" onClick={openCredits}>Top up balance →</button>
                  <div className="acct-list-head"><b>Payment methods</b><span>chosen at checkout</span></div>
                  <div className="acct-methods">
                    <button className={`acct-method ${prefs?.paymentMethod !== "usdc" ? "on" : ""}`} onClick={() => void patchPrefs({ paymentMethod: "card" })}>
                      <span className="acct-method-ico">▭</span>
                      <span className="acct-method-copy"><b>Credit or debit card</b><span>Secure card checkout — Visa, Mastercard, Amex.</span></span>
                      <span className="acct-method-check">✓</span>
                    </button>
                    <button className={`acct-method ${prefs?.paymentMethod === "usdc" ? "on" : ""}`} onClick={() => void patchPrefs({ paymentMethod: "usdc" })}>
                      <span className="acct-method-ico usd">◈</span>
                      <span className="acct-method-copy"><b>USDC</b><span>Stablecoin payment — settles in USD credits.</span></span>
                      <span className="acct-method-check">✓</span>
                    </button>
                  </div>
                  <div className="acct-list-head"><b>Ledger</b><span>{ledger.length} movement{ledger.length === 1 ? "" : "s"}</span></div>
                  <div className="account-ledger">
                    {ledger.map((e) => (
                      <div key={e.id} className="acct-ledger-row">
                        <span className={`acct-ledger-dot ${e.amountMinor >= 0 ? "in" : "out"}`} aria-hidden="true" />
                        <div className="acct-ledger-copy"><b>{e.description || e.type}</b><span>{e.status} · {new Date(e.createdAt).toLocaleDateString()} · {e.id.slice(0, 8)}</span></div>
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

              {section === "preferences" && (
                <>
                  <p className="account-lead">Set once — the studio prefills every new production with these.</p>
                  <div className="acct-list-head"><b>Notifications</b><span>email</span></div>
                  <div className="settings-card acct-set-card">
                    <div className="preference-row">
                      <div><b>When a render finishes</b><span>An email the moment a video is ready to review — the reason to come back.</span></div>
                      <Toggle on={prefs?.notifyRendersEmail ?? true} disabled={!prefs} onChange={() => void patchPrefs({ notifyRendersEmail: !prefs?.notifyRendersEmail })} />
                    </div>
                    <div className="preference-row">
                      <div><b>Product updates</b><span>New families, voices and styles as they land. Occasional, never noisy.</span></div>
                      <Toggle on={prefs?.notifyUpdatesEmail ?? false} disabled={!prefs} onChange={() => void patchPrefs({ notifyUpdatesEmail: !prefs?.notifyUpdatesEmail })} />
                    </div>
                  </div>
                  <div className="acct-list-head"><b>Studio defaults</b><span>prefill the composer</span></div>
                  <div className="settings-card acct-set-card">
                    <div className="preference-row pref-col">
                      <div><b>Default voice</b><span>Preselected in Voice &amp; pacing until you pick another.</span></div>
                      <div className="acct-chip-row">
                        {VOICES.map((v) => (
                          <button key={v.id} className={`opt-chip small ${prefs?.defaultVoice === v.id ? "on" : ""}`} disabled={!prefs} onClick={() => void patchPrefs({ defaultVoice: prefs?.defaultVoice === v.id ? null : v.id })}><b>{v.label}</b></button>
                        ))}
                      </div>
                    </div>
                    <div className="preference-row pref-col">
                      <div><b>Default length</b><span>Starting duration on every new direction — adjustable per video.</span></div>
                      <div className="acct-chip-row">
                        {DURATIONS.map((d) => (
                          <button key={d} className={`opt-chip small ${prefs?.defaultDuration === d ? "on" : ""}`} disabled={!prefs} onClick={() => void patchPrefs({ defaultDuration: prefs?.defaultDuration === d ? null : d })}><b>{d}s</b></button>
                        ))}
                      </div>
                    </div>
                    <div className="preference-row pref-col">
                      <div><b>Default family</b><span>Which production type a fresh brief opens with.</span></div>
                      <div className="acct-chip-row">
                        <button className={`opt-chip small ${prefs?.defaultFamily === "explainer" ? "on" : ""}`} disabled={!prefs} onClick={() => void patchPrefs({ defaultFamily: prefs?.defaultFamily === "explainer" ? null : "explainer" })}><b>Explainer</b></button>
                        <button className={`opt-chip small ${prefs?.defaultFamily === "whiteboard" ? "on" : ""}`} disabled={!prefs} onClick={() => void patchPrefs({ defaultFamily: prefs?.defaultFamily === "whiteboard" ? null : "whiteboard" })}><b>Whiteboard</b></button>
                      </div>
                    </div>
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
                          <span>{s.createdAt ? `Signed in ${new Date(s.createdAt).toLocaleDateString()} · ` : ""}Last seen {new Date(s.lastSeenAt).toLocaleString()}</span>
                        </div>
                        {s.current
                          ? <span className="acct-pill ok">current</span>
                          : <button className="acct-revoke" disabled={busy} onClick={() => void revokeSession(s.id)}>Revoke</button>}
                      </div>
                    ))}
                    {sessionsLoading && [0, 1].map((i) => (
                      <div key={i} className="acct-session work-sk" aria-hidden="true" style={{ pointerEvents: "none" }}>
                        <div className="sk-block" style={{ width: 34, height: 34, borderRadius: 10 }} />
                        <div style={{ flex: 1, minWidth: 0 }}><div className="sk-line sk-md" /><div className="sk-line sk-sm sk-gap" /></div>
                      </div>
                    ))}
                    {!sessionsLoading && sessions.length === 0 && (
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
                      <span>Removes productions, memory and billing history permanently. We email a confirmation link — nothing is deleted until you confirm. Export your data first.</span>
                      {devConfirmUrl && <a className="acct-dev-link" href={devConfirmUrl}>Confirm deletion (preview link) →</a>}
                    </div>
                    {deletion === "pending"
                      ? <button className="acct-danger-cancel" disabled={busy} onClick={() => void cancelDeletion()}>Cancel request</button>
                      : <button className="acct-danger-btn" disabled={busy} onClick={() => void requestDeletion()}>Request deletion</button>}
                  </div>
                  {deletion === "pending" && <p className="acct-danger-note">Confirmation link sent{profile?.email ? ` to ${profile.email}` : ""} — the account stays active until you confirm it.</p>}
                </>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
