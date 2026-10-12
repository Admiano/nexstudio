export type PlanTier = "FREE" | "CREATOR" | "PRO";
export type PlanStatus = "ACTIVE" | "EXPIRED";

export interface UserPlanState {
  tier: PlanTier;
  status: PlanStatus;
  renewsAt: string | null;
}

export const TIER_ORDER: PlanTier[] = ["FREE", "CREATOR", "PRO"];

export interface PlanSpec {
  tier: PlanTier;
  name: string;
  priceUsd: number;
  priceNote: string;
  quota: string;
  benefits: string[];
}

export const PLANS: Record<PlanTier, PlanSpec> = {
  FREE: {
    tier: "FREE",
    name: "Free",
    priceUsd: 0,
    priceNote: "forever",
    quota: "3 videos, up to 10 seconds each",
    benefits: [
      "Whiteboard and explainer videos",
      "Captions included",
      "NexStudio watermark on your videos",
      "Presenters and more styles unlock when you upgrade",
    ],
  },
  CREATOR: {
    tier: "CREATOR",
    name: "Creator",
    priceUsd: 20,
    priceNote: "per month",
    quota: "15 videos a month, up to 60 seconds each",
    benefits: [
      "Everything in Free",
      "Ready-made presenters like Daniel and Maya",
      "Every style: whiteboard, explainers, board scenes",
      "No watermark",
      "Onchain proof on every video",
    ],
  },
  PRO: {
    tier: "PRO",
    name: "Pro",
    priceUsd: 49,
    priceNote: "per month",
    quota: "50 videos a month, up to 3 minutes each",
    benefits: [
      "Everything in Creator",
      "Build your own presenters: face, hair, outfit, voice",
      "2 custom presenters included, extra ones about $12 each",
      "Faster queue and 4K downloads",
      "Your cost per video drops the more you make",
    ],
  },
};

interface PlanRowLike {
  plan: string;
  planStatus: string;
  planRenewsAt: Date | null;
}

export function normalizeTier(raw: string | null | undefined): PlanTier {
  const t = (raw || "").trim().toUpperCase();
  return t === "CREATOR" || t === "PRO" ? t : "FREE";
}

/** Paid plans lapse to EXPIRED once the renewal date passes; FREE never expires. */
export function effectivePlan(row: PlanRowLike, now: Date = new Date()): UserPlanState {
  const tier = normalizeTier(row.plan);
  if (tier === "FREE") return { tier, status: "ACTIVE", renewsAt: null };
  const expired = row.planStatus === "EXPIRED" || (row.planRenewsAt !== null && row.planRenewsAt <= now);
  return { tier, status: expired ? "EXPIRED" : "ACTIVE", renewsAt: row.planRenewsAt ? row.planRenewsAt.toISOString() : null };
}
