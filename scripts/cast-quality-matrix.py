#!/usr/bin/env python3
"""Render the complete approved wardrobe with the candidate quality profile."""
import argparse, concurrent.futures, json, os, subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--output-dir', type=Path, required=True)
p.add_argument('--blender', required=True)
p.add_argument('--frame', type=int, default=27)
p.add_argument('--only', nargs='+', help='Rerender named entries after a correction')
a = p.parse_args()
if not 1 <= a.frame <= 998:
    p.error('Frame outside approved action')
a.output_dir = a.output_dir.resolve()
a.output_dir.mkdir(parents=True, exist_ok=True)
tops = ['namuhekam_male_polo_shirt', 'toigo_basic_tucked_t-shirt',
        'elvs_male_shirt_untucked_bd1', 'mindfront_knitted_sweater_01',
        'toigo_fisherman_sweater']
bottoms = ['mindfront_male_trousers_1', 'elvs_jeans_straight_leg',
           'mindfront_male_trousers_2', 'punkduck_male_classic_jeans',
           'toigo_wool_pants']
dresses = ['mindfront_f_dress_11', 'mindfront_f_dress_09',
           'mindfront_f_dress_07', 'punkduck_black_cocktail_dress',
           'punkduck_middle_length_qipao']
jobs = [('male', f'male-{t+1}-{b+1}', top, bottom)
        for t, top in enumerate(tops) for b, bottom in enumerate(bottoms)]
jobs += [('female', f'female-{i+1}', dress, '') for i, dress in enumerate(dresses)]
if a.only:
    unknown = set(a.only)-{job[1] for job in jobs}
    if unknown:
        p.error('Unknown entries: '+', '.join(sorted(unknown)))
    jobs = [job for job in jobs if job[1] in a.only]

def render(job):
    character, name, top, bottom = job
    request = json.loads((root/'docs/cast-quality-reference'/f'{character}-reference.request.json').read_text())
    config = request['config']
    config.update(frame=a.frame, resolutionPercentage=25)
    config['candidateProfile'] = 'finish-upgrade-v1'
    if character == 'male':
        config['env']['CAST_GARMENTS'] = f'{top}=A9C4DE,{bottom}=B59A6E,mindfront_shoes_monk_strap_male=4A2E1E'
    else:
        config['env']['CAST_DRESS'] = top
    request_path = a.output_dir/(name+'.request.json')
    request_path.write_text(json.dumps(request, indent=2)+'\n')
    env = dict(os.environ, **config['env'])
    env.update(BLENDER_BIN=str(Path(a.blender).resolve()),
               CAST_SOURCE_DIR=str(root/'engine_sources/makehuman-lineart/presenters_v1'),
               CAST_RENDER_ENTRY=str(root/'scripts/cast-render-assembled.py'),
               MH_ROOT=str(root/'engine_sources/makehuman-lineart/assets'),
               OPENBLAS_NUM_THREADS='1', CAST_RENDER_THREADS='3',
               CAST_QUALITY_PILOT='1', CAST_FINISH_UPGRADE='1',
               CAST_GARMENT_STRUCTURE_PILOT='1')
    command = ['bash', str(root/'scripts/cast-preview-render.sh'),
               str(request_path), str(a.output_dir/(name+'.png'))]
    with (a.output_dir/(name+'.log')).open('w') as log:
        result = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f'{name} failed; inspect its log')
    print('WARDROBE_RENDER_OK', name, flush=True)
    return {'name': name, 'character': character, 'topOrDress': top, 'bottom': bottom,
            'metadata': json.loads((a.output_dir/(name+'.json')).read_text())}

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    results = list(pool.map(render, jobs))
verification = a.output_dir/'verification.json'
if a.only and verification.exists():
    previous = json.loads(verification.read_text())
    if previous['frame'] != a.frame:
        raise RuntimeError('Cannot merge verification from different poses')
    merged = {row['name']: row for row in previous['renders']}
    merged.update({row['name']: row for row in results})
    results = list(merged.values())
(a.output_dir/'verification.json').write_text(json.dumps({'frame': a.frame, 'renders': results}, indent=2)+'\n')
