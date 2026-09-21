/*
 * Authorship gate: folds per-frame runtime inspections (window.__em2.inspect()) into the
 * render manifest's `authorship` block — the generated-look tells a viewer would catch:
 *
 *   EMPTY_CHASSIS / ICON_UNDERFILL / ICON_OVERFLOW / ORPHAN_CONNECTOR   (from the runtime, per frame)
 *   STATIC_HOLD   an on-stage illustration entity whose pose never changes for > STATIC_HOLD_MAX_MS
 *
 * Every finding is deterministic and names the beat + element so the treatment (or the engine
 * rule that produced the plan) can be fixed. The regression pack fails a film on any finding.
 */
const STATIC_HOLD_MAX_MS = 3000;

class AuthorshipLedger {
  constructor(fps) {
    this.frameMs = 1000 / fps;
    this.findings = new Map(); // code|beat|id -> finding with first/last ms and frame count
    this.runs = new Map(); // beat:entity -> { sig, since_ms, best_ms }
    this.frames = 0;
  }

  observe(ms, snap) {
    this.frames += 1;
    for (const f of snap.findings || []) {
      const key = `${f.code}|${f.beat_id}|${f.id}`;
      const cur = this.findings.get(key);
      if (cur) { cur.last_ms = ms; cur.frames += 1; } else this.findings.set(key, { ...f, first_ms: ms, last_ms: ms, frames: 1 });
    }
    const seen = new Set();
    for (const [key, sig] of Object.entries(snap.entities || {})) {
      seen.add(key);
      const run = this.runs.get(key);
      if (sig == null) { if (run) run.sig = null; continue; }
      if (!run) { this.runs.set(key, { sig, since_ms: ms, best_ms: 0, best_from: ms }); continue; }
      if (run.sig === sig) {
        const held = ms - run.since_ms + this.frameMs;
        if (held > run.best_ms) { run.best_ms = held; run.best_from = run.since_ms; }
      } else {
        run.sig = sig;
        run.since_ms = ms;
      }
    }
    // Entities absent from the snapshot (beat not on stage) end their run.
    for (const [key, run] of this.runs) if (!seen.has(key)) run.sig = null;
  }

  report() {
    const findings = Array.from(this.findings.values()).sort((a, b) => a.first_ms - b.first_ms || a.code.localeCompare(b.code));
    const holds = [];
    for (const [key, run] of this.runs) {
      if (run.best_ms > STATIC_HOLD_MAX_MS) {
        const [beat_id, id] = key.split(':');
        holds.push({ code: 'STATIC_HOLD', beat_id, id, detail: `pose unchanged for ${Math.round(run.best_ms)}ms`, first_ms: run.best_from, last_ms: run.best_from + run.best_ms, frames: Math.round(run.best_ms / this.frameMs) });
      }
    }
    holds.sort((a, b) => a.first_ms - b.first_ms);
    const all = findings.concat(holds);
    return {
      frames_inspected: this.frames,
      static_hold_max_ms: STATIC_HOLD_MAX_MS,
      longest_static_hold_ms: Math.round(Math.max(0, ...Array.from(this.runs.values()).map((r) => r.best_ms))),
      findings: all,
      codes: Array.from(new Set(all.map((f) => f.code))).sort(),
    };
  }
}

module.exports = { AuthorshipLedger, STATIC_HOLD_MAX_MS };
