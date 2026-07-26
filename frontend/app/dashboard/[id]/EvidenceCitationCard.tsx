"use client";

import type { EvidenceCitation } from "@/app/types";
import { FileText, ExternalLink, Building2, BookOpen, MapPin, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";
import { useState } from "react";

interface EvidenceCitationCardProps {
    evidence: EvidenceCitation;
    compact?: boolean;
}

const CATEGORY_LABELS: Record<string, string> = {
    building_vulnerability: "Building Vulnerability",
    earthquake_safety: "Earthquake Safety",
    environmental_hazards: "Environmental Hazards",
    local_context: "Local Context",
    mitigation: "Mitigation",
};

const CATEGORY_COLORS: Record<string, string> = {
    building_vulnerability: "bg-red-100 text-red-700 border-red-200",
    earthquake_safety: "bg-orange-100 text-orange-700 border-orange-200",
    environmental_hazards: "bg-amber-100 text-amber-700 border-amber-200",
    local_context: "bg-blue-100 text-blue-700 border-blue-200",
    mitigation: "bg-emerald-100 text-emerald-700 border-emerald-200",
};

function getCategoryLabel(category: string): string {
    return CATEGORY_LABELS[category] || category.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function getCategoryColor(category: string): string {
    return CATEGORY_COLORS[category] || "bg-slate-100 text-slate-700 border-slate-200";
}

function getRelevanceColor(score: number): string {
    if (score >= 0.8) return "bg-emerald-500";
    if (score >= 0.6) return "bg-amber-500";
    return "bg-slate-300";
}

export default function EvidenceCitationCard({ evidence, compact = false }: EvidenceCitationCardProps) {
    const [expanded, setExpanded] = useState(false);
    const isLongExcerpt = evidence.excerpt.length > 150;

    return (
        <div className={cn(
            "border rounded-lg bg-white transition-colors",
            compact ? "p-3" : "p-4",
        )}>
            {/* Header */}
            <div className="flex items-start gap-3">
                <div className={cn(
                    "shrink-0 rounded-lg flex items-center justify-center",
                    compact ? "w-7 h-7" : "w-8 h-8",
                    getCategoryColor(evidence.category),
                )}>
                    <FileText className={cn("shrink-0", compact ? "w-3.5 h-3.5" : "w-4 h-4")} />
                </div>
                <div className="flex-1 min-w-0 space-y-1">
                    {/* Source org + category */}
                    <div className="flex items-center gap-2 flex-wrap">
                        {evidence.source_org && (
                            <span className={cn(
                                "inline-flex items-center gap-1 font-semibold text-slate-800",
                                compact ? "text-xs" : "text-sm",
                            )}>
                                <Building2 className="w-3 h-3 shrink-0 text-slate-400" />
                                {evidence.source_org}
                            </span>
                        )}
                        <span className={cn(
                            "inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border",
                            getCategoryColor(evidence.category),
                        )}>
                            {getCategoryLabel(evidence.category)}
                        </span>
                    </div>

                    {/* Source title */}
                    {evidence.source_title && (
                        <p className={cn(
                            "text-slate-600 font-medium leading-snug",
                            compact ? "text-xs" : "text-sm",
                        )}>
                            {evidence.source_title}
                        </p>
                    )}
                </div>
            </div>

            {/* Excerpt */}
            <div className="mt-3">
                <p className={cn(
                    "text-slate-600 italic leading-relaxed",
                    compact ? "text-[11px]" : "text-xs",
                )}>
                    {isLongExcerpt && !expanded
                        ? `${evidence.excerpt.substring(0, 150)}...`
                        : evidence.excerpt
                    }
                    {isLongExcerpt && (
                        <button
                            onClick={() => setExpanded(!expanded)}
                            className="ml-1 text-blue-600 hover:text-blue-800 font-medium underline"
                        >
                            {expanded ? "Show less" : "Show more"}
                        </button>
                    )}
                </p>
            </div>

            {/* Footer: relevance + source link */}
            <div className={cn(
                "flex items-center justify-between gap-4",
                compact ? "mt-2" : "mt-3 pt-2 border-t border-slate-100",
            )}>
                {/* Relevance score */}
                <div className="flex items-center gap-2">
                    <TrendingUp className="w-3 h-3 text-slate-400 shrink-0" />
                    <div className="flex items-center gap-1.5">
                        <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                            <div
                                className={cn(
                                    "h-full rounded-full transition-all",
                                    getRelevanceColor(evidence.relevance_score),
                                )}
                                style={{ width: `${Math.round(evidence.relevance_score * 100)}%` }}
                            />
                        </div>
                        <span className="text-[10px] font-semibold text-slate-400">
                            {Math.round(evidence.relevance_score * 100)}%
                        </span>
                    </div>
                </div>

                {/* Source link */}
                {evidence.source_url && (
                    <a
                        href={evidence.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={cn(
                            "inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 font-medium",
                            "hover:underline",
                            compact ? "text-[10px]" : "text-xs",
                        )}
                    >
                        <ExternalLink className="w-3 h-3 shrink-0" />
                        View Source
                    </a>
                )}
            </div>
        </div>
    );
}