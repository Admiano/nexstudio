import { z } from "zod";
import { requireSession, requireTrustedOrigin } from "@/lib/route-auth";
import { json, problem, zodProblem } from "@/lib/http";
import { getPrisma } from "@/lib/db";

export const runtime = "nodejs";

const schema = z.object({
  name: z.string().trim().min(1).max(120).optional(),
  description: z.string().trim().max(2000).nullable().optional(),
});

export async function PATCH(request: Request, context: { params: Promise<{ id: string }> }) {
  const auth = await requireSession(request); if (auth.response) return auth.response;
  const origin = requireTrustedOrigin(request, auth.id); if (origin) return origin;
  const { id } = await context.params;
  const body = schema.safeParse(await request.json().catch(() => null));
  if (!body.success) return zodProblem(auth.id, body.error);
  const prisma = getPrisma()!;
  const brand = await prisma.studioBrand.findFirst({ where: { id, ownerUserId: auth.session!.userId } });
  if (!brand) return problem(auth.id, 404, "BRAND_NOT_FOUND", "Brand not found", "No production was changed.");
  const updated = await prisma.studioBrand.update({
    where: { id: brand.id },
    data: {
      name: body.data.name ?? brand.name,
      description: body.data.description === undefined ? brand.description : body.data.description,
    },
  });
  return json({ brand: updated }, auth.id);
}
