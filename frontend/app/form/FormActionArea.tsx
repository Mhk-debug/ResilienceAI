import { BarChart2, LoaderIcon, RotateCcw } from "lucide-react";

type FormActionAreaProps = {
    isLoading: boolean;
    handleFormReset: () => void;
};

function FormActionArea({ isLoading, handleFormReset }: FormActionAreaProps) {
    return (
        <div className="rounded-xl bg-card border border-border shadow-card px-5 py-5 flex flex-col sm:flex-row items-center gap-3">
            <button
                type="reset"
                onClick={handleFormReset}
                className="flex items-center justify-center gap-2 w-full sm:w-auto rounded-lg border border-border bg-card px-5 py-2.5 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent transition-all"
            >
                <RotateCcw className="h-4 w-4" />
                Reset Form
            </button>
            <button
                type="submit"
                disabled={isLoading}
                className="flex items-center justify-center gap-2 w-full sm:flex-1 rounded-lg bg-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground hover:opacity-90 transition-all shadow-sm disabled:cursor-not-allowed"
            >
                {isLoading ? (
                    <LoaderIcon className="animate-spin" />
                ) : (
                    <BarChart2 className="h-4 w-4" />
                )}
                {isLoading ? (
                    "Running Simulation..."
                ) : (
                    "Analyze Earthquake Risk"
                )}
            </button>
        </div>
    );
}

export default FormActionArea;
