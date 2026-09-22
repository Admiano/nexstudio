/**
 * Sketch-film spec: a plain JSON document that a storyboard agent (or a
 * template fixture) emits to describe one paper-sketch film. The assembler
 * turns it into a HyperFrames CompositionBundle built entirely from the
 * vendored sketch-ui + paper-motion runtime assets.
 */

export type SketchSceneSpec = {
  /** Stable beat id — also used for manifest beatTimings. */
  id: string;
  /** One of the scene builders in runtime-assets/sketch-ui/js/sketch-ui.js */
  type:
    | "type-card"
    | "chat-prompt"
    | "agent-window"
    | "step"
    | "phone-app"
    | "storyboard"
    | "compose-graph"
    | "render-bar"
    | "player"
    | "logo-mark"
    | "end-card";
  /** Absolute film seconds where the beat starts. */
  start: number;
  /** Beat length in film seconds. */
  duration: number;
  /** 'cut' (default), 'fade', or 'wipe' entrance. */
  transition?: "cut" | "fade" | "wipe";
  /** Top-left kicker text, e.g. "/ STEP 01". */
  kicker?: string;
  /** Top-right kicker text. */
  kickerR?: string;
  /** Bottom-left footnote (mono, uppercase). */
  foot?: string;
  /** Set false to hide the bottom-right "03/12" page index. */
  index?: boolean;
  /** Scene-specific params passed through to the component builder. */
  [key: string]: unknown;
};

export type SketchFilmSpec = {
  productionId: string;
  width: number;
  height: number;
  fps: number;
  durationSeconds: number;
  /** Looped music bed; resolved relative to the spec file. */
  music?: { path: string; volume?: number };
  /** SFX accents — one entry per sound file, cued at atSec times. */
  sfx?: { path: string; atSec: number[]; volume?: number }[];
  /** Named media assets usable from scene params (e.g. posters, card art). */
  assets?: Record<string, string>;
  /** Override paper texture path (defaults to the vendored paper006). */
  paperTexture?: string;
  scenes: SketchSceneSpec[];
};

export const SKETCH_UI_VERSION = "1.0.0";
