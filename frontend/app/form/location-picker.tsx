"use client";

import "leaflet/dist/leaflet.css";
import { useEffect, useRef, useState, useCallback } from "react";
import { MapPin, Compass } from "lucide-react";
import type L from "leaflet";
import { normalizeLatitude, normalizeLongitude } from "@/utils/tools";

// --- Types ---
interface LocationPickerProps {
    latitude: number;
    longitude: number;
    onLocationChange: (lat: number, lng: number) => void;
}

// --- Constants & Templates ---
const DEFAULT_LAT = 37.7749;
const DEFAULT_LNG = -122.4194;
const DEFAULT_ZOOM = 12;

const TILE_LAYER_URL =
    "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";
const TILE_LAYER_ATTRIBUTION =
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';

const CUSTOM_PIN_HTML = `
    <div class="relative flex items-center justify-center">
        <div class="absolute -top-1 w-9 h-9 bg-rose-500/30 rounded-full animate-ping"></div>
        <div class="w-8 h-8 flex items-center justify-center bg-rose-600 hover:bg-rose-500 text-white rounded-full border-2 border-white shadow-xl transform transition-transform duration-200 hover:scale-110">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
                <circle cx="12" cy="10" r="3"/>
            </svg>
        </div>
    </div>
`;

// --- Main Component ---
export default function LocationPicker({
    latitude,
    longitude,
    onLocationChange,
}: LocationPickerProps) {
    // State
    const [leaflet, setLeaflet] = useState<typeof L | null>(null);
    const [addressName, setAddressName] = useState<string>(
        "Locating position...",
    );

    // Refs
    const mapContainerRef = useRef<HTMLDivElement>(null);
    const mapRef = useRef<L.Map | null>(null);
    const markerRef = useRef<L.Marker | null>(null);
    const abortControllerRef = useRef<AbortController | null>(null);

    // 1. Load Leaflet Dynamically (SSR Safe)
    useEffect(() => {
        let isMounted = true;
        import("leaflet").then((L) => {
            if (isMounted) setLeaflet(L);
        });
        return () => {
            isMounted = false;
        };
    }, []);

    // 2. Reverse Geocoding Logic
    const reverseGeocode = useCallback(async (lat: number, lng: number) => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }

        const controller = new AbortController();
        abortControllerRef.current = controller;

        const fallbackName = `Lat: ${lat.toFixed(5)}, Lng: ${lng.toFixed(5)}`;

        try {
            const response = await fetch(
                `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`,
                {
                    headers: { "Accept-Language": "en" },
                    signal: controller.signal,
                },
            );

            if (!response.ok) throw new Error("Network response was not ok");

            const data = await response.json();
            setAddressName(data.display_name || fallbackName);
        } catch (error) {
            if ((error as Error).name !== "AbortError") {
                setAddressName(fallbackName);
            }
        }
    }, []);

    // 3. Initialize Map
    useEffect(() => {
        if (!leaflet || !mapContainerRef.current || mapRef.current) return;

        // --- THE FIX: Normalize the incoming props before giving them to Leaflet ---
        const initialLat = normalizeLatitude(latitude || DEFAULT_LAT);
        const initialLng = normalizeLongitude(longitude || DEFAULT_LNG);

        // Configure Map
        const map = leaflet
            .map(mapContainerRef.current, { zoomControl: false })
            .setView([initialLat, initialLng], DEFAULT_ZOOM);

        leaflet
            .tileLayer(TILE_LAYER_URL, {
                attribution: TILE_LAYER_ATTRIBUTION,
                subdomains: "abcd",
                maxZoom: 20,
                minZoom: 3,
            })
            .addTo(map);

        leaflet.control.zoom({ position: "bottomright" }).addTo(map);

        // Configure Marker
        const customPinIcon = leaflet.divIcon({
            html: CUSTOM_PIN_HTML,
            className: "custom-leaflet-pin",
            iconSize: [32, 32],
            iconAnchor: [16, 32],
        });

        const marker = leaflet
            .marker([initialLat, initialLng], {
                draggable: true,
                icon: customPinIcon,
            })
            .addTo(map);

        // Event Handlers
        const handleLocationUpdate = (lat: number, lng: number) => {
            // Keep clamping lat for parent state safety, but allow long wrapping
            const normLat = normalizeLatitude(lat);
            const normLng = normalizeLongitude(lng);
            onLocationChange(normLat, normLng);
            reverseGeocode(normLat, normLng);
        };

        marker.on("dragend", (e: L.LeafletEvent) => {
            const { lat, lng } = (e.target as L.Marker).getLatLng();
            handleLocationUpdate(lat, lng);
        });

        map.on("click", (e: L.LeafletMouseEvent) => {
            // Leaflet provides a built-in helper to wrap coordinates back into the primary world map boundaries (-180 to 180 long, -90 to 90 lat)
            const wrappedLatLng = map.wrapLatLng(e.latlng);

            // Move marker to the newly wrapped position
            marker.setLatLng(wrappedLatLng);

            // Instantly pan the map to center on the correct wrapped location
            map.setView(wrappedLatLng, map.getZoom());

            // Push the normalized coordinates back up to the parent component
            handleLocationUpdate(wrappedLatLng.lat, wrappedLatLng.lng);
        });

        // Store references
        mapRef.current = map;
        markerRef.current = marker;

        // Fix potential render sizing issues
        map.invalidateSize();
        setTimeout(() => mapRef.current?.invalidateSize(), 100);

        // Initial Geocode
        reverseGeocode(initialLat, initialLng);

        // Cleanup
        return () => {
            if (mapRef.current) {
                mapRef.current.remove();
                mapRef.current = null;
            }
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        };
    }, [leaflet, reverseGeocode]); // Intentionally omitting latitude/longitude to prevent re-initialization

    // --- Render ---
    if (!leaflet) {
        return (
            <div className="h-70 md:h-85 flex items-center justify-center border border-slate-200 rounded-xl bg-slate-50 text-sm text-slate-400 font-medium">
                Loading map assets...
            </div>
        );
    }

    return (
        <div className="space-y-3">
            <div className="relative rounded-xl overflow-hidden border border-slate-200 h-70 md:h-85 shadow-sm bg-white">
                <div
                    ref={mapContainerRef}
                    className="w-full h-full z-50"
                    id="seismic-map-container"
                />

                {/* GIS Site Coordinates Overlay */}
                <div className="absolute top-3 left-3 z-50 bg-white/95 backdrop-blur-md border border-slate-200 text-[11px] font-mono p-2.5 rounded-lg flex flex-col gap-1 shadow-md text-slate-800 pointer-events-auto">
                    <div className="flex items-center gap-1.5">
                        <Compass className="w-3.5 h-3.5 text-blue-600 animate-spin-slow" />
                        <span className="text-slate-500 uppercase font-bold text-[10px]">
                            GIS Site Coordinates
                        </span>
                    </div>
                    <div className="grid grid-cols-2 gap-x-3 mt-1 text-slate-900">
                        <div>
                            LAT:{" "}
                            <span className="text-blue-600 font-bold">
                                {latitude.toFixed(5)}
                            </span>
                        </div>
                        <div>
                            LNG:{" "}
                            <span className="text-blue-600 font-bold">
                                {longitude.toFixed(5)}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Floating Guidance Banner */}
                <div className="absolute bottom-3 left-3 z-1000 bg-white/95 backdrop-blur-sm px-2.5 py-1 rounded-md text-[10px] text-slate-500 border border-slate-200 pointer-events-none shadow-sm">
                    Click map or drag pin to re-locate
                </div>
            </div>

            {/* Address Context Bar */}
            <div className="bg-white border border-slate-200 rounded-lg p-3.5 flex items-start gap-2.5 shadow-sm">
                <MapPin className="w-4 h-4 text-rose-500 shrink-0 mt-0.5 animate-pulse" />
                <div className="space-y-0.5">
                    <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider font-bold">
                        Selected Assessment Site
                    </div>
                    <p
                        className="text-xs text-slate-800 leading-relaxed font-sans font-medium"
                        id="selected-address-text"
                    >
                        {addressName}
                    </p>
                </div>
            </div>
        </div>
    );
}
