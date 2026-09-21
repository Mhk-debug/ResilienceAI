"use client";

/**
 * The landing page's narrative sections.
 *
 * Phase 0 keeps these in one module with reveal-on-scroll only; Phase 1 splits the descent and the
 * shake lab into their own files when they gain real motion (see the plan's file map).
 *
 * Every number rendered here comes from `shake-lab.json`, which is generated from the shipped model
 * bundle by `scripts/generate_shake_lab.py`. Nothing quantitative is typed into this file.
 */

import Link from "next/link";
import { EVIDENCE, FINALE, FOOTER, HOW_IT_WORKS, MYANMAR } from "@/lib/landing/content";
import { useAuth } from "@/lib/auth-context";
import facts from "@/lib/landing/shake-lab.json";
import { useCountUp, useReveal } from "./motion";

function useFacts() {
  const m = facts.model_facts;
  const grouped = m.grouped_cv.monotone;
  return {
    // The labelled survey the model was drawn from — not the train split, which is smaller.
    buildings: m.survey_rows,
    features: m.features,
    crossDistrict: Math.round(grouped.accuracy * 1000) / 10,
    adjacent: Math.round(grouped.adjacent_accuracy * 1000) / 10,
    mae: grouped.mae,
    dataset: m.dataset,
    version: m.model_version,
  };
}

function Stat({ value, suffix, label, decimals }: { value: number; suffix?: string; label: string; decimals?: number }) {
  const { ref, display } = useCountUp<HTMLSpanElement>(decimals ? Number(value.toFixed(decimals)) : value);
  return (
    <div className="reveal rounded-2xl border border-white/10 bg-white/[0.03] p-5">
      <p className="l-mono text-2xl font-semibold text-white md:text-3xl">
        <span ref={ref}>{display}</span>
        {suffix}
      </p>
      <p className="mt-2 text-xs leading-relaxed text-white/55">{label}</p>
    </div>
  );
}

export function Evidence() {
  const f = useFacts();
  const ref = useReveal<HTMLDivElement>();
  return (
    <section className="relative bg-[var(--l-slate)] py-20 md:py-28">
      <div ref={ref} className="mx-auto w-full max-w-6xl px-6 md:px-10">
        <p className="reveal l-mono text-[11px] uppercase tracking-[0.28em] text-[var(--l-haze)]">{EVIDENCE.eyebrow}</p>
        <h2 className="reveal mt-4 max-w-3xl text-[clamp(1.8rem,3.6vw,2.8rem)] font-semibold leading-[1.1] tracking-[-0.02em] text-white" style={{ ["--d" as string]: "60ms" }}>
          {EVIDENCE.title}
        </h2>
        <p className="reveal mt-5 max-w-2xl text-[15px] leading-relaxed text-white/65" style={{ ["--d" as string]: "120ms" }}>
          {EVIDENCE.lede}
        </p>

        <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Stat value={f.buildings} label={EVIDENCE.stats.buildings} />
          <Stat value={f.crossDistrict} suffix="%" decimals={1} label={EVIDENCE.stats.crossDistrict} />
          <Stat value={f.adjacent} suffix="%" decimals={1} label={EVIDENCE.stats.adjacent} />
          <Stat value={f.features} label={EVIDENCE.stats.features} />
        </div>

        <ul className="mt-10 grid gap-4 md:grid-cols-3">
          {EVIDENCE.limitations.map((line, i) => (
            <li key={line} className="reveal rounded-2xl border border-white/10 bg-white/[0.02] p-5 text-sm leading-relaxed text-white/60" style={{ ["--d" as string]: `${i * 80}ms` }}>
              {line}
            </li>
          ))}
        </ul>

        <p className="l-mono mt-6 text-[11px] text-white/35">
          {f.dataset} · {f.version} · MAE {f.mae} grades on unseen districts
        </p>
      </div>
    </section>
  );
}

export function MyanmarSection() {
  const ref = useReveal<HTMLDivElement>();
  return (
    <section className="relative overflow-hidden bg-[linear-gradient(180deg,#121a24_0%,#1c2536_100%)] py-20 md:py-28">
      <div ref={ref} className="relative mx-auto w-full max-w-6xl px-6 md:px-10">
        <p className="reveal l-mono text-[11px] uppercase tracking-[0.28em] text-[var(--l-haze)]">{MYANMAR.eyebrow}</p>
        <h2 className="reveal mt-4 max-w-3xl text-[clamp(1.8rem,3.6vw,2.8rem)] font-semibold leading-[1.1] tracking-[-0.02em] text-white" style={{ ["--d" as string]: "60ms" }}>
          {MYANMAR.title}
        </h2>
        <p className="reveal mt-5 max-w-2xl text-[15px] leading-relaxed text-white/65" style={{ ["--d" as string]: "120ms" }}>
          {MYANMAR.body}
        </p>

        <div className="reveal mt-10 max-w-2xl rounded-2xl border border-white/10 bg-white/[0.03] p-5 md:p-6" style={{ ["--d" as string]: "180ms" }}>
          <p className="l-mono text-[10px] uppercase tracking-[0.2em] text-white/40">{MYANMAR.workedExample.label}</p>
          <p className="mt-3 text-sm font-semibold text-white">{MYANMAR.workedExample.place}</p>
          <p className="mt-1.5 text-sm leading-relaxed text-white/60">{MYANMAR.workedExample.note}</p>
          <Link
            href="/form"
            className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-[var(--l-haze)] underline decoration-[var(--l-haze)]/30 underline-offset-4 transition-colors hover:decoration-[var(--l-haze)]"
          >
            {MYANMAR.workedExample.cta} <span aria-hidden="true">→</span>
          </Link>
        </div>
      </div>
    </section>
  );
}

export function HowItWorks() {
  const ref = useReveal<HTMLDivElement>();
  return (
    <section className="bg-[var(--l-paper)] py-20 text-[var(--l-text)] md:py-24">
      <div ref={ref} className="mx-auto w-full max-w-6xl px-6 md:px-10">
        <p className="reveal l-mono text-[11px] uppercase tracking-[0.28em] text-slate-500">{HOW_IT_WORKS.eyebrow}</p>
        <h2 className="reveal mt-4 text-[clamp(1.7rem,3.2vw,2.5rem)] font-semibold leading-[1.1] tracking-[-0.02em]" style={{ ["--d" as string]: "60ms" }}>
          {HOW_IT_WORKS.title}
        </h2>

        <ol className="mt-12 grid gap-x-8 gap-y-8 sm:grid-cols-2 lg:grid-cols-3">
          {HOW_IT_WORKS.steps.map((s, i) => (
            <li key={s.index} className="reveal border-t border-slate-300/70 pt-5" style={{ ["--d" as string]: `${i * 60}ms` }}>
              <span className="l-mono text-xs text-slate-400">{s.index.padStart(2, "0")}</span>
              <h3 className="mt-2 text-base font-semibold">{s.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-slate-600">{s.body}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

export function Finale() {
  const ref = useReveal<HTMLDivElement>();
  return (
    <section className="relative overflow-hidden bg-[linear-gradient(180deg,#151a20_0%,#0b1524_100%)] py-24 md:py-32">
      <div ref={ref} className="mx-auto w-full max-w-4xl px-6 text-center md:px-10">
        <h2 className="reveal text-[clamp(1.9rem,4.2vw,3rem)] font-semibold leading-[1.08] tracking-[-0.02em] text-white">
          {FINALE.title}
        </h2>
        <p className="reveal mx-auto mt-5 max-w-2xl text-[15px] leading-relaxed text-white/65" style={{ ["--d" as string]: "80ms" }}>
          {FINALE.body}
        </p>
        <div className="reveal mt-9 flex flex-wrap items-center justify-center gap-3" style={{ ["--d" as string]: "140ms" }}>
          <Link
            href={FINALE.primaryCta.href}
            className="inline-flex items-center gap-2 rounded-full bg-[var(--l-haze)] px-6 py-3 text-sm font-semibold text-[var(--l-ink)] transition-transform duration-200 hover:-translate-y-0.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
          >
            {FINALE.primaryCta.label}
          </Link>
          <FinaleSecondaryCta />
        </div>
      </div>
    </section>
  );
}

/**
 * The second call to action depends on who is reading: a signed-out visitor has no saved
 * assessments, so offering to browse them would just bounce them to `/login`. The default target
 * (also what a no-JS visitor gets) is the saved list.
 */
function FinaleSecondaryCta() {
  const { isAuthenticated, isLoading } = useAuth();
  const target = !isLoading && !isAuthenticated ? FINALE.signUpCta : FINALE.secondaryCta;

  return (
    <Link
      href={target.href}
      className="inline-flex items-center gap-2 rounded-full border border-white/20 px-6 py-3 text-sm font-semibold text-white/85 transition-colors duration-200 hover:border-white/40 hover:text-white"
    >
      {target.label}
    </Link>
  );
}

export function LandingFooter() {
  return (
    <footer className="border-t border-white/10 bg-[var(--l-ink)] py-12">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 md:flex-row md:items-start md:justify-between md:px-10">
        <div>
          <p className="l-mono text-[11px] uppercase tracking-[0.24em] text-white/45">{FOOTER.wordmark}</p>
          <p className="mt-2 max-w-sm text-sm text-white/60">{FOOTER.line}</p>
        </div>
        <ul className="max-w-md space-y-1.5">
          {FOOTER.credits.map((line) => (
            <li key={line} className="text-[11px] leading-relaxed text-white/35">
              {line}
            </li>
          ))}
        </ul>
      </div>
    </footer>
  );
}
