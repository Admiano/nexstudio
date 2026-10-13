"use client";

import { useEffect, useRef, useState } from "react";
import { PLANS, TIER_ORDER, type PlanTier, type UserPlanState } from "@/lib/plan";

interface Cta {
  label: string;
  disabled: boolean;
  action: () => void;
}

export function PricingTiers({ plan, onNeedSignIn }: { plan: UserPlanState | null; onNeedSignIn?: () => void }) {
  const plansRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    plansRef.current?.querySelectorAll(".pw-reveal")
      .forEach(element => element.classList.add("in"));
  }, []);
  const [pending, setPending] = useState<PlanTier | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const myIdx = plan ? TIER_ORDER.indexOf(plan.tier) : -1;
  const needSignIn = onNeedSignIn ?? (() => { window.location.href = "/?signin=1"; });

  async function checkout(tier: PlanTier) {
    if (tier === "FREE") { needSignIn(); return; }
    setPending(tier); setNote(null);
    try {
      const res = await fetch("/api/v1/studio/plan/checkout", {
        method: "POST",
        headers: { "content-type": "application/json", "Idempotency-Key": `nx-plan:${tier}:${crypto.randomUUID()}` },
        body: JSON.stringify({ tier }),
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) {
        setNote(body?.detail || "Plan checkout is not available yet. Card billing opens when payments go live.");
        return;
      }
      if (body?.data?.checkoutUrl) { window.location.href = body.data.checkoutUrl; return; }
      setNote("Checkout did not return a payment link. Try again.");
    } catch {
      setNote("Could not reach checkout. Try again.");
    } finally {
      setPending(null);
    }
  }

  function ctaFor(tier: PlanTier, idx: number): Cta {
    const spec = PLANS[tier];
    if (!plan) {
      return { label: tier === "FREE" ? "Create free account" : tier === "PRO" ? "Go Pro" : `Choose ${spec.name}`, disabled: false, action: needSignIn };
    }
    if (idx === myIdx) {
      if (plan.status === "EXPIRED") return { label: `Rejoin ${spec.name}`, disabled: false, action: () => void checkout(tier) };
      return { label: "Your current plan", disabled: true, action: () => {} };
    }
    if (idx < myIdx) return { label: "Included in your plan", disabled: true, action: () => {} };
    return { label: tier === "PRO" ? "Upgrade to Pro" : `Upgrade to ${spec.name}`, disabled: false, action: () => void checkout(tier) };
  }

  return (
    <div className="pw-plans" ref={plansRef}>
      {TIER_ORDER.map((tier, i) => {
        const spec = PLANS[tier];
        const cta = ctaFor(tier, i);
        const featured = tier === "CREATOR";
        return (
          <section key={tier} className={`pw-plan pw-reveal${featured ? " featured" : ""}`} aria-label={`${spec.name} plan`}>
            {featured && <span className="pw-plan-tag">Most popular</span>}
            <h3>{spec.name}</h3>
            <div className="pw-plan-price">
              {spec.priceUsd === 0 ? <strong>$0</strong> : <><strong>${spec.priceUsd}</strong><small>{spec.priceNote}</small></>}
            </div>
            <p className="pw-plan-quota">{spec.quota}</p>
            <ul className="pw-plan-benefits">
              {spec.benefits.map(b => <li key={b}>{b}</li>)}
            </ul>
            <button className={featured ? "pw-solid" : "pw-ghost"} disabled={cta.disabled || pending === tier} onClick={cta.action}>
              {pending === tier ? "Opening checkout…" : cta.label}
            </button>
          </section>
        );
      })}
      {note && <p className="pw-plan-note" role="status">{note}</p>}
    </div>
  );
}
