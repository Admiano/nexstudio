import { normalizeCastSpec, specLayers, type CastSpec } from "../src/studio-v2/cast/spec";

function ok(value: unknown, message: string): asserts value {
  if (!value) throw new Error(message);
}
function eq(actual: unknown, expected: unknown, message: string) {
  if (actual !== expected) throw new Error(`${message}: expected ${String(expected)}, got ${String(actual)}`);
}

const legacyFemale = {
  character: "female",
  face: 0,
  skin: "light",
  hair: { style: "long", color: "auburn" },
  lip: "rose",
  neck: "fine",
  outfit: { kind: "maxi" },
  watch: null,
  voiceId: "emma",
} as CastSpec;
const nf = normalizeCastSpec(legacyFemale, "female");
eq(nf.outfit?.color, "burgundy", "legacy female outfit should inherit authored default colour");

const femaleSaved = normalizeCastSpec({ ...nf, outfit: { kind: "maxi", color: "emerald" } }, "female");
eq(femaleSaved.outfit?.kind, "maxi", "female style persists");
eq(femaleSaved.outfit?.color, "emerald", "female colour persists");
ok(specLayers(femaleSaved).some((x) => x.src.includes("fem_outfit_maxi_emerald.png")), "female colour plate resolves");

const femaleNoneNeck = normalizeCastSpec({ ...femaleSaved, neck: null }, "female");
eq(femaleNoneNeck.neck, null, "explicit no-neckwear persists");

const legacyMale = {
  character: "male",
  face: 0,
  skin: "tan",
  hair: { style: "quiff", color: "brown" },
  lip: null,
  neck: null,
  outfit: { kind: "o4" },
  watch: "smart",
  voiceId: "andrew",
} as CastSpec;
const nm = normalizeCastSpec(legacyMale, "male");
eq(nm.outfit?.color, "burgundy", "legacy male outfit should inherit authored top colour");

const maleSaved = normalizeCastSpec({ ...nm, outfit: { kind: "o4", color: "cream" } }, "male");
eq(maleSaved.outfit?.kind, "o4", "male style persists");
eq(maleSaved.outfit?.color, "cream", "male top colour persists");
ok(specLayers(maleSaved).some((x) => x.src.includes("male_outfit_o4_cream.png")), "male top colour plate resolves");

const maleNoWatch = normalizeCastSpec({ ...maleSaved, watch: null }, "male");
eq(maleNoWatch.watch, null, "explicit no-watch persists");

const coral = normalizeCastSpec({ ...nf, lip: "coral" }, "female");
ok(specLayers(coral).some((x) => x.src.includes("fem_lip_f0_coral.png")), "coral plate resolves");

console.log("PASS cast spec persistence: style/color + explicit none + Coral layer resolution");
