import type { EnvironmentalContext, Indicators } from "@/app/types";
import { Activity, Mountain, Map, Zap } from "lucide-react";
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

export default function ContributingFactors({ environmentalContext, indicators }: ContributingFactorsProps) {
    const { faults, soil, ground_motion, historical_activity, summary } = environmentalContext;

    return (
        <section className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-6 md:p-8 space-y-8">
                <div>
                    <h2 className="text-xl font-display font-semibold text-slate-900 mb-2">
                        Contributing Environmental Factors
                    </h2>
                    <p className="text-sm text-slate-500">
                        The environmental and geospatial conditions affecting this location&apos;s earthquake vulnerability.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Soil Conditions */}
                    <div className="space-y-3">
                        <div className="flex items-center gap-2">
                            <Map className="w-5 h-5 text-slate-400" />
                            <h3 className="font-medium text-slate-900">Soil & Liquefaction</h3>
                        </div>
                        <div className="p-4 rounded-lg border border-slate-100 bg-slate-50 space-y-2">
                            <div className="flex justify-between items-start">
                                <span className="text-sm text-slate-600">Dominant Soil</span>
                                <span className="text-sm font-semibold capitalize text-slate-900">{soil.dominant_soil}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-slate-600">Classification</span>
                                <span className={cn("text-xs font-medium px-2 py-1 rounded-full border capitalize", colorMap[indicators.soil_liquefaction.color] || colorMap.blue)}>
                                    {soil.classification}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Fault Proximity */}
                    <div className="space-y-3">
                        <div className="flex items-center gap-2">
                            <Mountain className="w-5 h-5 text-slate-400" />
                            <h3 className="font-medium text-slate-900">Fault Lines</h3>
                        </div>
                        <div className="p-4 rounded-lg border border-slate-100 bg-slate-50 space-y-2">
                            <div className="flex justify-between items-start">
                                <span className="text-sm text-slate-600">Nearest Fault</span>
                                <span className="text-sm font-semibold text-slate-900">{faults.distance_km} km</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-slate-600">Proximity Risk</span>
                                <span className={cn("text-xs font-medium px-2 py-1 rounded-full border capitalize", colorMap[indicators.fault_proximity.color] || colorMap.blue)}>
                                    {faults.classification}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Historical Activity */}
                    <div className="space-y-3">
                        <div className="flex items-center gap-2">
                            <Activity className="w-5 h-5 text-slate-400" />
                            <h3 className="font-medium text-slate-900">Seismic History</h3>
                        </div>
                        <div className="p-4 rounded-lg border border-slate-100 bg-slate-50 space-y-2">
                            <div className="flex justify-between items-start">
                                <span className="text-sm text-slate-600">Events Recorded</span>
                                <span className="text-sm font-semibold text-slate-900">{historical_activity.events_within_radius}</span>
                            </div>
                            {historical_activity.largest_magnitude && (
                                <div className="flex justify-between items-start">
                                    <span className="text-sm text-slate-600">Max Magnitude</span>
                                    <span className="text-sm font-semibold text-slate-900">M {historical_activity.largest_magnitude}</span>
                                </div>
                            )}
                            <div className="flex justify-between items-center pt-2 border-t border-slate-200 mt-2">
                                <span className="text-sm text-slate-600">Activity Level</span>
                                <span className={cn("text-xs font-medium px-2 py-1 rounded-full border capitalize", colorMap[indicators.historical_activity.color] || colorMap.blue)}>
                                    {historical_activity.classification}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Ground Motion */}
                    <div className="space-y-3">
                        <div className="flex items-center gap-2">
                            <Zap className="w-5 h-5 text-slate-400" />
                            <h3 className="font-medium text-slate-900">Ground Motion</h3>
                        </div>
                        <div className="p-4 rounded-lg border border-slate-100 bg-slate-50 space-y-2">
                            <div className="flex justify-between items-start">
                                <span className="text-sm text-slate-600">Peak Ground Accel (PGA)</span>
                                <span className="text-sm font-semibold text-slate-900">{ground_motion.estimated_pga_g} g</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-slate-600">Expected Intensity (MMI)</span>
                                <span className="text-sm font-semibold text-slate-900">Level {ground_motion.estimated_mmi}</span>
                            </div>
                            <div className="flex justify-between items-center pt-2 border-t border-slate-200 mt-2">
                                <span className="text-sm text-slate-600">Zone Classification</span>
                                <span className={cn("text-xs font-medium px-2 py-1 rounded-full border capitalize", colorMap[indicators.seismic_zone.color] || colorMap.blue)}>
                                    {indicators.seismic_zone.classification}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Synthesis Summary */}
                <div className="bg-slate-50/50 border border-slate-100 p-5 rounded-xl mt-8">
                    <h4 className="text-xs font-semibold text-green-700 uppercase tracking-wider mb-3">Environmental Summary</h4>
                    {summary && summary.length > 0 ? (
                        <ul className="space-y-2.5 text-slate-600 text-sm leading-relaxed">
                            {summary.map((point, idx) => (
                                <li key={idx} className="flex gap-2.5 items-start">
                                    <span className="text-slate-400 font-bold mt-0.5 leading-none text-base">•</span>
                                    <span>{point}</span>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-slate-500 text-sm italic">
                            Environmental context summary is currently unavailable.
                        </p>
                    )}
                </div>
            </div>
        </section>
    );
}
