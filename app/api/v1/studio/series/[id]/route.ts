import { z } from "zod";
import { requireSession, requireTrustedOrigin } from "@/lib/route-auth";
import { getPrisma } from "@/lib/db";
import { json, problem, zodProblem } from "@/lib/http";

export const runtime = "nodejs";

const patchSchema = z.object({
  name: z.string().trim().min(1).max(160).optional(),
  description: z.string().trim().max(1000).nullable().optional(),
  brandId: z.string().uuid().nullable().optional(),
});

export async function PATCH(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const auth = await requireSession(request);
  if (auth.response) return auth.response;
  const origin = requireTrustedOrigin(request, auth.id);
  if (origin) return origin;
  const { id } = await params;
  const body = patchSchema.safeParse(await request.json().catch(() => null));
  if (!body.success) return zodProblem(auth.id, body.error);
  const prisma = getPrisma()!;
  const series = await prisma.studioSeries.findFirst({ where: { id, ownerUserId: auth.session!.userId } });
  if (!series) return problem(auth.id, 404, "SERIES_NOT_FOUND", "Series not found", "Nothing was changed.");
  if (body.data.brandId && !await prisma.studioBrand.findFirst({ where: { id: body.data.brandId, ownerUserId: auth.session!.userId } })) {
    return problem(auth.id, 404, "BRAND_NOT_FOUND", "Brand not found", "Series was not changed.");
  }
  const data: { name?: string; description?: string | null; brandId?: string | null } = {};
  if (body.data.name !== undefined) data.name = body.data.name;
  if (body.data.description !== undefined) data.description = body.data.description;
  if (body.data.brandId !== undefined) data.brandId = body.data.brandId;
  const updated = await prisma.studioSeries.update({ where: { id: series.id }, data });
  return json({ series: updated }, auth.id);
}
