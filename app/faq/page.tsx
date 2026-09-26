import type { Metadata } from "next";
import { PublicDoc } from "@/studio-v2/PublicDoc";
import "@/studio-v2/nexstudio-v2.css";

export const metadata: Metadata = { title: "NexStudio · FAQ", description: "Questions people actually ask about NexStudio, answered." };
export default function Page() { return <PublicDoc slug="faq" />; }
