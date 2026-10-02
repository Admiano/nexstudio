import "dotenv/config";
import { createHmac } from "node:crypto";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "../src/generated/prisma/client";

// Preview setup only. Authentication still uses the application's existing
// expiring GUEST_PASS challenge and secure session-cookie flow.
async function main() {
  if (process.env.CAST_PREVIEW_MODE !== "true") {
    console.log("Cast preview guest setup skipped.");
    return;
  }
  const token = process.env.CAST_PREVIEW_GUEST_TOKEN ?? "";
  const secret = process.env.STUDIO_TRUST_SECRET ?? "";
  const connectionString = process.env.DATABASE_URL ?? "";
  const origin = process.env.APP_ORIGIN ?? "";
  if (token.length < 32 || secret.length < 32 || !connectionString || !origin.startsWith("https://")) {
    throw new Error("CAST_PREVIEW_CONFIGURATION_INCOMPLETE");
  }
  const email = "cast-v9-preview@nexstudio.invalid";
  const secretHash = createHmac("sha256", secret).update(`guest-pass\0${token}`).digest("hex");
  const expiresAt = new Date(Date.now() + 14 * 86400000);
  const prisma = new PrismaClient({ adapter: new PrismaPg({ connectionString, max: 1 }) });
  try {
    const userId = await prisma.$transaction(async (tx) => {
      const user = await tx.user.upsert({
        where: { email },
        create: { email, displayName: "Cast V9 Preview Tester" },
        update: {},
      });
      await tx.studioCreditAccount.upsert({
        where: { userId: user.id },
        create: { userId: user.id, balanceMinor: 0 },
        update: {},
      });
      const challenge = await tx.authChallenge.findFirst({
        where: { purpose: "GUEST_PASS", identifier: email, secretHash, userId: user.id },
      });
      if (challenge) {
        await tx.authChallenge.update({ where: { id: challenge.id }, data: { expiresAt } });
      } else {
        await tx.authChallenge.create({
          data: { purpose: "GUEST_PASS", identifier: email, secretHash, userId: user.id, expiresAt },
        });
      }
      return user.id;
    });
    console.log(JSON.stringify({ event: "CAST_PREVIEW_GUEST_READY", userId, expiresAt }));
  } finally {
    await prisma.$disconnect();
  }
}

main().catch(() => {
  console.error("CAST_PREVIEW_GUEST_SETUP_FAILED");
  process.exitCode = 1;
});
