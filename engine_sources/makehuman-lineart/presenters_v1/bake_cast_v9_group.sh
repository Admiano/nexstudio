#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
export PV1="$ROOT/scripts"
export MH_ROOT="${MH_ROOT:?MH_ROOT must point to the MakeHuman assets checkout}"
export OUT="${OUT:?OUT must point to this group's raw render directory}"
export BAKE_OUT="$OUT"
export PLATE_DST="${PLATE_DST:?PLATE_DST must point to this group's packed plate directory}"
export BLENDER="${BLENDER:?BLENDER must point to Blender 5.2.x}"
GROUP="${CAST_V9_GROUP:?CAST_V9_GROUP is required}"
source "$PV1/env.sh"
mkdir -p "$OUT" "$PLATE_DST"

run(){
  echo "==> GROUP=$GROUP LOOK=$1 VARIANT=${2:-}"
  LOOK="$1" VARIANT="${2:-}" "$BLENDER" -b "$ROOT/scenes/BASE_V58.blend" --python "$PV1/castbake3.py"
}

case "$GROUP" in
  lip)
    export BODY_SKINS=medium
    run fem_body
    unset BODY_SKINS
    export CAST_V9_EXPECTED=12
    ;;
  fem_long|fem_bob|fem_bangs|fem_bun|fem_braid)
    for c in navy burgundy sage emerald rose; do run "$GROUP" "$c"; done
    export CAST_V9_EXPECTED=5
    ;;
  male_O1|male_O2|male_O3|male_O4|male_O5)
    for c in navy ivory blue burgundy cream; do run "$GROUP" "$c"; done
    export CAST_V9_EXPECTED=5
    ;;
  *)
    echo "Unknown CAST_V9_GROUP: $GROUP" >&2
    exit 2
    ;;
esac

python3 "$PV1/castpack_v9_delta.py"
count="$(find "$PLATE_DST" -maxdepth 1 -type f -name '*.png' | wc -l | tr -d ' ')"
if [ "$count" != "$CAST_V9_EXPECTED" ]; then
  echo "FAIL group $GROUP produced $count/$CAST_V9_EXPECTED PNG plates" >&2
  exit 1
fi
echo "PASS group $GROUP produced $count/$CAST_V9_EXPECTED PNG plates"
