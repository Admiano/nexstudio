import type { Metadata } from "next";
import { PublicDoc } from "@/studio-v2/PublicDoc";
import "@/studio-v2/nexstudio-v2.css";

export const metadata: Metadata = { title: "NexStudio — Terms of Service", description: "The rules for using NexStudio, written plainly." };
export default function Page() { return <PublicDoc slug="terms" />; }
