from pathlib import Path
import shutil, zipfile
ROOT=Path(__file__).resolve().parents[1]
SOURCES=ROOT/'engine_sources'; ENGINES=ROOT/'engines'
items={
 'whiteboard':'WHITEBOARD_ENGINE_SOURCE.zip',
 'explainer':'EXPLAINER_ENGINE_SOURCE.zip',
 'editorial':'EDITORIAL_MOTION_ENGINE_SOURCE.zip',
 'stickman':'STICKMAN_V5_1_ENGINE_SOURCE.zip',
 'sound':'SOUND_LIBRARY_V2_SOURCE.zip',
 'editorial-text-led-bundle':'EDITORIAL_TEXT_LED_BUNDLE_SOURCE.zip',
}
# Tracked working trees win over their frozen archives. explainer-v2 is the
# development fork of the Explainer execution body (HyperFrames scene work);
# the zip stays as the pristine baseline it was extracted from.
tracked={ 'explainer': SOURCES/'explainer-v2' }
ENGINES.mkdir(exist_ok=True)
for name,archive in items.items():
 target=ENGINES/name
 if target.exists(): shutil.rmtree(target)
 target.mkdir(parents=True)
 worktree=tracked.get(name)
 if worktree is not None and worktree.exists():
  shutil.copytree(worktree,target,dirs_exist_ok=True)
  print(f'{name}: {target} (tracked tree {worktree})')
 else:
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

# Editorial Motion v2 lives unpacked at engine_sources/editorial-motion-v2 (compiler + runtime + fixtures).
# The text-led bundle archive above is its planning-authority source of record; the compiler ships
# vendored copies with provenance hashes, so the archive is extracted for audit, not imported at runtime.

print('\nEngine source installed, shared Paper Motion dependencies assembled, and runtime package boundaries applied. Use the paths in .env.example.')
