"""Start every requested output format together after shared preparation."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import time


def render_aspects(aspects, render, completed=None):
    formats = list(dict.fromkeys(aspects))
    if not formats:
        raise ValueError('At least one video format is required')

    def run(aspect):
        print('[aspect-render] ' + json.dumps({'event': 'start', 'aspect': aspect, 'time': time.monotonic()}), flush=True)
        result = render(aspect)
        print('[aspect-render] ' + json.dumps({'event': 'done', 'aspect': aspect, 'time': time.monotonic()}), flush=True)
        return result

    results = {}
    # One launcher per requested format, independent of CPU count and queue limits.
    with ThreadPoolExecutor(max_workers=len(formats)) as executor:
        futures = {executor.submit(run, aspect): aspect for aspect in formats}
        for future in as_completed(futures):
            aspect = futures[future]
            results[aspect] = future.result()
            if completed:
                completed(aspect, len(results), len(formats))
    return {aspect: results[aspect] for aspect in formats}
