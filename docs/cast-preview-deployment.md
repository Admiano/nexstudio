# Cast V9 application preview deployment

The application preview is configured to deploy from PR #45's `devin/1790231957-offerings-trim-two-families` branch. The explicit Node 24 Dockerfile avoids automatic Python detection caused by the separate rendering sources in this repository. Its context includes the complete public asset library and application source, while excluding engine authoring inputs and local credentials.

The Railway project contains the Next.js application and one private PostgreSQL service with a persistent volume. Application configuration uses `DATABASE_URL=${{Postgres.DATABASE_URL}}`, its HTTPS `APP_ORIGIN`, and a randomly generated `STUDIO_TRUST_SECRET`. Payment processing is disabled for this Cast-only test deployment.

Pre-deploy runs `node --import tsx scripts/cast-preview-db.ts`, `npm run db:deploy`, and `node --import tsx scripts/cast-preview-guest.ts` in that order. The database helper runs only with `CAST_PREVIEW_MODE=true` and only bootstraps when there are no public application tables. The repository's checked-in migrations are incremental from an existing Standalone V1 schema, so a new preview database is initialized from the authoritative Prisma schema and baselined. The custom immutable-audit trigger is also installed. The helper never resets existing application tables; subsequent deployments use normal migrations.

The guest helper runs only with `CAST_PREVIEW_MODE=true` and a configured `CAST_PREVIEW_GUEST_TOKEN`. It creates an isolated preview tester with zero credits and an expiring challenge for the existing guest-pass authentication route. It preserves the tester and saved Cast records across redeployments; neither credential values nor sign-in links are logged.

The Docker build uses a visibly non-secret placeholder solely for build-time configuration validation. The application requires the real trust secret from its runtime environment. No preview credentials are committed.

Browser certification and screenshots must be taken against a successful deployment, with its actual branch and commit verified from Railway deployment metadata. Video workers and motion/performance integration are outside this preview's scope.
