import { z } from "zod";
import { appendAuditEvent } from "@/lib/audit-log";
import { getPrisma } from "@/lib/db";
import { json, problem, zodProblem } from "@/lib/http";
import { createPlanCheckout, paymentProviderStatus, retrievePlanCheckout } from "@/lib/payment-provider";
import { idempotencyKey, requireSession } from "@/lib/route-auth";
import { consumeRateLimit } from "@/lib/rate-limit";
import { attachFundingProviderSession } from "@/studio-v1/billing";
import { PLANS, type PlanTier } from "@/lib/plan";
export const runtime = "nodejs";

const schema = z.object({ tier: z.enum(["CREATOR", "PRO"]) }).strict();

const PRICE_MINOR: Record<PlanTier, number> = { FREE: 0, CREATOR: PLANS.CREATOR.priceUsd * 100, PRO: PLANS.PRO.priceUsd * 100 };

export async function POST(request: Request) {
  const auth = await requireSession(request);
  if (auth.response) return auth.response;
  const limit = await consumeRateLimit(auth.session!.userId, "plan_checkout", 10, 3600000);
  if (!limit.allowed) return problem(auth.id, 429, "PLAN_RATE_LIMITED", "Too many plan checkout attempts", `Wait ${limit.retryAfterSeconds} seconds.`);
  const key = idempotencyKey(request, auth.id);
  if (key.response) return key.response;
  const parsed = schema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) return zodProblem(auth.id, parsed.error);
  const tier = parsed.data.tier;
  const provider = paymentProviderStatus();
  if (!provider.configured || !provider.readyForLive)
    return problem(auth.id, 503, "STUDIO_PAYMENT_PROVIDER_NOT_CONFIGURED", "Plan checkout is unavailable", "Card billing for plans opens when the payment provider is configured.");
  const prisma = getPrisma()!;
  try {
    const intent = await prisma.studioFundingIntent.upsert({
      where: { userId_idempotencyKey: { userId: auth.session!.userId, idempotencyKey: key.value! } },
      create: { userId: auth.session!.userId, amountMinor: PRICE_MINOR[tier], currency: "USD", purpose: "PLAN_SUBSCRIPTION", status: "PENDING", idempotencyKey: key.value!, provider: "stripe" },
      update: {},
    });
    let checkoutUrl = intent.providerCheckoutUrl ?? null;
    let providerReference = intent.providerReference;
    if (providerReference && !checkoutUrl) { const s = await retrievePlanCheckout(providerReference); checkoutUrl = s.url; }
    if (!providerReference) {
      try {
        const session = await createPlanCheckout({ fundingIntentId: intent.id, userId: intent.userId, tier, planName: PLANS[tier].name, amountMinor: PRICE_MINOR[tier], returnPath: "/pricing", idempotencyKey: `stripe-plan:${intent.id}` });
        if (!session.id || !session.url) throw new Error("PAYMENT_PROVIDER_SESSION_INVALID");
        providerReference = session.id; checkoutUrl = session.url;
        await attachFundingProviderSession({ userId: intent.userId, fundingIntentId: intent.id, providerReference: session.id, checkoutUrl: session.url });
      } catch (error) {
        await prisma.studioFundingIntent.update({ where: { id: intent.id }, data: { status: "FAILED", failureReason: error instanceof Error ? error.message : "CREATE_FAILED" } }).catch(() => undefined);
        throw error;
      }
    }
    await appendAuditEvent({ request, requestId: auth.id, actorUserId: auth.session!.userId, action: "PLAN_CHECKOUT_CREATED", entityType: "StudioFundingIntent", entityId: intent.id, after: { tier, amountMinor: PRICE_MINOR[tier] } });
    return json({ fundingIntentId: intent.id, tier, amountMinor: PRICE_MINOR[tier], currency: "USD", checkoutUrl }, auth.id);
  } catch (error) {
    const message = error instanceof Error ? error.message : "PLAN_CHECKOUT_FAILED";
    return problem(auth.id, 502, "PLAN_CHECKOUT_FAILED", "Could not start plan checkout", message.startsWith("PAYMENT_PROVIDER_ERROR:") ? "The payment provider rejected the request. Try again." : message);
  }
}
