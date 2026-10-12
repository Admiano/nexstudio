import type { Metadata } from "next";
import { headers } from "next/headers";
import { getSession } from "@/lib/auth";
import { effectivePlan } from "@/lib/plan";
import { env } from "@/lib/env";
import { PublicFooter, PublicHeader } from "@/studio-v2/PublicChrome";
import { PricingTiers } from "@/studio-v2/PricingTiers";
import "@/studio-v2/nexstudio-v2.css";

export const metadata: Metadata = { title: "NexStudio pricing", description: "Free, Creator and Pro plans for NexStudio video production." };

export default async function Page() {
  const h = await headers();
  const session = await getSession(new Request("http://localhost/pricing", { headers: h }));
  const user = session?.user as { plan?: string; planStatus?: string; planRenewsAt?: Date | null } | undefined;
  const plan = user ? effectivePlan({ plan: user.plan ?? "FREE", planStatus: user.planStatus ?? "ACTIVE", planRenewsAt: user.planRenewsAt ?? null }) : null;
  return (
    <div id="publicSite" className="pw-pricing-page">
      <PublicHeader authed={Boolean(session)} googleAuth={Boolean(env.googleClientId && env.googleClientSecret)} linkBase="/" />
      <main>
        <section className="pw-section">
          <div className="pw-wrap">
            <div className="pw-section-head">
              <div className="pw-kicker"><i /> Pricing</div>
              <h1>Start free. Upgrade when you're ready.</h1>
              <p>Free lets you make your first videos today. Creator opens up the whole studio. Pro lets you build your own presenters.</p>
            </div>
            <PricingTiers plan={plan} />
            <p className="pw-plan-note">Your videos reset each month on your billing date. Run out? Top up or upgrade anytime.</p>
          </div>
        </section>
      </main>
      <PublicFooter linkBase="/" />
    </div>
  );
}
