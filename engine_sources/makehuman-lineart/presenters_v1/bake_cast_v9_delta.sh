#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
export PV1="$ROOT/scripts"
export MH_ROOT="${MH_ROOT:?MH_ROOT must point to the checked-out mh-assets tree}"
export OUT="${OUT:-/home/runner/work/cast-v9-out}"
export BAKE_OUT="$OUT"
export PLATE_DST="${PLATE_DST:-/home/runner/work/cast-v9-plates}"
source "$PV1/env.sh"
B="${BLENDER:?BLENDER must point to Blender 5.2.x}"
SCENE="$ROOT/scenes/BASE_V58.blend"
BAKER="$PV1/castbake3.py"
mkdir -p "$OUT" "$PLATE_DST"

run(){ echo "==> LOOK=$1 VARIANT=${2:-}"; LOOK="$1" VARIANT="${2:-}" "$B" -b "$SCENE" --python-exit-code 1 --python "$BAKER"; }

# Female body generates the three canonical face/medium-skin bases plus
# face-specific red/berry/coral/nude renders used for true lipstick deltas.
export BODY_SKINS=medium
run fem_body
unset BODY_SKINS

for c in navy burgundy sage emerald rose; do
  for look in fem_long fem_bob fem_bangs fem_bun fem_braid; do run "$look" "$c"; done
done
for c in navy ivory blue burgundy cream; do
  for look in male_O1 male_O2 male_O3 male_O4 male_O5; do run "$look" "$c"; done
done

python3 "$PV1/castpack_v9_delta.py"
python3 "$PV1/check_cast_v9_assets.py" "$PLATE_DST"
