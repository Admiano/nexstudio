import type { Metadata } from "next";
import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth";
import { StudioDashboardExperience } from "@/studio-v1/react/StudioDashboardExperience";
export const metadata:Metadata={title:"Dashboard"};
export default async function Page(){const h=await headers();const session=await getSession(new Request("http://localhost/dashboard",{headers:h}));if(!session)redirect(process.env.NEXSTUDIO_PUBLIC_OPEN==="1"?"/api/v1/auth/guest/auto":"/?signin=1");redirect("/studio");}
