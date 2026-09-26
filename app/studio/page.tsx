import type { Metadata } from "next";
import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth";
import { StudioApp } from "@/studio-v2/App";
import "@/studio-v2/nexstudio-v2.css";

export const metadata: Metadata = { title: "Studio · NexStudio" };

export default async function Page() {
  const h = await headers();
  const session = await getSession(new Request("http://localhost/studio", { headers: h }));
  if (!session) redirect("/?signin=1");
  return <StudioApp initialAuthed />;
}
