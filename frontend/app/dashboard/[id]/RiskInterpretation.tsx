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
    },
    {
        key: "environmental_assessment" as const,
        label: "Environmental Assessment",
        icon: Globe2,
    },
    {
        key: "overall_reasoning" as const,
        label: "Overall Reasoning",
        icon: BrainCircuit,
    },
] as const;

const styles = {
    structural_assessment: {
        accent: "border-l-amber-600",
        iconBg: "bg-amber-100",
        iconColor: "text-amber-700",
        labelColor: "text-amber-800",
    },
    environmental_assessment: {
        accent: "border-l-emerald-600",
        iconBg: "bg-emerald-100",
        iconColor: "text-emerald-700",
        labelColor: "text-emerald-800",
    },
    overall_reasoning: {
        accent: "border-l-indigo-600",
        iconBg: "bg-indigo-100",
        iconColor: "text-indigo-700",
        labelColor: "text-indigo-800",
    },
};

export default function RiskInterpretation({ llm }: RiskInterpretationProps) {
    const ri = llm.risk_interpretation;
    const hasInterpretation =
        ri &&
        (ri.structural_assessment ||
            ri.environmental_assessment ||
            ri.overall_reasoning);

    if (!hasInterpretation) return null;

    return (
        <div className="flex flex-col gap-4 w-full">
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-widest px-1">
                Risk Interpretation
            </h3>

            {/* New top-level unpadded flex container for the cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 w-full">
                {interpretationFields.map(({ key, label, icon: Icon }) => {
                    const text = ri[key];
                    if (!text) return null;

                    const style =
                        styles[key as keyof typeof styles] ?? styles["overall_reasoning"];

                    return (
                        <div
                            key={key}
                            className={cn(
                                "min-w-0 w-full",
                                "bg-white rounded-xl",
                                "border border-slate-200",
                                "border-l-4",
                                style.accent,
                                "p-4 sm:p-5",
                                "flex flex-col",
                                "shadow-sm",
                                "transition-shadow duration-200",
                                "hover:shadow-md",
                            )}
                        >
                            {/* Card Header */}
                            <div className="flex items-center gap-3 pb-3 border-b border-slate-200">
                                <div
                                    className={cn(
                                        "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg",
                                        style.iconBg,
                                        style.iconColor,
                                    )}
                                >
                                    <Icon
                                        className="h-5 w-5"
                                        strokeWidth={2.25}
                                    />
                                </div>

                                <h3
                                    className={cn(
                                        "min-w-0",
                                        "text-xs sm:text-sm",
                                        "font-bold uppercase tracking-wider",
                                        style.labelColor,
                                    )}
                                >
                                    {label}
                                </h3>
                            </div>

                            {/* Interpretation */}
                            <p className="mt-4 text-sm leading-6 text-slate-800">
                                {text}
                            </p>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
