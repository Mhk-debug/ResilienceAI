"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import LocationPicker from "@/components/location-picker";
import {
    Activity,
    Building2,
    Layers,
    Wrench,
    RotateCcw,
    BarChart2,
    Globe,
    AlertCircle,
    Info,
    Scaling,
} from "lucide-react";
import { useState } from "react";
import z from "zod";
import { Controller, useForm, type Path, type Resolver } from "react-hook-form";
import { useRouter } from "next/navigation";

const formSchema = z.object({
    latitude: z
        .number()
        .min(-90, "Latitude must be between -90 and 90")
        .max(90, "Latitude must be between -90 and 90"),
    longitude: z
        .number()
        .min(-180, "Longitude must be between -180 and 180")
        .max(180, "Longitude must be between -180 and 180"),
    count_floors_pre_eq: z.coerce
        .number()
        .int()
        .min(1, "Number of floors must be at least 1")
        .max(10, "Maximum limit of floors is 10"),
    age: z.coerce
        .number()
        .nonnegative("Building age must be 0 or greater")
        .max(999, "Age exceeds normal engineering limits"),
    foundation_type: z.enum(["i", "u", "w", "r", "h"] as const),
    roof_type: z.enum(["q", "x", "n"] as const),
    ground_floor_type: z.enum(["x", "v", "m", "f", "z"] as const),
    has_superstructure_mud_mortar_stone: z.union([z.literal(0), z.literal(1)]),
    has_superstructure_rc_engineered: z.union([z.literal(0), z.literal(1)]),
    has_superstructure_cement_mortar_brick: z.union([
        z.literal(0),
        z.literal(1),
    ]),
    has_superstructure_rc_non_engineered: z.union([z.literal(0), z.literal(1)]),
    has_superstructure_adobe_mud: z.union([z.literal(0), z.literal(1)]),
    has_superstructure_timber: z.union([z.literal(0), z.literal(1)]),
    area_sq_ft: z.coerce
        .number()
        .positive("Building footprint must be a positive number")
        .min(70, "Footprint must be at least 70 sq ft")
        .max(5000, "Maximum limit of footprint is 5,000 sq ft"),
    height_ft: z.coerce
        .number()
        .positive("Building height must be a positive number")
        .min(6, "Height must be at least 6 ft")
        .max(305, "Maximum height is 305 ft"),
});

type FormFields = z.infer<typeof formSchema>;

const DEFAULT_FORM_VALUES: FormFields = {
    latitude: 37.7749, // 45 Ward North Dagon Myanmar
    longitude: -122.4194,
    count_floors_pre_eq: 2,
    age: 25,
    foundation_type: "i",
    roof_type: "q",
    ground_floor_type: "x",
    has_superstructure_mud_mortar_stone: 0,
    has_superstructure_rc_engineered: 1,
    has_superstructure_cement_mortar_brick: 1,
    has_superstructure_rc_non_engineered: 0,
    has_superstructure_adobe_mud: 0,
    has_superstructure_timber: 0,
    area_sq_ft: 1500, // standard detached house footprint default
    height_ft: 24, // standard 2-story building height default (e.g. 12ft per floor)
};

const BASE_API_URL = "http://127.0.0.1:8000";

export default function FormPage() {
    const router = useRouter();

    const [isLoading, setIsLoading] = useState(false);

    const {
        register,
        handleSubmit,
        setValue,
        watch,
        reset,
        control,
        setError,
        clearErrors,
        formState: { errors },
    } = useForm<FormFields>({
        resolver: zodResolver(formSchema) as Resolver<FormFields>,
        defaultValues: DEFAULT_FORM_VALUES,
    });

    // Watch fields to update coordinates reactively
    const watchedLat = watch("latitude");
    const watchedLng = watch("longitude");

    // Handle setting location via MapPicker
    const handleLocationChange = (lat: number, lng: number) => {
        setValue("latitude", parseFloat(lat.toFixed(6)));
        setValue("longitude", parseFloat(lng.toFixed(6)));

        // Clear errors if set
        if (errors.latitude || errors.longitude) {
            clearErrors(["latitude", "longitude"]);
        }
    };

    const onSubmit = async (data: FormFields) => {
        clearErrors();
        // 1. Validate using Zod
        const validationResult = formSchema.safeParse(data);
        if (!validationResult.success) {
            validationResult.error.issues.forEach((issue) => {
                const pathStr = issue.path[0] as Path<FormFields>;
                setError(pathStr, { message: issue.message });
            });

            return;
        }

        setIsLoading(true);

        try {
            // 2. Single unified API request to the backend orchestrator
            const response = await fetch(`${BASE_API_URL}/api/assessment/process`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data), // Sends all FormFields (including lat, lon) together
            });

            // 3. Handle network or server-side failure
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Server failed to process the assessment.");
            }

            const result = await response.json();
            const assessmentID = result.assessment_id;

            // 4. Clean absolute redirect to the dashboard
            router.push(`/dashboard/${assessmentID}`);

        } catch (err: unknown) {
            window.scrollTo({
                top: 0,
                behavior: "smooth",
            });
            if (err instanceof Error) {
                setError("root.serverError", {
                    message: `Assessment failed: ${err.message}`,
                });
            }
        } finally {
            setIsLoading(false);
        }
    };

    // Completely clear form and coordinates back to absolute default
    const handleFormReset = () => {
        reset(DEFAULT_FORM_VALUES);
        clearErrors();
    };

    return (
        <div className="flex min-h-full flex-col bg-background">
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

            {/* Form */}
            <main className="flex-1 px-4 py-8 md:px-6 max-w-4xl mx-auto w-full">
                {/* Server / API error banner */}
                {errors.root?.serverError && (
                    <div className="bg-rose-50 border border-rose-200 text-rose-800 rounded-xl p-4 flex items-start gap-3">
                        <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-rose-600" />
                        <div className="space-y-1">
                            <h4 className="text-sm font-bold text-rose-900">
                                Analyzer Connection Issue
                            </h4>
                            <p className="text-xs leading-relaxed">
                                {errors.root.serverError.message}
                            </p>
                        </div>
                    </div>
                )}

                {/* Validation error summary */}
                {Object.keys(errors).length > 0 &&
                    !(Object.keys(errors).length === 1 && errors.root) && (
                        <div
                            id="validation-error-alert"
                            className="bg-amber-50 border border-amber-200 text-amber-800 rounded-xl p-4 flex items-start gap-3"
                        >
                            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-amber-600" />
                            <div className="space-y-1">
                                <h4 className="text-sm font-bold text-amber-900">
                                    Form Validation Incomplete
                                </h4>
                                <p className="text-xs">
                                    Please fix the highlighted fields below (
                                    {Object.keys(errors).length} errors total).
                                </p>
                            </div>
                        </div>
                    )}
                <form
                    className="flex flex-col gap-5"
                    onSubmit={handleSubmit(onSubmit)}
                    id="seismic-assessment-form"
                >
                    {/* Section 1: Basic Building Info */}
                    <div className="rounded-xl bg-card border border-border shadow-card overflow-hidden">
                        <div className="flex items-center gap-3 px-5 py-4 border-b border-border bg-muted/30">
                            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                                <Building2 className="h-4 w-4 text-primary" />
                            </span>
                            <div>
                                <p className="text-sm font-semibold text-foreground">
                                    Basic Building Info
                                </p>
                                <p className="text-xs text-muted-foreground">
                                    General characteristics of the structure
                                </p>
                            </div>
                        </div>

                        <div className="px-5 py-5 grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4">
                            <div className="flex flex-col gap-1.5">
                                <label
                                    className="text-xs font-semibold text-slate-700"
                                    htmlFor="input-count-floors"
                                >
                                    Number of Floors{" "}
                                    <span className="text-rose-500">*</span>
                                </label>
                                <div className="relative">
                                    <input
                                        type="number"
                                        min="1"
                                        max="10"
                                        {...register("count_floors_pre_eq", {
                                            valueAsNumber: true,
                                        })}
                                        className="w-full bg-white border border-slate-200 text-slate-900 placeholder-slate-400 rounded-lg py-2.5 px-3.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600 transition-all font-sans"
                                        placeholder="e.g. 2"
                                        id="input-count-floors"
                                    />
                                    <span className="absolute right-3.5 top-3 text-[10px] font-mono uppercase text-slate-400 tracking-wider">
                                        Floors (1 - 10)
                                    </span>
                                </div>
                                <p className="text-[11px] text-slate-500 leading-normal flex items-center gap-1 mt-1">
                                    <Info className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                                    Total number of above-ground floors (limit 1
                                    to 10).
                                </p>
                                {errors.count_floors_pre_eq && (
                                    <span className="text-[10px] text-rose-600 font-mono block">
                                        {errors.count_floors_pre_eq.message}
                                    </span>
                                )}
                            </div>

                            <div className="flex flex-col gap-1.5">
                                <label
                                    className="text-xs font-semibold text-slate-700"
                                    htmlFor="input-age"
                                >
                                    Building Age (Years){" "}
                                    <span className="text-rose-500">*</span>
                                </label>
                                <div className="relative">
                                    <input
                                        type="number"
                                        min="0"
                                        max="200"
                                        {...register("age", {
                                            valueAsNumber: true,
                                        })}
                                        className="w-full bg-white border border-slate-200 text-slate-900 placeholder-slate-400 rounded-lg py-2.5 px-3.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600 transition-all font-sans"
                                        placeholder="e.g. 25"
                                        id="input-age"
                                    />
                                    <span className="absolute right-3.5 top-3 text-[10px] font-mono uppercase text-slate-400 tracking-wider">
                                        Years Old
                                    </span>
                                </div>
                                <p className="text-[11px] text-slate-500 leading-normal flex items-center gap-1 mt-1">
                                    <Info className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                                    Approximate age of the structure.
                                </p>
                                {errors.age && (
                                    <span className="text-[10px] text-rose-600 font-mono block">
                                        {errors.age.message}
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="bg-white border border-slate-200 rounded-2xl space-y-6 shadow-sm">
                        <section className="space-y-4">
                            <div className="flex items-center gap-3 px-5 py-4 border-b border-border bg-muted/30">
                                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                                    <Scaling className="h-4 w-4 text-primary" />
                                </span>
                                <div>
                                    <p className="text-sm font-semibold text-foreground">
                                        Building Scale & Density
                                    </p>
                                    <p className="text-xs text-muted-foreground">
                                        These inputs help estimate how mass and
                                        density affect earthquake vulnerability.
                                    </p>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-2 px-6 pb-6 md:px-8 md:pb-8">
                                {/* Footprint Area Input */}
                                <div className="space-y-4">
                                    <div className="space-y-1.5">
                                        <label
                                            htmlFor="area_sq_ft"
                                            className="text-xs font-semibold text-slate-700 flex items-center justify-between"
                                        >
                                            <span className="flex items-center gap-1.5">
                                                Building Footprint (Plinth Area){" "}
                                                <span className="text-rose-500">
                                                    *
                                                </span>
                                            </span>
                                            <span className="text-[10px] font-mono text-slate-400">
                                                sq ft
                                            </span>
                                        </label>
                                        <div className="relative rounded-xl shadow-sm">
                                            <input
                                                type="number"
                                                id="area_sq_ft"
                                                placeholder="e.g. 1500"
                                                min={70}
                                                max={5000}
                                                {...register("area_sq_ft")}
                                                className="block w-full pl-4 pr-16 py-3 text-sm text-slate-900 placeholder-slate-400 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors duration-150"
                                            />
                                            <div className="absolute inset-y-0 right-0 flex items-center pr-4 pointer-events-none">
                                                <span className="text-xs text-slate-400 font-medium font-mono">
                                                    sq ft
                                                </span>
                                            </div>
                                        </div>
                                        <p className="text-[10px] text-slate-500 leading-relaxed font-normal">
                                            The ground level floor area of the
                                            building. Larger footprints contain
                                            greater inertial mass during seismic
                                            ground acceleration.
                                        </p>
                                        {errors.area_sq_ft && (
                                            <span className="text-[10px] text-rose-600 font-mono block mt-1">
                                                {errors.area_sq_ft.message}
                                            </span>
                                        )}
                                    </div>

                                    {/* Presets for Footprint */}
                                    <div className="space-y-1.5">
                                        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block">
                                            Or select a typical size helper:
                                        </span>
                                        <div className="grid grid-cols-2 gap-2">
                                            {[
                                                {
                                                    label: "Cabin / Cottage",
                                                    value: 600,
                                                    desc: "Small single room / cottage",
                                                },
                                                {
                                                    label: "Standard Home",
                                                    value: 1500,
                                                    desc: "Typical detached suburban home",
                                                },
                                                {
                                                    label: "Large House",
                                                    value: 2500,
                                                    desc: "Spacious detached home or villa",
                                                },
                                                {
                                                    label: "Large Res / Commercial",
                                                    value: 4000,
                                                    desc: "Multi-unit residential, shop-house, or small commercial building",
                                                },
                                            ].map((preset) => {
                                                const currentVal =
                                                    watch("area_sq_ft");
                                                const isSelected =
                                                    Number(currentVal) ===
                                                    preset.value;
                                                return (
                                                    <button
                                                        key={preset.value}
                                                        type="button"
                                                        onClick={() =>
                                                            setValue(
                                                                "area_sq_ft",
                                                                preset.value,
                                                                {
                                                                    shouldValidate: true,
                                                                },
                                                            )
                                                        }
                                                        className={`text-left p-2.5 rounded-lg border text-xs transition-all duration-150 ${
                                                            isSelected
                                                                ? "bg-teal-50 border-teal-200 text-teal-900 font-medium shadow-sm ring-1 ring-teal-500/10"
                                                                : "bg-slate-50/50 border-slate-100 text-slate-600 hover:bg-slate-100/50 hover:border-slate-200"
                                                        }`}
                                                    >
                                                        <div className="font-semibold">
                                                            {preset.label}
                                                        </div>
                                                        <div className="text-[9px] text-slate-400 mt-0.5">
                                                            {preset.value.toLocaleString()}{" "}
                                                            sq ft
                                                        </div>
                                                    </button>
                                                );
                                            })}
                                        </div>
                                    </div>
                                </div>

                                {/* Building Height Input */}
                                <div className="space-y-4">
                                    <div className="space-y-1.5">
                                        <label
                                            htmlFor="height_ft"
                                            className="text-xs font-semibold text-slate-700 flex items-center justify-between"
                                        >
                                            <span className="flex items-center gap-1.5">
                                                Building Height{" "}
                                                <span className="text-rose-500">
                                                    *
                                                </span>
                                            </span>
                                            <span className="text-[10px] font-mono text-slate-400">
                                                feet
                                            </span>
                                        </label>
                                        <div className="relative rounded-xl shadow-sm">
                                            <input
                                                type="number"
                                                id="height_ft"
                                                placeholder="e.g. 24"
                                                min={6}
                                                max={305}
                                                {...register("height_ft")}
                                                className="block w-full pl-4 pr-16 py-3 text-sm text-slate-900 placeholder-slate-400 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition-colors duration-150"
                                            />
                                            <div className="absolute inset-y-0 right-0 flex items-center pr-4 pointer-events-none">
                                                <span className="text-xs text-slate-400 font-medium font-mono">
                                                    ft
                                                </span>
                                            </div>
                                        </div>
                                        <p className="text-[10px] text-slate-500 leading-relaxed font-normal">
                                            Total height from ground base to
                                            roof. Higher structures amplify
                                            rotational moment, displacement, and
                                            whip forces during seismic movement.
                                        </p>
                                        {errors.height_ft && (
                                            <span className="text-[10px] text-rose-600 font-mono block mt-1">
                                                {errors.height_ft.message}
                                            </span>
                                        )}
                                    </div>

                                    {/* Presets for Height */}
                                    <div className="space-y-1.5">
                                        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block">
                                            Or estimate by story height:
                                        </span>
                                        <div className="grid grid-cols-2 gap-2">
                                            {[
                                                {
                                                    label: "1-Story Building",
                                                    value: 12,
                                                    floors: 1,
                                                },
                                                {
                                                    label: "2-Story Building",
                                                    value: 24,
                                                    floors: 2,
                                                },
                                                {
                                                    label: "3-Story Building",
                                                    value: 36,
                                                    floors: 3,
                                                },
                                                {
                                                    label: "Commercial Block",
                                                    value: 60,
                                                    floors: 5,
                                                },
                                            ].map((preset) => {
                                                const currentVal =
                                                    watch("height_ft");
                                                const isSelected =
                                                    Number(currentVal) ===
                                                    preset.value;
                                                return (
                                                    <button
                                                        key={preset.value}
                                                        type="button"
                                                        onClick={() => {
                                                            setValue(
                                                                "height_ft",
                                                                preset.value,
                                                                {
                                                                    shouldValidate: true,
                                                                },
                                                            );
                                                            setValue(
                                                                "count_floors_pre_eq",
                                                                preset.floors,
                                                                {
                                                                    shouldValidate: true,
                                                                },
                                                            );
                                                        }}
                                                        className={`text-left p-2.5 rounded-lg border text-xs transition-all duration-150 ${
                                                            isSelected
                                                                ? "bg-teal-50 border-teal-200 text-teal-900 font-medium shadow-sm ring-1 ring-teal-500/10"
                                                                : "bg-slate-50/50 border-slate-100 text-slate-600 hover:bg-slate-100/50 hover:border-slate-200"
                                                        }`}
                                                    >
                                                        <div className="font-semibold">
                                                            {preset.label}
                                                        </div>
                                                        <div className="text-[9px] text-slate-450 mt-0.5">
                                                            ~{preset.value} ft (
                                                            {preset.floors} fl)
                                                        </div>
                                                    </button>
                                                );
                                            })}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </section>
                    </div>

                    {/* Section 3: Structural Materials Materials */}
                    <div className="rounded-xl bg-card border border-border shadow-card overflow-hidden">
                        <div className="flex items-center gap-3 px-5 py-4 border-b border-border bg-muted/30">
                            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                                <Layers className="h-4 w-4 text-primary" />
                            </span>
                            <div>
                                <p className="text-sm font-semibold text-foreground">
                                    Structural Materials
                                </p>
                                <p className="text-xs text-muted-foreground">
                                    Primary construction materials used
                                </p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 px-6 pt-6 pb-8">
                            {/* Foundation Type Dropdown */}
                            <div className="space-y-2">
                                <label
                                    className="text-xs font-semibold text-slate-700"
                                    htmlFor="select-foundation"
                                >
                                    Foundation Type{" "}
                                    <span className="text-rose-500">*</span>
                                </label>
                                <select
                                    {...register("foundation_type")}
                                    className="w-full bg-white border border-slate-200 text-slate-900 rounded-lg py-2.5 px-3.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600 transition-all cursor-pointer"
                                    id="select-foundation"
                                >
                                    <option value="i">
                                        Reinforced Concrete Foundation
                                    </option>
                                    <option value="u">
                                        Cement-Stone Masonry Foundation
                                    </option>
                                    <option value="w">Timber Foundation</option>
                                    <option value="r">
                                        Mud-Stone Foundation
                                    </option>
                                    <option value="h">
                                        Bamboo / Adobe Foundation
                                    </option>
                                </select>
                                <p className="text-[10px] text-slate-400 leading-normal">
                                    Rigidity matches footing standard.
                                </p>
                            </div>

                            {/* Roof Type Dropdown */}
                            <div className="space-y-2">
                                <label
                                    className="text-xs font-semibold text-slate-700"
                                    htmlFor="select-roof"
                                >
                                    Roof Type{" "}
                                    <span className="text-rose-500">*</span>
                                </label>
                                <select
                                    {...register("roof_type")}
                                    className="w-full bg-white border border-slate-200 text-slate-900 rounded-lg py-2.5 px-3.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600 transition-all cursor-pointer"
                                    id="select-roof"
                                >
                                    <option value="q">
                                        Corrugated Metal Roof
                                    </option>
                                    <option value="x">
                                        Reinforced Concrete Roof
                                    </option>
                                    <option value="n">
                                        Traditional Bamboo / Timber Roof
                                    </option>
                                </select>
                                <p className="text-[10px] text-slate-400 leading-normal">
                                    Impacts top-heavy inertia loading.
                                </p>
                            </div>

                            {/* Ground Floor Type Dropdown */}
                            <div className="space-y-2">
                                <label
                                    className="text-xs font-semibold text-slate-700"
                                    htmlFor="select-ground-floor"
                                >
                                    Ground Floor Type{" "}
                                    <span className="text-rose-500">*</span>
                                </label>
                                <select
                                    {...register("ground_floor_type")}
                                    className="w-full bg-white border border-slate-200 text-slate-900 rounded-lg py-2.5 px-3.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600 transition-all cursor-pointer"
                                    id="select-ground-floor"
                                >
                                    <option value="x">
                                        Reinforced Concrete Floor
                                    </option>
                                    <option value="v">
                                        Brick / Stone Floor
                                    </option>
                                    <option value="m">Timber Floor</option>
                                    <option value="f">Mud Floor</option>
                                    <option value="z">Other</option>
                                </select>
                                <p className="text-[10px] text-slate-400 leading-normal">
                                    Basal standard for shear transmission.
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Section 4: Structural Condition */}
                    <div className="rounded-xl bg-card border border-border shadow-card overflow-hidden">
                        <div className="flex items-center gap-3 px-5 py-4 border-b border-border bg-muted/30">
                            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                                <Wrench className="h-4 w-4 text-primary" />
                            </span>
                            <div>
                                <p className="text-sm font-semibold text-foreground">
                                    Structural Components
                                </p>
                                <p className="text-xs text-muted-foreground">
                                    Toggle active superstructures on the layout
                                    to calculate combined elasticity.
                                </p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-6">
                            {/* Mud Mortar Stone Switch Custom Checkbox */}
                            <Controller
                                name="has_superstructure_mud_mortar_stone"
                                control={control}
                                render={({ field }) => (
                                    <div
                                        onClick={() =>
                                            field.onChange(
                                                field.value === 1 ? 0 : 1,
                                            )
                                        }
                                        className={`flex flex-col p-4 rounded-xl border transition-all duration-150 cursor-pointer select-none ${
                                            field.value === 1
                                                ? "bg-rose-50 border-rose-200 text-rose-900 hover:bg-rose-50/70"
                                                : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50"
                                        }`}
                                        id="component-mud-mortar-stone"
                                    >
                                        <div className="flex items-center justify-between gap-2">
                                            <span className="text-xs font-semibold">
                                                Mud Mortar Stone
                                            </span>
                                            <div
                                                className={`w-8 h-4 rounded-full p-0.5 transition-colors duration-250 ${
                                                    field.value === 1
                                                        ? "bg-rose-600"
                                                        : "bg-slate-200"
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
                                        <p className="text-[10px] text-slate-500 mt-2 font-normal leading-relaxed">
                                            Low cohesion binding; extremely
                                            fragile under horizontal shaking.
                                        </p>
                                    </div>
                                )}
                            />

                            {/* RC Engineered Switch Custom Checkbox */}
                            <Controller
                                name="has_superstructure_rc_engineered"
                                control={control}
                                render={({ field }) => (
                                    <div
                                        onClick={() =>
                                            field.onChange(
                                                field.value === 1 ? 0 : 1,
                                            )
                                        }
                                        className={`flex flex-col p-4 rounded-xl border transition-all duration-150 cursor-pointer select-none ${
                                            field.value === 1
                                                ? "bg-teal-50 border-blue-200 text-blue-900 hover:bg-teal-55/70"
                                                : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50"
                                        }`}
                                        id="component-rc-engineered"
                                    >
                                        <div className="flex items-center justify-between gap-2">
                                            <span className="text-xs font-semibold">
                                                RC Engineered Frame
                                            </span>
                                            <div
                                                className={`w-8 h-4 rounded-full p-0.5 transition-colors duration-250 ${
                                                    field.value === 1
                                                        ? "bg-blue-600"
                                                        : "bg-slate-200"
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
                                        <p className="text-[10px] text-slate-500 mt-2 font-normal leading-relaxed">
                                            Ductile rigid framing engineered to
                                            absorb shear and bend safely.
                                        </p>
                                    </div>
                                )}
                            />

                            {/* Cement Mortar Brick Switch Custom Checkbox */}
                            <Controller
                                name="has_superstructure_cement_mortar_brick"
                                control={control}
                                render={({ field }) => (
                                    <div
                                        onClick={() =>
                                            field.onChange(
                                                field.value === 1 ? 0 : 1,
                                            )
                                        }
                                        className={`flex flex-col p-4 rounded-xl border transition-all duration-150 cursor-pointer select-none ${
                                            field.value === 1
                                                ? "bg-teal-50 border-blue-200 text-blue-900 hover:bg-teal-55/70"
                                                : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50"
                                        }`}
                                        id="component-cement-mortar-brick"
                                    >
                                        <div className="flex items-center justify-between gap-2">
                                            <span className="text-xs font-semibold">
                                                Cement Mortar Brick
                                            </span>
                                            <div
                                                className={`w-8 h-4 rounded-full p-0.5 transition-colors duration-250 ${
                                                    field.value === 1
                                                        ? "bg-blue-600"
                                                        : "bg-slate-200"
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
                                        <p className="text-[10px] text-slate-500 mt-2 font-normal leading-relaxed">
                                            Strong brick bonding; decent load
                                            support but stiff, prone to shear
                                            cracks.
                                        </p>
                                    </div>
                                )}
                            />
                            {/* RC Non-Engineered Switch Custom Checkbox */}
                            <Controller
                                name="has_superstructure_rc_non_engineered"
                                control={control}
                                render={({ field }) => (
                                    <div
                                        onClick={() =>
                                            field.onChange(
                                                field.value === 1 ? 0 : 1,
                                            )
                                        }
                                        className={`flex flex-col p-4 rounded-xl border transition-all duration-150 cursor-pointer select-none ${
                                            field.value === 1
                                                ? "bg-amber-50 border-amber-200 text-amber-900 hover:bg-amber-50/70"
                                                : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50"
                                        }`}
                                        id="component-rc-non-engineered"
                                    >
                                        <div className="flex items-center justify-between gap-2">
                                            <span className="text-xs font-semibold">
                                                RC Non-Engineered Frame
                                            </span>
                                            <div
                                                className={`w-8 h-4 rounded-full p-0.5 transition-colors duration-250 ${
                                                    field.value === 1
                                                        ? "bg-amber-600"
                                                        : "bg-slate-200"
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
                                        <p className="text-[10px] text-slate-500 mt-2 font-normal leading-relaxed">
                                            Reinforced concrete built without
                                            formal seismic details; prone to
                                            joint shear failure.
                                        </p>
                                    </div>
                                )}
                            />

                            {/* Adobe Mud Switch Custom Checkbox */}
                            <Controller
                                name="has_superstructure_adobe_mud"
                                control={control}
                                render={({ field }) => (
                                    <div
                                        onClick={() =>
                                            field.onChange(
                                                field.value === 1 ? 0 : 1,
                                            )
                                        }
                                        className={`flex flex-col p-4 rounded-xl border transition-all duration-150 cursor-pointer select-none ${
                                            field.value === 1
                                                ? "bg-rose-50 border-rose-200 text-rose-900 hover:bg-rose-50/70"
                                                : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50"
                                        }`}
                                        id="component-adobe-mud"
                                    >
                                        <div className="flex items-center justify-between gap-2">
                                            <span className="text-xs font-semibold">
                                                Adobe Mud
                                            </span>
                                            <div
                                                className={`w-8 h-4 rounded-full p-0.5 transition-colors duration-250 ${
                                                    field.value === 1
                                                        ? "bg-rose-600"
                                                        : "bg-slate-200"
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
                                        <p className="text-[10px] text-slate-500 mt-2 font-normal leading-relaxed">
                                            Brittle sundried mud brick walls;
                                            extremely high inertia mass, prone
                                            to rapid collapse.
                                        </p>
                                    </div>
                                )}
                            />

                            {/* Timber Switch Custom Checkbox */}
                            <Controller
                                name="has_superstructure_timber"
                                control={control}
                                render={({ field }) => (
                                    <div
                                        onClick={() =>
                                            field.onChange(
                                                field.value === 1 ? 0 : 1,
                                            )
                                        }
                                        className={`flex flex-col p-4 rounded-xl border transition-all duration-150 cursor-pointer select-none ${
                                            field.value === 1
                                                ? "bg-teal-50 border-blue-200 text-blue-900 hover:bg-teal-50/70"
                                                : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50"
                                        }`}
                                        id="component-timber"
                                    >
                                        <div className="flex items-center justify-between gap-2">
                                            <span className="text-xs font-semibold">
                                                Timber Frame
                                            </span>
                                            <div
                                                className={`w-8 h-4 rounded-full p-0.5 transition-colors duration-250 ${
                                                    field.value === 1
                                                        ? "bg-blue-600"
                                                        : "bg-slate-200"
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
                                        <p className="text-[10px] text-slate-500 mt-2 font-normal leading-relaxed">
                                            Lightweight flexible timber framing;
                                            excellent inherent seismic energy
                                            absorption.
                                        </p>
                                    </div>
                                )}
                            />
                        </div>
                    </div>

                    {/* Section 5: Location Context */}
                    <div className="rounded-xl bg-card border border-border shadow-card overflow-hidden">
                        <div className="flex items-center gap-3 px-5 py-4 border-b border-border bg-muted/30">
                            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                                <Globe className="h-4 w-4 text-primary" />
                            </span>
                            <div>
                                <p className="text-sm font-semibold text-foreground">
                                    Building Location
                                </p>
                                <p className="text-xs text-muted-foreground">
                                    Pin the building coordinates manually for
                                    hazard zone analysis
                                </p>
                            </div>
                        </div>
                        <div className="px-5 py-5 space-y-4">
                            {/* Coordinates numeric display overlay & inputs */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-1.5">
                                    <label className="text-xs font-mono text-slate-500 uppercase tracking-wider font-bold">
                                        Latitude{" "}
                                        <span className="text-rose-500">*</span>
                                    </label>
                                    <input
                                        type="number"
                                        step="any"
                                        {...register("latitude", {
                                            valueAsNumber: true,
                                        })}
                                        className="w-full bg-white border border-slate-200 text-slate-900 placeholder-slate-400 rounded-lg py-2.5 px-3.5 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-teal-600 focus:border-teal-600 transition-all"
                                        placeholder="e.g. 37.7749"
                                        id="input-latitude"
                                    />
                                    {errors.latitude && (
                                        <span className="text-[10px] text-rose-600 font-mono block">
                                            {errors.latitude.message}
                                        </span>
                                    )}
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-xs font-mono text-slate-500 uppercase tracking-wider font-bold">
                                        Longitude{" "}
                                        <span className="text-rose-500">*</span>
                                    </label>
                                    <input
                                        type="number"
                                        step="any"
                                        {...register("longitude", {
                                            valueAsNumber: true,
                                        })}
                                        className="w-full bg-white border border-slate-200 text-slate-900 placeholder-slate-400 rounded-lg py-2.5 px-3.5 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-teal-600 focus:border-teal-600 transition-all"
                                        placeholder="e.g. -122.4194"
                                        id="input-longitude"
                                    />
                                    {errors.longitude && (
                                        <span className="text-[10px] text-rose-600 font-mono block">
                                            {errors.longitude.message}
                                        </span>
                                    )}
                                </div>
                            </div>

                            {/* Embed Leaflet map */}
                            <LocationPicker
                                latitude={
                                    watchedLat || DEFAULT_FORM_VALUES.latitude
                                }
                                longitude={
                                    watchedLng || DEFAULT_FORM_VALUES.longitude
                                }
                                onLocationChange={handleLocationChange}
                            />
                        </div>
                    </div>

                    {/* Submit Area */}
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
                            <BarChart2 className="h-4 w-4" />
                            {isLoading
                                ? "Running Simulation..."
                                : "Analyze Earthquake Risk"}
                        </button>
                    </div>
                </form>
            </main>

            <footer className="border-t border-border px-6 py-4 text-center">
                <p className="text-xs text-muted-foreground">
                    codeTrio &nbsp;·&nbsp; STIMU &nbsp;·&nbsp; For academic and
                    demonstration purposes only
                </p>
            </footer>
        </div>
    );
}
