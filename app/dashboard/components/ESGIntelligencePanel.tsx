"use client";

import React from "react";
import { Sparkles, Globe, AlertTriangle } from "lucide-react";

interface ESGIntelligencePanelProps {
  sustainabilityMetrics: {
    total_energy_kwh?: number;
    total_water_liters?: number;
    total_waste_kg?: number;
  } | null;
  loadingSustMetrics: boolean;
}

const EmptySlate = ({ message }: { message: string }) => (
  <div className="bg-slate-50 border border-slate-100 p-4 rounded-lg text-center">
    <p className="text-[10px] text-slate-500 font-semibold leading-relaxed">{message}</p>
  </div>
);

const ESG_EMPTY_MESSAGE =
  "No ESG metrics generated yet. Run Conformance Analysis and Carbon Attribution with mapped energy_kwh, water_liters, or waste_kg columns to unlock ESG analytics.";

export function ESGIntelligencePanel({
  sustainabilityMetrics,
  loadingSustMetrics
}: ESGIntelligencePanelProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

      {/* Energy Consumption */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm space-y-4">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="font-extrabold text-sm text-slate-800">Energy Consumption</h3>
            <p className="text-[10px] text-slate-400 mt-0.5">Rolled-up total kilowatt-hour electrical usage.</p>
          </div>
          <Sparkles className="h-5 w-5 text-amber-500" />
        </div>
        <div className="text-2xl font-black text-slate-800">
          {loadingSustMetrics ? (
            <div className="h-8 bg-slate-100 rounded animate-pulse w-28" />
          ) : sustainabilityMetrics?.total_energy_kwh !== undefined && sustainabilityMetrics.total_energy_kwh > 0 ? (
            `${sustainabilityMetrics.total_energy_kwh.toLocaleString()} kWh`
          ) : (
            <EmptySlate message={ESG_EMPTY_MESSAGE} />
          )}
        </div>
      </div>

      {/* Water Usage */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm space-y-4">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="font-extrabold text-sm text-slate-800">Water Usage</h3>
            <p className="text-[10px] text-slate-400 mt-0.5">Rolled-up total clean water metrics (Liters).</p>
          </div>
          <Globe className="h-5 w-5 text-blue-500" />
        </div>
        <div className="text-2xl font-black text-slate-800">
          {loadingSustMetrics ? (
            <div className="h-8 bg-slate-100 rounded animate-pulse w-28" />
          ) : sustainabilityMetrics?.total_water_liters !== undefined && sustainabilityMetrics.total_water_liters > 0 ? (
            `${sustainabilityMetrics.total_water_liters.toLocaleString()} L`
          ) : (
            <EmptySlate message={ESG_EMPTY_MESSAGE} />
          )}
        </div>
      </div>

      {/* Waste Generated */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm space-y-4">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="font-extrabold text-sm text-slate-800">Waste Generated</h3>
            <p className="text-[10px] text-slate-400 mt-0.5">Solid waste output metrics (kg).</p>
          </div>
          <AlertTriangle className="h-5 w-5 text-rose-500" />
        </div>
        <div className="text-2xl font-black text-slate-800">
          {loadingSustMetrics ? (
            <div className="h-8 bg-slate-100 rounded animate-pulse w-28" />
          ) : sustainabilityMetrics?.total_waste_kg !== undefined && sustainabilityMetrics.total_waste_kg > 0 ? (
            `${sustainabilityMetrics.total_waste_kg.toLocaleString()} kg`
          ) : (
            <EmptySlate message={ESG_EMPTY_MESSAGE} />
          )}
        </div>
      </div>

    </div>
  );
}
