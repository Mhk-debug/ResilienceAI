import { Activity } from "lucide-react";
import React from "react";

function FormHeader() {
    return (
        <>
            {/* Header */}
            <header className="bg-header-gradient px-6 py-4 md:px-10 md:py-5 flex items-center shadow-lg">
                <div className="flex flex-col gap-0.5">
                    <div className="flex items-center gap-2.5">
                        <Activity className="h-5 w-5 text-primary-foreground opacity-80" />
                        <h1 className="text-lg font-bold tracking-tight text-primary-foreground md:text-xl">
                            Earthquake Risk Assessment AI
                        </h1>
                    </div>
                    <p className="text-xs font-medium tracking-widest text-primary-foreground/50 pl-7 uppercase">
                        codeTrio &nbsp;·&nbsp; STIMU
                    </p>
                </div>
            </header>
            {/* Page hero */}
            <div className="bg-card border-b border-border px-4 py-8 text-center">
                <span className="inline-block rounded-full border border-border bg-muted px-3 py-0.5 text-[11px] font-semibold uppercase tracking-widest text-muted-foreground mb-3">
                    codeTrio | STIMU
                </span>
                <h2 className="text-2xl font-bold text-foreground tracking-tight">
                    Earthquake Risk Assessment
                </h2>
                <p className="mt-1.5 text-sm text-muted-foreground max-w-md mx-auto">
                    Enter building details and select your location to evaluate
                    seismic vulnerability using our AI model.
                </p>
            </div>
        </>
    );
}

export default FormHeader;
