#!/usr/bin/env python3
"""review_page — self-contained HTML review surface for a render.

Written next to the video in the out-dir as <name>_REVIEW.html: the
mp4, the QA contact sheet, a per-beat table (stage / narration / window)
and the plan JSON — everything a reviewer needs in one file.
"""
from __future__ import annotations

import html
import json
from pathlib import Path


def write_review(plan: dict, out_dir: Path, name: str,
                 metrics: dict) -> Path:
    beats = plan.get('beats') or []
    rows = []
    for i, b in enumerate(beats):
        dg = b.get('diagram') or {}
        stage = dg.get('stage') or ''
        elems = [
            e.get('icon') or e.get('part') or e.get('chip')
            or e.get('callout') or 'arrow'
            for e in (dg.get('elements') or [])]
        rows.append(
            '<tr><td>{}</td><td>{}</td><td>{:.2f}s</td><td>{}</td>'
            '<td>{}</td></tr>'.format(
                i + 1, html.escape(stage),
                float(b.get('start_seconds') or 0),
                html.escape(str(b.get('narration') or '')),
                html.escape(' · '.join(elems))))

    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(name)} — review</title>
<style>
 body{{font:15px/1.5 system-ui,sans-serif;margin:2rem auto;max-width:960px;
      padding:0 1rem;color:#1a1a17;background:#fafaf6}}
 h1{{font-size:1.4rem;margin-bottom:.2rem}}
 .meta{{color:#666;font-size:.85rem;margin-bottom:1.2rem}}
 video{{width:100%;max-width:720px;border:1px solid #ddd;border-radius:8px;
       display:block}}
 img{{max-width:100%;border:1px solid #ddd;border-radius:8px;margin:1rem 0}}
 table{{border-collapse:collapse;width:100%;font-size:.85rem}}
 td,th{{border:1px solid #ddd;padding:.35rem .5rem;text-align:left;
       vertical-align:top}}
 th{{background:#f0eee6}}
 details{{margin-top:1.2rem}}
 pre{{background:#f0eee6;padding:1rem;border-radius:8px;overflow-x:auto;
     font-size:.75rem}}
</style></head><body>
<h1>{html.escape(name)}</h1>
<p class="meta">{metrics.get('type', '')} · {metrics.get('ratio', '')} ·
 {metrics.get('duration_seconds', 0)}s · {metrics.get('beat_count', 0)} beats ·
 {metrics.get('element_count', 0)} elements</p>
<video controls preload="metadata" src="{html.escape(name)}.mp4"></video>
<h2>QA contact sheet</h2>
<img src="{html.escape(name)}_QA.jpg" alt="qa sheet">
<h2>Beats</h2>
<table><tr><th>#</th><th>stage</th><th>start</th><th>narration</th>
<th>elements</th></tr>
{''.join(rows)}
</table>
<details><summary>Plan JSON</summary>
<pre>{html.escape(json.dumps(plan, indent=1))}</pre></details>
</body></html>"""
    path = Path(out_dir) / f'{name}_REVIEW.html'
    path.write_text(doc)
    return path
