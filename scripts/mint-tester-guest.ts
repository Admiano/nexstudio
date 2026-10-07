import "dotenv/config";
import { createHmac, randomBytes } from "node:crypto";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "../src/generated/prisma/client";
async function main() {
  const token = randomBytes(24).toString("base64url");
  const secret = process.env.STUDIO_TRUST_SECRET ?? "";
  const connectionString = process.env.DATABASE_URL ?? "";
  const email = `tester-${Date.now().toString(36)}@nexstudio.invalid`;
  const secretHash = createHmac("sha256", secret).update(`guest-pass\0${token}`).digest("hex");
  const expiresAt = new Date(Date.now() + 14 * 86400000);
  const prisma = new PrismaClient({ adapter: new PrismaPg({ connectionString, max: 1 }) });
  try {
    await prisma.$transaction(async (tx) => {
      const user = await tx.user.create({ data: { email, displayName: "NexStudio Tester" } });
      await tx.studioCreditAccount.create({ data: { userId: user.id, balanceMinor: 0 } });
      await tx.authChallenge.create({ data: { purpose: "GUEST_PASS", identifier: email, secretHash, userId: user.id, expiresAt } });
    });
    console.log(JSON.stringify({ token, email, expiresAt }));
  } finally { await prisma.$disconnect(); }
}
main().catch((e) => { console.error("MINT_FAILED", e?.message); process.exitCode = 1; });
