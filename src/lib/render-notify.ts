import path from "node:path";
import { existsSync, writeFileSync } from "node:fs";
import { getPrisma } from "./db";
import { sendMail } from "./mailer";
import { env } from "./env";

// Called when a job status read first observes "done". One marker file in the
// job dir dedupes forever, so a finished render never mails twice and a mail
// failure never breaks the status endpoint.
export async function maybeNotifyRenderDone(jobDir: string, userId: string, title: string): Promise<void> {
  const marker = path.join(jobDir, ".render-notified");
  if (existsSync(marker)) return;
  try { writeFileSync(marker, new Date().toISOString()); } catch { return; }
  try {
    const prisma = getPrisma(); if (!prisma) return;
    const user = await prisma.user.findUnique({ where: { id: userId }, select: { email: true, settings: true } });
    if (!user?.email) return;
    const settings = (user.settings ?? {}) as Record<string, unknown>;
    if (settings.notifyRendersEmail === false) return;
    const url = `${env.appOrigin}/studio#work`;
    const clean = title.replace(/\s+/g, " ").trim().slice(0, 90) || "Your video";
    await sendMail({
      to: user.email,
      subject: "Your video is ready to review",
      html: `<p><b>${clean}</b> finished rendering.</p><p>All three screens (16:9, 9:16, 1:1) are ready to review.</p><p><a href="${url}">Open it in your Studio</a></p>`,
      text: `${clean} finished rendering. Open it in your Studio: ${url}`,
    });
  } catch { /* never surface mail failures to the status read */ }
}
