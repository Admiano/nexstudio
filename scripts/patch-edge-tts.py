#!/usr/bin/env python3
"""Update legacy edge-tts endpoints in the current Python environment.

Compatibility fix for edge-tts 7.2.8 and Microsoft's October 2026 migration:
https://github.com/rany2/edge-tts/issues/490
The new host currently accepts the library's existing GEC token/version.
This patch changes the endpoints, not the token algorithm or selected voice.
Run again after installing/upgrading Python dependencies.
"""
import importlib.util
import os
from pathlib import Path
import stat
import tempfile


REPLACEMENTS = (
    ('BASE_URL = "speech.platform.bing.com/consumer/speech/synthesize/readaloud"',
     'BASE_URL = "api.msedgeservices.com/tts/cognitiveservices"'),
    ('/edge/v1?TrustedClientToken=', '/websocket/v1?Ocp-Apim-Subscription-Key='),
    ('/voices/list?trustedclienttoken=', '/voices/list?Ocp-Apim-Subscription-Key='),
    ('"Authority": "speech.platform.bing.com"', '"Authority": "api.msedgeservices.com"'),
)


def patch_constants(target: Path) -> bool:
    original = target.read_text(encoding="utf-8")
    if "speech.platform.bing.com" not in original:
        return False  # Already patched, or a future upstream endpoint update.
    if not all(old in original for old, _ in REPLACEMENTS):
        raise RuntimeError("Unrecognized edge-tts constants; refusing a partial endpoint patch")
    updated = original
    for old, new in REPLACEMENTS:
        updated = updated.replace(old, new, 1)
    compile(updated, str(target), "exec")
    # Keep the package readable by the container's non-root runtime user.
    mode = stat.S_IMODE(target.stat().st_mode)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent,
                                         prefix=".nexstudio-edge-", delete=False) as file:
            temporary = Path(file.name)
            file.write(updated)
        os.chmod(temporary, mode)
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return True


def main():
    spec = importlib.util.find_spec("edge_tts")
    if spec is None or not spec.submodule_search_locations:
        raise SystemExit("Install edge-tts in this Python environment before applying the endpoint patch")
    target = Path(next(iter(spec.submodule_search_locations))) / "constants.py"
    changed = patch_constants(target)
    print("edge-tts: Microsoft endpoints updated" if changed else "edge-tts: no legacy endpoint patch needed")


if __name__ == "__main__":
    main()
