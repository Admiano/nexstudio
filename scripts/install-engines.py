from pathlib import Path
import shutil, zipfile
ROOT=Path(__file__).resolve().parents[1]
SOURCES=ROOT/'engine_sources'; ENGINES=ROOT/'engines'
TREES={'paper-cast':'paper-cast-v1','editorial-motion':'editorial-motion-v1'}
items={
 'whiteboard':'WHITEBOARD_ENGINE_SOURCE.zip',
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

# Paper Cast is authored in-repo rather than archived, and ships its own
# CommonJS package boundary; copy it alongside the extracted engines so every
# engine path in .env.example resolves the same way.
for name,tree in TREES.items():
    source=SOURCES/tree
    if not source.exists(): continue
    target=ENGINES/name
    if target.exists(): shutil.rmtree(target)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns('.review'))
    print(f'{name}: {target}')

# Paper Cast is also a paper-motion (paperbook) citizen: its runtime, component,
# stylesheet and reel composition are grafted into the extracted Explainer
# paper-motion tree so paperbook compositions can load them by relative path.
paper_motion=ENGINES/'explainer'/'NexStudio_Explainer_Execution_Body_V2'/'runtime-assets'/'paper-motion'
cast_source=SOURCES/TREES['paper-cast']
if paper_motion.exists() and cast_source.exists():
    runtime=paper_motion/'runtime'/'paper-cast'
    if runtime.exists(): shutil.rmtree(runtime)
    shutil.copytree(cast_source/'runtime', runtime)
    shutil.copytree(cast_source/'manifests', paper_motion/'manifests'/'paper-cast', dirs_exist_ok=True)
    shutil.copy2(cast_source/'paperbook'/'paper-cast-stage.js', paper_motion/'components'/'paper-cast-stage.js')
    shutil.copy2(cast_source/'paperbook'/'paper-cast.css', paper_motion/'styles'/'paper-cast.css')
    shutil.copy2(cast_source/'paperbook'/'cast-reel.js', paper_motion/'runtime'/'cast-reel.js')
    shutil.copy2(cast_source/'paperbook'/'cast-reel.html', paper_motion/'compositions'/'cast-reel.html')
    print(f'paper-cast -> paper-motion: {paper_motion}')

# Editorial Motion v2 lives unpacked at engine_sources/editorial-motion-v2 (compiler + runtime + fixtures).
# The text-led bundle archive above is its planning-authority source of record; the compiler ships
# vendored copies with provenance hashes, so the archive is extracted for audit, not imported at runtime.

print('\nEngine source installed, shared Paper Motion dependencies assembled, and runtime package boundaries applied. Use the paths in .env.example.')
