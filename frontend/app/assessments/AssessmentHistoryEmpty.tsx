import Link from "next/link";
import { Activity, FilePlus2, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";

function AssessmentHistoryEmpty() {
    return (
        <div className="mx-auto flex w-full max-w-2xl flex-col items-center justify-center px-6 py-20 text-center">
            <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-50 text-blue-600 ring-1 ring-blue-100">
                <Activity className="h-8 w-8" />
            </div>

            <h2 className="text-xl font-semibold tracking-tight text-slate-900 md:text-2xl">
                No assessments yet
            </h2>

            <p className="mt-2 max-w-md text-sm leading-relaxed text-slate-500">
                Your past resilience assessments will appear here. Run a new
                assessment to evaluate a building&apos;s earthquake vulnerability
                and environmental hazard exposure.
            </p>

            <div className="mt-6 flex items-center gap-2 text-xs text-slate-400">
                <MapPin className="h-3.5 w-3.5" />
                <span>Each assessment is tied to a geographic location</span>
            </div>

            <Link href="/form" className="mt-8 block">
                <Button className="w-full sm:w-auto">
                    <FilePlus2 className="h-4 w-4" />
                    Create your first assessment
                </Button>
            </Link>
        </div>
    );
}

export default AssessmentHistoryEmpty;