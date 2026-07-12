import type { BuildingLLMContext } from "@/app/types";
import { Building, Layers, ShieldCheck, Ruler, Calendar, Grid, CheckCircle, XCircle } from "lucide-react";

interface BuildingProfileCardProps {
  context: BuildingLLMContext;
  resilienceScore: number;
}

export default function BuildingProfileCard({ context }: BuildingProfileCardProps) {
  const { structural, material, substructure } = context;

  const substructureItems = [
    { key: "rc_engineered", label: "RC Engineered Substructure", active: substructure.rc_engineered },
    { key: "cement_brick", label: "Cement Brick Framing", active: substructure.cement_brick },
    { key: "mud_mortar_stone", label: "Mud Mortar Stone", active: substructure.mud_mortar_stone },
    { key: "rc_non_engineered", label: "RC Non-Engineered", active: substructure.rc_non_engineered },
    { key: "adobe_mud", label: "Adobe Mud Composition", active: substructure.adobe_mud },
    { key: "timber", label: "Timber Framing", active: substructure.timber },
  ];

  return (
    <div id="building-profile-card" className="bg-white border border-slate-200 rounded-3xl p-6 shadow-xs flex flex-col justify-between h-full hover:border-blue-300 hover:shadow-md transition-all duration-150">
      
      {/* Card Header */}
      <div className="space-y-1.5 border-b border-slate-100 pb-3">
        <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Section 1.1 — Asset Under Assessment</span>
        <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-1.5">
          <Building className="w-4.5 h-4.5 text-blue-600" />
          Building Engineering Profile
        </h3>
      </div>

      {/* Profile Details grouped in clear subsections */}
      <div className="space-y-5 my-4">
        
        {/* Subsection 1: Structural Parameters */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
            <Layers className="w-3.5 h-3.5 text-blue-600" />
            Structural Specifications
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-slate-50/50 border border-slate-200/50 p-2.5 rounded-xl space-y-0.5">
              <span className="text-[10px] text-slate-450 font-medium">Floors Count</span>
              <div className="text-xs font-bold text-slate-800 flex items-center gap-1">
                <Grid className="w-3.5 h-3.5 text-slate-400" />
                {structural.floors} Storeys
              </div>
            </div>
            <div className="bg-slate-50/50 border border-slate-200/50 p-2.5 rounded-xl space-y-0.5">
              <span className="text-[10px] text-slate-450 font-medium">Building Age</span>
              <div className="text-xs font-bold text-slate-800 flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                {structural.age_years} Years
              </div>
            </div>
            <div className="bg-slate-50/50 border border-slate-200/50 p-2.5 rounded-xl space-y-0.5">
              <span className="text-[10px] text-slate-450 font-medium">Floor Area</span>
              <div className="text-xs font-bold text-slate-800 flex items-center gap-1">
                <Ruler className="w-3.5 h-3.5 text-slate-400" />
                {structural.floor_area_sq_feets.toLocaleString()} sq ft
              </div>
            </div>
            <div className="bg-slate-50/50 border border-slate-200/50 p-2.5 rounded-xl space-y-0.5">
              <span className="text-[10px] text-slate-450 font-medium">Overall Height</span>
              <div className="text-xs font-bold text-slate-800 flex items-center gap-1">
                <Ruler className="w-3.5 h-3.5 text-slate-400" />
                {structural.height_feets} ft
              </div>
            </div>
          </div>
        </div>

        {/* Subsection 2: Materials */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
            <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
            Key Substructure Components
          </div>
          <div className="grid grid-cols-2 gap-2 text-[11px]">
            {substructureItems.map((item) => (
              <div 
                key={item.key} 
                className={`flex items-center gap-1.5 px-2 py-1.5 rounded-lg border transition-all ${
                  item.active 
                    ? "bg-blue-50 border-blue-100 text-blue-800 font-semibold" 
                    : "bg-slate-50/40 border-slate-100 text-slate-400"
                }`}
              >
                {item.active ? (
                  <CheckCircle className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                ) : (
                  <XCircle className="w-3.5 h-3.5 text-slate-300 shrink-0" />
                )}
                <span className="truncate">{item.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Subsection 3: Substructure Types */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
            <Building className="w-3.5 h-3.5 text-blue-600" />
            Envelope & Material Classification
          </div>
          <div className="divide-y divide-slate-100 text-xs bg-slate-50/40 border border-slate-200/60 rounded-xl overflow-hidden">
            <div className="p-2.5 flex items-center justify-between gap-2">
              <span className="text-slate-500 font-medium text-[11px] shrink-0">Foundation</span>
              <strong className="text-slate-800 font-semibold text-right leading-tight">{material.foundation_type}</strong>
            </div>
            <div className="p-2.5 flex items-center justify-between gap-2">
              <span className="text-slate-500 font-medium text-[11px] shrink-0">Roof Envelope</span>
              <strong className="text-slate-800 font-semibold text-right leading-tight">{material.roof_type}</strong>
            </div>
            <div className="p-2.5 flex items-center justify-between gap-2">
              <span className="text-slate-500 font-medium text-[11px] shrink-0">Ground Floor</span>
              <strong className="text-slate-800 font-semibold text-right leading-tight">{material.ground_floor_type}</strong>
            </div>
          </div>
        </div>

      </div>

      {/* Engineering Rating Label */}
      <div className="pt-2 border-t border-slate-100 text-[10px] text-slate-400 font-mono">
        Classification: EN-1998 Eurocode 8 Seismic Diagnostic Specs
      </div>

    </div>
  );
}
