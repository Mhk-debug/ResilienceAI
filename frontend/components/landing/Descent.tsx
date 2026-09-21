"use client";

/**
 * The descent: what the engine measures, revealed as strata.
 *
 * Scroll drives which horizon is active. Two rules this file obeys:
 *
 *  - No `transform` is ever applied to a sticky ancestor (that silently breaks pinning), so the
 *    parallax writes go to a background layer *inside* the panel.
 *  - The pinned behaviour exists only under `html.js-motion` + `prefers-reduced-motion:
 *    no-preference` (see globals.css). Without JS, and for anyone who asks for less motion, the
 *    same five horizons render as a plain, fully legible list.
 */

import { useCallback, useRef, useState } from "react";
import { DESCENT } from "@/lib/landing/content";
import { useElementProgress, useReveal } from "./motion";

const HORIZONS = DESCENT.horizons;

export default function Descent() {
  const [active, setActive] = useState(0);
  const activeRef = useRef(0);
  const strataRef = useRef<HTMLDivElement | null>(null);
  const headRef = useReveal<HTMLDivElement>();

  const onProgress = useCallback((progress: number) => {
    // Drive the strata layer imperatively — a per-frame style write, never a React render.
    if (strataRef.current) {
      strataRef.current.style.transform = `translate3d(0, ${(-progress * 26).toFixed(2)}%, 0)`;
    }
    // React state only when the horizon actually changes (≤5 renders for a full pass).
    const next = Math.min(HORIZONS.length - 1, Math.floor(progress * HORIZONS.length * 1.04));
    if (next !== activeRef.current) {
      activeRef.current = next;
      setActive(next);
    }
  }, []);

  const scrollerRef = useElementProgress<HTMLDivElement>(onProgress);

  return (
    <section id="descent" className="l-descent relative bg-[linear-gradient(180deg,#241c14_0%,#2a2118_40%,#151a20_100%)] py-20 md:py-24">
      <div ref={scrollerRef} className="l-descent-scroller">
        <div className="l-descent-panel">
          {/* Strata that drift as you descend — inside the pinned panel, never transforming it */}
          <div aria-hidden="true" className="pointer-events-none absolute inset-0 overflow-hidden">
            <div ref={strataRef} className="absolute inset-x-0 -top-[13%] h-[126%] opacity-70">
              <div className="absolute inset-x-0 top-0 h-px bg-[linear-gradient(90deg,transparent,rgba(127,179,232,0.35),transparent)]" />
              <div className="absolute inset-x-0 top-[18%] h-px bg-white/[0.045]" />
              <div className="absolute inset-x-0 top-[42%] h-px bg-white/[0.04]" />
              <div className="absolute inset-x-0 top-[67%] h-px bg-white/[0.045]" />
              <div className="absolute inset-x-0 top-[86%] h-px bg-white/[0.035]" />
            </div>
          </div>

          <div className="relative mx-auto w-full max-w-6xl px-6 md:px-10">
            <div ref={headRef} className="reveal">
              <p className="l-mono text-[11px] uppercase tracking-[0.28em] text-[var(--l-haze)]">{DESCENT.eyebrow}</p>
              <h2 className="mt-4 max-w-3xl text-[clamp(1.8rem,3.6vw,2.8rem)] font-semibold leading-[1.1] tracking-[-0.02em] text-white">
                {DESCENT.title}
              </h2>
              <p className="mt-5 max-w-2xl text-[15px] leading-relaxed text-white/65">{DESCENT.lede}</p>
            </div>

            <div className="l-descent-stage mt-12 grid gap-8 md:grid-cols-[auto_minmax(0,1fr)] md:gap-12">
              {/* Depth ruler — dots only, one per horizon */}
              <div aria-hidden="true" className="l-descent-ruler hidden md:block">
                <ol className="flex flex-col gap-0">
                  {HORIZONS.map((h, i) => (
                    <li key={h.id} className="flex items-center gap-3">
                      <span
                        className={`l-mono text-[10px] transition-colors duration-500 ${
                          i === active ? "text-[var(--l-haze)]" : "text-white/25"
                        }`}
                      >
                        {h.depth}
                      </span>
                      <span
                        className={`block h-1.5 w-1.5 rounded-full transition-all duration-500 ${
                          i === active ? "scale-150 bg-[var(--l-haze)]" : "bg-white/20"
                        }`}
                      />
                    </li>
                  ))}
                </ol>
                <span className="mt-3 block h-24 w-px bg-[linear-gradient(180deg,rgba(255,255,255,0.28),transparent)]" />
              </div>

              <ol className="l-descent-list space-y-3">
                {HORIZONS.map((h, i) => {
                  const isActive = i === active;
                  return (
                    <li
                      key={h.id}
                      className={`l-horizon grid gap-4 rounded-2xl border p-5 transition-colors duration-500 md:grid-cols-[auto_1fr_auto] md:items-baseline md:gap-8 md:p-6 ${
                        isActive
                          ? "is-active border-[var(--l-haze)]/35 bg-[linear-gradient(90deg,rgba(127,179,232,0.10),rgba(255,255,255,0.015))]"
                          : "border-white/10 bg-[linear-gradient(90deg,rgba(255,255,255,0.04),rgba(255,255,255,0.008))]"
                      }`}
                    >
                      <span className="l-mono text-xs text-[var(--l-haze)]/80">{h.index}</span>
                      <div>
                        <h3 className="text-lg font-semibold text-white">{h.title}</h3>
                        <p className="mt-1.5 max-w-2xl text-sm leading-relaxed text-white/60">{h.body}</p>
                      </div>
                      <div className="text-left md:text-right">
                        <span className="l-mono block text-xs text-white/70">{h.depth}</span>
                        <span className="l-mono mt-1 block text-[10px] uppercase tracking-[0.16em] text-white/35">
                          {h.source}
                        </span>
                      </div>
                    </li>
                  );
                })}
              </ol>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
