import type { Metadata } from "next";
import { PublicDoc } from "@/studio-v2/PublicDoc";
import "@/studio-v2/nexstudio-v2.css";

export const metadata: Metadata = { title: "NexStudio — Privacy Policy", description: "What NexStudio collects, why, and how you take it back." };
export default function Page() { return <PublicDoc slug="privacy" />; }
