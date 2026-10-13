"""Install the small narration timing model beside the other local models."""
import argparse
import shutil
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', default=str(Path(__file__).resolve().parents[1] / 'llm' / 'whisper-small'))
args = parser.parse_args()
destination = Path(args.out).resolve()
required_files = ('model.bin', 'config.json', 'tokenizer.json')
if not all((destination / filename).exists() for filename in required_files):
    from huggingface_hub import snapshot_download
    from huggingface_hub.errors import LocalEntryNotFoundError
    try:
        cached = snapshot_download('Systran/faster-whisper-small', local_files_only=True)
    except LocalEntryNotFoundError:
        from faster_whisper.utils import download_model
        download_model('small', output_dir=str(destination), cache_dir=str(destination.parent / 'huggingface'))
    else:
        shutil.copytree(cached, destination, dirs_exist_ok=True)
        if not all((destination / filename).exists() for filename in required_files):
            from faster_whisper.utils import download_model
            download_model('small', output_dir=str(destination), cache_dir=str(destination.parent / 'huggingface'))
if not all((destination / filename).exists() for filename in required_files):
    raise SystemExit('Narration timing model installation is incomplete')
print(f'Narration timing model ready: {destination}')
