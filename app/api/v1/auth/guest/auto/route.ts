import { NextResponse } from "next/server";
import { createSessionTx, setSessionCookie } from "@/lib/auth";
import { getPrisma } from "@/lib/db";
import { problem, requestId } from "@/lib/http";
export const runtime = "nodejs";

// Open-test sign-in: when NEXSTUDIO_PUBLIC_OPEN=1 the deployment is a public
// demo — any visitor to /studio gets silently signed into a shared guest
// account instead of being bounced to the email sign-in page. The client only
// sees /studio -> 303 -> /studio; no token, no email form.
const PUBLIC_GUEST_EMAIL = "public-guest@nexstudio.invalid";

export async function GET(request: Request) {
  const id = requestId(request);
  if (process.env.NEXSTUDIO_PUBLIC_OPEN !== "1")
    return new NextResponse(null, { status: 303, headers: { Location: "/?signin=1" } });
  const prisma = getPrisma();
  if (!prisma) return problem(id, 503, "DATABASE_REQUIRED", "Guest sign-in is unavailable", "Persistent account storage is required.");
  const session = await prisma.$transaction(async (tx) => {
    let user = await tx.user.findUnique({ where: { email: PUBLIC_GUEST_EMAIL } });
    if (!user) {
      try {
        user = await tx.user.create({ data: { email: PUBLIC_GUEST_EMAIL, displayName: "Public Guest" } });
        await tx.studioCreditAccount.create({ data: { userId: user.id, balanceMinor: 0 } });
      } catch {
        // Concurrent first visit created the shared guest — re-read it.
        user = await tx.user.findUnique({ where: { email: PUBLIC_GUEST_EMAIL } });
        if (!user) throw new Error("GUEST_UNAVAILABLE");
      }
    }
    return createSessionTx(tx, user.id, request);
  });
  const response = new NextResponse(null, { status: 303, headers: { Location: "/studio" } });
  setSessionCookie(response, session.token, session.expiresAt, request);
  return response;
}
