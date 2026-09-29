import { createHash } from "node:crypto";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";
import { EXPLAINER_LIBRARY_ROOT } from "./registry-loader";
import type { ScenePlan, SoundScheduleItem, VideoSpec, VisualVerb } from "./types";

// The RC1 source pack keeps the private audio pack beside `library/`, not
// inside it. Keep this path private and explicit so the pack is never served
// from `public/` or addressed by a browser URL.
export const AUTHORIZED_AUDIO_ROOT = resolve(EXPLAINER_LIBRARY_ROOT, "..", "audio", "authorized");

export type AuthorizedSound = {
  id: string;
  sourceFilename: string;
  path: string;
  sourceHash: string;
  semanticTags: string[];
  actions: string[];
  duplicateOf?: string;
};

function tagFor(filename: string) {
  const value = filename.toLowerCase();
  if (/paper|newspaper|handle/.test(value)) return { tags: ["paper", "reveal", "physical"], actions: ["Reveal", "Extract", "Assemble"] };
  if (/camera|shutter/.test(value)) return { tags: ["capture", "evidence", "click"], actions: ["Scan", "Detect", "Validate"] };
  if (/swipe|navigation|open/.test(value)) return { tags: ["transition", "swipe", "open"], actions: ["Route", "Split", "Transform"] };
  if (/success|confirm|level-up/.test(value)) return { tags: ["confirm", "success", "validation"], actions: ["Validate", "Deliver", "Repair"] };
  if (/cancel|back|exit/.test(value)) return { tags: ["cancel", "reverse"], actions: ["Collapse", "Filter"] };
  if (/pop|click|button|tap|ui/.test(value)) return { tags: ["ui", "click", "impact"], actions: ["Compare", "Rank", "Connect"] };
  if (/knife|place/.test(value)) return { tags: ["placement", "physical", "impact"], actions: ["Assemble", "Package"] };
  return { tags: ["general", "transition"], actions: ["Reveal", "Deliver"] };
}

export function loadAuthorizedSoundRegistry(root = AUTHORIZED_AUDIO_ROOT): AuthorizedSound[] {
  if (!existsSync(root)) throw new Error("AUTHORIZED_SOUND_PACK_MISSING");
  const files = readdirSync(root, { withFileTypes: true }).filter((entry) => entry.isFile() && /\.(mp3|wav|ogg)$/i.test(entry.name)).map((entry) => entry.name).sort((left, right) => left.localeCompare(right));
  const byHash = new Map<string, AuthorizedSound>();
  return files.map((sourceFilename) => {
    const path = join(root, sourceFilename);
    const sourceHash = createHash("sha256").update(readFileSync(path)).digest("hex");
    const existing = byHash.get(sourceHash);
    const semantic = tagFor(sourceFilename);
    const sound: AuthorizedSound = { id: `authorized.${sourceHash.slice(0, 16)}`, sourceFilename, path, sourceHash, semanticTags: semantic.tags, actions: semantic.actions, ...(existing ? { duplicateOf: existing.id } : {}) };
    if (!existing) byHash.set(sourceHash, sound);
    return sound;
  });
}

function soundAction(verb: VisualVerb) { return verb; }

export function buildAuthorizedSoundSchedule(scenes: ScenePlan[], registry = loadAuthorizedSoundRegistry()): SoundScheduleItem[] {
  const active = registry.filter((sound) => !sound.duplicateOf);
  return scenes.flatMap((scene) => {
    const action = soundAction(scene.visualVerb);
    const selected = active.filter((sound) => sound.actions.includes(action)).sort((left, right) => left.id.localeCompare(right.id))[0] ?? active[0];
    if (!selected) return [];
    return [{ sceneId: scene.id, soundId: selected.id, action, startSec: scene.startSec, volume: 0.32, sourceFilename: selected.sourceFilename, sourceHash: selected.sourceHash }];
  });
}

/** Sparse semantic accents for motion proofs. Unlike the legacy per-scene
 * schedule, this maps sound only to a causal event that benefits from it. */
export function buildSemanticSoundSchedule(scenes: ScenePlan[], registry = loadAuthorizedSoundRegistry()): SoundScheduleItem[] {
  const active = registry.filter((sound) => !sound.duplicateOf);
  const find = (tags: string[]) => active.find((sound) => tags.some((tag) => sound.semanticTags.includes(tag))) ?? active[0];
  const cueFor = (action: NonNullable<ScenePlan["motionDirection"]>["actions"][number]) => {
    if (["unfold", "open", "assemble", "reveal"].includes(action.action)) return { tags: ["paper", "physical", "open"], volume: .19 };
    if (["validate"].includes(action.action)) return { tags: ["success", "confirm"], volume: .22 };
    if (["flow", "travel", "fall", "rise", "transfer", "route"].includes(action.action as string)) return { tags: ["swipe", "transition"], volume: .17 };
    if (["grow", "branch", "extend", "transform"].includes(action.action)) return { tags: ["physical", "transition"], volume: .18 };
    if (["connect", "merge", "split"].includes(action.action)) return { tags: ["click", "impact"], volume: .17 };
    return undefined;
  };
  return scenes.flatMap((scene) => {
    const actions = scene.motionDirection?.actions ?? [];
    const primary = actions.find((item) => item.priority === "primary" && cueFor(item)) ?? actions.find((item) => cueFor(item));
    if (!primary) return [];
    const cue = cueFor(primary);
    if (!cue) return [];
    const sound = find(cue.tags);
    if (!sound) return [];
    return [{
      sceneId: scene.id,
      soundId: sound.id,
      action: primary.id,
      startSec: Math.round((scene.startSec + primary.startSec + primary.durationSec * .72) * 100) / 100,
      volume: cue.volume,
      sourceFilename: sound.sourceFilename,
      sourceHash: sound.sourceHash,
    }];
  });
}

export function assertAuthorizedSoundSchedule(spec: Pick<VideoSpec, "soundSchedule">, registry = loadAuthorizedSoundRegistry()) {
  const allowed = new Map(registry.filter((sound) => !sound.duplicateOf).map((sound) => [sound.id, sound.sourceHash]));
  for (const item of spec.soundSchedule) {
    if (item.soundId.startsWith("audio.")) throw new Error(`LEGACY_AUDIO_REFERENCE_FORBIDDEN: ${item.soundId}`);
    if (allowed.get(item.soundId) !== item.sourceHash) throw new Error(`AUTHORIZED_AUDIO_REFERENCE_INVALID: ${item.soundId}`);
  }
  return true;
}
