#!/usr/bin/env bash
# Parallel clip baker: one Blender worker per clip, P-way parallel.
# Usage: bake_parallel.sh <clip...> [--vault PATH] [--blend PATH] [--out DIR] [--res WxH] [--cam VIEW]
set -u
BLEND="${BLEND:-$HOME/nexstick_rigs/mh_rigged.blend}"
VAULT="${VAULT:-$(dirname "$0")/../compiled/nex_vault_v5.json}"
OUTROOT="${OUTROOT:-$(dirname "$0")/../../nexstick/baked}"
RES="${RES:-300x400}"
CAM="${CAM:-side}"
P="${P:-6}"
BLENDER="${BLENDER:-/usr/local/bin/blender}"
ARGS=()
for clip in "$@"; do
  ARGS+=("$clip")
done
printf '%s\n' "${ARGS[@]}" | xargs -P "$P" -I{} sh -c \
  '"$0" -b "$1" --python "$2/mh_bake.py" -- --vault "$3" --clip {} --out "$4/{}" --res "$5" --cam "$6" > "$4/{}.log" 2>&1' \
  "$BLENDER" "$BLEND" "$(dirname "$0")" "$VAULT" "$OUTROOT" "$RES" "$CAM"
echo "bake done -> $OUTROOT"
