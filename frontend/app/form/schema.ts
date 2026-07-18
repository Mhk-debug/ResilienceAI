import z from "zod";

export const formSchema = z.object({
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

export type FormFields = z.infer<typeof formSchema>;