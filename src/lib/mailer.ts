import { appendFileSync, mkdirSync } from "node:fs";
import path from "node:path";
import { env } from "./env";

const OUTBOX = path.join(process.cwd(), "data", "mail-outbox.log");

export interface Mail { to: string; subject: string; html: string; text?: string; }

// Resend when configured; in non-production without a key, mail lands in
// data/mail-outbox.log so the flow still works end to end. In production
// without a key, sends fail closed.
export async function sendMail(mail: Mail): Promise<{ sent: boolean; via: "resend" | "outbox" | "none" }> {
  if (env.resendApiKey && env.emailFrom) {
    try {
      const res = await fetch("https://api.resend.com/emails", {
        method: "POST",
        headers: { authorization: `Bearer ${env.resendApiKey}`, "content-type": "application/json" },
        body: JSON.stringify({ from: env.emailFrom, to: [mail.to], subject: mail.subject, html: mail.html, ...(mail.text ? { text: mail.text } : {}) }),
      });
      return res.ok ? { sent: true, via: "resend" } : { sent: false, via: "resend" };
    } catch {
      return { sent: false, via: "resend" };
    }
  }
  if (process.env.NODE_ENV === "production") return { sent: false, via: "none" };
  try {
    mkdirSync(path.dirname(OUTBOX), { recursive: true });
    appendFileSync(OUTBOX, JSON.stringify({ at: new Date().toISOString(), to: mail.to, subject: mail.subject, html: mail.html }) + "\n");
    return { sent: true, via: "outbox" };
  } catch {
    return { sent: false, via: "none" };
  }
}
