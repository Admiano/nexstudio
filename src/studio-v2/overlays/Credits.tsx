"use client";

import { useState } from "react";
import { formatUSD, useStudio } from "../App";
import { studioApi } from "../api";

const PACKS = [
  { label: "$10", minor: 1000, note: "A couple of videos" },
  { label: "$45", minor: 4500, note: "A working month" },
  { label: "$96", minor: 9600, note: "A full season" },
];

export function CreditsSheet({ onClose, notify }: { onClose: () => void; notify: (m: string) => void }) {
  const { balance, ledger, refresh } = useStudio();
  const [pack, setPack] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);

  async function pay() {
    if (!pack) return;
    setBusy(true);
    try {
      const res = await studioApi.fundingIntent(pack) as { checkoutUrl?: string };
      if (res?.checkoutUrl) { window.location.href = res.checkoutUrl; return; }
      notify("Checkout couldn't start. Try again.");
    } catch (e) {
      notify(e instanceof Error ? e.message : "Couldn't start checkout.");
      setBusy(false);
    }
  }

  return (
    <div aria-hidden="true" className="credit-utility open" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <section className="utility-card">
        <div className="utility-head">
          <div><div className="micro">Credits</div><h2>Your balance.</h2><p>Credits are used only when you start meaningful production or approve a paid revision.</p></div>
          <button aria-label="Close credits" className="pay-close" onClick={onClose}>×</button>
        </div>
        <div className="balance-hero">
          <label>Available</label>
          <strong>{balance ? formatUSD(balance.availableMinor) : "···"}</strong>
          <span>{balance && balance.pendingMinor > 0 ? `${formatUSD(balance.pendingMinor)} pending` : "Nothing reserved"}</span>
        </div>
        <div className="pack-label">Add credits</div>
        <div className="packs">
          {PACKS.map((p) => (
            <button key={p.minor} className={`pack ${pack === p.minor ? "selected" : ""}`} onClick={() => setPack(p.minor)}>
              <b>{p.label}</b><span>{p.note}</span>
            </button>
          ))}
        </div>
        <button className="utility-add" disabled={!pack || busy} onClick={() => void pay()}>{busy ? "Opening checkout…" : pack ? `Add ${formatUSD(pack)} via secure checkout` : "Choose an amount"}</button>
        <div className="ledger-title"><b>Recent activity</b><span>Credit ledger</span></div>
        <div id="ledgerList">
          {ledger.slice(0, 8).map((e) => (
            <div key={e.id} className="ledger-row">
              <b>{e.description || e.type}</b>
              <span className={e.amountMinor < 0 ? "neg" : "pos"}>{formatUSD(e.amountMinor)}</span>
              <small>{e.status} · {new Date(e.createdAt).toLocaleDateString()}</small>
            </div>
          ))}
          {ledger.length === 0 && <p className="empty-note">No transactions yet.</p>}
        </div>
      </section>
    </div>
  );
}
