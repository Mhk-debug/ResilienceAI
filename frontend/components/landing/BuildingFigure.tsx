"use client";

/**
 * The building, and what the shaking does to it.
 *
 * Damage state is derived from the model's expected grade — state 1 is intact, state 5 is partial
 * collapse — and every layer is always in the DOM with its opacity driven by the state, so the
 * degradation cross-fades instead of popping. Geometry is per archetype because a four-storey RC
 * frame and a single-storey bamboo house do not fail the same way: the frame drifts and spalls, the
 * masonry cracks through the joints, the light timber house racks and sheds its roof.
 *
 * Decorative in the honest sense: it illustrates the model's *output*. It is not a structural
 * simulation and the caption says so.
 */

import data from "@/lib/landing/shake-lab.json";

export type ArchetypeKey = keyof typeof data.archetypes;

const DAMAGE_STATES = [
  { state: 1, name: "No damage" },
  { state: 2, name: "Slight damage" },
  { state: 3, name: "Moderate damage" },
  { state: 4, name: "Heavy damage" },
  { state: 5, name: "Partial collapse" },
] as const;

interface Box {
  x0: number;
  x1: number;
  yTop: number;
  yBase: number;
  floors: number;
  roof: "pitched" | "flat" | "light";
}

/** Facade footprint per archetype, in a 200×170 viewBox with the ground at y = 150. */
const GEOMETRY: Record<ArchetypeKey, Box> = {
  mud_stone: { x0: 66, x1: 134, yTop: 58, yBase: 150, floors: 3, roof: "pitched" },
  brick_cement: { x0: 50, x1: 150, yTop: 78, yBase: 150, floors: 2, roof: "flat" },
  timber_bamboo: { x0: 60, x1: 140, yTop: 104, yBase: 150, floors: 1, roof: "light" },
  engineered_rc: { x0: 62, x1: 138, yTop: 40, yBase: 150, floors: 4, roof: "flat" },
};

const FACADE: Record<ArchetypeKey, { fill: string; stroke: string }> = {
  mud_stone: { fill: "#4a4038", stroke: "#6d6055" },
  brick_cement: { fill: "#5a4034", stroke: "#7d5a48" },
  timber_bamboo: { fill: "#4c4636", stroke: "#6f6750" },
  engineered_rc: { fill: "#3f4854", stroke: "#5f6b7a" },
};

function stateFor(grade: number): number {
  return Math.max(1, Math.min(5, Math.round(grade)));
}

export default function BuildingFigure({
  archetype,
  grade,
  paused = false,
}: {
  archetype: ArchetypeKey;
  grade: number;
  paused?: boolean;
}) {
  const box = GEOMETRY[archetype];
  const state = stateFor(grade);
  const facade = FACADE[archetype];
  const label = data.archetypes[archetype].label;
  const stateName = DAMAGE_STATES[state - 1].name;

  const w = box.x1 - box.x0;
  const h = box.yBase - box.yTop;
  const floorH = h / box.floors;
  const mid = (box.x0 + box.x1) / 2;

  /** Crack opacity ramps with the state so the facade degrades continuously, not in steps. */
  const show = (from: number) => (state >= from ? 1 : 0);
  /** Storeys above the base drift laterally once the joint has gone. */
  const drift = state >= 5 ? 7 : state === 4 ? 3.5 : 0;

  return (
    <figure className={`l-building ${paused ? "is-paused" : ""}`}>
      <svg
        viewBox="0 0 200 170"
        className="l-building-svg w-full"
        role="img"
        aria-label={`${label}: ${stateName} — damage state ${state} of 5.`}
      >
        {/* ground + shallow strata */}
        <g aria-hidden="true">
          <path d="M0 150 H200" stroke="rgba(255,255,255,0.22)" strokeWidth="1" />
          <path d="M0 158 H200" stroke="rgba(255,255,255,0.07)" strokeWidth="1" />
          {archetype === "timber_bamboo" && (
            <path d="M0 164 L60 150 H140 L200 160" stroke="rgba(255,255,255,0.12)" strokeWidth="1" fill="none" />
          )}
        </g>

        {/* neighbouring buildings, to show the row-building case */}
        {archetype === "brick_cement" && (
          <g aria-hidden="true" fill="#2f2a26" stroke="#3d3630">
            <rect x={18} y={96} width={32} height={54} />
            <rect x={150} y={88} width={34} height={62} />
          </g>
        )}

        {/* the building itself — the whole mass sways very slowly while motion is allowed */}
        <g className="l-building-mass" aria-hidden="true">
          {/* upper storeys, which is what drifts and collapses */}
          <g style={{ transform: `translateX(${drift}px)`, transition: "transform 700ms cubic-bezier(0.22,0.61,0.36,1)" }}>
            {box.roof === "pitched" && (
              <path
                d={`M${box.x0 - 6} ${box.yTop} L${mid} ${box.yTop - 16} L${box.x1 + 6} ${box.yTop} Z`}
                fill="#33302b"
                stroke={facade.stroke}
                strokeWidth="1.2"
                style={{ opacity: state >= 5 ? 0 : 1, transition: "opacity 600ms linear" }}
              />
            )}
            {box.roof === "light" && (
              <path
                d={`M${box.x0 - 8} ${box.yTop} L${mid} ${box.yTop - 10} L${box.x1 + 8} ${box.yTop} Z`}
                fill="#3a382f"
                stroke={facade.stroke}
                strokeWidth="1"
                style={{ opacity: state >= 5 ? 0.15 : 1, transform: state >= 4 ? "translateY(4px) rotate(-1.2deg)" : "none", transition: "opacity 600ms linear, transform 700ms cubic-bezier(0.22,0.61,0.36,1)", transformOrigin: `${mid}px ${box.yTop}px` }}
              />
            )}
            {box.roof === "flat" && (
              <rect x={box.x0 - 3} y={box.yTop - 5} width={w + 6} height={6} fill="#33302b" stroke={facade.stroke} strokeWidth="1" />
            )}
          </g>

          {/* facade */}
          <rect
            x={box.x0}
            y={box.yTop}
            width={w}
            height={h}
            fill={facade.fill}
            stroke={facade.stroke}
            strokeWidth="1.3"
            style={{
              transform: `skewX(${state >= 4 ? -1.2 : 0}deg)`,
              transition: "transform 700ms cubic-bezier(0.22,0.61,0.36,1)",
              transformOrigin: `${box.x0}px ${box.yBase}px`,
            }}
          />

          {/* floor divisions and openings */}
          <g stroke={facade.stroke} strokeWidth="0.9" fill="none">
            {Array.from({ length: box.floors - 1 }, (_, i) => (
              <path key={i} d={`M${box.x0} ${box.yTop + floorH * (i + 1)} H${box.x1}`} />
            ))}
          </g>
          <g fill="rgba(11,21,36,0.55)" stroke={facade.stroke} strokeWidth="0.7">
            {Array.from({ length: box.floors }, (_, f) =>
              [0, 1].map((c) => (
                <rect
                  key={`${f}-${c}`}
                  x={box.x0 + w * (c === 0 ? 0.2 : 0.58)}
                  y={box.yTop + floorH * f + floorH * 0.28}
                  width={w * 0.22}
                  height={floorH * 0.42}
                  style={{ opacity: state >= 5 && f === box.floors - 1 ? 0 : 1, transition: "opacity 600ms linear" }}
                />
              )),
            )}
          </g>

          {/* bamboo shading for the light frame house */}
          {archetype === "timber_bamboo" && (
            <g stroke="rgba(180,170,120,0.35)" strokeWidth="0.8" fill="none">
              <path d={`M${box.x0} ${box.yBase - 6} H${box.x1}`} />
              <path d={`M${box.x0 + 8} ${box.yTop + 4} V${box.yBase - 6} M${mid} ${box.yTop + 4} V${box.yBase - 6} M${box.x1 - 8} ${box.yTop + 4} V${box.yBase - 6}`} />
            </g>
          )}

          {/* Construction detailing. Without this the four archetypes are the same box at different
              heights, which loses the section's entire argument: a masonry house and an RC frame do
              not fail alike. */}
          <g aria-hidden="true" fill="none" stroke={facade.stroke}>
            {archetype === "mud_stone" && (
              <>
                {/* thick rubble-stone wall with irregular joints */}
                <rect x={box.x0 + 2.5} y={box.yTop + 2.5} width={w - 5} height={h - 5} strokeWidth="0.8" opacity="0.7" />
                <g strokeWidth="0.6" opacity="0.55">
                  <path d={`M${box.x0 + 2.5} ${box.yTop + floorH * 0.5} H${box.x1 - 2.5}`} />
                  <path d={`M${box.x0 + 2.5} ${box.yTop + floorH * 1.5} H${box.x1 - 2.5}`} />
                  <path d={`M${box.x0 + w * 0.35} ${box.yTop + 2.5} V${box.yTop + floorH * 0.5}`} />
                  <path d={`M${box.x0 + w * 0.68} ${box.yTop + floorH * 0.5} V${box.yTop + floorH * 1.5}`} />
                  <path d={`M${box.x0 + w * 0.42} ${box.yTop + floorH * 1.5} V${box.yBase - 2.5}`} />
                </g>
              </>
            )}

            {archetype === "brick_cement" && (
              <>
                {/* regular brick courses */}
                <g strokeWidth="0.55" opacity="0.6">
                  {Array.from({ length: 9 }, (_, i) => (
                    <path key={i} d={`M${box.x0} ${box.yTop + 7 * (i + 1)} H${box.x1}`} />
                  ))}
                </g>
                {/* the shared-wall joints of a row building, and the pounding gap between them */}
                <g strokeWidth="1.1" opacity="0.85" strokeDasharray="3 3">
                  <path d={`M${box.x0 + 1.5} ${box.yTop} V${box.yBase}`} />
                  <path d={`M${box.x1 - 1.5} ${box.yTop} V${box.yBase}`} />
                </g>
              </>
            )}

            {archetype === "engineered_rc" && (
              <>
                {/* column grid and floor beams */}
                <g strokeWidth="1.6" opacity="0.75">
                  <path d={`M${box.x0 + w * 0.25} ${box.yTop} V${box.yBase}`} />
                  <path d={`M${box.x0 + w * 0.75} ${box.yTop} V${box.yBase}`} />
                </g>
                <g strokeWidth="1.9" opacity="0.8">
                  {Array.from({ length: box.floors - 1 }, (_, i) => (
                    <path key={i} d={`M${box.x0} ${box.yTop + floorH * (i + 1)} H${box.x1}`} />
                  ))}
                </g>
              </>
            )}

            {archetype === "timber_bamboo" && (
              <>
                {/* exposed posts, and a roof that simply sits on them */}
                <g strokeWidth="1.5" opacity="0.7">
                  {[0.08, 0.5, 0.92].map((f) => (
                    <path key={f} d={`M${box.x0 + w * f} ${box.yTop + 3} V${box.yBase}`} />
                  ))}
                </g>
              </>
            )}
          </g>

          {/* ── Damage, cross-faded by state ─────────────────────────────────────────────── */}
          <g className="l-cracks" stroke="#e0725f" fill="none" strokeLinecap="round">
            {/* hairline cracks appear first */}
            <path d={`M${box.x0 + w * 0.62} ${box.yBase - 4} l-3 -${floorH * 0.5} l4 -${floorH * 0.4}`} strokeWidth="1" style={{ opacity: show(2), transition: "opacity 500ms linear" }} />
            <path d={`M${box.x0 + w * 0.3} ${box.yTop + floorH * 0.9} l5 -${floorH * 0.4}`} strokeWidth="0.9" style={{ opacity: show(2), transition: "opacity 500ms linear" }} />
            {/* then shear cracking through the joints */}
            <path d={`M${box.x0} ${box.yTop + floorH} l${w * 0.35} ${floorH * 0.55} l-${w * 0.12} ${floorH * 0.6}`} strokeWidth="1.5" style={{ opacity: show(3), transition: "opacity 500ms linear" }} />
            <path d={`M${box.x1} ${box.yTop + floorH * 0.4} l-${w * 0.28} ${floorH * 0.7}`} strokeWidth="1.3" style={{ opacity: show(3), transition: "opacity 500ms linear" }} />
            <path d={`M${box.x0 + w * 0.2} ${box.yBase} l${w * 0.22} -${floorH * 1.1}`} strokeWidth="1.4" style={{ opacity: show(3), transition: "opacity 500ms linear" }} />
            {/* spalling at the corners, then the collapsed top */}
            <path d={`M${box.x0} ${box.yTop + floorH * 0.5} l${w * 0.22} -${floorH * 0.3} l-${w * 0.05} ${floorH * 0.75}`} strokeWidth="2.2" style={{ opacity: show(4), transition: "opacity 500ms linear" }} />
            <path d={`M${box.x1} ${box.yBase - floorH * 0.2} l-${w * 0.2} -${floorH * 0.5} l${w * 0.08} ${floorH * 0.4}`} strokeWidth="2" style={{ opacity: show(5), transition: "opacity 500ms linear" }} />
          </g>

          {/* collapsed top storey, revealed only at state 5 */}
          <g style={{ opacity: state >= 5 ? 1 : 0, transition: "opacity 700ms linear" }} aria-hidden="true">
            <path
              d={`M${box.x0 + 4} ${box.yTop + floorH * 0.55} L${box.x1 - 2} ${box.yTop + floorH * 0.2} L${box.x1} ${box.yTop + floorH * 0.85} L${box.x0 + 8} ${box.yTop + floorH * 1.05} Z`}
              fill="#2b2622"
              stroke="#6d6055"
              strokeWidth="1"
            />
            <g fill="#3a332c" stroke="#584f45" strokeWidth="0.8">
              <path d={`M${box.x0 - 14} ${box.yBase} l9 -8 l11 5 l-6 3 Z`} />
              <path d={`M${box.x1 - 4} ${box.yBase} l14 -6 l7 4 l-11 2 Z`} />
              <path d={`M${mid - 8} ${box.yBase} l7 -5 l6 5 Z`} />
            </g>
          </g>
        </g>
      </svg>

      <figcaption className="l-mono mt-2 flex items-baseline justify-between text-[10px] uppercase tracking-[0.16em]">
        <span className="text-white/45">Damage state {state}/5</span>
        <span className={state >= 4 ? "text-[var(--l-risk-5)]" : state === 3 ? "text-[var(--l-risk-3)]" : "text-white/60"}>
          {stateName}
        </span>
      </figcaption>
    </figure>
  );
}
