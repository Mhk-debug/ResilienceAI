"use client";

import type { LLMAnalysisOutput } from "@/app/types";
import {
    Sparkles,
    AlertCircle,
    AlertTriangle,
    Lightbulb,
    CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface AiInsightsProps {
    llm: LLMAnalysisOutput;
}

// ─── Priority config ──────────────────────────────────────────────────────────
type PriorityKey = "red" | "orange" | "yellow" | "green" | "blue";

const PRIORITY: Record<
    PriorityKey,
    {
        bar: string;
        badge: string;
        badgeText: string;
        label: string;
        Icon: React.ElementType;
    }
> = {
    red: {
        bar: "bg-red-500",
        badge: "bg-red-100 text-red-700",
        badgeText: "text-red-700",
        label: "Critical",
        Icon: AlertCircle,
    },
    orange: {
        bar: "bg-orange-500",
        badge: "bg-orange-100 text-orange-700",
        badgeText: "text-orange-700",
        label: "High",
        Icon: AlertTriangle,
    },
    yellow: {
        bar: "bg-amber-400",
        badge: "bg-amber-100 text-amber-700",
        badgeText: "text-amber-700",
        label: "Medium",
        Icon: AlertTriangle,
    },
    green: {
        bar: "bg-emerald-500",
        badge: "bg-emerald-100 text-emerald-700",
        badgeText: "text-emerald-700",
        label: "Low",
        Icon: Lightbulb,
    },
    blue: {
        bar: "bg-blue-500",
        badge: "bg-blue-100 text-blue-700",
        badgeText: "text-blue-700",
        label: "Advisory",
        Icon: Lightbulb,
    },
};

function getPriority(p: string) {
    return PRIORITY[p.toLowerCase() as PriorityKey] ?? PRIORITY.blue;
}

// ─── Component ────────────────────────────────────────────────────────────────
export default function AiInsights({ llm }: AiInsightsProps) {
    const hasSummary = llm.summary && llm.summary.length > 0;
    const hasRecs = llm.recommendations && llm.recommendations.length > 0;

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
            {/* ── LEFT: Key Findings ─────────────────────────────────────── */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
                <div className="flex items-center gap-2.5 px-6 pt-6 pb-4 border-b border-slate-100">
                    <Sparkles className="w-4 h-4 text-blue-500 shrink-0" />
                    <h2 className="text-sm font-semibold text-slate-900 tracking-tight">
                        Key Findings
                    </h2>
                    <span className="ml-auto text-[10px] font-semibold uppercase tracking-widest text-slate-400">
                        AI Analysis
                    </span>
                </div>

                <div className="p-6 flex-1">
                    {hasSummary ? (
                        <ol className="space-y-4">
                            {llm.summary.map((point, i) => (
                                <li
                                    key={i}
                                    className="flex gap-3.5 items-start group border-b border-slate-200 pb-3"
                                >
                                    {/* Step indicator */}
                                    <span
                                        className={cn(
                                            "shrink-0 mt-0.5 w-5 h-5 rounded-full text-[10px] font-bold flex items-center justify-center leading-none transition-colors",
                                            i === 0
                                                ? "bg-blue-600 text-white"
                                                : "bg-slate-100 text-slate-500 group-hover:bg-blue-100 group-hover:text-blue-700",
                                        )}
                                    >
                                        {i + 1}
                                    </span>
                                    <span className="text-sm text-slate-700 leading-relaxed">
                                        {point}
                                    </span>
                                </li>
                            ))}
                        </ol>
                    ) : (
                        <div className="flex flex-col items-center justify-center py-10 text-center">
                            <Sparkles className="w-7 h-7 text-slate-200 mb-3" />
                            <p className="text-sm text-slate-400 italic">
                                No AI findings are available for this
                                assessment.
                            </p>
                        </div>
                    )}
                </div>
            </div>

            {/* ── RIGHT: Recommendations ─────────────────────────────────── */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
                <div className="flex items-center gap-2.5 px-6 pt-6 pb-4 border-b border-slate-100">
                    <Lightbulb className="w-4 h-4 text-amber-500 shrink-0" />
                    <h2 className="text-sm font-semibold text-slate-900 tracking-tight">
                        Improvement Recommendations
                    </h2>
                </div>

                <div className="flex-1">
                    {hasRecs ? (
                        <>
                            <ul className="divide-y divide-slate-100">
                                {llm.recommendations.map((rec, i) => {
                                    const cfg = getPriority(rec.priority);
                                    const Icon = cfg.Icon;

                                    return (
                                        <li
                                            key={i}
                                            className="flex gap-0 items-stretch"
                                        >
                                            {/* Left priority bar */}
                                            <div
                                                className={cn(
                                                    "w-1 shrink-0 rounded-l-none",
                                                    cfg.bar,
                                                )}
                                            />

                                            <div className="flex-1 px-4 py-4 flex gap-3.5 items-start min-w-0">
                                                {/* Icon */}
                                                <div
                                                    className={cn(
                                                        "shrink-0 mt-0.5 w-7 h-7 rounded-lg flex items-center justify-center",
                                                        cfg.badge,
                                                    )}
                                                >
                                                    <Icon className="w-3.5 h-3.5" />
                                                </div>

                                                {/* Text */}
                                                <div className="flex-1 min-w-0 space-y-0.5">
                                                    <div className="flex items-center gap-2 flex-wrap">
                                                        <span className="text-sm font-semibold text-slate-900 leading-snug">
                                                            {rec.title}
                                                        </span>
                                                        <span
                                                            className={cn(
                                                                "text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded",
                                                                cfg.badge,
                                                            )}
                                                        >
                                                            {cfg.label}
                                                        </span>
                                                    </div>
                                                    <p className="text-xs text-slate-500 leading-relaxed">
                                                        {rec.description}
                                                    </p>
                                                </div>
                                            </div>
                                        </li>
                                    );
                                })}
                            </ul>

                            {/* Footer */}
                            <div className="px-5 py-3.5 border-t border-slate-100 bg-slate-50/60 flex items-start gap-2.5">
                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                                <p className="text-[11px] text-slate-400 leading-relaxed">
                                    AI-generated based on building data and
                                    geospatial hazards. Consult a certified
                                    structural engineer before undertaking major
                                    modifications.
                                </p>
                            </div>
                        </>
                    ) : (
                        <div className="flex flex-col items-center justify-center py-10 text-center px-6">
                            <Lightbulb className="w-7 h-7 text-slate-200 mb-3" />
                            <p className="text-sm text-slate-400 italic">
                                No specific recommendations were generated for
                                this assessment.
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
