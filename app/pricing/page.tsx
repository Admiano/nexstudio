import type { Metadata } from "next";
import { headers } from "next/headers";
import { getSession } from "@/lib/auth";
import { effectivePlan } from "@/lib/plan";
import { env } from "@/lib/env";
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
      <header className="pw-nav">
        <a aria-label="NexStudio" className="pw-logo" href="/"><span className="brand-mark"><i /></span><span>NexStudio</span></a>
        <nav aria-label="Public navigation" className="pw-links"><a href="/">Home</a><a href="/#pricing">Plans</a></nav>
        <div className="pw-actions"><a className="pw-solid" href={session ? "/studio" : "/?signin=1"}>{session ? "Open Studio" : "Sign in"}</a></div>
      </header>
      <main>
        <section className="pw-section">
          <div className="pw-wrap">
            <div className="pw-section-head"><div className="pw-kicker"><i /> Pricing</div><h1>Start free. Upgrade when it earns its keep.</h1><p>Every film ships with onchain proof. Higher plans unlock more engines, more presenters and a lower cost per film. Quotas reset each billing cycle, and top-up packs keep you rolling between them.</p></div>
            <PricingTiers plan={plan} />
          </div>
        </section>
      </main>
    </div>
  );
}
