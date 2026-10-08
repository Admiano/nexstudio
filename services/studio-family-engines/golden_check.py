#!/usr/bin/env python3
"""Golden subtype pack: locked reference renders per certified dispatch subtype.

  record <family>/<subtype> <job_dir>   — fingerprint a finished job dir into golden/
  verify <family>/<subtype>             — re-render the fixture through site_job_runner,
                                          compare fingerprints; exit 1 on regression
  verify all                            — every registered subtype with a baseline
  list                                  — baseline status per subtype

Fingerprints are structural, not bytes: dispatch contract (status done, outputs
present), duration band, non-blank sampled frames, and per-subtype extras
(kinetic icon count, gate-report failures). Deterministic engines still vary
frame-level output across environments, so hashes are recorded for forensics
but never compared.
"""
from __future__ import annotations

import json, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GOLDEN = HERE / "golden"
FIXTURES = json.loads((HERE / "golden-subtypes.json").read_text())["fixtures"]
DISPATCH = json.loads((HERE / "site-dispatch.json").read_text())
RUNNER = HERE / "site_job_runner.py"

NONBLANK_MIN_STD = 12.0  # luma stddev below this reads as a blank frame


def _probe(path: Path) -> dict:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration", "-show_entries", "stream=codec_type,width,height",
             "-of", "json", str(path)],
            capture_output=True, text=True, check=True).stdout
        return json.loads(out)
    except Exception:
        return {}


def _duration(probe: dict) -> float:
    try:
        return float(probe.get("format", {}).get("duration") or 0)
    except (TypeError, ValueError):
        return 0.0


def _nonblank(path: Path, dur: float) -> float:
    """Fraction of 3 sampled mid-video frames whose luma stddev clears the floor."""
    from PIL import Image
    ok, sampled = 0, 0
    for frac in (0.3, 0.55, 0.8):
        t = max(0.2, dur * frac)
        frame = path.parent / f".golden-frame-{int(t * 10)}.png"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t),
                        "-i", str(path), "-vframes", "1", str(frame)],
                       capture_output=True)
        if frame.exists():
            sampled += 1
            im = Image.open(frame).convert("L")
            px = list(im.getdata())
            mean = sum(px) / len(px)
            std = (sum((p - mean) ** 2 for p in px) / len(px)) ** 0.5
            if std >= NONBLANK_MIN_STD:
                ok += 1
            frame.unlink()
    return ok / sampled if sampled else 0.0


def _metrics_files(j: Path) -> list[Path]:
    return sorted((j / "out").glob("*/[A-Z0-9]*_METRICS.json")) if (j / "out").exists() else []


def _gate_failures(j: Path) -> list[str]:
    out = []
    d = j / "out"
    if not d.exists():
        return out
    for entry in d.iterdir():
        rep = entry / "gate_report.json"
        if rep.exists():
            try:
                out += json.loads(rep.read_text()).get("failures") or []
            except Exception:
                pass
    return out


def fingerprint(j: Path, family: str, subtype: str, job_id: str) -> dict:
    """Structural fingerprint of a finished job dir."""
    status = json.loads((j / "status.json").read_text()) if (j / "status.json").exists() else {}
    outputs = status.get("outputs") or {}
    videos = {}
    files = j / "files"
    if files.exists():
        for p in sorted(files.glob("*.mp4")):
            probe = _probe(p)
            dur = _duration(probe)
            videos[p.stem] = {"durationSec": round(dur, 2), "nonBlank": round(_nonblank(p, dur), 2),
                              "bytes": p.stat().st_size}
    icons = None
    for m in _metrics_files(j):
        try:
            icons = len(json.loads(m.read_text()).get("icons") or [])
            break
        except Exception:
            continue
    return {
        "schema": "StudioGoldenBaselineV1", "family": family, "subtype": subtype,
        "recordedFrom": job_id, "recordedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": status.get("status"), "outputs": sorted(outputs),
        "videos": videos, "iconCount": icons, "gateFailures": _gate_failures(j),
    }


def record(family: str, subtype: str, j: Path) -> Path:
    status = json.loads((j / "status.json").read_text()) if (j / "status.json").exists() else {}
    if status.get("status") != "done":
        raise SystemExit(f"refusing baseline: {j} status is {status.get('status')!r}, not done")
    fp = fingerprint(j, family, subtype, j.name)
    dest = GOLDEN / family / f"{subtype}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(fp, indent=1) + "\n")
    print(f"recorded {family}/{subtype} from {j.name}: "
          f"{len(fp['videos'])} videos, icons={fp['iconCount']}, gateFailures={len(fp['gateFailures'])}")
    return dest


def _prepare_fixture_dir(family: str, subtype: str, fx: dict) -> Path:
    """Materialise a job dir the runner can dispatch, incl. files routes would write."""
    j = Path(tempfile.mkdtemp(prefix=f"golden-{subtype}-"))
    params = dict(fx["params"])
    if family == "presenter":
        # presenter-job.py reads request.json (cast config, voice, background);
        # the golden template carries a real saved-cast spec.
        tpl = GOLDEN / "templates" / f"{subtype}.request.json"
        if not tpl.exists():
            raise SystemExit(f"{family}/{subtype}: missing template {tpl}")
        shutil.copyfile(tpl, j / "request.json")
        req = {"schema": "StudioSiteEngineRequestV1", "family": family,
               "subtype": subtype, "jobId": f"golden-{subtype}", "params": {}}
        (j / "engine_request.json").write_text(json.dumps(req, indent=1))
        (j / "status.json").write_text(json.dumps({"status": "running"}))
        return j
    script = params.pop("script", None)
    script_path = None
    if script:
        script_path = j / "script.txt"
        script_path.write_text(script if script.endswith("\n") else script + "\n")
    req = {"schema": "StudioSiteEngineRequestV1", "family": family, "subtype": subtype,
           "jobId": f"golden-{subtype}",
           "params": {**params, "scriptPath": str(script_path) if script_path else None,
                      "voiceFile": None, "media": []}}
    if family == "explainer":
        req["params"]["script"] = script  # make_reel takes inline script text
    (j / "engine_request.json").write_text(json.dumps(req, indent=1))
    (j / "request.json").write_text(json.dumps({"createdAt": time.strftime(
        "%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "goldenFixture": True}))
    (j / "status.json").write_text(json.dumps({"status": "running"}))
    return j


def verify(family: str, subtype: str) -> bool:
    key = f"{family}/{subtype}"
    fx = FIXTURES.get(key)
    base_path = GOLDEN / family / f"{subtype}.json"
    if not fx:
        print(f"{key}: SKIP — no fixture"); return True
    if not base_path.exists():
        print(f"{key}: NO BASELINE — run record first"); return False
    base = json.loads(base_path.read_text())

    j = _prepare_fixture_dir(family, subtype, fx)
    code = subprocess.run([sys.executable, str(RUNNER), str(j)]).returncode
    fp = fingerprint(j, family, subtype, j.name)
    expect = fx.get("expect") or {}
    failures = []

    if code != 0 or fp["status"] != "done":
        failures.append(f"dispatch did not complete (exit {code}, status {fp['status']})")
    if not fp["outputs"]:
        failures.append("no outputs produced")
    lo, hi = (expect.get("durationSec") or [0, 10**6])
    for stem, v in fp["videos"].items():
        if not (lo <= v["durationSec"] <= hi):
            failures.append(f"{stem} duration {v['durationSec']}s outside [{lo},{hi}]")
        if v["nonBlank"] < 1.0:
            failures.append(f"{stem} has blank sampled frames ({v['nonBlank']:.0%} ok)")
    if len(fp["videos"]) < len(fx["params"].get("aspects") or base["outputs"] or [1]):
        failures.append(f"only {len(fp['videos'])} aspect outputs")
    if expect.get("minIcons") and (fp["iconCount"] or 0) < expect["minIcons"]:
        failures.append(f"icons={fp['iconCount']} below floor {expect['minIcons']}")
    if fp["gateFailures"]:
        failures.append(f"gate failures: {fp['gateFailures'][0]}")

    shutil.rmtree(j, ignore_errors=True)
    if failures:
        print(f"{key}: FAIL — " + "; ".join(failures)); return False
    parts = ", ".join(f"{k} {v['durationSec']}s" for k, v in fp["videos"].items())
    print(f"{key}: PASS ({parts}"
          + (f", {fp['iconCount']} icons" if fp['iconCount'] is not None else "") + ")")
    return True


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list":
        for key in sorted(FIXTURES):
            fam, sub = key.split("/", 1)
            mark = "baseline" if (GOLDEN / fam / f"{sub}.json").exists() else "NO BASELINE"
            print(f"{key}: {mark}")
        return
    if cmd == "record":
        family, subtype = sys.argv[2].split("/", 1)
        record(family, subtype, Path(sys.argv[3]).resolve())
        return
    if cmd == "verify":
        if sys.argv[2] == "all":
            ok = True
            for key in sorted(FIXTURES):
                fam, sub = key.split("/", 1)
                if (GOLDEN / fam / f"{sub}.json").exists():
                    ok = verify(fam, sub) and ok
            sys.exit(0 if ok else 1)
        family, subtype = sys.argv[2].split("/", 1)
        sys.exit(0 if verify(family, subtype) else 1)
    print(__doc__)
    sys.exit(2)


if __name__ == "__main__":
    main()
