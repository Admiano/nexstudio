import { existsSync } from "node:fs";

function existingCandidate(candidates: Array<string | undefined>) {
  return candidates
    .filter((candidate): candidate is string => Boolean(candidate))
    .find((candidate) => existsSync(candidate));
}

/**
 * Resolve the browser executable used by deterministic capture/QA.
 * Environment configuration wins, followed by the common Linux paths, then
 * the common Windows paths. Callers should fail explicitly when undefined.
 */
export function findChromiumExecutable() {
  return existingCandidate([
    process.env.CHROMIUM_EXECUTABLE_PATH,
    process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
    ...(process.platform === "win32"
      ? [
          "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
          "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
          "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        ]
      : []),
    ...(process.platform === "darwin"
      ? [
          "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
          "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        ]
      : []),
  ]);
}

/** Resolve ffmpeg from an explicit environment override or the host PATH. */
export function resolveFfmpegExecutable() {
  return process.env.FFMPEG_PATH ?? (process.platform === "win32" ? "ffmpeg.exe" : "ffmpeg");
}
