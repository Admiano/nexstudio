/**
 * CLI: prompt OR structured script → spec directory (spec.json + audio).
 *
 *   tsx src/hyperframes/sketch-films/direct-cli.ts \
 *     "make a film about how our agent turns a brief into a launch video" \
 *     src/hyperframes/sketch-films/specs/generated
 *
 *   tsx src/hyperframes/sketch-films/direct-cli.ts \
 *     --script beats.json \
 *     src/hyperframes/sketch-films/specs/generated
 *
 * Options: [--duration 38] [--product "NEX STUDIO"] [--cta "..."] [--tagline "..."] [--seed 97]
 * Then render with render.ts as usual.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { directToSpec, type FilmBeat } from "./direct.js";

const here = path.dirname(fileURLToPath(import.meta.url));

const args = process.argv.slice(2);
const opt = (name: string) => { const i = args.indexOf(`--${name}`); return i >= 0 ? args[i + 1] : undefined; };
const positional = args.filter((a, i) => !a.startsWith("--") && (i === 0 || args[i - 1] !== "--script") && !["--duration", "--product", "--cta", "--tagline", "--seed"].includes(args[i - 1] || ""));
const scriptPath = opt("script");
const outDir = path.resolve(positional[positional.length - 1] || "");

if (!outDir || (!scriptPath && !positional[0])) {
  console.error('usage: direct-cli.ts "<prompt>"|--script beats.json <outDir> [--duration 38] [--product "NEX STUDIO"] [--cta "..."] [--tagline "..."] [--seed 97]');
  process.exit(2);
}

let script: FilmBeat[] | undefined;
if (scriptPath) {
  script = JSON.parse(fs.readFileSync(path.resolve(scriptPath), "utf8"));
  if (!Array.isArray(script)) { console.error("--script must be a JSON array of beats"); process.exit(2); }
}

const spec = directToSpec({
  prompt: scriptPath ? undefined : positional[0],
  script,
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
spec.scenes.forEach(s => console.log(`  ${s.start.toFixed(1).padStart(5)}s +${s.duration.toFixed(1)}s  ${s.type}  ${String((s as Record<string, unknown>).text ?? (s as Record<string, unknown>).title ?? "")}`));
