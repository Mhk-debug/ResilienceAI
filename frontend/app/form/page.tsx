"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import LocationPicker from "./location-picker";
import {
    Building2,
    Layers,
    Wrench,
    Globe,
    AlertCircle,
    Info,
    Scaling,
    Mountain,
    Map,
    Grid3x3,
} from "lucide-react";
import { useState } from "react";
import { useForm, type Path, type Resolver } from "react-hook-form";
import { useRouter } from "next/navigation";
import { formSchema, type FormFields } from "./schema";
import {
    DEFAULT_FORM_VALUES,
    heightTemplates,
    plinchAreaTemplates,
    LAND_SURFACE_OPTIONS,
    POSITION_OPTIONS,
    PLAN_CONFIGURATION_OPTIONS,
    OTHER_FLOOR_TYPE_OPTIONS,
} from "./data";
import StructuralComponentCheckbox from "./StructuralComponentCheckbox";
import FormHeader from "./FormHeader";
import FormSectionCard from "./FormSectionCard";
import FormActionArea from "./FormActionArea";
import Footer from "@/components/footer";
import BuildingScalePresetsDisplay from "./BuildingScalePresetsDisplay";
import MultiStageLoadingDisplay, {
    type StageStatusMap,
} from "./MultiStageLoadingDisplay";

/* ─── Inline SVG diagrams for the terrain cross-section selector ─── */

/* Terrain geometry. The sloped cards used to place a hand-rotated body and then
   draw the windows and roof in the un-rotated frame, so on a slope the roof and
   windows drifted off the walls and the whole building floated above the ground
   line. Both curves are defined once here; the house transform is derived from
   the curve that draws the ground, so the base stays on the line. */
type Quad = [[number, number], [number, number], [number, number]];

const TERRAIN_MODERATE: Quad[] = [
    [[5, 65], [30, 60], [60, 52]],
    [[60, 52], [90, 44], [115, 40]],
];

const TERRAIN_STEEP: Quad[] = [
    [[5, 70], [30, 60], [60, 45]],
    [[60, 45], [90, 30], [115, 20]],
];

const quadPoint = (seg: Quad, t: number): [number, number] => {
    const [[x0, y0], [cx, cy], [x1, y1]] = seg;
    const u = 1 - t;
    return [
        u * u * x0 + 2 * u * t * cx + t * t * x1,
        u * u * y0 + 2 * u * t * cy + t * t * y1,
    ];
};

/** y of the terrain at a given x, by sampling the curve (curves are gentle, so
 *  the nearest sample is exact enough for a 120 × 80 icon). */
const terrainY = (segments: Quad[], x: number): number => {
    let bestY = quadPoint(segments[0], 0)[1];
    let bestDx = Number.POSITIVE_INFINITY;
    for (const seg of segments) {
        for (let i = 0; i <= 240; i += 1) {
            const [px, py] = quadPoint(seg, i / 240);
            const dx = Math.abs(px - x);
            if (dx < bestDx) {
                bestDx = dx;
                bestY = py;
            }
        }
    }
    return bestY;
};

/** Place a building on the terrain: the base spans [centre − half, centre + half]
 *  and is tilted to the chord between the two ground points, so both base corners
 *  — and therefore the walls, windows and roof, which share this transform — sit
 *  exactly on the ground line. */
const houseTransform = (segments: Quad[], centreX: number, halfWidth: number): string => {
    const left = centreX - halfWidth;
    const right = centreX + halfWidth;
    const yLeft = terrainY(segments, left);
    const yRight = terrainY(segments, right);
    const angle = (Math.atan2(yRight - yLeft, right - left) * 180) / Math.PI;
    const yBase = (yLeft + yRight) / 2;
    return `translate(${centreX} ${yBase.toFixed(2)}) rotate(${angle.toFixed(1)})`;
};

const quadPath = (segments: Quad[]): string =>
    `M${segments[0][0][0]} ${segments[0][0][1]}` +
    segments.map(([, c, e]) => ` Q ${c[0]} ${c[1]} ${e[0]} ${e[1]}`).join("");

const slopeFill = (segments: Quad[]): string => {
    const last = segments[segments.length - 1][2];
    return `${quadPath(segments)} L${last[0]} 78 L${segments[0][0][0]} 78 Z`;
};

function TerrainFlat({ active }: { active: boolean }) {
    return (
        <svg viewBox="0 0 120 80" className="w-full h-full" aria-hidden="true">
            <line
                x1="5" y1="58" x2="115" y2="58"
                stroke={active ? "#b45309" : "#a8a29e"}
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeDasharray="0"
            />
            <path
                d="M5 58 Q 30 56 60 58 Q 90 60 115 58"
                fill={active ? "#d4a574" : "#e7e5e4"}
                stroke="none"
            />
            <rect
                x="42" y="28" width="22" height="30"
                rx="1"
                fill={active ? "#fbbf24" : "#d6d3d1"}
                stroke={active ? "#b45309" : "#a8a29e"}
                strokeWidth="1.5"
            />
            <rect x="46" y="32" width="6" height="5" rx="0.5" fill={active ? "#92400e" : "#78716c"} />
            <rect x="54" y="32" width="6" height="5" rx="0.5" fill={active ? "#92400e" : "#78716c"} />
            <rect x="48" y="50" width="8" height="8" rx="0.5" fill={active ? "#92400e" : "#78716c"} />
            <polygon
                points="42,28 53,18 64,28"
                fill={active ? "#dc2626" : "#a8a29e"}
                stroke={active ? "#b45309" : "#a8a29e"}
                strokeWidth="1"
            />
            <text x="60" y="76" textAnchor="middle" fontSize="6" fill={active ? "#78716c" : "#a8a29e"} fontFamily="sans-serif">
                flat ground
            </text>
        </svg>
    );
}

function TerrainModerate({ active }: { active: boolean }) {
    return (
        <svg viewBox="0 0 120 80" className="w-full h-full" aria-hidden="true">
            <path
                d={quadPath(TERRAIN_MODERATE)}
                fill="none"
                stroke={active ? "#b45309" : "#a8a29e"}
                strokeWidth="2.5"
                strokeLinecap="round"
            />
            <path
                d={slopeFill(TERRAIN_MODERATE)}
                fill={active ? "#d4a574" : "#e7e5e4"}
                stroke="none"
            />
            {/* body, windows and roof share one transform → they cannot drift apart,
                and the base sits on the ground line (base at y=0, up is −y) */}
            <g transform={houseTransform(TERRAIN_MODERATE, 55, 10)}>
                <rect
                    x="-10" y="-30" width="20" height="30"
                    rx="1"
                    fill={active ? "#fbbf24" : "#d6d3d1"}
                    stroke={active ? "#b45309" : "#a8a29e"}
                    strokeWidth="1.5"
                />
                <rect x="-6" y="-26" width="5" height="4" rx="0.5" fill={active ? "#92400e" : "#78716c"} />
                <rect x="1" y="-26" width="5" height="4" rx="0.5" fill={active ? "#92400e" : "#78716c"} />
                <polygon
                    points="-10,-30 0,-38 10,-30"
                    fill={active ? "#dc2626" : "#a8a29e"}
                    stroke={active ? "#b45309" : "#a8a29e"}
                    strokeWidth="1"
                />
            </g>
            <text x="60" y="76" textAnchor="middle" fontSize="6" fill={active ? "#78716c" : "#a8a29e"} fontFamily="sans-serif">
                gentle slope
            </text>
        </svg>
    );
}

function TerrainSteep({ active }: { active: boolean }) {
    return (
        <svg viewBox="0 0 120 80" className="w-full h-full" aria-hidden="true">
            <path
                d={quadPath(TERRAIN_STEEP)}
                fill="none"
                stroke={active ? "#b45309" : "#a8a29e"}
                strokeWidth="2.5"
                strokeLinecap="round"
            />
            <path
                d={slopeFill(TERRAIN_STEEP)}
                fill={active ? "#d4a574" : "#e7e5e4"}
                stroke="none"
            />
            <g transform={houseTransform(TERRAIN_STEEP, 51, 9)}>
                <rect
                    x="-9" y="-28" width="18" height="28"
                    rx="1"
                    fill={active ? "#fbbf24" : "#d6d3d1"}
                    stroke={active ? "#b45309" : "#a8a29e"}
                    strokeWidth="1.5"
                />
                <rect x="-6" y="-24" width="4" height="4" rx="0.5" fill={active ? "#92400e" : "#78716c"} />
                <rect x="1" y="-24" width="4" height="4" rx="0.5" fill={active ? "#92400e" : "#78716c"} />
                <polygon
                    points="-9,-28 0,-36 9,-28"
                    fill={active ? "#dc2626" : "#a8a29e"}
                    stroke={active ? "#b45309" : "#a8a29e"}
                    strokeWidth="1"
                />
            </g>
            <text x="60" y="76" textAnchor="middle" fontSize="6" fill={active ? "#78716c" : "#a8a29e"} fontFamily="sans-serif">
                steep slope
            </text>
        </svg>
    );
}

/* ─── Position SVG diagrams ─── */

function PositionNotAttached({ active }: { active: boolean }) {
    return (
        <svg viewBox="0 0 100 60" className="w-full h-full" aria-hidden="true">
            <rect
                x="35" y="10" width="30" height="35" rx="2"
                fill={active ? "#a78bfa" : "#d6d3d1"}
                stroke={active ? "#7c3aed" : "#a8a29e"}
                strokeWidth="1.5"
            />
            <rect x="40" y="15" width="8" height="6" rx="1" fill={active ? "#4c1d95" : "#78716c"} />
            <rect x="52" y="15" width="8" height="6" rx="1" fill={active ? "#4c1d95" : "#78716c"} />
            <rect x="43" y="35" width="10" height="10" rx="1" fill={active ? "#4c1d95" : "#78716c"} />
            <line x1="35" y1="45" x2="65" y2="45" stroke={active ? "#7c3aed" : "#a8a29e"} strokeWidth="1.5" />
        </svg>
    );
}

function Position1Side({ active }: { active: boolean }) {
    return (
        <svg viewBox="0 0 100 60" className="w-full h-full" aria-hidden="true">
            <rect
                x="10" y="10" width="22" height="35" rx="2"
                fill={active ? "#c4b5fd" : "#e7e5e4"}
                stroke={active ? "#a78bfa" : "#d6d3d1"}
                strokeWidth="1"
            />
            <rect
                x="32" y="10" width="30" height="35" rx="2"
                fill={active ? "#a78bfa" : "#d6d3d1"}
                stroke={active ? "#7c3aed" : "#a8a29e"}
                strokeWidth="1.5"
            />
            <rect x="37" y="15" width="8" height="6" rx="1" fill={active ? "#4c1d95" : "#78716c"} />
            <rect x="49" y="15" width="8" height="6" rx="1" fill={active ? "#4c1d95" : "#78716c"} />
            <rect x="40" y="35" width="10" height="10" rx="1" fill={active ? "#4c1d95" : "#78716c"} />
            <line x1="32" y1="45" x2="62" y2="45" stroke={active ? "#7c3aed" : "#a8a29e"} strokeWidth="1.5" />
            <line x1="32" y1="10" x2="32" y2="45" stroke={active ? "#dc2626" : "#a8a29e"} strokeWidth="1.5" strokeDasharray="3 2" />
        </svg>
    );
}

function Position2Side({ active }: { active: boolean }) {
    return (
        <svg viewBox="0 0 100 60" className="w-full h-full" aria-hidden="true">
            <rect
                x="5" y="10" width="22" height="35" rx="2"
                fill={active ? "#c4b5fd" : "#e7e5e4"}
                stroke={active ? "#a78bfa" : "#d6d3d1"}
                strokeWidth="1"
            />
            <rect
                x="27" y="10" width="28" height="35" rx="2"
                fill={active ? "#a78bfa" : "#d6d3d1"}
                stroke={active ? "#7c3aed" : "#a8a29e"}
                strokeWidth="1.5"
            />
            <rect
                x="55" y="10" width="22" height="35" rx="2"
                fill={active ? "#c4b5fd" : "#e7e5e4"}
                stroke={active ? "#a78bfa" : "#d6d3d1"}
                strokeWidth="1"
            />
            <rect x="32" y="15" width="7" height="5" rx="1" fill={active ? "#4c1d95" : "#78716c"} />
            <rect x="42" y="15" width="7" height="5" rx="1" fill={active ? "#4c1d95" : "#78716c"} />
            <rect x="36" y="35" width="10" height="10" rx="1" fill={active ? "#4c1d95" : "#78716c"} />
            <line x1="27" y1="45" x2="55" y2="45" stroke={active ? "#7c3aed" : "#a8a29e"} strokeWidth="1.5" />
            <line x1="27" y1="10" x2="27" y2="45" stroke={active ? "#dc2626" : "#a8a29e"} strokeWidth="1.5" strokeDasharray="3 2" />
            <line x1="55" y1="10" x2="55" y2="45" stroke={active ? "#dc2626" : "#a8a29e"} strokeWidth="1.5" strokeDasharray="3 2" />
        </svg>
    );
}

function Position3Side({ active }: { active: boolean }) {
    return (
        <svg viewBox="0 0 100 60" className="w-full h-full" aria-hidden="true">
            <rect
                x="5" y="10" width="18" height="35" rx="2"
                fill={active ? "#c4b5fd" : "#e7e5e4"}
                stroke={active ? "#a78bfa" : "#d6d3d1"}
                strokeWidth="1"
            />
            <rect
                x="23" y="10" width="28" height="35" rx="2"
                fill={active ? "#a78bfa" : "#d6d3d1"}
                stroke={active ? "#7c3aed" : "#a8a29e"}
                strokeWidth="1.5"
            />
            <rect
                x="51" y="10" width="18" height="35" rx="2"
                fill={active ? "#c4b5fd" : "#e7e5e4"}
                stroke={active ? "#a78bfa" : "#d6d3d1"}
                strokeWidth="1"
            />
            <rect
                x="23" y="0" width="28" height="10" rx="2"
                fill={active ? "#c4b5fd" : "#e7e5e4"}
                stroke={active ? "#a78bfa" : "#d6d3d1"}
                strokeWidth="1"
            />
            <rect x="28" y="16" width="7" height="5" rx="1" fill={active ? "#4c1d95" : "#78716c"} />
            <rect x="39" y="16" width="7" height="5" rx="1" fill={active ? "#4c1d95" : "#78716c"} />
            <rect x="32" y="35" width="10" height="10" rx="1" fill={active ? "#4c1d95" : "#78716c"} />
            <line x1="23" y1="45" x2="51" y2="45" stroke={active ? "#7c3aed" : "#a8a29e"} strokeWidth="1.5" />
            <line x1="23" y1="10" x2="23" y2="45" stroke={active ? "#dc2626" : "#a8a29e"} strokeWidth="1.5" strokeDasharray="3 2" />
            <line x1="51" y1="10" x2="51" y2="45" stroke={active ? "#dc2626" : "#a8a29e"} strokeWidth="1.5" strokeDasharray="3 2" />
            <line x1="23" y1="10" x2="51" y2="10" stroke={active ? "#dc2626" : "#a8a29e"} strokeWidth="1.5" strokeDasharray="3 2" />
        </svg>
    );
}

/* ─── Plan Configuration footprint SVGs ─── */

function FootprintSVG({ shape, active }: { shape: string; active: boolean }) {
    const fill = active ? "#818cf8" : "#d6d3d1";
    const stroke = active ? "#4f46e5" : "#a8a29e";
    const sw = "1.5";

    switch (shape) {
        case "Rectangular":
            return (
                <svg viewBox="0 0 40 40" className="w-full h-full" aria-hidden="true">
                    <rect x="6" y="10" width="28" height="20" rx="1" fill={fill} stroke={stroke} strokeWidth={sw} />
                </svg>
            );
        case "Square":
            return (
                <svg viewBox="0 0 40 40" className="w-full h-full" aria-hidden="true">
                    <rect x="8" y="8" width="24" height="24" rx="1" fill={fill} stroke={stroke} strokeWidth={sw} />
                </svg>
            );
        case "L-shape":
            return (
                <svg viewBox="0 0 40 40" className="w-full h-full" aria-hidden="true">
                    <path d="M8 8 L22 8 L22 20 L32 20 L32 32 L8 32 Z" fill={fill} stroke={stroke} strokeWidth={sw} />
                </svg>
            );
        case "T-shape":
            return (
                <svg viewBox="0 0 40 40" className="w-full h-full" aria-hidden="true">
                    <path d="M6 8 L34 8 L34 16 L25 16 L25 32 L15 32 L15 16 L6 16 Z" fill={fill} stroke={stroke} strokeWidth={sw} />
                </svg>
            );
        case "U-shape":
            return (
                <svg viewBox="0 0 40 40" className="w-full h-full" aria-hidden="true">
                    <path d="M8 8 L16 8 L16 24 L24 24 L24 8 L32 8 L32 32 L8 32 Z" fill={fill} stroke={stroke} strokeWidth={sw} />
                </svg>
            );
        case "E-shape":
            return (
                <svg viewBox="0 0 40 40" className="w-full h-full" aria-hidden="true">
                    <path d="M8 8 L32 8 L32 13 L20 13 L20 18 L30 18 L30 23 L20 23 L20 28 L32 28 L32 32 L8 32 Z" fill={fill} stroke={stroke} strokeWidth={sw} />
                </svg>
            );
        case "H-shape":
            return (
                <svg viewBox="0 0 40 40" className="w-full h-full" aria-hidden="true">
                    <path d="M8 8 L16 8 L16 16 L24 16 L24 8 L32 8 L32 32 L24 32 L24 24 L16 24 L16 32 L8 32 Z" fill={fill} stroke={stroke} strokeWidth={sw} />
                </svg>
            );
        case "Multi-projected":
            return (
                <svg viewBox="0 0 40 40" className="w-full h-full" aria-hidden="true">
                    <path d="M14 6 L26 6 L26 14 L34 14 L34 26 L26 26 L26 34 L14 34 L14 26 L6 26 L6 14 L14 14 Z" fill={fill} stroke={stroke} strokeWidth={sw} />
                </svg>
            );
        case "Building with Central Courtyard":
            return (
                <svg viewBox="0 0 40 40" className="w-full h-full" aria-hidden="true">
                    <rect x="6" y="6" width="28" height="28" rx="1" fill={fill} stroke={stroke} strokeWidth={sw} />
                    <rect x="14" y="14" width="12" height="12" rx="1" fill="white" stroke={stroke} strokeWidth="1" />
                </svg>
            );
        case "Others":
            return (
                <svg viewBox="0 0 40 40" className="w-full h-full" aria-hidden="true">
                    <polygon points="20,6 34,14 30,30 10,30 6,14" fill={fill} stroke={stroke} strokeWidth={sw} />
                    <text x="20" y="24" textAnchor="middle" fontSize="10" fill={active ? "#4f46e5" : "#78716c"} fontWeight="bold" fontFamily="sans-serif">?</text>
                </svg>
            );
        default:
            return null;
    }
}

export default function FormPage() {
    const router = useRouter();

    const [isLoading, setIsLoading] = useState(false);
    const [stageStatuses, setStageStatuses] = useState<StageStatusMap>({
        initializing: "pending",
        resilience: "pending",
        hazard: "pending",
        llm: "pending",
        saving: "pending",
    });

    const [statusText, setStatusText] = useState(
        "Preparing your assessment...",
    );

    const [isComplete, setIsComplete] = useState(false);

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
        mode: "onBlur",
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

        const validationResult = formSchema.safeParse(data);

        if (!validationResult.success) {
            validationResult.error.issues.forEach((issue) => {
                const pathStr = issue.path[0] as Path<FormFields>;

                setError(pathStr, {
                    message: issue.message,
                });
            });

            return;
        }

        // Reset assessment UI state
        setIsLoading(true);
        setIsComplete(false);
        setStatusText("Preparing your assessment...");
        setStageStatuses({
            initializing: "pending",
            resilience: "pending",
            hazard: "pending",
            llm: "pending",
            saving: "pending",
        });

        try {
            const response = await fetch(
                "/api/sse/assessment/process",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(data),
                },
            );

            /*
             * Handle errors that occur before the server
             * successfully starts the stream.
             */
            if (!response.ok || !response.body) {
                const errorData = await response.json().catch(() => ({}));

                throw new Error(
                    errorData.detail ||
                        "Server failed to start the assessment.",
                );
            }

            const reader = response.body.getReader();

            const decoder = new TextDecoder();

            let buffer = "";

            let assessmentID: string | null = null;

            /*
             * Read the SSE stream.
             */
            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    break;
                }

                buffer += decoder.decode(value, {
                    stream: true,
                });

                /*
                 * SSE events are separated by
                 * a blank line:
                 *
                 * data: {...}\n\n
                 */
                const events = buffer.split("\n\n");

                /*
                 * Keep the last incomplete event
                 * in the buffer.
                 */
                buffer = events.pop() ?? "";

                for (const event of events) {
                    const dataLine = event
                        .split("\n")
                        .find((line) => line.startsWith("data:"));
                    if (!dataLine) {
                        continue;
                    }

                    const jsonString = dataLine.replace(/^data:\s*/, "").trim();

                    if (!jsonString) {
                        continue;
                    }

                    let parsed;
                    try {
                        parsed = JSON.parse(jsonString);
                    } catch (parseError) {
                        console.warn(
                            "Failed to parse SSE event:",
                            jsonString,
                            parseError,
                        );

                        continue;
                    }

                    /*
                     * ------------------------------------
                     * STAGE STARTED
                     * ------------------------------------
                     */
                    if (parsed.type === "stage_started") {
                        setStageStatuses((previous) => ({
                            ...previous,
                            [parsed.stage]: "active",
                        }));

                        if (parsed.status) {
                            setStatusText(parsed.status);
                        }

                        continue;
                    }

                    /*
                     * ------------------------------------
                     * STAGE COMPLETED
                     * ------------------------------------
                     */
                    if (parsed.type === "stage_completed") {
                        setStageStatuses((previous) => ({
                            ...previous,
                            [parsed.stage]: "completed",
                        }));

                        continue;
                    }

                    /*
                     * ------------------------------------
                     * ASSESSMENT COMPLETE
                     * ------------------------------------
                     */
                    if (parsed.type === "complete") {
                        assessmentID = parsed.assessment_id;

                        setStageStatuses({
                            initializing: "completed",
                            resilience: "completed",
                            hazard: "completed",
                            llm: "completed",
                            saving: "completed",
                        });

                        setIsComplete(true);

                        continue;
                    }

                    /*
                     * ------------------------------------
                     * STREAM ERROR
                     * ------------------------------------
                     */
                    if (parsed.type === "error") {
                        throw new Error(
                            parsed.detail || "The assessment pipeline failed.",
                        );
                    }
                }
            }

            /*
             * Flush any remaining decoder content.
             */
            buffer += decoder.decode();

            /*
             * Usually there should be no remaining
             * complete event here because SSE events
             * are separated by \n\n, but this handles
             * a final event safely.
             */
            if (buffer.trim()) {
                const dataLine = buffer
                    .split("\n")
                    .find((line) => line.startsWith("data:"));
                if (dataLine) {
                    const jsonString = dataLine.replace(/^data:\s*/, "").trim();
                    if (jsonString) {
                        try {
                            const parsed = JSON.parse(jsonString);

                            if (parsed.type === "complete") {
                                assessmentID = parsed.assessment_id;
                            }

                            if (parsed.type === "error") {
                                throw new Error(
                                    parsed.detail ||
                                        "The assessment pipeline failed.",
                                );
                            }
                        } catch (err) {
                            /*
                             * Re-throw actual stream errors,
                             * but ignore malformed trailing
                             * data.
                             */
                            if (
                                err instanceof Error && err.message !== "Unexpected end of JSON input"
                            ) {
                                throw err;
                            }
                        }
                    }
                }
            }

            /*
             * The backend should always send a complete
             * event containing the assessment ID.
             */
            if (!assessmentID) {
                throw new Error(
                    "Assessment completed without returning an assessment ID. Please check your assessment history.",
                );
            }

            /*
             * Keep the loading display visible while
             * navigation begins.
             */
            router.push(`/dashboard/${assessmentID}`);
        } catch (err: unknown) {
            window.scrollTo({
                top: 0,
                behavior: "smooth",
            });

            /*
             * This unmounts the multi-stage loading UI.
             */
            setIsLoading(false);

            /*
             * The form page owns the error display.
             */
            if (err instanceof Error) {
                setError("root.serverError", {
                    message: `Assessment failed: ${err.message}`,
                });
            } else {
                setError("root.serverError", {
                    message:
                        "An unexpected error occurred while processing the assessment.",
                });
            }
        }
    };
    
    // Completely clear form and coordinates back to absolute default
    const handleFormReset = () => {
        reset(DEFAULT_FORM_VALUES);
        clearErrors();
    };

    /* Watched values for the new visual selectors */
    const watchedLandSurface = watch("land_surface_condition");
    const watchedPosition = watch("position");
    const watchedPlanConfig = watch("plan_configuration");
    const watchedOtherFloorType = watch("other_floor_type");

    return (
        <div className="flex min-h-full flex-col bg-background">
            <FormHeader />

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
                    <FormSectionCard
                        title="Basic Building Info"
                        desc="General characteristics of the structure"
                        Icon={Building2}
                    >
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
                                Total number of above-ground floors (limit 1 to
                                10).
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
                    </FormSectionCard>

                    {/* Section 2: Building Scale & Density */}
                    <FormSectionCard
                        title="Building Scale & Density"
                        desc="These inputs help estimate how mass and
                            density affect earthquake vulnerability."
                        Icon={Scaling}
                        className="grid grid-cols-1 md:grid-cols-2 gap-8 py-6 px-6 md:px-8 md:pb-8"
                    >
                        {/* Footprint Area Input */}
                        <div className="space-y-6">
                            <div className="space-y-1.5">
                                <label
                                    htmlFor="area_sq_ft"
                                    className="text-xs font-semibold text-slate-700 flex items-center justify-between"
                                >
                                    <span className="flex items-center gap-1.5">
                                        Building Footprint (Plinth Area){" "}
                                        <span className="text-rose-500">*</span>
                                    </span>
                                    <span className="text-[10px] font-mono text-red-600">
                                        5000 sq ft max
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
                                <p className="text-[10px] text-slate-600 leading-relaxed font-normal">
                                    The ground level floor area of the building.
                                    We limit to <b>5000 sq feets max</b> within
                                    our application for practicality.
                                </p>
                                {errors.area_sq_ft && (
                                    <span className="text-[10px] text-rose-600 font-mono block mt-1">
                                        {errors.area_sq_ft.message}
                                    </span>
                                )}
                            </div>

                            {/* Presets for Footprint */}
                            <BuildingScalePresetsDisplay
                                watch={watch}
                                setValue={setValue}
                                value="area_sq_ft"
                                presetTemplates={plinchAreaTemplates}
                                label="Or select a typical size helper:"
                            />
                        </div>

                        {/* Building Height Input */}
                        <div className="space-y-6">
                            <div className="space-y-1.5">
                                <label
                                    htmlFor="height_ft"
                                    className="text-xs font-semibold text-slate-700 flex items-center justify-between"
                                >
                                    <span className="flex items-center gap-1.5">
                                        Building Height{" "}
                                        <span className="text-rose-500">*</span>
                                    </span>
                                    <span className="text-[10px] font-mono text-red-600">
                                        305 feet max
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
                                <p className="text-[10px] text-slate-600 leading-relaxed font-normal">
                                    Total height from ground base to roof. We
                                    limit to <b>305 feets max</b> within our
                                    application for practicality.
                                </p>
                                {errors.height_ft && (
                                    <span className="text-[10px] text-rose-600 font-mono block mt-1">
                                        {errors.height_ft.message}
                                    </span>
                                )}
                            </div>

                            {/* Presets for Height */}
                            <BuildingScalePresetsDisplay
                                watch={watch}
                                setValue={setValue}
                                value="height_ft"
                                presetTemplates={heightTemplates}
                                label="Or estimate by building floor count"
                            />
                        </div>
                    </FormSectionCard>

                    {/* Section 3: Structural Materials Materials */}
                    <FormSectionCard
                        title="Structural Materials"
                        desc="Primary construction materials used"
                        className="grid grid-cols-1 md:grid-cols-3 gap-6 px-6 pt-6 pb-8"
                        Icon={Layers}
                    >
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
                                <option value="w">Bamboo / Timber Foundation</option>
                                <option value="r">Mud-Stone Foundation</option>
                                <option value="h">
                                    Other / Unclassified Foundation
                                </option>
                            </select>
                            <p className="text-[10px] text-slate-500 leading-normal">
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
                                <option value="x">
                                    Reinforced Concrete Slab Roof (RCC)
                                </option>
                                <option value="n">
                                    Bamboo / Timber — Light Roof (thatch, CGI/tin)
                                </option>
                                <option value="q">
                                    Bamboo / Timber — Heavy Roof (mud-covered)
                                </option>
                            </select>
                            <p className="text-[10px] text-slate-500 leading-normal">
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
                                <option value="v">
                                    Reinforced Concrete Floor
                                </option>
                                <option value="m">Other / Unclassified Floor</option>
                                <option value="z">Timber Floor</option>
                                <option value="x">Brick / Stone Floor</option>
                                <option value="f">Mud Floor</option>
                            </select>
                            <p className="text-[10px] text-slate-500 leading-normal">
                                Basal standard for shear transmission.
                            </p>
                        </div>
                    </FormSectionCard>

                    {/* Section 4: Structural Condition — original 6 + 5 new */}
                    <FormSectionCard
                        title="Structural Components"
                        desc="Toggle active superstructures on the layout
                                    to calculate combined elasticity."
                        Icon={Wrench}
                        className="grid grid-cols-1 md:grid-cols-3 gap-4 p-6"
                    >
                        {/* Stone with Mud Mortar */}
                        <StructuralComponentCheckbox
                            control={control}
                            title="Stone & Mud Mortar"
                            desc="Stone walls joined with weak mud mortar."
                            name="has_superstructure_mud_mortar_stone"
                            color="rose"
                        />

                        {/* RC Engineered */}
                        <StructuralComponentCheckbox
                            control={control}
                            title="Engineered Concrete"
                            desc="Engineer-designed reinforced concrete structure."
                            name="has_superstructure_rc_engineered"
                            color="emerald"
                        />

                        {/* Cement Mortar Brick */}
                        <StructuralComponentCheckbox
                            control={control}
                            title="Brick & Cement Mortar"
                            desc="Brick walls joined with strong cement mortar."
                            name="has_superstructure_cement_mortar_brick"
                            color="green"
                        />

                        {/* RC Non-Engineered */}
                        <StructuralComponentCheckbox
                            control={control}
                            title="Non-Engineered Concrete"
                            desc="Reinforced concrete built without formal engineering."
                            name="has_superstructure_rc_non_engineered"
                            color="amber"
                        />

                        {/* Adobe Mud */}
                        <StructuralComponentCheckbox
                            control={control}
                            title="Adobe / Mud Brick"
                            desc="Walls made from mud or sun-dried earth."
                            name="has_superstructure_adobe_mud"
                            color="yellow"
                        />

                        {/* Timber */}
                        <StructuralComponentCheckbox
                            control={control}
                            title="Timber / Wood"
                            desc="A lightweight structure built mainly with wood."
                            name="has_superstructure_timber"
                            color="red"
                        />

                        {/* NEW: Stone Flag */}
                        <StructuralComponentCheckbox
                            control={control}
                            title="Stone Flag / Dressed Stone"
                            desc="Cut and dressed stone used as structural element."
                            name="has_superstructure_stone_flag"
                            color="stone"
                        />

                        {/* NEW: Cement Mortar Stone */}
                        <StructuralComponentCheckbox
                            control={control}
                            title="Stone & Cement Mortar"
                            desc="Stone walls joined with cement mortar for strength."
                            name="has_superstructure_cement_mortar_stone"
                            color="slate"
                        />

                        {/* NEW: Mud Mortar Brick */}
                        <StructuralComponentCheckbox
                            control={control}
                            title="Brick & Mud Mortar"
                            desc="Brick walls joined with weak mud mortar."
                            name="has_superstructure_mud_mortar_brick"
                            color="orange"
                        />

                        {/* NEW: Bamboo */}
                        <StructuralComponentCheckbox
                            control={control}
                            title="Bamboo"
                            desc="Structural framing using bamboo poles."
                            name="has_superstructure_bamboo"
                            color="lime"
                        />

                        {/* NEW: Other */}
                        <StructuralComponentCheckbox
                            control={control}
                            title="Other Material"
                            desc="Any other structural material not listed above."
                            name="has_superstructure_other"
                            color="neutral"
                        />
                    </FormSectionCard>

                    {/* NEW Section 5: Land Surface Condition — visual terrain cross-section */}
                    <div className="rounded-xl bg-card border border-border shadow-card overflow-hidden">
                        <div className="flex items-center gap-3 px-5 py-4 border-b border-amber-100 bg-amber-50/60">
                            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-amber-100">
                                <Mountain className="h-4 w-4 text-amber-700" />
                            </span>
                            <div>
                                <p className="text-sm font-semibold text-foreground">
                                    Land Surface Condition
                                </p>
                                <p className="text-xs text-amber-700/70">
                                    What does the ground under the building look like?
                                </p>
                            </div>
                        </div>
                        <div className="px-5 py-5 grid grid-cols-1 sm:grid-cols-3 gap-4">
                            {LAND_SURFACE_OPTIONS.map((opt) => {
                                const isActive = watchedLandSurface === opt.value;
                                return (
                                    <button
                                        key={opt.value}
                                        type="button"
                                        onClick={() => setValue("land_surface_condition", opt.value)}
                                        className={`flex flex-col items-center gap-2 p-3 rounded-xl border-2 transition-all cursor-pointer select-none ${
                                            isActive
                                                ? "border-amber-500 bg-amber-50 shadow-sm"
                                                : "border-slate-200 bg-white hover:border-amber-300 hover:bg-amber-50/30"
                                        }`}
                                    >
                                        <div className="w-full h-20">
                                            {opt.value === "Flat" && <TerrainFlat active={isActive} />}
                                            {opt.value === "Moderate slope" && <TerrainModerate active={isActive} />}
                                            {opt.value === "Steep slope" && <TerrainSteep active={isActive} />}
                                        </div>
                                        <span className={`text-xs font-semibold ${isActive ? "text-amber-800" : "text-slate-700"}`}>
                                            {opt.label}
                                        </span>
                                        <span className="text-[10px] text-slate-500 leading-snug text-center">
                                            {opt.description}
                                        </span>
                                    </button>
                                );
                            })}
                        </div>
                        {errors.land_surface_condition && (
                            <span className="text-[10px] text-rose-600 font-mono block px-5 pb-3">
                                {errors.land_surface_condition.message}
                            </span>
                        )}
                    </div>

                    {/* NEW Section 6: Building Position — visual attachment diagram */}
                    <div className="rounded-xl bg-card border border-border shadow-card overflow-hidden">
                        <div className="flex items-center gap-3 px-5 py-4 border-b border-violet-100 bg-violet-50/60">
                            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-violet-100">
                                <Map className="h-4 w-4 text-violet-700" />
                            </span>
                            <div>
                                <p className="text-sm font-semibold text-foreground">
                                    Building Position
                                </p>
                                <p className="text-xs text-violet-700/70">
                                    How many sides of the building are attached to neighbours?
                                </p>
                            </div>
                        </div>
                        <div className="px-5 py-5 grid grid-cols-2 sm:grid-cols-4 gap-3">
                            {POSITION_OPTIONS.map((opt) => {
                                const isActive = watchedPosition === opt.value;
                                return (
                                    <button
                                        key={opt.value}
                                        type="button"
                                        onClick={() => setValue("position", opt.value)}
                                        className={`flex flex-col items-center gap-2 p-3 rounded-xl border-2 transition-all cursor-pointer select-none ${
                                            isActive
                                                ? "border-violet-500 bg-violet-50 shadow-sm"
                                                : "border-slate-200 bg-white hover:border-violet-300 hover:bg-violet-50/30"
                                        }`}
                                    >
                                        <div className="w-full h-14">
                                            {opt.value === "Not attached" && <PositionNotAttached active={isActive} />}
                                            {opt.value === "Attached-1 side" && <Position1Side active={isActive} />}
                                            {opt.value === "Attached-2 side" && <Position2Side active={isActive} />}
                                            {opt.value === "Attached-3 side" && <Position3Side active={isActive} />}
                                        </div>
                                        <span className={`text-[11px] font-semibold text-center leading-tight ${isActive ? "text-violet-800" : "text-slate-700"}`}>
                                            {opt.label}
                                        </span>
                                        <span className="text-[9px] text-slate-500 leading-snug text-center">
                                            {opt.description}
                                        </span>
                                    </button>
                                );
                            })}
                        </div>
                        {errors.position && (
                            <span className="text-[10px] text-rose-600 font-mono block px-5 pb-3">
                                {errors.position.message}
                            </span>
                        )}
                    </div>

                    {/* NEW Section 7: Plan Configuration — footprint grid */}
                    <div className="rounded-xl bg-card border border-border shadow-card overflow-hidden">
                        <div className="flex items-center gap-3 px-5 py-4 border-b border-indigo-100 bg-indigo-50/60">
                            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-indigo-100">
                                <Grid3x3 className="h-4 w-4 text-indigo-700" />
                            </span>
                            <div>
                                <p className="text-sm font-semibold text-foreground">
                                    Plan Configuration
                                </p>
                                <p className="text-xs text-indigo-700/70">
                                    Footprint shape in plan view
                                </p>
                            </div>
                        </div>
                        <div className="px-5 py-5 grid grid-cols-5 sm:grid-cols-5 gap-3">
                            {PLAN_CONFIGURATION_OPTIONS.map((opt) => {
                                const isActive = watchedPlanConfig === opt.value;
                                return (
                                    <button
                                        key={opt.value}
                                        type="button"
                                        onClick={() => setValue("plan_configuration", opt.value)}
                                        className={`flex flex-col items-center gap-1.5 p-2 rounded-xl border-2 transition-all cursor-pointer select-none ${
                                            isActive
                                                ? "border-indigo-500 bg-indigo-50 shadow-sm"
                                                : "border-slate-200 bg-white hover:border-indigo-300 hover:bg-indigo-50/30"
                                        }`}
                                    >
                                        <div className="w-10 h-10">
                                            <FootprintSVG shape={opt.value} active={isActive} />
                                        </div>
                                        <span className={`text-[9px] font-semibold text-center leading-tight ${isActive ? "text-indigo-800" : "text-slate-600"}`}>
                                            {opt.label}
                                        </span>
                                    </button>
                                );
                            })}
                        </div>
                        {errors.plan_configuration && (
                            <span className="text-[10px] text-rose-600 font-mono block px-5 pb-3">
                                {errors.plan_configuration.message}
                            </span>
                        )}
                    </div>

                    {/* NEW Section 8: Other Floor Type */}
                    <div className="rounded-xl bg-card border border-border shadow-card overflow-hidden">
                        <div className="flex items-center gap-3 px-5 py-4 border-b border-teal-100 bg-teal-50/60">
                            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-teal-100">
                                <Layers className="h-4 w-4 text-teal-700" />
                            </span>
                            <div>
                                <p className="text-sm font-semibold text-foreground">
                                    Other Floor Type
                                </p>
                                <p className="text-xs text-teal-700/70">
                                    Floor construction above the ground floor (select &quot;Not applicable&quot; for single-storey)
                                </p>
                            </div>
                        </div>
                        <div className="px-5 py-5 grid grid-cols-1 sm:grid-cols-2 gap-3">
                            {OTHER_FLOOR_TYPE_OPTIONS.map((opt) => {
                                const isActive = watchedOtherFloorType === opt.value;
                                return (
                                    <button
                                        key={opt.value}
                                        type="button"
                                        onClick={() => setValue("other_floor_type", opt.value)}
                                        className={`flex flex-col items-start gap-1 p-3 rounded-xl border-2 transition-all cursor-pointer select-none text-left ${
                                            isActive
                                                ? "border-teal-500 bg-teal-50 shadow-sm"
                                                : "border-slate-200 bg-white hover:border-teal-300 hover:bg-teal-50/30"
                                        }`}
                                    >
                                        <span className={`text-xs font-semibold ${isActive ? "text-teal-800" : "text-slate-700"}`}>
                                            {opt.label}
                                        </span>
                                        <span className="text-[10px] text-slate-500 leading-snug">
                                            {opt.description}
                                        </span>
                                        {opt.value === "TImber/Bamboo-Mud" && (
                                            <span className="text-[9px] text-amber-600 italic mt-0.5">
                                                Survey spelling preserved
                                            </span>
                                        )}
                                    </button>
                                );
                            })}
                        </div>
                        {errors.other_floor_type && (
                            <span className="text-[10px] text-rose-600 font-mono block px-5 pb-3">
                                {errors.other_floor_type.message}
                            </span>
                        )}
                    </div>

                    {/* Section 9: Location Context */}
                    <FormSectionCard
                        title="Building Location"
                        desc="Pin the building coordinates manually for
                            hazard zone analysis"
                        Icon={Globe}
                        className="px-5 py-5 space-y-4"
                    >
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
                                    className="w-full bg-white border border-slate-200 text-slate-900 placeholder-slate-400 rounded-lg py-2.5 px-3.5 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600 transition-all"
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
                                    className="w-full bg-white border border-slate-200 text-slate-900 placeholder-slate-400 rounded-lg py-2.5 px-3.5 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600 transition-all"
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
                    </FormSectionCard>

                    {/* Action Area (Submit / Reset form) */}
                    <FormActionArea
                        isLoading={isLoading}
                        handleFormReset={handleFormReset}
                    />
                </form>
            </main>

            <Footer />

            {isLoading && (
                <MultiStageLoadingDisplay
                    stageStatuses={stageStatuses}
                    statusText={statusText}
                    isComplete={isComplete}
                />
            )}
        </div>
    );
}
