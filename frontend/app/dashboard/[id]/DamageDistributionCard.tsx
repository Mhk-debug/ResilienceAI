"use client";

import type { ResilienceAssessmentResponse } from "@/app/types";
import { AlertTriangle, Info, CheckCircle } from "lucide-react";

interface DamageDistributionCardProps {
    building: ResilienceAssessmentResponse;
}

const GRADE_COLORS: Record<number, { bg: string; border: string; text: string; label: string }> = {
    1: { bg: "bg-emerald-500", border: "border-emerald-200", text: "text-emerald-700", label: "No damage" },
    2: { bg: "bg-green-500", border: "border-green-200", text: "text-green-700", label: "Minor damage" },
    3: { bg: "bg-amber-500", border: "border-amber-200", text: "text-amber-700", label: "Moderate damage" },
    4: { bg: "bg-orange-500", border: "border-orange-200", text: "text-orange-700", label: "Severe damage" },
    5: { bg: "bg-red-500", border: "border-red-200", text: "text-red-700", label: "Destruction" },
};

function hasData(building: ResilienceAssessmentResponse): boolean {
    return (
        building.probabilities != null ||
        building.expected_grade != null ||
        building.grade_class != null ||
        building.p_severe_grade45 != null
    );
}

function getProbability(building: ResilienceAssessmentResponse, grade: number): number {
    if (!building.probabilities) return 0;
    return building.probabilities[`grade${grade}`] ?? 0;
}

function getSevereText(pSevere: number): { text: string; className: string } {
    if (pSevere >= 0.5) {
        return {
            text: `${Math.round(pSevere * 100)}% chance of severe damage or collapse`,
            className: "bg-red-50 border-red-200 text-red-800",
        };
    }
    if (pSevere >= 0.25) {
        return {
            text: `${Math.round(pSevere * 100)}% chance of severe damage or collapse`,
            className: "bg-orange-50 border-orange-200 text-orange-800",
        };
    }
    return {
        text: `${Math.round(pSevere * 100)}% chance of severe damage or collapse`,
        className: "bg-amber-50 border-amber-200 text-amber-800",
    };
}

export default function DamageDistributionCard({
    building,
}: DamageDistributionCardProps) {
    if (!hasData(building)) return null;

    const probabilities = [1, 2, 3, 4, 5].map((g) => ({
        grade: g,
        prob: getProbability(building, g),
        ...GRADE_COLORS[g],
    }));

    const total = probabilities.reduce((s, p) => s + p.prob, 0);
    const normalized = probabilities.map((p) => ({
        ...p,
        pct: total > 0 ? (p.prob / total) * 100 : 0,
    }));

    const expectedGrade = building.expected_grade;
    const pSevere = building.p_severe_grade45 ?? 0;
    const severeCallout = getSevereText(pSevere);

    return (
        <section className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-6 md:p-8 space-y-6">
                {/* Header */}
                <div>
                    <h2 className="text-xl font-display font-semibold text-slate-900 mb-2 flex items-center gap-2">
                        <CheckCircle className="w-5 h-5 text-emerald-600" />
                        Building Damage Distribution
                    </h2>
                    <p className="text-sm text-slate-500">
                        Probabilistic estimate of damage grade under the reported
                        ground motion, based on Nepal 2015 survey data.
                    </p>
                </div>

                {/* Stacked bar */}
                <div className="space-y-3">
                    <div className="relative flex h-8 w-full rounded-lg overflow-hidden border border-slate-200">
                        {normalized.map((p) =>
                            p.pct > 0 ? (
                                <div
                                    key={p.grade}
                                    className={`${p.bg} transition-all duration-200 relative group`}
                                    style={{ width: `${p.pct}%` }}
                                >
                                    {p.pct >= 12 && (
                                        <span className="absolute inset-0 flex items-center justify-center text-[11px] font-bold text-white drop-shadow-sm">
                                            {p.pct.toFixed(0)}%
                                        </span>
                                    )}
                                </div>
                            ) : null,
                        )}

                        {/* Expected grade marker */}
                        {expectedGrade != null && total > 0 && (
                            <div
                                className="absolute top-0 bottom-0 w-0.5 bg-slate-900 z-10"
                                style={{
                                    left: `${((expectedGrade - 1) / 4) * 100}%`,
                                }}
                            >
                                <div className="absolute -top-6 left-1/2 -translate-x-1/2 whitespace-nowrap text-[10px] font-bold text-slate-700 bg-white border border-slate-200 rounded px-1.5 py-0.5 shadow-sm">
                                    Expected {expectedGrade.toFixed(1)}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Grade labels below bar */}
                    <div className="flex w-full">
                        {normalized.map((p) => (
                            <div
                                key={p.grade}
                                className="text-center text-[10px] font-semibold text-slate-400"
                                style={{ width: `${p.pct}%` }}
                            >
                                G{p.grade}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Detailed rows */}
                <div className="space-y-2">
                    {normalized.map((p) => (
                        <div
                            key={p.grade}
                            className={`flex items-center gap-3 p-2.5 rounded-lg border ${p.border} bg-slate-50/60`}
                        >
                            <div
                                className={`w-3 h-3 rounded-sm shrink-0 ${p.bg}`}
                            />
                            <span className="text-xs font-semibold text-slate-700 w-6">
                                G{p.grade}
                            </span>
                            <span className="text-xs text-slate-500 flex-1">
                                {p.label}
                            </span>
                            <div className="flex items-center gap-2">
                                <div className="w-24 h-2 bg-slate-200 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full rounded-full ${p.bg}`}
                                        style={{ width: `${p.pct}%` }}
                                    />
                                </div>
                                <span className="text-xs font-bold text-slate-700 w-12 text-right">
                                    {p.pct.toFixed(1)}%
                                </span>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Severe damage callout */}
                <div
                    className={`flex items-center gap-3 p-3 rounded-lg border ${severeCallout.className}`}
                >
                    <AlertTriangle className="w-5 h-5 shrink-0" />
                    <span className="text-sm font-bold">
                        {severeCallout.text}
                    </span>
                </div>

                {/* Model info footer */}
                <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400 border-t border-slate-100 pt-4">
                    {building.model_version && (
                        <span className="inline-flex items-center gap-1 bg-slate-50 border border-slate-200 rounded px-2 py-0.5">
                            <Info className="w-3 h-3" />
                            {building.model_version}
                        </span>
                    )}
                    {building.used_fallback_model && (
                        <span className="inline-flex items-center gap-1 bg-amber-50 border border-amber-200 text-amber-700 rounded px-2 py-0.5 font-medium">
                            Fallback model used
                        </span>
                    )}
                    {building.grade_class != null && (
                        <span className="inline-flex items-center gap-1">
                            Most likely: Grade {building.grade_class}
                        </span>
                    )}
                </div>

                {/* Model flags */}
                {building.flags && building.flags.length > 0 && (
                    <div className="space-y-1">
                        {building.flags.map((flag, i) => (
                            <p
                                key={i}
                                className="text-[11px] text-slate-400 italic"
                            >
                                Note: {flag}
                            </p>
                        ))}
                    </div>
                )}
            </div>
        </section>
    );
}
