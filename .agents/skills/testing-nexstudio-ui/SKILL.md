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
- Chrome's real viewport is 1600x1069 while `computer` screenshots are scaled to 1024x768 — the direction-stage "Create video" dock (`position:fixed; bottom:0`) lands behind the OS taskbar in screenshots. Click it via CDP `Input.dispatchMouseEvent` at real CSS coords (query `getBoundingClientRect` via `Runtime.evaluate` first).

## Engine jobs E2E
- `POST /api/v1/whiteboards` and `/api/v1/explainers` are multipart (`-F`); they REQUIRE `-H "Origin: http://localhost:3000"` (same-origin guard → 403 `ORIGIN_REQUIRED` without it) and the session cookie.
- Job dirs: `engine_sources/whiteboard-v3-runtime/out/whiteboard-jobs/wb-*/` and `engine_sources/editorial-motion-v2/out/explainer-jobs/xr-*/` — each has `request.json`, `status.json` (`{"status":"running|done|failed", ...}`), `files/<aspect>.mp4`, and a `gate_report.json` on failure.
- Whiteboard params: `script` (or `voiceFile`), `type`=kinetic-text|hand-drawn-board, `theme`=light|dark, `accent`=#hex (3-8 hex digits), `aspects`=16x9,1x1,9x16. Explainer: `style` from `styles.json` + `voice`=emma|ava|andrew|brian|sonia|natasha.
- Renders are fast in practice (whiteboard kinetic ~20s for a 3-beat script; explainer ~55s) — 9-40s mp4s, h264+aac.
- **Explainer entity-bank trap**: `tools/make_reel.py` builds illustration entities only from words in `styles.json` `entity_bank` (~78 words have `colour` assets for the tiles style: team/app/money/time/win/rocket/...). A natural script whose words aren't in the bank produces ZERO entities → engine gate `ILLUSTRATION_TOO_FEW_ENTITIES` → exit 1 → UI shows honest "render failed — try again". To get a render through, write the script from bank words (e.g. "Your team builds the app. Money grows. Time wins. The rocket ships.").
- Whiteboard kinetic renders ANY script (text-only); use it for the quick E2E sanity job.

## Second explainer trap — legibility gate
Beyond the entity bank, explainers also fail the `gate_report.json` LEGIBILITY gate when beats can't hold ≥ minimum on-screen time at the target length (`LEGIBLE_HOLD_*_UNDER_*`, `CASCADE_OVERRUNS_EXIT`). Long/multi-line scripts are the usual trigger. Two gates can kill a render for different reasons — check `gate_report.json` `failures[]` to tell which.

## Audit interaction gotchas (V2 flow + overlays)
- The NexMind flow is an overlay over the app, persisted via `sessionStorage nx.flow`. While a flow stage is open it covers ALL views and blocks clicks (elementFromPoint → `.review-canvas`/`.direction-stage`). Reach it via the real flow (Create submit) or a Work row → history → "Open review →"; a minimal hand-injected `nx.flow` renders nothing. Clear stuck overlays with `sessionStorage.removeItem('nx.flow')` + reload, or the stage's own `.review-back` / "← Work" control.
- Backdrop-close classes differ per overlay: `.overlay.open`, `.credit-utility.open`, `.series-edit-overlay.open`, `.sheet-backdrop.open`. To close from automation, dispatch `click` on the backdrop element itself (the panel is a child — target the element with the `.open` class).
- The direction stage scrolls internally on `.direction-stage` (scrollHeight >> clientHeight) — `window.scrollTo` does NOT reach the decision/voice/length/speed sections; set `element.scrollTop` instead.
- Sign-out invalidates the session server-side and redirects to `/` — re-mint a session via psql afterwards if more authed testing is needed.
- Mobile (≤760px): composer tool buttons collapse to icon-only (`span{display:none}`) with 40px targets — they still open the sheets; `.mobile-nav` bottom bar has Create/Work/Brand/Library (no Series).
