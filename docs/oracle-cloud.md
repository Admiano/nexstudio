# Deploy NexStudio to Oracle Cloud

## Public homepage and pricing link

The public Caddy configuration serves an isolated static homepage and pricing at
`studio.nexmarkets.xyz`. Only `/`, `/pricing` and their own static assets are
available. Other pages, sign-in APIs, production APIs and POST requests
return 404 on that hostname. The original address
`nexstudio.150-136-4-228.sslip.io` serves the full authenticated application.
`STUDIO_DOMAIN` selects the restricted public site; `STUDIO_APP_DOMAIN` selects
the full app host, and `APP_ORIGIN` must use that full app host so forms and
sign-in links work. Caddy routes the two hostnames separately.

Additional full-app domains use `STUDIO_APP_ALIASES` and
`APP_ADDITIONAL_ORIGINS`. For example, point the `@` A record for
`scenebam.online` to `150.136.4.228`, then configure the existing private env:

```console
node deploy/oracle/add-app-domain.cjs deploy/oracle/.env scenebam.online
```

The helper preserves the primary app origin, other settings and a private
backup. Deploy an app image that includes additional-origin support, then
recreate web and Caddy to load the updated environment and host routing.
Caddy obtains HTTPS automatically once DNS points at the VM. The additional
hostname serves the same full app; email sign-in stays on the hostname used.
Keep `studio.nexmarkets.xyz` out of the additional app hostnames and origins.

The full application runs from its Docker image. Pulling source or changing
host routing does not update that image: build the current working tree and
deploy the new image when publishing application changes. Verify the running
build, rather than relying only on the checkout's Git revision.

After pulling an update on the VM, refresh just the public homepage with:

```console
bash deploy/oracle/deploy-homepage.sh
```

This packages the committed homepage, pricing components, styles and referenced media
from the current Git revision, builds a separate Next.js static export, and
restarts only Caddy. It does not rebuild the rendering stack or migrate the
database. Build output stays in the ignored `deploy/oracle/homepage/` folder.
`homepage-source.json` records the Git revision and source hashes outside
the public site. The homepage's existing links remain intact; links to other
pages and sign-in requests fail because those routes are unavailable.

## External Enclave model

The private dotenv files can use an external Enclave model for script generation
and plan previews. With the Enclave creative provider, URL, model and referenced
API key already configured, synchronize the app's provider settings locally:

```console
node scripts/configure-enclave.cjs .env .env.local deploy/oracle/.env
```

The helper keeps private backups, preserves other credentials and writes the
`STUDIO_SCRIPT_OPENAI_*`, `STUDIO_PLAN_PREVIEW_OPENAI_*`,
`NEXMIND_STUDIO_SCRIPT_*` and plan-preview routing variables together.
On the VM, use its private `deploy/oracle/.env` as the credential source, then
recreate the app containers so they load the new environment. Compose respects
these external endpoint and credential settings; empty settings retain the
private local AI defaults. Rendering the saved plan still runs on the VM.

This deployment runs the web app, render worker, durable studio worker,
account-data worker, Postgres, local Qwen AI server, and Caddy HTTPS proxy.
The app and workers share persistent job and object storage. Postgres and AI
have no public ports. Landscape, square and portrait remain available.

## Server

For the paid deployment, use **VM.Standard.E4.Flex (AMD), 2 OCPUs
(4 vCPUs), 16 GB RAM, Ubuntu 24.04 LTS x86_64 and a 100 GB boot volume**.
Choose standard on-demand capacity, leave fault domain automatic, and keep
the public subnet and automatically assigned public IPv4 address. This is a
starting configuration to validate with actual renders. The full image
includes the x86 Blender/MFA toolchain; it downloads model files and cast
assets during the first build.

At USD list rates of $0.025/OCPU-hour and $0.0015/GB-hour, compute is
`(2 * 0.025 + 16 * 0.0015) * 730 = $54.02` per 730-hour month. Storage and
taxes are additional unless included in your account allowance. Confirm
the console's estimate before creating the VM. If E4 has no capacity,
**VM.Standard.E5.Flex** with the same CPU/RAM is an x86 alternative:
at $0.03/OCPU-hour and $0.002/GB-hour it is about **$67.16/month** for compute.
[Oracle VM pricing](https://www.oracle.com/cloud/compute/virtual-machines/cost-estimator/)

Paid shapes can use remaining eligible trial credit. To keep paid resources
after the trial, upgrade through the console's **Upgrade** link to
**Pay As You Go**. This account change must be completed in your own Oracle
console. Paid resources are reclaimed after the trial without an upgrade.
[Oracle account upgrade and trial policy](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm)

Use the normal `sudo bash deploy/oracle/deploy.sh` command for this x86 VM;
the `--core` flag and Arm Compose override belong to the Arm deployment.

For **Always Free**, create an Arm **VM.Standard.A1.Flex** instance in your
home region: **2 OCPUs, 12 GB RAM, Ubuntu 24.04 (Arm), 100 GB boot volume**.
Confirm the console's Always Free allowance and keep all your boot/block
volumes within the tenancy's 200 GB combined allowance. Use the default
balanced storage performance. All three sizes remain enabled.

Render job concurrency, explainer frame workers, and local AI request slots
default to the number of available CPUs. Narration uses automatic CPU
threading. No fixed one-job, eight-frame-worker or one/two-thread cap is
applied. Positive integer overrides have no fixed maximum:
`RENDER_WORKER_CONCURRENCY`, `RENDER_FRAME_WORKERS`, `WHISPER_CPU_THREADS`,
`KOKORO_CPU_THREADS`, `AI_THREADS` and `AI_PARALLEL`.
Parallelism changes how work shares the VM's existing CPU and memory.

The native Arm image runs the app, local AI, whiteboard and explainer engines.
It uses Arm Node/Chromium/Python packages and compiles llama.cpp natively.
It includes offline narration and word timing. 3D presenter rendering is
explicitly disabled in this image because the full image uses x86 Blender
and MFA binaries; a native 3D toolchain must be built and validated separately.

Trial credits can provision larger machines temporarily, but paid resources
are reclaimed when the trial ends unless you upgrade. Stay at 2 OCPUs/12 GB
total across Ampere instances for the continuing Always Free account.
[Oracle Always Free resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
[Oracle trial expiration](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm)

In the OCI Console, open **Compute → Instances → Create instance**. Choose
the settings above, a public subnet with an assigned public IPv4 address,
and upload your SSH public key. The default Ubuntu SSH username is `ubuntu`.
If Oracle reports insufficient A1 capacity, try another availability domain
in your home region or retry later. The paid AMD configuration above is the
alternative when a paid deployment is intended.

To create a dedicated SSH key pair on this PC, run:

```console
node scripts/prepare-oracle-ssh.cjs
```

Upload only `certs/oracle-nexstudio.key.pub`. Keep the private `.key` file on
your PC. Both files are excluded from the source archive and Docker context.

Use a public subnet and public IP. Point the domain's A record at that IP.
Allow TCP 80 and 443 in the VM's OCI network security group or security list,
and SSH from your administrator IP. Check the host firewall as well. The app
listens on host loopback 3000 for local checks; only Caddy exposes HTTP/HTTPS.
[OCI security lists](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securitylists.htm)

If you do not own a domain, an IP-based hostname such as
`nexstudio.203-0-113-10.sslip.io` can be used for initial testing (replace the
example address with the VM's actual public IPv4 address). That DNS service
resolves embedded IPs and supports individual HTTPS certificates through
Caddy. A custom domain can be configured later without rotating secrets.
[sslip.io / nip.io DNS and TLS](https://nip.io/)

## Prepare this checkout

Deploy this working tree, including its uncommitted fixes, rather than
cloning an older revision. Exclude `.env*`, `.git`, `node_modules`, `.next`,
`tmp`, `llm`, generated `engines`, data, uploads, backups and private keys
from the source archive. Keep the tracked engine source archives.

Create that source archive with:

```console
python scripts/package-oracle.py
```

It writes `tmp/nexstudio-oracle.tar.gz` from tracked and untracked source
files, excluding secrets and generated runtime data. Transfer and extract it
into an empty release directory on the VM, then transfer the private Oracle
environment file separately.

On the local PC with Node and dependencies installed:

```console
node deploy/oracle/configure.cjs studio.yourdomain.com app.yourdomain.com
```

This writes ignored `deploy/oracle/.env`, generates independent database and
AI secrets, keeps an existing trust secret, and carries over the configured
Resend sender and key. It prints no secrets. Run it again to change the
domain without rotating credentials. Previous hostnames are kept in
`STUDIO_ALIASES` and redirect to the new HTTPS origin, preserving saved links.
Transfer this file separately over SSH;
never put it in the source archive or commit it. Add production provider and
payment settings to this private file as needed.

Alternatively, copy `deploy/oracle/.env.example` on the VM and fill it in.
Use separate `openssl rand -hex 32` values for the three secrets. Set
`RESEND_API_KEY` and `EMAIL_FROM` to enable real sign-in emails.

## Install and start

From the checkout on the VM:

```bash
sudo bash deploy/oracle/setup-ubuntu.sh
sudo bash deploy/oracle/deploy.sh
```

For the native Arm deployment, use:

```bash
sudo bash deploy/oracle/setup-ubuntu.sh
sudo bash deploy/oracle/deploy.sh --core
```

`--core` explicitly chooses the 2D video deployment. It preserves all three
aspect ratios and refuses 3D presenter submissions before creating a job.
The Arm image has not been built or rendered on a live VM yet; those checks
are required after the instance is created.

Docker is installed from its official Ubuntu apt repository.
[Docker installation instructions](https://docs.docker.com/engine/install/ubuntu/)

The initializer bootstraps only an empty database, installs the immutable
audit trigger and baselines the repo's incremental migrations. It does not
seed a user or bypass authentication. Existing initialized databases use
`prisma migrate deploy`. No database reset or `--accept-data-loss` is used.

The AI service compiles pinned llama.cpp `b6605` and downloads the existing
Qwen 2.5 3B model into its own persistent volume. Interrupted model downloads
resume on restart. It uses an internal API key and is never exposed publicly.

The app image also downloads the offline Kokoro explainer voice bundle and
includes the Microsoft endpoint patch, narration timing model and extracted
WordNet data. Local Windows model files are excluded from the source archive.

## Verify and update

```bash
sudo docker compose --env-file deploy/oracle/.env -f deploy/oracle/compose.yml ps
sudo docker compose --env-file deploy/oracle/.env -f deploy/oracle/compose.yml logs --tail 50 web render-worker ai db-init
curl -I https://studio.yourdomain.com
```

On Arm, add `-f deploy/oracle/compose.arm.yml` to every Compose command above
so it uses the same deployment configuration as `deploy.sh --core`.

Before calling the deployment complete, verify HTTPS, a real sign-in link,
AI script generation, and a video render in all three sizes. Uploaded source
scanning additionally needs a configured ClamAV service and upload worker;
those are not enabled in this initial deployment. Paid production reviewer
and provider routes require the account's own production configuration.

Named volumes preserve database, jobs, objects, models and TLS certificates.
Back up the database and objects before schema updates. Upload revised source
and rerun `deploy.sh`; retain the same private `.env`. Do not use `down -v`
unless deliberately deleting the entire deployment's data.

This configuration starts a fresh database. Moving existing local users,
projects and videos is a separate database and volume transfer that must
preserve the trust secret and stored object paths.
