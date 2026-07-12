function AssessmentLoading() {
    return (
        <div className="flex min-h-[60vh] items-center justify-center">
            <div className="flex flex-col items-center gap-4 rounded-xl border bg-white p-8 shadow-sm">
                <div className="h-10 w-10 animate-spin rounded-full border-4 border-muted border-t-primary" />

                <div className="text-center">
                    <h2 className="text-lg font-semibold text-foreground">
                        Loading Assessment
                    </h2>
                    <p className="mt-1 text-sm text-muted-foreground">
                        Retrieving your resilience analysis...
                    </p>
                </div>
            </div>
        </div>
    );
}

export default AssessmentLoading;