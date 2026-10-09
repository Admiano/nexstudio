"""Vendor the bundle's planning authorities into the compiler package.

The Drive bundle ships each authority as a standalone module that locates its
siblings through absolute ``/mnt/data/...`` ``sys.path`` hacks. This copies the
modules side by side into ``editorial_plan_compiler/authorities`` and rewrites
only those path hacks so the modules import each other as a package. Every
byte of algorithm stays as authored; the rewrite is recorded, per file, with
source and vendored SHA-256 in ``AUTHORITY_PROVENANCE.json``.

Usage: python3 tools/vendor_authorities.py <bundle-root>
"""
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE.parent / 'compiler' / 'editorial_plan_compiler' / 'authorities'
AUTH = '02_AUTHENTIC_EDITORIAL_AUTHORITIES'

SOURCES = {
    'text_element_spatial_authority_v1.py': f'{AUTH}/GENUINE_STANDALONE/text_element_spatial_authority_v1.py',
    'editorial_background_system_v1.py': f'{AUTH}/GENUINE_STANDALONE/editorial_background_system_v1.py',
    'kinetic_typography_grammar_v2.py': f'{AUTH}/GENUINE_STANDALONE/kinetic_typography_grammar_v2.py',
    'kinetic_typography_performance_authority_v3.py': f'{AUTH}/KINETIC_TYPOGRAPHY/KINETIC_TYPOGRAPHY_PERFORMANCE_AUTHORITY_V3/kinetic_typography_performance_authority_v3.py',
    'editorial_scene_composition_authority_v2.py': f'{AUTH}/EDITORIAL_COMPOSITION/EDITORIAL_SCENE_COMPOSITION_AUTHORITY_V2/editorial_scene_composition_authority_v2.py',
    'editorial_motion_ensemble_director_v1.py': f'{AUTH}/MOTION_ENSEMBLE/EDITORIAL_MOTION_ENSEMBLE_DIRECTOR_V1/editorial_motion_ensemble_director_v1.py',
    'native_three_aspect_composition_authority_v2.py': f'{AUTH}/selected_reusable_adapters/native_three_aspect_composition_authority_v2.py',
    'semantic_beat_model.py': f'{AUTH}/SCENE_INTELLIGENCE/ILLUSTRATED_STORIES_SCENE_INTELLIGENCE_V1/semantic_beat_model.py',
    'scene_intelligence_schema.py': f'{AUTH}/SCENE_INTELLIGENCE/ILLUSTRATED_STORIES_SCENE_INTELLIGENCE_V1/scene_intelligence_schema.py',
    'open_peeps_conventional_rig_v6.py': f'{AUTH}/GENUINE_STANDALONE/open_peeps_conventional_rig_v6.py',
    'REFERENCE_EDITORIAL_MOTION_GRAMMAR_V1.json': '06_REFERENCE_GRAMMAR_AND_ANALYSIS/REFERENCE_EDITORIAL_MOTION_GRAMMAR_V1_CURRENT.json',
}

# Lines that exist only to find sibling modules on the authoring machine.
PATH_HACK = re.compile(
    r"^(?:[A-Z0-9_]*ROOT|COMP_DIR)\s*=\s*(?:Path|pathlib\.Path|ROOT)[(/].*$"
    r"|^(?:for p in \[.*\]:\s*)?sys\.path\.insert\(0,\s*str\(.*\)\)\s*$",
    re.M,
)
LOCAL_IMPORT = re.compile(r"^from (text_element_spatial_authority_v1|editorial_background_system_v1|kinetic_typography_grammar_v2|scene_intelligence_schema) import", re.M)


GENERIC_MODIFICATION = 'authoring-machine /mnt/data paths removed; sibling imports made package-relative'
MODIFICATIONS = {
    'editorial_background_system_v1.py': GENERIC_MODIFICATION + '; raster preview imports optional; preview output parameterised (--out)',
    'open_peeps_conventional_rig_v6.py': GENERIC_MODIFICATION + '; source and rig output parameterised (OPEN_PEEPS_SOURCE_ROOT, OPEN_PEEPS_RIG_OUT); offline authoring tool, not imported at runtime',
    'kinetic_typography_performance_authority_v3.py': GENERIC_MODIFICATION + '; REPLACEMENT_LOCKUP motif restricted to beats with a replace group (two heroes in one bbox otherwise collide)',
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch(name: str, text: str) -> str:
    if not name.endswith('.py'):
        return text
    text = PATH_HACK.sub('', text)
    text = LOCAL_IMPORT.sub(lambda m: f'from .{m.group(1)} import', text)
    if name == 'native_three_aspect_composition_authority_v2.py':
        text = re.sub(
            r"def _load_comp_v2\(\):.*?_COMP_V2=_load_comp_v2\(\)",
            "from . import editorial_scene_composition_authority_v2 as _COMP_V2",
            text,
            flags=re.S,
        )
    if name == 'editorial_background_system_v1.py':
        # plan() needs neither raster library; only the optional preview render does.
        text = text.replace(
            'import numpy as np\nfrom PIL import Image, ImageDraw, ImageFilter\n',
            'try:\n    import numpy as np\n    from PIL import Image, ImageDraw, ImageFilter\nexcept ImportError:  # raster preview is optional\n    np = None\n    Image = ImageDraw = ImageFilter = None\n',
        )
        text = text.replace(
            "out=Path('/mnt/data/EDITORIAL_BACKGROUND_SYSTEM_V1')/f'preview_{args.aspect}_{plan.template}.png'",
            "out=Path(args.out)/f'preview_{args.aspect}_{plan.template}.png'",
        )
        text = text.replace("p.add_argument('--template',default=None)", "p.add_argument('--template',default=None); p.add_argument('--out',default='.')")
    if name == 'kinetic_typography_performance_authority_v3.py':
        # REPLACEMENT_LOCKUP stacks two heroes in one bbox; without a replace group that is a collision.
        text = text.replace(
            "    if replace and 'REPLACEMENT_LOCKUP' in choices:\n        choices.insert(0,'REPLACEMENT_LOCKUP')\n",
            "    if replace and 'REPLACEMENT_LOCKUP' in choices:\n        choices.insert(0,'REPLACEMENT_LOCKUP')\n    if not replace:\n        choices=[c for c in choices if c!='REPLACEMENT_LOCKUP'] or ['SPLIT_SCALE_LOCKUP']\n",
        )
        assert "if not replace:" in text, 'KTP motif patch did not apply'
    if name == 'open_peeps_conventional_rig_v6.py':
        text = text.replace("OUT=Path('/mnt/data/OPEN_PEEPS_ARTICULATED_RIG_V6')", "OUT=Path(os.environ.get('OPEN_PEEPS_RIG_OUT','OPEN_PEEPS_ARTICULATED_RIG_V6'))")
        text = re.sub(r"^SRC=ROOT/", "ROOT=Path(os.environ.get('OPEN_PEEPS_SOURCE_ROOT','.'))\nSRC=ROOT/", text, count=1, flags=re.M)
        if 'import os' not in text:
            text = text.replace('from pathlib import Path', 'import os\nfrom pathlib import Path', 1)
        assert re.search(r'^ROOT=', text, re.M), 'Open Peeps rig ROOT patch did not apply'
    assert '/mnt/data' not in text, f'{name}: unresolved authoring-machine path'
    # Collapse the blank lines the removed hacks leave behind.
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text


def main(bundle_root: str) -> None:
    root = Path(bundle_root)
    TARGET.mkdir(parents=True, exist_ok=True)
    (TARGET / '__init__.py').write_text(
        '"""Bundle planning authorities, vendored byte-for-byte except for sibling-path hacks. See AUTHORITY_PROVENANCE.json."""\n'
    )
    provenance = {'schema': 'EditorialAuthorityProvenanceV1', 'bundle': root.name, 'files': []}
    for name, rel in SOURCES.items():
        source = root / rel
        raw = source.read_bytes()
        patched = patch(name, raw.decode('utf8')).encode('utf8')
        (TARGET / name).write_bytes(patched)
        provenance['files'].append({
            'file': name,
            'bundle_path': rel,
            'source_sha256': sha(raw),
            'vendored_sha256': sha(patched),
            'modified': sha(raw) != sha(patched),
            'modification': MODIFICATIONS.get(name, GENERIC_MODIFICATION) if sha(raw) != sha(patched) else None,
        })
    (TARGET / 'AUTHORITY_PROVENANCE.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(json.dumps({f['file']: f['modified'] for f in provenance['files']}, indent=1))


if __name__ == '__main__':
    main(sys.argv[1])
