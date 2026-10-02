"use client";

declare global {
  interface Window {
    initNexMindPresence?: (root?: Document | HTMLElement) => void;
    setNexMindPresenceState?: (root: string | HTMLElement, state: string) => void;
  }
}

let pending: Promise<void> | null = null;

function loadRuntime(): Promise<void> {
  if (pending) return pending;
  pending = new Promise((resolve) => {
    const done = () => resolve();
    const existing = document.querySelector<HTMLScriptElement>('script[src="/nexstudio/nx-presence.js"]');
    if (existing) {
      existing.addEventListener("load", done, { once: true });
      if (window.initNexMindPresence) done();
      return;
    }
    const s = document.createElement("script");
    s.src = "/nexstudio/nx-presence.js";
    s.async = true;
    s.onload = done;
    s.onerror = done;
    document.head.appendChild(s);
  });
  return pending;
}

export function ensureNxPresence(root?: HTMLElement) {
  if (typeof window === "undefined") return;
  void loadRuntime().then(() => window.initNexMindPresence?.(root ?? document));
}
