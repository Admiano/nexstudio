"use client";

import { useEffect, useMemo, useState } from "react";
import { Eyebrow } from "../App";
import { studioApi } from "../api";
import AvatarStage from "../cast/AvatarStage";
import {
  DEFAULT_SPEC, FACES, FEM_HAIRSTYLES, FEM_OUTFITS, HAIR_COLORS, LIPS,
  MALE_HAIRSTYLES, MALE_PIECES, NECKS, SKINS, VOICES, WATCHES,
  type CastMember, type CastSpec,
} from "../cast/spec";

type BuilderState = { mode: "new" } | { mode: "edit"; member: CastMember };

const hairStyles = (c: CastSpec["character"]) => (c === "female" ? FEM_HAIRSTYLES : MALE_HAIRSTYLES);
const voiceOf = (id: string | null) => VOICES.find((v) => v.id === id)?.label ?? "No voice yet";

function specSummary(s: CastSpec): string {
  const bits: string[] = [];
  const hair = s.hair ? `${s.hair.color} ${s.hair.style}` : "bald";
  bits.push(hair);
  const skin = SKINS.find((k) => k.key === s.skin)?.label ?? s.skin;
  bits.push(`${skin.toLowerCase()} skin`);
  if (s.character === "female" && s.lip) bits.push(`${s.lip} lip`);
  if (s.outfit?.kind) {
    const o = FEM_OUTFITS.find((x) => x.key === s.outfit!.kind);
    bits.push(s.character === "female" ? (o?.label ?? s.outfit.kind) : "shirt and trousers");
  }
  if (s.watch && s.watch !== "none") bits.push(`${s.watch} watch`);
  return bits.join(" · ");
}

function playVoice(id: string) {
  const a = new Audio(`/previews/voices/${id}.mp3`);
  void a.play().catch(() => {});
}

export function CastView({ notify, loading }: { notify: (msg: string) => void; loading: boolean }) {
  const [members, setMembers] = useState<CastMember[]>([]);
  const [busy, setBusy] = useState(true);
  const [builder, setBuilder] = useState<BuilderState | null>(null);
  const [spec, setSpec] = useState<CastSpec>(DEFAULT_SPEC.female);
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);

  const reload = () => {
    setBusy(true);
    studioApi.cast().then((r) => setMembers(r.cast)).catch(() => {}).finally(() => setBusy(false));
  };
  useEffect(reload, []);

  const open = (state: BuilderState) => {
    setBuilder(state);
    if (state.mode === "edit") {
      const s = state.member.spec;
      const ch: "female" | "male" = s?.character === "male" ? "male" : "female";
      setSpec(s ?? DEFAULT_SPEC[ch]);
      setName(state.member.name);
    } else {
      setSpec(DEFAULT_SPEC.female);
      setName("");
    }
  };

  const patch = (p: Partial<CastSpec>) => setSpec((s) => ({ ...s, ...p }));

  const switchCharacter = (c: CastSpec["character"]) => {
    setSpec((s) => (s.character === c ? s : DEFAULT_SPEC[c]));
  };

  const save = async () => {
    const trimmed = name.trim();
    if (!trimmed) { notify("Give your avatar a name first."); return; }
    setSaving(true);
    try {
      if (builder?.mode === "edit") {
        await studioApi.updateCast(builder.member.id, { name: trimmed, spec });
        notify(`${trimmed} updated.`);
      } else {
        await studioApi.createCast({ name: trimmed, spec });
        notify(`${trimmed} joined your cast.`);
      }
      setBuilder(null);
      reload();
    } catch {
      notify("Could not save. Try again.");
    } finally {
      setSaving(false);
    }
  };

  const remove = async (m: CastMember) => {
    try {
      await studioApi.deleteCast(m.id);
      notify(`${m.name} left the cast.`);
      reload();
    } catch {
      notify("Could not remove them. Try again.");
    }
  };

  return (
    <div className="cast-v2">
      <div className="v2-page-head">
        <div>
          <Eyebrow>Your cast</Eyebrow>
          <h1>Who presents your stories.</h1>
          <p>Build a presenter once, then cast them into any video or series. Their look, voice and name travel with them.</p>
        </div>
        <div className="v2-page-actions">
          <button className="v2-primary" onClick={() => open({ mode: "new" })}>+ New avatar</button>
        </div>
      </div>

      {(loading || busy) && (
        <div className="cast-grid" aria-hidden="true">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="cast-card cast-sk">
              <div className="cast-card-stage sk-block" />
              <div className="cast-card-meta"><div className="sk-line sk-lg" /><div className="sk-line sk-sm sk-gap" /></div>
            </div>
          ))}
        </div>
      )}

      {!busy && members.length === 0 && (
        <div className="cast-empty">
          <div className="cast-empty-stage" aria-hidden="true">
            <AvatarStage spec={DEFAULT_SPEC.female} />
          </div>
          <b>No one on your cast yet.</b>
          <p>Build your first presenter. Pick their look, their voice and a name, and they will be ready for every video and series you make.</p>
          <button className="v2-primary" onClick={() => open({ mode: "new" })}>Build an avatar</button>
        </div>
      )}

      {!busy && members.length > 0 && (
        <div className="cast-grid">
          {members.map((m) => (
            <div key={m.id} className="cast-card">
              <div className="cast-card-stage">
                {m.spec ? <AvatarStage spec={m.spec} /> : null}
              </div>
              <div className="cast-card-meta">
                <b>{m.name}</b>
                <span>{m.spec ? specSummary(m.spec) : "No look saved"}</span>
                <em>{voiceOf(m.spec?.voiceId ?? null)}</em>
              </div>
              <div className="cast-card-actions">
                <button className="v2-secondary" onClick={() => open({ mode: "edit", member: m })}>Edit</button>
                <button className="cast-remove" aria-label={`Remove ${m.name}`} onClick={() => remove(m)}>×</button>
              </div>
            </div>
          ))}
          <button className="cast-new" onClick={() => open({ mode: "new" })}>
            <span>+</span>
            <b>Build another avatar</b>
          </button>
        </div>
      )}

      {builder && (
        <div className={`series-identity-overlay open`} role="dialog" aria-modal="true">
          <div className="series-identity-panel">
            <div className="series-identity-body">
              <div className="panel-head">
                <div>
                  <p>{builder.mode === "new" ? "New avatar" : "Edit avatar"}</p>
                  <h2>{builder.mode === "new" ? "Build your presenter." : `Editing ${builder.member.name}`}</h2>
                </div>
                <button aria-label="Close builder" className="panel-close" onClick={() => setBuilder(null)}>×</button>
              </div>

              <div className="series-identity-live">
                <div className="series-identity-live-preview cast-live-preview">
                  <AvatarStage spec={spec} />
                </div>
                <div className="series-identity-live-copy">
                  <span>On stage</span>
                  <strong>{name.trim() || "Your avatar"}</strong>
                  <small>{specSummary(spec)}</small>
                </div>
              </div>

              <div className="cast-name-field">
                <label>Name</label>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="What should we call them?"
                  maxLength={60}
                />
              </div>

              <div className="identity-group">
                <div className="identity-group-head"><label>Character</label><span>the base performer</span></div>
                <div className="identity-frame">
                  <button aria-pressed={spec.character === "female"} onClick={() => switchCharacter("female")}>Woman</button>
                  <button aria-pressed={spec.character === "male"} onClick={() => switchCharacter("male")}>Man</button>
                </div>
              </div>

              <div className="identity-group">
                <div className="identity-group-head"><label>Face</label><span>how their features read</span></div>
                <div className="identity-tile-options">
                  {FACES.map((f) => (
                    <button key={f.id} className="identity-tile" aria-pressed={spec.face === f.id} onClick={() => patch({ face: f.id as CastSpec["face"] })}>{f.label}</button>
                  ))}
                </div>
              </div>

              <div className="identity-group">
                <div className="identity-group-head"><label>Skin</label><span>skin tone</span></div>
                <div className="identity-color-row">
                  {SKINS.map((s) => (
                    <button key={s.key} aria-label={`Skin ${s.label}`} className="identity-color" style={{ ["--c" as string]: s.hex }} aria-pressed={spec.skin === s.key} onClick={() => patch({ skin: s.key })} />
                  ))}
                </div>
              </div>

              <div className="identity-group">
                <div className="identity-group-head"><label>Hair</label><span>{spec.character === "female" ? "each style carries its own earring" : "hairstyle"}</span></div>
                <div className="identity-tile-options">
                  {hairStyles(spec.character).map((h) => (
                    <button key={h.key} className="identity-tile" aria-pressed={spec.hair?.style === h.key} onClick={() => patch({ hair: { style: h.key, color: spec.hair?.color ?? "auburn" } })}>
                      {h.label}{"note" in h && h.note ? <small>{h.note as string}</small> : null}
                    </button>
                  ))}
                </div>
                {spec.hair && (
                  <div className="identity-color-row" style={{ marginTop: 10 }}>
                    {HAIR_COLORS.map((c) => (
                      <button key={c.key} aria-label={`Hair ${c.label}`} className="identity-color" style={{ ["--c" as string]: c.hex }} aria-pressed={spec.hair?.color === c.key} onClick={() => patch({ hair: { style: spec.hair!.style, color: c.key } })} />
                    ))}
                    <label className="identity-custom-hex" title="Custom colour">
                      <input type="color" value={spec.hair.color.startsWith("#") ? spec.hair.color : "#9A4A2E"} onChange={(e) => patch({ hair: { style: spec.hair!.style, color: e.target.value } })} />
                      <span>custom</span>
                    </label>
                  </div>
                )}
              </div>

              {spec.character === "female" && (
                <div className="identity-group">
                  <div className="identity-group-head"><label>Lipstick</label><span>lip colour</span></div>
                  <div className="identity-options">
                    {LIPS.map((l) => (
                      <button key={l.key} className="identity-option" aria-pressed={spec.lip === l.key} onClick={() => patch({ lip: l.key })}>{l.label}</button>
                    ))}
                  </div>
                </div>
              )}

              {spec.character === "female" && (
                <div className="identity-group">
                  <div className="identity-group-head"><label>Neckwear</label><span>around the neckline</span></div>
                  <div className="identity-options">
                    {NECKS.map((n) => (
                      <button key={n.key} className="identity-option" aria-pressed={(spec.neck ?? "none") === n.key} onClick={() => patch({ neck: n.key === "none" ? null : n.key })}>{n.label}</button>
                    ))}
                  </div>
                </div>
              )}

              {spec.character === "female" ? (
                <div className="identity-group">
                  <div className="identity-group-head"><label>Outfit</label><span>what they wear</span></div>
                  <div className="identity-tile-options">
                    {FEM_OUTFITS.map((o) => (
                      <button key={o.key} className="identity-tile" aria-pressed={spec.outfit?.kind === o.key} onClick={() => patch({ outfit: { kind: o.key, color: spec.outfit?.color ?? null } })}>{o.label}</button>
                    ))}
                  </div>
                  <div className="identity-color-row" style={{ marginTop: 10 }}>
                    <label className="identity-custom-hex" title="Recolour the outfit">
                      <input type="color" value={spec.outfit?.color?.startsWith("#") ? spec.outfit.color : "#2E3A55"} onChange={(e) => patch({ outfit: { kind: spec.outfit?.kind ?? "sheath", color: e.target.value } })} />
                      <span>{spec.outfit?.color ? `wearing ${spec.outfit.color}` : "recolour"}</span>
                    </label>
                    {spec.outfit?.color ? <button className="identity-color-reset" onClick={() => patch({ outfit: { kind: spec.outfit!.kind, color: null } })}>reset</button> : null}
                  </div>
                </div>
              ) : (
                <div className="identity-group">
                  <div className="identity-group-head"><label>Outfit</label><span>recolour each piece</span></div>
                  <div className="identity-colour-fields">
                    {MALE_PIECES.map((p) => (
                      <label key={p.key} className="identity-colour-field">
                        <span>{p.label}</span>
                        <input type="color" value={spec.outfit?.pieces?.[p.key] ?? "#888888"} onChange={(e) => patch({ outfit: { kind: "casual", pieces: { ...(spec.outfit?.pieces ?? {}), [p.key]: e.target.value } } })} />
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {spec.character === "male" && (
                <div className="identity-group">
                  <div className="identity-group-head"><label>Watch</label><span>on the wrist</span></div>
                  <div className="identity-options">
                    {WATCHES.map((w) => (
                      <button key={w.key} className="identity-option" aria-pressed={(spec.watch ?? "none") === w.key} onClick={() => patch({ watch: w.key === "none" ? null : w.key })}>{w.label}</button>
                    ))}
                  </div>
                </div>
              )}

              <div className="identity-group">
                <div className="identity-group-head"><label>Voice</label><span>how they sound</span></div>
                <div className="identity-voice-list">
                  {VOICES.map((v) => (
                    <div key={v.id} className={`identity-voice ${spec.voiceId === v.id ? "selected" : ""}`}>
                      <button type="button" className="identity-voice-main" onClick={() => patch({ voiceId: v.id })}>
                        <b>{v.label}</b>
                        <span>{v.tag} voice</span>
                      </button>
                      <button type="button" aria-label={`Hear ${v.label}`} className="identity-voice-preview" onClick={() => playVoice(v.id)}>▶</button>
                    </div>
                  ))}
                </div>
              </div>

              <button className="series-identity-save" disabled={saving} onClick={save}>
                {saving ? "Saving…" : builder.mode === "new" ? "Add to cast" : "Save changes"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
