import { ColorClasses, type TailwindBaseColor } from "@/utils/constants";
import { Controller } from "react-hook-form";

type StructuralComponentCheckboxProps = {
    control: any;
    title: string;
    desc: string;
    name: string;
    color: TailwindBaseColor;
};

function StructuralComponentCheckbox({
    control,
    name,
    desc,
    title,
    color,
}: StructuralComponentCheckboxProps) {
    const selectedColors = ColorClasses[color];

    return (
        <Controller
            name={name}
            control={control}
            render={({ field }) => (
                <div
                    onClick={() => field.onChange(field.value === 1 ? 0 : 1)}
                    style={
                        field.value === 1
                            ? {
                                  backgroundColor: selectedColors.background,
                                  borderColor: selectedColors.border,
                                  color: selectedColors.text,
                              }
                            : undefined
                    }
                    className={`flex flex-col p-4 rounded-xl border transition-all duration-150 cursor-pointer select-none ${
                        field.value === 1
                            ? "hover:opacity-90"
                            : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50"
                    }`}
                >
                    <div className="flex items-center justify-between gap-2">
                        <span className="text-xs font-semibold">{title}</span>
                        <div
                            style={
                                field.value === 1
                                    ? { backgroundColor: selectedColors.toggle }
                                    : undefined
                            }
                            className={`w-8 h-4 rounded-full p-0.5 transition-colors duration-250 ${
                                field.value === 1 ? "" : "bg-slate-200"
                            }`}
                        >
                            <div
                                className={`w-3 h-3 bg-white rounded-full shadow-sm transform transition-transform duration-250 ${
                                    field.value === 1
                                        ? "translate-x-4"
                                        : "translate-x-0"
                                }`}
                            />
                        </div>
                    </div>
                    <p className="text-xs text-slate-600 mt-2 font-normal leading-relaxed">
                        {desc}
                    </p>
                </div>
            )}
        />
    );
}

export default StructuralComponentCheckbox;
