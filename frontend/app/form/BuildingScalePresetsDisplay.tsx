type BuildingScalePresetsDisplay = {
    presetTemplates: {
        label: string;
        value: number;
    }[];
    watch: any;
    setValue: any;
    value: string;
    label: string;
};

const DEFAULT_LABEL = "Or select a preset"

function BuildingScalePresetsDisplay({ presetTemplates, watch, setValue, value, label = DEFAULT_LABEL }: BuildingScalePresetsDisplay) {
    return (
        <div className="space-y-1.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block">
                {label}
            </span>
            <div className="grid grid-cols-2 gap-2">
                {presetTemplates.map((preset) => {
                    const currentVal = watch(value);
                    const isSelected = Number(currentVal) === preset.value;
                    return (
                        <button
                            key={preset.value}
                            type="button"
                            onClick={() =>
                                setValue(value, preset.value, {
                                    shouldValidate: true,
                                })
                            }
                            className={`text-left p-2.5 rounded-lg border text-xs transition-all duration-150 ${
                                isSelected
                                    ? "bg-teal-50 border-teal-200 text-teal-900 font-medium shadow-sm ring-1 ring-teal-500/10"
                                    : "bg-slate-50/50 border-slate-100 text-slate-600 hover:bg-slate-100/50 hover:border-slate-200"
                            }`}
                        >
                            <div className="font-semibold">{preset.label}</div>
                            <div className="text-[9px] text-slate-600 mt-0.5">
                                {preset.value.toLocaleString()} {value=="area_sq_ft" && "sq"} ft
                            </div>
                        </button>
                    );
                })}
            </div>
        </div>
    );
}

export default BuildingScalePresetsDisplay;
