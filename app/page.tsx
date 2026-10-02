import type { Metadata } from "next";
import { headers } from "next/headers";
import { getSession } from "@/lib/auth";
import { PublicSite } from "@/studio-v2/PublicSite";
import "@/studio-v2/nexstudio-v2.css";

export const metadata: Metadata = { title: "NexStudio · Make something worth watching", description: "Creative production, directed by NexMind." };

export default async function Page() {
  const h = await headers();
  const session = await getSession(new Request("http://localhost/", { headers: h }));
  return <PublicSite authed={Boolean(session)} />;
}
