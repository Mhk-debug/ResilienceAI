"use client";

import React from "react";
import { Check, Loader2, Info } from "lucide-react";

export type AssessmentStage =
    | "initializing"
    | "resilience"
    | "hazard"
    | "llm"
    | "saving";

export type StageStatus = "pending" | "active" | "completed";

export type StageStatusMap = Record<AssessmentStage, StageStatus>;

export interface LoadingStage {
    stage: AssessmentStage;
    title: string;
    description: string;
}

interface MultiStageLoadingDisplayProps {
    /**
     * Current status of every processing stage.
     *
     * Resilience and hazard may both be "active"
     * at the same time because they run concurrently.
     */
    stageStatuses: StageStatusMap;

    /**
     * Current status message sent by the backend.
     */
    statusText: string;

    /**
     * True after the backend sends the "complete" event.
     */
    isComplete?: boolean;

    /**
     * Optional custom stage definitions.
     */
    stages?: LoadingStage[];
}

const DEFAULT_STAGES: LoadingStage[] = [
    {
        stage: "initializing",
        title: "Preparing assessment",
        description:
            "Preparing your building information and environmental data.",
    },
    {
        stage: "resilience",
        title: "Assessing resilience score",
        description:
            "Analyzing the structural characteristics of your building.",
    },
    {
        stage: "hazard",
        title: "Running hazard engine",
        description:
            "Evaluating seismic activity, faults, soil conditions, and environmental factors.",
    },
    {
        stage: "llm",
        title: "Getting AI feedback",
        description:
            "Generating an understandable explanation of the assessment results.",
    },
    {
        stage: "saving",
        title: "Saving assessment",
        description: "Securely saving your assessment results.",
    },
];

export default function MultiStageLoadingDisplay({
    stageStatuses,
    statusText,
    isComplete = false,
    stages = DEFAULT_STAGES,
}: MultiStageLoadingDisplayProps) {
    /*
     * Progress is milestone-based rather than simply
     * counting stages because resilience and hazard run
     * concurrently.
     */
    const getProgressPercentage = () => {
        if (isComplete) {
            return 100;
        }

        const initializingComplete = stageStatuses.initializing === "completed";

        const resilienceComplete = stageStatuses.resilience === "completed";

        const hazardComplete = stageStatuses.hazard === "completed";

        const llmComplete = stageStatuses.llm === "completed";

        const savingComplete = stageStatuses.saving === "completed";

        if (savingComplete) {
            return 100;
        }

        if (llmComplete) {
            return 80;
        }

        if (resilienceComplete && hazardComplete) {
            return 60;
        }

        if (resilienceComplete || hazardComplete) {
            return 40;
        }

        if (initializingComplete) {
            return 20;
        }

        return 5;
    };

    const progressPercent = getProgressPercentage();

    const activeStages = stages.filter(
        (stage) => stageStatuses[stage.stage] === "active",
    );

    const getHeaderDescription = () => {
        if (isComplete) {
            return "Your earthquake risk assessment has been generated successfully.";
        }

        if (activeStages.length > 1) {
            return "We are analyzing your building and its surrounding environment simultaneously.";
        }

        return statusText;
    };

    return (
        <div className="fixed inset-0 z-1000 overflow-y-auto bg-black/60 backdrop-blur-sm">
            <div className="min-h-full flex items-center justify-center p-4 md:p-6">
                <div className="w-full max-w-2xl mx-auto space-y-6 my-auto py-6 animate-in fade-in slide-in-from-bottom-3 duration-300">
                    {/* Header */}
                    <div className="text-center py-4">
                        <div className="w-16 h-16 bg-blue-50 border border-blue-200 text-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-sm">
                            {isComplete ? (
                                <Check className="w-8 h-8 text-emerald-600 stroke-[2.5]" />
                            ) : (
                                <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                            )}
                        </div>

                        {/* Changed to text-white for accessible contrast against the dark overlay */}
                        <h2 className="text-2xl font-bold tracking-tight text-white">
                            {isComplete
                                ? "Analysis Complete"
                                : "Analyzing Your Building"}
                        </h2>

                        {/* Changed to text-slate-300 for readable contrast against the dark overlay */}
                        <p className="mt-2 text-slate-300 text-sm max-w-md mx-auto leading-relaxed">
                            {getHeaderDescription()}
                        </p>
                    </div>

                    {/* Progress Card */}
                    <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-xl">
                        {/* Progress Header */}
                        <div className="flex items-center justify-between mb-3 text-sm font-bold">
                            <span className="text-slate-700">
                                Calculation Progress
                            </span>

                            <span
                                className={
                                    isComplete
                                        ? "text-emerald-600"
                                        : "text-blue-600"
                                }
                            >
                                {progressPercent}%
                            </span>
                        </div>

                        {/* Progress Bar */}
                        <div className="h-2.5 w-full bg-slate-100 rounded-full overflow-hidden">
                            <div
                                className={`h-full rounded-full transition-all duration-700 ease-out ${
                                    isComplete
                                        ? "bg-emerald-500"
                                        : "bg-blue-600"
                                }`}
                                style={{
                                    width: `${progressPercent}%`,
                                }}
                            />
                        </div>

                        {/* Timeline */}
                        <div className="mt-8 space-y-6">
                            {stages.map((stage, index) => {
                                const status = stageStatuses[stage.stage];

                                const isActive = status === "active";

                                const isCompleted = status === "completed";

                                return (
                                    <div
                                        key={stage.stage}
                                        className="relative flex gap-4"
                                    >
                                        {/* Connector Line */}
                                        {index < stages.length - 1 && (
                                            <div
                                                className={`absolute left-4.75 top-10 bottom-0 w-0.5 transition-colors duration-500 ${
                                                    isCompleted
                                                        ? "bg-emerald-200"
                                                        : "bg-slate-100"
                                                }`}
                                            />
                                        )}

                                        {/* Status Indicator */}
                                        <div className="relative z-10 shrink-0 w-10 h-10 flex items-center justify-center">
                                            {isCompleted ? (
                                                <div className="w-10 h-10 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-600 flex items-center justify-center transition-all duration-300">
                                                    <Check className="w-5 h-5 stroke-[2.5]" />
                                                </div>
                                            ) : isActive ? (
                                                <div className="w-10 h-10 rounded-full bg-blue-50 border border-blue-200 text-blue-600 flex items-center justify-center transition-all duration-300">
                                                    <Loader2 className="w-5 h-5 animate-spin" />
                                                </div>
                                            ) : (
                                                <div className="w-10 h-10 rounded-full bg-white border border-slate-200 text-slate-400 flex items-center justify-center font-bold text-sm">
                                                    {index + 1}
                                                </div>
                                            )}
                                        </div>

                                        {/* Stage Content */}
                                        <div className="flex-1 pt-1.5">
                                            <div className="flex items-center gap-2 flex-wrap">
                                                <span
                                                    className={`text-sm font-bold ${
                                                        isActive
                                                            ? "text-blue-600"
                                                            : isCompleted
                                                              ? "text-slate-800"
                                                              : "text-slate-400"
                                                    }`}
                                                >
                                                    {stage.title}
                                                </span>

                                                {isActive && (
                                                    <span className="bg-blue-50 text-blue-600 border border-blue-100 text-[10px] font-extrabold px-2 py-0.5 rounded-full uppercase tracking-wider">
                                                        In Progress
                                                    </span>
                                                )}
                                            </div>

                                            <p
                                                className={`text-xs mt-1 leading-relaxed ${
                                                    isCompleted
                                                        ? "text-slate-400"
                                                        : isActive
                                                          ? "text-slate-600 font-medium"
                                                          : "text-slate-400"
                                                }`}
                                            >
                                                {stage.description}
                                            </p>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    {/* Information Box */}
                    {!isComplete && (
                        <div className="flex gap-3 bg-white border border-slate-200 text-slate-600 p-4 rounded-xl text-xs leading-relaxed shadow-sm">
                            <Info className="w-4 h-4 shrink-0 text-slate-400 mt-0.5" />

                            <span>
                                Please keep this tab open while we analyze your
                                building and environmental conditions.
                            </span>
                        </div>
                    )}

                    {/* Completion Announcement */}
                    {isComplete && (
                        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm font-semibold p-4 rounded-xl text-center shadow-md animate-in zoom-in-95 duration-300">
                            Assessment generated successfully! Preparing your
                            dashboard workspace...
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
