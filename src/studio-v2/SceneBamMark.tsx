import type { SVGProps } from "react";

/**
 * SceneBam Frame B: two connected scene chambers in a single geometric frame.
 * The lower chamber expands further right, expressing idea → full production.
 * The vector is shared in geometry and colors with app/icon.svg.
 */
export function SceneBamMark(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 80 80" role="img" aria-label="SceneBam" xmlns="http://www.w3.org/2000/svg" {...props}>
      <rect width="80" height="80" rx="18" fill="#111612" />
      <path d="M21 16 H42 C54 16 60 22 60 31 C60 38 56 43 50 45 C59 47 65 52 65 61 C65 71 57 74 43 74 H21 V16 Z M32 26 V39 H41 C47 39 50 37 50 33 C50 28 47 26 41 26 H32 Z M32 51 V64 H42 C50 64 54 62 54 58 C54 53 50 51 42 51 H32 Z" fill="#FFB000" fillRule="evenodd" />
    </svg>
  );
}
