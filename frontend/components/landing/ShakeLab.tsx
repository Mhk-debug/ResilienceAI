"use client";

/**
 * The shake lab.
 *
 * Two panels, because there are two genuinely different computations behind them and the page says
 * so rather than pretending otherwise:
 *
 *   magnitude + distance → the hazard engine's own attenuation relation → PGA / MMI
 *   distance             → the shipped damage model → the five-grade distribution
 *
 * The damage model's only site term is epicentral distance to the governing event; magnitude never
 * enters it. A single panel driven by both controls would have to fake that response, so the lab
 * shows the real split instead. Both tables come from `shake-lab.json`, generated from the shipped
 * bundle by `scripts/generate_shake_lab.py` — no number here is typed by hand.
 */

import { useId, useMemo, useState } from "react";
import data from "@/lib/landing/shake-lab.json";
import { SHAKE_LAB } from "@/lib/landing/content";
import BuildingFigure, { type ArchetypeKey } from "./BuildingFigure";
import { useReveal } from "./motion";

const ARCHETYPES = Object.keys(data.archetypes) as ArchetypeKey[];
const MAGNITUDES = data.magnitudes as number[];
const DISTANCES = data.distances_km as number[];

/** MMI is drawn on a fixed axis so the marker's position is comparable between settings. */
const MMI_AXIS = { min: 4, max: 9 };
const MMI_TICKS: Array<[number, string]> = [
  [5, "V"],
  [6, "VI"],
  [7, "VII"],
  [8, "VIII"],
  [9, "IX"],
];

const GRADE_KEYS = ["grade1", "grade2", "grade3", "grade4", "grade5"] as const;
const GRADE_LABELS = ["Grade 1 · no damage", "Grade 2 · slight", "Grade 3 · moderate", "Grade 4 · heavy", "Grade 5 · destruction"];

function ArchetypeGlyph({ icon }: { icon: string }) {
  const common = { fill: "none", stroke: "currentColor", strokeWidth: 1.4, strokeLinejoin: "round" as const };
  return (
    <svg viewBox="0 0 32 28" className="h-7 w-8" aria-hidden="true">
      {icon === "stone" && (
        <g {...common}>
          <path d="M3 24h26" />
          <path d="M6 24V16h7v8M15 24V13h7v11M24 24V18h5v6" />
          <path d="M7 16l3-3 3 3M16 13l3-3 3 3" />
        </g>
      )}
      {icon === "brick" && (
        <g {...common}>
          <path d="M4 24h24" />
          <path d="M6 24V6h20v18z" />
          <path d="M6 12h20M6 18h20M16 6v6M11 12v6M21 12v6M16 18v6" />
        </g>
      )}
      {icon === "timber" && (
        <g {...common}>
          <path d="M2 25l9-6h19" />
          <path d="M8 21v-9h6v9M18 19v-8h6v8" />
          <path d="M8 12l3-3 3 3M18 11l3-3 3 3" />
        </g>
      )}
      {icon === "rc" && (
        <g {...common}>
          <path d="M4 24h24" />
          <path d="M7 24V5M16 24V5M25 24V5" />
          <path d="M7 9h18M7 15h18M7 21h18" />
        </g>
      )}
    </svg>
  );
}

function pct(value: number): number {
  return Math.round(value * 1000) / 10;
}

export default function ShakeLab() {
  const [archetype, setArchetype] = useState<ArchetypeKey>("mud_stone");
  const [distanceIdx, setDistanceIdx] = useState(2); // 25 km
  const [magnitudeIdx, setMagnitudeIdx] = useState(4); // M7.0
  const [expanded, setExpanded] = useState(false);
  // The building sways continuously, so the plan's pause control is real: it stops the ambient
  // motion without touching the layout or the numbers.
  const [paused, setPaused] = useState(false);
  const resultId = useId();
  // `.reveal` only becomes visible once an observed ancestor carries `is-in` — without this ref the
  // section's own heading stays at opacity 0 forever.
  const headRef = useReveal<HTMLDivElement>();

  const distance = DISTANCES[distanceIdx];
  const magnitude = MAGNITUDES[magnitudeIdx];

  const hazard = useMemo(
    () => data.hazard_by_magnitude_distance.find((r) => r.magnitude === magnitude && r.distance_km === distance),
    [magnitude, distance],
  );
  const damage = useMemo(
    () => data.damage_by_archetype_distance.find((r) => r.archetype === archetype && r.distance_km === distance),
    [archetype, distance],
  );

  if (!hazard || !damage) return null;

  const probs = damage.probabilities as Record<string, number>;
  const mmiPosition = ((hazard.mmi - MMI_AXIS.min) / (MMI_AXIS.max - MMI_AXIS.min)) * 100;
  const meta = data.archetypes[archetype];

  return (
    <section
      id="shake-lab"
      data-archetype={archetype}
      data-distance-km={distance}
      data-magnitude={magnitude}
      data-expected-grade={damage.expected_grade}
      data-p-severe={damage.p_severe_grade45}
      data-pga-g={hazard.pga_g}
      data-mmi={hazard.mmi}
      className={`relative overflow-hidden bg-[linear-gradient(180deg,#121a24_0%,#0d1520_100%)] py-20 md:py-28 ${paused ? "l-paused" : ""}`}
    >
      <div className="mx-auto w-full max-w-6xl px-6 md:px-10">
        <div ref={headRef}>
          <p className="reveal l-mono text-[11px] uppercase tracking-[0.28em] text-[var(--l-haze)]">{SHAKE_LAB.eyebrow}</p>
          <h2 className="reveal mt-4 max-w-3xl text-[clamp(1.8rem,3.6vw,2.8rem)] font-semibold leading-[1.1] tracking-[-0.02em] text-white" style={{ ["--d" as string]: "60ms" }}>
            {SHAKE_LAB.title}
          </h2>
          <p className="reveal mt-5 max-w-2xl text-[15px] leading-relaxed text-white/65" style={{ ["--d" as string]: "120ms" }}>
            {SHAKE_LAB.lede}
          </p>
        </div>

        <div className="mt-12 grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)]">
          {/* ── Controls ─────────────────────────────────────────────────────────────── */}
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 md:p-6">
            <fieldset>
              <legend className="l-mono text-[10px] uppercase tracking-[0.2em] text-white/45">
                {SHAKE_LAB.controls.archetype}
              </legend>
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                {ARCHETYPES.map((key) => {
                  const active = key === archetype;
                  return (
                    <button
                      key={key}
                      type="button"
                      aria-pressed={active}
                      onClick={() => setArchetype(key)}
                      className={`flex items-start gap-3 rounded-xl border p-3 text-left transition-colors ${
                        active
                          ? "border-[var(--l-haze)]/70 bg-[var(--l-haze)]/10 text-white"
                          : "border-white/10 text-white/70 hover:border-white/25 hover:text-white"
                      }`}
                    >
                      <span className={active ? "text-[var(--l-haze)]" : "text-white/45"}>
                        <ArchetypeGlyph icon={data.archetypes[key].icon} />
                      </span>
                      <span className="text-[13px] font-medium leading-snug">{data.archetypes[key].label}</span>
                    </button>
                  );
                })}
              </div>
              <p className="mt-3 text-xs leading-relaxed text-white/45">{meta.blurb}</p>
            </fieldset>

            <div className="mt-7">
              <label htmlFor={`${resultId}-distance`} className="l-mono flex items-baseline justify-between text-[10px] uppercase tracking-[0.2em] text-white/45">
                <span>{SHAKE_LAB.controls.distance}</span>
                <span className="l-mono text-sm normal-case tracking-normal text-white">{distance} km</span>
              </label>
              <input
                id={`${resultId}-distance`}
                type="range"
                min={0}
                max={DISTANCES.length - 1}
                step={1}
                value={distanceIdx}
                onChange={(event) => setDistanceIdx(Number(event.target.value))}
                aria-valuetext={`${distance} kilometres from the fault`}
                className="l-range mt-3 w-full"
              />
              <div className="l-mono mt-1.5 flex justify-between text-[10px] text-white/35">
                {DISTANCES.map((d) => (
                  <span key={d}>{d}</span>
                ))}
              </div>
            </div>

            <div className="mt-6">
              <label htmlFor={`${resultId}-magnitude`} className="l-mono flex items-baseline justify-between text-[10px] uppercase tracking-[0.2em] text-white/45">
                <span>{SHAKE_LAB.controls.magnitude}</span>
                <span className="l-mono text-sm normal-case tracking-normal text-white">M{magnitude.toFixed(1)}</span>
              </label>
              <input
                id={`${resultId}-magnitude`}
                type="range"
                min={0}
                max={MAGNITUDES.length - 1}
                step={1}
                value={magnitudeIdx}
                onChange={(event) => setMagnitudeIdx(Number(event.target.value))}
                aria-valuetext={`magnitude ${magnitude.toFixed(1)}`}
                className="l-range mt-3 w-full"
              />
              <div className="l-mono mt-1.5 flex justify-between text-[10px] text-white/35">
                {MAGNITUDES.map((m) => (
                  <span key={m}>{m.toFixed(1)}</span>
                ))}
              </div>
            </div>

            <button
              type="button"
              aria-pressed={paused}
              onClick={() => setPaused((v) => !v)}
              className="l-mono mt-7 inline-flex items-center gap-2 rounded-full border border-white/15 px-3.5 py-1.5 text-[11px] uppercase tracking-[0.14em] text-white/60 transition-colors hover:border-white/35 hover:text-white/90"
            >
              <span aria-hidden="true" className={`block h-1.5 w-1.5 rounded-full ${paused ? "bg-white/40" : "bg-[var(--l-haze)]"}`} />
              {paused ? SHAKE_LAB.controls.resume : SHAKE_LAB.controls.pause}
            </button>
          </div>

          {/* ── Results ──────────────────────────────────────────────────────────────── */}
          <div className="grid content-start gap-6">
            {/* The shaking */}
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 md:p-6">
              <p className="l-mono text-[10px] uppercase tracking-[0.2em] text-white/45">{SHAKE_LAB.panels.hazard}</p>
              <div className="mt-4 flex items-end gap-6">
                <div>
                  <p className="l-mono text-3xl font-semibold text-white">{hazard.pga_g.toFixed(3)}<span className="ml-1 text-base font-normal text-white/50">g</span></p>
                  <p className="l-mono mt-1 text-[10px] uppercase tracking-[0.16em] text-white/35">Peak ground acceleration</p>
                </div>
                <div>
                  <p className="l-mono text-3xl font-semibold text-white">{hazard.mmi.toFixed(1)}</p>
                  <p className="l-mono mt-1 text-[10px] uppercase tracking-[0.16em] text-white/35">MMI intensity</p>
                </div>
              </div>
              <div className="mt-5">
                <div className="l-mmi relative h-2 rounded-full">
                  <span
                    className="l-mmi-marker absolute top-1/2 h-4 w-1 -translate-y-1/2 rounded-full bg-white shadow-[0_0_0_3px_rgba(11,21,36,0.9)]"
                    style={{ left: `${Math.min(100, Math.max(0, mmiPosition))}%` }}
                  />
                </div>
                <div className="l-mono mt-1.5 flex justify-between text-[10px] text-white/35">
                  {MMI_TICKS.map(([value, label]) => (
                    <span key={value}>{label}</span>
                  ))}
                </div>
              </div>
            </div>

            {/* The damage */}
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 md:p-6">
              <p className="l-mono text-[10px] uppercase tracking-[0.2em] text-white/45">{SHAKE_LAB.panels.damage}</p>

              {/* The building first, then what the model predicts for it — one story, not two widgets */}
              <div className="mt-4 grid gap-5 sm:grid-cols-[minmax(0,170px)_minmax(0,1fr)] sm:items-center">
                <BuildingFigure archetype={archetype} grade={damage.expected_grade} paused={paused} />

                <div className="flex items-end gap-6">
                  <div>
                    <p className="l-mono text-3xl font-semibold text-white">{damage.expected_grade.toFixed(2)}</p>
                    <p className="l-mono mt-1 text-[10px] uppercase tracking-[0.16em] text-white/35">Expected damage grade</p>
                  </div>
                  <div>
                    <p className={`l-mono text-3xl font-semibold ${damage.p_severe_grade45 >= 0.5 ? "text-[var(--l-risk-5)]" : damage.p_severe_grade45 >= 0.2 ? "text-[var(--l-risk-3)]" : "text-[var(--l-risk-1)]"}`}>
                      {pct(damage.p_severe_grade45)}<span className="ml-0.5 text-base font-normal text-white/50">%</span>
                    </p>
                    <p className="l-mono mt-1 text-[10px] uppercase tracking-[0.16em] text-white/35">Chance of grade 4–5</p>
                  </div>
                </div>
              </div>

              <div className="mt-5 flex h-3 w-full overflow-hidden rounded-full bg-white/5">
                {GRADE_KEYS.map((key, i) => (
                  <span
                    key={key}
                    className="l-grade-seg block h-full"
                    style={{
                      width: `${pct(probs[key])}%`,
                      background: `var(--l-risk-${i + 1})`,
                    }}
                    title={`${GRADE_LABELS[i]} — ${pct(probs[key])}%`}
                  />
                ))}
              </div>

              <button
                type="button"
                onClick={() => setExpanded((v) => !v)}
                aria-expanded={expanded}
                aria-controls={`${resultId}-detail`}
                className="l-mono mt-3 text-[11px] uppercase tracking-[0.14em] text-white/45 transition-colors hover:text-white/80"
              >
                {expanded ? "Hide grade detail" : "Show grade detail"}
              </button>

              {expanded && (
                <dl id={`${resultId}-detail`} className="mt-3 space-y-2">
                  {GRADE_KEYS.map((key, i) => (
                    <div key={key} className="flex items-center gap-3">
                      <dt className="l-mono w-40 shrink-0 text-[11px] text-white/55">{GRADE_LABELS[i]}</dt>
                      <dd className="flex flex-1 items-center gap-3">
                        <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/5">
                          <span className="l-grade-seg block h-full" style={{ width: `${pct(probs[key])}%`, background: `var(--l-risk-${i + 1})` }} />
                        </span>
                        <span className="l-mono w-12 text-right text-[11px] text-white/70">{pct(probs[key])}%</span>
                      </dd>
                    </div>
                  ))}
                </dl>
              )}

              {damage.flags.length > 0 && (
                <p className="mt-3 text-[11px] italic leading-relaxed text-white/40">{damage.flags.join(" · ")}</p>
              )}
            </div>
          </div>
        </div>

        {/* Screen-reader summary of the current state — the visual panels are decorative to AT. */}
        <p aria-live="polite" className="sr-only">
          Magnitude {magnitude.toFixed(1)} at {distance} kilometres: peak ground acceleration{" "}
          {hazard.pga_g.toFixed(2)} g, intensity {hazard.mmi.toFixed(1)}. For {meta.label}: expected damage
          grade {damage.expected_grade.toFixed(2)}, {pct(damage.p_severe_grade45)} percent chance of grade 4 or 5.
        </p>

        <div className="mt-8 flex flex-col gap-4 rounded-2xl border border-white/10 bg-white/[0.02] p-5 md:flex-row md:items-center md:justify-between">
          <p className="max-w-2xl text-xs leading-relaxed text-white/50">{SHAKE_LAB.caveat}</p>
          <a
            href="/form"
            className="inline-flex shrink-0 items-center gap-2 rounded-full bg-[var(--l-haze)] px-5 py-2.5 text-sm font-semibold text-[var(--l-ink)] transition-transform duration-200 hover:-translate-y-0.5"
          >
            {SHAKE_LAB.cta} <span aria-hidden="true">→</span>
          </a>
        </div>
      </div>
    </section>
  );
}
