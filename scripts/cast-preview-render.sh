#!/usr/bin/env bash
set -e
source "$CAST_SOURCE_DIR/presets.sh"
if [ "$CAST_CHARACTER" = female ]; then
  female_look "$CAST_HAIR_STYLE" "$CAST_HAIR_HEX" "$CAST_SKIN_HEX" "$CAST_LIP_HEX" "$CAST_NECK" "$CAST_DRESS" "$CAST_DRESS_HEX" 0
  export SIDES=1,-1
else
  male_look "$CAST_MALE_LOOK" "$CAST_WATCH" 0
  export HAIR="$CAST_MALE_HAIR" HCOL="$CAST_HAIR_HEX" HDYE="$CAST_HAIR_DYE" STONE="$CAST_SKIN_HEX" MG="$CAST_GARMENTS" WATCH="$CAST_WATCH"
fi
exec "$BLENDER_BIN" -b "$CAST_SOURCE_DIR/scenes/BASE_V58.blend" --threads "${CAST_RENDER_THREADS:-4}" --python-exit-code 1 --python "$CAST_RENDER_ENTRY" -- "$@"
