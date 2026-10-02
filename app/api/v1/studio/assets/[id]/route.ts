import { requireSession, requireTrustedOrigin } from "@/lib/route-auth";
import { json, problem } from "@/lib/http";
import { getPrisma } from "@/lib/db";
import { appendAuditEvent } from "@/lib/audit-log";

export const runtime = "nodejs";

// Soft-remove: the file leaves the reusable Library but stays traceable in audit + source productions.
export async function DELETE(request: Request, context: { params: Promise<{ id: string }> }) {
  const auth = await requireSession(request); if (auth.response) return auth.response;
  const origin = requireTrustedOrigin(request, auth.id); if (origin) return origin;
  const { id } = await context.params;
  const prisma = getPrisma()!;
  const source = await prisma.source.findFirst({ where: { id, ownerUserId: auth.session!.userId, isReusable: true } });
  if (!source) return problem(auth.id, 404, "ASSET_NOT_FOUND", "Asset not found", "Nothing was removed.");
  await prisma.source.update({ where: { id: source.id }, data: { isReusable: false } });
  await appendAuditEvent({ request, requestId: auth.id, actorUserId: auth.session!.userId, action: "ASSET_REMOVED", entityType: "Source", entityId: source.id, after: { name: source.name } });
  return json({ id: source.id, removed: true }, auth.id);
}
