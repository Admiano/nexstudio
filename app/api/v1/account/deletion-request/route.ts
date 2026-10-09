import { createHash, randomBytes } from "node:crypto";
import { requireSession } from "@/lib/route-auth";
import { getPrisma } from "@/lib/db";
import { json, problem } from "@/lib/http";
import { appendAuditEvent } from "@/lib/audit-log";

export const runtime = "nodejs";

const TOKEN_TTL_MS = 60 * 60 * 1000; // 1 hour

// POST — request deletion: flags the account and issues an emailed
// confirmation token. Without a mailer wired the link is returned in
// development so the flow is still exercisable end to end.
export async function POST(request: Request) {
  const auth = await requireSession(request);
  if (auth.response) return auth.response;
  const prisma = getPrisma()!;
  const user = await prisma.user.findUnique({ where: { id: auth.session!.userId }, select: { email: true, privacyStatus: true } });
  if (!user) return problem(auth.id, 404, "USER_NOT_FOUND", "Account not found", "Sign in again and retry.");
  if (user.privacyStatus === "DELETED") return problem(auth.id, 409, "ACCOUNT_ALREADY_DELETED", "Account already deleted", "This account has been removed.");

  const token = randomBytes(32).toString("base64url");
  const secretHash = createHash("sha256").update(token).digest("hex");
  await prisma.$transaction([
    prisma.user.update({ where: { id: auth.session!.userId }, data: { deletionRequestedAt: new Date() } }),
    prisma.authChallenge.create({ data: { userId: auth.session!.userId, purpose: "ACCOUNT_DELETION", identifier: auth.session!.userId, secretHash, expiresAt: new Date(Date.now() + TOKEN_TTL_MS) } }),
  ]);
  await appendAuditEvent({ request, requestId: auth.id, actorUserId: auth.session!.userId, action: "ACCOUNT_DELETION_REQUESTED", entityType: "User", entityId: auth.session!.userId });

  const body: Record<string, unknown> = { requested: true, email: user.email };
  if (process.env.NODE_ENV !== "production") {
    body.devConfirmUrl = `/api/v1/account/deletion-request/confirm?token=${token}`;
  }
  return json(body, auth.id);
}

// DELETE — cancel a pending deletion request before it is confirmed.
export async function DELETE(request: Request) {
  const auth = await requireSession(request);
  if (auth.response) return auth.response;
  const prisma = getPrisma()!;
  const user = await prisma.user.update({ where: { id: auth.session!.userId }, data: { deletionRequestedAt: null } });
  await prisma.authChallenge.deleteMany({ where: { userId: auth.session!.userId, purpose: "ACCOUNT_DELETION", usedAt: null } });
  await appendAuditEvent({ request, requestId: auth.id, actorUserId: auth.session!.userId, action: "ACCOUNT_DELETION_CANCELLED", entityType: "User", entityId: auth.session!.userId });
  return json({ cancelled: user.deletionRequestedAt === null }, auth.id);
}
