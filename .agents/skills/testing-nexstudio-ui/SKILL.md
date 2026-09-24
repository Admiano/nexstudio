---
name: testing-nexstudio-ui
description: How to run the NexStudio Next.js app locally and authenticate the browser for UI testing (Postgres via pgserver, seeded session cookie injected through Chrome CDP).
---

# NexStudio UI testing setup

## Services to start
- Postgres: `/home/ubuntu/.local/lib/python3.10/site-packages/pgserver/pginstall/bin/postgres -D /home/ubuntu/data/pgdb -k /home/ubuntu/data/pgdb` (datadir AND socket dir are both `/home/ubuntu/data/pgdb`; not covered by blueprint initialize — start it yourself).
- Dev server: `export PATH="$HOME/.nvm/versions/node/v24.19.0/bin:$PATH" && cd /home/ubuntu/repos/nexstudio && npm run dev` → :3000. `.env` already has `DATABASE_URL` pointing at the pgserver socket host.

## Authenticating the browser
`/studio` is session-gated server-side (anonymous → 307 `/?signin=1`). The session cookie is **httpOnly**, so it cannot be set via `document.cookie` — inject it through Chrome DevTools Protocol instead:

- Chrome (Chrome for Testing) runs with CDP at `http://localhost:29229/json`.
- `Network.setCookie` needs `suppress_origin=True` on the websocket-client connect, otherwise Chrome rejects the handshake with 403 "Rejected an incoming WebSocket connection from the origin". A working helper is at `/tmp/cdp_cookie.py` (recreate if missing): connect to the page target's `webSocketDebuggerUrl` with `suppress_origin=True`, then `Network.setCookie` with `url=http://localhost:3000/`, `httpOnly=True`, `sameSite=Lax`.
- Seeded `studio_session` value lives in the session handoff notes; verify with `curl http://localhost:3000/api/v1/studio/balance -H "Cookie: studio_session=..."` (200 JSON = valid, 401 AUTHENTICATION_REQUIRED = expired/reseed).
- Test anonymous behavior FIRST (before injecting the cookie) — the cookie persists in the profile.

## App structure (V2 studio UI)
- `/` → `PublicSite` (hero + NexMind demo panel); `?signin=1` opens the magic-link sheet.
- `/studio` → hash-routed views: `#create` (default), `#work`, `#brand`, `#library`, `#series`. Series has no top-nav button — reach it via URL hash or the composer Series tool.
- Overlays: Credits (topbar balance pill), Account (avatar button, 5 tabs), production History (Work row click), picker sheets (composer tools), NexMind flow (Create submit).
- Expected gated behavior: any public production type returns 409 `PUBLIC_PRODUCTION_TYPE_NOT_CERTIFIED` → the flow lands on "Not open for new productions yet." with "Production type unavailable". This is CORRECT, not a bug.

## Gotchas
- `pgrep -f "postgres -D"` / `pgrep -f "next dev"` inside an exec call matches the exec's own command line — check `postmaster.pid` / `curl localhost:3000` instead.
- Browser console via the `browser_console` tool only returns output wrapped in `console.log(...)` inside your script.
