"use client";

import { useEffect, useRef } from "react";
import { specLayers, type CastLayer, type CastSpec } from "./spec";

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

async function loadLayer(layer: CastLayer): Promise<HTMLImageElement | null> {
  const primary = await loadImg(layer.src);
  if (primary || !layer.fallbackSrc) return primary;
  return loadImg(layer.fallbackSrc);
}

const W = 720, H = 1080;

export default function AvatarStage({ spec, className }: { spec: CastSpec; className?: string }) {
  const ref = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    let cancelled = false;
    const layers = specLayers(spec);
    Promise.all(layers.map(loadLayer)).then((imgs) => {
      if (cancelled || !ref.current) return;
      const ctx = ref.current.getContext("2d");
      if (!ctx) return;
      ctx.clearRect(0, 0, W, H);
      for (const img of imgs) {
        if (img) ctx.drawImage(img, 0, 0, W, H);
      }
    });
    return () => { cancelled = true; };
  }, [spec]);

  return <canvas ref={ref} className={className} width={W} height={H} aria-hidden="true" />;
}
