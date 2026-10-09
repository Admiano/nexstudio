from pathlib import Path
import shutil, zipfile
ROOT=Path(__file__).resolve().parents[1]
SOURCES=ROOT/'engine_sources'; ENGINES=ROOT/'engines'
items={
 'whiteboard':'WHITEBOARD_ENGINE_SOURCE.zip',
 'whiteboard-v3-system':'NEXMIND_WHITEBOARD_V3_SYSTEM_PACKAGE.zip',
 'whiteboard-v3-approved-source':'NEXSTUDIO_WHITEBOARD_APPROVED_V3_SOURCE_FOCUSED_2026-09-18.zip',
 'explainer':'EXPLAINER_ENGINE_SOURCE.zip',
 'sound':'SOUND_LIBRARY_V2_SOURCE.zip',
 'whiteboard-v3-system':'NEXMIND_WHITEBOARD_V3_SYSTEM_PACKAGE.zip',
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

# Whiteboard v3 runtime lives checked-in at engine_sources/whiteboard-v3-runtime
# (no archive install step). The approved explainer pipeline lives unpacked at
# engine_sources/editorial-motion-v2 (compiler + runtime + fixtures).

# NexMind Whiteboard V3 curated package (Cluster Travel TEXTFIX_V2 lineage): provenance and
# reference-output archive extracted for audit. The runtime adapter still roots at
# engines/whiteboard/Whiteboard_Execution_Body_V2 via STUDIO_WHITEBOARD_ENGINE_ROOT.

print('\nEngine source installed, shared Paper Motion dependencies assembled, and runtime package boundaries applied. Use the paths in .env.example.')
