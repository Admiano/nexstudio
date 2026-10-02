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

FROM base AS runtime
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000
# Retain Prisma CLI and the schema so pre-deploy migrations run from this image.
COPY --from=build --chown=node:node /app ./
USER node
EXPOSE 3000
CMD ["npm", "run", "start", "--", "--hostname", "0.0.0.0"]
