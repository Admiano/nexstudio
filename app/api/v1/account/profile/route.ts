import { z } from "zod";
import { requireSession } from "@/lib/route-auth";
import { getPrisma } from "@/lib/db";
import { json, problem, zodProblem } from "@/lib/http";
import { appendAuditEvent } from "@/lib/audit-log";

export const runtime = "nodejs";

const patchSchema = z.object({
  displayName: z.string().trim().min(1).max(60),
}).strict();

export async function GET(request: Request) {
  const auth = await requireSession(request);
  if (auth.response) return auth.response;
  const user = await getPrisma()!.user.findUnique({ where: { id: auth.session!.userId }, select: { displayName: true, email: true } });
  return json({ profile: { displayName: user?.displayName ?? null, email: user?.email ?? null } }, auth.id);
}

export async function PATCH(request: Request) {
  const auth = await requireSession(request);
  if (auth.response) return auth.response;
  const parsed = patchSchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) return zodProblem(auth.id, parsed.error);
  const user = await getPrisma()!.user.update({
    where: { id: auth.session!.userId },
    data: { displayName: parsed.data.displayName },
    select: { displayName: true, email: true },
  });
  await appendAuditEvent({ request, requestId: auth.id, actorUserId: auth.session!.userId, action: "ACCOUNT_PROFILE_UPDATED", entityType: "User", entityId: auth.session!.userId, after: { displayName: user.displayName } });
  return json({ profile: user }, auth.id);
}
