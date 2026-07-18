"use client";

import type { AssessmentIDResponse } from "@/app/types";
import { LocalStorageManager } from "@/components/local-storage-manager";
import { calculateRiskScore, getRiskLevel } from "@/utils/risk";
import { formatTimeAgo } from "@/utils/tools";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import AssessmentLoading from "./AssessmentLoading";
import AssessmentError from "./AssessmentError";
import AssessmentNotFound from "./AssessmentNotFound";
import { Calendar } from "lucide-react";
import BuildingProfileCard from "./BuildingProfileCard";
import RiskGauge from "./RiskGauge";
import RiskInterpretation from "./RiskInterpretation";
import ContributingFactors from "./ContributingFactors";
import AiInsights from "./AiInsights";
import SupportingEvidence from "./SupportingEvidence";
import Footer from "@/components/footer";

function DashboardPage() {
    const params = useParams();
    const id = params.id as string;

    const [assessment, setAssessment] = useState<AssessmentIDResponse | null>(
        null,
    );
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const loadAssessment = async () => {
        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(
                `http://127.0.0.1:8000/api/assessment/${id}`,
            );

            if (response.status == 404) {
                return;
            }

            if (!response.ok) {
                throw new Error(`Server returned status ${response.status}`);
            }

            const data = await response.json();
            setAssessment(data);
        } catch (err) {
            if (err instanceof Error) {
                console.error("Failed to load assessment:", err);
                setError("Failed to load assessment.");
            }
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (!id) return;

        // Defer calling loadAssessment to avoid synchronous setState calls within the effect
        const t = setTimeout(() => {
            loadAssessment();
        }, 0);

        return () => clearTimeout(t);
    }, [id]);

    const computedRiskScore = assessment
        ? calculateRiskScore(
              assessment.hazard_score,
              assessment.resilience_score,
          )
        : 0;

    const computedRiskLevel = getRiskLevel(computedRiskScore);

    if (isLoading) {
        return <AssessmentLoading />;
    }

    if (error) {
        return (
            <AssessmentError message={error} onRetry={() => loadAssessment()} />
        );
    }

    if (!assessment) {
        return <AssessmentNotFound />;
    }

    return (
        <div className="min-h-screen bg-slate-100 pb-20 selection:bg-blue-600 selection:text-white font-sans">
            <LocalStorageManager id={assessment.id} />

            <div className="max-w-7xl mx-auto px-0 xs:px-4 sm:px-6 lg:px-8 mt-8 space-y-12">
                <div className="w-full border-b border-slate-200 pb-5 space-y-2">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                        <div className="space-y-1">
                            <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                                Code Trio | AI innovation 2026
                            </span>
                            <h1 className="text-2xl md:text-3xl font-display font-semibold tracking-tight text-slate-900 leading-tight">
                                ResilienceAI Dashboard
                            </h1>
                            <p className="text-xs font-semibold text-blue-600">
                                Assessed Location:{" "}
                                {assessment.place_name ??
                                    `${assessment.latitude} ${assessment.longitude}`}
                            </p>
                        </div>

                        <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-slate-500 font-medium">
                            <span className="flex items-center gap-1.5">
                                <Calendar className="w-4 h-4 text-slate-400" />
                                Assessed:{" "}
                                <strong className="text-slate-700">
                                    {formatTimeAgo(
                                        new Date(assessment.created_at),
                                    )}
                                </strong>
                            </span>
                        </div>
                    </div>
                </div>
                <section id="building-overview-section" className="space-y-4">
                    <div className="grid grid-cols-1 lg:grid-cols-15 gap-8 items-stretch">
                        {/* Left Column - Building Profile Card */}
                        <div className="lg:col-span-8">
                            <BuildingProfileCard
                                context={
                                    assessment.building.building_llm_context
                                }
                                resilienceScore={assessment.resilience_score}
                            />
                        </div>

                        {/* Right Column - Earthquake Risk Gauge */}
                        <div className="lg:col-span-7">
                            <RiskGauge
                                score={computedRiskScore}
                                level={computedRiskLevel}
                                resilienceScore={assessment.resilience_score}
                                hazardScore={assessment.hazard_score}
                            />
                        </div>
                    </div>
                </section>

                <div className="space-y-12 pb-12">
                    <RiskInterpretation llm={assessment.llm} />

                    <ContributingFactors
                        environmentalContext={
                            assessment.hazard.environmental_context
                        }
                        indicators={assessment.hazard.indicators}
                    />

                    <AiInsights llm={assessment.llm} />

                    <SupportingEvidence events={assessment.hazard.events} />
                </div>

                <Footer />
            </div>
        </div>
    );
}

export default DashboardPage;
