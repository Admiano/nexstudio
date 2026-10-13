"""Check the installed video toolchain and the declared Python requirements."""
import importlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import shutil
from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[1]
packages = {}
for line in (ROOT / 'requirements.txt').read_text().splitlines():
    line = line.split('#', 1)[0].strip()
    if not line:
        continue
    requirement = Requirement(line)
    installed = version(requirement.name)
    if installed not in requirement.specifier:
        raise RuntimeError(f'{requirement.name} {installed} does not satisfy {requirement.specifier}')
    packages[requirement.name] = installed
for module in ['PIL', 'cairosvg', 'matplotlib', 'numpy', 'cv2', 'jsonschema',
               'playwright', 'edge_tts', 'kokoro_onnx', 'soundfile', 'faster_whisper', 'av', 'nltk']:
    importlib.import_module(module)
tools = {}
for name in ['node', 'ffmpeg', 'ffprobe', 'chromium', 'blender']:
    tools[name] = shutil.which(name)
    if not tools[name]:
        raise RuntimeError(f'Missing engine tool: {name}')
import nltk
nltk.corpus.wordnet.synsets('toothpick')
data = {name: Path(os.environ[name]).exists() for name in [
    'KOKORO_MODEL_PATH', 'KOKORO_VOICES_PATH', 'WHISPER_MODEL_PATH', 'MFA_BIN']}
if not all(data.values()):
    raise RuntimeError(f'Missing runtime model or tool: {data}')
print(json.dumps({'packages': packages, 'tools': tools, 'modelData': data, 'wordnet': 'ready'}))
