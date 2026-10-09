import json
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parent
SCENES = {
    "living_room": "Contemporary living room",
    "home_office": "Home office",
    "creator_studio": "Creator studio",
    "workplace": "Modern workplace",
    "cafe": "Neighborhood café",
    "kitchen": "Contemporary kitchen",
    "library": "Library and study",
    "classroom": "Training classroom",
    "terrace": "Garden terrace",
    "neutral_studio": "Neutral illustrated studio",
}
FORMATS = {
    "landscape": (1920, 1080),
    "square": (1080, 1080),
    "portrait": (1080, 1920),
}


def source_path(scene: str, aspect: str) -> Path:
    if aspect == "landscape":
        return ROOT / "masters" / f"{scene}.png"
    return ROOT / "variants" / f"{scene}_{aspect}_source.png"


manifest = {
    "version": 1,
    "family": "illustrated",
    "description": "Illustrated companions to the photographic catalog, composed separately for each aspect ratio.",
    "scene_ids": SCENES,
    "formats": {
        name: {"width": width, "height": height, "aspect": f"{width}:{height}"}
        for name, (width, height) in FORMATS.items()
    },
    "assets": {},
    "sources": {},
    "framing": "Front-facing hips-up presenter with both hands visible; select the asset for the output aspect.",
}

for scene in SCENES:
    manifest["assets"][scene] = {}
    manifest["sources"][scene] = {}
    for aspect, dimensions in FORMATS.items():
        source = source_path(scene, aspect)
        if not source.is_file():
            raise FileNotFoundError(source)
        output = ROOT / "assets" / aspect / f"{scene}.jpg"
        output.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(source) as image:
            prepared = ImageOps.fit(
                image.convert("RGB"),
                dimensions,
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )
        prepared.save(output, format="JPEG", quality=95, subsampling=0, optimize=True)
        manifest["assets"][scene][aspect] = str(output.relative_to(ROOT))
        manifest["sources"][scene][aspect] = str(source.relative_to(ROOT))
        print(scene, aspect, dimensions, output.stat().st_size, flush=True)

(ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
