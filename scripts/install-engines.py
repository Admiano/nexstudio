from pathlib import Path
import shutil, zipfile
ROOT=Path(__file__).resolve().parents[1]
SOURCES=ROOT/'engine_sources'; ENGINES=ROOT/'engines'
items={
 'whiteboard':'WHITEBOARD_ENGINE_SOURCE.zip',
 'whiteboard-v3-system':'NEXMIND_WHITEBOARD_V3_SYSTEM_PACKAGE.zip',
 'whiteboard-v3-approved-source':'NEXSTUDIO_WHITEBOARD_APPROVED_V3_SOURCE_FOCUSED_2026-09-18.zip',
 'explainer':'EXPLAINER_ENGINE_SOURCE.zip',
 'editorial':'EDITORIAL_MOTION_ENGINE_SOURCE.zip',
 'stickman':'STICKMAN_V5_1_ENGINE_SOURCE.zip',
 'sound':'SOUND_LIBRARY_V2_SOURCE.zip',
 'editorial-text-led-bundle':'EDITORIAL_TEXT_LED_BUNDLE_SOURCE.zip',
}
ENGINES.mkdir(exist_ok=True)
for name,archive in items.items():
 target=ENGINES/name
 if target.exists(): shutil.rmtree(target)
 target.mkdir(parents=True)
 with zipfile.ZipFile(SOURCES/archive) as z: z.extractall(target)
 print(f'{name}: {target}')

# Explainer archive is an execution-only authored-art body beneath full NexMind P8.
# It is self-contained and must not be supplemented with the P14.1 DirectorV3/semantic-family path.
# Runtime TypeScript executes via the Standalone root node_modules/tsx while cwd is
# the extracted Explainer execution-body root, so its own tsconfig aliases remain authoritative.

# NexStick V5.1 runtime is authored as CommonJS. The standalone Next app is ESM,
# so establish a local package boundary after extraction without altering vendor files.
stick_root=ENGINES/'stickman'/'NEXSTICK_MASTER_V2_UNIFIED_PERFORMANCE_V5_1_CLEAN_2026-08-13'
if stick_root.exists():
    (stick_root/'package.json').write_text('{\n  \"type\": \"commonjs\"\n}\n')

# NexMind Whiteboard V3 curated package (Cluster Travel TEXTFIX_V2 lineage): provenance and
# reference-output archive extracted for audit. The runtime adapter still roots at
# engines/whiteboard/Whiteboard_Execution_Body_V2 via STUDIO_WHITEBOARD_ENGINE_ROOT.

# Editorial Motion v2 lives unpacked at engine_sources/editorial-motion-v2 (compiler + runtime + fixtures).
# The text-led bundle archive above is its planning-authority source of record; the compiler ships
# vendored copies with provenance hashes, so the archive is extracted for audit, not imported at runtime.

print('\nEngine source installed, shared Paper Motion dependencies assembled, and runtime package boundaries applied. Use the paths in .env.example.')
