function AssessmentNotFound() {
    return (
        <div className="flex min-h-[60vh] items-center justify-center">
            <div className="flex max-w-md flex-col items-center gap-5 rounded-xl border bg-white p-8 text-center shadow-sm">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
                    <svg
                        className="h-6 w-6 text-muted-foreground"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        viewBox="0 0 24 24"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M9 13h6m-3-3v6m8-2a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                    </svg>
                </div>

                <div>
                    <h2 className="text-lg font-semibold text-foreground">
                        Assessment Not Found
                    </h2>
                    <p className="mt-2 text-sm text-muted-foreground">
                        We could not find an assessment matching this ID.
                        Please check the link and try again.
                    </p>
                </div>
            </div>
        </div>
    );
}

export default AssessmentNotFound;