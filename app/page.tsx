import type { Metadata } from "next";
import { headers } from "next/headers";
import { getSession } from "@/lib/auth";
import { PublicSite } from "@/studio-v2/PublicSite";
import "@/studio-v2/nexstudio-v2.css";

export const metadata: Metadata = { title: { absolute: "SceneBam · From brief to finished video" }, description: "Tell Bam what to make. Create explainers, whiteboards, stories and character-led videos without a timeline." };

export default async function Page() {
  const h = await headers();
  const session = await getSession(new Request("http://localhost/", { headers: h }));
  return <PublicSite authed={Boolean(session)} />;
}
