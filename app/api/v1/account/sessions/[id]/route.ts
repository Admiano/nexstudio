import { requireSession } from "@/lib/route-auth";
import { getPrisma } from "@/lib/db";
import { json, problem } from "@/lib/http";
import { appendAuditEvent } from "@/lib/audit-log";

export const runtime = "nodejs";

export async function DELETE(request: Request, ctx: { params: Promise<{ id: string }> }) {
  const auth = await requireSession(request);
  if (auth.response) return auth.response;
  const { id } = await ctx.params;
  const prisma = getPrisma()!;
  const row = await prisma.session.findFirst({ where: { id, userId: auth.session!.userId, status: "ACTIVE", revokedAt: null } });
  if (!row) return problem(auth.id, 404, "SESSION_NOT_FOUND", "Session not found", "It may already be signed out.");
  await prisma.session.update({ where: { id: row.id }, data: { status: "REVOKED", revokedAt: new Date() } });
  await appendAuditEvent({ request, requestId: auth.id, actorUserId: auth.session!.userId, action: "SESSION_REVOKED", entityType: "Session", entityId: row.id });
  return json({ revoked: true, current: row.id === auth.session!.id }, auth.id);
}
