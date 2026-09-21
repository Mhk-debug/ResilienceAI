"use client";

/**
 * The pre-landing behaviour of `/`, preserved verbatim behind `/?resume=1`.
 *
 * Signed in  → the most recent assessment, else the form.
 * Anonymous  → the assessment id left in localStorage, else the form.
 *
 * Demo links, bookmarks and recorded walkthroughs keep working unchanged; the landing page is the
 * default for `/` from now on.
 */

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { BASE_API_URL } from "@/utils/constants";

export default function ResumeRedirect() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) return;

    if (isAuthenticated && user) {
      fetch(`${BASE_API_URL}/assessment?limit=1`, { credentials: "include" })
        .then((res) => (res.ok ? res.json() : Promise.reject(new Error("list failed"))))
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
      return;
    }

    try {
      const latestAssessment = window.localStorage.getItem("latestAssessmentId");
      router.replace(latestAssessment ? `/dashboard/${latestAssessment}` : "/form");
    } catch {
      router.replace("/form");
    }
  }, [isAuthenticated, isLoading, user, router]);

  return (
    <main className="flex min-h-[80vh] items-center bg-[#0b1524] px-6">
      <p className="mx-auto max-w-3xl text-sm text-white/60">Restoring your last assessment…</p>
    </main>
  );
}
