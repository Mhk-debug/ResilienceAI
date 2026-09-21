import type { Metadata } from "next";
import { Suspense } from "react";

import Hero from "@/components/landing/Hero";
import Descent from "@/components/landing/Descent";
import ShakeLab from "@/components/landing/ShakeLab";
import {
  Evidence,
  Finale,
  HowItWorks,
  LandingFooter,
  MyanmarSection,
} from "@/components/landing/Sections";
import { META } from "@/lib/landing/content";
import ResumeRedirect from "./resume-redirect";

export const metadata: Metadata = {
  title: META.title,
  description: META.description,
};

/**
 * `/` — the public landing page, for signed-in and anonymous visitors alike.
 *
 * The pre-existing behaviour (jump to the latest assessment, else the form) is preserved verbatim
 * behind `/?resume=1`, so demo links and bookmarks behave exactly as before.
 */
export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{ resume?: string }>;
}) {
  const params = await searchParams;

  if (params?.resume === "1") {
    return (
      <Suspense
        fallback={
          <main className="mx-auto flex min-h-[60vh] max-w-3xl items-center px-6">
            <p className="text-sm text-slate-500">Restoring your last assessment…</p>
          </main>
        }
      >
        <ResumeRedirect />
      </Suspense>
    );
  }

  return (
    <main className="landing l-grain flex-1">
      <Hero />
      <Descent />
      <ShakeLab />
      <Evidence />
      <MyanmarSection />
      <HowItWorks />
      <Finale />
      <LandingFooter />
    </main>
  );
}
