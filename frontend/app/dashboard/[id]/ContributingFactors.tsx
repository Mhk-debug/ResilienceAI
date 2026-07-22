import type { EnvironmentalContext, Indicators } from "@/app/types";
import {
    Activity,
    Mountain,
    Map,
    Zap,
    MapPin,
    TrendingUp,
    History,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface ContributingFactorsProps {
    environmentalContext: EnvironmentalContext;
    indicators: Indicators;
}

const colorMap: Record<string, string> = {
    red: "bg-red-50 text-red-700 border-red-200",
    yellow: "bg-yellow-50 text-yellow-700 border-yellow-200",
    green: "bg-green-50 text-green-700 border-green-200",
    blue: "bg-blue-50 text-blue-700 border-blue-200",
};

const items = [
    {
        icon: Activity,
        label: "Seismic Hazard",
        iconColor: "text-amber-700",
        iconBg: "bg-amber-100",
        accent: "border-l-amber-600",
    },
    {
        icon: MapPin,
        label: "Fault Proximity",
        iconColor: "text-blue-700",
        iconBg: "bg-blue-100",
        accent: "border-l-blue-600",
    },
    {
        icon: Mountain,
        label: "Soil Conditions",
        iconColor: "text-emerald-700",
        iconBg: "bg-emerald-100",
        accent: "border-l-emerald-600",
    },
    {
        icon: History,
        label: "Historical Activity",
        iconColor: "text-purple-700",
        iconBg: "bg-purple-100",
        accent: "border-l-purple-600",
    },
    {
        icon: TrendingUp,
        label: "Earthquake Recurrence",
        iconColor: "text-indigo-700",
        iconBg: "bg-indigo-100",
        accent: "border-l-indigo-600",
    },
];

export default function ContributingFactors({
    environmentalContext,
    indicators,
}: ContributingFactorsProps) {
    const { faults, soil, ground_motion, historical_activity, summary } =
        environmentalContext;

    return (
        <section className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-6 md:p-8 space-y-8">
                <div>
                    <h2 className="text-xl font-display font-semibold text-slate-900 mb-2">
                        Contributing Environmental Factors
                    </h2>
                    <p className="text-sm text-slate-500">
                        The environmental and geospatial conditions affecting
                        this location&apos;s earthquake vulnerability.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-5 sm:gap-6">
                    {/* Soil Conditions */}
                    <div className="min-w-0 space-y-3">
                        <div className="flex items-center gap-2 min-w-0">
                            <Map className="w-5 h-5 shrink-0 text-emerald-700" />
                            <h3 className="min-w-0 font-semibold text-slate-900">
                                Soil & Liquefaction
                            </h3>
                        </div>

                        <div className="rounded-xl border border-slate-200 bg-slate-100/80 p-3.5 sm:p-4 shadow-sm">
                            <div className="space-y-3">
                                <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-1">
                                    <span className="text-sm font-medium text-slate-700">
                                        Dominant Soil
                                    </span>

                                    <span className="max-w-full text-right text-sm font-bold capitalize text-slate-900">
                                        {soil.dominant_soil}
                                    </span>
                                </div>

                                <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
                                    <span className="text-sm font-medium text-slate-700">
                                        Classification
                                    </span>

                                    <span
                                        className={cn(
                                            "shrink-0 rounded-full border px-2.5 py-1 text-xs font-semibold capitalize",
                                            colorMap[
                                                indicators.soil_liquefaction
                                                    .color
                                            ] || colorMap.blue,
                                        )}
                                    >
                                        {soil.classification}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Fault Proximity */}
                    <div className="min-w-0 space-y-3">
                        <div className="flex items-center gap-2 min-w-0">
                            <Mountain className="w-5 h-5 shrink-0 text-blue-700" />
                            <h3 className="min-w-0 font-semibold text-slate-900">
                                Fault Lines
                            </h3>
                        </div>

                        <div className="rounded-xl border border-slate-200 bg-slate-100/80 p-3.5 sm:p-4 shadow-sm">
                            <div className="space-y-3">
                                <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-1">
                                    <span className="text-sm font-medium text-slate-700">
                                        Nearest Fault
                                    </span>

                                    <span className="text-right text-sm font-bold text-slate-900">
                                        {faults.distance_km} km
                                    </span>
                                </div>

                                <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
                                    <span className="text-sm font-medium text-slate-700">
                                        Proximity Risk
                                    </span>

                                    <span
                                        className={cn(
                                            "shrink-0 rounded-full border px-2.5 py-1 text-xs font-semibold capitalize",
                                            colorMap[
                                                indicators.fault_proximity.color
                                            ] || colorMap.blue,
                                        )}
                                    >
                                        {faults.classification}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Historical Activity */}
                    <div className="min-w-0 space-y-3">
                        <div className="flex items-center gap-2 min-w-0">
                            <Activity className="w-5 h-5 shrink-0 text-purple-700" />
                            <h3 className="min-w-0 font-semibold text-slate-900">
                                Seismic History
                            </h3>
                        </div>

                        <div className="rounded-xl border border-slate-200 bg-slate-100/80 p-3.5 sm:p-4 shadow-sm">
                            <div className="space-y-3">
                                <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-1">
                                    <span className="text-sm font-medium text-slate-700">
                                        Events Recorded
                                    </span>

                                    <span className="text-right text-sm font-bold text-slate-900">
                                        {
                                            historical_activity.events_within_radius
                                        }
                                    </span>
                                </div>

                                {historical_activity.largest_magnitude && (
                                    <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-1">
                                        <span className="text-sm font-medium text-slate-700">
                                            Max Magnitude
                                        </span>

                                        <span className="text-right text-sm font-bold text-slate-900">
                                            M{" "}
                                            {
                                                historical_activity.largest_magnitude
                                            }
                                        </span>
                                    </div>
                                )}

                                <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-t border-slate-300 pt-3">
                                    <span className="text-sm font-medium text-slate-700">
                                        Activity Level
                                    </span>

                                    <span
                                        className={cn(
                                            "shrink-0 rounded-full border px-2.5 py-1 text-xs font-semibold capitalize",
                                            colorMap[
                                                indicators.historical_activity
                                                    .color
                                            ] || colorMap.blue,
                                        )}
                                    >
                                        {historical_activity.classification}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Ground Motion */}
                    <div className="min-w-0 space-y-3">
                        <div className="flex items-center gap-2 min-w-0">
                            <Zap className="w-5 h-5 shrink-0 text-amber-700" />
                            <h3 className="min-w-0 font-semibold text-slate-900">
                                Ground Motion
                            </h3>
                        </div>

                        <div className="rounded-xl border border-slate-200 bg-slate-100/80 p-3.5 sm:p-4 shadow-sm">
                            <div className="space-y-3">
                                <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-1">
                                    <span className="max-w-[70%] text-sm font-medium text-slate-700">
                                        Peak Historical PGA 
                                    </span>

                                    <span className="text-right text-sm font-bold text-slate-900">
                                        {ground_motion.estimated_pga_g} g
                                    </span>
                                </div>

                                <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-1">
                                    <span className="max-w-[70%] text-sm font-medium text-slate-700">
                                        Peak Historical MMI
                                    </span>

                                    <span className="text-right text-sm font-bold text-slate-900">
                                        Level {ground_motion.estimated_mmi}
                                    </span>
                                </div>

                                <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-t border-slate-300 pt-3">
                                    <span className="text-sm font-medium text-slate-700">
                                        Zone Classification
                                    </span>

                                    <span
                                        className={cn(
                                            "rounded-full border px-2.5 py-1 text-xs text-wrap font-semibold capitalize",
                                            colorMap[
                                                indicators.seismic_zone.color
                                            ] || colorMap.blue,
                                        )}
                                    >
                                        {indicators.seismic_zone.classification}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Environmental Synthesis */}
                <div className="mt-8">
                    <div className="flex items-start justify-between mb-5">
                        <div>
                            <div className="flex items-center gap-2.5">
                                <div className="w-1.5 h-6 rounded-full bg-green-600" />

                                <h4 className="text-lg font-bold text-slate-900 tracking-tight">
                                    Environmental Evidence
                                </h4>
                            </div>

                            <p className="text-sm text-slate-600 mt-2 ml-4">
                                Key factors contributing to the environmental
                                risk assessment
                            </p>
                        </div>
                    </div>

                    {summary && summary.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {summary.map((point, idx) => {
                                const item = items[idx] ?? items[0];
                                const Icon = item.icon;

                                return (
                                    <div
                                        key={idx}
                                        className={`
                        group rounded-xl border border-slate-200
                        border-l-4 ${item.accent}
                        bg-white p-3.5 sm:p-4
                        transition-all duration-200
                        hover:shadow-md
                    `}
                                    >
                                        <div className="flex flex-col min-[400px]:flex-row gap-3">
                                            <div
                                                className={`
                                shrink-0 w-10 h-10 rounded-lg
                                ${item.iconBg} ${item.iconColor}
                                flex items-center justify-center
                            `}
                                            >
                                                <Icon
                                                    className="w-5 h-5"
                                                    strokeWidth={2.25}
                                                />
                                            </div>

                                            <div className="min-w-0 flex-1">
                                                <p className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                                                    {item.label}
                                                </p>

                                                <p className="text-sm leading-relaxed text-slate-800">
                                                    {point}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    ) : (
                        <div className="rounded-xl border border-slate-100 bg-slate-50/50 p-5">
                            <p className="text-slate-500 text-sm italic">
                                Environmental context summary is currently
                                unavailable.
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </section>
    );
}
