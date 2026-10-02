import { z } from "zod";
import { castSpecSchema } from "@/lib/cast-spec-schema";
import { normalizeCastSpec,type CastSpec } from "@/studio-v2/cast/spec";
import type { Prisma } from "@/generated/prisma/client";
import { requireSession, requireTrustedOrigin } from "@/lib/route-auth";
import { getPrisma } from "@/lib/db";
import { json, problem, zodProblem } from "@/lib/http";

export const runtime = "nodejs";

const specSchema = castSpecSchema.nullable().default(null);

const schema = z.object({
  name: z.string().trim().min(1).max(120),
  brandId: z.string().uuid().nullable().optional(),
  spec: specSchema,
});

const castOut = (m: { id: string; name: string; brandId: string | null; spec: unknown; createdAt: Date; updatedAt: Date }) => ({
  id: m.id, name: m.name, brandId: m.brandId, spec: m.spec ?? null,
  createdAt: m.createdAt.toISOString(), updatedAt: m.updatedAt.toISOString(),
});

export async function GET(request: Request) {
  const auth = await requireSession(request); if (auth.response) return auth.response;
  const members = await getPrisma()!.studioCastMember.findMany({
    where: { ownerUserId: auth.session!.userId },
    orderBy: { updatedAt: "desc" },
  });
  return json({ cast: members.map(castOut) }, auth.id);
}

export async function POST(request: Request) {
  const auth = await requireSession(request); if (auth.response) return auth.response;
  const origin = requireTrustedOrigin(request, auth.id); if (origin) return origin;
  const body = schema.safeParse(await request.json().catch(() => null));
  if (!body.success) return zodProblem(auth.id, body.error);
  const prisma = getPrisma()!;
  if (body.data.brandId && !await prisma.studioBrand.findFirst({ where: { id: body.data.brandId, ownerUserId: auth.session!.userId } })) {
    return problem(auth.id, 404, "BRAND_NOT_FOUND", "Brand not found", "Cast member was not saved.");
  }
  const slug = body.data.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "avatar";
  const identityKey = `${slug}-${Date.now().toString(36)}`;
  try {
    const member = await prisma.studioCastMember.create({
      data: {
        ownerUserId: auth.session!.userId,
        brandId: body.data.brandId ?? null,
        name: body.data.name,
        identityKey,
        spec: body.data.spec ? normalizeCastSpec(body.data.spec as CastSpec) as unknown as Prisma.InputJsonValue : undefined,
      },
    });
    return json({ member: castOut(member) }, auth.id, { status: 201 });
  } catch (error) {
    const code = error instanceof Error ? error.message : "CAST_CREATE_FAILED";
    return problem(auth.id, 409, code, "Cast member could not be saved", "No cast was changed.");
  }
}
