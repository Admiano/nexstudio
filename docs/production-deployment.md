# NexStudio — Going Live

Everything needed to run NexStudio on your own server, end to end. Read top to
bottom once, then follow the numbered steps.

---

## 1. What you are deploying

Three long-running services, all from one Docker image:

```
                 ┌─────────────────────────────┐
   internet ───► │  Caddy (TLS, ports 80/443)  │
                 └─────────────┬───────────────┘
                               │
                 ┌─────────────▼───────────────┐     ┌──────────────┐
                 │  web  (Next.js, port 3000)  │────►│  postgres 16 │
                 │  serves the studio + API,   │     │  user data,  │
                 │  accepts render requests    │     │  job queue   │
                 └─────────────┬───────────────┘     └──────▲───────┘
                               │ enqueues jobs             │
                 ┌─────────────▼───────────────┐           │
                 │  worker (render-worker.cjs) │───────────┘
                 │  drains the queue, runs the │
                 │  P8 runner + engines        │
                 └─────────────────────────────┘
```

- **web** — the site + API. Cheap to run.
- **worker** — does the heavy lifting: TTS, whisper captions, Blender character
  renders, Chromium board rendering, ffmpeg muxing. This is where CPU matters.
- **postgres** — users, sessions, cast, P8 memory, and the render queue
  (pg-boss). No external service needed.
- **volumes** — job outputs stay on disk (or move to S3 — see §8).

### What users get

- **Presenter videos** — 20 studio cast presets (10 female, 10 male) plus a
  user's own saved characters; 10 environments; Microsoft voices. The
  **Direction** options on the presenter flow: *Director cuts* (punch-in
  cuts, a hero word behind the character, a quiet whoosh/thump sound bed —
  on by default, off = clean captions only) and *Infographics* (hand-drawn
  icon discs on emphasis beats — off by default). Portrait renders ship
  clean framing; landscape centers the presenter.
- **Whiteboard, explainer, kids' lesson** — the certified 12-subtype set,
  all dispatched through P8's fail-closed registry with a sha256'd result
  envelope per job.

One machine can run all three. Split them when you outgrow it — §9.

---

## 2. What you need before starting

| Thing | Recommendation | Cost |
|---|---|---|
| Server | Hetzner CX32 (4 vCPU / 8 GB) to start; AX42 (8 dedicated cores) if you expect real volume | ~$8 / ~$55 per month |
| Domain | any registrar; one A record | ~$12/yr |
| OS | Ubuntu 24.04 LTS | free |
| Software | Docker Engine + compose plugin | free |
| Time | ~45 minutes for the first deploy | — |

No paid APIs are required. Voices (edge-tts), captions (whisper), icons,
characters — all run inside the image.

---

## 3. Provision the server

```bash
# on the fresh Ubuntu box, as root or a sudo user
apt update && apt upgrade -y
curl -fsSL https://get.docker.com | sh
apt install -y docker-compose-plugin git
```

Firewall — only three ports should ever be public:

```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

Do **not** open 3000, 5432, 9000, or 9001 — those stay behind the firewall.
Traffic reaches the app only through Caddy.

---

## 4. Get the code

The repo is private. Two options:

**Deploy key (recommended):**
```bash
ssh-keygen -t ed25519 -f ~/.ssh/deploy-nexstudio -N ""
cat ~/.ssh/deploy-nexstudio.pub   # add as a read-only Deploy Key in GitHub repo settings
GIT_SSH_COMMAND="ssh -i ~/.ssh/deploy-nexstudio" git clone git@github.com:Admiano/nexstudio.git
cd nexstudio
git checkout devin/20261006-board-scenes-option   # or your release branch
```

**Or a fine-grained PAT** (repo contents: read) cloned over HTTPS.

---

## 5. Configure `.env`

Create `.env` in the repo root — compose reads it for interpolation:

```bash
echo "STUDIO_TRUST_SECRET=$(openssl rand -hex 32)" >> .env
echo "APP_ORIGIN=https://studio.yourdomain.com" >> .env
```

| Variable | Required | Notes |
|---|---|---|
| `STUDIO_TRUST_SECRET` | **yes** | ≥32 chars. Signs sessions + encryption. Never commit it. |
| `APP_ORIGIN` | **yes** | The public URL, https included. POSTs from any other Origin are rejected (403 ORIGIN_NOT_TRUSTED). |
| `WEB_PORT` | no | Host port for web (default 3000). Caddy proxies to it. |
| `RENDER_QUEUE` | no | `on` (default). `off` reverts to in-process spawns — dev only. |
| `STUDIO_MAX_QUEUED_RENDERS` | no | Backlog cap before 429 (default 25). |
| `RENDER_WORKER_CONCURRENCY` | no | Jobs per worker (default 1 — ~1 per 4 CPU cores is the honest ratio). |
| `STORAGE_DRIVER` | no | `local` (default) or `s3` — see §8. |
| `S3_*` | only with s3 | endpoint/bucket/keys/region/public base URL. |

Engine tool paths (`WHISPER_PYTHON`, `MFA_BIN`, `BLENDER_BIN`, `CHROME_PATH`)
are baked into the image — don't set them.

**Optional: change the database password.** Edit `docker-compose.yml`:
`POSTGRES_PASSWORD` and the password inside both `DATABASE_URL`s must match.
Postgres is never exposed to the internet, so this is hygiene, not an emergency.

---

## 6. Boot

```bash
docker compose up -d --build        # ~20 min first build, cached after
docker compose exec web node_modules/.bin/prisma db push   # schema init, first boot only
docker compose ps                   # postgres healthy, web + worker Up
curl -s http://localhost:3000 >/dev/null && echo "web up"
docker logs nexstudio-worker-1 --tail 5   # expect: listening on site-render
```

> `prisma migrate deploy` does **not** work on this repo — migrations drifted.
> `db push` is the canonical bootstrap, same as dev.

Container names follow the checkout directory (e.g. `nexstudio-worker-1`); check
`docker compose ps` for yours.

---

## 7. Domain + HTTPS

Caddy is the simplest TLS terminator — auto certificates, two lines of config:

```bash
apt install -y caddy
cat > /etc/caddy/Caddyfile <<'EOF'
studio.yourdomain.com {
    reverse_proxy localhost:3000
}
EOF
systemctl reload caddy
```

Point the domain's A record at the server IP first — Caddy fetches the
certificate on first request. From then on the site is live at
`https://studio.yourdomain.com` and `APP_ORIGIN` already matches it.

---

## 8. Storage: local vs S3

**Local (default):** renders write into named volumes shared between web and
worker; the `/files` routes stream them. Zero config — right for a single box.

**S3-compatible** — needed the moment web and worker live on different machines,
or you want outputs to survive the host:

- **Self-hosted:** `docker compose --profile s3 up -d` adds MinIO + creates the
  `renders` bucket. Uncomment the `S3_*` block in compose for both web and
  worker, set `STORAGE_DRIVER=s3`, and `S3_PUBLIC_BASE_URL` to a URL clients
  can reach (e.g. `https://files.yourdomain.com/renders` behind Caddy).
- **Hosted:** Backblaze B2 / Cloudflare R2 are the cheap options — point
  `S3_ENDPOINT` at them. Same envs, no code change.

Flow with S3 on: worker uploads finished outputs → `/files` routes answer with
a 302 to a 15-minute presigned GET. Job metadata still lives in postgres.

---

## 9. Scaling

Measured on this codebase: whiteboard/explainer ≈ 10–20 CPU-min per video,
presenter (Blender) ≈ 25–40 CPU-min.

| Load | Setup | ~Cost/mo |
|---|---|---|
| < 10k videos/mo | One CX32→AX42, web+worker+db together | $8–80 |
| ~10k (3k character) | AX42 + small web VPS | ~$80–120 |
| ~30k (9k character) | Web box + 2–3 worker boxes + S3 | ~$250–320 |

To scale out: run `docker compose up -d worker` on additional machines sharing
the same `DATABASE_URL`, switch storage to S3, raise
`RENDER_WORKER_CONCURRENCY` per box (~1 per 4 cores), raise
`STUDIO_MAX_QUEUED_RENDERS` if you want a deeper queue before 429s.

The constraint is queue wait, not money — renders are CPU-heavy and there is
zero per-render API spend. All inference (whisper, CLIP, icon art, gestures)
is local.

---

## 10. Day-2 operations

**Deploy an update**
```bash
git pull && docker compose up -d --build    # web+worker restart; queue survives
```

**Backups**
```bash
docker compose exec postgres pg_dump -U postgres studio | gzip > studio-$(date +%F).sql.gz
docker run --rm -v nexstudio_jobs-whiteboard:/a -v nexstudio_jobs-explainer:/b \
  -v nexstudio_jobs-presenter:/c -v nexstudio_jobs-boards:/d \
  -v $(pwd):/backup alpine tar czf /backup/jobs-$(date +%F).tgz /a /b /c /d
```
(Adjust volume names to your project prefix — `docker volume ls`.)
Nightly cron on both is enough; postgres is the irreplaceable one.

**Watch it**
```bash
docker compose logs -f worker        # render progress + failures
docker compose ps                    # health
```
Queue depth:
```bash
docker compose exec postgres psql -U postgres studio -c \
  "select state,count(*) from render_queue.job group by 1"
```

**Failure modes worth knowing**
- A render that dies writes `failed` to the job's `status.json` — the site
  shows it honestly. Jobs never sit at "running" forever; the runner
  guarantees a terminal status and queued jobs expire after 4 h.
- Worker restart mid-job: the pg-boss job completes or expires; nothing
  duplicates (`singletonKey` = job id, `retryLimit` = 0 by design — engines
  own their own terminal state).
- Everything is CPU-bound: slow renders under load mean add a worker, not a
  code problem.

---

## 11. Optional: move existing users/data

The Devin box's data doesn't come across automatically. To bring it:

```bash
# on the dev box
pg_dump "$DATABASE_URL" | gzip > studio-seed.sql.gz
# on the server
gunzip -c studio-seed.sql.gz | docker compose exec -T postgres psql -U postgres studio
```

Copy the four `engine_sources/*/out/*-jobs` trees into the named volumes to
keep old videos downloadable. Skip both for a clean launch.

---

## 12. Security checklist

- [ ] `STUDIO_TRUST_SECRET` generated, in `.env`, never committed
- [ ] `APP_ORIGIN` = the real https URL (origin gate depends on it)
- [ ] Firewall: only 22/80/443 open
- [ ] Postgres + MinIO ports not published to the internet
- [ ] Postgres password changed from the compose default
- [ ] Caddy serving https; http→https redirect is automatic
- [ ] Nightly pg_dump cron + volume tarball
- [ ] `.env` is `chmod 600`, root-owned

---

## 13. Verification after go-live

1. Open `https://yourdomain` — the studio loads.
2. Mint a tester guest pass on the server:
   `docker compose exec web npx tsx scripts/mint-tester-guest.ts`
   then open `https://yourdomain/api/v1/auth/guest?token=<token>`.
3. In the create flow, pick **Presenter** → a studio cast character →
   a background → leave *Director cuts* on → generate. The worker drains
   the job; watch `docker compose logs -f worker`.
4. Confirm the finished video downloads from the library, and the job's
   `result.json` carries `authorityId: P8_SITE_DISPATCH_V1` plus a
   `director` block and sha256'd artifacts — that is P8's evidence the
   render went through the certified path.
5. Re-run with *Infographics* on to see drawn-on icon discs on emphasis
   beats; with *Director cuts* off for the clean-captions-only variant.

1. `https://yourdomain` loads, signup works.
2. Create a whiteboard video (short script, kinetic text) — watch
   `docker compose logs -f worker` show `start` … `exit … code=0`, then the
   file downloads.
3. Repeat one explainer + one presenter render (presenter needs a saved cast
   member — create it in the studio UI first).
4. `psql ... render_queue.job` shows no stuck `created` rows.
5. Reboot the box once (`docker compose up -d` comes back clean) — proves
   restartability.

If all five pass, you're live. Total cost: the box + the domain — nothing else.
