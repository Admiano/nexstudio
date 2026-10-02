import "dotenv/config";
import { execFileSync } from "node:child_process";
import { readdir } from "node:fs/promises";
import path from "node:path";
import { Client } from "pg";

// The checked-in migrations are incremental from an existing Standalone V1
// database. Bootstrap only an empty, explicitly enabled preview database.
// Existing application tables are never reset or replaced by this helper.
async function main() {
  if (process.env.CAST_PREVIEW_MODE !== "true") return;
  const connectionString = process.env.DATABASE_URL;
  if (!connectionString) throw new Error("CAST_PREVIEW_DATABASE_REQUIRED");
  const client = new Client({ connectionString });
  await client.connect();
  let applicationTables: number;
  try {
    const result = await client.query<{ count: string }>(
      `SELECT count(*) FROM information_schema.tables
       WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
         AND table_name <> '_prisma_migrations'`,
    );
    applicationTables = Number(result.rows[0].count);
  } finally {
    await client.end();
  }
  if (applicationTables > 0) {
    console.log("Cast preview database already initialized; normal migrations will run.");
    return;
  }
  const prismaCli = path.join(process.cwd(), "node_modules", "prisma", "build", "index.js");
  const run = (...args: string[]) => execFileSync(process.execPath, [prismaCli, ...args], { stdio: "inherit" });
  run("db", "push");
  // Retain the custom immutable-audit trigger that is outside Prisma's schema.
  run("db", "execute", "--file", "prisma/migrations/20260814160000_studio_trust_commerce_account/migration.sql");
  const migrations = (await readdir("prisma/migrations", { withFileTypes: true }))
    .filter((entry) => entry.isDirectory()).map((entry) => entry.name).sort();
  for (const migration of migrations) run("migrate", "resolve", "--applied", migration);
  console.log("CAST_PREVIEW_DATABASE_BASELINED");
}

main().catch(() => {
  console.error("CAST_PREVIEW_DATABASE_INITIALIZATION_FAILED");
  process.exitCode = 1;
});
