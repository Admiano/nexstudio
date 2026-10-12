import { NextResponse } from "next/server";
import { createHash } from "node:crypto";
import { createSessionTx, setSessionCookie } from "@/lib/auth";
import { appendAuditEvent } from "@/lib/audit-log";
import { getPrisma } from "@/lib/db";
import { env } from "@/lib/env";
import { problem, requestId } from "@/lib/http";
export const runtime = "nodejs";

const STATE_COOKIE = "nx_google_oauth";

interface GoogleUserInfo { sub: string; email?: string; email_verified?: boolean; name?: string; picture?: string; }

export async function GET(request: Request) {
  const id = requestId(request);
  const url = new URL(request.url);
  if (!env.googleClientId || !env.googleClientSecret)
    return problem(id, 503, "GOOGLE_AUTH_NOT_CONFIGURED", "Google sign-in is unavailable", "Use email sign-in instead.");
  const prisma = getPrisma();
  if (!prisma) return problem(id, 503, "DATABASE_REQUIRED", "Google sign-in is unavailable", "Persistent account storage is required.");
  const code = url.searchParams.get("code");
  const stateParam = url.searchParams.get("state") || "";
  const cookieState = request.headers.get("cookie")?.split(";").map(p => p.trim()).find(p => p.startsWith(`${STATE_COOKIE}=`))?.split("=").slice(1).join("=");
  const [stateHash, payloadB64] = stateParam.split(".");
  let next = "/studio";
  try {
    const payload = JSON.parse(Buffer.from(payloadB64 || "", "base64url").toString()) as { s?: string; n?: string };
    const expected = createHash("sha256").update(JSON.stringify(payload)).digest("base64url");
    if (!cookieState || payload.s !== decodeURIComponent(cookieState || "") || expected !== stateHash)
      return problem(id, 403, "GOOGLE_STATE_MISMATCH", "Sign-in could not be verified", "Start Google sign-in again.");
    if (payload.n && payload.n.startsWith("/") && !payload.n.startsWith("//")) next = payload.n;
  } catch {
    return problem(id, 403, "GOOGLE_STATE_MISMATCH", "Sign-in could not be verified", "Start Google sign-in again.");
  }
  if (!code) return problem(id, 400, "GOOGLE_CODE_MISSING", "Google did not return a sign-in code", "Start Google sign-in again.");
  let tokens: { access_token?: string };
  try {
    const res = await fetch("https://oauth2.googleapis.com/token", {
      method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ code, client_id: env.googleClientId, client_secret: env.googleClientSecret, redirect_uri: `${env.appOrigin}/api/v1/auth/google/callback`, grant_type: "authorization_code" }).toString(),
    });
    tokens = await res.json();
    if (!res.ok || !tokens.access_token) throw new Error("token exchange failed");
  } catch {
    return problem(id, 502, "GOOGLE_TOKEN_FAILED", "Google sign-in failed", "Start Google sign-in again.");
  }
  let info: GoogleUserInfo;
  try {
    const res = await fetch("https://openidconnect.googleapis.com/v1/userinfo", { headers: { authorization: `Bearer ${tokens.access_token}` } });
    info = await res.json();
    if (!res.ok || !info.sub) throw new Error("userinfo failed");
  } catch {
    return problem(id, 502, "GOOGLE_USERINFO_FAILED", "Could not read your Google profile", "Start Google sign-in again.");
  }
  const email = info.email?.toLowerCase() || null;
  if (email && info.email_verified === false)
    return problem(id, 403, "GOOGLE_EMAIL_UNVERIFIED", "Your Google email is not verified", "Verify it in Google, or use email sign-in.");
  try {
    const result = await prisma.$transaction(async tx => {
      const existingIdentity = await tx.authIdentity.findUnique({ where: { provider_subject: { provider: "GOOGLE", subject: info.sub } } });
      let userId = existingIdentity?.userId || null;
      if (!userId && email) {
        const byEmail = await tx.user.findUnique({ where: { email } });
        if (byEmail) {
          if ((byEmail as { privacyStatus?: string }).privacyStatus === "DELETED") throw new Error("ACCOUNT_DELETED");
          userId = byEmail.id;
        }
      }
      if (!userId) {
        const created = await tx.user.create({ data: { email, displayName: info.name?.trim() || (email ? email.split("@")[0].replace(/[._-]+/g, " ").replace(/\b\w/g, c => c.toUpperCase()) : "Studio member"), avatarUrl: info.picture || null, settings: {} } });
        userId = created.id;
      }
      await tx.authIdentity.upsert({ where: { provider_subject: { provider: "GOOGLE", subject: info.sub } }, create: { userId, provider: "GOOGLE", subject: info.sub, email, emailVerified: info.email_verified ?? Boolean(email) }, update: { userId, email, emailVerified: info.email_verified ?? Boolean(email) } });
      const session = await createSessionTx(tx, userId, request);
      return { userId, session };
    }, { isolationLevel: "Serializable" });
    await appendAuditEvent({ request, requestId: id, actorUserId: result.userId, action: "AUTH_GOOGLE_VERIFIED", entityType: "AuthIdentity", entityId: `google:${info.sub}` });
    const response = NextResponse.redirect(new URL(next, url.origin), 303);
    setSessionCookie(response, result.session.token, result.session.expiresAt, request);
    response.cookies.set(STATE_COOKIE, "", { httpOnly: true, path: "/", maxAge: 0 });
    return response;
  } catch (error) {
    const code2 = error instanceof Error ? error.message : "GOOGLE_SIGNIN_FAILED";
    if (code2 === "ACCOUNT_DELETED") return problem(id, 410, code2, "Account is no longer active", "Contact support if you believe this is incorrect.");
    return problem(id, 500, "GOOGLE_SIGNIN_FAILED", "Google sign-in failed", "Start Google sign-in again.");
  }
}
