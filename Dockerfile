# syntax=docker/dockerfile:1
# NexStudio — one image, two processes:
#   web:    node server.js            (Next standalone, :3000)
#   worker: node dist/render-worker.cjs (pg-boss render queue)
# Carries the full engine toolchain: ffmpeg, chromium (CDP), Blender 5.2.1,
# faster-whisper venv, MFA (conda), plus the Python deps the engines import.

# ---------- stage 1: build web + bundle worker ----------
FROM mirror.gcr.io/library/node:24-bookworm-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# env.ts requires a >=32-char trust secret whenever NODE_ENV=production —
# including build-time page-data collection. Throwaway value: it never reaches
# the runtime image and server envs resolve at run time.
RUN export STUDIO_TRUST_SECRET="$(head -c48 /dev/urandom | base64)" \
 && npx prisma generate && npm run build \
 && npx esbuild scripts/render-worker.ts --bundle --platform=node \
      --format=cjs --outfile=dist/render-worker.cjs

# ---------- stage 2: runtime ----------
FROM mirror.gcr.io/library/debian:bookworm-slim
ARG NODE_VERSION=24.19.0
ARG BLENDER_VERSION=5.2.1
ARG BLENDER_MINOR=5.2

RUN apt-get update && apt-get install -y --no-install-recommends \
      python3.11 python3.11-venv python3-pip ffmpeg \
      chromium fonts-dejavu fonts-liberation fonts-noto-color-emoji \
      ca-certificates curl xz-utils procps \
      libgl1 libglib2.0-0 libxrender1 libxkbcommon0 libegl1 libxi6 libxxf86vm1 libxfixes3 \
      libnss3 libnspr4 libasound2 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
      libxcomposite1 libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Node 24 (web + engine JS tools + bundled worker)
RUN curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" \
      | tar -xJ -C /opt
ENV PATH=/opt/node-v${NODE_VERSION}-linux-x64/bin:$PATH

# Blender 5.2.1 (presenter renders + nexstick baking)
RUN curl -fsSL "https://download.blender.org/release/Blender${BLENDER_MINOR}/blender-${BLENDER_VERSION}-linux-x64.tar.xz" \
      | tar -xJ -C /opt \
 && ln -s /opt/blender-${BLENDER_VERSION}-linux-x64/blender /usr/local/bin/blender

# faster-whisper venv (engine phoneme/word timing)
RUN python3.11 -m venv /opt/whisper \
 && /opt/whisper/bin/pip install --no-cache-dir faster-whisper==1.2.1

# Python deps the engines import under the system interpreter
RUN pip3 install --no-cache-dir --break-system-packages \
      pillow numpy scipy lxml edge-tts==7.2.8 OpenEXR

# MFA 3.4.2 via miniforge (presenter word timings; engines degrade gracefully without it)
RUN curl -fsSL https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -o /tmp/mf.sh \
 && bash /tmp/mf.sh -b -p /opt/mamba \
 && /opt/mamba/bin/mamba create -y -n mfa -c conda-forge montreal-forced-aligner=3.4.2 \
 && /opt/mamba/bin/mamba clean -afy && rm /tmp/mf.sh

WORKDIR /app

# Engine JS tools resolve playwright-core upward — install prod deps at root.
COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force

# App: standalone server + static + public
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public

# Engines + orchestration + the pieces the runner delegates to
COPY engine_sources ./engine_sources
COPY engines ./engines
COPY services ./services
COPY scripts/presenter-job.py ./scripts/presenter-job.py
COPY prisma ./prisma
COPY --from=build /app/src/generated ./src/generated
COPY --from=build /app/dist/render-worker.cjs ./dist/render-worker.cjs

ENV NODE_ENV=production \
    WHISPER_PYTHON=/opt/whisper/bin/python3 \
    NEXSTUDIO_WHISPER_PYTHON=/opt/whisper/bin/python3 \
    MFA_BIN=/opt/mamba/envs/mfa/bin/mfa \
    BLENDER_BIN=/usr/local/bin/blender \
    CHROME_PATH=/usr/bin/chromium \
    RENDER_QUEUE=on

EXPOSE 3000
CMD ["node", "server.js"]
