import { NextResponse } from "next/server";
import { createSessionTx, secretHashCandidates, setSessionCookie } from "@/lib/auth";
import { appendAuditEvent } from "@/lib/audit-log";
import { getPrisma } from "@/lib/db";
import { problem, requestId } from "@/lib/http";
export const runtime = "nodejs";

// Shareable guest sign-in: a long-lived challenge (purpose GUEST_PASS) that is
// NOT consumed on use, so one link can be handed to a tester and reused until
// it expires or the challenge row is deleted. Each use creates a fresh session
// for the guest account the challenge belongs to.
export async function GET(request: Request) {
  const id = requestId(request);
  const token = new URL(request.url).searchParams.get("token");
  if (!token || token.length > 512) return problem(id, 422, "GUEST_LINK_INVALID", "Guest link is incomplete", "Ask for a fresh guest link.");
  const prisma = getPrisma();
  if (!prisma) return problem(id, 503, "DATABASE_REQUIRED", "Guest sign-in is unavailable", "Persistent account storage is required.");
  const hashes = secretHashCandidates("guest-pass", token);
  try {
    const result = await prisma.$transaction(async (tx) => {
      const challenge = await tx.authChallenge.findFirst({
        where: { purpose: "GUEST_PASS", secretHash: { in: hashes }, expiresAt: { gt: new Date() } },
        orderBy: { createdAt: "desc" },
      });
      if (!challenge || !challenge.userId) throw new Error("GUEST_LINK_EXPIRED");
      const user = await tx.user.findUnique({ where: { id: challenge.userId } });
      if (!user || (user as { privacyStatus?: string }).privacyStatus === "DELETED") throw new Error("ACCOUNT_DELETED");
      const session = await createSessionTx(tx, user.id, request);
      return { user, session, challengeId: challenge.id };
    }, { isolationLevel: "Serializable" });
    await appendAuditEvent({ request, requestId: id, actorUserId: result.user.id, action: "AUTH_GUEST_VERIFIED", entityType: "AuthChallenge", entityId: result.challengeId });
    const response = new NextResponse(null, { status: 303, headers: { Location: "/studio" } });
    setSessionCookie(response, result.session.token, result.session.expiresAt, request);
    return response;
  } catch (e) {
    const code = e instanceof Error ? e.message : "GUEST_LINK_EXPIRED";
    if (code === "ACCOUNT_DELETED") return problem(id, 403, "ACCOUNT_DELETED", "This guest account is closed", "Ask for a fresh guest link.");
    return problem(id, 410, "GUEST_LINK_EXPIRED", "This guest link has expired or been revoked", "Ask for a fresh guest link.");
  }
}
