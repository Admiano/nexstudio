import { readFile } from "node:fs/promises";
import path from "node:path";

export type SecretFinding = { file: string; category: "ENVIRONMENT_FILE" | "PRIVATE_KEY" | "CREDENTIAL_VALUE" | "TOKEN_VALUE" | "ARCHIVE_ENVIRONMENT_ENTRY"; name?: string };

const ignoredEnvironmentNames = new Set([".env.example"]);
const secretPatterns: Array<{ category: SecretFinding["category"]; name: string; pattern: RegExp }> = [
  { category: "PRIVATE_KEY", name: "private-key", pattern: /-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----/i },
  { category: "TOKEN_VALUE", name: "jwt", pattern: /\beyJ[a-zA-Z0-9_-]{8,}\.[a-zA-Z0-9_-]{8,}\.[a-zA-Z0-9_-]{8,}\b/ },
  { category: "CREDENTIAL_VALUE", name: "provider-key", pattern: /\b(?:sk|pk|rk|xai|AIza)[-_][A-Za-z0-9_-]{16,}\b/ },
  { category: "CREDENTIAL_VALUE", name: "credential-assignment", pattern: /\b(?:API_KEY|SECRET_KEY|ACCESS_KEY|CLIENT_SECRET|PASSWORD|AUTH_TOKEN|PRIVATE_KEY)\s*[:=]\s*["']?(?!$|example|change[-_ ]?me|your[-_ ]|<)[A-Za-z0-9_./+:-]{12,}/i },
];

export function scanSecretText(file: string, text: string): SecretFinding[] {
  const findings: SecretFinding[] = [];
  for (const pattern of secretPatterns) if (pattern.pattern.test(text)) findings.push({ file, category: pattern.category, name: pattern.name });
  return findings;
}

export function scanExportPathNames(files: string[]) {
  return files.flatMap((file): SecretFinding[] => {
    const base = path.basename(file).toLowerCase();
    if (base.startsWith(".env") && !ignoredEnvironmentNames.has(base)) return [{ file, category: "ENVIRONMENT_FILE", name: base }];
    if (/(?:^|[\\/])(?:\.env(?:\.|$)|node_modules|\.git)(?:[\\/]|$)/i.test(file)) return [];
    if (/\.(?:zip|tar|tgz|7z)$/i.test(file) && /(?:\.env|credentials?|secrets?)/i.test(file)) return [{ file, category: "ARCHIVE_ENVIRONMENT_ENTRY", name: "environment-or-secret-archive" }];
    return [];
  });
}

export async function scanSourceExport(files: Array<{ path: string; text?: string; bytes?: Uint8Array }>) {
  const findings = scanExportPathNames(files.map((file) => file.path));
  for (const file of files) {
    if (file.text != null) findings.push(...scanSecretText(file.path, file.text));
    else if (file.bytes) {
      const sample = Buffer.from(file.bytes).toString("utf8");
      if (/-----BEGIN .*PRIVATE KEY-----|\beyJ[a-zA-Z0-9_-]{8,}\./.test(sample)) findings.push({ file: file.path, category: "PRIVATE_KEY", name: "binary-secret-marker" });
    }
  }
  return findings;
}

export function formatSecretFindings(findings: SecretFinding[]) {
  return findings.map((finding) => `${finding.category}:${finding.name ?? "unknown"}:${finding.file}`).join("\n");
}

export async function readAndScanSourceExport(files: string[]) {
  const findings = scanExportPathNames(files);
  for (const file of files) {
    if (scanExportPathNames([file]).length) continue;
    try { findings.push(...scanSecretText(file, await readFile(file, "utf8"))); } catch { /* binary/unreadable files are checked by the export implementation */ }
  }
  return findings;
}
