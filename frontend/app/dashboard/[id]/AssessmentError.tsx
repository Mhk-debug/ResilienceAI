"use client";

interface AssessmentErrorProps {
    message: string;
    onRetry: () => void;
}

function AssessmentError({ message, onRetry }: AssessmentErrorProps) {
    return (
        <div className="flex min-h-[60vh] items-center justify-center">
            <div className="flex max-w-md flex-col items-center gap-5 rounded-xl border bg-white p-8 text-center shadow-sm">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-50">
                    <svg
                        className="h-6 w-6 text-red-500"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        viewBox="0 0 24 24"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
                        />
                    </svg>
                </div>

                <div>
                    <h2 className="text-lg font-semibold text-foreground">
                        Unable to Load Assessment
                    </h2>
                    <p className="mt-2 text-sm text-muted-foreground">
                        {message}
                    </p>
                </div>

                <button
                    onClick={onRetry}
                    className="rounded-lg bg-primary px-5 py-2 text-sm font-medium text-primary-foreground transition hover:bg-primary/90"
                >
                    Try Again
                </button>
            </div>
        </div>
    );
}

export default AssessmentError;