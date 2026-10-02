FROM node:24-bookworm-slim AS base
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends openssl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

FROM base AS build
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG APP_ORIGIN
ENV NEXT_TELEMETRY_DISABLED=1
# Page collection imports the server configuration. This build-only value is
# deliberately not a runtime credential, and is never copied into the runtime ENV.
RUN STUDIO_TRUST_SECRET=build-only-placeholder-never-use-as-runtime-secret npm run build
RUN mkdir -p .next/standalone/public .next/standalone/.next/static \
    && cp -a public/. .next/standalone/public/ \
    && cp -a .next/static/. .next/standalone/.next/static/

FROM base AS runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 curl xz-utils libegl1 libgl1 libxi6 libxrender1 libxfixes3 libxkbcommon0 libsm6 libice6 libgomp1 \
    && curl --fail --location --retry 3 https://download.blender.org/release/Blender5.2/blender-5.2.0-linux-x64.tar.xz -o /tmp/blender.tar.xz \
    && echo '96f6c181a30f4950607839dc84d42a354b250d8a0231b098b59b7bc69c351c48  /tmp/blender.tar.xz' | sha256sum -c - \
    && mkdir /opt/blender \
    && tar -xJf /tmp/blender.tar.xz --strip-components=1 -C /opt/blender \
    && rm /tmp/blender.tar.xz \
    && rm -rf /var/lib/apt/lists/*
ENV BLENDER_BIN=/opt/blender/blender
ENV CAST_PROJECT_ROOT=/app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
# Retain Prisma CLI and the schema so pre-deploy migrations run from this image.
COPY --from=build --chown=node:node /app ./
RUN python3 scripts/install-cast-assets.py \
    && node --import tsx scripts/cast-warm-defaults.ts \
    && python3 scripts/cast-preview-worker.py --drain \
    && node --import tsx scripts/cast-warm-defaults.ts --check \
    && chown -R node:node engine_sources/makehuman-lineart/out
USER node
EXPOSE 3000
CMD ["node", ".next/standalone/server.js"]
