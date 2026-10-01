#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "public/cast")
need = set()
for face in range(3):
    for shade in ("red", "berry", "coral", "nude"):
        need.add(f"fem_lip_f{face}_{shade}.png")
for kind in ("sheath", "maxi", "column", "cocktail", "qipao"):
    for c in ("navy", "burgundy", "sage", "emerald", "rose"):
        need.add(f"fem_outfit_{kind}_{c}.png")
for kind in ("o1", "o2", "o3", "o4", "o5"):
    for c in ("navy", "ivory", "blue", "burgundy", "cream"):
        need.add(f"male_outfit_{kind}_{c}.png")
missing = sorted(x for x in need if not (root / x).is_file())
if missing:
    print(f"FAIL: {len(missing)} Cast V9 plate(s) missing")
    for x in missing: print(" -", x)
    raise SystemExit(1)
print(f"PASS: {len(need)} Cast V9 colour/lip plates present")
