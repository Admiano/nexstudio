import { NextResponse } from "next/server";
import { randomBytes, createHash } from "node:crypto";
import { env } from "@/lib/env";
import { problem, requestId } from "@/lib/http";
export const runtime = "nodejs";

const STATE_COOKIE = "nx_google_oauth";

export async function GET(request: Request) {
  const id = requestId(request);
  if (!env.googleClientId || !env.googleClientSecret)
    return problem(id, 503, "GOOGLE_AUTH_NOT_CONFIGURED", "Google sign-in is unavailable", "Use email sign-in instead.");
  const next = new URL(request.url).searchParams.get("next");
  const state = randomBytes(24).toString("base64url");
  const payload = JSON.stringify({ s: state, n: next && next.startsWith("/") && !next.startsWith("//") ? next : "/studio" });
  const redirectUri = `${env.appOrigin}/api/v1/auth/google/callback`;
  const url = new URL("https://accounts.google.com/o/oauth2/v2/auth");
  url.searchParams.set("client_id", env.googleClientId);
  url.searchParams.set("redirect_uri", redirectUri);
  url.searchParams.set("response_type", "code");
  url.searchParams.set("scope", "openid email profile");
  url.searchParams.set("state", createHash("sha256").update(payload).digest("base64url") + "." + Buffer.from(payload).toString("base64url"));
  url.searchParams.set("access_type", "online");
  const response = NextResponse.redirect(url, 302);
  response.cookies.set(STATE_COOKIE, state, { httpOnly: true, sameSite: "lax", secure: process.env.NODE_ENV === "production" || new URL(request.url).protocol === "https:", path: "/", maxAge: 600 });
  return response;
}
