"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function Home() {
    const router = useRouter();

    useEffect(() => {
        const latestAssessment = localStorage.getItem("latestAssessmentId");

        if (!latestAssessment) {
            router.replace("/form");
            return;
        }

        try {
            router.replace(`/dashboard/${latestAssessment}`);
        } catch {
            localStorage.removeItem("earthquake_assessment");
            router.replace("/form");
        }
    }, [router]);

    return (
        <div className="flex min-h-screen items-center justify-center bg-background">
            <div className="flex flex-col items-center gap-5 rounded-xl border bg-card p-8 text-center shadow-sm">
                <div className="h-10 w-10 animate-spin rounded-full border-4 border-muted border-t-orange-500" />

                <div>
                    <h1 className="text-lg font-semibold text-foreground">
                        Loading Assessment
                    </h1>
                    <p className="mt-2 text-sm text-muted-foreground">
                        Preparing your resilience dashboard...
                    </p>
                </div>
            </div>
        </div>
    );
}