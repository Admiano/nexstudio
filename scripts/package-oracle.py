"""Package this working tree for Oracle without local secrets or runtime data."""
import argparse
import json
import os
import stat
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--list', action='store_true', help='Print file count and size without creating the archive.')
args = parser.parse_args()
tracked = subprocess.run(['git', '-c', 'core.quotepath=false', 'ls-files', '-z', '--cached'], cwd=ROOT, capture_output=True, check=True)
print('Tracked source inventory loaded.', flush=True)
# rg respects ignore files and prunes generated trees before visiting them.
# Include new source files without asking git to scan large runtime directories.
source_dirs = [name for name in ('app', 'src', 'services', 'scripts', 'config', 'vendor', 'engine_sources', 'prisma', 'docs', 'deploy', 'public') if (ROOT / name).is_dir()]
source_names = set()
for directory in source_dirs:
    print(f'Discovering {directory} sources.', flush=True)
    new_sources = subprocess.run(['rg', '--files', '--hidden',
        '-g', '!**/out/**', '-g', '!**/node_modules/**', '-g', '!**/__pycache__/**',
        '-g', '!**/.venv/**', '-g', '!**/.git/**', '-g', '!**/reports/**', '--', directory], cwd=ROOT, capture_output=True)
    if new_sources.returncode not in (0, 1):
        raise SystemExit('Source discovery failed; no archive was created.')
    source_names.update(Path(name.decode('utf-8')).as_posix() for name in new_sources.stdout.splitlines())
source_names.update(name.decode('utf-8') for name in tracked.stdout.split(b'\0') if name)
print(f'Filtering {len(source_names)} source paths.', flush=True)
excluded = {'reports', 'tmp', 'llm', 'engines', 'data', 'uploads', 'local-renders', 'backups', '.git', '.agents', '.codex', '.aws', 'certs', 'node_modules', '.next', 'dist'}
files = []
source_bytes = 0
checked_parents = set()
current_parent = None
directory_entries = {}
for name in sorted(source_names):
    relative = Path(name)
    if relative.parts[0] in excluded or '__pycache__' in relative.parts:
        continue
    if any(part.startswith('.env') and part != '.env.example' for part in relative.parts):
        continue
    if relative.suffix.lower() in {'.pem', '.key', '.p12', '.pfx', '.log', '.pyc'}:
        continue
    if relative.parts[0] == 'engine_sources' and 'out' in relative.parts:
        continue
    filename = ROOT / relative
    if relative.parent not in checked_parents:
        if not filename.parent.resolve().is_relative_to(ROOT):
            raise SystemExit('A source directory resolves outside this checkout.')
        checked_parents.add(relative.parent)
    if current_parent != relative.parent:
        current_parent = relative.parent
        try:
            with os.scandir(filename.parent) as entries:
                directory_entries = {entry.name: entry.stat(follow_symlinks=False) for entry in entries if entry.is_file(follow_symlinks=False)}
        except FileNotFoundError:
            directory_entries = {}
    info = directory_entries.get(relative.name)
    if not info or not stat.S_ISREG(info.st_mode):
        continue
    files.append((relative, info))
    source_bytes += info.st_size
summary = {'sourceFiles': len(files), 'sourceBytes': source_bytes, 'secretsAndRuntimeData': 'excluded'}
print(json.dumps(summary), flush=True)
if not args.list:
    output = ROOT / 'tmp' / 'nexstudio-oracle.tar.gz'
    output.parent.mkdir(exist_ok=True)
    partial = output.with_suffix(output.suffix + '.partial')
    with tarfile.open(partial, 'w:gz', compresslevel=1) as bundle:
        for index, (relative, info) in enumerate(files, 1):
            member = tarfile.TarInfo(relative.as_posix())
            member.size = info.st_size
            member.mtime = int(info.st_mtime)
            member.mode = stat.S_IMODE(info.st_mode)
            with (ROOT / relative).open('rb') as source:
                bundle.addfile(member, source)
            if index % 25000 == 0:
                print(f'Packaged {index}/{len(files)} source files.', flush=True)
    partial.replace(output)
    summary['archive'] = str(output)
    summary['archiveBytes'] = output.stat().st_size
print(json.dumps(summary))
