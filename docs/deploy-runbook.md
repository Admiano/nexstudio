# NexStudio self-host runbook

One image, two processes. The web app serves the site + API on :3000; the
worker drains the render queue and runs the engines. Postgres is the only
required dependency; object storage is optional.

## 1. Build and run (single VPS)

```bash
git clone <repo> && cd nexstudio
docker compose up -d --build
```

That starts `postgres`, `web`, and `worker`. Visit http://<host>:3000 —
sign-up/login works as on dev; videos render through the queue.

Default profile renders to local disk (job dirs live on the named volumes).
Outputs are served by the app's own `/api/v1/*/files/` routes.

## 2. Scaling renders

Render jobs are CPU-bound. The worker default is `RENDER_WORKER_CONCURRENCY=1`
(one render at a time — the right setting on one box). To go faster:

- more cores on the same box → bump `RENDER_WORKER_CONCURRENCY` (roughly
  one worker per 4 cores);
- more boxes → run `worker` services on other machines pointing at the same
  `DATABASE_URL`. The queue is Postgres (`render_queue` schema), so any
  worker anywhere drains the same queue. Only `web` needs the public port.
- Queue backpressure: `STUDIO_MAX_QUEUED_RENDERS` (default 25) — how many
  queued+running jobs a user-facing POST accepts before returning 429.

## 3. Object storage (multi-box or disk-bounded hosts)

Outputs default to the shared `jobs-*` volumes, which only works when web
and worker are on the same host. For split hosts or large retention, switch
to S3-compatible storage (MinIO in this repo, or Backblaze B2 ~free tier):

```bash
docker compose --profile s3 up -d   # adds MinIO + creates the "renders" bucket
```

Then set on `web` **and** `worker`:

```
STORAGE_DRIVER=s3
S3_ENDPOINT=http://minio:9000        # or https://s3.us-west-004.backblazeb2.com
S3_BUCKET=renders
S3_ACCESS_KEY_ID=...
S3_SECRET_ACCESS_KEY=...
S3_REGION=us-east-1                  # b2 region when using B2
```

Worker uploads `files/*.mp4` after each successful render; the `/files`
route 302s to a presigned GET (15 min). Nothing else changes shape.

## 4. Domain + TLS

Put a reverse proxy in front of :3000. Caddy is the two-line option:

```
studio.example.com {
    reverse_proxy localhost:3000
}
```

Set `NEXTAUTH_URL`/`APP_ORIGIN`-style origin envs per `.env.example` and keep
`Origin`-checked POSTs working by forwarding the `Host` header (default in
Caddy/nginx). WebSocket/SSE aren't used; plain HTTP proxying is enough.

## 5. Env reference (production)

| Var | Purpose |
| --- | --- |
| `DATABASE_URL` | Postgres DSN — required everywhere |
| `RENDER_QUEUE` | `on` (default in image) — `off` reverts to in-process spawn |
| `RENDER_WORKER_CONCURRENCY` | jobs per worker process (default 1) |
| `STUDIO_MAX_QUEUED_RENDERS` | backlog cap before 429 (default 25) |
| `STORAGE_DRIVER` | `local` (default) or `s3` |
| `S3_*` | endpoint/bucket/keys/region/public base for object storage |
| `WHISPER_PYTHON` | faster-whisper venv (image: `/opt/whisper/bin/python3`) |
| `MFA_BIN` | MFA binary (image: `/opt/mamba/envs/mfa/bin/mfa`) |
| `BLENDER_BIN` | Blender (image: `/usr/local/bin/blender`) |
| `CHROME_PATH` | Chromium for the explainer CDP renderer |

## 6. Ops notes

- **Nothing runs without the DB**: auth, drafts, queue, memory all Postgres.
- **Job status survives crashes**: jobs stuck `running` for >1h stop counting
  toward the capacity gate; the worker marks terminal status itself.
- **Golden pack**: `python3 services/studio-family-engines/golden_check.py
  verify all` inside the worker container re-renders all 12 subtypes and
  compares fingerprints — run after any engine change before shipping.
- **P8 evidence**: every job writes `result.json` next to `status.json`;
  cast-linked jobs also write CAST-scope memory and a `VERSION_READY`
  production on completion.
- **HF model cache**: whisper/CLIP models download into `/root/.cache/
  huggingface` — the `hf-cache` volume keeps it warm across restarts.
