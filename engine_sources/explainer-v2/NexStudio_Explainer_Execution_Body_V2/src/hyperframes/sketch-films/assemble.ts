import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import type { CompositionBundle } from "../types.js";
import type { SketchFilmSpec } from "./spec.js";
import { SKETCH_UI_VERSION } from "./spec.js";
import { resolveSfxPath } from "./sfx-library.js";

const execFileAsync = promisify(execFile);
const sha256 = (bytes: Uint8Array | string) => createHash("sha256").update(bytes).digest("hex");

const toBytes = (v: string | Uint8Array): Uint8Array =>
  typeof v === "string" ? new TextEncoder().encode(v) : v;

async function probeDurationSec(file: string): Promise<number> {
  try {
    const { stdout } = await execFileAsync("ffprobe", [
      "-v", "error",
      "-show_entries", "format=duration",
      "-of", "default=noprint_wrappers=1:nokey=1",
      file,
    ]);
    const d = Number(stdout.trim());
    return Number.isFinite(d) && d > 0 ? d : 1;
  } catch {
    return 1;
  }
}

/* Surface runtimes — the skin a spec renders in. Every surface shares the
   NexMotion engine + film master contract (scene windows, furniture, camera,
   transition drivers); what differs is the visual grammar + scene registry. */
type SurfaceId = "sketch" | "product";

const MOTION_FILES: Record<string, string> = {
  "paper-motion/vendor/gsap-compat.js": "runtime-assets/paper-motion/vendor/gsap-compat.js",
  "paper-motion/runtime/motion-registry.js": "runtime-assets/paper-motion/runtime/motion-registry.js",
  "paper-motion/runtime/motion-engine.js": "runtime-assets/paper-motion/runtime/motion-engine.js",
};

const SURFACE_FILES: Record<SurfaceId, Record<string, string>> = {
  sketch: {
    "sketch-ui/styles/sketch-ui.css": "runtime-assets/sketch-ui/styles/sketch-ui.css",
    "sketch-ui/js/sketch-ui.js": "runtime-assets/sketch-ui/js/sketch-ui.js",
    "sketch-ui/vendor/rough.js": "runtime-assets/sketch-ui/vendor/rough.js",
    "sketch-ui/textures/paper006-color-1k.jpg": "runtime-assets/sketch-ui/textures/paper006-color-1k.jpg",
    "sketch-ui/textures/paper-warm-1k.png": "runtime-assets/sketch-ui/textures/paper-warm-1k.png",
    "sketch-ui/textures/grain-fine-256.png": "runtime-assets/sketch-ui/textures/grain-fine-256.png",
    "sketch-ui/fonts/DMSerifDisplay-Regular.ttf": "runtime-assets/sketch-ui/fonts/DMSerifDisplay-Regular.ttf",
    "sketch-ui/fonts/DMSerifDisplay-Italic.ttf": "runtime-assets/sketch-ui/fonts/DMSerifDisplay-Italic.ttf",
    "sketch-ui/fonts/InterVariable.woff2": "runtime-assets/sketch-ui/fonts/InterVariable.woff2",
    "sketch-ui/fonts/JetBrainsMono-SemiBold.ttf": "runtime-assets/sketch-ui/fonts/JetBrainsMono-SemiBold.ttf",
    ...MOTION_FILES,
  },
  product: {
    "product-ui/styles/product-ui.css": "runtime-assets/product-ui/styles/product-ui.css",
    "product-ui/js/product-ui.js": "runtime-assets/product-ui/js/product-ui.js",
    /* product skin shares the vendored OFL font files at its own bundle prefix */
    "product-ui/fonts/SpaceGrotesk-Variable.woff2": "runtime-assets/sketch-ui/fonts/SpaceGrotesk-Variable.woff2",
    "product-ui/fonts/InterVariable.woff2": "runtime-assets/sketch-ui/fonts/InterVariable.woff2",
    "product-ui/fonts/JetBrainsMono-SemiBold.ttf": "runtime-assets/sketch-ui/fonts/JetBrainsMono-SemiBold.ttf",
    "product-ui/textures/grain-fine-256.png": "runtime-assets/sketch-ui/textures/grain-fine-256.png",
    ...MOTION_FILES,
  },
};

const SURFACE_RUNTIME = (surface: SurfaceId) =>
  surface === "product"
    ? { css: "product-ui/styles/product-ui.css", js: "product-ui/js/product-ui.js", global: "NexFilm", cls: "pf" }
    : { css: "sketch-ui/styles/sketch-ui.css", js: "sketch-ui/js/sketch-ui.js", global: "NexSketch", cls: "sk" };

export function filmPageHtml(spec: SketchFilmSpec): string {
  const surface: SurfaceId = spec.surface === "product" ? "product" : "sketch";
  const rt = SURFACE_RUNTIME(surface);
  const boot = `window.__FILM_SPEC__=${JSON.stringify(spec)};
    (function boot(){
      var ready=function(){
        try{
          var t=window.${rt.global}.start(window.__FILM_SPEC__);
          t.pause();
          Promise.all([
            document.fonts ? document.fonts.ready : Promise.resolve(),
            new Promise(function(r){requestAnimationFrame(function(){requestAnimationFrame(r)})})
          ]).then(function(){ window.__renderReady=true; });
        }catch(e){ document.title='SKETCH-FILM-ERR'; var el=document.createElement('pre'); el.id='boot-error'; el.textContent=String(e&&e.stack||e); document.body.appendChild(el); throw e; }
      };
      if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ready);else ready();
    })();`;
  const rough = surface === "sketch" ? `<script src="sketch-ui/vendor/rough.js"></script>` : "";
  return `<!doctype html><html class="${rt.cls}"><head><meta charset="utf-8"><title>${spec.productionId}</title>
<link rel="stylesheet" href="${rt.css}">
<style>html,body{width:${spec.width}px;height:${spec.height}px;overflow:hidden}[data-nex-production-canvas]{position:relative;width:${spec.width}px;height:${spec.height}px;overflow:hidden}</style>
</head><body class="${rt.cls}"><main data-nex-production-canvas data-composition-src="index.html" data-width="${spec.width}" data-height="${spec.height}"></main>
${rough}
<script src="paper-motion/vendor/gsap-compat.js"></script>
<script src="paper-motion/runtime/motion-registry.js"></script>
<script src="paper-motion/runtime/motion-engine.js"></script>
<script src="${rt.js}"></script>
<script>${boot}</script></body></html>`;
}

export type AssembleOptions = {
  /** Absolute path of the extracted engine root (…/NexStudio_Explainer_Execution_Body_V2). */
  engineRoot: string;
  /** Directory the spec file lives in — spec-relative media paths resolve against it. */
  specDir: string;
};

export async function assembleSketchFilmBundle(
  spec: SketchFilmSpec,
  opts: AssembleOptions,
): Promise<CompositionBundle> {
  if (!spec.productionId) throw new Error("spec.productionId required");
  if (!spec.scenes?.length) throw new Error("spec.scenes must be non-empty");
  const files: Record<string, string | Uint8Array> = {};
  const surface: SurfaceId = spec.surface === "product" ? "product" : "sketch";

  for (const [bundlePath, rel] of Object.entries(SURFACE_FILES[surface])) {
    files[bundlePath] = await readFile(path.join(opts.engineRoot, rel));
  }

  // Spec-referenced media assets (posters, card art, screenshots).
  const svgAssets: Record<string, string> = {};
  for (const [name, rel] of Object.entries(spec.assets ?? {})) {
    const disk = path.isAbsolute(rel) ? rel : path.join(opts.specDir, rel);
    const bytes = await readFile(disk);
    files[`media/${name}${path.extname(rel)}`] = bytes;
    if (path.extname(rel).toLowerCase() === ".svg") svgAssets[name] = bytes.toString("utf8");
  }
  if (Object.keys(svgAssets).length) spec.svgAssets = svgAssets;

  const audioTracks: CompositionBundle["manifest"]["audioTracks"] = [];
  if (spec.music) {
    const disk = path.isAbsolute(spec.music.path) ? spec.music.path : path.join(opts.specDir, spec.music.path);
    const bytes = await readFile(disk);
    const ext = path.extname(disk) || ".mp3";
    files[`audio/music${ext}`] = bytes;
    audioTracks.push({
      id: "music",
      path: `audio/music${ext}`,
      sha256: sha256(bytes),
      durationSec: spec.durationSeconds,
      volume: spec.music.volume ?? 0.2,
    });
  }
  for (const [i, sfx] of (spec.sfx ?? []).entries()) {
    const resolved = resolveSfxPath(sfx.path);
    const disk = resolved ?? (path.isAbsolute(sfx.path) ? sfx.path : path.join(opts.specDir, sfx.path));
    const bytes = await readFile(disk);
    const ext = path.extname(disk) || ".mp3";
    const p = `audio/sfx-${i}${ext}`;
    files[p] = bytes;
    audioTracks.push({
      id: "sound-effect",
      path: p,
      sha256: sha256(bytes),
      durationSec: Math.min(spec.durationSeconds, await probeDurationSec(disk)),
      volume: sfx.volume ?? 0.4,
      cueTimesSec: sfx.atSec,
    });
  }

  files["index.html"] = filmPageHtml(spec);

  const assets = Object.entries(files)
    .filter(([p]) => p !== "index.html")
    .map(([p, v]) => ({ path: p, sha256: sha256(toBytes(v)) }));

  const bundle: CompositionBundle = {
    entry: "index.html",
    hyperframesVersion: `sketch-films/${SKETCH_UI_VERSION}`,
    width: spec.width,
    height: spec.height,
    durationSeconds: spec.durationSeconds,
    files,
    manifest: {
      productionId: spec.productionId,
      templateVersion: `sketch-ui@${SKETCH_UI_VERSION}`,
      compositionHash: sha256(filmPageHtml(spec)),
      sourceHash: sha256(JSON.stringify(spec)),
      createdAt: new Date().toISOString(),
      assets,
      beatCount: spec.scenes.length,
      beatTimings: spec.scenes.map((s) => ({ beatId: s.id, startSec: s.start, endSec: s.start + s.duration })),
      audioTracks,
      sceneLibrary: spec.scenes.map((s) => ({
        family: spec.surface === "product" ? "product-ui" : "sketch-ui",
        sceneId: s.type,
        version: SKETCH_UI_VERSION,
        beatId: s.id,
      })),
    },
  };
  return bundle;
}
