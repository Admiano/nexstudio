"use client";
import { SceneBamMark } from "./SceneBamMark";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { ensureNxPresence } from "./nx-presence";

const FAMILY_ART: Record<string, ReactNode> = {
  explainer: (
    <svg aria-hidden="true" preserveAspectRatio="xMidYMid slice" role="presentation" viewBox="0 0 320 150">
      <rect fill="#63736A" height="150" width="320" />
      <path d="M-12 104 C44 104 72 104 116 104" fill="none" stroke="#F3EEE4" strokeLinecap="round" strokeWidth="2.2" />
      <path d="M-12 76 C48 76 92 76 143 76" fill="none" opacity=".88" stroke="#F3EEE4" strokeLinecap="round" strokeWidth="2.2" />
      <path d="M-12 48 C62 48 115 48 170 48" fill="none" opacity=".72" stroke="#F3EEE4" strokeLinecap="round" strokeWidth="2.2" />
      <circle cx="213" cy="76" fill="#F3EEE4" r="37" />
      <circle cx="213" cy="76" fill="#63736A" r="11" />
      <circle cx="270" cy="111" fill="#E9B89B" r="18" />
    </svg>
  ),
  whiteboard: (
    <svg aria-hidden="true" preserveAspectRatio="xMidYMid slice" role="presentation" viewBox="0 0 320 150">
      <rect fill="#F4F1E9" height="150" width="320" />
      <path d="M34 105 C73 75 109 64 149 72 C181 78 199 98 236 97 C260 97 276 87 289 71" fill="none" stroke="#20241F" strokeLinecap="round" strokeWidth="2.5" />
      <path d="M58 112 C77 115 96 114 114 108" fill="none" opacity=".58" stroke="#20241F" strokeLinecap="round" strokeWidth="2" />
      <circle cx="149" cy="72" fill="none" r="22" stroke="#20241F" strokeWidth="2.2" />
      <circle cx="149" cy="72" fill="#FFB000" r="5" />
      <path d="M225 43 C242 39 258 40 274 47" fill="none" stroke="#20241F" strokeLinecap="round" strokeWidth="2" />
      <path d="M254 34 L275 47 L252 53" fill="none" stroke="#20241F" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
    </svg>
  ),
  character: (
    <svg aria-hidden="true" preserveAspectRatio="xMidYMid slice" role="presentation" viewBox="0 0 320 150">
      <rect fill="#CFC1B2" height="150" width="320" />
      <rect fill="#BDAA98" height="29" width="320" x="0" y="121" />
      <circle cx="167" cy="47" fill="#E9B99B" r="25" />
      <path d="M132 84 C145 69 190 69 204 84 C212 94 217 111 219 150 H116 C119 112 123 95 132 84Z" fill="#F4F0E7" />
      <path d="M199 91 C218 97 231 107 243 119" fill="none" stroke="#F4F0E7" strokeLinecap="round" strokeWidth="15" />
      <circle cx="246" cy="121" fill="#E9B99B" r="7" />
      <path d="M132 92 C116 99 105 109 98 120" fill="none" opacity=".92" stroke="#F4F0E7" strokeLinecap="round" strokeWidth="14" />
      <circle cx="96" cy="121" fill="#E9B99B" r="6.5" />
    </svg>
  ),
  illustrated: (
    <svg aria-hidden="true" preserveAspectRatio="xMidYMid slice" role="presentation" viewBox="0 0 320 150">
      <rect fill="#D8C9BC" height="150" width="320" />
      <circle cx="236" cy="52" fill="#E7B995" r="38" />
      <g transform="rotate(-6 160 76)">
        <rect fill="#F6F2E9" height="112" width="154" x="83" y="20" />
        <rect fill="#EEE7DB" height="112" width="17" x="83" y="20" />
        <path d="M115 101 C130 80 151 69 174 68 C197 66 215 76 237 98 L237 132 L115 132Z" fill="#2A2D29" />
        <circle cx="189" cy="59" fill="#FFB000" r="12" />
      </g>
      <rect fill="#2A2D29" height="7" opacity=".88" rx="3.5" width="50" x="46" y="39" />
      <rect fill="#2A2D29" height="5" opacity=".45" rx="2.5" width="31" x="46" y="52" />
    </svg>
  ),
};

function WorkClip({ src, poster, label }: { src: string; poster: string; label: string }) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  useEffect(() => {
    const node = videoRef.current;
    if (!node) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (!("IntersectionObserver" in window)) { void node.play().catch(() => undefined); return; }
    const io = new IntersectionObserver((entries) => {
      const entry = entries[0];
      if (entry?.isIntersecting && entry.intersectionRatio >= 0.3) void node.play().catch(() => undefined);
      else node.pause();
    }, { threshold: [0, 0.3, 0.7] });
    io.observe(node);
    return () => { io.disconnect(); node.pause(); };
  }, []);
  return (
    <video ref={videoRef} className="pw-work-clip" muted loop playsInline preload="metadata" poster={poster} aria-label={label}>
      <source src={src} type="video/mp4" />
    </video>
  );
}

const OPTION_RAIL: Array<{ slot: string; name: string; img: string; tile: string }> = [
  { slot: "Hair", name: "Braids", img: "/home/opts/base.png", tile: "/cast/options/v21/male/hair/braids.webp" },
  { slot: "Wardrobe", name: "Tee", img: "/home/opts/base.png", tile: "/cast/options/v21/male/top/o2.webp" },
  { slot: "Face", name: "Two", img: "/home/opts/m-face1.png", tile: "/cast/options/v21/male/face/1.webp" },
  { slot: "Hair", name: "Quiff", img: "/home/opts/m-quiff.png", tile: "/cast/options/v21/male/hair/quiff.webp" },
  { slot: "Bottom", name: "Jeans", img: "/home/opts/base.png", tile: "/cast/options/v21/male/bottom/classic-jeans.webp" },
  { slot: "Hair", name: "Swept", img: "/home/opts/m-swept.png", tile: "/cast/options/v21/male/hair/swept.webp" },
  { slot: "Wardrobe", name: "Oxford", img: "/home/opts/m-oxford.png", tile: "/cast/options/v21/male/top/o3.webp" },
  { slot: "Face", name: "Three", img: "/home/opts/m-face2.png", tile: "/cast/options/v21/male/face/2.webp" },
  { slot: "Bottom", name: "Chinos", img: "/home/opts/m-chinos.png", tile: "/cast/options/v21/male/bottom/chinos.webp" },
  { slot: "Wardrobe", name: "Knit", img: "/home/opts/m-knit.png", tile: "/cast/options/v21/male/top/o4.webp" },
];

const WATCH_SVG = (
  <svg viewBox="0 0 120 120" aria-hidden="true" className="pw-ad-product">
    <circle cx="60" cy="60" r="44" fill="#10100f" />
    <circle cx="60" cy="60" r="38" fill="none" stroke="#c8a24a" strokeWidth="1.6" />
    <circle cx="60" cy="60" r="34" fill="#1c1b19" />
    {[...Array(12)].map((_, i) => { const a = (i * 30 * Math.PI) / 180; const x1 = 60 + Math.sin(a) * 29, y1 = 60 - Math.cos(a) * 29, x2 = 60 + Math.sin(a) * 33, y2 = 60 - Math.cos(a) * 33; return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#e8dcc0" strokeWidth={i % 3 === 0 ? 2 : 1} />; })}
    <line x1="60" y1="60" x2="60" y2="38" stroke="#e8dcc0" strokeWidth="2.6" strokeLinecap="round" />
    <line x1="60" y1="60" x2="76" y2="66" stroke="#e8dcc0" strokeWidth="2" strokeLinecap="round" />
    <line x1="60" y1="62" x2="50" y2="82" stroke="#c8a24a" strokeWidth="1.4" strokeLinecap="round" />
    <circle cx="60" cy="60" r="3" fill="#c8a24a" />
    <rect x="102" y="56" width="6" height="9" rx="1.6" fill="#c8a24a" />
  </svg>
);

function PresenterScene() {
  const [phase, setPhase] = useState<0 | 1 | 2>(0);
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) { setPhase(1); return; }
    const seq: Array<[0 | 1 | 2, number]> = [[0, 3600], [1, 3000], [0, 900], [2, 4300]];
    let step = 0, timer = 0;
    const tick = () => {
      const [next, duration] = seq[step % seq.length];
      setPhase(next);
      timer = window.setTimeout(tick, duration);
      step += 1;
    };
    tick();
    return () => window.clearTimeout(timer);
  }, []);
  return (<>
    <div className={`pw-scene${phase === 2 ? " is-squeezed" : ""}`} aria-label="A presenter in the studio as a lower third and a squeeze-back ad appear">
      <div className="pw-sq-band" aria-hidden="true">
        <i className="pw-sq-seam-v" /><i className="pw-sq-seam-h" />
        <div className="pw-sq-side">
          {WATCH_SVG}
          <b className="pw-ad-brand">AURELLE</b>
          <span className="pw-ad-line">The Meridian. A quiet kind of punctual.</span>
          <span className="pw-ad-cta">Shop the collection<i>→</i></span>
        </div>
        <div className="pw-sq-promo">
          <span className="pw-ad-tag">sponsored</span>
          <span className="pw-promo-copy"><i>AURELLE</i><b>The Meridian · aurelle.co</b></span>
        </div>
      </div>
      <div className="pw-scene-frame">
        <video className="pw-scene-video" src="/home/cast-host.mp4?v=2" autoPlay muted loop playsInline preload="auto" aria-label="Daniel, a SceneBam presenter, speaking in the studio" />
        <div className={`pw-scene-voice${phase === 0 ? " on" : ""}`} aria-hidden="true"><i /><i /><i /><i /></div>
        <div className={`pw-lt${phase === 1 ? " on" : ""}`} aria-hidden="true">
          <i className="pw-lt-bar" />
          <div className="pw-lt-plate">
            <span>host · scenebam</span>
            <b>Daniel Cole</b>
          </div>
          <div className="pw-lt-slot"><i>presented with a brand here</i></div>
        </div>
      </div>
    </div>
    <div className="pw-cast-stages" aria-hidden="true">
      <span className={phase === 0 ? "on" : ""}><i>01</i>speaking</span>
      <span className={phase === 1 ? "on" : ""}><i>02</i>lower third</span>
      <span className={phase === 2 ? "on" : ""}><i>03</i>squeeze-back</span>
    </div>
  </>);
}

function PartsScene() {
  const N = OPTION_RAIL.length;
  const [raw, setRaw] = useState(0);
  const [jump, setJump] = useState(false);
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const id = window.setInterval(() => {
      setRaw((r) => {
        if (r >= 2 * N) { setJump(true); return 0; }
        return r + 1;
      });
    }, 2200);
    return () => window.clearInterval(id);
  }, [N]);
  useEffect(() => { if (jump) { const t = window.setTimeout(() => setJump(false), 700); return () => window.clearTimeout(t); } }, [jump]);
  const pos = raw % N;
  const cur = OPTION_RAIL[pos];
  return (
    <div className="pw-conf" aria-label="A presenter being assembled from swappable parts">
      <div className="pw-conf-host">
        {OPTION_RAIL.map((o, i) => (
          <img key={o.name + o.slot} className={i === pos ? "on" : ""} src={o.img} alt={`${o.name} ${o.slot.toLowerCase()} on the presenter`} loading="lazy" />
        ))}
        <span className="pw-conf-name">Daniel</span>
        <span className="pw-conf-cur"><i>{cur.slot}</i><b>{cur.name}</b></span>
      </div>
      <div className="pw-rail" aria-hidden="true">
        <div className={`pw-rail-track${jump ? " jump" : ""}`} style={{ transform: `translateY(calc(${-raw} * var(--rail-item)))` }}>
          {[...OPTION_RAIL, ...OPTION_RAIL, ...OPTION_RAIL].map((o, i) => (
            <div key={i} className={`pw-rail-item${i === raw ? " live" : ""}`}>
              <img src={o.tile} alt="" loading="lazy" />
              <div><b>{o.slot}</b><span>{o.name}</span></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function CastScene() {
  const [speaker, setSpeaker] = useState<0 | 1>(0);
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const id = window.setInterval(() => setSpeaker((s) => (s === 0 ? 1 : 0)), 3800);
    return () => window.clearInterval(id);
  }, []);
  return (
    <div className="pw-cast-scene" aria-label="Two presenters handing the same scene to each other">
      <div className="pw-cast-frame">
        <img className={speaker === 0 ? "on" : ""} src="/cast/default-female-v20.webp" alt="Maya, a SceneBam presenter" />
        <img className={speaker === 1 ? "on" : ""} src="/cast/default-male-v20.webp" alt="Daniel, a SceneBam presenter" />
        <div className="pw-cast-voice" aria-hidden="true"><i /><i /><i /><i /></div>
      </div>
      <div className="pw-cast-take">
        <span className={`pw-cast-who ${speaker === 0 ? "on" : ""}`}>Maya</span>
        <span className={`pw-cast-who ${speaker === 1 ? "on" : ""}`}>Daniel</span>
        <p>“…and instead of waiting two days, it settles in seconds.”</p>
        <span className="pw-cast-note">Same take. Different presenter, mid-sentence if you want.</span>
      </div>
    </div>
  );
}

const RECOMP_LAYERS = <><i className="rc-rule a" /><i className="rc-rule b faint" /><i className="rc-mass" /><i className="rc-signal" /></>;
const GHOST_LAYERS = <><i className="build-pencil" /><span className="build-ghost-lines"><i /><i /></span></>;

const FAMILIES = [
  { key: "explainer", name: "Explainer", desc: "Make complex systems instantly understandable without flattening the idea.", art: "explainer" },
  { key: "whiteboard", name: "Whiteboard", desc: "Reason visually in real time so the viewer follows the thinking, not just the answer.", art: "whiteboard" },
  { key: "stickman", name: "Character", desc: "Carry the message through performance, gesture, framing and believable physical intent.", art: "character", soon: true },
  { key: "editorial-motion", name: "Illustrated Stories", desc: "Build narrative meaning through typography, illustration, staging and editorial rhythm.", art: "illustrated", soon: true },
];

export function PublicSite({ authed }: { authed: boolean }) {
  const router = useRouter();
  const [brief, setBrief] = useState("Make a 30-second explainer for a language-learning app. Friendly, memorable, and built for social.");
  const [signIn, setSignIn] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined" && new URLSearchParams(window.location.search).get("signin") === "1") setSignIn(true);
  }, []);

  useEffect(() => { ensureNxPresence(); }, []);

  useEffect(() => {
    const els = Array.from(document.querySelectorAll<HTMLElement>(".pw-reveal:not(.in)"));
    if (!("IntersectionObserver" in window)) { els.forEach((el) => el.classList.add("in")); return; }
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
    }, { threshold: 0.12 });
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);

  const enter = () => {
    if (brief.trim()) sessionStorage.setItem("nx.brief", brief);
    if (authed) router.push("/studio"); else setSignIn(true);
  };

  return (
    <div id="publicSite">
      <header className="pw-nav">
        <a aria-label="SceneBam" className="pw-logo" href="#top"><span className="brand-mark sb-mark"><SceneBamMark aria-hidden="true" focusable="false" /></span><span className="sb-wordmark">Scene<strong>Bam</strong></span></a>
        <nav aria-label="Public navigation" className="pw-links"><a href="#make">Create</a><a href="#proof">Explore</a><a href="#bam">How it works</a></nav>
        <div className="pw-actions">
          <button className="pw-ghost" onClick={() => { if (authed) router.push("/studio"); else setSignIn(true); }}>Sign in</button>
          <button className="pw-solid" onClick={enter}>Open Studio</button>
        </div>
      </header>
      <main id="top">
        <section className="pw-wrap pw-hero">
          <div className="pw-hero-main pw-reveal in">
            <div className="pw-kicker"><i /> Your creative studio · Meet Bam</div>
            <h1>From brief to <em>finished video.</em></h1>
            <p className="pw-hero-copy">Tell Bam what you want to make. Approve the creative direction. SceneBam produces the video, and you can revise, download, or publish it. No timeline. No complex editing. Just the production you asked for.</p>
            <div className="pw-hero-actions"><button className="pw-solid" onClick={() => document.getElementById("pwBrief")?.focus()}>Make a video →</button><button className="pw-ghost" onClick={() => document.getElementById("make")?.scrollIntoView({ behavior: "smooth" })}>See what it makes</button></div>
            <div className="pw-small-proof"><span>Direction before production</span><span>Made for every screen</span><span>Download or publish</span></div>
          </div>
          <div className="pw-live pw-reveal in">
            <div className="pw-demo">
              <div className="pw-demo-top"><div className="pw-demo-brand"><span aria-hidden="true" className="nx-presence nx-presence--mini" data-mode="matrix" data-nx-presence="" data-state="idle"><canvas /></span> Bam</div><span className="pw-demo-status">Your brief · Start with Bam</span></div>
              <div className="pw-demo-body">
                <div className="pw-demo-state">
                  <textarea id="pwBrief" aria-label="Describe the video you want to make" value={brief} onChange={(e) => setBrief(e.target.value)} placeholder="Make a 30-second explainer for a language-learning app…" />
                  <div className="pw-demo-chips" aria-label="Context available inside the Studio"><span className="pw-demo-chip">Files</span><span className="pw-demo-chip">Brand</span><span className="pw-demo-chip">References</span><span className="pw-demo-chip">Series</span></div>
                  <div className="pw-demo-foot"><span>Your brief carries into the Studio for Bam to develop.</span><button className="pw-demo-go" onClick={enter}>Continue in Studio <b>→</b></button></div>
                </div>
              </div>
            </div>
          </div>
        </section>
        <section className="pw-section" id="make">
          <div className="pw-wrap">
            <div className="pw-section-head pw-reveal"><div><div className="pw-kicker"><i /> Production families</div></div><div><h2>Choose a direction. Or don’t.</h2><p>Bam can infer the right production treatment from the brief. When you already know what you want, give it a nudge. Either way, you stay in one flow.</p></div></div>
            <div className="pw-families">
              {FAMILIES.map((f, i) => (
                <button key={f.key} disabled={Boolean(f.soon)} aria-label={`Choose ${f.name}`} className={`pw-family pw-reveal ${f.soon ? "soon" : ""}`} data-delay={String(i)} onClick={() => { if (f.soon) return; sessionStorage.setItem("nx.family", f.key); enter(); }}>
                  {f.soon && <em className="pw-soon-tag">Coming soon</em>}
                  <div aria-hidden="true" className="pw-family-media"><div className="pw-family-frame"><div className={`family-native family-native-${f.art}`}>{FAMILY_ART[f.art]}</div></div></div>
                  <div className="pw-family-copy"><b>{f.name}</b><span>{f.desc}</span></div>
                </button>
              ))}
            </div>
          </div>
        </section>
        <section className="pw-section" id="work">
          <div className="pw-wrap">
            <div className="pw-section-head pw-reveal"><div><div className="pw-kicker"><i /> Drawn for you</div></div><div><h2>From intent to video in one prompt.</h2><p>Say “explain Solana in a minute” and the answer gets drawn out on the board, line by line. Not a wall of text. Someone sketching it out for you while they talk.</p></div></div>
            <div className="pw-work-stage pw-reveal">
              <WorkClip src="/home/board.mp4" poster="/home/board.jpg" label="A Solana explainer drawn live on a whiteboard" />
              <div className="pw-work-cap"><span className="pw-work-chip">Whiteboard · Explainer</span><span>One line in. A minute of film out.</span></div>
            </div>
          </div>
        </section>
        <section aria-label="Native production intelligence" className="pw-section" id="proof">
          <div className="pw-wrap">
            <div className="pw-proof-grid">
              <article className="pw-proof-card recompose pw-reveal">
                <div className="pw-proof-visual"><div className="recomp-artboard" aria-hidden="true"><div className="recomp-board wide" data-ratio="16:9">{RECOMP_LAYERS}</div><div className="recomp-board tall" data-ratio="9:16">{RECOMP_LAYERS}</div><div className="recomp-board square" data-ratio="1:1">{RECOMP_LAYERS}</div></div></div>
                <div className="pw-proof-copy"><span className="pw-proof-label">Native recomposition</span><h3>Same direction. Different frame.</h3><p>Headline, subject, negative space and supporting copy are deliberately restaged for 16:9, 9:16 and 1:1 instead of cropped from one master.</p></div>
              </article>
              <article className="pw-proof-card production pw-reveal" data-delay="1">
                <div className="pw-proof-visual"><div className="build-artboard" aria-hidden="true"><div className="build-ghost g1">{GHOST_LAYERS}</div><div className="build-ghost g2">{GHOST_LAYERS}</div><div className="build-ghost g3">{GHOST_LAYERS}</div><div className="build-work"><div className="build-preview"><i className="bp-line" /><i className="bp-mass" /><i className="bp-signal" /></div><div className="build-meta"><div className="build-meta-top"><span>Same work</span><b>V3 · Ready</b></div><div className="build-meta-signal"><i /><i /><i /></div><div className="build-lineage"><span>V1</span><i /><em /><span>V2</span><i /><em /><span>V3</span><i /></div></div></div></div></div>
                <div className="pw-proof-copy"><span className="pw-proof-label">Production, not editing</span><h3>You direct. SceneBam builds.</h3><p>You approve the creative direction, then review the result. Revisions go back through Bam instead of forcing you into a timeline editor.</p></div>
              </article>
            </div>
          </div>
        </section>
        <section className="pw-section" id="cast">
          <div className="pw-wrap">
            <div className="pw-section-head pw-reveal"><div><div className="pw-kicker"><i /> Your cast</div></div><div><h2>Characters that stay in character.</h2><p>Build a recognizable presenter using face, hair, wardrobe and voice. Explore scene treatments and casting possibilities as the presenter system develops.</p></div></div>
            <div className="pw-cast-bento">
              <div className="pw-cast-tile pw-cast-main pw-reveal">
                <PresenterScene />
                <div className="pw-cast-cap"><span className="pw-work-chip">Presenter preview</span><span>Lower thirds and squeeze-backs are the moments in a film that can work for you.</span></div>
              </div>
              <div className="pw-cast-tile pw-cast-swap pw-reveal" data-delay="1"><CastScene /></div>
              <div className="pw-cast-tile pw-cast-parts pw-reveal" data-delay="2">
                <span className="pw-cast-parts-label">Every presenter is parts you can change</span>
                <PartsScene />
              </div>
            </div>
          </div>
        </section>
        <section className="pw-section" id="bam">
          <div className="pw-wrap">
            <div className="pw-section-head pw-reveal"><div className="pw-kicker"><i /> Meet Bam</div><h2>Context becomes creative direction.</h2><p>Bam reads the brief alongside Brand, Series, references and previous work, then resolves a production direction you can inspect before anything is produced.</p></div>
            <div className="pw-mind-stage pw-reveal">
              <div className="mind-context-stack"><div className="mind-context-label">What Bam understands</div>
                <div className="mind-context-card"><div className="mind-context-ico">B</div><div className="mind-context-copy"><b>Brief</b><span>30-second language-learning app explainer</span></div><i className="mind-context-check" /></div>
                <div className="mind-context-card"><div className="mind-context-ico">N</div><div className="mind-context-copy"><b>Brand</b><span>Identity, voice and visual guidance</span></div><i className="mind-context-check" /></div>
                <div className="mind-context-card"><div className="mind-context-ico">S</div><div className="mind-context-copy"><b>Series</b><span>Continuity preserved across episodes</span></div><i className="mind-context-check" /></div>
                <div className="mind-context-card"><div className="mind-context-ico">↗</div><div className="mind-context-copy"><b>Reference</b><span>Links and uploads become production context</span></div><i className="mind-context-check" /></div>
              </div>
              <div className="mind-core-shell"><div className="mind-core-unit"><span aria-hidden="true" className="nx-presence nx-presence--hero" data-mode="fluid" data-nx-presence="" data-state="listening"><canvas /></span><b>Bam</b><span>resolving the production</span></div><i className="mind-core-arrow" /></div>
              <div className="mind-direction-card"><div className="mind-direction-label">Creative direction</div><h3>Start with the friction. Make the mechanism visible.</h3><div className="mind-direction-meta"><span>Explainer</span><span>30 sec</span><span>All screens</span></div><div className="mind-decision"><label>Opening</label><b>Lead with the problem people already feel.</b></div><div className="mind-decision"><label>Treatment</label><b>Clear staged visuals + typed motion + one dominant visual system.</b></div><div className="mind-decision"><label>Voice</label><b>Confident, direct, no unnecessary performance.</b></div><div className="mind-direction-ready"><i /> Ready for your approval</div></div>
            </div>
          </div>
        </section>
        <section className="pw-final"><div className="pw-final-inner pw-reveal"><div className="pw-kicker"><i /> SceneBam</div><h2>Make something worth watching.</h2><p>Start with the brief. Bam takes it from there, and you see the direction before anything is made.</p><button className="pw-solid" onClick={enter}>Open SceneBam →</button></div></section>
      </main>
      <footer className="pw-footer"><span>© 2026 SceneBam · Meet Bam, your creative director</span><div className="pw-footer-links"><a href="#make">Create</a><a href="#bam">How it works</a><a href="/terms">Terms</a><a href="/privacy">Privacy</a><a href="/faq">FAQ</a></div></footer>
      {signIn && <SignInSheet onClose={() => setSignIn(false)} />}
    </div>
  );
}

function SignInSheet({ onClose }: { onClose: () => void }) {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  async function submit() {
    if (!email.includes("@")) { setError("Enter a valid email."); return; }
    setBusy(true);
    try {
      const res = await fetch("/api/v1/auth/email/request", {
        method: "POST",
        headers: { "content-type": "application/json", "Idempotency-Key": `nx-signin:${crypto.randomUUID()}` },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) throw new Error("The sign-in link couldn't be sent. Try again.");
      setSent(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't send the sign-in link.");
    } finally { setBusy(false); }
  }
  return (
    <div className="overlay open" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="sheet" role="dialog" aria-modal="true">
        <div className="sheet-head"><div><p>Sign in</p><h2>Your Studio is one link away.</h2></div><button aria-label="Close" className="close" onClick={onClose}>×</button></div>
        {sent ? (
          <div className="sent-state"><b>Check your inbox.</b><p>We sent a sign-in link to {email}. It opens your Studio directly.</p></div>
        ) : (
          <>
            <div className="field"><label>Email</label><input autoFocus type="email" value={email} onChange={(e) => setEmail(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") void submit(); }} placeholder="you@company.com" /></div>
            {error && <p className="field-error">{error}</p>}
            <button className="sheet-action" disabled={busy} onClick={() => void submit()}>{busy ? "Sending…" : "Email me a sign-in link"}</button>
            <p className="sheet-legal">By continuing you agree to the <a href="/terms">Terms</a> and <a href="/privacy">Privacy Policy</a>.</p>
          </>
        )}
      </div>
    </div>
  );
}
