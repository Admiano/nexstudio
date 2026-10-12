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
    quota: "3 videos, 10 seconds each",
    benefits: [
      "Whiteboard and one explainer style",
      "Kinetic captions included",
      "NexStudio watermark on every video",
      "Cast and all other engines stay locked",
    ],
  },
  CREATOR: {
    tier: "CREATOR",
    name: "Creator",
    priceUsd: 20,
    priceNote: "per month",
    quota: "15 productions a month, up to 60s",
    benefits: [
      "Everything in Free, unlocked",
      "Stock presenter roster (Daniel, Maya)",
      "All engines: whiteboard, explainers, board scenes",
      "No watermark, onchain proof on every film",
      "Top-up packs when you run hot",
    ],
  },
  PRO: {
    tier: "PRO",
    name: "Pro",
    priceUsd: 49,
    priceNote: "per month",
    quota: "50 productions a month, up to 3 minutes",
    benefits: [
      "Everything in Creator",
      "Character builder: faces, hair, wardrobe, voice",
      "2 custom presenters included, extras ~$12 one-off",
      "Priority render queue, 4K output, premium voices",
      "Cheaper cost per film the more you make",
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
