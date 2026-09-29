"""Storyboard ship gate: visual composition + semantic + audio checks.

    python3 sb_qa.py plan.json out_dir [--voiceover vo.wav]

Writes <out_dir>/<name>_SB_QA.json and exits 1 when any check fails.
Every check is deterministic and local; nothing here needs a network.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

_FEEL = re.compile(r'\b(happy|sad|afraid|scared|worr\w*|stress\w*|calm|'
                   r'angry|proud|excited|tired|confused|relieved|panic\w*|'
                   r'fear\w*|love\w*)\b', re.I)


def _area(b):
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def _issue(out, sev, check, beat, detail):
    out.append({'severity': sev, 'check': check, 'beat': beat,
                'detail': detail})


def _semantic(v3r, out, si, name, ic, word: str = '') -> dict:
    """How a word resolved to art: exact authored drawing, curated kit
    fallback, or library fallback with its CLIP rank. A library pick the
    model ranks far down for its word fails the gate."""
    # judged against the word the viewer reads, not the icon key the
    # author substituted for it ('anvil' drawn via 'block')
    phrase = str(word or name).lower().strip()
    exact = ic is not None and ic == v3r.kit_exact(phrase)
    curated = isinstance(ic, tuple) and (
        ic[0] == 'custom' or str(ic[1]).startswith('kit:'))
    rk = None if exact else v3r.sem_rank(phrase, ic)
    how = 'exact' if exact else ('kit-fallback' if curated else 'library')
    rec = {'word': phrase, 'art': str(ic), 'via': how, 'rank': rk}
    if how != 'exact' and rk is not None and rk > v3r.SEM_BAD_RANK:
        rec['severity'] = 'fail'
        _issue(out, 'fail', 'semantic-art', si,
               f'{phrase} -> {ic} (clip rank {rk} > {v3r.SEM_BAD_RANK})')
    elif how == 'library' and not v3r.art_related(phrase, ic):
        rec['severity'] = 'warn'
        _issue(out, 'warn', 'semantic-loose', si,
               f'{phrase} -> {ic}: art name unrelated to the word')
    elif how != 'exact':
        rec['severity'] = 'info'
        _issue(out, 'info', 'semantic-fallback', si,
               f'{phrase} -> {ic} via {how}'
               + (f' (clip rank {rk})' if rk is not None else ''))
    return rec


def visual(plan: dict, ratio: str = '16:9') -> tuple[list, list]:
    import pipeline_v3_narration_timed as pipe
    wbc, _a, _b, v3r = pipe.load_execution_body()
    import v3_board_sections as bs
    plan = pipe.normalize_plan(plan)
    plan['board_layout'] = 'storyboard'
    v3r.configure_art(plan)
    plan.update(wbc.compile_whiteboard_plan(plan, {'ratio': ratio}))
    plan.pop('_sb_audit', None)
    plan.pop('_sb_qa', None)
    flow = bs._build(plan, ratio)
    out, scenes = [], []
    for a in plan.get('_sb_audit') or []:
        for iss in a['issues']:
            _issue(out, 'fail', 'overlap/off-frame', a['beat'], list(iss))
    for q in plan.get('_sb_qa') or []:
        _issue(out, q['severity'], q['check'], q['beat'], q['detail'])
    art_owner: dict = {}
    fig_h = []
    for si, sec in enumerate(s for s in flow['sections']
                             if 'qa_els' in s):
        els = sec['qa_els']
        cb = sec['qa_content']
        beat = plan['beats'][si] if si < len(plan['beats']) else {}
        ink_area = 0.0
        row = {'beat': si, 'layout': sec.get('layout'), 'elements': []}
        for e in els:
            if e.get('in_activity'):
                # drawn by its actor's activity apparatus, not as art
                continue
            role = e['role'] or {}
            name = str(role.get('icon') or e['label'] or '')
            ink = e.get('ink')
            if ink:
                ink_area += _area(ink)
            if e['kind'] == 'person':
                if ink and not e.get('act_meta'):
                    fig_h.append((si, ink[3] - ink[1]))
                if str(role.get('icon', 'person')) != 'person' \
                        and not role.get('emotion'):
                    _issue(out, 'fail', 'character-unneeded', si,
                           e['label'])
                txt = ' '.join(str(role.get(k) or '') for k in
                               ('annotate', 'label', 'narration'))
                if e['emo'] == 'neutral' and _FEEL.search(txt):
                    _issue(out, 'fail', 'emotion-mismatch', si,
                           f'{e["label"]}: neutral vs "{txt.strip()}"')
                row['elements'].append((e['label'], 'figure', e['emo']))
            elif e['kind'] == 'art':
                ic = v3r._icon_for(name)
                if ic in (None, 'card', 'tile') or v3r._is_emblem(ic):
                    _issue(out, 'fail', 'generic-art', si, f'{name} -> {ic}')
                key = json.dumps(ic, default=str)
                owner = art_owner.setdefault(key, (e['label'], si))
                if owner[0] != e['label'] and owner[1] == si:
                    _issue(out, 'fail', 'duplicate-art', si,
                           f'{e["label"]} and {owner[0]} both draw {ic}')
                row['elements'].append((e['label'], str(ic), ''))
                row.setdefault('semantic', []).append(_semantic(v3r,
                    out, si, name, ic, str(e['label'] or '')))
            lb = e.get('lab_box')
            if lb and ink:
                lcx = (lb[0] + lb[2]) / 2
                w = ink[2] - ink[0]
                if not (ink[0] - 0.15 * w <= lcx <= ink[2] + 0.15 * w):
                    _issue(out, 'fail', 'label-detached', si,
                           e['label_text'])
                if lb[1] < ink[1] - (ink[3] - ink[1]) * 0.1 and \
                        lb[3] > ink[3]:
                    _issue(out, 'fail', 'label-detached', si,
                           e['label_text'])
            if e['label_text'] and len(e['label_text']) > 24:
                _issue(out, 'warn', 'label-long', si, e['label_text'])
        fill = ink_area / max(1.0, _area(cb))
        row['fill'] = round(fill, 3)
        if fill < 0.07:
            _issue(out, 'fail', 'sparse-scene', si, f'fill {fill:.2f}')
        elif fill < 0.11:
            _issue(out, 'warn', 'sparse-scene', si, f'fill {fill:.2f}')
        heroes = [e for e in els if not e['kid'] and e.get('ink')]
        if len(heroes) >= 2 and sec.get('layout') == 'focus':
            h0 = heroes[0]['ink'][3] - heroes[0]['ink'][1]
            if any(h['ink'][3] - h['ink'][1] > h0 * 1.05
                   for h in heroes[1:]):
                _issue(out, 'warn', 'hierarchy', si, 'hero not largest')
        cap = str(beat.get('caption') or '')
        if len(cap.split()) > 9:
            _issue(out, 'warn', 'caption-long', si, cap)
        row['marks'] = sec.get('qa_marks', [])
        scenes.append(row)
    if fig_h:
        hs = [h for _s, h in fig_h]
        if max(hs) > min(hs) * 1.8:
            _issue(out, 'warn', 'cast-scale', None,
                   f'figure heights {min(hs):.0f}..{max(hs):.0f}px')
    for a, b in zip(scenes, scenes[1:]):
        if a['layout'] == b['layout'] and a['layout'] not in (None,):
            _issue(out, 'warn', 'layout-repeat', b['beat'], a['layout'])
    return out, scenes


def _read_wav(p: Path):
    with wave.open(str(p)) as w:
        n, ch, sr = w.getnframes(), w.getnchannels(), w.getframerate()
        a = np.frombuffer(w.readframes(n), '<i2').astype(np.float32) / 32768
    return a.reshape(-1, ch).mean(1), sr


def audio(out_dir: Path, name: str, vo: Path | None) -> tuple[list, dict]:
    out, m = [], {}
    sfx = out_dir / f'{name}.sfx.wav'
    ev_p = sfx.with_suffix('.events.json')
    mp4 = out_dir / f'{name}.mp4'
    x, sr = _read_wav(sfx)
    m['sfx_peak'] = round(float(np.abs(x).max()), 4)
    if m['sfx_peak'] >= 0.99:
        _issue(out, 'fail', 'sfx-clip', None, m['sfx_peak'])
    ev = json.loads(ev_p.read_text()) if ev_p.exists() else []
    pen = np.zeros(len(x), bool)
    for e in ev:
        a = int(e['start'] * sr)
        b = int((e['start'] + e['duration'] + 0.08) * sr)
        pen[max(0, a):min(len(x), b)] = True
    hop = sr // 100
    k = len(x) // hop
    rms = np.sqrt((x[:k * hop].reshape(k, hop) ** 2).mean(1) + 1e-12)
    pw = pen[:k * hop].reshape(k, hop)
    off = rms[~pw.any(1)]
    # the cap clicks at head/tail are deliberate; skip the first/last 0.6s
    edge = int(0.6 * 100)
    mid_off = rms[edge:-edge][~pw[edge:-edge].any(1)]
    loud_off = float((mid_off > 10 ** (-50 / 20)).mean()) if len(mid_off) \
        else 0.0
    m['pen_up_loud_frac'] = round(loud_off, 4)
    m['pen_up_windows'] = int(len(off))
    if loud_off > 0.005:
        _issue(out, 'fail', 'sfx-during-pen-up', None, loud_off)
    on = rms[pw.all(1)]
    cov = float((on > 10 ** (-45 / 20)).mean()) if len(on) else 0.0
    m['pen_down_audible_frac'] = round(cov, 4)
    if cov < 0.9:
        _issue(out, 'fail', 'sfx-missing-on-stroke', None, cov)
    # spectral: marker friction is broadband; no dominant tone
    seg = x[pen][: sr * 20]
    if len(seg) > sr:
        spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
        f = np.fft.rfftfreq(len(seg), 1 / sr)
        band = spec[(f > 200) & (f < 12000)]
        m['tone_peak_to_median'] = round(float(band.max() /
                                               np.median(band)), 1)
        if m['tone_peak_to_median'] > 60:
            _issue(out, 'fail', 'sfx-tonal', None, m['tone_peak_to_median'])
    probe = json.loads(subprocess.run(
        ['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of',
         'json', str(mp4)], capture_output=True, text=True).stdout)
    kinds = [s['codec_type'] for s in probe['streams']]
    m['streams'] = kinds
    m['duration'] = round(float(probe['format']['duration']), 2)
    if kinds.count('video') != 1 or kinds.count('audio') != 1:
        _issue(out, 'fail', 'tracks', None, kinds)
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(mp4), '-f',
                          's16le', '-ac', '1', '-ar', '48000', '-'],
                         capture_output=True).stdout
    mix = np.frombuffer(raw, '<i2').astype(np.float32) / 32768
    m['mix_peak'] = round(float(np.abs(mix).max()), 4)
    if m['mix_peak'] >= 0.995:
        _issue(out, 'fail', 'mix-clip', None, m['mix_peak'])
    if vo and vo.exists():
        v, vsr = _read_wav(vo)
        vd = len(v) / vsr
        m['vo_duration'] = round(vd, 2)
        if vd > m['duration'] + 0.05:
            _issue(out, 'fail', 'vo-truncated', None,
                   f'vo {vd:.2f}s > video {m["duration"]}s')
        # measured in the delivered mix: speech windows vs pen-only windows
        n_ = min(len(mix), len(pen), int(m['duration'] * 48000))
        vv = np.zeros(n_, np.float32)
        if vsr != 48000:
            v = np.interp(np.arange(int(len(v) * 48000 / vsr)) * vsr / 48000,
                          np.arange(len(v)), v).astype(np.float32)
        vv[:min(n_, len(v))] = v[:n_]
        h_ = 480
        kk = n_ // h_
        vo_r = np.sqrt((vv[:kk * h_].reshape(kk, h_) ** 2).mean(1) + 1e-12)
        mx_r = np.sqrt((mix[:kk * h_].reshape(kk, h_) ** 2).mean(1) + 1e-12)
        pw_ = pen[:kk * h_].reshape(kk, h_).all(1)
        speech = vo_r > 10 ** (-30 / 20)
        pen_only = pw_ & (vo_r < 10 ** (-50 / 20))
        if speech.any() and pen_only.any():
            db = 20 * np.log10(np.sqrt((mx_r[speech] ** 2).mean())
                               / np.sqrt((mx_r[pen_only] ** 2).mean()))
            m['vo_over_sfx_db'] = round(float(db), 1)
            if db < 6:
                _issue(out, 'fail', 'sfx-masks-vo', None, round(float(db), 1))
    return out, m


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('plan')
    ap.add_argument('out_dir')
    ap.add_argument('--voiceover', default=None)
    ap.add_argument('--ratio', default='16:9')
    a = ap.parse_args(argv)
    plan = json.loads(Path(a.plan).read_text())
    name = str(plan.get('production_id') or 'whiteboard-v3')
    out_dir = Path(a.out_dir)
    vis, scenes = visual(plan, a.ratio)
    aud, metrics = audio(out_dir, name, Path(a.voiceover)
                         if a.voiceover else None)
    issues = vis + aud
    fails = [i for i in issues if i['severity'] == 'fail']
    rep = {'schema': 'NexMindStoryboardQAV1', 'production_id': name,
           'pass': not fails, 'fail_count': len(fails),
           'issues': issues, 'scenes': scenes, 'audio': metrics}
    (out_dir / f'{name}_SB_QA.json').write_text(
        json.dumps(rep, indent=1, default=str) + '\n')
    print(json.dumps({'pass': rep['pass'], 'fails': fails,
                      'warns': [i for i in issues
                                if i['severity'] == 'warn'],
                      'audio': metrics}, indent=1, default=str))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent))
    sys.exit(main())
