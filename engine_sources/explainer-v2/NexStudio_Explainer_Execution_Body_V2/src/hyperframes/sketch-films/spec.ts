/**
 * Sketch-film spec: a plain JSON document that a storyboard agent (or a
 * template fixture) emits to describe one film. The assembler turns it into
 * a HyperFrames CompositionBundle built from a vendored surface runtime —
 * `surface: 'sketch'` renders the ink-on-paper skin (sketch-ui + paper-motion),
 * `surface: 'product'` renders the clean brand-surface skin (product-ui).
 * Same beats/timing/audio contract; the surface is swappable.
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
    | "end-card"
    | "hero-build"
    | "phrase-swap"
    | "process-rail"
    | "payoff-lockup"
    | "word-object-bridge"
    /* content-typed primitives — domain-agnostic, driven by content params */
    | "chapter"
    | "word-list"
    | "feature-grid"
    | "stat"
    | "quote"
    | "media-frame"
    | "split"
    | "marquee-word"
    | "orbit"
    | "kinetic-headline";
  /** Absolute film seconds where the beat starts. */
  start: number;
  /** Beat length in film seconds. */
  duration: number;
  /**
   * Entrance transition. 'cut'/'fade'/'rise'/'wipe' are inline; on the sketch
   * surface the paper set maps to paper-motion transitions ('torn' →
   * torn-paper-reveal, 'push' → collage-push, 'page' → page-turn, 'shuffle' →
   * card-stack-shuffle, 'tape' → tape-peel, 'crumple' → crumple-transition,
   * 'paper' → paper-wipe); on the product surface the paper set remaps via
   * T_MAP and 'mask'/'zoom'/'slide' run as native product transitions.
   */
  transition?: "cut" | "fade" | "rise" | "wipe" | "torn" | "push" | "page" | "shuffle" | "tape" | "crumple" | "paper" | "mask" | "zoom" | "slide";
  /** Camera move over the beat — push scales in, pan translates (fractions of stage size). */
  camera?: { push?: number; pan?: [number, number] };
  /** Top-left kicker text, e.g. "/ STEP 01". */
  kicker?: string;
  /** Top-right kicker text. */
  kickerR?: string;
  /** Bottom-left footnote (mono, uppercase). */
  foot?: string;
  /** Small italic annotation inside the safe lane, bottom-left — detail layer. */
  note?: string;
  /** Set false to hide the bottom-right "03/12" page index. */
  index?: boolean;
  /** Scene-specific params passed through to the component builder. */
  [key: string]: unknown;
};

export type SketchFilmSpec = {
  productionId: string;
  /** Which surface runtime renders this spec. Default 'sketch'.
      'product' = clean brand surface (product-ui runtime). */
  surface?: "sketch" | "product";
  /** Frame (film seconds) baked as the mp4's frame 0 — the share thumbnail.
      Director defaults it to a settled end-card moment. */
  posterSec?: number;
  /** Share caption written next to the mp4 (<out>-share.txt). */
  shareCopy?: string;
  width: number;
  height: number;
  fps: number;
  durationSeconds: number;
  /** Looped music bed; resolved relative to the spec file. */
  music?: { path: string; volume?: number };
  /** SFX accents — one entry per sound file, cued at atSec times. */
  sfx?: { path: string; atSec: number[]; volume?: number }[];
  /**
   * Named media assets usable from scene params ({name: spec-relative path}).
   * Scene params (media, poster, thumbs, card img) accept the bare name —
   * they resolve to media/<name><ext> in the bundle. Each <img> renders through
   * the #sk-inkify SVG filter (edges → dark-line-on-white, multiply-blended onto
   * the paper) unless the scene sets `inkify: false` for a plain grayscale photo.
   */
  assets?: Record<string, string>;
  /** Override paper texture path (defaults to the generated warm fibred sheet). */
  paperTexture?: string;
  /** Named paper stock: warm (default) | ivory | kraft | newsprint —
      supplies texture + tints; explicit theme tokens still win. */
  paperStock?: string;
  /** Presentation weight: 'editorial' (default) | 'poster' (type-forward,
      centered lane) | 'deck' (tighter lane). A scene-level `layout`
      overrides the film default per beat. */
  layout?: "editorial" | "poster" | "deck";
  /** Override speckle/grain tile path (defaults to grain-fine-256). */
  grainTexture?: string;
  /**
   * Per-film theme tokens — brand accents and paper/ink colors, applied as
   * CSS custom properties at boot (so both DOM elements and rough.js stroke
   * colors resolve them). All optional; hex/rgb/hsl strings.
   * `accent`/`accentDeep` drive the mint→brand accent; `texture` overrides paperTexture.
   */
  theme?: {
    paper?: string; paper2?: string; surface?: string;
    ink?: string; ink2?: string;
    accent?: string; accentDeep?: string;
    texture?: string;
    /** Named paper stock — same values as top-level paperStock. */
    stock?: string;
    /* product-surface tokens (ignored by the sketch skin) */
    bg?: string; fg?: string; muted?: string;
    card?: string; card2?: string; line?: string; accent2?: string;
    display?: string; sans?: string; mono?: string;
  };
  scenes: SketchSceneSpec[];
};

export const SKETCH_UI_VERSION = "1.0.0";
