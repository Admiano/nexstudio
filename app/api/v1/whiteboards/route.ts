import path from "node:path";
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync, existsSync, readFileSync, copyFileSync } from "node:fs";
import { randomUUID } from "node:crypto";
import { homedir } from "node:os";
import { requireSession } from "@/lib/route-auth";
import { json, problem } from "@/lib/http";

export const runtime = "nodejs";

const ENGINE = process.env.WHITEBOARD_V3_RUNTIME_DIR
  ?? path.join(process.cwd(), "engine_sources", "whiteboard-v3-runtime");
const JOBS = path.join(ENGINE, "out", "whiteboard-jobs");

const TYPES = {
  "kinetic-text": { id: "kinetic-text", name: "Text-Driven Whiteboard", pipeline: "kinetic" },
  "hand-drawn-board": { id: "hand-drawn-board", name: "Hand-Drawn Whiteboard", pipeline: "board" },
} as const;
const VOICES = ["emma", "ava", "andrew", "brian", "sonia", "natasha"];
const THEMES = new Set(["light", "dark"]);
const ASPECTS = new Set(["16x9", "1x1", "9x16"]);

export async function GET(request: Request) {
  const auth = await requireSession(request); if (auth.response) return auth.response;
  return json({
    types: Object.values(TYPES).map(({ id, name }) => ({ id, name })),
    themes: [...THEMES], voices: VOICES, aspects: [...ASPECTS],
  }, auth.id);
}

export async function POST(request: Request) {
  const auth = await requireSession(request); if (auth.response) return auth.response;
  const id = auth.id;
  let form: FormData;
  try { form = await request.formData(); }
  catch { return problem(id, 400, "BAD_FORM", "Invalid form", "Send multipart/form-data."); }

  const type = String(form.get("type") ?? "kinetic-text");
  const spec = TYPES[type as keyof typeof TYPES];
  if (!spec)
    return problem(id, 422, "TYPE_UNKNOWN", "Unknown whiteboard type",
      `Pick one of: ${Object.keys(TYPES).join(", ")}.`);

  const script = String(form.get("script") ?? "").trim();
  const voiceFile = form.get("voiceFile");
  if (!script && !(voiceFile instanceof File))
    return problem(id, 422, "VOICE_REQUIRED", "Voice required", "Send 'script' (for a Microsoft voice) or a 'voiceFile' upload.");

  const voice = String(form.get("voice") ?? "emma");
  if (script && !VOICES.includes(voice))
    return problem(id, 422, "VOICE_UNKNOWN", "Unknown voice", `Pick one of: ${VOICES.join(", ")}.`);

  const theme = String(form.get("theme") ?? "light");
  if (!THEMES.has(theme))
    return problem(id, 422, "THEME_UNKNOWN", "Unknown theme", `Pick one of: ${[...THEMES].join(", ")}.`);

  const accent = String(form.get("accent") ?? "").trim();
  if (accent && !/^#[0-9a-fA-F]{3,8}$/.test(accent))
    return problem(id, 422, "ACCENT_INVALID", "Invalid accent color", "Send a hex color like #2f6fb3.");

  const aspects = String(form.get("aspects") ?? "16x9,1x1,9x16")
    .split(",").map((a) => a.trim()).filter((a) => ASPECTS.has(a));
  if (!aspects.length)
    return problem(id, 422, "ASPECT_UNKNOWN", "No valid aspect", `Pick from: ${[...ASPECTS].join(", ")}.`);

  const durationRaw = Number(form.get("duration") ?? 0);
  if (durationRaw && (!Number.isFinite(durationRaw) || durationRaw < 5 || durationRaw > 600))
    return problem(id, 422, "DURATION_RANGE", "Invalid length", "Target length must be 5–600 seconds.");

  const jobId = `wb-${randomUUID().slice(0, 8)}`;
  const dir = path.join(JOBS, jobId);
  mkdirSync(dir, { recursive: true });

  const args: string[] = [path.join(ENGINE, "tools", "nexstudio_job.py"),
    "--type", spec.pipeline, "--theme", theme,
    "--voice", voice, "--title", jobId.toUpperCase(),
    "--aspects", aspects.map((a) => a.replace("x", ":")).join(","),
    "--out", path.join(dir, "out"), "--job-id", jobId];
  if (durationRaw) args.push("--duration", String(durationRaw));

  const scriptPath = path.join(dir, "script.txt");
  if (script) {
    writeFileSync(scriptPath, script.endsWith("\n") ? script : `${script}\n`);
    args.push("--script", scriptPath);
  }
  if (voiceFile instanceof File) {
    const vf = path.join(dir, `voice_src${path.extname(voiceFile.name || ".mp3")}`);
    writeFileSync(vf, Buffer.from(await voiceFile.arrayBuffer()));
    args.push("--voice-file", vf);
  }
  if (accent) args.push("--accent", accent);

  writeFileSync(path.join(dir, "request.json"), JSON.stringify({
    userId: auth.session!.userId, type, voice, theme, accent: accent || null, aspects,
    script: script || null, createdAt: new Date().toISOString(),
  }, null, 1));
  writeFileSync(path.join(dir, "status.json"), JSON.stringify({ status: "running", startedAt: new Date().toISOString() }));

  const nodeBin = path.join(homedir(), ".nvm", "versions", "node", "v24.19.0", "bin");
  const child = spawn("python3", args, {
    cwd: ENGINE, detached: true, stdio: ["ignore", "pipe", "pipe"],
    env: {
      ...process.env,
      PATH: `${nodeBin}:${process.env.PATH}`,
      WHITEBOARD_V3_SYSTEM_PACKAGE: path.join(
        process.cwd(), "engines", "whiteboard-v3-system", "NEXMIND_WHITEBOARD_V3_SYSTEM_PACKAGE"),
    },
  });
  child.stdout?.on("data", () => {});
  child.stderr?.on("data", () => {});
  child.on("exit", (code) => {
    try {
      const manifestPath = path.join(dir, "out", "manifest.json");
      const manifest = existsSync(manifestPath) ? JSON.parse(readFileSync(manifestPath, "utf8")) : null;
      const filesDir = path.join(dir, "files");
      mkdirSync(filesDir, { recursive: true });
      const outputs: Record<string, string> = {};
      if (manifest?.outputs) {
        for (const [aspect, p] of Object.entries<string>(manifest.outputs)) {
          const key = aspect.replace(":", "x");
          const dest = path.join(filesDir, `${key}.mp4`);
          try { copyFileSync(p, dest); } catch { continue; }
          outputs[key] = `/api/v1/whiteboards/${jobId}/files/${key}.mp4`;
        }
      }
      writeFileSync(path.join(dir, "status.json"), JSON.stringify({
        status: code === 0 ? "done" : "failed",
        exitCode: code, outputs, finishedAt: new Date().toISOString(),
      }));
    } catch (e) {
      writeFileSync(path.join(dir, "status.json"), JSON.stringify({
        status: "failed", exitCode: code, error: String(e), finishedAt: new Date().toISOString(),
      }));
    }
  });
  child.unref();

  return json({ jobId, status: "running", statusUrl: `/api/v1/whiteboards/${jobId}` }, id, { status: 202 });
}
