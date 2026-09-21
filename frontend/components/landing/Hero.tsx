"use client";

/**
 * Landing hero: layered parallax city over strata, with the seismograph trace that draws itself.
 *
 * Every moving part is a `data-parallax` layer driven by the single director in motion.ts. The
 * artwork is hand-authored SVG/DOM — no images, no WebGL — so it stays crisp at any DPR, works
 * offline, and costs nothing at LCP.
 */

import Link from "next/link";
import { useEffect, useState } from "react";
import { HERO } from "@/lib/landing/content";
import { useParallax, useReveal } from "./motion";

/** Skyline blocks: [x, width, height] in a 1000×420 viewBox. Two rows so the city has depth. */
const FAR_SKYLINE: Array<[number, number, number]> = [
  [0, 46, 120], [52, 30, 168], [88, 54, 96], [148, 38, 210], [192, 44, 140],
  [242, 26, 250], [274, 60, 118], [340, 34, 186], [380, 48, 150], [434, 30, 214],
  [470, 62, 104], [538, 40, 176], [584, 28, 232], [618, 56, 128], [680, 36, 196],
  [722, 50, 142], [778, 32, 224], [816, 58, 110], [880, 42, 182], [928, 30, 156],
  [964, 36, 204],
];

const NEAR_SKYLINE: Array<[number, number, number]> = [
  [-10, 70, 96], [66, 52, 150], [124, 40, 74], [170, 66, 118],
  [300, 58, 168], [364, 44, 92], [412, 72, 134], [560, 46, 156],
  [616, 68, 88], [700, 50, 176], [756, 74, 122], [860, 48, 148],
  [914, 62, 100],
];

/** The trace: a flat line with one escalating event, then decay. Rendered as one polyline. */
const TRACE_PATH =
  "M0 60 L120 60 L138 58 L152 62 L168 59 L300 60 L318 55 L332 64 L352 58 " +
  "L420 60 L438 52 L450 68 L462 40 L474 84 L488 26 L500 96 L512 34 L524 88 " +
  "L538 46 L552 70 L566 54 L582 62 L600 58 L700 60 L718 57 L734 61 L760 60 " +
  "L1000 60";

function ResumeCard() {
  const [target, setTarget] = useState<string | null>(null);

  useEffect(() => {
    // Anonymous visitors get the same resume affordance as signed-in ones; the id is what the
    // app has always stored in localStorage for this purpose.
    try {
      const id = window.localStorage.getItem("latestAssessmentId");
      if (id) setTarget(`/dashboard/${id}`);
    } catch {
      /* private mode: no resume card */
    }
  }, []);

  if (!target) return null;

  return (
    <div className="reveal is-in mt-10 flex w-full max-w-xl flex-col gap-3 rounded-2xl border border-white/12 bg-white/[0.04] p-4 backdrop-blur-sm sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="text-sm font-semibold text-white/90">{HERO.resume.title}</p>
        <p className="mt-0.5 text-xs text-white/55">{HERO.resume.body}</p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <Link
          href={target}
          className="rounded-full bg-white px-4 py-2 text-xs font-semibold text-[var(--l-ink)] transition-transform duration-200 hover:-translate-y-0.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--l-haze)]"
        >
          {HERO.resume.cta}
        </Link>
        <Link
          href="/form"
          className="rounded-full px-3 py-2 text-xs font-semibold text-white/70 underline decoration-white/25 underline-offset-4 transition-colors hover:text-white"
        >
          {HERO.resume.fresh}
        </Link>
      </div>
    </div>
  );
}

export default function Hero() {
  const contentRef = useReveal<HTMLDivElement>();
  const cueRef = useReveal<HTMLDivElement>("0px");
  const traceRef = useReveal<SVGSVGElement>("0px");
  const hazeRef = useParallax<HTMLDivElement>(6, { disabled: false });
  const farRef = useParallax<HTMLDivElement>(18, { pointer: 10, idle: 3 });
  const nearRef = useParallax<HTMLDivElement>(34, { pointer: 18, idle: 5 });
  const groundRef = useParallax<HTMLDivElement>(54, { pointer: 6 });

  return (
    <section
      aria-label="ResilienceAI"
      className="l-vignette relative isolate flex min-h-[100svh] flex-col justify-end overflow-hidden bg-[linear-gradient(180deg,#070d18_0%,#0d1a2e_45%,#1b2b45_74%,#2a2118_74.5%,#3a2d20_100%)]"
    >
      {/* Haze band — the low sky the city sits in */}
      <div ref={hazeRef} data-parallax className="pointer-events-none absolute inset-x-0 bottom-[26%] h-[46vh]">
        <div className="absolute inset-0 bg-[radial-gradient(60%_100%_at_50%_100%,rgba(127,179,232,0.20),transparent_70%)]" />
      </div>

      {/* Far skyline */}
      <div ref={farRef} data-parallax className="pointer-events-none absolute inset-x-0 bottom-[26%] h-[38vh]">
        <svg viewBox="0 0 1000 420" preserveAspectRatio="xMidYMax slice" className="h-full w-full" aria-hidden="true">
          <g fill="#16263e" opacity="0.9">
            {FAR_SKYLINE.map(([x, w, h], i) => (
              <rect key={i} x={x} y={420 - h} width={w} height={h} rx={1.5} />
            ))}
          </g>
          {/* lit windows, sparse — enough to read as a city at night */}
          <g fill="#7fb3e8" opacity="0.5">
            {FAR_SKYLINE.flatMap(([x, w, h], i) =>
              Array.from({ length: Math.max(1, Math.floor(h / 70)) }, (_, j) => (
                <rect key={`${i}-${j}`} x={x + 6 + (j % 2) * 14} y={420 - h + 12 + j * 34} width={5} height={7} rx={1} />
              )),
            )}
          </g>
        </svg>
      </div>

      {/* Near skyline — darker, larger, moves most */}
      <div ref={nearRef} data-parallax className="pointer-events-none absolute inset-x-0 bottom-[26%] h-[30vh]">
        <svg viewBox="0 0 1000 420" preserveAspectRatio="xMidYMax slice" className="h-full w-full" aria-hidden="true">
          <g fill="#0d1a2c">
            {NEAR_SKYLINE.map(([x, w, h], i) => (
              <rect key={i} x={x} y={420 - h} width={w} height={h} rx={2} />
            ))}
          </g>
          <g fill="#a9cdf0" opacity="0.35">
            {NEAR_SKYLINE.flatMap(([x, w, h], i) =>
              Array.from({ length: Math.max(1, Math.floor(h / 56)) }, (_, j) => (
                <rect key={`n-${i}-${j}`} x={x + Math.round(w * 0.3)} y={420 - h + 10 + j * 26} width={4} height={6} rx={1} />
              )),
            )}
          </g>
        </svg>
      </div>

      {/* Ground line + strata bands */}
      <div ref={groundRef} data-parallax className="pointer-events-none absolute inset-x-0 bottom-0 h-[26vh]">
        <div className="absolute inset-x-0 top-0 h-px bg-[linear-gradient(90deg,transparent,rgba(127,179,232,0.55),transparent)]" />
        <div className="absolute inset-x-0 top-0 h-[34%] bg-[#241c14]" />
        <div className="absolute inset-x-0 top-[34%] h-[30%] bg-[#2c2318]" />
        <div className="absolute inset-x-0 top-[64%] h-[36%] bg-[#1c1610]" />
        {/* sediment lines — enough texture to read as rock rather than a flat band */}
        <svg viewBox="0 0 1000 100" preserveAspectRatio="none" className="absolute inset-0 h-full w-full" aria-hidden="true">
          <g stroke="rgba(255,255,255,0.055)" strokeWidth="1">
            <path d="M0 12 H1000" />
            <path d="M0 27 H1000" />
            <path d="M0 48 H1000" />
            <path d="M0 61 H1000" />
            <path d="M0 79 H1000" />
            <path d="M0 92 H1000" />
          </g>
          {/* a fault cutting through the strata, with a strand that steps as it descends */}
          <path d="M604 0 L588 26 L612 52 L596 78 L620 100" fill="none" stroke="rgba(239,68,68,0.5)" strokeWidth="1.6" />
          <path d="M624 0 L640 22 L628 44 L646 68 L636 100" fill="none" stroke="rgba(239,68,68,0.22)" strokeWidth="1.1" />
        </svg>
      </div>

      {/* The seismograph trace sits on the horizon line, clear of the call to action above it */}
      <div className="pointer-events-none absolute inset-x-0 bottom-[22%] h-[9vh] px-6 md:px-16">
        <svg
          ref={traceRef}
          className="l-trace h-full w-full"
          viewBox="0 0 1000 120"
          preserveAspectRatio="none"
          role="img"
          aria-label={HERO.trace.label}
          style={{ ["--trace-len" as string]: "2600" }}
        >
          <path d={TRACE_PATH} fill="none" stroke="rgba(190,222,255,0.75)" strokeWidth="1.6" strokeLinejoin="round" />
        </svg>
      </div>

      {/* Content — sits on the night side of the horizon, so the copy never crosses the strata */}
      <div ref={contentRef} className="relative z-10 mx-auto w-full max-w-6xl px-6 pb-[32vh] pt-[20vh] md:px-10">
        <p className="reveal l-mono text-[11px] uppercase tracking-[0.28em] text-[var(--l-haze)]" style={{ ["--d" as string]: "80ms" }}>
          {HERO.eyebrow}
        </p>

        <h1 className="mt-6 max-w-4xl text-[clamp(2.4rem,6.4vw,4.6rem)] font-semibold leading-[1.02] tracking-[-0.03em] text-white">
          {HERO.headline.map((line, i) => (
            <span key={line} className="reveal-line" style={{ ["--d" as string]: `${180 + i * 120}ms` }}>
              <span>{line}</span>
            </span>
          ))}
        </h1>

        <p
          className="reveal mt-7 max-w-2xl text-[15px] leading-relaxed text-white/68 md:text-base"
          style={{ ["--d" as string]: "460ms" }}
        >
          {HERO.lede}
        </p>

        <div className="reveal mt-9 flex flex-wrap items-center gap-3" style={{ ["--d" as string]: "560ms" }}>
          <Link
            href={HERO.primaryCta.href}
            className="group inline-flex items-center gap-2 rounded-full bg-[var(--l-haze)] px-6 py-3 text-sm font-semibold text-[var(--l-ink)] transition-transform duration-200 hover:-translate-y-0.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
          >
            {HERO.primaryCta.label}
            <span aria-hidden="true" className="transition-transform duration-200 group-hover:translate-x-0.5">→</span>
          </Link>
          <a
            href={HERO.secondaryCta.href}
            className="inline-flex items-center gap-2 rounded-full border border-white/20 px-6 py-3 text-sm font-semibold text-white/85 transition-colors duration-200 hover:border-white/40 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
          >
            {HERO.secondaryCta.label}
          </a>
        </div>

        <ResumeCard />
      </div>

      {/* Scroll cue */}
      <div ref={cueRef} className="reveal pointer-events-none absolute bottom-6 left-1/2 z-10 -translate-x-1/2 text-center" style={{ ["--d" as string]: "900ms" }}>
        <span className="l-mono text-[10px] uppercase tracking-[0.3em] text-white/50">{HERO.scrollCue}</span>
        <span aria-hidden="true" className="l-drift mx-auto mt-2 block h-6 w-px bg-[linear-gradient(180deg,rgba(255,255,255,0.5),transparent)]" />
      </div>
    </section>
  );
}
