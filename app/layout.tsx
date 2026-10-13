import type { Metadata } from "next";
import "./studio-v1.css";
import "./scenebam-brand.css";
import "@/studio-v1/dashboard/react/studio-dashboard.css";
export const metadata:Metadata={title:{default:"SceneBam",template:"%s · SceneBam"},description:"Bring explainers, whiteboards, characters and stories to life with Bam, your creative director."};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body><div className="studio-v1-boundary">{children}</div></body></html>;}
