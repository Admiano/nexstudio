#!/usr/bin/env bash
# Usage: build.sh female|male OUT.blend   (set the look first via presets.sh, or use defaults)
set -e; D="$(cd "$(dirname "$0")" && pwd)"; source "$D/presets.sh"
BASE=${BASE:-$D/scenes/BASE_V58.blend}
case $1 in
 female) [ -n "$MODF" ] || female_look long "" "" "" fine mindfront_f_dress_11 2B3A5C;;
 male)   [ -n "$MODF" ] || male_look O3;;
esac
blender -b "$BASE" --python "$PV1/save.py" -- "$2"
