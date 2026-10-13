#!/usr/bin/env python3
"""Isolated fit of six CC0 formal garments to SceneBam's current approved v3/v6 meshes.

This deliberately does not reuse any old-suit .blend, transmute old preview images,
or modify production. Refit every donor garment from its original MHClO barycentric
body-vertex mapping onto the selected current approved male/female body in Blender.
The producer is the repository's already-audited Blender wardrobe builder.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/illustrated-family/build_formal_cast.py"
SOURCES = ROOT / "engine_sources/makehuman-lineart/NexStudio_Presenter_Reference/characters"
TARGETS = {
    "female": "NEXSTUDIO_V1_FEMALE_v3.blend",
    "male": "NEXSTUDIO_V1_MALE_v6.blend",
}
spec = importlib.util.spec_from_file_location("upstream_formal_bank_builder", BUILDER)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def live_source_scene(gender: str, dest: Path):
    source = SOURCES / TARGETS[gender]
    if not source.is_file():
        raise FileNotFoundError("SCENEBAM_CURRENT_APPROVED_SOURCE_NOT_FOUND: " + str(source))
    target = dest / f"SceneBam-approved-{gender}.blend"
    header = source.open("rb").read(7)
    if header == b"BLENDER":
        shutil.copyfile(source, target)
    else:
        with target.open("wb") as sink:
            subprocess.run(["zstd", "-q", "-d", "-c", str(source)], stdout=sink, check=True)
        if target.open("rb").read(7) != b"BLENDER":
            raise RuntimeError("SCENEBAM_APPROVED_SOURCE_UNREADABLE")
    return target, mod.sha256(source)

mod.source_scene = live_source_scene
mod.main()
if "--list" in sys.argv:
    sys.exit(0)
variant = sys.argv[sys.argv.index("--variant") + 1]
output = Path(sys.argv[sys.argv.index("--output-dir") + 1])
p = output / "build_provenance.json"
original = json.loads(p.read_text())
gender = original["gender"]
h = hashlib.sha256((SOURCES / TARGETS[gender]).read_bytes()).hexdigest()
assert original["originalSceneSha256"] == h, "SOURCE_PROVENANCE_MISMATCH"
original.update({
    "product": "SceneBam",
    "fitTarget": "Current approved original female v3 / male v6 character scene, not older illustrated V1",
    "approvedCharacterSource": "engine_sources/makehuman-lineart/NexStudio_Presenter_Reference/characters/" + TARGETS[gender],
    "approvedCharacterSourceSha256": h,
    "method": "recompute CC0 garment positions from selected approved body shaped coordinates; interpolate original Host.rig weights; never copy earlier garment meshes",
    "shipped": False,
    "visualAcceptance": "REQUIRES_REVIEW",
    "liveV21RenderPipeline": "not claimed - static genuine Blender renders from approved geometry"
})
p.write_text(json.dumps(original, indent=2) + "\n")
print("SCENEBAM_CURRENT_GEOMETRY_REFIT_COMPLETE", variant, h, flush=True)
