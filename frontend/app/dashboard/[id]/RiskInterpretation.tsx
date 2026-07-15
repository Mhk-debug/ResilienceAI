import type { LLMAnalysisOutput } from "@/app/types";
import { Building2, Globe2, BrainCircuit } from "lucide-react";
import { cn } from "@/lib/utils";

interface RiskInterpretationProps {
    llm: LLMAnalysisOutput;
}

const interpretationFields = [
    {
        key: "structural_assessment" as const,
        label: "Structural Assessment",
        icon: Building2,
        accent: "border-blue-200",
        iconColor: "text-blue-500",
        labelColor: "text-blue-700",
    },
    {
        key: "environmental_assessment" as const,
        label: "Environmental Assessment",
        icon: Globe2,
        accent: "border-emerald-200",
        iconColor: "text-emerald-500",
        labelColor: "text-emerald-700",
    },
    {
        key: "overall_reasoning" as const,
        label: "Overall Reasoning",
        icon: BrainCircuit,
        accent: "border-violet-200",
        iconColor: "text-violet-500",
        labelColor: "text-violet-700",
    },
] as const;

export default function RiskInterpretation({ llm }: RiskInterpretationProps) {
    const ri = llm.risk_interpretation;
    const hasInterpretation =
        ri &&
        (ri.structural_assessment || ri.environmental_assessment || ri.overall_reasoning);

    if (!hasInterpretation) return null;

    return (
        <div className="flex flex-col gap-4 w-full">
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-widest px-1">
                Risk Interpretation
            </h3>
            
            {/* New top-level unpadded flex container for the cards */}
            <div className="flex flex-col md:flex-row gap-4 w-full">
                {interpretationFields.map(({ key, label, icon: Icon, accent, iconColor, labelColor }) => {
                    const text = ri[key];
                    if (!text) return null;

                    return (
                        <div
                            key={key}
                            className={cn(
                                "flex-1 bg-white rounded-xl border p-5 flex flex-col gap-2.5",
                                accent
                            )}
                        >
                            <div className={cn("flex items-center gap-2 border-b pb-2", accent)}>
                                <Icon className={cn("w-4 h-4 shrink-0", iconColor)} />
                                <span className={cn("text-xs font-semibold uppercase tracking-wider", labelColor)}>
                                    {label}
                                </span>
                            </div>
                            <p className="text-sm text-slate-700 leading-relaxed">
                                {text}
                            </p>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}