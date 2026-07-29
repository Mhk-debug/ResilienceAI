"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/auth-context";
import { BASE_API_URL } from "@/utils/constants";

export default function Home() {
    const router = useRouter();
    const { user, isAuthenticated, isLoading } = useAuth();

    useEffect(() => {
        if (isLoading) return; // wait for auth check

        if (isAuthenticated && user) {
            // Tier 1: logged-in user → fetch latest from API
            fetch(`${BASE_API_URL}/assessment?limit=1`, { credentials: "include" })
                .then((res) => (res.ok ? res.json() : Promise.reject()))
                .then((assessments) => {
                    if (Array.isArray(assessments) && assessments.length > 0) {
                        router.replace(`/dashboard/${assessments[0].id}`);
                    } else {
                        router.replace("/form");
                    }
                })
                .catch(() => {
                    router.replace("/form");
                });
        } else {
            // Tier 2: anonymous → fall back to localStorage
            try {
                const latestAssessment = localStorage.getItem("latestAssessmentId");
                if (latestAssessment) {
                    router.replace(`/dashboard/${latestAssessment}`);
                } else {
                    router.replace("/form");
                }
            } catch {
                router.replace("/form");
            }
        }
    }, [router, user, isAuthenticated, isLoading]);

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
