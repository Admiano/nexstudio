import { z } from "zod";
import { requireSession, requireTrustedOrigin } from "@/lib/route-auth";
import { json, problem, zodProblem } from "@/lib/http";
import { getPrisma } from "@/lib/db";

export const runtime = "nodejs";

const specSchema = z.object({
  character: z.enum(["female", "male"]),
  face: z.number().int().min(0).max(2).default(0),
  skin: z.string().trim().max(24).default("light"),
  hair: z.object({ style: z.string().trim().max(40), color: z.string().trim().max(24) }).nullable().default(null),
  lip: z.string().trim().max(24).nullable().default(null),
  neck: z.string().trim().max(24).nullable().default(null),
  outfit: z.object({
    kind: z.string().trim().max(40),
    color: z.string().trim().max(24).nullable().optional(),
    pieces: z.record(z.string(), z.string().trim().max(24)).optional(),
  }).nullable().default(null),
  watch: z.string().trim().max(24).nullable().default(null),
  voiceId: z.string().trim().max(120).nullable().default(null),
}).nullable();

const schema = z.object({
  name: z.string().trim().min(1).max(120).optional(),
  brandId: z.string().uuid().nullable().optional(),
  spec: specSchema.optional(),
});

export async function PATCH(request: Request, context: { params: Promise<{ id: string }> }) {
  const auth = await requireSession(request); if (auth.response) return auth.response;
  const origin = requireTrustedOrigin(request, auth.id); if (origin) return origin;
  const { id } = await context.params;
  const body = schema.safeParse(await request.json().catch(() => null));
  if (!body.success) return zodProblem(auth.id, body.error);
  const prisma = getPrisma()!;
  const member = await prisma.studioCastMember.findFirst({ where: { id, ownerUserId: auth.session!.userId } });
  if (!member) return problem(auth.id, 404, "CAST_NOT_FOUND", "Cast member not found", "No cast was changed.");
  if (body.data.brandId && !await prisma.studioBrand.findFirst({ where: { id: body.data.brandId, ownerUserId: auth.session!.userId } })) {
    return problem(auth.id, 404, "BRAND_NOT_FOUND", "Brand not found", "No cast was changed.");
  }
  const updated = await prisma.studioCastMember.update({
    where: { id: member.id },
    data: {
      name: body.data.name ?? member.name,
      brandId: body.data.brandId === undefined ? member.brandId : body.data.brandId,
      spec: body.data.spec === undefined ? member.spec ?? undefined : body.data.spec ?? undefined,
    },
  });
  return json({ member: { id: updated.id, name: updated.name, brandId: updated.brandId, spec: updated.spec ?? null, createdAt: updated.createdAt.toISOString(), updatedAt: updated.updatedAt.toISOString() } }, auth.id);
}

export async function DELETE(request: Request, context: { params: Promise<{ id: string }> }) {
  const auth = await requireSession(request); if (auth.response) return auth.response;
  const origin = requireTrustedOrigin(request, auth.id); if (origin) return origin;
  const { id } = await context.params;
  const prisma = getPrisma()!;
  const member = await prisma.studioCastMember.findFirst({ where: { id, ownerUserId: auth.session!.userId } });
  if (!member) return problem(auth.id, 404, "CAST_NOT_FOUND", "Cast member not found", "No cast was changed.");
  // cast links are Restrict-delete: drop the memberships first, then the member
  await prisma.studioProductionCastMember.deleteMany({ where: { castMemberId: member.id } });
  await prisma.studioCastMember.delete({ where: { id: member.id } });
  return json({ deleted: true }, auth.id);
}
