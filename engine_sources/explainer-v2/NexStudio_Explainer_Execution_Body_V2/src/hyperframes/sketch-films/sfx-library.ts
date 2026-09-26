/* SFX library — semantic slots over the bundled sound pool.
 *
 * spec.sfx entries may carry a path of `sfx:<name>` which resolves here to a
 * file inside runtime-assets/sfx (Kenney interface-sounds pack, CC0 + the two
 * legacy freesound mp3s). Plain relative paths still resolve against the spec
 * dir, so existing specs are unaffected.
 */
import * as path from "path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const SFX_ROOT = path.resolve(here, "../../../runtime-assets/sfx");

export const SFX_LIBRARY: Record<string, string> = {
  /* transitions */
  "transition.swipe": "swipe.mp3",      // paper-leaning whoosh (legacy)
  "transition.torn": "paper.mp3",       // tear/crumple family
  "transition.hard": "switch_001.ogg",  // doors/push/diamond — mechanical snap
  "transition.soft": "drop_002.ogg",    // fade-ish drops
  /* entrances + accents */
  "entrance.pop": "pop.mp3",
  "accent.tick": "tick_001.ogg",        // stat wheel settle / decode ticks
  "accent.pluck": "pluck_001.ogg",      // callout annotations
  "accent.glitch": "glitch_004.ogg",    // decode reveals
  /* reveals */
  "reveal.confirm": "confirmation_001.ogg",
  "reveal.success": "confirmation_002.ogg",
  "reveal.open": "open_001.ogg",
  /* micro-effects */
  "fx.burst": "maximize_001.ogg",
  "fx.ring": "bong_001.ogg",
  "fx.confetti": "confirmation_002.ogg",
  /* ui */
  "ui.select": "select_001.ogg",
  "ui.close": "close_001.ogg",
};

export function resolveSfxPath(ref: string): string | null {
  if (!ref.startsWith("sfx:")) return null;
  const name = ref.slice(4);
  const file = SFX_LIBRARY[name];
  return file ? path.join(SFX_ROOT, file) : null;
}
