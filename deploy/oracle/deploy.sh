#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$repo_root"
architecture=$(uname -m)
if [[ $architecture != x86_64 && $architecture != aarch64 ]]; then
  echo "This deployment supports x86_64 and aarch64 Linux." >&2
  exit 1
fi
if [[ ! -f deploy/oracle/.env ]]; then
  echo "Configure deploy/oracle/.env from its .env.example before deploying." >&2
  exit 1
fi
compose=(docker compose --env-file deploy/oracle/.env -f deploy/oracle/compose.yml)
if [[ $architecture == aarch64 ]]; then
  if [[ ${1:-} != --core ]]; then
    echo "For native Arm whiteboard/explainer deployment, run deploy.sh --core. Full 3D rendering still needs native Blender/MFA validation." >&2
    exit 1
  fi
  compose+=(-f deploy/oracle/compose.arm.yml)
  echo "Deploying the native Arm studio, AI, whiteboard and explainer services. 3D presenter rendering is disabled."
fi
"${compose[@]}" config --quiet
"${compose[@]}" build web ai
# Re-run the one-shot initializer on updates. It only bootstraps empty DBs;
# existing initialized databases follow the checked-in migrations.
"${compose[@]}" up -d --wait postgres ai
"${compose[@]}" run --rm db-init
"${compose[@]}" up -d --wait
"${compose[@]}" ps
curl --fail --silent --show-error http://127.0.0.1:3000/ >/dev/null
echo "Local web readiness passed. Verify the public HTTPS domain and sign-in flow next."
