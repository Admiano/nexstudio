"use client";

import { useEffect, useRef } from "react";
import { specLayers, type CastSpec } from "./spec";

// Draw order is baked into specLayers; every plate is a finished render of
// the authored look, so the stage only stacks them.

const IMG_CACHE = new Map<string, Promise<HTMLImageElement | null>>();

function loadImg(src: string): Promise<HTMLImageElement | null> {
  let p = IMG_CACHE.get(src);
  if (!p) {
    p = new Promise((resolve) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => resolve(null);
      img.src = src;
    });
    IMG_CACHE.set(src, p);
  }
  return p;
}

const W = 720, H = 1080;

export default function AvatarStage({ spec, className }: { spec: CastSpec; className?: string }) {
  const ref = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    let cancelled = false;
    const layers = specLayers(spec);
    Promise.all(layers.map((l) => loadImg(l.src))).then((imgs) => {
      if (cancelled || !ref.current) return;
      const ctx = ref.current.getContext("2d");
      if (!ctx) return;
      ctx.clearRect(0, 0, W, H);
      for (let i = 0; i < layers.length; i++) {
        const img = imgs[i];
        if (!img) continue;
        ctx.drawImage(img, 0, 0, W, H);
      }
    });
    return () => { cancelled = true; };
  }, [spec]);

  return <canvas ref={ref} className={className} width={W} height={H} aria-hidden="true" />;
}
