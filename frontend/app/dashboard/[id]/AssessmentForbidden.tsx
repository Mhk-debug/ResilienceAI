"use client";

import Link from "next/link";

function AssessmentForbidden() {
    return (
        <div className="flex min-h-[60vh] items-center justify-center">
            <div className="flex max-w-md flex-col items-center gap-5 rounded-xl border bg-white p-8 text-center shadow-sm">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-50">
                    <svg
                        className="h-6 w-6 text-amber-500"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        viewBox="0 0 24 24"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M12 15v2m0 0v2m0-2h2m-2 0H10m9.364-7.364A9 9 0 1112 3a9 9 0 017.364 4.636z"
                        />
                    </svg>
                </div>

                <div>
                    <h2 className="text-lg font-semibold text-foreground">
                        Access Denied
                    </h2>
                    <p className="mt-2 text-sm text-muted-foreground">
                        This assessment belongs to another account. You do not
                        have permission to view it.
                    </p>
                </div>

                <Link
                    href="/dashboard"
                    className="rounded-lg bg-primary px-5 py-2 text-sm font-medium text-primary-foreground transition hover:bg-primary/90"
                >
                    Go to Dashboard
                </Link>
            </div>
        </div>
    );
}

export default AssessmentForbidden;