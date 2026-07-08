"use client";

import "leaflet/dist/leaflet.css";
import { useEffect, useRef, useState } from "react";
import { MapPin, Compass } from "lucide-react";
import type L from "leaflet";

interface LocationPickerProps {
    latitude: number;
    longitude: number;
    onLocationChange: (lat: number, lng: number) => void;
}

export default function LocationPicker({
    latitude,
    longitude,
    onLocationChange,
}: LocationPickerProps) {
    const [leafletInstance, setLeafletInstance] = useState<typeof L | null>(
        null,
    );
    const [addressName, setAddressName] = useState<string>(
        "Locating position...",
    );

    const mapContainerRef = useRef<HTMLDivElement>(null);
    const mapRef = useRef<L.Map | null>(null);
    const markerRef = useRef<L.Marker | null>(null);
    const abortControllerRef = useRef<AbortController | null>(null);

    // Dynamic import to support SSR frameworks (like Next.js) safely
    useEffect(() => {
        import("leaflet").then((leaflet) => {
            setLeafletInstance(leaflet);
        });
    }, []);

    // Reverse geocode latitude/longitude to a readable place name
    const reverseGeocode = async (lat: number, lng: number) => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }

        const controller = new AbortController();
        abortControllerRef.current = controller;

        try {
            const response = await fetch(
                `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`,
                {
                    headers: { "Accept-Language": "en" },
                    signal: controller.signal,
                },
            );

            if (response.ok) {
                const data = await response.json();
                setAddressName(
                    data.display_name ||
                        `Lat: ${lat.toFixed(5)}, Lng: ${lng.toFixed(5)}`,
                );
            } else {
                setAddressName(
                    `Lat: ${lat.toFixed(5)}, Lng: ${lng.toFixed(5)}`,
                );
            }
        } catch (error) {
            if ((error as Error).name !== "AbortError") {
                setAddressName(
                    `Lat: ${lat.toFixed(5)}, Lng: ${lng.toFixed(5)}`,
                );
            }
        }
    };

    // Initialize Map once Leaflet and the DOM container are ready
    useEffect(() => {
        if (!leafletInstance || !mapContainerRef.current || mapRef.current)
            return;

        const initialLat = latitude || 37.7749;
        const initialLng = longitude || -122.4194;

        // Custom modern SVG pin icon
        const customPinIcon = leafletInstance.divIcon({
            html: `
                <div class="relative flex items-center justify-center">
                    <div class="absolute -top-1 w-9 h-9 bg-rose-500/30 rounded-full animate-ping"></div>
                    <div class="w-8 h-8 flex items-center justify-center bg-rose-600 hover:bg-rose-500 text-white rounded-full border-2 border-white shadow-xl transform transition-transform duration-200 hover:scale-110">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
                            <circle cx="12" cy="10" r="3"/>
                        </svg>
                    </div>
                </div>
            `,
            className: "custom-leaflet-pin",
            iconSize: [32, 32],
            iconAnchor: [16, 32],
        });

        const map = leafletInstance
            .map(mapContainerRef.current, {
                zoomControl: false,
            })
            .setView([initialLat, initialLng], 12);

        leafletInstance
            .tileLayer(
                "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
                {
                    attribution:
                        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
                    subdomains: "abcd",
                    maxZoom: 20,
                },
            )
            .addTo(map);

        leafletInstance.control.zoom({ position: "bottomright" }).addTo(map);

        const marker = leafletInstance
            .marker([initialLat, initialLng], {
                draggable: true,
                icon: customPinIcon,
            })
            .addTo(map);

        // Marker Drag events
        marker.on("dragend", (e: L.LeafletEvent) => {
            const targetMarker = e.target as L.Marker;
            const newLatLng = targetMarker.getLatLng();
            onLocationChange(newLatLng.lat, newLatLng.lng);
            reverseGeocode(newLatLng.lat, newLatLng.lng);
        });

        // Map click events to move marker
        map.on("click", (e: L.LeafletMouseEvent) => {
            const { lat, lng } = e.latlng;
            marker.setLatLng([lat, lng]);
            onLocationChange(lat, lng);
            reverseGeocode(lat, lng);
        });

        mapRef.current = map;
        markerRef.current = marker;

        // 1. Force immediate recalculation of map container bounds
        map.invalidateSize();

        // 2. Fallback macro-task to handle trailing CSS/flexbox layout paints
        setTimeout(() => {
            if (mapRef.current) {
                mapRef.current.invalidateSize();
            }
        }, 100);

        reverseGeocode(initialLat, initialLng);

        return () => {
            if (mapRef.current) {
                mapRef.current.remove();
                mapRef.current = null;
            }
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        };
    }, [leafletInstance]);

    // Track and reflect external parent prop updates down to the map
    useEffect(() => {
        if (mapRef.current && markerRef.current) {
            const currentMarkerLatLng = markerRef.current.getLatLng();
            const hasMoved =
                Math.abs(currentMarkerLatLng.lat - latitude) > 0.0001 ||
                Math.abs(currentMarkerLatLng.lng - longitude) > 0.0001;

            if (hasMoved) {
                markerRef.current.setLatLng([latitude, longitude]);
                mapRef.current.setView(
                    [latitude, longitude],
                    mapRef.current.getZoom(),
                );
                reverseGeocode(latitude, longitude);
            }
        }
    }, [latitude, longitude]);

    if (!leafletInstance) {
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
                    className="w-full h-full"
                    id="seismic-map-container"
                />

                {/* GIS Site Coordinates Overlay */}
                <div className="absolute top-3 left-3 z-[1000] bg-white/95 backdrop-blur-md border border-slate-200 text-[11px] font-mono p-2.5 rounded-lg flex flex-col gap-1 shadow-md text-slate-800 pointer-events-auto">
                    <div className="flex items-center gap-1.5">
                        <Compass className="w-3.5 h-3.5 text-teal-600 animate-spin-slow" />
                        <span className="text-slate-500 uppercase font-bold text-[10px]">
                            GIS Site Coordinates
                        </span>
                    </div>
                    <div className="grid grid-cols-2 gap-x-3 mt-1 text-slate-900">
                        <div>
                            LAT:{" "}
                            <span className="text-teal-600 font-bold">
                                {latitude.toFixed(5)}
                            </span>
                        </div>
                        <div>
                            LNG:{" "}
                            <span className="text-teal-600 font-bold">
                                {longitude.toFixed(5)}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Floating Guidance Banner */}
                <div className="absolute bottom-3 left-3 z-[1000] bg-white/95 backdrop-blur-sm px-2.5 py-1 rounded-md text-[10px] text-slate-500 border border-slate-200 pointer-events-none shadow-sm">
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
