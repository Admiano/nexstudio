import type { Metadata } from "next";
import "./studio-v1.css";
import "./scenebam-brand.css";
import "@/studio-v1/dashboard/react/studio-dashboard.css";

const siteDescription = "Tell Bam what you want to create. SceneBam turns ideas into explainers, whiteboards, presenter-led videos and more, without a traditional editing timeline.";

export const metadata: Metadata = {
  title: { default: "SceneBam", template: "%s · SceneBam" },
  description: siteDescription,
  applicationName: "SceneBam",
  icons: { icon: [{ url: "/icon.svg", type: "image/svg+xml" }] },
  openGraph: {
    type: "website",
    siteName: "SceneBam",
    title: "SceneBam · From brief to finished video",
    description: siteDescription,
  },
  twitter: {
    card: "summary",
    title: "SceneBam · From brief to finished video",
    description: siteDescription,
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body><div className="studio-v1-boundary">{children}</div></body></html>;
}
