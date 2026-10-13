"""Install and verify the WordNet data used by whiteboard scene planning."""
import argparse
import os
import zipfile
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--data-dir', default=os.environ.get('NLTK_DATA') or str(Path(__file__).resolve().parents[1] / 'llm' / 'nltk'))
args = parser.parse_args()
data_dir = Path(args.data_dir).resolve()
data_dir.mkdir(parents=True, exist_ok=True)

import nltk
nltk.data.path.insert(0, str(data_dir))
archive = data_dir / 'corpora' / 'wordnet.zip'
if not archive.exists():
    if not nltk.download('wordnet', download_dir=str(data_dir), raise_on_error=True):
        raise SystemExit('WordNet download did not complete')
# The planner performs random dictionary lookups. Reading directly from
# the compressed corpus repeatedly decompresses it during WordNet seeks.
corpora = data_dir / 'corpora'
dictionary = corpora / 'wordnet'
if not all((dictionary / name).is_file() for name in ('index.noun', 'data.noun', 'cntlist.rev', 'lexnames')):
    with zipfile.ZipFile(archive) as source:
        for entry in source.infolist():
            if not (corpora / entry.filename).resolve().is_relative_to(dictionary):
                raise SystemExit('WordNet archive contains a path outside its dictionary')
        source.extractall(corpora)
from nltk.corpus import wordnet
if not wordnet.synsets('ball'):
    raise SystemExit('WordNet verification failed')
print(f'Whiteboard language data ready: {data_dir}')
