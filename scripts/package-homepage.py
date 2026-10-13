"""Package the committed homepage and pricing page for an isolated static site."""
import argparse
import hashlib
import json
import re
import subprocess
import tarfile
from io import BytesIO
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--revision", default="HEAD")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent

    def git(*arguments):
        return subprocess.check_output(["git", *arguments], cwd=root)

    revision = git("rev-parse", args.revision).decode().strip()
    files = {}
    for name in (
        "package.json", "package-lock.json", "tsconfig.json", "app/layout.tsx",
        "app/studio-v1.css", "src/studio-v1/dashboard/react/studio-dashboard.css",
        "src/studio-v2/PublicSite.tsx", "src/studio-v2/nx-presence.ts",
        "src/studio-v2/nexstudio-v2.css", "public/nexstudio/nx-presence.js",
        "src/studio-v2/PricingTiers.tsx", "src/lib/plan.ts",
    ):
        files[name] = git("show", f"{revision}:{name}")

    # Keep the actual homepage component intact. This static entry point has no
    # session, database, auth configuration, API handlers or other app routes.
    files["app/page.tsx"] = b'''import type { Metadata } from "next";
import { PublicSite } from "@/studio-v2/PublicSite";
import "@/studio-v2/nexstudio-v2.css";

export const metadata: Metadata = {
  title: "NexStudio \\u00b7 Make something worth watching",
  description: "Creative production, directed by NexMind.",
};
export default function Page() {
  return <PublicSite authed={false} googleAuth={false} />;
}
'''
    pricing_source = git("show", f"{revision}:app/pricing/page.tsx").decode()
    pricing_source = re.sub(
        r'^import .* from "(?:next/headers|@/lib/(?:auth|plan|env))";\n',
        "", pricing_source, flags=re.MULTILINE,
    )
    start = pricing_source.index("export default async function Page() {")
    end = pricing_source.index("  return (", start)
    pricing_source = (
        pricing_source[:start]
        + "export default function Page() {\n  const session = null;\n  const plan = null;\n"
        + pricing_source[end:]
    )
    pricing_source = 'import { RevealPricing } from "./reveal";\n' + pricing_source
    pricing_source = pricing_source.replace(
        '<div id="publicSite" className="pw-pricing-page">',
        '<div id="publicSite" className="pw-pricing-page"><RevealPricing />',
    )
    files["app/pricing/page.tsx"] = pricing_source.encode()
    # The homepage installs its own reveal observer; the standalone pricing
    # page also needs to reveal its plan cards after hydration.
    files["app/pricing/reveal.tsx"] = b'''"use client";
import { useEffect } from "react";
export function RevealPricing() {
  useEffect(() => {
    document.querySelectorAll(".pw-pricing-page .pw-reveal")
      .forEach(element => element.classList.add("in"));
  }, []);
  return null;
}
'''
    files["next.config.mjs"] = b'''export default {
  output: "export", poweredByHeader: false, images: { unoptimized: true },
};
'''
    files["Dockerfile"] = b'''FROM mirror.gcr.io/library/node:24-bookworm-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN node node_modules/next/dist/bin/next build
'''
    files[".dockerignore"] = b"node_modules\n.next\nout\n.git\n.env*\n"
    assets = set(re.findall(r'["\'](/(?:home|cast)/[^"\']+)["\']', files["src/studio-v2/PublicSite.tsx"].decode()))
    for url in sorted(assets):
        name = "public" + url.split("?", 1)[0]
        files[name] = git("show", f"{revision}:{name}")
    for name in ("public/favicon.ico",):
        if subprocess.run(["git", "cat-file", "-e", f"{revision}:{name}"], cwd=root, capture_output=True).returncode == 0:
            files[name] = git("show", f"{revision}:{name}")

    manifest = {
        "revision": revision,
        "homepageSha256": hashlib.sha256(files["src/studio-v2/PublicSite.tsx"]).hexdigest(),
        "stylesheetSha256": hashlib.sha256(files["src/studio-v2/nexstudio-v2.css"]).hexdigest(),
        "pricingPageSha256": hashlib.sha256(files["app/pricing/page.tsx"]).hexdigest(),
        "pricingTiersSha256": hashlib.sha256(files["src/studio-v2/PricingTiers.tsx"]).hexdigest(),
        "assetCount": len(assets),
        "routes": ["/", "/pricing"],
    }
    files["homepage-source.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(args.output, "w:gz") as archive:
        for name, content in sorted(files.items()):
            info = tarfile.TarInfo(name)
            info.size = len(content)
            info.mode = 0o644
            archive.addfile(info, BytesIO(content))
    print(json.dumps({**manifest, "archiveBytes": args.output.stat().st_size}))


if __name__ == "__main__":
    main()
