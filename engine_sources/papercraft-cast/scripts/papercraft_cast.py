#!/usr/bin/env python3
"""Cast-queue driver for papercraft plates.

Reads a cast spec (manifests/cast.papercraft.schema.json), resolves the
chassis entry from manifests/papercraft-facets.json, and shells out to
Blender with the matching renderer.

    python3 papercraft_cast.py <spec.json> [--dry-run]

Palette overrides are passed to render_q2.py via $PAPER_PALETTE (a JSON
file written next to the spec): material-name fragment -> [r,g,b] tint.
"""

import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACETS = json.load(open(os.path.join(ROOT, "manifests", "papercraft-facets.json")))


def resolve(spec):
    cid = spec["chassis"]["id"]
    entry = FACETS["chassis"].get(cid)
    if not entry:
        raise SystemExit(f"unknown chassis '{cid}' — have: {sorted(FACETS['chassis'])}")
    return cid, entry


def build_cmd(spec, root=ROOT):
    cid, entry = resolve(spec)
    out = os.path.abspath(spec["output"]["path"])
    script = os.path.join(root, entry["renderer"])
    dec = spec["chassis"].get("decimate") or entry.get("decimate") or 1.0
    cmd = ["blender", "-b", "--python", script, "--"]
    if entry["renderer"].endswith("rain_paper.py"):
        cmd += [out, str(dec)]
    elif entry["renderer"].endswith("render_q2.py"):
        cmd += [os.path.join(root, entry["source"]), out]
    elif entry["renderer"].endswith("assemble_paper.py"):
        cmd += [out]
    return cmd, out


def main():
    spec_path = sys.argv[1]
    dry = "--dry-run" in sys.argv
    spec = json.load(open(spec_path))
    if spec.get("style") != "papercraft":
        raise SystemExit(f"spec style must be 'papercraft', got {spec.get('style')!r}")

    env = os.environ.copy()
    pal = (spec.get("look") or {}).get("paletteOverrides")
    if pal:
        fd, pal_path = tempfile.mkstemp(suffix=".json", prefix="paperpal_")
        with os.fdopen(fd, "w") as f:
            json.dump(pal, f)
        env["PAPER_PALETTE"] = pal_path

    cmd, out = build_cmd(spec)
    print("chassis:", spec["chassis"]["id"])
    print("cmd:", " ".join(cmd))
    if dry:
        return
    subprocess.run(cmd, env=env, check=True)
    print("WROTE", out)


if __name__ == "__main__":
    main()
