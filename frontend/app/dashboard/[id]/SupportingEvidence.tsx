import type { ProcessedEvent } from "@/app/types";
import { History } from "lucide-react";
import { cn } from "@/lib/utils";
interface SupportingEvidenceProps {
    events: ProcessedEvent[];
}
export default function SupportingEvidence({ events }: SupportingEvidenceProps) {
    if (!events || events.length === 0) {
        return (
            <section className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="p-6 md:p-8 space-y-4">
                    <h2 className="text-xl font-display font-semibold text-slate-900">
                        Historical Seismic Evidence
                    </h2>
                    <p className="text-slate-500 text-sm">
                        No significant historical seismic events found within the assessment radius.
                    </p>
                </div>
            </section>
        );
    }
    // Sort events by magnitude descending, then by date (newest first)
    const sortedEvents = [...events].sort((a, b) => {
        if (b.magnitude !== a.magnitude) {
            return b.magnitude - a.magnitude;
        }
        return new Date(b.date).getTime() - new Date(a.date).getTime();
    });
    const getMagnitudeColor = (mag: number) => {
        if (mag >= 7.0) return "bg-red-500";
        if (mag >= 6.0) return "bg-orange-500";
        if (mag >= 5.0) return "bg-yellow-500";
        if (mag >= 4.0) return "bg-blue-500";
        return "bg-slate-300";
    };
    return (
        <section className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden mt-12">
            <div className="p-6 md:p-8 space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
                    <div>
                        <h2 className="text-xl font-display font-semibold text-slate-900 mb-2 flex items-center gap-2">
                            <History className="w-5 h-5 text-slate-400" />
                            Historical Seismic Evidence
                        </h2>
                        <p className="text-sm text-slate-500">
                            Recorded earthquakes within the region that influenced the hazard assessment.
                        </p>
                    </div>
                    <div className="bg-slate-50 text-slate-600 text-xs font-semibold px-3 py-1.5 rounded-full border border-slate-200 shrink-0">
                        {events.length} Events Analyzed
                    </div>
                </div>
                <div className="border border-slate-200 rounded-lg overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm whitespace-nowrap">
                            <thead className="bg-slate-50 text-slate-500 border-b border-slate-200">
                                <tr>
                                    <th className="px-4 py-3 font-semibold w-24">Magnitude</th>
                                    <th className="px-4 py-3 font-semibold">Location</th>
                                    <th className="px-4 py-3 font-semibold w-32">Date</th>
                                    <th className="px-4 py-3 font-semibold w-24">Distance</th>
                                    <th className="px-4 py-3 font-semibold w-24">Depth</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 bg-white">
                                {sortedEvents.map((event) => (
                                    <tr key={event.id} className="hover:bg-slate-50 transition-colors">
                                        <td className="px-4 py-3">
                                            <div className="flex items-center gap-2">
                                                <div 
                                                    className={cn(
                                                        "w-2 h-2 rounded-full",
                                                        getMagnitudeColor(event.magnitude)
                                                    )}
                                                />
                                                <span className="font-semibold text-slate-900">
                                                    {event.magnitude.toFixed(1)}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="px-4 py-3">
                                            <span className="text-slate-700 truncate block max-w-50 sm:max-w-xs md:max-w-md" title={event.place}>
                                                {event.place}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-slate-500">
                                            {new Date(event.date).toLocaleDateString("en-US", { year: 'numeric', month: 'short', day: 'numeric' })}
                                        </td>
                                        <td className="px-4 py-3 text-slate-500">
                                            {event.distance_km.toFixed(1)} km
                                        </td>
                                        <td className="px-4 py-3 text-slate-500">
                                            {event.depth_km.toFixed(1)} km
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </section>
    );
}