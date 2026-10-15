#!/usr/bin/env bash
# Read-only Oracle VM check: confirms that BOTH web and actual render worker
# run exact tracked formal wardrobe code and ship checksum-pinned genuine assets.
# This is not a substitute for art, collision, motion, or full-video sign-off.
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$repo_root"
if [[ ! -f deploy/oracle/.env ]]; then
  echo "Oracle .env not present; run on the deployed Oracle VM." >&2
  exit 2
fi
compose=(docker compose --env-file deploy/oracle/.env -f deploy/oracle/compose.yml)
arch=$(uname -m)
if [[ $arch != x86_64 ]]; then
  echo "CAST_PARITY_UNAVAILABLE: 3D presenter production requires validated x86_64 Blender host; Oracle Arm core disables it." >&2
  exit 3
fi
"${compose[@]}" config --quiet
for service in web render-worker; do
  if ! "${compose[@]}" ps --status running --services | grep -Fxq "$service"; then
    echo "CAST_PARITY_SERVICE_NOT_RUNNING: $service" >&2
    exit 4
  fi
  printf 'CHECK %s: Blender and asset provenance\n' "$service"
  "${compose[@]}" exec -T "$service" blender --version | head -n 1
  "${compose[@]}" exec -T "$service" python3 /app/scripts/install-cast-formals.py
  "${compose[@]}" exec -T "$service" sh -c 'test -s /app/engine_sources/makehuman-lineart/presenters_v1/scenes/BASE_V58.blend'
  for relative in \
    scripts/cast-preview-worker.py \
    scripts/cast-render-assembled.py \
    scripts/cast-apply-formal.py \
    scripts/install-cast-formals.py \
    src/studio-v2/cast/render-config.ts \
    src/lib/cast-formal-availability.ts \
    config/scenebam-formal-assets.json; do
    if [[ ! -f "$relative" ]]; then
      echo "CAST_PARITY_SOURCE_MISSING: $relative" >&2
      exit 5
    fi
    expected=$(sha256sum "$relative" | cut -d ' ' -f1)
    actual=$("${compose[@]}" exec -T "$service" sha256sum "/app/$relative" | cut -d ' ' -f1)
    if [[ "$expected" != "$actual" ]]; then
      echo "CAST_PARITY_HASH_DRIFT: service=$service path=$relative expected=$expected actual=$actual" >&2
      exit 6
    fi
  done
  "${compose[@]}" exec -T "$service" sh -c 'test "${STUDIO_PRESENTER_ENABLED:-true}" != "false"' || {
    echo "CAST_PARITY_PRESENTER_DISABLED: $service" >&2;exit 7;
  }
  echo "CAST_PARITY_SOURCE_MATCH: $service"
done
echo 'CAST_PARITY_SOURCE_AND_ASSETS_PASS: both live containers match repo files and six pinned garment hashes.'
echo 'NOT CERTIFIED: full presenter video job, actual dress fit, collisions, art approval and motion integrity.'
echo 'This script intentionally does not modify SCENEBAM_FORMAL_WARDROBE_ENABLED or the certification manifest.'
