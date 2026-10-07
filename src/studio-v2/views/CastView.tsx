"use client";

import { useEffect, useState } from "react";
import { Eyebrow } from "../App";
import { studioApi } from "../api";
import {ENVIRONMENTS,environmentImage,type EnvironmentFormat} from '../cast/environments';
import OptionImage from "../cast/OptionImage";
import AvatarStage, {type AvatarPreviewState} from "../cast/AvatarStage";
import LiveCastStage from "../cast/LiveCastStage";
import {castRenderConfig} from "../cast/render-config";
import {
  DEFAULT_SPEC, FACES, FEM_DRESSES, FEM_DRESS_COLORS, FEM_HAIRSTYLES, FEM_HAIR_COLORS, LIPS,
  MALE_BOTTOMS, MALE_HAIRSTYLES, MALE_HAIR_COLORS, MALE_OUTFITS, MALE_TOP_COLORS, NECKS, SKINS, VOICES, WATCHES,
  MALE_OUTFIT_PIECES, malePieces, maleWatchAvailable, normalizeCastSpec,
  type CastMember, type CastSpec,
} from "../cast/spec";

type BuilderState = { mode: "new" } | { mode: "edit"; member: CastMember };

const hairStyles = (c: CastSpec["character"]) => (c === "female" ? FEM_HAIRSTYLES : MALE_HAIRSTYLES);
const hairColors = (c: CastSpec["character"]) => (c === "female" ? FEM_HAIR_COLORS : MALE_HAIR_COLORS);
const voiceOf = (id: string | null) => VOICES.find((v) => v.id === id)?.label ?? "No voice yet";

function CustomColour({label,value,onChange}:{label:string;value:string;onChange:(hex:string)=>void}){
 return <label className="identity-custom-hex"><input type="color" aria-label={label} value={value} onChange={e=>onChange(e.target.value)}/><span>Custom colour</span></label>;
}
const colourValue=(v:string|null|undefined,choices:readonly {key:string;hex:string}[])=>v&&/^#?[0-9a-f]{6}$/i.test(v)?"#"+v.replace(/^#/,""):choices.find(x=>x.key===v)?.hex??"#808080";

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
  if(s.character==="male"){const p=malePieces(s);bits.push(MALE_BOTTOMS.find(b=>b.key===p.bottom)!.label.toLowerCase());}
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

  const [preview,setPreview]=useState<{key:string;state:AvatarPreviewState}|null>(null);
  const visualKey=JSON.stringify({config:castRenderConfig(spec),environment:spec.environment,format:spec.environmentFormat});
  const previewReady=preview?.state==="ready"&&preview.key===visualKey;

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
    setPreview(null);
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
      outfit: { kind, color: s.outfit?.color ?? undefined, ...(s.character==="male"&&MALE_OUTFIT_PIECES[kind]?{pieces:{...MALE_OUTFIT_PIECES[kind]}}:{}) },
    }, s.character));
  };

  const patchOutfitColor = (color: string) => {
    setSpec((s) => normalizeCastSpec({
      ...s,
      outfit: { ...s.outfit, kind: s.outfit?.kind ?? DEFAULT_SPEC[s.character].outfit!.kind, color },
    }, s.character));
  };

  const patchPieces=(values:Record<string,string>)=>setSpec(s=>normalizeCastSpec({...s,outfit:{...s.outfit!,pieces:{...malePieces(s),...values}}}));

  const save = async () => {
    if(!previewReady){notify("Wait for your selected look to finish previewing.");return;}
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
        <div className="series-identity-overlay open cast-builder" role="dialog" aria-modal="true" aria-label="Presenter customizer">
          <div className="series-identity-panel">
            <div className="series-identity-body">
              <div className="panel-head">
                <div>
                  <p>{builder.mode === "new" ? "New avatar" : "Edit avatar"}</p>
                  <h2>{builder.mode === "new" ? "Build your presenter." : `Editing ${builder.member.name}`}</h2>
                </div>
                <button aria-label="Close builder" className="panel-close" onClick={() => setBuilder(null)}>×</button>
              </div>

              <div className="cast-builder-workspace">
              <div className="series-identity-live">
                <div className="series-identity-live-preview cast-live-preview">
                  <LiveCastStage spec={spec} onStatus={state=>setPreview({key:visualKey,state})}/>
                </div>
                <div className="series-identity-live-copy">
                  <span>On stage</span>
                  <strong>{name.trim() || "Your avatar"}</strong>
                  <small>{specSummary(spec)}</small>
                </div>
              </div>

              <div className="cast-builder-controls">
              <div className="cast-name-field">
                <label>Name</label>
                <input value={name} onChange={(e) => setName(e.target.value)} placeholder="What should we call them?" maxLength={60} />
              </div>

              <div className="identity-group">
                <div className="identity-group-head"><label>Character</label><span>the base performer</span></div>
                <div className="cast-image-options cast-character-options">
                  <OptionImage character="female" category="character" option="female" label="Woman" selected={spec.character === "female"} onSelect={() => switchCharacter("female")} />
                  <OptionImage character="male" category="character" option="male" label="Man" selected={spec.character === "male"} onSelect={() => switchCharacter("male")} />
                </div>
              </div>

              <div className="identity-group">
                <div className="identity-group-head"><label>Face</label><span>how their features read</span></div>
                <div className="cast-image-options">
                  {FACES.map((f) => (
                    <OptionImage key={f.id} character={spec.character} category="face" option={f.id} label={f.label} selected={spec.face === f.id} onSelect={() => patch({ face: f.id as CastSpec["face"] })} />
                  ))}
                </div>
              </div>

              <div className="identity-group">
                <div className="identity-group-head"><label>Skin</label><span>skin tone</span></div>
                <div className="identity-color-row">
                  {SKINS.map((s) => (
                    <button key={s.key} aria-label={`Skin ${s.label}`} className="identity-color" style={{ ["--c" as string]: s.hex }} aria-pressed={spec.skin === s.key} onClick={() => patch({ skin: s.key })} />
                  ))}
                    <CustomColour label="Custom skin colour" value={colourValue(spec.skin,SKINS)} onChange={skin=>patch({skin})}/>
                </div>
              </div>

              <div className="identity-group">
                <div className="identity-group-head"><label>Hair</label><span>{spec.character === "female" ? "each style carries its own earring" : "hairstyle"}</span></div>
                <div className="cast-image-options">
                  {hairStyles(spec.character).map((h) => (
                    <OptionImage key={h.key} character={spec.character} category="hair" option={h.key} label={h.label} selected={spec.hair?.style === h.key} onSelect={() => patch({ hair: { style: h.key, color: spec.hair?.color ?? DEFAULT_SPEC[spec.character].hair!.color } })} note={"note" in h ? h.note as string : undefined} />
                  ))}
                </div>
                {spec.hair && (
                  <div className="identity-color-row" style={{ marginTop: 10 }}>
                    {hairColors(spec.character).map((c) => (
                      <button key={c.key} aria-label={`Hair ${c.label}`} className="identity-color" style={{ ["--c" as string]: c.hex }} aria-pressed={spec.hair?.color === c.key} onClick={() => patch({ hair: { style: spec.hair!.style, color: c.key } })} />
                    ))}
                    <CustomColour label="Custom hair colour" value={colourValue(spec.hair!.color,hairColors(spec.character))} onChange={color=>patch({hair:{...spec.hair!,color}})}/>
                  </div>
                )}
              </div>

              {spec.character === "female" && (
                <div className="identity-group">
                  <div className="identity-group-head"><label>Lipstick</label><span>lip colour</span></div>
                  <div className="identity-color-row">
                    {LIPS.map((l) => (
                      <button key={l.key} className="identity-color" aria-label={l.label} title={l.label} style={{["--c" as string]:l.hex}} aria-pressed={spec.lip === l.key} onClick={() => patch({ lip: l.key })} />
                    ))}
                    <CustomColour label="Custom lipstick colour" value={colourValue(spec.lip,LIPS)} onChange={lip=>patch({lip})}/>
                  </div>
                </div>
              )}

              {spec.character === "female" && (
                <div className="identity-group">
                  <div className="identity-group-head"><label>Neckwear</label><span>around the neckline</span></div>
                  <div className="cast-image-options">
                    {NECKS.map((n) => (
                      <OptionImage key={n.key} character={"female"} category="neck" option={n.key} label={n.label} selected={(spec.neck ?? "none") === n.key} onSelect={() => patch({ neck: n.key === "none" ? null : n.key })} />
                    ))}
                  </div>
                </div>
              )}

              {spec.character === "female" ? (
                <>
                  <div className="identity-group">
                    <div className="identity-group-head"><label>Dress style</label><span>shape and cut</span></div>
                    <div className="cast-image-options">
                      {FEM_DRESSES.map((o) => (
                        <OptionImage key={o.key} character={"female"} category="dress" option={o.key} label={o.label} selected={spec.outfit?.kind === o.key} onSelect={() => patchOutfitKind(o.key)} />
                      ))}
                    </div>
                  </div>
                  <div className="identity-group">
                    <div className="identity-group-head"><label>Dress colour</label><span>independent of style</span></div>
                    <div className="identity-color-row">
                      {FEM_DRESS_COLORS.map((c) => (
                        <button key={c.key} aria-label={`Dress ${c.label}`} className="identity-color" style={{ ["--c" as string]: c.hex }} aria-pressed={spec.outfit?.color === c.key} onClick={() => patchOutfitColor(c.key)} />
                      ))}
                    <CustomColour label="Custom dress colour" value={colourValue(spec.outfit?.color,FEM_DRESS_COLORS)} onChange={patchOutfitColor}/>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div className="identity-group">
                    <div className="identity-group-head"><label>Top style</label><span>shape and cut</span></div>
                    <div className="cast-image-options">
                      {MALE_OUTFITS.map((o) => (
                        <OptionImage key={o.key} character={"male"} category="top" option={o.key} label={o.label} selected={spec.outfit?.kind === o.key} onSelect={() => patchOutfitKind(o.key)} />
                      ))}
                    </div>
                  </div>
                  <div className="identity-group">
                    <div className="identity-group-head"><label>Top colour</label><span>independent of style</span></div>
                    <div className="identity-color-row">
                      {MALE_TOP_COLORS.map((c) => (
                        <button key={c.key} aria-label={`Top ${c.label}`} className="identity-color" style={{ ["--c" as string]: c.hex }} aria-pressed={spec.outfit?.color === c.key} onClick={() => patchOutfitColor(c.key)} />
                      ))}
                    <CustomColour label="Custom top colour" value={colourValue(spec.outfit?.color,MALE_TOP_COLORS)} onChange={patchOutfitColor}/>
                    </div>
</div>
<div className="identity-group"><div className="identity-group-head"><label>Trousers</label><span>choose separately</span></div><div className="cast-image-options">{MALE_BOTTOMS.map(b=><OptionImage key={b.key} character="male" category="bottom" option={b.key} label={b.label} selected={malePieces(spec).bottom===b.key} onSelect={()=>patchPieces({bottom:b.key})} />)}</div><div className="identity-color-row" style={{marginTop:10}}>{MALE_BOTTOMS.map(b=><button key={b.key} aria-label={"Trousers "+b.label+" colour"} className="identity-color" style={{["--c" as string]:b.hex}} aria-pressed={malePieces(spec).bottomColor===b.hex} onClick={()=>patchPieces({bottomColor:b.hex})}/>)}<CustomColour label="Custom trouser colour" value={malePieces(spec).bottomColor} onChange={bottomColor=>patchPieces({bottomColor})}/></div></div>



                </>
              )}

              {spec.character === "male" && maleWatchAvailable(spec.outfit?.kind ?? "") && (
                <div className="identity-group">
                  <div className="identity-group-head"><label>Watch</label><span>on the wrist</span></div>
                  <div className="cast-image-options">
                    {WATCHES.map((w) => (
                      <OptionImage key={w.key} character={"male"} category="watch" option={w.key} label={w.label} selected={(spec.watch ?? "none") === w.key} onSelect={() => patch({ watch: w.key === "none" ? null : w.key })} />
                    ))}
                  </div>
                </div>
              )}

              <div className="identity-group">
                <div className="identity-group-head"><label>Environment</label><span>where they present</span></div>
                <div className="identity-options"><button className="identity-option" aria-pressed={!spec.environment} onClick={()=>patch({environment:null})}>No background</button></div>
                <div className="cast-image-options cast-environment-options">{ENVIRONMENTS.map(e=><button type="button" key={e.key} className="cast-image-option" aria-label={e.label} aria-pressed={spec.environment===e.key} onClick={()=>patch({environment:e.key})}><span className="cast-image-option-art"><img src={environmentImage(e.key,'square')} alt="" width={224} height={224} loading="lazy" />{spec.environment===e.key&&<span className="cast-image-option-check" aria-hidden="true">✓</span>}</span><span className="cast-image-option-label">{e.label}</span></button>)}</div>
                {spec.environment&&<div className="identity-options" style={{marginTop:10}}>{(['landscape','square','portrait'] as EnvironmentFormat[]).map(format=><button type="button" key={format} className="identity-option" aria-pressed={(spec.environmentFormat??'square')===format} onClick={()=>patch({environmentFormat:format})}>{format==='landscape'?'16:9':format==='portrait'?'9:16':'1:1'}</button>)}</div>}
              </div>

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

              <button className="series-identity-save" disabled={saving||!previewReady} onClick={save}>
                {saving ? "Saving…" : !previewReady ? "Waiting for preview…" : builder.mode === "new" ? "Add to cast" : "Save changes"}
              </button>
              </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
