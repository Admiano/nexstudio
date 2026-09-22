/**
 * CLI: prompt → spec directory (spec.json + audio assets).
 *
 *   tsx src/hyperframes/sketch-films/direct-cli.ts \
 *     "make a film about how our agent turns a brief into a launch video" \
 *     src/hyperframes/sketch-films/specs/generated \
 *     [--duration 38] [--product "NEX STUDIO"] [--seed 97]
 *
 * Then render with render.ts as usual.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { directToSpec } from "./direct.js";

const here = path.dirname(fileURLToPath(import.meta.url));

const args = process.argv.slice(2);
const promptArg = args[0];
const outDir = args[1] && !args[1].startsWith("--") ? path.resolve(args[1]) : undefined;
const opt = (name: string) => { const i = args.indexOf(`--${name}`); return i >= 0 ? args[i + 1] : undefined; };

if (!promptArg || !outDir || args[0]?.startsWith("--")) {
  console.error('usage: direct-cli.ts "<prompt>" <outDir> [--duration 38] [--product "NEX STUDIO"] [--cta "..."] [--tagline "..."] [--seed 97]');
  process.exit(2);
}

const spec = directToSpec({
  prompt: promptArg,
  duration: opt("duration") ? Number(opt("duration")) : undefined,
  product: opt("product"),
  tagline: opt("tagline"),
  cta: opt("cta"),
  seed: opt("seed") ? Number(opt("seed")) : undefined,
});

fs.mkdirSync(path.join(outDir, "audio"), { recursive: true });
/* shared vendored clips — copy so the spec dir is self-contained */
const libAudio = path.resolve(here, "specs/launch-promo/audio");
for (const f of ["music.mp3", "swipe.mp3", "pop.mp3", "paper.mp3", "confirm.mp3"]) {
  fs.copyFileSync(path.join(libAudio, f), path.join(outDir, "audio", f));
}
fs.writeFileSync(path.join(outDir, "spec.json"), JSON.stringify(spec, null, 2) + "\n");
console.log(`wrote ${path.join(outDir, "spec.json")} — ${spec.scenes.length} beats, ${spec.durationSeconds}s`);
spec.scenes.forEach(s => console.log(`  ${s.start.toFixed(1).padStart(5)}s +${s.duration.toFixed(1)}s  ${s.type}`));
