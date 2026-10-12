import type { Metadata } from "next";
import { headers } from "next/headers";
import { getSession } from "@/lib/auth";
import { effectivePlan } from "@/lib/plan";
import { env } from "@/lib/env";
import { PublicSite } from "@/studio-v2/PublicSite";
import "@/studio-v2/nexstudio-v2.css";

export const metadata: Metadata = { title: "NexStudio · Make something worth watching", description: "Creative production, directed by NexMind." };

export default async function Page() {
  const h = await headers();
  const session = await getSession(new Request("http://localhost/", { headers: h }));
  const user = session?.user as { plan?: string; planStatus?: string; planRenewsAt?: Date | null } | undefined;
  const plan = user ? effectivePlan({ plan: user.plan ?? "FREE", planStatus: user.planStatus ?? "ACTIVE", planRenewsAt: user.planRenewsAt ?? null }) : null;
  return <PublicSite authed={Boolean(session)} plan={plan} googleAuth={Boolean(env.googleClientId && env.googleClientSecret)} />;
}
