import { z } from "zod";
import { requireSession } from "@/lib/route-auth";
import { getPrisma } from "@/lib/db";
import { json, zodProblem } from "@/lib/http";
import { appendAuditEvent } from "@/lib/audit-log";

export const runtime = "nodejs";

const VOICES = ["emma", "ava", "andrew", "brian", "sonia", "natasha"] as const;
const FAMILIES = ["explainer", "whiteboard"] as const;

export interface AccountPreferences {
  notifyRendersEmail: boolean;
  notifyUpdatesEmail: boolean;
  defaultVoice: (typeof VOICES)[number] | null;
  defaultDuration: number | null;
  defaultFamily: (typeof FAMILIES)[number] | null;
  paymentMethod: "card" | "usdc";
}

const DEFAULTS: AccountPreferences = {
  notifyRendersEmail: true,
  notifyUpdatesEmail: false,
  defaultVoice: null,
  defaultDuration: null,
  defaultFamily: null,
  paymentMethod: "card",
};

const patchSchema = z.object({
  notifyRendersEmail: z.boolean().optional(),
  notifyUpdatesEmail: z.boolean().optional(),
  defaultVoice: z.enum(VOICES).nullable().optional(),
  defaultDuration: z.number().int().min(5).max(600).nullable().optional(),
  defaultFamily: z.enum(FAMILIES).nullable().optional(),
  paymentMethod: z.enum(["card", "usdc"]).optional(),
}).strict();

function read(settings: unknown): AccountPreferences {
  const s = (settings && typeof settings === "object" ? settings : {}) as Record<string, unknown>;
  return {
    notifyRendersEmail: typeof s.notifyRendersEmail === "boolean" ? s.notifyRendersEmail : DEFAULTS.notifyRendersEmail,
    notifyUpdatesEmail: typeof s.notifyUpdatesEmail === "boolean" ? s.notifyUpdatesEmail : DEFAULTS.notifyUpdatesEmail,
    defaultVoice: VOICES.includes(s.defaultVoice as never) ? (s.defaultVoice as AccountPreferences["defaultVoice"]) : null,
    defaultDuration: typeof s.defaultDuration === "number" && s.defaultDuration >= 5 && s.defaultDuration <= 600 ? s.defaultDuration : null,
    defaultFamily: FAMILIES.includes(s.defaultFamily as never) ? (s.defaultFamily as AccountPreferences["defaultFamily"]) : null,
    paymentMethod: s.paymentMethod === "usdc" ? "usdc" : "card",
  };
}

export async function GET(request: Request) {
  const auth = await requireSession(request);
  if (auth.response) return auth.response;
  const user = await getPrisma()!.user.findUnique({ where: { id: auth.session!.userId }, select: { settings: true } });
  return json({ preferences: read(user?.settings) }, auth.id);
}

export async function PATCH(request: Request) {
  const auth = await requireSession(request);
  if (auth.response) return auth.response;
  const parsed = patchSchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) return zodProblem(auth.id, parsed.error);
  const prisma = getPrisma()!;
  const user = await prisma.user.findUnique({ where: { id: auth.session!.userId }, select: { settings: true } });
  const current = (user?.settings && typeof user.settings === "object" ? user.settings : {}) as Record<string, unknown>;
  const next = { ...current, ...parsed.data };
  const saved = await prisma.user.update({ where: { id: auth.session!.userId }, data: { settings: next }, select: { settings: true } });
  await appendAuditEvent({ request, requestId: auth.id, actorUserId: auth.session!.userId, action: "ACCOUNT_PREFERENCES_UPDATED", entityType: "User", entityId: auth.session!.userId, after: parsed.data });
  return json({ preferences: read(saved.settings) }, auth.id);
}
