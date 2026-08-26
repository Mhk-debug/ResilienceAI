"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { History, Plus, RefreshCw, FileSearch } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/lib/auth-context";
import { BASE_API_URL } from "@/utils/constants";
import type { AssessmentSummary } from "./AssessmentHistoryCard";
import AssessmentHistoryCard from "./AssessmentHistoryCard";
import AssessmentHistoryLoading from "./AssessmentHistoryLoading";
import AssessmentHistoryEmpty from "./AssessmentHistoryEmpty";

interface AssessmentHistoryResponse {
    items: AssessmentSummary[];
    total: number;
    limit: number;
    offset: number;
}

const PAGE_SIZE = 20;

function AssessmentHistoryPage() {
    const { isAuthenticated, isLoading: authLoading } = useAuth();
    const [assessments, setAssessments] = useState<AssessmentSummary[]>([]);
    const [total, setTotal] = useState(0);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadHistory = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await fetch(
                `${BASE_API_URL}/assessment/history?limit=${PAGE_SIZE}&offset=0`,
                { credentials: "include" }
            );
            if (!response.ok) {
                throw new Error(`Server returned status ${response.status}`);
            }
            const data: AssessmentHistoryResponse = await response.json();
            setAssessments(data.items);
            setTotal(data.total);
        } catch (err) {
            console.error("Failed to load assessment history:", err);
            setError(
                "We couldn't load your assessment history. Please try again."
            );
            setAssessments([]);
            setTotal(0);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        if (authLoading || !isAuthenticated) return;

        // Defer to a microtask to avoid synchronous setState within the effect
        // (matches the pattern used in the dashboard page).
        const timer = window.setTimeout(() => {
            void loadHistory();
        }, 0);

        return () => {
            window.clearTimeout(timer);
        };
    }, [authLoading, isAuthenticated, loadHistory]);

    if (authLoading || isLoading) {
        return <AssessmentHistoryLoading />;
    }

    return (
        <div className="mx-auto w-full max-w-6xl px-6 py-8 md:px-10 md:py-10">
            <header className="mb-8 flex flex-wrap items-end justify-between gap-4">
                <div className="space-y-1.5">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
                        codeTrio · STIMU
                    </span>
                    <h1 className="flex items-center gap-2.5 text-2xl font-semibold tracking-tight text-slate-900 md:text-3xl">
                        <History className="h-6 w-6 text-blue-600" />
                        Assessment History
                    </h1>
                    <p className="max-w-xl text-sm text-slate-500">
                        Browse and revisit every earthquake resilience
                        assessment you&apos;ve created. Click any card to open the
                        full report.
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={loadHistory}
                        disabled={isLoading}
                    >
                        <RefreshCw
                            className={
                                isLoading
                                    ? "h-3.5 w-3.5 animate-spin"
                                    : "h-3.5 w-3.5"
                            }
                        />
                        Refresh
                    </Button>
                    <Link href="/form">
                        <Button size="sm">
                            <Plus className="h-3.5 w-3.5" />
                            New assessment
                        </Button>
                    </Link>
                </div>
            </header>
            <Separator className="mb-6" />
            {error ? (
                <Alert variant="destructive" className="max-w-2xl">
                    <AlertTitle>Couldn&apos;t load history</AlertTitle>
                    <AlertDescription>
                        {error}{" "}
                        <button
                            type="button"
                            onClick={loadHistory}
                            className="font-semibold underline underline-offset-2 hover:no-underline"
                        >
                            Try again
                        </button>
                    </AlertDescription>
                </Alert>
            ) : assessments.length === 0 ? (
                <AssessmentHistoryEmpty />
            ) : (
                <>
                    <div className="mb-4 flex items-center justify-between text-xs text-slate-500">
                        <span className="flex items-center gap-1.5">
                            <FileSearch className="h-3.5 w-3.5" />
                            Showing {assessments.length} of {total} assessment
                            {total === 1 ? "" : "s"}
                        </span>
                    </div>
                    <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
                        {assessments.map((a) => (
                            <AssessmentHistoryCard key={a.id} assessment={a} />
                        ))}
                    </div>
                </>
            )}
        </div>
    );
}

export default AssessmentHistoryPage;
