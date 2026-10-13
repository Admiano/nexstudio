import { env } from "./env";

export function allowedAppOrigins(): Set<string> {
  const origins = new Set([new URL(env.appOrigin).origin]);
  for (const value of env.appAdditionalOrigins) {
    const url = new URL(value);
    if (url.username || url.password || url.pathname !== "/" || url.search || url.hash
        || (process.env.NODE_ENV === "production" && url.protocol !== "https:")) {
      throw new Error("APP_ADDITIONAL_ORIGINS must contain explicit application origins.");
    }
    origins.add(url.origin);
  }
  return origins;
}

// Caddy supplies the public host while Next's standalone request URL may use
// its internal bind address. Only explicitly configured app origins qualify.
export function requestAppOrigin(request: Request): string {
  const allowed = allowedAppOrigins();
  const origin = request.headers.get("origin");
  if (origin && allowed.has(origin)) return origin;
  const requestUrl = new URL(request.url);
  const host = request.headers.get("x-forwarded-host")?.split(",")[0].trim();
  const protocol = request.headers.get("x-forwarded-proto")?.split(",")[0].trim();
  if (host && !/[\s/\\@]/.test(host) && ["http", "https"].includes(protocol || "")) {
    try {
      const candidate = new URL(`${protocol}://${host}`).origin;
      if (allowed.has(candidate)) return candidate;
    } catch {
      // An invalid forwarded host cannot select an application origin.
    }
  }
  if (allowed.has(requestUrl.origin)) return requestUrl.origin;
  return new URL(env.appOrigin).origin;
}
