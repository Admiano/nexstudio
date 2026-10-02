from pathlib import Path
import shutil, zipfile
ROOT=Path(__file__).resolve().parents[1]
SOURCES=ROOT/'engine_sources'; ENGINES=ROOT/'engines'
items={
 'whiteboard':'WHITEBOARD_ENGINE_SOURCE.zip',
 'explainer':'EXPLAINER_ENGINE_SOURCE.zip',
 'sound':'SOUND_LIBRARY_V2_SOURCE.zip',
 'whiteboard-v3-system':'NEXMIND_WHITEBOARD_V3_SYSTEM_PACKAGE.zip',
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

# Whiteboard v3 runtime lives checked-in at engine_sources/whiteboard-v3-runtime
# (no archive install step). The approved explainer pipeline lives unpacked at
# engine_sources/editorial-motion-v2 (compiler + runtime + fixtures).

print('\nEngine source installed. Use the paths in .env.example.')
