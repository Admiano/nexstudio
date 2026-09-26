import { createHash } from "node:crypto";
import { z } from "zod";
import { getPrisma } from "@/lib/db";
import { json, problem, requestId, zodProblem } from "@/lib/http";
import { appendAuditEvent } from "@/lib/audit-log";

export const runtime = "nodejs";

const schema = z.object({ token: z.string().min(10) }).strict();

async function confirm(token: string, request: Request) {
  const prisma = getPrisma()!;
  const secretHash = createHash("sha256").update(token).digest("hex");
  const challenge = await prisma.authChallenge.findFirst({
    where: { purpose: "ACCOUNT_DELETION", secretHash, usedAt: null, expiresAt: { gt: new Date() } },
  });
  if (!challenge || !challenge.userId) return problem(requestId(request), 410, "DELETION_LINK_EXPIRED", "Confirmation link expired", "Request account deletion again from your account settings.");
  await prisma.$transaction([
    prisma.authChallenge.update({ where: { id: challenge.id }, data: { usedAt: new Date() } }),
    prisma.user.update({ where: { id: challenge.userId }, data: { privacyStatus: "DELETED", deletedAt: new Date() } }),
    prisma.session.updateMany({ where: { userId: challenge.userId, status: "ACTIVE", revokedAt: null }, data: { status: "REVOKED", revokedAt: new Date() } }),
  ]);
  await appendAuditEvent({ request, requestId: requestId(request), actorUserId: challenge.userId, action: "ACCOUNT_DELETED", entityType: "User", entityId: challenge.userId });
  return json({ deleted: true }, requestId(request));
}

// GET — the emailed confirmation link target.
export async function GET(request: Request) {
  const token = new URL(request.url).searchParams.get("token") ?? "";
  if (token.length < 10) return problem(requestId(request), 400, "DELETION_TOKEN_REQUIRED", "Confirmation token required", "Use the link from your deletion email.");
  return confirm(token, request);
}

// POST — same confirm for programmatic clients.
export async function POST(request: Request) {
  const parsed = schema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) return zodProblem(requestId(request), parsed.error);
  return confirm(parsed.data.token, request);
}
