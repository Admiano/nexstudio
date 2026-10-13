import type { SVGProps } from "react";

/** SceneBam's initial Frame B vector mark. */
export function SceneBamMark(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 80 80" role="img" aria-label="SceneBam" xmlns="http://www.w3.org/2000/svg" {...props}>
      <rect width="80" height="80" rx="18" fill="#111612" />
      <path d="M23 18 V63 M23 21 H39 C51 21 56 26 56 34 C56 41 51 45 39 45 H23 M23 45 H42 C55 45 61 51 61 57 C61 64 54 66 42 66 H23" fill="none" stroke="#FFB000" strokeWidth="7.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
