#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
export PV1="$ROOT/scripts"
export MH_ROOT="${MH_ROOT:-/home/ubuntu/mh_assets}"
export OUT="${OUT:-/home/ubuntu/work/castbake_v9}"
export BAKE_OUT="$OUT"
export PLATE_DST="${PLATE_DST:-$(cd "$ROOT/../../.." && pwd)/public/cast}"
source "$PV1/env.sh"
B="${BLENDER:-blender}"
SCENE="$ROOT/scenes/BASE_V58.blend"
BAKER="$PV1/castbake3.py"

run(){ echo "==> LOOK=$1 VARIANT=${2:-}"; LOOK="$1" VARIANT="${2:-}" "$B" -b "$SCENE" --python "$BAKER"; }

run fem_body
run male_body
run fem_hands
run male_hands

for look in fem_long fem_bob fem_bangs fem_bun fem_braid; do run "$look"; done
for look in male_O1 male_O2 male_O3 male_O4 male_O5; do run "$look"; done
for look in male_watch_o1 male_watch_o2 male_watch_o3 male_watch_o4 male_watch_o5; do run "$look"; done

for c in navy burgundy sage emerald rose; do
  for look in fem_long fem_bob fem_bangs fem_bun fem_braid; do run "$look" "$c"; done
done
for c in navy ivory blue burgundy cream; do
  for look in male_O1 male_O2 male_O3 male_O4 male_O5; do run "$look" "$c"; done
done

python "$PV1/castpack4.py"
python "$PV1/check_cast_v9_assets.py" "$PLATE_DST"
echo "CAST V9 BAKE COMPLETE: $PLATE_DST"
