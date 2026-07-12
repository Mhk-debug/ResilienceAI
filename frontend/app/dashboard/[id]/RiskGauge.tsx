import {
    RadialBarChart,
    RadialBar,
    PolarAngleAxis,
    ResponsiveContainer,
} from "recharts";
import { AlertCircle } from "lucide-react";

interface RiskGaugeProps {
    score: number;
    level: string;
}

export default function RiskGauge({ score, level }: RiskGaugeProps) {
    // Determine color based on severity
    let severityColor = "#3b82f6"; // Blue
    let severityBg = "bg-blue-50 border-blue-100";
    let severityText = "text-blue-700";
    let severityLabel = "Low Risk";

    if (score >= 75) {
        severityColor = "#ef4444"; // Red
        severityBg = "bg-rose-50 border-rose-100";
        severityText = "text-rose-700";
        severityLabel = "Critical Threat";
    } else if (score >= 55) {
        severityColor = "#f97316"; // Orange
        severityBg = "bg-orange-50 border-orange-100";
        severityText = "text-orange-700";
        severityLabel = "High Threat";
    } else if (score >= 35) {
        severityColor = "#eab308"; // Yellow
        severityBg = "bg-amber-50 border-amber-100";
        severityText = "text-amber-700";
        severityLabel = "Moderate Threat";
    }

    // Data formatted for Recharts RadialBar
    const chartData = [
        {
            name: "Risk Score",
            value: score,
            fill: severityColor,
        },
    ];

    return (
        <div
            id="risk-gauge"
            className="bg-white border border-slate-200 rounded-3xl p-6 shadow-xs flex flex-col justify-between h-full hover:border-slate-300 transition-all duration-150"
        >
            <div className="space-y-1.5 border-b border-slate-100 pb-3">
                <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
                    Section 1.2 — Core Structural Safety Index
                </span>
                <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-1.5">
                    <AlertCircle className="w-4.5 h-4.5 text-blue-600" />
                    Earthquake Risk Gauge
                </h3>
            </div>

            {/* Recharts Circular RadialBarChart Container */}
            <div className="relative flex items-center justify-center h-50 my-4">
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

                {/* Absolute Centered Risk Score Content */}
                <div className="absolute inset-0 flex flex-col items-center justify-center mt-2">
                    <span className="text-4xl font-mono font-bold tracking-tight text-slate-850">
                        {score}
                        <span className="text-lg font-sans font-medium text-slate-400">
                            /100
                        </span>
                    </span>
                    <span className="text-[10px] uppercase font-bold tracking-widest text-slate-400 mt-1">
                        Calculated risk
                    </span>
                    <div
                        className={`mt-2 px-3 py-1 rounded-full text-[11px] font-bold border ${severityBg} ${severityText}`}
                    >
                        {level} ({severityLabel})
                    </div>
                </div>
            </div>
            {/* Segmented Horizontal Legend (0-33 Red/Danger, 34-66 Yellow/Warning, 67-100 Green/Safe) */}
            <div className="w-full mt-6 space-y-2.5">
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
    );
}
