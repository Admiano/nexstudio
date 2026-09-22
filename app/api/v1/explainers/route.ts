import path from "node:path";
import { spawn } from "node:child_process";
import { mkdirSync, writeFileSync, existsSync, readFileSync, copyFileSync } from "node:fs";
import { randomUUID } from "node:crypto";
import { homedir } from "node:os";
import { requireSession } from "@/lib/route-auth";
import { json, problem } from "@/lib/http";

export const runtime = "nodejs";

const ENGINE = process.env.EXPLAINER_ENGINE_DIR
  ?? path.join(process.cwd(), "engine_sources", "editorial-motion-v2");
const JOBS = path.join(ENGINE, "out", "explainer-jobs");
const VOICES = ["af_bella","af_sarah","am_onyx","am_adam","bf_emma","bf_isabella","bm_george","bm_lewis"];
const ASPECTS = new Set(["16x9", "1x1", "9x16"]);

function stylesList() {
  try {
    const doc = JSON.parse(readFileSync(path.join(ENGINE, "styles.json"), "utf8"));
    return (doc.styles ?? []).map((s: any) => ({
      id: s.id, name: s.name, tagline: s.tagline,
      variants: (s.variants ?? []).map((v: any) => ({ id: `${s.id}.${v.id}`, name: `${s.name} · ${v.name}`, tagline: v.tagline })),
    }));
  } catch { return []; }
}

export async function GET(request: Request) {
  const auth = await requireSession(request); if (auth.response) return auth.response;
  return json({ styles: stylesList(), voices: VOICES, aspects: [...ASPECTS] }, auth.id);
}

export async function POST(request: Request) {
  const auth = await requireSession(request); if (auth.response) return auth.response;
  const id = auth.id;
  let form: FormData;
  try { form = await request.formData(); }
  catch { return problem(id, 400, "BAD_FORM", "Invalid form", "Send multipart/form-data."); }

  const style = String(form.get("style") ?? "tiles");
  const validStyles = new Set(stylesList().flatMap((s: any) => [s.id, ...s.variants.map((v: any) => v.id)]));
  if (validStyles.size && !validStyles.has(style))
    return problem(id, 422, "STYLE_UNKNOWN", "Unknown style", `Pick one of: ${[...validStyles].join(", ")}.`);

  const script = String(form.get("script") ?? "").trim();
  const voiceFile = form.get("voiceFile");
  if (!script && !(voiceFile instanceof File))
    return problem(id, 422, "VOICE_REQUIRED", "Voice required", "Send 'script' (for a Kokoro voice) or a 'voiceFile' upload.");

  const voice = String(form.get("voice") ?? "bm_george");
  if (script && !VOICES.includes(voice))
    return problem(id, 422, "VOICE_UNKNOWN", "Unknown voice", `Pick one of: ${VOICES.join(", ")}.`);

  const aspects = String(form.get("aspects") ?? "16x9,1x1,9x16")
    .split(",").map((a) => a.trim()).filter((a) => ASPECTS.has(a));
  if (!aspects.length)
    return problem(id, 422, "ASPECT_UNKNOWN", "No valid aspect", `Pick from: ${[...ASPECTS].join(", ")}.`);

  const jobId = `xr-${randomUUID().slice(0, 8)}`;
  const dir = path.join(JOBS, jobId);
  const mediaDir = path.join(dir, "media");
  mkdirSync(mediaDir, { recursive: true });

  const args: string[] = [path.join(ENGINE, "tools", "make_reel.py"), "--style", style,
    "--aspects", aspects.join(","), "--out", path.join(dir, "out"), "--film-id", jobId];

  if (voiceFile instanceof File) {
    const vf = path.join(dir, `voice_src${path.extname(voiceFile.name || ".mp3")}`);
    writeFileSync(vf, Buffer.from(await voiceFile.arrayBuffer()));
    args.push("--voice-file", vf);
  } else {
    args.push("--script", script, "--voice", voice);
  }

  const mediaPaths: string[] = [];
  for (const m of form.getAll("media")) {
    if (!(m instanceof File)) continue;
    const safe = (m.name || `media-${mediaPaths.length}`).replace(/[^\w.-]/g, "_");
    const dest = path.join(mediaDir, safe);
    writeFileSync(dest, Buffer.from(await m.arrayBuffer()));
    mediaPaths.push(dest);
  }
  if (mediaPaths.length) args.push("--media", ...mediaPaths);

  writeFileSync(path.join(dir, "request.json"), JSON.stringify({
    userId: auth.session!.userId, style, voice, aspects,
    script: script || null, media: mediaPaths.map((p) => path.basename(p)), createdAt: new Date().toISOString(),
  }, null, 1));
  writeFileSync(path.join(dir, "status.json"), JSON.stringify({ status: "running", startedAt: new Date().toISOString() }));

  const nodeBin = path.join(homedir(), ".nvm", "versions", "node", "v24.19.0", "bin");
  const child = spawn("python3", args, {
    cwd: ENGINE, detached: true, stdio: ["ignore", "pipe", "pipe"],
    env: { ...process.env, PATH: `${nodeBin}:${process.env.PATH}` },
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
          const dest = path.join(filesDir, `${aspect}.mp4`);
          try { copyFileSync(p, dest); } catch { continue; }
          outputs[aspect] = `/api/v1/explainers/${jobId}/files/${aspect}.mp4`;
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

  return json({ jobId, status: "running", statusUrl: `/api/v1/explainers/${jobId}` }, id, { status: 202 });
}
