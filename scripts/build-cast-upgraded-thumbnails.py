#!/usr/bin/env python3
"""Crop upgraded presenter renders into the Cast picker images.

Supply renders named female-default.png, male-default.png, female-braid.png,
female-face1.png, female-face2.png, male-face1.png, male-face2.png,
female-{sheath,maxi,column,cocktail,qipao}.png and
male-{bald,polo,tee,shirt,knit,fisherman}.png in --renders.
Use render-character-system.py for the packaged looks and the Cast request
builder for the defaults and female braid so the images match the live renderer.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "public/cast/options/v21"
BOXES = {
    "dress": (0.25, 0.23, 0.75, 0.93),
    "top": (0.19, 0.23, 0.81, 0.82),
    "bottom": (0.23, 0.71, 0.77, 1.0),
}
OPTIONS = {
    "female": {
        "character": {"female": "default"},
        "face": {0: "default", 1: "face1", 2: "face2"},
        "hair": {"long": "default", "bob": "sheath", "bangs": "qipao", "bun": "cocktail", "braid": "braid"},
        "dress": {style: style for style in ("sheath", "maxi", "column", "cocktail", "qipao")},
    },
    "male": {
        "character": {"male": "default"},
        "face": {0: "default", 1: "face1", 2: "face2"},
        "hair": {"bald": "bald", "crop": "tee", "quiff": "default", "braids": "knit", "swept": "fisherman"},
        "top": dict(zip(("o1", "o2", "o3", "o4", "o5"), ("polo", "tee", "shirt", "knit", "fisherman"))),
        "bottom": dict(zip(("trousers", "straight-jeans", "chinos", "classic-jeans", "wool-trousers"),
                           ("polo", "tee", "shirt", "knit", "fisherman"))),
    },
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--renders", type=Path, required=True)
    args = parser.parse_args()
    records = []
    for character, categories in OPTIONS.items():
        for category, options in categories.items():
            for key, style in options.items():
                source = args.renders / f"{character}-{style}.png"
                with Image.open(source) as original:
                    image = original.convert("RGBA")
                if category in ("character", "face", "hair"):
                    bounds = image.getchannel("A").getbbox()
                    if bounds is None:
                        raise ValueError(f"Render has no visible presenter: {source}")
                    x0, y0, x1, y1 = bounds
                    width, height = x1 - x0, y1 - y0
                    if category == "character":
                        crop = (x0 - width * .04, y0 - height * .02,
                                x1 + width * .04, y0 + height * .90)
                    else:
                        middle = (x0 + x1) / 2
                        crop = (middle - width * .39, y0 - height * .02,
                                middle + width * .39, y0 + height * .36)
                else:
                    left, top, right, bottom = BOXES[category]
                    crop = (left * image.width, top * image.height,
                            right * image.width, bottom * image.height)
                image = image.crop(tuple(round(value) for value in crop))
                image.thumbnail((212, 212), Image.Resampling.LANCZOS)
                canvas = Image.new("RGB", (224, 224), "white")
                canvas.paste(image, ((224 - image.width) // 2, (224 - image.height) // 2), image)
                destination = OUTPUT / character / category / f"{key}.webp"
                destination.parent.mkdir(parents=True, exist_ok=True)
                canvas.save(destination, format="WEBP", quality=92, method=6)
                records.append({
                    "path": str(destination.relative_to(ROOT)),
                    "source": source.name,
                    "sourceSha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    "renderVersion": "approved-v3-v6-corrected-original-performance-v21-oral-soft",
                })
    (OUTPUT / "SOURCES.json").write_text(json.dumps(records, indent=2) + "\n")
    print("CAST_UPGRADED_IMAGES", len(records))


if __name__ == "__main__":
    main()
