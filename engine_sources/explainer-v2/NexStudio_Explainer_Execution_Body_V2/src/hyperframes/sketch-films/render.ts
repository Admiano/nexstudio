/**
 * Render a sketch-film spec to MP4 via the self-hosted Chromium renderer.
 *
 *   tsx src/hyperframes/sketch-films/render.ts <spec.json> <out.mp4> [--inspect <dir>]
 *
 * Run from the engine root so `@/` path aliases resolve (see engine tsconfig).
 */
import path from "node:path";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { assembleSketchFilmBundle } from "./assemble.js";
import type { SketchFilmSpec } from "./spec.js";
import { renderSelfHostedChromium } from "../self-hosted-renderer.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const engineRoot = path.resolve(here, "../../..");

async function main() {
  const [, , specArg, outArg, ...rest] = process.argv;
  if (!specArg || !outArg) {
    console.error("usage: render.ts <spec.json> <out.mp4> [--inspect <dir>]");
    process.exit(2);
  }
  const specPath = path.resolve(specArg);
  const outPath = path.resolve(outArg);
  const inspectIdx = rest.indexOf("--inspect");
  const inspectDir = inspectIdx >= 0 ? path.resolve(rest[inspectIdx + 1]) : undefined;

  const spec = JSON.parse(await readFile(specPath, "utf8")) as SketchFilmSpec;
  const bundle = await assembleSketchFilmBundle(spec, {
    engineRoot,
    specDir: path.dirname(specPath),
  });
  const bundlePath = outPath.replace(/\.mp4$/i, "") + ".bundle.json";
  await mkdir(path.dirname(outPath), { recursive: true });
  await writeFile(
    bundlePath,
    JSON.stringify(
      {
        ...bundle,
        files: Object.fromEntries(
          Object.entries(bundle.files).map(([k, v]) => [k, typeof v === "string" ? v : `<${v.byteLength} bytes>`]),
        ),
      },
      null,
      2,
    ),
  );

  const result = await renderSelfHostedChromium(bundle, {
    fps: spec.fps,
    outputPath: outPath,
    inspectionFrameDirectory: inspectDir,
  });
  console.log(JSON.stringify({ bundlePath, result }, null, 2));
  if (result.status !== "completed") process.exit(1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
