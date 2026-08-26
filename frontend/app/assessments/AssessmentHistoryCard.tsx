import Link from "next/link";
import { Calendar, MapPin, ShieldCheck, AlertTriangle, ArrowUpRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatTimeAgo } from "@/utils/tools";
import {
    calculateRiskScore,
    getRiskColorClasses,
    getRiskLevel,
} from "@/utils/risk";

export interface AssessmentSummary {
    id: string;
    created_at: string;
    place_name: string | null;
    latitude: number;
    longitude: number;
    resilience_score: number;
    hazard_score: number;
    hazard_level: string;
}

interface AssessmentHistoryCardProps {
    assessment: AssessmentSummary;
}

/**
 * Map a free-form hazard_level string (e.g. "Very High", "Low") from the
 * backend into a stable badge variant + color. Falls back to "default".
 */
function hazardBadgeVariant(
    level: string
): "default" | "destructive" | "secondary" | "outline" {
    const normalized = level.toLowerCase();
    if (normalized.includes("very high") || normalized.includes("critical")) {
        return "destructive";
    }
    if (normalized.includes("high")) {
        return "destructive";
    }
    if (normalized.includes("moderate") || normalized.includes("medium")) {
        return "secondary";
    }
    if (normalized.includes("low") || normalized.includes("very low")) {
        return "outline";
    }
    return "default";
}

function AssessmentHistoryCard({ assessment }: AssessmentHistoryCardProps) {
    const riskScore = calculateRiskScore(
        assessment.hazard_score,
        assessment.resilience_score
    );
    const riskLevel = getRiskLevel(riskScore);
    const riskColors = getRiskColorClasses(riskLevel);

    const locationLabel =
        assessment.place_name?.trim() ||
        `${assessment.latitude.toFixed(3)}, ${assessment.longitude.toFixed(3)}`;

    return (
        <article className="group flex h-full flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-xs transition-all duration-200 hover:-translate-y-0.5 hover:border-blue-300 hover:shadow-md">
            {/* Top row: timestamp + hazard badge */}
            <div className="mb-3 flex items-center justify-between gap-2">
                <span className="flex items-center gap-1.5 text-xs font-medium text-slate-500">
                    <Calendar className="h-3.5 w-3.5 text-slate-400" />
                    {formatTimeAgo(new Date(assessment.created_at))}
                </span>
                <Badge variant={hazardBadgeVariant(assessment.hazard_level)}>
                    {assessment.hazard_level}
                </Badge>
            </div>

            {/* Location */}
            <div className="mb-1 flex items-start gap-1.5">
                <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-blue-600" />
                <h3 className="line-clamp-2 text-sm font-semibold leading-snug text-slate-800">
                    {locationLabel}
                </h3>
            </div>

            {/* Coordinates (secondary, only if a real place name was returned) */}
            {assessment.place_name && (
                <p className="ml-5.5 pl-0.5 text-[11px] text-slate-400">
                    {assessment.latitude.toFixed(4)}°,{" "}
                    {assessment.longitude.toFixed(4)}°
                </p>
            )}

            {/* Score grid */}
            <div className="mt-4 grid grid-cols-2 gap-3">
                <div className="rounded-xl border border-slate-100 bg-slate-50/60 p-3">
                    <div className="mb-1 flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                        <ShieldCheck className="h-3 w-3" />
                        Resilience
                    </div>
                    <div className="text-lg font-bold leading-none text-slate-800">
                        {assessment.resilience_score.toFixed(0)}
                        <span className="ml-0.5 text-xs font-medium text-slate-400">
                            /100
                        </span>
                    </div>
                </div>
                <div
                    className={`rounded-xl border p-3 ${riskColors.bg} ${riskColors.border}`}
                >
                    <div
                        className={`mb-1 flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider ${riskColors.text}`}
                    >
                        <AlertTriangle className="h-3 w-3" />
                        Risk
                    </div>
                    <div
                        className={`text-lg font-bold leading-none ${riskColors.text}`}
                    >
                        {riskScore}
                        <span className="ml-0.5 text-xs font-medium opacity-70">
                            /100
                        </span>
                    </div>
                </div>
            </div>

            {/* Spacer to push CTA down */}
            <div className="flex-1" />

            {/* CTA */}
            <Link
                href={`/dashboard/${assessment.id}`}
                className="mt-5 block w-full"
            >
                <Button
                    variant="outline"
                    size="sm"
                    className="w-full justify-center"
                >
                    View assessment
                    <ArrowUpRight className="h-3.5 w-3.5" />
                </Button>
            </Link>
        </article>
    );
}

export default AssessmentHistoryCard;