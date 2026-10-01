"use client";

import { useEffect, useState } from "react";
import { Eyebrow } from "../App";
import { studioApi } from "../api";
import AvatarStage from "../cast/AvatarStage";
import {
  DEFAULT_SPEC, FACES, FEM_DRESSES, FEM_DRESS_COLORS, FEM_HAIRSTYLES, FEM_HAIR_COLORS, LIPS,
  MALE_HAIRSTYLES, MALE_HAIR_COLORS, MALE_OUTFITS, MALE_TOP_COLORS, NECKS, SKINS, VOICES, WATCHES,
  normalizeCastSpec,
  type CastMember, type CastSpec,
} from "../cast/spec";

type BuilderState = { mode: "new" } | { mode: "edit"; member: CastMember };

const hairStyles = (c: CastSpec["character"]) => (c === "female" ? FEM_HAIRSTYLES : MALE_HAIRSTYLES);
const hairColors = (c: CastSpec["character"]) => (c === "female" ? FEM_HAIR_COLORS : MALE_HAIR_COLORS);
const voiceOf = (id: string | null) => VOICES.find((v) => v.id === id)?.label ?? "No voice yet";

function specSummary(s0: CastSpec): string {
  const s = normalizeCastSpec(s0, s0.character);
  const bits: string[] = [];
  const hs = hairStyles(s.character).find((h) => h.key === s.hair?.style);
  const hc = hairColors(s.character).find((c) => c.key === s.hair?.color);
  bits.push(s.hair ? `${(hc?.label ?? s.hair.color).toLowerCase()} ${(hs?.label ?? s.hair.style).toLowerCase()}` : "bald");
  const skin = SKINS.find((k) => k.key === s.skin)?.label ?? s.skin;
  bits.push(`${skin.toLowerCase()} skin`);
  if (s.character === "female" && s.lip) {
    bits.push(`${(LIPS.find((l) => l.key === s.lip)?.label ?? s.lip).toLowerCase()} lip`);
  }
  if (s.outfit?.kind) {
    const label = s.character === "female"
      ? FEM_DRESSES.find((x) => x.key === s.outfit!.kind)?.label
      : MALE_OUTFITS.find((x) => x.key === s.outfit!.kind)?.label;
    const colour = s.character === "female"
      ? FEM_DRESS_COLORS.find((x) => x.key === s.outfit!.color)?.label
      : MALE_TOP_COLORS.find((x) => x.key === s.outfit!.color)?.label;
    bits.push(`${(colour ?? "").toLowerCase()} ${(label ?? s.outfit.kind).toLowerCase()}`.trim());
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
  const [armedId, setArmedId] = useState<string | null>(null);

  const castChanged = () => window.dispatchEvent(new Event("nx-cast-changed"));

  const reload = () => {
    setBusy(true);
    studioApi.cast()
      .then((r) => setMembers(r.cast))
      .catch(() => {})
      .finally(() => setBusy(false));
  };
  useEffect(reload, []);

  const open = (state: BuilderState) => {
    setBuilder(state);
    if (state.mode === "edit") {
      const raw = state.member.spec;
      const ch: "female" | "male" = raw?.character === "male" ? "male" : "female";
      setSpec(normalizeCastSpec(raw, ch));
      setName(state.member.name);
    } else {
      setSpec(DEFAULT_SPEC.female);
      setName("");
    }
  };

  const patch = (p: Partial<CastSpec>) => setSpec((s) => normalizeCastSpec({ ...s, ...p }, s.character));

  const switchCharacter = (c: CastSpec["character"]) => {
    setSpec((s) => (s.character === c ? s : DEFAULT_SPEC[c]));
  };

  const patchOutfitKind = (kind: string) => {
    setSpec((s) => normalizeCastSpec({
      ...s,
      outfit: { kind, color: s.outfit?.color ?? undefined },
    }, s.character));
  };

  const patchOutfitColor = (color: string) => {
    setSpec((s) => normalizeCastSpec({
      ...s,
      outfit: { kind: s.outfit?.kind ?? DEFAULT_SPEC[s.character].outfit!.kind, color },
    }, s.character));
  };

  const save = async () => {
    const trimmed = name.trim();
    if (!trimmed) { notify("Give your avatar a name first."); return; }
    const cleanSpec = normalizeCastSpec(spec, spec.character);
    setSaving(true);
    try {
      if (builder?.mode === "edit") {
        await studioApi.updateCast(builder.member.id, { name: trimmed, spec: cleanSpec });
        notify(`${trimmed} updated.`);
      } else {
        await studioApi.createCast({ name: trimmed, spec: cleanSpec });
        notify(`${trimmed} joined your cast.`);
      }
      setBuilder(null);
      reload();
      castChanged();
    } catch {
      notify("Could not save. Try again.");
    } finally {
      setSaving(false);
    }
  };

  const remove = async (m: CastMember) => {
    if (armedId !== m.id) {
      setArmedId(m.id);
      setTimeout(() => setArmedId((a) => (a === m.id ? null : a)), 3000);
      return;
    }
    setArmedId(null);
    try {
      await studioApi.deleteCast(m.id);
      notify(`${m.name} left the cast.`);
      reload();
      castChanged();
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
          {members.map((m) => {
            const cardSpec = m.spec ? normalizeCastSpec(m.spec, m.spec.character) : null;
            return (
              <div key={m.id} className="cast-card">
                <div className="cast-card-stage">
                  {cardSpec ? <AvatarStage spec={cardSpec} /> : null}
                </div>
                <div className="cast-card-meta">
                  <b>{m.name}</b>
                  <span>{cardSpec ? specSummary(cardSpec) : "No look saved"}</span>
                  <em>{voiceOf(cardSpec?.voiceId ?? null)}</em>
                </div>
                <div className="cast-card-actions">
                  <button className="v2-secondary" onClick={() => open({ mode: "edit", member: m })}>Edit</button>
                  <button className={`cast-remove ${armedId === m.id ? "armed" : ""}`} aria-label={`Remove ${m.name}`} onClick={() => remove(m)}>{armedId === m.id ? "Remove?" : "×"}</button>
                </div>
              </div>
            );
          })}
          <button className="cast-new" onClick={() => open({ mode: "new" })}>
            <span>+</span>
            <b>Build another avatar</b>
          </button>
        </div>
      )}

      {builder && (
        <div className="series-identity-overlay open" role="dialog" aria-modal="true">
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
                <input value={name} onChange={(e) => setName(e.target.value)} placeholder="What should we call them?" maxLength={60} />
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
                    <button key={h.key} className="identity-tile" aria-pressed={spec.hair?.style === h.key} onClick={() => patch({ hair: { style: h.key, color: spec.hair?.color ?? DEFAULT_SPEC[spec.character].hair!.color } })}>
                      {h.label}{"note" in h && h.note ? <small>{h.note as string}</small> : null}
                    </button>
                  ))}
                </div>
                {spec.hair && (
                  <div className="identity-color-row" style={{ marginTop: 10 }}>
                    {hairColors(spec.character).map((c) => (
                      <button key={c.key} aria-label={`Hair ${c.label}`} className="identity-color" style={{ ["--c" as string]: c.hex }} aria-pressed={spec.hair?.color === c.key} onClick={() => patch({ hair: { style: spec.hair!.style, color: c.key } })} />
                    ))}
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
                <>
                  <div className="identity-group">
                    <div className="identity-group-head"><label>Dress style</label><span>shape and cut</span></div>
                    <div className="identity-tile-options">
                      {FEM_DRESSES.map((o) => (
                        <button key={o.key} className="identity-tile" aria-pressed={spec.outfit?.kind === o.key} onClick={() => patchOutfitKind(o.key)}>
                          {o.label}<small>{o.note}</small>
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="identity-group">
                    <div className="identity-group-head"><label>Dress colour</label><span>independent of style</span></div>
                    <div className="identity-color-row">
                      {FEM_DRESS_COLORS.map((c) => (
                        <button key={c.key} aria-label={`Dress ${c.label}`} className="identity-color" style={{ ["--c" as string]: c.hex }} aria-pressed={spec.outfit?.color === c.key} onClick={() => patchOutfitColor(c.key)} />
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div className="identity-group">
                    <div className="identity-group-head"><label>Outfit style</label><span>top cut, trousers and shoes</span></div>
                    <div className="identity-tile-options">
                      {MALE_OUTFITS.map((o) => (
                        <button key={o.key} className="identity-tile" aria-pressed={spec.outfit?.kind === o.key} onClick={() => patchOutfitKind(o.key)}>
                          {o.label}<small>{o.note}</small>
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="identity-group">
                    <div className="identity-group-head"><label>Top colour</label><span>trousers and shoes stay with the outfit</span></div>
                    <div className="identity-color-row">
                      {MALE_TOP_COLORS.map((c) => (
                        <button key={c.key} aria-label={`Top ${c.label}`} className="identity-color" style={{ ["--c" as string]: c.hex }} aria-pressed={spec.outfit?.color === c.key} onClick={() => patchOutfitColor(c.key)} />
                      ))}
                    </div>
                  </div>
                </>
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
                        <b>{v.label}</b><span>{v.tag} voice</span>
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
