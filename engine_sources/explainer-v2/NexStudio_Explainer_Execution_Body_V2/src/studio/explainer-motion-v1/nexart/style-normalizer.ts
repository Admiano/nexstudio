import { AUTHORED_STYLE_FAMILY } from "./style-grammar";

export const AUTHORED_CARTOON_PALETTE = {
  ink: "#20282B",
  slate: "#60757B",
  slateDark: "#3E4B50",
  mutedLight: "#D9E1DF",
  paper: "#FFFDF8",
  accent: "#E58A4A",
  green: "#748A76",
} as const;

function hexToRgb(hex: string) {
  const value = hex.replace("#", "");
  return { r: parseInt(value.slice(0,2),16), g: parseInt(value.slice(2,4),16), b: parseInt(value.slice(4,6),16) };
}
function rgbToHsl({r,g,b}:{r:number;g:number;b:number}) {
  const rn=r/255,gn=g/255,bn=b/255,max=Math.max(rn,gn,bn),min=Math.min(rn,gn,bn),d=max-min;
  let h=0;
  if(d){ if(max===rn)h=((gn-bn)/d)%6; else if(max===gn)h=(bn-rn)/d+2; else h=(rn-gn)/d+4; h*=60;if(h<0)h+=360; }
  const l=(max+min)/2;
  const s=d===0?0:d/(1-Math.abs(2*l-1));
  return {h,s,l};
}
function normalizedColor(hex:string){
  const rgb=hexToRgb(hex), {h,s,l}=rgbToHsl(rgb);
  if(l>.94)return AUTHORED_CARTOON_PALETTE.paper;
  if(s<.08&&l<.22)return AUTHORED_CARTOON_PALETTE.ink;
  if(s<.08&&l>.78)return AUTHORED_CARTOON_PALETTE.mutedLight;
  if(l<.34)return AUTHORED_CARTOON_PALETTE.slateDark;
  if(l>.82)return AUTHORED_CARTOON_PALETTE.mutedLight;
  if((h<55||h>=330)&&s>.18)return AUTHORED_CARTOON_PALETTE.accent;
  if(h>=70&&h<175&&s>.16)return AUTHORED_CARTOON_PALETTE.green;
  return AUTHORED_CARTOON_PALETTE.slate;
}

/** Normalize permissively-licensed donor SVGs into one visible NexStudio hand. */
export function normalizeAuthoredSvgStyle(svg:string){
  let out=svg.replace(/#[0-9A-Fa-f]{6}\b/g,(hex)=>normalizedColor(hex));
  out=out.replace(/<svg\b/,`<svg data-nexstudio-style-family="${AUTHORED_STYLE_FAMILY}"`);
  return out;
}
