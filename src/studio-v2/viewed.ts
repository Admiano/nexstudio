"use client";

// Finished-but-unviewed render tracking, per browser. localStorage is honest
// here: production records already persist server-side; this only answers
// "has this user opened this finished render on this device yet".

const KEY = "nx.viewed";
const CAP = 300;

export function loadViewed(): Set<string> {
  try {
    const raw = localStorage.getItem(KEY);
    return new Set(raw ? (JSON.parse(raw) as string[]) : []);
  } catch {
    return new Set();
  }
}

export function markViewed(id: string): void {
  try {
    const set = loadViewed();
    set.add(id);
    localStorage.setItem(KEY, JSON.stringify([...set].slice(-CAP)));
  } catch { /* storage unavailable — badge simply stays */ }
}
