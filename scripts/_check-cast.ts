import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "../src/generated/prisma/client";
const p = new PrismaClient({ adapter: new PrismaPg({ connectionString: process.env.DATABASE_URL! }) });
const m = await p.studioCastMember.findFirst({ where: { name: { contains: "Teacher" } } });
console.log(JSON.stringify(m, null, 1).slice(0, 2200));
await p.$disconnect();
