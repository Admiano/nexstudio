#!/usr/bin/env python3
"""Reassemble oversized Blender scenes stored as GitHub-safe parts."""
from pathlib import Path
import hashlib, json
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/"scene-parts.json").read_text())
for scene in sorted({x["scene"] for x in manifest["parts"]}):
    entries=sorted((x for x in manifest["parts"] if x["scene"]==scene), key=lambda x:x["index"])
    out=ROOT.parent.parent.parent / scene
    out.parent.mkdir(parents=True,exist_ok=True)
    data=b"".join((ROOT.parent.parent.parent / x["part"]).read_bytes() for x in entries)
    out.write_bytes(data)
    print(f"materialized {scene} ({len(data)} bytes, sha256={hashlib.sha256(data).hexdigest()})")
