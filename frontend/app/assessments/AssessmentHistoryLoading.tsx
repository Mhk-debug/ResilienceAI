import { Skeleton } from "@/components/ui/skeleton";

function AssessmentHistoryLoading() {
    return (
        <div className="mx-auto w-full max-w-6xl px-6 py-8 md:px-10 md:py-10">
            {/* Header skeleton */}
            <div className="mb-8 space-y-2">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-8 w-64" />
                <Skeleton className="h-4 w-96 max-w-full" />
            </div>

            {/* Grid of card skeletons */}
            <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
                {Array.from({ length: 6 }).map((_, i) => (
                    <div
                        key={i}
                        className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs"
                    >
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <Skeleton className="h-4 w-24" />
                                <Skeleton className="h-5 w-16 rounded-full" />
                            </div>
                            <Skeleton className="h-5 w-3/4" />
                            <Skeleton className="h-3 w-full" />
                            <Skeleton className="h-3 w-2/3" />
                            <div className="grid grid-cols-2 gap-3 pt-2">
                                <Skeleton className="h-16 w-full rounded-lg" />
                                <Skeleton className="h-16 w-full rounded-lg" />
                            </div>
                            <Skeleton className="h-9 w-full rounded-md" />
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default AssessmentHistoryLoading;