import {
    RadialBarChart,
    RadialBar,
    PolarAngleAxis,
    ResponsiveContainer,
} from "recharts";
import { AlertCircle, Shield, AlertTriangle, Info } from "lucide-react";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";

interface RiskGaugeProps {
    score: number;
    level: string;
    resilienceScore: number;
    hazardScore: number;
}

// ─── Tooltip content ──────────────────────────────────────────────────────────

function ResilienceTooltip() {
    return (
        <div className="space-y-2.5 max-w-60">
            <p className="font-semibold text-xs text-white">
                What is the Resilience Score?
            </p>
            <p className="text-[11px] leading-relaxed text-slate-300">
                Measures how well the <em>building itself</em> is expected to
                withstand an earthquake, based on its age, materials, structure,
                and foundation. Higher means stronger.
            </p>
            <div className="space-y-1 pt-1 border-t border-slate-600">
                <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                    Score ranges
                </p>
                {[
                    {
                        range: "75 – 100",
                        label: "Strong",
                        color: "bg-emerald-400",
                    },
                    {
                        range: "50 – 74",
                        label: "Moderate",
                        color: "bg-amber-400",
                    },
                    { range: "25 – 49", label: "Weak", color: "bg-orange-400" },
                    {
                        range: "0 – 24",
                        label: "Very vulnerable",
                        color: "bg-red-400",
                    },
                ].map(({ range, label, color }) => (
                    <div key={range} className="flex items-center gap-2">
                        <span
                            className={`w-2 h-2 rounded-full shrink-0 ${color}`}
                        />
                        <span className="text-[11px] text-white">{range}</span>
                        <span className="text-[11px] text-slate-400">
                            — {label}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
}

function HazardTooltip() {
    return (
        <div className="space-y-2.5 max-w-60">
            <p className="font-semibold text-xs text-white">
                What is the Hazard Score?
            </p>
            <p className="text-[11px] leading-relaxed text-slate-300">
                Measures how dangerous the <em>location</em> is, based on nearby
                fault lines, soil type, historical earthquakes, and expected
                ground shaking. Higher means riskier surroundings.
            </p>
            <div className="space-y-1 pt-1 border-t border-slate-600">
                <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                    Score ranges
                </p>
                {[
                    {
                        range: "75 – 100",
                        label: "Very high hazard",
                        color: "bg-red-400",
                    },
                    {
                        range: "50 – 74",
                        label: "High hazard",
                        color: "bg-orange-400",
                    },
                    {
                        range: "25 – 49",
                        label: "Moderate hazard",
                        color: "bg-amber-400",
                    },
                    {
                        range: "0 – 24",
                        label: "Low hazard",
                        color: "bg-emerald-400",
                    },
                ].map(({ range, label, color }) => (
                    <div key={range} className="flex items-center gap-2">
                        <span
                            className={`w-2 h-2 rounded-full shrink-0 ${color}`}
                        />
                        <span className="text-[11px] text-white">{range}</span>
                        <span className="text-[11px] text-slate-400">
                            — {label}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function RiskGauge({
    score,
    level,
    resilienceScore,
    hazardScore,
}: RiskGaugeProps) {
    // Determine color based on severity
    let severityColor = "#3b82f6"; // Blue
    let severityBg = "bg-blue-50 border-blue-100";
    let severityText = "text-blue-700";

    if (score >= 75) {
        severityColor = "#ef4444";
        severityBg = "bg-rose-50 border-rose-100";
        severityText = "text-rose-700";
    } else if (score >= 55) {
        severityColor = "#f97316";
        severityBg = "bg-orange-50 border-orange-100";
        severityText = "text-orange-700";
    } else if (score >= 35) {
        severityColor = "#eab308";
        severityBg = "bg-amber-50 border-amber-100";
        severityText = "text-amber-700";
    }

    const chartData = [
        { name: "Risk Score", value: score, fill: severityColor },
    ];

    return (
        <TooltipProvider delay={200}>
            <div
                id="risk-gauge"
                className="bg-white border border-slate-200 rounded-3xl p-6 shadow-xs flex flex-col h-full hover:border-slate-300 transition-all duration-150"
            >
                <div className="space-y-1.5 border-b border-slate-100 pb-3 mb-6">
                    <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-1.5">
                        <AlertCircle className="w-4.5 h-4.5 text-blue-600" />
                        Overall Risk Assessment
                    </h3>
                </div>

                <div className="flex flex-col md:flex-row items-center justify-between gap-8 flex-1">
                    {/* Primary Risk Gauge */}
                    <div className="relative flex flex-col items-center justify-center w-full max-w-50 aspect-square shrink-0">
                        <ResponsiveContainer width="100%" height="100%">
                            <RadialBarChart
                                cx="50%"
                                cy="50%"
                                innerRadius="75%"
                                outerRadius="100%"
                                barSize={14}
                                data={chartData}
                                startAngle={220}
                                endAngle={-40}
                            >
                                <PolarAngleAxis
                                    type="number"
                                    domain={[0, 100]}
                                    angleAxisId={0}
                                    tick={false}
                                />
                                <RadialBar
                                    background={{ fill: "#f1f5f9" }}
                                    dataKey="value"
                                    cornerRadius={12}
                                />
                            </RadialBarChart>
                        </ResponsiveContainer>

                        <div className="absolute inset-0 flex flex-col items-center justify-center mt-2">
                            <span className="text-4xl font-mono font-bold tracking-tight text-slate-900">
                                {score}
                            </span>
                            <span className="text-[10px] uppercase font-bold tracking-widest text-slate-400 mt-1">
                                Risk Score
                            </span>
                            <div
                                className={`mt-2 px-3 py-1 rounded-full text-[11px] font-bold border ${severityBg} ${severityText}`}
                            >
                                {level}
                            </div>
                        </div>
                    </div>

                    {/* Sub-scores */}
                    <div className="flex-1 flex flex-col justify-center gap-4 w-full">
                        {/* Resilience Score */}
                        <Tooltip>
                            <TooltipTrigger
                                type="button"
                                className="flex items-center p-4 rounded-2xl bg-emerald-50 border border-emerald-100 hover:border-emerald-300 hover:shadow-sm transition-all duration-150 cursor-default text-left w-full group"
                            >
                                <div className="p-3 bg-white rounded-xl shadow-sm mr-4 shrink-0">
                                    <Shield className="w-6 h-6 text-emerald-600" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="text-xs font-bold uppercase tracking-wider text-emerald-700 mb-0.5 flex items-center gap-1.5">
                                        Resilience Score
                                        <Info className="w-3 h-3 text-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                                    </div>
                                    <div className="text-2xl font-mono font-bold text-slate-900">
                                        {resilienceScore}
                                        <span className="text-sm font-sans font-medium text-slate-500 ml-1">
                                            / 100
                                        </span>
                                    </div>
                                </div>
                            </TooltipTrigger>
                            <TooltipContent
                                side="left"
                                sideOffset={10}
                                className="bg-slate-800 border-slate-700 p-4 shadow-xl"
                            >
                                <ResilienceTooltip />
                            </TooltipContent>
                        </Tooltip>

                        {/* Hazard Score */}
                        <Tooltip>
                            <TooltipTrigger
                                type="button"
                                className="flex items-center p-4 rounded-2xl bg-rose-50 border border-rose-100 hover:border-rose-300 hover:shadow-sm transition-all duration-150 cursor-default text-left w-full group"
                            >
                                <div className="p-3 bg-white rounded-xl shadow-sm mr-4 shrink-0">
                                    <AlertTriangle className="w-6 h-6 text-rose-600" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="text-xs font-bold uppercase tracking-wider text-rose-700 mb-0.5 flex items-center gap-1.5">
                                        Hazard Score
                                        <Info className="w-3 h-3 text-rose-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                                    </div>
                                    <div className="text-2xl font-mono font-bold text-slate-900">
                                        {hazardScore}
                                        <span className="text-sm font-sans font-medium text-slate-500 ml-1">
                                            / 100
                                        </span>
                                    </div>
                                </div>
                            </TooltipTrigger>
                            <TooltipContent
                                side="left"
                                sideOffset={10}
                                className="bg-slate-800 border-slate-700 p-4 shadow-xl"
                            >
                                <HazardTooltip />
                            </TooltipContent>
                        </Tooltip>
                    </div>
                </div>

                {/* Segmented Horizontal Legend */}
                <div className="w-full mt-8 space-y-2.5">
                    <div className="relative flex h-2.5 w-full rounded-full overflow-hidden border border-slate-200">
                        <div
                            className="bg-blue-500 flex-35"
                            title="Low Risk: 0-34"
                        />
                        <div
                            className="bg-amber-400 flex-20 border-l border-white"
                            title="Moderate Threat: 35-54"
                        />
                        <div
                            className="bg-orange-500 flex-20 border-l border-white"
                            title="High Threat: 55-74"
                        />
                        <div
                            className="bg-red-500 flex-25 border-l border-white"
                            title="Critical Threat: 75-100"
                        />
                    </div>
                    <div className="flex justify-between text-[10px] font-bold text-slate-500 font-mono px-1">
                        <span className="text-blue-600">0-34 Low</span>
                        <span className="text-amber-600">35-54 Moderate</span>
                        <span className="text-orange-600">55-74 High</span>
                        <span className="text-red-600">75-100 Critical</span>
                    </div>
                </div>
            </div>
        </TooltipProvider>
    );
}
